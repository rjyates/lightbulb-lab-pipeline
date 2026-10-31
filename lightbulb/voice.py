"""Kip's voice, with character-level timestamps for exact caption/scene timing.

LBL_VOICE picks the provider:
  kokoro      free, offline, open-source (default). Needs requirements-voice.txt; downloads the model on first use.
  elevenlabs  ElevenLabs API. Its free plan is not licensed for commercial use.
Both write voice.mp3 plus voice.json = {text, voice, alignment} in ElevenLabs' alignment format, so the engine needs no changes.
"""
import base64, json, os, subprocess, time
import requests

API = 'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps'
SEP = ' ... '  # engine.full_text joins scenes with this
KIP = 'af_heart:0.4,am_michael:0.6'  # owner's pick "B-warm", 2026-10-30
KIP_SPEED = '0.97'
CREDITS = {'kokoro': 'Kip’s voice is AI-generated with Kokoro, an open-source text-to-speech model.',
           'elevenlabs': 'Kip’s voice is AI-generated with ElevenLabs.'}

def provider(cfg): return cfg.get('LBL_VOICE', 'kokoro')
def voice_id(cfg):
    """what a cached take must match to be reused"""
    return f"kokoro:{cfg.get('KOKORO_VOICE', KIP)}@{cfg.get('KOKORO_SPEED', KIP_SPEED)}" if provider(cfg) == 'kokoro' else 'elevenlabs'
def credit(cfg): return CREDITS[provider(cfg)]

def synthesize(text, cfg, out_mp3, out_json):
    al = (_kokoro if provider(cfg) == 'kokoro' else _elevenlabs)(text, cfg, out_mp3)
    json.dump({'text': text, 'voice': voice_id(cfg), 'alignment': al}, open(out_json, 'w'))
    return out_mp3, out_json

# ------------------------------------------------------------------ Kokoro
_PIPE = None
def _kokoro(text, cfg, out_mp3, sr=24000, gap=0.55):
    """each scene separately, joined by a short pause; token timestamps become per-character times"""
    global _PIPE
    import numpy as np, soundfile as sf
    from kokoro import KPipeline
    _PIPE = _PIPE or KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')  # American English
    mix = [(v, float(w)) for v, w in (p.split(':') for p in cfg.get('KOKORO_VOICE', KIP).split(','))]
    voice = sum(_PIPE.load_voice(v) * w for v, w in mix) / sum(w for _, w in mix)
    chunks, segs, t = [], [], 0.0
    for scene in text.split(SEP):
        t0, toks = t, []
        for r in _PIPE(scene, voice=voice, speed=float(cfg.get('KOKORO_SPEED', KIP_SPEED))):
            a = np.asarray(r.audio, dtype=np.float32)
            toks += [(tk.text, t + tk.start_ts, t + (tk.end_ts or tk.start_ts)) for tk in (r.tokens or []) if tk.start_ts is not None]
            chunks.append(a); t += len(a) / sr
        segs.append((scene, t0, t, toks))
        chunks.append(np.zeros(int(gap * sr), np.float32)); t += gap
    wav = out_mp3[:-4] + '.wav'; sf.write(wav, np.concatenate(chunks[:-1]), sr)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', wav, '-b:a', '160k', out_mp3], check=True); os.remove(wav)
    return align(segs)

def align(segs):
    """[(scene_text, start, end, [(token, t0, t1)])] -> ElevenLabs-style alignment for SEP.join(scene texts)"""
    import numpy as np
    chars, st, en = [], [], []
    for i, (scene, a, b, toks) in enumerate(segs):
        idx, times, pos = [0], [a], 0  # anchors: (char index, time), scene start first
        for word, t0, t1 in toks:  # pin each spoken token to its place in the text
            k = scene.find(word, pos)
            if k < 0 or not word or t0 < times[-1]: continue
            idx += [k, k + len(word)]; times += [t0, max(t0, t1)]; pos = k + len(word)
        idx.append(len(scene)); times.append(max(b, times[-1]))
        # every character between anchors is interpolated, so times never run backwards
        s = np.interp(np.arange(len(scene)), idx, times).tolist(); e = np.interp(np.arange(1, len(scene) + 1), idx, times).tolist()
        chars += list(scene); st += s; en += e
        if i < len(segs) - 1: chars += list(SEP); st += [b] * len(SEP); en += [b] * len(SEP)
    return {'characters': chars, 'character_start_times_seconds': st, 'character_end_times_seconds': en}

# ------------------------------------------------------------------ ElevenLabs
def _elevenlabs(text, cfg, out_mp3):
    key, voice = cfg.get('ELEVENLABS_API_KEY'), cfg.get('ELEVENLABS_VOICE_ID')
    if not key or not voice:
        raise RuntimeError('Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in config.env')
    body = {'text': text, 'model_id': cfg['ELEVENLABS_MODEL_ID'],
            'voice_settings': {'stability': float(cfg['ELEVENLABS_STABILITY']), 'similarity_boost': float(cfg['ELEVENLABS_SIMILARITY']),
                               'speed': float(cfg['ELEVENLABS_SPEED'])}}
    for attempt in range(3):
        r = requests.post(API.format(voice=voice), params={'output_format': 'mp3_44100_128'},
                          headers={'xi-api-key': key, 'Content-Type': 'application/json'}, json=body, timeout=300)
        if r.status_code == 200: break
        if r.status_code in (429, 500, 502, 503) and attempt < 2: time.sleep(20 * (attempt + 1)); continue
        raise RuntimeError(f'ElevenLabs error {r.status_code}: {r.text[:400]}')
    data = r.json()
    with open(out_mp3, 'wb') as f: f.write(base64.b64decode(data['audio_base64']))
    return data.get('normalized_alignment') if not data.get('alignment') else data['alignment']

def characters_left(cfg):
    """ElevenLabs free-tier budget check (None if unknown or not using ElevenLabs)"""
    if provider(cfg) != 'elevenlabs': return None
    try:
        r = requests.get('https://api.elevenlabs.io/v1/user/subscription', headers={'xi-api-key': cfg['ELEVENLABS_API_KEY']}, timeout=30)
        d = r.json(); return d['character_limit'] - d['character_count']
    except Exception:
        return None
