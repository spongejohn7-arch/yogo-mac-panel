import shlex
import unittest
from pathlib import Path
from create_app import launcher_script

class Launcher(unittest.TestCase):
    def test_path_with_spaces_and_shell_metacharacters_remains_one_argument(self):
        root=Path('/tmp/My project $HOME `test`')
        command=launcher_script(root).splitlines()[1]
        self.assertEqual(shlex.split(command),['exec',str(root/'.venv/bin/python'),str(root/'launch.py')])

if __name__=='__main__':unittest.main()
