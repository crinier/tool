#!/usr/bin/env python3
"""Manda lo schermo del PC alla console (app "Schermo PC") e riceve il mouse.

Uso:  python schermo_su_console.py [indirizzo-console]
      (senza indirizzo prova 169.254.7.1, quello del cavo USB)

Richiede:  pip install mss pygame-ce
Il mouse comandato dalla console funziona su Windows.
"""
import ctypes
import io
import select
import socket
import struct
import sys
import time

import pygame

PORT = 5577
OUT_W, OUT_H = 640, 480
FPS = 15
IS_WIN = sys.platform == "win32"

if IS_WIN:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)   # coordinate vere anche con zoom di Windows
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


# ------------------------------------------------------------ mouse (Windows)

class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def cursor_pos():
    if not IS_WIN:
        return None
    p = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def mouse_event(cmd, arg):
    if not IS_WIN:
        return
    u = ctypes.windll.user32
    if cmd == "M":
        dx, dy = (int(v) for v in arg.split())
        x, y = cursor_pos()
        u.SetCursorPos(x + dx, y + dy)
    elif cmd == "C":
        down, up = {"L": (0x02, 0x04), "R": (0x08, 0x10), "D": (0x02, 0x04)}[arg]
        for _ in range(2 if arg == "D" else 1):
            u.mouse_event(down, 0, 0, 0, 0)
            u.mouse_event(up, 0, 0, 0, 0)
    elif cmd == "S":
        u.mouse_event(0x0800, 0, 0, int(arg) * 120, 0)


# ------------------------------------------------------------ cattura

def region(mon, zoom, cur):
    """Zona da catturare: tutto lo schermo (zoom 1) o una zona attorno al mouse."""
    if zoom <= 1 or cur is None:
        return mon
    w = {2: OUT_W * 2, 3: OUT_W}[zoom]
    h = w * OUT_H // OUT_W
    w, h = min(w, mon["width"]), min(h, mon["height"])
    x = min(max(cur[0] - w // 2, mon["left"]), mon["left"] + mon["width"] - w)
    y = min(max(cur[1] - h // 2, mon["top"]), mon["top"] + mon["height"] - h)
    return {"left": x, "top": y, "width": w, "height": h}


def draw_cursor(surf, x, y):
    pts = [(x, y), (x, y + 17), (x + 4, y + 13), (x + 8, y + 20), (x + 11, y + 19), (x + 7, y + 12), (x + 12, y + 12)]
    pygame.draw.polygon(surf, (255, 255, 255), pts)
    pygame.draw.polygon(surf, (0, 0, 0), pts, 1)


def encode(raw_bgra, size, reg, cur):
    img = pygame.image.frombuffer(raw_bgra, size, "BGRA")
    k = min(OUT_W / size[0], OUT_H / size[1])
    out = pygame.transform.smoothscale(img, (max(1, int(size[0] * k)), max(1, int(size[1] * k))))
    if cur is not None:
        cx = (cur[0] - reg["left"]) * k
        cy = (cur[1] - reg["top"]) * k
        if 0 <= cx < out.get_width() and 0 <= cy < out.get_height():
            draw_cursor(out, int(cx), int(cy))
    buf = io.BytesIO()
    pygame.image.save(out, buf, "frame.jpg")
    return buf.getvalue()


def connect(host):
    while True:
        try:
            s = socket.create_connection((host, PORT), timeout=3)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print("Collegato a", host)
            return s
        except OSError as e:
            print("Console %s non raggiungibile (%s). Riprovo... (Ctrl+C per uscire)" % (host, e))
            time.sleep(2)


def main():
    import mss
    host = sys.argv[1] if len(sys.argv) > 1 else (input("Indirizzo della console [169.254.7.1]: ").strip()
                                                   or "169.254.7.1")
    pygame.init()
    zoom = 1
    with mss.mss() as sct:
        mon = sct.monitors[1]           # schermo principale
        while True:
            sock = connect(host)
            pending = b""
            try:
                while True:
                    t0 = time.monotonic()
                    # comandi dalla console
                    while select.select([sock], [], [], 0)[0]:
                        data = sock.recv(4096)
                        if not data:
                            raise ConnectionError("console chiusa")
                        pending += data
                    *lines, pending = pending.split(b"\n")
                    for ln in lines:
                        parts = ln.decode(errors="ignore").split(" ", 1)
                        if len(parts) == 2:
                            if parts[0] == "Z":
                                zoom = int(parts[1])
                            else:
                                mouse_event(parts[0], parts[1])
                    cur = cursor_pos()
                    reg = region(mon, zoom, cur)
                    shot = sct.grab(reg)
                    jpg = encode(shot.bgra, shot.size, reg, cur)
                    sock.sendall(b"F" + struct.pack(">I", len(jpg)) + jpg)
                    time.sleep(max(0.0, 1 / FPS - (time.monotonic() - t0)))
            except (OSError, ConnectionError) as e:
                print("Collegamento perso:", e)
                sock.close()
                time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
