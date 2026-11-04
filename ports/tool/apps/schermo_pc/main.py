"""Schermo PC: mostra lo schermo di Windows sulla console.

Sul PC gira pc/schermo_su_console.py, che cattura lo schermo e lo manda qui
via rete (cavo USB in modalita' rete, oppure WiFi). Dalla console comandi
il mouse del PC.

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


def my_ips():
    ips = []
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr"], capture_output=True, text=True, timeout=2).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[2] == "inet":
                ip = parts[3].split("/")[0]
                if not ip.startswith("127."):
                    ips.append("%s (%s)" % (ip, parts[1]))
    except (OSError, subprocess.SubprocessError):
        pass
    return ips


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
    ips = my_ips()
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
                ips, next_ips = my_ips(), now + 3
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
                    ctx.text("In attesa del PC sulla porta %d" % PORT, W // 2, 100, 28, FG, align="center")
                    ctx.text("Indirizzi di questa console:", W // 2, 150, 26, DIM, align="center")
                    y = 185
                    for ip in ips[:5] or ["(nessuna rete: cavo USB o WiFi?)"]:
                        ctx.text(ip, W // 2, y, 30, (255, 255, 255), align="center", bold=True)
                        y += 36
                    ctx.text("Sul PC avvia 'Schermo su console.bat'", W // 2, 380, 24, DIM, align="center")
                    ctx.text("e scrivi uno di questi indirizzi.", W // 2, 408, 24, DIM, align="center")
                ctx.text("SELECT+START esci", W // 2, H - 26, 20, DIM, align="center")
            ctx.flip(60)
    finally:
        link.close()
