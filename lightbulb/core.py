"""Shared constants, easing, fonts, glows, captions and overlays for all Lightbulb Lab videos."""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
W, H, FPS = 1920, 1080, 30

NAVY = (11, 29, 59); NAVY_L = (40, 64, 104); AMBER = (247, 168, 37); AMBER_L = (255, 205, 110)
CREAM = (255, 247, 230); SAGE = (107, 143, 107); RED = (220, 84, 64)
F_BOLD = os.path.join(ASSETS, 'fonts', 'Poppins-Bold.ttf')
F_MED = os.path.join(ASSETS, 'fonts', 'Poppins-Medium.ttf')

_fonts = {}
def font(path, size):
    k = (path, int(size))
    if k not in _fonts: _fonts[k] = ImageFont.truetype(path, int(size))
    return _fonts[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def ramp(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)

def radial(r, color, alpha, power=2):
    g = np.linspace(-1, 1, 2 * r); d = np.sqrt(g[None, :] ** 2 + g[:, None] ** 2)
    arr = np.zeros((2 * r, 2 * r, 4), np.uint8); arr[..., :3] = color
    arr[..., 3] = (np.clip(1 - d, 0, 1) ** power * alpha).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')
GLOW = radial(320, AMBER, 200)
LAMP = radial(700, (255, 190, 90), 60)

def vignette(w=W, h=H):
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h * 0.46) / (h * 0.62)) ** 2)
    a = (np.clip(d - 0.55, 0, 1) ** 1.6 * 230).astype(np.uint8)
    return Image.fromarray(np.dstack([np.zeros_like(a)] * 3 + [a]), 'RGBA')

class Motes:
    """dust drifting through the lamp light (draw behind the characters)"""
    def __init__(self, n=40, seed=7):
        rnd = random.Random(seed)
        self.m = [(rnd.uniform(520, 1400), rnd.uniform(220, 700), rnd.uniform(1.5, 4), rnd.uniform(0, 6.28), rnd.uniform(0.15, 0.4)) for _ in range(n)]
    def draw(self, fr, t, k=1.0):
        lay = Image.new('RGBA', fr.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for x, y, r, ph, sp in self.m:
            mx = x + math.sin(t * sp + ph) * 30; my = y - (t * 12 * sp) % 80 + math.cos(t * sp * 1.3 + ph) * 10
            a = int((90 + 70 * math.sin(t * 2 + ph)) * k)
            d.ellipse([mx - r, my - r, mx + r, my + r], fill=(255, 220, 150, max(0, a)))
        fr.alpha_composite(lay)

def wrap(d, text, f, maxw):
    out, cur = [], ''
    for w in text.split():
        tst = (cur + ' ' + w).strip()
        if d.textlength(tst, font=f) <= maxw: cur = tst
        else: out.append(cur); cur = w
    out.append(cur); return out

CAP_F = font(F_MED, 46)
def caption(fr, txt):
    """bottom caption box (16:9 videos)"""
    if not txt: return
    d = ImageDraw.Draw(fr); lines = wrap(d, txt, CAP_F, 1400)
    lh = 62; boxh = lh * len(lines) + 36; y0 = H - 60 - boxh
    maxw = max(d.textlength(l, font=CAP_F) for l in lines)
    ov = Image.new('RGBA', fr.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle([W / 2 - maxw / 2 - 36, y0, W / 2 + maxw / 2 + 36, y0 + boxh], 24, fill=(5, 14, 30, 200))
    fr.alpha_composite(ov)
    for k, l in enumerate(lines): d.text((W / 2, y0 + 18 + lh * k + lh / 2), l, font=CAP_F, fill=CREAM, anchor='mm')

def fade(fr, a):
    if a < 1: fr.alpha_composite(Image.new('RGBA', fr.size, (0, 0, 0, int(255 * (1 - a)))))
