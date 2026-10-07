# Progreso del Proyecto - PDF Converter

Versión del Plan: 1.0.0  
Fecha de Actualización: 2026-10-07  
Estado Actual: **INICIADO - Fase P01 (Corpus y Métricas)**

## Estado Resumen

```yaml
proyecto: conversion-pdf
plan_version: 1.0.0
actualizado: 2026-10-07
fase_actual: F0 - Viabilidad
fase_detalle: P01 - Definir corpus y métricas (herramientas listas, corpus pendiente)
estado: en_progreso
ultimo_commit: pendiente
completado:
  - Lectura de plan
  - Selección de framework
  - Revisión de arquitectura
  - Creación de estructura de proyecto
  - Definición de modelos IR
  - Configuración de dependencias
  - Herramientas de benchmark P02 (tables_benchmark.py, ocr_benchmark.py, runner.py)
  - Plantilla de manifest de corpus y ground truth (P01)
pendiente_verificacion:
  - Bootstrap de proyecto
  - Funcionalidad mínima de API
decisiones: []
bloqueos:
  - Corpus de 60 PDFs autorizados aún no recolectado
pruebas_ejecutadas: []
metricas_medidas: []
riesgos_abiertos:
  - Corpus de 60 PDFs no disponible aún
  - Benchmark de motores no ejecutado (herramienta lista, falta corpus real)
  - Gate F0 sin criterios cuantitativos finales
siguiente_tarea: P01_preparar_corpus_autorizado
criterio_siguiente_tarea: manifest_de_60_pdfs_con_ground_truth
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
**Estado:** EN PROGRESO — herramientas y plantillas listas, corpus real pendiente
**Duración Estimada:** 3-5 días
**Criterio de Salida:** 60+ PDFs categorizados con ground truth

**Entregado:**
- `benchmarks/README.md` — flujo completo P01 → P02 → Gate F0
- `benchmarks/corpus_manifest.csv` — plantilla con columnas y categorías
- `benchmarks/ground_truth/README.md` — plantilla de anotación JSON
- `benchmarks/corpus/files/` — carpeta destino para los PDFs (no versionada)

**Requerimientos:**
- Mínimo 60 PDFs autorizados
- Al menos 10 por grupo:
  - Tablas digitales simples
  - Tablas digitales complejas/multipágina
  - Texto digital con columnas
  - Escaneados limpios
  - Escaneados difíciles
  - Documentos mixtos
- Suite adversarial (cifrados, corruptos, grandes)

**Acciones Siguientes:**
1. [ ] Definir fuente de PDFs de prueba
2. [ ] Obtener autorización de uso
3. [ ] Copiar PDFs a `benchmarks/corpus/files/` y completar `corpus_manifest.csv`
4. [ ] Anotar ground truth (texto, tablas, celdas críticas) en `benchmarks/ground_truth/`
5. [ ] Separar conjunto de desarrollo vs evaluación

### Benchmarking de Motores (P02) - CRÍTICA
**Estado:** HERRAMIENTA LISTA — bloqueada por P01 (sin corpus real aún no hay métricas)
**Después de:** P01
**Duración Estimada:** 3-5 días

**Entregado:**
- `benchmarks/tables_benchmark.py` — pdfplumber vs Camelot vs Docling, F1 por fila de tabla
- `benchmarks/ocr_benchmark.py` — Tesseract (con/sin preprocesamiento OCRmyPDF), CER
- `benchmarks/runner.py` — corre ambos y evalúa contra los umbrales del Gate F0
- `make benchmark` / `make benchmark-tables` / `make benchmark-ocr`

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
- [ ] P03: Revisar viabilidad XLSX digital
- [ ] P04: Revisar viabilidad DOCX digital
- [ ] P05: Gate F0 (Go/No-Go)

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
| Sin corpus de prueba | P01 crítico bloqueado | Obtener/generar PDFs autorizados | 2-3 días |
| Motores sin evaluar | F0 gate incompleto | Ejecutar benchmark (P02) | Después P01 |
| Herramientas OCR sin instalar | F4 planificación afectada | Setup de Tesseract + OCRmyPDF | Antes F0 evaluación |

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

## Próxima Actualización

**Fecha Planeada:** 2026-10-14 (después de completar P01)  
**Actualizador:** Coordinador técnico  
**Cambios Esperados:**
- Status de corpus actualizado
- Benchmark inicial de motores
- Decisiones de F0 documentadas
- Bloqueos removidos o escalados
