@echo off
setlocal

if /i "%~1"=="backend" goto run_backend
if /i "%~1"=="frontend" goto run_frontend

start "Invertix Backend" cmd /k ""%~f0" backend"
start "Invertix Frontend" cmd /k ""%~f0" frontend"
exit /b 0

:run_backend
cd /d "%~dp0backend"
set "PYTHON_CMD="
if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" -c "import fastapi, sqlalchemy, uvicorn" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=venv\Scripts\python.exe"
)
if not defined PYTHON_CMD (
  py -3 -c "import fastapi, sqlalchemy, uvicorn" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py -3"
)
if not defined PYTHON_CMD (
  python -c "import fastapi, sqlalchemy, uvicorn" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo No se encontro Python con las dependencias del backend. Revisa backend\README.md.
  pause
  exit /b 1
)
call %PYTHON_CMD% -m uvicorn src.app:app --reload --host 127.0.0.1 --port 8000
echo.
echo El backend se detuvo. Revisa los errores de esta ventana.
pause
exit /b

:run_frontend
cd /d "%~dp0frontend"
rem Use the frontend origin so other devices reach the API through Vite's proxy.
set "VITE_API_URL="
set "PORTABLE_NODE=%~dp0.local-node\node-v26.13.1-win-x64"
if exist "%PORTABLE_NODE%\node.exe" set "PATH=%PORTABLE_NODE%;%PATH%"
if exist "node_modules\.bin\vite.cmd" (
  npm run dev
) else (
  echo No se encontraron las dependencias del frontend. Primero ejecuta npm install.
  pause
)
exit /b
