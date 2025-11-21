#!/usr/bin/env python3
"""
View current betting opportunities
"""

import json
import sys
from pathlib import Path


def main():
    data_dir = Path("betting_data")

    if not data_dir.exists():
        print("[ERROR] No betting_data directory found")
        print("        Run analyze_edges.py first")
        sys.exit(1)

    analysis_files = sorted(data_dir.glob("analysis_*.json"), reverse=True)

    if not analysis_files:
        print("[ERROR] No analysis files found")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("  BETTING OPPORTUNITIES")
    print("=" * 70 + "\n")

    latest = analysis_files[0]
    print(f"Latest analysis: {latest.name}\n")

    try:
        with open(latest) as f:
            data = json.load(f)

        print(f"Analysis timestamp: {data.get('timestamp')}")
        print(f"Total opportunities: {data.get('opportunities', 0)}")

    except Exception as e:
        print(f"[ERROR] Error reading file: {e}")
        sys.exit(1)

    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
