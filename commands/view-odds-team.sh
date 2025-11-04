#!/bin/bash
# Quick command: View games for a specific team
# Usage: ./view-odds-team.sh "Cowboys"

cd "$(dirname "$0")/.." || exit

if [ -z "$1" ]; then
    echo "Usage: $0 <team_name>"
    echo "Example: $0 \"Cowboys\""
    exit 1
fi

uv run walters-analyzer view-odds --team "$1" "${@:2}"

