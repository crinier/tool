"""Rilevatore di movimento da film di fantascienza (finto!).

Un radar circolare color ambra: il fascio gira, compaiono "presenze" che si
avvicinano piano piano, i bip diventano piu' acuti e veloci. Quando una
presenza arriva troppo vicino... allarme.

Trucco per gli scherzi: tieni premuto L1 per far avvicinare tutto piu' in fretta,
R1 per farlo sparire.
"""
import math
import random

import pygame

import r36
from r36 import sound

NAME = "Rilevatore"
DESCRIPTION = "Radar di movimento da film (finto): bip, presenze, allarme"
W, H = r36.W, r36.H
AMBER = (255, 170, 40)
DARK = (40, 26, 6)
MID = (120, 80, 20)
CX, CY, R = W // 2, 250, 190


class Blip:
    def __init__(self, range_m):
        self.a = random.uniform(0, 2 * math.pi)
        self.d = random.uniform(0.6, 1.0) * range_m
        self.speed = random.uniform(0.25, 0.7)   # metri al secondo
        self.wobble = random.uniform(0, 10)
        self.seen = 0.0                          # luminosita' (si accende al passaggio del fascio)


def run(ctx):
    rng = 20.0
    blips = []
    sweep = 0.0
    t = 0.0
    alarm = 0.0
    next_spawn = 2.0
    flash = 0.0
    pings = {}
    for f in (700, 900, 1150, 1500):
        pings[f] = sound.synth([(f, f * 0.98, 0.09, "sine")], 0.3)
    alarm_snd = sound.synth([(880, 880, 0.12, "square"), (0, 0, 0.04, "sine"), (880, 880, 0.12, "square")], 0.22)
    jump_snd = sound.synth([(140, 60, 0.6, "noise")], 0.5)
    ctx.input.flush()
    clock_dt = 1 / 30
    while True:
        for a in ctx.input.poll():
            if a == "B":
                return
            if a == "UP":
                rng = min(50.0, rng + 5)
            if a == "DOWN":
                rng = max(10.0, rng - 5)
            if a == "A":
                blips.append(Blip(rng))
        held = ctx.input.held
        dt = clock_dt
        t += dt
        prev = sweep
        sweep = (sweep + dt * 2.4) % (2 * math.pi)

        if t >= next_spawn and len(blips) < 4 and "R1" not in held:
            blips.append(Blip(rng))
            next_spawn = t + random.uniform(4, 9)
        if "R1" in held:
            blips.clear()

        nearest = None
        for b in blips:
            b.d -= b.speed * dt * (4 if "L1" in held else 1)
            b.a += math.sin(t * 0.8 + b.wobble) * 0.004
            b.seen = max(0.0, b.seen - dt * 0.6)
            # il fascio "illumina" la presenza quando ci passa sopra
            da = (b.a - prev) % (2 * math.pi)
            if da <= (sweep - prev) % (2 * math.pi) + 1e-6:
                b.seen = 1.0
                k = max(0.0, min(1.0, 1 - b.d / rng))
                sound.play(pings[[700, 900, 1150, 1500][min(3, int(k * 4))]])
            if nearest is None or b.d < nearest.d:
                nearest = b
        if nearest and nearest.d < 1.5:
            flash = 1.0
            sound.play(jump_snd)
            blips.clear()
            next_spawn = t + 5
        if nearest and nearest.d < 5 and t >= alarm:
            sound.play(alarm_snd)
            alarm = t + 0.25 + nearest.d * 0.12
        flash = max(0.0, flash - dt * 1.5)

        # ---- disegno
        s = ctx.surf
        s.fill((0, 0, 0))
        for i in range(1, 5):
            pygame.draw.circle(s, MID if i == 4 else DARK, (CX, CY), R * i // 4, 2)
            ctx.text("%d" % (rng * i / 4), CX + 4, CY - R * i // 4 + 2, 18, MID)
        for i in range(12):
            a = i * math.pi / 6
            pygame.draw.line(s, DARK, (CX, CY), (CX + math.cos(a) * R, CY + math.sin(a) * R), 1)
        # scia del fascio
        for i in range(24):
            a = sweep - i * 0.035
            col = tuple(int(c * (1 - i / 24) * 0.55) for c in AMBER)
            pygame.draw.line(s, col, (CX, CY), (CX + math.cos(a) * R, CY + math.sin(a) * R), 3)
        pygame.draw.line(s, AMBER, (CX, CY), (CX + math.cos(sweep) * R, CY + math.sin(sweep) * R), 3)
        for b in blips:
            if b.seen > 0.02 and b.d < rng:
                rr = b.d / rng * R
                x, y = CX + math.cos(b.a) * rr, CY + math.sin(b.a) * rr
                col = tuple(int(c * b.seen) for c in AMBER)
                pygame.draw.circle(s, col, (int(x), int(y)), int(7 + 5 * b.seen))
                pygame.draw.circle(s, col, (int(x), int(y)), int(14 + 8 * (1 - b.seen)), 1)
        pygame.draw.circle(s, AMBER, (CX, CY), 5)

        # pannello
        ctx.text("RILEVATORE DI MOVIMENTO", 16, 12, 26, AMBER, bold=True)
        ctx.text("PORTATA %d m" % rng, W - 16, 12, 24, MID, align="right")
        if nearest and nearest.d < rng:
            txt = "%5.1f m" % nearest.d
            col = AMBER if nearest.d > 5 or int(t * 6) % 2 else (255, 60, 30)
            ctx.text(txt, W - 16, 40, 48, col, align="right", bold=True)
            ctx.text("PRESENZE: %d" % len([b for b in blips if b.d < rng]), 16, 44, 24, AMBER)
        else:
            ctx.text("NESSUN MOVIMENTO", 16, 44, 24, MID)
        ctx.text("A nuova presenza   SU/GIU portata   B esci", W // 2, H - 26, 20, MID, align="center")
        if flash > 0:
            ov = pygame.Surface((W, H))
            ov.fill((255, 60, 20))
            ov.set_alpha(int(220 * flash))
            s.blit(ov, (0, 0))
            if flash > 0.5:
                ctx.text("CONTATTO!", W // 2, H // 2 - 40, 90, (255, 255, 255), align="center", bold=True)
        ctx.flip()
