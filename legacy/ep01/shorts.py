"""Vertical 1080x1920 clips for YouTube Shorts / TikTok, built from the Episode 1 scene components.
python3 shorts.py preview   -> sample frames
python3 shorts.py N         -> render clip N (1..3)
"""
import math, subprocess, sys
from PIL import Image, ImageDraw
import ep1 as E
R, V = E.R, E.V

VW, VH, FPS = 1080, 1920, 30
END = 2.2  # seconds of end screen
CLIPS = {
    1: dict(t0=E.v(0.0), t1=E.v(12.7), hook='You own more computers than you think', name='short1-more-computers'),
    2: dict(t0=E.v(28.4), t1=E.v(92.4), hook='A computer is just a kitchen', name='short2-computer-kitchen'),
    3: dict(t0=E.v(56.4), t1=E.v(84.0), hook='Why does your computer forget when it turns off?', name='short3-ram-vs-storage'),
}
F = lambda s: R.font(R.F_BOLD, s)

import numpy as np
_y = np.linspace(0, 1, VH)[:, None, None]
BG = Image.fromarray((np.array((22, 46, 86)) * (1 - _y) + np.array((8, 20, 42)) * _y).repeat(VW, 1).astype(np.uint8), 'RGB').convert('RGBA')

def wrap(d, text, f, maxw):
    out, cur = [], ''
    for w in text.split():
        tst = (cur + ' ' + w).strip()
        if d.textlength(tst, font=f) <= maxw: cur = tst
        else: out.append(cur); cur = w
    out.append(cur); return out

def scene(t):
    """room + Kip + Bub (no card, no captions), horizontal"""
    fr = E.BACK.copy(); E.motes(fr, t); E.kip_layer(fr, t); fr.alpha_composite(E.DESK); fr.alpha_composite(E.VIG); E.bub_layer(fr, t)
    return fr

def current_card(t):
    for t0, t1, fn in E.SEG:
        if t0 <= t < t1:
            sc = R.back((t - t0) / 0.4) * (1 - R.ease((t - (t1 - 0.3)) / 0.3))
            return fn(t), sc
    return None, 0

def caption_text(t):
    at = t - E.OFFSET; txt = None
    for i, (s, x) in enumerate(E.SEGS):
        e = E.SEGS[i + 1][0] if i + 1 < len(E.SEGS) else E.AUD_LEN
        if s <= at < e: txt = x
    return txt

def vframe(t, clip):
    c = CLIPS[clip]; fr = BG.copy(); d = ImageDraw.Draw(fr)
    if t > c['t1']:  # end screen
        u = t - c['t1']; a = R.ease(u / 0.4)
        sc = scene(c['t1']).crop((420, 230, 1440, 990)).resize((1080, 805), Image.LANCZOS)
        fr.alpha_composite(sc, (0, 640))
        ov = Image.new('RGBA', (VW, VH), (6, 16, 34, int(200 * a))); fr.alpha_composite(ov); d = ImageDraw.Draw(fr)
        d.text((VW / 2, 720), 'Full episode on YouTube', font=F(64), fill=(*R.CREAM, int(255 * a)), anchor='mm')
        lab = '@LightbulbLabYT'; w = d.textlength(lab, font=F(72)) + 80
        d.rounded_rectangle([VW / 2 - w / 2, 800, VW / 2 + w / 2, 920], 60, fill=(*R.AMBER, int(255 * a)))
        d.text((VW / 2, 860), lab, font=F(72), fill=(*R.NAVY, int(255 * a)), anchor='mm')
        d.text((VW / 2, 1010), 'Tech from Scratch · Ep. 1', font=R.font(R.F_MED, 44), fill=(*R.CREAM, int(220 * a)), anchor='mm')
        return fr.convert('RGB')
    # characters (lower middle)
    sc = scene(t).crop((420, 230, 1440, 990)).resize((1080, 805), Image.LANCZOS)
    fr.alpha_composite(sc, (0, 860))
    # card (top)
    card, s = current_card(t)
    s *= R.ease((t - c['t0'] - 2.5) / 0.4) if t < c['t0'] + 2.9 and c['t0'] > 1 else 1.0
    if card is not None and s > 0.02:
        w, h = int(1000 * s), int(1000 * V.CH / V.CW * s)
        im = card.im.resize((max(1, w), max(1, h)), Image.LANCZOS)
        fr.alpha_composite(im, (int(VW / 2 - w / 2), int(560 - h / 2)))
    # hook label (first 2.5 s)
    ha = R.ease((t - c['t0']) / 0.3) * (1 - R.ease((t - c['t0'] - 2.5) / 0.3))
    if ha > 0.02:
        lay = Image.new('RGBA', (VW, 420), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        lines = wrap(ld, c['hook'], F(76), 900); y = 40
        for i, ln in enumerate(lines):
            w = ld.textlength(ln, font=F(76)) + 60; bgc = R.CREAM if i % 2 == 0 else R.AMBER
            ld.rounded_rectangle([VW / 2 - w / 2, y, VW / 2 + w / 2, y + 110], 26, fill=bgc); ld.text((VW / 2, y + 55), ln, font=F(76), fill=R.NAVY, anchor='mm'); y += 125
        lay = lay.rotate(-2, resample=Image.BICUBIC)
        lay.putalpha(lay.getchannel('A').point(lambda p: int(p * ha))); fr.alpha_composite(lay, (0, 120))
    # big captions (bottom)
    txt = caption_text(t)
    if txt:
        lines = wrap(d, txt, F(60), 960)[:3]; y0 = 1700 - (len(lines) - 1) * 40
        for i, ln in enumerate(lines):
            y = y0 + i * 80
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (3, 3)): d.text((VW / 2 + dx, y + dy), ln, font=F(60), fill=(4, 10, 24), anchor='mm')
            d.text((VW / 2, y), ln, font=F(60), fill=R.CREAM if i % 2 == 0 else V.AMBER_L, anchor='mm')
    return fr.convert('RGB')

def render(clip):
    c = CLIPS[clip]; t0, t1 = c['t0'], c['t1'] + END; out = f"/home/claude/ep1/{c['name']}.mp4"
    au = '/home/claude/ep1/final_mix.wav'
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{VW}x{VH}', '-r', str(FPS), '-i', '-',
                          '-ss', f'{t0:.3f}', '-t', f'{t1 - t0:.3f}', '-i', au,
                          '-filter_complex', f'[1:a]volume=enable=\'gte(t,{c["t1"]-t0:.2f})\':volume=0.55,afade=t=in:d=0.3,afade=t=out:st={t1-t0-0.8:.2f}:d=0.8[a]',
                          '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                          '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int((t1 - t0) * FPS)):
        p.stdin.write(vframe(t0 + i / FPS, clip).tobytes())
    p.stdin.close(); p.wait(); print('done', out)

if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        ims = [vframe(E.v(1.5), 1), vframe(E.v(9.5), 1), vframe(E.v(40.5), 2), vframe(E.v(71.5), 3), vframe(E.v(84.0) + 1.2, 3)]
        s = Image.new('RGB', (540 * 5, 960)); [s.paste(im.resize((540, 960)), (i * 540, 0)) for i, im in enumerate(ims)]
        s.resize((1350, 480)).save('/home/claude/ep1/shorts_prev.png')
    else:
        render(int(sys.argv[1]))
