#!/usr/bin/env python3
"""
Backfill Power Ratings Script - Billy Walters Sports Analyzer

Regenerates power ratings for weeks 1-9 using actual game results and 90/10 formula.

Usage:
    python scripts/backfill_weekly_ratings.py --dry-run
    python scripts/backfill_weekly_ratings.py --start-week 1 --end-week 9
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import date
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from walters_analyzer.valuation.power_ratings import PowerRatingSystem, GameResult

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Backfill power ratings')
    parser.add_argument('--start-week', type=int, default=1)
    parser.add_argument('--end-week', type=int, default=9)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    # Load initial ratings and games
    prs = PowerRatingSystem()
    master_file = project_root / "data" / "power_ratings_nfl_2025.json"
    if master_file.exists():
        prs.load_ratings(master_file)
        logger.info(f"Loaded initial ratings for {len(prs.ratings)} teams")

    # Load game results
    games_file = project_root / "data" / "nfl_2025_games_weeks_1_9.json"
    with open(games_file) as f:
        data = json.load(f)
    all_games = data['games'] if 'games' in data else data

    # Process each week
    ratings_dir = project_root / "data" / "power_ratings"
    ratings_dir.mkdir(exist_ok=True)

    for week_num in range(args.start_week, args.end_week + 1):
        logger.info(f"\n{'='*60}\nWEEK {week_num}\n{'='*60}")
        week_games = [g for g in all_games if g['week'] == week_num]

        for game in week_games:
            result = GameResult(
                date=date.fromisoformat(game['date']),
                home_team=game['home_team'],
                away_team=game['away_team'],
                home_score=game['home_score'],
                away_score=game['away_score'],
                home_injury_level=game.get('home_injury_level', 0.0),
                away_injury_level=game.get('away_injury_level', 0.0),
                location='home'
            )
            logger.info(f"  {result.away_team} @ {result.home_team} ({result.away_score}-{result.home_score})")
            prs.update_ratings_from_game(result)

        # Save snapshot
        if not args.dry_run:
            snapshot_file = ratings_dir / f"nfl_2025_week_{week_num:02d}.json"
            snapshot = {
                "season": "2025",
                "week": week_num,
                "ratings": prs.export_ratings(),
                "games_processed_total": len(prs.history),
                "system_constants": {
                    "old_rating_weight": prs.OLD_RATING_WEIGHT,
                    "true_performance_weight": prs.TRUE_PERFORMANCE_WEIGHT,
                    "home_field_advantage": prs.HOME_FIELD_ADVANTAGE,
                }
            }
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot, f, indent=2)
            logger.info(f"Saved to {snapshot_file.name}")

        # Show top 10
        top_10 = prs.get_top_teams(10)
        logger.info("\nTop 10:")
        for rank, (team, rating) in enumerate(top_10, 1):
            logger.info(f"  {rank:2d}. {team:20s} {rating:.2f}")

    logger.info(f"\n[SUCCESS] Processed weeks {args.start_week}-{args.end_week}")


if __name__ == "__main__":
    main()
