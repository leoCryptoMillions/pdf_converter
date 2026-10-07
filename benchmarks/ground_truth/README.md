# Ground Truth

Un archivo JSON por PDF del corpus, nombrado `<file_id>.json` (el mismo
`file_id` usado en `../corpus_manifest.csv`).

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
