#!/bin/bash
cd "$(dirname "$0")"
python3 -m src.tui_browser "$@"
