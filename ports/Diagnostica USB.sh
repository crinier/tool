#!/bin/bash
# Diagnostica USB: dice se questa console puo' fare da "chiavetta" o da
# "schermo" via cavo. Mostra tutto sullo schermo (fai una foto) e salva
# il rapporto in tool/diagnostica-usb.txt sulla SD.

DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
REP="$DIR/tool/diagnostica-usb.txt"
TTY=/dev/tty1
if [ "$(id -u)" -eq 0 ]; then SUDO=""; elif command -v sudo >/dev/null; then SUDO="sudo -n"; else SUDO=""; fi
[ -e "$TTY" ] && [ ! -w "$TTY" ] && $SUDO chmod 666 "$TTY" 2>/dev/null
FONT=/usr/share/consolefonts/Lat7-Terminus16.psf.gz
[ -f "$FONT" ] && $SUDO setfont -C "$TTY" "$FONT" 2>/dev/null
printf "\033c" >"$TTY" 2>/dev/null

{
  echo "=== DIAGNOSTICA USB  $(date '+%d/%m %H:%M') ==="
  echo "Sistema: $(. /etc/os-release 2>/dev/null; echo "$PRETTY_NAME") | kernel $(uname -r)"
  echo "Modello: $(tr -d '\0' </proc/device-tree/model 2>/dev/null)"
  $SUDO modprobe libcomposite 2>/dev/null
  mountpoint -q /sys/kernel/config || $SUDO mount -t configfs none /sys/kernel/config 2>/dev/null
  UDC="$(ls /sys/class/udc 2>/dev/null | tr '\n' ' ')"
  echo "UDC (porta device): ${UDC:-NESSUNO}"
  for f in /proc/device-tree/*usb*/dr_mode /proc/device-tree/*/*usb*/dr_mode; do
    [ -f "$f" ] && echo "dr_mode $(basename "$(dirname "$f")"): $(tr -d '\0' <"$f")"
  done
  for u in /sys/class/udc/*; do [ -e "$u/state" ] && echo "stato $(basename "$u"): $(cat "$u/state")"; done
  echo -n "configfs gadget: "; [ -d /sys/kernel/config/usb_gadget ] && echo si || echo NO
  echo -n "moduli: "
  for m in libcomposite usb_f_ncm usb_f_ecm usb_f_rndis usb_f_mass_storage g_ether g_mass_storage dwc2; do
    if modinfo "$m" >/dev/null 2>&1 || grep -qw "${m}" /proc/modules 2>/dev/null; then echo -n "$m:si "; else echo -n "$m:no "; fi
  done
  echo
  for f in $(find /sys/devices/platform -maxdepth 5 -name otg_mode 2>/dev/null); do echo "otg_mode: $(cat "$f")  ($f)"; done
  if [ -d /sys/kernel/config/usb_gadget ]; then
    T=/sys/kernel/config/usb_gadget/r36test
    echo -n "funzioni USB nel kernel: "
    $SUDO mkdir -p "$T" 2>/dev/null
    for fn in ncm ecm rndis mass_storage acm; do
      if $SUDO mkdir "$T/functions/$fn.t" 2>/dev/null; then echo -n "$fn:SI "; $SUDO rmdir "$T/functions/$fn.t"; else echo -n "$fn:no "; fi
    done
    $SUDO rmdir "$T" 2>/dev/null
    echo
  fi
  echo -n "gadget gia' attivi: "; ls /sys/kernel/config/usb_gadget 2>/dev/null | tr '\n' ' '; echo
  echo "Python: $(python3 --version 2>&1)"
  echo "--- log Schermo PC (ultime righe) ---"
  grep -v CRTC "$DIR/tool/log-schermo.txt" 2>/dev/null | tail -n 8; [ -f "$DIR/tool/log-schermo.txt" ] || echo "(nessun log: Schermo PC mai avviato?)"
  echo "--- VERDETTO ---"
  if [ -z "$UDC" ]; then
    echo "La porta USB della console funziona solo da 'host' (per chiavette e pad)."
    echo "Chiavetta USB e Schermo PC via cavo NON possono funzionare con questo sistema."
  else
    echo "La porta puo' fare da 'device': Chiavetta e Schermo via cavo sono possibili."
    echo "Se non vanno, manda questa foto: il problema e' altrove."
  fi
} 2>&1 | tee "$REP" | cut -c1-78 >"$TTY"

# aspetta un tasto (o 60 s) per dare tempo alla foto
python3 - <<'EOF' 2>/dev/null || sleep 60
import glob, os, select, time
fds = []
for p in glob.glob("/dev/input/event*"):
    try:
        fds.append(os.open(p, os.O_RDONLY | os.O_NONBLOCK))
    except OSError:
        pass
end = time.time() + 120
time.sleep(1.5)
for fd in fds:
    try:
        while os.read(fd, 4096):
            pass
    except OSError:
        pass
while time.time() < end:
    r, _, _ = select.select(fds, [], [], 1)
    if r:
        break
EOF
printf "\033c" >"$TTY" 2>/dev/null
