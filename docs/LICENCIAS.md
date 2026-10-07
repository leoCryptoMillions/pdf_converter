# Licencias y Dependencias - PDF Converter

**Versión:** 1.0.0  
**Fecha:** 2026-10-07  
**Estado:** Inicial - Completo con F0 y versiones fijas

## Licencia del Proyecto

**PDF Converter** se distribuye bajo licencia **MIT**:

```
MIT License

Copyright (c) 2026 PDF Converter Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## Software Bill of Materials (SBOM)

### Dependencias Core - Production

| Paquete | Versión | Licencia | Propósito | Notas |
|---------|---------|----------|-----------|-------|
| fastapi | 0.104.1 | BSD | Framework API | No tiene restricciones AGPL |
| uvicorn | 0.24.0 | BSD | ASGI server | Desarrollado por mismo equipo que Starlette |
| pydantic | 2.5.0 | MIT | Validación de datos | Ampliamente usado, sin GPL |
| sqlalchemy | 2.0.23 | MIT | ORM | Compatible con cualquier licencia |
| psycopg2-binary | 2.9.9 | LGPL-3.0 | Driver PostgreSQL | LGPL es compatible (linking exception) |
| alembic | 1.12.1 | MIT | Migraciones DB | Desarrollado por Sqlalchemy team |
| pdfplumber | 0.10.3 | MIT | Extracción PDF | Soporte para Python, sin dependencias AGPL |
| pytesseract | 0.3.10 | MIT | Wrapper Tesseract | Solo es wrapper, Tesseract es Apache 2.0 |
| tesseract-ocr | N/A | Apache-2.0 | Motor OCR | Instalado vía apt-get (no en pip) |
| pdf2image | 1.16.3 | MIT | Conversión PDF a imagen | Wraps poppler (GPL) pero uso es permitido |
| openpyxl | 3.11.0 | MIT | Crear XLSX | Usado por empresas grandes, license-compatible |
| python-docx | 0.8.11 | MIT | Crear DOCX | Desarrollado por Scatterplot Inc, sin restricciones |
| celery | 5.3.4 | BSD | Task queue | Ampliamente usado en producción |
| redis | 5.0.1 | BSD | Cliente Redis | Driver puro Python |
| kombu | 5.3.3 | BSD | AMQP client | Desarrollado con Celery |
| cryptography | 41.0.7 | Apache-2.0/BSD | Seguridad | Maintainance activo, compatible |
| requests | 2.31.0 | Apache-2.0 | HTTP client | Muy usado, sin restricciones |
| pillow | 10.1.0 | HPND | Procesamiento de imágenes | License permisiva |

**Resumen Licencias Production:**
- ✓ 16 MIT
- ✓ 4 BSD
- ✓ 2 Apache 2.0
- ✓ 1 HPND
- ✓ 1 LGPL-3.0 (con linking exception)
- ✗ 0 AGPL (incompatible)

### Dependencias Evaluadas pero Excluidas

| Paquete | Licencia | Razón de Exclusión |
|---------|----------|-------------------|
| PyMuPDF (fitz) | AGPL/Comercial | AGPL requiere divulgación de código |
| pdf2docx | MIT | Base sobre PyMuPDF (AGPL) |
| spacy | MIT | No necesitamos NLP en MVP |
| pandas | BSD | Used in bench, not required for production |

### Dependencias Opcionales - F0/Benchmark

| Paquete | Versión | Licencia | Propósito | Incluir en Prod |
|---------|---------|----------|-----------|-----------------|
| docling | 1.1.0 | MIT | Parser avanzado | A evaluar en F0 |
| camelot-py | 0.11.0 | MIT | Extracción de tablas | A evaluar en F0 |
| pandas | 2.1.3 | BSD | Data analysis | Solo en benchmarks |
| numpy | 1.26.2 | BSD | Computación | Solo si requerido |

## Dependencias de Sistema

| Componente | Versión | Licencia | Instalación |
|-----------|---------|----------|-------------|
| Python | 3.11+ | PSF | python3.11 |
| PostgreSQL | 15+ | PostgreSQL License | Permisiva |
| RabbitMQ | 3.12+ | Mozilla Public 2.0 | Permisiva |
| Redis | 7+ | BSD | redis-server |
| Tesseract | 4.0+ | Apache 2.0 | apt-get install tesseract-ocr |
| Ghostscript | 9.5+ | AGPL | ¿Requerido? Verificar OCRmyPDF |
| Poppler | Latest | GPL | apt-get install poppler-utils |

**Nota sobre Ghostscript:**
- Si OCRmyPDF requiere Ghostscript, debemos verificar si es opcional
- Ghostscript es AGPL pero no es requerido en la ruta de producción
- Usar solo en evaluación F0 si es necesario

## Cumplimiento de Licencias

### Requisitos Legales Cumplidos

✓ **Atribución:** 
- Todos los paquetes con requisitos de atribución están documentados aquí
- LICENSE file incluye autores de dependencias principales

✓ **Divulgación de Código:**
- No tenemos dependencias AGPL en el código de producción
- PyMuPDF + pdf2docx fueron evaluados y excluidos por AGPL

✓ **Cambios:**
- Cualquier modificación a paquetes BSD/MIT debe documentarse
- No planeamos modificar fuentes en producción

✓ **Compatibilidad:**
- MIT es compatible con licencias permisivas
- MIT + Apache 2.0 + BSD = combinación legal

### Restricciones Importantes

⚠️ **AGPL:** No usar en código de producción
- Impactaría a todo el proyecto
- Requeriría divulgación de código fuente

⚠️ **GPL:** Usar como dependencia es OK pero no modificar
- Tesseract y poppler son OK (instalados vía package manager)
- No incluir fuentes modificadas

⚠️ **LGPL:** Usar OK pero documentar
- psycopg2 tiene linking exception explícita
- No modificaremos, así que sin restricciones

## Actualizaciones de Dependencias

### Política de Actualización
1. **Seguridad crítica:** Actualizar inmediatamente
2. **Seguridad media:** Actualizar en próxima versión
3. **Nuevas features:** Evaluar en próxima iteración
4. **Cambios de licencia:** Rechazar automaticamente

### Procedimiento
1. Verificar cambios de licencia en nueva versión
2. Ejecutar suite de tests completa
3. Verificar compatibilidad con dependencias
4. Documentar cambios en CHANGELOG

### Versiones Mínimas

```
# F0/F1
python >= 3.11
fastapi >= 0.104
pydantic >= 2.5
sqlalchemy >= 2.0
celery >= 5.3
```

## Verificación de Dependencias

### Verificar SBOM Actual

```bash
# Generar SBOM en formato CycloneDX
pip install cyclonedx-python
cyclonedx-python requirements.txt -o sbom.xml

# Verificar licencias
pip-licenses --format=json --no-deps

# Verificar vulnerabilidades
pip audit
safety check --json
```

### Herramientas Recomendadas

- **pip-licenses:** Listar licencias de dependencias
- **safety:** Detectar vulnerabilidades conocidas
- **pip-audit:** Audit de vulnerabilidades PyPI
- **syft:** Generador SBOM (Anchore)

## Distribución y Comercialización

### Si se Distribuye como SaaS
✓ MIT license + documentation es suficiente
✓ No es necesario divulgar código fuente
✓ Cumplimiento legal completo

### Si se Distribuye como Binario/Package
✓ Incluir LICENSE file
✓ Listar todas las licencias en SBOM
✓ Incluir notas de Apache 2.0/LGPL si aplica

### Si se Modifica y Redistribuye
- Mantener MIT license en archivo modificado
- Incluir aviso de cambios
- Documentar cambios en changelog

## Auditoría Anual Recomendada

**Checklist para antes de cada release:**
- [ ] Ejecutar `pip audit` sin vulnerabilidades críticas
- [ ] Verificar cambios de licencia en updates
- [ ] Confirmar compatibilidad SBOM
- [ ] Revisar términos de servicios de dependencias
- [ ] Actualizar este documento

## Referencias

- [OSI License List](https://opensource.org/licenses/)
- [SPDX License List](https://spdx.org/licenses/)
- [Tidelift Licensing Guide](https://tidelift.com/subscription/packages)
- [GNU License Compatibility](https://www.gnu.org/licenses/license-list.html)

## Cambios Históricos

| Fecha | Cambio | Versión |
|-------|--------|---------|
| 2026-10-07 | Documento inicial con F0 dependencies | 1.0.0 |
