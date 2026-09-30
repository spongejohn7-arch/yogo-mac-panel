import unittest
from robot_theme import robot_frame
from panel import validate, render

class RobotTheme(unittest.TestCase):
    def test_all_states_fit_display_and_use_two_or_three_colors(self):
        for state in ('idle','thinking','tool','waiting','done','error'):
            for t in (0,.3,.7,1.4,2.5,4.3):
                with self.subTest(state=state,t=t):
                    pixels=robot_frame(state,t).pixels
                    self.assertEqual(len(pixels),36)
                    colors=set(pixels)-{(0,0,0)}
                    self.assertGreaterEqual(len(colors),2)
                    self.assertLessEqual(len(colors),3)
                    self.assertTrue(all(0<=v<=255 for p in pixels for v in p))
    def test_idle_blinks_and_tool_feet_move(self):
        self.assertNotEqual(robot_frame('idle',0).pixels,robot_frame('idle',4.3).pixels)
        self.assertNotEqual(robot_frame('tool',0).pixels[30:],robot_frame('tool',.6).pixels[30:])
    def test_completion_changes_from_face_to_heart(self):
        self.assertNotEqual(robot_frame('done',.2).pixels,robot_frame('done',2).pixels)
        self.assertEqual(robot_frame('done',2).pixels[2*6+2],(255,60,120))
    def test_theme_validation_and_brightness(self):
        with self.assertRaises(ValueError):validate({'mode':'codex','theme':'bad'})
        c=validate({'mode':'codex','theme':'robot','brightness':.5})
        c['_codex']={'state':'done','age':2}
        self.assertEqual(render(c,2)[14],(127,30,60))
        self.assertNotEqual(render(c,2),render({**c,'theme':'simple'},2))

if __name__=='__main__': unittest.main()
