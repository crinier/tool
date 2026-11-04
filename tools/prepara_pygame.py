#!/usr/bin/env python3
"""Prepara pygame "offline" per la console (ARM64), da mettere sulla SD.

La console non ha internet: questo script gira sul PC (Linux, o WSL su
Windows), scarica le wheel ufficiali di pygame per aarch64 e crea
ports/tool/vendor/ con:

  vendor/libs/          librerie in comune (SDL2_mixer, ttf, image, ...)
  vendor/sdl-interno/   SDL2 incluso in pygame (riserva)
  vendor/py37 ... py313 il pacchetto pygame per ogni versione di Python

Modifica importante: l'SDL2 dentro le wheel non ha il driver KMSDRM, che
serve per disegnare sullo schermo della console senza X11. Per questo le
librerie vengono modificate (con patchelf) per usare l'SDL2 del sistema
(libSDL2-2.0.so.0, quello degli emulatori). L'SDL2 interno resta come
riserva e lo usa launcher.py solo se il sistema non ne ha uno.

Requisiti:
    pip install patchelf
Uso:
    python3 tools/prepara_pygame.py
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

VERSION = "2.6.1"
PYTHONS = os.environ.get("R36_PYTHONS", "3.7 3.8 3.9 3.10 3.11 3.12 3.13").split()
PLATFORM = os.environ.get("R36_PLATFORM", "manylinux2014_aarch64")  # per i test
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("R36_OUT") or os.path.join(ROOT, "ports", "tool", "vendor")
SYSTEM_SDL = "libSDL2-2.0.so.0"


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def needed(path):
    return run("patchelf", "--print-needed", path).split()


def main():
    shutil.which("patchelf") or sys.exit("Serve patchelf:  pip install patchelf")
    tmp = tempfile.mkdtemp()
    for v in PYTHONS:
        print("scarico pygame %s per Python %s ..." % (VERSION, v))
        subprocess.run([sys.executable, "-m", "pip", "download", "-q", "--no-deps",
                        "--only-binary=:all:", "--platform", PLATFORM,
                        "--python-version", v, "pygame==" + VERSION, "-d", tmp], check=True)
    shutil.rmtree(OUT, ignore_errors=True)
    libs = os.path.join(OUT, "libs")
    fallback = os.path.join(OUT, "sdl-interno")
    os.makedirs(libs)
    os.makedirs(fallback)
    bundled_sdl = None

    for whl in sorted(glob.glob(os.path.join(tmp, "*.whl"))):
        tag = os.path.basename(whl).split("-")[2]          # cp311
        dest = os.path.join(OUT, "py" + tag[2:])           # py311
        with zipfile.ZipFile(whl) as z:
            for name in z.namelist():
                if name.startswith("pygame.libs/"):
                    target = os.path.join(libs, os.path.basename(name))
                    if not os.path.exists(target):
                        with open(target, "wb") as f:
                            f.write(z.read(name))
                elif name.startswith("pygame/") and "/tests/" not in name \
                        and "/examples/" not in name and "/docs/" not in name:
                    z.extract(name, dest)
        print("  " + os.path.relpath(dest, ROOT))

    # SDL2 interno: spostato da parte, rinominato col nome di sistema
    for f in os.listdir(libs):
        if f.startswith("libSDL2-2"):
            bundled_sdl = f
            shutil.move(os.path.join(libs, f), os.path.join(fallback, SYSTEM_SDL))
    assert bundled_sdl, "SDL2 non trovato nella wheel"

    # tutte le .so: SDL2 -> quello di sistema, librerie cercate in vendor/libs
    count = 0
    for so in glob.glob(os.path.join(OUT, "**", "*.so*"), recursive=True):
        deps = needed(so)
        if bundled_sdl in deps:
            run("patchelf", "--replace-needed", bundled_sdl, SYSTEM_SDL, so)
            count += 1
        rel = os.path.relpath(libs, os.path.dirname(so))
        if not so.startswith(fallback):
            run("patchelf", "--set-rpath", "$ORIGIN" if rel == "." else "$ORIGIN/" + rel, so)
    # l'SDL interno trova le sue dipendenze in vendor/libs
    run("patchelf", "--set-rpath", "$ORIGIN/../libs", os.path.join(fallback, SYSTEM_SDL))
    print("modificate %d librerie per usare l'SDL2 di sistema" % count)

    size = sum(os.path.getsize(p) for p in glob.glob(os.path.join(OUT, "**"), recursive=True)
               if os.path.isfile(p))
    print("pronto: %s (%.0f MB)" % (os.path.relpath(OUT, ROOT), size / 1e6))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
