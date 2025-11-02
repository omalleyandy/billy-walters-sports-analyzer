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

if [ -d tests ]; then
  if [ -n "$UV" ]; then
    $UV run pytest -q || { echo "❌ tests failed"; exit 1; }
  elif command -v python >/dev/null 2>&1; then
    python -m pytest -q || { echo "❌ tests failed"; exit 1; }
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m pytest -q || { echo "❌ tests failed"; exit 1; }
  else
    echo "⚠ Neither uv nor python found; skipping tests"
    exit 0
  fi
else
  echo "ℹ no tests/ directory; skipping pytest"
fi
