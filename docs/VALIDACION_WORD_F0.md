# Validación técnica de Word en tres diseños

Fecha de cierre de la corrida: 2026-10-27. Inicio: 2026-10-26.
Estado: revisión de ingeniería completada; adjudicación humana y Gate F0 pendientes.

## Alcance y resultados

Se procesaron completos tres PDFs con `authorized=yes` en el manifest,
usando texto digital, sin OCR ni anexo de advertencias. Se abrieron en
Microsoft Word 16.0 de Windows, se renderizaron y se compararon las siete
páginas. Los ejemplos editados se guardaron y reabrieron en Word.

| ID del corpus | Diseño revisado | Páginas PDF / Word | Caracteres no blancos | Diferencias de caracteres observadas | Edición y reapertura |
| --- | --- | --- | --- | --- | --- |
| cep_001 | Comprobante con campos, logotipo y fondos | 1 / 1 | 2,647 | 0 faltantes / 0 adicionales | Texto: pasa. Campos complejos como texto posicionado, con advertencia. |
| carta_privacidad_001 | Carta legal de dos páginas, columna lateral e imágenes | 2 / 2 | 2,432 | 0 faltantes / 0 adicionales | Texto: pasa. Imágenes y disposición revisadas localmente. |
| doc_texto_002 | Informe con portada, página vacía y tablas de varias columnas | 4 / 4 | 2,341 | 0 faltantes / 0 adicionales | Texto y celda de tabla de tres columnas: pasan. |

Los mismos multiconjuntos de caracteres coinciden contra dos extracciones
de origen —pdfplumber y PDFium— y contra el PDF renderizado por Word.
Las siete páginas mantienen sus dimensiones dentro de 0.2 puntos, margen
que cubre el redondeo de Word a twips. Se conservaron logotipos, una imagen
de firma y los fondos gráficos observados; esto no valida firmas digitales.

**Límite de la medición:** contar caracteres sin blancos no verifica
espacios, orden de lectura ni exactitud semántica. La coincidencia entre
extractores tampoco equivale a una referencia humana independiente.
No se calculó un nuevo CER contra ground truth adjudicado ni un F1 de
estructura Word. No se promovió ninguna referencia automática a `verified`.

## Fallos encontrados y correcciones

1. Los rectángulos de relleno de un informe se interpretaban como bordes:
   una tabla visible de cinco filas y tres columnas se convertía en una
   cuadrícula de trece filas y nueve columnas. Se excluyen rellenos grandes
   de la detección de diseño cuando una cuadrícula de bordes alternativa
   conserva la multiplicidad de caracteres y coincide con la misma región.
   Se registra `TABLE_DECORATION_FILTERED`. La extracción solo texto/tablas
   (`preserve_layout=False`) mantiene su estrategia anterior.
2. Los párrafos vacíos de filas de relleno heredaban una altura de letra
   de 10 puntos; las filas crecían y alcanzaban el contenido siguiente.
   Se usa una altura mínima pequeña en los párrafos vacíos.
3. Los márgenes de celda heredados de Word y los márgenes superiores
   distintos entre celdas desplazaban el texto. Se fijan márgenes globales
   explícitos y se usan sangrías/espaciado por párrafo. El interlineado se
   aproxima a partir de líneas de origen y se ignora el tamaño de fuente
   de blancos al estimar la altura del contenido visible.
4. Las líneas de página podían atravesar dos celdas y perder los estilos
   de una de ellas. La tipografía de cada celda se extrae en su propia región.
5. Una página estructuralmente vacía generaba `OCR_REQUIRED`. Ahora se
   conserva y se informa como `EMPTY_PAGE`, sin ejecutar OCR innecesario.

En la página que contiene la tabla principal del informe, el desplazamiento
mediano pasó de **8.872 puntos (147 palabras únicas coincidentes)** a
**0.426 puntos (150 palabras)**. Los subconjuntos coincidentes pueden variar
entre corridas. Es un diagnóstico geométrico, no una calificación de calidad.
Siguen existiendo diferencias de posición, interlineado y ajuste de texto;
el percentil 95 de este diagnóstico no es cero y no se utiliza como gate.

La revisión visual fue realizada por el agente Codex, con ambos renderizados
locales. La corrida inicial tenía solapamientos; tras las correcciones,
la revisión de las tablas no reproduce esos solapamientos. Esto no sustituye
la adjudicación humana ni demuestra soporte general para otras plantillas.

## Evidencia reproducible

- Automatización: `benchmarks/validate_word.py` y `benchmarks/render_word.ps1`.
- Artefactos privados: `.generated/word-validation-20261026/final/`.
- Comparativo navegable: `review.html`, con PDF/Word por página y descargas.
- Métricas: `report.json`; incluye hashes de los originales y del código,
  versiones de motores, dimensiones, diferencias y pruebas de edición.
- Revisión del agente: `review-notes.json`; adjudicación humana: `pending`.
- Las corridas `baseline` y `revision1` a `revision4` conservan los pasos
  intermedios; no se sobrescribió la evidencia inicial.

```powershell
python -m benchmarks.validate_word prepare --output .generated/word-validation/run-01
powershell -NoProfile -ExecutionPolicy Bypass -File benchmarks/render_word.ps1 -Batch .generated/word-validation/run-01/batch.json
python -m benchmarks.validate_word compare --output .generated/word-validation/run-01
```

Usar un directorio nuevo por corrida. El renderizador requiere Microsoft
Word instalado en Windows; crea una instancia oculta y opera solo sobre
DOCX generados dentro de `.generated/`. No convierte ni modifica los PDF
originales. Las imágenes, textos, firmas y documentos reales quedan fuera
de Git. Este informe contiene únicamente IDs del corpus y resultados.

Verificación automatizada: **86 pruebas unitarias/HTTP pasan**, incluidas
regresiones de Word, Excel, TXT, CLI y OCR. Se conservan dos avisos de
configuración de pytest preexistentes. Los tests nuevos usan documentos
sintéticos para fondos pintados, filas pequeñas, páginas vacías y conteo
sin duplicación de celdas combinadas.

Chromium pasa los recorridos de la app y del tablero de brechas. Se
verificaron además las 14 imágenes y los enlaces a los Word del comparativo
local, sin incorporar esos archivos al repositorio.

## Decisión y continuación

Los tres diseños son candidatos comprobados para uso local con revisión.
El comprobante utiliza campos posicionados; el informe conserva tablas
editables y una portada parcialmente representada mediante tabla. La
edición en flujo continuo, las fuentes disponibles y otros visores siguen
siendo limitaciones. No se evaluaron aquí contratos largos, OCR con
geometría, documentos reservados nuevos ni una muestra estadística amplia.

**F0-04 mantiene `partial/pending/pending`.** Sigue pendiente que una persona
adjudique texto, estructura y apariencia de las referencias y que se midan
los criterios acordados sobre una muestra representativa/reservada.
El corpus no creció ni se marcaron referencias nuevas como verificadas.
F0-01/F0-02 y licencias/costo siguen pendientes para F0-11. Esta corrida
no decide Go/No-Go ni acredita F1. Indicadores del tablero sin cambios:
verificación 18% (2/11), decisiones 27% (3/11).
