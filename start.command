#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo '请先在此目录运行 bash install.sh。'
  exit 1
fi
exec "$ROOT/.venv/bin/python" "$ROOT/launch.py"
