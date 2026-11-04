"""Schermo PC: mostra lo schermo di Windows sulla console.

Sul PC gira pc/schermo_su_console.py, che cattura lo schermo e lo manda qui
attraverso il cavo USB (niente WiFi, niente internet). Dalla console
comandi il mouse del PC.

Tasti: croce = mouse (piu' la tieni, piu' va veloce)
       A = click sinistro, B = click destro, X = doppio click
       L1/R1 = rotella su/giu', L2/R2 = zoom -/+
       Y = mostra/nasconde le info, SELECT+START = esci
"""
import io
import socket
import struct
import subprocess
import time

import pygame

import r36
from r36 import sound

NAME = "Schermo PC"
DESCRIPTION = "Lo schermo di Windows sulla console"
W, H = r36.W, r36.H
PORT = 5577
FG = (220, 225, 235)
DIM = (120, 126, 140)


CABLE_IP = "169.254.7.1"


def usb_status():
    """Stato del cavo: ('configured' = il PC ha riconosciuto la console)."""
    import glob
    info = []
    for u in glob.glob("/sys/class/udc/*/state"):
        try:
            st = open(u).read().strip()
            info.append(("Cavo USB: " + {"configured": "collegato al PC",
                                          "not attached": "il PC non vede la console"}.get(st, st),
                         st == "configured"))
        except OSError:
            pass
    # otg_mode: cerca solo pochi livelli (una ricerca completa in /sys si blocca)
    for pat in ("/sys/devices/platform/*/otg_mode", "/sys/devices/platform/*/*/otg_mode",
                "/sys/devices/platform/*/*/*/otg_mode"):
        found = glob.glob(pat)
        if found:
            try:
                info.append(("modo porta: " + open(found[0]).read().strip(), False))
            except OSError:
                pass
            break
    if not glob.glob("/sys/kernel/config/usb_gadget/r36net"):
        info.append(("Collegamento non attivo: avvia da Ports -> Schermo PC", False))
    if not info:
        info.append(("Nessuna porta USB device trovata", False))
    return info


class Link:
    def __init__(self):
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("0.0.0.0", PORT))
        self.srv.listen(1)
        self.srv.setblocking(False)
        self.conn = None
        self.peer = None
        self.buf = b""
        self.frames = 0

    def close(self):
        for s in (self.conn, self.srv):
            try:
                if s:
                    s.close()
            except OSError:
                pass

    def poll(self):
        """Ritorna l'ultimo frame JPEG arrivato (bytes) o None."""
        if self.conn is None:
            try:
                self.conn, addr = self.srv.accept()
                self.conn.setblocking(False)
                self.conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.peer, self.buf = addr[0], b""
                sound.play("chirp")
            except (BlockingIOError, OSError):
                return None
        latest = None
        try:
            while True:
                chunk = self.conn.recv(262144)
                if not chunk:
                    self.drop()
                    return None
                self.buf += chunk
                if len(self.buf) > 8_000_000:
                    self.buf = b""
        except BlockingIOError:
            pass
        except OSError:
            self.drop()
            return None
        while len(self.buf) >= 5:
            if self.buf[:1] != b"F":
                self.buf = b""
                break
            n = struct.unpack(">I", self.buf[1:5])[0]
            if len(self.buf) < 5 + n:
                break
            latest = self.buf[5:5 + n]
            self.buf = self.buf[5 + n:]
            self.frames += 1
        return latest

    def send(self, line):
        if self.conn is None:
            return
        try:
            self.conn.sendall((line + "\n").encode())
        except OSError:
            self.drop()

    def drop(self):
        try:
            self.conn.close()
        except OSError:
            pass
        self.conn, self.peer = None, None
        sound.play("sad")


def run(ctx):
    try:
        link = Link()
    except OSError as e:
        r36.message(ctx, NAME, "Non riesco ad aprire la porta %d:\n%s" % (PORT, e), r36.BAD)
        return
    frame_img = None
    usb = usb_status()
    next_ips = time.monotonic() + 3
    zoom = 1
    show_info = True
    speed = 0.0
    fps_t, fps_n, fps = time.monotonic(), 0, 0.0
    ctx.input.flush()
    try:
        while True:
            acts = ctx.input.poll()
            held = ctx.input.held
            for a in acts:
                if a == "A":
                    link.send("C L")
                elif a == "B":
                    link.send("C R")
                elif a == "X":
                    link.send("C D")
                elif a == "L1":
                    link.send("S 1")
                elif a == "R1":
                    link.send("S -1")
                elif a == "L2":
                    zoom = max(1, zoom - 1)
                    link.send("Z %d" % zoom)
                elif a == "R2":
                    zoom = min(3, zoom + 1)
                    link.send("Z %d" % zoom)
                elif a == "Y":
                    show_info = not show_info
            dx = ("RIGHT" in held) - ("LEFT" in held)
            dy = ("DOWN" in held) - ("UP" in held)
            if dx or dy:
                speed = min(40.0, speed + 1.2) if speed else 3.0
                link.send("M %d %d" % (dx * speed, dy * speed))
            else:
                speed = 0.0

            data = link.poll()
            if data:
                try:
                    frame_img = pygame.image.load(io.BytesIO(data), "frame.jpg").convert()
                    fps_n += 1
                except pygame.error:
                    pass
            now = time.monotonic()
            if now - fps_t >= 1:
                fps, fps_n, fps_t = fps_n / (now - fps_t), 0, now
            if link.conn is None and now >= next_ips:
                usb, next_ips = usb_status(), now + 1
                frame_img = None

            s = ctx.surf
            s.fill((0, 0, 0))
            if frame_img is not None:
                iw, ih = frame_img.get_size()
                if (iw, ih) == (W, H):
                    s.blit(frame_img, (0, 0))
                else:
                    k = min(W / iw, H / ih)
                    img = pygame.transform.smoothscale(frame_img, (int(iw * k), int(ih * k)))
                    s.blit(img, ((W - img.get_width()) // 2, (H - img.get_height()) // 2))
                if show_info:
                    ctx.text("%s  %.0f fps  zoom %dx" % (link.peer or "", fps, zoom), 8, 6, 20, (255, 255, 0))
            else:
                ctx.text("SCHERMO PC", W // 2, 30, 44, r36.ACCENT, align="center", bold=True)
                if link.conn:
                    ctx.text("Collegato a %s, aspetto le immagini..." % link.peer, W // 2, 120, 28, FG, align="center")
                else:
                    ctx.text("In attesa del PC (solo cavo USB)", W // 2, 100, 28, FG, align="center")
                    y = 160
                    for line, ok in usb:
                        ctx.text(line, W // 2, y, 30 if y == 160 else 24,
                                 (120, 230, 140) if ok else (255, 190, 90), align="center", bold=True)
                        y += 40 if y == 160 else 30
                    ctx.text("1. cavo DATI nella porta OTG", W // 2, 300, 24, DIM, align="center")
                    ctx.text("2. sul PC: doppio clic su 'Schermo su console.bat'", W // 2, 330, 24, DIM, align="center")
                    ctx.text("console = %s" % CABLE_IP, W // 2, 372, 22, (90, 96, 110), align="center")
                ctx.text("SELECT+START esci", W // 2, H - 26, 20, DIM, align="center")
            ctx.flip(60)
    finally:
        link.close()
