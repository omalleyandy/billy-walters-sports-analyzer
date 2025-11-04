#!/bin/bash
# Quick command: View NFL odds from latest scrape

cd "$(dirname "$0")/.." || exit
uv run walters-analyzer view-odds --sport nfl "$@"

