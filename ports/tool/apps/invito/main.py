"""Invito: Bobo fa la domanda al posto tuo, con una grafica curata.

Idee prese dai consigli piu' diffusi su come invitare qualcuno:
  - invito preciso e leggero (un caffe', 15 minuti) invece di un vago "usciamo?"
  - un po' di umorismo (hai costruito un robot per chiederglielo!)
  - via d'uscita facile e nessuna pressione: se dice "un'altra volta", Bobo la ringrazia
  - se dice si', le mostra il tuo numero: decide lei se scriverti

Nel titolo: Y tuo nome, X cambia domanda, START tuo numero (facoltativo).
"""
import importlib.util
import json
import math
import os
import random

import pygame

import r36
from r36 import sound

NAME = "Invito"
DESCRIPTION = "Bobo fa la domanda al posto tuo"
W, H = r36.W, r36.H
HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(HERE, "invito.json")

_spec = importlib.util.spec_from_file_location(
    "bobo_occhi", os.path.join(os.path.dirname(HERE), "amichetto", "main.py"))
bobo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bobo)

DOMANDE = [
    ("Ti va un caffe' con lui?", "Solo 15 minuti, quando stacchi."),
    ("Ti va un gelato insieme?", "Uno piccolo, offre lui."),
    ("Un aperitivo venerdi'?", "Due chiacchiere, niente di impegnativo."),
    ("Una passeggiata un giorno di questi?", "Lui porta i biscotti, io il buonumore."),
]
SI, NO = "Si', volentieri", "Magari un'altra volta"

PALETTES = [((28, 10, 52), (110, 30, 90)), ((12, 18, 60), (150, 50, 110))]
PINK = (255, 120, 180)
GOLD = (255, 205, 130)


def load():
    try:
        with open(SAVE) as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    d.setdefault("nome", "")
    d.setdefault("domanda", 0)
    d.setdefault("numero", "")
    d["domanda"] %= len(DOMANDE)
    return d


def save(cfg):
    try:
        with open(SAVE, "w") as f:
            json.dump(cfg, f)
    except OSError:
        pass


def gradient(top, bottom):
    s = pygame.Surface((W, H))
    for y in range(H):
        k = y / (H - 1)
        pygame.draw.line(s, tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)), (0, y), (W, y))
    return s


def soft_circle(r, color, power=0.28):
    """Luce sfocata su nero, da sommare allo sfondo (BLEND_ADD): piu' chiara al centro."""
    s = pygame.Surface((r * 2, r * 2))
    s.fill((0, 0, 0))
    for i in range(r, 0, -1):
        k = power * (1 - i / r) ** 2
        pygame.draw.circle(s, tuple(int(c * k) for c in color), (r, r), i)
    return s


class Look:
    """Tutto quello che fa 'bella grafica': sfondo, luci, scheda, testo luminoso."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.bgs = [gradient(*p) for p in PALETTES]
        self.bokeh_img = [soft_circle(r, c) for r in (22, 36, 54) for c in ((255, 160, 210), (255, 220, 170), (170, 160, 255))]
        self.bokeh = [[random.uniform(0, W), random.uniform(0, H), random.choice(self.bokeh_img),
                       random.uniform(8, 25), random.uniform(0, 6.3)] for _ in range(16)]
        self.card = pygame.Surface((W - 60, 150), pygame.SRCALPHA)
        pygame.draw.rect(self.card, (255, 255, 255, 26), self.card.get_rect(), border_radius=26)
        pygame.draw.rect(self.card, (255, 255, 255, 70), self.card.get_rect(), 2, border_radius=26)
        self.eyes_layer = pygame.Surface((W, 230))
        self.glow_cache = {}

    def background(self, t):
        s = self.ctx.surf
        s.blit(self.bgs[0], (0, 0))
        k = 0.5 + 0.5 * math.sin(t * 0.35)
        self.bgs[1].set_alpha(int(255 * k))
        s.blit(self.bgs[1], (0, 0))
        for b in self.bokeh:
            b[1] -= b[3] / 30
            if b[1] < -60:
                b[0], b[1] = random.uniform(0, W), H + 60
            img = b[2]
            x = b[0] + math.sin(t * 0.6 + b[4]) * 12
            s.blit(img, (x - img.get_width() // 2, b[1] - img.get_height() // 2), special_flags=pygame.BLEND_ADD)

    def eyes(self, eyes, t, expr, bounce=0.0):
        self.eyes_layer.fill((0, 0, 0))
        eyes.draw(self.eyes_layer, W // 2, 120, t, expr, 0, bounce)
        # BLEND_ADD: il nero (palpebre) diventa trasparente, gli occhi brillano sullo sfondo
        self.ctx.surf.blit(self.eyes_layer, (0, 0), special_flags=pygame.BLEND_ADD)

    def glow_text(self, text, cx, y, size, color, glow=(255, 120, 200)):
        if not text.strip():
            return      # una scritta vuota fa crashare smoothscale
        key = (text, size, color, glow)
        if key not in self.glow_cache:
            if len(self.glow_cache) > 80:
                self.glow_cache.clear()
            font = self.ctx.font(size, True)
            img = font.render(text, True, color)
            g8 = font.render(text, True, tuple(c // 9 for c in glow), (0, 0, 0))
            w, h = g8.get_size()
            g = pygame.Surface((w, h))          # il testo con sfondo e' a 8 bit: serve 24 bit
            g.blit(g8, (0, 0))
            # alone che segue la forma delle lettere: copie spostate tutto intorno, sommate
            pad = 8
            halo = pygame.Surface((w + pad * 2, h + pad * 2))
            halo.fill((0, 0, 0))
            for k in range(12):
                a = k * math.pi / 6
                for r in (5,):
                    halo.blit(g, (pad + math.cos(a) * r, pad + math.sin(a) * r), special_flags=pygame.BLEND_ADD)
            hw, hh = halo.get_size()
            blur = pygame.transform.smoothscale(pygame.transform.smoothscale(halo, (max(1, hw // 3), max(1, hh // 3))), (hw, hh))
            shadow = font.render(text, True, (40, 10, 40))
            self.glow_cache[key] = (img, blur, shadow)
        img, blur, shadow = self.glow_cache[key]
        s = self.ctx.surf
        s.blit(blur, (cx - blur.get_width() // 2, y - 8), special_flags=pygame.BLEND_ADD)
        s.blit(shadow, (cx - img.get_width() // 2 + 1, y + 2))
        s.blit(img, (cx - img.get_width() // 2, y))

    def card_text(self, lines, alpha_k=1.0):
        s = self.ctx.surf
        y0 = 238
        s.blit(self.card, (30, y0))
        y = y0 + 75 - len(lines) * 21
        for i, (txt, size, col) in enumerate(lines):
            self.glow_text(txt, W // 2, y, size, col)
            y += size + 8

    def pill(self, x, y, w, h, label, on, t, accent):
        s = self.ctx.surf
        pulse = 1 + (0.04 * math.sin(t * 6) if on else 0)
        ww, hh = int(w * pulse), int(h * pulse)
        rx, ry = x + (w - ww) // 2, y + (h - hh) // 2
        if on:
            glow = pygame.Surface((ww + 40, hh + 40), pygame.SRCALPHA)
            for i, a in ((20, 30), (12, 50), (6, 80)):
                pygame.draw.rect(glow, accent + (a,), (20 - i, 20 - i, ww + 2 * i, hh + 2 * i), border_radius=hh)
            s.blit(glow, (rx - 20, ry - 20))
        body = pygame.Surface((ww, hh), pygame.SRCALPHA)
        for yy in range(hh):
            k = yy / hh
            c = [int(accent[i] * (1.15 - 0.4 * k)) for i in range(3)] if on else [255, 255, 255]
            a = 255 if on else 30
            pygame.draw.line(body, tuple(min(255, v) for v in c) + (a,), (0, yy), (ww, yy))
        mask = pygame.Surface((ww, hh), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, ww, hh), border_radius=hh // 2)
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(body, (rx, ry))
        pygame.draw.rect(s, (255, 255, 255) if on else (200, 180, 220), (rx, ry, ww, hh), 2, border_radius=hh // 2)
        self.ctx.text(label, rx + ww // 2, ry + hh // 2 - 13, 30, (255, 255, 255), align="center", bold=True)


class Sparks:
    def __init__(self):
        self.p = []

    def burst(self, x, y, n=40, kind="heart"):
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(80, 260)
            self.p.append([kind if random.random() < 0.6 else "spark", x, y, math.cos(a) * v, math.sin(a) * v - 60,
                           random.uniform(1.0, 1.8), random.choice([PINK, GOLD, (255, 255, 255), (190, 160, 255)])])

    def update_draw(self, surf, dt):
        alive = []
        for p in self.p:
            p[1] += p[3] * dt
            p[2] += p[4] * dt
            p[4] += 160 * dt
            p[3] *= 0.985
            p[5] -= dt
            if p[5] <= 0:
                continue
            alive.append(p)
            k = min(1.0, p[5])
            if p[0] == "heart":
                bobo.heart(surf, p[1], p[2], 5 + 4 * k, p[6])
            else:
                pygame.draw.circle(surf, p[6], (int(p[1]), int(p[2])), max(1, int(3 * k)))
        self.p = alive


class Music:
    """Carillon leggero in sottofondo (pentatonica, non stona mai)."""
    MELODY = [0, 2, 4, 7, 4, 2, 5, 4, 2, 0, 2, 4, 9, 7, 4, 2]

    def __init__(self):
        base = 523.25
        self.notes = {i: sound.synth([(base * 2 ** (i / 12), base * 2 ** (i / 12), 0.5, "sine")], 0.09)
                      for i in set(self.MELODY)}
        self.i, self.next = 0, 0.0

    def tick(self, t):
        if t >= self.next:
            sound.play(self.notes[self.MELODY[self.i % len(self.MELODY)]])
            self.i += 1
            self.next = t + 0.42


class Show:
    def __init__(self, ctx, cfg):
        self.ctx, self.cfg = ctx, cfg
        self.look = Look(ctx)
        self.eyes = bobo.Eyes()
        self.sparks = Sparks()
        self.music = Music()
        self.t = 0.0
        self.expr = "happy"
        self.bounce = 0.0

    def frame(self, lines=None, extra=None, look=None):
        dt = 1 / 30
        self.t += dt
        self.music.tick(self.t)
        col = {"love": (255, 120, 190), "joy": (255, 170, 220)}.get(self.expr, (150, 220, 255))
        self.eyes.update(dt, self.t, self.expr, col, look)
        self.look.background(self.t)
        self.look.eyes(self.eyes, self.t, self.expr, self.bounce)
        if lines:
            self.look.card_text(lines)
        if extra:
            extra()
        self.sparks.update_draw(self.ctx.surf, dt)
        self.ctx.flip()

    def say(self, *texts, expr="happy", secs=3.2):
        """Una o due righe, scritte lettera per lettera."""
        self.expr = expr
        sound.play(sound.babble("happy"))
        full = sum(len(x) for x in texts)
        shown, wait = 0.0, 0.0
        self.ctx.input.flush()
        while True:
            acts = self.ctx.input.poll()
            if shown < full:
                shown += 1.4
                if "A" in acts:
                    shown = full
            else:
                wait += 1 / 30
                if "A" in acts or wait > secs:
                    return
            lines, left = [], shown
            for i, x in enumerate(texts):
                part = x[:max(0, int(left))]
                left -= len(x)
                lines.append((part, 34 if i == 0 else 26, (255, 255, 255) if i == 0 else (255, 215, 235)))
            self.frame(lines)

    def ask(self):
        q, sub = DOMANDE[self.cfg["domanda"]]
        sel = 0
        self.ctx.input.flush()
        while True:
            for a in self.ctx.input.poll():
                if a in ("LEFT", "RIGHT", "UP", "DOWN"):
                    sel = 1 - sel
                    sound.play("tick")
                elif a == "A":
                    return sel == 0
            self.expr = "love" if sel == 0 else "happy"

            def buttons():
                self.look.pill(40, 400, 270, 58, SI, sel == 0, self.t, (255, 90, 160))
                self.look.pill(330, 400, 270, 58, NO, sel == 1, self.t, (130, 120, 200))
                self.ctx.text("croce per scegliere, A per confermare", W // 2, 462, 16, (220, 190, 230), align="center")

            self.frame([(q, 36, (255, 255, 255)), (sub, 26, (255, 215, 235))], buttons,
                       look=(-35 if sel == 0 else 35, 12))

    def yes(self):
        sound.play("win")
        self.expr = "love"
        t0 = self.t
        nome = self.cfg["nome"] or "Lui"
        numero = self.cfg["numero"]
        self.ctx.input.flush()
        while True:
            acts = self.ctx.input.poll()
            el = self.t - t0
            if el > 2.5 and acts:
                return
            if int(el * 30) % 18 == 0 and el < 5:
                self.sparks.burst(random.uniform(120, W - 120), random.uniform(120, 260), 30)
                sound.play("chirp")
            self.bounce = el % 1.0 if el < 3 else 0.0
            if el > 3:
                self.expr = "joy"
            if el < 3 or not numero:
                lines = [("Evviva!!", 46, (255, 255, 255)), ("%s ora e' felicissimo" % nome, 28, (255, 215, 235))]
            else:
                lines = [("Ecco il suo numero:", 26, (255, 215, 235)), (numero, 46, GOLD),
                         ("scrivigli quando vuoi :)", 22, (255, 215, 235))]
            self.frame(lines)

    def maybe_later(self):
        sound.play("love")
        self.say("Nessun problema!", "Grazie per avermi ascoltato, buona giornata :)", expr="joy", secs=5)


def title(ctx, cfg, look):
    t = 0.0
    ctx.input.flush()
    while True:
        for a in ctx.input.poll():
            if a == "A":
                return True
            if a == "B":
                return False
            if a == "Y":
                n = r36.keyboard(ctx, "Il tuo nome", cfg["nome"].upper(), 12)
                if n is not None:
                    cfg["nome"] = n.title()
                    save(cfg)
            if a == "X":
                cfg["domanda"] = (cfg["domanda"] + 1) % len(DOMANDE)
                save(cfg)
            if a == "START":
                n = r36.keyboard(ctx, "Il tuo numero (facoltativo)", cfg["numero"], 14)
                cfg["numero"] = (n or "").strip()
                save(cfg)
        t += 1 / 30
        look.background(t)
        look.glow_text("Invito", W // 2, 28, 56, (255, 255, 255))
        rows = [("Nome", cfg["nome"] or "(dira' 'il mio amico')"),
                ("Domanda", DOMANDE[cfg["domanda"]][0]),
                ("Numero", cfg["numero"] or "(nessuno)")]
        y = 120
        for k, v in rows:
            ctx.text(k, 50, y, 24, (230, 200, 230))
            ctx.text(v, 50, y + 26, 30, (255, 255, 255), bold=True)
            y += 72
        ctx.text("A via   Y nome   X domanda   START numero   B esci", W // 2, 440, 20, (230, 200, 230), align="center")
        ctx.flip()


def run(ctx):
    cfg = load()
    look = Look(ctx)
    while title(ctx, cfg, look):
        show = Show(ctx, cfg)
        chi = cfg["nome"] or "Il mio amico"
        show.say("Ciao! Scusa se ti disturbo...", "ci metto solo un attimo.")
        show.say("Io sono Bobo.", "%s e' troppo timido per chiedertelo," % chi)
        show.say("...quindi ha costruito me.", "(si', davvero)", expr="joy")
        if show.ask():
            show.yes()
        else:
            show.maybe_later()
