# Corpus de PDFs (no versionado)

Coloca aquí los PDFs autorizados del corpus de prueba, dentro de
`benchmarks/corpus/files/` (la carpeta `files/` está excluida de git en
`.gitignore` — solo este README y la estructura se versionan).

Cada PDF debe:
1. Estar registrado en `../corpus_manifest.csv` con su `file_id`.
2. Tener autorización de uso confirmada (`authorized=yes`).
3. Idealmente, tener su ground truth en `../ground_truth/<file_id>.json`.

Ver `../README.md` para el detalle de categorías y el flujo completo de F0.
