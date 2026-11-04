@echo off
rem Avvia R36 Tool sul PC Windows (in una finestra).
rem Doppio clic su questo file. Serve Python 3: https://www.python.org
rem (durante l'installazione spunta "Add python.exe to PATH").
cd /d "%~dp0tool"
set PY=python
where py >nul 2>nul && set PY=py -3
%PY% -c "import pygame" 2>nul
if errorlevel 1 (
  echo Installo pygame-ce, una volta sola...
  rem pygame-ce: stessa cosa di pygame, ma con i pacchetti pronti anche per Python 3.14
  %PY% -m pip install --user --only-binary=:all: pygame-ce
  %PY% -c "import pygame" 2>nul
  if errorlevel 1 (
    %PY% -m pip install --user --only-binary=:all: pygame
  )
  %PY% -c "import pygame" 2>nul
  if errorlevel 1 goto nopy
)
%PY% launcher.py
if errorlevel 1 pause
exit /b

:nopy
echo.
echo Non riesco a installare pygame.
echo Prova a mano:   %PY% -m pip install --user pygame-ce
echo Se non va, installa Python 3.13 da https://www.python.org
echo (spunta "Add python.exe to PATH") e riprova.
pause
