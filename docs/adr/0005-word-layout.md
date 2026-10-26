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
