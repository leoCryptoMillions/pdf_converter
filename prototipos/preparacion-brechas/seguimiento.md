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
| 2026-10-21 | Adopción de `docs/DASHBOARD_PREPARACION_BRECHAS_IA.md` v3.1.0: look and feel completo de §3.1 (catálogo de 7 puntos, todos adoptados) y línea de tiempo de hitos de §3.20 (`milestones[]`, 4 hitos reales) | Ninguna de las 11 áreas (`deliverables[]`) cambió de estado; cambio puramente de presentación/UI e incorporación de una colección nueva (`milestones[]`) | Solo visual/estructural: `index.html` (CSS y JS), sin tocar `fuentes.json`. Fuentes de los 4 hitos: commits `2e5002e` y `6cb7b96` (2026-10-07), `README.md` (sección "Características Principales" y texto general), `docs/PROTOTIPO_F0.md` — todas ya citadas en la petición original del usuario, no releídas de nuevo esta sesión | `node --check` sobre el `<script>` extraído del HTML: sintaxis OK; verificación programática de balance de etiquetas (`html/body/div/dialog/header/aside/nav/main/footer/section`) e IDs estáticos duplicados: ninguno encontrado; confirmación manual de que los IDs de área reales son `F0-01`..`F0-11` antes de decidir `related_area_ids` | Ninguna automatizada de interacción en navegador real (abrir cada nodo de la línea de tiempo) en esta sesión — pendiente verificarlo visualmente la próxima vez que se abra el dashboard |
| 2026-10-21 | Aplicación de las 3 correcciones de usabilidad obligatorias de `docs/DASHBOARD_PREPARACION_BRECHAS_IA.md` v4.0.1 (detectadas al revisar en navegador real la primera aplicación de la guía, proyecto Nexia/conta01, ahora obligatorias para cualquier proyecto que use la guía): (1) reubicar `.milestones-timeline` al inicio de la vista Resumen (§3.20); (2) convertir en botones navegables los pasos "02 · Evidencia" y "03 · Decisiones" de la secuencia inferior (§3.2); (3) hacer interactivas las entradas de discrepancias/riesgos/bloqueos, con ficha de detalle propia (§3.2/§3.15) | F0-01 a F0-11 (sin cambio de estado documental); `discrepancies[]`, `risks[]`, `blockers[]` (sin cambio de datos, solo de presentación) | **(1)** `<section class="milestones-timeline">` se movió dentro de `renderOverview()` para ser el primer elemento del `innerHTML` de `#view-overview` (antes del `.overview-grid` con la tabla de áreas), en vez de ir después de `.overview-grid` y `.sequence`; CSS `.milestones-timeline` cambiado de `margin-top:26px` a `margin-bottom:26px` para que el espaciado siga teniendo sentido en la nueva posición. **(2)** De los 4 `<div class="step">` de la secuencia, "02 · Evidencia" y "03 · Decisiones" pasaron a `<button class="step" data-view="evidence">`/`data-view="decisions">`, reutilizando `switchView()` (el mismo mecanismo que usa la barra de navegación `#nav`), sin lógica nueva de navegación. "01 · Alcance" y "04 · Validación" se dejaron como `<div>` no interactivos porque este dashboard **no tiene** ni una sola área/ficha que represente literalmente "el alcance del proyecto" (las 11 áreas de `deliverables[]` son categorías temáticas — Datos y evidencia, Calidad técnica, Conversión, Infraestructura, Seguridad y datos, Cumplimiento, Gobernanza — ninguna es "Alcance") ni una vista de "Validación"; se añadió una nota visible en la propia etiqueta de cada paso ("Sin ficha única equivalente... fuera de alcance de la navegación" / "Sin vista propia... fuera de alcance de la navegación"), tal como permite explícitamente la guía v4.0.1 para un paso sin vista ni ficha equivalente — no se inventó una ficha de alcance ni una vista de validación que no existían. **(3)** Se investigó `#detail-dialog` primero: es específico de `deliverables[]` (tiene formulario de campos de borrador con `textarea`/`data-key`, grid de estados implementación/verificación/decisión, y guarda en `draft[d.id]`) — no apto para discrepancias/riesgos/bloqueos sin forzar su semántica, así que se añadió un diálogo nuevo **pequeño y compartido** `#item-dialog` (sin formulario, sin guardado, solo lectura), reutilizado por las 3 entidades vía `openDiscrepancy()`/`openRisk()`/`openBlocker()`. Las tarjetas "Fuentes por conciliar" y "Bloqueos abiertos" (ya existentes, antes `<div class="item">` sin interacción) pasaron a `<button class="item" data-discrepancy="ID">`/`data-blocker="ID">`. Se encontró que `risks[]` (5 riesgos, `RSK-01`..`RSK-05`) **no tenía ninguna tarjeta ni listado visual** — solo se mostraba su conteo agregado en `legend-note` ("Riesgos registrados: N") — así que se añadió la tarjeta "Riesgos abiertos" en el `side-col` del Resumen, con el mismo patrón visual que "Bloqueos abiertos", para que los 5 riesgos sean alcanzables desde la UI y no solo desde el código fuente; esto no es una de las 3 correcciones en sí, sino la pieza mínima de render que la corrección 3 necesitaba para poder aplicarse a `risks[]` sin inventar datos nuevos (los campos severidad/categoría/probabilidad/impacto/mitigación/contingencia ya existían en `risks[]`, solo faltaba mostrarlos). Adicionalmente se actualizó `review.guide_version` de `"3.0.1"` a `"4.0.1"` para reflejar la versión de la guía realmente aplicada (dato interno, usado solo en la exportación de borrador) | Guía `docs/DASHBOARD_PREPARACION_BRECHAS_IA.md` v4.0.1 (texto de las 3 correcciones, §3.2/§3.15/§3.20, citado tal cual en la instrucción recibida); estructura real de `index.html` inspeccionada directamente en esta sesión (CSS, HTML de diálogos, `renderOverview()`, `renderEvidence()`, `renderDecisions()`, arrays `discrepancies`/`risks`/`blockers`, función `byId()`) antes de decidir cada cambio | `node --check` sobre el `<script>` extraído de `index.html`: sintaxis OK; llaves `{`/`}` balanceadas (391/391); conteo de `<dialog` 3→4 (+`#item-dialog`), `<section` 7→7 (sin cambio, solo se reubicó una sección existente), `<button` incrementado (nuevos botones de pasos, discrepancias, riesgos, bloqueos y cierre de `#item-dialog`); IDs estáticos duplicados: ninguno encontrado | Ninguna prueba en navegador real en esta sesión — pendiente confirmar visualmente que: la línea de tiempo de hitos aparece primero en el Resumen, los pasos 02/03 navegan correctamente, y las 3 fichas nuevas (`#item-dialog` para discrepancia/riesgo/bloqueo) abren y cierran sin atrapar el foco |
| 2026-10-23 | A pedido directo del usuario ("procede con F0-05"): implementación del enrutamiento `needs_review` de DEC-04 en el pipeline real, antes solo decidido como criterio. Antes de escribir código se verificó que `apps/convert.py` no ejecutaba OCR en absoluto (solo pdfplumber); construir esto adelanta alcance de F4 a F0, lo cual se le preguntó explícitamente al usuario (opciones: redefinir como scope-deferred / construir OCR mínimo ahora / solo test del comportamiento actual) y eligió construirlo | F0-05 (cerrado: `implementation_status=implemented`, `verification_status=passed`), BLK-04 (`next_action` limpiado, ya no apunta a algo pendiente), DEC-04 (texto actualizado: "implementado" en vez de "pendiente"), RSK-03 (nota añadida: el mecanismo ya es genérico, pero la calidad de `scanned_difficult` en sí sigue sin medirse — riesgo sigue abierto) | Nuevo `packages/converters/ocr.py`: OCR opt-in (`ocr=True` en `extract_digital`, flag `--ocr` nuevo en `apps/convert.py`, antes inexistente) usando Tesseract vía `pytesseract.image_to_data` (confianza real de palabra, no fabricada) y la misma detección de binarios Windows que ya usaba `benchmarks/ocr_benchmark.py`. Página 1 ("portada", heurística **posicional**, no visual — limitación documentada explícitamente en el `gap` de F0-05) siempre `needs_review=True`; el resto se enruta por confianza media >= 0.85 (el mismo número que ya usa el ejemplo de `ContentWarning` en `CLAUDE.md`, no inventado para esta tarea). Integrado también en `packages/exporters/xlsx.py`/`docx.py` sin tocarlos: ya recorren `page.warnings`, así que los nuevos códigos (`OCR_COVER_PAGE_UNVALIDATED`, `OCR_LOW_CONFIDENCE`, `OCR_APPLIED`, `OCR_FAILED`) aparecen solos en `_Warnings`/"Conversion warnings" | **Corrida real** (no mock) de `extract_digital(..., ocr=True)` contra `benchmarks/corpus/files/manualcargadorBYD.pdf` páginas 1 y 3 (la muestra exacta de DEC-04): página 1 con confianza real de Tesseract 92% quedó igual `needs_review=True` (confirma que el piso de confianza no aplica a portada); página 3 con 95% quedó `needs_review=False`. Se verificó también que el texto con acentos se decodifica correctamente por code point (`ord()`), porque la primera inspección visual en esta terminal parecía mostrar corrupción UTF-8 y resultó ser solo mal renderizado por la consola, no un bug real. 5 pruebas nuevas en `tests/unit/test_ocr_routing.py` (incluida la corrida real anterior), todas pasan. Suite completa: 43 passed, 3 failed — los 3 fallos (dependen de `python-docx`, no instalado en el intérprete que usa `subprocess` en esos tests) son preexistentes a esta sesión, confirmado comparando con el estado documentado en `AVANCE.md` antes de tocar nada | Pendiente, no bloqueante de este cierre: aplicar el mismo tratamiento de calidad a `scanned_difficult` (RSK-03, sigue abierto); si se usa en producción, revisar la heurística posicional de portada contra documentos reales con portada fuera de la página 1. No se verificó en navegador el resto de cambios de UI pendientes de la sesión anterior (2026-10-21, ver filas previas) — siguen sin confirmarse visualmente |

`verification_coverage` (§3.17): 2/11 (18%) — F0-08 y, desde el 2026-10-23,
F0-05 tienen `verification_status = passed` (ambos con evidencia real
ejecutada en la sesión que cerró el hallazgo, no autoatestada; ver sus
`history[]` en `index.html`). La métrica cruda de portada (3.723% CER) en sí
no cambió ni se reclama resuelta — lo que se verificó es el enrutamiento
`needs_review` de DEC-04, que es una afirmación distinta y más estrecha.
`decision_coverage` (§3.17): 2/11 (18%) — F0-08 y F0-05 tienen ya
`decision_status = accepted` (ambos el 2026-10-20, sin `authority_ref`
externo formal; aceptados por instrucción directa del usuario en esta
sesión de chat, registrado así en vez de inventar una referencia externa
que no existe). Las otras 9 áreas siguen "por revisar".

| 2026-10-23 | A pedido del usuario ("genera un front end en web para que sea fácil para el usuario"), se preguntó explícitamente el alcance (wrapper mínimo local vs. primer endpoint real de F1) por la misma razón de disciplina de fases que ya aplicó a F0-05; el usuario eligió el wrapper mínimo. Se construyó `apps/local_review_ui.py` (FastAPI, un solo usuario, sin auth/DB/cola) que solo envuelve `apps/convert.py`: formulario de subida, checkboxes de formato/OCR, página de resultado con advertencias y descargas | F0-06 (nota añadida, sin cambio de `implementation_status`/`verification_status`/`decision_status` — explícitamente no es avance de esa área, para no generar una discrepancia aparente entre "API mínima: sin rutas" y un FastAPI funcional en otro archivo) | `apps/local_review_ui.py` nuevo; no toca `apps/api/` ni `packages/converters`/`packages/exporters` (los reutiliza tal cual). Dependencias nuevas: `fastapi`, `uvicorn`, `python-multipart` (ya estaban instaladas en el entorno salvo `python-multipart`, que se instaló) | `tests/unit/test_local_review_ui.py` (4 passed, sin mocks: sube un PDF real vía `TestClient`, descarga el XLSX resultante y valida que es un zip válido; prueba rechazo de no-PDF; prueba que `/download` rechaza traversal de ruta). Adicionalmente: servidor real levantado con `python -m apps.local_review_ui`, formulario revisado en un navegador real (Chrome vía claude-in-chrome), y una conversión real de extremo a extremo por `curl` (subida multipart → descarga → `openpyxl.load_workbook` confirma la hoja `Table_1` correcta) | Ninguna bloqueante. Pendiente si se usa más: borrado/TTL de `.generated/web_ui/` (hoy no se borra solo, documentado en la propia página); si algún día se decide escalar esto a F1, usar `apps/api/` desde cero en vez de extender este wrapper |

`verification_coverage` y `decision_coverage` no cambian con esta fila: es
una herramienta de conveniencia nueva, no una verificación ni decisión sobre
ninguna de las 11 áreas existentes.

## UX local, temas y revisión de conta01 (2026-10-23)

Autorización: pedidos directos del usuario en esta conversación («mejora el
UX/UI» y «agrega un botón de modo claro/obscuro y revisa … conta01 … las
mejores prácticas … para replicar»). La revisión de conta01 fue de lectura;
no se cambió ese repositorio.

| Fecha | Tarea/avance | Áreas | Actualización o motivo de no impacto | Fuentes/evidencia | Verificaciones | Decisión pendiente |
|---|---|---|---|---|---|---|
| 2026-10-23 | Rediseño del wrapper, temas y adopción de prácticas de conta01 | F0-06 / F0-10, nota de alcance local | Sin impacto en las brechas: no se modifican estados ni decisiones de F1. Se corrigen los dos textos de Flujos que aún negaban la existencia de interfaz. Se adaptan variables semánticas, preferencia antes del CSS, almacenamiento tolerante a fallos, revisión por superficies, cabeceras/CSP y documentación con evidencia. | `apps/local_review_ui.py`, `apps/local_review_assets/`, `tests/unit/test_local_review_ui.py`, `tests/e2e/local_review_ui.cjs`, `docs/PROTOTIPO_F0.md`, `docs/AVANCE.md`; fuentes SRC-10 a SRC-13. Capturas y mediciones en `.generated/ui-check/`. | 18 pruebas HTTP pasan. Chromium: ambos temas, sistema, persistencia, pestañas, teclado, contraste de pares de texto >=4.5:1, botón >=44×44 px y separaciones de 10/18 px, responsive 375–1440 px, subida/conversión/descarga reales, errores y alternativa sin JavaScript. Dashboard abierto y vista Flujos revisada sin errores de consola. | Ninguna para este cambio. Borrado/TTL sigue pendiente. Cuentas, permisos y preferencias por usuario se reservan para F1. |

Indicadores leídos del dashboard: `verification_coverage` **18% (2/11)** y
`decision_coverage` **27% (3/11)**, sin cambios. Se preserva el snapshot
global de la revisión anterior; esta entrada solo acredita las fuentes y
las verificaciones locales descritas. La matriz de prácticas adaptadas y
deferidas está en `docs/PROTOTIPO_F0.md`.

## Ayuda, FAQ y mascota PDF Converter (2026-10-23)

Pedido directo del usuario: «menú ayuda, FAQ … la misma mascota que Nexia,
pero ahora ponle PDF Converter … cada botón tenga su botón de ? … procede
directo». Se amplía el wrapper local dentro del alcance ya autorizado.

| Fecha | Tarea/avance | Áreas | Actualización o motivo de no impacto | Fuentes/evidencia | Verificaciones | Decisión pendiente |
|---|---|---|---|---|---|---|
| 2026-10-23 | Menú Ayuda, FAQ, guía y ayuda contextual con mascota | F0-06 / F0-10, conveniencia local | Sin impacto en las brechas: no se modifican estados, decisiones ni alcance de F1. Se añade `/ayuda`, 13 FAQ buscables y 20 temas compartidos con los `?` de las acciones. Mascota 3D editada con «PDF Converter» y transparencia, integrada en ayuda y diálogos. | `apps/local_review_help.py`, `apps/local_review_assets/help.json`, `help.js`, `help.css`, `shell.html`, `pdf-converter-guide.png`; `docs/PROTOTIPO_F0.md` (incluye referencia y prompt); pruebas HTTP y de navegador. | 21 pruebas HTTP pasan. Chromium: menú/FAQ, búsqueda sin acentos, estado sin resultados, ayuda sin perder archivo ni foco, imágenes cargadas, temas, móvil, conversión/descargas reales y alternativa sin JavaScript. Evidencia `.generated/ui-check/`. | Ninguna para este ajuste. Se mantienen los pendientes de F1 y borrado/TTL. |

Se conservan `verification_coverage` **18% (2/11)** y
`decision_coverage` **27% (3/11)**. No se renuevan snapshots globales ni
hashes de fuentes ajenas a este cambio. Las mejoras de ayuda no acreditan
verificación ni aceptación operativa de las 11 áreas de F0.

## Adopción de la guía v3.1.0 (2026-10-21): look and feel + línea de tiempo de hitos

Se leyó `docs/DASHBOARD_PREPARACION_BRECHAS_IA.md` v3.1.0 completa en las dos
secciones relevantes (§3.1 "Componentes visuales adicionales observados en
la referencia Nexia" y §3.20 "Línea de tiempo de hitos del proyecto") antes
de tocar `index.html`. Ambas ampliaciones son opcionales según la guía; se
adoptaron las dos por instrucción directa del usuario, reutilizando siempre
los tokens de color ya existentes en `:root` (ningún color nuevo añadido).

**Look and feel (§3.1, catálogo de 7 puntos) — los 7 se adoptaron:**

1. **Botones**: se añadió la variante `.btn.text` (sin borde, subrayado al
   hover) y se aplicó al botón "Quitar filtros" como ejemplo terciario,
   igual que indica la guía. `.btn.secondary` se declaró como alias
   explícito del estilo por defecto (contorno + fondo blanco), que ya existía
   de facto. Alto mínimo 44 px y radio 8 px aplicados a las tres variantes.
2. **Iconos**: `stroke-width` de los SVG lineales bajado de 1.8 a 1.7 (dentro
   del rango 1.6–1.7 sugerido); extremos/uniones redondeados ya existían.
3. **Badges reutilizables**: se agregaron las clases `pending`/`red`/`green`/
   `neutral` como alias de las ya existentes (`warn`→`pending`, `bad`→`red`,
   `ok`→`green`) más una `neutral` nueva (fondo `--selected`, texto
   `--text-2`). Las clases existentes `warn/bad/ok/risk` no se renombraron
   para no romper la tabla/fichas ya probadas; las nuevas clases con el
   nombre del catálogo se usan en los puntos de color de la línea de tiempo
   de hitos (punto done→green, planned/in_progress→neutral, delayed→red).
4. **Tarjeta "El siguiente paso"**: se le añadió la clase `next-step` con
   fondo `var(--selected)` (tono de acento suave ya existente, no nuevo) y
   un `::after` puramente decorativo (par de círculos concéntricos
   recortados en la esquina inferior derecha, `pointer-events:none`, sin
   texto ni función).
5. **Indicador de fase en la barra lateral**: bloque fijo debajo de `#nav`
   (con `margin-top:auto` dentro de un sidebar `flex-direction:column`) con
   el texto real del proyecto — **"F0 — Prototipo CLI de viabilidad"**,
   tomado de `CLAUDE.md` ("Current Phase: F0 - Viability Assessment") y del
   propio dashboard (`review.phase`) — y una fila de 7 segmentos (F0 a F6,
   según la tabla de fases de `CLAUDE.md`), el primero (F0, fase actual)
   resaltado con `var(--accent-2)`.
6. **Foco visible**: `outline-offset` de `:focus-visible` subido de 2 px a
   3 px (ya era 3 px de grosor); sigue aplicado de forma uniforme vía un
   único selector global, sin reglas dispersas por componente.
7. **Avatar de perfil local**: círculo de iniciales ficticias "PB" (de
   "Preparación y Brechas", sin implicar una persona real ni un rol de
   revisor nombrado, que este proyecto todavía no tiene) junto al texto de
   snapshot/revisión en la barra superior.

**Línea de tiempo de hitos (§3.20):** se añadió la colección `milestones[]`
(namespace `HITO-xxx`, separado de `deliverables[]`/`decisions[]`) con los 4
hitos solicitados, copiados tal cual (fechas, SHAs de commit y textos sin
alterar):

| ID | Label | Status | Fecha | Fuente principal |
|---|---|---|---|---|
| HITO-01 | Inicio del proyecto | done | 2026-10-07 (real) | commits `2e5002e`, `6cb7b96` |
| HITO-02 | MVP | planned | sin fecha | `README.md`, `docs/PROTOTIPO_F0.md` |
| HITO-03 | Revisión en QA | planned | sin fecha | `docs/PROTOTIPO_F0.md` |
| HITO-04 | Salida a producción | planned | sin fecha | `README.md` (ausencia de declaración) |

Dado que el proyecto está en F0 (etapa muy temprana), **solo HITO-01 está
`done`**; los otros tres quedan `planned` sin fecha, para no sobre-declarar
avance inexistente. Se revisaron los IDs de área reales en `index.html`
(`F0-01` a `F0-11`) antes de considerar `related_area_ids`: ninguno de los
4 hitos tiene una relación obvia por título con un área existente (no hay
un área llamada "MVP", "QA" o "Producción"), así que los cuatro quedan con
`related_area_ids: []` y `related_decision_ids: []` — no se inventó ninguna
referencia para evitar dejarlos vacíos.

**UI de la línea de tiempo:** fila horizontal de nodos (punto de color +
label + fecha) debajo de la secuencia de revisión del Resumen y antes del
`legend-note`/pie de página, dentro de `#view-overview`; se apila en
vertical por debajo de 960 px, reutilizando el punto de quiebre que ya usa
el resto de grids del dashboard. Cada nodo abre un `<dialog>` propio
(`#milestone-dialog`, independiente del `#detail-dialog` de áreas para no
mezclar su lógica de campos/borrador) con label, fechas, `summary`,
`changes[]` agrupados por tipo (Definido/Agregado/Cambiado/Quitado) con sus
`source_refs[]` visibles, y botones hacia las áreas relacionadas cuando
`related_area_ids` no está vacío (ninguno de los 4 hitos actuales lo tiene).
`milestones[]` se añadió también a la exportación v2 (`buildExportV2()`).

**Verificación ejecutada antes de cerrar esta tarea:** `node --check` sobre
el `<script>` extraído de `index.html` (sintaxis válida); conteo
programático de apertura/cierre de `html/body/div/dialog/header/aside/nav/
main/footer/section` (todos balanceados); conteo de IDs estáticos
duplicados en el HTML (ninguno). No se abrió el archivo en un navegador
real en esta sesión — queda pendiente confirmar visualmente que los 4
nodos abren su ficha correctamente la próxima vez que se trabaje en este
dashboard.

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

## Guardado de la sesión (2026-10-23)

Pedido del usuario: «listo, guarda todo». Código, mascota, pruebas y
documentación del wrapper preparados para commit local. La configuración
personal `.claude/settings.local.json` y los artefactos de `.generated/`
se conservan en disco y se excluyen de Git. Punto de continuidad registrado
en `docs/AVANCE.md`. Sin impacto adicional en las brechas: se conservan
`verification_coverage` 18% (2/11) y `decision_coverage` 27% (3/11).
La evidencia vigente para este cierre es la corrida de 21 pruebas HTTP y
el recorrido Chromium ya registrado; este guardado no acredita pruebas nuevas.

## Próxima actualización esperada

Disparador según `docs/mantenimiento-dashboard.md`: antes de cerrar
cualquier tarea de P01 (corpus), P02 (benchmark), o al resolver el hallazgo
de F0-08, actualizar este dashboard siguiendo el procedimiento de §5 de la
guía genérica.
