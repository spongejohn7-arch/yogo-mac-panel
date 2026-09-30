import unittest
from panel import validate, render

class Controls(unittest.TestCase):
    def test_reject_invalid_commands_before_device_access(self):
        for value in ({'mode':'bad'}, {'mode':'solid','brightness':float('nan')},
                      {'mode':'pixels','pixels':[[1,2,3]]}, {'mode':'text','text':'中文'},
                      {'mode':'solid','brightness':2}, {'mode':'pixels','pixels':[[999,0,0]]*36}):
            with self.subTest(value=value), self.assertRaises(ValueError): validate(value)
    def test_brightness_and_pixels(self):
        c=validate({'mode':'pixels','pixels':[[200,100,0]]*36,'brightness':.5})
        self.assertEqual(render(c,0),[(100,50,0)]*36)
    def test_text_advances_and_blank_is_dark(self):
        c=validate({'mode':'text','text':'A ','brightness':1,'color':'#ff0000'})
        self.assertTrue(any(r for r,g,b in render(c,0)))
        self.assertEqual(render(c,1.3),[(0,0,0)]*36)
    def test_stop_works_with_empty_text_field(self):
        self.assertEqual(validate({"mode":"stop","text":""})["mode"], "stop")
    def test_off_is_black(self):
        self.assertEqual(render(validate({'mode':'off'}),0),[(0,0,0)]*36)

if __name__=='__main__': unittest.main()
