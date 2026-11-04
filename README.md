# R36 Tool: programmi fatti da noi sulla R36S (clone)

Un menu che parte dalla sezione **Ports** della console e lancia programmini
in Python + pygame: **Amichetto** (Bobo), **Areometro**, **Cronometro**, **Configura tasti**, piu' un
modello per scriverne di nuovi.

```
ports/
  Tool.sh                 <- avviatore (va in roms/ports/)
  tool/
    launcher.py           <- menu principale
    r36/                  <- mini-libreria: schermo, tasti, menu, moduli
    apps/
      areometro/          <- correzione temperatura, ABV, SG/Plato/Brix
      amichetto/          <- Bobo, il piccolo amico virtuale
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

Con la SD nel PC, copia `ports/Tool.sh` **e** la cartella `ports/tool/` dentro
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

Un piccolo amico verde col germoglio in testa. Ha tre bisogni: **fame**, **energia** e **allegria**.

- **Mangia**: mela, biscotto o pizza. Se e' pieno rifiuta e sbuffa.
- **Gioca**: indovina in quale pacchetto ha nascosto il biscotto (SINISTRA o DESTRA).
- **Coccole**: cuoricini! Fanno passare anche il broncio.
- **Luce**: lo metti a dormire o lo svegli. Se lo svegli quando e' stanco si arrabbia.
- **X = stuzzica**: tre volte di fila e diventa rosso e sbuffa fumo.

Quando chiudi l'app lo stato viene salvato in `bobo.json`. Il tempo passa
anche mentre sei via, ma piu' piano, e Bobo non muore mai.
