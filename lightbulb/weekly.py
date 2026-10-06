"""The Sunday job: next episode -> voice -> video + shorts + thumbnail -> YouTube draft (or upload folder) -> phone ping.

  python3 -m lightbulb.weekly                 # normal weekly run
  python3 -m lightbulb.weekly --episode ep02  # a specific episode (even if already done)
  python3 -m lightbulb.weekly --dry-run       # show what would run, spend nothing
  python3 -m lightbulb.weekly --quick         # low-cost test: first 3 scenes only, no upload
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time, traceback
from datetime import datetime
from .config import load, truthy
from .core import ROOT
from . import engine as E, video as V, thumbnail as T, notify as N

EPISODES = os.path.join(ROOT, 'episodes')

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def audio_len(path):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip())

def state_path(cfg): return os.path.join(cfg['LBL_OUTPUT'], 'state.json')
def load_state(cfg):
    p = state_path(cfg); return json.load(open(p)) if os.path.exists(p) else {'done': {}}
def save_state(cfg, st):
    os.makedirs(cfg['LBL_OUTPUT'], exist_ok=True); json.dump(st, open(state_path(cfg), 'w'), indent=1)

def all_episodes():
    eps = []
    for p in sorted(glob.glob(os.path.join(EPISODES, 'ep*.json'))):
        e = json.load(open(p)); e['_path'] = p; eps.append(e)
    return sorted(eps, key=lambda e: e['number'])

def pick(cfg, want=None):
    st = load_state(cfg)
    for e in all_episodes():
        if want:
            if e['id'] == want: return e
        elif e.get('status', 'ready') == 'ready' and e['id'] not in st['done']: return e
    return None

def load_links():
    p = os.path.join(ROOT, 'links.json')
    return json.load(open(p)) if os.path.exists(p) else {}

def link_lines(ep, short=False):
    L = load_links(); out = []
    if L.get('website'): out.append(f"\U0001F4D8 {L['website']['label']}: {L['website']['url']}")
    series = ep.get('series', 'Tech from Scratch')
    guides = [g for g in L.get('guides', []) if not g.get('series') or series in g['series']]
    for g in guides[:1 if short else 3]: out.append(f"\U0001F4CB {g['label']}: {g['url']}")
    return out

def description(ep, cfg):
    d = ep.get('description', '').strip()
    lines = [d, ''] if d else []
    links = link_lines(ep)
    if links: lines += links + ['']
    if ep.get('chapters'): lines += ['Chapters:'] + ep['chapters'] + ['']
    lines += [f"{ep.get('series', 'Tech from Scratch')} is a beginner-friendly series that explains everyday tech from the ground up, one short episode at a time.", '',
              'New episodes every week. Subscribe so you don\u2019t miss the next one.', '',
              'Kip\u2019s voice is AI-generated with ElevenLabs. Animation made with code by Lightbulb Lab.',
              'Music: "Nebula" by The Grey Room / Density & Time, from the YouTube Audio Library.', '',
              f"TikTok: {load_links().get('tiktok', '@lightbulblab')}", '', '#techforbeginners #learntech #techfromscratch']
    return '\n'.join(lines)

def chapters(ep, epi):
    """YouTube chapters from each card block's start (first must be 0:00)"""
    out = ['0:00 Intro']
    for blk in epi.cards:
        title = blk['spec'].get('title') or blk['spec'].get('text') or ''
        title = title.split(':')[0].strip().rstrip('.').title() if title.isupper() or ':' in title else title.rstrip('.')
        t = max(0, blk['t0']); stamp = f'{int(t // 60)}:{int(t % 60):02d}'
        if t > 10 and title and stamp != out[-1].split()[0] and len(out) < 12: out.append(f'{stamp} {title}')
    return out if len(out) >= 3 else []

def srt(epi, path, t0=0.0, t1=None):
    caps = [(t, s) for t, s in epi.caps]; end = epi.audio_len + E.OFFSET + 0.3; rows = []
    for i, (t, s) in enumerate(caps):
        e = caps[i + 1][0] if i + 1 < len(caps) else end
        if t1 is not None and (e <= t0 or t >= t1): continue
        a, b = max(t, t0) - t0, (min(e, t1) if t1 else e) - t0
        f = lambda x: f'{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(x * 1000 % 1000):03d}'
        rows.append(f'{len(rows) + 1}\n{f(a)} --> {f(b)}\n{s}\n')
    open(path, 'w').write('\n'.join(rows))

def run(cfg, ep, quick=False, dry=False):
    t_start = time.time(); workers = int(cfg['LBL_WORKERS'])
    if quick: ep = dict(ep, scenes=ep['scenes'][:3], shorts=[{'hook': 'Quick test', 'scenes': [0, 1]}])
    name = f"{ep['id']}-{slug(ep['title'])}"; out = os.path.join(cfg['LBL_OUTPUT'], name + ('-quicktest' if quick else ''))
    work = os.path.join(out, 'work'); os.makedirs(work, exist_ok=True)
    text = E.full_text(ep); print(f'[{name}] {len(ep["scenes"])} scenes, {len(text)} characters')
    # ---- voice: a hand-made file in episodes/audio/ wins (free fallback), else the ElevenLabs API
    manual = next((p for p in (os.path.join(EPISODES, 'audio', ep['id'] + x) for x in ('.mp3', '.wav')) if os.path.exists(p)), None)
    mp3, al = os.path.join(work, 'voice.mp3'), os.path.join(work, 'voice.json')
    if dry:
        print('dry run: voice from', manual or 'ElevenLabs API', '->', out); return None
    if manual and not quick:
        shutil.copy(manual, mp3); timing = E.Timing.from_pauses(text, E.scene_text(ep), mp3); print('voice: using', manual)
    elif os.path.exists(mp3) and os.path.exists(al) and json.load(open(al)).get('text') == text:
        timing = E.Timing.from_alignment(text, json.load(open(al))['alignment']); print('voice: reusing earlier take')
    else:
        from . import voice as VO
        left = VO.characters_left(cfg)
        if left is not None and left < len(text):
            raise RuntimeError(f'ElevenLabs free credits too low this month ({left} left, need {len(text)}). '
                               f'Record it in the ElevenLabs website and save it as episodes/audio/{ep["id"]}.mp3, then rerun.')
        VO.synthesize(text, cfg, mp3, al); timing = E.Timing.from_alignment(text, json.load(open(al))['alignment']); print('voice: generated')
    epi = E.Episode(ep, timing, audio_len(mp3)); epi.set_audio(mp3)
    # ---- audio + video
    mix = os.path.join(work, 'mix.wav'); V.mix_audio(epi, mp3, mix)
    main = os.path.join(out, f'{name}.mp4'); print(f'rendering {epi.dur:.0f}s on {workers} cores...'); V.render_main(epi, mix, main, work, workers)
    shorts = []
    for i, sh in enumerate(ep.get('shorts', []), 1):
        p = os.path.join(out, f'short{i}-{slug(sh["hook"])[:40]}.mp4'); V.render_short(epi, sh, mix, p, work, workers); shorts.append((sh, p))
    th = ep.get('thumbnail', {}); tl = ep['title'].rstrip('?').split()
    thumb = T.make(th.get('line1', ' '.join(tl[:len(tl) // 2]).upper() or 'TECH'), th.get('line2', ' '.join(tl[len(tl) // 2:]).upper() + ('?' if ep['title'].endswith('?') else '')),
                   th.get('sub1', ep.get('series', 'Tech from Scratch')), th.get('sub2', f"Episode {ep['number']}"), os.path.join(out, f'{name}-thumbnail.jpg'))
    # ---- metadata
    if not ep.get('chapters'): ep = dict(ep, chapters=chapters(ep, epi))
    title = ep.get('youtube_title') or f"{ep['title']} | {ep.get('series', 'Tech from Scratch')} Ep. {ep['number']}"
    desc = description(ep, cfg); tags = ep.get('tags', []) + ['tech for beginners', 'computer basics', 'Lightbulb Lab', 'Tech from Scratch']
    srt(epi, os.path.join(out, f'{name}.en.srt'))
    meta = {'title': title, 'description': desc, 'tags': tags, 'shorts': []}
    for sh, p in shorts:
        a, b = V.short_range(epi, sh); srt(epi, p[:-4] + '.en.srt', a, b)
        meta['shorts'].append({'file': os.path.basename(p), 'title': f"{sh['hook']} #shorts", 'description': f"From {title}. Full episode on @LightbulbLabYT.\n\n" + '\n'.join(link_lines(ep, short=True)) + "\n\nKip’s voice is AI-generated (ElevenLabs).\n\n#techforbeginners #shorts"})
    json.dump(meta, open(os.path.join(out, 'metadata.json'), 'w'), indent=1)
    with open(os.path.join(out, 'UPLOAD-ME.txt'), 'w') as f:
        f.write(f'TITLE\n{title}\n\nDESCRIPTION\n{desc}\n\nTAGS\n{", ".join(tags)}\n\nSETTINGS\nAudience: No, not made for kids | Category: Education | Playlist: {ep.get("series", "Tech from Scratch")}\n'
                f'Thumbnail: {os.path.basename(thumb)} | Subtitles: {name}.en.srt\n\nSHORTS / TIKTOK\n' + '\n'.join(f"{s['file']}: {s['title']}" for s in meta['shorts']) + '\n')
    shutil.rmtree(work, ignore_errors=True) if not quick else None
    # ---- YouTube (private draft) or leave the folder
    link = None
    if truthy(cfg['YOUTUBE_UPLOAD']) and not quick:
        from . import youtube as YT
        vid = YT.upload(cfg, main, title, desc, tags, cfg['YOUTUBE_PRIVACY'], thumbnail=thumb, playlist_id=cfg.get('YOUTUBE_PLAYLIST_ID'))
        link = f'https://studio.youtube.com/video/{vid}/edit'
        for s, (sh, p) in zip(meta['shorts'], shorts): YT.upload(cfg, p, s['title'], s['description'], tags, cfg['YOUTUBE_PRIVACY'])
    mins = (time.time() - t_start) / 60
    return {'id': ep['id'], 'title': title, 'folder': out, 'link': link, 'minutes': round(mins, 1), 'shorts': len(shorts)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--episode'); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--quick', action='store_true')
    a = ap.parse_args(); cfg = load()
    ep = pick(cfg, a.episode)
    if not ep:
        N.send(cfg, 'Lightbulb Lab: nothing to make', 'No ready episodes left in episodes/. Add the next script.', priority='high'); return 1
    try:
        r = run(cfg, ep, quick=a.quick, dry=a.dry_run)
    except Exception as e:
        traceback.print_exc(); N.send(cfg, f"Lightbulb Lab: {ep['id']} failed", f'{type(e).__name__}: {e}'[:900], priority='high'); return 1
    if not r: return 0
    if not a.quick:
        st = load_state(cfg); st['done'][ep['id']] = {'when': datetime.now().isoformat(timespec='minutes'), **r}; save_state(cfg, st)
    left = len([e for e in all_episodes() if e.get('status', 'ready') == 'ready' and e['id'] not in load_state(cfg)['done']])
    where = 'Draft is in YouTube Studio (private).' if r['link'] else f"Ready to upload: {r['folder']}"
    N.send(cfg, f"Lightbulb Lab: {r['title']}", f"{where}\n{r['shorts']} shorts made in {r['minutes']} min. Scripts left in the queue: {left}.", url=r['link'])
    print(json.dumps(r, indent=1)); return 0

if __name__ == '__main__': sys.exit(main())
