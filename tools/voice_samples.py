"""Render Kip voice candidates with Kokoro (local, offline after the first model download).

Evaluation only (milestone M0, see docs/autonomy/proposal.md section 8.1); not used by the pipeline.
Needs its own environment:  pip install torch kokoro soundfile  (downloads about 330 MB of model files on first run)
  python tools/voice_samples.py
Writes one WAV per blend plus word timings and render times to output/voice-eval/.
"""
import json, os, sys, time
import numpy as np, soundfile as sf
from kokoro import KPipeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, 'output', 'voice-eval')
SR, GAP = 24000, 0.55  # Kokoro sample rate; pause between scenes, like " ... " in the pipeline

BLENDS = {  # name: ({voice: weight}, speed)
    'A-bright': ({'af_heart': 0.5, 'am_puck': 0.5}, 1.0),
    'B-warm': ({'af_heart': 0.4, 'am_michael': 0.6}, 0.97),
    'C-playful': ({'am_puck': 0.7, 'af_sky': 0.3}, 1.0),
    'D-crisp': ({'af_bella': 0.5, 'am_echo': 0.5}, 1.0),
}

def scenes():
    out = []
    for f, n in (('ep03-what-is-the-internet.json', 4), ('fif05-wi-fi-connected-but-no-internet.json', 2)):
        e = json.load(open(os.path.join(ROOT, 'episodes', f), encoding='utf-8'))
        out += [s['say'] for s in e['scenes'][:n]]
    return out

def main():
    os.makedirs(HERE, exist_ok=True)
    pipe = KPipeline(lang_code='a')  # American English
    text, report = scenes(), {}
    for name, (mix, speed) in BLENDS.items():
        voice = sum(pipe.load_voice(v) * w for v, w in mix.items())
        t0, chunks, words, at = time.time(), [], [], 0.0
        for say in text:
            for r in pipe(say, voice=voice, speed=speed):
                a = r.audio.numpy() if hasattr(r.audio, 'numpy') else np.asarray(r.audio)
                for tk in r.tokens or []:
                    if tk.start_ts is not None: words.append([tk.text, round(at + tk.start_ts, 3), round(at + (tk.end_ts or tk.start_ts), 3)])
                chunks.append(a); at += len(a) / SR
            chunks.append(np.zeros(int(GAP * SR), np.float32)); at += GAP
        audio = np.concatenate(chunks)
        sf.write(os.path.join(HERE, f'kip-{name}.wav'), audio, SR)
        json.dump(words, open(os.path.join(HERE, f'kip-{name}.words.json'), 'w'), indent=0)
        report[name] = {'mix': mix, 'speed': speed, 'seconds': round(len(audio) / SR, 1), 'render_s': round(time.time() - t0, 1), 'words_timed': len(words)}
        print(name, report[name], flush=True)
    json.dump(report, open(os.path.join(HERE, 'report.json'), 'w'), indent=1)

if __name__ == '__main__': sys.exit(main())
