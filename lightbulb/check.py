"""Check episode scripts before Sunday:  python3 -m lightbulb.check"""
import glob, json, os, sys
from datetime import date
from . import cards as C, engine as E
from .core import ROOT

# schema v2 lifecycle (docs/autonomy/proposal.md 4.4); 'ready' and 'done' are the original names for 'approved' and 'published'
STATUSES = ('idea', 'draft', 'reviewed', 'approved', 'produced', 'gated', 'scheduled', 'published', 'measured', 'blocked', 'retired', 'ready', 'done')
RELEASED = ('done', 'published', 'measured', 'retired')

def check_facts(e, today=None):
    """schema v2: sources, claims with expiry dates, sensitive flag. Returns (errors, warnings)."""
    errs, warn = [], []; today = today or date.today(); status = e.get('status', 'ready')
    if status not in STATUSES: errs.append(f'unknown status "{status}" (use {", ".join(STATUSES)})')
    if 'sensitive' in e and not isinstance(e['sensitive'], bool): errs.append('"sensitive" must be true or false')
    sources, claims = e.get('sources', []), e.get('claims', [])
    for i, s in enumerate(sources):
        if not isinstance(s, dict) or not str(s.get('url', '')).startswith(('https://', 'http://')): errs.append(f'source {i}: needs an http(s) "url"')
    for i, c in enumerate(claims):
        if not isinstance(c, dict) or not c.get('text'): errs.append(f'claim {i}: needs "text"'); continue
        if not (isinstance(c.get('source'), int) and 0 <= c['source'] < len(sources)): errs.append(f'claim {i}: "source" must be the index of an entry in "sources"')
        if not (isinstance(c.get('scene'), int) and 0 <= c['scene'] < len(e.get('scenes', []))): errs.append(f'claim {i}: "scene" out of range')
        if 'valid_until' in c:
            try: until = date.fromisoformat(c['valid_until'])
            except (TypeError, ValueError): errs.append(f'claim {i}: "valid_until" must be YYYY-MM-DD'); continue
            if until < today and status not in RELEASED:
                (warn if status in ('idea', 'draft') else errs).append(f'claim {i}: expired on {until} ("{c["text"][:50]}")')
    # new-vocabulary approvals must be sourced; original 'ready' episodes predate sources
    if status == 'approved' and not (sources and claims): errs.append('status "approved" needs "sources" and "claims"')
    return errs, warn

def check_assets():
    """every file in assets/ needs a MANIFEST.json entry; unknown licenses are flagged until the owner confirms them"""
    adir = os.path.join(ROOT, 'assets'); man = json.load(open(os.path.join(adir, 'MANIFEST.json'), encoding='utf-8'))
    files = [os.path.relpath(p, adir).replace(os.sep, '/') for p in glob.glob(os.path.join(adir, '**', '*'), recursive=True)
             if os.path.isfile(p) and not p.endswith(('.md', 'MANIFEST.json'))]
    errs = [f'assets/{f}: not in assets/MANIFEST.json' for f in files if f not in man]
    errs += [f'assets/MANIFEST.json: "{k}" has no file' for k in man if not k.startswith('_') and k not in files]
    errs += [f'assets/{k}: needs "source" and "license"' for k, v in man.items() if not k.startswith('_') and not (isinstance(v, dict) and v.get('source') and v.get('license'))]
    warn = [f'assets/{k}: license unknown' for k, v in man.items() if isinstance(v, dict) and v.get('license') == 'unknown']
    return errs, warn

def check(path):
    e = json.load(open(path, encoding='utf-8')); errs = []; warn = []
    for k in ('id', 'number', 'title', 'scenes'):
        if k not in e: errs.append(f'missing "{k}"')
    for i, s in enumerate(e.get('scenes', [])):
        if not s.get('say'): errs.append(f'scene {i}: no "say"')
        if s.get('kip') and s['kip'] not in E.POSES: errs.append(f'scene {i}: unknown kip pose "{s["kip"]}" (use {", ".join(E.POSES)})')
        c = s.get('card')
        if isinstance(c, dict):
            if c.get('type') not in C.TEMPLATES: errs.append(f'scene {i}: unknown card type "{c.get("type")}"'); continue
            icons = [x.get('icon') for x in c.get('items', [])] + [c.get('icon')] + [c[k].get('icon') for k in ('left', 'right') if k in c]
            errs += [f'scene {i}: unknown icon "{x}"' for x in icons if x and x not in C.ICONS]
            for a in [x.get('at') for x in c.get('items', [])] + c.get('at', []):
                if a and a.lower() not in s['say'].lower(): warn.append(f'scene {i}: "at" word "{a}" not in this scene (item will pop in on its own)')
    for sh in e.get('shorts', []):
        a, b = sh['scenes']; ns = len(e.get('scenes', []))
        if not (0 <= a <= b < ns): errs.append(f'short "{sh["hook"]}": scenes {sh["scenes"]} out of range (count from 0; last scene is {ns - 1})'); continue
        n = sum(len(e['scenes'][j]['say']) for j in range(a, b + 1))
        print(f'   short {e["id"]} {sh["scenes"]} "{sh["hook"]}" -> starts: "{e["scenes"][a]["say"][:50]}"') if '--shorts' in sys.argv else None
        if n > 900: warn.append(f'short "{sh["hook"]}" may run over 60 seconds')
    fe, fw = check_facts(e); errs += fe; warn += fw
    n = len(E.full_text(e)); return e, n, errs, warn

if __name__ == '__main__':
    bad = 0
    for p in sorted(glob.glob(os.path.join(ROOT, 'episodes', '*.json'))):
        e, n, errs, warn = check(p); bad += len(errs)
        print(f"{'FAIL' if errs else 'ok  '} {os.path.basename(p)}  ({n} characters, status: {e.get('status', 'ready')})")
        for x in errs: print('   error:', x)
        for x in warn: print('   note: ', x)
    aerrs, awarn = check_assets(); bad += len(aerrs)
    print(f"\n{'FAIL' if aerrs else 'ok  '} assets/MANIFEST.json  ({len(awarn)} unknown licenses)")
    for x in aerrs: print('   error:', x)
    print('\nIcons:', ', '.join(sorted(C.ICONS))); sys.exit(1 if bad else 0)
