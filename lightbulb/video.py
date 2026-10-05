"""Audio mixing, parallel rendering of the main video, and the vertical Shorts/TikTok clips."""
import math, os, subprocess, multiprocessing as mp
from PIL import Image, ImageDraw
from . import core as K
from . import cards as C
from .engine import OFFSET

MUSIC = os.path.join(K.ASSETS, 'music', 'nebula-the-grey-room-density-time.mp3')
_EP = None  # set before forking workers

def mix_audio(ep, voice_mp3, out_wav):
    """voice + Bub/pop cues + ducked music -> out_wav"""
    cues = ep.cues(); D = ep.dur
    ins = ['-i', voice_mp3]; f = [f'[0:a]adelay={int(OFFSET * 1000)}:all=1[k]']
    for i, (t, path, vol) in enumerate(cues, 1):
        ins += ['-i', path]; f.append(f'[{i}:a]adelay={int(max(0, t) * 1000)}:all=1,volume={vol}[s{i}]')
    n = len(cues) + 1; m = n
    f.append('[k]' + ''.join(f'[s{i}]' for i in range(1, n)) + f'amix=inputs={n}:normalize=0,apad=whole_dur={D:.2f},asplit=2[v][sc]')
    ins += ['-stream_loop', '-1', '-i', MUSIC]
    f.append(f'[{m}:a]atrim=0:{D:.2f},asetpts=N/SR/TB,volume=0.28,afade=t=in:d=1.0,afade=t=out:st={D - 3.5:.2f}:d=3.5[mu]')
    f.append('[mu][sc]sidechaincompress=threshold=0.025:ratio=5:attack=30:release=500:makeup=1[md]')
    f.append('[v][md]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *ins, '-filter_complex', ';'.join(f), '-map', '[a]', '-t', f'{D:.2f}', '-ar', '48000', out_wav], check=True)

def _pipe(path, w, h):
    return subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(K.FPS), '-i', '-',
                             '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)

def _render_part(args):
    kind, t0, t1, path, extra = args
    w, h = (K.W, K.H) if kind == 'main' else (1080, 1920)
    p = _pipe(path, w, h)
    for i in range(int(round(t0 * K.FPS)), int(round(t1 * K.FPS))):
        t = i / K.FPS
        im = _EP.frame(t) if kind == 'main' else vframe(_EP, t, extra)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait(); return path

def _parallel(kind, t0, t1, out_mp4, workdir, workers, extra=None):
    global _EP
    n = max(1, workers); step = (t1 - t0) / n
    jobs = [(kind, t0 + i * step, t0 + (i + 1) * step if i < n - 1 else t1, os.path.join(workdir, f'{kind}_part{i}.mp4'), extra) for i in range(n)]
    ctx = mp.get_context('fork')
    with ctx.Pool(n) as pool: parts = pool.map(_render_part, jobs)
    lst = os.path.join(workdir, f'{kind}_parts.txt')
    open(lst, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out_mp4], check=True)
    for p in parts: os.remove(p)
    os.remove(lst)

def render_main(ep, mix_wav, out_mp4, workdir, workers):
    global _EP; _EP = ep
    silent = os.path.join(workdir, 'video_only.mp4')
    _parallel('main', 0.0, ep.dur, silent, workdir, workers)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', silent, '-i', mix_wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
                    '-b:a', '192k', '-shortest', '-movflags', '+faststart', out_mp4], check=True)
    os.remove(silent)

# ------------------------------------------------------------------ shorts (1080x1920)
VW, VH, END = 1080, 1920, 2.2
_BG = None
def _bg():
    global _BG
    if _BG is None:
        import numpy as np
        y = np.linspace(0, 1, VH)[:, None, None]
        _BG = Image.fromarray((np.array((22, 46, 86)) * (1 - y) + np.array((8, 20, 42)) * y).repeat(VW, 1).astype('uint8'), 'RGB').convert('RGBA')
    return _BG

def short_range(ep, sh):
    a, b = sh['scenes']; return ep.s_start[a] - 0.25, ep.s_end[b] + 0.35

def vframe(ep, t, sh):
    t0, t1 = short_range(ep, sh); fr = _bg().copy(); d = ImageDraw.Draw(fr); F = lambda s: K.font(K.F_BOLD, s)
    def chars(tt):
        s = ep.scene(tt); ep.bub(s, tt); return s.crop((420, 230, 1440, 990)).resize((1080, 805), Image.LANCZOS)
    if t > t1:
        a = K.ease((t - t1) / 0.4); fr.alpha_composite(chars(t1), (0, 640))
        fr.alpha_composite(Image.new('RGBA', (VW, VH), (6, 16, 34, int(200 * a)))); d = ImageDraw.Draw(fr)
        d.text((VW / 2, 720), 'Full episode on YouTube', font=F(64), fill=(*K.CREAM, int(255 * a)), anchor='mm')
        lab = '@LightbulbLabYT'; w = d.textlength(lab, font=F(72)) + 80
        d.rounded_rectangle([VW / 2 - w / 2, 800, VW / 2 + w / 2, 920], 60, fill=(*K.AMBER, int(255 * a)))
        d.text((VW / 2, 860), lab, font=F(72), fill=(*K.NAVY, int(255 * a)), anchor='mm')
        d.text((VW / 2, 1010), f"{ep.ep.get('series', 'Tech from Scratch')} · Ep. {ep.ep['number']}", font=K.font(K.F_MED, 44), fill=(*K.CREAM, int(220 * a)), anchor='mm')
        return fr.convert('RGB')
    fr.alpha_composite(chars(t), (0, 860))
    card, s = ep.card_now(t)
    if t < t0 + 2.9: s *= K.ease((t - t0 - 2.5) / 0.4)
    if card is not None and s > 0.02:
        w, h = int(1000 * s), int(1000 * C.CH / C.CW * s); im = card.im.resize((max(1, w), max(1, h)), Image.LANCZOS)
        fr.alpha_composite(im, (int(VW / 2 - w / 2), int(560 - h / 2)))
    ha = K.ease((t - t0) / 0.3) * (1 - K.ease((t - t0 - 2.5) / 0.3))
    if ha > 0.02:
        lay = Image.new('RGBA', (VW, 420), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); y = 40
        for i, ln in enumerate(K.wrap(ld, sh['hook'], F(76), 900)[:3]):
            w = ld.textlength(ln, font=F(76)) + 60
            ld.rounded_rectangle([VW / 2 - w / 2, y, VW / 2 + w / 2, y + 110], 26, fill=K.CREAM if i % 2 == 0 else K.AMBER)
            ld.text((VW / 2, y + 55), ln, font=F(76), fill=K.NAVY, anchor='mm'); y += 125
        lay = lay.rotate(-2, resample=Image.BICUBIC); lay.putalpha(lay.getchannel('A').point(lambda p: int(p * ha))); fr.alpha_composite(lay, (0, 120))
    txt = ep.caption_at(t)
    if txt:
        lines = K.wrap(d, txt, F(60), 960)[:3]; y0 = 1700 - (len(lines) - 1) * 40
        for i, ln in enumerate(lines):
            y = y0 + i * 80
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (3, 3)): d.text((VW / 2 + dx, y + dy), ln, font=F(60), fill=(4, 10, 24), anchor='mm')
            d.text((VW / 2, y), ln, font=F(60), fill=K.CREAM if i % 2 == 0 else K.AMBER_L, anchor='mm')
    return fr.convert('RGB')

def render_short(ep, sh, mix_wav, out_mp4, workdir, workers):
    global _EP; _EP = ep
    t0, t1 = short_range(ep, sh); t1e = t1 + END
    silent = os.path.join(workdir, 'short_only.mp4')
    _parallel('short', t0, t1e, silent, workdir, workers, sh)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', silent, '-ss', f'{t0:.3f}', '-t', f'{t1e - t0:.3f}', '-i', mix_wav,
                    '-filter_complex', f"[1:a]volume=enable='gte(t,{t1 - t0:.2f})':volume=0.4,afade=t=in:d=0.3,afade=t=out:st={t1e - t0 - 0.8:.2f}:d=0.8[a]",
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out_mp4], check=True)
    os.remove(silent)
