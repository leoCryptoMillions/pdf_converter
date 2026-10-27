# Prototipo local de viabilidad

Estado al 2026-10-08: extracción digital con pdfplumber, modelo intermedio
con procedencia, exportación XLSX/DOCX/TXT y validación de una muestra.
El prototipo funciona desde CLI. El flujo web con usuarios, trabajos,
storage y cola corresponde a F1 y permanece pendiente del Gate F0.

## Uso

La validación Word más reciente está en
[VALIDACION_WORD_F0.md](VALIDACION_WORD_F0.md): tres diseños completos,
siete páginas, comparación visual y edición/reapertura en Microsoft Word.
`benchmarks.validate_word` prepara y compara la evidencia;
`benchmarks/render_word.ps1` realiza el render local. El informe describe
las correcciones de tablas y la aceptación humana todavía pendiente.

Instalar el subconjunto probado, preferentemente en un entorno virtual:

```powershell
python -m pip install -r requirements-prototype.txt
python -m apps.convert benchmarks/corpus/files/synthetic_base_invoice.pdf --output .generated/demo --formats xlsx docx txt
```

Para limitar las páginas, agregar `--pages 1 3`. La salida conserva los
números de página originales; `source_pages` cuenta las páginas del PDF y
`pages` cuenta las procesadas. `_Origin` identifica las páginas exportadas.

Se crean `document.ir.json`, `result.xlsx`, `result.docx`, `result.txt` y
`summary.json`. La carpeta debe ser nueva y nunca se sobrescribe.
Toda conversión termina con `needs_review`: extraer contenido no garantiza
que coincida con lo visible en el PDF. Los artefactos de `.generated/`
permanecen locales y no están sujetos todavía a borrado automático.

### Interfaz web local (no es el flujo web de F1)

`apps/local_review_ui.py` (añadido 2026-10-23) es un wrapper mínimo de un
solo usuario sobre este mismo CLI, para no tener que escribir flags a mano.
Es deliberadamente distinto del "flujo web con usuarios, trabajos, storage y
cola" de F1 mencionado arriba: sin cuentas, sin base de datos, sin cola, un
documento a la vez, pensado para correr en `127.0.0.1` en tu propia máquina.

```powershell
python -m apps.local_review_ui
# abre http://127.0.0.1:8420/
```

Sube un PDF, elige formato(s) y si quieres `--ocr`, y descarga el resultado.
La interfaz incluye carga por arrastre, selección de varios formatos, resumen
de opciones y un indicador mientras se convierte. Los errores conservan
formatos, páginas y OCR; el archivo debe seleccionarse de nuevo. La pantalla
de resultados muestra descargas, páginas y tablas detectadas, notas de revisión
y una vista de los primeros 6 000 caracteres del texto extraído. El formulario
y las descargas funcionan también sin JavaScript. Los recursos visuales están
en `apps/local_review_assets/`, sin dependencias web ni fuentes externas.

El botón de la cabecera alterna entre modo claro y oscuro en el formulario,
los resultados y los errores. Respeta el tema del sistema hasta que eliges
uno; guarda la elección en `localStorage` (`pdf-converter:theme`), la aplica
antes de cargar los estilos y sincroniza otras pestañas del mismo origen.
Si el navegador bloquea el almacenamiento, el botón funciona durante esa
página; al navegar se vuelve al tema del sistema. Sin JavaScript, los estilos
siguen el sistema y el botón se oculta.

Los artefactos quedan en `.generated/web_ui/<id>/`, sin borrado automático
(igual que el resto de `.generated/`). Pruebas reales (sin mocks, sube un
PDF y descarga el resultado) en `tests/unit/test_local_review_ui.py`.

#### Ayuda, FAQ y mascota PDF Converter

El menú **Ayuda** de la cabecera abre el [centro de ayuda local](http://127.0.0.1:8421/ayuda),
las preguntas frecuentes y la guía de uso. La página `/ayuda` incluye 13 FAQ
agrupadas por tema y una guía de cuatro pasos. La búsqueda revisa preguntas
y respuestas sin distinguir acentos ni mayúsculas, abre las coincidencias y
ofrece limpiar la consulta. Funciona también por GET sin JavaScript.

Las acciones de convertir, quitar archivo, cambiar tema, descargar archivos,
empezar otra conversión y buscar/limpiar tienen un `?` adyacente. También hay
explicaciones para archivo, formatos, páginas, OCR y revisión. Con JavaScript
se abren en un diálogo nativo sin ejecutar la acción ni perder el archivo;
Escape o Cerrar devuelven el foco al enlace que lo abrió. Sin JavaScript,
los `?` enlazan a su explicación en `/ayuda`. La propia ayuda y su cierre no
generan controles de ayuda recursivos.

`apps/local_review_assets/help.json` contiene los 20 temas compartidos entre
FAQ y explicaciones; `apps/local_review_help.py` los renderiza, y `help.js`
mejora el diálogo y la búsqueda. No se envían consultas a servicios externos.
La mascota aparece en el centro de ayuda y las explicaciones; su animación
respeta la preferencia de movimiento reducido.

**Recurso generado:** `apps/local_review_assets/pdf-converter-guide.png`,
PNG RGBA de 1254 × 1254, con transparencia real verificada. Se utilizó la
herramienta integrada de generación de imágenes, con
`conta01/public/imagenes/nexia-guia-ayuda.png` como referencia de edición.
El original de Nexia no se modificó. Prompt final utilizado:

```text
Use case: text-localization. Edit target: the attached transparent PNG of the Nexia 3D robot mascot. Create the PDF Converter version of exactly this same mascot. Preserve the robot's identity, cream ceramic shell, dark navy visor, warm gold eyes and smiling expression, blue arms and headphones, translucent dome, four fingers per hand, right-hand pointing pose, framing, and soft studio lighting. Change ONLY the chest lettering: remove 'Nexia' and put the exact text 'PDF Converter', preferably neatly centered on two lines ('PDF' then 'Converter') in warm gold lettering. No other letters or logos anywhere. Render the complete character with ample safe margin on a genuinely transparent RGBA background, no checkerboard, no solid background, no additional props, no caption outside the character. High quality, sharp enough for a website help center.
```

Verificación: 21 pruebas HTTP y el recorrido de navegador versionado. Se
comprueban FAQ, menú, ayuda sin pérdida del archivo, foco, mascota cargada,
tema claro/oscuro, móvil y alternativa sin JavaScript, además de convertir y
descargar archivos reales. Evidencia en `.generated/ui-check/help-*.png` y
`report.json`.

#### Prácticas revisadas en conta01 y adaptación local (2026-10-23)

Revisión dirigida de código y documentación en el repositorio vecino
`conta01`; no se ejecutó ni modificó ese proyecto. Se adaptaron patrones al
wrapper FastAPI/HTML existente, con implementación propia y sin incorporar
React, Next.js ni la infraestructura de Nexia.

| Práctica observada | Fuente revisada en conta01 | Aplicación en este proyecto |
|---|---|---|
| Colores semánticos, incluido texto sobre acento y colores de error por tema | `src/app/globals.css` | `style.css`: todas las superficies, avisos, controles y estados consumen variables; paletas clara y oscura. |
| Preferencia antes del primer render, con elección manual prioritaria | `src/app/layout.tsx`, `src/app/dashboard/ThemeToggle.tsx` | `theme.js` se carga antes del CSS; preferencia validada, alternativa del sistema y botón en la cabecera compartida. |
| Fallos de almacenamiento no bloquean la función principal | `ThemeToggle.tsx`, `src/lib/useFormDraft.ts` | Lecturas/escrituras protegidas; sin almacenamiento siguen funcionando el tema de la página y la conversión. |
| Revisión por superficies y verificación del DOM | `.claude/skills/revisar-cobertura/SKILL.md`, `.claude/skills/revisar-ui/SKILL.md` | Prueba de formulario, resultados, errores, foco, separación del botón, móvil y ambos temas. No aplican las comprobaciones específicas de JSX. |
| Cabeceras comunes y CSP restrictiva | `next.config.ts`, `src/lib/csp.ts` | Middleware del wrapper con `nosniff`, bloqueo de marcos, `no-referrer` y recursos/formularios del mismo origen. Scripts y estilos externos locales permiten evitar código inline y nonces. |
| Documentación que distingue implementación de pendientes | `README.md`, `docs/CONTINUIDAD.md`, `docs/mantenimiento-dashboard.md` | Guía de uso, avance y seguimiento del dashboard actualizados con alcance y evidencia; F1 conserva sus estados. |

Para etapas posteriores: la recuperación explícita de borradores de
`useFormDraft.ts` será útil si aparecen formularios largos; el diálogo nativo
y la restauración del foco de `src/components/Modal.tsx`, si se agrega una
vista de revisión modal. Las preferencias por cuenta, permisos, sesiones y
persistencia de Nexia corresponden al futuro flujo F1. El wrapper mantiene
el límite de un usuario local y no guarda PDFs en el almacenamiento del
navegador. Esta revisión dirigida no acredita la seguridad ni las pruebas
completas de ninguno de los dos proyectos.

#### Verificación de la interfaz

Pruebas HTTP (incluyen conversión y descargas reales):

```powershell
python -m pytest tests/unit/test_local_review_ui.py -o addopts='--strict-markers --tb=short -q'
```

Prueba opcional de navegador versionada en `tests/e2e/local_review_ui.cjs`.
Requiere Node.js y Playwright, únicamente para desarrollo:

```powershell
npm install --no-save --package-lock=false playwright
npx playwright install chromium
python -m uvicorn apps.local_review_ui:app --host 127.0.0.1 --port 8421
# En otra terminal, desde la raíz del proyecto:
node tests/e2e/local_review_ui.cjs
```

`PDF_UI_URL` permite cambiar la URL. Para reutilizar herramientas ya
instaladas, `PDF_UI_PLAYWRIGHT_MODULE` acepta la ruta del módulo Playwright
o Playwright Core y `PDF_UI_CHROMIUM_EXECUTABLE`, la ruta del navegador.
La muestra requerida es `benchmarks/corpus/files/synthetic_base_invoice.pdf`
(generada por `python -m benchmarks.generate_synthetic_adversarial`).
El recorrido cubre ambos temas, preferencia del sistema, recarga, pestañas,
almacenamiento bloqueado, teclado, contraste de pares de texto, anchos de
375–1440 px, conversión y descarga reales, errores y uso sin JavaScript.
Las capturas y mediciones quedan en `.generated/ui-check/`, ignorado por Git;
no sustituyen pruebas con lectores de pantalla ni dispositivos físicos.

XLSX crea una hoja por tabla, `_Original` con texto original por celda,
`_Origin` con hash/motor/página/rectángulo y `_Warnings` con incidencias.
Por defecto conserva todas las celdas como texto, incluidas fechas y códigos.
No interpreta contenido recibido como fórmulas. Si el texto no cabe en Excel
o tiene caracteres no representables, falla en vez de truncarlo.

Para convertir columnas explícitas de una tabla a números, crear un JSON:

```json
{"p1_t1": {"1": "integer", "2": "currency", "3": "currency"}}
```

Pasarlo con `--types ruta/al/archivo.json`. Columnas con índice desde cero;
la primera fila queda como texto. Sintaxis numérica `en_US`, sin inferencia
de moneda ni fechas. Identificadores, ceros iniciales, formatos ambiguos,
precisión superior a 15 dígitos y valores fuera del rango numérico se
conservan como texto. El original siempre se conserva en `_Original`.
Un importe que se parte entre líneas queda como texto para revisión.

Desde 2026-10-26, DOCX conserva texto editable con posiciones, tamaño de
página, tamaños de letra, colores, negritas y cursivas observados. Incorpora
imágenes y una capa gráfica sin el texto digital, como PNG dentro del Word.
Las tablas sencillas mantienen anchos y combinaciones detectadas; los
paneles complejos usan texto posicionado y generan una nota de revisión.
La fidelidad es aproximada: las fuentes, los visores y las ediciones pueden
cambiar la distribución. Los marcos permiten editar fragmentos, aunque no
ofrecen el mismo flujo continuo que un Word escrito desde cero.

Las notas se conservan en los resultados y en `document.ir.json`. Para
agregarlas como anexo al Word, usar `--docx-warnings` o marcar «Anexar notas
de revisión al Word». La opción está desactivada por defecto para no añadir
páginas al documento convertido. Ver alcance, límites de recursos y
decisión técnica en [ADR 0005](adr/0005-word-layout.md).

La extracción visual solo se activa desde CLI/web cuando se solicita DOCX.
`extract_digital` también admite `preserve_layout=False` para rutas que solo
necesitan texto/tablas. El IR 1.1.0 incorpora estilos y recursos autocontenidos
y sigue admitiendo documentos 1.0.0. El subconjunto probado fija
`pypdfium2==5.14.0`, ya instalado en este entorno.

TXT conserva la extracción digital sin formato. Escaneos sin texto producen advertencia `OCR_REQUIRED`
por defecto; el CLI no ejecuta OCR salvo que se pase `--ocr` explícitamente
(añadido 2026-10-23, no debe confundirse con el benchmark OCR independiente
de `benchmarks/ocr_benchmark.py`). Con `--ocr`, cada página sin texto
extraíble se procesa con Tesseract (`spa+eng`, PSM 3) vía
`packages/converters/ocr.py`, que aplica el enrutamiento `needs_review` de
DEC-04: la página 1 ("portada", heurística posicional, no visual) siempre
sale `needs_review` sin importar la confianza observada; el resto se enruta
por la confianza media de palabra que reporta el propio Tesseract (piso
0.85). Verificado con OCR real contra `benchmarks/corpus/files/
manualcargadorBYD.pdf` páginas 1 y 3 (ver `docs/AVANCE.md`).

## Evidencia de esta sesión

```powershell
python -m benchmarks.prepare_review
python -m benchmarks.validate_prototype
python -m pytest tests/unit/test_f0_prototype.py -o addopts='--strict-markers --tb=short -q'
```

Se ejecutaron con Python 3.13 en Windows. La dependencia de Word se instaló
en `.generated/deps`; esta sesión usó `PYTHONPATH` apuntando a esa carpeta.
La lectura de esos archivos fue bloqueada por el aislamiento y la ejecución
de pruebas/validación requirió aprobación. En un entorno virtual normal,
instalar `requirements-prototype.txt` evita depender de esa ruta temporal.

**41 pruebas aprobadas**, cubriendo PDF real generado desde datos esperados,
identificadores, duplicados, fórmulas, tipos numéricos, texto que excede Excel,
límites de entrada, cifrado, edición DOCX, CLI sin sobrescritura y referencias
con hash incorrecto, borradores y rutas inválidas, selección de páginas,
referencias parciales, presupuesto de píxeles OCR y una segunda ruta Word.
También verifican candidatos de continuidad, rechazo de geometrías distintas
y cálculo de escenarios de costo con parámetros explícitos.
Se reemplazaron los `addopts` generales porque no están instalados los
plugins de cobertura/asyncio/timeout de desarrollo. Hubo dos avisos de
configuración (`asyncio_mode`, `timeout`); no se midió cobertura global.

| Caso | Evidencia medida |
| --- | --- |
| Factura sintética | F1 de filas 1.000 con pdfplumber y Camelot; 20/20 celdas conservadas semánticamente, incluido el total convertido a número; originales conservados |
| Estado de cuenta real de una página | pdfplumber F1 de filas 1.000; Camelot 0.000; XLSX conserva 26/26 celdas y 3/3 valores críticos como texto |
| Tabla de página 19 de un estado de cuenta de 19 páginas | pdfplumber F1 de filas 1.000; Camelot 0.000; 88/88 celdas y 4/4 valores críticos conservados; no se valida unión de páginas |
| Documento digital de texto, una página | CER normalizado 0% tanto en pdfplumber → DOCX como en PDFium → DOCX textual; ambas rutas pasan edición/guardado/reapertura |
| Escaneo limpio, página 1 (portada) | Tesseract PSM 3: CER normalizado 3.723%, crudo 5.851%; PSM 6: normalizado 60.106% |
| Escaneo limpio, página 3 (texto continuo) | Tesseract PSM 3: CER normalizado 0.968%, crudo 1.936%; PSM 6: normalizado 1.245% |
| Región de un escaneo difícil | Tesseract, español+inglés, 300 DPI y PSM 6: CER normalizado 9.125%; solo región, no documento completo |

**Corrección de la medición anterior:** el CER Word de 4.675% provenía de una
referencia mal transcrita: faltaba el pie y varias palabras diferían del PDF.
La revisión a mayor resolución confirmó también la errata `SOCIEAD` en el
original. Se corrigió la referencia (revisión 2), conservando la errata y el
pie visible; no se modificó el extractor para borrar texto ni cambiar palabras.
El reporte y la referencia anteriores permanecen en `.generated/review_round2/`.
La segunda ruta Word usa PDFium y párrafos editables como comparación textual;
no reconstruye tablas, imágenes ni distribución y no cambia el motor de la CLI.

La tabla multipágina también se adjudicó con recortes de celdas a 6×: conserva
la errata `AMINISTRATIVA`, identificadores largos y la fila que continúa desde
la página anterior. No se corrigen errores presentes en el PDF. La portada OCR
supera el umbral candidato del 2% y el resultado varía con PSM; no promediarla
con texto continuo para ocultar la brecha ni declarar soporte general.

Las referencias reales están en `benchmarks/ground_truth/local/` y ligadas
al SHA256 del PDF. Hay seis documentos con referencias contando el
sintético: uno de los estados de cuenta cubre solo la página 19; un escaneo
cubre las páginas completas 1 y 3 y otro solo una región. La selección
produce doce tareas de creación o ampliación y una propuesta de división que
mantiene juntos los duplicados exactos; falta agrupar por plantilla/origen.
Las anotaciones parciales vuelven a aparecer como tareas de ampliación.

## Continuidad, OCR y recursos

Las tablas en páginas consecutivas pueden recibir un vínculo candidato si
coinciden columnas y ocupan los bordes de ambas páginas. El IR y `_Origin`
registran el vínculo y las advertencias. Las hojas y filas siguen separadas:
no se eliminan encabezados ni se fusionan transacciones automáticamente.
La validación de páginas 18–19 conservó las **16 celdas anotadas de frontera**
y las 232 celdas extraídas en XLSX. Estas últimas verifican el transporte,
no la exactitud contra referencia de toda la página 18. La reconstrucción
de una transacción partida sigue pendiente.

Se ejecutaron 14 experimentos OCR: siete configuraciones en portada y texto
continuo, variando PSM 3/11, contraste, umbral y 300/450 DPI. La mejor portada
continuó en **3.723%**; el umbral global empeoró la portada a más de 60%.
En texto continuo, el umbral con PSM 3 dio 0.899%, frente a 0.968% base.
Son páginas de desarrollo previamente inspeccionadas; no se eligió un motor
general ni se modificó la referencia para mejorar el resultado.

Medición local de tres procesos nuevos por ruta, en Windows/Python 3.13,
14 núcleos físicos, 20 lógicos y 15.73 GiB RAM:

| Ruta de una página | Tiempo medio | Máximo RSS observado |
| --- | --- | --- |
| Digital sintético → XLSX | 1.276 s | 64.18 MiB |
| OCR del cuerpo del manual, 300 DPI/PSM 3 | 4.194 s | 311.61 MiB |

Incluye arranque, imports y procesos hijos, muestreados cada 20 ms. RSS
agregado puede contar memoria compartida varias veces y omitir picos breves.
No mide concurrencia, cola, almacenamiento ni percentiles de producción.
A 1k/10k/100k páginas idénticas, las horas secuenciales estimadas son
0.354/3.545/35.448 para digital y 1.165/11.651/116.511 para OCR.
Los costos monetarios quedan null hasta proporcionar tarifa y costo fijo;
estas horas no representan una carga mixta ni procesamiento por lotes.

El inventario de dependencias incluye 33 componentes y 61 archivos de avisos,
sin conflictos declarados en el cierre instalado. La revisión de binarios,
modelos y distribución permanece pendiente: véase [LICENCIAS.md](LICENCIAS.md).

```powershell
python -m benchmarks.validate_continuity
python -m benchmarks.ocr_experiments
python -m benchmarks.resource_benchmark
python -m benchmarks.dependency_inventory
```

Reportes locales: `.generated/f0/continuity/report.json`,
`.generated/f0/ocr_experiments/report.json`, `.generated/f0/resources/report.json`
y `.generated/licenses/inventory.json`. Tesseract/modelos locales y paquetes
opcionales del benchmark deben estar instalados; `requirements-benchmark.txt`
añade el monitor psutil al entorno de comparación existente.

## Límites y continuación

Los límites de 25 MiB y 100 páginas se comprueban, pero el CLI no ofrece
aislamiento de seguridad, cuota de memoria ni timeout de producción.
No se verificó apertura en Microsoft Office/LibreOffice ni render DOCX.
Las versiones de `requirements-prototype.txt` son un subconjunto probado,
no un lockfile de producción ni una reconciliación del stack completo.

**Gate F0 pendiente.** La muestra es pequeña, faltan documentos anotados por
completo, estructura y unión multipágina, otros diseños Word, licencias,
tarifas y rendimiento bajo carga. Continuar con las tareas de ampliación,
reconstrucción de filas partidas y nuevos diseños OCR. Repetir métricas por
clase y decidir el alcance antes de implementar el flujo web F1.
