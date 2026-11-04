"""Cielo stellato: il suo nome diventa una costellazione.

Lei scrive il suo nome, il cielo si spegne, le stelle si accendono una alla
volta (ognuna con una nota) e si collegano disegnando le lettere del nome.
Poi una stella cadente e il messaggio.

A rivedi, X nuovo nome, Y cambia messaggio, B esci.
"""
import math
import random

import pygame

import r36
from r36 import sound

NAME = "Cielo stellato"
DESCRIPTION = "Il suo nome scritto con le stelle"
W, H = r36.W, r36.H

MESSAGES = [
    "Anche le stelle conoscono il tuo nome",
    "Il cielo stanotte brilla per te",
    "Fra tutte le stelle, la piu' bella sei tu",
    "Esprimi un desiderio...",
]
SCALE = [262, 294, 330, 392, 440]          # pentatonica: suona sempre bene


def fit_font(ctx, name):
    size = 230
    while size > 60 and sum(ctx.font(size, True).size(ch)[0] for ch in name) > W - 50:
        size -= 10
    return ctx.font(size, True)


def letter_points(ctx, name, per_letter=16):
    """Punti-stella sui tratti di ogni lettera + linee corte (albero minimo) per lettera."""
    font = fit_font(ctx, name)
    total_w = sum(font.size(ch)[0] for ch in name)
    x = (W - total_w) // 2
    y = 190 - font.get_height() // 2
    stars, edges = [], []
    for ch in name:
        w = font.size(ch)[0]
        if ch.strip():
            img = font.render(ch, True, (255, 255, 255))
            mask = pygame.mask.from_surface(img)
            step = 5
            cand = [(px, py) for px in range(1, img.get_width(), step)
                    for py in range(1, img.get_height(), step) if mask.get_at((px, py))]
            if cand:
                pick = [min(cand, key=lambda p: p[0] + p[1])]
                while len(pick) < min(per_letter, len(cand)):
                    pick.append(max(cand, key=lambda c: min((c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 for p in pick)))
                pts = [(x + px, y + py) for px, py in pick]
                # distanza tipica fra stelle vicine: oltre il doppio non si collega
                near = sorted(min((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 for b in pts if b is not a) for a in pts)
                limit = near[len(near) // 2] * 4.5
                base = len(stars)
                stars += pts
                inside, rest = [0], list(range(1, len(pts)))
                while rest:
                    a, b = min(((i, j) for i in inside for j in rest),
                               key=lambda e: (pts[e[0]][0] - pts[e[1]][0]) ** 2 + (pts[e[0]][1] - pts[e[1]][1]) ** 2)
                    d = (pts[a][0] - pts[b][0]) ** 2 + (pts[a][1] - pts[b][1]) ** 2
                    if d <= limit:
                        edges.append((base + a, base + b))
                    inside.append(b)
                    rest.remove(b)
        x += w
    ghost = pygame.Surface((W, H), pygame.SRCALPHA)
    gx = (W - total_w) // 2
    for ch in name:
        ghost.blit(font.render(ch, True, (90, 110, 200)), (gx, y))
        gx += font.size(ch)[0]
    return stars, edges, ghost


def run(ctx):
    name = r36.keyboard(ctx, "Come ti chiami?", "", 10)
    if not name:
        return
    msg_i = 0
    notes = [sound.synth([(f * m, f * m, 0.35, "sine")], 0.22) for m in (1, 2) for f in SCALE]
    sky = [(random.randint(0, W), random.randint(0, H), random.uniform(0, 6.3), random.random())
           for _ in range(140)]
    bg = pygame.Surface((W, H))
    for yy in range(H):
        k = yy / H
        pygame.draw.line(bg, (int(4 + 10 * k), int(6 + 8 * k), int(22 + 30 * k)), (0, yy), (W, yy))

    while True:
        stars, edges, ghost = letter_points(ctx, name.strip().upper())
        t, shown, next_star = 0.0, 0, 0.6
        shooting = None
        ctx.input.flush()
        restart = False
        while not restart:
            for a in ctx.input.poll():
                if a == "B":
                    return
                if a == "A":
                    restart = True
                if a == "X":
                    n = r36.keyboard(ctx, "Come ti chiami?", name, 10)
                    if n:
                        name = n
                    restart = True
                if a == "Y":
                    msg_i = (msg_i + 1) % len(MESSAGES)
            dt = 1 / 30
            t += dt
            if shown < len(stars) and t >= next_star:
                sound.play(notes[min(len(notes) - 1, shown * len(notes) // max(1, len(stars)))])
                shown += 1
                next_star = t + max(0.07, 2.6 / max(1, len(stars)))
            done_at = 0.6 + len(stars) * max(0.07, 2.6 / max(1, len(stars))) + 0.5
            if t > done_at + 1.2 and shooting is None:
                shooting = [W + 20, 40.0, t]
                sound.play("love")

            s = ctx.surf
            s.blit(bg, (0, 0))
            for x, y, ph, b in sky:
                v = int(60 + 70 * b * (0.6 + 0.4 * math.sin(t * 2 + ph)))
                s.set_at((x, y), (v, v, min(255, v + 30)))
            # il nome compare in trasparenza dietro le stelle
            if t > done_at:
                ghost.set_alpha(int(70 * min(1.0, (t - done_at) / 2.0)))
                s.blit(ghost, (0, 0))
            # linee della costellazione
            for i, j in edges:
                if i < shown and j < shown:
                    pygame.draw.aaline(s, (110, 130, 200), stars[i], stars[j])
            # stelle del nome
            for i in range(shown):
                x, y = stars[i]
                tw = 0.75 + 0.25 * math.sin(t * 3 + i)
                pygame.draw.circle(s, (60, 70, 140), (int(x), int(y)), int(7 * tw))
                pygame.draw.circle(s, (255, 250, 220), (int(x), int(y)), 3)
                if t > done_at:
                    pygame.draw.line(s, (200, 210, 255), (x - 6 * tw, y), (x + 6 * tw, y))
                    pygame.draw.line(s, (200, 210, 255), (x, y - 6 * tw), (x, y + 6 * tw))
            # stella cadente
            if shooting:
                shooting[0] -= 520 * dt
                shooting[1] += 150 * dt
                sx, sy = shooting[0], shooting[1]
                for k in range(16):
                    c = int(255 * (1 - k / 16))
                    pygame.draw.circle(s, (c, c, min(255, c + 20)), (int(sx + k * 9), int(sy - k * 2.6)), max(1, 3 - k // 6))
            # messaggio
            if t > done_at:
                k = min(1.0, (t - done_at) / 1.5)
                col = tuple(int(c * k) for c in (240, 225, 255))
                ctx.text(MESSAGES[msg_i] + ",", W // 2, 350, 30, col, align="center", bold=True)
                ctx.text(name.strip().title(), W // 2, 388, 46, tuple(int(c * k) for c in (255, 200, 120)),
                         align="center", bold=True)
            ctx.text("A rivedi  X nome  Y messaggio  B esci", W // 2, H - 22, 18, (60, 66, 100), align="center")
            ctx.flip()
