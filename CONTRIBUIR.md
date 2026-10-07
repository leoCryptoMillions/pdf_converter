# Guía de Contribución - PDF Converter

Gracias por tu interés en contribuir a PDF Converter. Este documento describe el proceso de desarrollo y las expectativas de calidad.

## Principios de Desarrollo

1. **Calidad sobre Velocidad:** Código revisable y mantenible
2. **Seguridad Primero:** Validación y aislamiento en todos los niveles
3. **Documentación Incluida:** Código auto-documentado + docs externas
4. **Tests Requeridos:** Cobertura >= 70% para cualquier cambio
5. **Auditoría de Cambios:** Todas las decisiones registradas

## Setup del Ambiente de Desarrollo

### Requisitos Previos
```bash
Python 3.11+
Docker & Docker Compose
Node.js 18+ (para frontend, opcional)
Git
```

### Instalación

```bash
# Clonar repositorio
git clone <repo>
cd pdf_converter

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copiar configuración
cp .env.example .env

# Iniciar servicios
docker-compose up -d

# Ejecutar migraciones (cuando exista schema)
# alembic upgrade head

# Iniciar API
cd apps/api
uvicorn main:app --reload
```

## Estructura del Código

```
apps/
  ├── api/              # Backend FastAPI
  │   ├── main.py       # Application factory
  │   ├── config.py     # Configuration
  │   ├── routes/       # API endpoints
  │   ├── schemas.py    # Pydantic models
  │   └── middleware/   # Middleware customizado
  │
  ├── worker/           # Celery tasks
  │   ├── config.py     # Celery configuration
  │   └── tasks.py      # Task definitions
  │
  └── web/              # React frontend (separado)

packages/
  ├── document_ir/      # Document Intermediate Representation
  │   ├── models.py     # Pydantic models
  │   └── validators.py # Custom validators
  │
  ├── converters/       # PDF parsing engines
  │   ├── base.py       # Abstract converter
  │   └── engines/      # Concrete implementations
  │
  └── exporters/        # Format exporters
      ├── base.py       # Abstract exporter
      ├── xlsx.py       # Excel export
      └── docx.py       # Word export

tests/
  ├── unit/             # Unit tests (sin dependencias)
  ├── integration/      # Integration tests (con DB/broker)
  ├── e2e/              # End-to-end tests
  └── conftest.py       # Shared fixtures
```

## Estándares de Código

### Python

**Formato:**
```bash
# Black - Formatting
black apps/ packages/ tests/

# isort - Import sorting
isort apps/ packages/ tests/

# flake8 - Linting
flake8 apps/ packages/ tests/
```

**Type Hints:**
```python
from typing import List, Optional, Dict, Any

def process_document(
    document_id: str,
    options: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Process a document and return results."""
    pass
```

**Docstrings:**
```python
def extract_tables(pdf_path: str) -> List[Table]:
    """
    Extract tables from PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of Table objects with content
        
    Raises:
        FileNotFoundError: If PDF doesn't exist
        CorruptedPDFError: If PDF is corrupted
    """
    pass
```

### Git

**Commits:**
```
[type] subject

Description of why this change is needed.
More details if necessary.

Fixes #123
```

**Types:**
- `feat:` Nueva feature
- `fix:` Bug fix
- `docs:` Cambios de documentación
- `style:` Formatting (no lógica)
- `refactor:` Reorganizar código
- `perf:` Optimización de performance
- `test:` Tests nuevos o mejorados
- `chore:` Build, deps, etc

**Ejemplo:**
```
feat: Add table correction UI component

Implements interactive table editor allowing users to:
- Edit cell content
- Add/remove rows
- Fix column headers
- Preview changes before export

Closes #42
```

**Branches:**
- `main` - Production-ready
- `develop` - Integration branch
- `feature/<nombre>` - Nueva feature
- `fix/<nombre>` - Bug fix
- `docs/<nombre>` - Documentation

## Testing

### Ejecutar Tests Localmente

```bash
# Todos los tests
pytest tests/ -v

# Específica categoría
pytest tests/unit -v
pytest tests/integration -v
pytest tests/e2e -v

# Con cobertura
pytest tests/ --cov=apps --cov=packages --cov-report=html

# Solo tests rápidos (no slow)
pytest tests/ -m "not slow"
```

### Escribir Tests

**Unit Test Example:**
```python
import pytest
from packages.document_ir.models import Cell, DataType

def test_cell_creation():
    """Test creating a cell with valid data"""
    cell = Cell(
        content="123.45",
        data_type=DataType.DECIMAL,
        row_index=0,
        col_index=0,
        extraction_method="direct",
    )
    
    assert cell.content == "123.45"
    assert cell.data_type == DataType.DECIMAL
```

**Integration Test Example:**
```python
@pytest.mark.integration
async def test_create_conversion_job(client, db_session):
    """Test creating a conversion job via API"""
    response = await client.post(
        "/v1/conversions",
        json={
            "format": "xlsx",
            "filename": "test.pdf",
        },
    )
    
    assert response.status_code == 202
    assert "job_id" in response.json()
```

### Requisitos de Cobertura

- ✓ >= 70% cobertura general
- ✓ 100% de funciones críticas (validación, conversión)
- ✓ 95% de converters/exporters
- ✓ 80% de utils

No pasar PR si:
- [ ] Cobertura baja (<70%)
- [ ] Tests rotos
- [ ] Linting falla

## Revisar y Mergear

### Checklist Antes de PR

- [ ] Branch actualizado con `main`
- [ ] Tests pasan localmente
- [ ] Cobertura >= 70%
- [ ] `black`, `isort`, `flake8` pasan
- [ ] `mypy` sin errores críticos
- [ ] Documentación actualizada
- [ ] CHANGELOG actualizado
- [ ] No hay secretos en commits

### Process de PR

1. **Crear PR** con descripción clara
2. **CI pasa** (tests, linting, coverage)
3. **Code review** de maintainer
4. **Cambios solicitados** se implementan
5. **Aprobación** antes de merge
6. **Squash & merge** a `develop`
7. **Release** en `main` cuando se cumple

### Criterios de Aprobación

- ✓ Funcionalidad correcta
- ✓ Tests comprehensivos
- ✓ Código legible y documentado
- ✓ Sin regresiones
- ✓ Performance aceptable
- ✓ Cumple decisiones de diseño

## Release Process

### Versioning

Usar Semantic Versioning: `MAJOR.MINOR.PATCH`

- `MAJOR:` Cambios incompatibles
- `MINOR:` Nuevas features (compatible)
- `PATCH:` Bug fixes

### Release Checklist

```bash
# 1. Actualizar version en código
# apps/api/config.py: APP_VERSION
# packages/document_ir/__init__.py: __version__

# 2. Actualizar CHANGELOG.md

# 3. Tag en git
git tag v1.0.1
git push origin v1.0.1

# 4. Build Docker images
docker build -t pdf-converter:1.0.1 -f infra/docker/Dockerfile.api .

# 5. Push a registry (futuro)
# docker push registry/pdf-converter:1.0.1

# 6. Create GitHub Release
# gh release create v1.0.1 --notes "Release notes..."
```

## Documentación

### Mantener Actualizado

- **README.md**: Información general, quick start
- **docs/ARQUITECTURA.md**: Decisiones técnicas
- **docs/ALCANCE.md**: Features y limitaciones
- **docs/LICENCIAS.md**: Dependencies
- **docs/AVANCE.md**: Estado actual
- **docs/adr/**: Architectural Decision Records

### ADR - Decisiones Importantes

Cuando tomes una decisión arquitectónica importante:

```bash
# Crear nuevo ADR
cp docs/adr/template.md docs/adr/0005-your-decision.md
```

**Estructura ADR:**
```markdown
# ADR NNNN: Title

**Date:** YYYY-MM-DD
**Status:** Accepted/Pending/Deprecated
**Deciders:** Names

## Context
Problema a resolver

## Decision
Solución elegida

## Rationale
Porqué esta solución

## Alternatives Considered
Opciones rechazadas y porqué

## Consequences
Impacto positivo y negativo

## References
Links relevantes
```

## Performance y Optimización

### Benchmarking

```bash
# Ejecutar benchmark suite
python benchmarks/runner.py

# Benchmarks específicos
python benchmarks/runner.py --pdf sample.pdf --engine pdfplumber
```

### Perfilado

```bash
# Memory profiling
python -m memory_profiler apps/worker/tasks.py

# Time profiling
python -m cProfile -s cumulative apps/api/main.py
```

## Seguridad

### Reportar Vulnerabilidades

⚠️ **NO** reportar en issues públicas.

Contactar al equipo de seguridad privadamente:
- Email: [security contact]
- PGP Key: [key] 

### Auditoría de Seguridad

```bash
# Escanear dependencias
pip audit

# Verificar secretos no commitidos
git secrets scan

# Análisis de seguridad Python
bandit -r apps/ packages/
```

## Mejora Continua

### Reporte Bugs

1. Verificar que no existe issue similar
2. Crear issue con título descriptivo
3. Incluir:
   - Versión de código
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Logs relevantes

### Sugerir Features

1. Discutir en issue primero
2. Verificar que está en roadmap
3. Si no: crear issue con etiqueta `enhancement`
4. Describir use case y valor propuesto

## Contacto

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Security:** [security contact]
- **General:** [team email]

---

**Gracias por contribuir a PDF Converter!**
