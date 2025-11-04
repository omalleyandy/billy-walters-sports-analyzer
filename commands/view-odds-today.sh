#!/bin/bash
# Quick command: View today's games

cd "$(dirname "$0")/.." || exit
uv run walters-analyzer view-odds --today "$@"

