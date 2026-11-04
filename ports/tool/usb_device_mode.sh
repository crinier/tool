# Funzioni condivise (da includere con "."): forza la porta OTG in modalita'
# device e poi la rimette com'era. Sui Rockchip la porta, con un cavo verso il
# PC, spesso resta in "host" e il PC non vede niente ("not attached").
#   force_device   -> salva il modo attuale e mette "peripheral"
#   restore_mode   -> rimette il modo salvato
OTG_FILE=""
OTG_OLD=""
force_device() {
  OTG_FILE="$(find /sys/devices/platform -maxdepth 5 -name otg_mode 2>/dev/null | head -n1)"
  if [ -n "$OTG_FILE" ]; then
    OTG_OLD="$(cat "$OTG_FILE" 2>/dev/null | tr -d '[:space:]')"
    case "$OTG_OLD" in host|peripheral|otg) ;; *) OTG_OLD=otg ;; esac
    $SUDO sh -c "echo peripheral > '$OTG_FILE'" 2>>"$LOG" && echo "otg_mode: $OTG_OLD -> peripheral ($OTG_FILE)" >>"$LOG"
    sleep 1
    return 0
  fi
  echo "otg_mode non trovato: uso il modo automatico" >>"$LOG"
  return 1
}
restore_mode() {
  [ -n "$OTG_FILE" ] && $SUDO sh -c "echo '$OTG_OLD' > '$OTG_FILE'" 2>>"$LOG"
}
# toglie un gadget lasciato a meta' da un'esecuzione precedente
remove_gadget() {
  local g="$1"
  [ -d "$g" ] || return 0
  $SUDO sh -c "
    [ -n \"\$(cat '$g/UDC' 2>/dev/null)\" ] && echo '' > '$g/UDC'
    for l in '$g'/configs/*/*.*; do [ -L \"\$l\" ] && rm -f \"\$l\"; done
    for d in '$g'/configs/*/strings/*; do [ -d \"\$d\" ] && rmdir \"\$d\"; done
    for d in '$g'/configs/*; do [ -d \"\$d\" ] && rmdir \"\$d\"; done
    for d in '$g'/functions/*; do [ -d \"\$d\" ] && rmdir \"\$d\"; done
    for d in '$g'/strings/*; do [ -d \"\$d\" ] && rmdir \"\$d\"; done
    rmdir '$g'
  " 2>>"$LOG"
}
