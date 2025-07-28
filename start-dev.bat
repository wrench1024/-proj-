@echo off
echo Starting RegDoc Development Environment...
echo.

echo [1/2] Starting Backend Server...
start cmd /k "cd /d backend && python main.py"

echo [2/2] Starting Frontend Development Server...
timeout /t 3 >nul
start cmd /k "cd /d frontend && npm run dev"

echo.
echo Both servers are starting...
echo Backend: http://10.21.22.107:8443
echo Frontend: http://localhost:5173
echo.
pause
