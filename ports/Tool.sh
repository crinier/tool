#!/bin/bash
# Avviatore per la sezione "Ports" di EmulationStation (ArkOS / dArkOS / ROCKNIX).
# Copia questo file e la cartella "tool" dentro roms/ports/ della scheda SD.

DIR="$(cd "$(dirname "$0")" && pwd)/tool"
LOG="$DIR/log.txt"
TTY=/dev/tty1

[ -w "$TTY" ] || sudo chmod 666 "$TTY" 2>/dev/null
printf "\033c" > "$TTY" 2>/dev/null

cd "$DIR" || exit 1

if ! python3 -c "import pygame" 2>/dev/null; then
  {
    echo "python3 o pygame non trovati."
    echo
    echo "Con il WiFi attivo, da terminale/SSH:"
    echo "  sudo apt update && sudo apt install python3-pygame"
    echo
    echo "Dettagli nel README del progetto."
  } > "$TTY"
  sleep 12
  printf "\033c" > "$TTY"
  exit 1
fi

# Rimuovi la riga sotto se SDL sceglie gia' il driver video giusto da solo.
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-kmsdrm}"
python3 launcher.py > "$LOG" 2>&1 || {
  # secondo tentativo lasciando scegliere SDL
  unset SDL_VIDEODRIVER
  python3 launcher.py >> "$LOG" 2>&1
}

printf "\033c" > "$TTY" 2>/dev/null
