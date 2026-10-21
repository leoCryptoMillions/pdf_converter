# Mantenimiento del Dashboard de preparación y brechas

Dashboard: [`prototipos/preparacion-brechas/index.html`](../prototipos/preparacion-brechas/index.html)
(abrir directamente con `file://`, sin servidor). Fuentes:
[`fuentes.json`](../prototipos/preparacion-brechas/fuentes.json). Seguimiento:
[`seguimiento.md`](../prototipos/preparacion-brechas/seguimiento.md).

## Regla de mantenimiento (obligatoria)

**Disparador explícito:** antes de marcar cualquier tarea o ítem del
seguimiento/backlog como cerrado, y antes de cualquier commit que cambie
código o documentación de producto relevante para una de las 11 áreas del
dashboard (`F0-01` a `F0-11`).

- **Sí dispara la regla:** cerrar una tarea de P01/P02; mergear cambios de
  producto (API, worker, exportadores, OCR); terminar una sesión que tocó
  requisitos, corpus o licencias; resolver el hallazgo de datos personales
  de `F0-08`.
- **No la dispara:** un commit de formato sin cambio de comportamiento; una
  exploración sin cambios persistidos; una pregunta respondida sin tocar
  código ni documentos.

Antes de cerrar cada tarea o avance relevante:

1. Revisar qué áreas (`F0-01`...`F0-11`), preguntas, fuentes, bloqueos y
   riesgos cambian.
2. Actualizar el contenido afectado en `index.html` (datos en el bloque
   `<script>`), `fuentes.json` y `seguimiento.md`. Si no cambia el
   diagnóstico, registrar "sin impacto en las brechas" con el motivo.
3. Añadir una entrada a la tabla de avances de `seguimiento.md` con fecha,
   tarea, áreas afectadas, fuentes/evidencia, verificaciones ejecutadas,
   decisión pendiente y el valor actual de `verification_coverage` /
   `decision_coverage`.
4. Ante una fuente no revisada o inaccesible, registrar "pendiente de
   conciliación" en `fuentes.json`, sin afirmar que el dashboard está
   vigente. Si esa fuente bloquea una decisión, abrir el bloqueo
   correspondiente en vez de dejarla como nota suelta.
5. Si cambian datos del dashboard, abrir `index.html` en un navegador y
   repetir al menos los puntos de la lista de aceptación de la guía
   genérica (§3.9) relevantes al cambio: estructura, guardado/cancelado,
   exportación.

Esto es una obligación de quien realiza cada avance, no un servicio
automático en segundo plano. La guía genérica completa (fuera de este
repositorio) describe además una ampliación opcional (JSON Schema de
exportación, scripts de verificación de fuentes/evidencia, vigencia por
cambio de alcance) que esta primera versión difirió explícitamente — ver
"Decisión registrada" en `seguimiento.md`. Esa ampliación pasa a ser
obligatoria en cuanto se implemente o se anuncie como completa; mientras
tanto, registrar su ausencia en vez de darla por hecha.
