import unittest
from world_themes import world_frame
from panel import validate, render

class WorldThemes(unittest.TestCase):
    def test_all_states_have_36_valid_pixels(self):
        for theme in ('garden','space'):
            for state in ('idle','thinking','tool','waiting','done','error'):
                for t in (0,.65,1.3,1.95,8):
                    pixels=world_frame(theme,state,t).pixels
                    self.assertEqual(len(pixels),36)
                    self.assertTrue(all(len(p)==3 and all(0<=c<=255 for c in p) for p in pixels))
    def test_completion_holds_final_frame_but_work_repeats(self):
        for theme in ('garden','space'):
            self.assertEqual(world_frame(theme,'done',8).pixels,world_frame(theme,'done',1.96).pixels)
            self.assertNotEqual(world_frame(theme,'done',0).pixels,world_frame(theme,'done',8).pixels)
            self.assertEqual(world_frame(theme,'tool',0).pixels,world_frame(theme,'tool',2.6).pixels)
    def test_integrated_color_and_brightness(self):
        c=validate({'mode':'codex','theme':'garden','brightness':.5})
        c['_codex']={'state':'done','age':1.3}
        self.assertEqual(render(c,1.3)[2],(127,55,84))
        c=validate({'mode':'codex','theme':'space','brightness':1})
        c['_codex']={'state':'tool','age':0}
        self.assertEqual(render(c,0)[2],(239,246,255))

if __name__=='__main__':unittest.main()
