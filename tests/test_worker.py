"""Worker scheduling with fake rendering and a fake YouTube: nothing here renders or uploads."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest
from lightbulb import worker as WK, weekly as W

CT = ZoneInfo('America/Chicago')
NOW = datetime(2026, 11, 1, 6, 0, tzinfo=timezone.utc)  # early Sunday in Chicago: Tuesday 9:00 is more than LEAD away

def episodes(n=5):
    eps = []
    for series, pre in (('Tech from Scratch', 'ep'), ('Fix It Friday', 'fif')):
        eps += [{'id': f'{pre}{i:02d}', 'number': i, 'series': series, 'status': 'ready', 'scenes': [{'say': 'x'}]} for i in range(1, n + 1)]
    return eps

@pytest.fixture
def env(tmp_path, monkeypatch):
    eps = episodes(); monkeypatch.setattr(W, 'all_episodes', lambda: eps)
    calls = {'produce': [], 'publish': [], 'unschedule': [], 'notify': []}
    def produce(cfg, ep):
        calls['produce'].append(ep['id']); f = str(tmp_path / ep['id'])
        return {'folder': f, 'main': f + '/main.mp4', 'thumb': f + '/t.jpg', 'short_files': [f + '/s1.mp4', f + '/s2.mp4'], 'tags': ['t'],
                'meta': {'title': ep['id'], 'description': 'd', 'shorts': [{'title': 's1', 'description': 'd'}, {'title': 's2', 'description': 'd'}]}}
    def publish(cfg, key, path, title, desc, tags, **kw): calls['publish'].append((key, kw['publish_at'])); return 'vid-' + key
    cfg = {'LBL_OUTPUT': str(tmp_path), 'YOUTUBE_UPLOAD': 'true'}
    run = lambda now=NOW: WK.run_once(cfg, now, produce, publish, lambda c, v: calls['unschedule'].append(v), lambda t, m: calls['notify'].append(t))
    return cfg, eps, calls, run

def local(s): return WK.when(s).astimezone(CT)

def test_fills_three_weeks_on_the_calendar(env):
    cfg, _, calls, run = env
    r = run()
    assert r['scheduled'] == ['ep01', 'ep02', 'ep03', 'fif01', 'fif02', 'fif03'] and r['failed'] == []
    q = WK.load_queue(cfg)
    assert [(local(e['slots'][e['id'] + '-main']).strftime('%a %d %H:%M')) for e in q] == \
        ['Tue 03 09:00', 'Tue 10 09:00', 'Tue 17 09:00', 'Fri 06 09:00', 'Fri 13 09:00', 'Fri 20 09:00']
    ep1, fif1 = q[0]['slots'], q[3]['slots']
    assert [local(ep1[k]).strftime('%a') for k in ('ep01-short1', 'ep01-short2')] == ['Wed', 'Thu']
    assert [local(fif1[k]).strftime('%a') for k in ('fif01-short1', 'fif01-short2')] == ['Sat', 'Sun']
    assert len(calls['publish']) == 18 and q[0]['videos']['ep01-main'] == 'vid-ep01-main'

def test_second_run_same_day_does_nothing(env):
    _, _, calls, run = env
    run(); n = len(calls['publish'])
    assert run()['scheduled'] == [] and len(calls['publish']) == n

def test_next_week_adds_one_per_series(env):
    _, _, calls, run = env
    run(); r = run(NOW + timedelta(days=7))
    assert r['scheduled'] == ['ep04', 'fif04']

def test_slot_keeps_9am_across_daylight_saving(env):
    cfg, *_ = env
    q = [{'id': 'ep01', 'series': 'Tech from Scratch', 'status': 'scheduled', 'slots': {'ep01-main': '2026-10-27T14:00:00Z'}}]  # 9:00 CDT
    assert WK.next_slot(cfg, q, 'Tech from Scratch', NOW).astimezone(CT).hour == 9

def test_veto_holds_and_unschedules(env, tmp_path):
    cfg, _, calls, run = env
    run(); (tmp_path / 'veto').mkdir(); (tmp_path / 'veto' / 'ep01').touch()
    r = run(NOW + timedelta(days=1))  # ep01 goes live Tue 9:00, within 48 h
    assert r['held'] == ['ep01'] and len(calls['unschedule']) == 3
    assert WK.load_queue(cfg)[0]['status'] == 'held' and 'held ep01' in calls['notify'][-1]

def test_expired_fact_holds(env):
    cfg, eps, calls, run = env
    run()
    eps[0].update(sources=[{'url': 'https://example.gov'}], claims=[{'scene': 0, 'text': 'x', 'source': 0, 'valid_until': '2026-11-02'}])  # still true today, but not on Tuesday when it goes live
    assert run(NOW + timedelta(days=1))['held'] == ['ep01']

def test_pause_holds_due_items_and_makes_nothing(env, tmp_path):
    cfg, _, calls, run = env
    run(); n = len(calls['produce']); (tmp_path / 'PAUSE').touch()
    r = run(NOW + timedelta(days=8))
    assert r['scheduled'] == [] and len(calls['produce']) == n and r['held']

def test_marks_published(env):
    cfg, _, _, run = env
    run(); r = run(NOW + timedelta(days=5))  # ep01 and its Shorts are all past
    assert 'ep01' in r['published'] and 'ep01' in W.load_state(cfg)['done']

def test_failure_stops_that_series_only(env, monkeypatch):
    cfg, _, calls, run = env
    def produce(cfg, ep):
        if ep['series'] == 'Tech from Scratch': raise RuntimeError('quality gates failed')
        return {'folder': 'f', 'main': 'm.mp4', 'thumb': 't', 'short_files': [], 'tags': [], 'meta': {'title': 'T', 'description': 'D', 'shorts': []}}
    r = WK.run_once(cfg, NOW, produce, lambda *a, **k: 'v', lambda *a: None, lambda t, m: calls['notify'].append(t))
    assert r['failed'] == ['ep01'] and r['scheduled'] == ['fif01', 'fif02', 'fif03'] and 'ep01 failed' in calls['notify'][0]

def test_runs_out_of_scripts(env):
    cfg, eps, calls, run = env
    for e in eps[1:5]: e['status'] = 'draft'
    r = run()
    assert r['scheduled'][0] == 'ep01' and any('no scripts left' in t for t in calls['notify'])

def test_uploads_off_leaves_folders(env):
    cfg, _, calls, run = env
    cfg['YOUTUBE_UPLOAD'] = 'false'; run()
    assert calls['publish'] == [] and WK.load_queue(cfg)[0]['status'] == 'awaiting-manual-upload'
