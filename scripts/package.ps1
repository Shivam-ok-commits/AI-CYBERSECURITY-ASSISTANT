<#
.SYNOPSIS
  Sentinel Desktop -- Production Packaging Pipeline
  Always builds from clean state:
  1. Clean all previous builds
  2. Build frontend (React + Vite)
  3. Build Electron TypeScript
  4. Build backend (PyInstaller)
  5. Package with electron-builder (NSIS installer + Portable)
#>

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$FRONTEND_DIR = Join-Path $ROOT "frontend"
$ELECTRON_DIR = Join-Path $ROOT "electron"
$BACKEND_DIST = Join-Path (Join-Path $ROOT "dist") "backend"

Write-Host "+--------------------------------------------+" -ForegroundColor Cyan
Write-Host "|   Sentinel Desktop -- Packaging Pipeline   |" -ForegroundColor Cyan
Write-Host "+--------------------------------------------+" -ForegroundColor Cyan

# -- 0. Clean --
Write-Host "`n[0/5] Cleaning previous builds..." -ForegroundColor Yellow
$cleanDirs = @(
    (Join-Path $FRONTEND_DIR "dist"),
    (Join-Path $ELECTRON_DIR "dist"),
    (Join-Path $ELECTRON_DIR "release"),
    $BACKEND_DIST,
    (Join-Path $ROOT "build")
)
foreach ($dir in $cleanDirs) {
    if (Test-Path $dir) {
        Remove-Item -Recurse -Force $dir
        Write-Host "  Removed: $dir" -ForegroundColor Gray
    }
}
Remove-Item -Force (Join-Path $ROOT "*.spec") -ErrorAction SilentlyContinue
Write-Host "  Clean complete" -ForegroundColor Green

# -- 1. Frontend Build --
Write-Host "`n[1/5] Building frontend..." -ForegroundColor Yellow
Push-Location $FRONTEND_DIR
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
    Write-Host "  Frontend built: frontend/dist/" -ForegroundColor Green
} finally {
    Pop-Location
}

# -- 2. Electron TypeScript Build --
Write-Host "`n[2/5] Compiling Electron..." -ForegroundColor Yellow
Push-Location $ELECTRON_DIR
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Electron build failed" }
    Write-Host "  Electron compiled: electron/dist/" -ForegroundColor Green
} finally {
    Pop-Location
}

# -- 3. Backend PyInstaller Build --
Write-Host "`n[3/5] Building backend executable..." -ForegroundColor Yellow
Push-Location $ROOT
try {
    # Ensure PyInstaller is available
    & "$ROOT\.venv\Scripts\python.exe" -m pip install pyinstaller --quiet
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller install failed" }

    & "$ROOT\.venv\Scripts\python.exe" -m PyInstaller `
        --onefile `
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
        (Join-Path (Join-Path $ROOT "src") "packaged.py")
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

    Write-Host "  Backend executable created: $BACKEND_DIST" -ForegroundColor Green
} finally {
    Pop-Location
}

# -- 4. electron-builder --
Write-Host "`n[4/5] Packaging Electron app..." -ForegroundColor Yellow
Push-Location $ELECTRON_DIR
try {
    # Install dependencies if needed
    if (-not (Test-Path "node_modules")) {
        npm install
    }

    npx electron-builder --win
    if ($LASTEXITCODE -ne 0) { throw "electron-builder failed" }

    Write-Host "`n  === Package Complete ===" -ForegroundColor Green
    Write-Host "  Output: electron/release/" -ForegroundColor Cyan

    $releaseDir = Join-Path $ELECTRON_DIR "release"
    if (Test-Path $releaseDir) {
        Get-ChildItem $releaseDir -Recurse -File | ForEach-Object {
            $name = $_.Name
            $sizeMB = [math]::Round($_.Length / 1048576, 2)
            $msg = "    " + $name + " (" + $sizeMB + " MB)"
            Write-Host $msg -ForegroundColor White
        }
    }
} finally {
    Pop-Location
}

# -- 5. Cleanup build artifacts --
Write-Host "`n[5/5] Cleaning up temporary artifacts..." -ForegroundColor Yellow
if (Test-Path (Join-Path $ROOT "build")) {
    Remove-Item -Recurse -Force (Join-Path $ROOT "build")
}
if (Test-Path (Join-Path $ROOT "*.spec")) {
    Remove-Item -Force (Join-Path $ROOT "*.spec")
}
Write-Host "  Done!" -ForegroundColor Green

Write-Host "`n+--------------------------------------------+" -ForegroundColor Cyan
Write-Host "|        Packaging Complete!                 |" -ForegroundColor Cyan
Write-Host "+--------------------------------------------+" -ForegroundColor Cyan
