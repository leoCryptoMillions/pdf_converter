# Prototipo local de viabilidad

Estado al 2026-10-08: extracción digital con pdfplumber, modelo intermedio
con procedencia, exportación XLSX/DOCX/TXT y validación de una muestra.
El prototipo funciona desde CLI. El flujo web con usuarios, trabajos,
storage y cola corresponde a F1 y permanece pendiente del Gate F0.

## Uso

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

DOCX contiene líneas de texto y tablas editables en orden geométrico
aproximado. No reconstruye imágenes, firmas, columnas ni estilos originales;
las advertencias se agregan en una página final. TXT conserva la extracción
digital sin formato. Escaneos sin texto producen advertencia `OCR_REQUIRED`;
el CLI no ejecuta OCR ni debe confundirse con el benchmark OCR.

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
