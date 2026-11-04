"""Macchina della verita' (per gioco).

Fai una domanda a un amico, lui tiene premuto A mentre risponde: il grafico
impazzisce e dopo qualche secondo arriva il verdetto.
Trucco segreto per chi tiene la console: tenendo premuto L1 al rilascio esce
VERITA', tenendo R1 esce BUGIA. Senza niente e' a caso.
"""
import math
import random

import pygame

import r36
from r36 import sound

NAME = "Macchina della verita'"
DESCRIPTION = "Tieni premuto A e rispondi... (c'e' un trucco)"
W, H = r36.W, r36.H
GREEN = (80, 230, 120)
RED = (255, 70, 60)


def run(ctx):
    trace = [0.0] * 300
    phase = "wait"       # wait / measure / verdict
    t = 0.0
    measure = 0.0
    verdict = None
    beat_at = 0.0
    beep = sound.synth([(1000, 1000, 0.03, "sine")], 0.15)
    ctx.input.flush()
    while True:
        for a in ctx.input.poll():
            if a == "B":
                return
            if a == "A" and phase in ("wait", "verdict"):
                phase, measure, verdict = "measure", 0.0, None
        held = ctx.input.held
        t += 1 / 30
        if phase == "measure":
            measure += 1 / 30
            if "A" not in held or measure > 6:
                if measure < 1.5:
                    phase = "wait"
                else:
                    if "L1" in held:
                        verdict = True
                    elif "R1" in held:
                        verdict = False
                    else:
                        verdict = random.random() < 0.5
                    phase = "verdict"
                    sound.play("win" if verdict else "angry")
        # il grafico: calmo in attesa, agitato durante la misura
        agit = 0.08 if phase != "measure" else 0.35 + 0.5 * math.sin(measure * 1.3) ** 2
        v = math.sin(t * 7) * 0.3 * agit + random.uniform(-1, 1) * agit
        trace = trace[1:] + [max(-1.0, min(1.0, v))]
        if phase == "measure" and t >= beat_at:
            sound.play(beep)
            beat_at = t + 0.35 - min(0.2, measure * 0.04)

        s = ctx.surf
        s.fill((4, 10, 6))
        for x in range(20, W - 20, 40):
            pygame.draw.line(s, (12, 40, 20), (x, 80), (x, 330))
        for y in range(80, 331, 25):
            pygame.draw.line(s, (12, 40, 20), (20, y), (W - 20, y))
        col = GREEN if phase != "verdict" else (GREEN if verdict else RED)
        pts = [(20 + i * (W - 40) / len(trace), 205 - v * 115) for i, v in enumerate(trace)]
        pygame.draw.lines(s, col, False, pts, 3)
        ctx.text("POLIGRAFO", 20, 18, 34, GREEN, bold=True)
        bpm = 70 + (int(40 * agit) if phase == "measure" else 0) + random.randint(-2, 2)
        ctx.text("BPM %d" % bpm, W - 20, 22, 30, GREEN, align="right")
        if phase == "wait":
            ctx.text("Fai la domanda. Tieni premuto A mentre risponde.", W // 2, 360, 26, GREEN, align="center")
        elif phase == "measure":
            dots = "." * (1 + int(t * 3) % 3)
            ctx.text("ANALISI IN CORSO" + dots, W // 2, 355, 40, GREEN, align="center", bold=True)
        else:
            ctx.text("VERITA'" if verdict else "BUGIA!", W // 2, 345, 84, col, align="center", bold=True)
            ctx.text("A nuova domanda", W // 2, 430, 22, (60, 120, 80), align="center")
        ctx.text("B esci", W - 20, H - 26, 20, (60, 120, 80), align="right")
        ctx.flip()
