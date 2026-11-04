"""Nucleo del mini-framework: schermo, input, testo.

Tutto viene disegnato su una superficie logica 640x480 (la risoluzione della
R36S originale) e poi scalato sullo schermo reale, cosi' le app funzionano
uguale anche sui cloni con schermi diversi e sul PC.
"""
import json
import os
import time

import pygame

from .compat import joy_id

W, H = 640, 480
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# Azioni astratte: le app ragionano solo con questi nomi.
ACTIONS = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "X", "Y",
           "L1", "R1", "L2", "R2", "SELECT", "START"]
REPEATABLE = {"UP", "DOWN", "LEFT", "RIGHT", "L1", "R1"}

# Mappatura di partenza (gamepad "GO-Super" di ArkOS sulla R36S originale).
# Sui cloni puo' essere diversa: per questo c'e' l'app "Configura tasti".
DEFAULT_BINDINGS = {
    "b8": "UP", "b9": "DOWN", "b10": "LEFT", "b11": "RIGHT",
    "b1": "A", "b0": "B", "b2": "X", "b3": "Y",
    "b4": "L1", "b5": "R1", "b6": "L2", "b7": "R2",
    "b12": "SELECT", "b13": "START",
    "h0:up": "UP", "h0:down": "DOWN", "h0:left": "LEFT", "h0:right": "RIGHT",
    "a1-": "UP", "a1+": "DOWN", "a0-": "LEFT", "a0+": "RIGHT",
}

# Tastiera, per provare le app sul PC.
KEYBOARD = {
    pygame.K_UP: "UP", pygame.K_DOWN: "DOWN",
    pygame.K_LEFT: "LEFT", pygame.K_RIGHT: "RIGHT",
    pygame.K_z: "A", pygame.K_RETURN: "A",
    pygame.K_x: "B", pygame.K_BACKSPACE: "B",
    pygame.K_c: "X", pygame.K_v: "Y",
    pygame.K_q: "L1", pygame.K_e: "R1",
    pygame.K_1: "L2", pygame.K_3: "R2",
    pygame.K_TAB: "SELECT", pygame.K_SPACE: "START",
}

# Colori
BG = (16, 18, 24)
FG = (230, 232, 238)
DIM = (130, 136, 150)
ACCENT = (255, 176, 46)
OK = (110, 210, 120)
BAD = (240, 90, 90)
PANEL = (32, 36, 46)


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_config(cfg):
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2, sort_keys=True)
    os.replace(tmp, CONFIG_PATH)


class QuitApp(Exception):
    """Sollevata con SELECT+START: chiude l'app corrente."""


class QuitAll(Exception):
    """Chiusura totale (finestra chiusa sul PC / ESC)."""


class Input:
    REPEAT_DELAY = 0.35
    REPEAT_RATE = 0.07
    AXIS_DEAD = 0.5

    def __init__(self, bindings):
        self.bindings = dict(bindings)
        self.held = set()
        self._next_repeat = {}
        self._axis_state = {}
        self._hat_state = {}
        self.joysticks = {}
        pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            self._add_joy(i)

    def _add_joy(self, index):
        try:
            j = pygame.joystick.Joystick(index)
            j.init()
            self.joysticks[joy_id(j)] = j
        except pygame.error:
            pass

    @staticmethod
    def raw_codes(event, axis_state=None, hat_state=None):
        """Converte un evento joystick in codici grezzi (premuti, rilasciati)."""
        down, up = [], []
        if event.type == pygame.JOYBUTTONDOWN:
            down.append("b%d" % event.button)
        elif event.type == pygame.JOYBUTTONUP:
            up.append("b%d" % event.button)
        elif event.type == pygame.JOYHATMOTION:
            x, y = event.value
            now = set()
            if y > 0: now.add("h%d:up" % event.hat)
            if y < 0: now.add("h%d:down" % event.hat)
            if x < 0: now.add("h%d:left" % event.hat)
            if x > 0: now.add("h%d:right" % event.hat)
            prev = hat_state.get(event.hat, set()) if hat_state is not None else set()
            down += sorted(now - prev)
            up += sorted(prev - now)
            if hat_state is not None:
                hat_state[event.hat] = now
        elif event.type == pygame.JOYAXISMOTION:
            v = event.value
            now = None
            if v < -Input.AXIS_DEAD: now = "a%d-" % event.axis
            elif v > Input.AXIS_DEAD: now = "a%d+" % event.axis
            prev = axis_state.get(event.axis) if axis_state is not None else None
            if now != prev:
                if prev: up.append(prev)
                if now: down.append(now)
            if axis_state is not None:
                axis_state[event.axis] = now
        return down, up

    def poll(self):
        """Ritorna la lista di azioni 'premute' in questo frame (con auto-repeat)."""
        pressed = []
        now = time.monotonic()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise QuitAll()
            if event.type == pygame.JOYDEVICEADDED:
                self._add_joy(event.device_index)
                continue
            if event.type == pygame.JOYDEVICEREMOVED:
                self.joysticks.pop(getattr(event, "instance_id", None), None)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise QuitAll()
                act = KEYBOARD.get(event.key)
                if act:
                    self._press(act, now, pressed)
                continue
            if event.type == pygame.KEYUP:
                act = KEYBOARD.get(event.key)
                if act:
                    self._release(act)
                continue
            down, up = self.raw_codes(event, self._axis_state, self._hat_state)
            for code in up:
                act = self.bindings.get(code)
                if act:
                    self._release(act)
            for code in down:
                act = self.bindings.get(code)
                if act:
                    self._press(act, now, pressed)

        for act in list(self.held):
            if act in REPEATABLE and now >= self._next_repeat.get(act, now + 1):
                pressed.append(act)
                self._next_repeat[act] = now + self.REPEAT_RATE

        if "SELECT" in self.held and "START" in self.held:
            self.held.clear()
            raise QuitApp()
        return pressed

    def _press(self, act, now, pressed):
        if act not in self.held:
            self.held.add(act)
            pressed.append(act)
            self._next_repeat[act] = now + self.REPEAT_DELAY

    def _release(self, act):
        self.held.discard(act)
        self._next_repeat.pop(act, None)

    def flush(self):
        pygame.event.clear()
        self.held.clear()


class Ctx:
    """Contesto passato a ogni app: ctx.surf, ctx.input, ctx.text(), ctx.flip()..."""

    def __init__(self):
        os.environ.setdefault("SDL_NOMOUSE", "1")
        try:
            pygame.mixer.pre_init(22050, -16, 1, 1024)
        except pygame.error:
            pass
        pygame.init()
        windowed = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
                        or os.environ.get("R36_WINDOW"))
        if windowed:
            self.display = pygame.display.set_mode((W, H))
        else:
            self.display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("R36 Tool")
        pygame.mouse.set_visible(False)
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self._fonts = {}
        self.config = load_config()
        self.first_run = self.config is None
        if self.config is None:
            self.config = {"bindings": DEFAULT_BINDINGS}
        self.input = Input(self.config.get("bindings", DEFAULT_BINDINGS))
        self._compute_scale()

    def _compute_scale(self):
        dw, dh = self.display.get_size()
        s = min(dw / W, dh / H)
        self._scaled = (max(1, int(W * s)), max(1, int(H * s)))
        self._offset = ((dw - self._scaled[0]) // 2, (dh - self._scaled[1]) // 2)

    def set_bindings(self, bindings):
        self.config["bindings"] = bindings
        self.input.bindings = dict(bindings)
        save_config(self.config)

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self._fonts:
            f = pygame.font.Font(None, size)
            f.set_bold(bold)
            self._fonts[key] = f
        return self._fonts[key]

    def text(self, s, x, y, size=32, color=FG, align="left", bold=False):
        img = self.font(size, bold).render(str(s), True, color)
        r = img.get_rect()
        if align == "center":
            r.midtop = (x, y)
        elif align == "right":
            r.topright = (x, y)
        else:
            r.topleft = (x, y)
        self.surf.blit(img, r)
        return r

    def header(self, title, hint=None):
        self.surf.fill(BG)
        pygame.draw.rect(self.surf, PANEL, (0, 0, W, 52))
        self.text(title, 20, 14, 38, ACCENT, bold=True)
        if hint:
            pygame.draw.rect(self.surf, PANEL, (0, H - 34, W, 34))
            self.text(hint, W // 2, H - 27, 24, DIM, align="center")

    def flip(self, fps=30):
        if self._scaled == (W, H) and self._offset == (0, 0):
            self.display.blit(self.surf, (0, 0))
        else:
            self.display.fill((0, 0, 0))
            self.display.blit(pygame.transform.smoothscale(self.surf, self._scaled), self._offset)
        pygame.display.flip()
        self.clock.tick(fps)
