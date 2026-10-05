"""Explainer-card template kit + icon library.

Every template draws onto a 730x410 cream card (2x supersampled) and takes `times`,
a list of reveal times (one per item, in video seconds) worked out from the script.

Templates (card "type" in an episode file):
  grid      title + up to 6 icon/label items that pop in one by one
  tiles     title + up to 4 tiles: big WORD, small sub-line, icon
  callout   title + 3 icons with labels in a row
  statement one big sentence (+ optional sub-line and icon)
  compare   two columns (left vs right), each with icon, title and up to 3 points
  steps     title + up to 5 tiles that light up in order (great for recaps)
  flow      up to 4 icons joined by arrows that light up in order (A -> B -> C)
"""
import math
from PIL import Image, ImageDraw, ImageFont
from .core import F_BOLD as FB, F_MED as FM

NAVY = (11, 29, 59); NAVY_L = (40, 64, 104); AMBER = (247, 168, 37); AMBER_L = (255, 205, 110)
CREAM = (255, 247, 230); CREAM_D = (238, 222, 194); SAGE = (107, 143, 107); RED = (220, 84, 64)
BLUE = (64, 104, 160); SKY = (150, 190, 230); WHITE = (255, 255, 255); GREY = (200, 206, 214)
CW, CH, S = 730, 410, 2
_f = {}
def F(path, size):
    k = (path, size)
    if k not in _f: _f[k] = ImageFont.truetype(path, int(size * S))
    return _f[k]
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

class Card:
    def __init__(self, bg=CREAM):
        self.im = Image.new('RGBA', (CW * S, CH * S), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
        if bg: self.d.rounded_rectangle([0, 0, CW * S - 1, CH * S - 1], 34 * S, fill=bg)
    def rr(self, x0, y0, x1, y1, r, fill, outline=None, w=0):
        self.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], r * S, fill=fill, outline=outline, width=int(w * S))
    def el(self, cx, cy, rx, ry, fill, outline=None, w=0):
        self.d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill, outline=outline, width=int(w * S))
    def poly(self, pts, fill): self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill)
    def line(self, pts, fill, w): self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(w * S), joint='curve')
    def arc(self, cx, cy, r, a0, a1, fill, w): self.d.arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], a0, a1, fill=fill, width=int(w * S))
    def text(self, x, y, s, size, fill, font=FB, anchor='mm'): self.d.text((x * S, y * S), s, font=F(font, size), fill=fill, anchor=anchor)
    def tw(self, s, size, font=FB): return self.d.textlength(s, font=F(font, size)) / S
    def fit(self, s, size, maxw, font=FB):
        while size > 12 and self.tw(s, size, font) > maxw: size -= 1
        return size
    def layer(self, sub, alpha=1.0, x=0, y=0):
        im = sub.im
        if alpha < 1.0: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda p: int(p * alpha)))
        self.im.alpha_composite(im, (int(x * S), int(y * S)))
    def chip(self, x, y, s, size=22, bg=AMBER, fg=NAVY):
        w = self.tw(s, size) + 36; self.rr(x, y, x + w, y + size * 1.7, size * 0.85, bg); self.text(x + w / 2, y + size * 0.85, s, size, fg); return w
    def title(self, s, y=40, size=28):
        self.text(CW / 2, y, s, self.fit(s, size, CW - 60), NAVY)

def blank(): return Card(bg=None)

# ------------------------------------------------------------------ icons
ICONS = ['laptop', 'phone', 'tv', 'car', 'microwave', 'thermostat', 'keyboard', 'touch', 'mic', 'screen', 'speaker', 'printer',
         'photo', 'folder', 'apps', 'gear', 'arrow_in', 'arrow_out', 'memory', 'chip', 'wifi', 'cloud', 'update', 'lock', 'key',
         'globe', 'router', 'server', 'download', 'upload', 'question', 'check', 'cross', 'battery', 'bulb', 'user', 'mail',
         'search', 'browser', 'code', 'link', 'shield', 'warning', 'house', 'plug', 'clock', 'bug', 'chat', 'calendar', 'star']

def icon(c, kind, cx, cy, s=1.0):
    k = s
    R = lambda x0, y0, x1, y1, r, f, o=None, w=0: c.rr(cx + x0 * k, cy + y0 * k, cx + x1 * k, cy + y1 * k, r * k, f, o, w * k)
    E = lambda x, y, rx, ry, f, o=None, w=0: c.el(cx + x * k, cy + y * k, rx * k, ry * k, f, o, w * k)
    L = lambda pts, f, w: c.line([(cx + x * k, cy + y * k) for x, y in pts], f, w * k)
    P = lambda pts, f: c.poly([(cx + x * k, cy + y * k) for x, y in pts], f)
    A = lambda x, y, r, a0, a1, f, w: c.arc(cx + x * k, cy + y * k, r * k, a0, a1, f, w * k)
    T = lambda x, y, s_, size, f: c.text(cx + x * k, cy + y * k, s_, size * k, f)
    if kind == 'laptop':
        R(-62, -46, 62, 30, 8, NAVY); R(-52, -37, 52, 21, 4, BLUE); P([(-78, 32), (78, 32), (70, 44), (-70, 44)], NAVY_L)
    elif kind == 'phone':
        R(-32, -58, 32, 58, 12, NAVY); R(-25, -46, 25, 44, 5, BLUE); R(-10, -53, 10, -50, 2, NAVY_L)
    elif kind == 'tv':
        R(-70, -46, 70, 34, 8, NAVY); R(-60, -37, 60, 25, 4, BLUE); L([(-20, 52), (0, 34), (20, 52)], NAVY, 6)
    elif kind == 'car':
        P([(-74, 20), (-64, -6), (-36, -12), (-18, -38), (30, -38), (52, -10), (74, -4), (76, 20)], AMBER)
        P([(-10, -30), (26, -30), (40, -12), (-22, -12)], SKY)
        for wx in (-42, 46): E(wx, 22, 17, 17, NAVY); E(wx, 22, 7, 7, CREAM_D)
    elif kind == 'microwave':
        R(-70, -42, 70, 42, 8, GREY); R(-60, -32, 24, 32, 5, NAVY); E(46, -14, 9, 9, NAVY_L); R(36, 8, 58, 20, 3, AMBER)
    elif kind == 'thermostat':
        E(0, 0, 52, 52, NAVY); E(0, 0, 42, 42, (24, 46, 84)); A(0, 0, 46, 140, 400, AMBER, 5); T(0, 2, '72°', 26, CREAM)
    elif kind == 'keyboard':
        R(-78, -30, 78, 30, 8, NAVY)
        for r in range(3):
            for q in range(8): R(-68 + q * 17, -22 + r * 15, -56 + q * 17, -12 + r * 15, 2, CREAM_D)
    elif kind == 'touch':
        icon(c, 'phone', cx - 8 * k, cy, k); E(14, 10, 13, 17, (240, 196, 160)); R(6, 12, 34, 60, 10, (240, 196, 160)); A(14, -4, 22, 200, 340, AMBER, 4)
    elif kind == 'mic':
        R(-18, -50, 18, 6, 18, NAVY); A(0, -10, 32, 20, 160, NAVY, 6); L([(0, 22), (0, 46)], NAVY, 6); R(-24, 44, 24, 52, 4, NAVY)
    elif kind == 'screen':
        icon(c, 'tv', cx, cy, k); R(-44, -24, 10, -14, 4, AMBER); R(-44, -6, 30, 2, 4, CREAM)
    elif kind == 'speaker':
        R(-40, -56, 40, 56, 12, NAVY); E(0, 18, 24, 24, NAVY_L); E(0, 18, 9, 9, AMBER); E(0, -30, 11, 11, NAVY_L)
    elif kind == 'printer':
        R(-46, -56, 46, -14, 4, WHITE, NAVY, 3); R(-70, -24, 70, 34, 10, NAVY); R(-44, 22, 44, 58, 3, WHITE, NAVY, 3); E(52, -6, 5, 5, AMBER)
    elif kind == 'photo':
        R(-46, -36, 46, 36, 6, WHITE, NAVY, 4); P([(-38, 28), (-10, -6), (8, 14), (20, 2), (38, 28)], SAGE); E(22, -16, 8, 8, AMBER)
    elif kind == 'folder':
        R(-50, -38, -6, -20, 6, AMBER); R(-50, -28, 50, 38, 8, AMBER_L)
    elif kind == 'apps':
        for i, col in enumerate([AMBER, SAGE, RED, NAVY_L]):
            x, y = (i % 2 - 0.5) * 44, (i // 2 - 0.5) * 44; R(x - 18, y - 18, x + 18, y + 18, 8, col)
    elif kind == 'gear':
        for a in range(8):
            r = math.radians(a * 45); R(math.cos(r) * 34 - 9, math.sin(r) * 34 - 9, math.cos(r) * 34 + 9, math.sin(r) * 34 + 9, 3, NAVY)
        E(0, 0, 34, 34, NAVY); E(0, 0, 13, 13, CREAM)
    elif kind == 'arrow_in':
        R(-10, -34, 46, 34, 8, None, NAVY, 6); L([(-52, 0), (14, 0)], AMBER, 10); P([(26, 0), (6, -18), (6, 18)], AMBER)
    elif kind == 'arrow_out':
        R(-46, -34, 10, 34, 8, None, NAVY, 6); L([(-14, 0), (44, 0)], AMBER, 10); P([(58, 0), (38, -18), (38, 18)], AMBER)
    elif kind == 'memory':
        R(-56, -22, 56, 22, 6, (44, 120, 84))
        for q in range(4): R(-46 + q * 25, -14, -30 + q * 25, 8, 2, NAVY)
        for q in range(14): R(-50 + q * 7.5, 22, -46 + q * 7.5, 30, 1, AMBER)
    elif kind == 'chip':
        for q in range(5):
            for sd in (-1, 1): R(sd * 46 - 6, -30 + q * 14, sd * 46 + 6, -24 + q * 14, 2, GREY); R(-30 + q * 14, sd * 46 - 6, -24 + q * 14, sd * 46 + 6, 2, GREY)
        R(-42, -42, 42, 42, 10, NAVY); R(-28, -28, 28, 28, 6, NAVY_L); T(0, 0, 'CPU', 18, AMBER)
    elif kind == 'wifi':
        for r in (60, 40, 20): A(0, 30, r, 225, 315, NAVY, 10)
        E(0, 30, 8, 8, AMBER)
    elif kind == 'cloud':
        E(-30, 10, 30, 28, BLUE); E(10, -10, 40, 38, BLUE); E(40, 12, 28, 26, BLUE); R(-50, 10, 60, 38, 14, BLUE)
    elif kind == 'update':
        A(0, 0, 40, 30, 330, NAVY, 9); P([(40, -2), (26, -22), (54, -20)], NAVY); L([(0, -18), (0, 18)], AMBER, 8); P([(0, -30), (-14, -12), (14, -12)], AMBER)
    elif kind == 'lock':
        A(0, -14, 26, 180, 360, NAVY, 10); R(-36, -14, 36, 44, 8, AMBER); E(0, 12, 8, 8, NAVY); R(-3, 12, 3, 30, 2, NAVY)
    elif kind == 'key':
        E(-30, 0, 24, 24, AMBER); E(-30, 0, 9, 9, CREAM); R(-8, -6, 56, 6, 3, AMBER); R(34, 6, 42, 20, 2, AMBER); R(48, 6, 56, 16, 2, AMBER)
    elif kind == 'globe':
        E(0, 0, 50, 50, BLUE); E(0, 0, 22, 50, None, CREAM, 4); L([(-50, 0), (50, 0)], CREAM, 4); A(0, 40, 50, 230, 310, CREAM, 4); A(0, -40, 50, 50, 130, CREAM, 4)
    elif kind == 'router':
        R(-62, 0, 62, 36, 10, NAVY); L([(-40, 0), (-52, -46)], NAVY, 7); L([(40, 0), (52, -46)], NAVY, 7)
        for q in range(4): E(-36 + q * 18, 18, 5, 5, (120, 230, 140) if q < 3 else AMBER)
        A(0, -10, 24, 230, 310, AMBER, 5); A(0, -10, 40, 235, 305, AMBER, 5)
    elif kind == 'server':
        for q in range(3):
            R(-50, -54 + q * 38, 50, -22 + q * 38, 6, NAVY); E(-34, -38 + q * 38, 5, 5, (120, 230, 140)); R(-10, -41 + q * 38, 36, -35 + q * 38, 2, NAVY_L)
    elif kind in ('download', 'upload'):
        R(-50, 30, 50, 46, 4, NAVY); L([(0, -46), (0, 18)] if kind == 'download' else [(0, 24), (0, -40)], AMBER, 12)
        P([(0, 34), (-24, 6), (24, 6)] if kind == 'download' else [(0, -52), (-24, -24), (24, -24)], AMBER)
    elif kind == 'question':
        E(0, 0, 50, 50, AMBER); T(0, 2, '?', 64, NAVY)
    elif kind == 'check':
        E(0, 0, 50, 50, SAGE); L([(-24, 2), (-6, 22), (26, -18)], WHITE, 12)
    elif kind == 'cross':
        E(0, 0, 50, 50, RED); L([(-20, -20), (20, 20)], WHITE, 12); L([(20, -20), (-20, 20)], WHITE, 12)
    elif kind == 'battery':
        R(-56, -28, 48, 28, 8, None, NAVY, 7); R(48, -12, 60, 12, 3, NAVY); R(-46, -18, 10, 18, 4, SAGE)
    elif kind == 'bulb':
        E(0, -14, 38, 38, AMBER_L); R(-18, 20, 18, 46, 6, NAVY)
        for a in (-150, -120, -90, -60, -30):
            r = math.radians(a); L([(math.cos(r) * 46, -14 + math.sin(r) * 46), (math.cos(r) * 60, -14 + math.sin(r) * 60)], AMBER, 6)
    elif kind == 'user':
        E(0, -22, 22, 22, NAVY_L); c.d.chord([(cx - 44 * k) * S, (cy + 4 * k) * S, (cx + 44 * k) * S, (cy + 84 * k) * S], 180, 360, fill=NAVY_L)
    elif kind == 'mail':
        R(-56, -36, 56, 36, 8, WHITE, NAVY, 5); L([(-52, -30), (0, 8), (52, -30)], NAVY, 5)
    elif kind == 'search':
        E(-10, -10, 32, 32, None, NAVY, 10); L([(14, 14), (44, 44)], NAVY, 12)
    elif kind == 'browser':
        R(-72, -50, 72, 50, 10, WHITE, NAVY, 5); R(-72, -50, 72, -26, 10, NAVY)
        for q in range(3): E(-58 + q * 14, -38, 4, 4, [RED, AMBER, SAGE][q])
        R(-56, -14, 56, -2, 6, GREY); R(-56, 10, 20, 18, 4, CREAM_D); R(-56, 26, 40, 34, 4, CREAM_D)
    elif kind == 'code':
        R(-66, -46, 66, 46, 10, NAVY); T(-6, 2, '</>', 40, AMBER)
    elif kind == 'link':
        R(-58, -16, 0, 16, 16, None, NAVY, 9); R(0, -16, 58, 16, 16, None, AMBER, 9)
    elif kind == 'shield':
        P([(0, -52), (44, -36), (40, 14), (0, 52), (-40, 14), (-44, -36)], SAGE); L([(-16, 0), (-2, 16), (20, -14)], WHITE, 9)
    elif kind == 'warning':
        P([(0, -50), (52, 42), (-52, 42)], AMBER); R(-5, -20, 5, 14, 3, NAVY); E(0, 28, 6, 6, NAVY)
    elif kind == 'house':
        P([(-56, -4), (0, -50), (56, -4)], RED); R(-42, -6, 42, 46, 4, CREAM_D); R(-12, 14, 12, 46, 3, NAVY_L)
    elif kind == 'plug':
        R(-30, -20, 30, 30, 10, NAVY); R(-18, -46, -8, -20, 3, GREY); R(8, -46, 18, -20, 3, GREY); L([(0, 30), (0, 54)], NAVY, 8)
    elif kind == 'clock':
        E(0, 0, 50, 50, WHITE, NAVY, 6); L([(0, 0), (0, -30)], NAVY, 6); L([(0, 0), (22, 10)], NAVY, 5); E(0, 0, 6, 6, AMBER)
    elif kind == 'bug':
        E(0, 6, 26, 36, (90, 70, 50)); E(0, -34, 16, 14, (70, 54, 40))
        for sd in (-1, 1):
            for q in range(3): L([(sd * 22, -10 + q * 18), (sd * 46, -20 + q * 22)], (70, 54, 40), 4)
            E(sd * 30, -8, 24, 12, (200, 220, 240, 180))
    elif kind == 'chat':
        R(-60, -42, 44, 20, 16, BLUE); P([(-30, 18), (-44, 40), (-10, 18)], BLUE); R(-20, -10, 64, 46, 16, AMBER_L)
    elif kind == 'calendar':
        R(-50, -40, 50, 48, 8, WHITE, NAVY, 5); R(-50, -40, 50, -16, 8, RED); T(0, 16, '7', 36, NAVY)
    elif kind == 'star':
        P([(math.cos(math.radians(-90 + i * 36)) * (52 if i % 2 == 0 else 22), math.sin(math.radians(-90 + i * 36)) * (52 if i % 2 == 0 else 22)) for i in range(10)], AMBER)
    else:
        E(0, 0, 46, 46, AMBER_L); T(0, 2, (kind or '?')[:2].upper(), 30, NAVY)

# ------------------------------------------------------------------ templates
def _pop(t, t0, d=0.4): return back((t - t0) / d)

def grid(spec, t, times):
    c = Card(); items = spec['items'][:6]; c.title(spec.get('title', ''))
    n = len(items); cols = 3 if n > 4 else max(1, min(n, 3 if n == 3 else 2))
    rows = (n + cols - 1) // cols
    for i, (it, t0) in enumerate(zip(items, times)):
        sc = _pop(t, t0)
        if sc <= 0.01: continue
        cx = CW / 2 + ((i % cols) - (cols - 1) / 2) * (680 / cols); cy = (140 if rows > 1 else 205) + (i // cols) * 160
        s = blank(); icon(s, it['icon'], cx, cy, 0.85); s.text(cx, cy + 66, it['label'], s.fit(it['label'], 22, 680 / cols - 20, FM), NAVY, FM)
        c.layer(s, min(1.0, sc), 0, (1 - min(1.0, sc)) * 16)
    return c

def tiles(spec, t, times):
    c = Card(); c.title(spec.get('title', ''), 38); items = spec['items'][:4]; n = len(items)
    for i, (it, t0) in enumerate(zip(items, times)):
        a = ease((t - t0) / 0.35)
        if a <= 0.01: continue
        if n <= 2: x0, y0, w, h = 30 + i * 340, 90, 330, 290
        else: x0, y0, w, h = 30 + (i % 2) * 340, 76 + (i // 2) * 162, 330, 148
        s = blank(); s.rr(x0, y0, x0 + w, y0 + h, 20, (255, 236, 200) if i % 3 == 0 else (247, 232, 206))
        icon(s, it['icon'], x0 + 70, y0 + h / 2, 0.75)
        s.text(x0 + 140, y0 + h / 2 - 18, it['word'], s.fit(it['word'], 34, w - 150), NAVY, anchor='lm')
        s.text(x0 + 140, y0 + h / 2 + 24, it.get('sub', ''), s.fit(it.get('sub', ''), 20, w - 150, FM), NAVY_L, FM, anchor='lm')
        c.layer(s, a, 0, (1 - a) * 20)
    return c

def callout(spec, t, times):
    c = Card(); c.title(spec.get('title', ''), 60, 26); items = spec['items'][:3]
    for i, (it, t0) in enumerate(zip(items, times)):
        sc = _pop(t, t0)
        if sc <= 0.01: continue
        cx = CW / 2 + (i - (len(items) - 1) / 2) * 225
        s = blank(); icon(s, it['icon'], cx, 205, 0.95); s.text(cx, 300, it['label'], s.fit(it['label'], 24, 210, FM), NAVY, FM)
        c.layer(s, min(1.0, sc), 0, (1 - min(1.0, sc)) * 16)
    return c

def statement(spec, t, times):
    c = Card(); a = ease((t - (times[0] if times else 0)) / 0.4)
    s = blank(); y = 205
    if spec.get('icon'): icon(s, spec['icon'], CW / 2, 120, 1.0); y = 255
    d = ImageDraw.Draw(Image.new('L', (1, 1)))
    lines, size = [], 40
    while True:
        lines, cur = [], ''
        for w in spec['text'].split():
            tst = (cur + ' ' + w).strip()
            if s.tw(tst, size) <= 640: cur = tst
            else: lines.append(cur); cur = w
        lines.append(cur)
        if len(lines) <= 3 or size <= 26: break
        size -= 2
    y0 = y - (len(lines) - 1) * size * 0.65
    for i, ln in enumerate(lines): s.text(CW / 2, y0 + i * size * 1.3, ln, size, NAVY)
    if spec.get('sub'): s.text(CW / 2, min(380, y0 + len(lines) * size * 1.3 + 14), spec['sub'], s.fit(spec['sub'], 22, 640, FM), NAVY_L, FM)
    c.layer(s, a, 0, (1 - a) * 18); return c

def compare(spec, t, times):
    c = Card(); c.title(spec.get('title', ''), 36)
    for i, side in enumerate(('left', 'right')):
        col = spec[side]; t0 = times[i] if i < len(times) else 0; a = ease((t - t0) / 0.35)
        if a <= 0.01: continue
        x0 = 30 + i * 340; s = blank(); s.rr(x0, 70, x0 + 330, 390, 22, (255, 236, 200) if i == 0 else (232, 240, 236))
        icon(s, col['icon'], x0 + 165, 135, 0.8); s.text(x0 + 165, 205, col['title'], s.fit(col['title'], 30, 300), NAVY)
        for j, p in enumerate(col.get('points', [])[:3]):
            s.el(x0 + 30, 250 + j * 42, 6, 6, AMBER); s.text(x0 + 46, 250 + j * 42, p, s.fit(p, 19, 270, FM), NAVY_L, FM, 'lm')
        c.layer(s, a, (1 - a) * (-20 if i == 0 else 20), 0)
    if all(t >= x for x in times[:2]):
        c.el(CW / 2, 230, 26, 26, NAVY); c.text(CW / 2, 231, 'vs', 20, CREAM)
    return c

def steps(spec, t, times):
    c = Card(); c.title(spec.get('title', ''), 40, 30); items = spec['items'][:5]; n = len(items)
    gap = (CW - 40) / n
    for i, (it, t0) in enumerate(zip(items, times)):
        on = t >= t0; cur = on and (i == n - 1 or t < times[i + 1])
        x = 20 + gap * (i + 0.5); s = blank(); w = gap - 14
        s.rr(x - w / 2, 92, x + w / 2, 330, 20, AMBER if cur else ((255, 232, 190) if on else (244, 236, 222)))
        icon(s, it['icon'], x, 165, 0.62 if n >= 5 else 0.75)
        s.text(x, 262, it['label'], s.fit(it['label'], 20, w - 12), NAVY)
        if it.get('sub'): s.text(x, 292, it['sub'], s.fit(it['sub'], 15, w - 12, FM), NAVY_L, FM)
        lift = -6 * back((t - t0) / 0.3) if on and t - t0 < 0.3 else 0
        c.layer(s, 1.0 if on else 0.4, 0, lift)
    return c

def flow(spec, t, times):
    c = Card(); c.title(spec.get('title', ''), 40, 28); items = spec['items'][:4]; n = len(items)
    gap = (CW - 60) / n
    for i, (it, t0) in enumerate(zip(items, times)):
        on = t >= t0; x = 30 + gap * (i + 0.5); a = ease((t - t0) / 0.35) if on else 0
        s = blank(); s.el(x, 190, 68, 68, (255, 236, 200) if on else (244, 236, 222)); icon(s, it['icon'], x, 190, 0.72)
        s.text(x, 290, it['label'], s.fit(it['label'], 21, gap - 10), NAVY)
        if it.get('sub'): s.text(x, 320, it['sub'], s.fit(it['sub'], 15, gap - 10, FM), NAVY_L, FM)
        c.layer(s, 0.35 + 0.65 * a)
        if i < n - 1:
            a2 = ease((t - times[i + 1]) / 0.35) if i + 1 < len(times) else 0
            x1, x2 = x + 76, x + gap - 76
            c.line([(x1, 190), (x2, 190)], AMBER if a2 > 0.5 else GREY, 6); c.poly([(x2 + 10, 190), (x2 - 4, 180), (x2 - 4, 200)], AMBER if a2 > 0.5 else GREY)
    return c

TEMPLATES = {'grid': grid, 'tiles': tiles, 'callout': callout, 'statement': statement, 'compare': compare, 'steps': steps, 'flow': flow}
def n_reveals(spec):
    t = spec['type']
    if t == 'statement': return 1
    if t == 'compare': return 2
    return len(spec.get('items', []))
def render(spec, t, times):
    return TEMPLATES[spec['type']](spec, t, times)
