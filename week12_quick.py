#!/usr/bin/env python3
"""
Week 12 NFL Quick Analysis - Overtime Only
Fast version using just Overtime.ag odds (no Massey scraping)
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "clients"))

from overtime_api_client import OvertimeApiClient


async def quick_analyze():
    """Quick Week 12 analysis using just Overtime odds"""

    print("\n" + "=" * 70)
    print("WEEK 12 NFL QUICK ANALYSIS - Billy Walters Methodology")
    print("Using Overtime.ag odds only (fast version)")
    print("=" * 70)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")

    # Get odds
    print("[STEP 1] Fetching Overtime.ag odds...")
    print("-" * 70)

    try:
        overtime = OvertimeApiClient()
        odds_data = await overtime.scrape_nfl()
        games = odds_data.get("games", [])
        print(f"[OK] Overtime: {len(games)} games found\n")

        # Display all games
        for i, game in enumerate(games, 1):
            away = game.get("away_team", "Unknown")
            home = game.get("home_team", "Unknown")
            spread = game.get("spread", {}).get("home", "N/A")
            total = game.get("total", {}).get("points", "N/A")

            print(f"  {i}. {away} @ {home}")
            print(f"     Spread: {home} {spread:+.1f} | Total: {total}")

    except Exception as e:
        print(f"[ERROR] Overtime scraping failed: {e}")
        return

    print("\n" + "-" * 70)

    # Billy Walters key numbers
    KEY_NUMBERS = {3: 1.5, 7: 1.2, 6: 1.0, 14: 0.8}

    opportunities = []

    print("\n[STEP 2] Analyzing for edges...")
    print("-" * 70)
    print("[CRITERIA] Billy Walters Requirements:")
    print("  - Minimum 5.5% edge")
    print("  - Large spreads (contrarian value)")
    print("  - Key numbers: 3, 7, 6, 14")
    print("-" * 70 + "\n")

    for game in games:
        away = game.get("away_team", "Unknown")
        home = game.get("home_team", "Unknown")
        spread_data = game.get("spread", {})

        try:
            home_spread = float(spread_data.get("home", 0))
        except (ValueError, TypeError):
            continue

        abs_spread = abs(home_spread)

        # Large spread contrarian strategy
        base_edge = 0.0
        reasons = []

        if abs_spread >= 13:
            base_edge = 7.0
            reasons.append(f"Large spread ({abs_spread:.1f}) - contrarian value")
        elif abs_spread >= 10:
            base_edge = 5.0
            reasons.append(f"Large spread ({abs_spread:.1f}) - potential overreaction")

        # Key number bonus
        key_bonus = 0.0
        for key_num, premium in KEY_NUMBERS.items():
            if abs(abs_spread - key_num) < 0.5:
                key_bonus += premium
                reasons.append(f"Near key number {key_num} (+{premium}%)")

        total_edge = base_edge + key_bonus

        if total_edge >= 5.5:
            # Confidence and sizing
            if total_edge >= 9.0:
                confidence, stars = "HIGH", 2.5
            elif total_edge >= 7.5:
                confidence, stars = "MEDIUM-HIGH", 2.0
            elif total_edge >= 6.5:
                confidence, stars = "MEDIUM", 1.5
            else:
                confidence, stars = "LOW-MEDIUM", 1.0

            # Recommend dog on large spreads
            if abs_spread >= 10:
                recommended = f"{away} +{abs_spread:.1f}"
            else:
                recommended = "REVIEW MANUALLY"

            bankroll = 20000
            bet_size = min(bankroll * (stars / 100), bankroll * 0.03)

            opportunities.append(
                {
                    "game": f"{away} @ {home}",
                    "spread": home_spread,
                    "edge": total_edge,
                    "confidence": confidence,
                    "stars": stars,
                    "recommended": recommended,
                    "bet_size": bet_size,
                    "reasons": reasons,
                }
            )

    # Display results
    print(f"\n{'=' * 70}")
    print(f"OPPORTUNITIES FOUND: {len(opportunities)}")
    print(f"{'=' * 70}\n")

    if not opportunities:
        print("[INFO] No qualified opportunities (edge <5.5%)")
        print("[INFO] This is NORMAL - don't force bets!\n")
        print("Billy Walters: 'The best bet is often no bet at all.'\n")
        return

    opportunities.sort(key=lambda x: x["edge"], reverse=True)

    for i, opp in enumerate(opportunities, 1):
        print(f"[OPPORTUNITY #{i}]")
        print(f"Game: {opp['game']}")
        print(f"Edge: {opp['edge']:.1f}%")
        print(f"Confidence: {opp['confidence']}")
        print(f"Stars: {opp['stars']}")
        print(f"Recommended: {opp['recommended']}")
        print(f"Bet Size: ${opp['bet_size']:.0f} ({opp['bet_size'] / 200:.1f}%)")
        print("Reasons:")
        for reason in opp["reasons"]:
            print(f"  - {reason}")
        print("-" * 70 + "\n")

    # Risk summary
    total_exposure = sum(opp["bet_size"] for opp in opportunities)
    exposure_pct = (total_exposure / 20000) * 100

    print(f"\n{'=' * 70}")
    print("RISK MANAGEMENT SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total Opportunities: {len(opportunities)}")
    print(f"Total Exposure: ${total_exposure:.0f} ({exposure_pct:.1f}%)")

    if exposure_pct > 15:
        print("[WARNING] Exceeds 15% weekly limit!")
    else:
        print("[OK] Within 15% weekly limit")

    if max(o["bet_size"] for o in opportunities) > 600:
        print("[WARNING] Single bet exceeds 3% limit!")
    else:
        print("[OK] All bets within 3% limit")

    print(f"\n{'=' * 70}\n")

    # Save
    output_dir = Path("output/week12")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"week12_quick_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "opportunities": opportunities,
                "risk_summary": {
                    "total_exposure": total_exposure,
                    "exposure_pct": exposure_pct,
                    "num_bets": len(opportunities),
                },
            },
            f,
            indent=2,
        )

    print(f"[OK] Saved: {output_file}\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Billy Walters NFL Week 12 Quick Analysis")
    print("For Educational Research Purposes Only")
    print("=" * 70)

    try:
        asyncio.run(quick_analyze())
    except KeyboardInterrupt:
        print("\n[CANCELLED]")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback

        traceback.print_exc()
