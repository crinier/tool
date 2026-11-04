"""Widget pronti: menu a lista, modulo con campi numerici, messaggi."""
import pygame

from .core import W, H, FG, DIM, ACCENT, OK, BAD, PANEL, QuitApp


def menu(ctx, title, items, subtitle=None, index=0):
    """Lista verticale. items = lista di stringhe o (testo, descrizione).
    Ritorna l'indice scelto con A, oppure None con B."""
    rows = [(it, None) if isinstance(it, str) else it for it in items]
    if not rows:
        message(ctx, title, "Niente da mostrare.")
        return None
    index = max(0, min(index, len(rows) - 1))
    visible = 8
    top = 0
    ctx.input.flush()
    while True:
        for a in ctx.input.poll():
            if a == "UP":
                index = (index - 1) % len(rows)
            elif a == "DOWN":
                index = (index + 1) % len(rows)
            elif a == "L1":
                index = max(0, index - visible)
            elif a == "R1":
                index = min(len(rows) - 1, index + visible)
            elif a in ("A", "START"):
                return index
            elif a == "B":
                return None
        top = min(max(top, index - visible + 1), index)
        ctx.header(title, "A scegli   B indietro   SELECT+START esci")
        y = 66
        if subtitle:
            ctx.text(subtitle, 20, y, 24, DIM)
            y += 28
        for i in range(top, min(len(rows), top + visible)):
            label, desc = rows[i]
            sel = i == index
            if sel:
                pygame.draw.rect(ctx.surf, PANEL, (12, y - 4, W - 24, 42), border_radius=8)
                pygame.draw.rect(ctx.surf, ACCENT, (12, y - 4, 6, 42), border_radius=3)
            ctx.text(label, 30, y + 4, 34, ACCENT if sel else FG)
            y += 46
        desc = rows[index][1]
        if desc:
            ctx.text(desc, W // 2, H - 64, 24, DIM, align="center")
        ctx.flip()


class Field:
    def __init__(self, label, value, step=1.0, big=10.0, lo=None, hi=None,
                 fmt="{:.0f}", unit=""):
        self.label, self.value = label, value
        self.step, self.big, self.lo, self.hi = step, big, lo, hi
        self.fmt, self.unit = fmt, unit

    def add(self, delta):
        v = round(self.value + delta, 6)
        if self.lo is not None:
            v = max(self.lo, v)
        if self.hi is not None:
            v = min(self.hi, v)
        self.value = v

    def show(self):
        return self.fmt.format(self.value) + (" " + self.unit if self.unit else "")


def form(ctx, title, fields, compute):
    """Campi modificabili + risultati calcolati al volo.
    SU/GIU scegli campo, SX/DX +-passo, L1/R1 +-passo grande, B esci.
    compute(valori) -> lista di (etichetta, testo[, colore])."""
    index = 0
    ctx.input.flush()
    while True:
        for a in ctx.input.poll():
            f = fields[index]
            if a == "UP":
                index = (index - 1) % len(fields)
            elif a == "DOWN":
                index = (index + 1) % len(fields)
            elif a == "LEFT":
                f.add(-f.step)
            elif a == "RIGHT":
                f.add(f.step)
            elif a == "L1":
                f.add(-f.big)
            elif a == "R1":
                f.add(f.big)
            elif a == "B":
                return [x.value for x in fields]
        ctx.header(title, "SX/DX valore   L1/R1 veloce   B indietro")
        y = 66
        for i, f in enumerate(fields):
            sel = i == index
            if sel:
                pygame.draw.rect(ctx.surf, PANEL, (12, y - 4, W - 24, 40), border_radius=8)
            ctx.text(f.label, 26, y + 4, 30, ACCENT if sel else DIM)
            v = ("< " + f.show() + " >") if sel else f.show()
            ctx.text(v, W - 26, y + 2, 34, FG, align="right", bold=sel)
            y += 44
        y += 8
        pygame.draw.line(ctx.surf, PANEL, (20, y), (W - 20, y), 2)
        y += 12
        try:
            results = compute([x.value for x in fields])
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            results = [("Errore", str(e), BAD)]
        for r in results:
            color = r[2] if len(r) > 2 else OK
            ctx.text(r[0], 26, y + 4, 28, DIM)
            ctx.text(r[1], W - 26, y, 36, color, align="right", bold=True)
            y += 40
        ctx.flip()


def message(ctx, title, text, color=FG):
    """Mostra un testo (anche multi-riga) finche' non premi A o B."""
    lines = []
    for par in str(text).split("\n"):
        words, cur = par.split(" "), ""
        for w in words:
            test = (cur + " " + w).strip()
            if ctx.font(26).size(test)[0] > W - 40 and cur:
                lines.append(cur)
                cur = w
            else:
                cur = test
        lines.append(cur)
    scroll = 0
    ctx.input.flush()
    while True:
        try:
            acts = ctx.input.poll()
        except QuitApp:
            return
        for a in acts:
            if a in ("A", "B", "START"):
                return
            if a == "DOWN":
                scroll = min(scroll + 1, max(0, len(lines) - 13))
            if a == "UP":
                scroll = max(0, scroll - 1)
        ctx.header(title, "A / B continua")
        y = 66
        for ln in lines[scroll:scroll + 13]:
            ctx.text(ln, 20, y, 26, color)
            y += 28
        ctx.flip()
