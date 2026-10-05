"""Episode 1 explainer card visuals (drawn on a cream card, supersampled)."""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

NAVY = (11, 29, 59); NAVY_L = (40, 64, 104); AMBER = (247, 168, 37); AMBER_L = (255, 205, 110)
CREAM = (255, 247, 230); CREAM_D = (238, 222, 194); SAGE = (107, 143, 107); RED = (220, 84, 64)
WOOD = (196, 140, 84); WOOD_D = (150, 100, 58); WHITE = (255, 255, 255)
FB = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
FM = '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'
CW, CH, S = 730, 410, 2
_fonts = {}
def F(path, size):
    k = (path, size)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(path, int(size * S))
    return _fonts[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

class Card:
    """2x supersampled drawing surface in card units"""
    def __init__(self, bg=CREAM):
        self.im = Image.new('RGBA', (CW * S, CH * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        if bg: self.d.rounded_rectangle([0, 0, CW * S - 1, CH * S - 1], 34 * S, fill=bg)
    def P(self, x, y): return (x * S, y * S)
    def rr(self, x0, y0, x1, y1, r, fill, outline=None, w=0):
        self.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], r * S, fill=fill, outline=outline, width=int(w * S))
    def el(self, cx, cy, rx, ry, fill, outline=None, w=0):
        self.d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill, outline=outline, width=int(w * S))
    def poly(self, pts, fill): self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)
    def line(self, pts, fill, w): self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(w * S), joint='curve')
    def arc(self, cx, cy, r, a0, a1, fill, w): self.d.arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], a0, a1, fill=fill, width=int(w * S))
    def text(self, x, y, s, size, fill, font=FB, anchor='mm'): self.d.text((x * S, y * S), s, font=F(font, size), fill=fill, anchor=anchor)
    def tw(self, s, size, font=FB): return self.d.textlength(s, font=F(font, size)) / S
    def layer(self, sub, alpha=1.0, x=0, y=0, scale=1.0):
        """composite another Card's image with alpha/scale centred offset"""
        im = sub.im
        if scale != 1.0:
            w, h = max(1, int(im.width * scale)), max(1, int(im.height * scale)); im = im.resize((w, h), Image.LANCZOS)
            x += (CW - CW * scale) / 2; y += (CH - CH * scale) / 2
        if alpha < 1.0:
            im = im.copy(); im.putalpha(im.getchannel('A').point(lambda p: int(p * alpha)))
        self.im.alpha_composite(im, (int(x * S), int(y * S)))
    def chip(self, x, y, s, size=24, bg=AMBER, fg=NAVY, alpha=1.0):
        w = self.tw(s, size) + 36
        c = tuple(list(bg) + [int(255 * alpha)]); f = tuple(list(fg) + [int(255 * alpha)])
        self.rr(x, y, x + w, y + size * 1.7, size * 0.85, c); self.text(x + w / 2, y + size * 0.85, s, size, f)
        return w
    def out(self): return self.im.resize((CW, CH), Image.LANCZOS)

def blank(): return Card(bg=None)

# ---------------- icons (centred at cx, cy, size ~ s) ----------------
def icon(c, kind, cx, cy, s=1.0):
    k = s
    if kind == 'laptop':
        c.rr(cx - 62 * k, cy - 46 * k, cx + 62 * k, cy + 30 * k, 8 * k, NAVY); c.rr(cx - 52 * k, cy - 37 * k, cx + 52 * k, cy + 21 * k, 4 * k, (64, 104, 160))
        c.poly([(cx - 78 * k, cy + 32 * k), (cx + 78 * k, cy + 32 * k), (cx + 70 * k, cy + 44 * k), (cx - 70 * k, cy + 44 * k)], NAVY_L)
    elif kind == 'phone':
        c.rr(cx - 32 * k, cy - 58 * k, cx + 32 * k, cy + 58 * k, 12 * k, NAVY); c.rr(cx - 25 * k, cy - 46 * k, cx + 25 * k, cy + 44 * k, 5 * k, (64, 104, 160))
        c.rr(cx - 10 * k, cy - 53 * k, cx + 10 * k, cy - 50 * k, 2 * k, NAVY_L)
    elif kind == 'tv':
        c.rr(cx - 70 * k, cy - 46 * k, cx + 70 * k, cy + 34 * k, 8 * k, NAVY); c.rr(cx - 60 * k, cy - 37 * k, cx + 60 * k, cy + 25 * k, 4 * k, (64, 104, 160))
        c.line([(cx - 20 * k, cy + 52 * k), (cx, cy + 34 * k), (cx + 20 * k, cy + 52 * k)], NAVY, 6 * k)
    elif kind == 'car':
        c.poly([(cx - 74 * k, cy + 20 * k), (cx - 64 * k, cy - 6 * k), (cx - 36 * k, cy - 12 * k), (cx - 18 * k, cy - 38 * k), (cx + 30 * k, cy - 38 * k), (cx + 52 * k, cy - 10 * k), (cx + 74 * k, cy - 4 * k), (cx + 76 * k, cy + 20 * k)], AMBER)
        c.poly([(cx - 10 * k, cy - 30 * k), (cx + 26 * k, cy - 30 * k), (cx + 40 * k, cy - 12 * k), (cx - 22 * k, cy - 12 * k)], (150, 190, 230))
        for wx in (-42, 46): c.el(cx + wx * k, cy + 22 * k, 17 * k, 17 * k, NAVY); c.el(cx + wx * k, cy + 22 * k, 7 * k, 7 * k, CREAM_D)
    elif kind == 'microwave':
        c.rr(cx - 70 * k, cy - 42 * k, cx + 70 * k, cy + 42 * k, 8 * k, (200, 206, 214)); c.rr(cx - 60 * k, cy - 32 * k, cx + 24 * k, cy + 32 * k, 5 * k, NAVY)
        c.el(cx + 46 * k, cy - 14 * k, 9 * k, 9 * k, NAVY_L); c.rr(cx + 36 * k, cy + 8 * k, cx + 58 * k, cy + 20 * k, 3 * k, AMBER)
    elif kind == 'thermostat':
        c.el(cx, cy, 52 * k, 52 * k, NAVY); c.el(cx, cy, 42 * k, 42 * k, (24, 46, 84))
        c.arc(cx, cy, 46 * k, 140, 400, AMBER, 5 * k); c.text(cx, cy + 2 * k, '72°', 26 * k, CREAM)
    elif kind == 'keyboard':
        c.rr(cx - 78 * k, cy - 30 * k, cx + 78 * k, cy + 30 * k, 8 * k, NAVY)
        for r in range(3):
            for q in range(8): c.rr(cx - 68 * k + q * 17 * k, cy - 22 * k + r * 15 * k, cx - 56 * k + q * 17 * k, cy - 12 * k + r * 15 * k, 2 * k, CREAM_D)
    elif kind == 'touch':
        icon(c, 'phone', cx - 8 * k, cy, k)
        c.el(cx + 14 * k, cy + 10 * k, 13 * k, 17 * k, (240, 196, 160)); c.rr(cx + 6 * k, cy + 12 * k, cx + 34 * k, cy + 60 * k, 10 * k, (240, 196, 160))
        c.arc(cx + 14 * k, cy - 4 * k, 22 * k, 200, 340, AMBER, 4 * k)
    elif kind == 'mic':
        c.rr(cx - 18 * k, cy - 50 * k, cx + 18 * k, cy + 6 * k, 18 * k, NAVY); c.arc(cx, cy - 10 * k, 32 * k, 20, 160, NAVY, 6 * k)
        c.line([(cx, cy + 22 * k), (cx, cy + 46 * k)], NAVY, 6 * k); c.rr(cx - 24 * k, cy + 44 * k, cx + 24 * k, cy + 52 * k, 4 * k, NAVY)
    elif kind == 'screen':
        icon(c, 'tv', cx, cy, k); c.rr(cx - 44 * k, cy - 24 * k, cx + 10 * k, cy - 14 * k, 4 * k, AMBER); c.rr(cx - 44 * k, cy - 6 * k, cx + 30 * k, cy + 2 * k, 4 * k, CREAM)
    elif kind == 'speaker':
        c.rr(cx - 40 * k, cy - 56 * k, cx + 40 * k, cy + 56 * k, 12 * k, NAVY); c.el(cx, cy + 18 * k, 24 * k, 24 * k, NAVY_L); c.el(cx, cy + 18 * k, 9 * k, 9 * k, AMBER)
        c.el(cx, cy - 30 * k, 11 * k, 11 * k, NAVY_L)
    elif kind == 'printer':
        c.rr(cx - 46 * k, cy - 56 * k, cx + 46 * k, cy - 14 * k, 4 * k, WHITE, NAVY, 3 * k)
        c.rr(cx - 70 * k, cy - 24 * k, cx + 70 * k, cy + 34 * k, 10 * k, NAVY); c.rr(cx - 44 * k, cy + 22 * k, cx + 44 * k, cy + 58 * k, 3 * k, WHITE, NAVY, 3 * k)
        c.el(cx + 52 * k, cy - 6 * k, 5 * k, 5 * k, AMBER)
    elif kind == 'photo':
        c.rr(cx - 46 * k, cy - 36 * k, cx + 46 * k, cy + 36 * k, 6 * k, WHITE, NAVY, 4 * k)
        c.poly([(cx - 38 * k, cy + 28 * k), (cx - 10 * k, cy - 6 * k), (cx + 8 * k, cy + 14 * k), (cx + 20 * k, cy + 2 * k), (cx + 38 * k, cy + 28 * k)], SAGE)
        c.el(cx + 22 * k, cy - 16 * k, 8 * k, 8 * k, AMBER)
    elif kind == 'folder':
        c.rr(cx - 50 * k, cy - 38 * k, cx - 6 * k, cy - 20 * k, 6 * k, AMBER); c.rr(cx - 50 * k, cy - 28 * k, cx + 50 * k, cy + 38 * k, 8 * k, AMBER_L)
    elif kind == 'apps':
        for i, col in enumerate([AMBER, SAGE, RED, NAVY_L]):
            x, y = cx + (i % 2 - 0.5) * 44 * k, cy + (i // 2 - 0.5) * 44 * k
            c.rr(x - 18 * k, y - 18 * k, x + 18 * k, y + 18 * k, 8 * k, col)
    elif kind == 'gear':
        for a in range(8):
            r = math.radians(a * 45); c.rr(cx + math.cos(r) * 34 * k - 9 * k, cy + math.sin(r) * 34 * k - 9 * k, cx + math.cos(r) * 34 * k + 9 * k, cy + math.sin(r) * 34 * k + 9 * k, 3 * k, NAVY)
        c.el(cx, cy, 34 * k, 34 * k, NAVY); c.el(cx, cy, 13 * k, 13 * k, CREAM)
    elif kind == 'arrow_in':
        c.rr(cx - 10 * k, cy - 34 * k, cx + 46 * k, cy + 34 * k, 8 * k, None, NAVY, 6 * k)
        c.line([(cx - 52 * k, cy), (cx + 14 * k, cy)], AMBER, 10 * k); c.poly([(cx + 26 * k, cy), (cx + 6 * k, cy - 18 * k), (cx + 6 * k, cy + 18 * k)], AMBER)
    elif kind == 'arrow_out':
        c.rr(cx - 46 * k, cy - 34 * k, cx + 10 * k, cy + 34 * k, 8 * k, None, NAVY, 6 * k)
        c.line([(cx - 14 * k, cy), (cx + 44 * k, cy)], AMBER, 10 * k); c.poly([(cx + 58 * k, cy), (cx + 38 * k, cy - 18 * k), (cx + 38 * k, cy + 18 * k)], AMBER)
    elif kind == 'memory':
        c.rr(cx - 56 * k, cy - 22 * k, cx + 56 * k, cy + 22 * k, 6 * k, (44, 120, 84))
        for q in range(4): c.rr(cx - 46 * k + q * 25 * k, cy - 14 * k, cx - 30 * k + q * 25 * k, cy + 8 * k, 2 * k, NAVY)
        for q in range(14): c.rr(cx - 50 * k + q * 7.5 * k, cy + 22 * k, cx - 46 * k + q * 7.5 * k, cy + 30 * k, 1, AMBER)

# ---------------- scenes ----------------
DEVICES = ['laptop', 'phone', 'tv', 'car', 'microwave', 'thermostat']
DEV_NAMES = ['Laptop', 'Phone', 'TV', 'Car', 'Microwave', 'Thermostat']
def devices_card(times, t):
    c = Card(); c.text(CW / 2, 40, 'Computers you might own', 28, NAVY)
    for i, (k, nm, t0) in enumerate(zip(DEVICES, DEV_NAMES, times)):
        sc = back((t - t0) / 0.4)
        if sc <= 0.01: continue
        cx, cy = 140 + (i % 3) * 225, 140 + (i // 3) * 160
        sub = blank(); icon(sub, k, cx, cy, 0.9); sub.text(cx, cy + 66, nm, 22, NAVY, FM)
        c.layer(sub, min(1.0, sc))
    return c

JOBS = [('IN', 'takes in info', 'arrow_in'), ('WORK', 'works on it', 'gear'), ('REMEMBER', 'remembers it', 'memory'), ('OUT', 'gives a result', 'arrow_out')]
def jobs_card(times, t):
    c = Card(); c.text(CW / 2, 38, 'A computer does 4 jobs', 28, NAVY)
    for i, ((w, sub_t, ic), t0) in enumerate(zip(JOBS, times)):
        a = ease((t - t0) / 0.35)
        if a <= 0.01: continue
        x0, y0 = 30 + (i % 2) * 340, 76 + (i // 2) * 162
        s = blank(); s.rr(x0, y0, x0 + 330, y0 + 148, 20, (255, 236, 200) if i % 3 == 0 else (247, 232, 206))
        icon(s, ic, x0 + 70, y0 + 74, 0.75); s.text(x0 + 140, y0 + 56, w, 34, NAVY, anchor='lm'); s.text(x0 + 140, y0 + 98, sub_t, 20, NAVY_L, FM, anchor='lm')
        c.layer(s, a, 0, (1 - a) * 20)
    return c

# kitchen components (card coordinates)
def _kitchen_base(c):
    c.rr(0, 0, CW, CH, 34, (252, 238, 212))
    for x in range(30, CW, 60): c.line([(x, 20), (x, 300)], (244, 226, 196), 2)  # wall tiles
    c.rr(14, 296, CW - 14, 316, 6, WOOD)                  # counter top
    c.rr(24, 314, CW - 24, CH - 16, 12, WOOD_D)           # counter front
    for x in (120, 300, 480): c.rr(x, 340, x + 24, 348, 4, AMBER_L)

def _bowl(c, cx=100):
    c.d.chord([(cx - 60) * S, 250 * S, (cx + 60) * S, 330 * S], 0, 180, fill=(80, 140, 190))
    c.rr(cx - 62, 284, cx + 62, 292, 4, (100, 160, 210))

def _ingredient(c, kind, x, y, sc=1.0):
    if kind == 'tomato':
        c.el(x, y, 22 * sc, 20 * sc, RED); c.poly([(x - 8 * sc, y - 20 * sc), (x, y - 12 * sc), (x + 8 * sc, y - 20 * sc), (x, y - 26 * sc)], SAGE)
    elif kind == 'carrot':
        c.poly([(x - 10 * sc, y - 22 * sc), (x + 10 * sc, y - 22 * sc), (x, y + 26 * sc)], (240, 140, 50)); c.poly([(x - 6 * sc, y - 22 * sc), (x, y - 38 * sc), (x + 6 * sc, y - 22 * sc)], SAGE)
    else:
        c.el(x, y, 17 * sc, 22 * sc, (255, 250, 240), (220, 200, 170), 2)

def _stove(c, cx=275):
    c.rr(cx - 82, 230, cx + 82, 298, 10, (60, 72, 96)); c.rr(cx - 70, 222, cx + 70, 234, 5, (40, 50, 70))
    for q in (-45, 0, 45): c.el(cx + q, 268, 9, 9, AMBER)

def _pot(c, cx=275, stir=0.0, steam=0.0):
    c.rr(cx - 56, 160, cx + 56, 224, 14, (120, 132, 150)); c.rr(cx - 66, 156, cx + 66, 168, 6, (150, 160, 176))
    for k in range(3):
        if steam > 0: c.arc(cx - 30 + k * 30, 128 - (steam * 10 + k * 4) % 16, 12, 180, 360, (200, 200, 210, int(200 * steam)), 4)
    a = math.radians(-60 + 30 * math.sin(stir))
    c.line([(cx + math.cos(a) * 10, 170 + math.sin(a) * 10), (cx + math.cos(a) * 80, 170 + math.sin(a) * 80 - 30)], WOOD_D, 7)

def _chip_chef(c, cx, cy, sc=1.0, blink=False):
    for q in range(5):
        for side in (-1, 1):
            c.rr(cx + side * 46 * sc - 6 * sc, cy - 30 * sc + q * 14 * sc, cx + side * 46 * sc + 6 * sc, cy - 24 * sc + q * 14 * sc, 2, (190, 196, 206))
    c.rr(cx - 42 * sc, cy - 40 * sc, cx + 42 * sc, cy + 40 * sc, 10 * sc, NAVY); c.rr(cx - 30 * sc, cy - 28 * sc, cx + 30 * sc, cy + 28 * sc, 6 * sc, NAVY_L)
    for side in (-1, 1):
        if blink: c.line([(cx + side * 13 * sc - 6 * sc, cy - 4 * sc), (cx + side * 13 * sc + 6 * sc, cy - 4 * sc)], CREAM, 3 * sc)
        else: c.el(cx + side * 13 * sc, cy - 4 * sc, 5 * sc, 7 * sc, CREAM)
    c.arc(cx, cy + 4 * sc, 12 * sc, 30, 150, AMBER, 3 * sc)
    c.rr(cx - 30 * sc, cy - 58 * sc, cx + 30 * sc, cy - 40 * sc, 4 * sc, WHITE)  # chef hat band
    for q in (-20, 0, 20): c.el(cx + q * sc, cy - 70 * sc, 18 * sc, 18 * sc, WHITE)

PLATES = [('Email', AMBER), ('Photos', SAGE), ('Music', RED), ('Notes', NAVY_L)]
def _plates(c, n, alpha_list=None):
    for i in range(n):
        x = 420 + (i % 2) * 120; y = 262 - (i // 2) * 74
        a = 1.0 if not alpha_list else alpha_list[i]
        if a <= 0.02: continue
        s = blank(); nm, col = PLATES[i]
        s.el(x, y, 52, 16, WHITE, (210, 200, 180), 2); s.rr(x - 32, y - 40, x + 32, y - 6, 8, col); s.text(x, y - 23, nm, 15, WHITE)
        c.layer(s, a)

def _pantry(c, open_=1.0, items=0, glow=0.0):
    x0, x1 = 600, 716
    c.rr(x0, 30, x1, 292, 10, (110, 76, 44))
    c.rr(x0 + 8, 40, x1 - 8, 284, 6, (70, 48, 30))
    for y in (110, 186, 262): c.rr(x0 + 8, y, x1 - 8, y + 6, 2, (150, 104, 62))
    kinds = ['photo', 'folder', 'apps']
    for i in range(items):
        icon(c, kinds[i], (x0 + x1) / 2, [86, 160, 236][i], 0.48)
    if open_ < 1:
        w = (x1 - x0) / 2 * (1 - open_)
        c.rr(x0, 30, x0 + w, 292, 6, (140, 96, 56)); c.rr(x1 - w, 30, x1, 292, 6, (140, 96, 56))
    c.text((x0 + x1) / 2, 18, '', 1, NAVY)

def kitchen_card(t, T, beat):
    """beat: which part is in focus. T: dict of timings (video time)."""
    c = Card(bg=None); _kitchen_base(c)
    dim = lambda on: 1.0 if on else 0.32
    # ingredients + bowl (input)
    s = blank(); _bowl(s)
    if beat in ('kitchen', 'input'):
        for i, k in enumerate(['tomato', 'carrot', 'egg']):
            ti = T['input'] + 0.4 + i * 0.35
            p = ease((t - ti) / 0.45) if beat == 'input' else 1.0
            _ingredient(s, k, 70 + i * 30, 120 + p * 140)
    c.layer(s, dim(beat in ('kitchen', 'input')))
    # stove, pot, chip chef (processing)
    s = blank(); _stove(s); fast = beat == 'process' and t > T.get('fast', 1e9)
    _pot(s, stir=t * (14 if fast else 4), steam=0.8 if beat == 'process' else 0.3)
    _chip_chef(s, 275, 98 + (math.sin(t * 20) * 3 if fast else 0), 0.8, blink=(int(t * 3) % 9 == 0))
    if fast:
        for q in range(4): s.line([(190 - q * 6, 60 + q * 22), (150 - q * 6, 60 + q * 22)], (200, 160, 100), 4)
    c.layer(s, dim(beat in ('kitchen', 'process')))
    # counter + plates (memory)
    s = blank()
    if beat in ('memory', 'catch', 'storage', 'output', 'kitchen'):
        if beat == 'memory': n = sum(1 for i in range(4) if t > T['memory'] + 1.2 + i * 0.9); _plates(s, n)
        elif beat == 'catch':
            al = [1 - ease((t - T['wipe']) / 0.35)] * 4; _plates(s, 4, al)
        elif beat == 'kitchen': pass
    c.layer(s, dim(beat in ('kitchen', 'memory', 'catch')))
    # pantry (storage)
    s = blank()
    if beat == 'storage':
        op = ease((t - T['storage'] - 0.3) / 0.6); items = sum(1 for i in range(3) if t > T['items'] + i * 0.8)
        _pantry(s, op, items)
    else: _pantry(s, 0.0 if beat != 'output' else 0.0, 0)
    c.layer(s, dim(beat in ('kitchen', 'storage')))
    # output: served plate with cloche
    if beat == 'output':
        s = blank(); lift = ease((t - T['output'] - 0.6) / 0.5)
        s.el(470, 282, 84, 18, WHITE, (210, 200, 180), 2)
        if lift < 1: s.d.chord([(410) * S, (196 - lift * 60) * S, (530) * S, (316 - lift * 60) * S], 180, 360, fill=(200, 206, 214))
        s.el(470, 230 - lift * 60, 8, 8, (170, 176, 186))
        if lift > 0.5:
            for k in range(5):
                a = math.radians(-90 + (k - 2) * 30); s.line([(470 + math.cos(a) * 60, 250 + math.sin(a) * 60), (470 + math.cos(a) * 84, 250 + math.sin(a) * 84)], AMBER, 6)
        c.layer(s)
    # lights off overlay (catch)
    if beat == 'catch':
        a = ease((t - T['off']) / 0.3) * (1 - ease((t - T['storage'] + 0.2) / 0.3))
        if a > 0: o = blank(); o.rr(0, 0, CW, CH, 34, (8, 18, 38, int(200 * a))); c.layer(o)
    # label chip
    labels = {'kitchen': 'A computer is like a kitchen', 'input': 'INPUT', 'process': 'PROCESSOR (CPU)', 'memory': 'MEMORY (RAM)',
              'catch': 'MEMORY (RAM)', 'storage': 'STORAGE (SSD / hard drive)', 'output': 'OUTPUT'}
    c.chip(24, 22, labels[beat], 22)
    return c

def callout_row(items, names, times, t, title=None, alpha=1.0):
    """band with three icons + labels popping in"""
    c = blank(); c.rr(30, 80, CW - 30, 300, 26, (255, 250, 240, int(245 * alpha)), (230, 210, 176, int(255 * alpha)), 3)
    if title: c.text(CW / 2, 112, title, 22, NAVY_L, FM)
    for i, (k, nm, t0) in enumerate(zip(items, names, times)):
        sc = back((t - t0) / 0.4)
        if sc <= 0.01: continue
        cx = 140 + i * 225; s = blank(); icon(s, k, cx, 196, 0.8); s.text(cx, 266, nm, 22, NAVY, FM)
        c.layer(s, min(1.0, sc) * alpha)
    return c

def phone_card(t, times):
    """send-a-text example: phone centre, five role labels light up in order"""
    c = Card(); cx, cy = CW / 2, 205
    c.rr(cx - 62, cy - 150, cx + 62, cy + 150, 22, NAVY); c.rr(cx - 52, cy - 128, cx + 52, cy + 124, 10, (236, 240, 248))
    typed = 'Running late!'; n = int(clamp((t - times[0]) / 1.4) * len(typed))
    if t < times[4]:
        c.rr(cx - 46, cy + 70, cx + 46, cy + 104, 10, WHITE, (200, 206, 214), 2); c.text(cx - 40, cy + 87, typed[:n] + ('|' if int(t * 3) % 2 else ''), 13, NAVY, FM, 'lm')
    if t >= times[4]:
        c.rr(cx - 46, cy - 20, cx + 48, cy + 14, 12, (64, 120, 220)); c.text(cx + 1, cy - 3, typed, 12, WHITE, FM)
        c.text(cx + 40, cy + 26, 'Sent ✓', 12, (64, 120, 220), FB, 'rm')
    roles = [('Input', 'your thumbs', 120, 92), ('Processor', 'does the work', 120, 205), ('Memory', 'holds the message', 120, 318),
             ('Storage', 'saves the chat', CW - 120, 130), ('Output', 'screen shows it sent', CW - 120, 280)]
    for i, (nm, sub, x, y) in enumerate(roles):
        on = t >= times[i]; a = 1.0 if on else 0.35
        bg = AMBER if (on and (i == 4 or t < times[i + 1])) else ((255, 228, 180) if on else (240, 232, 216))
        s = blank(); s.rr(x - 104, y - 40, x + 104, y + 40, 18, bg); s.text(x, y - 12, nm, 23, NAVY); s.text(x, y + 16, sub, 17, NAVY_L, FM)
        c.layer(s, a)
    return c

RECAP = [('Ingredients in', 'Input'), ('Cook works', 'Processor'), ('Counter holds', 'Memory'), ('Pantry keeps', 'Storage'), ('Meal comes out', 'Output')]
def recap_card(t, times):
    c = Card(); c.text(CW / 2, 40, "That's a computer", 30, NAVY)
    draw = [lambda s, x, y: _ingredient(s, 'tomato', x, y + 6, 1.3), lambda s, x, y: _chip_chef(s, x, y + 20, 0.55),
            lambda s, x, y: (s.rr(x - 50, y + 10, x + 50, y + 24, 5, WOOD), s.rr(x - 26, y - 26, x + 26, y + 6, 6, AMBER)),
            lambda s, x, y: (s.rr(x - 34, y - 46, x + 34, y + 40, 8, (110, 76, 44)), s.rr(x - 26, y - 4, x + 26, y + 2, 2, (150, 104, 62)), icon(s, 'folder', x, y - 22, 0.3)),
            lambda s, x, y: (s.el(x, y + 22, 50, 12, WHITE, (210, 200, 180), 2), s.d.chord([(x - 36) * S, (y - 20) * S, (x + 36) * S, (y + 44) * S], 180, 360, fill=(200, 206, 214)))]
    for i, ((a_txt, b_txt), t0) in enumerate(zip(RECAP, times)):
        on = t >= t0; cur = on and (i == 4 or t < times[i + 1])
        x = 80 + i * 142; y = 190
        s = blank(); s.rr(x - 64, 92, x + 64, 330, 20, AMBER if cur else ((255, 232, 190) if on else (244, 236, 222)))
        draw[i](s, x, y - 30); s.text(x, 262, b_txt, 20, NAVY); s.text(x, 292, a_txt, 15, NAVY_L, FM)
        c.layer(s, 1.0 if on else 0.4, 0, -6 * back((t - t0) / 0.3) if on and t - t0 < 0.3 else 0)
        if i < 4: c.line([(x + 68, 210), (x + 76, 210)], NAVY_L, 4)
    return c
