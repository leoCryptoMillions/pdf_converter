param([switch]$Install, [switch]$Check)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$appPython = Join-Path $projectRoot '.venv\Scripts\python.exe'

try {
    if (-not (Test-Path -LiteralPath $appPython)) {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            & py -3.13 -m venv .venv
        } else {
            & python -m venv .venv
        }
        if ($LASTEXITCODE -ne 0) { throw 'Instala Python 3.13 antes de continuar.' }
        $Install = $true
    }
    & $appPython -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)"
    if ($LASTEXITCODE -ne 0) { throw 'Este paquete necesita Python 3.13 o posterior.' }
    if ($Install) {
        & $appPython -m pip install --require-hashes -r requirements-mvp.lock
        if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias. Revisa la conexion y el espacio disponible.' }
    }
    & $appPython -c "from apps.local_review_ui import APP_VERSION; print('PDF Converter ' + APP_VERSION + ': instalacion y configuracion verificadas')"
    if ($LASTEXITCODE -ne 0) { throw 'Revisa el error de configuracion anterior. Para instalar dependencias ejecuta iniciar.cmd -Install.' }
    if ($Check) { exit 0 }
    Write-Host 'Abre la direccion que aparecera a continuacion. Para terminar, pulsa Ctrl+C.'
    & $appPython -m apps.local_review_ui
    exit $LASTEXITCODE
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
