# Seguridad y Privacidad

Documento que especifica el modelo de seguridad del conversor PDF, amenazas identificadas, controles implementados y procedimientos de validación.

**Versión:** 1.0  
**Fecha:** 2026-10-07  
**Última Actualización:** 2026-10-07

## 1. Principios de Seguridad

1. **Defensa en profundidad**: Múltiples capas de control; ninguna es suficiente por sí sola
2. **Least Privilege**: Procesos, usuarios y credenciales con mínimos permisos necesarios
3. **Fail Secure**: Ante duda, denegar; no asumir que un archivo es válido por defecto
4. **Aislamiento**: PDFs sin confianza se procesan en procesos aislados, sin acceso a secretos
5. **No Confiar en Entrada**: Nombres de archivo, MIME type, metadatos de usuarios son no confiables
6. **Transparencia**: El usuario ve limitaciones, advertencias y decisiones de la conversión
7. **Cumplimiento**: Respetar regulación local de privacidad (GDPR, LGPD, etc.)

## 2. Amenazas y Controles

### 2.1 Parseo de PDF Malicioso

**Amenaza**: PDF crafted para explotar vulnerabilidades en pdfplumber, Tesseract, o dependencias.

**Impacto**: RCE, DoS, fuga de información.

**Controles**:
- [x] Parser ejecuta en proceso worker separado (no en API)
- [x] Límites de recursos: CPU, memoria, timeout por página
- [x] Sandboxing: Procesos sin root, sin red, /tmp efímero
- [x] Dependencias versionadas y auditadas; CVE monitoring
- [x] Validación previa: Magic bytes (PDF signature), estructura básica

**Verificación**:
```bash
# Tests de seguridad
pytest tests/security/test_pdf_parsing.py -v

# Simulación de archivos malformados
python scripts/test_security_pdfs.py
```

### 2.2 Traversal de Directorios

**Amenaza**: PDF con nombre `../../etc/passwd` u otro camino relativo.

**Impacto**: Lectura/escritura de archivos fuera de la quarantine.

**Controles**:
- [x] Nombres de archivo generados por servidor (UUID + timestamp)
- [x] Caminos validados antes de cada operación (no relativos)
- [x] Storage privado con ACLs (S3 con bucket policy)
- [x] Permisos POSIX restrictivos: archivos 0600, directorios 0700

**Verificación**:
```python
# Ejemplos en tests/security/
assert not os.path.isabs(user_filename)  # Never trust user input
storage_path = f"{SECURE_UPLOAD_DIR}/{uuid.uuid4()}.pdf"
assert os.path.abspath(storage_path).startswith(SECURE_UPLOAD_DIR)
```

### 2.3 Inyección de Fórmulas (CSV/XLSX)

**Amenaza**: Texto `=cmd|'/c calc'!A1` en PDF se exporta a XLSX sin escape.

**Impacto**: Ejecución de comandos al abrir archivo en Excel/Calc.

**Controles**:
- [x] Exportador XLSX: openpyxl crea celdas como tipo text, no formula
- [x] Exportador CSV: Celdas con `=`, `+`, `@`, `-` se escapan o prefijan (RFC 4180 + OWASP)
- [x] Testing específico: Suite de PDFs con fórmulas intentadas
- [x] Documentación: Advertir que algunos programas pueden reinterpretar al guardar

**Verificación**:
```python
# tests/security/test_formula_injection.py
def test_formula_not_interpreted_in_xlsx(tmp_path):
    # PDF con "=1+1" en celda
    xlsx_file = export_to_xlsx(sample_pdf, tmp_path)
    
    # Leer con openpyxl, validar que es texto, no fórmula
    wb = load_workbook(xlsx_file)
    cell = wb.active['A1']
    assert cell.value == "=1+1"  # Texto literal
    assert cell.data_type == 's'  # String type
```

### 2.4 Fuga de Información Sensible en Logs

**Amenaza**: Contenido PDF (números de cuenta, secretos) logged en texto plano.

**Impacto**: Exposición en logs centralizados, backups, rotaciones.

**Controles**:
- [x] structlog con filtros para sanitizar contenido
- [x] Nunca loguear: texto de PDF, celdas, metadatos completos, contraseñas
- [x] Sí loguear: file_id (hash), fases de procesamiento, errores técnicos
- [x] Logs encriptados en reposo; acceso limitado a ops

**Ejemplos de logs válidos:**
```python
log.info("pdf_parsed", file_hash=sha256_file, pages=50, engine="pdfplumber")
log.warning("extraction_low_quality", page=1, text_coverage=0.2)

# NO:
# log.info("content_found", text="CLABE:......")
# log.debug("user_pdf", content=pdf_bytes)
```

### 2.5 Denegación de Servicio (DoS)

**Amenaza**: Usuario sube PDF de 1 GB o con 1000 páginas.

**Impacto**: Exhaust RAM, CPU, almacenamiento; afecta otros usuarios.

**Controles**:
- [x] Límites en API: tamaño máximo 25 MB, páginas máximo 100 (configurable)
- [x] Límites en worker: memory cap, CPU time cap (via cgroups, ulimit)
- [x] Backpressure: Rechazar si cola > threshold
- [x] Per-user quotas: Páginas/mes, conversiones concurrentes

**Verificación**:
```bash
# Simular carga
pytest tests/security/test_dos.py -v

# Manual: cargar PDF de 1 GB, debe ser rechazado
curl -F "file=@huge.pdf" http://localhost:8000/v1/files
# Esperado: 413 Payload Too Large
```

### 2.6 Validación Incorrecta de Permisos

**Amenaza**: Usuario A accede a conversión de Usuario B.

**Impacto**: Fuga de PDFs, resultados de otros usuarios.

**Controles**:
- [x] user_id obligatorio en toda consulta (nunca confiar solo en job_id)
- [x] Middleware valida JWT/session en cada request
- [x] Tests de separación: intentos cruzados deben fallar
- [x] Auditoría: Log de accesos denegados

**Verificación**:
```python
# tests/security/test_access_control.py
def test_user_cannot_access_other_user_conversion(client_user_a, client_user_b):
    conv_id = create_conversion(client_user_a, sample_pdf)
    response = client_user_b.get(f"/v1/conversions/{conv_id}")
    assert response.status_code == 403  # Forbidden
```

### 2.7 Limpieza Incompleta de Archivos Temporales

**Amenaza**: PDFs sin convertir quedan en /tmp después de errores o expiraciones.

**Impacto**: Acumulación de archivos sensibles; espacio agotado; recuperación accidental.

**Controles**:
- [x] Carpeta efímera por conversión (path uniqueness)
- [x] finally block garantiza cleanup incluso en exception
- [x] Task de limpieza nocturna busca huérfanos > 24h
- [x] Verificación: archivos borrados antes de finalizar result
- [x] Pruebas de race conditions (simultánea cleanup y result publish)

**Verificación**:
```python
# tests/security/test_cleanup.py
def test_temp_files_deleted_after_conversion(tmp_path):
    temp_dir = tmp_path / "job_123"
    temp_dir.mkdir()
    (temp_dir / "input.pdf").write_text("fake")
    
    # Procesar y verificar cleanup
    convert_pdf(temp_dir)
    
    assert not temp_dir.exists()  # Must be deleted
```

## 3. Gestión de Credenciales y Secretos

**Política**:
- Todas las credenciales en variables de entorno, no en código
- No commitear .env o secrets en git
- Use `.env.example` como plantilla sin valores
- Rotar secretos después de exposición
- Secret manager en producción (AWS Secrets Manager, Vault, etc.)

**Verificación**:
```bash
# Pre-commit hook
git diff --cached | grep -i "password\|secret\|key" && exit 1
```

## 4. Autenticación y Autorización

### 4.1 Autenticación
- **Mecanismo**: JWT con OIDC provider (Auth0, Cognito, Keycloak) o sesiones seguras
- **Token Lifespan**: 1 hora (acceso); 7 días (refresh)
- **Cookie Security**: HttpOnly, Secure, SameSite=Strict (en HTTPS)
- **CSRF Protection**: Cuando se usen cookies (tokens en body/header son CORS-safe)

### 4.2 Autorización
- **Por Recurso**: Validar user_id + resource ownership en cada operación
- **Roles**: Admin (RBAC) para operaciones de sistema (cuotas, auditoría); otros usuarios son "standard"
- **Scope**: Tokens pueden incluir alcance (ej: "read:files", "write:conversions")

## 5. Criptografía y TLS

### 5.1 En Tránsito
- [x] TLS 1.2+ obligatorio en producción
- [x] Certificados válidos (no self-signed en prod)
- [x] HSTS header: `Strict-Transport-Security: max-age=31536000`

### 5.2 En Reposo
- [x] PostgreSQL: Cifrado a nivel de volumen o aplicación (pgcrypto)
- [x] S3/Object Store: Cifrado por defecto (SSE-S3 o SSE-KMS)
- [x] Archivos temporales: No necesariamente cifrados si en /tmp del worker (aislado)

## 6. API Security (OWASP Top 10)

| Riesgo | Control |
|--------|---------|
| A01: Broken Access Control | Validar user_id en cada request |
| A02: Cryptographic Failures | TLS + datos sensibles encrypted at rest |
| A03: Injection | Input validation (Pydantic), parameterized queries (SQLAlchemy) |
| A04: Insecure Design | Separación de confianza, aislamiento de procesos |
| A05: Security Misconfiguration | Checklist de hardening, no exposición de errores |
| A06: Vulnerable Components | Dependencias versionadas, CVE monitoring |
| A07: Authentication Failures | JWT + session management validado |
| A08: Data Integrity Failures | Outbox pattern, idempotence keys, transaccionabilidad |
| A09: Logging & Monitoring Failures | structlog + alerts; auditoría de accesos |
| A10: SSRF | No carga por URL en MVP; validar si se agrega |

## 7. Procesamiento Seguro de PDF

### 7.1 Validación Inicial
```python
def validate_pdf(file_bytes: bytes) -> bool:
    # Magic bytes: %PDF
    if not file_bytes.startswith(b'%PDF'):
        raise InvalidPDFError("Not a PDF file")
    
    # Tamaño
    if len(file_bytes) > MAX_SIZE:
        raise FileTooLargeError(f"Max {MAX_SIZE} bytes")
    
    # Intentar parsear cabecera
    try:
        parser = PDFParser(file_bytes)
        parser.parse_header()  # Lightweight validation
    except Exception as e:
        raise InvalidPDFError(f"Malformed PDF: {str(e)}")
    
    return True
```

### 7.2 Aislamiento de Procesos
```bash
# Dockerfile.worker
FROM python:3.11-slim

# Sin root, sin networking, sin acceso a sistema
RUN useradd -m -u 1000 pdfworker
USER pdfworker

# Limits via cgroups (docker) o ulimit
# memory: 2GB max per task
# cpu-shares: 512 (relative)
# disk: mount /tmp as tmpfs, 1GB max
```

### 7.3 Manejo de PDFs Protegidos
- **Contraseña**: Solicitar al usuario si es necesaria; nunca persistir
- **Cifrado**: Detectar y informar al usuario; no intentar romper
- **Firmas**: Informar si se detectan; conversión invalida la firma
- **Scripts/Adjuntos**: No ejecutar; informar presencia y no incluir

## 8. Auditoría y Cumplimiento

### 8.1 Eventos Auditados
- [x] Creación de conversión (usuario, formato, archivo hash)
- [x] Acceso a resultado (usuario, descarga, IP)
- [x] Eliminación y expiración (automática vs manual)
- [x] Cambios de configuración (cuotas, políticas)

### 8.2 Retención de Datos
- **PDFs originales**: Hasta 24h (configurable por org)
- **Resultados**: Hasta 24h (configurable)
- **Logs de auditoría**: 90 días mínimo (compliance)
- **Borrado verificable**: Script de auditoría comprueba que no hay "huérfanos"

## 9. Checklist de Hardening

Ejecutar antes de cada release a producción:

```bash
# Security checklist
□ Todas las secretos en env, no en código
□ CORS restrictivo (solo dominios permitidos)
□ Errores no exponen detalles internos
□ Rate limiting activado (100 req/min por IP)
□ TLS 1.2+ único protocolo soportado
□ Certificados válidos, HSTS header presente
□ Todos los tests de seguridad pasando
□ Dependencias auditadas (pip-audit)
□ Database backups encriptados
□ Logs centralizados y protegidos
□ Monitoreo de anomalías activado
□ Runbook de incidente de seguridad listo
```

## 10. Respuesta a Incidentes

### 10.1 Sospecha de Brecha
1. **Contener**: Aislar sistema afectado (detener procesos si necesario)
2. **Investigar**: Revisar logs en último período (24h)
3. **Notificar**: Alertar a responsables técnicos
4. **Remediar**: Aplicar parche, rotar secretos, actualizar logs

### 10.2 Línea de Reporte
- Responsable de seguridad: TBD
- Escalada ejecutiva: TBD
- Consultor legal: TBD (si fuga de datos)

## 11. Educación y Entrenamiento

- [ ] Todos los desarrolladores leen este documento
- [ ] Code reviews incluyen consideraciones de seguridad
- [ ] Pruebas de seguridad en CI/CD (SAST, dependency scan)
- [ ] Penetration testing anual (antes de publicación a producción)

## 12. Referencias

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [OWASP Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

**Próxima Revisión:** 2026-12-07 (después de piloto)
