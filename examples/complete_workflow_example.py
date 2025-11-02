"""
Complete Billy Walters Workflow Example

This script demonstrates the full workflow using all core components:
1. Power Ratings
2. S/W/E Factors
3. Key Numbers
4. Bet Sizing (Star System)
5. CLV Tracking

Run this to see how everything works together.
"""

from walters_analyzer.analyzer import BillyWaltersAnalyzer
from walters_analyzer.situational_factors import GameContext
from walters_analyzer.power_ratings import GameResult


def main():
    print("=" * 70)
    print("BILLY WALTERS SPORTS ANALYZER - COMPLETE WORKFLOW DEMO")
    print("=" * 70)
    print()

    # Step 1: Initialize the analyzer
    print("Step 1: Initializing Billy Walters Analyzer...")
    print("-" * 70)

    bankroll = 10000.0  # $10,000 starting bankroll
    analyzer = BillyWaltersAnalyzer(
        bankroll=bankroll,
        ratings_file="data/power_ratings/demo_ratings.json",
        bets_db="data/bets/demo_bets.db"
    )

    print(f"Starting Bankroll: ${bankroll:,.2f}")
    print()

    # Step 2: Build power ratings from historical games
    print("Step 2: Building Power Ratings from Historical Games...")
    print("-" * 70)

    # Simulate some historical games to build ratings
    historical_games = [
        # CFB Games
        GameResult("Alabama", "Mississippi State", 49, 9, True, "cfb", "2024-10-26"),
        GameResult("Georgia", "Texas", 30, 15, False, "cfb", "2024-10-19"),
        GameResult("Ohio State", "Penn State", 20, 13, True, "cfb", "2024-10-26"),
        GameResult("Oregon", "Illinois", 38, 9, True, "cfb", "2024-10-26"),
        GameResult("LSU", "Arkansas", 34, 10, True, "cfb", "2024-10-19"),
        GameResult("Alabama", "Tennessee", 24, 17, False, "cfb", "2024-10-19"),
        GameResult("Georgia", "Florida", 34, 20, False, "cfb", "2024-11-02"),

        # NFL Games
        GameResult("Chiefs", "Raiders", 27, 20, True, "nfl", "2024-10-27"),
        GameResult("Ravens", "Buccaneers", 41, 31, True, "nfl", "2024-10-21"),
        GameResult("49ers", "Cowboys", 30, 24, True, "nfl", "2024-10-27"),
        GameResult("Lions", "Vikings", 31, 29, True, "nfl", "2024-10-20"),
        GameResult("Bills", "Titans", 34, 10, True, "nfl", "2024-10-27"),
    ]

    for game in historical_games:
        analyzer.update_power_ratings(game)
        print(f"  Updated: {game.team} vs {game.opponent} ({game.sport.upper()})")

    print()

    # Show current ratings
    print("Current Power Ratings:")
    print()

    print("  CFB Top Teams:")
    cfb_ratings = analyzer.get_team_ratings(sport="cfb")
    for rating in cfb_ratings[:5]:
        print(f"    {rating['team']:20s} {rating['rating']:+6.2f} ({rating['games_played']} games)")

    print()
    print("  NFL Top Teams:")
    nfl_ratings = analyzer.get_team_ratings(sport="nfl")
    for rating in nfl_ratings[:5]:
        print(f"    {rating['team']:20s} {rating['rating']:+6.2f} ({rating['games_played']} games)")

    print()

    # Step 3: Analyze a game with complete context
    print("Step 3: Analyzing Upcoming Game (Alabama @ LSU)...")
    print("-" * 70)

    # Create game context with S/W/E factors
    game_context = GameContext(
        team="Alabama",
        opponent="LSU",
        sport="cfb",
        is_home=False,  # Alabama is away
        game_date="2024-11-09",

        # Situational factors
        team_rest_days=7,
        opponent_rest_days=7,
        travel_miles=300,  # Not too far
        is_divisional=False,
        is_conference=True,  # SEC conference game
        is_rivalry=True,    # Historic rivalry!
        is_revenge=False,
        team_ats_last_5=3,  # 3-2 ATS
        opponent_ats_last_5=-2,  # 1-4 ATS

        # Weather factors (Death Valley at night)
        wind_speed_mph=8,
        precipitation_prob=20,
        temperature_f=68,
        is_dome=False,

        # Emotional factors
        playoff_implications="seeding",  # Both teams in playoff hunt
        coaching_change=False,
        injury_motivation=False
    )

    # Analyze the game
    analysis = analyzer.analyze_game(
        away_team="Alabama",
        home_team="LSU",
        sport="cfb",
        market_spread=-3.0,  # Alabama favored by 3
        market_total=55.5,
        spread_price=-110,
        game_context=game_context,
        game_date="2024-11-09"
    )

    # Display analysis
    print()
    print(f"Game: {analysis.game}")
    print()

    print("POWER RATINGS:")
    print(f"  Alabama Rating: {analysis.away_rating:+.2f}")
    print(f"  LSU Rating:     {analysis.home_rating:+.2f}")
    print(f"  Predicted Spread: {analysis.predicted_spread:.1f} (negative = LSU favored)")
    print(f"  Market Spread:    {analysis.market_spread:.1f}")
    print(f"  Edge: {abs(analysis.predicted_spread - analysis.market_spread):.1f} points")
    print()

    print("S/W/E FACTORS:")
    print(f"  {analysis.swe_summary}")
    print(f"  Spread Adjustment: {analysis.swe_spread_adjustment:+.1f} points")
    print()

    print("KEY NUMBER ANALYSIS:")
    print(f"  Key Numbers Crossed: {analysis.key_number_analysis.key_numbers_crossed}")
    print(f"  Edge Percentage: {analysis.edge_percentage*100:.2f}%")
    print()

    print("BET RECOMMENDATION:")
    if analysis.should_bet:
        rec = analysis.recommendation
        print(f"  ⭐ {rec.stars} STAR BET")
        print(f"  Side: {rec.side.upper()} {analysis.away_team if rec.side == 'away' else analysis.home_team}")
        print(f"  Line: {rec.line}")
        print(f"  Price: {rec.price}")
        print(f"  Bet Amount: ${rec.bet_amount:,.2f} ({rec.bet_percentage:.2f}% of bankroll)")
        print(f"  Confidence: {rec.confidence}")
        print(f"  Expected Value: ${rec.expected_value:,.2f}")
        print(f"  Risk of Ruin: {rec.risk_of_ruin*100:.2f}%")
        print()
        print(f"  Reasoning: {rec.reasoning}")
    else:
        print(f"  NO BET - {analysis.reasoning}")

    print()

    # Step 4: Place the bet (if recommended)
    if analysis.should_bet:
        print("Step 4: Placing Bet and Logging in CLV Tracker...")
        print("-" * 70)

        bet_id = analyzer.place_bet(analysis, game_date="2024-11-09")

        print(f"  Bet placed! Bet ID: {bet_id}")
        print(f"  Remaining Bankroll: ${analyzer.bankroll:,.2f}")
        print()

        # Step 5: Simulate game completion and update results
        print("Step 5: Simulating Game Completion...")
        print("-" * 70)

        # Simulate: Alabama wins 31-28 (covered the -3 spread)
        print("  Final Score: Alabama 31, LSU 28")
        print("  Spread Result: Alabama -3 ✓ (WIN)")
        print()

        # Update closing line (moved to -3.5)
        closing_spread = -3.5
        print(f"  Opening Line: {analysis.market_spread}")
        print(f"  Closing Line: {closing_spread}")
        print(f"  CLV: {closing_spread - analysis.market_spread:+.1f} points (POSITIVE - you beat the close!)")
        print()

        # Calculate profit (assume $100 bet at -110)
        bet_amount = analysis.recommendation.bet_amount
        profit = bet_amount * (100 / 110)  # Win at -110

        # Update result
        analyzer.update_game_result(
            bet_id=bet_id,
            closing_line=closing_spread,
            actual_result="win",
            profit=profit
        )

        print(f"  Profit: ${profit:,.2f}")
        print(f"  New Bankroll: ${analyzer.bankroll:,.2f}")
        print()

    # Step 6: Generate performance report
    print("Step 6: Performance Report...")
    print("-" * 70)
    print()

    report = analyzer.get_performance_report()
    print(report)
    print()

    # Step 7: Save state
    print("Step 7: Saving State...")
    print("-" * 70)
    analyzer.save_state()
    print("  Power ratings saved to data/power_ratings/demo_ratings.json")
    print("  Bet history saved to data/bets/demo_bets.db")
    print()

    # Clean up
    analyzer.close()

    print("=" * 70)
    print("DEMO COMPLETE!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("  1. Integrate with live odds scraper (overtime.ag)")
    print("  2. Automate S/W/E factor collection")
    print("  3. Set up daily betting workflow")
    print("  4. Backtest strategy on historical data")
    print("  5. Monitor CLV and adjust thresholds")
    print()


if __name__ == "__main__":
    main()
