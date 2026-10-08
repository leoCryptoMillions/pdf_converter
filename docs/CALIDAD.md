# Estrategia de Calidad y Testing

Documento que define la estrategia de testing, métricas de calidad, y criterios de aceptación para el conversor PDF.

**Versión:** 1.0  
**Fecha:** 2026-10-07  
**Última Actualización:** 2026-10-07

## 1. Objetivos de Calidad

1. **Confiabilidad**: Conversiones precisas sin pérdida de datos
2. **Robustez**: Manejo gracioso de PDFs defectuosos o inesperados
3. **Rendimiento**: Procesamiento dentro de límites de tiempo/memoria
4. **Seguridad**: Sin exposición de datos sensibles, sin ejecución maliciosa
5. **Mantenibilidad**: Código limpio, bien documentado, fácil de debuguear
6. **Usabilidad**: Errores claros, recuperación intuitiva

## 2. Pirámide de Testing

```
        /\
       /  \ E2E (5%)
      /----\
     /      \ Integration (25%)
    /--------\
   /          \ Unit (70%)
  /____________\
```

### 2.1 Unit Tests (70%)
**Propósito**: Verificar lógica aislada sin dependencias externas.

**Cobertura**:
- Modelos Pydantic (ValidationError cases)
- Funciones de normalización (regional formats, encoding)
- Validadores de tablas (spans, boundaries)
- Exportadores (type coercion, formula prevention)

**Ejemplo**:
```python
# tests/unit/test_models.py
def test_table_model_validates_spans():
    """Spans no pueden exceder columnas"""
    with pytest.raises(ValidationError):
        Table(
            rows=1, cols=3,
            cells=[Cell(row=0, col=0, col_span=5)]  # Inválido
        )

def test_currency_preservation():
    """Importes se exportan como Decimal, no float"""
    cell = Cell(value="$1,234.56", normalized_value=1234.56)
    exported = export_to_xlsx_cell(cell)
    assert isinstance(exported.value, Decimal)
    assert str(exported.value) == "1234.56"
```

**Ejecución**:
```bash
make test-unit
# o
pytest tests/unit/ -v --cov=apps --cov=packages
```

### 2.2 Integration Tests (25%)
**Propósito**: Verificar interacciones entre componentes (DB, queue, storage).

**Cobertura**:
- Database transactions y migrations
- Celery task idempotence
- Outbox pattern (atomicity)
- Storage upload/retrieval
- API request/response contracts

**Ejemplo**:
```python
# tests/integration/test_conversion_flow.py
@pytest.mark.asyncio
async def test_conversion_task_idempotent(db_session, celery_app):
    """Ejecutar task dos veces con mismo ID no crea duplicados"""
    
    # Primera ejecución
    result1 = convert_pdf_task.apply_async(
        args=(file_id, "xlsx"),
        task_id="unique-id-123"
    )
    result1.wait()
    
    # Segunda ejecución (retry)
    result2 = convert_pdf_task.apply_async(
        args=(file_id, "xlsx"),
        task_id="unique-id-123"
    )
    result2.wait()
    
    # Ambas producen el mismo resultado
    assert result1.get() == result2.get()
    
    # Resultado se publicó solo una vez
    artifacts = db_session.query(Artifact).filter_by(
        conversion_id=conversion_id
    ).all()
    assert len(artifacts) == 1

def test_conversion_database_outbox_atomicity(db_session):
    """Insertar en DB y publicar evento es atómico"""
    
    # Transaction 1: Crear conversión + enviar evento outbox
    with db_session.begin():
        conv = Conversion(file_id="f1", format="xlsx", user_id="u1")
        db_session.add(conv)
        db_session.flush()  # Get conv.id
        
        event = OutboxEvent(entity_id=conv.id, type="conversion_created")
        db_session.add(event)
    
    # Verificar que ambos se guardaron
    assert db_session.query(Conversion).filter_by(id=conv.id).first()
    assert db_session.query(OutboxEvent).filter_by(entity_id=conv.id).first()
```

**Ejecución**:
```bash
make test-integration
# Requiere docker-compose up
```

### 2.3 E2E Tests (5%)
**Propósito**: Verificar flujo completo desde cliente hasta resultado.

**Cobertura**:
- Upload PDF → conversión → descarga
- Flujos de error (PDF corrupto, timeout, cancellación)
- Validación de artefactos (abrir en Excel/Word)

**Ejemplo**:
```python
# tests/e2e/test_conversion_workflow.py
@pytest.mark.e2e
def test_full_conversion_workflow(api_client, sample_pdf_path):
    """Flujo completo: upload → convert → download"""
    
    # 1. Upload
    with open(sample_pdf_path, "rb") as f:
        upload_resp = api_client.post(
            "/v1/files",
            files={"file": f}
        )
    assert upload_resp.status_code == 201
    file_id = upload_resp.json()["file_id"]
    
    # 2. Crear conversión
    conv_resp = api_client.post(
        "/v1/conversions",
        json={"file_id": file_id, "format": "xlsx"}
    )
    assert conv_resp.status_code == 202
    job_id = conv_resp.json()["job_id"]
    
    # 3. Polling estado
    for _ in range(60):  # 60 segundos máximo
        status_resp = api_client.get(f"/v1/conversions/{job_id}")
        if status_resp.status_code == 200:
            state = status_resp.json()["state"]
            if state in ["succeeded", "needs_review", "failed"]:
                break
        time.sleep(1)
    
    assert state in ["succeeded", "needs_review"]
    
    # 4. Download
    download_resp = api_client.get(f"/v1/artifacts/{file_id}/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # 5. Validar integridad
    xlsx_bytes = download_resp.content
    wb = openpyxl.load_workbook(BytesIO(xlsx_bytes))
    assert wb is not None  # Archivo válido
```

**Ejecución**:
```bash
make test-e2e
```

## 3. Testing Específico por Formato

### 3.1 XLSX Testing
```python
# tests/unit/test_xlsx_export.py
def test_formula_injection_prevention():
    """Celdas con fórmulas se exportan como texto"""
    cells = [
        Cell(value="=1+1"),
        Cell(value="@SUM(A1:A10)"),
        Cell(value="+cmd|'/c calc'!A1"),
    ]
    table = Table(rows=3, cols=1, cells=cells)
    
    xlsx_bytes = export_to_xlsx(table)
    wb = openpyxl.load_workbook(BytesIO(xlsx_bytes))
    ws = wb.active
    
    # Todos son texto, no fórmulas
    assert ws['A1'].data_type == 's'  # String
    assert ws['A1'].value == "=1+1"  # Literal text

def test_numeric_type_preservation():
    """Números se exportan con tipos correctos"""
    cells = [
        Cell(value="1234.56", normalized_value=Decimal("1234.56")),
        Cell(value="RFC123456ABC", normalized_value=None),  # Debe quedar texto
        Cell(value="2026-10-07", normalized_value=date(2026, 10, 7)),
    ]
    table = Table(rows=3, cols=1, cells=cells)
    
    xlsx_bytes = export_to_xlsx(table)
    wb = openpyxl.load_workbook(BytesIO(xlsx_bytes))
    ws = wb.active
    
    assert isinstance(ws['A1'].value, Decimal) or ws['A1'].data_type == 'n'
    assert ws['A2'].data_type == 's'  # RFC as text
    assert isinstance(ws['A3'].value, (date, datetime))
```

### 3.2 DOCX Testing
```python
# tests/unit/test_docx_export.py
def test_docx_is_editable():
    """DOCX generado es editable en Word"""
    doc_ir = DocumentIR(
        pages=[
            Page(number=1, text_blocks=[
                TextBlock(value="Título", level=1),
                TextBlock(value="Párrafo 1", level=0),
            ])
        ]
    )
    
    docx_bytes = export_to_docx(doc_ir)
    doc = Document(BytesIO(docx_bytes))
    
    # Validar estructura
    assert len(doc.paragraphs) >= 2
    assert doc.paragraphs[0].style.name == "Heading 1"
    
    # Re-guardar sin cambios debe suceder sin errores
    tmp = BytesIO()
    doc.save(tmp)
    assert tmp.tell() > 0  # Se guardó algo
```

### 3.3 OCR Testing
```python
# tests/integration/test_ocr_quality.py
@pytest.mark.benchmark
def test_ocr_character_error_rate():
    """OCR CER <= 2% en PDFs limpios"""
    ocr_pdf = load_sample_pdf("scanned_clean.pdf")
    extracted = extract_text_ocr(ocr_pdf)
    
    # ground_truth es anotación manual
    ground_truth = load_ground_truth("scanned_clean_truth.txt")
    
    cer = calculate_cer(extracted, ground_truth)
    assert cer <= 0.02  # 2%
    
    # Por página
    for page_num, page_text in extracted.items():
        page_truth = ground_truth[page_num]
        page_cer = calculate_cer(page_text, page_truth)
        assert page_cer <= 0.03  # Permitir 3% por página
```

## 4. Métricas de Calidad

### 4.1 Cobertura de Código
- **Target**: >= 80% (production code)
- **Exclusiones**: Migrations, configs, test fixtures
- **Herramienta**: pytest-cov
- **CI**: Rechazar si cae < 75%

```bash
pytest --cov=apps --cov=packages --cov-report=html
# Abrir htmlcov/index.html para detalle
```

### 4.2 Defects Encontrados

| Tipo | Máximo/Sprint | Severidad | Acción |
|------|---------------|-----------|--------|
| Critical (RCE, data loss) | 0 | Bloquea release | Detener, investigar, patch |
| High (DoS, auth bypass) | <= 1 | Bloquea si no mitigado | Patch inmediato o mitigation |
| Medium (UX, performance) | <= 3 | Registrar, priorizar | Fix en sprint siguiente |
| Low (typos, docs) | Sin límite | Nice-to-have | Backlog |

### 4.3 Performance

| Métrica | Target | Medida |
|---------|--------|--------|
| PDF 10p digital | p95 <= 30s | Desde upload a end |
| PDF 10p OCR | p95 <= 180s | Desde upload a end |
| XLSX export | <= 5s | Desde DocumentIR a bytes |
| Memory peak | <= 500MB | Por tarea (2GB worker limit) |
| CPU utilización | <= 90% | No monopolizar core |

**Benchmark antes de cada release**:
```bash
make benchmark
# Resultados en benchmarks/results/
```

### 4.4 Availability

| Componente | Target | Alertas |
|-----------|--------|--------|
| API | 99.5% | Si down > 5 min |
| Worker | 99% | Si job failure rate > 5% |
| Database | 99.9% | Si latencia > 1s |
| Queue | 99% | Si messages_pending > 1000 |

## 5. Ciclo de Testing

### 5.1 Pre-Commit
```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/isort
    hooks:
      - id: isort
  - repo: https://github.com/PyCQA/flake8
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

Instalar:
```bash
pre-commit install
pre-commit run --all-files  # Manual check
```

### 5.2 CI Pipeline (.github/workflows/tests.yml)

GitHub Actions deshabilitado en el repositorio por solicitud del usuario
(2026-10-08). El workflow se conserva para uso opcional y su disparador local
es únicamente `workflow_dispatch`; requiere reactivar Actions para ejecutarlo.
No hay despliegues ni requisitos de checks en la rama `master` al revisar
esta configuración. Las pruebas locales siguen disponibles.

El archivo conservado instala dependencias, levanta PostgreSQL y Redis como
servicios temporales, ejecuta flake8, mypy, black y pytest con cobertura, y
envía cobertura a Codecov. mypy y black no bloquean por sus `|| true`.
No implementa los pasos de seguridad o umbral de cobertura antes descritos.

```bash
# Simular CI localmente
make quality
make test-coverage
```

### 5.3 Release Checklist

Antes de publicar a producción:

```
[ ] Pruebas de la versión pasando localmente (CI opcional)
[ ] Cobertura >= 80%
[ ] Seguridad: No findings críticos/altos abiertos
[ ] Documentación: README, ADRs, AVANCE.md actualizados
[ ] Dependencias: Auditadas, sin vulnerabilidades conocidas
[ ] Performance: Benchmarks ejecutados, dentro de targets
[ ] Rollback: Plan documentado y probado
[ ] Capacitación: Team comprende cambios
```

## 6. Herramientas y Configuración

### 6.1 Pytest Config (pytest.ini)
```ini
[pytest]
minversion = 7.0
testpaths = tests
pythonpath = .
markers =
    unit: unit tests
    integration: integration tests
    e2e: end-to-end tests
    security: security tests
    benchmark: performance tests
    asyncio: async tests
```

### 6.2 Fixture Compartidas (tests/conftest.py)
```python
@pytest.fixture
def sample_pdf_digital():
    """PDF digital con tablas y texto"""
    return open("tests/fixtures/sample_digital.pdf", "rb")

@pytest.fixture
def db_session():
    """Sesión transaccional para tests"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()

@pytest.fixture
def celery_app():
    """Celery en modo eager para tests"""
    app = Celery()
    app.conf.task_always_eager = True
    return app
```

## 7. Monitoreo en Producción

### 7.1 Métricas Críticas
- Error rate (% de conversiones fallidas)
- P95 latency (tiempo de conversión)
- Queue depth (trabajos pendientes)
- Memory usage (worker peak)
- Disk usage (almacenamiento)

### 7.2 Alertas
```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 5%
    action: page_oncall
  
  - name: QueueBacklog
    condition: queue_depth > 1000 and age_oldest > 5min
    action: scale_workers
  
  - name: DiskFull
    condition: disk_usage > 90%
    action: trigger_cleanup
```

### 7.3 SLI/SLO
```
SLI: Availability = (successful_conversions / total_conversions) * 100
SLO: >= 99% en ventana de 30 días

SLI: Latency p95 = percentile(conversion_time, 95)
SLO: <= 60 segundos (digital) o <= 180 segundos (OCR)
```

## 8. Mejora Continua

### 8.1 Post-Mortem de Defectos
Cuando se encuentra un defecto crítico:
1. Documentar síntomas, impacto, duración
2. Determinar root cause
3. Crear test que reproduzca
4. Implementar fix
5. Actualizar documentación
6. Share learnings con equipo

### 8.2 Metrics Review (semanal)
- Test execution time
- Coverage trends
- Defect arrival rate
- Performance trends

### 8.3 Testing Strategy Review (trimestral)
- Casos de prueba obsoletos
- Cobertura en áreas críticas
- Nuevos riesgos identificados
- Herramientas o técnicas mejoradas

## 9. Referencias y Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [ISTQB Testing Levels](https://www.istqb.org/)
- [Google Testing Blog](https://testing.googleblog.com/)

**Próxima Revisión:** 2026-12-07 (después de F1)
