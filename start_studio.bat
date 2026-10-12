@echo off
setlocal
set "CURRENT_DIR=%CD%"
set "PYTHONPATH=%CURRENT_DIR%"

echo ========================================================
echo        Dark_print - Servidor Principal
echo ========================================================
echo Acesse no seu navegador: http://127.0.0.1:8080
echo.

if exist "%CURRENT_DIR%\.venv\Scripts\python.exe" (
    "%CURRENT_DIR%\.venv\Scripts\python.exe" main.py
) else (
    python main.py
)
pause
