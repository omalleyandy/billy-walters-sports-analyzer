"""
Run Power Rating System Backtest on NFL 2024 Season Data (Weeks 1-9)

This script validates the Billy Walters 90/10 power rating formula
against actual NFL game results from the 2024 season.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from walters_analyzer.backtest.power_rating_backtest import PowerRatingBacktest


def main():
    """Run comprehensive backtest"""
    print("=" * 80)
    print("BILLY WALTERS POWER RATING SYSTEM - BACKTEST")
    print("NFL 2025 Season - Weeks 1-9")
    print("=" * 80)
    print()
    
    # Load game data
    data_file = Path(__file__).parent.parent / "data" / "nfl_2025_games_weeks_1_9.json"
    print(f"Loading game data from: {data_file}")
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    games = data['games']
    print(f"Loaded {len(games)} games from weeks 1-9")
    print()
    
    # Initialize backtest
    print("Initializing Power Rating System with NFL 2025 preseason ratings...")
    backtest = PowerRatingBacktest()
    print(f"Starting with {len(backtest.initial_ratings)} teams")
    print()
    
    # Show initial top 5
    print("Initial Top 5 Teams:")
    top_5 = sorted(backtest.initial_ratings.items(), key=lambda x: x[1], reverse=True)[:5]
    for i, (team, rating) in enumerate(top_5, 1):
        print(f"  {i}. {team:<25} {rating:.2f}")
    print()
    
    # Run backtest
    print("Running backtest...")
    print("(Making predictions and updating ratings after each game)")
    print()
    
    result = backtest.run_backtest(games)
    
    # Generate and display report
    report = backtest.generate_report(result)
    print(report)
    
    # Save report to file
    output_file = Path(__file__).parent.parent / "POWER_RATING_BACKTEST_REPORT.md"
    with open(output_file, 'w') as f:
        f.write("# Power Rating System Backtest Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(report)
    
    print()
    print("=" * 80)
    print(f"Full report saved to: {output_file}")
    print("=" * 80)
    
    # Summary statistics
    print()
    print("QUICK SUMMARY:")
    print(f"  Games Analyzed: {result.total_games}")
    print(f"  Winner Accuracy: {result.correct_winner_pct:.1%}")
    print(f"  ATS Record: {result.ats_record[0]}-{result.ats_record[1]}")
    print(f"  ATS Win Rate: {result.ats_win_pct:.1%}")
    print(f"  Mean Error: {result.mean_absolute_error:.2f} points")
    print(f"  Median Error: {result.median_absolute_error:.2f} points")
    print()
    
    # Rating evolution highlights
    print("TOP 5 RATING CHANGES:")
    for i, (team, change) in enumerate(result.biggest_movers[:5], 1):
        initial = result.initial_ratings[team]
        final = result.final_ratings[team]
        direction = "UP" if change > 0 else "DOWN"
        print(f"  {i}. {team:<25} {initial:.2f} -> {final:.2f} ({change:+.2f}) {direction}")
    print()
    
    # Best week
    if result.weekly_stats:
        best_week = max(result.weekly_stats.items(), 
                       key=lambda x: x[1]['ats_accuracy'])
        print(f"BEST WEEK: Week {best_week[0]}")
        print(f"  ATS: {best_week[1]['ats_accuracy']:.1%}")
        print(f"  Winner: {best_week[1]['winner_accuracy']:.1%}")
        print(f"  Avg Error: {best_week[1]['avg_error']:.2f} points")
    
    print()
    print("Backtest complete!")


if __name__ == "__main__":
    main()

