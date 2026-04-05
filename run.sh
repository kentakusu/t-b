#!/bin/bash
export LD_LIBRARY_PATH="$HOME/.local/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
cd "$(dirname "$0")"
python3 -m src.tui_browser "$@"
