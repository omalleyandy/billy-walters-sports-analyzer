"""
Week 12 Live Odds Scraper with Edge Detection
Combines Overtime.ag API with Billy Walters Edge Calculator

This script:
1. Fetches LIVE odds from Overtime.ag
2. Identifies Week 12 NFL games
3. Calculates edges using Billy Walters methodology
4. Shows betting recommendations with actual spreads

Usage:
    python scrape_week12_odds.py
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from billy_walters_edge_calculator import BillyWaltersEdgeCalculator

# Inline simplified Overtime API client (no external dependencies)
import httpx


class OvertimeApiClient:
    """Client for Overtime.ag API"""

    BASE_URL = "https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering"

    async def fetch_nfl_games(self):
        """Fetch live NFL games from Overtime.ag"""
        payload = {
            "sportType": "Football",
            "sportSubType": "NFL",
            "wagerType": "Straight Bet",
            "hoursAdjustment": 0,
            "periodNumber": 0,  # Full game
            "gameNum": None,
            "parentGameNum": None,
            "teaserName": "",
            "requestMode": "G",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.BASE_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            if "d" in data and "Data" in data["d"] and "GameLines" in data["d"]["Data"]:
                return data["d"]["Data"]["GameLines"]

            return []


# Week 12 Expected Matchups and Power Ratings
WEEK12_GAMES = {
    "IND @ KC": {
        "our_line": 0.5,  # IND slight underdog
        "sfactor_points": 11.25,  # Bye week + motivation
        "notes": "Colts off bye, playoff push",
        "priority": "HIGH",
        "expected_bet": 500,
    },
    "LAR @ TB": {
        "our_line": -3.0,  # LAR favorite by 3
        "sfactor_points": 7.5,  # Revenge + travel
        "notes": "Rams revenge for playoff loss",
        "priority": "HIGH",
        "expected_bet": 400,
    },
    "CIN vs NE": {
        "our_line": -4.5,  # CIN favorite
        "sfactor_points": 5.0,  # Home field
        "notes": "[WARNING] CONDITIONAL - Only if Ja'Marr Chase OUT",
        "priority": "CONDITIONAL",
        "expected_bet": 300,
    },
    "BUF @ HOU": {
        "our_line": -8.0,  # BUF big favorite
        "sfactor_points": 3.75,  # Motivation
        "notes": "[WARNING] CONDITIONAL - Only if C.J. Stroud OUT",
        "priority": "CONDITIONAL",
        "expected_bet": 500,
    },
    "GB vs MIN": {
        "our_line": -0.5,  # GB slight favorite
        "sfactor_points": 3.75,  # Home field
        "notes": "[WARNING] CONDITIONAL - Only if Josh Jacobs PLAYS",
        "priority": "CONDITIONAL",
        "expected_bet": 200,
    },
}


def match_game(away_team: str, home_team: str) -> str:
    """Match game to our Week 12 list"""
    # Normalize team names for matching
    away_norm = away_team.upper().replace(" ", "")
    home_norm = home_team.upper().replace(" ", "")

    for game_key in WEEK12_GAMES.keys():
        parts = game_key.split(" @ " if " @ " in game_key else " vs ")
        if len(parts) == 2:
            expected_away = parts[0].upper().replace(" ", "")
            expected_home = parts[1].upper().replace(" ", "")

            # Check if teams match (abbreviation or full name)
            if (away_norm in expected_away or expected_away in away_norm) and (
                home_norm in expected_home or expected_home in home_norm
            ):
                return game_key

    return None


async def scrape_and_analyze():
    """Scrape Overtime.ag and analyze edges"""
    print("=" * 80)
    print("WEEK 12 LIVE ODDS SCRAPER - OVERTIME.AG")
    print(f"Scraped: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
    print("=" * 80)

    # Initialize clients
    overtime_client = OvertimeApiClient()
    edge_calc = BillyWaltersEdgeCalculator()
    bankroll = 20000.0

    print("\n[*] Fetching live NFL odds from Overtime.ag...")

    try:
        games = await overtime_client.fetch_nfl_games()
        print(f"[*] Received {len(games)} NFL games")
    except Exception as e:
        print(f"[ERROR] Error fetching odds: {e}")
        return

    # Filter and analyze Week 12 games
    print("\n" + "=" * 80)
    print("ANALYZING WEEK 12 GAMES")
    print("=" * 80)

    qualified_bets = []
    total_risk = 0

    for game in games:
        # Extract team names
        away_team = game.get("Team1ID", "")
        home_team = game.get("Team2ID", "")

        # Match to our Week 12 games
        game_key = match_game(away_team, home_team)
        if not game_key:
            continue  # Not a Week 12 game we're tracking

        game_config = WEEK12_GAMES[game_key]

        # Extract Overtime spreads
        # Team1 = Away, Team2 = Home
        away_spread = float(game.get("Spread1", 0) or 0)
        home_spread = float(game.get("Spread2", 0) or 0)

        # Use away spread as the market line
        # If away_spread is positive (+3.5), away team is underdog
        # If away_spread is negative (-3.5), away team is favorite
        overtime_line = away_spread

        print(f"\n{'=' * 80}")
        print(f"[NFL] {game_key}")
        print(f"{'=' * 80}")
        print(f"[*] Game Time: {game.get('GameDateTimeString', 'TBD')}")
        print(f"[NOTE] Notes: {game_config['notes']}")
        print(f"[TARGET] Priority: {game_config['priority']}")

        print("\n[CHART] OVERTIME.AG LIVE ODDS:")
        print(f"   {away_team}: {away_spread:+.1f}")
        print(f"   {home_team}: {home_spread:+.1f}")

        # Calculate edge
        result = edge_calc.calculate_complete_edge(
            our_line=game_config["our_line"],
            market_line=overtime_line,
            sfactor_points=game_config["sfactor_points"],
        )

        print("\n[INFO] EDGE ANALYSIS:")
        print(f"   Our Line: {game_config['our_line']:+.1f}")
        print(f"   Overtime Line: {overtime_line:+.1f}")
        print(f"   Base Edge: {result.base_edge_points:.1f} points")
        print(f"   S-Factors: +{result.sfactor_adjustment_points:.2f} points")
        print(f"   Key Numbers: {result.crossed_key_numbers}")
        print(f"   Key Premium: +{result.key_number_premium_pct:.1f}%")

        print(f"\n[TARGET] TOTAL EDGE: {result.total_edge_pct:.1f}%")
        print(f"   Confidence: {result.confidence_level}")
        print(f"   [STAR] Stars: {result.star_rating}")

        # Calculate bet size
        bet_amount = result.recommended_bet_pct * bankroll

        print("\n[MONEY] BET SIZING:")
        print(
            f"   Recommended: ${bet_amount:.0f} ({result.recommended_bet_pct * 100:.1f}%)"
        )

        # Warnings
        if result.warnings:
            print("\n[WARNING]  WARNINGS:")
            for warning in result.warnings:
                print(f"   {warning}")

        # Recommendation
        print(f"\n{'=' * 80}")
        if result.total_edge_pct >= 5.5 and result.star_rating > 0:
            print(f"[*] RECOMMENDATION: BET ${bet_amount:.0f}")

            # Determine which team to bet
            if overtime_line > 0:
                bet_team = away_team
                bet_line = f"+{overtime_line:.1f}"
            else:
                bet_team = home_team
                bet_line = f"{overtime_line:.1f}"

            print(f"\n[TARGET] BET: {bet_team} {bet_line}")
            print(f"{'=' * 80}")

            qualified_bets.append(
                {
                    "game": game_key,
                    "bet_team": bet_team,
                    "line": bet_line,
                    "amount": bet_amount,
                    "edge": result.total_edge_pct,
                    "stars": result.star_rating,
                    "priority": game_config["priority"],
                }
            )
            total_risk += bet_amount
        else:
            print("[ERROR] RECOMMENDATION: NO BET (Edge below 5.5% minimum)")
            print(f"{'=' * 80}")

    # Summary
    print("\n\n" + "=" * 80)
    print("[LIST] BETTING SUMMARY")
    print("=" * 80)

    if qualified_bets:
        print(f"\n[*] QUALIFIED BETS ({len(qualified_bets)} games):")

        # Sort by priority
        qualified_bets.sort(key=lambda x: (x["priority"] != "HIGH", -x["edge"]))

        for bet in qualified_bets:
            print(f"\n   [TARGET] {bet['game']}")
            print(f"      Team: {bet['bet_team']} {bet['line']}")
            print(f"      Amount: ${bet['amount']:.0f}")
            print(f"      Edge: {bet['edge']:.1f}%")
            print(f"      Stars: {bet['stars']} [STAR]")
            print(f"      Priority: {bet['priority']}")

        print(f"\n{'=' * 80}")
        print(
            f"[MONEY] TOTAL RISK: ${total_risk:.0f} ({total_risk / bankroll * 100:.1f}%)"
        )

        if total_risk / bankroll <= 0.15:
            print("[*] Within 15% weekly limit")
        else:
            print("[WARNING]  EXCEEDS 15% weekly limit!")

        print("\n[NOTE] NEXT STEPS:")
        print("   1. Go to overtime.ag/sports#/nfl")
        print("   2. Verify lines haven't moved")
        print("   3. Place bets in priority order")
        print("   4. Screenshot confirmations")

    else:
        print("\n[ERROR] NO QUALIFIED BETS")
        print("   • All games below 5.5% minimum edge")
        print("   • Wait for better lines or skip this week")

    print("\n" + "=" * 80)
    print("[WARNING]  REMEMBER: Only bet if edge >= 5.5%!")
    print("=" * 80)

    # Save results
    output = {
        "scrape_time": datetime.now().isoformat(),
        "bankroll": bankroll,
        "qualified_bets": qualified_bets,
        "total_risk": total_risk,
        "risk_percentage": (total_risk / bankroll * 100),
    }

    output_file = Path("output/week12_live_odds.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(output, indent=2))

    print(f"\n[*] Results saved to: {output_file}")
    print("\nGood luck! [NFL][MONEY]\n")


def main():
    """Main entry point"""
    asyncio.run(scrape_and_analyze())


if __name__ == "__main__":
    main()
