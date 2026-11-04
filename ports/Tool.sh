#!/bin/bash
# Avviatore per la sezione "Ports" di EmulationStation.
# Provato come struttura su ArkOS / dArkOS (utente con sudo) e ROCKNIX /
# AmberELEC (root, senza sudo). Copia questo file e la cartella "tool"
# dentro la cartella ports/ della scheda SD.

DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)/tool"
LOG="$DIR/log.txt"
TTY=/dev/tty1

if [ "$(id -u)" -eq 0 ]; then SUDO=""; elif command -v sudo >/dev/null; then SUDO="sudo -n"; else SUDO=""; fi
[ -e "$TTY" ] && [ ! -w "$TTY" ] && $SUDO chmod 666 "$TTY" 2>/dev/null
out() { if [ -w "$TTY" ]; then printf "%s\n" "$@" >"$TTY"; else printf "%s\n" "$@"; fi; }
cls() { [ -w "$TTY" ] && printf "\033c" >"$TTY"; }

cls
cd "$DIR" || { out "Cartella $DIR non trovata"; sleep 5; exit 1; }

PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
  out "Python 3 non trovato su questo sistema." "Serve un sistema tipo dArkOS / ArkOS (vedi README)."
  sleep 10
  cls
  exit 1
fi
# pygame: se il sistema non ce l'ha, il launcher usa quello incluso nel kit (vendor/)

# driver video: prima kmsdrm (schermo senza X), poi scelta automatica di SDL, poi fbcon
{
  echo "=== $(date) : $PY, utente $(id -un)"
  for drv in "${SDL_VIDEODRIVER:-kmsdrm}" "" fbcon; do
    if [ -n "$drv" ]; then export SDL_VIDEODRIVER="$drv"; else unset SDL_VIDEODRIVER; fi
    echo "--- video: ${drv:-auto}"
    "$PY" launcher.py
    rc=$?
    [ $rc -eq 0 ] && break
    [ $rc -eq 2 ] && break      # pygame mancante: inutile cambiare driver
  done
  echo "exit $rc"
} >"$LOG" 2>&1

if [ "${rc:-0}" -ne 0 ]; then
  out "Qualcosa non va (codice $rc). Ultime righe di tool/log.txt:" ""
  tail -n 12 "$LOG" | cut -c1-60 | while IFS= read -r l; do out "$l"; done
  sleep 15
fi

cls
