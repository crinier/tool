"""Lovometro: scrivi due nomi e scopri l'affinita'.

Il risultato dipende solo dai nomi: le stesse due persone hanno sempre la
stessa percentuale (cosi' sembra "scientifico").
Trucco segreto: tieni premuto L1 mentre confermi il secondo nome e viene 100%.
"""
import math
import random
import zlib

import pygame

import r36
from r36 import sound

NAME = "Lovometro"
DESCRIPTION = "Due nomi, quanta affinita' c'e'?"
W, H = r36.W, r36.H
PINK = (255, 90, 140)

MESSAGES = [
    (95, "Anime gemelle. Prenotate il ristorante!"),
    (80, "Scintille vere! Chiedile un caffe'."),
    (65, "Bella intesa, c'e' del potenziale."),
    (50, "Si puo' fare... con un po' di impegno."),
    (30, "Mmm, meglio come amici?"),
    (0, "Il Lovometro ha qualche dubbio..."),
]


def score(a, b):
    key = "|".join(sorted([a.strip().upper(), b.strip().upper()]))
    return 15 + zlib.crc32(key.encode()) % 86   # 15..100


def heart(surf, x, y, s, color, fill=1.0):
    pts = []
    for i in range(60):
        t = i / 60 * 2 * math.pi
        hx = 16 * math.sin(t) ** 3
        hy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x + hx * s, y - hy * s))
    pygame.draw.polygon(surf, (60, 20, 35), pts)
    if fill > 0:
        clip = pygame.Rect(0, int(y + 17 * s - fill * 34 * s), W, H)
        old = surf.get_clip()
        surf.set_clip(clip)
        pygame.draw.polygon(surf, color, pts)
        surf.set_clip(old)
    pygame.draw.polygon(surf, color, pts, 4)


def run(ctx):
    a = b = ""
    while True:
        a = r36.keyboard(ctx, "Primo nome", a)
        if not a:
            return
        b = r36.keyboard(ctx, "Secondo nome", b)
        if not b:
            continue
        forced = "L1" in ctx.input.held
        target = 100 if forced else score(a, b)
        # animazione: il cuore si riempie, il numero sale "indeciso"
        shown, t = 0.0, 0.0
        sounds = [sound.synth([(400 + i * 12, 400 + i * 12, 0.03, "sine")], 0.2) for i in range(0, 101, 5)]
        last_step = -1
        ctx.input.flush()
        done = False
        while True:
            acts = ctx.input.poll()
            if done and any(x in ("A", "B", "START") for x in acts):
                break
            t += 1 / 30
            if not done:
                # sale, poi oscilla un po' prima di fermarsi
                shown = min(target, t / 3.0 * target + math.sin(t * 9) * 6 * (1 - t / 3.0))
                shown = max(0.0, shown)
                step = int(shown) // 5
                if step != last_step:
                    sound.play(sounds[min(step, 20)])
                    last_step = step
                if t >= 3.0:
                    shown, done = target, True
                    sound.play("win" if target >= 65 else "love" if target >= 40 else "sad")
            ctx.surf.fill((20, 8, 16))
            beat = 1 + 0.06 * math.sin(t * 10) if done and target >= 65 else 1
            heart(ctx.surf, W // 2, 200, 7.5 * beat, PINK, shown / 100)
            ctx.text("%s  +  %s" % (a, b), W // 2, 24, 36, (255, 200, 220), align="center", bold=True)
            ctx.text("%d%%" % shown, W // 2, 170, 72, (255, 255, 255), align="center", bold=True)
            if done:
                msg = next(m for lim, m in MESSAGES if target >= lim)
                ctx.text(msg, W // 2, 352, 30, (255, 200, 220), align="center", bold=True)
                ctx.text("A riprova", W // 2, 440, 22, (150, 100, 120), align="center")
                if target >= 80 and random.random() < 0.3:
                    x = random.randint(40, W - 40)
                    pygame.draw.circle(ctx.surf, PINK, (x, random.randint(60, 140)), 3)
            ctx.flip()
