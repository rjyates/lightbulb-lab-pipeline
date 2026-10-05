"""Tech from Scratch Ep. 1: What Is a Computer?  (Kip & Bub in the desk room + explainer card)
python3 ep1.py            -> renders ep1-video.mp4 (no music)
python3 ep1.py 5,20,40    -> preview frames into chk/
"""
import math, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, '/home/claude/intro')
import render as R
from puppet2 import draw_kip, draw_bub
from room import make_room, FLOOR, DESK_TOP
import visuals as V

AUDIO = '/home/claude/ep1/kip-ep1.mp3'
OFFSET = 1.0; FPS = 30; AUD_LEN = 125.81
DUR = AUD_LEN + OFFSET + 4.0
v = lambda a: a + OFFSET
ease, ramp, clamp, back = R.ease, R.ramp, R.clamp, R.back
OUT = '/home/claude/ep1/ep1-video.mp4'

# ---------- captions (audio time) ----------
SEGS = [(0.0, "Quick question."), (1.25, "How many computers do you think you own?"),
 (3.83, "There's the laptop, sure."), (5.65, "But also your phone."), (7.06, "Your TV."), (8.09, "Your car."),
 (9.06, "Your microwave, probably."), (10.89, "Maybe even your thermostat."),
 (13.28, "Today on Tech from Scratch:"), (15.11, "what is a computer, really?"),
 (17.78, "Here's the simple version."), (19.43, "A computer is a machine that takes in information,"),
 (22.23, "works on it,"), (23.14, "remembers it,"), (24.08, "and gives you a result."), (25.69, "That's it."), (26.54, "Four jobs."),
 (28.52, "The easiest way to picture it is a kitchen."),
 (31.77, "First, ingredients come in."), (33.95, "For a computer, that's input:"), (36.07, "what you type, tap, click, or say."),
 (39.20, "Your keyboard, your touchscreen, your microphone."),
 (43.09, "Next, someone has to cook."), (45.32, "That's the processor, sometimes called the CPU."),
 (48.90, "It follows instructions, step by step,"), (51.39, "incredibly fast."), (53.04, "Billions of tiny steps every second."),
 (56.71, "While the cook works, they need counter space."), (59.37, "That's memory, or RAM."),
 (61.46, "It holds whatever you're working on right now."), (63.92, "More counter space means you can juggle more at once."),
 (67.82, "But here's the catch."), (69.15, "When you turn the computer off,"), (70.78, "the counter gets wiped clean."),
 (73.71, "That's why there's a pantry."), (75.30, "That's storage:"), (76.49, "your hard drive or SSD."),
 (78.74, "It keeps your photos, files, and apps safe,"), (81.74, "even when the power's off."),
 (84.31, "Finally, the meal is served."), (86.53, "That's output:"), (87.75, "what you see on the screen, hear from the speakers, or get from the printer."),
 (92.80, "So when you send a text:"), (94.42, "your thumbs are the input,"), (96.10, "the processor does the work,"),
 (97.86, "memory holds the message while you type,"), (100.19, "storage saves the conversation,"), (102.23, "and the screen shows it sent."),
 (104.48, "Every computer, from a phone to a supercomputer,"), (107.50, "does those same four jobs."),
 (110.56, "Ingredients in."), (111.85, "Cook works."), (112.90, "Counter holds."), (114.01, "Pantry keeps."), (115.20, "Meal comes out."), (116.51, "That's a computer."),
 (118.47, "Next time, we'll open one up and look at the parts that make all this happen."),
 (122.83, "Subscribe so you don't miss it,"), (124.65, "and we'll see you then.")]
R.SEGS = SEGS; R.SEG_END = AUD_LEN + 0.3; R.OFFSET = OFFSET

# ---------- voice loudness for mouth sync ----------
def loudness(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; hop = 16000 // FPS
    e = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a), hop)]); return e / (e.max() + 1e-9)
ENV = loudness(AUDIO)
def env(t):
    i = int((t - OFFSET) * FPS); return float(ENV[i]) if 0 <= i < len(ENV) else 0.0

# ---------- set ----------
BACK, DESK = make_room()
KIP_X, BUB_X = 800, 1250
CS = 1.15
CARD_X, CARD_Y = 1050, 28
_yy, _xx = np.mgrid[0:R.H, 0:R.W]
_d = np.sqrt(((_xx - R.W / 2) / (R.W * 0.62)) ** 2 + ((_yy - R.H * 0.46) / (R.H * 0.62)) ** 2)
_va = (np.clip(_d - 0.55, 0, 1) ** 1.6 * 230).astype(np.uint8)
VIG = Image.fromarray(np.dstack([np.zeros_like(_va)] * 3 + [_va]), 'RGBA')
random.seed(7)
MOTES = [(random.uniform(520, 1400), random.uniform(220, 700), random.uniform(1.5, 4), random.uniform(0, 6.28), random.uniform(0.15, 0.4)) for _ in range(40)]
def motes(fr, t):
    lay = Image.new('RGBA', (R.W, R.H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x, y, r, ph, sp in MOTES:
        mx = x + math.sin(t * sp + ph) * 30; my = y - (t * 12 * sp) % 80 + math.cos(t * sp * 1.3 + ph) * 10
        a = int(90 + 70 * math.sin(t * 2 + ph)); d.ellipse([mx - r, my - r, mx + r, my + r], fill=(255, 220, 150, max(0, a)))
    fr.alpha_composite(lay)
CWs, CHs = int(V.CW * 1.15), int(V.CH * 1.15)
_cs = Image.new('RGBA', (CWs + 80, CHs + 80), (0, 0, 0, 0)); ImageDraw.Draw(_cs).rounded_rectangle([40, 48, CWs + 40, CHs + 48], 38, fill=(0, 0, 0, 150))
CARD_SHADOW = _cs.filter(ImageFilter.GaussianBlur(16))

# ---------- Kip acting ----------
REST, POINT, OPEN, SHRUG, ASK = (14, 8), (100, -14), (58, 22), (74, 70), (50, 40)
#        time    arm_l  arm_r  look  lean  eyes
KEYS = [(0.0, ASK, ASK, 0.0, 0.25, 'open'),
 (v(3.5), REST, POINT, 0.7, 0.25, 'open'), (v(12.6), REST, POINT, 0.7, 0.25, 'open'),
 (v(13.1), OPEN, OPEN, 0.0, 0.0, 'happy'), (v(17.3), OPEN, OPEN, 0.0, 0.0, 'happy'),
 (v(17.8), REST, POINT, 0.7, 0.25, 'open'), (v(28.0), REST, POINT, 0.7, 0.25, 'open'),
 (v(28.5), OPEN, OPEN, 0.2, 0.0, 'happy'), (v(31.3), OPEN, OPEN, 0.2, 0.0, 'happy'),
 (v(31.7), REST, POINT, 0.7, 0.25, 'open'), (v(48.6), REST, POINT, 0.7, 0.25, 'open'),
 (v(48.9), (48, -70), (34, -40), -0.7, -0.2, 'open'), (v(55.3), (48, -70), (34, -40), -0.7, -0.2, 'open'),
 (v(56.6), REST, POINT, 0.7, 0.25, 'open'), (v(63.6), REST, POINT, 0.7, 0.25, 'open'),
 (v(63.9), OPEN, OPEN, 0.1, 0.0, 'happy'), (v(67.4), OPEN, OPEN, 0.1, 0.0, 'happy'),
 (v(67.8), SHRUG, SHRUG, 0.0, 0.0, 'open'), (v(73.3), SHRUG, SHRUG, 0.0, 0.0, 'wide'),
 (v(73.7), REST, POINT, 0.7, 0.25, 'open'), (v(84.0), REST, POINT, 0.7, 0.25, 'open'),
 (v(84.3), REST, OPEN, 0.5, 0.1, 'happy'), (v(87.4), REST, OPEN, 0.5, 0.1, 'happy'),
 (v(87.75), REST, POINT, 0.7, 0.25, 'open'), (v(104.2), REST, POINT, 0.7, 0.25, 'open'),
 (v(104.5), OPEN, OPEN, 0.0, 0.0, 'happy'), (v(110.2), OPEN, OPEN, 0.0, 0.0, 'happy'),
 (v(110.5), REST, POINT, 0.7, 0.25, 'open'), (v(117.0), REST, POINT, 0.7, 0.25, 'open'),
 (v(117.5), REST, REST, 0.0, 0.0, 'happy'), (v(122.6), REST, REST, 0.0, 0.0, 'happy'),
 (v(122.9), REST, (132, 4), 0.0, 0.0, 'happy'), (DUR, REST, (132, 4), 0.0, 0.0, 'happy')]
WIDE_AT = (v(70.4), v(72.6))
def keyed(t):
    for a, b in zip(KEYS, KEYS[1:]):
        if a[0] <= t <= b[0]:
            u = ease((t - a[0]) / max(1e-6, min(0.4, b[0] - a[0]))); L = lambda p, q: p + (q - p) * u
            return (L(a[1][0], b[1][0]), L(a[1][1], b[1][1])), (L(a[2][0], b[2][0]), L(a[2][1], b[2][1])), L(a[3], b[3]), L(a[4], b[4]), (b[5] if u > 0.5 else a[5])
    return REST, REST, 0.0, 0.0, 'happy'

def kip_layer(fr, t):
    al, ar, look, lean, eyes = keyed(t)
    if t > v(122.9): ar = (ar[0], ar[1] + 28 * math.sin(t * 9))
    if v(48.9) < t < v(55.3): al = (al[0], al[1] + 6 * math.sin(t * 22)); ar = (ar[0], ar[1] + 6 * math.sin(t * 19 + 1))
    if WIDE_AT[0] < t < WIDE_AT[1]: eyes = 'wide'
    if ar == POINT or abs(ar[0] - POINT[0]) < 2: ar = (ar[0] + 4 * math.sin(t * 2.3), ar[1])
    m = min(1.0, env(t) * 1.6)
    blink = 1.0 if (t % 4.3) < 0.1 else 0.0
    ant = math.sin(t * 10) * 0.12 + m * 0.25 * math.sin(t * 14)
    bob = 4 * math.sin(t * 2.2) + m * 6
    k = draw_kip(scale=0.9, walk=0, walking=0, bob=bob, arm_l=al, arm_r=ar, mouth=m, blink=blink, eyes=eyes, antenna=ant, lean=lean, look=look)
    fr.alpha_composite(k, (int(KIP_X - k.width / 2), FLOOR - k.height + 30))

# ---------- Bub acting ----------
MOODS = [(0, 'curious'), (v(3.6), 'happy'), (v(13.2), 'aha'), (v(17.6), 'happy'), (v(42.9), 'curious'), (v(51.4), 'confused'),
         (v(56.4), 'curious'), (v(67.8), 'confused'), (v(73.8), 'happy'), (v(84.3), 'aha'), (v(92.6), 'happy'),
         (v(110.4), 'happy'), (v(116.5), 'aha'), (v(118.3), 'happy')]
def bub_mood(t):
    m = 'happy'
    for a, s in MOODS:
        if t >= a: m = s
    return m
HOPS = [v(x) for x in (3.83, 5.65, 7.06, 8.09, 9.06, 10.89, 20.4, 22.23, 23.14, 24.08, 94.42, 96.10, 97.86, 100.19, 102.23, 110.56, 111.85, 112.90, 114.01, 115.20)]
def bub_layer(fr, t):
    mood = bub_mood(t); y = DESK_TOP; squash = 0.0
    for h in HOPS:
        u = (t - h) / 0.35
        if 0 <= u <= 1: y -= math.sin(math.pi * u) * 34; squash = -0.35 * math.sin(math.pi * u)
        elif 1 < u < 1.6: squash = 0.4 * math.exp(-(u - 1) * 8)
    y -= abs(math.sin(t * 2.6)) * 6
    rays = 1.0 if mood == 'aha' else 0.0
    dim = 0.5 if (mood == 'confused' and v(67.8) <= t < v(73.8)) else 0.0
    if v(70.3) < t < v(73.6): dim = 0.75
    glow = {'happy': 0.85, 'aha': 1.15, 'confused': 0.4, 'curious': 0.7}[mood] * (1 - dim * 0.7) + 0.06 * math.sin(t * 4)
    g = R.GLOW.resize((int(640 * glow * 0.75),) * 2); fr.alpha_composite(g, (int(BUB_X - g.width / 2), int(y - 150 - g.height / 2)))
    b = draw_bub(scale=0.66, squash=squash, mood=mood, rays=rays, dim=dim, blink=1.0 if (t % 5.1) < 0.1 else 0.0)
    if v(51.4) < t < v(55.4):  # dizzy spin while the processor goes fast
        b = b.rotate(math.sin((t - v(51.4)) * 9) * 18, resample=Image.BICUBIC, center=(b.width / 2, b.height * 0.55))
    fr.alpha_composite(b, (int(BUB_X - b.width / 2), int(y - b.height + 14)))

# ---------- explainer card timeline ----------
KT = {'input': v(31.77), 'fast': v(51.39), 'memory': v(58.4), 'off': v(70.3), 'wipe': v(71.3), 'storage': v(73.71), 'items': v(78.9), 'output': v(84.31)}
def kitchen_beat(t):
    for a, b in [(v(84.0), 'output'), (v(73.5), 'storage'), (v(67.6), 'catch'), (v(56.4), 'memory'), (v(42.8), 'process'), (v(31.5), 'input')]:
        if t >= a: return b
    return 'kitchen'
def kitchen(t):
    c = V.kitchen_card(t, KT, kitchen_beat(t))
    if v(35.9) <= t < v(42.6):
        c.layer(V.callout_row(['keyboard', 'touch', 'mic'], ['Keyboard', 'Touchscreen', 'Microphone'], [v(39.3), v(40.3), v(41.1)], t,
                              'What you type, tap, click or say', ramp(t, v(35.9), v(36.3)) * (1 - ramp(t, v(42.3), v(42.6)))))
    if t >= v(53.04) and kitchen_beat(t) == 'process':
        a = ease((t - v(53.04)) / 0.3); c.chip(440, 340, 'Billions of steps per second', 18, V.NAVY, V.CREAM, a)
    if v(87.6) <= t:
        c.layer(V.callout_row(['screen', 'speaker', 'printer'], ['Screen', 'Speakers', 'Printer'], [v(88.3), v(89.5), v(90.6)], t,
                              'What you see, hear, or print', ramp(t, v(87.6), v(88.0))))
    return c
SEG = [(v(3.6), v(12.7), lambda t: V.devices_card([v(x) for x in (3.83, 5.65, 7.06, 8.09, 9.06, 10.89)], t)),
       (v(17.7), v(28.0), lambda t: V.jobs_card([v(x) for x in (20.4, 22.23, 23.14, 24.08)], t)),
       (v(28.4), v(92.4), kitchen),
       (v(92.5), v(109.9), lambda t: V.phone_card(t, [v(x) for x in (94.42, 96.10, 97.86, 100.19, 102.23)])),
       (v(110.1), v(118.2), lambda t: V.recap_card(t, [v(x) for x in (110.56, 111.85, 112.90, 114.01, 115.20)]))]
def card_layer(fr, t):
    for t0, t1, fn in SEG:
        if t0 <= t < t1:
            sc = back((t - t0) / 0.4) * (1 - ease((t - (t1 - 0.3)) / 0.3))
            if sc <= 0.02: return
            im = fn(t).im.resize((max(1, int(CWs * sc)), max(1, int(CHs * sc))), Image.LANCZOS)
            cx, cy = CARD_X + CWs / 2, CARD_Y + CHs / 2
            sh = CARD_SHADOW if sc >= 0.999 else CARD_SHADOW.resize((max(1, int(CARD_SHADOW.width * sc)), max(1, int(CARD_SHADOW.height * sc))))
            fr.alpha_composite(sh, (int(cx - sh.width / 2), int(cy - sh.height / 2)))
            fr.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
            return

# ---------- full-screen title + end card ----------
def title_card(fr, t):
    a = ramp(t, v(13.0), v(13.4)) * (1 - ramp(t, v(17.2), v(17.6)))
    if a <= 0: return
    card = Image.new('RGBA', (R.W, R.H), (*R.NAVY, 255)); d = ImageDraw.Draw(card)
    card.alpha_composite(R.LAMP, (R.W // 2 - 700, -200))
    txt = 'TECH FROM SCRATCH  ·  EPISODE 1'; f = R.font(R.F_BOLD, 34); bw = d.textlength(txt, font=f) + 70
    d.rounded_rectangle([R.W / 2 - bw / 2, 330, R.W / 2 + bw / 2, 392], 31, fill=R.AMBER); d.text((R.W / 2, 361), txt, font=f, fill=R.NAVY, anchor='mm')
    s = back((t - v(15.0)) / 0.6)
    if s > 0.02:
        t1 = Image.new('RGBA', (R.W, 220), (0, 0, 0, 0)); ImageDraw.Draw(t1).text((R.W / 2, 110), 'What Is a Computer?', font=R.font(R.F_BOLD, 130), fill=R.CREAM, anchor='mm')
        t1 = t1.resize((max(1, int(R.W * s)), max(1, int(220 * s)))); card.alpha_composite(t1, (int(R.W / 2 - t1.width / 2), int(520 - t1.height / 2)))
    b = draw_bub(scale=0.5, mood='aha', rays=1.0); hop = abs(math.sin(t * 5)) * 26
    g = R.GLOW.resize((300, 300)); card.alpha_composite(g, (1680 - 150, int(860 - hop - 150))); card.alpha_composite(b, (1680 - b.width // 2, int(960 - hop - b.height)))
    if a < 1: card.putalpha(card.getchannel('A').point(lambda p: int(p * a)))
    fr.alpha_composite(card)

def end_card(fr, t):
    a = ramp(t, v(118.6), v(119.1))
    if a <= 0: return
    ov = Image.new('RGBA', (R.W, R.H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([1390, 120, 1860, 680], 40, fill=(6, 16, 34, 215)); lx = 1625
    d.text((lx, 225), 'Lightbulb', font=R.font(R.F_BOLD, 96), fill=R.CREAM, anchor='mm')
    d.text((lx, 325), 'Lab', font=R.font(R.F_BOLD, 96), fill=R.AMBER, anchor='mm')
    d.text((lx, 405), 'T E C H   M A D E   S I M P L E', font=R.font(R.F_MED, 26), fill=R.CREAM, anchor='mm')
    d.text((lx, 470), 'Next: Inside a Computer', font=R.font(R.F_MED, 30), fill=(200, 210, 230), anchor='mm')
    pulse = 1 + 0.04 * math.sin(t * 5) * (t > v(122.8)); bw, bh = 300 * pulse, 84 * pulse
    d.rounded_rectangle([lx - bw / 2, 585 - bh / 2, lx + bw / 2, 585 + bh / 2], 42, fill=R.AMBER)
    d.text((lx, 585), 'Subscribe', font=R.font(R.F_BOLD, 40), fill=R.NAVY, anchor='mm')
    ov.putalpha(ov.getchannel('A').point(lambda p: int(p * a))); fr.alpha_composite(ov)

def frame(t):
    fr = BACK.copy(); motes(fr, t)
    kip_layer(fr, t); fr.alpha_composite(DESK)
    fr.alpha_composite(VIG)
    card_layer(fr, t); bub_layer(fr, t); title_card(fr, t); end_card(fr, t)
    R.caption(fr, t)
    fade = ramp(t, 0, 0.5) * (1 - ramp(t, DUR - 0.8, DUR))
    if fade < 1: fr.alpha_composite(Image.new('RGBA', (R.W, R.H), (0, 0, 0, int(255 * (1 - fade)))))
    return fr.convert('RGB')

# ---------- sound ----------
SR = 44100
def _wav(name, x):
    x = x / max(1e-9, np.abs(x).max()) * 0.8
    with wave.open(name, 'w') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
def make_sfx():
    t = np.linspace(0, 0.12, int(SR * 0.12), False); f = np.linspace(900, 400, len(t))
    _wav('/home/claude/ep1/pop.wav', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35))
    t = np.linspace(0, 1.4, int(SR * 1.4), False); f = 700 + 300 * np.sin(2 * np.pi * 3.2 * t) * (1 - t / 1.6)
    _wav('/home/claude/ep1/dizzy.wav', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.05) * np.minimum(1, (1.4 - t) / 0.2))
    t = np.linspace(0, 0.6, int(SR * 0.6), False); f = np.linspace(260, 70, len(t))
    _wav('/home/claude/ep1/off.wav', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4))
B = '/home/claude/bub/'
CUES = [(v(1.4), B + 'bub-curious-chirp.wav', 0.4)] + [(v(x), '/home/claude/ep1/pop.wav', 0.35) for x in (3.83, 5.65, 7.06, 8.09, 9.06, 10.89, 20.4, 22.23, 23.14, 24.08, 39.3, 40.3, 41.1, 88.3, 89.5, 90.6, 94.42, 96.10, 97.86, 100.19, 102.23, 110.56, 111.85, 112.90, 114.01, 115.20)] + [
    (v(13.3), B + 'bub-aha-ding.wav', 0.35), (v(31.9), B + 'bub-happy-chirp.wav', 0.35), (v(51.4), '/home/claude/ep1/dizzy.wav', 0.3),
    (v(56.8), B + 'bub-curious-chirp.wav', 0.35), (v(70.3), '/home/claude/ep1/off.wav', 0.5), (v(71.0), B + 'bub-confused-warble.wav', 0.35),
    (v(74.0), B + 'bub-happy-chirp.wav', 0.35), (v(85.3), B + 'bub-aha-ding.wav', 0.35), (v(104.6), B + 'bub-excited-beeps.wav', 0.35),
    (v(116.6), B + 'bub-aha-ding.wav', 0.35), (v(123.0), B + 'bub-happy-chirp.wav', 0.35)]
def mix(path):
    ins = ['-i', AUDIO]; f = [f'[0:a]adelay={int(OFFSET*1000)}:all=1[k]']
    for i, (tt, n, vol) in enumerate(CUES, 1):
        ins += ['-i', n]; f.append(f'[{i}:a]adelay={int(tt*1000)}:all=1,volume={vol}[s{i}]')
    f.append('[k]' + ''.join(f'[s{i}]' for i in range(1, len(CUES) + 1)) + f'amix=inputs={len(CUES)+1}:normalize=0,apad=whole_dur={DUR}[a]')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *ins, '-filter_complex', ';'.join(f), '-map', '[a]', '-t', f'{DUR:.2f}', '-ar', '48000', path], check=True)

def render(t0=0.0, t1=None, out=OUT):
    t1 = t1 or DUR
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{R.W}x{R.H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    n0, n1 = int(t0 * FPS), int(t1 * FPS)
    for i in range(n0, n1):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 300 == 0: print(f'{i}/{n1}', flush=True)
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'part':
        a, b, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]; render(a, b, out); print('done', out); raise SystemExit
    if len(sys.argv) > 1:
        for tt in map(float, sys.argv[1].split(',')):
            frame(tt).resize((960, 540)).save(f'/home/claude/ep1/chk_{tt:06.1f}.png')
        raise SystemExit
    make_sfx(); mix('/home/claude/ep1/voice_sfx.wav'); render(); print('done')
