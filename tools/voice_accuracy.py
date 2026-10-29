"""Narrate episodes with Kip's voice recipe and check them with Whisper (proposal section 8.1 and 6.3).

Evaluation only; not used by the pipeline yet. Runs in the voice environment:
  pip install torch kokoro soundfile faster-whisper   (Whisper base.en model is about 145 MB on first run)
  python tools/voice_accuracy.py ep03 ep06 fif05 fif08 fif10
Writes one WAV, transcript and word-level diff per episode, plus report.json, to output/voice-eval/accuracy/.
Pass condition: word error rate <= 5% per episode.
"""
import glob, json, os, re, sys, time
import numpy as np, soundfile as sf
from kokoro import KPipeline
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'output', 'voice-eval', 'accuracy')
RECIPE = json.load(open(os.path.join(ROOT, 'assets', 'voice', 'kip.json'), encoding='utf-8'))
MAX_WER = 0.05

ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()

def say_int(n):
    if n < 20: return ONES[n]
    if n < 100: return TENS[n // 10] + ('' if n % 10 == 0 else ' ' + ONES[n % 10])
    if n < 1000: return ONES[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' ' + say_int(n % 100))
    return say_int(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + say_int(n % 1000))

def say_number(tok):
    if '-' in tok:  # phone numbers: 1-800-633-4227 is read "one eight hundred six three three four two two seven"
        return ' '.join(say_int(int(p)) if p in ('1', '800') else ' '.join(ONES[int(d)] for d in p) for p in tok.split('-') if p)
    n = int(tok)
    if 2000 < n < 2100: return 'twenty ' + say_int(n % 100)  # years: twenty twenty seven
    return say_int(n)

ORD = {'one': 'first', 'two': 'second', 'three': 'third', 'five': 'fifth', 'eight': 'eighth', 'nine': 'ninth', 'twelve': 'twelfth'}

def ordinal(n):
    w = say_int(n).split(); last = w[-1]
    w[-1] = ORD.get(last) or (last[:-1] + 'ieth' if last.endswith('y') else last + 'th')
    return ' '.join(w)

def words(text):
    """Normalize script or transcript text to comparable lowercase words."""
    t = text.lower().replace('’', "'")
    t = re.sub(r'(?<=[a-z])\.(?=[a-z])', ' dot ', t)          # ftc.gov -> ftc dot gov
    t = re.sub(r'\b(\d+)(st|nd|rd|th)\b', lambda m: ' ' + ordinal(int(m.group(1))) + ' ', t)  # 15th -> fifteenth
    t = re.sub(r'\d+(?:-\d+)+|\d+', lambda m: ' ' + say_number(m.group()) + ' ', t)
    t = re.sub(r'(?<=[a-z])-(?=[a-z])', '', t)                # wi-fi -> wifi
    out = []
    for w in (w.strip("'") for w in re.findall(r"[a-z']+", t)):
        letter = len(w) == 1 and w not in ('a', 'i')
        if letter and out and out[-1][1]: out[-1][0] += w      # f t c -> ftc
        elif w: out.append([w, letter])
    return [w for w, _ in out]

def align(ref, hyp):
    d = [[j for j in range(len(hyp) + 1)]] + [[i] + [0] * len(hyp) for i in range(1, len(ref) + 1)]
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (ref[i-1] != hyp[j-1]))
    i, j, ops = len(ref), len(hyp), []
    while i or j:
        if i and j and d[i][j] == d[i-1][j-1] + (ref[i-1] != hyp[j-1]):
            if ref[i-1] != hyp[j-1]: ops.append(f'{ref[i-1]} -> {hyp[j-1]}')
            i, j = i - 1, j - 1
        elif i and d[i][j] == d[i-1][j] + 1: ops.append(f'missing: {ref[i-1]}'); i -= 1
        else: ops.append(f'extra: {hyp[j-1]}'); j -= 1
    return d[len(ref)][len(hyp)], ops[::-1]

def spoken(text):
    for k, v in RECIPE['spoken_forms'].items(): text = text.replace(k, v)
    return text

def main(ids):
    os.makedirs(OUT, exist_ok=True)
    pipe = KPipeline(lang_code=RECIPE['lang_code'])
    voice = sum(pipe.load_voice(v) * w for v, w in RECIPE['blend'].items())
    asr = WhisperModel('base.en', device='cpu', compute_type='int8')
    sr, gap, report = RECIPE['sample_rate'], RECIPE['scene_gap_s'], {}
    for eid in ids:
        path = glob.glob(os.path.join(ROOT, 'episodes', eid + '-*.json'))[0]
        e = json.load(open(path, encoding='utf-8'))
        script = ' '.join(s['say'] for s in e['scenes'])
        t0, chunks = time.time(), []
        for s in e['scenes']:
            for r in pipe(spoken(s['say']), voice=voice, speed=RECIPE['speed']):
                chunks.append(r.audio.numpy() if hasattr(r.audio, 'numpy') else np.asarray(r.audio))
            chunks.append(np.zeros(int(gap * sr), np.float32))
        audio = np.concatenate(chunks); tts_s = time.time() - t0
        wav = os.path.join(OUT, f'{eid}.wav'); sf.write(wav, audio, sr)
        x16 = np.interp(np.arange(0, len(audio), sr / 16000), np.arange(len(audio)), audio).astype(np.float32)  # Whisper wants 16 kHz; passing samples avoids PyAV
        segs, _ = asr.transcribe(x16, language='en', beam_size=5)
        heard = ' '.join(s.text.strip() for s in segs)
        ref, hyp = words(script), words(heard)
        errs, ops = align(ref, hyp)
        wer = errs / len(ref)
        open(os.path.join(OUT, f'{eid}.transcript.txt'), 'w', encoding='utf-8').write(heard + '\n')
        open(os.path.join(OUT, f'{eid}.diff.txt'), 'w', encoding='utf-8').write('\n'.join(ops) + '\n')
        report[eid] = {'audio_s': round(len(audio) / sr, 1), 'tts_s': round(tts_s, 1), 'words': len(ref),
                       'errors': errs, 'wer': round(wer, 4), 'pass': wer <= MAX_WER, 'diffs': ops}
        print(eid, {k: v for k, v in report[eid].items() if k != 'diffs'}, flush=True)
    json.dump({'recipe_version': RECIPE['version'], 'asr': 'faster-whisper base.en', 'max_wer': MAX_WER, 'episodes': report},
              open(os.path.join(OUT, 'report.json'), 'w', encoding='utf-8'), indent=1)
    return 0 if all(r['pass'] for r in report.values()) else 1

if __name__ == '__main__': sys.exit(main(sys.argv[1:] or ['ep03', 'ep06', 'fif05', 'fif08', 'fif10']))
