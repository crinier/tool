"""Procedura guidata: premi ogni tasto quando richiesto, salva in config.json.
Parte da sola al primo avvio (quando config.json non esiste)."""
import time

import pygame

import r36
from r36.core import Input

NAME = "Configura tasti"
DESCRIPTION = "Rifai la mappatura dei tasti (utile sui cloni)"

STEPS = [
    ("UP", "Croce SU"), ("DOWN", "Croce GIU"), ("LEFT", "Croce SINISTRA"),
    ("RIGHT", "Croce DESTRA"), ("A", "Tasto A"), ("B", "Tasto B"),
    ("X", "Tasto X"), ("Y", "Tasto Y"), ("L1", "Dorsale L1"), ("R1", "Dorsale R1"),
    ("L2", "Dorsale L2"), ("R2", "Dorsale R2"), ("SELECT", "SELECT"), ("START", "START"),
]
TIMEOUT = 8.0


def wait_code(ctx, label, n, total, taken):
    """Aspetta un input joystick nuovo. None = saltato per timeout."""
    deadline = time.monotonic() + TIMEOUT
    axis_state, hat_state = {}, {}
    pygame.event.clear()
    while True:
        left = deadline - time.monotonic()
        if left <= 0:
            return None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                raise r36.QuitAll()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                raise r36.QuitApp()
            if ev.type == pygame.JOYDEVICEADDED:
                ctx.input._add_joy(ev.device_index)
            down, _ = Input.raw_codes(ev, axis_state, hat_state)
            for code in down:
                if code not in taken:
                    return code
        ctx.header("Configura tasti  %d/%d" % (n, total),
                   "Non hai il tasto? aspetta e si salta   (ESC annulla)")
        ctx.text("Premi:", r36.W // 2, 130, 40, r36.DIM, align="center")
        ctx.text(label, r36.W // 2, 180, 80, r36.ACCENT, align="center", bold=True)
        ctx.text("%d s" % (int(left) + 1), r36.W // 2, 290, 36, r36.DIM, align="center")
        if not ctx.input.joysticks:
            ctx.text("Nessun gamepad trovato!", r36.W // 2, 350, 30, r36.BAD, align="center")
        ctx.flip()


def run(ctx):
    bindings = {}
    for n, (act, label) in enumerate(STEPS, 1):
        code = wait_code(ctx, label, n, len(STEPS), bindings)
        if code:
            bindings[code] = act
    # tieni lo stick sinistro come croce se non e' stato usato altro
    for code, act in (("a1-", "UP"), ("a1+", "DOWN"), ("a0-", "LEFT"), ("a0+", "RIGHT")):
        bindings.setdefault(code, act)
    if not any(v == "A" for v in bindings.values()) or not any(v == "B" for v in bindings.values()):
        r36.message(ctx, "Configura tasti",
                    "A o B non assegnati: mappatura NON salvata, uso quella precedente.", r36.BAD)
        return
    ctx.set_bindings(bindings)
    lines = ["%-7s <- %s" % (v, k) for k, v in sorted(bindings.items(), key=lambda kv: kv[1])]
    r36.message(ctx, "Salvato!", "Mappatura salvata in config.json\n\n" + "\n".join(lines), r36.OK)
