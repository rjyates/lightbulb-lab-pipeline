"""Painterly set-dressing helpers for the Lightbulb Lab room (drawn supersampled, then composited)."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 3
LEAF_L = (124, 168, 116); LEAF_M = (86, 128, 88); LEAF_D = (52, 88, 66); LEAF_X = (34, 62, 52)

def _canvas(w, h): return Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
def _down(im): return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)

def _leaf(d, ox, oy, x, y, length, width, ang, light, dark, rib=True):
    """almond leaf from base (x,y) toward angle; left half light, right half dark, pale midrib"""
    ca, sa = math.cos(ang), math.sin(ang); nx, ny = -sa, ca
    pts_l, pts_r = [], []
    for i in range(17):
        t = i / 16; hw = width * (math.sin(math.pi * t) ** 0.75) * (1 - 0.25 * t)
        cx, cy = x + ca * length * t, y + sa * length * t
        bend = math.sin(math.pi * t) * width * 0.25
        pts_l.append((cx + nx * (hw + bend), cy + ny * (hw + bend)))
        pts_r.append((cx - nx * (hw - bend), cy - ny * (hw - bend)))
    mid = [(x + ca * length * (i / 16) + nx * math.sin(math.pi * i / 16) * width * 0.25,
            y + sa * length * (i / 16) + ny * math.sin(math.pi * i / 16) * width * 0.25) for i in range(17)]
    P = lambda pts: [((px - ox) * SS, (py - oy) * SS) for px, py in pts]
    d.polygon(P(pts_l + mid[::-1]), fill=light)
    d.polygon(P(mid + pts_r[::-1]), fill=dark)
    if rib: d.line(P(mid[:15]), fill=(196, 222, 176, 150), width=int(1.6 * SS))

def plant(img, bx, by, size=1.0, leaves=11, seed=1, pot=(54, 70, 104), spread=1.0):
    """leafy potted plant; (bx, by) = bottom-centre of the pot"""
    rnd = random.Random(seed)
    W, H = int(420 * size), int(520 * size)
    ox, oy = bx - W / 2, by - H
    c = _canvas(W, H); d = ImageDraw.Draw(c)
    P = lambda x, y: ((x - ox) * SS, (y - oy) * SS)
    pot_h, pot_w = 92 * size, 98 * size
    top = by - pot_h
    # stems + leaves (back to front, darker at the back)
    specs = []
    for i in range(leaves):
        a = math.radians(-90 + (rnd.uniform(-1, 1) * 78) * spread)
        L = rnd.uniform(150, 250) * size; specs.append((rnd.random(), a, L))
    specs.sort()
    for depth, a, L in specs:
        sx, sy = bx + rnd.uniform(-14, 14) * size, top + 6 * size
        ex, ey = sx + math.cos(a) * L * 0.55, sy + math.sin(a) * L * 0.55
        d.line([P(sx, sy), P((sx + ex) / 2 + rnd.uniform(-8, 8), (sy + ey) / 2), P(ex, ey)], fill=LEAF_X, width=int(4 * size * SS), joint='curve')
        k = depth
        light = tuple(int(a_ * (0.62 + 0.38 * k)) for a_ in LEAF_L); dark = tuple(int(a_ * (0.62 + 0.38 * k)) for a_ in LEAF_D)
        la = a + rnd.uniform(-0.35, 0.35)
        _leaf(d, ox, oy, ex, ey, rnd.uniform(90, 140) * size, rnd.uniform(26, 38) * size, la, light, dark)
    # pot: tapered, shaded, with rim highlight and soil
    pts = [P(bx - pot_w / 2, top), P(bx + pot_w / 2, top), P(bx + pot_w * 0.40, by), P(bx - pot_w * 0.40, by)]
    d.polygon(pts, fill=pot)
    d.polygon([P(bx + pot_w * 0.08, top), P(bx + pot_w / 2, top), P(bx + pot_w * 0.40, by), P(bx + pot_w * 0.04, by)],
              fill=tuple(int(v * 0.7) for v in pot))
    d.rounded_rectangle([P(bx - pot_w * 0.56, top - 14 * size), P(bx + pot_w * 0.56, top + 6 * size)], int(5 * size * SS),
                        fill=tuple(min(255, int(v * 1.25)) for v in pot))
    d.ellipse([P(bx - pot_w * 0.46, top - 10 * size), P(bx + pot_w * 0.46, top + 2 * size)], fill=(36, 28, 26))
    img.alpha_composite(_down(c), (int(ox), int(oy)))

def books(img, x0, shelf_y, specs, seed=3):
    """books standing on a shelf: specs = [(width, height, colour, lean_deg), ...]"""
    W = int(sum(s[0] + 8 for s in specs) + 80); H = 200
    ox, oy = x0 - 20, shelf_y - H
    c = _canvas(W, H); x = 20
    for w, h, col, lean in specs:
        b = Image.new('RGBA', (int(w * SS), int(h * SS)), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
        # left-to-right shading across the spine
        arr = np.zeros((b.height, b.width, 4), np.uint8)
        t = np.linspace(0, 1, b.width)[None, :]
        shade = 1.08 - 0.32 * t
        for ch in range(3): arr[..., ch] = np.clip(col[ch] * shade, 0, 255).astype(np.uint8)
        arr[..., 3] = 255
        g = Image.fromarray(arr, 'RGBA'); m = Image.new('L', b.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, b.width - 1, b.height - 1], int(3 * SS), fill=255)
        b.paste(g, (0, 0), m)
        band = tuple(int(v * 0.72) for v in col); hi = tuple(min(255, int(v * 1.2)) for v in col)
        for yy in (0.12, 0.84):
            bd.rectangle([0, b.height * yy, b.width, b.height * yy + 4 * SS], fill=band)
        bd.rectangle([b.width * 0.25, b.height * 0.40, b.width * 0.75, b.height * 0.48], fill=hi)
        if lean: b = b.rotate(lean, expand=True, resample=Image.BICUBIC)
        c.alpha_composite(b, (int(x * SS), int(c.height - b.height)))
        x += w + (4 if not lean else 14)
    img.alpha_composite(_down(c), (int(ox), int(oy)))

def wall_shadows(layer, offset=(10, 12), blur=10, alpha=0.55):
    """soft drop shadow for everything on a layer (gives wall objects depth)"""
    a = np.array(layer.getchannel('A')).astype(np.float32) * alpha
    sh = Image.fromarray(np.dstack([np.zeros(a.shape + (3,), np.uint8), a.astype(np.uint8)]), 'RGBA').filter(ImageFilter.GaussianBlur(blur))
    out = Image.new('RGBA', layer.size, (0, 0, 0, 0)); out.alpha_composite(sh, offset); return out

def grain(size, strength=9, seed=5):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (size[1], size[0]))
    a = (np.abs(n) * strength).clip(0, 40).astype(np.uint8)
    col = np.where(n[..., None] > 0, 255, 0).astype(np.uint8).repeat(3, 2)
    return Image.fromarray(np.dstack([col, a]), 'RGBA')
