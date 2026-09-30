"""Start the local panel once, using this checkout's environment."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:18765'

def ready():
    try:
        with urllib.request.urlopen(URL + '/api/status', timeout=1) as response:
            state = json.load(response)
            return isinstance(state.get('token'), str) and 'pixels' in state
    except (OSError, ValueError):
        return False

def main():
    with (ROOT / 'launch.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not ready():
            env = dict(os.environ)
            search = [env.get('DYLD_LIBRARY_PATH', ''), str(ROOT / 'lib'),
                      '/opt/homebrew/lib', '/usr/local/lib']
            env['DYLD_LIBRARY_PATH'] = ':'.join(filter(None, search))
            with (ROOT / 'server.log').open('ab') as log:
                child = subprocess.Popen(
                    [sys.executable, str(ROOT / 'panel.py')], env=env,
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                    start_new_session=True)
            for _ in range(40):
                if ready() or child.poll() is not None:
                    break
                time.sleep(.2)
        if not ready():
            raise SystemExit(f'YOGO failed to start. See {ROOT / "server.log"}')
    subprocess.run(['/usr/bin/open', URL], check=True)

if __name__ == '__main__':
    main()
