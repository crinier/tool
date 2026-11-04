"""Invito: Bobo chiede al posto tuo.

Mostri lo schermo, Bobo si presenta e fa la domanda. Lei sceglie SI' o NO
con la croce e preme A.
- SI': festa, cuori, musichetta.
- NO: Bobo ci prova in modo simpatico al massimo due volte, poi accetta
  con un sorriso (un no e' un no!).

Personalizza: nel titolo premi Y per scrivere il tuo nome e X per cambiare
la domanda. Tutto viene salvato in invito.json.
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
    "Ti andrebbe un caffe' con lui?",
    "Ti va un gelato insieme?",
    "Posso offrirti un aperitivo?",
    "Gli lasceresti il tuo numero?",
]
INSISTI = [
    "Sicura? Ci pensi un attimo?",
    "Ultima occasione... offre lui!",
]


def load():
    try:
        with open(SAVE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"nome": "", "domanda": 0}


def save(cfg):
    try:
        with open(SAVE, "w") as f:
            json.dump(cfg, f)
    except OSError:
        pass


class Scene:
    def __init__(self, ctx):
        self.ctx = ctx
        self.eyes = bobo.Eyes()
        self.parts = bobo.Particles()
        self.t = 0.0
        self.expr = "happy"

    def frame(self, text="", shown=None, look=None, extra=None, fx_jump=0.0):
        dt = 1 / 30
        self.t += dt
        color = bobo.EYE_COLORS.get(self.expr, bobo.EYE_COLORS["happy"])
        self.eyes.update(dt, self.t, self.expr, color, look)
        self.parts.update(dt)
        s = self.ctx.surf
        s.fill((0, 0, 0))
        self.eyes.draw(s, W // 2, 175, self.t, self.expr, 0, fx_jump)
        self.parts.draw(self.ctx, self.t)
        if text:
            part = text if shown is None else text[:int(shown)]
            self.ctx.text(part, W // 2, 300, 34, (235, 240, 250), align="center", bold=True)
        if extra:
            extra(s)
        self.ctx.flip()

    def hearts(self, n=8):
        for _ in range(n):
            self.parts.add("heart", W // 2 + random.uniform(-200, 200), 200 + random.uniform(-40, 60),
                           random.uniform(-30, 30), random.uniform(-90, -50), 1.6)


def say(scene, text, expr="happy", wait_key=True):
    """Scrive la frase lettera per lettera con il versetto, poi aspetta A (o 3 s)."""
    scene.expr = expr
    sound.play(sound.babble("sad" if expr == "sad" else "happy"))
    shown, wait = 0.0, 0.0
    scene.ctx.input.flush()
    while True:
        acts = scene.ctx.input.poll()
        if "B" in acts:
            return False
        if shown < len(text):
            shown += 1.2
            if "A" in acts:
                shown = len(text)
        else:
            wait += 1 / 30
            if "A" in acts or (not wait_key and wait > 0.6) or wait > 3.0:
                return True
        scene.frame(text, shown)


def ask(scene, question, tries):
    """Domanda con SI'/NO. Ritorna True (si') o False (no)."""
    sel = 0
    dodge = 0.0
    scene.ctx.input.flush()
    while True:
        acts = scene.ctx.input.poll()
        for a in acts:
            if a in ("LEFT", "RIGHT"):
                sel = 1 - sel
                sound.play("tick")
            elif a == "A":
                return sel == 0
        dodge = max(0.0, dodge - 1 / 30)

        def buttons(s):
            for i, label in enumerate(("SI'", "NO")):
                bw = 170 if i == 0 else max(90, 170 - tries * 40)   # il NO rimpicciolisce
                x = (W // 2 - 200 if i == 0 else W // 2 + 30) + (0 if i == 0 else int(math.sin(scene.t * 3) * 6 * tries))
                on = sel == i
                col = (255, 110, 175) if i == 0 else (120, 126, 140)
                pygame.draw.rect(s, (14, 16, 22), (x, 360, bw, 60), border_radius=16)
                pygame.draw.rect(s, col if on else (60, 64, 76), (x, 360, bw, 60), 5 if on else 2, border_radius=16)
                scene.ctx.text(label, x + bw // 2, 374, 38, (255, 255, 255) if on else col, align="center", bold=True)
            scene.ctx.text("Usa la croce e premi A", W // 2, 440, 22, (90, 95, 110), align="center")

        scene.expr = "love" if sel == 0 else ("sad" if tries else "happy")
        scene.frame(question, None, look=(-40 if sel == 0 else 40, 10), extra=buttons)


def celebrate(scene, nome):
    sound.play("win")
    scene.expr = "love"
    t0 = scene.t
    scene.ctx.input.flush()
    while True:
        acts = scene.ctx.input.poll()
        if scene.t - t0 > 1.5 and acts:
            return
        if int(scene.t * 10) % 3 == 0:
            scene.hearts(2)
        if scene.t - t0 > 2.2:
            scene.expr = "joy"
        scene.frame("Evviva!! %s ora e' felicissimo!" % (nome or "Lui"), None,
                    fx_jump=(scene.t - t0) % 1.0)


def title(ctx, cfg):
    """Schermata per chi tiene la console: A parte, Y nome, X domanda, B esce."""
    ctx.input.flush()
    while True:
        for a in ctx.input.poll():
            if a == "A":
                return True
            if a == "B":
                return False
            if a == "Y":
                n = r36.keyboard(ctx, "Il tuo nome", cfg["nome"].upper())
                if n is not None:
                    cfg["nome"] = n.title()
                    save(cfg)
            if a == "X":
                cfg["domanda"] = (cfg["domanda"] + 1) % len(DOMANDE)
                save(cfg)
        ctx.header("Invito", "A via   Y tuo nome   X cambia domanda   B esci")
        ctx.text("Nome:", 40, 90, 30, r36.DIM)
        ctx.text(cfg["nome"] or "(nessuno: dira' 'lui')", 160, 88, 34, r36.FG, bold=True)
        ctx.text("Domanda:", 40, 150, 30, r36.DIM)
        ctx.text(DOMANDE[cfg["domanda"]], 40, 190, 32, r36.ACCENT, bold=True)
        ctx.text("Premi A e passa la console :)", r36.W // 2, 300, 30, r36.FG, align="center")
        ctx.flip()


def run(ctx):
    cfg = load()
    while title(ctx, cfg):
        scene = Scene(ctx)
        chi = cfg["nome"] or "il mio amico"
        chi = chi[0].upper() + chi[1:]
        lines = ["Ciao! Io sono Bobo.",
                 "%s e' un po' timido..." % chi,
                 "...e mi ha chiesto di farti una domanda."]
        ok = True
        for ln in lines:
            if not say(scene, ln):
                ok = False
                break
        if not ok:
            continue
        domanda = DOMANDE[cfg["domanda"]]
        tries = 0
        while True:
            if ask(scene, domanda, tries):
                celebrate(scene, cfg["nome"])
                break
            if tries < len(INSISTI):
                say(scene, INSISTI[tries], "sad")
                tries += 1
            else:
                sound.play("love")
                say(scene, "Va bene, nessun problema!", "joy")
                say(scene, "Grazie lo stesso, buona giornata!", "joy")
                break
