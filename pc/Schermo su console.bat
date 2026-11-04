@echo off
rem Manda lo schermo di questo PC alla console (app "Schermo PC" sulla console).
rem Doppio clic. Serve Python 3 da https://www.python.org
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py -3
%PY% -c "import mss, pygame" 2>nul
if errorlevel 1 (
  echo Installo mss e pygame-ce, una volta sola...
  %PY% -m pip install --user --only-binary=:all: mss pygame-ce
)
echo.
echo Sulla console apri:  Ports - "Schermo PC"  (oppure Tool - Schermo PC)
echo Collega il cavo USB dati alla porta OTG della console. Niente altro da fare.
echo.
%PY% schermo_su_console.py
pause
