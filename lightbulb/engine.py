"""Turns an episode file + Kip's voice (with timing) into video frames.

Episode file (episodes/epNN.json), simplified:
{
  "id": "ep02", "number": 2, "series": "Tech from Scratch", "title": "Hardware vs. Software",
  "next": "Next: What Is the Internet?",
  "scenes": [
    {"say": "Quick question...", "kip": "ask", "bub": "curious"},
    {"say": "Today on Tech from Scratch: ...", "title": true},
    {"say": "...", "kip": "point", "card": {"type": "grid", "title": "...",
        "items": [{"icon": "laptop", "label": "Laptop", "at": "laptop"}, ...]}},
    {"say": "...", "card": "keep"}          # keep showing the previous card
  ],
  "shorts": [{"hook": "...", "scenes": [1, 3]}]
}
Item "at" = a word in the script; the item pops in when Kip says it (otherwise items are spread evenly).
Kip poses: rest, point, open, shrug, ask, type, wave.   Bub moods: happy, curious, aha, confused, sleepy.
"""
import json, math, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from . import core as K
from . import cards as C
from .characters import draw_kip, draw_bub
from .room import make_room, FLOOR, DESK_TOP

OFFSET, TAIL = 1.0, 4.0
KIP_X, BUB_X = 800, 1250
CARD_SCALE, CARD_X, CARD_Y = 1.15, 1050, 28
CWs, CHs = int(C.CW * CARD_SCALE), int(C.CH * CARD_SCALE)
REST, POINT, OPEN, SHRUG, ASK = (14, 8), (100, -14), (58, 22), (74, 70), (50, 40)
TYPE_L, TYPE_R, WAVE = (48, -70), (34, -40), (132, 4)
POSES = {  # arm_l, arm_r, look, lean, eyes
    'rest': (REST, REST, 0.0, 0.0, 'happy'), 'point': (REST, POINT, 0.7, 0.25, 'open'), 'open': (OPEN, OPEN, 0.0, 0.0, 'happy'),
    'shrug': (SHRUG, SHRUG, 0.0, 0.0, 'open'), 'ask': (ASK, ASK, 0.0, 0.25, 'open'), 'type': (TYPE_L, TYPE_R, -0.7, -0.2, 'open'),
    'wave': (REST, WAVE, 0.0, 0.0, 'happy')}

# ------------------------------------------------------------------ timing
def scene_text(ep): return [s['say'].strip() for s in ep['scenes']]
def full_text(ep): return ' ... '.join(scene_text(ep))

class Timing:
    """char-level times for the full script (audio seconds)"""
    def __init__(self, text, starts, ends):
        self.text, self.st, self.en = text, starts, ends
    @staticmethod
    def from_alignment(text, al):
        st, en = al['character_start_times_seconds'], al['character_end_times_seconds']
        if ''.join(al['characters']) != text:  # tolerate tiny normalisation differences
            st = np.interp(np.linspace(0, len(st) - 1, len(text)), np.arange(len(st)), st).tolist()
            en = np.interp(np.linspace(0, len(en) - 1, len(text)), np.arange(len(en)), en).tolist()
        return Timing(text, st, en)
    @staticmethod
    def from_pauses(text, scenes, audio_path):
        """fallback when there are no timestamps: scene breaks = the longest pauses, words spread by character count"""
        out = subprocess.run(['ffmpeg', '-hide_banner', '-i', audio_path, '-af', 'silencedetect=noise=-38dB:d=0.25', '-f', 'null', '-'],
                             capture_output=True, text=True).stderr
        st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
        dur = float(re.search(r'Duration: (\d+):(\d+):([\d.]+)', out).groups()[2]) + 60 * int(re.search(r'Duration: (\d+):(\d+)', out).group(2))
        gaps = sorted(zip(st, en), key=lambda g: g[1] - g[0], reverse=True)[:len(scenes) - 1]
        gaps.sort(); bounds = [0.0] + [g[1] for g in gaps] + [dur]; ends = [g[0] for g in gaps] + [dur]
        starts_c, ends_c = [0.0] * len(text), [0.0] * len(text); pos = 0
        for i, s in enumerate(scenes):
            a, b = bounds[i], ends[i]
            for j in range(len(s)):
                starts_c[pos + j] = a + (b - a) * j / max(1, len(s)); ends_c[pos + j] = a + (b - a) * (j + 1) / max(1, len(s))
            pos += len(s)
            if i < len(scenes) - 1:
                for j in range(5): starts_c[pos + j] = ends_c[pos + j] = b
                pos += 5
        return Timing(text, starts_c, ends_c)
    def at(self, idx): return self.st[min(max(idx, 0), len(self.st) - 1)]
    def end_at(self, idx): return self.en[min(max(idx, 0), len(self.en) - 1)]

def find_word(text, word, start, end):
    m = re.search(r'\b' + re.escape(word.lower()), text[start:end].lower())
    return start + m.start() if m else None

# ------------------------------------------------------------------ timeline
class Episode:
    def __init__(self, ep, timing, audio_len):
        self.ep, self.T = ep, timing; self.audio_len = audio_len
        self.dur = audio_len + OFFSET + TAIL
        texts = scene_text(ep); self.sc = []; pos = 0
        for t in texts:
            self.sc.append((pos, pos + len(t))); pos += len(t) + 5
        v = lambda a: a + OFFSET
        self.s_start = [v(timing.at(a)) for a, b in self.sc]
        self.s_end = [v(timing.end_at(b - 1)) for a, b in self.sc]
        # captions: split scenes at punctuation; long clauses also at commas
        self.caps = []
        for (a, b), t in zip(self.sc, texts):
            for m in re.finditer(r'[^.?!:;]+[.?!:;]*', t):
                chunk = m.group().strip()
                if not chunk: continue
                parts = [chunk] if len(chunk) <= 70 else [p.strip() for p in re.split(r'(?<=,)\s+', chunk)]
                off = a + m.start()
                for p in parts:
                    k = t.find(p, off - a); self.caps.append((v(timing.at(a + k)), p)); off = a + k + len(p)
        self.caps.sort()
        # cards: a "card" starts a block; following "keep" scenes extend it
        self.cards = []; cur = None
        for i, s in enumerate(ep['scenes']):
            c = s.get('card')
            if isinstance(c, dict): cur = {'spec': c, 'first': i, 'last': i}; self.cards.append(cur)
            elif c == 'keep' and cur: cur['last'] = i
            else: cur = None
        for blk in self.cards:
            a, b = self.sc[blk['first']][0], self.sc[blk['last']][1]
            spec = blk['spec']; n = C.n_reveals(spec); times = []; cursor = a
            ats = [it.get('at') for it in spec.get('items', [])] if spec['type'] not in ('statement', 'compare') else spec.get('at', [None] * n)
            ats = (list(ats) + [None] * n)[:n]
            for j, w in enumerate(ats):
                idx = find_word(timing.text, w, cursor, b) if w else None
                if idx is not None: times.append(v(timing.at(idx))); cursor = idx + 1
                else: times.append(None)
            t0, t1 = self.s_start[blk['first']], self.s_end[blk['last']]
            for j in range(n):  # fill unsynced items evenly
                if times[j] is None: times[j] = t0 + 0.6 + (t1 - t0 - 1.2) * (j + 0.5) / n if spec['type'] != 'statement' else t0 + 0.3
            blk['times'] = times; blk['t0'] = t0 - 0.35; blk['t1'] = t1 + 0.35
        self.reveals = sorted(x for blk in self.cards for x in blk['times'] if spec_pops(blk['spec']))
        # kip/bub key list
        self.kip_keys = []; self.moods = []
        for i, s in enumerate(ep['scenes']):
            pose = s.get('kip') or ('open' if s.get('title') else ('point' if s.get('card') else 'rest'))
            if i == len(ep['scenes']) - 1: pose = s.get('kip', 'rest')
            self.kip_keys.append((self.s_start[i] - 0.3, pose))
            self.moods.append((self.s_start[i] - 0.2, s.get('bub') or ('aha' if s.get('title') else 'happy')))
        self.wave_at = self.s_start[-1] + 0.4 * (self.s_end[-1] - self.s_start[-1])
        self.title_i = next((i for i, s in enumerate(ep['scenes']) if s.get('title')), None)
        self.room = make_room(); self.vig = K.vignette(); self.motes = Motes()
        sh = Image.new('RGBA', (CWs + 80, CHs + 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([40, 48, CWs + 40, CHs + 48], 38, fill=(0, 0, 0, 150))
        self.card_shadow = sh.filter(ImageFilter.GaussianBlur(16))
        self.env = None

    # ---- characters
    def kip_state(self, t):
        prev, nxt, t0 = 'rest', 'rest', 0.0
        for k, (tt, p) in enumerate(self.kip_keys):
            if t >= tt: prev = self.kip_keys[k - 1][1] if k else 'rest'; nxt = p; t0 = tt
        if t >= self.wave_at: prev, nxt, t0 = (self.kip_keys[-1][1], 'wave', self.wave_at)
        u = K.ease((t - t0) / 0.4); A, B = POSES[prev], POSES[nxt]
        L = lambda p, q: p + (q - p) * u
        al = (L(A[0][0], B[0][0]), L(A[0][1], B[0][1])); ar = (L(A[1][0], B[1][0]), L(A[1][1], B[1][1]))
        return al, ar, L(A[2], B[2]), L(A[3], B[3]), (B[4] if u > 0.5 else A[4]), nxt

    def kip(self, fr, t):
        al, ar, look, lean, eyes, pose = self.kip_state(t)
        if pose == 'wave': ar = (ar[0], ar[1] + 28 * math.sin(t * 9))
        if pose == 'type': al = (al[0], al[1] + 6 * math.sin(t * 22)); ar = (ar[0], ar[1] + 6 * math.sin(t * 19 + 1))
        if pose == 'point': ar = (ar[0] + 4 * math.sin(t * 2.3), ar[1])
        m = min(1.0, self.loud(t) * 1.6)
        k = draw_kip(scale=0.9, bob=4 * math.sin(t * 2.2) + m * 6, arm_l=al, arm_r=ar, mouth=m, blink=1.0 if (t % 4.3) < 0.1 else 0.0,
                     eyes=eyes, antenna=math.sin(t * 10) * 0.12 + m * 0.25 * math.sin(t * 14), lean=lean, look=look)
        fr.alpha_composite(k, (int(KIP_X - k.width / 2), FLOOR - k.height + 30))

    def mood(self, t):
        m = 'happy'
        for tt, s in self.moods:
            if t >= tt: m = s
        return m

    def bub(self, fr, t):
        mood = self.mood(t); y = DESK_TOP; squash = 0.0
        for h in self.reveals:
            u = (t - h) / 0.35
            if 0 <= u <= 1: y -= math.sin(math.pi * u) * 34; squash = -0.35 * math.sin(math.pi * u)
            elif 1 < u < 1.6: squash = 0.4 * math.exp(-(u - 1) * 8)
        y -= abs(math.sin(t * 2.6)) * 6
        dim = 0.55 if mood == 'confused' else 0.0
        glow = {'happy': 0.85, 'aha': 1.15, 'confused': 0.4, 'curious': 0.7, 'sleepy': 0.35}.get(mood, 0.85) + 0.06 * math.sin(t * 4)
        g = K.GLOW.resize((int(640 * glow * 0.75),) * 2); fr.alpha_composite(g, (int(BUB_X - g.width / 2), int(y - 150 - g.height / 2)))
        b = draw_bub(scale=0.66, squash=squash, mood=mood, rays=1.0 if mood == 'aha' else 0.0, dim=dim, blink=1.0 if (t % 5.1) < 0.1 else 0.0)
        fr.alpha_composite(b, (int(BUB_X - b.width / 2), int(y - b.height + 14)))

    # ---- voice loudness (mouth)
    def set_audio(self, path, fps=K.FPS):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True).stdout
        a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; hop = 16000 // fps
        e = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a), hop)]); self.env = e / (e.max() + 1e-9)
    def loud(self, t):
        if self.env is None: return 0.0
        i = int((t - OFFSET) * K.FPS); return float(self.env[i]) if 0 <= i < len(self.env) else 0.0

    # ---- overlays
    def card_now(self, t):
        for blk in self.cards:
            if blk['t0'] <= t < blk['t1']:
                sc = K.back((t - blk['t0']) / 0.4) * (1 - K.ease((t - (blk['t1'] - 0.3)) / 0.3))
                return C.render(blk['spec'], t, blk['times']), sc
        return None, 0.0
    def card(self, fr, t):
        c, sc = self.card_now(t)
        if c is None or sc <= 0.02: return
        im = c.im.resize((max(1, int(CWs * sc)), max(1, int(CHs * sc))), Image.LANCZOS)
        cx, cy = CARD_X + CWs / 2, CARD_Y + CHs / 2
        sh = self.card_shadow if sc >= 0.999 else self.card_shadow.resize((max(1, int(self.card_shadow.width * sc)), max(1, int(self.card_shadow.height * sc))))
        fr.alpha_composite(sh, (int(cx - sh.width / 2), int(cy - sh.height / 2))); fr.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

    def title(self, fr, t):
        if self.title_i is None: return
        a0, a1 = self.s_start[self.title_i], self.s_end[self.title_i]
        a = K.ramp(t, a0 - 0.3, a0) * (1 - K.ramp(t, a1 + 0.3, a1 + 0.7))
        if a <= 0: return
        ep = self.ep; W, H = K.W, K.H
        card = Image.new('RGBA', (W, H), (*K.NAVY, 255)); d = ImageDraw.Draw(card); card.alpha_composite(K.LAMP, (W // 2 - 700, -200))
        txt = f"{ep.get('series', 'Tech from Scratch').upper()}  ·  EPISODE {ep['number']}"; f = K.font(K.F_BOLD, 34); bw = d.textlength(txt, font=f) + 70
        d.rounded_rectangle([W / 2 - bw / 2, 330, W / 2 + bw / 2, 392], 31, fill=K.AMBER); d.text((W / 2, 361), txt, font=f, fill=K.NAVY, anchor='mm')
        s = K.back((t - a0 - 1.0) / 0.6)
        if s > 0.02:
            size = 130
            while size > 70 and d.textlength(ep['title'], font=K.font(K.F_BOLD, size)) > 1700: size -= 4
            t1 = Image.new('RGBA', (W, 220), (0, 0, 0, 0)); ImageDraw.Draw(t1).text((W / 2, 110), ep['title'], font=K.font(K.F_BOLD, size), fill=K.CREAM, anchor='mm')
            t1 = t1.resize((max(1, int(W * s)), max(1, int(220 * s)))); card.alpha_composite(t1, (int(W / 2 - t1.width / 2), int(520 - t1.height / 2)))
        b = draw_bub(scale=0.5, mood='aha', rays=1.0); hop = abs(math.sin(t * 5)) * 26
        g = K.GLOW.resize((300, 300)); card.alpha_composite(g, (1680 - 150, int(860 - hop - 150))); card.alpha_composite(b, (1680 - b.width // 2, int(960 - hop - b.height)))
        if a < 1: card.putalpha(card.getchannel('A').point(lambda p: int(p * a)))
        fr.alpha_composite(card)

    def endcard(self, fr, t):
        a = K.ramp(t, self.s_start[-1] - 0.2, self.s_start[-1] + 0.3)
        if a <= 0: return
        ov = Image.new('RGBA', (K.W, K.H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); lx = 1625
        d.rounded_rectangle([1390, 120, 1860, 680], 40, fill=(6, 16, 34, 215))
        d.text((lx, 225), 'Lightbulb', font=K.font(K.F_BOLD, 96), fill=K.CREAM, anchor='mm')
        d.text((lx, 325), 'Lab', font=K.font(K.F_BOLD, 96), fill=K.AMBER, anchor='mm')
        d.text((lx, 405), 'T E C H   M A D E   S I M P L E', font=K.font(K.F_MED, 26), fill=K.CREAM, anchor='mm')
        nx = self.ep.get('next', ''); f = K.font(K.F_MED, 30)
        while f.size > 18 and d.textlength(nx, font=f) > 440: f = K.font(K.F_MED, f.size - 2)
        d.text((lx, 470), nx, font=f, fill=(200, 210, 230), anchor='mm')
        pulse = 1 + 0.04 * math.sin(t * 5) * (t > self.wave_at); bw, bh = 300 * pulse, 84 * pulse
        d.rounded_rectangle([lx - bw / 2, 585 - bh / 2, lx + bw / 2, 585 + bh / 2], 42, fill=K.AMBER)
        d.text((lx, 585), 'Subscribe', font=K.font(K.F_BOLD, 40), fill=K.NAVY, anchor='mm')
        ov.putalpha(ov.getchannel('A').point(lambda p: int(p * a))); fr.alpha_composite(ov)

    def caption_at(self, t):
        txt = None
        for tt, s in self.caps:
            if t >= tt - 0.05: txt = s
        return txt if t < self.audio_len + OFFSET + 0.3 else None

    # ---- frames
    def scene(self, t):
        back, desk = self.room; fr = back.copy(); self.motes.draw(fr, t)
        self.kip(fr, t); fr.alpha_composite(desk); fr.alpha_composite(self.vig); return fr
    def frame(self, t):
        fr = self.scene(t); self.card(fr, t); self.bub(fr, t); self.title(fr, t); self.endcard(fr, t)
        K.caption(fr, self.caption_at(t)); K.fade(fr, K.ramp(t, 0, 0.5) * (1 - K.ramp(t, self.dur - 0.8, self.dur)))
        return fr.convert('RGB')

    # ---- sound cues: (time, file, volume)
    def cues(self):
        sfx = lambda n: f'{K.ASSETS}/sfx/{n}.wav'
        out = [(t, sfx('pop'), 0.35) for t in self.reveals]
        prev = None
        for tt, m in self.moods:
            if m != prev:
                n = {'aha': 'bub-aha-ding', 'confused': 'bub-confused-warble', 'curious': 'bub-curious-chirp', 'sleepy': 'bub-sleepy-beep'}.get(m)
                if n: out.append((tt + 0.3, sfx(n), 0.35))
            prev = m
        out.append((self.wave_at, sfx('bub-happy-chirp'), 0.35))
        return out

def spec_pops(spec): return spec['type'] in ('grid', 'tiles', 'callout', 'steps', 'flow', 'compare')

class Motes(K.Motes): pass
