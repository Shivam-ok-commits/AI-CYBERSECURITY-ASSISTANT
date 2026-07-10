param(
  [switch]$NoElectron
)

$Root = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $Root "frontend"
$ElectronDir = Join-Path $Root "electron"
$FrontendUrl = "http://localhost:5173"

Write-Host "=== Sentinel Desktop Development ===" -ForegroundColor Cyan
Write-Host ""

# Start frontend dev server
$frontendJob = Start-Job -ScriptBlock {
  param($dir)
  Set-Location $dir
  npm run dev
} -ArgumentList $FrontendDir

Write-Host "[frontend] Starting Vite dev server..." -ForegroundColor Yellow

$ready = $false
$maxWait = 30
$elapsed = 0
while (-not $ready -and $elapsed -lt $maxWait) {
  Start-Sleep -Seconds 1
  $elapsed++
  try {
    $response = Invoke-WebRequest -Uri $FrontendUrl -Method GET -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) { $ready = $true }
  } catch {}
}

if (-not $ready) {
  Write-Host "[frontend] Failed to start within $maxWait seconds." -ForegroundColor Red
  Stop-Job $frontendJob; Remove-Job $frontendJob; exit 1
}

Write-Host "[frontend] Ready at $FrontendUrl" -ForegroundColor Green

# Build Electron TypeScript
Write-Host "[electron] Building TypeScript..." -ForegroundColor Yellow
Set-Location $ElectronDir
npm run build
if ($LASTEXITCODE -ne 0) {
  Write-Host "[electron] Build failed" -ForegroundColor Red
  Stop-Job $frontendJob; Remove-Job $frontendJob; exit 1
}
Write-Host "[electron] Build complete" -ForegroundColor Green

# Launch Electron (backend starts automatically inside Electron)
if ($NoElectron) {
  Write-Host "[electron] Skipped (--NoElectron)" -ForegroundColor Gray
} else {
  Write-Host "[electron] Launching (backend will start automatically)..." -ForegroundColor Yellow
  $electronJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    npx electron .
  } -ArgumentList $ElectronDir
}

Write-Host ""
Write-Host "=== Sentinel Desktop — All Services ===" -ForegroundColor Green
Write-Host "  Frontend   : $FrontendUrl" -ForegroundColor Cyan
Write-Host "  Backend    : Auto-managed by Electron (127.0.0.1:8000)" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop all" -ForegroundColor Gray

try {
  while ($true) { Start-Sleep -Seconds 1 }
} finally {
  Write-Host "`nShutting down..." -ForegroundColor Yellow
  Get-Job | Stop-Job | Remove-Job
}
