<#
.SYNOPSIS
  Build the Sentinel backend into a standalone executable using PyInstaller.
  Output: dist/backend/sentinel-backend.exe
#>

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$BACKEND_DIST = Join-Path (Join-Path $ROOT "dist") "backend"

Write-Host "Building backend executable..." -ForegroundColor Yellow

# Clean previous build
if (Test-Path $BACKEND_DIST) {
    Remove-Item -Recurse -Force $BACKEND_DIST
}

if (Test-Path (Join-Path $ROOT "build")) {
    Remove-Item -Recurse -Force (Join-Path $ROOT "build")
}

# Ensure PyInstaller
& "$ROOT\.venv\Scripts\python.exe" -m pip install pyinstaller --quiet
if ($LASTEXITCODE -ne 0) { throw "PyInstaller install failed" }

& "$ROOT\.venv\Scripts\python.exe" -m PyInstaller `
    --onefile `
    --noconsole `
    --name "sentinel-backend" `
    --distpath $BACKEND_DIST `
    --workpath (Join-Path (Join-Path $ROOT "build") "pyinstaller") `
    --specpath $ROOT `
    --add-data "src;src" `
    --hidden-import "uvicorn.logging" `
    --hidden-import "uvicorn.loops.auto" `
    --hidden-import "uvicorn.protocols.http.auto" `
    --hidden-import "uvicorn.protocols.websockets.auto" `
    --hidden-import "httpx" `
    --hidden-import "openai" `
    --hidden-import "jose" `
    --hidden-import "cryptography" `
    --hidden-import "bcrypt" `
    --hidden-import "authlib" `
    --hidden-import "ldap3" `
    --hidden-import "dotenv" `
    --hidden-import "starlette" `
    --hidden-import "multipart" `
    --hidden-import "tqdm" `
    (Join-Path $ROOT "src" "packaged.py")

if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

# Cleanup
Remove-Item -Recurse -Force (Join-Path $ROOT "build") -ErrorAction SilentlyContinue
Remove-Item -Force (Join-Path $ROOT "*.spec") -ErrorAction SilentlyContinue

Write-Host "Backend executable created at: $BACKEND_DIST" -ForegroundColor Green
