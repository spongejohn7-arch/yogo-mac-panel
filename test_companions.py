import unittest
from panel import validate, render

THEMES=('monster','jelly','ghost','gardener')
STATES=('idle','thinking','tool','waiting','done','error')

class CompanionThemes(unittest.TestCase):
    def pixels(self,theme,state,t,brightness=1):
        c=validate({'mode':'codex','theme':theme,'brightness':brightness})
        c['_codex']={'state':state,'age':t}
        return render(c,t)

    def test_all_six_states_animate_on_36_pixels(self):
        for theme in THEMES:
            for state in STATES:
                with self.subTest(theme=theme,state=state):
                    frames=[self.pixels(theme,state,t) for t in (0,.61,1.21,1.81)]
                    self.assertGreater(len({tuple(f) for f in frames}),1)
                    for frame in frames:
                        self.assertEqual(len(frame),36)
                        self.assertTrue(all(len(p)==3 and all(0<=v<=255 for v in p) for p in frame))

    def test_ongoing_states_loop_but_terminal_states_hold(self):
        for theme in THEMES:
            for state in ('idle','thinking','tool','waiting'):
                self.assertEqual(self.pixels(theme,state,0),self.pixels(theme,state,2.41))
            for state in ('done','error'):
                self.assertEqual(self.pixels(theme,state,1.81),self.pixels(theme,state,9))

    def test_led_background_and_eyes_are_off_and_brightness_is_applied(self):
        frame=self.pixels('monster','idle',0,.5)
        self.assertEqual(frame[0],(53,112,68))
        self.assertEqual(frame[1],(0,0,0))
        self.assertEqual(frame[13],(0,0,0))
        self.assertEqual(self.pixels('jelly','idle',0)[2],(212,152,247))

if __name__=='__main__':unittest.main()
