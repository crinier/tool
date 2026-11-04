#!/bin/bash
# "Chiavetta USB": il PC (Windows, Mac, Linux) vede la partizione dei giochi
# della console come una chiavetta USB, cosi' ci copi dentro i file.
#
# SPERIMENTALE: serve un kernel con la modalita' USB "device" (USB gadget)
# attiva sulla porta OTG. Se non c'e', lo script lo dice e non tocca niente.
#
# Come si usa: avvialo da Ports, collega il cavo USB-C dati alla porta OTG,
# copia i file, poi su Windows "Espelli". In alternativa tieni premuto un
# tasto qualsiasi della console per 2 secondi.

TTY=/dev/tty1
WORK=/tmp/r36-chiavetta.sh
LOG=/tmp/r36-chiavetta.log

if [ "$(id -u)" -eq 0 ]; then SUDO=""; else SUDO="sudo -n"; fi
say() { printf "%s\n" "$@" | $SUDO tee "$TTY" >/dev/null 2>&1; printf "%s\n" "$@" >>"$LOG"; }
cls() { printf "\033c" | $SUDO tee "$TTY" >/dev/null 2>&1; }

# ---------------------------------------------------------------- fase 1
# Lo script vive sulla partizione da smontare: si copia in /tmp e riparte
# in un servizio separato, cosi' sopravvive allo stop di EmulationStation.
if [ "$1" != "--worker" ]; then
  SELF="$(readlink -f "$0")"
  MNT="$(findmnt -n -o TARGET -T "$SELF")"
  cp "$SELF" "$WORK" && chmod +x "$WORK"
  : >"$LOG"
  if command -v systemd-run >/dev/null 2>&1; then
    UNIT="r36-chiavetta-$$"
    if $SUDO systemd-run --unit="$UNIT" --collect "$WORK" --worker "$MNT" >>"$LOG" 2>&1; then
      # se EmulationStation viene fermato, questo script muore con lui: va bene
      sleep 1
      while systemctl is-active --quiet "$UNIT"; do sleep 1; done
      exit 0
    fi
  fi
  # niente systemd: si prova lo stesso, senza fermare EmulationStation
  exec $SUDO "$WORK" --worker "$MNT" --no-es-stop
fi

# ---------------------------------------------------------------- fase 2
MNT="$2"
NO_ES_STOP="$3"
G=/sys/kernel/config/usb_gadget/r36
FONT=/usr/share/consolefonts/Lat7-Terminus20x10.psf.gz
[ -f "$FONT" ] && setfont -C "$TTY" "$FONT" 2>/dev/null
cls

DEV="$(findmnt -n -o SOURCE --target "$MNT")"
FSTYPE="$(findmnt -n -o FSTYPE --target "$MNT")"
OPTS="$(findmnt -n -o OPTIONS --target "$MNT")"

ES_SVC=""
for s in emulationstation essway emustation; do
  systemctl is-active --quiet "$s" 2>/dev/null && ES_SVC="$s" && break
done
restart_es() { [ -n "$ES_SVC" ] && [ -z "$NO_ES_STOP" ] && systemctl start "$ES_SVC"; }

UNMOUNTED=""
fail() {
  say "" "ERRORE: $1" "" "Torno al menu tra 10 secondi." "(dettagli in $LOG)"
  if [ -n "$UNMOUNTED" ]; then trap - EXIT; cleanup; fi
  sleep 10
  cls
  restart_es
  exit 1
}

say "=== Chiavetta USB ===" "" "Partizione: $MNT ($DEV, $FSTYPE)"

[ -n "$DEV" ] && [ -b "$DEV" ] || fail "partizione dei giochi non trovata."
case "$FSTYPE" in
  vfat|exfat|ntfs|ntfs3|fuseblk) ;;
  *) fail "la partizione e' $FSTYPE: Windows non la sa leggere. Serve FAT32 / exFAT." ;;
esac
case "$MNT" in
  /|/boot|/usr|/var|/home) fail "la partizione $MNT e' di sistema, non la condivido." ;;
esac

# supporto USB gadget?
modprobe libcomposite 2>>"$LOG"
modprobe usb_f_mass_storage 2>>"$LOG"
mountpoint -q /sys/kernel/config || mount -t configfs none /sys/kernel/config 2>>"$LOG"
UDC="$(ls /sys/class/udc 2>/dev/null | head -n1)"
if [ -z "$UDC" ]; then
  modprobe dwc2 2>>"$LOG"
  sleep 1
  UDC="$(ls /sys/class/udc 2>/dev/null | head -n1)"
fi
LEGACY=""
if [ -z "$UDC" ] || [ ! -d /sys/kernel/config/usb_gadget ]; then
  if modinfo g_mass_storage >/dev/null 2>&1 && [ -n "$UDC" ]; then
    LEGACY=1
  else
    fail "questo kernel non ha la modalita' USB device (nessun UDC). Usa il lettore di schede SD sul PC."
  fi
fi

say "" "Fermo EmulationStation e smonto la partizione..."
[ -n "$ES_SVC" ] && [ -z "$NO_ES_STOP" ] && systemctl stop "$ES_SVC"
sleep 1
sync
if ! umount "$MNT" 2>>"$LOG"; then
  sleep 2
  umount "$MNT" 2>>"$LOG" || fail "non riesco a smontare $MNT (qualcosa lo sta usando)."
fi
UNMOUNTED=1

OLD=""
cleanup() {
  if [ -n "$LEGACY" ]; then
    rmmod g_mass_storage 2>>"$LOG"
  elif [ -d "$G" ]; then
    echo "" >"$G/UDC" 2>/dev/null
    rm -f "$G/configs/c.1/mass_storage.usb0"
    rmdir "$G/configs/c.1/strings/0x409" "$G/configs/c.1" \
          "$G/functions/mass_storage.usb0" "$G/strings/0x409" "$G" 2>>"$LOG"
  fi
  [ -n "$OLD" ] && echo "$UDC" >"$OLD/UDC" 2>>"$LOG"
  sync
  say "" "Rimonto la partizione..."
  case "$FSTYPE" in
    vfat) command -v fsck.vfat >/dev/null && fsck.vfat -a "$DEV" >>"$LOG" 2>&1 ;;
    exfat) command -v fsck.exfat >/dev/null && fsck.exfat -y "$DEV" >>"$LOG" 2>&1 ;;
  esac
  mount "$MNT" 2>>"$LOG" || mount -t "$FSTYPE" -o "$OPTS" "$DEV" "$MNT" 2>>"$LOG" \
    || say "ATTENZIONE: rimontaggio fallito, riavvia la console."
}
trap cleanup EXIT

if [ -n "$LEGACY" ]; then
  modprobe g_mass_storage file="$DEV" removable=1 stall=0 2>>"$LOG" \
    || fail "g_mass_storage non parte."
  LUNFILE=$(ls /sys/devices/platform/*/gadget/lun0/file 2>/dev/null | head -n1)
else
  for g in /sys/kernel/config/usb_gadget/*; do
    [ -d "$g" ] && [ "$g" != "$G" ] && [ "$(cat "$g/UDC" 2>/dev/null)" = "$UDC" ] && OLD="$g"
  done
  [ -n "$OLD" ] && echo "" >"$OLD/UDC"
  mkdir -p "$G" && cd "$G" || fail "configfs non scrivibile."
  echo 0x1d6b >idVendor
  echo 0x0104 >idProduct
  mkdir -p strings/0x409
  echo "R36S" >strings/0x409/manufacturer
  echo "R36S Giochi" >strings/0x409/product
  echo "R36S0001" >strings/0x409/serialnumber
  mkdir -p configs/c.1/strings/0x409
  echo "Chiavetta" >configs/c.1/strings/0x409/configuration
  echo 250 >configs/c.1/MaxPower
  mkdir -p functions/mass_storage.usb0 || fail "funzione mass_storage non disponibile."
  echo 1 >functions/mass_storage.usb0/lun.0/removable
  echo "$DEV" >functions/mass_storage.usb0/lun.0/file || fail "non riesco a esporre $DEV."
  ln -s functions/mass_storage.usb0 configs/c.1/
  echo "$UDC" >UDC 2>>"$LOG" || fail "porta USB occupata o in modalita' host."
  LUNFILE="$G/functions/mass_storage.usb0/lun.0/file"
fi

cls
say "=== CHIAVETTA USB ATTIVA ===" "" \
    "Collega il cavo alla porta OTG e apri" "'Questo PC' su Windows." "" \
    "Per finire:" "  - su Windows clicca 'Espelli'" "  - oppure tieni premuto un tasto" "    della console per 2 secondi" "" \
    "NON staccare il cavo mentre copi!"

# attesa: espulsione dal PC oppure tasto tenuto premuto 2 s (solo libreria standard)
python3 - "$LUNFILE" <<'EOF' 2>>"$LOG"
import glob, os, select, struct, sys, time
lun = sys.argv[1]
fds = []
for p in glob.glob("/dev/input/event*"):
    try:
        fds.append(os.open(p, os.O_RDONLY | os.O_NONBLOCK))
    except OSError:
        pass
fmt = "llHHi"
size = struct.calcsize(fmt)
held = {}
while True:
    try:
        if lun and not open(lun).read().strip():
            sys.exit(0)            # espulsa dal PC
    except OSError:
        pass
    r, _, _ = select.select(fds, [], [], 0.5)
    for fd in r:
        try:
            data = os.read(fd, size * 32)
        except OSError:
            continue
        for i in range(0, len(data) - size + 1, size):
            _, _, typ, code, val = struct.unpack(fmt, data[i:i + size])
            if typ == 1:
                if val == 1:
                    held[(fd, code)] = time.monotonic()
                elif val == 0:
                    held.pop((fd, code), None)
    now = time.monotonic()
    if any(now - t >= 2 for t in held.values()):
        sys.exit(0)
EOF
[ $? -ne 0 ] && { say "(python3 non disponibile: chiudo la chiavetta tra 120 s)"; sleep 120; }

say "" "Chiudo la chiavetta..."
cleanup
trap - EXIT
say "Fatto! Torno ai giochi."
sleep 2
cls
restart_es
exit 0
