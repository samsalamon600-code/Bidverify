@echo off
title Bidverify Enterprise Procurement Verification Platform
echo ======================================================================
echo    BIDVERIFY: AI-Powered Vendor Compliance & Risk Verification
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/3] Validating Python and Running Database Initialization...
python -c "from backend.app.seed_data import seed_database; seed_database(); print('Database initialized and verified.')"
if %errorlevel% neq 0 (
    echo [ERROR] Python environment failed. Ensure dependencies from backend\requirements.txt are installed.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Starting FastAPI Backend Engine on http://127.0.0.1:8000 ...
start "Bidverify Backend (FastAPI)" cmd /k "cd /d ""%~dp0"" && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo.
echo [3/3] Starting Next.js Frontend on http://localhost:3000 ...
start "Bidverify Frontend (Next.js)" cmd /k "cd /d ""%~dp0frontend"" && npm.cmd run dev"

timeout /t 5 /nobreak >nul

echo.
echo ======================================================================
echo Platform is LIVE!
echo Frontend: http://localhost:3000
echo Backend:  http://127.0.0.1:8000
echo Docs:     http://127.0.0.1:8000/docs
echo.
echo Demo Credentials:
echo   - Procurement Officer: officer@bidverify.com / officer123
echo   - System Admin:        admin@bidverify.com / admin123
echo ======================================================================

start http://localhost:3000

echo.
echo Press any key to stop all Bidverify services...
pause >nul

echo Stopping services...
taskkill /FI "WINDOWTITLE eq Bidverify Backend (FastAPI)*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Bidverify Frontend (Next.js)*" /T /F >nul 2>&1
echo Services terminated.
