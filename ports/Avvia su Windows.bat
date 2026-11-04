@echo off
rem Avvia R36 Tool sul PC Windows (in una finestra).
rem Doppio clic su questo file. Serve Python 3: https://www.python.org
rem (durante l'installazione spunta "Add python.exe to PATH").
cd /d "%~dp0tool"
set PY=python
where py >nul 2>nul && set PY=py -3
%PY% -c "import pygame" 2>nul
if errorlevel 1 (
  echo Installo pygame, una volta sola...
  %PY% -m pip install --user pygame
  if errorlevel 1 goto nopy
)
%PY% launcher.py
if errorlevel 1 pause
exit /b

:nopy
echo.
echo Python non trovato o pip non funziona.
echo Installa Python da https://www.python.org e spunta "Add python.exe to PATH".
pause
