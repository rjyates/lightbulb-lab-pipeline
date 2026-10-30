import glob, json, os
from datetime import date
import pytest
from lightbulb import check as CK
from lightbulb.core import ROOT

EPISODES = sorted(glob.glob(os.path.join(ROOT, 'episodes', '*.json')))
TODAY = date(2026, 11, 1)

@pytest.mark.parametrize('path', EPISODES, ids=os.path.basename)
def test_bundled_episodes_pass(path):
    _, _, errs, _ = CK.check(path)
    assert errs == []

def ep(**kw):
    e = {'id': 't1', 'number': 1, 'title': 'T', 'status': 'draft', 'scenes': [{'say': 'One.'}, {'say': 'Two.'}],
         'sources': [{'url': 'https://consumer.ftc.gov/x'}], 'claims': [{'scene': 1, 'text': 'A fact', 'source': 0}]}
    e.update(kw); return e

def errs_of(e): return CK.check_facts(e, TODAY)[0]

def test_sourced_episode_passes():
    assert CK.check_facts(ep(status='approved'), TODAY) == ([], [])

def test_approved_needs_sources():
    assert errs_of(ep(status='approved', sources=[], claims=[]))

def test_ready_without_sources_still_allowed():
    assert errs_of({'status': 'ready', 'scenes': []}) == []

def test_unknown_status():
    assert errs_of(ep(status='live'))

@pytest.mark.parametrize('claim', [
    {'scene': 1, 'text': 'x', 'source': 3},           # no such source
    {'scene': 9, 'text': 'x', 'source': 0},           # no such scene
    {'scene': 1, 'source': 0},                        # no text
    {'scene': 1, 'text': 'x', 'source': 0, 'valid_until': '31/12/2027'},
])
def test_bad_claims(claim):
    assert errs_of(ep(claims=[claim]))

def test_bad_source_url():
    assert errs_of(ep(sources=[{'url': 'ftc.gov'}]))

def test_expired_claim_blocks_approved_but_only_warns_draft():
    old = [{'scene': 1, 'text': 'x', 'source': 0, 'valid_until': '2026-10-01'}]
    assert errs_of(ep(status='approved', claims=old))
    errs, warn = CK.check_facts(ep(status='draft', claims=old), TODAY)
    assert errs == [] and warn
    assert CK.check_facts(ep(status='done', claims=old), TODAY) == ([], [])

def test_sensitive_must_be_bool():
    assert errs_of(ep(sensitive='yes'))
