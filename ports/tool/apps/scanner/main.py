"""Scanner corporeo (finto!): l'amico appoggia il pollice, tiene premuto A,
lo scanner "analizza" e da' una percentuale comica.

Trucco segreto per chi tiene la console, da tenere premuto quando finisce la scansione:
    L1 -> risultato ALTO (70-100%)
    R1 -> risultato a ZERO (0-5%)
    niente -> a caso
"""
import math
import random

import pygame

import r36
from r36 import sound

NAME = "Scanner"
DESCRIPTION = "Pollice sullo schermo, analisi comica (truccabile)"
W, H = r36.W, r36.H
CYAN = (60, 230, 255)
DIM = (20, 70, 90)

TESTS = [
    ("Livello di simpatia", ["Antipatico ufficiale", "Simpatico a giorni alterni",
                             "Simpatico!", "Simpatia radioattiva!"]),
    ("Livello di pigrizia", ["Iperattivo", "Normale", "Divano-dipendente",
                             "Fuso col divano"]),
    ("Fame in corso", ["Sazio", "Uno spuntino ci sta", "Fame seria",
                       "Mangerebbe il tavolo"]),
    ("Contenuto di pizza", ["Niente pizza", "Una fetta", "Mezza margherita",
                            "E' fatto di pizza"]),
    ("Livello nerd", ["Zero nerd", "Gioca ogni tanto", "Nerd certificato",
                      "Boss finale dei nerd"]),
    ("Potenza del russare", ["Silenzioso", "Fischietto", "Trattore",
                             "Terremoto notturno"]),
    ("Livello di fortuna", ["Gatto nero", "Nella media", "Fortunello",
                            "Gratta e vinci subito!"]),
]


def fingerprint(surf, cx, cy, color, k=1.0):
    for i in range(9):
        r = 14 + i * 11
        start = 0.5 + (i % 3) * 0.25
        pygame.draw.arc(surf, color, (cx - r, cy - r * 1.25, r * 2, r * 2.5),
                        start, math.pi * 2 - start + 0.6 * math.sin(i), 3)


def scan(ctx, title, comments):
    phase, prog, t, result = "wait", 0.0, 0.0, 0
    hum = sound.synth([(300, 360, 0.25, "tri")], 0.12)
    next_hum = 0.0
    ctx.input.flush()
    while True:
        for a in ctx.input.poll():
            if a == "B":
                return
            if a == "A" and phase == "done":
                phase, prog = "wait", 0.0
        held = ctx.input.held
        t += 1 / 30
        if phase == "wait" and "A" in held:
            phase = "scan"
        if phase == "scan":
            if "A" not in held:
                phase, prog = "wait", 0.0
            else:
                prog += 1 / 30 / 3.5
                if t >= next_hum:
                    sound.play(hum)
                    next_hum = t + 0.25
                if prog >= 1:
                    if "L1" in held:
                        result = random.randint(70, 100)
                    elif "R1" in held:
                        result = random.randint(0, 5)
                    else:
                        result = random.randint(0, 100)
                    phase, shown = "done", 0.0
                    sound.play("win" if result >= 50 else "lose")
        s = ctx.surf
        s.fill((0, 6, 10))
        ctx.text(title.upper(), W // 2, 14, 32, CYAN, align="center", bold=True)
        cx, cy = W // 2, 200
        pygame.draw.rect(s, DIM, (cx - 110, cy - 130, 220, 260), 3, border_radius=30)
        col = CYAN if phase == "scan" else DIM
        fingerprint(s, cx, cy, col)
        if phase == "scan":
            y = cy - 125 + (math.sin(t * 4) * 0.5 + 0.5) * 250
            pygame.draw.line(s, (255, 255, 255), (cx - 105, y), (cx + 105, y), 3)
            pygame.draw.line(s, CYAN, (cx - 105, y + 4), (cx + 105, y + 4), 2)
        pygame.draw.rect(s, DIM, (120, 350, W - 240, 18), border_radius=9)
        pygame.draw.rect(s, CYAN, (120, 350, int((W - 240) * min(1, prog)), 18), border_radius=9)
        if phase == "wait":
            ctx.text("Appoggia il pollice e tieni premuto A", W // 2, 385, 26, CYAN, align="center")
        elif phase == "scan":
            ctx.text("SCANSIONE %d%%" % (prog * 100), W // 2, 385, 28, CYAN, align="center", bold=True)
        else:
            shown = min(result, shown + 3)
            ctx.text("%d%%" % shown, W // 2, 160, 90, (255, 255, 255), align="center", bold=True)
            if shown >= result:
                c = comments[min(3, result * 4 // 101)]
                ctx.text(c, W // 2, 385, 32, (255, 255, 255), align="center", bold=True)
            ctx.text("A nuova scansione   B indietro", W // 2, 440, 20, DIM, align="center")
        ctx.flip()


def run(ctx):
    i = 0
    while True:
        i = r36.menu(ctx, NAME, [(n, "Analisi scientificissima") for n, _ in TESTS], index=i)
        if i is None:
            return
        scan(ctx, *TESTS[i])
