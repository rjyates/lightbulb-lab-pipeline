"""YouTube thumbnail (1280x720): Kip & Bub from the brand sheet + tilted label text."""
import math, os
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from .core import ASSETS, F_BOLD

SHEET = os.path.join(ASSETS, 'brand', 'brand-sheet.png')
W, H = 1280, 720
AMBER, NAVY, CREAM = (247, 168, 37), (11, 29, 59), (255, 247, 230)
F = lambda s: ImageFont.truetype(F_BOLD, s)
_CHARS = None

def _radial(r, c, a):
    g = np.linspace(-1, 1, 2 * r); d = np.sqrt(g[None, :] ** 2 + g[:, None] ** 2)
    arr = np.zeros((2 * r, 2 * r, 4), np.uint8); arr[..., :3] = c; arr[..., 3] = (np.clip(1 - d, 0, 1) ** 2 * a).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

def _chars():
    """Kip & Bub cut out of the brand sheet's main logo panel (navy background removed)"""
    global _CHARS
    if _CHARS is None:
        pan = Image.open(SHEET).convert('RGB').crop((50, 22, 430, 338)); a = np.array(pan).astype(int); h, w, _ = a.shape
        ref = np.array([14, 32, 60]); seen = np.zeros((h, w), bool); q = deque([(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)])
        while q:
            y, x = q.popleft()
            if seen[y, x] or np.abs(a[y, x] - ref).sum() > 70: continue
            seen[y, x] = True
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx]: q.append((ny, nx))
        al = Image.fromarray(np.where(seen, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
        ch = pan.convert('RGBA'); ch.putalpha(al); ch = ch.crop(ch.getbbox())
        ch = ch.resize((int(ch.width * 640 / ch.height), 640), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 70, 2))
        arr = np.array(ch); arr[90:340, 722:, 3] = 0; _CHARS = Image.fromarray(arr, 'RGBA')  # trim a sliver of the wordmark
    return _CHARS

def make(line1, line2, sub1, sub2, out_path):
    src = Image.open(SHEET).convert('RGB')
    strip = src.crop((770, 824, 978, 996)); strip = strip.resize((int(strip.width * H / strip.height), H), Image.LANCZOS)
    bg = Image.new('RGB', (W, H)); x = W
    while x > 0:
        bg.paste(strip, (x - strip.width, 0)); x -= strip.width; strip = strip.transpose(Image.FLIP_LEFT_RIGHT)
    bg = Image.blend(bg.filter(ImageFilter.GaussianBlur(24)), Image.new('RGB', (W, H), (8, 20, 42)), 0.45).convert('RGBA')
    bg.alpha_composite(_radial(420, (255, 180, 70), 110), (330 - 420, 0))
    ch = _chars(); bg.alpha_composite(ch, (-40, H - ch.height + 40))
    d = ImageDraw.Draw(bg)
    for cx, cy, r in [(600, 150, 26), (90, 120, 18), (1220, 560, 16)]:
        d.polygon([(cx + math.cos(math.pi / 4 * k) * (r if k % 2 == 0 else r * 0.28), cy + math.sin(math.pi / 4 * k) * (r if k % 2 == 0 else r * 0.28)) for k in range(8)], fill=AMBER)
    lab = Image.new('RGBA', (640, 520), (0, 0, 0, 0)); ld = ImageDraw.Draw(lab)
    def label(y, text, size, bgc):
        while size > 40 and ld.textlength(text, font=F(size)) + 52 > 590: size -= 2
        w = ld.textlength(text, font=F(size)); ld.rounded_rectangle([20, y, 20 + w + 52, y + size * 1.18], 18, fill=bgc)
        ld.text((46, y + size * 0.58), text, font=F(size), fill=NAVY, anchor='lm')
    label(20, line1, 96, CREAM); label(150, line2, 112, AMBER)
    for y, txt, size, col in ((330, sub1, 54, CREAM), (395, sub2, 64, AMBER)):
        while size > 30 and ld.textlength(txt, font=F(size)) > 590: size -= 2
        ld.text((30, y), txt, font=F(size), fill=col)
    lab = lab.rotate(4, resample=Image.BICUBIC)
    sh = Image.fromarray(np.dstack([np.zeros((520, 640, 3), np.uint8), (np.array(lab)[..., 3] * 0.55).astype(np.uint8)]), 'RGBA').filter(ImageFilter.GaussianBlur(8))
    bg.alpha_composite(sh, (650, 110)); bg.alpha_composite(lab, (640, 100))
    yy, xx = np.mgrid[0:H, 0:W]; dd = np.sqrt(((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2)
    va = (np.clip(dd - 0.6, 0, 1) ** 1.5 * 200).astype(np.uint8); bg.alpha_composite(Image.fromarray(np.dstack([np.zeros_like(va)] * 3 + [va]), 'RGBA'))
    bg.convert('RGB').save(out_path, quality=92); return out_path
