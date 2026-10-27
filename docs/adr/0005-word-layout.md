# ADR 0005: Word editable con geometría, tipografía e imágenes

Fecha: 2026-10-26. Estado: aceptado para el prototipo local por instrucción
del usuario («procede con las mejoras que propones»). Amplía el alcance de
Word del ADR 0004; mantiene pendiente el Gate F0.

El exportador anterior descartaba imágenes y estilos, creaba un párrafo
por línea con formato predeterminado y añadía un anexo obligatorio. Se
conserva pdfplumber como extractor y python-docx como exportador. Se usa
el PDFium ya instalado (pypdfium2 5.14.0, fijado en el subconjunto probado)
para representar los elementos gráficos que Word no puede reconstruir.
No se incorpora un servicio externo ni pdf2docx/PyMuPDF.

## Representación y exportación

El IR 1.1.0 añade campos opcionales compatibles con documentos 1.0.0:
fragmentos con fuente, tamaño, negrita, cursiva y color; líneas posicionadas
dentro de tablas; medidas de filas/columnas y recursos PNG autocontenidos.
La geometría de esta ruta se expresa desde arriba/izquierda en puntos PDF.
Las coberturas y confianzas no medidas continúan siendo null.

Las páginas digitales usan párrafos con `w:framePr`, tablas con `w:tblpPr`
y dibujos con `wp:anchor`, relativos a la página. Cada página de entrada
origina una sección con sus dimensiones. El texto sigue siendo texto de
Word: puede editarse, guardarse y reabrirse. Las tablas sencillas conservan
su estructura, anchos y combinaciones detectadas. Las alturas son mínimas,
para que una edición no recorte silenciosamente contenido.

Los paneles detectados como tablas que contienen celdas de más de tres
líneas usan sus líneas originales posicionadas; se emite
`DOCX_TABLE_AS_POSITIONED_TEXT`. Es una heurística de representación,
no una clasificación semántica validada. Las tablas del IR/Excel se mantienen.

Los tipos PDF estándar Helvetica/Times/Courier se mapean a
Arial/Times New Roman/Courier New y se registra la sustitución. Otras
fuentes se solicitan por nombre: su disponibilidad depende del visor.

## Imágenes y gráficos

Se abre una copia privada en memoria del PDF, se eliminan los objetos de
texto —también dentro de formularios— y se comprueba que no quede texto
en la jerarquía admitida. Los recortes de imágenes y una capa transparente
de gráficos se codifican como PNG nuevos dentro del IR y del DOCX. La capa
gráfica puede abarcar el área de contenido, pero no contiene el texto
digital extraído. No se usa una captura completa como sustituto del texto.
Los gráficos vectoriales pasan a imagen; no son figuras vectoriales editables.
El archivo fuente nunca se modifica. No se cargan imágenes por URL ni por
una ruta externa al exportar el IR.

Límites: 8 millones de píxeles por render, escala máxima 2.5 (180 DPI),
100 imágenes por página, 12 MiB por PNG y 48 MiB de PNG por documento antes
de base64. Se serializa el acceso de esta ruta a PDFium porque no es seguro
entre hilos. Una jerarquía de formularios que exceda la profundidad admitida,
una discrepancia geométrica, un fallo de render o un presupuesto excedido
producen `LAYOUT_ASSETS_UNAVAILABLE`; se conserva el texto disponible.

En páginas OCR, la geometría del texto todavía no está validada. Se exporta
en flujo y se omite el fondo escaneado para evitar texto duplicado. Una
página escaneada sin OCR puede conservarse como imagen y mantiene
`OCR_REQUIRED`; no se presenta como texto editable.

## Advertencias y validación

Las notas permanecen en resultados e IR, con estado `needs_review`. El
anexo Word es opcional (`--docx-warnings` / casilla del formulario) y está
desactivado por defecto. El JSON se serializa después de exportar, para
incluir las advertencias de sustitución de fuentes y representación.

Las pruebas automatizadas usan PDFs sintéticos públicos dentro del test:
estilos, espacios, dos columnas, Form XObjects, páginas vertical/horizontal,
tabla combinada, imágenes, portabilidad del IR, límites y errores.
Una comprobación local adicional abre y renderiza en Microsoft Word un
comprobante proporcionado por el usuario y el caso sintético de dos páginas.
Los archivos reales y sus vistas permanecen en `.generated/docx-review/`.

No se promete paginación idéntica tras editar ni compatibilidad visual
equivalente en Word web, LibreOffice u otros visores no probados. Los
marcos posicionados favorecen la apariencia sobre la edición como flujo
continuo. Texto girado, anotaciones y formularios interactivos requieren
revisión. Esta ampliación no cierra la validación de tres diseños con
ground truth ni aprueba F0-04, F0-09 o F0-11. La distribución efectiva de
PDFium y sus avisos sigue dentro de la revisión pendiente de licencias.

## Revisión 2026-10-27: tablas y validación de tres diseños

La revisión completa de tres diseños reales encontró cuadrículas falsas
producidas por rellenos pintados, filas de relleno que crecían en Word y
estilos perdidos en celdas adyacentes. La ruta de diseño puede sustituir
una cuadrícula por otra sin rellenos grandes (>2 puntos en ambos ejes)
cuando cubre más del 95% de la región original, tiene menos celdas y
conserva el multiconjunto de caracteres no blancos. Son guardas heurísticas,
no una puntuación de calidad. Se informa `TABLE_DECORATION_FILTERED`.

Se extraen los estilos dentro de cada celda, se fijan márgenes globales
cero y se aplican sangrías/espaciado por párrafo. Las filas conservan altura
mínima y los párrafos vacíos usan una línea pequeña para no expandir el
relleno. Las páginas sin objetos detectados usan `EMPTY_PAGE`, sin pedir OCR.

Resultados y límites: [VALIDACION_WORD_F0.md](../VALIDACION_WORD_F0.md).
Se mantienen pendientes la adjudicación humana, el muestreo representativo
y el Gate F0; no se sustituye esa aceptación por un conteo de caracteres.

## Revisión 2026-10-27: texto superpuesto por sustitución de fuente

El usuario reportó, en un comprobante bancario real convertido con el MVP
desplegado, texto superpuesto: el título se encimaba con el folio y un
nombre de empresa en dos líneas se encimaba con la dirección debajo. La
causa no era el espaciado entre líneas posicionadas (hipótesis inicial,
corregida primero con un límite de espaciado basado en la distancia real al
siguiente elemento), sino la fuente incrustada del PDF (`Lato-Bold`), que no
está en el mapa de alias y se solicitaba a Word por su nombre literal. Word
la sustituye con un reemplazo propio impredecible, más ancho que el medido
en el PDF, y el texto se envuelve a una segunda línea dentro de su propio
marco de una sola línea, encimándose con el contenido siguiente.

Corrección: cualquier fuente no reconocida (no es Helvetica/Times/Courier ni
una fuente seguramente instalada como Arial/Calibri/Georgia) ahora se
solicita como Arial, una sustitución predecible y ya contemplada por el
margen de ancho del marco (ampliado de +5 pt fijo a +15% proporcional). La
advertencia `DOCX_FONT_SUBSTITUTED` ahora también cubre estas fuentes no
estándar; antes solo se registraba para Helvetica/Times/Courier. Verificado
contra el documento real del usuario (evidencia privada en
`.generated/docx-review/`, no en Git) y renderizado en Microsoft Word real:
sin superposición. Pruebas nuevas en `tests/unit/test_docx_layout.py`.

## Revisión 2026-10-27: palabras unidas sin espacio en texto de fuente pequeña

El usuario reportó un segundo documento real (una Constancia de Situación
Fiscal del SAT) donde palabras aparecían pegadas sin espacio, tanto en una
celda de tabla ("Sociedadesfinancierasdeobjetomúltiple") como en un párrafo
de texto corrido ("Susdatospersonalessonincorporados..."). Causa: el PDF
posiciona cada palabra individualmente sin un glifo de espacio real entre
ellas (común en generadores de PDF gubernamentales/administrativos), y el
hueco visual real (~2.2-2.9 pt a 8 pt de tamaño) es menor que el
`x_tolerance=3` por defecto de pdfplumber para insertar un espacio
sintético — tanto en `Table.extract()` (celdas) como en
`pdfplumber.utils.extract_text()` (texto libre, usado como referencia de
reconciliación de `styled_runs`).

Corrección en tres puntos que deben mantenerse consistentes entre sí: (1)
`packages/converters/digital.py` llama `found.extract(x_tolerance=1)` en
vez del valor por defecto; (2) `packages/converters/layout.py::styled_runs`
usa un umbral proporcional al tamaño de fuente (`max(1, size*.2)`) en vez de
un valor fijo de 3 pt; (3) el texto "esperado" que calcula
`positioned_lines` (usado por la verificación de reconciliación de
`styled_runs`) usa la misma fórmula proporcional — de lo contrario, aunque
`styled_runs` reconstruyera los espacios correctamente, la reconciliación
los descartaría por no coincidir con un texto de referencia que seguía
teniendo el mismo error. Verificado contra el documento real del usuario
(dos páginas completas, evidencia privada en `.generated/docx-review/`, no
en Git) y renderizado en Microsoft Word real: texto correctamente separado
en la tabla y en los párrafos. Prueba nueva en `tests/unit/test_docx_layout.py`
que reproduce el hueco real (~2.2 pt a 8 pt) sin glifo de espacio.

## Revisión 2026-10-27: documentos escaneados largos se quedaban en blanco

El usuario reportó un tercer documento real (un periódico de 32 páginas,
`Milenio-23-12-2025.pdf`, completamente escaneado, sin texto digital en
ninguna página) donde la conversión a Word "solo alcanzó" unas pocas
páginas; el resto aparecía vacío. Causa real: cada página completa se
preserva como imagen de respaldo (`kind='scanned_page'`, ya que no hay texto
que posicionar) codificada como PNG sin pérdida — para contenido fotográfico
real esto pesaba ~6 MB por página — y el presupuesto compartido de
imágenes por documento (`MAX_DOCUMENT_ASSET_BYTES`, 48 MB) se agotaba justo
después de la página 8. Las páginas siguientes no tienen texto (es un
escaneo, `OCR_REQUIRED`) ni imagen (`LAYOUT_ASSETS_UNAVAILABLE` por
presupuesto excedido), así que quedan completamente vacías en Word, aunque
la sección de cada página sí se crea.

Corrección: las imágenes de página completa (`kind='scanned_page'`) se
codifican como JPEG calidad 85 en vez de PNG — son una copia visual de
respaldo ya marcada `OCR_REQUIRED`, no texto autoritativo, por lo que la
pérdida de calidad JPEG no compromete nada que el documento ya reclame como
exacto. En el documento real esto redujo el tamaño por página de ~6 MB a
~1.2 MB (5x), permitiendo que las 32 páginas completas quepan. El
presupuesto compartido también se amplía de 48 MB a 150 MB como margen
adicional para documentos largos. El validador de imágenes de Word
(`packages/exporters/docx.py::_picture`) ahora acepta PNG o JPEG; las
imágenes incrustadas normales (`kind='embedded'`) y la capa de gráficos
(`kind='graphics'`) siguen en PNG sin cambios, por si necesitan
transparencia. Verificado con el documento real completo (32/32 páginas con
imagen, sin advertencias de presupuesto excedido) y render real en
Microsoft Word: las 32 páginas, incluida la última, muestran su contenido
correctamente. Prueba nueva en `tests/unit/test_docx_layout.py` que
reproduce la proporción de tamaño real (PNG ~770 KB vs JPEG ~98 KB a la
misma resolución) con un presupuesto reducido.
