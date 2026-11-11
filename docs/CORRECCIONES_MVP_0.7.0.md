# Correcciones del MVP 0.7.0

Fecha: 2026-11-10 · Base auditada: `de9c513` / app 0.6.4.

Se implementaron los siete paquetes del
[plan H01–H12](REVISION_BRECHAS_Y_PLAN_2026-11-10.md) en el MVP de un usuario.
El cierre local Windows pasó con instalación vacía del wheel, pruebas HTTP/CLI,
Chromium y auditoría de dependencias. La aceptación de los cinco documentos
del piloto 0.6.4 se conserva; el Gate F0 general sigue pendiente.

## Cambios y trazabilidad

| Hallazgo | Corrección implementada | Evidencia / límite |
|---|---|---|
| H01 · Acceso | Modo local/remoto explícito; credenciales completas obligatorias en remoto; configuración parcial rechazada. Comparación constante sobre UTF-8 y 401 para autenticación incorrecta. Local valida Host y cliente; POST valida origen y Fetch Metadata. | `apps/runtime_config.py`, `request_guard.py`, `local_review_ui.py`; pruebas de configuración, Unicode, cliente remoto con Host loopback y origen malformado. No se inspeccionó ni actualizó el servicio remoto. |
| H02 · IPC | Recepción concurrente con la supervisión; fecha límite común, mensajes acotados y detalles en disco. Preview de hasta 6000 caracteres; notas limitadas por cantidad y bytes sin perder el informe completo. Conexiones/proceso cerrados en finally. | `apps/conversion_isolation.py`; hijo real con 1000 advertencias, EOF y advertencias Unicode extensas. |
| H03 · Admisión/disco | Límite del cuerpo durante recepción, del archivo antes del spool y de campos/archivos multipart. Admisión antes de recibir, respuesta 409 si está ocupado, presupuesto total/por trabajo y reserva de disco. | `apps/request_guard.py`, `job_store.py`; bytes reales sin Content-Length, archivo en límite/+1 byte, archivos extra, bloqueo entre procesos y falta de capacidad sin persistir el PDF. |
| H04 · Cancelación | El supervisor conserva la admisión hasta terminar el executor/hijo, incluso si se cancela el handler. Apagado señala cancelación y espera supervisores. Bloqueo de sistema adicional para procesos que comparten directorio. | Solicitud cancelada con executor activo y rechazo de la siguiente hasta terminar; prueba de timeout/terminación. Solo se soporta un proceso y una réplica. |
| H05 · Memoria | Windows Job Objects con límites de proceso/job y cierre de descendientes; POSIX RLIMIT_AS. El límite se activa antes de importar el parser y cualquier fallo impide convertir. | Límite real Windows de 96 MiB contiene una asignación de 200 MiB en un hijo. Se elimina la antigua omisión Windows. La ruta POSIX queda fuera del alcance requerido; Linux no requiere versión ni validación para esta entrega web en Windows. |
| H06 · Notas | Recolector común con documento/página/bloque/tabla/celda y deduplicación. El exportador XLSX incorpora sus propias incidencias al IR. La UI muestra procedencia y total; `warnings.json` conserva todas las notas. `_Warnings` y el anexo DOCX usan la colección disponible al exportar. | `packages/document_ir/warnings.py`, exportadores y prueba HTTP con celda combinada; IR 1.3.0 añade contexto opcional, manteniendo lectura de versiones anteriores. |
| H07 · Retención | Metadatos de creación, caducidad y estado; publicación completa desde staging; limpieza de fallos y huérfanos. Barrido inicial y periódico, bloqueo de trabajos activos, descarga vencida 410 y fallos de borrado observables. | `apps/job_store.py`, `conversion_isolation.py`; exportación parcial, trabajo activo, vencimiento y reinicio simulados. El borrado físico se realiza durante el barrido, no al alcanzar la hora exacta de caducidad. |
| H08 · Privacidad | `Cache-Control: no-store` y protecciones de respuesta para páginas/archivos/errores. Texto de ubicación según modo y fecha UTC real de caducidad. | Pruebas HTTP y Chromium. El TTL no elimina descargas personales, corpus, evidencia externa a `web_ui` ni backups. |
| H09 · Instalación | Manifiestos del MVP alineados, locks transitivos con hashes, paquete 0.7.0 con subpaquetes/assets y entrypoints, lanzador Windows y perfiles anteriores archivados como legacy. | Wheel instalado en un segundo venv vacío, imports desde site-packages, conversión CLI/HTTP y descargas de los cinco artefactos esperados. Lanzador `-Check` aprobado. |
| H10 · Entrega | Comando de cierre con resultados de cada paso, cobertura de ramas, build/instalación, inventario, SBOM/auditoría y Chromium declarados. Workflow manual exclusivo de Windows y Makefile limitados al MVP web en Windows. | `scripts/check_release.py`, `package-lock.json`, locks Python y workflow. Cierre local Windows aprobado; workflow limitado a windows-latest. No se activaron Actions ni se ejecutó el workflow remoto. |
| H11 · Coherencia | README, guía del repositorio, configuración, preparación, alcance, avance, seguridad, calidad, operación y ayuda describen el producto efectivo. La ayuda deja de afirmar que los archivos nunca se borran o que un servidor remoto es el equipo del usuario. El dashboard distingue base histórica, actualización parcial, piloto aceptado y Gate abierto; BLK-02 deja de afirmar un solo diseño validado. | Fuentes/seguimiento actualizados; navegador comprueba guardar/cancelar/exportar sin alterar estados oficiales. No se renueva la vigencia de fuentes históricas no revisadas. |
| H12 · Operación | Números positivos finitos, rango de puerto y concurrencia validados; logs con UUID, duración, resultado/backend y tipos de error sin contenido PDF. Salud indica versión/modo/actividad/backend previsto. | Pruebas de configuración y runbook con recuperación de acceso, timeout, memoria, disco, caducidad y limpieza. No se añaden servicios de telemetría. |

## Cierre ejecutado

Entorno: Python 3.13.1 / Windows, venv sin paquetes globales. Comando:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_release --audit
```

| Comprobación | Resultado |
|---|---|
| `pip check` | Sin incompatibilidades. |
| Regresión completa | **144 aprobadas, 1 omitida**, 65.52 s. La única omisión requiere OCR real opcional (Tesseract/Poppler); la prueba de memoria Windows sí se ejecuta. |
| Cobertura de ramas | **75.24%**, mínimo exigido 70%; incluye `apps` y `packages`, también los esqueletos futuros, sin excluirlos para elevar el porcentaje. |
| Selección diaria, recolección | 93/145 casos, 52 excluidos; aumenta por las regresiones críticas nuevas. El conteo 44/88 es histórico. |
| Inventario runtime MVP | 26 componentes, 26 archivos de avisos, cero incompatibilidades declaradas. |
| Auditoría del lock runtime | Sin vulnerabilidades conocidas en la consulta de esta fecha; SBOM CycloneDX generado. No es monitoreo continuo ni dictamen legal. |
| Wheel limpio | Build e instalación vacía correctos; todos los assets; CLI, HTTP, TXT/IR/notas y DOCX/XLSX editados, guardados y reabiertos con sus bibliotecas. |
| Chromium | Ambos temas, persistencia, contraste, tamaños móviles, conversión/descargas, foco/ayuda y alternativa sin JavaScript aprobados. |
| Dashboard | Detalles Word/Gate, cancelar/guardar, exportar borrador, estados y métricas conservados; sin errores de navegador. |
| Lanzador Windows | `scripts/start.ps1 -Check` aprobado, sin abrir servidor. |

Evidencia local, excluida de Git:

- `.generated/release-check/report.json`: `passed=true`, `browser_checked=true`, `vulnerability_audit=true`, todos los pasos con código 0.
- `.generated/release-check/final-check.log`, `coverage.json`, `sbom.json` y `dist/pdf_converter-0.7.0-py3-none-any.whl`.
- `.generated/release-check/installed-9643536c12b9/report.json`: importación desde el entorno vacío y cinco artefactos verificados.
- `.generated/ui-check/` y `.generated/docx-review/dashboard-report.json`: resultados y capturas del navegador.
- `.generated/licenses/inventory.json` y `notices/`: inventario técnico y avisos.

SHA256 del wheel verificado:
`df40bfb7ecb05c97f132d73a9e75fe3ac39a33e44c522392b5b3dcc1615859e7`.

La edición/reapertura automatizada de esta entrega usa python-docx y openpyxl;
no se repitió una evaluación visual nueva en Microsoft Office de los documentos
privados aceptados. Las pruebas de cierre usan datos ficticios.

## Pendientes conservados y siguiente revisión

La única entrega requerida, por instrucción directa del usuario, es la
versión web ejecutada en Windows y utilizada desde el navegador. Se retira
la validación Linux de los pendientes: Linux queda fuera de alcance.

1. **Si se actualiza el servicio remoto:** aplicar esta versión y verificar
   modo remoto, credenciales completas, HTTPS, una réplica/proceso, presupuesto
   y almacenamiento del entorno. Esta entrega no despliega ni certifica ese
   servicio.
2. **Para Gate F0 general:** ampliar/adjudicar muestra representativa, resolver
   distribución de binarios/avisos y modelo de costo. No reabrir las cinco
   aceptaciones del piloto por estas condiciones de alcance general.
3. **Datos locales:** revisar por separado acceso/retención del corpus y evidencia
   privada (RSK-05). No se eliminan archivos autorizados del piloto/corpus como
   consecuencia de corregir el TTL del servidor web.

Los indicadores del dashboard siguen en `verification_coverage` **18% (2/11)**
y `decision_coverage` **27% (3/11)**. Miden decisiones/verificación de sus once
áreas generales, no cobertura de pruebas ni porcentaje de correcciones del MVP.
