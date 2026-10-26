# Progreso del Proyecto - PDF Converter

Versión del Plan: 1.0.0  
Fecha de Actualización: 2026-10-09
Estado Actual: **F0 EN PROGRESO — prototipo CLI y muestra validada; gate pendiente**

## Estado Resumen

```yaml
proyecto: conversion-pdf
plan_version: 1.0.0
actualizado: 2026-10-09
fase_actual: F0 - Viabilidad
fase_detalle: P01/P02 - 37 PDFs, referencias parciales y prototipo F0 medido
estado: en_progreso
ultimo_commit: 712df98 (pusheado a origin/master)
completado:
  - Lectura de plan
  - Selección de framework
  - Revisión de arquitectura
  - Creación de estructura de proyecto
  - Definición de modelos IR
  - Configuración de dependencias
  - Herramientas de benchmark P02 (tables_benchmark.py, ocr_benchmark.py, runner.py)
  - Plantilla de manifest de corpus y ground truth (P01)
  - CLI digital PDF a XLSX, DOCX y TXT con IR y advertencias
  - Cinco referencias visuales reales locales con alcance y SHA256, más una sintética
  - Métricas CER exacto y F1 de filas con multiplicidad de duplicados
  - Validación de contenido XLSX y edición/guardado/reapertura DOCX
  - Doce tareas de creación/ampliación y split provisional por hash
  - Selección de páginas conservando procedencia y límites por documento
  - Referencia Word adjudicada y segunda ruta textual PDFium comparada
  - Vínculos candidatos entre tablas consecutivas con advertencias, sin unir filas
  - Validación de 16 celdas de frontera y transporte XLSX de ambos segmentos
  - Catorce experimentos OCR y seis mediciones de tiempo/memoria
  - Inventario instalado de 33 componentes y 61 archivos de avisos
pendiente_verificacion:
  - Bootstrap de proyecto
  - Funcionalidad mínima de API
decisiones:
  - ADR 0004, prototipo local conservador; no aprobar F0 con esta muestra
bloqueos:
  - Corpus de 60 PDFs autorizados aún no recolectado
pruebas_ejecutadas:
  - 41 pruebas de prototipo aprobadas; dos avisos de configuración; sin cobertura global
metricas_medidas:
  - F1 filas pdfplumber 1.000 en tres PDFs; uno de ellos cubre solo la página 19
  - XLSX real 26/26 celdas y 3/3 valores críticos conservados
  - XLSX de página 19 conserva 88/88 celdas y 4/4 valores críticos
  - CER Word normalizado 0 en dos rutas, una página real; referencia anterior corregida
  - OCR limpio PSM 3, CER normalizado 3.723% portada y 0.968% texto continuo
  - CER región OCR difícil normalizado 0.091255; no representa página completa
  - Portada sin mejora en siete variantes; texto continuo experimental 0.899%
  - Tiempo medio por página digital 1.276 s y OCR 4.194 s; tres procesos nuevos por ruta
riesgos_abiertos:
  - Corpus de 60 PDFs no disponible aún
  - Muestra insuficiente; faltan documentos completos y unión de tablas multipágina
  - Portada OCR limpio falla umbral candidato de 2%; no ocultar con promedio
  - Gate F0 sin criterios cuantitativos finales
siguiente_tarea: P01_ampliar_referencias_y_P02_reconstruccion_de_filas_y_carga
criterio_siguiente_tarea: documentos_completos_y_filas_partidas_con_referencia_independiente
```

## Tareas Completadas (P0 - Críticas)

### ✓ Lectura y Análisis del Plan
- **Fecha:** 2026-10-07
- **Archivos:** PLAN_APP_CONVERSION_PDF_v1.0.md
- **Entrega:** Plan completo leído y comprendido
- **Verificación:** Análisis de viabilidad completado

### ✓ Selección de Framework
- **Decisión:** FastAPI + Python (ADR 0001)
- **Justificación:** Acceso directo a ecosistema PDF/OCR, tipado, OpenAPI
- **Alternativas:** Django, NestJS, ASP.NET Core evaluadas
- **Estado:** Documentado en ADR

### ✓ Diseño de Arquitectura
- **Componentes:** API (FastAPI), Worker (Celery), Storage, DB (PostgreSQL)
- **Patrón:** Monolito modular con procesos separados
- **Decisiones:** ADR 0001-0003 creadas
- **Estado:** Revisado y documentado

### ✓ Creación de Estructura de Proyecto
- **Directorios:** apps/, packages/, tests/, docs/, infra/, benchmarks/
- **Archivos:** README.md, .env.example, docker-compose.yml, requirements.txt
- **Estado:** Completado, estructura lista para desarrollo

### ✓ Definición de Modelo Intermedio (DocumentIR)
- **Archivo:** packages/document_ir/models.py
- **Componentes:** 
  - DocumentIR (esquema principal)
  - Page (páginas individuales)
  - Table (tablas con celdas)
  - Image (imágenes extraídas)
  - TextBlock (bloques de texto)
  - ContentWarning (advertencias)
- **Validaciones:** Pydantic models con schemas
- **Estado:** Completo, versión 1.0.0

### ✓ Configuración de Dependencias
- **requirements.txt:** Versiones fijas (41 paquetes)
- **requirements-dev.txt:** Herramientas de desarrollo
- **Versionado:** Todas las dependencias incluyen número de versión exacto
- **Estado:** Documentado, compatible con SBOM

### ✓ ADRs Iniciales
- **ADR 0001:** Framework Selection (FastAPI)
- **ADR 0002:** Database and State Management (PostgreSQL + SQLAlchemy)
- **ADR 0003:** Background Processing (Celery + RabbitMQ)
- **Estado:** Documentadas con alternativas consideradas

## Tareas en Progreso

### Preparación de Corpus (P01) - CRÍTICA
**Estado:** EN PROGRESO — 37/60 PDFs recolectados y categorizados
**Duración Estimada:** 3-5 días
**Criterio de Salida:** 60+ PDFs categorizados con ground truth

**Entregado:**
- `benchmarks/README.md` — flujo completo P01 → P02 → Gate F0
- `benchmarks/corpus_manifest.csv` — 37 filas cargadas; seis con referencias, tres de alcance parcial
- `benchmarks/generate_synthetic_adversarial.py` — genera PDFs sintéticos cifrado/corrupto a partir de una factura ficticia
- `benchmarks/generate_synthetic_id_card.py` — genera un mockup de credencial INE 100% ficticio (foto placeholder dibujada), usado en vez de un INE real que fue descartado del corpus
- `benchmarks/ground_truth/README.md` + `synthetic_digital_001.json` (referencia sintética de tablas)
- `benchmarks/ground_truth/local/` — cinco referencias revisadas de documentos reales; no versionadas
- `benchmarks/corpus/files/` — 37 PDFs registrados (no versionados)

**Cobertura actual por categoría (meta: 10 c/u en las 6 principales):**

| Categoría | Actual | Meta | Brecha |
|---|---|---|---|
| `digital_simple_table` | 6 | 10 | faltan 4 |
| `digital_complex_table` | 7 | 10 | faltan 3 |
| `digital_text_columns` | **11** | 10 | ✅ completa |
| `scanned_clean` | 5 (2 escaneos reales + 1 mockup sintético de ID) | 10 | faltan 5 |
| `scanned_difficult` | 2 (foto celular inclinada + escaneo con deformación/sombra) | 10 | faltan 8 |
| `mixed` | 4 | 10 | faltan 6 |
| `adversarial_encrypted` | 1 (sintético) | — | cubierto para P02 inicial |
| `adversarial_corrupt` | 1 (sintético) | — | cubierto para P02 inicial |
| `adversarial_large` | 0 dedicado (candidatos: `mixed_001` 10.49 MB, `yucash_manual_001` 148 páginas — excede MAX_PAGES_PER_JOB=100) | — | sin PDF dedicado, pero hay 2 candidatos reales |

**Brecha más crítica:** `scanned_difficult` (2/10) y `mixed` (4/10) son las más atrasadas. `digital_text_columns` ya alcanzó la meta — primera categoría completa.

**Nota de seguridad — documento descartado:** el usuario subió un escaneo real de una credencial INE (identificación oficial con foto, CURP, domicilio y firma de una persona). Se decidió **no incluirlo** en el corpus por su sensibilidad extrema (riesgo de suplantación de identidad si el archivo se filtrara). Se sustituyó por `synthetic_ine_001`, un mockup con datos 100% ficticios. **El archivo original (`INE_LUIS_ARENAS.pdf`) sigue en `benchmarks/corpus/files/` sin usarse — se recomienda borrarlo.**

**Nota de sensibilidad:** el corpus ya incluye documentos con datos personales reales de terceros (RFC, CURP, domicilio y fecha de nacimiento de personas físicas ajenas a Quark Payments, incluyendo un acta notarial protocolizada de una empresa distinta) — autorizados explícitamente por el usuario para uso interno, caso por caso. Todo el contenido permanece local (`.gitignore`); el manifest documenta la fuente (`tercero_autorizado` vs `quark_payments_interno` vs `synthetic`) para trazabilidad.

**Acciones Siguientes:**
1. [x] Definir fuente de PDFs de prueba (archivos internos de Quark Payments + documentos de terceros autorizados)
2. [x] Obtener autorización de uso (confirmado por el usuario en ambas rondas)
3. [x] Copiar PDFs a `benchmarks/corpus/files/` y completar `corpus_manifest.csv` (30 filas)
4. [ ] Conseguir más escaneos reales, especialmente de baja calidad, para `scanned_difficult` — bloqueador restante
5. [ ] Completar `digital_simple_table`, `digital_complex_table`, `digital_text_columns`, `scanned_clean` y `mixed` hasta 10 c/u
6. [ ] Ampliar ground truth real (hay tablas simples, una página de tablas complejas, texto Word, dos páginas OCR limpio y una región OCR difícil)
7. [ ] Finalizar desarrollo/evaluación por origen y plantilla (split por hash ya generado)

### Benchmarking de Motores (P02) - CRÍTICA
**Estado:** PIPELINE VALIDADO — muestra inicial medida; falta ampliar referencias por clase. La corrida 2026-10-07 descrita abajo es histórica; ver validación 2026-10-08 al final.
**Después de:** P01
**Duración Estimada:** 3-5 días

**Entregado:**
- `benchmarks/tables_benchmark.py` — pdfplumber vs Camelot vs Docling, F1 por fila de tabla
- `benchmarks/ocr_benchmark.py` — Tesseract (con/sin preprocesamiento OCRmyPDF), CER
- `benchmarks/runner.py` — corre ambos y evalúa contra los umbrales del Gate F0
- `make benchmark` / `make benchmark-tables` / `make benchmark-ocr`

**Corrida de validación (2026-10-07) — entorno de desarrollo Windows:**

Instalado para esta prueba (no son las versiones pineadas de producción en `requirements.txt`, se usaron las últimas disponibles solo para validar el pipeline):
- Binarios del sistema: Tesseract 5.4.0 (vía winget `UB-Mannheim.TesseractOCR`) + Poppler 25.07.0 (vía winget `oschwartz10612.Poppler`)
- Datos de idioma Tesseract (eng+spa+osd) en `benchmarks/.tessdata/` (gitignored) vía `TESSDATA_PREFIX`, porque la instalación en `Program Files` requiere admin y solo trae inglés por defecto
- Paquetes Python: `pdfplumber`, `pytesseract`, `pdf2image`, `camelot-py[cv]` 2.0.0, `ocrmypdf` 17.13.0
- **Docling no se instaló** (dependencias ML pesadas) — se omitió explícitamente para esta corrida, reportado como "DepMissing", no como error

**Resultado (13 PDFs con tabla, 11 PDFs para OCR):**

| Motor | Corrió | Errores | Notas |
|---|---|---|---|
| pdfplumber | 13/13 | 0 | F1=1.000 en el único PDF con ground truth (sintético) |
| camelot | 13/13 | 0 | F1=1.000 en el mismo PDF |
| docling | 0/13 | — | Dependencia no instalada (omitido a propósito) |
| tesseract | 11/11 | 0 | Sin ground truth real aún → no hay CER medido |
| tesseract+ocrmypdf | 10/11 | 1 | Error legítimo: una imagen embebida de resolución extrema (>178M píxeles) dispara el límite anti-"decompression bomb" de Pillow — hallazgo real, no bug del benchmark |

**Bug encontrado y corregido en `benchmarks/common.py`:** `print_summary` contaba las filas con "dependencia faltante" como "0 errores" (parecía que todo corría bien cuando en realidad no se ejecutó nada). Ahora distingue explícitamente `Ran` / `Errors` / `DepMissing` / `Scored`.

**Conclusión:** el pipeline de P02 funciona de extremo a extremo en Windows. La métrica real de calidad (F1/CER) sigue bloqueada por la falta de ground truth en los PDFs reales — es el siguiente paso crítico, no instalar más dependencias.

**Motores a Evaluar:**
- pdfplumber vs Camelot vs Docling (tablas)
- Tesseract (OCR)
- OCRmyPDF (preprocesamiento)

**Métricas Iniciales:**
- Detección de tablas: F1 >= 0.95 (digitales simples)
- Estructura de celdas: F1 >= 0.95
- Contenido digital: >= 99% exacto
- OCR CER: <= 2%

## Tareas Pendientes

### F0 - Viabilidad (1-2 semanas)
- [ ] P01: Corpus autorizado y métricas
- [ ] P02: Benchmark de motores
- [x] Experimento F0: prototipo XLSX digital y muestra inicial validada
- [x] Experimento F0: prototipo DOCX editable; brecha de texto medida
- [ ] Gate F0: calidad por clase, licencias y costo (Go/No-Go)

Los IDs P03/P04/P05 del plan corresponden a IR/API, aislamiento y permisos/storage.
Los prototipos no completan P08/P10 de producción ni el flujo TXT web P07.

**Gate F0:** Ir a F1 solo con evidencia de:
- XLSX digital simple funcional
- DOCX digital simple funcional
- Licencias revisadas
- Modelo de costo viable

### F1 - Base Segura (1 semana)
- [ ] Setup de API mínima (FastAPI)
- [ ] Database schema (PostgreSQL + Alembic)
- [ ] Autenticación/autorización básica
- [ ] Storage privado (local/S3)
- [ ] Cola (Celery + RabbitMQ)
- [ ] Aislamiento de procesos
- [ ] Flujo TXT end-to-end

### F2 - Conversión Excel (2 semanas)
- [ ] Extracción de tablas digitales
- [ ] Exportación a XLSX
- [ ] Validación de datos
- [ ] Preview interactivo
- [ ] Corrección de celdas

### F3 - Conversión Word (2 semanas)
- [ ] Extracción de estructura
- [ ] Exportación a DOCX
- [ ] Imágenes y tablas
- [ ] Estilos básicos
- [ ] Render comparativo

### F4 - OCR y Escaneados (1-2 semanas)
- [ ] OCR Tesseract
- [ ] Rotación de páginas
- [ ] Clasificación digital/escaneada/mixta
- [ ] Métricas por clase

### F5 - Otros Formatos y UX (1 semana)
- [ ] MD, JSON, PNG/JPEG
- [ ] Lotes (hasta 10 archivos)
- [ ] Accesibilidad
- [ ] UX mejorada

### F6 - Operación y Piloto (2-3 semanas)
- [ ] Pruebas de carga
- [ ] Monitoring y observabilidad
- [ ] Hardening de seguridad
- [ ] Runbooks de operación
- [ ] Piloto con usuarios reales

## Bloqueadores Actuales

| Bloqueador | Impacto | Solución | ETA |
|-----------|---------|---------|-----|
| Corpus incompleto (37 registrados) | Cobertura P01 insuficiente | Completar seis clases y referencias visuales | Por definir |
| Word validado en un solo diseño | Evidencia insuficiente para prometer soporte general | Anotar otros diseños y evaluar estructura/imágenes | Por definir |
| Referencias parciales de tablas complejas y OCR limpio | Gate sin cobertura documental completa | Ampliar páginas adyacentes y documentos reservados | Después de anotar |
| Portada OCR limpio con CER normalizado 3.723% | Supera umbral candidato 2% | Comparar segmentación/preprocesamiento por layout | Por definir |
| Licencias/costo y aislamiento de producción pendientes | No se puede aprobar F0/F1 | Revisión del stack efectivo y medición de recursos | Antes de F1 |

## Riesgos Monitoreados

| Riesgo | Probabilidad | Impacto | Mitigation |
|--------|-------------|--------|-----------|
| Motor PDF abandonado | Media | Alto | Adaptadores, SBOM actualizado |
| Conflict Word edición vs apariencia | Media | Medio | Evaluar en F0 con corpus |
| OCR de baja calidad | Media | Medio | Separar evaluación por clase |
| Escalabilidad no probada | Baja | Alto | Benchmark con límites |
| Pérdida de datos en retención | Baja | Crítico | Tests de borrado + auditoría |

## Decisiones Registradas

### D001: FastAPI + Python
- **Fecha:** 2026-10-07
- **Resultado:** Seleccionado como framework principal
- **Alternativas Rechazadas:** Django, NestJS, ASP.NET Core
- **Referencia:** ADR 0001

### D002: PostgreSQL + SQLAlchemy
- **Fecha:** 2026-10-07
- **Resultado:** Base de datos y ORM seleccionados
- **Patrón:** Outbox para durabilidad
- **Referencia:** ADR 0002

### D003: Celery + RabbitMQ
- **Fecha:** 2026-10-07
- **Resultado:** Sistema de colas seleccionado
- **Patrón:** Idempotencia y retries
- **Referencia:** ADR 0003

## Verificaciones Ejecutadas

### Verificación de Estructura
- [x] Directorios creados correctamente
- [x] Archivos de configuración presente
- [x] Modelos Pydantic validan
- [x] requirements.txt con versiones fijas

### Verificación de Documentación
- [x] README.md completo
- [x] ADRs documentadas
- [x] Comentarios en código
- [x] AVANCE.md actualizado

### Tests Ejecutados
- [ ] Unit tests de modelos IR
- [ ] Integration tests de DB
- [ ] E2E de API mínima

## Métricas Medidas

| Métrica | Valor | Fecha | Notas |
|---------|-------|-------|-------|
| Líneas de código base | 500+ | 2026-10-07 | Models + config |
| Dependencias | 41 + dev tools | 2026-10-07 | Todas versionadas |
| ADRs | 3 | 2026-10-07 | Framework, DB, queues |
| Documentación | 5 archivos | 2026-10-07 | README, ADRs, etc |

## Próximos Pasos Inmediatos

### Semana 1 (P01 - Definir Corpus)
```
Día 1: Reunión corpus + selección PDFs de prueba
Día 2-3: Obtener autorización + copiar archivos
Día 4-5: Anotar ground truth + crear manifest
```

**Entregables:**
- Manifest de corpus (CSV con metadata)
- Ground truth (anotaciones de tablas/celdas críticas)
- Script de reproducibilidad

### Semana 2 (P02 - Benchmark Motores)
```
Día 1: Setup de ambiente de benchmark
Día 2-3: Ejecutar pdfplumber vs Camelot vs Docling
Día 4-5: Calcular métricas F1, CER, timing
```

**Entregables:**
- Reporte comparativo de motores (CSV/JSON)
- Gráficos de rendimiento
- Decisión de motor por clase de documento

### Semana 3 (P03-P05 - Gate F0)
```
Día 1-2: Evaluar viabilidad XLSX
Día 3-4: Evaluar viabilidad DOCX
Día 5: Tomar decisión Go/No-Go
```

**Gate F0 - Criterios:**
- ✓ F1 XLSX >= 0.95 en tablas simples
- ✓ F1 DOCX >= 0.90 en estructura simple
- ✓ Licencias sin bloqueadores
- ✓ Modelo de costo definido
- ✓ Equipo comprometido con continuación

## Comandos Útiles de Desarrollo

```bash
# Clonar repo y setup
git clone <repo>
cd pdf_converter
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Docker Compose
docker-compose up -d
docker-compose logs -f api

# Tests
pytest tests/ -v
pytest tests/ --cov

# Code quality
black apps/ packages/ tests/
isort apps/ packages/ tests/
mypy apps/ packages/

# Database
alembic revision --autogenerate -m "message"
alembic upgrade head

# Run API
cd apps/api
uvicorn main:app --reload

# Run worker
cd apps/worker
celery -A tasks worker --loglevel=info
```

## Contactos y Roles

| Rol | Responsable | Contacto | Estado |
|-----|------------|----------|--------|
| Coordinador | TBD | - | Asignar |
| Arquitectura/Backend | TBD | - | Asignar |
| Conversión Documental | TBD | - | Asignar |
| UX/Frontend | TBD | - | Asignar |
| Calidad/QA | TBD | - | Asignar |
| Seguridad/DevOps | TBD | - | Asignar |

## Validación del prototipo — 2026-10-08

Entregables: `apps/convert.py`, extractor `packages/converters/digital.py`,
exportadores `packages/exporters/xlsx.py` y `docx.py`, herramientas
`benchmarks/prepare_review.py` y `validate_prototype.py`, y 31 pruebas.
Uso, métricas y límites: [PROTOTIPO_F0.md](PROTOTIPO_F0.md).
Decisión de alcance: [ADR 0004](adr/0004-f0-local-prototype.md).

Comandos realmente ejecutados:

```powershell
python -m pip install --target .generated/deps python-docx==1.2.0
python -m apps.convert benchmarks/corpus/files/synthetic_base_invoice.pdf --output .generated/check_initial --formats xlsx txt
python -m benchmarks.prepare_review
$env:PYTHONPATH = (Join-Path (Get-Location) '.generated/deps')
python -m benchmarks.validate_prototype
python -m pytest tests/unit/test_f0_prototype.py -o addopts='--strict-markers --tb=short -q'
```

La última corrida de pruebas dio **31 passed**, con avisos de plugins ausentes
para `asyncio_mode` y `timeout`. No se ejecutó cobertura global ni se validó
Office/LibreOffice. El entorno bloqueó la lectura de dependencias locales;
las corridas de pruebas y validación se aprobaron fuera del aislamiento.

Resultados locales: `.generated/f0/report.json`, salidas por documento bajo
`.generated/f0/<file_id>/`, referencias sensibles en
`benchmarks/ground_truth/local/`, tareas y split en `benchmarks/review/`.
Hay seis PDFs con referencia contando el sintético: tabla de página 19,
texto completo de páginas 1 y 3 y una región OCR, además de las tres muestras
iniciales. El split es provisional y evita cruzar duplicados exactos; falta
agrupar por origen/plantilla. No publicar estos artefactos ni transcripciones.

**Corrección de evidencia:** el CER Word inicial de 4.675% fue causado por
una transcripción incorrecta e incompleta de la referencia. La ampliación
visual confirmó el pie y las palabras del original; la referencia revisión 2
da CER 0% en pdfplumber → DOCX y en la segunda ruta PDFium → DOCX textual.
No se cambió la extracción para borrar el pie o corregir erratas del PDF.
El reporte y la referencia anteriores se preservaron en `.generated/review_round2/`.

La tabla de página 19 fue adjudicada con recortes a 6×: F1 de filas pdfplumber
1.000 y 88/88 celdas; no valida unión de tablas. OCR limpio tiene CER normalizado
3.723% en portada y 0.968% en texto continuo con PSM 3. PSM 6 empeora la portada
a 60.106%; reportar separado, no elegir un promedio que esconda ese fallo.

**Gate F0 permanece pendiente.** Faltan tamaño de muestra, estructura,
documentos completos, licencias/costo y rendimiento. Mantener el experimento
local; las páginas adyacentes y las variantes OCR ya se ensayaron con el
alcance descrito en [PROTOTIPO_F0.md](PROTOTIPO_F0.md).

## Punto de continuación guardado — 2026-10-08

Sesión detenida por solicitud del usuario. Prototipo digital CLI y exportadores
guardados, 41 pruebas aprobadas y validación de seis referencias ejecutada.
Continuidad candidata comprobada con 16 celdas de frontera; no reconstruye
filas partidas. Catorce experimentos OCR no mejoraron la portada (3.723%).
Mediciones de recursos e inventario de dependencias permanecen locales en
`.generated/`; referencias y PDFs sensibles conservan su exclusión de Git.

GitHub Actions está deshabilitado en el repositorio (`enabled: false`),
verificado mediante API. El workflow local conserva solo ejecución manual.

Retomar ampliando referencias completas y verificando reconstrucción de filas
partidas. Después medir carga y revisar binarios/modelos, dependencias del
stack completo y tarifas. No aprobar F0 ni iniciar el flujo web con la muestra
actual. Los detalles reproducibles están en `PROTOTIPO_F0.md` y `LICENCIAS.md`.

## Sincronización con GitHub — 2026-10-09

El commit `712df98` ("Guardar prototipo F0, validaciones y desactivar Actions")
se subió a `origin/master` (`leoCryptoMillions/pdf_converter`). No hubo trabajo
adicional en esta sesión: el árbol de trabajo está limpio y el estado del
prototipo, corpus y bloqueadores es el mismo descrito en las secciones
anteriores (validación 2026-10-08).

## Enrutamiento needs_review de OCR (DEC-04) implementado — 2026-10-23

A pedido directo del usuario ("procede con F0-05"), se implementó y verificó
el enrutamiento `needs_review` que el 2026-10-20 solo se había aceptado como
criterio (DEC-04), no como código. Antes de escribir nada se confirmó que
`apps/convert.py` no ejecutaba OCR en absoluto — solo pdfplumber, con una
advertencia `OCR_REQUIRED` para páginas sin texto — y que CLAUDE.md asigna
la integración de OCR a F4, no a F0. Se le preguntó al usuario si prefería
(a) redefinir el hallazgo como diferido a F4, (b) construir OCR mínimo ahora
adelantando ese alcance, o (c) solo fijar el comportamiento actual con una
prueba; eligió (b).

**Qué se construyó:** `packages/converters/ocr.py` (nuevo), opt-in vía
`extract_digital(..., ocr=True)` y la nueva bandera `--ocr` en
`apps/convert.py` (antes inexistente; el flag por defecto es `False`, el
comportamiento previo no cambia). Usa `pytesseract.image_to_data` (confianza
real de palabra reportada por el propio motor, no fabricada) con `spa+eng`,
PSM 3 — la configuración ya validada en `benchmarks/ocr_experiments.py` — y
reutiliza la misma detección de binarios de Windows que
`benchmarks/ocr_benchmark.py`. Enrutamiento: página 1 ("portada") siempre
`needs_review=True` sin importar la confianza (heurística **posicional**,
no visual — limitación conocida y documentada, no oculta: un documento con
portada fuera de la página 1 se clasifica mal); el resto de páginas se
enruta por confianza media >= 0.85, el mismo número que ya usa el ejemplo de
`ContentWarning` en `CLAUDE.md` (no un umbral inventado para esta tarea). La
corrección de texto plano se integra como `TextBlock` nuevo por página OCR'd
y los nuevos códigos de advertencia (`OCR_COVER_PAGE_UNVALIDATED`,
`OCR_LOW_CONFIDENCE`, `OCR_APPLIED`, `OCR_FAILED`) aparecen automáticamente
en las hojas `_Warnings`/"Conversion warnings" de XLSX y DOCX sin tocar esos
exportadores, porque ya recorren `page.warnings`.

**Verificación ejecutada (no autoatestada):** Tesseract 5.4.0 y Poppler 25.07
sí están disponibles en esta sesión (no lo estaban el 2026-10-20). Corrida
real de `extract_digital(ocr=True)` contra
`benchmarks/corpus/files/manualcargadorBYD.pdf` páginas 1 y 3 — la muestra
exacta de DEC-04: página 1 con confianza real 92% quedó `needs_review=True`
de todas formas (confirma que el piso no aplica a portada); página 3 con 95%
quedó `needs_review=False`. El texto con acentos se verificó correcto por
code point (`ord()`); una inspección visual inicial en terminal sugería
corrupción UTF-8 y resultó ser solo mal renderizado por la consola, no un
defecto real del dato. 5 pruebas nuevas en `tests/unit/test_ocr_routing.py`
(incluida la corrida real anterior, sin mocks), todas pasan. Suite completa:
43 passed, 3 failed — los 3 fallos dependen de `python-docx` no instalado en
el intérprete que usa `subprocess` en esos tests, preexistente a esta sesión
(ya documentado arriba, no causado por este cambio).

**Qué NO cambió:** la métrica cruda de CER de portada (3.723%) sigue igual;
DEC-04 ya había aceptado no perseguirla. `scanned_difficult` en general
(RSK-03) sigue sin el mismo tratamiento de calidad — el mecanismo de
enrutamiento ya es genérico por página, pero nadie midió su CER todavía.

Dashboard de preparación y brechas actualizado en la misma sesión: F0-05
pasa a `implementation_status=implemented`, `verification_status=passed`;
BLK-04 y DEC-04 actualizados para no apuntar a un pendiente ya resuelto; nota
añadida a RSK-03. Verificado en navegador real (servidor local, no
`file://` reabierto): sin errores de consola, ficha de F0-05 y RSK-03
renderizan correctamente. Detalle completo en
`prototipos/preparacion-brechas/seguimiento.md` (entrada 2026-10-23).

## Interfaz web local de conveniencia — 2026-10-23

A pedido del usuario ("genera un front end en web para que sea fácil para el
usuario"), se preguntó explícitamente el alcance antes de construir, por la
misma disciplina de fases aplicada a F0-05: ¿wrapper mínimo local de un solo
usuario, o el primer endpoint real de F1 sobre `apps/api/`? Eligió el
wrapper mínimo.

Se construyó `apps/local_review_ui.py`: un servidor FastAPI pensado para
`127.0.0.1`, sin cuentas, sin base de datos, sin cola, que reutiliza tal
cual `packages/converters/digital.py` y `packages/exporters/` — no es una
reimplementación, es el mismo motor del CLI con un formulario HTML encima.
Deliberadamente no toca `apps/api/` (reservado para F1) para no generar una
falsa señal de avance en esa área; se dejó una nota explícita en el
dashboard (F0-06) aclarando la distinción.

Verificado con pruebas reales (`tests/unit/test_local_review_ui.py`, 4
passed, sin mocks: sube un PDF, descarga el XLSX, valida que es un zip
correcto; rechaza no-PDF; rechaza traversal de ruta en `/download`), con el
servidor corriendo de verdad (`python -m apps.local_review_ui`) probado en
un navegador real, y con una conversión de extremo a extremo por `curl`
(subida → descarga → `openpyxl` confirma la tabla correcta). Suite completa:
50 passed. Dependencias nuevas instaladas en el entorno y fijadas en
`requirements-prototype.txt`: `fastapi`, `uvicorn`, `python-multipart`
(`python-docx` también se instaló, antes faltaba y causaba 3 fallos
preexistentes de la suite relacionados con DOCX, ya resueltos).

Pendiente, no bloqueante: sin borrado/TTL de `.generated/web_ui/`.

## UX del wrapper y prácticas adaptadas de conta01 — 2026-10-23

Por petición directa del usuario se mejoró el wrapper existente con carga
por arrastre, formatos visuales, resumen de opciones, progreso y resultados
con descargas, vista del texto y notas de revisión. Los errores conservan
formatos, páginas y OCR. Se corrigió el caso de desmarcar todos los formatos:
ahora se exige una selección explícita, también en el servidor.

Se añadió el botón claro/oscuro a la cabecera compartida. La elección se
aplica antes del CSS, persiste entre páginas y recargas, prevalece sobre el
tema del sistema y sincroniza otras pestañas. Con almacenamiento bloqueado
el botón conserva su función durante la página; sin JavaScript se usa la
preferencia del sistema. Todos los colores de superficies, controles,
errores y advertencias están centralizados por tema.

La revisión dirigida, de solo lectura, de `conta01` abarcó el tema y layout,
variables CSS, almacenamiento opcional, errores recuperables, diálogo
nativo, cabeceras/CSP y prácticas de cobertura y continuidad documental.
Las adaptaciones concretas y las que se reservan para F1 constan en
`docs/PROTOTIPO_F0.md`, sección «Prácticas revisadas en conta01».
El wrapper añade cabeceras `nosniff`, bloqueo de marcos, `no-referrer` y CSP
con recursos/formularios del mismo origen, sin scripts ni estilos inline.

Evidencia focalizada: 18 pruebas HTTP pasan. El recorrido real en Chromium,
versionado en `tests/e2e/local_review_ui.cjs`, verifica ambos temas,
persistencia, sistema, pestañas, almacenamiento bloqueado, teclado,
contraste de pares de texto, geometría de 375–1440 px, carga, conversión,
descarga y errores, además del formulario sin JavaScript. Las capturas y
mediciones están en `.generated/ui-check/`. Se verifica un botón de al menos
44 × 44 px con 10 px de separación móvil y 18 px en escritorio.
La evidencia no acredita la suite completa ni aceptación operativa de F1.

Sin impacto en las brechas de F0-06/F0-10: sigue siendo una herramienta
local de conveniencia. Se corrige el texto de Flujos del dashboard que aún
afirmaba que no existía ninguna interfaz; no cambian estados ni decisiones.

## Centro de ayuda, FAQ y mascota — 2026-10-23

A pedido directo del usuario se añadió el menú Ayuda, disponible en todas
las pantallas del wrapper. `/ayuda` contiene 13 preguntas frecuentes
buscables sin distinguir acentos o mayúsculas, una guía de cuatro pasos y
las explicaciones de las acciones. La búsqueda tiene alternativa GET sin
JavaScript. Los 20 temas viven en `apps/local_review_assets/help.json` y se
renderizan desde `apps/local_review_help.py`, evitando versiones distintas
de la misma explicación en las FAQ y los botones `?`.

Las acciones visibles de conversión, quitar archivo, tema, descargas,
nueva conversión y búsqueda tienen ayuda adyacente. También se explican
archivo, formatos, páginas, OCR y revisión. Un diálogo nativo muestra la
explicación sin ejecutar la acción y devuelve el foco al cerrar con Escape
o Cerrar. Los enlaces llevan a `/ayuda` cuando no hay JavaScript.

La mascota de Nexia se adaptó mediante la herramienta integrada de edición
de imágenes, conservando el personaje y sustituyendo el texto del pecho por
«PDF Converter». Recurso local: `pdf-converter-guide.png`, 1254 × 1254 RGBA
con transparencia real. Se utiliza en el centro de ayuda y los diálogos.
El prompt, la referencia y la ubicación están en `docs/PROTOTIPO_F0.md`.
No se modificó el repositorio conta01.

Verificación focalizada: 21 pruebas HTTP pasan. Recorrido Chromium de FAQ,
búsqueda, ayuda contextual, conservación del archivo y foco, imágenes,
ambos temas, móvil, conversión, descargas y alternativa sin JavaScript.
Capturas en `.generated/ui-check/help-*.png`, junto al informe del recorrido.
Sin impacto en las brechas de F0-06/F0-10; esta es una mejora de la
herramienta local, no una implementación de F1.

## Estado guardado para continuar — 2026-10-23

Por petición del usuario («listo, guarda todo»), quedan guardados el
rediseño del wrapper, los temas, la ayuda, las FAQ, los `?` contextuales,
la mascota, las pruebas y la documentación de esta sesión. Se prepara un
commit local de estos cambios. La configuración personal de herramientas y
la evidencia generada permanecen locales, fuera del control de versiones.

Última validación del wrapper: 21 pruebas HTTP y recorrido Chromium con
conversión, descargas, ayuda, foco, temas y vistas móviles. Las capturas y el
informe están en `.generated/ui-check/`. Para retomar la vista usada en la
sesión: `python -m uvicorn apps.local_review_ui:app --host 127.0.0.1 --port 8421`;
abrir `http://127.0.0.1:8421/` o `/ayuda`. El arranque habitual con
`python -m apps.local_review_ui` usa el puerto 8420.

El siguiente trabajo de producto debe elegirse de los pendientes reales de
F0; esta mejora de conveniencia no resuelve el Gate F0 ni adelanta F1.
Siguen pendientes el borrado/TTL local y las brechas descritas en el dashboard.

## Word con diseño, imágenes y estilos — 2026-10-26

Por autorización directa («procede con las mejoras que propones»), se
amplía el exportador Word del prototipo local. El IR 1.1.0 conserva estilos
de fragmentos, geometría, medidas de tablas y PNG autocontenidos. La ruta
mantiene texto editable mediante marcos de párrafo, tablas flotantes y
dibujos anclados a cada página. Los paneles complejos se representan con
líneas posicionadas y advertencia; no se presentan como tablas Word.

PDFium elimina el texto de una copia privada en memoria antes de renderizar
imágenes y gráficos. El original no cambia. Se fijan presupuestos de
píxeles/bytes, se serializa esta ruta de PDFium y se informa si algún recurso
no se conserva. OCR mantiene su salida de flujo y sus advertencias. La
extracción visual se activa desde CLI/web solo al solicitar Word.

El anexo de advertencias pasa a ser opcional; las notas siempre permanecen
en resultados/IR. Se actualizan el formulario, los mensajes y la FAQ Word.
`pypdfium2==5.14.0` se añade al subconjunto probado, usando la instalación
existente; la revisión de distribución/licencias sigue pendiente.

Validación: **81 pruebas unitarias/HTTP pasan**, incluidas regresiones de
CLI, XLSX, TXT y OCR real; dos avisos de configuración de pytest preexistentes.
Chromium pasa el recorrido de temas, ayuda, móvil y conversión/descargas.
El tablero pasa apertura de fichas, cancelado/guardado del borrador y
exportación sin cambiar estados (`tests/e2e/gaps_dashboard.cjs`).
Microsoft Word abre y renderiza un comprobante digital local del usuario
en una página y el caso sintético vertical/horizontal en dos páginas. En
el comprobante se verifica el mismo multiconjunto de caracteres no blancos
en el DOCX y en su PDF renderizado, sin pérdidas ni duplicaciones observadas.
No es una medición de CER contra una nueva referencia humana.

Evidencia privada en `.generated/docx-review/`; no se incorpora el archivo
del usuario ni sus datos al corpus o a Git. Decisión: ADR 0005. F0-04 sigue
parcial y pendiente de validación representativa; F0-09/F0-11 siguen abiertos.
Dashboard, fuentes y seguimiento se concilian con este alcance, sin cambiar
sus indicadores (verificación 18%, decisiones 27%).

## Requisitos Word incorporados al plan y alcance — 2026-10-26

Pedido del usuario: «también guarda estos cambios en los requerimientos del
proyecto». El plan y `docs/ALCANCE.md` pasan a revisión 1.1.0; se conserva
el nombre del archivo del plan para mantener los enlaces existentes.
§11.1 centraliza RF-DOCX-01 a RF-DOCX-08 y RNF-DOCX-01: contenido editable,
distribución/estilos, imágenes incorporadas, tablas y degradaciones, fuentes,
OCR, notas/anexo opcional, procedencia/IR y límites de recursos. Se incluyen
comprobaciones de aceptación y validación pendiente en tres diseños reales.

Se enlazan los requisitos desde F0-04 y las fuentes del dashboard. Cambio
documental: no modifica el convertidor ni declara una validación nueva de
calidad. Se mantiene la evidencia del commit `1e43e00` (81 pruebas y revisión
Word/Chromium), sin presentarla como una nueva ejecución de pruebas.
F0-04 sigue partial/pending; Gate F0 pendiente. Indicadores sin cambios:
verificación 18% (2/11), decisiones 27% (3/11).

## Calendario anterior (referencia histórica)

**Fecha Planeada:** 2026-10-14 (después de completar P01)  
**Actualizador:** Coordinador técnico  
**Cambios Esperados:**
- Status de corpus actualizado
- Benchmark inicial de motores
- Decisiones de F0 documentadas
- Bloqueos removidos o escalados
