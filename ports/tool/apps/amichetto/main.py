"""Bobo, il piccolo amico: due occhi su schermo nero.

Mangia, dorme, gioca, vuole le coccole e se lo stuzzichi troppo si arrabbia.
Ogni cosa ha il suo versetto (suoni sintetizzati, niente file audio).
Lo stato viene salvato in bobo.json: quando torni, il tempo e' passato anche
per lui (ma con calma, non muore mai).
"""
import json
import math
import os
import random
import time

import pygame

import r36
from r36 import sound

NAME = "Amichetto"
DESCRIPTION = "Bobo: due occhi che mangiano, dormono e si arrabbiano"
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bobo.json")
W, H = r36.W, r36.H
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (70, 74, 86)
DIMTXT = (120, 126, 140)

EYE_COLORS = {
    "happy": (90, 225, 255), "hungry": (255, 205, 90), "tired": (110, 150, 220),
    "sad": (100, 140, 255), "angry": (255, 60, 50), "sleep": (50, 80, 150),
    "love": (255, 110, 175),
}

FOODS = [  # nome, sazieta', felicita', energia, frase
    ("Mela", 25, 2, 0, "Croc croc!"),
    ("Biscotto", 12, 12, 0, "Gnam! Dolcissimo!"),
    ("Pizza", 40, 6, -5, "Buonissimaaa!"),
]
ACTIONS = ["Mangia", "Gioca", "Coccole", "Luce"]

TALK = {
    "happy": ["Ti voglio bene!", "Che bella giornata!", "Mi fai compagnia?",
              "Lalala~", "Sei il mio amico preferito!", "Hihi!"],
    "hungry": ["Ho fame...", "Pancino vuoto!", "Un biscottino?"],
    "tired": ["Che sonno...", "Uaaah...", "Spegni la luce?"],
    "sad": ["Giochiamo?", "Mi annoio...", "Mi dai una coccola?"],
    "angry": ["Uffa!", "Grrr!", "Hmpf!", "Non ti parlo!"],
}


def clamp(v):
    return max(0.0, min(100.0, v))


def lerp(a, b, k):
    return a + (b - a) * k


def lerp_color(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ---------------------------------------------------------------- stato

class Pet:
    def __init__(self):
        self.food = 80.0
        self.energy = 80.0
        self.fun = 80.0
        self.anger = 0.0          # secondi di broncio rimasti
        self.asleep = False
        self.born = time.time()
        self.pokes = []
        self.cuddles = []

    def load(self):
        try:
            with open(SAVE) as f:
                d = json.load(f)
        except (OSError, ValueError):
            return False
        for k in ("food", "energy", "fun", "asleep", "born"):
            if k in d:
                setattr(self, k, d[k])
        away = max(0.0, min(time.time() - d.get("saved", time.time()), 10 * 3600))
        while away > 0:  # mentre eri via il tempo passa piu' piano
            self.tick(min(60.0, away) * 0.35)
            away -= 60.0
        self.food, self.energy, self.fun = (max(8.0, x) for x in (self.food, self.energy, self.fun))
        return True

    def save(self):
        d = {k: getattr(self, k) for k in ("food", "energy", "fun", "asleep", "born")}
        d["saved"] = time.time()
        tmp = SAVE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(d, f)
        os.replace(tmp, SAVE)

    def tick(self, dt):
        m = dt / 60.0
        self.food = clamp(self.food - 1.2 * m)
        if self.asleep:
            self.energy = clamp(self.energy + 5.0 * m)
            self.fun = clamp(self.fun - 0.3 * m)
        else:
            self.energy = clamp(self.energy - 0.8 * m)
            self.fun = clamp(self.fun - (1.0 + (1.0 if self.food < 15 else 0)) * m)
        self.anger = max(0.0, self.anger - dt)

    def mood(self):
        if self.asleep:
            return "sleep"
        if self.anger > 0:
            return "angry"
        if self.food < 25:
            return "hungry"
        if self.energy < 20:
            return "tired"
        if self.fun < 30:
            return "sad"
        return "happy"

    def days(self):
        return int((time.time() - self.born) // 86400)


# ---------------------------------------------------------------- icone

def heart(surf, x, y, s, color=(255, 90, 140)):
    r = max(1, int(s * 0.55))
    pygame.draw.circle(surf, color, (int(x - s * 0.45), int(y)), r)
    pygame.draw.circle(surf, color, (int(x + s * 0.45), int(y)), r)
    pygame.draw.polygon(surf, color, [(x - s, y + s * 0.15), (x + s, y + s * 0.15), (x, y + s * 1.2)])


def apple(surf, x, y, s):
    pygame.draw.circle(surf, (235, 70, 80), (x, y), s)
    pygame.draw.line(surf, (150, 100, 50), (x, y - s), (x + 2, y - s - 6), 3)
    pygame.draw.ellipse(surf, (110, 200, 90), (x + 3, y - s - 8, 10, 6))


def cookie(surf, x, y, s):
    pygame.draw.circle(surf, (215, 160, 90), (x, y), s)
    for dx, dy in ((-4, -3), (5, -1), (-1, 5), (4, 6)):
        pygame.draw.circle(surf, (110, 70, 40), (x + dx * s // 14, y + dy * s // 14), max(2, s // 6))


def pizza(surf, x, y, s):
    pygame.draw.polygon(surf, (245, 200, 90), [(x - s, y - s * 0.7), (x + s, y - s * 0.7), (x, y + s)])
    pygame.draw.line(surf, (200, 140, 60), (x - s, y - s * 0.7), (x + s, y - s * 0.7), 5)
    for dx, dy in ((-0.3, -0.3), (0.3, -0.25), (0, 0.25)):
        pygame.draw.circle(surf, (220, 60, 60), (int(x + dx * s), int(y + dy * s)), max(2, s // 5))


def bolt(surf, x, y, s):
    pygame.draw.polygon(surf, (255, 200, 40), [
        (x + s * 0.2, y - s), (x - s * 0.6, y + s * 0.15), (x - s * 0.05, y + s * 0.15),
        (x - s * 0.25, y + s), (x + s * 0.6, y - s * 0.15), (x + s * 0.05, y - s * 0.15)])


def ball(surf, x, y, s):
    pygame.draw.circle(surf, (90, 150, 240), (x, y), s)
    pygame.draw.arc(surf, WHITE, (x - s, y - s // 2, s * 2, s), 0, math.pi, 3)
    pygame.draw.arc(surf, WHITE, (x - s, y - s // 2, s * 2, s), math.pi, 2 * math.pi, 3)


def moon(surf, x, y, s, bg=BLACK, color=(250, 235, 160)):
    pygame.draw.circle(surf, color, (x, y), s)
    pygame.draw.circle(surf, bg, (x + s // 2, y - s // 3), s)


def sun(surf, x, y, s):
    for i in range(8):
        a = i * math.pi / 4
        pygame.draw.line(surf, (255, 200, 60), (x + math.cos(a) * s * 1.2, y + math.sin(a) * s * 1.2),
                         (x + math.cos(a) * s * 1.6, y + math.sin(a) * s * 1.6), 3)
    pygame.draw.circle(surf, (255, 210, 70), (x, y), s)


FOOD_ICONS = [apple, cookie, pizza]


# ---------------------------------------------------------------- occhi

# Ogni espressione e' un insieme di parametri; gli occhi ci scivolano dentro
# morbidamente. lo/li = palpebra superiore lato esterno/interno (0..1),
# smile = palpebra inferiore che sale (occhi a "^"), w/h = dimensioni.
EXPR = {
    "happy":  dict(w=100, h=130, lo=0.0, li=0.0, smile=0.0),
    "joy":    dict(w=110, h=120, lo=0.0, li=0.0, smile=0.62),
    "hungry": dict(w=96, h=120, lo=0.25, li=0.0, smile=0.0),
    "tired":  dict(w=104, h=120, lo=0.48, li=0.48, smile=0.0),
    "sad":    dict(w=96, h=124, lo=0.42, li=0.0, smile=0.0),
    "angry":  dict(w=104, h=118, lo=0.0, li=0.52, smile=0.12),
    "sleep":  dict(w=110, h=10, lo=0.0, li=0.0, smile=0.0),
    "love":   dict(w=110, h=110, lo=0.0, li=0.0, smile=0.0),
    "squeeze": dict(w=110, h=14, lo=0.0, li=0.0, smile=0.0),
}


class Eyes:
    def __init__(self):
        self.p = dict(EXPR["happy"])
        self.color = EYE_COLORS["happy"]
        self.look = [0.0, 0.0]
        self.look_target = [0.0, 0.0]
        self.next_look = 1.0
        self.blink_at = 2.0
        self.blink_t = -1.0
        self.double = False
        self.glow = {}

    def update(self, dt, t, expr, color, look=None):
        k = min(1.0, dt * 10)
        for key, v in EXPR[expr].items():
            self.p[key] = lerp(self.p[key], v, k)
        self.color = lerp_color(self.color, color, min(1.0, dt * 6))
        if look is not None:
            self.look_target = list(look)
        elif t >= self.next_look:
            if expr in ("sleep", "squeeze"):
                self.look_target = [0, 6]
            elif random.random() < 0.35:
                self.look_target = [0, 0]
            else:
                self.look_target = [random.uniform(-45, 45), random.uniform(-22, 18)]
            self.next_look = t + random.uniform(1.2, 3.5)
        # gli occhi saltano rapidi verso il punto (saccade), come quelli veri
        k2 = min(1.0, dt * 14)
        self.look[0] = lerp(self.look[0], self.look_target[0], k2)
        self.look[1] = lerp(self.look[1], self.look_target[1], k2)
        if t >= self.blink_at and self.blink_t < 0:
            self.blink_t = 0.0
        if self.blink_t >= 0:
            self.blink_t += dt
            if self.blink_t > 0.16:
                self.blink_t = -1.0
                if self.double:
                    self.double = False
                    self.blink_at = t + 3.0 + random.uniform(0, 3)
                elif random.random() < 0.2:
                    self.double = True
                    self.blink_at = t + 0.12
                else:
                    self.blink_at = t + 2.5 + random.uniform(0, 3.5)

    def blink_factor(self):
        if self.blink_t < 0:
            return 1.0
        x = self.blink_t / 0.16
        return max(0.08, abs(1 - 2 * x))

    def _glow(self, w, h, r, color):
        key = (int(w) // 4, int(h) // 4, color)
        if key not in self.glow:
            if len(self.glow) > 60:
                self.glow.clear()
            pad = 22
            s = pygame.Surface((int(w) + pad * 2, int(h) + pad * 2), pygame.SRCALPHA)
            for i, a in ((18, 18), (12, 30), (6, 45)):
                pygame.draw.rect(s, color + (a,), (pad - i, pad - i, int(w) + i * 2, int(h) + i * 2),
                                 border_radius=int(r + i))
            self.glow[key] = s
        return self.glow[key]

    def draw(self, surf, cx, cy, t, mode, shake=0.0, bounce=0.0):
        p, col = self.p, self.color
        breathe = math.sin(t * 2.2) * 3
        hop = abs(math.sin(bounce * math.pi * 3)) * 25 if bounce > 0 else 0
        for side in (-1, 1):
            ex = cx + side * 105 + self.look[0] + math.sin(t * 50) * shake
            ey = cy + self.look[1] - hop
            if mode == "love":
                s = 52 + math.sin(t * 8) * 6
                heart(surf, ex, ey - s * 0.4, s, col)
                continue
            if mode == "squeeze":  # occhi a > <
                d = 38
                pts = [(ex - side * d, ey - d), (ex + side * d * 0.6, ey), (ex - side * d, ey + d)]
                pygame.draw.lines(surf, col, False, pts, 12)
                continue
            w = p["w"]
            h = max(6.0, p["h"] * self.blink_factor() + (breathe if mode != "sleep" else 0))
            r = min(w, h) * 0.32
            surf.blit(self._glow(w, h, r, col), (ex - w / 2 - 22, ey - h / 2 - 22))
            rect = pygame.Rect(0, 0, int(w), int(h))
            rect.center = (int(ex), int(ey))
            pygame.draw.rect(surf, col, rect, border_radius=int(r))
            if h > 40:  # riflesso
                pygame.draw.ellipse(surf, lerp_color(col, WHITE, 0.6),
                                    (rect.x + w * 0.18, rect.y + h * 0.14, w * 0.22, h * 0.16))
            # palpebra superiore inclinata (copre col nero)
            top = rect.top - 2
            outer_x = rect.left - 26 if side < 0 else rect.right + 26
            inner_x = rect.right + 26 if side < 0 else rect.left - 26
            lo, li = p["lo"] * h, p["li"] * h
            if lo > 1 or li > 1:
                pygame.draw.polygon(surf, BLACK, [(outer_x, top - 40), (inner_x, top - 40),
                                                  (inner_x, top + li), (outer_x, top + lo)])
            # palpebra inferiore che sale = occhi sorridenti
            if p["smile"] > 0.02:
                sy = rect.bottom - p["smile"] * h
                pygame.draw.ellipse(surf, BLACK, (rect.x - w * 0.3, sy, w * 1.6, h * 1.3))


class Particles:
    def __init__(self):
        self.items = []

    def add(self, kind, x, y, vx=0.0, vy=-40.0, life=1.6):
        self.items.append([kind, x, y, vx, vy, life, life])

    def update(self, dt):
        for p in self.items:
            p[1] += p[3] * dt
            p[2] += p[4] * dt
            p[5] -= dt
        self.items = [p for p in self.items if p[5] > 0]

    def draw(self, ctx, t):
        for kind, x, y, vx, vy, life, total in self.items:
            k = life / total
            if kind == "heart":
                heart(ctx.surf, x, y, 5 + 7 * k)
            elif kind == "z":
                ctx.text("z", int(x + math.sin(t * 3 + y) * 6), int(y), int(22 + (1 - k) * 24),
                         lerp_color((20, 30, 60), (120, 150, 230), k), bold=True)
            elif kind == "steam":
                pygame.draw.circle(ctx.surf, lerp_color((40, 10, 10), (255, 90, 70), k),
                                   (int(x), int(y)), max(1, int(14 * (1 - k) + 4)), 3)
            elif kind == "crumb":
                pygame.draw.circle(ctx.surf, (200, 150, 80), (int(x), int(y)), 3)
            elif kind == "tear":
                pygame.draw.circle(ctx.surf, (100, 150, 255), (int(x), int(y)), 6)


# ---------------------------------------------------------------- HUD

def stat_bar(ctx, x, y, icon, value):
    icon(ctx.surf, x, y + 9, 8)
    pygame.draw.rect(ctx.surf, (30, 32, 40), (x + 16, y + 4, 100, 10), border_radius=5)
    col = (90, 200, 120) if value > 50 else (240, 180, 60) if value > 25 else (240, 80, 80)
    pygame.draw.rect(ctx.surf, col, (x + 16, y + 4, max(0, int(100 * value / 100)), 10), border_radius=5)


def action_icon(surf, i, x, y, night):
    if i == 0:
        apple(surf, x, y, 11)
    elif i == 1:
        ball(surf, x, y, 11)
    elif i == 2:
        heart(surf, x, y - 5, 10)
    elif night:
        sun(surf, x, y, 8)
    else:
        moon(surf, x, y, 11, (14, 16, 22), (150, 140, 230))


# ---------------------------------------------------------------- app

class App:
    def __init__(self, ctx):
        self.ctx = ctx
        self.pet = Pet()
        self.t = 0.0
        first = not self.pet.load()
        self.eyes = Eyes()
        self.sel = 0
        self.mode = "main"   # main / food / game / reveal
        self.food_sel = 0
        self.fx = {}
        self.parts = Particles()
        self.msg, self.msg_until = "", 0.0
        self.next_talk = 8.0
        self.next_puff = 0.0
        self.game = None
        self.last_save = 0.0
        self.cx, self.cy = W // 2, 205
        if first:
            self.say("Ciao! Sono Bobo!", 4, "chirp")
        elif self.pet.asleep:
            self.say("Zzz...", 3, None)
        else:
            self.say(random.choice(["Bentornato!", "Mi sei mancato!", "Eccoti!"]), 3, "chirp")
            self.fx["joy"] = 1.5

    def say(self, text, secs=2.5, snd="babble"):
        self.msg, self.msg_until = text, self.t + secs
        if snd == "babble":
            sound.play(sound.babble(self.pet.mood()))
        elif snd:
            sound.play(snd)

    def hearts(self, n=5):
        for _ in range(n):
            self.parts.add("heart", self.cx + random.uniform(-150, 150), self.cy + random.uniform(-20, 40),
                           random.uniform(-20, 20), random.uniform(-80, -45), 1.4)

    # --- azioni
    def do_action(self, i):
        p = self.pet
        if i == 0:
            if p.asleep:
                self.say("Zzz... (dorme)", snd="snore")
            else:
                self.mode, self.food_sel = "food", 0
                sound.play("tick")
        elif i == 1:
            if p.asleep:
                self.say("Zzz... (dorme)", snd="snore")
            elif p.mood() == "angry":
                self.say("Non gioco con te! Hmpf!", snd="angry")
            elif p.energy < 15:
                self.say("Troppo stanco...", snd="sad")
            else:
                self.game = {"hand": random.randint(0, 1), "pick": None, "until": 0}
                self.mode = "game"
                self.say("Dov'e' il biscotto?", 30, "chirp")
        elif i == 2:
            self.cuddle()
        else:
            self.toggle_light()

    def eat(self, k):
        p = self.pet
        name, food, fun, energy, line = FOODS[k]
        self.mode = "main"
        if p.food > 92:
            p.anger = max(p.anger, 2.0)
            self.say("Sono pieno! Basta!", snd="refuse")
            return
        p.food = clamp(p.food + food)
        p.fun = clamp(p.fun + fun)
        p.energy = clamp(p.energy + energy)
        self.fx["eat"] = 1.6
        self.fx["food_icon"] = k
        self.say(line, snd="eat")
        for _ in range(8):
            self.parts.add("crumb", self.cx + random.uniform(-20, 20), self.cy + 140,
                           random.uniform(-80, 80), random.uniform(-40, 30), 0.8)

    def cuddle(self):
        p = self.pet
        now = self.t
        p.cuddles = [c for c in p.cuddles if now - c < 10] + [now]
        if p.asleep:
            self.parts.add("heart", self.cx, self.cy - 30, 0, -40, 1.5)
            self.say("Mmm... (sorride nel sonno)", snd="snore")
            return
        if p.anger > 0:
            p.anger = max(0.0, p.anger - 4)
            if p.anger == 0:
                self.say("...va bene, ti perdono", snd="love")
                self.hearts(3)
            else:
                self.say("Hmpf... ancora un po'", snd="refuse")
            return
        if len(p.cuddles) > 6:
            self.say("Basta coccole, mi spettini!", snd="refuse")
            return
        p.fun = clamp(p.fun + 8)
        self.fx["love"] = 1.6
        self.hearts()
        self.say(random.choice(["Hihi!", "Che bello!", "Ancora!", "Ti voglio bene!"]), snd="love")

    def toggle_light(self):
        p = self.pet
        if p.asleep:
            p.asleep = False
            if p.energy < 60:
                p.anger = 6.0
                self.say("Stavo dormendo!! Grrr!", snd="angry")
            else:
                self.say("Buongiorno!", snd="wake")
        elif p.energy > 75 and p.mood() != "angry":
            self.say("Non ho sonno!", snd="refuse")
        else:
            p.asleep = True
            self.say("Buonanotte...", snd="sleep")

    def poke(self):
        p = self.pet
        now = self.t
        self.fx["squeeze"] = 0.35
        if p.asleep:
            p.asleep = False
            if p.energy < 60:
                p.anger = 8.0
                self.say("Ma insomma! Dormivo!", snd="angry")
            else:
                self.say("Eh? Gia' mattina?", snd="wake")
            return
        p.pokes = [x for x in p.pokes if now - x < 4] + [now]
        if len(p.pokes) >= 3:
            p.anger = 10.0
            p.fun = clamp(p.fun - 10)
            p.pokes = []
            for k in ("love", "jump", "joy"):
                self.fx.pop(k, None)
            self.say("Grrr! BASTA!", snd="angry")
        elif p.anger > 0:
            p.anger += 3
            self.say("Lasciami stare!", snd="angry")
        else:
            self.say(random.choice(["Ehi!", "Ahi!", "Che c'e'?", "Hihi, solletico!"]), snd="boop")

    # --- ciclo
    def expression(self):
        mood = self.pet.mood()
        fx = self.fx
        if mood == "sleep":
            return "sleep"
        if "squeeze" in fx:
            return "squeeze"
        if mood == "angry":
            return "angry"
        if "love" in fx:
            return "love"
        if "eat" in fx or "jump" in fx or "joy" in fx:
            return "joy"
        return mood

    def update(self, dt):
        p = self.pet
        was_asleep = p.asleep
        p.tick(dt)
        if p.asleep and p.energy >= 100:
            p.asleep = False
            self.say("Buongiorno! Ho dormito benissimo!", snd="wake")
        if not was_asleep and not p.asleep and p.energy <= 0:
            p.asleep = True
            self.say("Crollo... zzz", snd="sleep")
        for k in list(self.fx):
            if isinstance(self.fx[k], float):
                self.fx[k] -= dt
                if self.fx[k] <= 0:
                    del self.fx[k]

        expr = self.expression()
        mood = p.mood()
        if expr in EYE_COLORS:
            color = EYE_COLORS[expr]
        else:  # joy / squeeze
            color = EYE_COLORS["angry" if mood == "angry" else "happy"]
        look = None
        if self.mode == "game":
            look = (-60 if int(self.t * 1.6) % 2 else 60, 20)
        elif self.mode == "reveal":
            look = (-70 if self.game["hand"] == 0 else 70, 30)
        elif self.mode == "food" or "eat" in self.fx:
            look = (0, 35)
        self.eyes.update(dt, self.t, expr, color, look)

        self.parts.update(dt)
        if self.t >= self.next_puff:
            if mood == "sleep":
                self.parts.add("z", self.cx + 150, self.cy - 20, 25, -35, 2.6)
                if random.random() < 0.4:
                    sound.play("snore")
                self.next_puff = self.t + 1.6
            elif mood == "angry":
                for side in (-1, 1):
                    self.parts.add("steam", self.cx + side * 170, self.cy - 70, side * 40, -60, 0.9)
                self.next_puff = self.t + 0.5
            elif mood == "sad" and random.random() < 0.5:
                self.parts.add("tear", self.cx + random.choice((-140, 140)), self.cy + 50, 0, 60, 1.2)
                self.next_puff = self.t + 2.5
            else:
                self.next_puff = self.t + 1
        if self.t >= self.next_talk and self.mode == "main":
            if mood != "sleep" and self.t > self.msg_until:
                self.say(random.choice(TALK[mood]), 3)
            self.next_talk = self.t + random.uniform(14, 28)
        if self.mode == "reveal" and self.t >= self.game["until"]:
            self.mode = "main"
        if self.t - self.last_save > 30:
            p.save()
            self.last_save = self.t

    def handle(self, a):
        if self.mode == "food":
            if a == "LEFT":
                self.food_sel = (self.food_sel - 1) % len(FOODS)
                sound.play("tick")
            elif a == "RIGHT":
                self.food_sel = (self.food_sel + 1) % len(FOODS)
                sound.play("tick")
            elif a == "A":
                self.eat(self.food_sel)
            elif a == "B":
                self.mode = "main"
            return True
        if self.mode == "game":
            if a in ("LEFT", "RIGHT"):
                pick = 0 if a == "LEFT" else 1
                g = self.game
                g["pick"], g["until"] = pick, self.t + 2.2
                p = self.pet
                p.energy = clamp(p.energy - 7)
                if pick == g["hand"]:
                    p.fun = clamp(p.fun + 20)
                    self.fx["jump"] = 1.0
                    self.hearts(6)
                    self.say("Bravissimo!! Hai vinto!", snd="win")
                else:
                    p.fun = clamp(p.fun + 8)
                    self.say("Ehehe, era di qua!", snd="lose")
                self.mode = "reveal"
            elif a == "B":
                self.mode = "main"
                self.say("Va bene, dopo!")
            return True
        if self.mode == "reveal":
            return True
        if a == "LEFT":
            self.sel = (self.sel - 1) % len(ACTIONS)
            sound.play("tick")
        elif a == "RIGHT":
            self.sel = (self.sel + 1) % len(ACTIONS)
            sound.play("tick")
        elif a == "A":
            self.do_action(self.sel)
        elif a == "X":
            self.poke()
        elif a == "Y":
            sound.enabled = not sound.enabled
            self.say("Suoni " + ("accesi" if sound.enabled else "spenti"), 1.5, "tick")
        elif a == "B":
            return False
        return True

    def draw(self):
        ctx, p, t = self.ctx, self.pet, self.t
        night = p.asleep
        ctx.surf.fill(BLACK)
        expr = self.expression()
        shake = 3.0 if expr == "angry" else 0.0
        self.eyes.draw(ctx.surf, self.cx, self.cy, t, expr, shake, self.fx.get("jump", 0))
        if "eat" in self.fx:
            k = self.fx["eat"] / 1.6
            FOOD_ICONS[self.fx.get("food_icon", 0)](ctx.surf, self.cx, int(self.cy + 100 + (1 - k) * 10),
                                                    max(3, int(22 * k)))
        if self.mode in ("game", "reveal"):
            g = self.game
            for i, bx in enumerate((110, W - 110)):
                sel = g["pick"] == i
                col = (255, 120, 170)
                pygame.draw.rect(ctx.surf, col, (bx - 34, 280, 68, 56), 6 if sel else 3, border_radius=10)
                pygame.draw.line(ctx.surf, col, (bx, 280), (bx, 336), 3)
                if self.mode == "reveal" and i == g["hand"]:
                    cookie(ctx.surf, bx, 258, 18)
                ctx.text("<" if i == 0 else ">", bx, 340, 36, DIMTXT, align="center", bold=True)
        self.parts.draw(ctx, t)
        if t < self.msg_until and self.msg:
            fade = min(1.0, (self.msg_until - t) / 0.4)
            ctx.text(self.msg, W // 2, 348, 32, lerp_color(BLACK, (225, 230, 240), fade),
                     align="center", bold=True)

        # HUD discreto
        stat_bar(ctx, 14, 8, apple, p.food)
        stat_bar(ctx, 150, 8, bolt, p.energy)
        stat_bar(ctx, 286, 8, lambda s, x, y, z: heart(s, x, y - 4, 7), p.fun)
        ctx.text("Bobo  %d g%s" % (p.days(), "" if sound.enabled else "  (muto)"), W - 14, 9, 22,
                 DIMTXT, align="right")

        y0 = 400
        if self.mode == "food":
            items, icons, sel = [f[0] for f in FOODS], FOOD_ICONS, self.food_sel
        else:
            items, icons, sel = ACTIONS, None, self.sel
        n = len(items)
        bw = 140 if n == 4 else 180
        gap = (W - n * bw) // (n + 1)
        for i, label in enumerate(items):
            x = gap + i * (bw + gap)
            on = i == sel and self.mode in ("main", "food")
            border = EYE_COLORS["happy"] if on else GREY
            pygame.draw.rect(ctx.surf, (14, 16, 22), (x, y0, bw, 46), border_radius=12)
            pygame.draw.rect(ctx.surf, border, (x, y0, bw, 46), 3 if on else 1, border_radius=12)
            if icons:
                icons[i](ctx.surf, x + 24, y0 + 23, 11)
            else:
                action_icon(ctx.surf, i, x + 24, y0 + 24, night)
            if label == "Luce" and night:
                label = "Sveglia"
            ctx.text(label, x + 42, y0 + 13, 27, WHITE if on else DIMTXT, bold=on)
        hint = {"main": "SX/DX scegli  A fai  X stuzzica  Y suoni  B esci",
                "food": "SX/DX scegli cibo   A dai   B annulla",
                "game": "SINISTRA o DESTRA?   B lascia stare",
                "reveal": ""}[self.mode]
        ctx.text(hint, W // 2, 456, 21, (85, 90, 105), align="center")


def run(ctx):
    app = App(ctx)
    ctx.input.flush()
    last = time.monotonic()
    try:
        while True:
            now = time.monotonic()
            dt = min(0.1, now - last)
            last = now
            app.t += dt
            for a in ctx.input.poll():
                if not app.handle(a):
                    return
            app.update(dt)
            app.draw()
            ctx.flip()
    finally:
        try:
            app.pet.save()
        except OSError:
            pass
