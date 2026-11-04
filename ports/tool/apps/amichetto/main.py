"""Bobo, il piccolo amico virtuale.

Mangia, dorme, gioca, vuole le coccole e se lo stuzzichi troppo si arrabbia.
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

NAME = "Amichetto"
DESCRIPTION = "Bobo: mangia, dorme, gioca e si arrabbia"
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bobo.json")
W, H = r36.W, r36.H

INK = (60, 50, 70)
BODY = (140, 222, 180)
BODY_ANGRY = (245, 120, 110)
BELLY = (205, 245, 220)
CHEEK = (255, 150, 170)
WHITE = (255, 255, 255)

FOODS = [  # nome, sazieta', felicita', energia, frase
    ("Mela", 25, 2, 0, "Croc croc!"),
    ("Biscotto", 12, 12, 0, "Gnam! Dolcissimo!"),
    ("Pizza", 40, 6, -5, "Buonissimaaa!"),
]
ACTIONS = ["Mangia", "Gioca", "Coccole", "Luce"]

TALK = {
    "happy": ["Ti voglio bene!", "Che bella giornata!", "Mi fai compagnia?",
              "Lalala~", "Sei il mio amico preferito!", "Hihi!"],
    "hungry": ["Ho fame...", "Pancino vuoto!", "Un biscottino?", "Gnam gnam... magari!"],
    "tired": ["Che sonno...", "Uaaah...", "Spegni la luce?"],
    "sad": ["Giochiamo?", "Mi annoio...", "Mi dai una coccola?"],
    "angry": ["Uffa!", "Grrr!", "Hmpf!", "Non ti parlo!"],
}


def clamp(v):
    return max(0.0, min(100.0, v))


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
        # mentre eri via il tempo passa piu' piano
        step = 60.0
        while away > 0:
            self.tick(min(step, away) * 0.35)
            away -= step
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


# ---------------------------------------------------------------- disegno

def heart(surf, x, y, s, color=(255, 90, 130)):
    r = max(1, int(s * 0.55))
    pygame.draw.circle(surf, color, (int(x - s * 0.45), int(y)), r)
    pygame.draw.circle(surf, color, (int(x + s * 0.45), int(y)), r)
    pygame.draw.polygon(surf, color, [(x - s, y + s * 0.15), (x + s, y + s * 0.15), (x, y + s * 1.2)])


def apple(surf, x, y, s):
    pygame.draw.circle(surf, (235, 70, 80), (x, y), s)
    pygame.draw.line(surf, (120, 80, 40), (x, y - s), (x + 2, y - s - 6), 3)
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


def moon(surf, x, y, s, bg, color=(250, 235, 160)):
    pygame.draw.circle(surf, color, (x, y), s)
    pygame.draw.circle(surf, bg, (x + s // 2, y - s // 3), s)


def sun(surf, x, y, s):
    for i in range(8):
        a = i * math.pi / 4
        pygame.draw.line(surf, (255, 200, 60), (x + math.cos(a) * s * 1.2, y + math.sin(a) * s * 1.2),
                         (x + math.cos(a) * s * 1.6, y + math.sin(a) * s * 1.6), 3)
    pygame.draw.circle(surf, (255, 210, 70), (x, y), s)


FOOD_ICONS = [apple, cookie, pizza]


def draw_room(surf, t, night):
    wall = (32, 36, 66) if night else (252, 240, 222)
    floor = (48, 46, 76) if night else (232, 206, 176)
    surf.fill(wall)
    pygame.draw.rect(surf, floor, (0, 330, W, H - 330))
    pygame.draw.line(surf, lerp_color(floor, INK, 0.25), (0, 330), (W, 330), 3)
    # finestra
    wx, wy, ww, wh = 470, 90, 130, 110
    sky = (20, 24, 50) if night else (170, 220, 255)
    pygame.draw.rect(surf, sky, (wx, wy, ww, wh), border_radius=10)
    if night:
        for i, (sx, sy) in enumerate(((490, 110), (530, 175), (585, 120), (560, 150), (505, 160))):
            if math.sin(t * 2 + i * 1.7) > -0.3:
                pygame.draw.circle(surf, (255, 250, 200), (sx, sy), 2)
        moon(surf, 560, 130, 18, sky)
    else:
        sun(surf, 505, 120, 14)
        cx = 560 + math.sin(t * 0.3) * 15
        for dx, r in ((-14, 11), (0, 15), (15, 11)):
            pygame.draw.circle(surf, WHITE, (int(cx + dx), 165), r)
    frame = (90, 80, 110) if night else (190, 150, 110)
    pygame.draw.rect(surf, frame, (wx, wy, ww, wh), 6, border_radius=10)
    pygame.draw.line(surf, frame, (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 4)
    pygame.draw.line(surf, frame, (wx, wy + wh // 2), (wx + ww, wy + wh // 2), 4)
    # tappetino
    pygame.draw.ellipse(surf, (90, 80, 130) if night else (240, 170, 170), (170, 345, 300, 50))


def draw_pet(surf, cx, cy, t, mood, fx):
    """fx: dict con effetti momentanei (jump, eat, love, poke)."""
    angry = mood == "angry"
    breathe = math.sin(t * (1.2 if mood == "sleep" else 2.4))
    jump = fx.get("jump", 0)
    y_off = -abs(math.sin(jump * math.pi * 2)) * 50 if jump > 0 else 0
    x_off = math.sin(t * 45) * 3 if angry else 0
    if fx.get("poke", 0) > 0:
        x_off += math.sin(t * 60) * 6
    bw = 120 * (1 - 0.035 * breathe)
    bh = 104 * (1 + 0.035 * breathe)
    x = cx + x_off
    y = cy + y_off + (4 if mood == "sleep" else 0)

    # ombra
    sh = 1 - min(1, -y_off / 80)
    pygame.draw.ellipse(surf, lerp_color((200, 170, 150), (30, 30, 50), 0.5 if mood == "sleep" else 0),
                        (cx - bw * sh, cy + bh - 12, bw * 2 * sh, 24))

    body = lerp_color(BODY, BODY_ANGRY, 0.85 if angry else 0)
    dark = lerp_color(body, INK, 0.35)
    # piedini
    for side in (-1, 1):
        pygame.draw.ellipse(surf, dark, (x + side * 55 - 24, y + bh - 30, 48, 30))
    # germoglio in testa
    sway = math.sin(t * 1.8) * 6
    top = y - bh + 6
    pygame.draw.line(surf, (90, 160, 80), (x, top), (x + sway, top - 30), 5)
    pygame.draw.ellipse(surf, (120, 200, 90), (x + sway - 26, top - 44, 26, 16))
    pygame.draw.ellipse(surf, (120, 200, 90), (x + sway, top - 40, 26, 16))
    # corpo
    pygame.draw.ellipse(surf, body, (x - bw, y - bh, bw * 2, bh * 2))
    pygame.draw.ellipse(surf, lerp_color(BELLY, body, 0.5 if angry else 0), (x - bw * 0.6, y + 5, bw * 1.2, bh * 0.85))
    pygame.draw.ellipse(surf, WHITE, (x - bw * 0.6, y - bh * 0.75, 30, 18))  # luccichio
    # braccini
    wave = math.sin(t * 10) * 10 if fx.get("love", 0) > 0 or jump > 0 else 0
    for side in (-1, 1):
        pygame.draw.ellipse(surf, dark, (x + side * (bw - 8) - 14, y + 10 - (wave if side > 0 else -wave) * 0.5, 28, 40))

    # guance
    if mood in ("happy", "sleep") or fx.get("love", 0) > 0 or angry:
        c = (255, 90, 90) if angry else CHEEK
        for side in (-1, 1):
            pygame.draw.ellipse(surf, c, (x + side * 62 - 16, y + 4, 32, 18))

    # occhi
    ey = y - 22
    blink = (t % 3.7) < 0.13
    love = (fx.get("love", 0) > 0 or jump > 0) and not angry
    for side in (-1, 1):
        ex = x + side * 36
        if mood == "sleep":
            pygame.draw.arc(surf, INK, (ex - 15, ey - 6, 30, 22), math.pi * 1.05, math.pi * 1.95, 4)
        elif love:
            pygame.draw.arc(surf, INK, (ex - 15, ey - 4, 30, 26), math.pi * 0.1, math.pi * 0.9, 5)
        elif blink:
            pygame.draw.line(surf, INK, (ex - 13, ey + 4), (ex + 13, ey + 4), 4)
        else:
            pygame.draw.ellipse(surf, WHITE, (ex - 14, ey - 16, 28, 36))
            pr = 7 if angry else 10
            look = math.sin(t * 0.7) * 3
            pygame.draw.circle(surf, INK, (int(ex + look), int(ey + 4)), pr)
            pygame.draw.circle(surf, WHITE, (int(ex + look + 3), int(ey)), 3)
        # sopracciglia
        if angry:
            pygame.draw.line(surf, INK, (ex - side * 10, ey - 14), (ex + side * 18, ey - 26), 6)
        elif mood in ("sad", "hungry", "tired"):
            pygame.draw.line(surf, INK, (ex - side * 10, ey - 26), (ex + side * 16, ey - 18), 4)

    # bocca
    my = y + 20
    eat = fx.get("eat", 0)
    if eat > 0:
        h = 22 if int(eat * 8) % 2 else 6
        pygame.draw.ellipse(surf, INK, (x - 14, my - h // 2 + 6, 28, h))
    elif mood == "sleep":
        r = 5 + breathe * 2
        pygame.draw.ellipse(surf, INK, (x - r, my + 4, r * 2, r * 1.6))
    elif mood == "angry":
        pygame.draw.arc(surf, INK, (x - 20, my + 6, 40, 24), math.pi * 0.15, math.pi * 0.85, 5)
    elif mood == "hungry":
        pygame.draw.ellipse(surf, INK, (x - 9, my + 2, 18, 20))
    elif mood in ("sad", "tired"):
        pygame.draw.arc(surf, INK, (x - 16, my + 8, 32, 20), math.pi * 0.15, math.pi * 0.85, 4)
        if mood == "sad":  # lacrimuccia
            ty = ey + 18 + (t * 30) % 30
            pygame.draw.circle(surf, (120, 180, 255), (int(x + 40), int(ty)), 5)
    else:
        pygame.draw.arc(surf, INK, (x - 20, my - 8, 40, 28), math.pi * 1.1, math.pi * 1.9, 5)
        if love:
            pygame.draw.ellipse(surf, (230, 90, 110), (x - 8, my + 8, 16, 10))
    return x, y - bh


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
                heart(ctx.surf, x, y, 6 + 6 * k)
            elif kind == "z":
                ctx.text("z", int(x + math.sin(t * 3 + y) * 6), int(y), int(22 + (1 - k) * 22), (200, 210, 255), bold=True)
            elif kind == "steam":
                pygame.draw.circle(ctx.surf, (250, 250, 250), (int(x), int(y)), max(1, int(14 * (1 - k) + 4)), 3)
            elif kind == "note":
                ctx.text("~", int(x), int(y), 40, (120, 110, 200), bold=True)
            elif kind == "crumb":
                pygame.draw.circle(ctx.surf, (200, 150, 80), (int(x), int(y)), 3)


# ---------------------------------------------------------------- HUD

def stat_bar(ctx, x, y, icon, value):
    icon(ctx.surf, x, y + 10, 10)
    pygame.draw.rect(ctx.surf, (255, 255, 255), (x + 20, y + 2, 110, 16), border_radius=8)
    col = (110, 200, 120) if value > 50 else (250, 190, 60) if value > 25 else (240, 90, 90)
    pygame.draw.rect(ctx.surf, col, (x + 22, y + 4, max(0, int(106 * value / 100)), 12), border_radius=6)
    pygame.draw.rect(ctx.surf, INK, (x + 20, y + 2, 110, 16), 2, border_radius=8)


def bubble(ctx, text, x, y):
    f = ctx.font(30, True)
    tw, th = f.size(text)
    bx = max(10, min(W - tw - 34, x - tw // 2 - 12))
    by = y - th - 30
    rect = pygame.Rect(bx, by, tw + 24, th + 16)
    pygame.draw.polygon(ctx.surf, WHITE, [(x - 10, rect.bottom - 2), (x + 10, rect.bottom - 2), (x, rect.bottom + 14)])
    pygame.draw.rect(ctx.surf, WHITE, rect, border_radius=14)
    pygame.draw.rect(ctx.surf, INK, rect, 3, border_radius=14)
    ctx.text(text, rect.x + 12, rect.y + 9, 30, INK, bold=True)


def action_icon(surf, i, x, y, night, bg=WHITE):
    if i == 0:
        apple(surf, x, y, 14)
    elif i == 1:
        ball(surf, x, y, 14)
    elif i == 2:
        heart(surf, x, y - 6, 12)
    else:
        if night:
            sun(surf, x, y, 10)
        else:
            moon(surf, x, y, 14, bg, (110, 100, 180))


# ---------------------------------------------------------------- app

class App:
    def __init__(self, ctx):
        self.ctx = ctx
        self.pet = Pet()
        if not self.pet.load():
            self.say("Ciao! Sono Bobo!", 4)
        self.t = 0.0
        self.sel = 0
        self.mode = "main"   # main / food / game / reveal
        self.food_sel = 0
        self.fx = {}
        self.parts = Particles()
        self.msg, self.msg_until = "", 0.0
        self.next_talk = 6.0
        self.next_puff = 0.0
        self.game = None
        self.last_save = 0.0
        self.head = (W // 2, 150)
        if not self.msg:
            self.say(random.choice(["Bentornato!", "Mi sei mancato!", "Eccoti!"]) if not self.pet.asleep else "Zzz...", 3)

    def say(self, text, secs=2.5):
        self.msg, self.msg_until = text, getattr(self, "t", 0.0) + secs

    def hearts(self, n=5):
        x, y = self.head
        for _ in range(n):
            self.parts.add("heart", x + random.uniform(-70, 70), y + random.uniform(0, 60),
                           random.uniform(-20, 20), random.uniform(-70, -40), 1.4)

    # --- azioni
    def do_action(self, i):
        p = self.pet
        if i == 0:
            if p.asleep:
                self.say("Zzz... (dorme)")
            else:
                self.mode, self.food_sel = "food", 0
        elif i == 1:
            if p.asleep:
                self.say("Zzz... (dorme)")
            elif p.mood() == "angry":
                self.say("Non gioco con te! Hmpf!")
            elif p.energy < 15:
                self.say("Troppo stanco...")
            else:
                self.game = {"hand": random.randint(0, 1), "pick": None, "until": 0}
                self.mode = "game"
                self.say("Dov'e' il biscotto?", 30)
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
            self.say("Sono pieno! Basta!")
            return
        p.food = clamp(p.food + food)
        p.fun = clamp(p.fun + fun)
        p.energy = clamp(p.energy + energy)
        self.fx["eat"] = 1.6
        self.fx["food_icon"] = k
        self.say(line)
        x, y = self.head
        for _ in range(6):
            self.parts.add("crumb", x + random.uniform(-15, 15), y + 125,
                           random.uniform(-60, 60), random.uniform(-30, 30), 0.8)

    def cuddle(self):
        p = self.pet
        now = self.t
        p.cuddles = [c for c in p.cuddles if now - c < 10] + [now]
        if p.asleep:
            self.parts.add("heart", self.head[0], self.head[1] + 30, 0, -40, 1.5)
            self.say("Mmm... (sorride nel sonno)")
            return
        if p.anger > 0:
            p.anger = max(0.0, p.anger - 4)
            self.say("...va bene, ti perdono" if p.anger == 0 else "Hmpf... ancora un po'")
            if p.anger == 0:
                self.hearts(3)
            return
        if len(p.cuddles) > 6:
            self.say("Basta coccole, mi spettini!")
            return
        p.fun = clamp(p.fun + 8)
        self.fx["love"] = 1.6
        self.hearts()
        self.say(random.choice(["Hihi!", "Che bello!", "Ancora!", "Ti voglio bene!"]))

    def toggle_light(self):
        p = self.pet
        if p.asleep:
            p.asleep = False
            if p.energy < 60:
                p.anger = 6.0
                self.say("Stavo dormendo!! Grrr!")
            else:
                self.say("Buongiorno!")
        else:
            if p.energy > 75 and p.mood() != "angry":
                self.say("Non ho sonno!")
            else:
                p.asleep = True
                self.say("Buonanotte...")

    def poke(self):
        p = self.pet
        now = self.t
        self.fx["poke"] = 0.4
        if p.asleep:
            if p.energy < 60:
                p.asleep = False
                p.anger = 8.0
                self.say("Ma insomma! Dormivo!")
            else:
                p.asleep = False
                self.say("Eh? Gia' mattina?")
            return
        p.pokes = [x for x in p.pokes if now - x < 4] + [now]
        if len(p.pokes) >= 3:
            p.anger = 10.0
            self.fx.pop("love", None)
            self.fx.pop("jump", None)
            p.fun = clamp(p.fun - 10)
            p.pokes = []
            self.say("Grrr! BASTA!")
        elif p.anger > 0:
            p.anger += 3
            self.say("Lasciami stare!")
        else:
            self.say(random.choice(["Ehi!", "Ahi!", "Che c'e'?", "Hihi, solletico!"]))

    # --- ciclo
    def update(self, dt):
        p = self.pet
        was_asleep = p.asleep
        p.tick(dt)
        if p.asleep and p.energy >= 100:
            p.asleep = False
            self.say("Buongiorno! Ho dormito benissimo!")
        if not was_asleep and not p.asleep and p.energy <= 0:
            p.asleep = True
            self.say("Crollo... zzz")
        for k in list(self.fx):
            if isinstance(self.fx[k], float):
                self.fx[k] -= dt
                if self.fx[k] <= 0:
                    del self.fx[k]
        self.parts.update(dt)
        mood = p.mood()
        x, y = self.head
        if self.t >= self.next_puff:
            if mood == "sleep":
                self.parts.add("z", x + 60, y + 40, 25, -35, 2.4)
                self.next_puff = self.t + 1.3
            elif mood == "angry":
                for side in (-1, 1):
                    self.parts.add("steam", x + side * 70, y + 10, side * 40, -60, 0.9)
                self.next_puff = self.t + 0.5
            elif mood == "happy" and random.random() < 0.3:
                self.parts.add("note", x + random.choice((-90, 90)), y + 40, 0, -30, 1.5)
                self.next_puff = self.t + 3
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
            elif a == "RIGHT":
                self.food_sel = (self.food_sel + 1) % len(FOODS)
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
                    self.say("Bravissimo!! Hai vinto!")
                else:
                    p.fun = clamp(p.fun + 8)
                    self.say("Ehehe, era di qua!")
                self.mode = "reveal"
            elif a == "B":
                self.mode = "main"
                self.say("Va bene, dopo!")
            return True
        if self.mode == "reveal":
            return True
        if a == "LEFT":
            self.sel = (self.sel - 1) % len(ACTIONS)
        elif a == "RIGHT":
            self.sel = (self.sel + 1) % len(ACTIONS)
        elif a == "A":
            self.do_action(self.sel)
        elif a == "X":
            self.poke()
        elif a == "B":
            return False
        return True

    def draw(self):
        ctx, p, t = self.ctx, self.pet, self.t
        night = p.asleep
        draw_room(ctx.surf, t, night)
        mood = p.mood()
        self.head = draw_pet(ctx.surf, W // 2 - 20, 250, t, mood, self.fx)
        hx, hy = self.head
        if "eat" in self.fx:
            k = self.fx["eat"] / 1.6
            FOOD_ICONS[self.fx.get("food_icon", 0)](ctx.surf, int(hx), int(hy + 158), max(4, int(18 * k)))
        if self.mode in ("game", "reveal"):
            g = self.game
            for i, bx in enumerate((W // 2 - 200, W // 2 + 160)):
                sel = g["pick"] == i
                pygame.draw.rect(ctx.surf, (250, 210, 230), (bx - 34, 250, 68, 56), border_radius=10)
                pygame.draw.rect(ctx.surf, INK, (bx - 34, 250, 68, 56), 3 if not sel else 5, border_radius=10)
                if self.mode == "reveal" and i == g["hand"]:
                    cookie(ctx.surf, bx, 232, 18)
                else:
                    pygame.draw.rect(ctx.surf, (240, 100, 130), (bx - 6, 250, 12, 56))
                ctx.text("<" if i == 0 else ">", bx, 312, 40, INK, align="center", bold=True)
        self.parts.draw(ctx, t)
        if t < self.msg_until and self.msg:
            bubble(ctx, self.msg, int(hx), int(hy - 40))

        # HUD
        pygame.draw.rect(ctx.surf, (255, 255, 255) if not night else (60, 60, 95), (0, 0, W, 34))
        stat_bar(ctx, 14, 7, apple, p.food)
        stat_bar(ctx, 164, 7, bolt, p.energy)
        stat_bar(ctx, 314, 7, lambda s, x, y, z: heart(s, x, y - 5, 9), p.fun)
        ctx.text("Bobo, %d g" % p.days(), W - 14, 9, 26, INK if not night else WHITE, align="right", bold=True)

        # barra azioni / scelta cibo
        y0 = 400
        if self.mode == "food":
            items = [f[0] for f in FOODS]
            icons = FOOD_ICONS
            sel = self.food_sel
        else:
            items, icons, sel = ACTIONS, None, self.sel
        n = len(items)
        bw = 140 if n == 4 else 180
        gap = (W - n * bw) // (n + 1)
        for i, label in enumerate(items):
            x = gap + i * (bw + gap)
            on = i == sel and self.mode in ("main", "food")
            col = (255, 235, 150) if on else ((255, 255, 255) if not night else (70, 70, 110))
            pygame.draw.rect(ctx.surf, col, (x, y0, bw, 52), border_radius=14)
            pygame.draw.rect(ctx.surf, INK, (x, y0, bw, 52), 4 if on else 2, border_radius=14)
            if icons:
                icons[i](ctx.surf, x + 26, y0 + 26, 13)
            else:
                action_icon(ctx.surf, i, x + 26, y0 + 28, night, col)
            if label == "Luce" and night:
                label = "Sveglia"
            ctx.text(label, x + 46, y0 + 15, 28, INK if (on or not night) else WHITE, bold=on)
        hint = {"main": "SX/DX scegli   A fai   X stuzzica   B esci",
                "food": "SX/DX scegli cibo   A dai   B annulla",
                "game": "SINISTRA o DESTRA?   B lascia stare",
                "reveal": ""}[self.mode]
        ctx.text(hint, W // 2, 458, 22, (130, 120, 140) if not night else (170, 170, 210), align="center")


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
