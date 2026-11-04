# R36 Tool: programmi fatti da noi sulla R36S (clone)

Un menu che parte dalla sezione **Ports** della console e lancia programmini
in Python + pygame: **Amichetto** (Bobo), **Areometro**, **Cronometro**, **Configura tasti**, piu' un
modello per scriverne di nuovi.

```
ports/
  Tool.sh                 <- avviatore (va in roms/ports/)
  Chiavetta USB.sh        <- la console diventa una chiavetta per il PC
  tool/
    launcher.py           <- menu principale
    r36/                  <- mini-libreria: schermo, tasti, menu, moduli, suoni
    apps/
      areometro/          <- correzione temperatura, ABV, SG/Plato/Brix
      amichetto/          <- Bobo: due occhi su schermo nero che vivono
      cronometro/
      configura_tasti/    <- mappatura tasti (parte da sola al 1o avvio)
      _modello/           <- copia questa cartella per una nuova app
docs/
  HARDWARE.md             <- cosa dice il dtb della tua console
  dtb-originale/          <- il tuo .dtb + versione leggibile .dts
```

## 1. Il sistema operativo

Il firmware originale dei cloni di solito **non** ha Python ne' pygame, e
non si possono installare. Serve un sistema basato su Linux "vero", con `apt`:

- **dArkOS / dArkOSRE per R36** (successore di ArkOS, Debian): consigliato.
  Ha python3 e `apt`.
- **ArkOS per K36 / cloni R36S** (AeolusUX): ha diversi dtb per gli schermi
  dei cloni nella cartella `boot`, da scambiare.
- ROCKNIX: ottimo per i giochi, ma senza `apt` installare pygame e' scomodo.

**Prima di tutto fai una copia della scheda SD originale** (es. con Win32DiskImager
o `dd`), cosi' puoi sempre tornare indietro.

Il tuo `.dtb` (vedi [docs/HARDWARE.md](docs/HARDWARE.md)) serve per capire quale
dtb del sistema nuovo scegliere: schermo ST7703 640x480. **Non va copiato
cosi' com'e'** nel sistema nuovo, perche' usa un driver dei tasti che c'e'
solo nel firmware originale.

Procedura tipica: scrivi l'immagine sulla SD -> se lo schermo resta nero o i
tasti non vanno, prova gli altri dtb per cloni che il sistema offre
(cartella `boot` della SD, istruzioni della release) -> quando schermo e
tasti funzionano, vai al punto 2.

## 2. Python e pygame sulla console

Serve una chiavetta WiFi USB oppure il WiFi integrato, se il tuo clone lo ha.
Dal terminale della console oppure via SSH:

```bash
python3 -c "import pygame; print(pygame.version.ver)"
```

Se da' errore:

```bash
sudo apt update && sudo apt install -y python3-pygame
```

## 3. Installazione

Con la SD nel PC, copia `ports/Tool.sh`, `ports/Chiavetta USB.sh` **e** la cartella `ports/tool/` dentro
la cartella `ports` della partizione giochi (`roms/ports/` su ArkOS,
`EASYROMS/ports/` su alcune immagini). Poi in EmulationStation:
*Start -> Game settings / Update games list*, e trovi **Tool** sotto Ports.

Al primo avvio parte **Configura tasti**: premi ogni tasto quando richiesto (se un
tasto non ce l'hai, aspetta 8 secondi e viene saltato). Tutto viene salvato in
`tool/config.json`; cancellalo per rifare la procedura.

- **SELECT + START** chiude sempre l'app corrente.
- Se qualcosa va storto, guarda `tool/log.txt`.

## 4. Provare sul PC

```bash
pip install pygame
```

```bash
python3 ports/tool/launcher.py
```

Tastiera: frecce = croce, Z/Invio = A, X/Backspace = B, C = X, V = Y,
Q/E = L1/R1, Tab = SELECT, Spazio = START, Esc = esci.

## 5. Fare una nuova app

1. Copia `ports/tool/apps/_modello` in `ports/tool/apps/mia_app`.
2. In `main.py` cambia `NAME` e scrivi `run(ctx)`.
3. Compare da sola nel menu.

Per calcolatori tipo l'areometro basta `r36.form(...)`: definisci i campi
(`Field(etichetta, valore, passo, passo_grande, min, max, formato, unita)`)
e una funzione che calcola i risultati. Guarda `apps/areometro/main.py`.

## Areometro: formule

- Correzione temperatura: formula polinomiale standard dei densimetri
  (taratura di default 20 C, modificabile).
- ABV = (OG - FG) x 131.25, piu' la formula alternativa "precisa" per gradi alti.
- SG -> Plato / Brix con i polinomi standard, Brix -> SG per il rifrattometro.

## Amichetto: Bobo

Schermo nero, due occhioni luminosi che si guardano intorno, sbattono le
palpebre e cambiano forma e colore con l'umore. Ogni cosa ha il suo versetto:
i suoni sono sintetizzati dal codice, quindi non servono file audio.

| Umore | Occhi |
|---|---|
| contento | azzurri, si guardano intorno |
| felice / mangia | a mezzaluna `^ ^`, saltellano |
| coccole | diventano due cuori rosa |
| arrabbiato | rossi, palpebre a V, tremano e fumano |
| triste | blu, palpebre cadenti, lacrimucce |
| fame | gialli |
| stanco | mezzi chiusi |
| dorme | due righine, con le "z" e il russare |
| stuzzicato | `> <` |

Tasti: **SX/DX** scegli, **A** fai, **X** stuzzica, **Y** suoni on/off, **B** esci.

- **Mangia**: mela, biscotto o pizza. Se e' pieno rifiuta e sbuffa.
- **Gioca**: indovina in quale pacchetto ha nascosto il biscotto (gli occhi ti fanno
  i dispetti guardando a destra e sinistra).
- **Coccole**: cuoricini e una melodia. Fanno passare anche il broncio.
- **Luce**: lo metti a dormire o lo svegli. Se lo svegli quando e' stanco si arrabbia.
- **X = stuzzica**: tre volte di fila e si arrabbia sul serio.

Quando chiudi l'app lo stato viene salvato in `bobo.json`. Il tempo passa
anche mentre sei via, ma piu' piano, e Bobo non muore mai.

I suoni sono nel modulo `r36.sound`, utilizzabile da tutte le app:
`sound.play("chirp")`, `sound.play(sound.babble("happy"))` oppure suoni tuoi con
`sound.synth([(frequenza_inizio, frequenza_fine, durata, "sine"), ...])`.

## Chiavetta USB (sperimentale)

Avvia **Chiavetta USB** da Ports e collega la console al PC col cavo USB-C
**dati** sulla porta **OTG**. Windows vede la partizione dei giochi come una
chiavetta e ci puoi copiare dentro i file (giochi, app nuove per `tool/apps/`, ...).
Per finire clicca **Espelli** su Windows, oppure tieni premuto un tasto della
console per 2 secondi: la partizione viene ricontrollata, rimontata e
EmulationStation riparte.

Cosa fa lo script, per sicurezza: ferma EmulationStation, **smonta** la
partizione (non va mai condivisa mentre e' in uso, si rovinerebbe), la espone
via USB gadget, poi rimette tutto com'era. Se qualcosa non va si ferma prima
di toccare i dati e lo scrive sullo schermo. Il log e' in `/tmp/r36-chiavetta.log`.

**Funziona solo se il kernel del sistema ha la modalita' USB "device" sulla
porta OTG.** Molte immagini per R36S la tengono solo in modalita' "host" (per
le chiavette WiFi e i gamepad). In quel caso lo script ti dice "nessun UDC" e
non fa niente. Restano due alternative:
- togli la SD e mettila nel PC con un lettore di schede (la partizione giochi
  e' FAT32/exFAT, Windows la vede);
- con il WiFi, ArkOS (e di solito anche dArkOS) ha *Enable Remote Services* nelle Opzioni: in Esplora risorse
  scrivi `\\<indirizzo-IP-della-console>` e vedi le cartelle in rete.

## Compatibilita'

- **pygame 2** (dArkOS, ROCKNIX, PC) e **pygame 1.9** (ArkOS vecchio basato su
  Ubuntu 19.10): con pygame 1.9 gli angoli dei riquadri vengono dritti, il resto
  e' uguale.
- **Schermi diversi**: tutto viene disegnato a 640x480 e poi scalato, quindi
  va bene anche sui cloni con schermi 720x720 o 480x320 (con le bande nere).
- **Audio**: se manca la scheda audio o il driver, le app restano mute ma funzionano.
- `Tool.sh` funziona da utente con `sudo` (ArkOS e dArkOS) o da root (ROCKNIX e
  AmberELEC). Prova in ordine i driver video `kmsdrm`, automatico e `fbcon`.

## App per stupire gli amici

| App | Cosa fa | Trucco segreto |
|---|---|---|
| **Rilevatore** | radar di movimento da film: fascio che gira, presenze che si avvicinano, bip sempre piu' veloci, allarme e "CONTATTO!" | tieni **L1**: arrivano piu' in fretta. Tieni **R1**: spariscono |
| **Lovometro** | scrivi due nomi e il cuore si riempie con la percentuale. Le stesse due persone hanno sempre lo stesso risultato | tieni **L1** mentre confermi il secondo nome: 100% |
| **Macchina della verita'** | l'amico tiene premuto A mentre risponde, il grafico impazzisce, poi arriva il verdetto | al rilascio tieni **L1** per VERITA' o **R1** per BUGIA |
| **Scanner** | pollice sullo schermo, tieni premuto A: impronta, linea di scansione, percentuale e frase. Misure: simpatia, pigrizia, fame, contenuto di pizza, nerd, russare, fortuna | a fine scansione tieni **L1** per 70-100%, **R1** per 0-5% |
| **Palla magica** | fai una domanda, premi A, la palla trema e risponde | - |

Sono tutte per gioco: niente sensori veri, e' teatro.
