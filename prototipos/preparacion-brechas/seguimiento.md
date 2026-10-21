# Seguimiento — Dashboard de preparación y brechas (PDF Converter)

Vocabulario de referencia (ver glosario de la guía genérica): "área o
entregable a diagnosticar" = `deliverables[]`; "decisión humana sobre un
área" = `decision_status`. No se detectó terminología local previa en este
proyecto que requiera mapeo adicional, porque este es el primer dashboard de
este tipo en el repositorio.

## Avances

| Fecha | Tarea/avance | Áreas | Actualización o motivo de no impacto | Fuentes/evidencia | Verificaciones | Decisión pendiente |
|---|---|---|---|---|---|---|
| 2026-10-20 | Creación inicial del dashboard (`prototipos/preparacion-brechas/`) a partir de la guía genérica v3.0.1, solicitada directamente por el usuario (autorización ya concedida, sin JSON previo) | F0-01 a F0-11 (todas) | Dashboard creado desde cero; 11 áreas, 6 bloqueos, 5 riesgos, 3 discrepancias y 3 decisiones registradas con datos reales de `docs/AVANCE.md`, `CLAUDE.md` y lectura directa de `apps/api/main.py`/`apps/worker/tasks.py` (solo conteo de líneas en este último) | docs/AVANCE.md, CLAUDE.md, apps/api/main.py, apps/api/config.py, apps/worker/tasks.py, apps/worker/config.py, docs/adr/0004 (referenciado, no releído) | Abrir en navegador real y ejecutar la lista de aceptación (§3.9 de la guía): pendiente, no ejecutado en esta sesión | Confirmar borrado de `INE_LUIS_ARENAS.pdf` (F0-08/BLK-06); decidir si se implementa JSON Schema v2 + `validar-exportacion.mjs` ahora o en una sesión posterior |
| 2026-10-20 | Corrección de layout de indicadores (tarjeta de bugs no se veía en una fila de 5 iguales) y, a pedido del usuario ("resuelve las áreas de atención inmediata"), investigación directa del hallazgo F0-08 | F0-08 (cerrado), RSK-05 (actualizado, sigue abierto), F0-05 (revisado, **no se pudo cerrar**) | **F0-08/BLK-06 cerrado**: verificación independiente en esta sesión confirmó que `benchmarks/corpus/files/INE_LUIS_ARENAS.pdf` ya no existe (`find`/`ls` sin resultados), que nunca entró a git (`git log --all --full-history -- "**/INE*"` sin resultados) y que el manifest (37 filas) coincide exactamente con los 37 archivos reales en disco — sin archivos huérfanos adicionales. `DISC-03` se retira de la lista activa de discrepancias por estar conciliada. **F0-05 NO se cerró**: el umbral de CER de portada (3.723% > 2%) es un problema de ingeniería OCR real, ya intentado 14 veces sin éxito según AVANCE.md; esta sesión no tiene el binario de Tesseract disponible en el PATH (`tesseract --version` falla tanto en bash como en PowerShell) para intentar un nuevo experimento, así que no se fabricó una resolución. Sigue como la única "área de atención inmediata" abierta. | find/ls sobre benchmarks/corpus/files/, `git log --all --full-history`, conteo de filas de benchmarks/corpus_manifest.csv vs archivos reales, verificación de `tesseract`/`pytesseract`/`ocrmypdf`/`pdf2image` en el entorno | Verificación de archivo/git ejecutada y documentada en el dashboard (history[] de F0-08 y BLK-06); no se ejecutó ninguna prueba de navegador adicional esta vez | Si se quiere intentar cerrar F0-05 de verdad, decidir si vale la pena instalar Tesseract en este entorno para repetir experimentos de preprocesamiento, o si se prefiere documentar la aceptación de un umbral distinto para portadas (ver nota más abajo) |
| 2026-10-20 | A pedido del usuario ("documentemos formalmente nada más" — sin intentar instalar Tesseract ni repetir experimentos OCR), se registró `DEC-04`: umbral de CER diferenciado por tipo de contenido para F0-05, en vez de seguir intentando un único 2% para portada y texto continuo | F0-05 (`decision_status` pasa a `accepted`; `kind` deja de ser "riesgo"), BLK-04 (cerrado), RSK-03 (actualizado), F0-11 (texto de dependencia corregido) | Se formalizó: texto continuo exige CER<=2% (cumplido, 0.968%); portada queda sin umbral numérico en el Gate F0 y debe marcarse `needs_review` de forma sistemática (reutiliza el principio ya existente en CLAUDE.md, no se inventó un umbral arbitrario nuevo). **Importante: esto NO es una mejora del CER real** — la cifra de portada (3.723%) no cambió; lo que cambió es el criterio de aceptación. La implementación real del enrutamiento `needs_review` para portada queda pendiente (`next_action` de F0-05), así que `implementation_status` de F0-05 sigue `partial` y `verification_status` sigue `failed` para el umbral antiguo. BLK-04 se cerró porque su propia `closure_condition` ya contemplaba "umbral revisado y justificado" como alternativa a bajar el CER. | Ninguna nueva — se reutilizó evidencia ya citada de AVANCE.md (CER medidos) y de CLAUDE.md (regla needs_review) | Ninguna automatizada; cambio puramente documental/de decisión, validado solo con `node -e "new Function(...)"` sobre el JS del dashboard | Implementar y probar el enrutamiento `needs_review` para portada en el pipeline real; hasta entonces, la "resolución" de F0-05 es solo de criterio, no de código |

`verification_coverage` (§3.17): 1/11 (9%) — solo F0-08 tiene
`verification_status = passed` (evidencia independiente, ver su `history[]`
en `index.html`). F0-05 sigue `failed` bajo la métrica cruda de portada: el
2026-10-20 se aceptó un criterio distinto (DEC-04), pero eso cambió
`decision_status`, no el resultado de la medición original, y el nuevo
enrutamiento `needs_review` para portada todavía no tiene código verificado.
`decision_coverage` (§3.17): 2/11 (18%) — F0-08 y F0-05 tienen ya
`decision_status = accepted` (ambos el 2026-10-20, sin `authority_ref`
externo formal; aceptados por instrucción directa del usuario en esta
sesión de chat, registrado así en vez de inventar una referencia externa
que no existe). Las otras 9 áreas siguen "por revisar".

## Decisión registrada: ampliación diferida, no omitida

La guía genérica (§3.8) establece que, en cuanto el dashboard declara al
menos un área `datos_personales` (F0-08) o `legal_fiscal_seguridad` (F0-09),
el JSON Schema de exportación v2 y `validar-exportacion.mjs` — con la
condición "sin excepción" de separación de funciones para esas categorías —
pasan a ser **obligatorios, no opcionales**, en cualquier dashboard, mínimo o
ampliado.

Esta primera versión **no los implementa**. Se registra aquí como decisión
explícita (permitida por §0.5, paso 7, y §3.19 de la guía: "ampliable no
significa nunca, sino que puede diferirse con esa decisión registrada"), no
como un olvido:

- Pendiente: `schema-exportacion-v2.json` (JSON Schema Draft 2020-12, con la
  condición `if/then` de separación de funciones para áreas de alto riesgo).
- Pendiente: `validar-exportacion.mjs` (debe fallar con código de salida 1
  ante una violación de esa condición).
- Pendiente: `verificar-fuentes.mjs`, `verificar-evidencia.mjs`,
  `hitos-alcance.json` y el histórico de exportaciones (`historico/`).

**Antes de anunciar estos artefactos como implementados**, deben escribirse
y ejecutarse realmente contra al menos un caso de prueba (incluida una
violación deliberada, para comprobar que el control detecta el hueco).

## Propuestas y decisiones (plantilla, sin casos reales todavía)

| ID local | Origen/revisión | Propuesta e impacto | Decisión | Autorización/criterio | Tarea y evidencia de cierre |
|---|---|---|---|---|---|
| ID por asignar | — | Sin propuestas recibidas aún en este formato | Pendiente | Por confirmar (referencia externa) | Sin implementar |

## Bloqueos y riesgos — ver también `index.html` → Resumen

Resumen rápido (detalle completo en el dashboard):

| ID | Tipo | Severidad | Categoría | Siguiente acción |
|---|---|---|---|---|
| BLK-01 | Bloqueo | high | operativo | Recolección dirigida a scanned_difficult y mixed |
| BLK-02 | Bloqueo | medium | funcional | Anotar otros diseños Word |
| BLK-03 | Bloqueo | medium | tecnico | Ampliar páginas adyacentes y documentos reservados |
| BLK-04 | Bloqueo | high | tecnico | **Cerrado 2026-10-20** — umbral revisado y justificado vía DEC-04 (no por mejora del CER) |
| BLK-05 | Bloqueo | blocker | legal_fiscal_seguridad | Revisión del stack efectivo y medición de recursos |
| BLK-06 | Bloqueo | blocker | datos_personales | **Cerrado 2026-10-20** — borrado y ausencia en git history verificados de forma independiente |
| RSK-01 | Riesgo | high | tecnico | Mantener adaptadores desacoplados por motor |
| RSK-02 | Riesgo | medium | funcional | Evaluar con corpus ampliado |
| RSK-03 | Riesgo | medium | tecnico | Portada resuelta por criterio (DEC-04); scanned_difficult en general sigue abierto |
| RSK-04 | Riesgo | high | tecnico | Benchmark de recursos con límites |
| RSK-05 | Riesgo | blocker | datos_personales | Confirmar `.gitignore` efectivo y borrar lo innecesario (revisar 2026-11-20) |

## Próxima actualización esperada

Disparador según `docs/mantenimiento-dashboard.md`: antes de cerrar
cualquier tarea de P01 (corpus), P02 (benchmark), o al resolver el hallazgo
de F0-08, actualizar este dashboard siguiendo el procedimiento de §5 de la
guía genérica.
