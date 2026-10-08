# F0 - Benchmarking y Corpus de Viabilidad

Esta carpeta contiene las herramientas para ejecutar la **Fase F0** del plan
([PLAN_APP_CONVERSION_PDF_v1.0.md](../PLAN_APP_CONVERSION_PDF_v1.0.md)):
decidir, con evidencia medible, si el stack de extracción elegido
(pdfplumber / Camelot / Docling / Tesseract) es viable para el MVP.

Estado y bloqueadores actuales: ver [docs/AVANCE.md](../docs/AVANCE.md).

## Flujo de trabajo (P01 → P02)

```
P01  Preparar corpus autorizado (60+ PDFs) + ground truth
          │
          ▼
P02  Ejecutar benchmarks (make benchmark)
          │
          ▼
     Reporte comparativo (benchmarks/results/)
          │
          ▼
F0   Prototipos XLSX/DOCX + revisión de calidad/licencias/costo → Gate F0
```

## 1. Preparar el corpus (P01)

Los PDFs reales **nunca se commitean** (pueden contener datos sensibles o no
tener licencia de redistribución). Esta carpeta solo versiona la
herramienta y los metadatos.

1. Coloca los archivos PDF autorizados en `benchmarks/corpus/files/`
   (ruta ignorada por git).
2. Registra cada archivo en `benchmarks/corpus_manifest.csv` — una fila por
   PDF, ver columnas abajo.
3. Crea las referencias de PDFs reales en
   `benchmarks/ground_truth/local/<file_id>.json` (excluido de Git).
   Solo las referencias sintéticas redistribuibles se guardan directamente
   en `benchmarks/ground_truth/`. Ver la plantilla de esa carpeta.

### Categorías requeridas (mínimo 10 cada una)

| category               | Descripción                                   |
|-------------------------|------------------------------------------------|
| `digital_simple_table`   | Tablas digitales de una sola página, sin fusión de celdas |
| `digital_complex_table`  | Tablas multipágina, celdas combinadas, anidadas |
| `digital_text_columns`   | Texto digital en columnas (sin tablas)         |
| `scanned_clean`          | Escaneado de buena calidad, texto legible      |
| `scanned_difficult`      | Escaneado de baja calidad, inclinado, ruido    |
| `mixed`                  | Páginas digitales y escaneadas combinadas       |
| `adversarial_encrypted`  | PDF cifrado/protegido con contraseña            |
| `adversarial_corrupt`    | PDF corrupto o truncado                        |
| `adversarial_large`      | PDF grande (cerca del límite de 25 MB / 100 pág.)|

### Columnas de `corpus_manifest.csv`

| Columna        | Descripción                                               |
|----------------|------------------------------------------------------------|
| `file_id`      | Identificador único (usado como nombre de archivo y ground truth) |
| `filename`     | Nombre original del archivo en `corpus/files/`             |
| `category`     | Una de las categorías de la tabla anterior                 |
| `page_count`   | Número de páginas                                          |
| `source`       | De dónde proviene (interno, dominio público, sintético, etc.) |
| `authorized`   | `yes`/`no` — confirmación de que se puede usar para pruebas |
| `has_ground_truth` | `yes`/`no`                                              |
| `notes`        | Observaciones (idioma, orientación, particularidades)       |

## 2. Ejecutar los benchmarks (P02)

Para la muestra anotada y los prototipos nuevos:

```bash
python -m benchmarks.prepare_review
python -m benchmarks.validate_prototype
```

El primer comando genera `benchmarks/review/corpus_split.csv` y tareas
de anotación o ampliación en `annotation_tasks.json`, sin inventar referencias.
Los PDFs idénticos por SHA256 reciben el mismo conjunto. La separación es
provisional: aún hay que agrupar por origen/plantilla y revisar el balance.
El segundo valida XLSX, dos rutas DOCX y OCR por página o región, con salidas en
`.generated/f0/` y métricas en `.generated/f0/report.json`.
No decide el Gate F0. Las referencias regionales no miden páginas completas.
Las referencias `selected_pages_tables` y `selected_pages_text` miden solo
las páginas anotadas, no el documento completo. El benchmark OCR general
no puntúa esas referencias parciales; usa `validate_prototype` para ello.

```bash
# Benchmark completo (tablas + OCR), guarda resultados en benchmarks/results/
make benchmark

# Solo extracción de tablas (pdfplumber vs Camelot vs Docling)
make benchmark-tables

# Solo OCR (Tesseract, con y sin preprocesamiento OCRmyPDF)
make benchmark-ocr
```

Cada script:
1. Lee `corpus_manifest.csv`.
2. Salta automáticamente las filas con `authorized != yes` o sin PDF presente
   en `corpus/files/` (y lo reporta como advertencia, nunca en silencio).
3. Corre cada motor sobre cada PDF aplicable y mide tiempo + métricas contra
   el ground truth (cuando existe).
4. Escribe `benchmarks/results/tables_benchmark.json` y/o
   `benchmarks/results/ocr_benchmark.json`, más un resumen en consola.

## 3. Criterios del Gate F0

Tomados de [docs/ALCANCE.md](../docs/ALCANCE.md):

| Métrica                                   | Umbral   |
|--------------------------------------------|----------|
| F1 detección de tablas (digital simple)     | >= 0.95  |
| F1 estructura de celdas                     | >= 0.95  |
| Exactitud de contenido digital               | >= 99%   |
| CER de OCR (escaneado limpio)                | <= 2%    |

Si algún motor no alcanza el umbral en su categoría, se documenta la brecha
y se decide: (a) cambiar de motor, (b) acotar el alcance de esa categoría,
o (c) marcarla como "requiere revisión manual" desde el MVP.

**Limitación de métricas:** `table_f1` mide coincidencia exacta de filas por
tabla, contando duplicados. No mide geometría, spans ni orden de filas;
por tanto no sustituye los dos F1 de detección y estructura del gate.
CER usa distancia Levenshtein exacta. El informe de prototipos normaliza
solo espacios del texto y reporta el alcance de cada referencia.
P03/P04/P05 del plan son IR/API, aislamiento y permisos/storage; no son
identificadores para las pruebas de viabilidad de Excel y Word.

## 4. Registrar resultados

### Experimentos locales adicionales

```powershell
python -m benchmarks.validate_continuity
python -m benchmarks.ocr_experiments
python -m benchmarks.resource_benchmark
python -m benchmarks.dependency_inventory
```

Continuidad valida celdas anotadas de la frontera y conservación XLSX; no
une transacciones. OCR compara siete configuraciones en dos páginas de
desarrollo, sin promover el mejor resultado a configuración de producción.
Recursos usa tres procesos nuevos por ruta y requiere psutil de
`requirements-benchmark.txt`, además del entorno PDFium/Tesseract existente.
Inventario copia avisos y revisa requisitos activos de paquetes instalados;
no certifica cumplimiento ni examina todos los binarios nativos.
Resultados y límites: [prototipo F0](../docs/PROTOTIPO_F0.md).

Después de correr los benchmarks, actualiza:
- `docs/AVANCE.md` — sección "Métricas Medidas" y "Bloqueadores Actuales".
- Si hay una decisión de motor, agrega un ADR en `docs/adr/`.
