# ADR 0006: despliegue del MVP local en Railway con endurecimiento mínimo

Fecha: 2026-10-27. Estado: aceptado para el piloto de un solo usuario.

El MVP local (`apps/local_review_ui.py`) se desplegó en Railway
(https://mvp-web-production.up.railway.app) sin que existiera ninguna
decisión documentada previa de exponerlo en red: el único rastro era un
comentario de código. El documento, al nacer explícitamente como
`127.0.0.1`-only, de un solo usuario y sin cuentas, no tenía ningún control
pensado para una red pública: sin timeout ni límite de memoria en el parseo
de PDFs no confiables, con el handler `/convert` bloqueando en línea el
único proceso de uvicorn, y sin limpieza de `.generated/web_ui/`.

Decisión: mantener el despliegue como un servicio de un solo usuario de
confianza, protegido por HTTP Basic Auth (credenciales en variables de
entorno de Railway, no en el repositorio). No se construyen cuentas reales,
base de datos ni cola de tareas — eso sigue siendo el trabajo de F1 ya
descrito en `docs/AVANCE.md` y pospuesto en `docs/ALCANCE.md`. En su lugar
se añade `apps/conversion_isolation.py`: cada conversión corre en un
subproceso (`multiprocessing`, contexto `spawn`) nuevo por solicitud, con
timeout duro (`CONVERT_TIMEOUT_SECONDS`, terminate → espera de gracia →
kill), límite de memoria best-effort vía `RLIMIT_AS`
(`CONVERT_MEMORY_LIMIT_MB`, no-op en Windows), un semáforo de concurrencia
(`CONVERT_CONCURRENCY=1`, coherente con "un documento a la vez") y una
limpieza TTL periódica (`RETENTION_HOURS`, `CLEANUP_INTERVAL_SECONDS`) de
los directorios de trabajo.

Explícitamente fuera de alcance de esta decisión: autenticación por usuario
(JWT/OIDC), base de datos, Celery/RabbitMQ, multi-tenencia. Rotar las
credenciales de Basic Auth ya configuradas tampoco es parte de este cambio.
`docs/SEGURIDAD.md` describe la arquitectura objetivo F1+ con controles que
no existen en este MVP; esa reconciliación se registra aparte en el propio
documento, no se reescribe el documento para anticipar F1.
