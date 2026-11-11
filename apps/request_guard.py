"""Admission before multipart parsing, streaming limits and response protections."""
from __future__ import annotations

import logging
from urllib.parse import urlsplit

from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser
from starlette.requests import Request
from starlette.responses import HTMLResponse

from apps.job_store import FileLease, ensure_capacity
from apps.runtime_config import is_loopback, settings

logger = logging.getLogger("pdf_converter.requests")


class RequestTooLarge(MultiPartException):
    pass


class BoundedMultipartParser(MultiPartParser):
    def __init__(self, headers, stream, max_file_bytes):
        super().__init__(headers, stream, max_files=1, max_fields=8, max_part_size=4096)
        self.max_file_bytes = max_file_bytes
        self.file_bytes = 0

    def on_part_data(self, data, start, end):
        if self._current_part.file is not None:
            self.file_bytes += end - start
            if self.file_bytes > self.max_file_bytes:
                raise RequestTooLarge("El archivo excede el límite de 25 MB.")
        super().on_part_data(data, start, end)

    async def parse(self):
        try:
            return await super().parse()
        except BaseException:
            # Also close spools after disconnection/cancellation, not only parser errors.
            for stream in self._files_to_close_on_error:
                stream.close()
            raise


class Admission:
    """The permit outlives a cancelled HTTP request while its supervisor works."""
    def __init__(self, semaphore, disk_lease):
        self.semaphore, self.disk_lease = semaphore, disk_lease
        self.task = None
        self.closed = False

    def close(self):
        if not self.closed:
            self.closed = True
            self.disk_lease.close()
            self.semaphore.release()

    def request_finished(self):
        if self.task is not None and not self.task.done():
            self.task.add_done_callback(lambda _: self.close())
        else:
            self.close()


class RequestGuard:
    def __init__(self, app, *, root, semaphore, authorized, render_error, max_upload):
        self.app = app
        self.root, self.semaphore = root, semaphore
        self.authorized, self.render_error, self.max_upload = authorized, render_error, max_upload

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)

        async def protected_send(message):
            if message["type"] == "http.response.start":
                message = dict(message, headers=list(message.get("headers", [])))
                headers = {
                    "x-content-type-options": "nosniff", "x-frame-options": "DENY",
                    "referrer-policy": "no-referrer", "cache-control": "no-store",
                    "content-security-policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
                        "img-src 'self' data:; object-src 'none'; base-uri 'none'; "
                        "form-action 'self'; frame-ancestors 'none'",
                }
                message["headers"] = [(k, v) for k, v in message["headers"] if k.lower().decode() not in headers]
                message["headers"].extend((k.encode(), v.encode()) for k, v in headers.items())
            await send(message)

        async def deny(status, message, headers=None):
            response = HTMLResponse(self.render_error(message), status_code=status, headers=headers)
            await response(scope, receive, protected_send)

        # Local mode remains safe even if someone bypasses main() with uvicorn CLI.
        hostname = request.url.hostname or ""
        peer = (scope.get("client") or ("",))[0]
        test_client = peer == "testclient" and hostname == "testserver"
        if settings.mode == "local" and not (test_client or (is_loopback(hostname) and is_loopback(peer))):
            await deny(403, "El modo local solo admite acceso desde localhost.")
            return
        if not self.authorized(request):
            await deny(401, "Se requiere autenticación.", {"WWW-Authenticate": 'Basic realm="PDF Converter", charset="UTF-8"'})
            return
        if request.method == "POST":
            origin = request.headers.get("origin")
            # Chromium may send Origin: null for native forms with no-referrer.
            # Fetch Metadata still distinguishes a same-origin navigation from
            # an opaque/sandboxed cross-site form; browsers forbid JS from forging it.
            try:
                parsed_origin = urlsplit(origin) if origin and origin != "null" else None
            except ValueError:
                await deny(403, "El origen de la solicitud no es válido.")
                return
            same_origin = (parsed_origin.scheme == request.url.scheme and
                           parsed_origin.netloc.lower() == request.headers.get("host", "").lower()) if parsed_origin else True
            if origin == "null":
                same_origin = request.headers.get("sec-fetch-site") == "same-origin"
            if request.headers.get("sec-fetch-site") == "cross-site":
                same_origin = False
            if not same_origin:
                await deny(403, "El origen de la solicitud no es válido.")
                return

        admission = None
        if request.method == "POST" and scope["path"] == "/convert":
            # No await between locked() and acquire(): fail fast on a single event loop.
            semaphore = self.semaphore()
            if semaphore.locked():
                await deny(409, "Ya hay una conversión en curso. Inténtalo de nuevo en unos segundos.", {"Retry-After": "3"})
                return
            await semaphore.acquire()
            try:
                disk_lease = FileLease(self.root() / ".admission.lock")
            except (PermissionError, BlockingIOError):
                semaphore.release()
                await deny(409, "Ya hay una conversión en curso. Inténtalo de nuevo en unos segundos.")
                return
            except OSError:
                semaphore.release()
                await deny(503, "No hay almacenamiento disponible. Inténtalo más tarde.")
                return
            admission = Admission(semaphore, disk_lease)
            scope.setdefault("state", {})["conversion_admission"] = admission
        try:
            if admission:
                # Reserve enough for one bounded job before receiving or spooling any bytes.
                try:
                    ensure_capacity(self.root())
                except OSError as exc:
                    logger.warning("admission_storage_refused error_type=%s", type(exc).__name__)
                    await deny(503, "No hay espacio suficiente para convertir. Inténtalo más tarde.")
                    return
                max_body = self.max_upload() + 64 * 1024  # Bounded multipart overhead.
                content_length = request.headers.get("content-length")
                if content_length is not None:
                    try:
                        length = int(content_length)
                        if length < 0:
                            raise ValueError()
                    except ValueError:
                        await deny(400, "El tamaño de la solicitud no es válido.")
                        return
                    if length > max_body:
                        await deny(413, "El archivo excede el límite de 25 MB.")
                        return
                consumed = 0
                original_receive = receive

                async def bounded_receive():
                    nonlocal consumed
                    message = await original_receive()
                    if message["type"] == "http.request":
                        consumed += len(message.get("body", b""))
                        if consumed > max_body:
                            raise RequestTooLarge("El archivo excede el límite de 25 MB.")
                    return message

                receive = bounded_receive
            await self.app(scope, receive, protected_send)
        finally:
            if admission:
                admission.request_finished()
