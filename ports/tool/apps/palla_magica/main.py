"""Palla magica: fai una domanda, premi A e la palla risponde."""
import math
import random

import pygame

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


def run(ctx):
    answer = None
    shake = 0.0
    t = 0.0
    rumble = sound.synth([(90, 70, 0.6, "noise")], 0.25)
    ctx.input.flush()
    while True:
        for a in ctx.input.poll():
            if a == "B":
                return
            if a == "A" and shake <= 0:
                shake, answer = 1.2, None
                sound.play(rumble)
        t += 1 / 30
        if shake > 0:
            shake -= 1 / 30
            if shake <= 0:
                answer = random.choice(ANSWERS)
                sound.play("chirp")
        s = ctx.surf
        s.fill((10, 6, 24))
        ox = math.sin(t * 50) * 14 * max(0.0, shake)
        cx, cy = W // 2 + int(ox), 220
        pygame.draw.circle(s, (20, 20, 30), (cx, cy), 170)
        pygame.draw.circle(s, (45, 45, 60), (cx - 50, cy - 60), 40)
        pygame.draw.circle(s, (30, 40, 140), (cx, cy), 82)
        tri = [(cx, cy - 70), (cx - 62, cy + 40), (cx + 62, cy + 40)]
        if answer:
            pygame.draw.polygon(s, (60, 80, 220), tri)
            words, lines, cur = answer.split(), [], ""
            for w in words:
                if ctx.font(24, True).size(cur + " " + w)[0] > 100 and cur:
                    lines.append(cur)
                    cur = w
                else:
                    cur = (cur + " " + w).strip()
            lines.append(cur)
            for i, ln in enumerate(lines):
                ctx.text(ln, cx, cy - 18 + i * 22 - (len(lines) - 1) * 8, 24, (255, 255, 255),
                         align="center", bold=True)
        else:
            ctx.text("8" if shake <= 0 else "?", cx, cy - 34, 80, (255, 255, 255), align="center", bold=True)
        ctx.text("Pensa a una domanda e premi A", W // 2, 410, 28, (180, 170, 230), align="center")
        ctx.text("B esci", W // 2, 448, 20, (100, 90, 140), align="center")
        ctx.flip()
