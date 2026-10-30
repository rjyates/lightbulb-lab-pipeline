import json
from lightbulb import weekly as W

def cfg(tmp_path, done=()):
    (tmp_path / 'state.json').write_text(json.dumps({'done': {i: {} for i in done}}))
    return {'LBL_OUTPUT': str(tmp_path)}

def test_pick_next_ready_in_series(tmp_path):
    assert W.pick(cfg(tmp_path))['id'] == 'ep03'  # ep01-02 are "done" in their JSON
    assert W.pick(cfg(tmp_path, ['ep03']))['id'] == 'ep04'
    assert W.pick(cfg(tmp_path), series='Fix It Friday')['id'] == 'fif01'

def test_pick_skips_drafts_and_can_run_out(tmp_path):
    fif = [e['id'] for e in W.all_episodes() if e['series'] == 'Fix It Friday' and e.get('status', 'ready') == 'ready']
    assert W.pick(cfg(tmp_path, fif), series='Fix It Friday') is None  # fif06+ are drafts

def test_pick_explicit_episode(tmp_path):
    assert W.pick(cfg(tmp_path), want='fif08')['id'] == 'fif08'

def test_description_has_links_and_credits():
    ep = next(e for e in W.all_episodes() if e['id'] == 'ep03')
    d = W.description(ep, {})
    assert 'fourthwall.com' in d and 'The Grey Room' in d and len(d) <= 5000

def test_pick_accepts_approved(tmp_path, monkeypatch):
    eps = [{'id': 'x1', 'number': 1, 'series': 'S', 'status': 'draft'}, {'id': 'x2', 'number': 2, 'series': 'S', 'status': 'approved'}]
    monkeypatch.setattr(W, 'all_episodes', lambda: eps)
    assert W.pick(cfg(tmp_path), series='S')['id'] == 'x2'
