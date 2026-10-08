# PDF Converter Application

Aplicación web para convertir PDFs digitales, escaneados y mixtos en archivos editables y reutilizables: Excel (.xlsx), Word (.docx), CSV, TXT, Markdown, JSON y PNG/JPEG.

## Características Principales

**Estado actual:** prototipo CLI de viabilidad (F0). La aplicación web,
la carga de archivos y los trabajos de conversión siguen pendientes.
Las características enumeradas a continuación describen el objetivo del MVP.

Para probar el flujo local PDF → XLSX/DOCX/TXT:

```bash
python -m pip install -r requirements-prototype.txt
python -m apps.convert benchmarks/corpus/files/synthetic_base_invoice.pdf --output .generated/demo --formats xlsx docx txt
```

La carpeta de salida debe ser nueva. Consulte [el prototipo F0](docs/PROTOTIPO_F0.md)
para anotaciones, validación, tipos de Excel y limitaciones medidas.

- Conversión de PDFs a múltiples formatos
- Soporte para documentos digitales, escaneados y mixtos
- OCR en español e inglés
- Validación de datos y prevención de pérdida de información
- Interfaz interactiva para revisar y corregir resultados
- Almacenamiento privado seguro
- Procesamiento distribuido con Celery + RabbitMQ

## Stack Tecnológico

- **Backend**: FastAPI + Python
- **Frontend**: React + TypeScript + Vite
- **Procesamiento**: Celery + RabbitMQ
- **Base de datos**: PostgreSQL
- **Almacenamiento**: Compatible con S3
- **Infraestructura**: Docker + Docker Compose

## Requisitos Previos

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (para desarrollo frontend)
- 4-8 vCPU y 16 GB RAM recomendado

## Inicio Rápido

### Desarrollo Local con Docker Compose

```bash
# Copiar configuración
cp .env.example .env

# Iniciar servicios
docker-compose up -d

# Ejecutar migraciones
docker-compose exec api python -m alembic upgrade head

# Acceder a:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000 (en desarrollo)
```

### Desarrollo Manual

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurar variables de entorno
cp .env.example .env

# Ejecutar migraciones
alembic upgrade head

# Iniciar API (desde apps/api)
python -m uvicorn main:app --reload

# Iniciar worker (desde apps/worker)
celery -A tasks worker --loglevel=info

# Iniciar frontend (desde apps/web)
npm install
npm run dev
```

## Documentación

- [Plan de Trabajo](./PLAN_APP_CONVERSION_PDF_v1.0.md) - Plan completo del proyecto
- [Arquitectura](./docs/ARQUITECTURA.md) - Decisiones arquitectónicas
- [Alcance](./docs/ALCANCE.md) - Formatos y limitaciones
- [Seguridad](./docs/SEGURIDAD.md) - Consideraciones de seguridad
- [Calidad](./docs/CALIDAD.md) - Métricas y criterios
- [Licencias](./docs/LICENCIAS.md) - SBOM y dependencias
- [Progreso](./docs/AVANCE.md) - Estado actual del desarrollo
- [ADRs](./docs/adr/) - Decisiones arquitectónicas registradas

## Fases de Desarrollo

- **F0**: Viabilidad y benchmark (1-2 semanas)
- **F1**: Base segura e infraestructura (1 semana)
- **F2**: Conversión a Excel (2 semanas)
- **F3**: Conversión a Word (2 semanas)
- **F4**: OCR y documentos escaneados (1-2 semanas)
- **F5**: Otros formatos y UX (1 semana)
- **F6**: Operación y piloto (2-3 semanas)

## Estructura de Directorios

```
pdf_converter/
├── apps/
│   ├── api/              # Backend FastAPI
│   ├── worker/           # Procesador Celery
│   └── web/              # Frontend React
├── packages/             # Código compartido
│   ├── document_ir/      # Modelo intermedio
│   ├── converters/       # Motores de conversión
│   └── exporters/        # Exportadores de formato
├── tests/                # Suite de pruebas
├── docs/                 # Documentación
├── infra/                # Scripts de infraestructura
├── benchmarks/           # Suite de benchmark
└── .github/workflows/    # Pruebas opcionales; Actions deshabilitado
```

## Comandos Útiles

```bash
# Ejecutar pruebas
pytest tests/ -v

# Ejecutar benchmark
python benchmarks/runner.py

# Generar cobertura
pytest --cov=apps --cov=packages

# Linting
black apps/ packages/ tests/
isort apps/ packages/ tests/

# Type checking
mypy apps/ packages/

# Generar documentación OpenAPI
python -c "from apps.api.main import app; import json; print(json.dumps(app.openapi(), indent=2))"
```

## Contribución

Por favor leer [CONTRIBUIR.md](./CONTRIBUIR.md) para detalles sobre nuestro proceso de desarrollo.

## Licencia

Ver [LICENCIAS.md](./docs/LICENCIAS.md) para detalles completos de licencias y dependencias.

## Contacto

Proyecto: Conversión PDF a Múltiples Formatos
Responsable: Equipo de Desarrollo
Versión Plan: 1.0.0
Fecha: 2026-10-07
