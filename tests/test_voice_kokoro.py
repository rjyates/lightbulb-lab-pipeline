"""Kokoro voice provider: timing alignment, spoken forms and description credit. No model or audio needed."""
import unittest
from lightbulb import voice_kokoro as VK, weekly as W


class Align(unittest.TestCase):
    def test_words_get_their_own_times(self):
        scenes = ['Hello there.', 'Bye now.']
        words = [[('Hello', 0.0, 0.5), ('there', 0.6, 1.0), ('.', 1.0, 1.1)], [('Bye', 2.0, 2.4), ('now', 2.5, 2.9)]]
        text, al = VK.align(scenes, words, [(0.0, 1.2), (1.75, 3.0)])
        self.assertEqual(text, 'Hello there. ... Bye now.')
        st, en = al['character_start_times_seconds'], al['character_end_times_seconds']
        self.assertEqual(len(st), len(text)); self.assertEqual(len(en), len(text))
        self.assertEqual(st[text.index('Hello')], 0.0)
        self.assertAlmostEqual(en[text.index('there') + 4], 1.0)
        self.assertEqual(st[text.index('Bye')], 2.0)
        self.assertTrue(1.2 <= st[text.index('...')] <= 1.75)  # separator sits in the pause
        self.assertEqual(st, sorted(st)); self.assertTrue(all(e >= s for s, e in zip(st, en)))

    def test_matches_engine_full_text(self):
        from lightbulb import engine as E
        ep = {'scenes': [{'say': 'One.'}, {'say': ' Two. '}, {'say': 'Three.'}]}
        scenes = E.scene_text(ep)
        text, _ = VK.align(scenes, [[] for _ in scenes], [(0, 1), (1.5, 2), (2.5, 3)])
        self.assertEqual(text, E.full_text(ep))

    def test_unmatched_words_are_interpolated(self):
        text, al = VK.align(['Use 2FA today.'], [[('Use', 0.0, 0.3), ('two-F-A', 0.4, 1.0), ('today', 1.1, 1.5)]], [(0.0, 1.6)])
        st = al['character_start_times_seconds']
        self.assertTrue(0.3 <= st[text.index('2FA')] <= 1.1)
        self.assertEqual(st[text.index('today')], 1.1)


class Recipe(unittest.TestCase):
    def test_recipe_is_complete(self):
        r = VK.recipe()
        for k in ('version', 'blend', 'speed', 'lang_code', 'sample_rate', 'scene_gap_s', 'model'):
            self.assertIn(k, r)
        self.assertAlmostEqual(sum(r['blend'].values()), 1.0)

    def test_spoken_forms(self):
        self.assertEqual(VK.spoken('Turn on 2FA.', {'spoken_forms': {'2FA': 'two-F-A'}}), 'Turn on two-F-A.')


class Credit(unittest.TestCase):
    def test_credit_follows_provider(self):
        self.assertIn('Kokoro', W.voice_credit({'LBL_VOICE': 'kokoro'}))
        self.assertIn('ElevenLabs', W.voice_credit({'LBL_VOICE': 'elevenlabs'}))
        self.assertIn('Kokoro', W.voice_credit({}))


if __name__ == '__main__':
    unittest.main()
