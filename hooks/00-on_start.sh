#!/usr/bin/env bash
set -e
echo "🧠 Repo: $(basename "$(pwd)")  Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'n/a')"
[ -f pyproject.toml ] && echo "✓ pyproject.toml present" || echo "⚠ no pyproject.toml"
