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

## Calendario anterior (referencia histórica)

**Fecha Planeada:** 2026-10-14 (después de completar P01)  
**Actualizador:** Coordinador técnico  
**Cambios Esperados:**
- Status de corpus actualizado
- Benchmark inicial de motores
- Decisiones de F0 documentadas
- Bloqueos removidos o escalados
