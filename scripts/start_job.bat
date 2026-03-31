@echo off
REM Run the data lineage scanning job
setlocal

set ROOT=%~dp0..
cd /d "%ROOT%"

if exist "backend\.venv\Scripts\activate.bat" (
    call backend\.venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo [job] Starting data lineage scan...
python -m backend.job.data_lineage %*
echo [job] Done.
