@echo off
setlocal
cd /d "%~dp0"
echo Instalando o pygame (precisa de internet)...
echo.
python -m pip install --upgrade pygame
if errorlevel 1 (
    echo.
    echo Tentando pelo Python Launcher...
    py -3 -m pip install --upgrade pygame
)
echo.
echo Pronto. Se nao apareceu nenhum erro acima, pode abrir o Arcade.
pause
