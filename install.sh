#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
[[ "$(uname -s)" == Darwin ]] || { echo 'This installer supports macOS only.'; exit 1; }
PYTHON="${YOGO_PYTHON:-python3}"
"$PYTHON" -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required"'
BREW="$(command -v brew || true)"
if [[ -z "$BREW" ]]; then
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [[ -x "$candidate" ]]; then BREW="$candidate"; break; fi
  done
fi
[[ -n "$BREW" ]] || { echo 'Install Homebrew from https://brew.sh first.'; exit 1; }
"$BREW" list hidapi >/dev/null 2>&1 || "$BREW" install hidapi
"$PYTHON" -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/requirements.txt"
chmod +x "$ROOT/start.command"
export DYLD_LIBRARY_PATH="$("$BREW" --prefix hidapi)/lib:${DYLD_LIBRARY_PATH:-}"
"$ROOT/.venv/bin/python" -c 'import hid; from yogo.device import YogoDisplay; print("Dependencies ready")'
"$ROOT/.venv/bin/python" "$ROOT/create_app.py"
printf '%s\n' '安装完成。可双击本目录 start.command 或 ~/Applications/YOGO Mac Panel.app。'
