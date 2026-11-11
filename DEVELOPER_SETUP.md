# Preparación del desarrollo del MVP

Actualizado: 2026-11-10 · Versión 0.7.0 · Python 3.13.

El producto activo es `apps.local_review_ui`, para un usuario y PDF digital.
Los esqueletos de `apps/api` y `apps/worker` pertenecen a la plataforma futura;
PostgreSQL, Redis, RabbitMQ y Docker no son requisitos del MVP.

Desde la raíz, en Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-mvp-dev.lock
.\.venv\Scripts\python.exe -m apps.local_review_ui
```

La única entrega requerida es la versión web ejecutada en Windows y utilizada
desde el navegador. El desarrollo y el cierre se verifican en Windows; Linux
queda fuera del alcance y no constituye una validación pendiente.

Abrir http://127.0.0.1:8420/. Para uso sin herramientas de desarrollo,
`iniciar.cmd` crea el entorno e instala únicamente el runtime. `iniciar.cmd
-Check` verifica importación/configuración; `-Install` reinstala desde el lock.

La configuración se toma del entorno del proceso. No se carga `.env`
automáticamente. Ver [CONFIG_GUIDE.md](CONFIG_GUIDE.md).

## Verificación

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q -m "mvp or not mvp"
npm ci
npx playwright install chromium
.\.venv\Scripts\python.exe -m scripts.check_release --audit
```

El último comando añade cobertura de ramas (umbral 70%), `pip check`, inventario
de avisos, wheel, instalación vacía fuera del árbol fuente, conversión HTTP/CLI,
edición y reapertura de archivos Office, Chromium, auditoría y SBOM. `--skip-browser`
registra una comprobación parcial. Las pruebas generan PDFs ficticios; no
requieren los documentos privados del corpus. OCR real es opcional y se omite
si no están sus dependencias. La instalación de Chromium y la auditoría requieren
red. La edición de Office automatizada aquí usa python-docx/openpyxl; la revisión
visual con Microsoft Office del piloto aceptado conserva su evidencia histórica.

`requirements-mvp.txt` y `requirements-mvp-dev.txt` declaran dependencias directas.
Los `.lock` fijan transitivas y hashes. Tras modificar una dependencia, regenerar
ambos locks con pip-tools, con el runtime como restricción del lock de desarrollo,
revisar el diff y ejecutar el cierre completo. Los manifiestos históricos están
rotulados en `infra/requirements-platform-*-legacy.txt`.

El workflow `.github/workflows/tests.yml` sigue siendo manual. No se activan
Actions ni se despliega ningún servicio al ejecutar los checks locales.
