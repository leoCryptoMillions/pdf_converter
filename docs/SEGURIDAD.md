# Seguridad efectiva del MVP

Actualizado: 2026-11-10 · 0.7.0. Este documento describe controles implementados
en el conversor de un usuario. La arquitectura futura con cuentas y servicios
se conserva en el plan; no constituye evidencia de controles desplegados.

## Acceso y respuestas

El modo local vincula loopback y valida Host y dirección cliente. El modo
remoto exige ambas credenciales Basic Auth al arrancar; configuración parcial
falla cerrada. Las rutas de ayuda, archivos estáticos y descargas pasan por la
misma protección. Credenciales Unicode no producen errores de comparación.
No hay cuentas, roles, JWT ni separación entre distintos usuarios.

Los POST rechazan orígenes distintos y Fetch Metadata cross-site. Los formularios
del propio navegador con Origin:null requieren Sec-Fetch-Site:same-origin.
Todas las respuestas añaden `Cache-Control: no-store`, CSP, nosniff, DENY y
no-referrer. Un proxy HTTPS es necesario si se utiliza el modo remoto.

## PDFs y recursos

La admisión ocurre antes de leer multipart. Se limita un PDF a 25 MiB, el cuerpo
completo, el número/tamaño de campos y el disco reservado. Se validan firma PDF,
cifrado y hasta 100 páginas dentro del proceso de conversión. Cada trabajo usa
un UUID del servidor; las descargas aceptan una lista fija de nombres y solo
resultados completos no caducados. Los nombres del usuario se escapan en HTML.
XLSX conserva valores como texto de forma predeterminada y protege fórmulas.

La conversión corre con spawn, límite temporal y límite nativo de memoria
activado antes del parser: Windows Job Objects y POSIX RLIMIT_AS. Un fallo al
activar el límite impide procesar. El padre recibe mientras supervisa al hijo;
el IPC tiene presupuesto y los detalles extensos van a archivos. La cancelación
y el apagado conservan el permiso hasta terminar el subproceso. Se soporta un
proceso servidor y una réplica, con bloqueo de disco adicional entre procesos
que comparten almacenamiento.

Estos controles limitan recursos de un subproceso que ejecuta bajo la misma
identidad del usuario. No implementan aislamiento de red, una identidad de
sistema separada, antivirus, cuotas por usuario ni un sandbox de privilegios.

## Retención y observación

Cada trabajo guarda creación, caducidad y estado. Las descargas vencidas
responden 410; la limpieza se ejecuta al arrancar y periódicamente, omitiendo
trabajos con bloqueo activo. Los fallos se retiran y los resultados se publican
mediante un cambio de directorio. Los fallos de borrado quedan registrados para
reintentar el barrido. Los logs técnicos usan UUID, estado, duración y tipo de
error, sin texto del PDF ni credenciales. El operador controla acceso, copias y
retención de los logs del servidor/proxy.

El TTL web no elimina el corpus, las evidencias de `.generated/` fuera de
`web_ui`, las descargas guardadas por el usuario ni backups. No-store solicita
no almacenar caché; no borra copias ya descargadas. No se afirma cifrado del
disco ni borrado criptográfico. Ver [RUNBOOK.md](RUNBOOK.md).

## Verificación y dependencias

`tests/unit/test_mvp_hardening.py`, `test_conversion_isolation.py` y
`test_local_review_ui.py` comprueban acceso, cargas, cancelación, memoria Windows,
expiración, limpieza y descargas con documentos ficticios. Los checks de
instalación y Chromium están en `scripts/check_release.py`.

Los locks fijan versiones y hashes. `python -m scripts.check_release --audit`
consulta vulnerabilidades y genera un SBOM CycloneDX. Un resultado sin
vulnerabilidades conocidas refleja la consulta de esa fecha, no un monitoreo
continuo. El inventario de licencias es técnico; la revisión de distribución
del binario y sus avisos sigue pendiente. No se ejecutó un pentest ni se
certificó cumplimiento regulatorio.

Ante un incidente, detener el acceso al servicio, preservar únicamente la
evidencia autorizada, revisar UUID/fechas y tipos de errores, corregir y rotar
credenciales si estuvieron expuestas. Las responsabilidades y notificaciones
deben asignarse según el incidente; el repositorio no inventa responsables.
