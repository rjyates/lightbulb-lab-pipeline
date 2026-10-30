"""Duplicate-upload protection: simulated crashes at each step must never produce a second upload."""
import pytest
from lightbulb import youtube as YT, ledger as L

@pytest.fixture
def fake(tmp_path, monkeypatch):
    """a pretend channel: upload() adds a video, find_by_tag() searches it"""
    ch = {'videos': {}, 'crash_after_insert': False, 'calls': 0}
    def upload(cfg, path, title, desc, tags, on_insert=None, **kw):
        ch['calls'] += 1; vid = f'v{ch["calls"]}'; ch['videos'][vid] = tags
        if ch.pop('crash_before_record', False): raise ConnectionError('lost connection after insert')
        if on_insert: on_insert(vid)
        if ch.pop('crash_after_insert', False): raise ConnectionError('playlist call failed')
        return vid
    monkeypatch.setattr(YT, 'upload', upload)
    monkeypatch.setattr(YT, 'find_by_tag', lambda cfg, tag: next((v for v, t in ch['videos'].items() if tag in t), None))
    return {'LBL_OUTPUT': str(tmp_path)}, ch

def pub(cfg): return YT.publish_once(cfg, 'ep03-main', 'ep03.mp4', 'T', 'D', ['tech'])

def test_second_run_skips(fake):
    cfg, ch = fake
    assert pub(cfg) == pub(cfg) == 'v1' and ch['calls'] == 1
    assert ch['videos']['v1'][0] == 'lbl-ep03-main'

def test_crash_after_insert_is_recorded(fake):
    cfg, ch = fake; ch['crash_after_insert'] = True
    with pytest.raises(ConnectionError): pub(cfg)
    assert pub(cfg) == 'v1' and ch['calls'] == 1

def test_crash_before_record_is_reconciled_from_channel(fake):
    cfg, ch = fake; ch['crash_before_record'] = True
    with pytest.raises(ConnectionError): pub(cfg)
    assert L.state(cfg, 'ep03-main') == ('pending', None)
    assert pub(cfg) == 'v1' and ch['calls'] == 1
    assert L.records(cfg, 'ep03-main')[-1]['reconciled'] is True

def test_pending_with_nothing_on_channel_uploads(fake):
    cfg, ch = fake
    L.append(cfg, 'ep03-main', 'intent')  # crashed before the upload reached YouTube
    assert pub(cfg) == 'v1' and ch['calls'] == 1

def test_shorts_are_separate_keys(fake):
    cfg, ch = fake
    pub(cfg); YT.publish_once(cfg, 'ep03-short1', 's1.mp4', 'S', 'D', [])
    assert ch['calls'] == 2
