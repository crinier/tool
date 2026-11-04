#!/bin/bash
# "Schermo PC": lo schermo di Windows sulla console, via cavo USB.
#
# Il cavo USB (porta OTG) diventa una piccola rete fra PC e console:
#   console = 169.254.7.1   (il PC si prende da solo un indirizzo 169.254.x.x)
# Poi parte l'app "Schermo PC". Sul PC avvia pc/"Schermo su console.bat".
#
# SPERIMENTALE: serve la modalita' USB "device" (come per Chiavetta USB).
# Se non c'e', l'app parte lo stesso e funziona via WiFi, se c'e' il WiFi.

DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)/tool"
LOG="$DIR/log-schermo.txt"
TTY=/dev/tty1
G=/sys/kernel/config/usb_gadget/r36net
IP=169.254.7.1

if [ "$(id -u)" -eq 0 ]; then SUDO=""; elif command -v sudo >/dev/null; then SUDO="sudo -n"; else SUDO=""; fi
[ -e "$TTY" ] && [ ! -w "$TTY" ] && $SUDO chmod 666 "$TTY" 2>/dev/null
out() { if [ -w "$TTY" ]; then printf "%s\n" "$@" >"$TTY"; else printf "%s\n" "$@"; fi; }
printf "\033c" >"$TTY" 2>/dev/null
: >"$LOG"

OLD=""
UDC=""
gadget_up() {
  $SUDO modprobe libcomposite 2>>"$LOG"
  $SUDO modprobe usb_f_ncm 2>>"$LOG"
  mountpoint -q /sys/kernel/config || $SUDO mount -t configfs none /sys/kernel/config 2>>"$LOG"
  UDC="$(ls /sys/class/udc 2>/dev/null | head -n1)"
  [ -z "$UDC" ] && { $SUDO modprobe dwc2 2>>"$LOG"; sleep 1; UDC="$(ls /sys/class/udc 2>/dev/null | head -n1)"; }
  [ -z "$UDC" ] && { echo "nessun UDC" >>"$LOG"; return 1; }
  for g in /sys/kernel/config/usb_gadget/*; do
    [ -d "$g" ] && [ "$g" != "$G" ] && [ "$(cat "$g/UDC" 2>/dev/null)" = "$UDC" ] && OLD="$g"
  done
  $SUDO sh -c "
    [ -n '$OLD' ] && echo '' > '$OLD/UDC'
    mkdir -p '$G' && cd '$G' || exit 1
    echo 0x1d6b > idVendor; echo 0x0104 > idProduct
    echo 0x0200 > bcdUSB
    mkdir -p strings/0x409
    echo R36S > strings/0x409/manufacturer
    echo 'R36S Schermo' > strings/0x409/product
    echo R36S0002 > strings/0x409/serialnumber
    mkdir -p configs/c.1/strings/0x409
    echo Rete > configs/c.1/strings/0x409/configuration
    echo 250 > configs/c.1/MaxPower
    mkdir -p functions/ncm.usb0 || exit 1
    ln -sf functions/ncm.usb0 configs/c.1/
    echo '$UDC' > UDC
  " 2>>"$LOG" || return 1
  sleep 1
  IFACE="$(cat "$G/functions/ncm.usb0/ifname" 2>/dev/null)"
  [ -z "$IFACE" ] && IFACE=usb0
  $SUDO ip addr add "$IP/16" dev "$IFACE" 2>>"$LOG"
  $SUDO ip link set "$IFACE" up 2>>"$LOG"
  echo "gadget ok: $IFACE $IP" >>"$LOG"
  return 0
}

gadget_down() {
  [ -d "$G" ] || return
  $SUDO sh -c "
    echo '' > '$G/UDC'
    rm -f '$G/configs/c.1/ncm.usb0'
    rmdir '$G/configs/c.1/strings/0x409' '$G/configs/c.1' '$G/functions/ncm.usb0' '$G/strings/0x409' '$G'
    [ -n '$OLD' ] && echo '$UDC' > '$OLD/UDC'
  " 2>>"$LOG"
}

if gadget_up; then
  out "Cavo USB pronto: la console e' $IP" "Collega il cavo alla porta OTG e avvia sul PC" "'Schermo su console.bat'."
else
  out "Modalita' USB device non disponibile (vedi $LOG)." "Provo comunque via WiFi, se c'e'."
fi
sleep 2
trap gadget_down EXIT

PY="$(command -v python3 || command -v python)"
cd "$DIR" && SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-kmsdrm}" "$PY" launcher.py --app schermo_pc >>"$LOG" 2>&1 \
  || (cd "$DIR" && unset SDL_VIDEODRIVER && "$PY" launcher.py --app schermo_pc >>"$LOG" 2>&1)
printf "\033c" >"$TTY" 2>/dev/null
