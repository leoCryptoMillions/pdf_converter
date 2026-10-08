# Licencias y dependencias: evidencia F0

Actualizado: 2026-10-08. Estado: inventario técnico generado; revisión de distribución y cumplimiento pendiente. Este documento reemplaza las afirmaciones anteriores de cumplimiento completo, que no estaban verificadas.

## Entorno observado

`python -m benchmarks.dependency_inventory` recorre los requisitos declarados de las dependencias instaladas para el prototipo y el benchmark, evaluando los marcadores de la plataforma actual sin extras opcionales. Encontró **33 componentes**, copió **61 archivos de licencias/avisos** con SHA256 y no detectó incumplimientos de versiones en ese conjunto instalado.

La evidencia permanece local en `.generated/licenses/inventory.json` y `.generated/licenses/notices/`. Es un inventario JSON propio, no un SBOM CycloneDX validado ni una auditoría de vulnerabilidades. Los metadatos de licencia y las copias de avisos requieren revisión del artefacto a distribuir.

| Dependencia raíz instalada | Versión | Licencia declarada en el paquete |
| --- | --- | --- |
| pdfplumber | 0.11.10 | MIT |
| pydantic | 2.13.5 | MIT |
| openpyxl | 3.1.5 | MIT |
| python-docx | 1.2.0 | MIT |
| reportlab | 5.0.1 | BSD |
| pypdfium2 | 5.14.0 | BSD-3-Clause, Apache-2.0 y licencias de dependencias |
| pytesseract | 0.3.13 | Apache-2.0 |
| camelot-py | 2.0.0 | MIT |
| psutil | 7.0.0 | BSD |

Los textos oficiales de [pdfplumber 0.11.10](https://github.com/jsvine/pdfplumber/blob/v0.11.10/LICENSE.txt) y [python-docx 1.2.0](https://github.com/python-openxml/python-docx/blob/v1.2.0/LICENSE) confirman MIT. [pypdfium2](https://github.com/pypdfium2-team/pypdfium2/blob/main/README.md#licensing) documenta las licencias del wrapper, PDFium y componentes incluidos; los avisos del binario concreto deben acompañar su redistribución. No asignar una licencia única al conjunto por la licencia del wrapper.

## Pendientes que el inventario no resuelve

- Registrar procedencia, hashes y avisos del ejecutable nativo Tesseract y sus dependencias; las mediciones usan Tesseract 5.4.0 en Windows.
- Registrar origen y condiciones de los modelos `spa`, `eng` y `osd` de `.tessdata/`. [Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html) se publica bajo Apache-2.0; esto no sustituye revisar los artefactos instalados.
- Revisar binarios incluidos en wheels, avisos de terceros y el paquete final antes de distribuirlo. Los archivos copiados son evidencia de entrada.
- Resolver y comprobar el stack propuesto en `requirements.txt` y `pyproject.toml` en un entorno limpio. Sus versiones antiguas no representan este entorno; el pin `openpyxl==3.11.0` debe reconciliarse con 3.1.5 probado.
- Inventariar por separado cualquier ruta que use Poppler, OCRmyPDF o Ghostscript. La nueva ruta OCR de comparación usa PDFium y Tesseract; el script OCR general conserva otras rutas experimentales.
- Revisar servicios de infraestructura, extras y futuras dependencias de F1, que están fuera del cierre instalado del prototipo.

No inferir que una dependencia GPL/AGPL/LGPL carece de obligaciones porque no se modifica, se instala con un gestor o se utiliza como servicio. Las obligaciones dependen del componente concreto y de cómo se integra y entrega. No se ha aprobado todavía la distribución comercial ni el Gate F0.

## Reproducción

Instalar el subconjunto de `requirements-prototype.txt` y los componentes opcionales necesarios para el benchmark. Luego ejecutar:

```powershell
python -m benchmarks.dependency_inventory
```

El inventario registra las versiones efectivamente instaladas y los requisitos activos. Regenerarlo cuando cambien paquetes, plataforma, extras o binarios.
