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
P03-P05  Revisar viabilidad XLSX/DOCX → Gate F0 (Go/No-Go)
```

## 1. Preparar el corpus (P01)

Los PDFs reales **nunca se commitean** (pueden contener datos sensibles o no
tener licencia de redistribución). Esta carpeta solo versiona la
herramienta y los metadatos.

1. Coloca los archivos PDF autorizados en `benchmarks/corpus/files/`
   (ruta ignorada por git).
2. Registra cada archivo en `benchmarks/corpus_manifest.csv` — una fila por
   PDF, ver columnas abajo.
3. Crea el ground truth de cada PDF en
   `benchmarks/ground_truth/<file_id>.json` (ver plantilla en esa carpeta).

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

## 4. Registrar resultados

Después de correr los benchmarks, actualiza:
- `docs/AVANCE.md` — sección "Métricas Medidas" y "Bloqueadores Actuales".
- Si hay una decisión de motor, agrega un ADR en `docs/adr/`.
