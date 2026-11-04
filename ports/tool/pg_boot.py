"""Trova pygame anche su una console senza internet.

Ordine:
  1. pygame gia' installato nel sistema
  2. vendor/pyXY del kit (usa l'SDL2 del sistema, quello con KMSDRM)
  3. copia di vendor in ~/.cache (se la SD e' montata 'noexec')
  4. riavvio di Python con l'SDL2 interno del kit (ultima spiaggia)
Va importato PRIMA di pygame. Non usa nulla fuori dalla libreria standard.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "vendor")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "r36tool", "vendor")
TAG = "py%d%d" % sys.version_info[:2]
FLAG = "R36_SDL_INTERNO"


def _forget():
    for name in list(sys.modules):
        if name == "pygame" or name.startswith("pygame."):
            del sys.modules[name]


def _try(path, errors):
    if path and not os.path.isdir(path):
        return False
    if path:
        sys.path.insert(0, path)
    try:
        import pygame  # noqa: F401
        return True
    except ImportError as e:
        errors.append("%s: %s" % (path or "sistema", e))
        if path:
            sys.path.remove(path)
        _forget()
        return False


def _copy_to_cache():
    try:
        for sub in ("libs", "sdl-interno", TAG):
            src, dst = os.path.join(VENDOR, sub), os.path.join(CACHE, sub)
            if os.path.isdir(src) and not os.path.isdir(dst):
                shutil.copytree(src, dst)
        return True
    except OSError:
        return False


def ensure_pygame():
    errors = []
    if not os.environ.get(FLAG) and _try(None, errors):
        return "sistema"
    import platform
    if not (sys.platform.startswith("linux") and platform.machine() in ("aarch64", "arm64")):
        # sul PC il pygame del kit (ARM) non serve: va installato normalmente
        sys.stderr.write("pygame non installato. Sul PC:  pip install pygame\n")
        sys.exit(2)
    if _try(os.path.join(VENDOR, TAG), errors):
        return "kit"
    if os.path.isdir(os.path.join(VENDOR, TAG)) and _copy_to_cache() \
            and _try(os.path.join(CACHE, TAG), errors):
        return "kit (copia in cache)"
    if not os.environ.get(FLAG):
        for base in (VENDOR, CACHE):
            sdl = os.path.join(base, "sdl-interno")
            if os.path.isdir(sdl) and os.path.isdir(os.path.join(base, TAG)):
                env = dict(os.environ)
                env[FLAG] = "1"
                env["LD_LIBRARY_PATH"] = sdl + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
                sys.stderr.write("pygame: provo con l'SDL2 interno\n")
                sys.stderr.flush()
                os.execve(sys.executable, [sys.executable] + sys.argv, env)
    msg = ("pygame non disponibile per Python %d.%d (il kit ha 3.7-3.13).\n" % sys.version_info[:2]
           + "\n".join(errors[-4:]))
    sys.stderr.write(msg + "\n")
    sys.exit(2)
