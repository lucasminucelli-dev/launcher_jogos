@echo off
setlocal
cd /d "%~dp0"

rem Tenta abrir sem janela de console (pythonw), depois py, depois python.
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw launcher.py
    exit /b
)
where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw -3 launcher.py
    exit /b
)
where python >nul 2>nul
if %errorlevel%==0 (
    python launcher.py
    exit /b
)
echo Python nao encontrado.
echo Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
pause
