#!/usr/bin/env python3
"""Menu principale: elenca le app in apps/ e le avvia.

Ogni app e' una cartella apps/<nome>/main.py con:
    NAME = "Nome nel menu"
    DESCRIPTION = "riga di descrizione"   (opzionale)
    def run(ctx): ...
Le cartelle che iniziano con "_" vengono ignorate (es. _modello).
"""
import importlib.util
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import r36  # noqa: E402

APPS_DIR = os.path.join(HERE, "apps")


def find_apps():
    apps = []
    for name in sorted(os.listdir(APPS_DIR)):
        path = os.path.join(APPS_DIR, name, "main.py")
        if name.startswith(("_", ".")) or not os.path.isfile(path):
            continue
        apps.append((name, path))
    return apps


def load(name, path):
    spec = importlib.util.spec_from_file_location("app_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(os.path.dirname(path))
    return mod


def run_app(ctx, name, path):
    try:
        mod = load(name, path)
        mod.run(ctx)
    except r36.QuitApp:
        pass
    except r36.QuitAll:
        raise
    except Exception:
        err = traceback.format_exc()
        print(err, file=sys.stderr)
        r36.message(ctx, "Errore in " + name, err, r36.BAD)


def main():
    ctx = r36.Ctx()
    try:
        apps = find_apps()
        if ctx.first_run and ctx.input.joysticks:
            for name, path in apps:
                if name == "configura_tasti":
                    run_app(ctx, name, path)
        index = 0
        while True:
            items = []
            for name, path in apps:
                try:
                    mod = load(name, path)
                    items.append((getattr(mod, "NAME", name), getattr(mod, "DESCRIPTION", None)))
                except Exception as e:
                    items.append((name + " (rotta)", str(e)))
            try:
                choice = r36.menu(ctx, "R36 Tool", items + [("Esci", "Torna a EmulationStation")],
                                  index=index)
            except r36.QuitApp:
                break
            if choice is None or choice == len(apps):
                break
            index = choice
            run_app(ctx, *apps[choice])
    except r36.QuitAll:
        pass
    finally:
        import pygame
        pygame.quit()


if __name__ == "__main__":
    main()
