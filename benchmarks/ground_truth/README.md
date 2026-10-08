# Ground Truth

Un archivo JSON por PDF del corpus, nombrado `<file_id>.json` (el mismo
`file_id` usado en `../corpus_manifest.csv`).

Las transcripciones de documentos reales se guardan en `local/`, excluido
de Git. El cargador busca primero allí y verifica `source_sha256` cuando
está presente. No copiar datos reales a archivos versionados.

Cada referencia nueva registra `review_status: "verified"`, `review_method`,
`source_sha256` y `scope`: `tables_only`, `full_text`, `text_region`,
`selected_pages_tables` o `selected_pages_text`.
`reference_revision` distingue correcciones y ampliaciones posteriores.
Los borradores (`review_status: "draft"`) no se puntúan. `has_ground_truth=yes`
significa que existe una anotación revisada; su cobertura puede ser parcial.
La referencia sintética anterior tiene cobertura de tablas, no texto completo.

Una referencia `text_region` usa `pages[].text_regions[]` con `bbox_relative`
en coordenadas relativas 0–1 desde la esquina superior izquierda y `text`.
Solo `validate_prototype` puntúa estas regiones. Nunca usarlas para aprobar
el criterio OCR de página completa.

Para `selected_pages_*`, incluir exclusivamente las páginas anotadas con
sus números originales. La extracción/exportación se limita a esas páginas.
El resultado registra su alcance; no afirmar cobertura del PDF completo.
Ampliar las referencias mediante `prepare_review`, que conserva tareas
pendientes para documentos anotados parcialmente.

## Plantilla

```json
{
  "file_id": "example_001",
  "pages": [
    {
      "page_number": 1,
      "text": "Texto completo esperado de la página, en orden de lectura...",
      "tables": [
        {
          "bbox": [72.0, 100.0, 540.0, 300.0],
          "rows": [
            ["Encabezado 1", "Encabezado 2", "Encabezado 3"],
            ["Valor 1", "Valor 2", "Valor 3"]
          ],
          "critical_cells": [
            {"row": 1, "col": 1, "value": "Valor 2", "reason": "monto o identificador que no debe alterarse"}
          ]
        }
      ]
    }
  ]
}
```

Reglas:
- `text` debe ser el texto de referencia para calcular CER/exactitud de OCR
  o de extracción digital.
- `tables[].rows` es la tabla "verdadera" tal como debería quedar en el
  XLSX exportado — se usa para calcular F1 de detección y de estructura
  de celdas.
- `critical_cells` marca valores que nunca deben cambiar silenciosamente
  (RFC, CLABE, montos, fechas) — ver `docs/ALCANCE.md`.
- No es necesario anotar las 60 PDFs con el mismo nivel de detalle: como
  mínimo, anota texto completo + tablas para los PDFs que definan el
  Gate F0 (categorías `digital_simple_table`, `digital_complex_table`,
  `scanned_clean`).
