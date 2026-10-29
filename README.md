# PDF Converter

MVP local para convertir PDFs digitales a **Word y Excel**, con TXT opcional,
advertencias y descarga desde el navegador. Un usuario y un documento a la vez.

**Estado al 2026-10-28 (0.6.4):** flujo local verificado; piloto de cinco documentos
preparado para revisión humana. La plataforma con cuentas, trabajos y
almacenamiento distribuido corresponde a una entrega posterior.

## Arranque local en Windows

Se ha comprobado con Python 3.13. Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-mvp.txt
.\.venv\Scripts\python.exe -m apps.local_review_ui
```

Abrir [http://127.0.0.1:8420/](http://127.0.0.1:8420/). En el entorno ya
preparado también sirve `python -m apps.local_review_ui`.

1. Cargar un PDF con texto seleccionable (hasta 25 MB y 100 páginas).
2. Elegir Word, Excel o ambos; seleccionar páginas si hace falta.
3. Convertir, revisar las advertencias y descargar los archivos.
4. Abrirlos y comparar contenido, cifras y distribución con el original.

Los archivos quedan en `.generated/web_ui/`, con limpieza automática tras
24 horas de inactividad por defecto (`RETENTION_HOURS` permite ajustarlo).
Los resultados requieren revisión. Word aproxima el diseño; Excel conserva
las celdas como texto de forma predeterminada para proteger identificadores y
ceros iniciales. Excel abre en `Pagina_1`, con una vista editable por página;
`Table_N` conserva los datos y `Texto completo` el texto de todas las páginas.

La app se utiliza en la propia máquina, vinculada a `127.0.0.1`. El MVP digital
no necesita Docker, React, PostgreSQL, RabbitMQ, Tesseract ni Poppler. OCR
existente sigue disponible con sus dependencias opcionales, fuera de la
aceptación de este piloto.

## Desarrollo y pruebas reducidas

Instalar las herramientas de desarrollo en el mismo entorno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-mvp-dev.txt
```

Los siguientes comandos usan el Python de ese entorno (puede reemplazarse
`python` por `.\.venv\Scripts\python.exe`):

```powershell
# Desarrollo: selección crítica por riesgo (objetivo aproximado del 50%)
python -m pytest -q

# Módulo modificado: incluir todos sus casos
python -m pytest tests/unit/test_docx_layout.py -q -m "mvp or not mvp"

# Cierre de entrega: regresión completa
python -m pytest -q -m "mvp or not mvp"
```

Se conservan todas las pruebas. La selección crítica protege conversión,
integridad, límites y descargas; las pruebas de ayuda, temas, benchmark y OCR
ampliado quedan para el cierre o cambios en esos módulos. Los documentos de
las pruebas HTTP se generan con datos ficticios; no requieren el corpus privado.
La cobertura es explícita y requiere `pytest-cov`; `make test-coverage`
conserva el umbral anterior del 70%.

## Piloto de cinco documentos

Con las herramientas de desarrollo y los documentos autorizados ya disponibles:

```powershell
python -m benchmarks.pilot_local --output .generated/mvp-pilot/run-01
```

Elegir siempre una carpeta nueva. Se verifica el flujo HTTP de carga,
conversión y descarga con cinco PDFs digitales completos, nueve páginas,
sin OCR. Cada carpeta incluye original, Word, Excel, TXT y JSON de procedencia.
`report.json` registra comprobaciones y `revision.csv` deja pendiente la
aceptación de cada documento. `--ids` permite seleccionar otros IDs digitales
autorizados del manifest; los PDFs privados no se incluyen en Git.

La comparación de caracteres no verifica orden de lectura, significado ni
apariencia. La persona revisora compara texto, cifras, estructura y diseño,
edita, guarda y reabre los archivos, y registra su decisión en el CSV.
Los resultados técnicos no aprueban automáticamente el Gate F0.

Para comprobar con Microsoft Word y Excel instalados y generar el comparativo
visual privado, después de preparar el paquete:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File benchmarks/render_pilot.ps1 -Batch .generated/mvp-pilot/run-01/office-batch.json
python -m benchmarks.review_pilot --output .generated/mvp-pilot/run-01
```

Abrir `review.html` en esa carpeta: muestra el original junto a sus renders de
Word y Excel, con descargas y copias editadas. Las aplicaciones de Office se
ejecutan ocultas y solo escriben copias de comprobación; `revision.csv`
conserva las decisiones humanas pendientes. Excel incluye las páginas en blanco.

## Uso por consola

```powershell
python -m apps.convert documento.pdf --output .generated/demo --formats docx xlsx txt
```

La carpeta de salida debe ser nueva. La guía de [prototipo F0](docs/PROTOTIPO_F0.md)
describe selección de páginas, tipos numéricos explícitos y OCR opcional.
`requirements-prototype.txt` amplía las dependencias locales con herramientas
de benchmark y OCR.

## Alcance y continuación

Se priorizan los bloqueos del recorrido cargar → convertir → revisar →
descargar → editar. Se posponen cuentas, organizaciones, cuotas, procesamiento
distribuido, formatos nuevos y mejoras de OCR. Se congelan cambios cosméticos,
ayuda, mascota y tablero salvo fallos que bloqueen el uso.

- [Alcance activo y criterios de cierre](docs/ALCANCE.md)
- [Avance y evidencia](docs/AVANCE.md)
- [Validación Word previa en tres diseños](docs/VALIDACION_WORD_F0.md)
- [Plan ampliado de la plataforma](PLAN_APP_CONVERSION_PDF_v1.0.md)
- [Arquitectura](docs/ARQUITECTURA.md), [seguridad](docs/SEGURIDAD.md) y [licencias](docs/LICENCIAS.md)

La API en `apps/api`, las tareas en `apps/worker` y Docker Compose forman parte
del trabajo futuro de plataforma; el arranque del MVP usa `apps.local_review_ui`.
