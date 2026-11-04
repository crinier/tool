"""Palla magica (senza palla): fai una domanda, premi A, arriva la risposta."""
import math
import random

import r36
from r36 import sound

NAME = "Palla magica"
DESCRIPTION = "Fai una domanda, premi A"
W, H = r36.W, r36.H

ANSWERS = [
    "Si'!", "Assolutamente si'", "Senza dubbio", "Puoi contarci", "Le stelle dicono si'",
    "Molto probabile", "Direi di si'", "Ci sono buone speranze",
    "Riprova piu' tardi", "Non te lo posso dire ora", "Concentrati e richiedi",
    "Meglio non dirtelo...", "Non ci contare", "La risposta e' no", "Molto improbabile",
    "Neanche per sogno", "Chiedi alla mamma", "Solo se offri la pizza",
]


def wrap(ctx, text, size, width):
    lines, cur = [], ""
    for w in text.split():
        if ctx.font(size, True).size((cur + " " + w).strip())[0] > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + [cur]


def run(ctx):
    answer, think, t, since = None, 0.0, 0.0, 0.0
    rumble = sound.synth([(90, 70, 0.6, "noise")], 0.25)
    ctx.input.flush()
    while True:
        for a in ctx.input.poll():
            if a == "B":
                return
            if a == "A" and think <= 0:
                think, answer = 1.2, None
                sound.play(rumble)
        t += 1 / 30
        if think > 0:
            think -= 1 / 30
            if think <= 0:
                answer, since = random.choice(ANSWERS), 0.0
                sound.play("chirp")
        since += 1 / 30
        ctx.surf.fill((10, 6, 24))
        if answer:
            k = min(1.0, since / 0.6)                      # appare piano piano
            col = tuple(int(c * k) for c in (230, 225, 255))
            lines = wrap(ctx, answer, 64, W - 80)
            y0 = H // 2 - 40 - (len(lines) - 1) * 34
            for i, ln in enumerate(lines):
                ctx.text(ln, W // 2, y0 + i * 68, 64, col, align="center", bold=True)
        elif think > 0:
            dots = "." * (1 + int(t * 6) % 3)
            ox = int(math.sin(t * 50) * 6)
            ctx.text(dots, W // 2 + ox, H // 2 - 70, 120, (150, 140, 230), align="center", bold=True)
        else:
            ctx.text("?", W // 2, H // 2 - 110, 160, (90, 80, 160), align="center", bold=True)
        ctx.text("Pensa a una domanda e premi A", W // 2, 410, 28, (180, 170, 230), align="center")
        ctx.text("B esci", W // 2, 448, 20, (100, 90, 140), align="center")
        ctx.flip()
