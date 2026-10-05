"""Check episode scripts before Sunday:  python3 -m lightbulb.check"""
import glob, json, os, sys
from . import cards as C, engine as E
from .core import ROOT

def check(path):
    e = json.load(open(path)); errs = []; warn = []
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
        a, b = sh['scenes']; n = sum(len(e['scenes'][j]['say']) for j in range(a, b + 1))
        if n > 900: warn.append(f'short "{sh["hook"]}" may run over 60 seconds')
    n = len(E.full_text(e)); return e, n, errs, warn

if __name__ == '__main__':
    bad = 0
    for p in sorted(glob.glob(os.path.join(ROOT, 'episodes', 'ep*.json'))):
        e, n, errs, warn = check(p); bad += len(errs)
        print(f"{'FAIL' if errs else 'ok  '} {os.path.basename(p)}  ({n} characters, status: {e.get('status', 'ready')})")
        for x in errs: print('   error:', x)
        for x in warn: print('   note: ', x)
    print('\nIcons:', ', '.join(sorted(C.ICONS))); sys.exit(1 if bad else 0)
