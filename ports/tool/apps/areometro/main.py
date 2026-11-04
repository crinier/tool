"""Areometro (densimetro) per birra / vino / mosto."""
import r36
from r36 import Field

NAME = "Areometro"
DESCRIPTION = "Correzione temperatura, grado alcolico, SG/Plato/Brix"


def c_to_f(c):
    return c * 9 / 5 + 32


def _poly(t_f):
    return (1.00130346 - 0.000134722124 * t_f + 0.00000204052596 * t_f ** 2
            - 0.00000000232820948 * t_f ** 3)


def correct_sg(sg, temp_c, calib_c):
    """Corregge la lettura dell'areometro per la temperatura del campione."""
    return sg * _poly(c_to_f(temp_c)) / _poly(c_to_f(calib_c))


def sg_to_plato(sg):
    return -616.868 + 1111.14 * sg - 630.272 * sg ** 2 + 135.997 * sg ** 3


def sg_to_brix(sg):
    return ((182.4601 * sg - 775.6821) * sg + 1262.7794) * sg - 669.5622


def brix_to_sg(brix):
    return 1 + brix / (258.6 - (brix / 258.2) * 227.1)


def abv_simple(og, fg):
    return (og - fg) * 131.25


def abv_alt(og, fg):
    return (76.08 * (og - fg) / (1.775 - og)) * (fg / 0.794)


def screen_temp(ctx):
    fields = [
        Field("Lettura (SG)", 1.050, 0.001, 0.010, 0.980, 1.200, "{:.3f}"),
        Field("Temp. campione", 25.0, 0.5, 5.0, 0, 80, "{:.1f}", "C"),
        Field("Temp. taratura", 20.0, 0.5, 5.0, 10, 30, "{:.1f}", "C"),
    ]

    def compute(v):
        sg, t, cal = v
        c = correct_sg(sg, t, cal)
        return [("SG corretta", "{:.3f}".format(c)),
                ("Differenza", "{:+.3f}".format(c - sg), r36.DIM),
                ("Plato / Brix", "{:.1f} / {:.1f}".format(sg_to_plato(c), sg_to_brix(c)), r36.DIM)]

    r36.form(ctx, "Correzione temperatura", fields, compute)


def screen_abv(ctx):
    fields = [
        Field("OG (iniziale)", 1.050, 0.001, 0.010, 0.990, 1.200, "{:.3f}"),
        Field("FG (finale)", 1.010, 0.001, 0.010, 0.980, 1.200, "{:.3f}"),
    ]

    def compute(v):
        og, fg = v
        if fg > og:
            return [("Attenzione", "FG > OG ?", r36.BAD)]
        att = (og - fg) / (og - 1) * 100 if og > 1 else 0
        return [("Alcol (ABV)", "{:.2f} %".format(abv_simple(og, fg))),
                ("ABV (formula alt.)", "{:.2f} %".format(abv_alt(og, fg)), r36.DIM),
                ("Attenuazione", "{:.0f} %".format(att), r36.DIM)]

    r36.form(ctx, "Grado alcolico", fields, compute)


def screen_sg(ctx):
    fields = [Field("SG", 1.050, 0.001, 0.010, 0.990, 1.200, "{:.3f}")]

    def compute(v):
        sg = v[0]
        return [("Plato", "{:.1f} P".format(sg_to_plato(sg))),
                ("Brix", "{:.1f} Bx".format(sg_to_brix(sg)))]

    r36.form(ctx, "SG -> Plato / Brix", fields, compute)


def screen_brix(ctx):
    fields = [Field("Brix (rifrattometro)", 12.0, 0.1, 1.0, 0, 40, "{:.1f}", "Bx")]

    def compute(v):
        sg = brix_to_sg(v[0])
        return [("SG", "{:.3f}".format(sg)),
                ("Plato", "{:.1f} P".format(sg_to_plato(sg)), r36.DIM)]

    r36.form(ctx, "Brix -> SG", fields, compute)


def run(ctx):
    screens = [
        ("Correzione temperatura", "Lettura a una temperatura diversa da quella di taratura", screen_temp),
        ("Grado alcolico", "ABV da densita' iniziale e finale", screen_abv),
        ("SG -> Plato / Brix", "Conversione da densita'", screen_sg),
        ("Brix -> SG", "Conversione da rifrattometro (mosto non fermentato)", screen_brix),
    ]
    i = 0
    while True:
        i = r36.menu(ctx, NAME, [(s[0], s[1]) for s in screens], index=i)
        if i is None:
            return
        screens[i][2](ctx)
