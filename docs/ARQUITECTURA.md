# Arquitectura del Sistema - PDF Converter

**Versión:** 1.0.0  
**Fecha:** 2026-10-07  
**Estado:** Diseño - Implementación en progreso (F0)

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (React + TypeScript + Vite)                            │
│ - Carga de PDF                                                   │
│ - Vista previa                                                   │
│ - Edición de tablas                                              │
│ - Descarga de resultados                                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/REST + WebSocket (SSE)
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ API (FastAPI - Puerto 8000)                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Routes:                                                     │ │
│ │ - POST   /v1/files        → Upload PDF                     │ │
│ │ - POST   /v1/conversions  → Create job                     │ │
│ │ - GET    /v1/conversions/{id}                              │ │
│ │ - GET    /v1/conversions/{id}/preview                      │ │
│ │ - PATCH  /v1/conversions/{id}/tables                       │ │
│ │ - POST   /v1/conversions/{id}/exports                      │ │
│ │ - GET    /v1/artifacts/{id}/download                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────┬──────────────────────┬──────────────────┬──────────────────┘
     │ Read/Write           │ Read/Write       │ Enqueue
     ↓                      ↓                  ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ PostgreSQL   │    │ Storage      │    │ RabbitMQ     │
│ (Users, Jobs,│    │ (PDF files,  │    │ (Task Queue) │
│  Artifacts,  │    │  Artifacts,  │    │              │
│  Outbox)     │    │  Previews)   │    │              │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                                │
                                                ↓
                                       ┌──────────────┐
                                       │ Celery       │
                                       │ Workers      │
                                       │ (2-N)        │
                                       └──────┬───────┘
                                              │
                ┌─────────────────────────────┼─────────────────┐
                ↓                             ↓                 ↓
        ┌───────────────┐        ┌───────────────────┐  ┌──────────────┐
        │ PDF Parser    │        │ OCR Engine        │  │ Exporters    │
        │ (pdfplumber,  │        │ (Tesseract)       │  │ (openpyxl,   │
        │  Docling,     │        │                   │  │  python-docx)│
        │  Camelot)     │        └───────────────────┘  └──────────────┘
        └───────────────┘
                │
                ↓
        ┌───────────────┐
        │ Document IR   │
        │ (Intermediate │
        │  Represent.)  │
        └───────────────┘
```

## Componentes Principales

### 1. Frontend (React + TypeScript + Vite)
- **Puerto:** 3000 (desarrollo)
- **Build:** Vite
- **Funciones:**
  - Upload de PDF (drag-and-drop)
  - Vista previa con PDF.js
  - Tabla editable para correcciones
  - Descarga de resultados
  - Indicadores de progreso

**Ubicación:** `apps/web/`

### 2. Backend API (FastAPI)
- **Puerto:** 8000
- **Framework:** FastAPI + Uvicorn
- **Features:**
  - OpenAPI/Swagger documentation
  - Request validation (Pydantic)
  - Autenticación/Autorización
  - Rate limiting y quotas
  - CORS configuration

**Ubicación:** `apps/api/`

**Endpoints Principales:**
- Gestión de archivos (upload, validación)
- Creación y seguimiento de trabajos
- Vista previa de resultados
- Descarga de artefactos
- Corrección de tablas

### 3. Worker (Celery)
- **Broker:** RabbitMQ (AMQP)
- **Result Backend:** Redis
- **Concurrencia:** Configurable (1-N workers)
- **Funciones:**
  - Validación de PDF
  - Extracción de contenido
  - Exportación a formatos
  - OCR de documentos escaneados
  - Limpieza de datos expirados

**Ubicación:** `apps/worker/`

**Tareas Principales:**
- `validate_pdf` - Validación y clasificación
- `convert_to_xlsx` - Conversión a Excel
- `convert_to_docx` - Conversión a Word
- `perform_ocr` - Procesamiento OCR
- `cleanup_expired_files` - Mantenimiento

### 4. Base de Datos (PostgreSQL)
- **Versión:** 15+
- **Puerto:** 5432
- **Esquema:**
  - `users` - Cuentas de usuario
  - `organizations` - Tenants multi-usuario
  - `conversion_jobs` - Estado de trabajos
  - `documents` - Metadata de PDFs
  - `artifacts` - Archivos resultantes
  - `outbox_events` - Durabilidad de eventos

**Features:**
- ACID transactions
- Outbox pattern para durabilidad
- Full-text search
- JSON columns para metadata flexible

### 5. Storage (S3-compatible o Local)
- **Modos:** Local (/tmp/), MinIO, AWS S3
- **Contenido:**
  - PDFs originales (cuarentena)
  - Previews generadas
  - Artefactos exportados (XLSX, DOCX, etc)
- **Ciclo de vida:** Expiran según retention_hours
- **Seguridad:** Acceso privado, sin URLs públicas

### 6. Caching (Redis)
- **Puerto:** 6379
- **Usos:**
  - Sesiones
  - Cache de resultados
  - Backend de Celery
  - Locks distribuidos

### 7. Message Broker (RabbitMQ)
- **Puerto:** 5672 (AMQP)
- **UI:** 15672 (Management)
- **Queues:**
  - `default` - Validación y tareas rápidas
  - `processing` - Conversión XLSX/DOCX
  - `ocr` - Trabajos OCR (CPU intensivos)
  - `maintenance` - Limpieza y mantenimiento

## Patrones Arquitectónicos

### 1. Modelo Intermedio (Document IR)
Esquema canónico para representar documentos entre motores:
```
PDF → Parser → DocumentIR → Exporter → XLSX/DOCX/etc
```
- Independiente del motor de extracción
- Versionado para compatibilidad
- Incluye metadatos de origen y confianza

### 2. Outbox Pattern
Garantiza durabilidad de eventos:
```
API transaction: save Job + OutboxEvent (atómico)
    ↓
Worker: poll OutboxEvents
    ↓
Publish to broker
    ↓
Mark as published (solo tras confirmación)
```

### 3. Idempotencia
Protección contra entregas duplicadas de tareas:
```
Check: ¿Job ya procesado?
    ↓ No
Process: generar artefacto
    ↓
Store: atomic save con generation token
    ↓
Mark: task complete (idempotent)
```

### 4. Isolación de Procesos
PDF processing en containers separados:
```
API: sin root, sin red → Solo coordina
Worker Supervisor: acceso a cola y storage
Conversion Process: solo archivos necesarios, sin secretos
```

## Decisiones Tecnológicas

| Componente | Tecnología | Rationale |
|-----------|-----------|-----------|
| API | FastAPI | Tipado, async, OpenAPI, Python |
| Frontend | React + Vite | SPA, HMR, build rápido |
| Backend | Python 3.11+ | Ecosistema PDF/OCR |
| DB | PostgreSQL 15+ | ACID, JSON, full-text |
| Queue | RabbitMQ | AMQP, reliable delivery |
| Cache | Redis | Sessions, result backend |
| Storage | S3-compat | Flexible, local/cloud |
| Containers | Docker | Aislamiento, reproducibilidad |
| OCR | Tesseract | Open source, español/inglés |

## Escalabilidad

### Horizontal
- **API:** Múltiples instancias (load balancer)
- **Workers:** Escalar según carga OCR
- **Database:** Replica read-only (futuro)
- **Storage:** S3 es automáticamente escalable

### Vertical
- Aumentar vCPU/RAM para API
- Limites por proceso en workers
- Connection pooling optimizado

### Límites Iniciales (F1)
- 1 API instance
- 1-2 workers
- Single PostgreSQL instance
- Local storage (escalable a S3)

## Seguridad

### Validación
- ✓ ZIP bombs, archivos corrupto detectados
- ✓ Límites de tamaño/páginas enforced
- ✓ Escaneo de contenido malicioso (aislamiento)
- ✓ Validación de tipos MIME

### Aislamiento
- ✓ Procesos sin root
- ✓ Sin red saliente
- ✓ Sin secretos/credenciales
- ✓ Filesystem restringido

### Autorización
- ✓ Multi-tenant (organization_id)
- ✓ RBAC (roles básicos)
- ✓ Quotas por usuario/org
- ✓ Audit logging

### Datos
- ✓ TLS en tránsito (HTTPS)
- ✓ Contraseña de DB versionada
- ✓ Retención automática (24h)
- ✓ Borrado verificable

## Performance

### Benchmarks Iniciales (F0)
- **Digital limpio:** p95 <= 30s (10 páginas)
- **OCR limpio:** p95 <= 180s (10 páginas)
- **RAM:** < 2GB por proceso
- **CPU:** Escalable con workers

### Optimizaciones (Futuro)
- GPU para Tesseract
- Caché de DocumentIR
- Batch processing
- Streaming de resultados

## Observabilidad

### Logging
- Structlog (JSON)
- Niveles por módulo
- Sin contenido sensible
- Búsqueda centralizada (futuro)

### Métricas
- Prometheus en puerto 9090
- Duración por fase
- Errores por motor
- Profundidad de cola
- RAM/CPU peak

### Alertas
- Cola atascada
- Crecimiento de errores
- Disco lleno
- Worker offline

## Referencias

- **Plan Completo:** [PLAN_APP_CONVERSION_PDF_v1.0.md](../PLAN_APP_CONVERSION_PDF_v1.0.md)
- **ADR 0001:** Framework Selection
- **ADR 0002:** Database Strategy
- **ADR 0003:** Background Processing
- **API Docs:** http://localhost:8000/docs
