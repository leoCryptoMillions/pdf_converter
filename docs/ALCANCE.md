# Alcance del Proyecto - PDF Converter v1.2

**Versión:** 1.2.0

**Fecha base:** 2026-10-07 · Recorte del MVP local: 2026-10-27

**Estado:** Prototipo local F0; Gate F0 pendiente

## Entrega activa: MVP local de Word y Excel

Prioridad autorizada el 2026-10-27: terminar primero un piloto local de un
usuario. Esta sección prevalece sobre el alcance ampliado de las tablas
posteriores. La aceptación humana sigue pendiente; no se declara aprobado
el Gate F0 ni implementada la plataforma F1.

Incluye carga de un PDF digital, selección de páginas, conversión a DOCX y
XLSX, TXT existente, advertencias y descarga. Se reutiliza la interfaz de
`apps.local_review_ui`, con 25 MB y 100 páginas por PDF. No se añaden
dependencias de React, base de datos ni cola.

Desde el 2026-10-27, la misma interfaz también se despliega en Railway
(https://mvp-web-production.up.railway.app) para un solo usuario de
confianza, detrás de HTTP Basic Auth — ver
[ADR 0006](adr/0006-mvp-railway-hardening.md). El uso local en `127.0.0.1`
sigue disponible y sin autenticación (README); el despliegue remoto añade
aislamiento por subproceso, timeout y límite de memoria por conversión
(`apps/conversion_isolation.py`), concurrencia de 1 conversión a la vez y
limpieza TTL de `.generated/web_ui/` — ninguno de estos controles sustituye
cuentas reales ni multi-tenencia, que siguen fuera de alcance.

Se posponen cuentas, organizaciones, cuotas, lotes, concurrencia de usuarios,
infraestructura distribuida, formatos nuevos y mejoras de OCR. OCR existente
sigue siendo opcional y queda fuera de los criterios del piloto digital.
Se congelan cambios cosméticos, ayuda, mascota y tablero salvo fallos que
bloqueen el flujo principal. Los archivos se eliminan automáticamente pasado
el período de retención configurado (`RETENTION_HOURS`, 24 horas por defecto).

### Criterios de cierre del piloto

1. Arrancar la app con `requirements-mvp.txt` y el comando del README.
2. Completar carga → conversión → advertencias → descarga con los cinco
   documentos autorizados seleccionados en `benchmarks.pilot_local`.
3. Descargar y reabrir Word/Excel, conservar todos los valores de las celdas
   extraídas, procedencia y TXT; no introducir fórmulas desde texto recibido.
4. Una persona compara texto y orden, cifras/identificadores, estructura de
   tablas y apariencia Word frente al PDF; edita, guarda y reabre ambos
   archivos. Registra aceptación o rechazo por documento en `revision.csv`.
   Puede indicar `n/a` para tablas ausentes, explicándolo en las notas.
5. Suite crítica aprobada en desarrollo y suite completa aprobada al cierre;
   ninguna incidencia bloqueante en los documentos aceptados. Las clases
   fuera de esta muestra siguen pendientes de validación general.

La selección inicial es `cep_001`, `carta_privacidad_001`, `doc_texto_002`,
`estado_cuenta_006` y `estado_cuenta_008`: cinco PDFs digitales completos,
nueve páginas. `report.json` contiene verificaciones automáticas; no acredita
calidad semántica, orden de lectura ni aceptación humana. Los artefactos y
la lista de revisión permanecen privados en `.generated/`.

### Política de pruebas durante el MVP

`python -m pytest -q` selecciona el marcador `mvp`: 44 de 88 casos a la fecha
de este recorte, exactamente el 50%. Es una selección explícita por riesgo,
no aleatoria: integridad de Excel, texto editable de Word, ligaduras,
límites/rechazos de PDF, selección de páginas, carga/descarga y seguridad
básica de las rutas. La proporción puede variar al incorporar regresiones;
no se excluye un riesgo crítico para mantener un porcentaje exacto.

Ejecutar además las pruebas del módulo modificado con `-m "mvp or not mvp"`.
La misma expresión sin ruta específica ejecuta la suite completa al cerrar
entregas. La cobertura queda como comprobación explícita, conservando el
umbral del 70% en `make test-coverage`; reducir pruebas diarias no significa
declarar ni exigir una cobertura del 50%. No se promete reducir a la mitad
el tiempo de ejecución sin medirlo.

## Alcance ampliado de la plataforma (posterior al piloto local)

Las tablas siguientes conservan el objetivo ampliado anterior. Su inclusión
no acredita implementación o aprobación. El avance real se registra en
[AVANCE.md](AVANCE.md).

## Alcance de MVP

### Formatos Soportados

| Formato | MVP | Alcance Inicial | Limitaciones |
|---------|-----|-----------------|---------------|
| **XLSX** | ✓ Sí | Tablas extraídas con tipos | No recupera fórmulas originales |
| **DOCX** | ✓ Sí | Texto y tablas editables, imágenes, estilos y distribución aproximada | Fuentes, edición y visor pueden alterar el diseño; gráficos como PNG y paneles complejos con advertencia |
| **CSV** | ✓ Sí | Una tabla por archivo | No conserva estilos |
| **TXT** | ✓ Sí | Texto en orden de lectura | Pierde formato |
| **Markdown** | ✓ Sí | Texto y tablas | No reproduce posicionamiento |
| **JSON** | ✓ Sí | Modelo estructurado versionado | No es documento Office |
| **PNG/JPEG** | ✓ Sí | Una imagen por página | No es contenido editable |
| **PPTX** | ✗ No | Fase posterior | Requerida evaluación separada |
| **ODT** | ✗ No | Fase posterior | Demanda futura |
| **PDF OCR** | ✗ No | Fase posterior | Requiere F4 completo |

### Clases de Documentos Soportadas

| Clase | MVP | Cobertura | Soporte |
|-------|-----|-----------|---------|
| **Digital simple** | ✓ | Tablas simples, texto claro | F1-F2 |
| **Digital complejo** | ✓ | Multipágina, anidadas | F2+ |
| **Escaneado limpio** | ✓ | Buena calidad OCR | F4 |
| **Escaneado difícil** | ◐ | Baja calidad, distorsión | F4, marcado para revisión |
| **Mixto** | ◐ | Combinación | F4, clasificación por página |

### Límites de Recursos

| Límite | Valor Inicial | Cuándo Revisar |
|--------|---------------|----------------|
| Tamaño por PDF | 25 MB | Al medir memoria |
| Páginas por trabajo | 100 | Al cerrar F0 |
| Lote (archivos) | 10 | Después estabilizar single |
| Tiempo máximo | 10 minutos | Al medir OCR |
| Retención de datos | 24 horas | Antes de piloto |
| Concurrencia | 10 trabajos simultáneos | Según capacidad |

### Usuarios y Multi-tenancy

**MVP Scope:**
- ✓ Autenticación básica (local)
- ✓ Multi-tenant (organization_id)
- ✓ Quotas por usuario/org
- ✓ Role básico (user, admin org)

**Futuro:**
- OIDC/OAuth2
- SSO empresarial
- Permisos granulares

### Funcionalidades Incluidas

**Procesamiento Core:**
- ✓ Validación de PDF (estructura, corrupción)
- ✓ Clasificación de páginas (digital/escaneado)
- ✓ Extracción de tablas y texto
- ✓ Detección de imágenes
- ✓ OCR básico (Tesseract)

**Interfaz:**
- ✓ Carga de PDF (drag & drop)
- ✓ Vista previa con PDF.js
- ✓ Tabla editable interactiva
- ✓ Indicadores de advertencias
- ✓ Descarga segura

**Confiabilidad:**
- ✓ Reintentos automáticos
- ✓ Idempotencia
- ✓ Logging de auditoría
- ✓ Durabilidad (outbox pattern)

## Exclusiones Explícitas

### No Incluidas en MVP
- ✗ Integración con APIs documental externas
- ✗ Conversión inversa (Office a PDF)
- ✗ Formularios interactivos de PDF
- ✗ Firmas digitales y certificados
- ✗ Búsqueda full-text
- ✗ Colaboración en tiempo real
- ✗ Aplicación de escritorio
- ✗ App móvil nativa

### A Evaluar en F0
- ¿Editabilidad Word vs Apariencia (conflicto)?
- ¿Rendimiento OCR suficiente?
- ¿Licencias sin bloqueadores?
- ¿Modelo de costo viable?

## Criterios de Éxito por Formato

### XLSX Digital Simple
- F1 >= 0.95 en detección de tablas
- >= 99% de contenido exacto
- Tipos de datos correctos
- Cero cambios silenciosos en números críticos
- Apertura sin reparación en Excel/Calc

### DOCX Digital Simple
- >= 99% de cobertura de texto
- F1 >= 0.90 en estructura (títulos, párrafos)
- Editabilidad 100% (seleccionar, editar, guardar)
- Imágenes embebidas correctamente
- Apertura sin reparación

La conservación visual debe incluir dimensiones/orientación, posiciones,
tamaños de letra, colores, negrita/cursiva e imágenes cuando puedan
recuperarse. Las tablas sencillas mantienen celdas editables y combinaciones
detectadas; un panel complejo puede conservarse como texto posicionado con
advertencia. Los marcos favorecen la apariencia y limitan la edición como
flujo continuo. Las fuentes sustituidas y los recursos omitidos se informan.

Las advertencias permanecen en resultados e IR. El anexo Word es opcional,
desactivado por defecto, y agrega páginas al documento. Una página escaneada
conservada como imagen no se considera texto editable; el OCR sin geometría
validada conserva un orden aproximado y sus notas de revisión.

Estos requisitos se identifican como **RF-DOCX-01 a RF-DOCX-08** y
**RNF-DOCX-01** en el [plan, §11.1](../PLAN_APP_CONVERSION_PDF_v1.0.md#111-requisitos-verificables-de-conversión-a-word),
que centraliza los criterios de aceptación y los presupuestos de recursos.
La decisión técnica inicial es [ADR 0005](adr/0005-word-layout.md).
Se requiere validar al menos tres diseños reales con referencias
adjudicadas y comparación visual. La implementación local no cierra esa
validación ni el Gate F0.

### Documentos Escaneados (F4)
- CER <= 2% en OCR limpio
- Datos críticos >= 99.5%
- Rotación detectada y corregida
- Marcado como "requiere revisión" cuando confianza baja

## Promesas vs Limitaciones

### Lo que Prometemos
- "Convierte tablas digitales a Excel editable"
- "Extrae texto y estructura a Word editable"
- "Valida datos y marca dudas"
- "Previene pérdida de números críticos"

### Lo que NO Prometemos
- "Recupera fórmulas Excel originales" (imposible)
- "Replica apariencia perfecta" (pixel-perfect)
- "Procesa cualquier PDF" (hay límites)
- "Garantiza 100% de precisión" (humanos revisan)
- "Procesa sin internet" (requiere servidor)

## Decisiones de Alcance Pendientes

| Decisión | Opción A | Opción B | Estado |
|----------|----------|----------|--------|
| Word: edición y apariencia | Texto editable con diseño aproximado (§11.1) | Ampliar clases/visores solo con evaluación | Alcance local aceptado en ADR 0005; validación representativa pendiente |
| Batch processing | MVP (10 files) | F5 | Planificado F5 |
| Accesibilidad WCAG | A (basic) | AA (enhanced) | F5+ |
| Lotes con fallos parciales | Permitir | Rechazar | TBD |

## Roadmap Post-MVP

### Fase F5+ (Según Demanda)
- PPTX basado en imágenes (NO diapositivas editables)
- ODT para LibreOffice
- PDF con capa OCR descargable
- Batch processing (20+ files)
- Búsqueda full-text en histórico

### Fase F6+ (Post-Piloto)
- SDK comercial para alta fidelidad
- GPU para OCR acelerado
- Kubernetes multi-region
- SSO empresarial
- Data warehouse para analytics

## Referencias

- **Plan Completo:** [PLAN_APP_CONVERSION_PDF_v1.0.md](../PLAN_APP_CONVERSION_PDF_v1.0.md) Sección 6
- **Tabla de Formatos:** [PLAN_APP_CONVERSION_PDF_v1.0.md](../PLAN_APP_CONVERSION_PDF_v1.0.md#6-alcance-y-formatos)
- **Supuestos:** [PLAN_APP_CONVERSION_PDF_v1.0.md](../PLAN_APP_CONVERSION_PDF_v1.0.md#2-supuestos-decisiones-pendientes-y-límites-de-autonomía)
