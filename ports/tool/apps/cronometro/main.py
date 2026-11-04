"""Cronometro con giri."""
import time

import r36

NAME = "Cronometro"
DESCRIPTION = "A avvia/ferma, X giro, Y azzera"


def fmt(t):
    m, s = divmod(t, 60)
    return "%02d:%05.2f" % (m, s)


def run(ctx):
    start, acc, running, laps = 0.0, 0.0, False, []
    ctx.input.flush()
    while True:
        now = time.monotonic()
        for a in ctx.input.poll():
            if a == "A":
                if running:
                    acc += now - start
                else:
                    start = now
                running = not running
            elif a == "X" and running:
                laps.append(acc + now - start)
            elif a == "Y":
                start, acc, running, laps = now, 0.0, False, []
            elif a == "B":
                return
        t = acc + (now - start if running else 0)
        ctx.header(NAME, "A start/stop   X giro   Y azzera   B esci")
        ctx.text(fmt(t), r36.W // 2, 90, 130, r36.OK if running else r36.FG, align="center", bold=True)
        y = 210
        for n, lap in list(enumerate(laps, 1))[-6:]:
            ctx.text("Giro %d" % n, 160, y, 32, r36.DIM)
            ctx.text(fmt(lap), 480, y, 32, r36.FG, align="right")
            y += 36
        ctx.flip()
