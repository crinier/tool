"""MODELLO per una nuova app.

1. Copia questa cartella: apps/_modello -> apps/mia_app  (senza "_" davanti)
2. Cambia NAME e DESCRIPTION
3. Scrivi la tua logica in run(ctx)

Cose utili:
  ctx.input.poll()        -> lista azioni premute: "UP","DOWN","LEFT","RIGHT",
                             "A","B","X","Y","L1","R1","L2","R2","SELECT","START"
  ctx.header(titolo, aiuto)  pulisce lo schermo e disegna la barra in alto
  ctx.text(s, x, y, size, color, align="left"|"center"|"right")
  ctx.surf                -> superficie pygame 640x480 per disegnare quello che vuoi
  ctx.flip()              -> mostra il frame (chiamalo una volta per ciclo)
  r36.menu(ctx, titolo, voci)          -> indice scelto o None
  r36.form(ctx, titolo, campi, calcola)-> campi numerici + risultati live
  r36.message(ctx, titolo, testo)
SELECT+START chiude sempre l'app.
"""
import r36

NAME = "Mia app"
DESCRIPTION = "Descrizione breve"


def run(ctx):
    count = 0
    ctx.input.flush()
    while True:
        for a in ctx.input.poll():
            if a == "A":
                count += 1
            elif a == "B":
                return
        ctx.header(NAME, "A +1   B esci")
        ctx.text(str(count), r36.W // 2, 180, 120, r36.ACCENT, align="center")
        ctx.flip()
