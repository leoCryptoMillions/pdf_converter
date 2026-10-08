# ADR 0004: prototipo F0 local con datos conservadores

Fecha: 2026-10-08. Estado: aceptado para el experimento F0.

La arquitectura base existe, pero los convertidores y exportadores estaban
vacíos y solo una factura sintética tenía referencia. Se necesita evidencia
de conservación del contenido antes del flujo web.

Implementar CLI con extracción digital pdfplumber y exportadores separados
para XLSX, DOCX y TXT. No declarar todavía un motor definitivo: pdfplumber
superó a Camelot en un estado de cuenta real, pero solo se puntuaron dos
PDFs con tablas. Todas las conversiones mantienen estado `needs_review`.

Excel conserva texto por defecto y permite tipos numéricos mediante mapa
explícito de columnas, con formato regional en_US y guardas de precisión.
Los originales permanecen en una hoja independiente. Word prioriza edición
y contenido; imágenes, estilos y firmas quedan fuera del prototipo.

`Page.text_coverage` admite null cuando no hay referencia. No usar cero ni
uno para representar una calidad que no fue medida. No fabricar confianza
de tablas/celdas. La geometría se declara en puntos desde arriba/izquierda.

Las anotaciones reales y resultados quedan fuera de Git; las referencias
nuevas incluyen revisión, alcance y SHA256. Los borradores no se puntúan.
Separar CER regional de página completa y F1 de filas de detección/estructura.

No aprobar F0 con esta muestra pequeña ni con cobertura parcial por documento.
La CLI no sustituye el aislamiento ni el flujo de permisos/cola/storage de F1.

Revisión posterior del 2026-10-08: el CER Word de 4.675% se debía a una
referencia incompleta e incorrectamente transcrita. Tras adjudicación visual,
el texto tiene CER 0% en ambas rutas, pdfplumber y un baseline PDFium textual.
No se cambió el extractor para eliminar el pie ni corregir erratas del original.
El baseline no declara reconstrucción de estructura, tablas ni imágenes.

La ampliación mide una tabla de la página 19 de un documento de 19 páginas y
texto completo de las páginas 1 y 3 de un escaneo de 14 páginas. Estos alcances
se registran explícitamente. La portada OCR no alcanza el umbral candidato
del 2%, mientras que el texto continuo sí; OCR difícil sigue en 9.125% para
una región. Mantener F1 pendiente de calidad por clase, licencias y costo.

La continuidad entre páginas se registra solo como candidato cuando las
columnas y los bordes coinciden. Conservar segmentos separados y advertir
que las filas de frontera necesitan revisión: unirlas o deduplicar importes
sin evidencia podría mezclar transacciones. La muestra comprueba 16 celdas
de frontera, sin aprobar reconstrucción automática de filas partidas.
Las variantes OCR no mejoraron la portada; mantener el resultado fallido.
El inventario técnico y tres mediciones de recursos por ruta amplían la
evidencia, sin aprobar licencias, tarifas ni rendimiento de producción.
