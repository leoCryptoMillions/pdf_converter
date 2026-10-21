# Dashboard de preparación y brechas — PDF Converter

Prototipo local, autocontenido, generado a partir de la guía genérica
`DASHBOARD_PREPARACION_BRECHAS_IA.md` v3.0.1 (documento externo al
repositorio, no incluido aquí) y adaptado con datos reales de este proyecto
en su fase **F0 — Viabilidad** (snapshot: 2026-10-20, HEAD `19eb900`).

## Cómo abrirlo

Abre `index.html` directamente con doble clic o `file://` en cualquier
navegador. No requiere servidor, instalación, red ni dependencias externas.
Funciona sin conexión.

## Qué es y qué no es

- Es un diagnóstico **documental**: estado observado en código y documentos,
  separado en tres dimensiones (implementación, verificación, decisión).
  No ejecuta el producto ni certifica calidad.
- Es un **borrador editable en memoria del navegador**: cualquier texto que
  escribas en una ficha se pierde al recargar o cerrar la pestaña, salvo que
  lo descargues antes con **Descargar borrador**.
- No sustituye el backlog completo del proyecto ni el plan
  (`PLAN_APP_CONVERSION_PDF_v1.0.md`). Son **11 áreas** seleccionadas para
  esta revisión, no todas las tareas del backlog.
- No aprueba ni rechaza nada. Las decisiones reales siguen el flujo de
  `docs/AVANCE.md`, los ADR y la autorización humana correspondiente.

## Las cinco vistas

1. **Resumen** — tabla de las 11 áreas, filtros, búsqueda, siguiente paso,
   discrepancias y bloqueos abiertos.
2. **Primera operación** — 5 preguntas abiertas sobre qué falta para decidir
   el Gate F0 y resolver el hallazgo de datos personales.
3. **Flujos y canales** — el proyecto aún no tiene interfaz de usuario; esta
   vista cubre el CLI de conversión, los pipelines de benchmark y los
   procesos planeados (API, worker, OCR).
4. **Fuentes y discrepancias** — fuente real por área y 3 discrepancias
   documentales detectadas en esta revisión.
5. **Decisiones** — 3 decisiones agrupadas por familia (Gate F0, Alcance y
   datos, Técnica), todas "por revisar".

## Hallazgo de seguridad (F0-08 / BLK-06) — resuelto el 2026-10-20

`docs/AVANCE.md` (2026-10-09) documentaba que un archivo real de
identificación oficial (`INE_LUIS_ARENAS.pdf`) permanecía en
`benchmarks/corpus/files/` sin usarse, con una recomendación explícita de
borrarlo. El 2026-10-20 se verificó de forma independiente (no por quien
escribió la recomendación original) que:

- El archivo ya no existe en el filesystem (`find`/`ls` sin resultados).
- Nunca llegó al historial de git (`git log --all --full-history` sin
  coincidencias para ese nombre de archivo).
- El manifest (`benchmarks/corpus_manifest.csv`, 37 filas) coincide
  exactamente con los 37 archivos reales en disco — sin archivos huérfanos
  adicionales que pudieran ser otro hallazgo similar sin catalogar.

`F0-08`/`BLK-06` quedan cerrados en el dashboard. **El riesgo general
persiste** (`RSK-05`, abierto): el corpus sigue reteniendo localmente otros
documentos reales con datos sensibles (estados de cuenta, constancias
fiscales, un acta notarial), ya autorizados caso por caso según AVANCE.md,
pero cuya retención prolongada no deja de ser un riesgo — por eso RSK-05
sigue abierto y con `review_by` en 2026-11-20, aunque el hallazgo puntual
del INE ya se cerró.

## F0-05 (umbral de CER de OCR) — decisión documentada, no una mejora técnica

A pedido explícito del usuario ("documentemos formalmente nada más", sin
intentar instalar Tesseract ni repetir experimentos), el 2026-10-20 se
registró `DEC-04`: un umbral de CER **diferenciado por tipo de contenido**,
en vez de seguir forzando un único 2% para portada y texto continuo:

- **Texto continuo:** CER <= 2% (cumplido, 0.968%).
- **Portada:** sin umbral numérico en el Gate F0; toda página clasificada
  como portada debe marcarse `needs_review` de forma sistemática en
  producción — reutilizando el principio ya existente en `CLAUDE.md`
  ("Always return `needs_review` if uncertainty detected"), no un umbral
  inventado.

**Esto no mejoró el CER real de portada** (sigue en 3.723%, tras 14
experimentos fallidos documentados en `AVANCE.md`): lo que cambió es el
criterio de aceptación del Gate F0, no la métrica. Por eso `F0-05` ya no
aparece en la tarjeta de "atención inmediata" (la decisión sobre qué hacer
con el hallazgo ya se tomó), pero su `verification_status` sigue `failed`
bajo la medición cruda y su `next_action` deja pendiente **implementar y
probar de verdad** el enrutamiento `needs_review` para portada — hoy es
solo un criterio decidido, no código verificado. `BLK-04` se cerró porque
su propia condición de cierre ya contemplaba "umbral revisado y
justificado" como alternativa válida a bajar el CER.

## Exportación

Botón **Descargar borrador** → JSON v2, `prototype_only: true`,
`validated: false` en cada campo. Nombre sugerido:
`pdf-converter-preparacion-brechas-borrador-no-validado-<fecha>.json`.
Revisa el contenido antes de compartirlo: los campos de texto libre pueden
admitir información sensible aunque las fichas base no la tengan.

## Lo que queda pendiente (registrado, no omitido en silencio)

Según la guía de referencia (§3.8), con al menos una área `datos_personales`
(F0-08) y una `legal_fiscal_seguridad` (F0-09), el JSON Schema de exportación
v2 y el script `validar-exportacion.mjs` con la condición "sin excepción"
pasan a ser obligatorios, no opcionales. **Esta primera versión no los
implementa todavía** — es una decisión registrada explícitamente (ver
`seguimiento.md`), no un olvido. Tampoco se implementaron `verificar-fuentes.mjs`,
`verificar-evidencia.mjs`, `hitos-alcance.json` ni el histórico de
exportaciones (`historico/`). Todos son candidatos para una siguiente sesión,
priorizando primero el cierre de F0-08.

## Límites conocidos de esta maqueta

- Sin persistencia, sin importación, sin historial de URL.
- No se ejecutó en navegador real esta sesión (sin capturas de pantalla
  adjuntas); verificar interacción, responsive y accesibilidad antes de
  darla por aceptada (checklist completo en la guía de referencia, §3.9).
- Los conteos del corpus (37/60, por categoría) se tomaron de `docs/AVANCE.md`
  y no se recalcularon directamente contra `benchmarks/corpus_manifest.csv`
  en esta sesión (ver `fuentes.json`, `SRC-03`).

## Mantenimiento

Regla instalada en `docs/mantenimiento-dashboard.md` y enlazada desde
`CLAUDE.md`: actualizar este dashboard antes de cerrar cualquier tarea o
commit que cambie código/documentación relevante para alguna de las 11 áreas.
