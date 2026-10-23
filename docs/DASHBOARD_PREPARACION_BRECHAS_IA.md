# Dashboard de preparación y brechas, y supervisión de proyecto — guía para otro equipo (humano o IA)

Versión 4.0.1 · 2026-10-21. Documento Markdown autónomo y genérico para entregar a otro equipo (una IA u otro equipo humano) junto con acceso a un proyecto destino cualquiera. Fusiona la especificación de navegación, apariencia, datos e interacciones de ediciones anteriores con gobernanza, gestión de riesgos y verificación automatizada ampliadas, y añade desde la versión 4.0.0 una capa de **supervisión de proyecto**: objetivos y alcance, cronograma e hitos, artefactos de gerencia y administración, gestión de riesgos a nivel de proyecto, QA del producto y continuidad documental — construida sobre el mismo dashboard, sin duplicar sus colecciones de datos. No describe ni presupone un proyecto concreto: todo ejemplo con nombres, cifras o dominio específico (fiscal, logístico u otro) está marcado explícitamente como referencia histórica o ejemplo sintético, nunca como "el proyecto actual". La versión de esta guía, la del esquema JSON de exportación y la del producto de cada proyecto destino son independientes entre sí.

Esta guía también existe empaquetada como Skill de Claude Code (`supervisor-proyectos`, invocable con un comando) que usa este mismo documento como cuerpo de conocimiento — ver la nota al final de §11. El Skill facilita invocarla dentro de Claude Code; este Markdown sigue siendo la fuente autónoma y portable, utilizable por cualquier IA o equipo humano con o sin Claude Code.

## Cómo usar y qué cambió 

Leer §0.4 para la convención de etiquetado [IA]/[Requiere humano]; §0.5 para una ruta rápida y §0.6 para el diagrama de flujo de gobernanza; §1–2 para descubrir el proyecto y diseñar el diagnóstico; §3.1–§3.13 para reproducir apariencia, datos e interacciones; §3.14–§3.19 para gobernanza, riesgos y verificación ampliadas; §3.20 para la línea de tiempo de hitos; §4–§6 para revisión, mantenimiento y entregables del dashboard; **§7–§11 para la capa de supervisión de proyecto** (objetivos/alcance/cronograma, artefactos de gerencia, riesgos a nivel de proyecto, QA del producto, continuidad para cualquier equipo); y los anexos para un ejemplo mínimo neutral y un inventario histórico real. La entrega es este Markdown autónomo; no se presupone un ZIP ni un HTML adjunto, aunque uno puede acompañarlo.

La capa de supervisión (§7–§11) es **opcional y adoptable por partes**, igual que el resto de ampliaciones de esta guía (§3.14 en adelante): un proyecto puede quedarse solo con el dashboard de preparación y brechas (§0–§6) si eso es lo que necesita, adoptar únicamente el cronograma de hitos (§7.2, que ya existía como §3.20) sin el resto, o adoptar las cinco secciones completas cuando de verdad haga falta gerencia de proyecto formal. No es una capa obligatoria por el solo hecho de existir en esta guía.

La versión 3.0.0 fusionó dos guías equivalentes desarrolladas para proyectos distintos (una con foco en inventariar la superficie funcional ya existente de un producto; otra con foco en especificación visual exhaustiva, DOM de referencia y checklist de entrega agrupado por categoría) y abordó brechas identificadas por un análisis multi-óptica (gobernanza, usabilidad, profundidad técnica, gestión de riesgos). Una revisión de completitud posterior encontró siete puntos resueltos solo de forma parcial o no resueltos; la versión 3.0.1 los cierra: convención de etiquetado [IA]/[Requiere humano] desde su primera aparición, verificación mecánica de `source_refs[]`/`evidence_refs[]` contra el repositorio real, segundo disparador de vigencia por cambio de alcance mayor (no solo por tiempo), generalización explícita del patrón «hermano sin cobertura» a campos de código arbitrarios, reubicación del diagrama de flujo cerca del inicio, regla mecánica «sin excepción» para áreas de alto riesgo en el JSON Schema, y unificación del criterio opcional/obligatorio para los scripts y JSON Schema de verificación. La versión 3.0.2 incorpora, a partir de una captura de pantalla real de un proyecto de referencia (Nexia/conta01), dos convenciones opcionales de redacción que no estaban descritas con ese nivel de detalle: el título de cada vista como enunciado breve de propósito en vez de frase descriptiva (§3.1) y la estructura de cuatro partes de la tarjeta «El siguiente paso» del Resumen (§3.2); ninguna de las dos es obligatoria ni cambia los contratos de exportación o las reglas de gobernanza ya descritos. La versión 3.1.0 amplía la misma referencia (Nexia/conta01) con el detalle completo de look and feel observado en su `index.html` real — botones, badges, iconos, tarjeta decorativa, indicador de fase lateral y foco visible (§3.1) — y añade una capacidad nueva, también opcional: la línea de tiempo de hitos del proyecto con detalle de qué cambió/se agregó/se definió en cada uno (§3.20), con su propio contrato de exportación, fila de matriz y cruce con el disparador de vigencia por cambio de alcance mayor de §3.16. La versión 4.0.1 corrige tres brechas de usabilidad detectadas al revisar en navegador real la primera aplicación de esta guía (Nexia/conta01): la línea de tiempo de hitos (§3.20) pasa de estar al final de la vista a ser uno de los primeros elementos visibles del Resumen; los cuatro pasos de la secuencia visual inferior (§3.2) dejan de ser texto decorativo y navegan a su vista/ficha real cuando existe una; y las tarjetas de discrepancias/riesgos/bloqueos de la columna lateral (§3.2/§3.15) pasan a ser interactivas, con una ficha de detalle propia en vez de mostrar solo un resumen sin forma de ver el resto. Ninguno de los tres cambia un contrato de exportación ni una regla de gobernanza; son correcciones de interacción, no de alcance. La sección «Procedimiento para comparar y fusionar guías equivalentes», cerca del final, documenta el método seguido para la fusión de 3.0.0, reutilizable para la próxima.

| Origen de la mejora | Incorporación |
|---|---|
| Revisión en navegador real de la primera aplicación de la guía (Nexia/conta01) | §3.20 línea de tiempo como primer elemento del Resumen, no el último; §3.2 pasos de la secuencia inferior navegables a su vista/ficha real; §3.2/§3.15 ficha de detalle obligatoria para cada discrepancia/riesgo/bloqueo listado, no solo un resumen |
| Solicitud explícita de convertir la guía en supervisión de proyecto | §7 objetivos/alcance/cronograma; §8 artefactos de gerencia generables; §9 riesgos a nivel de proyecto; §10 QA del producto; §11 continuidad para cualquier equipo; empaquetado adicional como Skill de Claude Code |
| Captura de pantalla de un dashboard real (Nexia/conta01) | §3.1 antetítulo/título de vista redactado como enunciado breve de propósito (opcional); §3.2 estructura de cuatro partes de la tarjeta «El siguiente paso» |
| `index.html` real de Nexia/conta01, revisión de look and feel completo | §3.1 «Componentes visuales adicionales observados en la referencia Nexia» (botones, badges, iconos, tarjeta decorativa, indicador de fase, foco visible) |
| Solicitud de línea de tiempo de hitos con detalle de cambios | §3.20 «Línea de tiempo de hitos del proyecto»: modelo `milestones[]`, UI, ficha de detalle (qué cambió/se agregó/se definió/se quitó), exportación, matriz §3.13 y cruce con `hitos-alcance.json` (§3.16) |
| Guía con foco en inventario de superficie funcional | §1.1 «Inventariar la superficie funcional»; §3.14 «Conservar inventario y ampliaciones del proyecto destino»; autorización directa del usuario sin JSON previo (§4) |
| Guía con foco en especificación visual y DOM de referencia | Esqueleto HTML copiable (§3.1); checklist de aceptación agrupado por categoría (§3.9); matriz estilo-referencia/regla-nueva (§3.1); ID estable por menú con mapeo de renombrado (§3.2) |
| Análisis de gobernanza | §3.18 «Meta-gobernanza, separación de funciones y autoridad verificable» con regla condicional mecánica para áreas de alto riesgo; historial append-only; campo de objeción registrada; vigencia/expiración de fuentes y decisiones por tiempo y por cambio de alcance mayor |
| Análisis de usabilidad | §0.4 Convención de etiquetado [IA]/[Requiere humano]; §0.5 Ruta rápida; Glosario de equivalencias; ejemplo mínimo neutral (Anexo A); heurística de cuántas áreas son suficientes; diagrama de flujo único cerca del inicio (§0.6); nota de alcance/esfuerzo; adopción incremental (§3.19) |
| Análisis de profundidad técnica | §3.16 «Verificación automatizada y vigencia de fuentes», incluido `verificar-evidencia.mjs`; JSON Schema de exportación con la regla condicional de riesgo alto (§3.18); algoritmo y normalización de hash; §3.17 «Métricas de cobertura de verificación/decisión»; serie temporal de exportaciones; generalización del patrón de cobertura por campo (§3.13) |
| Análisis de gestión de riesgos | §3.15 «Riesgos, bloqueos y escalamiento»; separación de `risks[]` y `blockers[]`; severidad, antigüedad, SLA y matriz de escalamiento |

Se mantienen los cinco menús, la paleta de referencia, los cuatro indicadores y el flujo de revisión de las ediciones anteriores. La fusión aporta patrones reutilizables; no incorpora identificadores, cifras de muestra, nombres de personas, DOR, gates, RACI, requisitos fiscales ni autorizaciones de ningún proyecto real como si fueran del proyecto destino.

## 0.4. Convención de etiquetado: qué puede ejecutar una IA sola

Dos etiquetas recorren el resto de esta guía desde aquí en adelante, para que la distinción entre lo que una IA puede hacer por sí sola y lo que necesita decisión o autorización humana no quede solo implícita en la prosa, como ocurría antes de esta sección:

- **[IA]** — una IA con acceso al repositorio puede ejecutarlo sin pedir autorización adicional: leer, inventariar, construir la maqueta, completar el borrador, calcular contadores, correr scripts de verificación, exportar.
- **[Requiere humano]** — necesita una decisión, autorización o revisión humana antes de proceder: aceptar/rechazar una propuesta o un área, autorizar un cambio de alcance, confirmar una `authority_ref`, aprobar un release, dar de alta credenciales o tocar sistemas en producción.

Un paso sin etiqueta explícita hereda la etiqueta del paso o la sección que lo contiene. Cuando un mismo paso mezcla ambas — por ejemplo, construir el borrador es [IA] pero decidir sobre su contenido es [Requiere humano] — se etiquetan por separado en vez de dejar la mezcla implícita. §0.5 y §4 aplican esta convención a sus propios pasos.

## 0.5. Ruta rápida

Para quien solo dispone de una sesión corta. Cada paso referencia la sección con el detalle completo; omitir un paso opcional debe quedar registrado, no asumido en silencio.

1. **[IA]** Leer las reglas del repositorio destino (AGENTS/CLAUDE, README) y su estado real — rama, HEAD, cambios sin commit (§1).
2. **[IA]** Inventariar brevemente la superficie funcional visible: menús, módulos, flujos principales (§1.1). Ampliar después si el tiempo lo permite.
3. **[IA]** Elegir entre 6 y 12 áreas/entregables a diagnosticar, usando la heurística de §3.3. No inventar áreas de relleno para llegar a un número redondo.
4. **[IA]** Reutilizar la carpeta `prototipos/preparacion-brechas/` si ya existe; si no, copiar el esqueleto HTML de §3.1 y adaptar los datos.
5. **[IA]** Completar el modelo mínimo por área (§3.3/§3.10): estado observado, fuente, evidencia, qué falta, criterio y siguiente acción. Los campos de gobernanza ampliada (§3.15–§3.18) pueden añadirse en una segunda pasada.
6. **[IA]** Declarar los cuatro indicadores con su denominador (§3.2) — nunca un porcentaje de preparación inventado.
7. **[IA]** Registrar bloqueos y riesgos reales si existen, aunque sea de forma mínima (§3.15); si no hay ninguno, declarar «ninguno observado», no omitir la sección. Confirmar la severidad final y el dueño cuando haya ambigüedad es **[Requiere humano]**.
8. **[IA]** Exportar un borrador (§3.6/§3.11) y verificar que abre, guarda y exporta sin errores (como mínimo los puntos 1, 6, 9 y 11 de §3.9).
9. **[IA]** Dejar seguimiento con fecha, alcance cubierto, lo que quedó pendiente y decisión pendiente (plantillas al final del documento).
10. **[IA]** Instalar la regla de mantenimiento de §5 en las instrucciones del repositorio para que el dashboard no quede huérfano tras esta sesión.

Los pasos 1–6, 8 y 9 son la ruta mínima accionable; el paso 7 y las secciones §3.14–§3.19 son ampliables según el tiempo y el riesgo del proyecto — "ampliable" no significa "nunca", sino que puede diferirse a una siguiente sesión con esa decisión registrada, no omitido en silencio. Ningún paso de esta ruta rápida es [Requiere humano] por sí solo: las decisiones humanas (aceptar, rechazar, autorizar) llegan en §4, después de que el borrador exista.

## 0.6. Diagrama de flujo de gobernanza

Colocado aquí, cerca del inicio, para no obligar a reconstruir el modelo mental leyendo solo la prosa dispersa de §4 y §3.18. Las etiquetas de nodo usan la convención de §0.4.

```mermaid
flowchart LR
    A["Borrador [IA]"] --> B["Revision registrada [IA]"]
    B --> C{"Decision [Requiere humano]"}
    C -->|aceptada| D["Tarea autorizada [Requiere humano]"]
    C -->|rechazada| H["Cerrado sin cambio"]
    C -->|diferida| I["review_by pendiente"]
    D --> E["Implementacion / verificacion [IA]"]
    E --> F["Actualizacion del dashboard [IA]"]
    F --> B
    I -. vence review_by .-> B
```

Cada flecha que cruza de un nodo [IA] a uno [Requiere humano] — y en particular la decisión misma — requiere una identidad distinta de la que originó el nodo anterior cuando el área es de `risk_category` alta (§3.18): quien redacta el borrador no debería ser, sin control cruzado, quien registra la decisión de aceptarlo. El detalle de cada paso de este flujo está en §4.

## Alcance y esfuerzo estimado

Primera maqueta local con 6–12 áreas y sin automatización: aproximadamente 1–2 sesiones de trabajo de una IA con acceso al repositorio. Añadir verificación automatizada (§3.16), métricas de cobertura ampliadas (§3.17) o meta-gobernanza (§3.18) es una ampliación posterior, no parte del mínimo viable inicial. Mantenimiento continuo (§5): minutos por tarea cerrada, siempre que el dashboard ya exista. Fusionar esta guía con otra equivalente (procedimiento al final del documento) es un ejercicio aparte, no incluido en estas estimaciones.

## Glosario de equivalencias

Distintas adaptaciones de esta guía han usado vocabulario distinto para los mismos conceptos. Esta tabla evita releer documentos completos para alinear términos al comparar o fusionar guías, o al leer un dashboard ya construido con otra terminología:

| Concepto genérico (esta guía) | Variante observada 1 | Variante observada 2 |
|---|---|---|
| Área o entregable a diagnosticar | «ficha» / `deliverable` | «DOR» (definition of ready) |
| Colección de áreas | `deliverables[]` | `deliverables[]` (mismo nombre, otro dominio) |
| Decisión humana sobre un área | `decision_status` | `decision_status` (mismo campo, otra autoridad) |
| Validación de un campo de texto | `validated: false` por campo | igual |
| Vista de preguntas sobre el primer uso | «Primera operación» / `profile` | «Perfil operativo» / `profile` |
| Vista de flujos o canales | «Flujos y canales» / `devices` | «Dispositivos» / `devices` |
| Checklist de aceptación | lista plana numerada | lista agrupada por categoría (fuentes, estructura, campos, borradores, exportación, pantallas, continuidad, paquete) |
| Inventario de menús/acciones reales del producto | «superficie funcional» (§1.1) | no definido como paso propio |
| Snapshot histórico de fuentes | `fuentes-iniciales.json` | no definido con ese nombre |
| Problema potencial futuro, no materializado | no modelado aparte de `blocker` | no modelado aparte de `blocker` |
| Problema ya materializado | `blocker` | `blocker` |
| Persona/rol que ejecuta un cambio | `owner_role` | `owner_role` |
| Persona/rol que da seguimiento mientras no hay dueño confirmado | no modelado | no modelado |

Al adoptar esta guía en un proyecto nuevo, conservar la columna «concepto genérico» como vocabulario de referencia y anotar en `seguimiento.md` qué término local equivale a cuál, en vez de mezclar ambos sin aviso.

## Petición reutilizable

> En el repositorio indicado, genera o mantén un «Dashboard de preparación y brechas» local para revisar datos, decisiones y evidencias pendientes respecto de su objetivo. Lee las reglas del repositorio y sus fuentes de verdad antes de trabajar. Incluye el inventario de menús, acciones y características actuales del producto, con sus recorridos, fuentes y validaciones pendientes; no te limites al plan y al backlog. Conserva una revisión explícita entre los borradores del dashboard y cualquier cambio del proyecto, con observaciones exportables por ficha. Clasifica cada área por nivel de riesgo e instala la obligación de revisar y actualizar el dashboard con cada avance. Sigue el procedimiento y los criterios de aceptación de esta guía. No publiques, hagas commit/push o modifiques sistemas operativos sin autorización vigente.

### Prompt listo para copiar en otro proyecto

```text
Proyecto destino: [ruta o repositorio]
Nombre visible: [nombre del proyecto]
Objetivo de revisión: [primer uso, siguiente entrega o fase real del proyecto]
Idioma: español, salvo indicación distinta.

Usa este documento completo como especificación. Construye el mismo tipo de
Dashboard de preparación y brechas: cinco menús en el mismo orden, resumen
con tabla y panel lateral, cuatro indicadores, fichas editables, preguntas,
tarjetas de flujos, fuentes, bloqueos/riesgos y decisiones agrupadas.
Reproduce las proporciones, paleta y comportamiento descritos en §3.1–3.9;
adapta la marca si el proyecto ya tiene una identidad definida y registra
esa adaptación.

Primero examina las reglas, requisitos, pendientes, documentación, código y
pruebas del proyecto, incluida su superficie funcional real (§1.1): menús,
módulos, flujos, API, CLI y procesos sin pantalla propia. Sustituye la marca,
IDs, áreas, preguntas, flujos, fuentes, discrepancias, bloqueos, riesgos,
decisiones y snapshot por datos del proyecto destino. No copies los
hallazgos ni las aprobaciones de ningún proyecto de referencia. Calcula los
contadores con los datos reales seleccionados; si algo es desconocido,
indícalo. Clasifica cada área por categoría de riesgo (§3.15) y exige
revisores distintos del implementador para las de riesgo alto (§3.18).

Entrega index.html autocontenido que abra mediante file:// sin instalación,
README, fuentes.json, seguimiento.md y evidencia de las comprobaciones
ejecutadas. Usa la carpeta existente si ya hay un dashboard equivalente; si
el proyecto ya tiene un seguimiento más simple, sigue la adopción incremental
de §3.19 en vez de reescribirlo todo de una vez. Implementa borradores solo
en memoria, ejemplos protegidos contra sobrescritura, exportación JSON
explícita (v1 u v2, documentando cuál) y reinicio con confirmación. Conserva
la revisión humana antes de modificar fuentes oficiales, exige que toda
decisión de autoridad apunte a evidencia externa verificable (§3.18) y que
quien implementa un cambio no sea también quien lo marca como verificado.
Instala la regla de mantenimiento de §5 respetando las instrucciones
locales y verifica la aceptación de §3.9. Avanza con la información
disponible; registra como pendientes las decisiones de producto que no
puedas resolver con fuentes y autorización existentes.
```

La estructura y las interacciones se conservan; el contenido se obtiene del nuevo proyecto. Este archivo es una especificación para generar la interfaz, no una copia ejecutable de un HTML concreto ni una garantía de reproducción exacta de cada píxel.

## 1. Descubrir el proyecto

1. Confirmar raíz, reglas AGENTS/CLAUDE, README, fuentes de requisitos, plan/backlog, tareas y estado. Respetar reglas anidadas y permisos del entorno.
2. Inspeccionar rama, HEAD y cambios existentes. Trabajar en una rama aislada según las reglas locales; preservar cambios ajenos. Registrar si la rama hereda trabajo sin commit.
3. Identificar objetivo, fase, actores, flujos, plataformas, límites y qué está implementado, documentado, simulado o sin verificar. Leer código o pruebas pertinentes sin acceder a datos sensibles o servicios innecesarios.
4. Registrar archivos y secciones exactas, fecha de revisión, HEAD y cambios locales relevantes. El HEAD por sí solo no describe un árbol con cambios sin commit; usar hashes de fuentes cuando proceda (algoritmo y normalización en §3.16). Si falta evidencia, marcar «por verificar».

### 1.1. Inventariar la superficie funcional

1. Leer la navegación y los componentes o módulos reales: menús principales, submenús, acciones contextuales, ajustes, diálogos, herramientas y accesos auxiliares. Conservar los nombres que el usuario ve en el producto.
2. Incluir características que no tengan menú propio: API, CLI, procesos en segundo plano, importación/exportación, recuperación, almacenamiento, accesibilidad, operación sin conexión y otros flujos pertinentes. Si no se revisaron, declarar esa cobertura pendiente; no inventar una pantalla.
3. Para cada función registrar ID local estable, módulo o menú, recorrido, propósito, acciones y condiciones relevantes, alcance de datos o usuario, fuente de implementación, evidencia disponible, criterio de prueba y siguiente acción. Agrupar acciones relacionadas sin perder su trazabilidad.
4. Distinguir «presente en código», «probado en ejecución» y «aceptado por el usuario». Leer un botón y su manejador solo acredita su presencia en código; no demuestra persistencia, aislamiento, éxito de una API o uso correcto de un modelo. Las pruebas del dashboard verifican la maqueta, no el producto.
5. Contrastar el inventario con requisitos, ADR y backlog. Si una función existe pero su issue sigue abierto, registrar la conciliación pendiente por criterio de aceptación. No clasificarla como «no iniciada» solo por el estado del issue, ni cerrar el issue solo por encontrar el control.
6. Declarar cobertura, exclusiones y denominadores: funciones inventariadas, módulos revisados y recorridos ejecutados. Mantener estos conteos separados de criterios de salida del MVP y de aprobaciones. Obtener los conteos de los datos ejecutados, no de una cifra escrita manualmente en el README.

## 2. Diseñar el diagnóstico

Usar los identificadores reales del proyecto. Para áreas nuevas, declarar IDs locales de seguimiento, sin sustituir requisitos existentes. No copiar DOR, gates, nombres de personas o requisitos fiscales de otro proyecto.

Cada área debe mostrar: ID, pregunta o brecha, estado observado, fuente, evidencia disponible, qué falta, criterio de verificación y siguiente acción. Registrar responsable únicamente cuando esté confirmado; un rol sugerido no es una persona asignada.

Separar tres dimensiones: estado de implementación, estado de verificación y decisión humana. Código observado no equivale a funcionamiento probado; texto completo no equivale a requisito satisfecho. Mostrar contradicciones entre documentos y código en vez de resolverlas silenciosamente. Los indicadores deben declarar su denominador y alcance; evitar porcentajes ficticios de preparación.

Clasificar cada área por categoría de riesgo/impacto desde esta etapa de diseño, no después de implementarla (modelo completo en §3.15 y regla de revisores en §3.18): una revisión homogénea que trate igual un ajuste cosmético y un cambio legal, fiscal o de seguridad pierde la oportunidad de exigir más revisores o mayor autoridad a tiempo.

## 3. Construir la maqueta local

Respetar la tecnología y el diseño del repositorio. Si todavía no existe una aplicación apropiada, puede usarse HTML/CSS/JavaScript autocontenido en `prototipos/preparacion-brechas/`. Reutilizar una carpeta existente en lugar de duplicar dashboards; si ya existe un seguimiento más simple (listas de pendientes, un `requirements.md`), seguir la adopción incremental de §3.19 en vez de reescribirlo todo de una vez.

Incluir resumen, áreas/brechas, preguntas, flujos/canales, fuentes, bloqueos/riesgos y decisiones. Ofrecer búsqueda, filtros, fichas con etiquetas, ejemplos sintéticos opcionales y exportación explícita de borrador. Mantener los ejemplos separados de evidencia real y no sobrescribir borradores sin confirmación.

Si la edición queda en memoria, advertir que recargar/cerrar pierde lo no exportado. No prometer importación, persistencia o sincronización automática sin implementarlas y verificarlas. Exportar con `prototype_only: true` y `validated: false`, además de proyecto, revisión/fecha y versión de esquema cuando se incorporen esos metadatos. Revisar contenido antes de compartir. No precargar ni guardar secretos, datos personales o de clientes en Git.

### 3.1. Estructura visual que debe reproducirse

Construir una aplicación de una sola página con cinco vistas, sin recargas ni rutas de servidor. La vista inicial es **Resumen** (ID estable `overview`). Los cuatro indicadores y el encabezado general permanecen visibles en todas las vistas; cambiar de menú sustituye el contenido de la vista, la miga de navegación, el antetítulo, el título y su descripción.

Distribución de escritorio:

```text
┌──────────────────────┬──────────────────────────────────────────────────┐
│ Marca del proyecto   │ Proyecto / vista actual      Snapshot · Revisión │
│ Preparación y brechas├──────────────────────────────────────────────────┤
│                      │ Aviso: prototipo local, borradores sin validación │
│ Resumen              │ Antetítulo, título, descripción  Ejemplo/Descargar │
│ Primera operación   │ [Áreas] [Campos] [Discrepancias] [Validaciones]    │
│ Flujos y canales     ├──────────────────────────────────────────────────┤
│ Fuentes y            │ Contenido de la vista seleccionada               │
│ discrepancias        │ En el resumen: tabla amplia + columna de siguiente│
│ Decisiones           │ paso, bloqueos/riesgos; debajo, secuencia de revisión│
│                      ├──────────────────────────────────────────────────┤
│ Fase y límites       │ Pie: proyecto, snapshot, fuentes, sin backend    │
└──────────────────────┴──────────────────────────────────────────────────┘
```

Referencia de estilo: interfaz clara, sobria, con navegación de color oscuro sólido, tarjetas blancas, bordes suaves, iconos lineales SVG incluidos en el HTML y abundante separación entre bloques. No requiere fuentes, imágenes, iconos, librerías o CDN externos.

| Elemento | Valor de referencia 1 | Valor de referencia 2 (variante observada) |
|---|---|---|
| Fondo / superficie | `#f6f8fa` / `#ffffff` | `#f5f6f3` / `#ffffff` |
| Texto / texto secundario | `#142b41` / `#617185` | `#20332c` / (equivalente) |
| Sidebar y botón principal / acento | `#0b2540` / `#285475` | `#183e31` / `#d8edb5` |
| Bordes / fondo de selección | `#dde4ec` / `#edf3fa` | (equivalente, otra paleta) |
| Advertencia | texto `#805014`, fondo `#fff5e4` | (equivalente) |
| Discrepancia | texto `#9f4137`, fondo `#fbefed` | (equivalente) |
| Tipografía | `Segoe UI, Arial, sans-serif`; IDs en monospace del sistema | igual |
| Base / interlineado | 14 px / 1.55 en escritorio | igual |
| Sidebar | 228 px, sticky, alto de viewport; 205 px hasta 1200 px | igual |
| Barra superior | 79 px de alto; 70 px en móvil | igual |
| Contenido | ancho máximo 1530 px, padding horizontal 36 px en escritorio | igual |
| Tarjetas | radio 14 px, borde 1 px, sombra tenue | igual |
| Resumen | tabla flexible + columna derecha de 294 px; separación 22 px | igual |
| Indicadores | cuatro columnas; valor grande de unos 34 px | igual |
| Ventana de detalle | ancho máximo 680 px, alto máximo 90dvh, scroll interior | igual |

Ambas paletas de referencia son ejemplos reales observados en proyectos distintos, no un requisito de color. Elegir tokens propios o heredar la identidad existente del repositorio; comprobar contraste de cada combinación en vez de asumirlo por copiar una tabla. Incluir estados hover, foco visible, selección y mensajes de resultado.

**Redacción del antetítulo y el título como enunciado de propósito (opcional):** una variante observada en un proyecto de referencia separa el antetítulo en dos niveles — una leyenda fija en la barra lateral (p. ej. «Preparación y brechas») y un antetítulo de vista que no repite el nombre del menú, sino que añade contexto breve (p. ej. «Ejercicio de revisión / <Proyecto>», «Diez preguntas para acotar la revisión», «Documentación y código observado») — y redacta el título (`<h1>`) de cada vista como un enunciado breve de una o dos oraciones cortas que declara el propósito o la actitud de esa vista frente al diagnóstico (p. ej. «Ver lo que falta. Distinguir lo que existe.», «No todo tiene el mismo alcance.», «Cada afirmación, con su fuente.»), en vez de una frase puramente descriptiva del contenido. La descripción (`<p>`) que sigue conserva entonces el alcance y la advertencia explícitos, que el título por sí solo no debe cargar. Esta convención es opcional: puede sustituirse por un título literal y descriptivo si el proyecto destino lo prefiere. Si se adopta, redactar un enunciado distinto por cada una de las cinco vistas — no una frase genérica repetida — y no dejar que la brevedad del título omita la advertencia de alcance de la descripción.

**Componentes visuales adicionales observados en la referencia Nexia (look and feel completo, opcional):** la tabla de §3.1 ya documenta como «Valor de referencia 1» la paleta exacta de este proyecto real; lo que sigue es el resto del look and feel de su `index.html` que esa tabla, centrada en color y proporción, no detallaba. Adoptar cualquiera de estos puntos es independiente de los demás — no es un paquete de todo o nada:

| Componente | Detalle observado |
|---|---|
| Botones | Tres variantes con el mismo alto mínimo de 44 px: `primary` (relleno con el color de acento/sidebar, texto blanco, usado para la acción principal de una vista o ficha), `secondary` (contorno 1 px, fondo blanco, texto del color de texto principal, usado para acciones alternativas) y `text` (sin borde ni fondo, color de acento, subrayado solo al pasar el cursor, usado para acciones terciarias como «Quitar filtros»). Radio de 8 px, distinto del radio de 14 px de las tarjetas. |
| Iconos | SVG lineales de 20×20 px por defecto, `stroke-width` ~1.65, extremos y uniones redondeados (`stroke-linecap`/`stroke-linejoin: round`), sin relleno (`fill:none`) — un único set de trazo fino en vez de mezclar iconos lineales y de relleno. |
| Insignias de estado (`badge`) | Cuatro variantes de color con texto y fondo suaves del mismo tono (nunca color puro de fondo): `pending` (ámbar/tierra), `red` (discrepancia/riesgo), `green` (acento, aprobado/en curso) y `neutral` (gris). Mismo componente reutilizado en tabla, tarjetas y ficha de detalle — no un estilo de etiqueta distinto por vista. |
| Tarjeta «El siguiente paso» (decorativa) | Además de la estructura de cuatro partes de §3.2, esta tarjeta lleva un fondo de acento suave propio (distinto del blanco de las demás tarjetas) y un elemento puramente decorativo — p. ej. un par de círculos concéntricos parcialmente recortados en una esquina, generados por CSS (`::after`), sin texto ni función interactiva. Es ornamental: omitirlo no cambia ninguna regla de §3.2; añadirlo no debe interferir con el foco ni el texto. |
| Indicador de fase en la barra lateral | Debajo de la navegación, un bloque fijo opcional muestra la fase actual del proyecto como texto breve más una fila de segmentos horizontales (uno por fase conocida, el primero resaltado con el color de acento) — una barra de progreso de fases del *producto*, distinta de los cuatro indicadores de §3.2 (que miden la revisión) y distinta también de la línea de tiempo de hitos de §3.20 (que es por hito, con fecha y detalle, no una franja de progreso). |
| Foco visible | Contorno de 3 px en un tono de acento con separación (`outline-offset`) de 3 px respecto al control, aplicado de forma uniforme a botones, enlaces y campos — más grueso que un `outline` de navegador por defecto, para que sea perceptible sobre fondos claros y oscuros de la barra lateral. |
| Perfil local en la barra superior | Un avatar circular de iniciales (color de fondo suave, sin foto ni dato real) junto a un texto corto, para anclar visualmente «quién revisa» sin implicar autenticación real ni cuenta de usuario — se mantiene ficticio o se omite si el proyecto no tiene aún roles de revisor nombrados. |

Estos siete puntos son un catálogo a elegir, no una lista obligatoria: adoptar los que aporten valor al proyecto destino y declarar en `seguimiento.md` cuáles se tomaron de esta referencia, igual que con cualquier otra convención opcional de esta guía.

**Esqueleto HTML copiable (opcional):** punto de partida para no ensamblar la estructura completa a mano a partir de fragmentos dispersos del documento. Sustituir cada comentario `<!-- ... -->` y cada `TODO` antes de considerar la maqueta terminada; este esqueleto no es un formulario universal ni acredita por sí mismo ninguna de las secciones §3.2–§3.13.

```html
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="Diagnóstico local de preparación y brechas">
  <title>PROYECTO · Preparación y brechas</title>
  <style>/* TODO: tokens, distribución, componentes, estados y media queries de §3.1/§3.7 */</style>
</head>
<body>
  <a class="skip" href="#main-content">Saltar al contenido</a>
  <div class="shell">
    <aside id="sidebar" aria-label="Navegación principal">
      <nav id="nav" aria-label="Preparación y brechas"></nav> <!-- TODO: 5 menús de §3.2 -->
    </aside>
    <div class="workspace">
      <header class="topbar"><!-- TODO: menú móvil, proyecto/vista, snapshot y revisión --></header>
      <main id="main-content" tabindex="-1">
        <div class="notice"><!-- TODO: aviso de borrador, memoria local y límites --></div>
        <header class="page-head"><h1 id="page-title"></h1></header>
        <section class="stats" aria-label="Indicadores de la revisión"></section> <!-- TODO: 4 indicadores de §3.2 -->
        <section id="view-overview" aria-label="Resumen"></section>
        <section id="view-profile" aria-label="Primera operación" hidden></section>
        <section id="view-devices" aria-label="Flujos y canales" hidden></section>
        <section id="view-evidence" aria-label="Fuentes y discrepancias" hidden></section>
        <section id="view-decisions" aria-label="Decisiones" hidden></section>
        <footer><!-- TODO: fuentes, fecha de revisión, seguimiento --></footer>
      </main>
    </div>
  </div>
  <dialog id="detail-dialog" aria-labelledby="detail-title">
    <h2 id="detail-title"></h2><form id="detail-form"></form> <!-- TODO: §3.4 -->
  </dialog>
  <dialog id="confirm-dialog" aria-labelledby="confirm-title">
    <h2 id="confirm-title">Reiniciar el borrador</h2> <!-- TODO: §3.5 -->
  </dialog>
  <div id="toast" role="status" aria-live="polite"></div>
  <script>/* TODO: datos reales, draft[] independiente, renderizado y eventos — §3.3/§3.8 */</script>
</body>
</html>
```

Separar datos revisados, respuestas locales y presentación. Estructuras sugeridas: `project`, `sources`, `deliverables`, `questions`, `devices`, `decisions`, `blockers`, `risks`, `navItems` y `draft`. Las listas generan vistas y contadores desde la misma colección. No usar índices de posición como ID de registros que puedan reordenarse. No inyectar texto de borradores con `innerHTML`: usar `textContent`/`value` o escape contextual.

### 3.2. Los cinco menús y su contenido

| Orden / ID estable | Menú visible / clave de vista | Contenido y acciones |
|---|---|---|
| 1 / `overview` | **Resumen** | Tabla de áreas, filtros, búsqueda, apertura de fichas, siguiente paso, bloqueos/discrepancias destacadas y secuencia de revisión. |
| 2 / `profile` | **Primera operación** | Cuadrícula de preguntas sobre el primer uso o siguiente objetivo. Cada tarjeta tiene ID de pregunta, ID de área relacionada, título, explicación, estado «Respuesta por validar» y botón **Revisar campos** que abre esa ficha. |
| 3 / `devices` | **Flujos y canales** | Tarjetas de flujos, integraciones, canales o dispositivos pertinentes. Mostrar icono, nombre, explicación, estado documental y estado de ejecución separado; botón **Revisar evidencia** hacia la ficha vinculada. La clave interna `devices` no limita esta vista a dispositivos. |
| 4 / `evidence` | **Fuentes y discrepancias** | Una entrada por área con ID, título, archivo/sección, criterio o límite, estado documental y botón **Abrir ficha**. Encabezado con **Revisar evidencia** hacia el área de pruebas; leyenda de evidencia no ejecutada y roles sin nombramiento cuando corresponda. |
| 5 / `decisions` | **Decisiones** | Lista filtrada por familias propias del proyecto (p. ej. **Preparación**, **Mejoras**, **Técnica**). Cada entrada muestra ID, título, explicación y estado. Adaptar el significado de cada familia a la fase real. |

El menú activo usa `aria-current="page"`, icono y fondo claro. Los contadores del menú representan respectivamente áreas, preguntas, flujos, entradas de fuentes y total de decisiones en todas las familias; calcularlos siempre desde las colecciones de datos, nunca como número fijo en el HTML.

En otro dominio se permite renombrar **Primera operación** como «Contexto y preguntas» y **Flujos y canales** como «Dispositivos» o «Canales y compatibilidad»: registrar el mapeo nombre-visible → ID-estable en `seguimiento.md` y conservar la posición y el propósito de la vista. No arrastrar vocabulario, DOR, gates o RACI de un dominio ajeno al renombrar.

**Resumen, en detalle:**

- Tabla con columnas **Área / datos de revisión**, **Rol de revisión**, **Estado documental** y botón de apertura con nombre accesible. Mostrar icono, título, ID y número de campos pendientes por área.
- Filtros **Todos**, **Sin datos**, **Con borrador**. «Sin datos» significa cero campos guardados con texto; «Con borrador» significa al menos uno. No son filtros de implementación o aprobación.
- Buscar sin distinguir mayúsculas en ID, título, estado y rol; combinar búsqueda con el filtro activo. Una cadena vacía muestra todos los resultados del filtro.
- Sin coincidencias: explicación y botón **Quitar filtros**, que vacía la búsqueda y vuelve a **Todos**.
- Pie de tabla: resultados visibles sobre total de áreas, aviso de ausencia de veredicto y botón **Reiniciar borrador**.
- Columna lateral: tarjeta **El siguiente paso**, con acción que abre el área de alcance; tarjeta **Fuentes por conciliar**, con discrepancias identificadas, descripción y estado; tarjeta **Riesgos abiertos**/**Bloqueos abiertos** cuando existan (modelo en §3.15). Si no se observaron discrepancias, riesgos o bloqueos, indicar ese alcance sin inventarlos.
- **Cada entrada de discrepancia, riesgo o bloqueo en estas tarjetas debe ser interactiva, no solo texto informativo**: un botón/elemento clickeable que abra una ficha de detalle (reutilizando el mismo `<dialog>` y mecanismo de apertura de §3.4, o uno compartido entre discrepancias/riesgos/bloqueos si eso evita duplicar diálogos casi idénticos) con el registro completo — para una discrepancia, su descripción íntegra y la fuente/evidencia exacta que la originó (documento, sección, commit); para un riesgo o bloqueo, los campos de §3.15 (`mitigation_plan`/`contingency_plan`, `owner_role`, `status`, `severity`, `review_by`/`due_at`) más los de §9 cuando se adopte esa capa. Mostrar solo el resumen en la tarjeta y no ofrecer ninguna forma de ver el resto es un patrón detectado como brecha real en una revisión de usuario: «no hay liga para ver el detalle de la evidencia o de las decisiones» — no repetirlo en una implementación nueva.
- Secuencia visual inferior: **01 · Alcance → 02 · Evidencia → 03 · Decisiones → 04 · Validación**. Es una secuencia de trabajo, no progreso certificado. **Cada paso que corresponda a una vista o ficha real del dashboard debe ser un botón que navegue ahí** (abrir la vista «Fuentes y discrepancias» desde «02 · Evidencia», la vista «Decisiones» desde «03 · Decisiones», la ficha del área de alcance desde «01 · Alcance» — reutilizando el mecanismo de apertura de vista/ficha ya existente, sin añadir lógica nueva de navegación). Un paso sin vista ni ficha equivalente (p. ej. «04 · Validación» cuando la validación real está fuera de la maqueta) puede quedar sin enlace — declararlo explícitamente como fuera de alcance en la propia etiqueta del paso es preferible a simular un destino que no existe.

**Estructura de cuatro partes de la tarjeta «El siguiente paso» (detalle de la columna lateral):** una variante observada en un proyecto de referencia le da a esta tarjeta una composición fija: (1) una etiqueta superior (`eyebrow`) con el texto fijo «El siguiente paso»; (2) un título breve (`<h2>`) redactado como acuerdo o acción pendiente, no como descripción (p. ej. «Acordar el primer uso.»), siguiendo la misma convención opcional de enunciado que el título de página (ver más arriba en §3.1); (3) una sola oración que nombra qué falta resolver — útil cuando cubre a la vez qué se ofrece, qué sigue siendo manual y qué evidencia falta para operar, sin degenerar en una lista larga de viñetas; y (4) un botón primario con icono de flecha que abre la ficha del área que efectivamente define el alcance del proyecto (`data-open` apunta a ese ID real, no a un área arbitraria ni a la primera de la lista). Adaptar el texto de las tres partes a la brecha más relevante y vigente del proyecto destino en cada actualización del dashboard (§5); no conservar «Acordar el primer uso» ni ningún otro texto literal de un proyecto de referencia si ya no corresponde al estado actual.

**Indicadores comunes:**

| Indicador | Regla de cálculo y significado |
|---|---|
| Áreas de revisión | Cantidad de áreas seleccionadas; aclarar que no es el backlog completo. |
| Campos por responder | Total de campos menos campos guardados con texto, sobre total de campos. El progreso representa texto del borrador, siempre «sin validar». |
| Discrepancias seleccionadas | Cantidad de discrepancias documentales destacadas, con su alcance. No equivale a fallos probados del producto. |
| Validaciones del producto aquí | Ejecuciones del producto acreditadas en esta revisión. En una revisión exclusivamente documental es cero; las pruebas de esta maqueta no aumentan este número. |

Estos cuatro indicadores miden llenado de formulario y alcance documental, no verificación real. Para una segunda familia de métricas centrada en verificación y decisión, ver §3.17 — no sustituye a estos cuatro, los complementa.

**Indicador opcional: bugs conocidos.** Cuando el proyecto ya distingue, con una etiqueta propia (por ejemplo `bug-conocido`), un defecto confirmado de una simple «brecha activa» o «pendiente de conciliación», se puede añadir una quinta tarjeta al Resumen, junto a los cuatro indicadores anteriores, con el conteo de áreas con esa etiqueta y, dentro de la misma tarjeta, un botón de acceso directo por cada una hacia su ficha — sin pasar por búsqueda ni filtros. Reglas:

- Es aditivo: no sustituye ni se promedia con los cuatro indicadores base. Si no hay ninguna etiquetada, la tarjeta declara «ninguno etiquetado como bug conocido por ahora» en vez de ocultarse o mostrar un cero sin explicación.
- El conteo y la lista de botones salen siempre de filtrar la misma colección de áreas por esa etiqueta, nunca de un número o una lista escritos a mano. No etiquetar un issue del backlog como bug conocido solo para poblar la tarjeta: la etiqueta se reserva para un defecto ya confirmado, con su propia ficha de evidencia.
- Los botones de acceso directo reutilizan el mismo mecanismo de apertura de ficha que el resto del dashboard (§3.4); no crean una vista, modal o ruta aparte.

Adoptar este patrón implica también añadir la fila correspondiente a la matriz de §3.13.

### 3.3. Áreas y modelo de datos reutilizable

Usar una única colección de áreas como origen de tabla, fichas, fuentes y exportación. Las preguntas y los flujos apuntan a un ID existente. Las decisiones, bloqueos y riesgos necesitan IDs únicos y trazabilidad propia (modelo en §3.15). Ejemplo sintético de estructura:

```json
{
  "id": "PR-01",
  "title": "Alcance de la primera operación",
  "icon": "briefcase",
  "owner": "Rol sugerido de producto; sin nombramiento",
  "status": "Por definir",
  "kind": "pending",
  "priority": "Antes del piloto",
  "risk_category": "funcional",
  "short": "Acordar usuarios, flujos y exclusiones.",
  "source": "Documento real y sección por identificar",
  "acceptance": "Acordar alcance, fuente de decisión y evidencia necesaria.",
  "fields": [
    {"key":"audience","label":"Usuarios y contexto","hint":"Sin datos personales.","example":"Ejemplo sintético de perfil"},
    {"key":"flows","label":"Flujos incluidos","hint":"Distinguir pasos manuales.","example":"Flujo de demostración"},
    {"key":"limits","label":"Exclusiones y límites","hint":"No ampliar alcance sin decisión.","example":"Límites por revisar"},
    {"key":"evidence","label":"Evidencia y siguiente acción","hint":"Referencia, decisión y verificación.","example":"Sin validación real"}
  ]
}
```

Este objeto no es un hallazgo listo para incorporar. Sustituir sus fuentes y textos a partir del repositorio. `kind` solo controla la apariencia de una etiqueta; el estado debe explicarse también con palabras. `owner` es el rol de revisión, no una asignación confirmada. `risk_category` es el enum de §3.15/§3.18 y determina si el área necesita revisores adicionales. Conservar un objeto separado `draft[areaId][fieldKey]` para que el texto no modifique los datos observados.

**Heurística de cuántas áreas son suficientes:** no existe un número universal correcto, pero estas tres reglas evitan tanto omitir cobertura como inflar el inventario:

1. Una entrega o hito real del roadmap del proyecto puede corresponder a un área; no crear un área por cada tarea individual del backlog.
2. Si un área acumula más de 8 campos o mezcla criterios de aceptación independientes, dividirla en dos áreas con IDs propios en vez de sobrecargar una ficha.
3. Mantener el total visible sin agrupar por debajo de ~12 áreas; si el proyecto tiene más frentes reales, agruparlas por categoría (ver `category` en §3.10) y mostrar el detalle dentro de cada grupo en vez de una tabla plana interminable.

Documentar la decisión de número en `seguimiento.md` cuando no coincida con un ejemplo de referencia, y recalcular todos los denominadores de §3.2 al cambiarlo.

Mantener diez áreas y cuatro campos por área solo cuando ese número represente bien al proyecto destino; si las fuentes requieren otro número, adaptar sin inventar áreas de relleno, documentar el cambio y recalcular todos los denominadores. No reutilizar prefijos ni conceptos de dominio de un proyecto de referencia si no corresponden al destino.

Para un punto de partida sin vocabulario de ningún dominio concreto, ver el **Anexo A — ejemplo mínimo neutral**, al final de este documento, etiquetado como patrón a copiar. El **Anexo B** conserva un inventario real completo de un proyecto de referencia, etiquetado como lectura histórica, no como plantilla a copiar.

### 3.4. Fichas, guardado y cancelación

Abrir la misma ficha desde tabla, pregunta, flujo, fuentes o siguiente paso. Usar un `<dialog>` modal con título accesible, cabecera sticky y botón **Cerrar detalle**. Incluir ID, título, rol, estado y fuente; aviso de borrador local; los campos definidos para esa área; y un desplegable **Qué debe revisarse antes de resolver esta área** con el criterio de verificación.

Cada campo lleva etiqueta, ID, ayuda asociada y `textarea` con límite de 1200 caracteres, redimensionable verticalmente. Los campos comienzan vacíos y se cargan desde el borrador al abrir la ficha.

- **Guardar borrador**: copiar valores recortando espacios exteriores al objeto en memoria, cerrar la ficha, recalcular indicadores/filtros y anunciar el resultado. No cambiar el estado documental, fuentes, decisiones o requisitos.
- **Cancelar**, **Cerrar detalle** o **Escape**: descartar ediciones aún no guardadas y devolver el foco al control que abrió la ficha. Conservar lo guardado anteriormente en la sesión.
- Después de guardar, el texto aparece al reabrir desde cualquier vista, porque todas comparten el mismo borrador.
- Avisar que cerrar o recargar la pestaña pierde el borrador. No añadir localStorage, importación, backend o guardado automático como si fueran parte del original.

### 3.5. Acciones globales y mensajes

| Acción | Comportamiento exigido |
|---|---|
| **Cargar ejemplo** | Si todos los campos guardados están vacíos, copiar ejemplos sintéticos en todas las fichas y marcar el modo de ejemplo. Si hay al menos un campo con texto, bloquear la carga y explicar cómo conservar o reiniciar el borrador. No sobrescribirlo. |
| **Descargar borrador** | Exportar únicamente el borrador guardado en memoria como JSON UTF-8 mediante `Blob` y enlace de descarga. No incluir ediciones de un modal sin guardar. No contactar servicios externos. |
| **Reiniciar borrador** | Abrir confirmación: **Cancelar** conserva todo; **Reiniciar** vacía campos, desactiva modo de ejemplo y recalcula indicadores sin alterar estados oficiales. Advertir que se puede cancelar y descargar antes. |
| Notificaciones | Mensajes temporales con `role="status"` y `aria-live="polite"`, unos 4.5 segundos. Informar guardado local, bloqueo de ejemplos, descarga o reinicio sin afirmar validación. |

El modo de ejemplo permanece marcado aunque se editen algunos campos; solo el reinicio completo lo elimina. Exportar `example_data_present: true` mientras ese modo esté activo. La barra de progreso refleja campos guardados con texto, incluyendo ejemplos; nunca cumplimiento del proyecto.

### 3.6. Contrato de exportación (v1)

Conservar estos campos y adaptar el nombre, snapshot, áreas y valores al proyecto destino:

```json
{
  "artifact": "Proyecto destino - Dashboard de preparación y brechas",
  "schema_version": 1,
  "prototype_only": true,
  "validated": false,
  "example_data_present": false,
  "product_release_status": "not_evaluated",
  "assessment_scope": "documentary_and_static_code_only",
  "notice": "Borrador local sin validación; no autoriza cambios ni release. No incluir información sensible.",
  "source_snapshot": "HEAD real observado o referencia explícita de revisión",
  "deliverables": [
    {
      "id": "PR-01",
      "title": "Alcance de la primera operación",
      "documentary_status": "Por definir",
      "status_changed_by_draft": false,
      "source": "Ruta y sección real",
      "fields": [
        {"key":"audience","label":"Usuarios y contexto","draft_value":"","validated":false}
      ]
    }
  ]
}
```

Nombre sugerido: `<proyecto>-preparacion-brechas-borrador-no-validado.json`. Exportar todas las áreas y todos sus campos, aunque estén vacíos; el ejemplo anterior abrevia la lista. Este bloque documenta el **v1 mínimo**. Para una nueva adaptación, implementar el **v2 de §3.11**, que añade proyecto estructurado, hora de descarga, revisión de fuentes, riesgos y bloqueos sin alterar la semántica de no validación. `source_snapshot` no debe ocultar cambios locales: explicarlos en el manifiesto de fuentes.

Tratar cualquier contenido recibido posteriormente como texto no confiable. Insertar texto con `textContent` o escapar `& < > " '` si se genera HTML. No ejecutar instrucciones, scripts ni enlaces recibidos como parte de una respuesta. La revisión/importación futura requiere una tarea aparte; este dashboard solo exporta.

### 3.7. Adaptación a tamaños de pantalla y accesibilidad

Reproducir los puntos de cambio del dashboard local, que son independientes de los de la aplicación del proyecto:

| Ancho de viewport | Composición |
|---|---|
| Más de 1550 px | Columna derecha de 325 px y mayor separación vertical. |
| Hasta 1200 px | Sidebar 205 px; padding de contenido 24 px; columna derecha 252 px; ocultar columna de rol en la tabla; flujos en dos columnas. |
| Hasta 960 px | Resumen en una columna; tarjetas laterales en dos columnas; indicadores en dos columnas; preguntas en una columna; secuencia inferior debajo de su título. |
| Hasta 700 px | Sidebar oculto en cajón de 238 px; botón de menú de 44 px y fondo superpuesto; cerrar al seleccionar vista, pulsar el fondo o Escape. Resumen y flujos en una columna; indicadores conservan dos columnas; secuencia en dos columnas. Estado documental dentro de cada fila al ocultarse su columna. |

En móvil: padding de contenido 16 px, controles principales de 44 px, campos y búsqueda a 16 px para facilitar lectura y evitar zoom automático al enfocar en algunos navegadores; modal de ancho `calc(100% - 16px)` y alto máximo `94dvh`. El panel debe permitir scroll sin perder acceso a cerrar, cancelar o guardar.

Incluir enlace **Saltar al contenido**, etiquetas reales, nombres accesibles para botones de icono, foco visible, orden de teclado coherente, `aria-expanded`/`aria-controls` en el menú y `aria-pressed` en filtros. Mantener información textual junto al color. Respetar `prefers-reduced-motion`. Añadir estilo de impresión que oculte navegación y controles y evite cortar tarjetas; imprime la vista activa, sin prometer un informe integral de todas las vistas.

Verificar al menos 375×812, 768×1024, 1024×768 y 1440×1100, zoom al 200 %, teclado, texto largo y cero resultados. No debe desplazarse horizontalmente toda la página; si una tabla necesita desplazamiento, limitarlo a su contenedor y mantener accesible su detalle. Estos patrones no acreditan accesibilidad exhaustiva ni usabilidad en hardware físico por sí solos: verificar contraste y teclado en cada adaptación.

### 3.8. Archivos y organización técnica

```text
prototipos/preparacion-brechas/
  index.html                    # HTML, CSS, iconos SVG, datos y JavaScript locales
  README.md                     # Cómo abrir, alcance, interacción, exportación y límites
  fuentes.json                  # Archivos/secciones, revisión, hashes y cambios locales
  fuentes-iniciales.json        # Snapshot histórico previo a la última actualización del manifiesto
  hitos-alcance.json            # Ampliación (§3.16): fechas de cambios de alcance mayor, para el segundo disparador de vigencia
  seguimiento.md                # Avances y propuestas/decisiones
  verificar-fuentes.mjs         # Ampliación (§3.16): recalcula hashes y marca fuentes desalineadas por tiempo o por hito de alcance
  verificar-evidencia.mjs       # Ampliación (§3.16): resuelve source_refs[]/evidence_refs[] contra el repo real; marca referencias rotas/desactualizadas
  validar-exportacion.mjs       # Ampliación (§3.16): valida un export.json contra el JSON Schema, incluida la regla "sin excepción" de §3.18
  diff-exportaciones.mjs        # Ampliación (§3.16): compara dos snapshots y lista qué cambió
  schema-exportacion-v1.json    # Ampliación (§3.6/§3.16): JSON Schema del contrato v1
  schema-exportacion-v2.json    # Ampliación (§3.11/§3.16): JSON Schema del contrato v2, con la condición if/then de §3.18
  verificacion.json             # Solo resultados de comprobaciones realmente ejecutadas
  historico/
    export-AAAA-MM-DD.json      # Un snapshot por exportación relevante, para diff histórico (§3.17)
  vista-escritorio.png          # Captura real si se ejecutó navegador
  vista-movil.png               # Captura real si se ejecutó navegador
docs/
  mantenimiento-dashboard.md
  DASHBOARD_PREPARACION_BRECHAS_IA.md
```

Conservar `fuentes-iniciales.json` u otro snapshot histórico antes de actualizar un manifiesto existente. Los archivos de estado, tarea, resultado y handoff se crean según las convenciones locales, sin imponer una carpeta de agentes ajena al proyecto. Esta guía debe poder viajar sola: las rutas anteriores son destinos sugeridos, no archivos que otra IA deba tener previamente.

**Opcional en el mínimo, obligatorio en la ampliación — un solo criterio, no dos:** los artefactos marcados «ampliación» arriba (`hitos-alcance.json`, los tres scripts de verificación, los dos JSON Schema) son opcionales en el dashboard mínimo de §0.5/§3.1–§3.9: una primera maqueta sin ellos sigue siendo válida. Pasan a ser **obligatorios, sin excepción**, en dos casos, y solo en esos dos: (a) al declarar implementada la ampliación de §3.11/§3.16 — no se anuncia «implementé la v2» sin también implementar y correr `validar-exportacion.mjs` contra su schema; y (b) en cualquier dashboard, mínimo o ampliado, que tenga al menos un área de `risk_category` `legal_fiscal_seguridad` o `datos_personales` — porque sin `schema-exportacion-v2.json` y `validar-exportacion.mjs` la regla «sin excepción» de §3.18 para esas áreas queda solo en prosa, nunca comprobada. Fuera de esos dos casos, son plantillas a implementar cuando el entorno lo permita; no declarar que existen si no se escribieron y verificaron.

En JavaScript, separar datos (`deliverables`, `questions`, `flows`, `decisions`, `discrepancies`, `blockers`, `risks`), borrador y renderizado. Centralizar apertura de fichas, navegación y cálculo de contadores. Validar referencias entre colecciones: todo ID citado por otra colección debe existir, o la validación debe señalar la referencia huérfana en vez de ignorarla. Evitar números estáticos repetidos que queden desactualizados al cambiar el número de áreas. Un HTML autocontenido no necesita un framework; si se integra a una app existente, leer primero las instrucciones y documentación local de esa versión y documentar la diferencia de entrega.

### 3.9. Lista de aceptación para la IA que replica

Registrar qué se ejecutó, en qué navegador/entorno y con qué resultado. No marcar toda la lista por inspección estática si exige interacción.

**Estructura y datos**

1. El HTML abre localmente sin servidor, red, errores JavaScript ni recursos externos ausentes.
2. Los cinco menús existen en el orden indicado; actualizan selección, encabezado y vista; sus contadores coinciden con las colecciones.
3. El Resumen muestra cuatro indicadores, tabla, siguiente paso, discrepancias, bloqueos y secuencia; sus cifras corresponden al proyecto destino.
4. Todas las preguntas, flujos y botones de fuentes abren el ID correcto. No hay IDs duplicados ni referencias huérfanas entre colecciones (incluidas las referencias cruzadas de §3.15).
4.1. Si se adoptó la línea de tiempo de hitos (§3.20), es uno de los primeros elementos visibles del Resumen, no el último. Cada discrepancia, riesgo o bloqueo mostrado en la columna lateral abre su propia ficha de detalle al hacer clic — una tarjeta que solo muestra un resumen sin forma de ver el resto es una brecha de usabilidad, no un detalle menor. Los pasos de la secuencia visual inferior (§3.2) que correspondan a una vista o ficha real navegan ahí; un paso sin destino real lo declara en su propia etiqueta en vez de quedar como enlace simulado.

**Interacción del borrador**

5. Buscar y combinar filtros funciona; probar término inexistente y **Quitar filtros**.
6. Guardar texto en una ficha lo conserva al reabrirla desde otra vista; cancelar una edición posterior conserva el valor previamente guardado. Cerrar devuelve el foco al origen.
7. Guardar no cambia estado documental ni número de validaciones del producto. Los campos con espacios solamente se consideran vacíos.
8. Cargar ejemplo funciona en vacío y se bloquea después de guardar texto. Los ejemplos se anuncian como sintéticos.

**Exportación**

9. Descargar produce JSON parseable, con todas las áreas/campos y los indicadores de no validación; el modo de ejemplo se refleja correctamente. Probar también texto con acentos, comillas y caracteres HTML como contenido literal.
10. Si existe `schema-exportacion-v{1,2}.json` (obligatorio, no opcional, cuando se implementa la ampliación de §3.11 o cuando hay al menos un área `legal_fiscal_seguridad`/`datos_personales` — criterio unificado en §3.8), el JSON exportado valida contra él, incluida la condición «sin excepción» de §3.18 para esas áreas; registrar el resultado real de esa validación, no solo que el JSON parsea. Si existe `verificar-evidencia.mjs`, ejecutarlo y registrar cuántas referencias rotas o desactualizadas encontró, no solo que corrió sin error.
11. Cancelar reinicio conserva datos; confirmar lo vacía y elimina modo de ejemplo. Recargar pierde el borrador, conforme al aviso visible.

**Decisiones, pantallas y continuidad**

12. Las familias de decisiones muestran las entradas correctas y no aprueban ni implementan acciones.
13. Revisar escritorio, tableta y móvil, por ejemplo 1440×900, 1024×768, 768×1024 y 390×844. Comprobar transiciones cerca de 1200, 960 y 700 px, menú, scroll y modal. Anotar limitaciones de emulación frente a dispositivos reales.
14. Recorrer con teclado menú, filtros, fichas y confirmación; revisar Escape, foco, etiquetas, mensajes, movimiento reducido e impresión de la vista activa.
15. Revisar enlaces documentales, archivos/secciones de fuentes y ausencia de datos sensibles. Separar resultados del dashboard de cualquier prueba del producto.
16. Dejar seguimiento, decisión pendiente, límites y siguiente acción; no declarar release ni aprobación del proyecto por completar esta lista.

### 3.10. Diccionario ampliado para nuevas implementaciones

Estos datos amplían el modelo observado de §3.3. Hacerlos consultables en detalle, fuentes o documentos enlazados; no necesariamente como columnas adicionales. No inferir una aprobación al convertir estados antiguos a este modelo.

| Datos de revisión | Tipo y regla |
|---|---|
| `project.id`, `project.name` | Cadenas: identidad estable y nombre del proyecto destino. |
| `phase`, `baseline_version` | Fase y versión real; `null` con motivo visible si no existen o no se conocen. |
| `reviewed_at` | Fecha ISO de revisión documental; distinta de la hora de exportación. |
| `source_revision` | Objeto con `head`, `working_tree` y `note`; describir cambios locales relevantes o ausencia de Git. |
| `sources[]` | ID, ruta/referencia, sección, fecha/revisión, estado de conciliación, `revisado_el`, vigencia máxima declarada, `last_scope_checkpoint_id` (último hito de alcance mayor revisado; segundo disparador de vigencia, §3.16) y límites; hash según §3.16, nunca secretos. |
| `scope_notice`, `storage_mode` | Alcance real y `memory` mientras el borrador solo viva en la pestaña. |
| `guide_version`, `schema_version` | Versión de esta guía y del formato JSON de intercambio; no son versiones del producto. |

| Datos por área | Tipo y regla |
|---|---|
| `id`, `title`, `category`, `summary` | Cadenas, ID único estable y familia propia del proyecto. |
| `risk_category` | `legal_fiscal_seguridad` \| `funcional` \| `tecnico` \| `operativo` \| `terceros` \| `datos_personales` \| `cosmetico`. Determina revisores mínimos (§3.18). |
| `requirement_ids[]`, `question_ids[]`, `dependencies[]` | IDs reales y enlaces trazables; no usar posición en un array como identidad. |
| `implementation_status` | `not_started`, `partial`, `implemented`, `not_applicable`, `unknown`. Justificar N/A y desconocidos. |
| `verification_status` | `not_verified`, `pending`, `passed`, `failed`, `not_applicable`. `passed` solo con evidencia externa verificable (§3.18); de lo contrario degradar a `pending` con nota «autoatestado». |
| `decision_status` | `pending`, `accepted`, `rejected`, `deferred`. Aceptación requiere autoridad, fecha y referencia externa verificable (§3.18). `deferred` requiere `review_by`. |
| `official_status`, `observed_at` | Texto del estado según fuente y fecha observada; no calculado a partir del borrador. |
| `implemented_by`, `verified_by`, `decided_by` | Rol o identidad que ejecutó, verificó y decidió. Si `implemented_by` coincide con `verified_by` o `decided_by`, marcar la fila como «autoatestado, sin control cruzado» (§3.18). |
| `authority_ref` | Referencia a un artefacto externo con su propio autor y fecha (aprobación de PR, hilo de correo, acta, ticket). Un texto suelto escrito dentro del propio dashboard no cuenta como autorización verificable. |
| `source_refs[]`, `evidence_refs[]` | Referencias con tipo (`commit`\|`log`\|`captura`\|`run_ci`), ruta/URL/SHA y fecha; ver estructura completa en §3.18. Una plantilla no es un resultado. `referencia_rota`/`referencia_desactualizada` (booleanos, calculados por `verificar-evidencia.mjs`, §3.16) nunca se editan a mano. |
| `gap`, `acceptance_criteria`, `next_action` | Brecha, criterio verificable y siguiente paso concreto. |
| `owner_role`, `person_assigned` | Rol previsto y booleano de asignación acreditada; no inferir que el usuario ocupa un cargo. |
| `review_by` | Fecha de re-revisión obligatoria cuando `decision_status = deferred`. |
| `history[]` | Arreglo append-only `{status, changed_at, changed_by_role, note}`; nunca se edita una entrada pasada, solo se añade una nueva (§3.18). |
| `objection` | `{raised_by, reason, date, overridden_by, override_reason}` cuando un revisor objetó y una autoridad superior decidió igualmente aprobar; no se borra al aprobar (§3.18). |
| `fields[]` | Lista ordenada con `key`, `label`, `hint`, `question_ids[]`, `input_type`, `max_length` y `example`; mantener `draft_value` en el borrador separado. |

Usar `null` para metadatos desconocidos más una explicación; no confundirlo con `draft_value: ""`, que solo representa un campo de respuesta vacío. La identidad de campo es `(area_id, key)`; generar IDs DOM como `field-PR-01-context` y ayudas con el mismo prefijo. Permitir guardar borradores incompletos: ninguna respuesta es obligatoria por defecto. Si se incorporan fechas, números o listas, declarar unidades, rangos, formato y vacío. Un error de longitud/formato conserva el texto y se anuncia junto al campo.

### 3.11. Exportación v2 para nuevas réplicas y compatibilidad

Implementar y verificar este contrato antes de anunciarlo en una réplica. No cambia la exportación v1 de un dashboard ya existente por actualizar esta guía. Ejemplo ilustrativo abreviado:

```json
{
  "artifact": "preparation_gap_dashboard_draft",
  "schema_version": 2,
  "guide_version": "3.0.1",
  "prototype_only": true,
  "validated": false,
  "project": {"id": "EJEMPLO", "name": "Proyecto de ejemplo"},
  "review": {
    "reviewed_at": "2026-10-19",
    "phase": null,
    "baseline_version": null,
    "source_revision": {"head": null, "working_tree": "not_applicable", "note": "Ejemplo sin repositorio; fase y baseline desconocidas"},
    "sources": [{
      "id": "SRC-DEMO", "path": "requisitos.md", "section": "Objetivo",
      "status": "pending_reconciliation", "note": "Referencia ilustrativa sin revisar",
      "revisado_el": null, "vigencia_max_dias": 30,
      "hash": null, "hash_algorithm": "sha256", "hashed_at": null, "hashed_ref": null
    }]
  },
  "exported_at": "2026-10-19T00:00:00Z",
  "storage_mode": "memory",
  "example_data_present": false,
  "product_release_status": "not_evaluated",
  "assessment_scope": "documentary_and_static_code_only",
  "notice": "Borrador sin validar; no constituye evidencia, aprobación ni autorización.",
  "deliverables": [{
    "id": "AREA-DEMO",
    "title": "Área de ejemplo",
    "risk_category": "funcional",
    "official_status": "unknown",
    "implementation_status": "unknown",
    "verification_status": "not_verified",
    "decision_status": "pending",
    "implemented_by": null,
    "verified_by": null,
    "decided_by": null,
    "owner_role": null,
    "person_assigned": false,
    "authority_ref": null,
    "status_changed_by_draft": false,
    "source_refs": ["SRC-DEMO"],
    "review_by": null,
    "history": [],
    "objection": null,
    "fields": [{"key": "context", "label": "Contexto", "question_ids": [], "draft_value": "", "validated": false}]
  }],
  "blockers": [],
  "risks": []
}
```

`schema_version` es entero; las banderas son booleanos; IDs y valores de texto son cadenas; colecciones son arrays. En la exportación de borradores, `prototype_only` siempre es `true` y `validated` siempre `false`, también por campo. Los estados observados se copian de la revisión. El ejemplo de fecha es ilustrativo: `exported_at` se calcula al descargar en ISO 8601 con zona horaria. No sustituye `review.reviewed_at`. `example_data_present` sigue las reglas conservadoras de §3.5. Adaptar `assessment_scope` solo si el trabajo real tuvo otro alcance y registrarlo; las pruebas de la maqueta no amplían el alcance de producto.

Nombre sugerido: `<proyecto>-preparacion-borrador-v2-<fecha>.json`, guardado además en `historico/export-AAAA-MM-DD.json` (§3.17). Descargar como `application/json;charset=utf-8` y revocar la URL temporal después de iniciar la descarga. Informar errores sin borrar datos. No incluir claves, hashes de secretos, URLs con tokens o rutas sensibles.

Al revisar un JSON recibido, identificar primero origen y versión. Validar IDs, claves, tipos, longitudes, duplicados y referencias contra la revisión aplicable — y, si existe `schema-exportacion-v2.json` (§3.16), contra ese JSON Schema de forma mecánica, no solo por inspección. Un v1 no tiene todos los metadatos v2: registrar los ausentes como por verificar, sin inventar proyecto, fecha o HEAD. No tratar versiones desconocidas como compatibles; registrar la limitación para revisión. No se exige importación en la UI ni escritura automática a las fuentes oficiales.

### 3.12. Detalles adicionales de navegación, robustez y entrega

- **Fuentes:** conservarlas en **Fuentes y discrepancias** y ofrecer acceso desde el pie. Mostrar ruta/sección, fecha/revisión y conciliación, dentro de la vista o mediante documento local claramente enlazado. No inventar enlaces para fuentes restringidas: usar ID y explicar el límite.
- **Bloqueos y riesgos:** cuando existan, ubicarlos en el panel lateral del Resumen con los campos de §3.15 (causa, severidad, dependencia, estado, `opened_at`/`due_at`, condición de cierre y siguiente acción). Distinguirlos entre sí (un riesgo es un problema potencial; un bloqueo, uno ya materializado) y de discrepancias documentales o preguntas sin responder; no convertir todas las áreas abiertas en bloqueantes.
- **Seguimiento:** enlazar `seguimiento.md` desde el pie y **Decisiones** en una nueva implementación. Mantener las tablas de esta guía; no hace falta un sexto menú.
- **Decisiones:** ampliar cada entrada con alternativas e impacto, autoridad confirmada o pendiente con referencia externa verificable, y siguiente acción cuando existan; si no se conocen, declararlo. Filtrar no decide ni implementa nada.
- **Cambio de vista:** una sola vista visible. En nuevas réplicas, llevar el foco al encabezado o contenido activo cuando el foco quedaría oculto; al cerrar el cajón móvil devolverlo al botón cuando corresponda. No anunciar historial URL o navegación Atrás/Adelante si no se implementaron.
- **Información retirada de columnas:** mantener rol, estado y fuentes consultables en el detalle. Probar texto largo y zoom al 200 %; evitar desbordamiento horizontal global y limitar el scroll de tablas a su contenedor.
- **Descarga o validación fallida:** mostrar error accesible y conservar el borrador. Si hay edición sin guardar, advertir qué se exporta o pedir guardar/cancelar antes de descargar, sin perder texto silenciosamente.
- **Entrega portable:** enlazar este Markdown real y declarar su versión. Si posteriormente se ofrece un ZIP, verificar contenido, enlaces y hashes; distinguir HTML de referencia, plantilla y nueva implementación. Las capturas históricas deben identificarse por revisión y no presentarse como pruebas nuevas. No anunciar un ZIP que no se haya generado.

Añadir a §3.9 pruebas de borrador vacío/parcial/completo, metadatos y tipos v2, revisión compatible de v1, errores de validación/descarga, IDs DOM compuestos, zoom al 200 %, texto largo, foco al cambiar vista, y ejecución de `verificar-evidencia.mjs` sobre al menos una referencia rota a propósito para comprobar que se detecta. Registrar qué verificaciones no se pudieron ejecutar.

### 3.13. Matriz de capacidades observadas y ampliaciones

| Capacidad | Dashboard mínimo (§3.1–§3.9) | Contrato de una nueva réplica ampliada |
|---|---|---|
| Cinco menús y composición | Resumen, Primera operación, Flujos, Fuentes y Decisiones | Conservar orden, estructura y relaciones; adaptar datos al proyecto. |
| Inventario | N áreas, M campos, preguntas, flujos y decisiones del destino | Usar datos del destino y contadores derivados; ver heurística de §3.3. |
| Estados | Texto documental por área; no editable mediante borradores | Exponer las tres dimensiones y sus fuentes según §3.10. |
| Campos | Textareas con ayudas; IDs locales por clave en el modal | Usar identidad compuesta área/clave, diccionario e inventario verificable. |
| Fuentes y seguimiento | Fuentes por área y enlaces a documentos locales; seguimiento en archivo | Hacer consultables revisión, conciliación y seguimiento según §3.12; verificación automatizada según §3.16. |
| Exportación | v1 con snapshot y marcas de no validación | Implementar v2 antes de anunciar proyecto estructurado, fecha, revisión, riesgos y bloqueos. |
| Navegación y accesibilidad | Diálogos, restauración de foco del detalle, estilos responsive y foco visible | Verificar además foco entre vistas, zoom, contraste y errores; no presumir cumplimiento. |
| Riesgos y bloqueos | Panel de texto libre, sin severidad ni SLA | Modelo tipado de §3.15 con severidad, antigüedad y escalamiento. |
| Verificación de evidencia | «Evidencia disponible» como texto libre | Estructura tipada y verificación de autoría independiente (§3.18). |
| Vigencia de fuentes y decisiones | Revisión manual ad hoc | Script de staleness con dos disparadores — tiempo y cambio de alcance mayor (§3.16). |
| Patrón de cobertura por campo/identificador | No generalizado; mencionado solo como antecedente histórico (Anexo B) | Generalizar el patrón «hermano sin dato» (grep por identificador completo en alta, edición, tabla, acciones por fila, contexto, respaldo/seed y documentación, excluyendo carpetas generadas/build, código de salida ≠ 0 ante un hueco) a cualquier campo, rol o permiso nuevo del proyecto destino, no solo al propio dashboard (§3.16). |
| Indicador de bugs conocidos | Ausente; solo los cuatro indicadores base del Resumen | Quinta tarjeta opcional con conteo por etiqueta de bug confirmado y botón de acceso directo a cada ficha, sin alterar ni promediarse con los cuatro indicadores base (§3.2). |
| Look and feel ampliado (botones, badges, iconos, tarjeta decorativa, fase lateral, foco visible) | No detallado más allá de color y proporción | Catálogo opcional a elegir, tomado de la referencia real Nexia/conta01 (§3.1); adoptar cualquier subconjunto, declarando en `seguimiento.md` cuáles. |
| Línea de tiempo de hitos del proyecto | Ausente | `milestones[]` con ficha de detalle por hito (qué se definió/agregó/cambió/quitó, con fuentes); opcional, exportable en v2, y reutilizable como fuente de `hitos-alcance.json` (§3.16/§3.20). |
| Persistencia, importación, historial URL | Ausentes | Declarar el límite; requieren implementación y comprobación propias. |
| Cambios oficiales | No se escriben fuentes ni se aprueba producto desde el formulario | Conservar revisión y autoridad externas a la UI, con separación de funciones (§3.18). |

La actualización de esta guía es documental. No transforma las recomendaciones en capacidades ya implementadas, requisitos funcionales nuevos o aprobación de producto.

### 3.14. Conservar inventario y ampliaciones del proyecto destino

La composición de cinco vistas organiza el diagnóstico. Dentro del Resumen, conservar además los menús y funciones reales del producto según §1.1: no confundir los menús del dashboard con la navegación de la aplicación. Dar acceso por menú o módulo, mostrar sus conteos y explicar si seleccionar uno limpia filtros previos. Buscar por recorrido, característica, estado, rol, fuente e ID; mantener apertura por botón y foco tras actualizar filtros.

Si ya existen fichas de una versión anterior del dashboard, preservar sus IDs, estados documentales y evidencia. No comprimirlas a un número de referencia perdiendo requisitos o funciones. Documentar el número elegido y derivar todos los contadores. Mantener por separado el diagnóstico de CI, el avance del hito en curso, la presencia de controles y los campos con texto de revisión.

Los campos pueden adaptarse al contexto (por ejemplo: observaciones, evidencia, alcance/límites y siguiente acción). Un resultado de revisión adicional no cambia el estado del producto ni cuenta como evidencia. Cada texto admite hasta 1200 caracteres con etiqueta y ayuda asociada. Guardar solo al pulsar **Guardar borrador**; cerrar o cancelar descarta lo editado desde la apertura y conserva lo guardado antes.

Cuando se migre una exportación existente, versionar el esquema y documentar la compatibilidad. En una adaptación nueva se exportan todas las fichas y todos sus campos guardados, aunque estén vacíos o fuera del filtro, con los metadatos de §3.6/§3.11. Conservar los filtros e IDs visibles como contexto, sin usarlos para eliminar fichas del archivo. No incluir ediciones sin guardar. Los ejemplos se anuncian como sintéticos y no alteran fuentes ni decisiones.

Avisar que recargar pierde el borrador y que exportar no ofrece restauración si no existe importación. Las observaciones libres pueden contener datos sensibles aunque las fichas base no los tengan. Revisar antes de compartir. Separar fecha de exportación, revisión de cada fuente y pruebas históricas: una nueva interfaz no renueva por sí sola CI, hashes ni validaciones.

### 3.15. Riesgos, bloqueos y escalamiento

Un **riesgo** es un problema potencial que todavía no ocurrió; un **bloqueo** es un problema ya materializado que detiene un entregable. Mantenerlos en dos colecciones separadas, cada una con su propio namespace de ID (`RSK-xxx` para riesgos, `BLK-xxx` para bloqueos), nunca como el mismo objeto con un campo de estado ambiguo.

**Modelo de bloqueo (`blockers[]`):**

| Campo | Tipo / regla |
|---|---|
| `id`, `cause`, `status` | ID único `BLK-xxx`, descripción de la causa, estado (`open`, `mitigated`, `closed`). |
| `severity` | `blocker` \| `high` \| `medium` \| `low`. Determina orden de visualización y umbral de escalamiento. |
| `category` | Misma taxonomía de `risk_category` (§3.10): `legal_fiscal_seguridad`, `funcional`, `tecnico`, `operativo`, `terceros`, `datos_personales`, `cosmetico`. |
| `dependency`, `closure_condition`, `next_action` | Qué lo condiciona, cómo se cierra formalmente y el paso táctico inmediato (distinto de `mitigation_plan`). |
| `mitigation_plan`, `contingency_plan` | Estrategia de fondo y plan B si la mitigación principal falla. |
| `opened_at`, `due_at` | Fecha de apertura y fecha límite declarada (SLA). `days_open` se calcula siempre en la maqueta a partir de `opened_at`, nunca se edita a mano. |
| `owner_role`, `follow_up_owner_role` | Rol que ejecutará el cierre y rol que debe perseguir la asignación mientras no haya dueño confirmado — para que «sin dueño confirmado» no equivalga a «sin nadie dando seguimiento». |
| `escalated_to`, `escalated_at` | A quién se escaló y cuándo, según la matriz de escalamiento siguiente. El dashboard solo registra que se escaló, no ejecuta la notificación. |
| `related_decision_id`, `related_source_id`, `caused_by_risk_id` | IDs cruzados; deben existir en su colección correspondiente, sin referencias huérfanas. |
| `history[]` | Append-only, igual que en áreas (§3.10): nunca se reescribe una transición pasada. |

**Modelo de riesgo (`risks[]`):**

| Campo | Tipo / regla |
|---|---|
| `id`, `description`, `category` | ID único `RSK-xxx`, descripción del problema potencial, misma taxonomía de categoría. |
| `probability`, `impact`, `severity` | Probabilidad e impacto declarados; `severity` derivada o declarada explícitamente. |
| `mitigation_plan`, `contingency_plan` | Estrategia preventiva y plan de contingencia si el riesgo se materializa. |
| `owner_role`, `follow_up_owner_role` | Igual que en bloqueos. |
| `status` | `open`, `mitigated`, `accepted`, `materialized`, `closed`. |
| `materialized_to_blocker_id` | Si el riesgo se materializa, el ID del bloqueo nuevo que lo documenta — transición explícita, nunca silenciosa. |
| `review_by` | Obligatorio cuando `status = accepted`: un riesgo aceptado como residual no debe quedar aceptado para siempre sin fecha de reconsideración. |
| `related_decision_id`, `related_source_id` | IDs cruzados verificables. |
| `history[]` | Append-only. |

**Fuentes que bloquean una decisión:** si una fuente marcada `pending_reconciliation` (§3.10/§3.16) bloquea una decisión o un entregable, generar un registro correspondiente en `blockers[]` que la referencie (`related_source_id`). No dejarla solo como atributo suelto de `sources[]` cuando en los hechos está deteniendo algo.

**Matriz mínima de escalamiento** (plantilla, adaptar roles reales del proyecto):

| Severidad | Antigüedad (`days_open`) | Escalar a |
|---|---|---|
| `blocker` o `high` | más de 5 días abierto | responsable técnico o de dominio del área |
| `blocker` o `high` | más de 10 días abierto | sponsor o autoridad superior del proyecto |
| `medium` | más de 15 días abierto | responsable técnico o de dominio del área |
| `low` | sin escalamiento automático declarado | seguimiento regular en `seguimiento.md` |

Esta tabla es una plantilla de umbrales razonables, no una obligación universal: adaptar los días y roles a la cadencia real del proyecto y documentar el cambio.

**Panel agregado honesto (sin score global):** en el Resumen, mostrar contadores derivados — «bloqueos abiertos por severidad», «bloqueos vencidos (`due_at` < hoy)», «riesgos con `review_by` vencido» — cada uno con su denominador y alcance declarados, igual que los indicadores de §3.2. Nunca combinarlos en un porcentaje único de «salud del proyecto».

### 3.16. Verificación automatizada y vigencia de fuentes

**Hash de fuentes:** cuando se use un hash para detectar cambios en una fuente citada, fijar siempre:

- Algoritmo: `sha256`.
- Contenido exacto a hashear: el texto del archivo o del rango de líneas citado, normalizado a saltos de línea `LF`, sin BOM y sin espacios finales de línea añadidos por el editor.
- Campos que acompañan al hash: `hashed_at` (fecha del cálculo) y `hashed_ref` (commit SHA del repositorio en ese momento), junto al propio valor.

Sin estas tres reglas fijas, dos sesiones distintas obtienen hashes distintos del mismo contenido por diferencias triviales de línea, y el hash deja de ser una señal confiable.

**Script de referencia `verificar-fuentes.mjs` (plantilla):** recorre `fuentes.json`, recalcula el hash de cada fuente citada contra el árbol de trabajo actual con las reglas anteriores, y marca automáticamente `pendiente_de_conciliacion: true` en cualquier fuente cuyo hash no coincida con el registrado — sin esperar a que una persona note la discrepancia. Ejecutarlo antes de exportar o de cerrar una tarea (paso añadido a §5).

**Script de referencia `verificar-evidencia.mjs` (plantilla):** distinto de `verificar-fuentes.mjs`, que solo cubre las citas de documentos en `fuentes.json`/`sources[]`. Este script resuelve mecánicamente cada entrada de `source_refs[]`/`evidence_refs[]` (§3.10/§3.18) de áreas, bloqueos y riesgos contra el estado real del repositorio: confirma que un `commit` existe (p. ej. `git cat-file -e <sha>`), que la ruta de un `log`/`captura` sigue presente en el árbol de trabajo o en el histórico declarado, y que un `run_ci` corresponde a un identificador real cuando el proyecto expone esa consulta. Marca `referencia_rota: true` cuando la referencia ya no resuelve (SHA inexistente, archivo borrado, run purgado) y `referencia_desactualizada: true` cuando resuelve pero es anterior al último cambio relevante del área que referencia. Sin este script, una fila puede quedar marcada `verification_status: passed` indefinidamente aunque su evidencia ya no exista — es un hueco distinto del de `fuentes.json`, y no se cierra por analogía con `verificar-fuentes.mjs`, sino con su propia lógica de resolución.

**Vigencia por dos disparadores, no solo por tiempo:** el primer disparador es temporal — añadir a cada fuente `revisado_el` y una antigüedad máxima declarada por el proyecto (por ejemplo 30 días, o la siguiente fecha de corte relevante del dominio); el mismo script debe marcar `pendiente_de_conciliacion: true` cuando `revisado_el` exceda ese umbral, aunque el hash no haya cambiado — cubre el caso de «nadie volvió a mirarlo», no solo «el archivo cambió». El segundo disparador es un **cambio de alcance mayor** del proyecto (un hito de roadmap cerrado, una reestructuración de requisitos, un cambio de régimen/plataforma/alcance legal relevante): registrar cada uno como una entrada con fecha e ID en `hitos-alcance.json` (o en `seguimiento.md` si el proyecto no justifica un archivo aparte), y que el mismo script compare `revisado_el` de cada fuente — vía su `last_scope_checkpoint_id` (§3.10) — contra la fecha del hito de alcance más reciente que la afecte; si la fuente no se revisó después de ese hito, marcar `pendiente_de_conciliacion: true` aunque la antigüedad en días todavía no haya vencido. Un cambio de alcance mayor puede volver obsoleta una fuente revisada ayer; el disparador temporal por sí solo no lo detecta.

**JSON Schema del contrato de exportación:** mantener `schema-exportacion-v1.json` y `schema-exportacion-v2.json` (JSON Schema Draft 2020-12) como parte de §3.8, junto a un script `validar-exportacion.mjs <export.json>` que falle con código de salida 1 si el archivo no valida. Esto convierte el contrato de §3.6/§3.11 en algo mecánicamente comprobable, no solo descrito en prosa. El schema v2 codifica además, como condición `if/then`, la regla «sin excepción» de §3.18 para áreas de alto riesgo — ver el detalle de esa condición allí; sin ella en el schema, «sin excepción» es solo una frase, no un control. Sobre cuándo estos artefactos son obligatorios y no opcionales, ver §3.8.

**Generalización del patrón «hermano sin cobertura» a campos de código arbitrarios:** la misma técnica usada para la trazabilidad cruzada siguiente —grep por el identificador completo de un campo, rol o permiso nuevo en cada superficie donde debería aparecer (alta, edición, tabla, acciones por fila, contexto, respaldo/seed, documentación), excluyendo carpetas generadas o de build (`dist/`, `.next/`, `node_modules/`, `build/`) y reportando con código de salida distinto de cero cuando un hermano no tiene el dato— es reutilizable más allá de este dashboard: aplicarla a cualquier cambio del proyecto destino que agregue un campo, rol, permiso o ajuste, igual que `cobertura-campo.mjs` (Anexo B) lo hacía para su propio código fuente antes de dar por terminado un cambio. Ver la fila correspondiente en la matriz de §3.13.

**Trazabilidad cruzada con los documentos de requisitos del proyecto:** si el repositorio mantiene documentos de requisitos/pendientes en paralelo al dashboard, verificar tras cada actualización que todo ID de área/requisito marcado como implementado en el dashboard tenga su equivalente en esos documentos, y viceversa — aplicación del patrón anterior al propio dashboard en vez de dejarlo como disciplina de memoria.

**Diff histórico de exportaciones:** guardar cada exportación relevante como `historico/export-AAAA-MM-DD.json` (§3.8) y usar `diff-exportaciones.mjs` para comparar dos snapshots por área, listando qué `implementation_status`/`verification_status`/`decision_status` cambiaron entre ellos. Esto da una serie temporal auditable («cuándo y por qué cambió el diagnóstico de un área») en vez de solo un snapshot puntual.

**Hook de ejemplo (opcional, plantilla, no un hecho consumado):** un `pre-commit` o una acción de CI puede ejecutar `verificar-fuentes.mjs` y fallar si el commit toca una fuente que quedó `pendiente_de_conciliacion`. Documentarlo como plantilla disponible, no como automatización ya activa, salvo que realmente se haya instalado y probado.

### 3.17. Métricas de cobertura de verificación y decisión

Los cuatro indicadores de §3.2 miden llenado de formulario (texto guardado) y alcance documental — no verificación real. Añadir, por separado, una segunda familia de métricas con su propia fórmula y denominador documentados:

| Métrica | Fórmula |
|---|---|
| `verification_coverage` | áreas con `verification_status = passed` ÷ áreas totales |
| `decision_coverage` | áreas con `decision_status` en (`accepted`, `rejected`) ÷ áreas totales |

Registrar el valor de estas dos métricas en `seguimiento.md` en cada actualización relevante (§5), de modo que se pueda leer la tendencia entre tareas — apoyándose en el diff histórico de §3.16 — y no solo el valor puntual de la sesión actual. Ninguna de las dos sustituye ni se combina con un score global de preparación: siguen el mismo principio de los indicadores de §3.2, declarar alcance y denominador, nunca inventar un porcentaje certificador.

### 3.18. Meta-gobernanza, separación de funciones y autoridad verificable

**Separación de funciones (maker-checker):** usar siempre los tres campos `implemented_by`, `verified_by` y `decided_by` (§3.10). Cuando la misma identidad o rol aparece en dos de los tres, el dashboard debe mostrar la fila como «autoatestado, sin control cruzado» en vez de tratarla igual que una verificación independiente. Esto no bloquea el avance — un proyecto pequeño puede no tener separación de roles disponible — pero evita que una auto-aprobación se vea igual que una revisión cruzada real.

**Autoridad verificable, no texto libre:** `authority_ref` (§3.10) debe apuntar a un artefacto externo con su propio autor y timestamp — una aprobación de PR, un hilo de correo, un acta, un ticket — nunca a una frase tecleada dentro del propio dashboard. Sin ese enlace, la fila correspondiente queda forzosamente en «sin autorización verificable», sin importar qué tan convincente suene el texto.

**Evidencia verificable, no autoatestación:** `verification_status = passed` solo se marca cuando `evidence_refs[]` contiene al menos una entrada con origen externo e independiente del implementador — un run de CI con su ID, una captura con metadata, un log de prueba reproducible. La estructura mínima de cada entrada de evidencia es:

```json
{"tipo": "commit | log | captura | run_ci", "referencia": "SHA, URL o ruta exacta", "fecha": "AAAA-MM-DD"}
```

Sin una entrada que cumpla esto, degradar automáticamente a `pending` con la nota «autoatestado, no verificado de forma independiente» en vez de aceptar «yo ya lo probé» como equivalente.

**Historial append-only:** todo cambio de `decision_status`, `verification_status` o del estado de un bloqueo/riesgo se añade como una entrada nueva en `history[]` (§3.10/§3.15), nunca reescribiendo una entrada anterior. Cada entrada de decisión relevante debe corresponder a un commit propio del repositorio, nunca amendeado, para que el historial de git también sea auditable.

**Objeción registrada:** cuando un revisor objeta que algo no está listo pero una autoridad superior aprueba igualmente, registrar esa objeción en el campo `objection` (§3.10) con quién objetó, por qué, quién la pasó por encima y con qué justificación. Este campo no se borra ni se sobreescribe al aprobar — preserva la trazabilidad de responsabilidad si la decisión resulta equivocada más adelante.

**Meta-gobernanza de los propios criterios:** las definiciones de qué cuenta como `implemented`, `passed` o `accepted` en esta guía son parte de su contrato versionado (este documento), no un campo editable desde la UI de captura del dashboard. Cambiar esas definiciones para un proyecto sigue el mismo flujo borrador → revisión registrada → decisión que cualquier otro cambio de alcance (§4) — quien reporta su propio avance no puede relajar unilateralmente la definición de éxito que se usa para medirlo.

**Clasificación por riesgo y revisores mínimos:** usar `risk_category` (§3.10) para exigir, en áreas de categoría `legal_fiscal_seguridad` o `datos_personales`, que `verified_by` y `decided_by` sean distintos de `implemented_by` sin excepción, y que la autoridad de `authority_ref` corresponda a un nivel declarado como superior en las reglas locales del proyecto — en vez de tratar un cambio cosmético y uno de alto riesgo con el mismo único campo `decision_status` homogéneo.

Esta regla «sin excepción» no se queda en prosa: se declara como condición `if/then` en `schema-exportacion-v2.json` (§3.11/§3.16) — si `risk_category` ∈ {`legal_fiscal_seguridad`, `datos_personales`} y `decision_status = accepted`, entonces el esquema exige `verified_by` no nulo y distinto de `implemented_by`, `decided_by` no nulo y distinto de `implemented_by`, y `authority_ref` no nulo. `validar-exportacion.mjs` debe fallar con código de salida 1 si una fila de esa categoría viola la condición, del mismo modo que ya falla ante un JSON que no valida contra el resto del schema (§3.16). Sin esa condición codificada, «sin excepción» es solo una promesa de este párrafo, no un control real — por eso §3.8 trata estos dos artefactos como obligatorios, no opcionales, en cualquier dashboard que tenga al menos un área de esas dos categorías.

**Separación de fuentes y vigencia de decisiones:** una fuente marcada `pending_reconciliation` nunca se trata como vigente mientras no se revise (regla ya presente en §5); una decisión `deferred` o un riesgo `accepted` sin `review_by` vencido se señalan en el Resumen como pendientes de reconsideración, sin inventar semáforos de aprobación que no existen.

### 3.19. Adopción incremental sobre un seguimiento existente

Cuando el proyecto ya tiene un seguimiento más simple — una lista de pendientes, un documento de requisitos sin las tres dimensiones de §2 — no es necesario reescribirlo todo de una vez para empezar el dashboard:

1. Mapear cada entrada existente del seguimiento simple a una fila mínima del modelo de §3.3/§3.10: al menos `id`, `title`, `official_status` (copiado tal cual del documento original) y `source_refs[]` apuntando al documento original.
2. Dejar `implementation_status`, `verification_status` y `decision_status` como `unknown`/`not_verified`/`pending` hasta que se revisen explícitamente — no inferirlos del texto libre del documento original.
3. Migrar primero las áreas de mayor `risk_category`, no las que resulten más fáciles de transcribir.
4. Registrar en `seguimiento.md` qué proporción del documento original ya tiene fila equivalente en el dashboard y cuál sigue pendiente de migrar, para que la migración parcial sea visible y no se confunda con una migración completa silenciosa.
5. Mientras la migración esté incompleta, declarar explícitamente en el aviso permanente del dashboard (§3.1) que no cubre el 100 % del seguimiento previo.

### 3.20. Línea de tiempo de hitos del proyecto (opcional)

Los cuatro/cinco indicadores de §3.2 miden el alcance de esta revisión documental; el «siguiente paso» de §3.2 señala la brecha más urgente; pero ninguno de los dos responde «¿cómo llegó el proyecto hasta aquí y qué se decidió en el camino?». Esta línea de tiempo cubre ese hueco: una secuencia de hitos reales del proyecto, cada uno con una ficha propia que registra qué cambió, qué se agregó y qué se definió en ese punto — no un segundo lugar para repetir el estado actual de las áreas.

**Cuándo adoptarla:** útil desde que el proyecto tiene al menos dos hitos reales que comparar (p. ej. inicio y MVP); con un solo hito declarado, la línea de tiempo queda vacía de comparación y aporta poco. Es opcional igual que el indicador de bugs conocidos (§3.2) o el look and feel ampliado de §3.1: adoptarla no es obligatorio para el dashboard mínimo de §0.5.

**Modelo de datos (`milestones[]`):** colección propia, con namespace de ID separado de áreas/decisiones/bloqueos/riesgos (`HITO-xxx`).

| Campo | Tipo / regla |
|---|---|
| `id`, `label` | ID único `HITO-xxx` y nombre del hito. Cuatro hitos de plantilla razonables para la mayoría de proyectos — **Inicio del proyecto**, **MVP**, **Revisión en QA**, **Salida a producción** — pero no son obligatorios ni fijos: renombrar, añadir o quitar hitos según el roadmap real (p. ej. «Piloto cerrado», «Auditoría externa», «Migración de datos»), documentando el cambio en `seguimiento.md` igual que un renombrado de menú (§3.2). |
| `status` | `planned` \| `in_progress` \| `done` \| `delayed`. Reutiliza la misma paleta de `badge` que el resto del dashboard (§3.1): `done` → verde, `in_progress`/`planned` → neutral, `delayed` → ámbar o rojo según severidad. |
| `planned_date`, `actual_date` | Fecha ISO declarada y fecha real si ya ocurrió; `null` con nota si todavía no hay fecha objetivo. Un hito `done` sin `actual_date` es una fila inconsistente, no un hito confirmado. |
| `summary` | Una oración: qué representa este hito para el proyecto destino, no una descripción genérica («MVP» por sí solo no dice qué incluye el MVP de este proyecto). |
| `changes[]` | **El detalle de cada hito**, como pide esta ampliación: lista de entradas `{"type": "defined"\|"added"\|"changed"\|"removed", "text": "...", "source_refs": [...]}`. `defined` es una decisión de alcance o criterio tomada en ese hito; `added`, una capacidad o artefacto nuevo; `changed`, un ajuste sobre algo que ya existía; `removed`, algo que se descartó o pospuso. Cada entrada cita su fuente real (commit, documento, acta) en `source_refs[]`, igual que una entrada de área (§3.10) — una lista sin fuente es una afirmación, no evidencia. |
| `related_area_ids[]`, `related_decision_ids[]` | IDs reales de `deliverables[]`/`decisions[]` que este hito afecta o resuelve; deben existir en su colección, sin referencias huérfanas (misma regla de §3.8). |
| `owner_role` | Rol responsable del hito, igual criterio que `owner_role` en áreas (§3.3): rol sugerido, no nombramiento salvo que esté confirmado. |
| `history[]` | Append-only, igual que en áreas y bloqueos (§3.10/§3.15): un cambio de `status` se añade como entrada nueva, nunca reescribe una anterior. |

**Composición visual:** una fila horizontal de nodos en el Resumen (§3.2), colocada como uno de los **primeros elementos de la vista** — inmediatamente después del encabezado/indicadores y antes de la tabla principal de áreas, no al final junto al pie de página. Los hitos dan contexto de cómo llegó el proyecto hasta hoy; verlos solo después de haber revisado el detalle de cada área invierte el orden de lectura natural (contexto antes que detalle). Apilar en vertical en los anchos de §3.7 por debajo de 960 px, igual que el resto de grids de esta guía. Cada nodo muestra el `label`, la fecha (`actual_date` si existe, si no `planned_date` marcada como estimada) y un punto de color según `status`, conectados por una línea continua hasta el hito `done` más reciente y discontinua de ahí en adelante — el mismo lenguaje visual de «línea de progreso» que ya usa la secuencia inferior del Resumen (§3.2), pero aplicado a fechas de calendario en vez de a pasos de un flujo fijo de cuatro etapas; no fusionar ambos componentes, representan cosas distintas (progreso de la revisión vs. hitos del producto). Cada nodo es un botón que abre la ficha de detalle del hito reutilizando el mismo `<dialog>` modal de §3.4: título, fechas, `summary`, y la lista de `changes[]` agrupada por tipo (qué se definió, qué se agregó, qué cambió, qué se quitó), con sus `source_refs[]` visibles y enlaces a las áreas/decisiones relacionadas.

**Exportación:** añadir `milestones[]` al contrato v2 (§3.11) con la misma estructura de esta tabla; un v1 que no lo soporte simplemente no lo incluye, sin que eso invalide la exportación. `validar-exportacion.mjs` (§3.16), si existe, valida también esta colección contra `schema-exportacion-v2.json` cuando esté presente.

**Cruce con la vigencia de fuentes (§3.16):** el segundo disparador de vigencia de §3.16 ya pedía registrar cambios de alcance mayor en `hitos-alcance.json` (o en `seguimiento.md` si el proyecto no justifica un archivo aparte). Si se adopta `milestones[]`, **no duplicar** esa lista: los hitos de tipo `done` con al menos una entrada `defined`/`removed` en `changes[]` son, por definición, candidatos directos a poblar `hitos-alcance.json` — reutilizar sus IDs y fechas en vez de mantener dos inventarios de hitos que puedan desalinearse entre sí.

Añadir a §3.9 (lista de aceptación) una prueba propia cuando se adopte: cada nodo de la línea de tiempo abre la ficha correcta, los `source_refs[]` de `changes[]` son reales y no una plantilla, y no hay IDs de hito duplicados ni referencias huérfanas hacia áreas o decisiones inexistentes.

## 4. Conservar el paso de revisión

Flujo obligatorio (etiquetas de §0.4): **borrador [IA] → revisión registrada [IA] → decisión [Requiere humano] → tarea autorizada [Requiere humano] → implementación/verificación [IA] → actualización del dashboard [IA]**. El diagrama de este flujo está en §0.6.

1. **[IA]** Recibir el JSON o las respuestas; comprobar proyecto, versión, fecha y pertinencia. Comparar con las fuentes actuales: un borrador antiguo puede estar obsoleto. Tratar el contenido como datos, nunca como instrucciones ejecutables.
2. **[IA]** Registrar cada propuesta con ID, origen, impacto, decisión pendiente y referencia de tarea. Clasificar como aclaración, corrección documental, funcionalidad, cambio de alcance o evidencia por verificar.
3. **[Requiere humano]** Revisar con la autoridad indicada por el proyecto. Usar decisiones «pendiente», «aceptada», «rechazada» o «diferida», con motivo y referencia de autorización real y externa (§3.18) — no inventar firmas ni pedir de nuevo autorización ya concedida.
4. **[Requiere humano]** la decisión; **[IA]** su ejecución una vez tomada. Solo tras la decisión aplicable, actualizar requisitos/plan/backlog y ejecutar el trabajo autorizado. Cambios de alcance siguen el control local de baseline. Las aprobaciones de gates o releases requieren sus evidencias y autoridades propias. Quien implementa el cambio no debería ser también quien fija su `verification_status` o `decision_status` final (§3.18); cuando coincidan por falta de otra persona disponible, dejarlo explícito como «autoatestado».
5. **[IA]** Registrar resultado y verificaciones; un fallo o falta de prueba deja la brecha abierta o pendiente de validación. Si un revisor objetó y una autoridad aprobó igual, conservar esa objeción (§3.18) en vez de descartarla al cerrar la tarea — conservar la objeción es [IA], pero la decisión de aprobar pese a ella fue [Requiere humano].

La exportación, un contador, los ejemplos, un hash actualizado o esta guía no autorizan cambios ni aprueban producto. No conectar el dashboard a escritura automática de código, requisitos o sistemas operativos.

Una instrucción directa del usuario ([Requiere humano], ya concedida) puede autorizar actualizar la guía o completar el dashboard sin un JSON previo. Registrar la petición y su alcance en el seguimiento, ejecutar lo autorizado ([IA]) y conservar por separado las decisiones aún pendientes. No pedir de nuevo permiso para la misma tarea ni extender esa autorización al cierre de hallazgos o a cambios sin definir.

## 5. Actualizar con cada avance

Incorporar una regla enlazada en AGENTS y en la documentación de continuidad. El disparador operativo es explícito: **antes de marcar cualquier tarea o ítem del seguimiento/backlog como cerrado, y antes de cualquier commit que cambie código o documentación de producto relevante para un área del dashboard.** Ejemplos positivos (sí dispara la regla): cerrar una tarea del backlog; mergear una rama con cambios de producto; terminar una sesión que tocó requisitos. Ejemplos negativos (no la dispara): un commit de formato sin cambio de comportamiento; una exploración sin cambios persistidos; una pregunta respondida sin tocar código ni documentos.

Antes de cerrar cada tarea o entregar un avance relevante de requisitos, implementación, pruebas, evidencia, decisiones, bloqueos o riesgos:

1. Revisar qué áreas, preguntas, fuentes, contadores, bloqueos y riesgos cambian.
2. Actualizar el contenido afectado del dashboard, su README, fuentes y estado local. Si no cambia el diagnóstico, registrar «sin impacto en las brechas» y explicar por qué; no alterar estados solo para aparentar avance.
3. Añadir una entrada al seguimiento con fecha, tarea/avance, áreas afectadas, cambio o motivo de no impacto, fuentes/evidencias, verificaciones ejecutadas, decisiones pendientes y el valor actual de `verification_coverage`/`decision_coverage` (§3.17).
4. Si se usan hashes, inspeccionar primero el diff y aplicar las reglas de normalización de §3.16. Conservar el snapshot anterior y registrar el motivo de renovación. No regenerar hashes a ciegas para pasar controles. Distinguir fuentes históricas de la revisión vigente y evitar hashes autorreferentes.
5. Ante una fuente no revisada, inaccesible o cuya vigencia máxima (§3.16) ya venció, registrar «pendiente de conciliación» y no afirmar que el dashboard está vigente. Un control fallido no se oculta. Si esa fuente bloquea una decisión o entregable, abrir el bloqueo correspondiente (§3.15) en vez de dejarla como nota suelta.
6. Ejecutar las comprobaciones pertinentes, incluidos `verificar-fuentes.mjs`, `verificar-evidencia.mjs` y la validación de exportación si existen (§3.16) — y obligatoriamente si hay al menos un área `legal_fiscal_seguridad`/`datos_personales` (§3.8/§3.18). Si cambian HTML, comportamiento, estados o contadores, verificar interacciones, exportación, móvil/tableta/escritorio y ausencia de errores. Para cambios solo documentales, revisar enlaces, IDs y coherencia; no atribuir pruebas antiguas a la revisión nueva.
7. Verificar que ningún área marcada como implementada en el dashboard quede huérfana de su equivalente en los documentos de requisitos/pendientes del proyecto, y viceversa (trazabilidad cruzada, §3.16).

Esto es una obligación del flujo de trabajo de quien realiza cada avance; no es un servicio automático en segundo plano. Una futura automatización (hook de §3.16) debe definirse y verificarse como tarea separada.

## 6. Entregables y aceptación

- Dashboard local, README con apertura y límites, fuentes de la revisión, seguimiento y registro de propuestas/decisiones.
- Inventario de menús y características con IDs estables, cobertura pendiente y distinción entre código observado, ejecución funcional y aceptación humana (§1.1).
- Colecciones separadas de riesgos y bloqueos con severidad, antigüedad y escalamiento documentado (§3.15), aunque estén vacías.
- Observaciones por ficha, metadatos de revisión y exportación de alcance documentado, con separación de funciones y autoridad verificable cuando el riesgo del área lo exige (§3.18).
- JSON Schema del contrato de exportación y `validar-exportacion.mjs` (§3.8/§3.16): opcionales en un dashboard mínimo sin áreas de alto riesgo; **obligatorios, sin excepción**, en cuanto exista al menos un área `legal_fiscal_seguridad` o `datos_personales`, porque son el único control mecánico de la regla «sin excepción» de §3.18.
- Regla permanente en instrucciones del repositorio y actualización de tarea/resultado/estado según su estándar, con el disparador operativo explícito de §5.
- Brechas trazables a fuentes; lo desconocido y lo simulado se distinguen de lo probado y de lo autoatestado.
- Guardar/exportar no cambia estados oficiales; ninguna aprobación se deriva de llenar campos.
- Pruebas reales reportadas con alcance y límites. No declarar auditoría independiente, compatibilidad total o cumplimiento legal por probar la maqueta.
- Resultado con archivos, decisiones, limitaciones y siguiente acción. Git/publicación/despliegue solo según autorización vigente.

## 7. Objetivos, alcance y cronograma del proyecto

Todo lo anterior (§0–§6) diagnostica brechas documentales y de código de un proyecto ya en marcha. Esta sección y las cuatro siguientes (§8–§11) amplían la guía, de forma opcional, para **supervisar el proyecto como tal**: qué se busca lograr, cuándo, con qué artefactos de gerencia, qué riesgos tiene a nivel de proyecto (no solo de brecha documental), cómo se controla su calidad, y cómo cualquier equipo nuevo — humano o IA — puede retomarlo. No sustituye ninguna metodología de gestión de proyectos formal que el proyecto destino ya use (PMI, ágil, Shape Up, lo que sea); adapta su vocabulario al de esta guía solo si no tiene uno propio, siguiendo el mismo criterio de adopción incremental de §3.19.

### 7.1. Acta de objetivos y alcance (`project_charter`)

Un objeto, no una colección — un proyecto tiene una sola acta vigente a la vez, con historial append-only de revisiones (mismo patrón de `history[]` que el resto de la guía, §3.10):

| Campo | Tipo / regla |
|---|---|
| `objective` | Una o dos oraciones: el resultado que se busca, no una lista de tareas. Si el proyecto ya tiene esto en un README/plan real, citarlo y no reescribirlo desde cero. |
| `success_criteria[]` | Criterios medibles y verificables — «90 % de las operaciones del piloto sin intervención manual», no «que funcione bien». Cada uno con su propio `verification_status` (mismo enum de §3.10). |
| `scope_in[]`, `scope_out[]` | Qué entra y qué queda explícitamente fuera. Un `scope_out` sin registrar es la causa más común de que «mejora futura» se confunda con «bloqueador» (riesgo ya señalado en §3.3). |
| `stakeholders[]` | `{role, interest, authority_level, name_confirmed}` — rol sugerido por defecto, nunca un nombre real sin confirmación explícita (mismo criterio que `owner_role`/`person_assigned`, §3.10). |
| `constraints[]` | Restricciones reales: presupuesto, tiempo, regulatorias, de plataforma. Citar su fuente; no inventar un presupuesto o fecha límite que nadie declaró. |
| `assumptions[]` | Supuestos activos con fecha de registro y de próxima revisión — un supuesto no revisado en mucho tiempo es tan arriesgado como una fuente no reconciliada (§3.16). |
| `authority_ref` | Referencia externa verificable de quién aprobó el acta (§3.18) — un acta sin esto queda, igual que una decisión, «sin autorización verificable». |

**Flujo:** **[IA]** redacta el borrador del acta a partir de fuentes reales del proyecto (README, plan, requisitos) — nunca inventa objetivos o criterios de éxito que el proyecto no haya declarado en alguna parte. **[Requiere humano]** confirma o corrige el acta antes de tratarla como vigente; un acta en borrador se marca así explícitamente y no autoriza nada por sí sola (mismo principio de §4). Guardar en `docs/gerencia/acta-objetivos.md` o la ruta equivalente que el proyecto ya use.

### 7.2. Cronograma y fases

El cronograma **no es una colección nueva**: se construye sobre `milestones[]` (§3.20), que ya existe para esto. Esta sección añade un nivel más, opcional, de agrupación:

| Campo de `schedule.phases[]` | Tipo / regla |
|---|---|
| `id`, `label` | ID único de fase y nombre (p. ej. «Fase 0 — Descubrimiento», «Fase 1 — MVP», adaptar al vocabulario real del proyecto). |
| `planned_start`, `planned_end`, `actual_start`, `actual_end` | Fechas ISO; `null` con nota si no se han declarado. |
| `status` | Mismo enum que los hitos de §3.20: `planned`, `in_progress`, `done`, `delayed`. |
| `closing_milestone_ids[]` | IDs reales de `milestones[]` cuyo cierre marca el fin de esta fase — deben existir, sin referencias huérfanas (regla de §3.8 aplicada aquí también). |

**Regla mecánica:** una fase no puede declararse `done` si alguno de sus `closing_milestone_ids[]` sigue en `planned`/`in_progress`/`delayed` — la misma lógica de «sin excepción» de §3.18, aplicada al cronograma en vez de a la categoría de riesgo. Si se adopta `verificar-evidencia.mjs` o un script equivalente (§3.16), esta regla es mecánicamente comprobable, no solo descrita en prosa.

**Presentación:** una tabla de fases con fecha planeada/real es suficiente en la mayoría de los casos; un Gantt visual interactivo es opcional y solo si el proyecto lo justifica — no es un requisito de esta guía. Si se añade una vista de cronograma a la UI del dashboard, reutilizar los mismos componentes de línea de tiempo de §3.20 (nodos, colores de `status`, ficha de detalle), no un segundo lenguaje visual.

## 8. Artefactos de gerencia y administración generables

Lista de artefactos de gerencia que esta guía permite generar o mantener, cada uno **[IA] en borrador y [Requiere humano] en aprobación** (mismo flujo de §4), guardados por defecto en `docs/gerencia/` — o la convención que el proyecto ya tenga, adoptada incrementalmente (§3.19) en vez de forzar una carpeta nueva si ya existe una equivalente.

| Artefacto | Contenido mínimo | Se alimenta de |
|---|---|---|
| Acta de objetivos | Ver §7.1 | — |
| EDT/WBS simplificado | Entregables mayores desglosados en áreas/hitos existentes | `deliverables[]` (§3.3) y `milestones[]` (§3.20) — no una numeración paralela inventada desde cero |
| Matriz RACI | Responsable / Aprueba / Consultado / Informado por entregable o decisión mayor | `owner_role` (§3.3/§3.10) y `stakeholders[]` (§7.1) |
| Reporte de estado (periódico) | Periodo cubierto, avance por fase/hito desde el último reporte, riesgos/bloqueos abiertos y cerrados, decisiones pendientes, plan del siguiente periodo | `diff-exportaciones.mjs` (§3.16) para calcular qué cambió — no redactar un reporte de memoria cuando existe una herramienta que lo calcula |
| Minuta de reunión | Fecha, asistentes (roles), decisiones tomadas (con su ID real en `decisions[]`), tareas con responsable y fecha | `decisions[]` (§2/§3.18) |
| Registro de cambios de alcance | Qué cambió, cuándo, por qué | `hitos-alcance.json` (§3.16/§3.20) — no un changelog paralelo; un cambio de alcance mayor ya se registra ahí para el disparador de vigencia, reutilizarlo en vez de duplicarlo |

**Regla de no duplicación:** ningún artefacto de esta tabla introduce una fuente de verdad nueva para datos que ya viven en `deliverables[]`, `milestones[]`, `decisions[]`, `risks[]`/`blockers[]` o `hitos-alcance.json`. Cada artefacto es una **vista o reporte derivado** de esas colecciones — si un reporte de estado y el dashboard dicen cosas distintas sobre la misma área, hay un error de generación, no dos versiones legítimas de la verdad.

## 9. Gestión de riesgos del proyecto (nivel gerencial)

Esta sección **extiende** el modelo de `risks[]`/`blockers[]` de §3.15 — no crea una segunda colección paralela. Cuando se adopta la capa de supervisión de proyecto, añadir estos campos a cada riesgo existente:

| Campo adicional | Tipo / regla |
|---|---|
| `likelihood`, `impact` | Escala declarada por el proyecto (p. ej. 1–5 o baja/media/alta) — documentar cuál se usa, no mezclar escalas entre riesgos. |
| `risk_score` | Derivado de `likelihood` × `impact` según la fórmula declarada; nunca un número puesto a mano sin corresponder al cálculo. |
| `response_strategy` | `evitar` \| `mitigar` \| `transferir` \| `aceptar`. Distinto de `mitigation_plan`/`contingency_plan` (§3.15), que describen el *cómo*; este campo describe la *postura* elegida. |
| `early_warning_indicators[]` | Señales observables que, de aparecer, anticipan que el riesgo se está materializando — para no enterarse solo cuando ya es un bloqueo. |

**Cadencia de revisión:** revisar `risks[]` abiertos al menos en cada cierre de fase (§7.2) y declarar el resultado en el reporte de estado correspondiente (§8) — una lista de riesgos que nadie revisó desde hace dos fases es, en la práctica, letra muerta. Esta cadencia es adicional a la vigencia por tiempo/alcance mayor que ya aplica a fuentes y decisiones (§3.16); no la sustituye.

## 10. QA del proyecto (calidad del producto, distinta de la verificación del dashboard)

**Distinción explícita, para no confundir ambas:** §3.9/§3.16 verifican que *el dashboard mismo* funcione y que sus referencias sean reales — es QA de la herramienta de diagnóstico. Esta sección define QA *del producto que el proyecto destino está construyendo*, algo que el dashboard solo observa y registra, nunca certifica por sí mismo (principio ya establecido en §1.1 y §3.14: código observado no equivale a funcionamiento probado).

**Plan de calidad (`qa_plan`), campos mínimos:**

| Campo | Regla |
|---|---|
| `test_levels[]` | Niveles declarados que el proyecto realmente ejecuta: unitario, integración, extremo a extremo, manual, exploratorio. No declarar un nivel que no corre. |
| `entry_criteria`, `exit_criteria` (por fase o hito) | Condiciones objetivas y falsables para empezar/cerrar una fase de pruebas — p. ej. «0 defectos `blocker` abiertos y N pruebas E2E en verde», no «probado y funciona». Enlazar directamente con el hito de plantilla «Revisión en QA» de §3.20 cuando exista: su `changes[]` es el lugar natural para registrar qué criterio se cumplió y con qué evidencia. |
| `defect_severity` | Reutiliza el mismo enum de severidad de bloqueos (§3.15): `blocker`/`high`/`medium`/`low` — no inventar una segunda taxonomía de severidad para defectos de producto. |
| `known_bugs_ref` | Si el proyecto ya etiqueta defectos confirmados (p. ej. `bug-conocido`), reutilizar el indicador opcional de «bugs conocidos» del Resumen (§3.2) como vista de este dato — no construir un segundo tablero de bugs en paralelo. |

Guardar en `docs/gerencia/plan-de-calidad.md` o la convención ya existente del proyecto. Una «Revisión en QA» declarada `done` en `milestones[]` (§3.20) sin `exit_criteria` cumplidos y verificados es el mismo problema de autoatestación que ya cubre §3.18 para decisiones — degradarla a `in_progress` con la nota correspondiente en vez de darla por buena.

## 11. Documentación y continuidad para cualquier equipo (humano o IA)

§5 ya exige actualizar el dashboard con cada avance. Al adoptar la capa de supervisión de §7–§10, ese mismo disparador operativo se extiende a **todos** los artefactos de gerencia afectados — acta, cronograma, riesgos, plan de calidad — no solo al dashboard de brechas; el resto de §5 (qué cuenta como «sin impacto», cómo registrar fuentes no revisadas, qué verificaciones ejecutar) se aplica igual, sin reescribirlo aquí dos veces.

**Documento de continuidad:** un único archivo (`docs/CONTINUIDAD.md`, o el nombre equivalente que el proyecto ya use — adopción incremental, §3.19) que cualquier persona o IA nueva en el proyecto pueda leer en menos de diez minutos y entender: qué existe y qué falta, dónde está la fuente de verdad de cada artefacto (acta, cronograma, riesgos, plan de calidad, dashboard), qué decisiones siguen pendientes y de quién, y cuál es el siguiente paso real — el mismo contenido que ya resuelve la tarjeta «El siguiente paso» del Resumen (§3.2), pero a nivel de todo el proyecto, no de una sola área. Enlazarlo desde README/AGENTS/CLAUDE como primera lectura obligatoria para cualquier incorporación nueva.

**Relación con el Skill `supervisor-proyectos`:** esta guía existe también empaquetada como Skill de Claude Code, pensado para invocarse como comando dentro de un proyecto y guiar paso a paso el descubrimiento (§1), el diseño del diagnóstico (§2), la construcción del dashboard (§3) y, cuando corresponda, la capa de supervisión (§7–§11) — usando este mismo documento como cuerpo de conocimiento, sin duplicar su contenido en el Skill. Un equipo sin Claude Code puede seguir usando este Markdown de forma autónoma, exactamente igual que antes de que existiera el Skill.

## Plantilla mínima de seguimiento

| Fecha | Tarea/avance | Áreas | Actualización o motivo de no impacto | Fuentes/evidencia | Verificaciones | Decisión pendiente |
|---|---|---|---|---|---|---|
| AAAA-MM-DD | ID real o referencia | IDs reales | Descripción verificable | Ruta y sección | Ejecutadas / no ejecutadas | Referencia o ninguna |

## Plantilla mínima de revisión de propuestas

| ID local | Origen/revisión | Propuesta e impacto | Decisión | Autorización/criterio | Tarea y evidencia de cierre |
|---|---|---|---|---|---|
| ID por asignar | JSON/respuesta y fecha | Por revisar | Pendiente | Por confirmar (referencia externa, §3.18) | Sin implementar |

## Plantilla mínima de bloqueos y riesgos

| ID | Tipo | Severidad | Categoría | Abierto desde | Vence/revisar | Dueño / seguimiento | Escalado a | Siguiente acción |
|---|---|---|---|---|---|---|---|---|
| BLK/RSK por asignar | bloqueo / riesgo | blocker/high/medium/low | según §3.10/§3.15 | AAAA-MM-DD | AAAA-MM-DD o ninguna | rol / rol de seguimiento | ninguno | Por definir |

Las filas anteriores son plantillas, no hallazgos ni aprobaciones reales.

## Procedimiento para comparar y fusionar guías equivalentes

Cuando aparezca una guía equivalente a esta (de otro proyecto o de otra sesión) y haya que decidir qué incorporar a la semilla genérica, seguir este método en vez de improvisar cada vez:

1. Leer ambas guías completas, no solo su tabla de cambios o resumen.
2. Separar cada mecanismo nuevo en dos categorías: **genérico** (reutilizable sin vocabulario de un dominio concreto) o **específico de dominio** (DOR, gates, RACI, cifras de muestra, nombres de personas, requisitos fiscales o logísticos de un proyecto real).
3. Incorporar a la semilla solo lo genérico, generalizándolo como plantilla/placeholder cuando el mecanismo original estaba anclado a un dominio. Lo específico de dominio queda como referencia histórica en un anexo, claramente etiquetado «no copiar», o se descarta si no aporta un patrón reutilizable.
4. Verificar que la incorporación no duplique ni contradiga una sección ya existente de la semilla; si dos guías resuelven lo mismo de forma distinta, documentar ambas variantes en una tabla (como la de paleta en §3.1) en vez de elegir una arbitrariamente y perder la otra.
5. Registrar en la tabla de «Cómo usar y qué cambió», al inicio del documento, de qué guía u análisis proviene cada bloque incorporado, para que una fusión futura no tenga que releer todo el historial para saber qué ya se consideró.
6. Actualizar el glosario de equivalencias si la guía incorporada usa vocabulario distinto para un concepto ya existente en la semilla.

## Diagrama de flujo de gobernanza

El diagrama se movió a **§0.6**, cerca del inicio del documento, para que quede visible antes de leer la prosa de §4 y §3.18 en vez de solo al final — no se duplica aquí para no tener dos copias que puedan desalinearse entre sí.

## Anexo A. Ejemplo mínimo neutral (patrón a copiar)

Tres áreas ficticias sin vocabulario de ningún dominio concreto, para copiar la estructura sin tener que discriminar manualmente qué es idiosincrasia de un proyecto real y qué es el patrón genérico. No son hallazgos de ningún proyecto; sustituir su contenido por el del proyecto destino.

```json
{
  "deliverables": [
    {
      "id": "X-01",
      "title": "Autenticación de usuarios",
      "category": "Acceso",
      "risk_category": "datos_personales",
      "owner_role": "Responsable técnico (rol sugerido, sin nombramiento)",
      "official_status": "parcial, según código observado",
      "implementation_status": "partial",
      "verification_status": "not_verified",
      "decision_status": "pending",
      "source_refs": ["src/auth/login.ts"],
      "gap": "El flujo de recuperación de contraseña no tiene prueba automatizada conocida.",
      "acceptance_criteria": "Una prueba de extremo a extremo cubre login, fallo de credenciales y recuperación.",
      "next_action": "Confirmar si existe una suite de pruebas y ejecutarla con evidencia.",
      "fields": [
        {"key": "flows", "label": "Flujos cubiertos", "hint": "Login, registro, recuperación.", "example": "Login y registro documentados; recuperación sin prueba"},
        {"key": "risks", "label": "Riesgos de acceso", "hint": "Sesiones, bloqueo de cuenta, fuerza bruta.", "example": "Sin límite de intentos observado"},
        {"key": "evidence", "label": "Evidencia disponible", "hint": "Commit, log o run de CI, no solo una afirmación.", "example": "Sin evidencia externa todavía"},
        {"key": "next", "label": "Siguiente acción", "hint": "Paso concreto y responsable.", "example": "Por asignar"}
      ]
    },
    {
      "id": "X-02",
      "title": "Exportación de datos",
      "category": "Datos",
      "risk_category": "funcional",
      "owner_role": "Producto (rol sugerido)",
      "official_status": "documentado, sin ejecución verificada",
      "implementation_status": "implemented",
      "verification_status": "pending",
      "decision_status": "pending",
      "source_refs": ["docs/requisitos.md#exportacion"],
      "gap": "No hay evidencia de que la exportación se haya probado con datos reales del tamaño esperado.",
      "acceptance_criteria": "Una exportación de muestra se ejecuta sin error y su formato se valida contra el esquema.",
      "next_action": "Ejecutar una exportación de prueba y adjuntar el archivo resultante como evidencia.",
      "fields": [
        {"key": "format", "label": "Formato de salida", "hint": "CSV, JSON u otro.", "example": "JSON, sin confirmar"},
        {"key": "volume", "label": "Volumen esperado", "hint": "Orden de magnitud de registros.", "example": "Desconocido"},
        {"key": "evidence", "label": "Evidencia de ejecución", "hint": "Archivo de salida o log real.", "example": "Ninguna todavía"},
        {"key": "next", "label": "Siguiente acción", "hint": "Paso concreto.", "example": "Por definir"}
      ]
    },
    {
      "id": "X-03",
      "title": "Notificaciones por correo",
      "category": "Comunicación",
      "risk_category": "operativo",
      "owner_role": "Operación (rol sugerido)",
      "official_status": "no iniciado",
      "implementation_status": "not_started",
      "verification_status": "not_applicable",
      "decision_status": "pending",
      "source_refs": ["PENDIENTES.md#notificaciones"],
      "gap": "No existe código ni diseño del flujo de notificaciones todavía.",
      "acceptance_criteria": "Decisión de alcance: qué eventos notifican, a quién y por qué canal.",
      "next_action": "Programar una decisión de alcance antes de estimar esfuerzo.",
      "fields": [
        {"key": "events", "label": "Eventos a notificar", "hint": "Lista de disparadores candidatos.", "example": "Sin definir"},
        {"key": "channel", "label": "Canal", "hint": "Correo, push u otro.", "example": "Correo, tentativo"},
        {"key": "owner", "label": "Responsable de la decisión", "hint": "Rol, no persona.", "example": "Producto"},
        {"key": "next", "label": "Siguiente acción", "hint": "Paso concreto.", "example": "Agendar decisión de alcance"}
      ]
    }
  ],
  "blockers": [],
  "risks": [
    {
      "id": "RSK-01",
      "description": "El volumen real de datos a exportar (X-02) podría exceder lo probado en desarrollo.",
      "category": "tecnico",
      "probability": "media",
      "impact": "medio",
      "severity": "medium",
      "mitigation_plan": "Probar con un volumen sintético diez veces mayor al esperado antes de habilitar en producción.",
      "contingency_plan": "Paginar la exportación si el volumen real supera el umbral probado.",
      "owner_role": "Responsable técnico",
      "follow_up_owner_role": "Producto",
      "status": "open",
      "review_by": null,
      "related_decision_id": null,
      "related_source_id": null,
      "history": []
    }
  ]
}
```

Este ejemplo es el patrón a copiar al empezar una adaptación nueva. El **Anexo B** siguiente es un inventario real de un proyecto de referencia: léase como evidencia de que el patrón funciona en un caso real, no como plantilla a copiar literalmente.

## Anexo B. Inventario histórico de un proyecto de referencia (no copiar)

Extraído directamente del `index.html` de un dashboard de preparación y brechas real, revisado en su momento, para documentar cómo se ve la interfaz con datos reales de un dominio concreto (en este caso, software de contabilidad fiscal mexicana). Esta fecha acredita la lectura de ese HTML, no una nueva conciliación de sus fuentes de producto ni la vigencia actual de sus hallazgos. Todas las respuestas iniciales estaban vacías; cada campo es textarea de dos filas, máximo 1200 caracteres. Los ejemplos siguientes son sintéticos, no evidencia. Conservar orden y claves para entender la referencia; no reutilizar su vocabulario fiscal en un proyecto de otro dominio.

### NX-01 · Alcance de la primera operación

**Estado mostrado:** Por definir. **Rol de revisión:** Producto + despacho piloto.

**Fuente mostrada:** README.md · REQUIREMENTS.md §1/§7 · PENDING.md §3.

**Criterio mostrado:** Perfil del primer caso de uso y flujos incluidos/excluidos aceptados por las personas responsables. El ejercicio no certifica el MVP ni agrega automáticamente mejoras futuras.

| Orden | Clave | Etiqueta | Preguntas vinculadas al área | Ayuda | Ejemplo sintético |
|---|---|---|---|---|---|
| 1 | audience | Perfil del primer despacho | NX-Q-01 | Sin nombres, RFC ni información de clientes. | Despacho de ejemplo / caso sintético |
| 2 | flows | Flujos que entran en la revisión | NX-Q-01 | Acordar módulos y tipos de operación a evaluar. | Ingreso/Egreso y contabilidad del caso ficticio |
| 3 | exclusions | Límites que deben comunicarse | NX-Q-01 | Separar manual, simulado y fuera de alcance. | Timbrado externo; Nómina/Pago no asumidos reales |
| 4 | acceptance | Qué evidencia requiere la aceptación | NX-Q-01 | Responsable por designar, escenarios y criterio. | Escenarios sintéticos, sin acta real |

### NX-02 · Facturación y timbrado

**Estado mostrado:** Flujo manual. **Rol de revisión:** Producto + contador responsable.

**Fuente mostrada:** REQUIREMENTS.md §7.3.1 · PENDING.md §3 · código del módulo de CFDI.

**Criterio mostrado:** Distinguir el flujo manual implementado de Ingreso/Egreso del timbrado simulado de Nómina/Pago. La integración con un PAC externo es mejora futura, no bloqueador nuevo. Esta revisión no emite, firma ni timbra comprobantes.

| Orden | Clave | Etiqueta | Preguntas vinculadas al área | Ayuda | Ejemplo sintético |
|---|---|---|---|---|---|
| 1 | types | Tipos de comprobante a evaluar | NX-Q-02 | Clasificar por alcance documentado, sin emitir XML real. | Ingreso/Egreso: manual; Nómina/Pago: simulado |
| 2 | handoff | Paso fuera del sistema | NX-Q-02 | Quién realiza el paso externo y cómo vuelve al flujo. | Firma/timbrado externos en escenario demo |
| 3 | confirmation | Confirmación y rechazos | NX-Q-02 | Datos sintéticos y resultado esperado del flujo. | XML de ejemplo; confirmación y rechazo por revisar |
| 4 | evidence | Referencia de revisión del recorrido | NX-Q-02 | No subir XML con datos fiscales ni credenciales. | Caso DEMO-CFDI-01; sin ejecución real |

### NX-03 · Motores y reportes fiscales

**Estado mostrado:** Alcance documentado. **Rol de revisión:** Responsable fiscal + Producto.

**Criterio mostrado:** Inventariar motores y periodos según código/documentación, validar escenarios por especialista y conciliar resúmenes desactualizados. No se valida legislación, tasas, cifras ni declaraciones reales en esta maqueta.

*(Áreas NX-04 a NX-10 del mismo proyecto de referencia — correo y recuperación de acceso, usuarios/permisos/aislamiento, respaldos y recuperación, interfaz y acciones pendientes, pruebas y compatibilidad, preparación operativa del MVP, y coherencia de la documentación — siguen el mismo patrón de cuatro campos, rol de revisión, fuente y criterio mostrado. Su detalle completo se conserva en el histórico del proyecto de origen y no se reproduce íntegro aquí para no inflar esta guía genérica con contenido de un solo dominio; el patrón a replicar es el de NX-01/NX-02 anteriores y el del Anexo A.)*

Una nota de ese proyecto de referencia es, en sí misma, un ejemplo real del gap de automatización que cierra §3.16: su repositorio llegó a tener un script de verificación de cobertura de campos (`cobertura-campo.mjs`) que recorría el código fuente para detectar dónde un campo nuevo tenía un hermano sin el mismo dato — invocado por una skill de revisión antes de dar por terminado cualquier cambio, con código de salida distinto de cero si encontraba huecos. Esa misma lógica es la que §3.13/§3.16 generalizan explícitamente como patrón técnico reutilizable para cualquier campo, rol o permiso nuevo del proyecto destino — no solo para la trazabilidad cruzada del propio dashboard, que es apenas una aplicación particular de la técnica. La automatización descrita en esta guía no es aspiracional: ya existe como patrón real en al menos un proyecto que la usó como gate antes de cerrar un cambio.

### Decisiones de referencia (ejemplo histórico)

| ID | Familia | Asunto |
|---|---|---|
| MVP-01 | Preparación | Definir la primera operación: acordar alcance del caso piloto y límites del producto sin convertir toda mejora futura en bloqueador. |
| NEG-01 | Mejoras | Invitaciones de usuarios: el flujo de invitación por correo es una decisión distinta de la recuperación de cuenta. |
| TEC-01 | Técnica | Pruebas del producto: acordar escenarios de extremo a extremo y alcance de pruebas existentes; no asumir que una maqueta las sustituye. |

Estas decisiones se mostraban «Por revisar» en el proyecto de origen. Sus textos no constituyen decisiones aceptadas ni requisitos de ningún proyecto destino.

## Historial de la guía

| Versión | Cambio |
|---|---|
| Sin versión | Procedimiento de revisión, mantenimiento y plantillas de seguimiento. |
| 2.x | Especificación de menús, apariencia e interacciones; prompt portable; contrato de exportación v1/v2; diccionario ampliado; matriz observado/propuesto. |
| 3.0.0 · 2026-10-19 | Fusión con una guía equivalente centrada en inventario de superficie funcional y con otra centrada en especificación visual/DOM de referencia y checklist agrupado; cierre de brechas de gobernanza (separación de funciones, autoridad verificable, historial append-only, objeción registrada, meta-gobernanza), usabilidad (ruta rápida, glosario, ejemplo mínimo neutral, heurística de número de áreas, diagrama único, adopción incremental), profundidad técnica (JSON Schema, algoritmo de hash normalizado, script de staleness, diff histórico, métricas de cobertura de verificación/decisión) y gestión de riesgos (colecciones separadas de riesgos y bloqueos, severidad, SLA, matriz de escalamiento, seguimiento interino). |
| 3.0.1 · 2026-10-19 | Corrección de completitud sobre 3.0.0, a partir de una revisión que encontró siete puntos no resueltos o resueltos solo parcialmente: convención de etiquetado [IA]/[Requiere humano] desde §0.4, aplicada en §0.5 y §4; `verificar-evidencia.mjs` para resolver `source_refs[]`/`evidence_refs[]` contra el repositorio real (§3.16), distinto de `verificar-fuentes.mjs`; segundo disparador de vigencia por cambio de alcance mayor (`hitos-alcance.json`, §3.16), no solo por antigüedad; generalización explícita del patrón «hermano sin cobertura» a campos de código arbitrarios, con fila propia en la matriz de §3.13; diagrama de flujo movido a §0.6, cerca del inicio; condición `if/then` mecánica en el JSON Schema v2 para la regla «sin excepción» de áreas de alto riesgo (§3.18), verificable por `validar-exportacion.mjs`; y un único criterio opcional/obligatorio para los scripts y JSON Schema de verificación (§3.8), en vez de tratarlos como opcionales en un lugar y obligatorios en otro. |
| 3.0.2 · 2026-10-21 | A partir de una captura de pantalla real de un proyecto de referencia (Nexia/conta01): convención opcional de título de vista redactado como enunciado breve de propósito, distinto por cada una de las cinco vistas, en vez de frase descriptiva (§3.1); estructura de cuatro partes — etiqueta fija, título en modo de acuerdo/acción, oración de brecha pendiente y botón al área que define el alcance real — para la tarjeta «El siguiente paso» del Resumen (§3.2). Ambas convenciones son opcionales y no alteran los contratos de exportación ni las reglas de gobernanza ya descritas. |
| 3.1.0 · 2026-10-21 | A partir del `index.html` real completo de la misma referencia (Nexia/conta01), más allá de la captura de pantalla de 3.0.2: catálogo opcional de look and feel ampliado en §3.1 — tres variantes de botón, set único de iconos lineales, cuatro insignias de estado reutilizables, tarjeta decorativa de «siguiente paso», indicador de fase en la barra lateral y estilo de foco visible, cada punto adoptable por separado. Añade además una capacidad nueva, también opcional: línea de tiempo de hitos del proyecto (§3.20) con modelo `milestones[]`, ficha de detalle por hito que registra qué se definió/agregó/cambió/quitó con sus fuentes, cuatro hitos de plantilla (inicio del proyecto, MVP, revisión en QA, salida a producción) adaptables sin ser obligatorios, exportación en el contrato v2 (§3.11), fila propia en la matriz de §3.13 y reutilización explícita como fuente de `hitos-alcance.json` en vez de duplicar ese inventario (§3.16). Ninguna de las dos incorporaciones es obligatoria ni cambia los contratos ya descritos para quien no las adopte. |
| 4.0.0 · 2026-10-21 | Evolución de alcance mayor, a petición explícita: la guía deja de cubrir únicamente el dashboard de preparación y brechas y añade una capa opcional de **supervisión de proyecto**, construida sobre las colecciones ya existentes sin duplicarlas: §7 objetivos/alcance (`project_charter`, §7.1) y cronograma de fases sobre `milestones[]` ya existente (§7.2, antes §3.20); §8 artefactos de gerencia generables (acta, EDT/WBS, RACI, reporte de estado, minuta, registro de cambios de alcance) como vistas derivadas, nunca fuentes de verdad paralelas; §9 extensión de `risks[]`/`blockers[]` (§3.15) con probabilidad/impacto/estrategia de respuesta/indicadores de alerta temprana a nivel de proyecto; §10 plan de calidad del producto (`qa_plan`), explícitamente distinto de la verificación del dashboard (§3.9/§3.16), enlazado al hito «Revisión en QA» de §3.20; §11 documento de continuidad único para cualquier equipo nuevo (humano o IA), que amplía el disparador de §5 a todo el paquete de supervisión. Se empaqueta además como Skill de Claude Code (`supervisor-proyectos`) que usa este documento como cuerpo de conocimiento, sin bifurcar el contenido. Toda la capa §7–§11 es opcional y adoptable por partes, igual que §3.14 en adelante; no cambia los contratos de exportación v1/v2 ni las reglas de gobernanza de §3.18 para quien no la adopte. |
| 4.0.1 · 2026-10-21 | Corrección de tres brechas de usabilidad detectadas al revisar en navegador real la primera aplicación de esta guía (Nexia/conta01), sin cambiar contratos de exportación ni reglas de gobernanza: (1) §3.20 — la línea de tiempo de hitos pasa de estar al final del Resumen a ser uno de sus primeros elementos, para que el contexto del proyecto se lea antes que el detalle de cada área; (2) §3.2 — los pasos de la secuencia visual «Del diagnóstico a una decisión explícita» dejan de ser texto decorativo: cada uno que corresponda a una vista/ficha real navega ahí, reutilizando el mecanismo de apertura ya existente; un paso sin destino real lo declara en su propia etiqueta en vez de simular un enlace; (3) §3.2/§3.15 — cada discrepancia, riesgo o bloqueo de la columna lateral exige una ficha de detalle propia al hacer clic (campos completos, evidencia citada), no solo un resumen sin forma de ver el resto. Añadido también como punto de aceptación explícito en §3.9. |
