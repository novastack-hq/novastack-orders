#!/usr/bin/env bash
# Set up this laptop for NovaStack Orders (macOS and Linux).
# Installs uv if it's missing, then hands over to tools/setup.py, which does the
# rest on every operating system. Safe to run again.
#
#   ./scripts/setup.sh            normal run
#   ./scripts/setup.sh --dry-run  show what would change, change nothing
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  if [ -x "$HOME/.local/bin/uv" ]; then
    export PATH="$HOME/.local/bin:$PATH"
  else
    echo "Installing uv, the Python project manager (https://docs.astral.sh/uv/) ..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

# --no-project: run the set-up script before the project environment exists.
# --python 3.12: uv downloads Python 3.12 first if this laptop doesn't have it.
exec uv run --no-project --python 3.12 tools/setup.py "$@"
