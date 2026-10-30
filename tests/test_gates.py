"""Quality gates against deliberately broken media. Every broken fixture must fail its check."""
import json, os, shutil, subprocess
import pytest
from PIL import Image
from lightbulb import gates as G

pytestmark = pytest.mark.skipif(not shutil.which('ffmpeg'), reason='needs ffmpeg/ffprobe on PATH')
TONE = 'sine=f=440:d={d},volume=2.5'  # about -14 LUFS, peak -13 dBFS

@pytest.fixture(scope='session')
def make(tmp_path_factory):
    d = tmp_path_factory.mktemp('media')
    def make(name, size='1920x1080', dur=6, vf='null', af='anull', adur=None, shortest=True):
        p = str(d / f'{name}.mp4')
        if not os.path.exists(p):
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', f'testsrc2=s={size}:r=30:d={dur}', '-f', 'lavfi', '-i', TONE.format(d=adur or dur),
                            '-vf', vf, '-af', af, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ac', '2'] + (['-shortest'] if shortest else []) + [p], check=True)
        return p
    return make

def failed(checks): return {c['check'] for c in checks if not c['pass']}

def test_good_video_passes(make):
    assert failed(G.media(make('good'), G.MAIN, expect=6)) == set()

@pytest.mark.parametrize('name, kw, check', [
    ('black', {'vf': "drawbox=c=black:t=fill:enable='between(t,2,3.5)'"}, 'no black gaps'),
    ('silent', {'af': "volume=0:enable='between(t,1.5,4.5)'"}, 'no dead air'),
    ('clipped', {'af': 'volume=30'}, 'no clipping'),
    ('quiet', {'af': 'volume=0.05'}, 'loudness'),
    ('desync', {'adur': 3, 'shortest': False}, 'sync'),
    ('small', {'size': '1280x720'}, 'size'),
])
def test_broken_video_fails(make, name, kw, check):
    assert check in failed(G.media(make(name, **kw), G.MAIN, expect=6))

def test_fade_at_start_is_allowed(make):
    assert 'no black gaps' not in failed(G.media(make('fadein', vf="drawbox=c=black:t=fill:enable='lt(t,0.8)'"), G.MAIN))

def test_wrong_duration_and_long_short(make):
    assert {'duration', 'max length'} <= failed(G.media(make('good'), G.MAIN, expect=10, max_len=5))

def test_truncated_file_fails(make, tmp_path):
    src = make('good'); bad = tmp_path / 'cut.mp4'
    bad.write_bytes(open(src, 'rb').read()[: os.path.getsize(src) // 2])
    assert failed(G.media(str(bad), G.MAIN)) & {'readable', 'decodes cleanly', 'sync', 'duration'}

def srt(path, cues):
    t = lambda x: f'00:00:{int(x):02d},{int(x * 1000 % 1000):03d}'
    path.write_text('\n'.join(f'{i}\n{t(a)} --> {t(b)}\n{s}\n' for i, (a, b, s) in enumerate(cues, 1)), encoding='utf-8'); return str(path)

def test_captions(tmp_path):
    assert failed(G.captions(srt(tmp_path / 'a.srt', [(0, 2, 'Hi'), (2, 5.8, 'There')]), 6)) == set()
    assert 'captions in order' in failed(G.captions(srt(tmp_path / 'b.srt', [(3, 4, 'B'), (0, 2, 'A')]), 6))
    assert 'captions cover video' in failed(G.captions(srt(tmp_path / 'c.srt', [(0, 2, 'Only')]), 6))
    (tmp_path / 'd.srt').write_text('nonsense', encoding='utf-8')
    assert 'captions parse' in failed(G.captions(str(tmp_path / 'd.srt'), 6))

LINKS = {'website': {'url': 'https://lightbulb-lab.pages.dev/'}, 'guides': [{'url': 'https://lightbulb-lab-shop.fourthwall.com/p'}], 'tiktok': 'https://www.tiktok.com/@lightbulblab'}
DESC = 'Guide: https://lightbulb-lab-shop.fourthwall.com/p\nKip’s voice is AI-generated.\nMusic: Nebula'

def test_metadata():
    hosts = G.allowed_hosts(LINKS)
    assert failed(G.metadata('Title', DESC, ['a'], hosts)) == set()
    assert 'links are our own' in failed(G.metadata('T', DESC + ' https://evil.example/x', [], hosts))
    assert {'AI voice disclosed', 'music credited'} <= failed(G.metadata('T', 'plain', [], hosts))
    assert {'title length', 'tags length'} <= failed(G.metadata('x' * 101, DESC, ['t' * 60] * 9, hosts))

def test_thumbnail(tmp_path):
    good, bad = tmp_path / 't.jpg', tmp_path / 't.png'
    Image.new('RGB', (1280, 720), 'navy').save(good); Image.new('RGB', (1000, 700)).save(bad)
    assert failed(G.thumbnail(str(good))) == set()
    assert {'thumbnail size', 'thumbnail format'} <= failed(G.thumbnail(str(bad)))

@pytest.fixture
def episode(make, tmp_path):
    main = tmp_path / 'ep.mp4'; shutil.copy(make('good'), main)
    srt(tmp_path / 'ep.en.srt', [(0, 5.8, 'Hello')])
    Image.new('RGB', (1280, 720)).save(tmp_path / 'thumb.jpg')
    meta = {'title': 'T', 'description': DESC, 'tags': ['x'], 'shorts': []}
    return str(tmp_path), str(main), str(tmp_path / 'thumb.jpg'), meta

def test_gate_report_and_upload_lock(episode):
    folder, main, thumb, meta = episode
    assert G.gate(folder, main, [], thumb, meta, LINKS, main_dur=6)['pass']
    assert os.path.exists(os.path.join(folder, 'contact-0.jpg'))
    G.verify(main)  # passes: listed, unchanged
    open(main, 'ab').write(b'tampered')
    with pytest.raises(RuntimeError, match='changed'): G.verify(main)

def test_upload_lock_refuses_failed_or_missing_report(episode):
    folder, main, thumb, meta = episode
    with pytest.raises(RuntimeError, match='no qa-report'): G.verify(main)
    assert not G.gate(folder, main, [], thumb, dict(meta, description='no credits'), LINKS, main_dur=6)['pass']
    with pytest.raises(RuntimeError, match='failed'): G.verify(main)
