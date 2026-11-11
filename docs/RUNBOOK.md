# Operación del MVP 0.7.0

Actualizado: 2026-11-10. Un usuario, un proceso, una réplica y almacenamiento
local del servidor Windows. La entrega requerida es web en Windows, con acceso
desde el navegador. La app activa es `apps.local_review_ui`; los procedimientos
de PostgreSQL/Celery del diseño futuro no operan este MVP.

## Arranque y salud

En Windows ejecutar `iniciar.cmd`; `-Check` verifica instalación/configuración y
`-Install` instala el runtime bloqueado. El proceso queda en primer plano y se
detiene con Ctrl+C. Abrir http://127.0.0.1:8420/.

```powershell
Invoke-RestMethod http://127.0.0.1:8420/health
```

La respuesta informa estado, versión, modo, conversión activa y backend de
memoria previsto. No representa una conversión de prueba ni asegura espacio
para el siguiente PDF. En modo remoto también requiere Basic Auth. Configuración
en [CONFIG_GUIDE.md](../CONFIG_GUIDE.md); usar HTTPS para el acceso remoto.

## Respuestas y recuperación

| Síntoma | Acción |
|---|---|
| El arranque rechaza configuración | Revisar ambas credenciales, modo/Host, números positivos finitos y concurrencia 1. Reiniciar tras cambiar variables. |
| 401 | Revisar credenciales completas del proceso. |
| 403 | Revisar acceso local, Host, origen y cabeceras del proxy. |
| 409 | Hay un trabajo admitido; esperar su terminación y reintentar. No hay cola. |
| 413 | Reducir el archivo a 25 MiB o menos; elegir páginas en la UI no reduce el PDF subido. |
| 400 / PDF protegido o inválido | Abrir una copia legible sin contraseña o elegir otro PDF. |
| Timeout / memoria | Elegir menos páginas o un documento más simple. El proceso limitado se termina antes de liberar admisión. |
| 503 de disco | Revisar espacio libre, presupuestos y permisos en `.generated/web_ui/`. Esperar barrido o detener el servidor para revisar trabajos vencidos. |
| No se activa límite de memoria | Revisar compatibilidad/permisos del sistema; la app rechaza convertir. No desactivar el control. |
| 410 al descargar | Volver a convertir; la fecha expiró y no se renueva al descargar. |
| Resultado requiere revisión | Comparar con el PDF; descargar warnings.json para todas las notas y procedencia. |

## Limpieza, logs y actualización

El TTL empieza al crear el trabajo: 24 horas por defecto. Hay un barrido al
arrancar y cada hora; los trabajos fallidos se eliminan y los activos se
protegen por bloqueo. Si Windows impide un borrado se registra `cleanup_failed`
con UUID y tipo de error, para diagnóstico/reintento. Revisar antivirus,
permisos y archivos abiertos del trabajo señalado. No borrar trabajos activos.
El presupuesto por trabajo incluye original y resultados; la comprobación
total reserva un trabajo completo antes de admitirlo.

La caducidad de descarga es inmediata; la eliminación física ocurre en el
barrido. El TTL no afecta corpus, evidencia del piloto, descargas personales,
backups ni logs. Revisar su retención por separado. No enviar PDFs privados
ni contenido de conversiones a logs o incidencias.

Para actualizar, detener con Ctrl+C, conservar solo evidencias autorizadas,
aplicar el código y ejecutar `iniciar.cmd -Install -Check`. Reiniciar desde
el mismo directorio. Si se necesita volver atrás, usar una versión conocida
con sus propios locks y entorno; no reutilizar un entorno incompatible.

Antes de una entrega ejecutar `python -m scripts.check_release --audit` desde
el entorno de desarrollo y revisar `.generated/release-check/report.json`.
El workflow manual queda preparado; este cambio no activa Actions ni actualiza
el servicio remoto. La aceptación del piloto de cinco documentos se conserva;
el Gate F0 general permanece abierto.
