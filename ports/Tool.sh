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

PY=""
for p in python3 /usr/bin/python3 /storage/.local/bin/python3; do
  command -v "$p" >/dev/null 2>&1 && "$p" -c "import pygame" 2>/dev/null && PY="$p" && break
done
if [ -z "$PY" ]; then
  out "python3 o pygame non trovati." "" \
      "Con il WiFi attivo, da terminale o SSH:" \
      "  sudo apt update && sudo apt install python3-pygame" "" \
      "oppure:  pip3 install pygame" "" "Dettagli nel README."
  sleep 12
  cls
  exit 1
fi

# driver video: prima kmsdrm (schermo senza X), poi scelta automatica di SDL, poi fbcon
{
  echo "=== $(date) : $PY, utente $(id -un)"
  for drv in "${SDL_VIDEODRIVER:-kmsdrm}" "" fbcon; do
    if [ -n "$drv" ]; then export SDL_VIDEODRIVER="$drv"; else unset SDL_VIDEODRIVER; fi
    echo "--- video: ${drv:-auto}"
    "$PY" launcher.py && break
  done
} >"$LOG" 2>&1

cls
