# ==============================================================================
# BIDVERIFY - Windows PowerShell Master Launcher
# ==============================================================================

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   BIDVERIFY: AI-Powered Vendor Compliance & Risk Verification" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 1. Initialize and Seed Database
Write-Host "`n[1/3] Initializing Database & Verifying ML Benchmark Pipelines..." -ForegroundColor Yellow
python -c "from backend.app.seed_data import seed_database; seed_database(); print('Database verified.')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python execution failed. Check pip requirements." -ForegroundColor Red
    exit 1
}

# 2. Start FastAPI Backend in background process
Write-Host "`n[2/3] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000" -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 3

# 3. Start Next.js Frontend
Write-Host "`n[3/3] Launching Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Yellow
Set-Location "$ScriptDir\frontend"
$frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 4

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "   BIDVERIFY IS LIVE AND READY!" -ForegroundColor Green
Write-Host "   - Frontend UI:   http://localhost:3000" -ForegroundColor White
Write-Host "   - Backend API:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   - API Swagger:   http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "   - Demo User:     officer@bidverify.com / officer123" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Green

# Open browser
Start-Process "http://localhost:3000"

Write-Host "`nPress ENTER in this window to cleanly terminate all Bidverify processes..." -ForegroundColor Gray
Read-Host

Write-Host "Shutting down Bidverify processes..." -ForegroundColor Yellow
Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
Get-Process -Name "uvicorn", "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "Shutdown complete." -ForegroundColor Green
