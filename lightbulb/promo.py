"""Vertical promo Short/TikTok for the Lightbulb Lab guides (music only, no voice credits).

  python3 -m lightbulb.promo output/guides-promo.mp4
Guides come from links.json; covers are drawn in brand style.
"""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
from . import core as K
from .characters import draw_kip, draw_bub

VW, VH, FPS, DUR = 1080, 1920, 30, 26.0
F = lambda s: K.font(K.F_BOLD, s)
M = lambda s: K.font(K.F_MED, s)

GUIDES = [  # (cover title lines, tag, detail, price) -- matches links.json order
    (['New Computer', 'Starter Guide'], 'DIGITAL GUIDE', 'Setup, security, files & backups\n34 pages · Windows 11 & Mac', '$5'),
    (['Family Tech', 'Binder'], 'PRINT AT HOME', 'Large-print instructions & worksheets\n34-page printable binder', '$10'),
    (['Binder +', 'Setup Kit'], 'COMPLETE KIT', 'The binder plus a helper setup guide\n34 + 16 pages', '$12'),
]

def bg():
    import numpy as np
    y = np.linspace(0, 1, VH)[:, None, None]
    im = Image.fromarray((np.array((24, 50, 92)) * (1 - y) + np.array((8, 20, 42)) * y).repeat(VW, 1).astype('uint8'), 'RGB').convert('RGBA')
    im.alpha_composite(K.radial(700, (255, 190, 90), 70).resize((1400, 1400)), (VW // 2 - 700, 700))
    return im

def cover(lines, tag, i):
    w, h = 420, 560; c = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([26, 30, w + 26, h + 30], 22, fill=(0, 0, 0, 150))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d.rounded_rectangle([12, 12, w + 12, h + 12], 22, fill=K.NAVY)
    d.rectangle([12, 12, 40, h + 12], fill=K.AMBER if i != 1 else K.SAGE)  # spine
    d.rounded_rectangle([60, 46, w - 20, 92], 23, fill=K.AMBER); d.text(((w + 52) / 2, 69), tag, font=F(24), fill=K.NAVY, anchor='mm')
    y = 130
    for ln in lines:
        s = 58
        while d.textlength(ln, font=F(s)) > w - 90: s -= 2
        d.text(((w + 52) / 2, y), ln, font=F(s), fill=K.CREAM, anchor='mt'); y += s + 8
    b = draw_bub(scale=0.42, mood='happy', rays=0.6); k = draw_kip(scale=0.42, arm_r=(132, 4), eyes='happy')
    c.alpha_composite(k, (int(w * 0.36 - k.width / 2), h + 12 - k.height - 6)); c.alpha_composite(b, (int(w * 0.78 - b.width / 2), h + 12 - b.height - 10))
    d.text(((w + 52) / 2, h - 2), 'LIGHTBULB LAB', font=F(22), fill=(*K.AMBER_L, 255), anchor='mm')
    return c

COVERS = None
def label(fr, y, lines, sizes, colors, alpha, tilt=-2):
    lay = Image.new('RGBA', (VW, 600), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); yy = 20
    for ln, s, col in zip(lines, sizes, colors):
        w = ld.textlength(ln, font=F(s)) + 64
        ld.rounded_rectangle([VW / 2 - w / 2, yy, VW / 2 + w / 2, yy + s * 1.38], 26, fill=col)
        ld.text((VW / 2, yy + s * 0.69), ln, font=F(s), fill=K.NAVY, anchor='mm'); yy += s * 1.38 + 16
    lay = lay.rotate(tilt, resample=Image.BICUBIC); lay.putalpha(lay.getchannel('A').point(lambda p: int(p * alpha))); fr.alpha_composite(lay, (0, y))

def frame(t, BG):
    global COVERS
    if COVERS is None: COVERS = [cover(g[0], g[1], i) for i, g in enumerate(GUIDES)]
    fr = BG.copy(); d = ImageDraw.Draw(fr)
    # characters, bottom
    talk = 0.5 + 0.5 * math.sin(t * 3)
    pose = (132, 4) if t < 3.5 or t > 21.5 else (100, -14)
    k = draw_kip(scale=0.74, bob=math.sin(t * 2.2) * 0.5, arm_r=pose, eyes='happy', blink=float((t % 4.1) < 0.12), look=0.0)
    b = draw_bub(scale=0.78, squash=0.25 * math.sin(t * 4.4), mood='aha' if 7 < t < 21 else 'happy', rays=0.5 + 0.5 * talk)
    fr.alpha_composite(K.GLOW.resize((440, 440)), (790 - 220, 1640 - 220))
    fr.alpha_composite(k, (330 - k.width // 2, VH - 70 - k.height)); fr.alpha_composite(b, (790 - b.width // 2, VH - 160 - b.height + int(abs(math.sin(t * 2.2)) * -24)))
    # beats
    a1 = K.ramp(t, 0.1, 0.5) * (1 - K.ramp(t, 3.2, 3.6))
    if a1 > 0: label(fr, 260, ['Just got a', 'new computer?'], [96, 110], [K.CREAM, K.AMBER], a1)
    a2 = K.ramp(t, 3.6, 4.0) * (1 - K.ramp(t, 6.6, 7.0))
    if a2 > 0: label(fr, 260, ['Or helping', 'Mom & Dad', 'with theirs?'], [90, 104, 90], [K.CREAM, K.AMBER, K.CREAM], a2, tilt=2)
    for i, (lines, tag, detail, price) in enumerate(GUIDES):
        t0 = 7.0 + i * 4.6; a = K.ramp(t, t0, t0 + 0.45) * (1 - K.ramp(t, t0 + 4.2, t0 + 4.6))
        if a <= 0: continue
        s = K.back((t - t0) / 0.5)
        cv = COVERS[i].resize((max(1, int(COVERS[i].width * s)), max(1, int(COVERS[i].height * s))), Image.LANCZOS)
        cv.putalpha(cv.getchannel('A').point(lambda p: int(p * a))); fr.alpha_composite(cv, (VW // 2 - cv.width // 2, 250 + int(300 * (1 - s))))
        lay = Image.new('RGBA', (VW, 330), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.text((VW / 2, 20), ' '.join(lines).replace('+ ', '+ '), font=F(62), fill=K.CREAM, anchor='mt')
        for j, ln in enumerate(detail.split('\n')): ld.text((VW / 2, 110 + j * 52), ln, font=M(42), fill=(205, 215, 235), anchor='mt')
        pw = ld.textlength(price, font=F(64)) + 70; ld.rounded_rectangle([VW / 2 - pw / 2, 230, VW / 2 + pw / 2, 318], 44, fill=K.AMBER); ld.text((VW / 2, 274), price, font=F(64), fill=K.NAVY, anchor='mm')
        lay.putalpha(lay.getchannel('A').point(lambda p: int(p * a))); fr.alpha_composite(lay, (0, 850))
        d = ImageDraw.Draw(fr); d.text((VW / 2, 190), f'{i + 1} of 3', font=F(44), fill=(*K.AMBER_L, int(255 * a)), anchor='mm')
    a4 = K.ramp(t, 20.9, 21.3)
    if a4 > 0:
        label(fr, 230, ['Large print.', 'Step by step.', 'Windows 11 & Mac.'], [80, 80, 80], [K.CREAM, K.AMBER, K.CREAM], a4 * (1 - K.ramp(t, 23.4, 23.7)))
        a5 = K.ramp(t, 23.6, 24.0)
        if a5 > 0:
            d = ImageDraw.Draw(fr)
            d.text((VW / 2, 330), 'Get the guides', font=F(96), fill=(*K.CREAM, int(255 * a5)), anchor='mm')
            u = 'lightbulb-lab.pages.dev'; w = d.textlength(u, font=F(64)) + 80
            d.rounded_rectangle([VW / 2 - w / 2, 420, VW / 2 + w / 2, 530], 55, fill=(*K.AMBER, int(255 * a5))); d.text((VW / 2, 475), u, font=F(64), fill=(*K.NAVY, int(255 * a5)), anchor='mm')
            d.text((VW / 2, 600), 'Link in bio · @LightbulbLabYT', font=M(48), fill=(*K.CREAM, int(230 * a5)), anchor='mm')
    K.fade(fr, K.ramp(t, 0, 0.3) * (1 - K.ramp(t, DUR - 0.5, DUR)))
    return fr.convert('RGB')

def render(out):
    BG = bg(); tmp = out + '.silent.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{VW}x{VH}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): p.stdin.write(frame(i / FPS, BG).tobytes())
    p.stdin.close(); p.wait()
    music = os.path.join(K.ASSETS, 'music', 'nebula-the-grey-room-density-time.mp3'); pop = os.path.join(K.ASSETS, 'sfx', 'pop.wav'); chirp = os.path.join(K.ASSETS, 'sfx', 'bub-happy-chirp.wav')
    pops = [7.0, 11.6, 16.2]
    ins = ['-i', tmp, '-i', music] + sum([['-i', pop] for _ in pops], []) + ['-i', chirp]
    f = [f'[1:a]atrim=0:{DUR},asetpts=N/SR/TB,volume=0.55,afade=t=in:d=0.6,afade=t=out:st={DUR - 2}:d=2[m]']
    f += [f'[{i + 2}:a]adelay={int(t * 1000)}:all=1,volume=0.5[p{i}]' for i, t in enumerate(pops)]
    f += [f'[{len(pops) + 2}:a]adelay=23700:all=1,volume=0.5[c]']
    f += ['[m]' + ''.join(f'[p{i}]' for i in range(len(pops))) + f'[c]amix=inputs={len(pops) + 2}:normalize=0,alimiter=limit=0.95[a]']
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *ins, '-filter_complex', ';'.join(f), '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', str(DUR), '-movflags', '+faststart', out], check=True)
    os.remove(tmp); return out

if __name__ == '__main__':
    render(sys.argv[1] if len(sys.argv) > 1 else os.path.join(K.ROOT, 'output', 'guides-promo.mp4'))
