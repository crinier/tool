"""Suoni sintetizzati al volo: nessun file audio, nessuna dipendenza (no numpy).

    from r36 import sound
    sound.play("chirp")
    sound.play(sound.synth([(880, 1200, 0.1, "sine")]))

Se l'audio non funziona (niente scheda audio, driver mancante) le funzioni
non fanno nulla e l'app va avanti muta.
"""
import array
import math
import random

import pygame

_ok = None
_rate = 22050
_channels = 1
_cache = {}
enabled = True


def _init():
    global _ok, _rate, _channels
    if _ok is not None:
        return _ok
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(22050, -16, 1, 1024)
        rate, size, channels = pygame.mixer.get_init()
        if abs(size) != 16:
            pygame.mixer.quit()
            pygame.mixer.init(22050, -16, 1, 1024)
            rate, size, channels = pygame.mixer.get_init()
        _rate, _channels = rate, channels
        _ok = abs(size) == 16
    except (pygame.error, TypeError):
        _ok = False
    return _ok


def synth(segments, volume=0.35):
    """segments: lista di (freq_inizio, freq_fine, durata_s, forma).
    forma: "sine", "square", "tri", "noise"; freq 0 = silenzio."""
    if not _init():
        return None
    data = array.array("h")
    amp = int(32767 * max(0.0, min(1.0, volume)))
    for f0, f1, dur, wave in segments:
        n = max(1, int(dur * _rate))
        attack = max(1, min(n // 4, int(0.006 * _rate)))
        release = max(1, n // 3)
        phase = 0.0
        for i in range(n):
            if f0 == 0:
                s = 0.0
            else:
                f = f0 + (f1 - f0) * i / n
                phase += f / _rate
                p = phase % 1.0
                if wave == "square":
                    s = 0.6 if p < 0.5 else -0.6
                elif wave == "tri":
                    s = 4 * abs(p - 0.5) - 1
                elif wave == "noise":
                    s = random.uniform(-1, 1)
                else:
                    s = math.sin(2 * math.pi * p)
            env = min(1.0, i / attack, (n - i) / release)
            v = int(s * env * amp)
            for _ in range(_channels):
                data.append(v)
    try:
        return pygame.mixer.Sound(buffer=data.tobytes())
    except pygame.error:
        return None


# Libreria di versetti pronti
PRESETS = {
    "tick":   [(2200, 2200, 0.015, "sine")],
    "chirp":  [(900, 1400, 0.07, "sine"), (0, 0, 0.02, "sine"), (1200, 1750, 0.08, "sine")],
    "boop":   [(1500, 550, 0.08, "sine")],
    "love":   [(880, 880, 0.09, "sine"), (1175, 1175, 0.09, "sine"), (1568, 1568, 0.16, "sine")],
    "eat":    [(0, 0, 0.02, "sine"), (300, 200, 0.05, "noise"), (0, 0, 0.07, "sine"),
               (300, 200, 0.05, "noise"), (0, 0, 0.07, "sine"), (300, 200, 0.05, "noise"),
               (0, 0, 0.05, "sine"), (700, 1100, 0.07, "sine")],
    "angry":  [(190, 120, 0.18, "square"), (0, 0, 0.03, "sine"), (170, 100, 0.25, "square")],
    "refuse": [(420, 380, 0.09, "tri"), (0, 0, 0.05, "sine"), (330, 300, 0.12, "tri")],
    "sleep":  [(700, 260, 0.6, "sine")],
    "wake":   [(300, 950, 0.3, "sine"), (1100, 1300, 0.08, "sine")],
    "snore":  [(110, 90, 0.45, "tri")],
    "win":    [(523, 523, 0.1, "sine"), (659, 659, 0.1, "sine"), (784, 784, 0.1, "sine"),
               (1047, 1047, 0.25, "sine")],
    "lose":   [(500, 480, 0.15, "tri"), (380, 300, 0.3, "tri")],
    "sad":    [(600, 420, 0.35, "sine")],
}
_VOL = {"tick": 0.15, "snore": 0.12, "angry": 0.25, "eat": 0.3}


def get(name):
    if name not in _cache:
        _cache[name] = synth(PRESETS[name], _VOL.get(name, 0.35))
    return _cache[name]


def babble(mood="happy", syllables=None):
    """Versetto 'parlato' casuale, tipo cinguettio, che dipende dall'umore."""
    base = {"happy": 950, "sad": 520, "angry": 260, "hungry": 700, "tired": 480}.get(mood, 900)
    wave = "square" if mood == "angry" else "sine"
    segs = []
    for _ in range(syllables or random.randint(2, 4)):
        f = base * random.uniform(0.8, 1.35)
        segs.append((f, f * random.uniform(0.85, 1.25), random.uniform(0.045, 0.08), wave))
        segs.append((0, 0, 0.025, "sine"))
    return synth(segs, 0.18 if mood == "angry" else 0.28)


def play(snd):
    if not enabled:
        return
    if isinstance(snd, str):
        snd = get(snd)
    if snd is not None:
        try:
            snd.play()
        except pygame.error:
            pass
