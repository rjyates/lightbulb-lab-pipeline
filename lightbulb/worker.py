"""The daily worker: keeps about three weeks of finished, checked videos scheduled on the publishing calendar.

  python3 -m lightbulb.worker          # one run; the systemd timer runs this every night
  python3 -m lightbulb.worker --plan   # show the next slots and episodes; renders and uploads nothing

Each run: hold anything due within 48 h that is paused, vetoed or has expired facts; mark past slots published;
then render, check and schedule new episodes until each series is booked BUFFER_DAYS ahead.
Pause everything:  touch <LBL_OUTPUT>/PAUSE.   Veto one episode:  touch <LBL_OUTPUT>/veto/<episode id>.
"""
import argparse, json, os, subprocess, sys, traceback
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .config import load, truthy
from . import weekly as W, notify as N, check as CK

# series -> weekday of the long-form episode and of its Shorts (Mon=0). The Monday news Short has its own workflow.
CALENDAR = {'Tech from Scratch': {'main': 1, 'shorts': [2, 3]}, 'Fix It Friday': {'main': 4, 'shorts': [5, 6]}}
HOUR, LEAD, RECHECK = 9, timedelta(days=2), timedelta(hours=48)

def tz(cfg): return ZoneInfo(cfg.get('LBL_TZ', 'America/Chicago'))
def buffer(cfg): return timedelta(days=int(cfg.get('LBL_BUFFER_DAYS', 21)))
def out_path(cfg, *p): return os.path.join(cfg['LBL_OUTPUT'], *p)
def queue_path(cfg): return cfg.get('LBL_QUEUE') or out_path(cfg, 'queue.json')
def load_queue(cfg): p = queue_path(cfg); return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []
def save_queue(cfg, q):
    p = queue_path(cfg); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(q, open(p, 'w', encoding='utf-8'), indent=1)
def paused(cfg): return os.path.exists(cfg.get('LBL_PAUSE') or out_path(cfg, 'PAUSE'))
def vetoed(cfg, ep_id): return os.path.exists(out_path(cfg, 'veto', ep_id))
def iso(dt): return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def when(s): return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)

def next_slot(cfg, q, series, now):
    """the next free long-form slot for a series: a week after its last booked one, else the first one at least LEAD away"""
    booked = [when(e['slots'][f"{e['id']}-main"]).astimezone(tz(cfg)) for e in q if e['series'] == series and e['status'] != 'held']
    if booked: return max(booked) + timedelta(days=7)  # local wall-clock arithmetic, so 9:00 stays 9:00 across daylight-saving changes
    t = (now + LEAD).astimezone(tz(cfg)); day = t + timedelta(days=(CALENDAR[series]['main'] - t.weekday()) % 7)
    slot = day.replace(hour=HOUR, minute=0, second=0, microsecond=0)
    return slot if slot >= now + LEAD else slot + timedelta(days=7)

def slots(ep_id, series, main_dt, n_shorts):
    cal = CALENDAR[series]; out = {f'{ep_id}-main': iso(main_dt)}
    for i in range(n_shorts):  # more Shorts than calendar days: one per day after the last listed day
        day = cal['shorts'][i] if i < len(cal['shorts']) else cal['shorts'][-1] + i - len(cal['shorts']) + 1
        out[f'{ep_id}-short{i + 1}'] = iso(main_dt + timedelta(days=(day - cal['main']) % 7))
    return out

def candidate(cfg, q, series):
    taken, done = {e['id'] for e in q}, W.load_state(cfg)['done']
    return next((e for e in W.all_episodes() if e.get('series') == series and e.get('status', 'ready') in ('ready', 'approved')
                 and e['id'] not in taken and e['id'] not in done), None)

def hold_reasons(cfg, entry):
    reasons = ['publishing is paused'] if paused(cfg) else []
    if vetoed(cfg, entry['id']): reasons.append('vetoed by the owner')
    ep = next((e for e in W.all_episodes() if e['id'] == entry['id']), None)
    live = when(entry['slots'][f"{entry['id']}-main"]).astimezone(tz(cfg)).date()
    reasons += CK.check_facts(ep, today=live)[0] if ep else ['episode file is gone']  # facts must still be true on the day it goes live
    return reasons

def run_once(cfg, now=None, produce=None, publish=None, unschedule=None, notify=None):
    """one worker pass. The keyword arguments exist so tests can run it without rendering or YouTube."""
    now = now or datetime.now(timezone.utc); notify = notify or (lambda t, m: N.send(cfg, t, m, priority='high'))
    if publish is None or unschedule is None:
        from . import youtube as YT
        publish, unschedule = publish or YT.publish_once, unschedule or YT.unschedule
    produce = produce or (lambda c, ep: W.run(c, ep, upload=False))
    q, report = load_queue(cfg), {'held': [], 'published': [], 'scheduled': [], 'failed': []}
    # 1. last look before anything goes live
    for e in q:
        if e['status'] == 'scheduled' and when(e['slots'][f"{e['id']}-main"]) - now <= RECHECK:
            reasons = hold_reasons(cfg, e)
            if reasons:
                for vid in e['videos'].values(): unschedule(cfg, vid)
                e['status'], e['held_because'] = 'held', reasons; report['held'].append(e['id'])
                notify(f"Lightbulb Lab: held {e['id']}", 'Kept private: ' + '; '.join(reasons)[:800])
    # 2. slots that have passed are live now
    for e in q:
        if e['status'] == 'scheduled' and all(when(t) <= now for t in e['slots'].values()):
            e['status'] = 'published'; report['published'].append(e['id'])
            st = W.load_state(cfg); st['done'][e['id']] = {'when': e['slots'][f"{e['id']}-main"], 'folder': e['folder']}; W.save_state(cfg, st)
    save_queue(cfg, q)
    # 3. keep each series booked ahead
    if paused(cfg): return report
    upload = truthy(cfg.get('YOUTUBE_UPLOAD', 'false'))
    for series in CALENDAR:
        while (slot := next_slot(cfg, q, series, now)) < now + buffer(cfg):
            ep = candidate(cfg, q, series)
            if not ep:
                if slot < now + timedelta(days=14): notify(f'Lightbulb Lab: {series} has no scripts left', f'Nothing approved to fill {slot.astimezone(tz(cfg)):%a %b %d}.')
                break
            try:
                r = produce(cfg, ep)
                plan = slots(ep['id'], series, slot, len(r['short_files']))
                entry = {'id': ep['id'], 'series': series, 'folder': r['folder'], 'slots': plan, 'videos': {}, 'status': 'scheduled' if upload else 'awaiting-manual-upload'}
                q.append(entry); save_queue(cfg, q)
                if upload:
                    files = [r['main']] + r['short_files']; meta = r['meta']
                    texts = [(meta['title'], meta['description'])] + [(s['title'], s['description']) for s in meta['shorts']]
                    for (key, at), path, (title, desc) in zip(plan.items(), files, texts):
                        main = key.endswith('-main')
                        entry['videos'][key] = publish(cfg, key, path, title, desc, r['tags'], publish_at=at, captions=path[:-4] + '.en.srt',
                                                       thumbnail=r['thumb'] if main else None, playlist_id=cfg.get('YOUTUBE_PLAYLIST_ID') if main else None)
                        save_queue(cfg, q)
                else:
                    notify(f"Lightbulb Lab: {ep['id']} ready to upload", f"Uploads are off. Folder: {r['folder']}\nPlanned slot: {slot.astimezone(tz(cfg)):%a %b %d %H:%M}")
                report['scheduled'].append(ep['id'])
            except Exception as ex:
                traceback.print_exc(); report['failed'].append(ep['id'])
                notify(f"Lightbulb Lab: {ep['id']} failed", f'{type(ex).__name__}: {ex}'[:900])
                break  # leave this series for tomorrow rather than skipping ahead to the next script
    return report

def sync_ops(cfg, message):
    """commit the queue and ledger to the private ops repo, if one is configured"""
    repo = cfg.get('LBL_OPS_REPO')
    if not repo: return
    git = lambda *a: subprocess.run(['git', '-C', repo, *a], capture_output=True, text=True)
    git('add', '-A')
    if git('diff', '--cached', '--quiet').returncode: git('commit', '-m', message); r = git('push', '-q')
    else: return
    if r.returncode: print('ops repo push failed:', r.stderr[:300])

def plan(cfg, now=None):
    now = now or datetime.now(timezone.utc); q = load_queue(cfg)
    print('PAUSED' if paused(cfg) else 'active', '| buffer', buffer(cfg).days, 'days | uploads', 'on' if truthy(cfg.get('YOUTUBE_UPLOAD', 'false')) else 'off')
    for e in q: print(f"  {e['status']:<24} {e['id']:<7} {when(e['slots'][e['id'] + '-main']).astimezone(tz(cfg)):%a %b %d %H:%M}")
    for series in CALENDAR:
        ep = candidate(cfg, q, series)
        print(f"next {series}: {ep['id'] if ep else 'NO SCRIPT'} -> {next_slot(cfg, q, series, now).astimezone(tz(cfg)):%a %b %d %H:%M}")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--plan', action='store_true'); a = ap.parse_args(); cfg = load()
    if a.plan: plan(cfg); return 0
    repo = cfg.get('LBL_OPS_REPO')
    if repo: subprocess.run(['git', '-C', repo, 'pull', '-q', '--ff-only'])
    r = run_once(cfg); print(json.dumps(r)); sync_ops(cfg, f"worker: {datetime.now(timezone.utc):%Y-%m-%d} {json.dumps(r)}")
    return 1 if r['failed'] else 0

if __name__ == '__main__': sys.exit(main())
