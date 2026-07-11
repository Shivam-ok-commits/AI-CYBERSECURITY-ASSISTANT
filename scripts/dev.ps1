<#
.SYNOPSIS
  Sentinel Desktop — Development Mode (one command)
  Starts all three services with hot reload:
  - FastAPI (uvicorn --reload)    → backend terminal window
  - React (Vite HMR)              → frontend terminal window
  - Electron (auto-restart)       → app window
#>

param(
  [switch]$NoBackend,
  [switch]$NoElectron
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ElectronDir = Join-Path $Root "electron"
$FrontendDir = Join-Path $Root "frontend"
$Python = Join-Path (Join-Path (Join-Path $Root ".venv") "Scripts") "python.exe"
$TscWatch = Join-Path (Join-Path (Join-Path $ElectronDir "node_modules") ".bin") "tsc.cmd"
$ElectronExe = Join-Path (Join-Path (Join-Path $ElectronDir "node_modules") ".bin") "electron.cmd"
$BackendUrl = "http://127.0.0.1:8000/api/v1/health"
$ViteUrl = "http://localhost:5173"

# Colors
$C = "Cyan"; $G = "Green"; $Y = "Yellow"; $R = "Red"; $Gr = "Gray"

# PIDs we own (for cleanup)
$OwnedPids = @()

function Log($color, $msg) { Write-Host $msg -ForegroundColor $color }

function Ensure-Stale {
  Log $Y "[setup] Checking for stale services..."
  $stale = $false
  try { $r = Invoke-WebRequest -Uri $BackendUrl -UseBasicParsing -TimeoutSec 1; $stale = $true } catch {}
  if (-not $stale) { try { $r = Invoke-WebRequest -Uri $ViteUrl -UseBasicParsing -TimeoutSec 1; $stale = $true } catch {} }
  if ($stale) {
    Log $Y "[setup] Stale services detected, cleaning..."
    Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
      $_.CommandLine -match "uvicorn" 2>$null
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
      ($_.CommandLine -match "vite" -or $_.CommandLine -match "tsc") 2>$null
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "electron" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
  }
  Log $G "[setup] Clean"
}

function Wait-For($label, $url, $timeoutSec = 30) {
  Log $Y "[$label] Waiting for $url ..." -NoNewline
  for ($i = 0; $i -lt $timeoutSec; $i++) {
    try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { Log $G " Ready!"; return $true } } catch {}
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 1
  }
  Log $R " FAILED (timeout)"
  return $false
}

function Cleanup {
  Log $Y "`n[shutdown] Stopping services..."
  foreach ($pid in $OwnedPids) {
    try { taskkill /PID $pid /T /F 2>$null } catch {}
  }
  Get-Process -Name "electron" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Log $G "[shutdown] Done"
}

# ── Main ──

Log $C "══════════════════════════════════════════"
Log $C "    Sentinel Desktop — Development Mode"
Log $C "══════════════════════════════════════════"
Log $Gr ""

Ensure-Stale

# ── 1. Backend ──
if (-not $NoBackend) {
  Log $Y "[backend] Starting FastAPI..."
  $backendTitle = "Sentinel Backend — uvicorn --reload"
  $backendArgs = "-NoProfile -WindowStyle Normal -Title `"$backendTitle`" -Command `"& { Set-Location '$Root'; & '$Python' -m uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload --log-level info }`""
  $backendProc = Start-Process powershell -ArgumentList $backendArgs -PassThru
  $OwnedPids += $backendProc.Id
  Wait-For "backend" $BackendUrl
} else {
  Log $Gr "[backend] Skipped"
}

# ── 2. Frontend ──
Log $Y "[frontend] Starting Vite dev server..."
$frontendTitle = "Sentinel Frontend — Vite HMR"
$frontendArgs = "-NoProfile -WindowStyle Normal -Title `"$frontendTitle`" -Command `"& { Set-Location '$FrontendDir'; npm run dev }`""
$frontendProc = Start-Process powershell -ArgumentList $frontendArgs -PassThru
$OwnedPids += $frontendProc.Id
Wait-For "frontend" $ViteUrl

# ── 3. Electron ──
if (-not $NoElectron) {
  Log $Y "[electron] Compiling TypeScript..."
  Push-Location $ElectronDir
  & $TscWatch --preserveWatchOutput 2>&1 | Out-Null
  Pop-Location
  Log $G "[electron] Compiled"

  Log $Y "[electron] Launching..."
  $electronTitle = "Sentinel Desktop"
  $electronArgs = "-NoProfile -WindowStyle Normal -Title `"$electronTitle`" -Command `"& { Set-Location '$ElectronDir'; & '$ElectronExe' . }`""
  $electronProc = Start-Process powershell -ArgumentList $electronArgs -PassThru
  Log $G "[electron] PID: $($electronProc.Id)"

  # Watch electron/src/*.ts for changes → recompile + restart
  $watcher = New-Object System.IO.FileSystemWatcher
  $watcher.Path = Join-Path $ElectronDir "src"
  $watcher.Filter = "*.ts"
  $watcher.IncludeSubdirectories = $true
  $watcher.EnableRaisingEvents = $true
  $changeAction = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    Log $Y "[electron] Change detected: $name"
    try { taskkill /PID $electronProc.Id /T /F 2>$null } catch {}
    Start-Sleep -Seconds 1
    Push-Location $ElectronDir
    & $TscWatch 2>&1 | Out-Null
    Pop-Location
    Log $G "[electron] Recompiled, relaunching..."
    $electronProc = Start-Process powershell -ArgumentList $electronArgs -PassThru
    Log $G "[electron] PID: $($electronProc.Id)"
  }
  Register-ObjectEvent $watcher "Changed" -Action $changeAction | Out-Null
  Register-ObjectEvent $watcher "Created" -Action $changeAction | Out-Null
  Log $G "[electron] Watching electron/src/*.ts for changes"

} else {
  Log $Gr "[electron] Skipped"
}

# ── Status ──
Log $C ""
Log $C "══════════════════════════════════════════"
Log $C "  All Services Running"
Log $C "  Backend  : $BackendUrl"
Log $C "  Frontend : $ViteUrl"
Log $C "  API Docs : http://127.0.0.1:8000/docs"
Log $C ""
Log $C "  Hot Reload:"
Log $C "    Python  → uvicorn --reload (save .py)"
Log $C "    React   → Vite HMR (save .tsx/.ts)"
Log $C "    Electron→ FileSystemWatcher (save electron/src/*.ts)"
Log $C ""
Log $C "  Press Ctrl+C to stop all"
Log $C "══════════════════════════════════════════"

try { while ($true) { Start-Sleep -Seconds 1 } } finally { Cleanup }
