"""
Example usage of Billy Walters Power Rating System

This script demonstrates:
1. Loading initial power ratings
2. Calculating matchup spreads
3. Updating ratings after games
4. Predicting spreads with injury adjustments
"""

from pathlib import Path
from datetime import date

# Add parent directory to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from walters_analyzer.valuation.power_ratings import (
    PowerRatingSystem,
    GameResult,
    initialize_nfl_ratings,
    initialize_ncaaf_ratings,
)
from walters_analyzer.valuation.core import BillyWaltersValuation


def example_1_basic_power_ratings():
    """Example 1: Basic power rating operations"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Power Rating Operations")
    print("=" * 80)

    # Initialize power rating system
    prs = PowerRatingSystem()

    # Load NFL ratings
    nfl_ratings = initialize_nfl_ratings()
    prs.import_ratings(nfl_ratings)

    print(f"\nLoaded {len(prs.ratings)} NFL team ratings")

    # Show top 5 teams
    print("\nTop 5 Teams:")
    for i, (team, rating) in enumerate(prs.get_top_teams(5), 1):
        print(f"  {i}. {team:<20} {rating:.1f}")

    # Show bottom 5 teams
    print("\nBottom 5 Teams:")
    for i, (team, rating) in enumerate(prs.get_bottom_teams(5), 1):
        print(f"  {i}. {team:<20} {rating:.1f}")


def example_2_calculate_spreads():
    """Example 2: Calculate predicted spreads"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Calculate Predicted Spreads")
    print("=" * 80)

    prs = PowerRatingSystem()
    prs.import_ratings(initialize_nfl_ratings())

    matchups = [
        ("Kansas City", "Buffalo"),
        ("San Francisco", "Dallas"),
        ("Baltimore", "Cincinnati"),
        ("Philadelphia", "Detroit"),
    ]

    print("\nPredicted Spreads (Home team favored when positive):")
    print(f"{'Matchup':<40} {'Spread':<10} {'Breakdown'}")
    print("-" * 80)

    for home, away in matchups:
        spread = prs.calculate_matchup_spread(home, away)
        home_rating = prs.get_rating(home)
        away_rating = prs.get_rating(away)

        if spread is not None:
            matchup_str = f"{away} @ {home}"
            breakdown = f"{home_rating:.1f} - {away_rating:.1f} + 2.0 HFA"
            print(f"{matchup_str:<40} {spread:>+6.1f}     {breakdown}")


def example_3_update_ratings():
    """Example 3: Update ratings after a game"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Update Ratings After Games")
    print("=" * 80)

    prs = PowerRatingSystem()
    prs.import_ratings(initialize_nfl_ratings())

    # Kansas City vs Buffalo game
    print("\nBefore Game:")
    kc_before = prs.get_rating("Kansas City")
    buf_before = prs.get_rating("Buffalo")
    print(f"  Kansas City: {kc_before:.2f}")
    print(f"  Buffalo:     {buf_before:.2f}")

    expected_spread = prs.calculate_matchup_spread("Kansas City", "Buffalo")
    print(f"  Expected Spread: Kansas City {expected_spread:+.1f}")

    # Simulate game result: KC wins 27-24 at home
    game = GameResult(
        date=date.today(),
        home_team="Kansas City",
        away_team="Buffalo",
        home_score=27,
        away_score=24,
        location="home",
    )

    print("\nGame Result: Kansas City 27 - Buffalo 24")
    print("  Actual Margin: +3")
    print(f"  Expected Margin: {expected_spread:+.1f}")
    print(f"  Performance: {'Under' if 3 < expected_spread else 'Met'} expectations")

    # Update ratings
    kc_new, buf_new = prs.update_ratings_from_game(game)

    print("\nAfter Game:")
    print(f"  Kansas City: {kc_before:.2f} -> {kc_new:.2f} ({kc_new - kc_before:+.2f})")
    print(
        f"  Buffalo:     {buf_before:.2f} -> {buf_new:.2f} ({buf_new - buf_before:+.2f})"
    )


def example_4_november_7_memphis():
    """Example 4: November 7, 2025 Memphis example from PRD"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: November 7, 2025 - Memphis Game (PRD Example)")
    print("=" * 80)

    prs = PowerRatingSystem()
    prs.import_ratings(initialize_ncaaf_ratings())

    # Verify teams are loaded
    if not prs.get_rating("Memphis") or not prs.get_rating("Tulane"):
        print("\nNote: Memphis/Tulane not in initial ratings, adding them...")
        prs.set_rating("Memphis", 11.0)
        prs.set_rating("Tulane", 7.0)

    # Set ratings to produce the PRD example
    # Memphis -6 predicted, Market at -3.5
    # Need: Memphis rating - Tulane rating + 2.0 HFA = 6.0
    # So: Memphis rating - Tulane rating = 4.0

    print("\nScenario from PRD (lines 547-551):")
    print("  Game: Tulane @ Memphis")
    print("  Market Spread: Memphis -3.5")

    # Get our predicted spread
    our_spread = prs.calculate_matchup_spread("Memphis", "Tulane")
    market_spread = 3.5

    print(f"  Our Spread: Memphis {our_spread:+.1f}")

    if our_spread:
        edge = our_spread - market_spread
        print("\n  Edge Calculation:")
        print(f"    Our Line: {our_spread:.1f}")
        print(f"    Market Line: {market_spread:.1f}")
        print(f"    Edge: {edge:.1f} points")

        if abs(edge) >= 2.5:
            if edge > 0:
                print(
                    f"\n  [YES] EDGE DETECTED: Memphis -{market_spread} has {edge:.1f}-point edge"
                )
                print("    BET: Memphis (favorite has value)")
            else:
                print(
                    f"\n  [YES] EDGE DETECTED: Tulane +{market_spread} has {abs(edge):.1f}-point edge"
                )
                print("    BET: Tulane (underdog getting too many points)")
        else:
            print(f"\n  [NO] NO EDGE: {abs(edge):.1f} points below 2.5 threshold")


def example_5_integrated_valuation():
    """Example 5: Integrated valuation with injuries"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Integrated Valuation with Injuries")
    print("=" * 80)

    # Initialize the full Billy Walters system
    bw = BillyWaltersValuation(sport="NFL")

    print("\nCalculating spread with power ratings + injuries")
    print("Matchup: Kansas City vs Buffalo")

    # Base spread (no injuries)
    base_spread = bw.calculate_predicted_spread("Kansas City", "Buffalo")
    print(f"\n1. Base Spread (Power Ratings + HFA): {base_spread:+.1f}")

    # With injuries
    home_injuries = [
        {
            "player_name": "Travis Kelce",
            "position": "TE",
            "injury_status": "Questionable",
            "injury_type": "Ankle",
        }
    ]

    adjusted_spread = bw.calculate_predicted_spread(
        "Kansas City", "Buffalo", home_injuries=home_injuries
    )

    injury_impact = adjusted_spread - base_spread if adjusted_spread else 0
    print(f"2. With Kelce (TE) Questionable: {adjusted_spread:+.1f}")
    print(f"   Injury Impact: {injury_impact:+.1f} points")

    # Show power ratings
    kc_rating = bw.get_power_rating("Kansas City")
    buf_rating = bw.get_power_rating("Buffalo")
    print("\nPower Ratings:")
    print(f"  Kansas City: {kc_rating:.1f}")
    print(f"  Buffalo: {buf_rating:.1f}")
    print(f"  Differential: {kc_rating - buf_rating:+.1f} points")


def example_6_season_simulation():
    """Example 6: Simulate a few weeks of ratings updates"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Season Simulation - Ratings Evolution")
    print("=" * 80)

    prs = PowerRatingSystem()
    prs.import_ratings(initialize_nfl_ratings())

    # Simulate Week 1 games
    week1_games = [
        GameResult(date(2024, 9, 8), "Kansas City", "Baltimore", 27, 20),
        GameResult(date(2024, 9, 8), "San Francisco", "Pittsburgh", 30, 7),
        GameResult(date(2024, 9, 8), "Buffalo", "New York Jets", 21, 16),
    ]

    print("\nWeek 1 Results and Rating Changes:")
    print(f"{'Game':<35} {'Before':<20} {'After':<20} {'Change'}")
    print("-" * 80)

    for game in week1_games:
        home_before = prs.get_rating(game.home_team)
        away_before = prs.get_rating(game.away_team)

        home_new, away_new = prs.update_ratings_from_game(game)

        result_str = (
            f"{game.away_team} @ {game.home_team} ({game.away_score}-{game.home_score})"
        )
        before_str = f"H:{home_before:.1f} A:{away_before:.1f}"
        after_str = f"H:{home_new:.1f} A:{away_new:.1f}"
        change_str = f"H:{home_new - home_before:+.2f} A:{away_new - away_before:+.2f}"

        print(f"{result_str:<35} {before_str:<20} {after_str:<20} {change_str}")

    print("\nUpdated Top 5:")
    for i, (team, rating) in enumerate(prs.get_top_teams(5), 1):
        print(f"  {i}. {team:<20} {rating:.2f}")


def main():
    """Run all examples"""
    examples = [
        example_1_basic_power_ratings,
        example_2_calculate_spreads,
        example_3_update_ratings,
        example_4_november_7_memphis,
        example_5_integrated_valuation,
        example_6_season_simulation,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n[ERROR] Error in {example.__name__}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
