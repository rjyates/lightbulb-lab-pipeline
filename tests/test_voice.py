from lightbulb import voice as VO, engine as E

def test_align_matches_full_text_and_pins_words():
    segs = [('Hi there.', 0.0, 1.0, [('Hi', 0.1, 0.3), ('there', 0.4, 0.9)]), ('Bye!', 1.55, 2.0, [('Bye', 1.6, 1.9)])]
    al = VO.align(segs); text = VO.SEP.join(s for s, *_ in segs)
    assert ''.join(al['characters']) == text and len(al['character_start_times_seconds']) == len(text)
    t = E.Timing.from_alignment(text, al)
    assert t.at(text.index('there')) == 0.4 and t.at(text.index('Bye')) == 1.6
    assert t.at(text.index('...')) == 1.0  # the pause between scenes sits at the scene's end

def test_unmatched_tokens_keep_even_spread():
    al = VO.align([('Wi-Fi works', 0.0, 2.0, [('wifi', 0.0, 1.0)])])
    assert al['character_start_times_seconds'][0] == 0.0 and al['character_end_times_seconds'][-1] == 2.0

def test_provider_defaults_to_free_voice():
    assert VO.provider({}) == 'kokoro' and 'Kokoro' in VO.credit({}) and VO.characters_left({}) is None
    assert VO.voice_id({'KOKORO_VOICE': 'af_heart:1'}) != VO.voice_id({})  # changing the voice invalidates cached takes
