"""Default Lightbulb Lab set: a cozy navy room with a desk in the centre.
make_room() -> (back, desk_front): draw characters between the two layers so they stand *behind* the desk.
DESK_TOP = y of the desk surface (where Bub sits); FLOOR = y of the floor line.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import room_art as RA

W, H = 1920, 1080
NAVY = (11, 29, 59); NAVY2 = (22, 46, 86); AMBER = (247, 168, 37); AMBER_L = (255, 205, 110)
CREAM = (255, 240, 214); SAGE = (107, 143, 107); SLATE = (75, 85, 99)
WOOD = (52, 72, 110); WOOD_D = (36, 54, 88); WOOD_L = (70, 94, 136)
FLOOR = 900
DESK_TOP = 745
DESK_X0, DESK_X1 = 560, 1360

def radial(r, color, alpha, power=2):
    g = np.linspace(-1, 1, 2 * r)
    d = np.sqrt(g[None, :] ** 2 + g[:, None] ** 2)
    a = (np.clip(1 - d, 0, 1) ** power * alpha).astype(np.uint8)
    arr = np.zeros((2 * r, 2 * r, 4), np.uint8); arr[..., :3] = color; arr[..., 3] = a
    return Image.fromarray(arr, 'RGBA')

def _layer(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))

def grad_rrect(img, box, r, top, bot, alpha=255):
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0
    t = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top) * (1 - t) + np.array(bot) * t).repeat(w, 1).astype(np.uint8)
    g = Image.fromarray(arr, 'RGB').convert('RGBA'); g.putalpha(alpha)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    if alpha < 255: m = Image.fromarray((np.array(m).astype(np.float32) * alpha / 255).astype(np.uint8))
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); lay.paste(g, (x0, y0), m); img.alpha_composite(lay)

LIGHTS = [(x, 70 + 46 * math.sin(math.pi * (x - 60) / 900) ** 2) for x in range(80, 1860, 70)]

def _wall(d):
    """wallpaper dots + baseboard, drawn before any furniture"""
    for yy in range(40, FLOOR - 40, 64):
        for xx in range(32 + (yy // 64 % 2) * 32, W, 64): d.ellipse([xx - 2, yy - 2, xx + 2, yy + 2], fill=(255, 255, 255, 10))
    d.rectangle([0, FLOOR - 20, W, FLOOR], fill=(30, 50, 86, 255))

def _details(L, d):
    """extra set dressing on the back wall/floor"""
    # floor planks + baseboard
    for k, yy in enumerate(range(FLOOR + 30, H, 46)):
        d.line([(0, yy), (W, yy)], fill=(255, 255, 255, 7), width=2)
        for x in range((k % 2) * 160, W, 320): d.line([(x, yy - 46), (x, yy)], fill=(255, 255, 255, 6), width=2)
    # window: city skyline + curtains
    wx0, wy0, wx1, wy1 = 700, 120, 1000, 380
    for bx, bw, bh in [(712, 40, 70), (754, 30, 110), (786, 46, 60), (834, 34, 130), (870, 44, 80), (916, 30, 100), (948, 42, 66)]:
        d.rectangle([bx, wy1 - 10 - bh, bx + bw, wy1 - 10], fill=(14, 28, 54, 255))
        for wy in range(wy1 - bh, wy1 - 18, 18):
            for wxx in range(bx + 6, bx + bw - 6, 12):
                if (wxx * 7 + wy * 3) % 5 == 0: d.rectangle([wxx, wy, wxx + 5, wy + 7], fill=(*AMBER_L, 200))
    d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(60, 84, 124, 255), width=8)
    d.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=(60, 84, 124, 255), width=8)
    d.rounded_rectangle([660, 96, 1040, 110], 6, fill=WOOD_L)  # curtain rod
    for x0, x1, s in [(650, 730, 1), (970, 1050, -1)]:
        d.polygon([(x0, 104), (x1, 104), (x1 - 18 * s, 400), (x0 + 10 * s, 410)], fill=(64, 92, 120, 255))
        for k in range(3): d.line([(x0 + 18 + k * 22, 110), (x0 + 14 + k * 22, 400)], fill=(48, 74, 104, 255), width=4)
    # string lights wire across the top
    d.line(LIGHTS, fill=(30, 44, 70, 255), width=3)
    for i, (x, y) in enumerate(LIGHTS):
        d.ellipse([x - 7, y + 2, x + 7, y + 18], fill=AMBER_L if i % 2 else (255, 230, 170))
    # framed circuit print (left of window)
    d.rounded_rectangle([520, 160, 650, 320], 10, fill=(18, 36, 68, 255), outline=WOOD_L, width=8)
    for y0 in (190, 230, 270):
        d.line([(540, y0), (590, y0), (600, y0 + 14), (630, y0 + 14)], fill=(*AMBER, 200), width=4)
        d.ellipse([588, y0 - 5, 598, y0 + 5], fill=AMBER)
    # wall clock + corkboard with notes (right of window)
    d.ellipse([1180, 110, 1270, 200], fill=CREAM, outline=WOOD_L, width=8)
    d.line([(1225, 155), (1225, 125)], fill=NAVY, width=6); d.line([(1225, 155), (1248, 165)], fill=NAVY, width=5)
    d.ellipse([1219, 149, 1231, 161], fill=AMBER)
    d.rounded_rectangle([1090, 240, 1370, 420], 12, fill=(150, 112, 74, 255), outline=WOOD_L, width=10)
    for nx, ny, c, a in [(1115, 262, AMBER, -6), (1195, 270, CREAM, 4), (1275, 258, SAGE, -3), (1135, 340, CREAM, 5), (1230, 345, AMBER_L, -5), (1300, 330, CREAM, 2)]:
        note = Image.new('RGBA', (64, 60), (0, 0, 0, 0)); nd = ImageDraw.Draw(note)
        nd.rectangle([0, 0, 63, 59], fill=c)
        for ly in (18, 30, 42): nd.line([(10, ly), (52, ly)], fill=(60, 70, 90, 140), width=3)
        note = note.rotate(a, expand=True, resample=Image.BICUBIC); L.alpha_composite(note, (nx, ny))
        d.ellipse([nx + 26, ny + 2, nx + 38, ny + 14], fill=(220, 70, 60))
    # router with blinking-style lights + small speaker on shelf 2
    d.rounded_rectangle([300, 474, 356, 500], 6, fill=(30, 46, 80, 255))
    d.line([(308, 474), (302, 438)], fill=(30, 46, 80, 255), width=4); d.line([(348, 474), (354, 438)], fill=(30, 46, 80, 255), width=4)
    for k in range(3): d.ellipse([310 + k * 14, 484, 318 + k * 14, 492], fill=(120, 230, 140) if k < 2 else AMBER)
    # floor lamp (left of desk)
    d.ellipse([400, FLOOR - 14, 480, FLOOR + 4], fill=NAVY)
    d.line([(440, FLOOR - 8), (440, 600)], fill=NAVY, width=10)
    d.polygon([(392, 600), (488, 600), (470, 536), (410, 536)], fill=(230, 196, 140, 255))
    d.line([(392, 600), (488, 600)], fill=(200, 160, 100, 255), width=4)
    # rug stripes
    for k in range(3):
        d.ellipse([620 + k * 40, FLOOR + 48 + k * 10, 1300 - k * 40, FLOOR + 106 - k * 10], outline=(*CREAM, 26), width=3)

def _detail_glows(back):
    for x, y in LIGHTS: back.alpha_composite(radial(26, (255, 200, 110), 90), (int(x - 26), int(y + 10 - 26)))
    back.alpha_composite(radial(160, (255, 200, 120), 70), (440 - 160, 600 - 160))   # floor lamp
    back.alpha_composite(radial(90, (255, 210, 140), 40), (1225 - 90, 155 - 90))      # clock catches light

def make_room():
    # wall gradient
    y = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(NAVY2) * (1 - y) + np.array(NAVY) * y).repeat(W, 1).astype(np.uint8)
    back = Image.fromarray(arr, 'RGB').convert('RGBA')
    L = _layer(); d = ImageDraw.Draw(L)
    # subtle wall panels
    for x in range(0, W, 160):
        d.line([(x, 0), (x, FLOOR)], fill=(255, 255, 255, 9), width=2)
    _wall(d)
    # floor
    d.rectangle([0, FLOOR, W, H], fill=(8, 20, 42, 255))
    d.line([(0, FLOOR), (W, FLOOR)], fill=(*AMBER, 50), width=3)
    # window (centre-left, behind desk)
    wx0, wy0, wx1, wy1 = 700, 120, 1000, 380
    d.rounded_rectangle([wx0, wy0, wx1, wy1], 20, fill=(6, 18, 40, 255), outline=(60, 84, 124, 255), width=10)
    d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(60, 84, 124, 255), width=8)
    d.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=(60, 84, 124, 255), width=8)
    for sx, sy in [(740, 160), (930, 175), (780, 320), (960, 330), (850, 140), (900, 290)]:
        d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(*CREAM, 190))
    d.ellipse([920, 150, 970, 200], fill=(*CREAM, 230)); d.ellipse([935, 145, 980, 190], fill=(6, 18, 40, 255))  # moon
    # wall shelves (left) with books
    def shelf(x0, x1, yy, books):
        d.rounded_rectangle([x0, yy, x1, yy + 16], 6, fill=WOOD_L)
        x = x0 + 18
        for w_, h_, c in books:
            d.rounded_rectangle([x, yy - h_, x + w_, yy], 5, fill=c); x += w_ + 7
    shelf(150, 470, 300, []); shelf(150, 470, 500, [])
    # framed picture (right wall)
    d.rounded_rectangle([1460, 200, 1700, 380], 14, fill=(30, 52, 92), outline=WOOD_L, width=10)
    d.ellipse([1540, 230, 1620, 310], fill=(*AMBER, 230)); d.rounded_rectangle([1560, 305, 1600, 345], 6, fill=NAVY)
    for k in range(5):
        a = math.radians(-90 + (k - 2) * 35); d.line([(1580 + math.cos(a) * 52, 270 + math.sin(a) * 52), (1580 + math.cos(a) * 70, 270 + math.sin(a) * 70)], fill=AMBER, width=6)
    # tall floor plant (left)

    # bookcase-ish cabinet (right floor)

    # rug under the desk
    d.ellipse([560, FLOOR + 24, 1360, FLOOR + 130], fill=(22, 42, 78, 255))
    d.ellipse([584, FLOOR + 36, 1336, FLOOR + 118], outline=(*AMBER, 90), width=3)
    # cabinet top: book stack + plant

    _details(L, d)
    back.alpha_composite(RA.wall_shadows(L, (8, 10), 9, 0.45))
    back.alpha_composite(L)
    P = _layer()
    # cabinet (shaded) with book stack and plant on top
    grad_rrect(P, (1520, 640, 1800, FLOOR), 12, (52, 74, 112), (26, 40, 70))
    for y0, y1 in ((660, 760), (780, 880)):
        grad_rrect(P, (1540, y0, 1780, y1), 8, (68, 92, 134), (44, 64, 102))
        pd = ImageDraw.Draw(P); pd.line([(1546, y0 + 3), (1774, y0 + 3)], fill=(120, 146, 190, 160), width=2)
        grad_rrect(P, (1638, (y0 + y1) // 2 - 7, 1682, (y0 + y1) // 2 + 7), 6, AMBER_L, AMBER)
    pd = ImageDraw.Draw(P); pd.line([(1528, 643), (1792, 643)], fill=(110, 136, 180, 200), width=3)
    for k, (c, w_, dx) in enumerate([(SLATE, 150, 0), (AMBER, 136, 8), (CREAM, 144, 2)]):
        grad_rrect(P, (1556 + dx, 640 - (k + 1) * 26, 1556 + dx + w_, 640 - k * 26 - 2), 5, tuple(min(255, int(v * 1.1)) for v in c), tuple(int(v * 0.75) for v in c))
    RA.plant(P, 1752, 640, size=0.42, leaves=9, seed=11, pot=(196, 130, 40))
    # shelves: books with spines, a leaning book, small plant
    RA.books(P, 160, 300, [(36, 122, AMBER, 0), (30, 98, CREAM, 0), (42, 130, SAGE, 0), (30, 106, SLATE, 0), (38, 118, CREAM, 0), (34, 112, AMBER, -14)])
    RA.books(P, 160, 500, [(40, 112, SLATE, 0), (34, 126, AMBER, 0), (32, 92, CREAM, 0)])
    RA.plant(P, 412, 500, size=0.34, leaves=8, seed=4, pot=(60, 80, 116))
    # tall floor plant
    RA.plant(P, 230, FLOOR, size=1.0, leaves=14, seed=2, pot=(48, 64, 98), spread=0.75)
    back.alpha_composite(RA.wall_shadows(P, (10, 12), 10, 0.5))
    back.alpha_composite(P)
    _detail_glows(back)
    back.alpha_composite(RA.grain((W, H), 7))
    # warm lamp light pooled around the desk
    back.alpha_composite(radial(760, (255, 170, 60), 55, 2.4), (960 - 760, 470 - 760))
    back.alpha_composite(radial(420, (255, 170, 60), 45), (690 - 420, DESK_TOP - 180 - 420))

    # ---- desk (foreground layer, drawn over characters standing behind it) ----
    F = _layer(); d = ImageDraw.Draw(F)
    sh = radial(420, (0, 0, 0), 120); sh = sh.resize((1000, 120))
    F.alpha_composite(sh, (460, FLOOR - 60))  # floor shadow
    grad_rrect(F, (DESK_X0 + 30, DESK_TOP + 30, DESK_X1 - 30, FLOOR + 22), 10, (66, 90, 132), (30, 46, 78))  # front panel
    grad_rrect(F, (DESK_X0, DESK_TOP, DESK_X1, DESK_TOP + 36), 12, (96, 122, 166), (56, 80, 122))  # top
    d = ImageDraw.Draw(F)
    d.rounded_rectangle([DESK_X0 + 60, DESK_TOP + 60, 900, DESK_TOP + 120], 8, fill=WOOD_D)  # drawer
    d.rounded_rectangle([1020, DESK_TOP + 60, DESK_X1 - 60, DESK_TOP + 120], 8, fill=WOOD_D)
    for cx in (730, 1190): d.rounded_rectangle([cx - 24, DESK_TOP + 84, cx + 24, DESK_TOP + 96], 6, fill=AMBER)
    d.line([(DESK_X0 + 14, DESK_TOP + 4), (DESK_X1 - 14, DESK_TOP + 4)], fill=(110, 136, 180, 255), width=3)  # highlight edge
    # props on the desk (left side): laptop, lamp, mug, books; right side stays clear for Bub
    # desk lamp (left): base, two-part arm, shade
    d.ellipse([575, DESK_TOP - 16, 655, DESK_TOP + 4], fill=NAVY)
    d.line([(615, DESK_TOP - 8), (585, DESK_TOP - 170)], fill=NAVY, width=12)
    d.line([(585, DESK_TOP - 170), (660, DESK_TOP - 235)], fill=NAVY, width=12)
    d.ellipse([575, DESK_TOP - 180, 597, DESK_TOP - 158], fill=AMBER)
    d.polygon([(640, DESK_TOP - 262), (720, DESK_TOP - 232), (700, DESK_TOP - 180), (628, DESK_TOP - 214)], fill=NAVY)
    d.ellipse([672, DESK_TOP - 214, 712, DESK_TOP - 190], fill=AMBER_L)
    cone = _layer(); cd = ImageDraw.Draw(cone)
    cd.polygon([(650, DESK_TOP - 214), (720, DESK_TOP - 190), (900, DESK_TOP), (560, DESK_TOP)], fill=(255, 200, 110, 34))
    F.alpha_composite(cone.filter(ImageFilter.GaussianBlur(14)))
    F.alpha_composite(radial(170, (140, 180, 255), 70), (710 - 170, DESK_TOP - 80 - 170))
    d = ImageDraw.Draw(F)
    # laptop (seen from the front-left)
    d.polygon([(600, DESK_TOP), (820, DESK_TOP), (800, DESK_TOP - 150), (620, DESK_TOP - 150)], fill=(40, 62, 104))
    d.polygon([(612, DESK_TOP - 6), (808, DESK_TOP - 6), (792, DESK_TOP - 140), (628, DESK_TOP - 140)], fill=(28, 46, 82))
    d.polygon([(705, DESK_TOP - 92), (715, DESK_TOP - 102), (725, DESK_TOP - 92), (715, DESK_TOP - 78)], fill=AMBER)  # heart-ish
    d.rounded_rectangle([580, DESK_TOP - 10, 840, DESK_TOP + 2], 5, fill=(60, 84, 124))
    # mug
    d.rounded_rectangle([1010, DESK_TOP - 60, 1055, DESK_TOP], 10, fill=CREAM)
    d.arc([1040, DESK_TOP - 50, 1075, DESK_TOP - 18], -90, 90, fill=CREAM, width=8)
    for k in range(2):
        d.arc([1018 + k * 16, DESK_TOP - 100, 1038 + k * 16, DESK_TOP - 66], 180, 360, fill=(*CREAM, 90), width=4)
    # sticky notes on the laptop lid
    d.polygon([(640, DESK_TOP - 128), (672, DESK_TOP - 130), (674, DESK_TOP - 100), (642, DESK_TOP - 98)], fill=AMBER)
    d.polygon([(756, DESK_TOP - 124), (786, DESK_TOP - 120), (783, DESK_TOP - 92), (753, DESK_TOP - 95)], fill=CREAM)
    # pencil cup
    for px, c, hgt in [(1080, AMBER, 46), (1092, SAGE, 56), (1104, CREAM, 40)]:
        d.line([(px, DESK_TOP - 36), (px + (px - 1092) * 0.3, DESK_TOP - 36 - hgt)], fill=c, width=7)
    d.rounded_rectangle([1070, DESK_TOP - 44, 1114, DESK_TOP], 8, fill=SLATE)
    # notebook lying flat near the front edge
    d.rounded_rectangle([880, DESK_TOP - 12, 990, DESK_TOP], 3, fill=SAGE)
    d.line([(884, DESK_TOP - 6), (986, DESK_TOP - 6)], fill=CREAM, width=2)
    return back, F

if __name__ == '__main__':
    b, f = make_room(); b.alpha_composite(f); b.convert('RGB').resize((960, 540)).save('/home/claude/intro/chk/room.png')
