#!/usr/bin/env python3
"""
Week 12 NFL Analysis - Working Version
Uses actual available modules from your project
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "clients"))

from src.data.overtime_api_client import OvertimeApiClient
from src.data.massey_ratings_scraper import MasseyRatingsScraper


async def analyze_week12():
    """
    Week 12 NFL Analysis using Billy Walters methodology

    Workflow:
    1. Get current odds from Overtime.ag
    2. Get power ratings from Massey
    3. Calculate edges and identify opportunities
    4. Apply Billy Walters risk management
    """

    print("\n" + "=" * 70)
    print("WEEK 12 NFL ANALYSIS - Billy Walters Methodology")
    print("=" * 70)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")

    # Initialize collectors
    opportunities = []

    # ========================================================================
    # STEP 1: Get Overtime.ag Odds (Primary Source)
    # ========================================================================
    print("[STEP 1] Fetching Overtime.ag odds...")
    print("-" * 70)

    try:
        overtime = OvertimeApiClient()
        odds_data = await overtime.scrape_nfl()
        games = odds_data.get("games", [])
        print(f"[OK] Overtime: {len(games)} games found")

        # Display games
        for i, game in enumerate(games, 1):
            away = game.get("away_team", "Unknown")
            home = game.get("home_team", "Unknown")
            spread = game.get("spread", {}).get("home", "N/A")
            total = game.get("total", {}).get("points", "N/A")

            print(f"  {i}. {away} @ {home}")
            print(f"     Spread: {home} {spread:+.1f} | Total: {total}")

    except Exception as e:
        print(f"[ERROR] Overtime scraping failed: {e}")
        games = []

    print()

    # ========================================================================
    # STEP 2: Get Massey Power Ratings (Optional - may be slow)
    # ========================================================================
    print("[STEP 2] Fetching Massey power ratings...")
    print("-" * 70)
    print("[INFO] This uses Playwright and may take 30-60 seconds...")

    try:
        massey = MasseyRatingsScraper()
        ratings_data = await massey.scrape_nfl_ratings(save=True)
        teams = ratings_data.get("teams", [])
        print(f"[OK] Massey: {len(teams)} teams rated")

        # Create quick lookup dict
        massey_ratings = {}
        for team in teams:
            team_name = team.get("team", "")
            rating = team.get("rating", "0")
            try:
                massey_ratings[team_name] = float(rating)
            except ValueError:
                massey_ratings[team_name] = 0.0

        print(f"[OK] Converted {len(massey_ratings)} ratings to lookup")

    except Exception as e:
        print(f"[ERROR] Massey scraping failed: {e}")
        print("[INFO] Continuing without power ratings...")
        massey_ratings = {}

    print()

    # ========================================================================
    # STEP 3: Calculate Edges & Identify Opportunities
    # ========================================================================
    print("[STEP 3] Calculating edges...")
    print("-" * 70)
    print("[CRITERIA] Billy Walters Requirements:")
    print("  - Minimum 5.5% edge")
    print("  - Maximum 3% single bet risk")
    print("  - Key numbers: 3, 7, 6, 14")
    print("  - Look for: Large spreads, key number crosses, contrarian value")
    print("-" * 70 + "\n")

    if not games:
        print("[WARNING] No games to analyze!")
        return

    # Billy Walters key numbers (most common final margins)
    KEY_NUMBERS = {
        3: 1.5,  # Most common (field goal) - 1.5% edge premium
        7: 1.2,  # Second most common (TD) - 1.2% edge premium
        6: 1.0,  # Common (TD + missed XP) - 1.0% edge premium
        14: 0.8,  # Two TDs - 0.8% edge premium
    }

    for game in games:
        away = game.get("away_team", "Unknown")
        home = game.get("home_team", "Unknown")
        spread_data = game.get("spread", {})
        total_data = game.get("total", {})

        # Get spread (negative = home favorite)
        try:
            home_spread = float(spread_data.get("home", 0))
        except (ValueError, TypeError):
            continue

        # Get total
        try:
            total = float(total_data.get("points", 47))
        except (ValueError, TypeError):
            total = 47.0

        # ====================================================================
        # EDGE CALCULATION
        # ====================================================================

        # Base edge from large spread (market typically overreacts)
        base_edge = 0.0
        confidence = "NONE"
        reasons = []

        # Large spread contrarian strategy
        abs_spread = abs(home_spread)
        if abs_spread >= 13:
            base_edge = 7.0
            confidence = "MEDIUM"
            reasons.append(f"Large spread ({abs_spread:.1f}) - contrarian value")
        elif abs_spread >= 10:
            base_edge = 5.0
            confidence = "LOW"
            reasons.append(f"Large spread ({abs_spread:.1f}) - potential overreaction")

        # Key number premium
        key_bonus = 0.0
        for key_num, premium in KEY_NUMBERS.items():
            # Check if spread crosses or lands near key number
            if abs(abs_spread - key_num) < 0.5:
                key_bonus += premium
                reasons.append(f"Near key number {key_num} (+{premium}%)")

        # Power rating differential (if Massey available)
        power_edge = 0.0
        if massey_ratings and home in massey_ratings and away in massey_ratings:
            home_rating = massey_ratings[home]
            away_rating = massey_ratings[away]
            rating_diff = home_rating - away_rating

            # Compare to market spread (with HFA ~2.5 points)
            expected_spread = rating_diff + 2.5
            spread_discrepancy = abs(expected_spread - home_spread)

            if spread_discrepancy >= 4:
                power_edge = spread_discrepancy * 0.5  # Conservative multiplier
                reasons.append(f"Power rating mismatch ({spread_discrepancy:.1f}pts)")

        # Total edge
        total_edge = base_edge + key_bonus + power_edge

        # ====================================================================
        # OPPORTUNITY EVALUATION
        # ====================================================================

        if total_edge >= 5.5:  # Billy Walters minimum
            # Determine confidence level
            if total_edge >= 9.0:
                confidence = "HIGH"
                stars = 2.5
            elif total_edge >= 7.5:
                confidence = "MEDIUM-HIGH"
                stars = 2.0
            elif total_edge >= 6.5:
                confidence = "MEDIUM"
                stars = 1.5
            else:
                confidence = "LOW-MEDIUM"
                stars = 1.0

            # Recommend side (typically take dog with large spread)
            if abs_spread >= 10:
                recommended_side = f"{away} +{abs_spread:.1f}"
            else:
                recommended_side = "REVIEW MANUALLY"

            # Calculate bet size (Kelly Criterion at 25%)
            bankroll = 20000  # Standard bankroll
            bet_size = min(
                bankroll * (stars / 100),  # Star-based sizing
                bankroll * 0.03,  # Never exceed 3% cap
            )

            opportunities.append(
                {
                    "game": f"{away} @ {home}",
                    "spread": home_spread,
                    "total": total,
                    "edge": total_edge,
                    "confidence": confidence,
                    "stars": stars,
                    "recommended": recommended_side,
                    "bet_size": bet_size,
                    "reasons": reasons,
                }
            )

    # ========================================================================
    # STEP 4: Display Results
    # ========================================================================
    print(f"\n{'=' * 70}")
    print(f"OPPORTUNITIES FOUND: {len(opportunities)}")
    print(f"{'=' * 70}\n")

    if not opportunities:
        print("[INFO] No qualified opportunities this week (edge <5.5%)")
        print("[INFO] This is NORMAL and CORRECT - don't force bets!")
        print("\nBilly Walters: 'The best bet is often no bet at all.'\n")
        return

    # Sort by edge (highest first)
    opportunities.sort(key=lambda x: x["edge"], reverse=True)

    for i, opp in enumerate(opportunities, 1):
        print(f"[OPPORTUNITY #{i}]")
        print(f"Game: {opp['game']}")
        print(f"Edge: {opp['edge']:.1f}%")
        print(f"Confidence: {opp['confidence']}")
        print(f"Stars: {opp['stars']}")
        print(f"Recommended: {opp['recommended']}")
        print(
            f"Bet Size: ${opp['bet_size']:.0f} ({opp['bet_size'] / 200:.1f}% of bankroll)"
        )
        print("Reasons:")
        for reason in opp["reasons"]:
            print(f"  - {reason}")
        print("-" * 70 + "\n")

    # Risk management summary
    total_exposure = sum(opp["bet_size"] for opp in opportunities)
    exposure_pct = (total_exposure / 20000) * 100

    print(f"\n{'=' * 70}")
    print("RISK MANAGEMENT SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total Opportunities: {len(opportunities)}")
    print(f"Total Exposure: ${total_exposure:.0f} ({exposure_pct:.1f}% of bankroll)")
    print(f"Max Single Bet: ${max(o['bet_size'] for o in opportunities):.0f}")
    print(f"Avg Bet Size: ${total_exposure / len(opportunities):.0f}")
    print()

    # Risk compliance check
    if exposure_pct > 15:
        print("[WARNING] Total exposure exceeds 15% limit!")
        print("[ACTION] Reduce bet sizes proportionally")
    else:
        print("[OK] Within 15% weekly exposure limit")

    if max(o["bet_size"] for o in opportunities) > 600:
        print("[WARNING] Single bet exceeds 3% ($600) limit!")
    else:
        print("[OK] All bets within 3% single bet limit")

    print(f"\n{'=' * 70}\n")

    # Save results
    output_dir = Path("output/week12")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"week12_analysis_{timestamp}.json"

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

    print(f"[OK] Results saved to: {output_file}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Billy Walters NFL Week 12 Analysis System")
    print("For Educational Research Purposes Only")
    print("=" * 70)

    try:
        asyncio.run(analyze_week12())
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Analysis interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Analysis failed: {e}")
        import traceback

        traceback.print_exc()
