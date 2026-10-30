"""Quality gates: nothing is uploaded unless every check here passes (docs/autonomy/proposal.md section 6).

  python3 -m lightbulb.gates output/ep03-what-is-the-internet   # show a folder's QA result
gate() writes qa-report.json and contact-*.jpg into the episode folder; verify() is the upload lock.
"""
import hashlib, json, os, re, subprocess, sys
from urllib.parse import urlparse
from PIL import Image

REPORT = 'qa-report.json'
MAIN, SHORT = (1920, 1080), (1080, 1920)
EDGE = 0.4  # black or frozen frames touching the start or end are intentional fades and end cards

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def ok(name, passed, detail=''): return {'check': name, 'pass': bool(passed), 'detail': detail}

# ------------------------------------------------------------------ video and audio
def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout else None

def scan(path):
    """one decode pass: black, frozen and silent stretches, loudness, and whether the file decodes cleanly"""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-vf', 'blackdetect=d=0.5:pix_th=0.10,freezedetect=n=0.003:d=4',
                        '-af', 'silencedetect=n=-50dB:d=2.5,ebur128=peak=true:framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True)
    log = r.stderr; num = lambda pat: [float(x) for x in re.findall(pat, log)]
    pair = lambda a, b: list(zip(num(a), num(b) + [None] * (len(num(a)) - len(num(b)))))  # a stretch running to the end has no end line
    return {'decoded': r.returncode == 0 and not re.search(r'error while decoding|invalid data|corrupt', log, re.I), 'black': pair(r'black_start:([\d.]+)', r'black_end:([\d.]+)'),
            'frozen': pair(r'freeze_start: ([\d.]+)', r'freeze_end: ([\d.]+)'), 'silent': pair(r'silence_start: ([-\d.]+)', r'silence_end: ([\d.]+)'),
            'lufs': (num(r'I:\s+(-?[\d.]+) LUFS') or [None])[-1], 'peak': (num(r'Peak:\s+(-?[\d.]+) dBFS') or [None])[-1]}

def media(path, size, expect=None, max_len=None):
    """technical checks for one video. expect: intended duration in seconds"""
    info = probe(path)
    if not info: return [ok('readable', False, 'ffprobe could not read the file')]
    v = next((s for s in info['streams'] if s['codec_type'] == 'video'), {}); a = next((s for s in info['streams'] if s['codec_type'] == 'audio'), {})
    dur = float(info['format'].get('duration', 0)); vd, ad = float(v.get('duration', dur)), float(a.get('duration', 0))
    n, d = (int(x) for x in v.get('avg_frame_rate', '0/0').split('/')); fps = n / d if d else 0
    out = [ok('streams', v.get('codec_name') == 'h264' and v.get('pix_fmt') == 'yuv420p' and a.get('codec_name') == 'aac',
              f"video {v.get('codec_name')}/{v.get('pix_fmt')}, audio {a.get('codec_name')}"),
           ok('size', (v.get('width'), v.get('height')) == size, f"{v.get('width')}x{v.get('height')}, want {size[0]}x{size[1]}"),
           ok('frame rate', abs(fps - 30) < 0.01, f'{fps:.2f} fps'),
           ok('sync', abs(vd - ad) <= 0.1, f'video {vd:.2f}s, audio {ad:.2f}s')]
    if expect: out.append(ok('duration', abs(dur - expect) <= 0.03 * expect, f'{dur:.1f}s, expected {expect:.1f}s'))
    if max_len: out.append(ok('max length', dur <= max_len, f'{dur:.1f}s, limit {max_len}s'))
    s = scan(path); inside = lambda segs: [(a, b) for a, b in segs if a > EDGE and (b if b is not None else dur) < dur - EDGE]
    out += [ok('decodes cleanly', s['decoded']),
            ok('no black gaps', not inside(s['black']), str(inside(s['black']))),
            ok('no frozen picture', not inside(s['frozen']), str(inside(s['frozen']))),
            ok('no dead air', not inside(s['silent']), str(inside(s['silent']))),
            # shortcut: wide loudness band until real renders are measured; target is -14 LUFS, then tighten to +-1.5
            ok('loudness', s['lufs'] is not None and -20 <= s['lufs'] <= -10, f"{s['lufs']} LUFS"),
            ok('no clipping', s['peak'] is not None and s['peak'] <= -0.5, f"{s['peak']} dBFS peak")]
    return out

def contact_sheet(path, out_jpg, frames=12):
    dur = float(probe(path)['format']['duration'])
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', path, '-vf', f'fps={frames}/{dur:.3f},scale=480:-2,tile=4x{-(-frames // 4)}',
                    '-frames:v', '1', out_jpg], check=True)

# ------------------------------------------------------------------ captions, metadata, thumbnail
def captions(srt, video_dur):
    cues = []
    for block in open(srt, encoding='utf-8').read().strip().split('\n\n'):
        m = re.match(r'\d+\n(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)\n(.+)', block.strip(), re.S)
        if not m: return [ok('captions parse', False, f'bad cue: {block[:60]!r}')]
        g = [int(x) for x in m.groups()[:8]]
        cues.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, m.group(9).strip()))
    ordered = all(a < b for a, b, _ in cues) and all(cues[i][1] <= cues[i + 1][0] + 0.001 for i in range(len(cues) - 1))
    covered = sum(b - a for a, b, _ in cues) / video_dur if video_dur else 0
    return [ok('captions parse', bool(cues), f'{len(cues)} cues'), ok('captions in order', ordered),
            ok('captions have text', all(t for *_, t in cues)), ok('captions cover video', covered >= 0.85, f'{covered:.0%}')]

def allowed_hosts(links):
    hosts = {'youtube.com', 'www.youtube.com', 'youtu.be', 'studio.youtube.com', 'www.tiktok.com', 'tiktok.com'}
    for u in [links.get('website', {}).get('url', ''), links.get('tiktok', '')] + [g['url'] for g in links.get('guides', [])]: hosts.add(urlparse(u).hostname or '')
    return hosts - {''}

def metadata(title, description, tags, hosts):
    urls = re.findall(r'https?://[^\s)]+', description); bad = [u for u in urls if urlparse(u).hostname not in hosts]
    return [ok('title length', 0 < len(title) <= 100, f'{len(title)} chars'), ok('description length', len(description) <= 5000, f'{len(description)} chars'),
            ok('tags length', sum(len(t) for t in tags) + 2 * len(tags) <= 500, f'{len(tags)} tags'),  # YouTube counts quotes and commas too
            ok('links are our own', not bad, ', '.join(bad)),
            ok('AI voice disclosed', 'AI-generated' in description), ok('music credited', 'Music:' in description)]

def thumbnail(path):
    with Image.open(path) as im: size, fmt = im.size, im.format
    return [ok('thumbnail size', size == (1280, 720), f'{size[0]}x{size[1]}'), ok('thumbnail format', fmt == 'JPEG', fmt),
            ok('thumbnail under 2 MB', os.path.getsize(path) < 2_000_000, f'{os.path.getsize(path) // 1024} KB')]

# ------------------------------------------------------------------ report and lock
def gate(folder, main, shorts, thumb, meta, links, main_dur=None, short_durs=()):
    """run every check for one episode folder and write qa-report.json. shorts: [(path, expected_seconds)]"""
    hosts, checks = allowed_hosts(links), {}
    checks[os.path.basename(main)] = media(main, MAIN, main_dur) + captions(main[:-4] + '.en.srt', main_dur or float(probe(main)['format']['duration'])) \
        + metadata(meta['title'], meta['description'], meta['tags'], hosts)
    for (p, exp), sm in zip(shorts, meta['shorts']):
        checks[os.path.basename(p)] = media(p, SHORT, exp, max_len=60) + captions(p[:-4] + '.en.srt', exp) + metadata(sm['title'], sm['description'], meta['tags'], hosts)
    checks[os.path.basename(thumb)] = thumbnail(thumb)
    for i, p in enumerate([main] + [p for p, _ in shorts]):
        try: contact_sheet(p, os.path.join(folder, f'contact-{i}.jpg'))
        except Exception as e: checks[os.path.basename(p)].append(ok('contact sheet', False, str(e)[:200]))
    files = {os.path.basename(p): sha256(p) for p in [main, thumb] + [p for p, _ in shorts]}
    report = {'pass': all(c['pass'] for cs in checks.values() for c in cs), 'files': files, 'checks': checks}
    json.dump(report, open(os.path.join(folder, REPORT), 'w', encoding='utf-8'), indent=1)
    return report

def failures(report): return [f"{f}: {c['check']} ({c['detail']})" for f, cs in report['checks'].items() for c in cs if not c['pass']]

def verify(path):
    """upload lock: the file must be listed in a passing qa-report.json next to it, unchanged since it was checked"""
    rp = os.path.join(os.path.dirname(os.path.abspath(path)), REPORT)
    if not os.path.exists(rp): raise RuntimeError(f'{path}: no {REPORT}; run the quality gates first')
    rep = json.load(open(rp, encoding='utf-8')); name = os.path.basename(path)
    if not rep.get('pass'): raise RuntimeError(f'{path}: quality gates failed: ' + '; '.join(failures(rep))[:500])
    if rep.get('files', {}).get(name) != sha256(path): raise RuntimeError(f'{path}: changed since it passed the quality gates')

if __name__ == '__main__':
    folder = sys.argv[1]; rep = json.load(open(os.path.join(folder, REPORT), encoding='utf-8'))
    print('PASS' if rep['pass'] else 'FAIL'); [print('  ', x) for x in failures(rep)]
