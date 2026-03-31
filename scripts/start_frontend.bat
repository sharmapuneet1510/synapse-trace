@echo off
REM Start the frontend dev server
setlocal

set ROOT=%~dp0..
cd /d "%ROOT%\frontend"

set MODE=%1
if "%MODE%"=="preview" (
    echo [frontend] Building and starting preview server...
    call npm run build
    call npm run preview
) else (
    echo [frontend] Starting dev server...
    call npm run dev
)
