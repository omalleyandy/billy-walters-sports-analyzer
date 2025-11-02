#!/usr/bin/env bash
set -euo pipefail
# Prevent accidental overwrite of sensitive files
blocked=(".env" ".venv/" "env.template" "secrets*.json")
for p in "${blocked[@]}"; do
  if git diff --name-only --cached | grep -qE "^$(printf '%s' "$p" | sed 's/\./\\./g' | sed 's/\*/.*/g')$"; then
    echo "❌ Guard: attempted change to protected path: $p"
    exit 1
  fi
done
