@echo off
REM Start the FastAPI backend (foreground)
setlocal

set ROOT=%~dp0..
cd /d "%ROOT%"

if exist "backend\.venv\Scripts\activate.bat" (
    call backend\.venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

set MODE=%1
if "%MODE%"=="prod" (
    echo [app] Starting production server...
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4 --no-access-log
) else (
    echo [app] Starting development server...
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend\app
)
