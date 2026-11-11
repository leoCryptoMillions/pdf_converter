# Revisión de brechas y plan de remediación

Fecha: 2026-11-10 · Código revisado: `de9c513` · App auditada: 0.6.4.

**Remediación posterior implementada en 0.7.0:** ver [correcciones y evidencia](CORRECCIONES_MVP_0.7.0.md). Este documento conserva el diagnóstico y las mediciones anteriores a los cambios.

La conversión local tiene una base funcional y un piloto aceptado, pero conserva
fallos de aislamiento, admisión de archivos y comunicación de advertencias.
La prioridad es cerrar esos fallos y comprobar una instalación limpia antes de
ampliar usuarios, formatos o infraestructura.

## Alcance y evidencia

Se revisaron el servidor activo `apps.local_review_ui`, el subproceso, extracción,
exportadores, modelos IR, CLI, pruebas, dependencias, workflow y documentación.
La API de `apps/api` y Celery son esqueletos de una fase posterior; sus funciones
pendientes no se consideran regresiones del MVP local.

El piloto **ya está aceptado**: el CSV privado de
`.generated/mvp-pilot-20261028/final-v3/revision.csv` contiene cinco decisiones
`accepted`, coherentes con `docs/AVANCE.md`. Esta revisión preserva esa aceptación.
El Gate F0 general sigue pendiente y no queda aprobado por las pruebas actuales.

| Comprobación | Resultado observado |
|---|---|
| Suite completa, Python 3.13.1 / Windows | **118 aprobadas, 1 omitida**, 37.39 s. La omitida requiere `RLIMIT_AS` de POSIX. |
| Selección diaria, solo recolección | 66/119 casos seleccionados; 53 excluidos. El conteo histórico 44/88 quedó desactualizado. |
| Corpus local, sin publicar contenido | 37 registros autorizados y 37 PDFs presentes; 6 marcados con referencia; 5 JSON de referencia privados y 1 referencia sintética versionada. Una referencia puede cubrir solo una región/página. |
| Piloto privado | Cinco filas, cinco aceptaciones. No se volvió a ejecutar Office ni se reevaluó visualmente el piloto. |
| Reproducciones dirigidas | Se confirmaron acceso con autenticación incompleta, error de autenticación Unicode, bloqueo IPC, carga limitada después del parseo, archivo retenido al rechazar por ocupación, liberación prematura del semáforo al cancelar y advertencia de celda omitida. |
| Herramientas de empaquetado | El intento de construir un wheel sin descargas se detuvo porque el entorno no tiene `setuptools`/`wheel`. No acredita un fallo de build del producto ni permite afirmar que el wheel funciona. |

Comando de regresión ejecutado:

```powershell
python -m pytest -q -m "mvp or not mvp" --show-capture=no
```

La primera ejecución quedó impedida por los permisos sobre el directorio temporal
de pytest; la ejecución con permisos autorizados produjo el resultado anterior.
Las reproducciones usaron datos ficticios y directorios temporales. El script y
los resultados quedan locales, ignorados por Git, en
`.generated/auditoria-20261110/probes.py` y `probe-results.json`.

No se inspeccionó la configuración ni el estado del servicio remoto, ni se
ejecutaron un pentest, una auditoría de vulnerabilidades o una medición nueva de
cobertura. No se evaluó la distribución legal de binarios. Las conclusiones de
exposición remota son condicionales a su configuración, no una afirmación sobre
las credenciales efectivas del despliegue.

## Hallazgos priorizados

P0: resolver antes de permitir acceso remoto bajo esa condición. P1: siguiente
entrega del MVP. P2: cierre operativo y mantenibilidad. Los roles son sugeridos;
no representan asignaciones a personas.

| ID | Prioridad | Brecha y efecto | Evidencia de código | Remediación propuesta |
|---|---|---|---|---|
| H01 | **P0 si se expone en red** | La autenticación permite todo si falta cualquiera de las dos credenciales. Un error de configuración deja conversión y descargas sin protección. | `apps/local_review_ui.py:78`, `:90`, `:438`; HTTP 200 con usuario configurado y contraseña ausente. | Modo local/remoto explícito; impedir arranque remoto sin ambas credenciales válidas. Autenticación incorrecta siempre termina en 401. |
| H02 | **P1** | El padre espera la salida del hijo antes de leer el pipe. Un resumen grande puede bloquear su envío y producir un falso timeout aunque la conversión haya terminado. | `apps/conversion_isolation.py:100`, `:142`, `:151`; reproducción con envío pequeño y grande. | Recibir mientras el hijo vive, con una fecha límite global; limitar el mensaje IPC y guardar detalles extensos en un artefacto. Cerrar conexiones y proceso en `finally`. |
| H03 | **P1** | El límite de 25 MB se comprueba después del parseo multipart. Además, el rechazo por ocupación sucede después de escribir `source.pdf`. No hay presupuesto total de disco. | `apps/local_review_ui.py:306`, `:312`, `:315`, `:321`; reproducción de carga y rechazo ocupado. | Limitar bytes reales antes del parseo, archivos/campos multipart y admisión simultánea. Comprobar capacidad antes de persistir; reservar espacio y limpiar rechazos. |
| H04 | **P1** | Al cancelar el handler se libera el semáforo, pero el trabajo enviado al executor continúa. Otro handler puede iniciar una conversión mientras la anterior sigue activa. | `apps/local_review_ui.py:324`, `:326`; cancelación controlada del handler con executor aún activo. | Dar al supervisor la propiedad del permiso hasta terminar/matar el hijo. Definir cancelación y apagado; verificar también múltiples procesos de servidor. |
| H05 | **P1** | En Windows, el límite de memoria configurado es una operación vacía. El timeout no impide que un PDF consuma la memoria del equipo antes de vencer. | `apps/conversion_isolation.py:51`; omisión explícita en la prueba POSIX; ADR 0006 lo reconoce. | Implementar límite efectivo con Windows Job Objects o un contenedor soportado y verificado; comprobar que el límite se aplica antes de parsear. |
| H06 | **P1** | La UI recibe advertencias de documento/página, pero omite las de tablas/celdas. Algunas advertencias del exportador XLSX solo aparecen en `_Warnings`. El revisor no ve todas las dudas en la pantalla de resultados. | `apps/conversion_isolation.py:99`; `packages/exporters/xlsx.py:658`, `:704`; PDF sintético con celda combinada. | Definir una colección común de incidencias con página, tabla, celda y formato; usarla en UI, IR y exportaciones, sin duplicados. |
| H07 | **P2** | La limpieza espera una hora antes del primer barrido, usa modificación de archivos y no verifica expiración en descarga. Los rechazos/fallos dejan originales o salidas parciales. El borrado puede fallar silenciosamente. | `apps/conversion_isolation.py:84`, `:157`, `:173`, `:185`; `apps/local_review_ui.py:422`. | Metadatos de creación/expiración y estado; barrido inicial, rechazo de descargas caducadas, publicación atómica y limpieza por estado. Registrar fallos de borrado sin contenido. |
| H08 | **P2** | Las respuestas sensibles carecen de `Cache-Control: no-store`. El texto «Se queda en tu equipo» se muestra también si se sirve remotamente. La retención del servidor no controla las copias del navegador. | `apps/local_review_ui.py:104`, `:147`, `:431`; descarga sin cabecera de caché. | Aplicar política de caché a resultados/descargas y describir almacenamiento según modo local/remoto. Mostrar fecha real de expiración. |
| H09 | **P1 de entrega** | No existe evidencia de instalación limpia; conviven requisitos del MVP con manifiestos antiguos y versiones distintas. El próximo usuario puede seguir una guía que instala otro stack. | `requirements-mvp.txt`, `requirements.txt`, `pyproject.toml:52`, `DEVELOPER_SETUP.md:37`; pendiente reconocido en `docs/AVANCE.md`. | Una ruta de instalación soportada para el MVP; separar claramente el stack futuro, resolver dependencias transitivas y probar un entorno virtual vacío. |
| H10 | **P2** | Las comprobaciones de entrega no son reproducibles como un solo recorrido. El workflow es manual, instala el stack histórico y tolera fallos de mypy/Black. Los E2E JS requieren Playwright externo sin manifiesto Node versionado. | `.github/workflows/tests.yml:6`, `:64`, `:74`, `:78`; `tests/e2e/local_review_ui.cjs:5`; `requirements-mvp-dev.txt`. | Comando local de cierre con dependencias declaradas, regresión completa, navegador y cobertura medida. Conservar la decisión de CI manual; proponer su automatización por separado. |
| H11 | **P2** | Los documentos discrepan sobre aceptación, entorno y avance. README/alcance dejan pendiente el piloto ya aceptado; el tablero conserva snapshot de octubre y bloqueos históricos. | `README.md:6`, `docs/ALCANCE.md:13`, `docs/AVANCE.md:5`, `prototipos/preparacion-brechas/index.html:378`. | Conciliar por alcance y fecha; distinguir piloto aceptado de Gate F0 abierto. Actualizar conteos desde evidencia y registrar fuentes pendientes de conciliación. |
| H12 | **P2** | Faltan diagnóstico operativo por conversión y validación central de configuración. Variables no positivas/no finitas pueden inutilizar límites; los errores de arranque, disco o creación del proceso no tienen un tratamiento común. | `apps/conversion_isolation.py:28`, `:60`, `:141`, `:179`; `apps/local_review_ui.py:100`, `:315`. | Validar valores/rangos al arrancar; registrar ID, duración, resultado y tipo de fallo sin texto ni nombres del PDF. Supervisar limpieza y documentar recuperación. |

### Reproducciones y límites de las conclusiones

**H01.** Con `AUTH_USERNAME` presente y `AUTH_PASSWORD=None`, `GET /` devuelve
200 sin cabecera Authorization. Con ambas configuradas, un usuario Unicode en
Basic Auth devuelve 500: `compare_digest` con `str` no ASCII lanza una excepción
fuera del bloque que captura el error de decodificación. Convertir a bytes o
rechazar de manera controlada, sin un 500. El uso local sin credenciales puede
conservarse si solo se permite explícitamente en loopback.

**H02.** El hijo sintético pequeño terminó correctamente en 0.43 s; el hijo que
solo envía 1 000 advertencias terminó como `timeout` a los 3.03 s con un límite
de prueba de 3 s. El hijo no hace extracción: se aísla así el problema del
transporte. No se propone aumentar el timeout de producción como solución.
La documentación de [multiprocessing en Python 3.13](https://docs.python.org/3.13/library/multiprocessing.html#exchanging-objects-between-processes)
muestra la recepción del pipe antes de `join`; la reproducción confirma el
defecto de este orden en el proyecto.

**H03.** Con un límite de prueba reducido a 1 024 bytes, antes de que el handler
rechazara la carga ya existían **2 097 152 bytes** recibidos en `UploadFile`,
volcados al disco temporal. El código instalado de `MultiPartParser` aplica
`max_part_size` a campos ordinarios y escribe los archivos en un spool; ese
valor no reemplaza un límite de bytes para el archivo. El comportamiento también
puede contrastarse con el [código oficial de Starlette](https://github.com/Kludex/starlette/blob/main/starlette/formparsers.py).
Comprobar solo `Content-Length` o mover el semáforo dentro del mismo handler no
cierra la recepción previa, ni protege solicitudes sin esa cabecera. El rechazo
por ocupación dejó además un `source.pdf` nuevo. La solución debe abarcar el
flujo ASGI/proxy y el almacenamiento del trabajo.

**H04.** Después de cancelar directamente la tarea del handler, el executor
seguía trabajando y el semáforo estaba disponible. Esta prueba demuestra el
fallo ante cancelación; no prueba que todo cierre de pestaña cancele siempre el
handler, pues eso depende del servidor y del tipo de desconexión. Un semáforo
por proceso tampoco constituye un límite global si se añaden workers/réplicas.

**H06.** Un PDF generado con una celda combinada produjo
`MISSING_OR_MERGED_CELL` en la celda del IR. La conversión terminó correctamente,
pero el resumen para la UI solo incluyó `UNVALIDATED_EXTRACTION`. El IR conserva
la incidencia; el defecto es su propagación y visibilidad. Agregar incidencias
al resumen sin resolver H02 puede agravar el volumen de IPC.

**H07/H08.** Una descarga sintética de 48 horas respondió 200 al arrancar la app
de pruebas, sin `Cache-Control`. El barrido todavía no había ocurrido. El TTL
actual se basa en modificación, aunque README habla de «inactividad»: descargar
no renueva esa fecha. No se comprobó que un navegador concreto haya almacenado
el archivo; sí se confirmó la ausencia de la política de caché.

**H09.** El empaquetado merece una comprobación separada: `pyproject.toml:116`
enumera solo `apps` y `packages`, y los datos de paquete se declaran para
`packages`, no para los recursos web de `apps`. Hay riesgo estático de omitir
subpaquetes/assets en un wheel. No se construyó ni instaló un wheel con éxito,
por lo que no se presenta esa consecuencia como reproducida. Si la distribución
elegida es un ZIP del proyecto, puede posponerse el wheel y documentarlo.

## Plan de ejecución

Estimación orientativa: **10–16 días de ingeniería**, más la comprobación humana
del paquete de entrega. Depende de la solución de memoria elegida en Windows.
Cada paso debe entregar evidencia revisable; las estimaciones no son compromisos.

| Orden | Paquete / responsable sugerido | Trabajo concreto | Dependencias | Esfuerzo orientativo |
|---|---|---|---|---|
| 1 | Acceso seguro / backend | H01: modo explícito, comprobación de arranque y manejo de Basic Auth. Incluir validación de configuración de H12. | Ninguna. Es requisito previo al uso remoto con configuración incompleta. | 0.5–1 día |
| 2 | Supervisor de conversión / backend | H02 y H04: recibir IPC durante ejecución, deadline común, cierre de recursos, propiedad del permiso y cancelación/apagado. | Paquete 1 para revisión conjunta del arranque. | 2–3 días |
| 3 | Admisión y almacenamiento / backend | H03 y H07: bytes antes de multipart, límites por solicitud, capacidad en disco, estado/expiración y publicación/limpieza de artefactos. | Paquete 2 para conocer cuándo un trabajo deja de estar activo. | 2–3 días |
| 4 | Memoria de Windows / runtime | H05: aplicar y verificar un límite real antes del parseo; informar capacidades efectivas. | Supervisor del paquete 2. | 1.5–3 días |
| 5 | Integridad de revisión / conversión | H06: incidencias comunes para todas las capas; H08: caché, ubicación de datos y expiración visibles. | H02 antes de ampliar mensajes de advertencia; metadatos del paquete 3. | 1–2 días |
| 6 | Entrega reproducible / desarrollo y QA | H09 y H10: instalación vacía, versiones coherentes, lanzador Windows con diagnóstico, recorrido de cierre y dependencias del navegador. Elegir ZIP/wheel según entrega real. | Paquetes 1–5 estabilizados. | 2–3 días |
| 7 | Cierre documental y operativo / mantenimiento | H11 y H12: conciliar fuentes, registrar diagnóstico sin contenido, recuperación, limitaciones y evidencia de release. | Evidencia de paquetes anteriores. | 1 día |

### Criterios verificables por paquete

1. **Acceso/configuración:** modo remoto rechaza credenciales ausentes o parciales
   al arrancar; configuración numérica inválida falla con mensaje claro. Casos
   Basic Auth válido, inválido, malformado y Unicode; rutas de resultados y
   descarga quedan protegidas. El modo local conserva el arranque en loopback.
2. **Supervisor:** resumen grande y advertencias numerosas terminan sin timeout
   falso; crash/EOF y timeout reales producen un resultado controlado; no quedan
   conexiones/hijos abiertos. Ante cancelación, el permiso solo vuelve a estar
   disponible cuando terminó la conversión anterior. Si se soporta más de un
   proceso, probar la exclusión entre procesos; de otro modo impedir esa
   configuración y documentar un único worker/réplica.
3. **Admisión/estado:** aceptar el máximo permitido y rechazar máximo + 1 con
   413, también sin `Content-Length`, sin recibir el resto en disco. Limitar
   campos y archivos extra. Un rechazo por ocupación no deja carpetas nuevas;
   usar respuesta 409/429 con mensaje comprensible. Disco lleno, error a mitad
   de exportación y reinicio no publican archivos incompletos. Descargas vencidas
   no se sirven y el barrido inicial funciona, con fallos de borrado observables.
4. **Memoria:** una carga sintética controlada que intenta superar el presupuesto
   es contenida en Windows; el servidor responde después y la siguiente
   conversión funciona. Probar también el mecanismo POSIX en Linux antes de
   afirmar soporte allí. No agotar deliberadamente la memoria real del equipo.
5. **Revisión/privacidad:** celda combinada, multilineal, colisión visual e imagen
   omitida aparecen en los destinos que correspondan, con procedencia y sin
   duplicados. Resultados y descargas emiten `no-store`; el texto de ubicación de
   datos coincide con el modo. Mantener fórmulas recibidas como texto e
   identificadores con ceros iniciales.
6. **Instalación/entrega:** desde un entorno vacío de Windows se instala solo el
   perfil soportado, se arranca, convierte y descargan/reabren DOCX/XLSX/TXT.
   El lanzador comprueba prerrequisitos y comunica errores. Si se entrega wheel,
   instalarlo fuera del árbol fuente y verificar imports y todos los assets.
   Ejecutar suite completa y E2E declarado. Medir cobertura con su plugin
   instalado y conservar el umbral del 70%; documentar el denominador del MVP y
   la plataforma diferida, sin excluir módulos para ocultar fallos. Generar
   inventario/SBOM y ejecutar análisis de vulnerabilidades del perfil real,
   revisando los resultados antes de distribuir.
7. **Operación/documentación:** un fallo se rastrea por ID y categoría sin nombres
   ni texto documental. Timeout, disco, arranque y limpieza tienen una acción de
   recuperación documentada. README, alcance, avance y seguimiento coinciden
   sobre piloto aceptado y Gate F0 pendiente. La revisión documental no convierte
   automáticamente un área en aceptada ni reactiva GitHub Actions.

Tras cada paquete: ejecutar la selección crítica y todas las pruebas del módulo
afectado. La regresión completa y el recorrido de navegador se reservan para el
cierre, o para cambios que afecten todo el flujo. Las regresiones nuevas deben
reproducir el riesgo corregido, incluyendo solicitudes HTTP/subprocesos reales
donde corresponda.

## Trabajo posterior al MVP

| Frente | Brecha real pendiente | Condición para retomarlo |
|---|---|---|
| Gate F0 general | Corpus 37/60, referencias parciales, clases difíciles poco representadas, revisión de binarios/avisos y costo por documento sin cerrar. El piloto de nueve páginas no prueba el límite de 100 ni rendimiento general. | Antes de prometer soporte general, ampliar clases de documentos o aprobar el Gate F0. No reabrir la aceptación de los cinco casos ya aprobados. |
| Plataforma F1+ | Rutas de conversión de `apps/api` sin implementar; tareas de Celery con `pass`; cuentas, persistencia, permisos, outbox y almacenamiento sin flujo funcional. | Decisión explícita de construir la plataforma después del MVP. Diseñar el flujo vertical de carga a descarga con permisos y recuperación. |
| Infraestructura de desarrollo | Compose publica puertos y credenciales de ejemplo; el perfil histórico no acredita operación productiva. | Antes de reutilizarlo en un entorno compartido: perfil privado, secretos por entorno, comprobaciones reales de servicios y pruebas de recuperación. |
| OCR y formatos adicionales | Dependencias y validación separadas del piloto digital. | Mantener como trabajo posterior; no usarlos como requisito para cerrar las correcciones actuales. |

El tablero conserva 11 áreas, con `verification_coverage` **18% (2/11)** y
`decision_coverage` **27% (3/11)** calculados sobre sus datos actuales. Son
indicadores del tablero histórico, no cobertura de pruebas ni porcentaje de
remediación. Esta auditoría se añade como fuente y seguimiento; queda pendiente
su conciliación integral con las fichas del tablero. Ningún hallazgo H01–H12 se
declara corregido por la creación de este documento.
