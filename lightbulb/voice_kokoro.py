"""Kip's voice from Kokoro, an open-source model that runs offline (free, no character limit).

The voice recipe (blend, speed, model revision) lives in assets/voice/kip.json so every episode sounds the same.
Needs the voice extras:  pip install -r requirements-voice.txt  (about 330 MB of model files on first run).
Produces the same alignment JSON as the ElevenLabs provider, so timing, captions and reuse work unchanged.
"""
import json, os
import numpy as np
from .core import ROOT

RECIPE = os.path.join(ROOT, 'assets', 'voice', 'kip.json')
SEP = ' ... '  # matches engine.full_text

def recipe():
    return json.load(open(RECIPE, encoding='utf-8'))

def spoken(text, rec):
    """Rewrite words the model mispronounces (e.g. 2FA) before synthesis; timings still map to the script text."""
    for k, v in rec.get('spoken_forms', {}).items(): text = text.replace(k, v)
    return text

def align(scenes, words, spans):
    """Character timings for SEP.join(scenes).

    words: per scene, a list of (word, start, end) in seconds from the start of the episode audio.
    spans: per scene, (start, end) of that scene's audio.
    Characters inside a matched word get times spread across the word; everything else is interpolated.
    """
    text = SEP.join(scenes)
    st, en = np.full(len(text), np.nan), np.full(len(text), np.nan)
    pos = 0
    for i, (s, ws, (a, b)) in enumerate(zip(scenes, words, spans)):
        st[pos], en[pos + len(s) - 1] = a, b
        cur = 0
        for w, t0, t1 in ws:
            k = s.find(w, cur) if w else -1
            if k < 0: continue
            n = len(w); edges = np.linspace(t0, t1, n + 1)
            st[pos + k:pos + k + n], en[pos + k:pos + k + n] = edges[:-1], edges[1:]
            cur = k + n
        pos += len(s)
        if i < len(scenes) - 1:
            nxt = spans[i + 1][0]; edges = np.linspace(b, nxt, len(SEP) + 1)
            st[pos:pos + len(SEP)], en[pos:pos + len(SEP)] = edges[:-1], edges[1:]
            pos += len(SEP)
    idx = np.arange(len(text))
    for arr in (st, en):
        known = ~np.isnan(arr)
        arr[~known] = np.interp(idx[~known], idx[known], arr[known])
    st, en = np.maximum.accumulate(st), np.maximum.accumulate(en)
    return text, {'characters': list(text), 'character_start_times_seconds': st.round(3).tolist(),
                  'character_end_times_seconds': np.maximum(en, st).round(3).tolist()}

def synthesize(scenes, out_wav, out_json):
    try:
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError as e:
        raise RuntimeError('Kokoro is not installed: pip install -r requirements-voice.txt (or set LBL_VOICE=elevenlabs)') from e
    rec = recipe(); sr, gap = rec['sample_rate'], rec['scene_gap_s']
    pipe = KPipeline(lang_code=rec['lang_code'], repo_id=rec['model']['repo'])
    voice = sum(pipe.load_voice(v) * w for v, w in rec['blend'].items())
    chunks, words, spans, at = [], [], [], 0.0
    for s in scenes:
        start, ws = at, []
        for r in pipe(spoken(s, rec), voice=voice, speed=rec['speed']):
            a = r.audio.numpy() if hasattr(r.audio, 'numpy') else np.asarray(r.audio)
            ws += [(t.text, at + t.start_ts, at + (t.end_ts or t.start_ts)) for t in (r.tokens or []) if t.start_ts is not None]
            chunks.append(a); at += len(a) / sr
        words.append(ws); spans.append((start, at))
        chunks.append(np.zeros(int(gap * sr), np.float32)); at += gap
    sf.write(out_wav, np.concatenate(chunks), sr)
    text, al = align(scenes, words, spans)
    json.dump({'text': text, 'alignment': al, 'provider': 'kokoro', 'recipe_version': rec['version']},
              open(out_json, 'w', encoding='utf-8'))
    return out_wav, out_json
