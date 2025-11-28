#!/usr/bin/env python3
"""Quick analysis of divergence distributions between NFL and NCAAF."""

import json
from pathlib import Path

data_dir = Path("data/action_network")

# Load data
with open(data_dir / "nfl_odds_latest.json") as f:
    nfl = json.load(f)

with open(data_dir / "ncaaf_odds_latest.json") as f:
    ncaaf = json.load(f)

print("=" * 60)
print("DIVERGENCE DISTRIBUTION ANALYSIS")
print("=" * 60)

# NFL Analysis
print(f"\n📊 NFL ({nfl['game_count']} games)")
print("-" * 40)
nfl_divs = [p["divergence"] for p in nfl["sharp_plays"]]
print(
    f"Sharp plays (5+ div): {len(nfl_divs)} ({len(nfl_divs) / nfl['game_count'] * 100:.0f}%)"
)
print(f"Max divergence: {max(nfl_divs) if nfl_divs else 0}")
print(f"Avg divergence: {sum(nfl_divs) / len(nfl_divs):.1f}" if nfl_divs else "N/A")
print("\nAll sharp plays:")
for p in nfl["sharp_plays"]:
    print(f"  {p['game']}: {p['pick']} (+{p['divergence']})")

# NCAAF Analysis
print(f"\n📊 NCAAF ({ncaaf['game_count']} games)")
print("-" * 40)
ncaaf_divs = [p["divergence"] for p in ncaaf["sharp_plays"]]
print(
    f"Sharp plays (5+ div): {len(ncaaf_divs)} ({len(ncaaf_divs) / ncaaf['game_count'] * 100:.0f}%)"
)
print(f"Max divergence: {max(ncaaf_divs) if ncaaf_divs else 0}")
print(
    f"Avg divergence: {sum(ncaaf_divs) / len(ncaaf_divs):.1f}" if ncaaf_divs else "N/A"
)

# Threshold analysis
print("\n📈 NCAAF Threshold Analysis:")
print("-" * 40)
thresholds = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
for t in thresholds:
    count = len([d for d in ncaaf_divs if d >= t])
    pct = count / ncaaf["game_count"] * 100
    print(f"  {t:2d}+ div: {count:2d} games ({pct:5.1f}%)")

# Recommendation
print("\n💡 RECOMMENDED THRESHOLDS:")
print("-" * 40)
print("NFL:   5+ moderate, 10+ strong, 15+ very strong (current)")
print("NCAAF: 20+ moderate, 30+ strong, 40+ very strong (proposed)")

# Show top NCAAF plays with new thresholds
print("\n🎯 TOP NCAAF PLAYS (30+ divergence):")
print("-" * 40)
for p in ncaaf["sharp_plays"]:
    if p["divergence"] >= 30:
        print(f"  {p['game']}: {p['pick']}")
        print(
            f"    Tickets: {p['tickets_pct']}% | Money: {p['money_pct']}% | Div: +{p['divergence']}"
        )
