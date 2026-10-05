"""Kip & Bub character puppets: proportions and soft shading matched to the Lightbulb Lab concept art.
draw_kip(...) and draw_bub(...) return RGBA images anchored at the feet/base.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

NAVY = (11, 29, 59)
SS = 2

def mix(a, b, t): return tuple(int(x + (y - x) * t) for x, y in zip(a, b))
def shade(c, k): return mix(c, (0, 0, 0), k) if k > 0 else mix(c, (255, 255, 255), -k)

CREAM_T, CREAM_B = (255, 245, 224), (242, 192, 124)
NAVY_T, NAVY_B = (52, 78, 122), (20, 36, 66)
SCREEN_T, SCREEN_B = (22, 40, 72), (8, 18, 38)
AMBER_T, AMBER_B = (255, 210, 110), (232, 140, 20)
HAND_T, HAND_B = (60, 88, 136), (18, 34, 64)

class Pen:
    def __init__(self, w, h, ox, oy, scale):
        self.s = scale * SS; self.ox = ox * SS; self.oy = oy * SS
        self.im = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def p(self, x, y): return (self.ox + x * self.s, self.oy + y * self.s)
    def _grad_fill(self, box, top, bot, maskfn, angle=0.0, outline=None, ow=0):
        (x0, y0), (x1, y1) = self.p(box[0], box[1]), self.p(box[2], box[3])
        x0, y0, x1, y1 = int(x0) - 2, int(y0) - 2, int(x1) + 3, int(y1) + 3
        w, h = max(1, x1 - x0), max(1, y1 - y0)
        yy = np.linspace(0, 1, h)[:, None]; xx = np.linspace(0, 1, w)[None, :]
        t = np.clip(yy * math.cos(angle) + xx * math.sin(angle), 0, 1)
        arr = np.zeros((h, w, 4), np.uint8)
        for c in range(3): arr[..., c] = (top[c] + (bot[c] - top[c]) * t).astype(np.uint8)
        arr[..., 3] = 255
        g = Image.fromarray(arr, 'RGBA')
        m = Image.new('L', (w, h), 0); md = ImageDraw.Draw(m); maskfn(md, x0, y0)
        self.im.paste(g, (x0, y0), m)
        if outline:
            od = ImageDraw.Draw(self.im); maskfn(od, 0, 0, outline=outline, width=int(ow * self.s))
    def grrect(self, x0, y0, x1, y1, r, top, bot, outline=None, ow=0, angle=0.0):
        R = r * self.s
        def mk(md, ox, oy, outline=None, width=0):
            a, b = self.p(x0, y0), self.p(x1, y1)
            box = [a[0] - ox, a[1] - oy, b[0] - ox, b[1] - oy]
            if outline: md.rounded_rectangle(box, R, outline=outline, width=width)
            else: md.rounded_rectangle(box, R, fill=255)
        self._grad_fill((x0, y0, x1, y1), top, bot, mk, angle, outline, ow)
    def gellipse(self, cx, cy, rx, ry, top, bot, outline=None, ow=0, angle=0.0):
        def mk(md, ox, oy, outline=None, width=0):
            a, b = self.p(cx - rx, cy - ry), self.p(cx + rx, cy + ry)
            box = [a[0] - ox, a[1] - oy, b[0] - ox, b[1] - oy]
            if outline: md.ellipse(box, outline=outline, width=width)
            else: md.ellipse(box, fill=255)
        self._grad_fill((cx - rx, cy - ry, cx + rx, cy + ry), top, bot, mk, angle, outline, ow)
    def _blend(self, fn, fill):
        if len(fill) == 4 and fill[3] < 255:
            lay = Image.new('RGBA', self.im.size, (0, 0, 0, 0)); fn(ImageDraw.Draw(lay)); self.im.alpha_composite(lay)
        else: fn(self.d)
    def ellipse(self, cx, cy, rx, ry, fill):
        self._blend(lambda d: d.ellipse([self.p(cx - rx, cy - ry), self.p(cx + rx, cy + ry)], fill=fill), fill)
    def rrect(self, x0, y0, x1, y1, r, fill):
        self._blend(lambda d: d.rounded_rectangle([self.p(x0, y0), self.p(x1, y1)], r * self.s, fill=fill), fill)
    def poly(self, pts, fill):
        self._blend(lambda d: d.polygon([self.p(*q) for q in pts], fill=fill), fill)
    def line(self, a, b, fill, w): self.d.line([self.p(*a), self.p(*b)], fill=fill, width=int(w * self.s))
    def arc(self, cx, cy, rx, ry, a0, a1, fill, w):
        self.d.arc([self.p(cx - rx, cy - ry), self.p(cx + rx, cy + ry)], a0, a1, fill=fill, width=int(w * self.s))
    def tube(self, a, b, w, top, bot):
        """shaded limb segment: dark core line + lighter highlight stripe"""
        self.line(a, b, bot, w)
        for q in (a, b): self.ellipse(q[0], q[1], w / 2, w / 2, bot)
        ang = math.atan2(b[1] - a[1], b[0] - a[0]); nx, ny = -math.sin(ang), math.cos(ang)
        off = -w * 0.18
        self.line((a[0] + nx * off, a[1] + ny * off), (b[0] + nx * off, b[1] + ny * off), top, w * 0.45)
    def out(self): return self.im.resize((self.im.width // SS, self.im.height // SS), Image.LANCZOS)

def _arm(sh, a_up, a_low, side, L1=80, L2=74):
    r1 = math.radians(a_up); r2 = math.radians(a_up + a_low)
    e = (sh[0] + side * math.sin(r1) * L1, sh[1] + math.cos(r1) * L1)
    h = (e[0] + side * math.sin(r2) * L2, e[1] + math.cos(r2) * L2)
    return sh, e, h, r2

def draw_kip(scale=1.0, walk=0.0, walking=0.0, bob=0.0, arm_l=(14, 8), arm_r=(14, 8),
             mouth=0.0, blink=0.0, eyes='happy', antenna=0.0, lean=0.0, look=0.0):
    W, H, PAD = 720, 860, 30
    pn = Pen(W, H, W / 2, H - PAD, scale)
    sw = math.sin(walk) * walking
    body_y = -bob - abs(math.cos(walk)) * walking * 10
    sway = sw * 8
    OL = (8, 18, 38, 255)
    # ---- legs (stubby) ----
    for side, ph in [(-1, 1), (1, -1)]:
        up = max(0.0, math.sin(walk) * ph) * walking
        hip = (side * 56 + sway, -112 + body_y * 0.5)
        f = (side * 62 + sway * 0.5, -30 - up * 40)
        pn.tube(hip, f, 84, NAVY_T, NAVY_B)
        pn.grrect(f[0] - 60 + side * 8, f[1] - 14, f[0] + 60 + side * 8, f[1] + 30, 24, (44, 68, 110), (16, 30, 58), OL, 3)
    oy = body_y; lx = lean * 12 + sway
    # ---- torso: cream chest shell over a navy core ----
    pn.grrect(-118 + lx, -205 + oy, 118 + lx, -100 + oy, 44, NAVY_T, NAVY_B, OL, 3)
    pn.grrect(-126 + lx, -330 + oy, 126 + lx, -160 + oy, 56, CREAM_T, CREAM_B, (150, 100, 50, 255), 3, angle=0.7)
    pn.rrect(-88 + lx, -330 + oy, 40 + lx, -318 + oy, 6, (255, 252, 240, 160))  # top highlight
    # chest light
    cx, cy = lx, -252 + oy
    pn.gellipse(cx, cy, 46, 46, NAVY_T, NAVY_B, OL, 3)
    pn.gellipse(cx, cy, 30, 30, AMBER_T, AMBER_B)
    pn.ellipse(cx - 9, cy - 10, 9, 7, (255, 240, 200, 230))
    # ---- head ----
    hx = lx * 1.6; hy = oy * 1.15
    pn.grrect(-40 + hx, -372 + hy, 40 + hx, -330 + hy, 12, NAVY_T, NAVY_B, OL, 3)  # neck
    base = (-70 + hx, -660 + hy); tip = (base[0] - 16 + antenna * 22, base[1] - 74 + abs(antenna) * 6)
    pn.line(base, tip, (70, 98, 146), 13)
    pn.gellipse(tip[0], tip[1], 22, 22, AMBER_T, AMBER_B, OL, 2)
    pn.ellipse(tip[0] - 7, tip[1] - 8, 7, 5, (255, 244, 210))
    for side in (-1, 1):  # headphones: big navy cups with amber rings
        ex = side * 200 + hx
        pn.grrect(ex - 46, -560 + hy, ex + 46, -420 + hy, 40, NAVY_T, NAVY_B, OL, 3)
        pn.gellipse(ex + side * 10, -490 + hy, 46, 46, AMBER_T, AMBER_B, OL, 3)
        pn.gellipse(ex + side * 10, -490 + hy, 28, 28, NAVY_T, NAVY_B)
        pn.ellipse(ex + side * 10 - 14, -490 + hy - 18, 8, 6, (255, 236, 190, 200))
    # outer shell with bevel
    pn.grrect(-188 + hx, -665 + hy, 188 + hx, -352 + hy, 86, CREAM_T, CREAM_B, (150, 100, 50, 255), 4, angle=0.7)
    pn.grrect(-176 + hx, -654 + hy, 170 + hx, -366 + hy, 76, (255, 248, 230), (246, 196, 128), angle=0.7)
    pn.rrect(-120 + hx, -652 + hy, 60 + hx, -640 + hy, 6, (255, 255, 248, 200))
    # screen
    pn.grrect(-158 + hx, -634 + hy, 158 + hx, -392 + hy, 60, SCREEN_T, SCREEN_B, OL, 4)
    pn.poly([(-120 + hx, -612 + hy), (-40 + hx, -612 + hy), (-110 + hx, -540 + hy), (-136 + hx, -560 + hy)], (90, 120, 170, 60))
    # face
    ey = -516 + hy; fx = hx + look * 16; FACE = (255, 246, 228)
    for side in (-1, 1):
        x = fx + side * 70
        if blink > 0.5: pn.line((x - 26, ey + 4), (x + 26, ey + 4), FACE, 14)
        elif eyes == 'happy': pn.arc(x, ey + 26, 34, 50, 192, 348, FACE, 24)
        elif eyes == 'wide': pn.ellipse(x, ey, 20, 28, FACE)
        else: pn.ellipse(x, ey, 16, 22, FACE)
    my = -452 + hy
    if mouth > 0.06:
        pn.grrect(fx - 30, my - 4 - mouth * 22, fx + 30, my + 6 + mouth * 14, 16 + mouth * 6, AMBER_T, AMBER_B)
    # ---- arms (drawn last so a wave sits in front of the head) ----
    for side, (au, al) in [(-1, arm_l), (1, arm_r)]:
        sh, e, h, r2 = _arm((side * 116 + lx, -300 + oy), au, al, side)
        pn.tube(sh, e, 62, NAVY_T, NAVY_B); pn.tube(e, h, 58, NAVY_T, NAVY_B)
        pn.gellipse(e[0], e[1], 22, 22, (64, 92, 138), (24, 42, 74))
        pn.gellipse(sh[0], sh[1], 34, 34, NAVY_T, NAVY_B, OL, 3)
        # mitten hand
        hx2, hy2 = h[0] + side * math.sin(r2) * 16, h[1] + math.cos(r2) * 16
        pn.gellipse(hx2, hy2, 46, 42, HAND_T, HAND_B, OL, 3)
        tx = hx2 - side * 30 * math.cos(r2); ty = hy2 - 6 + 30 * math.sin(r2) * side * -0.3
        pn.gellipse(tx, ty, 18, 22, HAND_T, HAND_B, OL, 2)
    return pn.out()

BULB_C = (255, 226, 140); BULB_E = (240, 168, 50)
def draw_bub(scale=1.0, squash=0.0, mood='happy', blink=0.0, rays=0.0, dim=0.0):
    W, H, PAD = 460, 500, 20
    pn = Pen(W, H, W / 2, H - PAD, scale)
    sx, sy = 1 + 0.12 * squash, 1 - 0.12 * squash
    OL = (8, 18, 38, 255)
    # screw base: ridged navy
    for i, y in enumerate([-28, -52, -76, -98]):
        w = 46 - i * 1
        pn.grrect(-w * sx, (y - 13) * sy, w * sx, (y + 13) * sy, 13, (60, 88, 134), (18, 32, 60), OL, 2)
    pn.grrect(-22, -16 * sy, 22, 0, 8, (40, 62, 100), (14, 26, 50), OL, 2)
    # bulb with radial-ish shading
    cy = -214 * sy; r = 116
    c1 = mix(BULB_C, (150, 130, 100), dim); c2 = mix(BULB_E, (110, 90, 70), dim)
    pn.gellipse(0, cy + 74 * sy, 64 * sx, 54 * sy, c1, c2)
    pn.gellipse(0, cy, r * sx, r * sy, c1, c2, (196, 120, 20, 255), 3, angle=0.5)
    # soft facets (painterly planes)
    for (fx0, fy0, fx1, fy1, a) in [(-60, -70, 10, -10, 40), (20, -40, 80, 30, 26), (-80, 10, -20, 70, 22)]:
        pn.poly([(fx0 * sx, cy + fy0 * sy), (fx1 * sx, cy + fy0 * sy + 10), (fx1 * sx - 10, cy + fy1 * sy), (fx0 * sx + 8, cy + fy1 * sy)], (255, 250, 220, a))
    pn.ellipse(-44 * sx, cy - 56 * sy, 30 * sx, 20 * sy, (255, 252, 236, 220))
    if rays > 0:
        for k in range(7):
            a = math.radians(-90 + (k - 3) * 28); r0, r1 = r + 26, r + 26 + 48 * rays
            pn.line((math.cos(a) * r0 * sx, cy + math.sin(a) * r0 * sy), (math.cos(a) * r1 * sx, cy + math.sin(a) * r1 * sy), (247, 168, 37), 15)
    ey = cy + 8 * sy; FACE = (14, 28, 54)
    for side in (-1, 1):
        x = side * 38 * sx
        if blink > 0.5 or mood == 'sleepy': pn.arc(x, ey - 4, 18, 13, 20, 160, FACE, 8)
        elif mood == 'aha' and side > 0: pn.arc(x, ey + 8, 18, 15, 200, 340, FACE, 9)
        else:
            pn.ellipse(x, ey, 13 * sx, 20 * sy, FACE); pn.ellipse(x - 4, ey - 7, 4, 5, (255, 255, 255, 220))
    my = ey + 44 * sy
    if mood in ('happy', 'aha'):
        pn.d.chord([pn.p(-25 * sx, my - 20 * sy), pn.p(25 * sx, my + 18 * sy)], 0, 180, fill=FACE)
        pn.ellipse(0, my + 9 * sy, 10, 5, (220, 90, 70))
    elif mood == 'confused': pn.arc(0, my + 14, 20, 13, 200, 340, FACE, 8)
    elif mood == 'curious': pn.ellipse(0, my, 9, 10, FACE)
    else: pn.arc(0, my - 6, 13, 9, 20, 160, FACE, 7)
    for side in (-1, 1): pn.ellipse(side * 70 * sx, ey + 30 * sy, 16, 9, (255, 150, 90, 90))  # cheeks
    return pn.out()
