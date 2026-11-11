# Configuración del MVP 0.7.0

Actualizado: 2026-11-10. La configuración efectiva está en
`apps/runtime_config.py`. Se lee una vez al importar la app: reiniciar tras
cambiar variables. `.env.example` es una plantilla; no existe carga automática
de `.env`.

| Variable | Predeterminado | Validación / efecto |
|---|---|---|
| APP_MODE | local | Solo `local` o `remote`. |
| HOST | 127.0.0.1 en local, 0.0.0.0 en remote | Local requiere loopback; también valida Host y dirección cliente. |
| PORT | 8420 | Entero 1–65535. |
| AUTH_USERNAME / AUTH_PASSWORD | Ausentes | Configurar ambas o ninguna; ambas obligatorias en remote. Usuario sin `:` ni caracteres de control. Comparación constante sobre UTF-8. |
| CONVERT_CONCURRENCY / WEB_CONCURRENCY / UVICORN_WORKERS | 1 | Solo se admite 1; ejecutar un proceso y una réplica. |
| CONVERT_TIMEOUT_SECONDS | 90 | Fecha límite de conversión y transferencia IPC. |
| CONVERT_GRACE_SECONDS | 5 | Espera de terminación antes de forzar cierre. |
| CONVERT_MEMORY_LIMIT_MB | 768 | Entero positivo; Job Object en Windows, RLIMIT_AS en POSIX; si falla su activación se rechaza convertir. |
| RETENTION_HOURS | 24 | Caducidad fija desde la creación del trabajo; las descargas no la renuevan. |
| CLEANUP_INTERVAL_SECONDS | 3600 | Barrido al arrancar y cada intervalo. |
| MAX_STORAGE_MB | 2048 | Presupuesto total del directorio web; debe ser ≥ MAX_JOB_MB. |
| MAX_JOB_MB | 512 | Presupuesto por trabajo, mínimo 26. Se reserva capacidad antes de recibir. |
| MIN_FREE_DISK_MB | 256 | Reserva mínima de disco además del presupuesto admitido. |

Las cantidades deben ser positivas y finitas; los límites MB usan MiB
(1024² bytes). Los límites fijos son un archivo PDF de hasta 25 MiB, 100 páginas,
8 campos multipart de hasta 4096 bytes y 1000 directorios retenidos. El cuerpo
HTTP tiene un margen multipart de 64 KiB además del archivo; se cuentan bytes
reales, incluso sin Content-Length. Un segundo trabajo se rechaza con 409 antes
de guardar su PDF. Los resultados de un trabajo no se publican parcialmente.

Ejemplo local, PowerShell:

```powershell
$env:APP_MODE = 'local'
$env:HOST = '127.0.0.1'
$env:PORT = '8420'
.\.venv\Scripts\python.exe -m apps.local_review_ui
```

En modo remoto establecer `APP_MODE=remote` y ambas credenciales en la
configuración del proceso, con un proxy HTTPS. Basic Auth representa una
credencial compartida de un usuario de confianza; no implementa cuentas ni
separación de documentos entre usuarios. La dirección Host/origen debe llegar
correctamente desde el proxy; restringir sus cabeceras reenviadas a proxies de
confianza. No se verifica ni modifica un despliegue remoto en esta entrega.

El almacenamiento web es `.generated/web_ui/` relativo al directorio de trabajo.
Conservar ese directorio de trabajo entre arranques y permitir escritura. El
bloqueo de admisión funciona entre procesos que comparten ese directorio, pero
no sustituye una cola distribuida ni autoriza réplicas adicionales.

`API_WORKERS`, `DATABASE_URL`, `CELERY_BROKER_URL`, JWT, S3, cuotas y métricas de
Prometheus no configuran el MVP. Son parte del diseño futuro descrito en el plan.
