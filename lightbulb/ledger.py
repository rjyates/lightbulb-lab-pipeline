"""Append-only record of publish attempts, so a crash or rerun never uploads the same video twice.

One JSON line per event: {"key": "ep03-main", "event": "intent" | "result", "when": ..., ...}.
LBL_LEDGER sets the file (default: <LBL_OUTPUT>/ledger/videos.jsonl); point it at the private ops repo on the worker.
"""
import json, os
from datetime import datetime, timezone

def path(cfg): return cfg.get('LBL_LEDGER') or os.path.join(cfg['LBL_OUTPUT'], 'ledger', 'videos.jsonl')

def records(cfg, key=None):
    p = path(cfg)
    if not os.path.exists(p): return []
    rows = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    return [r for r in rows if key is None or r['key'] == key]

def append(cfg, key, event, **fields):
    p = path(cfg); os.makedirs(os.path.dirname(p), exist_ok=True)
    rec = {'key': key, 'event': event, 'when': datetime.now(timezone.utc).isoformat(timespec='seconds'), **fields}
    with open(p, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec) + '\n'); f.flush(); os.fsync(f.fileno())  # must hit disk before the API call it guards
    return rec

def state(cfg, key):
    """('none' | 'pending' | 'done', video_id)"""
    rs = records(cfg, key)
    done = next((r for r in reversed(rs) if r['event'] == 'result'), None)
    if done: return 'done', done['video_id']
    return ('pending' if rs else 'none'), None
