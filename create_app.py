"""Create a per-user launcher without embedding the author's machine paths."""
import plistlib
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def launcher_script(root):
    return '#!/bin/sh\nexec ' + shlex.quote(str(root / '.venv/bin/python')) + ' ' + shlex.quote(str(root / 'launch.py')) + '\n'

def main():
    app = Path.home() / 'Applications/YOGO Mac Panel.app'
    executable = app / 'Contents/MacOS/YogoPanel'
    if app.exists():
        print(f'Launcher already exists; leaving it unchanged: {app}')
        return
    executable.parent.mkdir(parents=True)
    executable.write_text(launcher_script(ROOT))
    executable.chmod(0o755)
    metadata = {'CFBundleName':'YOGO Mac Panel', 'CFBundleIdentifier':'community.yogo.mac-panel',
                'CFBundleVersion':'0.1.0', 'CFBundlePackageType':'APPL',
                'CFBundleExecutable':'YogoPanel', 'LSUIElement':True}
    with (app / 'Contents/Info.plist').open('wb') as output:
        plistlib.dump(metadata, output)
    print(f'Created {app}')

if __name__ == '__main__':
    main()
