# Runbook Operacional

Guía de procedimientos para operación, troubleshooting y respuesta a incidentes del conversor PDF.

**Versión:** 1.0  
**Fecha:** 2026-10-07  
**Audience**: Operators, DevOps, On-Call Engineers

## 1. Verificación de Salud del Sistema

### 1.1 Check Rápido (5 minutos)

```bash
# 1. API disponible
curl -s http://localhost:8000/health | jq .

# Expected output:
# {
#   "status": "healthy",
#   "version": "0.1.0",
#   "timestamp": "2026-10-07T10:30:00Z"
# }

# 2. Base de datos
docker-compose exec postgres psql -U postgres -d pdf_converter -c "SELECT COUNT(*) FROM conversions;"

# 3. RabbitMQ
curl -s http://guest:guest@localhost:15672/api/vhosts | jq .

# 4. Worker activo
docker-compose logs worker | grep "started with concurrency" | tail -1

# 5. Cola de procesamiento
docker-compose exec rabbitmq rabbitmq-diagnostics queue_info -p /

# Si todo es OK: ✓ Sistema operacional
# Si algo falla: → Ver sección de troubleshooting
```

### 1.2 Dashboards de Monitoreo

**Prometheus**: http://localhost:9090 (si está configurado)
- Métricas clave: `conversion_duration_seconds`, `conversion_errors_total`, `queue_depth`

**Grafana**: http://localhost:3000 (opcional, si configurado)
- Dashboard: "PDF Converter Overview"

**RabbitMQ Management**: http://localhost:15672
- User: `guest` / Password: `guest`
- Revisar "Queues" → `pdf_conversions` (depth, rates)

## 2. Operaciones Comunes

### 2.1 Reiniciar Componentes

```bash
# Reiniciar API
docker-compose restart api

# Reiniciar Worker
docker-compose restart worker

# Reiniciar Beat (scheduler)
docker-compose restart beat

# Reiniciar todos
docker-compose restart

# Reiniciar + forzar rebuild (después de cambios)
docker-compose down && docker-compose up -d
```

### 2.2 Ver Logs en Tiempo Real

```bash
# Todos los servicios
docker-compose logs -f

# Solo API
docker-compose logs -f api

# Solo Worker
docker-compose logs -f worker

# Últimas 100 líneas
docker-compose logs --tail=100 api

# Con timestamps
docker-compose logs --timestamps api

# Filtrar por palabra clave
docker-compose logs api | grep "error"
```

### 2.3 Ejecutar Comandos en Contenedores

```bash
# Bash en el contenedor API
docker-compose exec api bash

# Python interactivo en API
docker-compose exec api python

# Ejecutar script en worker
docker-compose exec worker python scripts/cleanup.py

# SQL directo en PostgreSQL
docker-compose exec postgres psql -U postgres -d pdf_converter -c "SELECT * FROM conversions ORDER BY created_at DESC LIMIT 5;"
```

### 2.4 Verificar Estado de Colas

```bash
# Ver tareas en espera
docker-compose exec worker celery -A apps.worker.tasks inspect active

# Ver tareas planificadas
docker-compose exec worker celery -A apps.worker.tasks inspect scheduled

# Ver estadísticas del worker
docker-compose exec worker celery -A apps.worker.tasks inspect stats

# Purgar colas (peligro: borra todos los trabajos pendientes)
docker-compose exec worker celery -A apps.worker.tasks purge
# Confirmar con: yes
```

### 2.5 Migraciones de Base de Datos

```bash
# Ver estado actual
docker-compose exec api alembic current

# Aplicar todas las pending
docker-compose exec api alembic upgrade head

# Revertir última migración
docker-compose exec api alembic downgrade -1

# Ver histórico
docker-compose exec api alembic history

# Crear nueva migración (después de cambiar models)
docker-compose exec api alembic revision --autogenerate -m "Add user preferences"

# Aplicar la nueva
docker-compose exec api alembic upgrade head
```

## 3. Troubleshooting

### 3.1 API No Responde

**Síntoma**: `curl http://localhost:8000/health` → Connection refused

**Pasos**:
1. Verificar si el contenedor está corriendo:
   ```bash
   docker-compose ps api
   # STATUS debe ser "Up"
   ```

2. Si no está corriendo, iniciar:
   ```bash
   docker-compose up -d api
   ```

3. Si está corriendo pero no responde, revisar logs:
   ```bash
   docker-compose logs api | tail -50
   ```

4. Buscar en logs:
   - `Traceback` → Error en código
   - `Address already in use` → Puerto 8000 ocupado
   - `Connection refused (postgres)` → PostgreSQL no disponible

5. Si PostgreSQL no disponible:
   ```bash
   docker-compose restart postgres
   docker-compose exec postgres pg_isready
   # Esperado: "accepting connections"
   ```

6. Reiniciar API:
   ```bash
   docker-compose restart api
   docker-compose logs -f api
   ```

### 3.2 Worker No Procesa Tareas

**Síntoma**: Conversiones quedan en `queued` sin pasar a `processing`

**Pasos**:
1. Verificar worker activo:
   ```bash
   docker-compose logs worker | grep "ready to accept"
   ```

2. Verificar cola tiene mensajes:
   ```bash
   docker-compose exec api python -c "
   from apps.api.models import Conversion
   from apps.api.config import SessionLocal
   
   db = SessionLocal()
   queued = db.query(Conversion).filter_by(status='queued').count()
   print(f'Conversiones encoladas: {queued}')
   "
   ```

3. Revisar RabbitMQ:
   ```bash
   curl -s http://guest:guest@localhost:15672/api/queues/%2F/pdf_conversions | jq '.messages_ready'
   # Si es 0 pero hay conversiones queued en DB → Problema de publicación
   ```

4. Revisar logs del worker:
   ```bash
   docker-compose logs worker | grep -i "error\|exception" | tail -20
   ```

5. Si worker crasheó:
   ```bash
   docker-compose up -d worker
   docker-compose logs -f worker
   ```

6. Si queue.messages_ready > 100 pero worker lento:
   ```bash
   # Aumentar concurrencia
   docker-compose exec worker celery -A apps.worker.tasks control pool_grow 2
   # O editar docker-compose.yml y cambiar `--concurrency=2` a `--concurrency=4`
   ```

### 3.3 Errores de Conversión Frecuentes

**Error**: "extraction_low_quality"

```
Significado: PDF escaneado con baja cobertura de texto
Acciones:
  1. Verificar si PDF es realmente digital o escaneado
  2. Probar OCR: PDF debe ir a ruta OCR, no digital
  3. Revisar logs: docker-compose logs worker | grep file_id
  4. Si muchos PDFs fallan: Aumentar modelo OCR o GPU
```

**Error**: "timeout"

```
Significado: Conversión tardó más de 10 minutos
Acciones:
  1. Revisar tamaño/páginas del PDF
  2. Aumentar resource limits en docker-compose.yml (memory, cpu)
  3. Revisar performance con: docker stats
  4. Si sistema sobrecargado: Distribuir a segundo worker
```

**Error**: "out_of_memory"

```
Significado: Worker se quedó sin RAM
Acciones:
  1. Revisar memory usage: docker stats
  2. Disminuir concurrencia: --concurrency=1
  3. Aumentar límite en docker-compose: mem_limit: 4GB
  4. Revisar si hay memory leaks: memory_profiler
```

### 3.4 Base de Datos Lenta o No Responde

**Síntoma**: Queries tardan > 1 segundo

```bash
# Verificar conexiones activas
docker-compose exec postgres psql -U postgres -c "SELECT datname, usename, application_name, state FROM pg_stat_activity;"

# Si hay muchas (> 50): Leak de conexiones en API
# Solución: Reiniciar API

# Ver queries lentas
docker-compose exec postgres psql -U postgres -d pdf_converter -c "EXPLAIN ANALYZE SELECT * FROM conversions WHERE user_id='...' ORDER BY created_at DESC LIMIT 100;"

# Si plan es ineficiente: Agregar índice
# docker-compose exec postgres psql -U postgres -d pdf_converter -c "CREATE INDEX idx_conversions_user_date ON conversions(user_id, created_at DESC);"
```

### 3.5 Almacenamiento (Disco) Lleno

**Síntoma**: Errores de "no space left"

```bash
# Verificar espacio
docker-compose exec worker df -h /tmp/pdf-converter-storage

# Listar archivos grandes
docker-compose exec worker find /tmp/pdf-converter-storage -type f -size +100M

# Limpiar archivos antiguos (CUIDADO: puede borrar conversiones en progreso)
docker-compose exec worker find /tmp/pdf-converter-storage -type f -mtime +1 -delete

# Mejor: Ejecutar limpieza automática
docker-compose exec api python scripts/cleanup_orphaned.py

# Aumentar espacio disponible:
# 1. Agregar volumen en docker-compose.yml
# 2. Parar contenedores: docker-compose down
# 3. Ampliar disco host
# 4. Reiniciar: docker-compose up -d
```

### 3.6 RabbitMQ No Disponible

**Síntoma**: "Connection refused" al crear conversión

```bash
# Verificar si RabbitMQ está corriendo
docker-compose ps rabbitmq
# STATUS debe ser "Up"

# Reiniciar
docker-compose restart rabbitmq

# Ver logs
docker-compose logs rabbitmq | tail -50

# Si no inicia, revisar espacio en disco
docker-compose exec rabbitmq df -h /var/lib/rabbitmq

# Purgar datos viejos (DESTRUYE TODO)
# docker-compose down -v
# docker-compose up -d rabbitmq
```

## 4. Respuesta a Incidentes

### 4.1 Incidente: Muchas Conversiones Fallando

**Objetivo**: Identificar raíz cause y mitigar rápidamente.

**Timeline**:
- **T+0**: Se reportan fallos de conversión
- **T+5**: Verificar health del sistema
- **T+10**: Identificar causa (PDF corrupto, motor caído, resource exhausted, etc.)
- **T+15**: Iniciar mitigación
- **T+30**: Sistema estable o degradado pero funcional
- **T+60**: Post-mortem y fix implementado

**Checklist**:

```bash
# 1. Verificar qué está fallando
docker-compose logs api | grep -i "failed\|error" | head -20
docker-compose logs worker | grep -i "failed\|error" | head -20

# 2. Quantify
docker-compose exec api python -c "
from apps.api.models import Conversion
from apps.api.config import SessionLocal
from datetime import datetime, timedelta

db = SessionLocal()
last_hour = datetime.utcnow() - timedelta(hours=1)

success = db.query(Conversion).filter(
    Conversion.status == 'succeeded',
    Conversion.created_at > last_hour
).count()

failed = db.query(Conversion).filter(
    Conversion.status == 'failed',
    Conversion.created_at > last_hour
).count()

print(f'Última hora: {success} éxitos, {failed} fallos')
print(f'Error rate: {failed/(success+failed)*100:.1f}%')
"

# 3. Determinar causa:
# Opción A: Todos los PDFs fallan → Motor PDF o worker
docker-compose exec worker python -c "from apps.worker.tasks import test_pdf_engine; test_pdf_engine()"

# Opción B: Algunos PDFs fallan → PDFs específicos
docker-compose logs api | grep -i "pdf_id\|file_id" | head -10

# Opción C: Timeout frecuente → Resources insuficientes
docker stats --no-stream

# Opción D: Errores de DB → Conexión o query
docker-compose logs api | grep -i "database\|sqlalchemy"

# 4. Mitigación según causa:

# Si motor caído: 
docker-compose logs worker | grep -i "import\|module" | tail -20
docker-compose down && docker-compose up -d worker

# Si resources exhausted:
docker-compose down && \
docker-compose up -d postgres rabbitmq redis && \
sleep 10 && \
docker-compose up -d api worker

# Si DB corrupted:
docker-compose restart postgres
docker-compose exec api alembic current

# Si rate de fallos sigue alta:
# Pausar aceptar nuevas conversiones (set quota a 0)
docker-compose exec api python -c "
from apps.api.config import settings
settings.MAX_DAILY_CONVERSIONS = 0
# Luego escribir en DB o reiniciar con env var
"

# 5. Comunicar
echo 'Incident: {title}
Status: {mitigated|investigating|resolved}
Impact: {X} conversions failed
Duration: {Ymin}
Next: {action}' > /tmp/incident.txt
```

### 4.2 Incidente: Pérdida de Datos/Archivos Inesperada

**Objetivo**: Determinar alcance y recuperar si es posible.

```bash
# 1. Verificar backups
ls -lah /backups/
ls -lah /data/postgres_backups/  # Si existen

# 2. Cantidad de conversiones huérfanas
docker-compose exec api python -c "
from apps.api.models import Conversion, Artifact
from apps.api.config import SessionLocal
from datetime import datetime, timedelta

db = SessionLocal()
one_day_ago = datetime.utcnow() - timedelta(days=1)

conversions_without_artifact = db.query(Conversion).filter(
    Conversion.status == 'succeeded',
    Conversion.created_at > one_day_ago
).join(Artifact, Conversion.id == Artifact.conversion_id, isouter=True).filter(
    Artifact.id == None
).count()

print(f'Conversiones sin artefacto (posible pérdida): {conversions_without_artifact}')
"

# 3. Recuperar desde backup (si existe)
# Parar servicios
docker-compose down

# Restaurar DB
docker volume rm pdf_converter_postgres_data
docker-compose up -d postgres
docker-compose exec postgres pg_restore /backups/latest.dump -d pdf_converter

# Restaurar almacenamiento
rsync -av /backups/storage/* /tmp/pdf-converter-storage/

# Reiniciar
docker-compose up -d

# 4. Si no hay backup: Notificar a stakeholders
echo "Data Loss Incident: {count} conversions lost between {time1} and {time2}"
```

### 4.3 Incident Post-Mortem

Después de resolver, documentar:

```markdown
# Post-Mortem: [Nombre del Incidente]

## Timeline
- T+0: Síntoma detectado
- T+X: Root cause identificado
- T+Y: Mitigado
- T+Z: Resuelto

## Root Cause
[Descripción técnica de qué salió mal]

## Impact
- Usuarios afectados: X
- Conversiones fallidas: Y
- Duración: Z minutos
- Estimated cost: $W

## Contributing Factors
1. Factor A permitió que…
2. Factor B no detectó…
3. Factor C no previno…

## Corrective Actions
- [ ] Action 1 (Owner, Target Date)
- [ ] Action 2
- [ ] Action 3

## Lessons Learned
- What went well
- What didn't go well
- How we'll improve

## Prevention
- Mejor testing
- Mejor monitoring
- Mejor automation
- Mejor documentation
```

## 5. Mantenimiento Preventivo

### 5.1 Diario (Cada 24h)

```bash
# Morning check
docker-compose ps  # Verify all services up
docker-compose logs --tail=100 | grep -i error

# Si hay alertas: Investigar y reportar
```

### 5.2 Semanal (Cada 7 días)

```bash
# Performance review
# 1. Error rate
# 2. P95 latency
# 3. Queue depth trends
# 4. Disk usage

# Database maintenance
docker-compose exec postgres psql -U postgres -d pdf_converter -c "VACUUM ANALYZE;"

# Dependency updates check
pip list --outdated

# Log rotation (si logs se acumulan)
docker-compose exec api logrotate /etc/logrotate.conf
```

### 5.3 Mensual (Cada 30 días)

```bash
# 1. Security updates
docker pull postgres:15-alpine
docker pull rabbitmq:3.12-management-alpine
docker pull redis:7-alpine

# 2. Performance review & optimization
# Revisar slow query log
# Revisar memory leaks
# Revisar unused indexes

# 3. Capacity planning
# Si crecimiento, ¿tenemos capacidad para 2x volumen?

# 4. Disaster recovery drill
# Simular restauración desde backup
# Verificar rollback procedure
```

### 5.4 Trimestral (Cada 90 días)

```bash
# 1. Full system upgrade
# Actualizar dependencias
# Actualizar imágenes Docker
# Ejecutar regression tests

# 2. Security audit
# Revisar CVEs
# Revisar acceso logs
# Revisar firewall rules

# 3. Capacity expansion
# Si storage, DB o workers en límite
```

## 6. Contacts y Escaladas

| Rol | Nombre | Teléfono | Slack | Disponible |
|-----|--------|----------|-------|-----------|
| On-Call Engineer | TBD | TBD | TBD | 24/7 |
| Platform Lead | TBD | TBD | TBD | Business hours |
| CTO | TBD | TBD | TBD | Por emergencia |
| External Support | TBD | TBD | TBD | SLA: 1h crítico |

## 7. Links Útiles

- Documentación: [docs/](../docs/)
- Plan del Proyecto: [PLAN_APP_CONVERSION_PDF_v1.0.md](../PLAN_APP_CONVERSION_PDF_v1.0.md)
- Arquitectura: [ARQUITECTURA.md](./ARQUITECTURA.md)
- Seguridad: [SEGURIDAD.md](./SEGURIDAD.md)
- Testing: [CALIDAD.md](./CALIDAD.md)
- Progreso: [AVANCE.md](./AVANCE.md)

## 8. Quick Reference

```bash
# Health Check
curl http://localhost:8000/health

# Logs Quick
docker-compose logs -f api

# Restart Everything
docker-compose down && docker-compose up -d

# Clean Cache & Rebuild
docker-compose down -v && docker-compose build --no-cache && docker-compose up -d

# Check Performance
docker stats

# Database CLI
docker-compose exec postgres psql -U postgres -d pdf_converter

# Worker Status
docker-compose exec worker celery -A apps.worker.tasks inspect active

# Cleanup Orphans
docker-compose exec api python scripts/cleanup_orphaned.py
```

**Última Actualización:** 2026-10-07  
**Próxima Revisión:** 2026-12-07
