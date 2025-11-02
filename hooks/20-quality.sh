#!/usr/bin/env bash
set -e

# Find uv in common locations (Windows/Linux/Mac)
UV=""
if command -v uv >/dev/null 2>&1; then
  UV="uv"
elif [ -f "$HOME/.local/bin/uv" ]; then
  UV="$HOME/.local/bin/uv"
elif [ -f "$HOME/.cargo/bin/uv" ]; then
  UV="$HOME/.cargo/bin/uv"
elif command -v uv.exe >/dev/null 2>&1; then
  UV="uv.exe"
fi

if [ -n "$UV" ] && [ -f pyproject.toml ]; then
  $UV run python -c "import sys; sys.exit(0)" >/dev/null 2>&1 || true
fi
