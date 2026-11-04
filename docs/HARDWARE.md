# Cosa c'e' dentro la tua console (dal file `rf3536k4ka.dtb`)

Ho decompilato il `.dtb` del firmware originale (versione leggibile:
[`dtb-originale/rf3536k4ka.dts`](dtb-originale/rf3536k4ka.dts)).

| Parte | Cosa dice il dtb |
|---|---|
| Processore | Rockchip **RK3326** (4x Cortex-A35), GPU Mali-G31 |
| Scheda | `rockchip,rk3326-evb-lp3-v12-linux`: scheda di riferimento Rockchip con RAM LPDDR3 |
| Kernel | quello **di Rockchip** (BSP, ci sono `fiq-debugger`, `charge-animation`, tabelle `px30s`), non il kernel ufficiale Linux |
| Schermo | MIPI-DSI 4 linee, controller compatibile **Sitronix ST7703**, **640x480**, 153x85 mm, clock pixel 30 MHz. Sequenza di init inizia con `B9 F1 12 83` |
| Timing schermo | hfp 150 / hsync 50 / hbp 150, vfp 20 / vsync 6 / vbp 12 |
| Gestione energia + audio | **RK817** (batteria, caricatore, codec audio) |
| Tasti | driver **`play_joystick`** (proprietario): 19 tasti GPIO + 4 assi analogici |
| Stick analogici | SARADC canali 0-3 (sx X/Y, dx X/Y) |
| Tasti GPIO (attivi bassi) | GPIO3: B2, B3, B4, B5, B6, C0-C7, D0-D3; GPIO2: B5, B6 |
| Click stick / altro | `rocker` su GPIO2 B4, B7, C0 |
| Volume | `adc-keys` (vol+ / vol-) |
| WiFi/BT | nodo `seekwave,sv6160` presente ma **disattivato** (`status = "disabled"`): probabilmente il chip non c'e' |

## Cosa vuol dire per cambiare sistema operativo

- **Non puoi mettere questo `.dtb` dentro ArkOS / dArkOS / ROCKNIX.**
  Funziona solo col kernel del firmware originale. In particolare il driver
  dei tasti `play_joystick` non esiste negli altri sistemi: lo schermo forse si
  accende, ma i tasti no.
- Gli altri sistemi hanno **i loro** dtb per i cloni. Devi scegliere quello
  il cui schermo corrisponde al tuo. I dati della tabella sopra (ST7703,
  640x480, sequenza `B9 F1 12 83 ...`, timing) servono a confrontare.
- Se nessun dtb gia' pronto va bene, se ne fa uno: si prende il dtb del
  sistema nuovo per un clone simile e ci si copia **dal tuo** la sezione
  `panel@0` (init sequence + timing). I tasti di solito sono gia' sugli
  stessi GPIO3 (e' lo schema standard delle console RK3326). E' un lavoro
  fattibile, ma va provato sulla console.
