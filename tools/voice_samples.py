"""Render Kip voice candidates with the pipeline's own Kokoro provider, so the owner can choose by ear.

Evaluation only (docs/autonomy/proposal.md section 8.1). Needs requirements-voice.txt and ffmpeg; downloads about 330 MB of model files on first run.
  python tools/voice_samples.py
Writes kip-<blend>.mp3 plus voice.json timing and a report.json with render times to output/voice-eval/.
Put the chosen blend in config.env as KOKORO_VOICE (and KOKORO_SPEED).
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lightbulb import voice as VO
from lightbulb.core import ROOT

HERE = os.path.join(ROOT, 'output', 'voice-eval')
BLENDS = {  # name: (KOKORO_VOICE, KOKORO_SPEED)
    'A-bright': ('af_heart:0.5,am_puck:0.5', '1.0'),
    'B-warm': ('af_heart:0.4,am_michael:0.6', '0.97'),
    'C-playful': ('am_puck:0.7,af_sky:0.3', '1.0'),
    'D-crisp': ('af_bella:0.5,am_echo:0.5', '1.0'),
}

def scenes():
    out = []
    for f, n in (('ep03-what-is-the-internet.json', 4), ('fif05-wi-fi-connected-but-no-internet.json', 2)):
        e = json.load(open(os.path.join(ROOT, 'episodes', f), encoding='utf-8'))
        out += [s['say'].strip() for s in e['scenes'][:n]]
    return out

def main():
    os.makedirs(HERE, exist_ok=True); text, report = VO.SEP.join(scenes()), {}
    for name, (blend, speed) in BLENDS.items():
        cfg, t0 = {'LBL_VOICE': 'kokoro', 'KOKORO_VOICE': blend, 'KOKORO_SPEED': speed}, time.time()
        mp3 = os.path.join(HERE, f'kip-{name}.mp3'); VO.synthesize(text, cfg, mp3, mp3[:-4] + '.voice.json')
        al = json.load(open(mp3[:-4] + '.voice.json'))['alignment']
        report[name] = {'voice': blend, 'speed': speed, 'seconds': round(al['character_end_times_seconds'][-1], 1), 'render_s': round(time.time() - t0, 1)}
        print(name, report[name], flush=True)
    json.dump(report, open(os.path.join(HERE, 'report.json'), 'w'), indent=1)

if __name__ == '__main__': sys.exit(main())
