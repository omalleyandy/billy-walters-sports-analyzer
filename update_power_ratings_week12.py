#!/usr/bin/env python3
"""
Power Ratings Update for Week 12
Incorporates Week 11 results including Monday Night Football (PHI vs DAL)

Uses Billy Walters 90/10 Formula:
New Rating = (0.90 × Old Rating) + (0.10 × True Performance)
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class PowerRatingsUpdater:
    """Update power ratings with Week 11 results for Week 12 analysis"""

    def __init__(self):
        self.data_dir = Path("data")
        self.home_field_advantage = 2.0  # Billy Walters standard

    async def update_for_week12(self) -> Dict:
        """
        Update power ratings incorporating Week 11 results.

        Critical: Includes Monday Night Football result.
        """
        logger.info("=" * 70)
        logger.info("POWER RATINGS UPDATE FOR WEEK 12")
        logger.info("Billy Walters 90/10 Formula")
        logger.info("=" * 70 + "\n")

        # 1. Load current ratings
        logger.info("[1/4] Loading Week 10 Power Ratings...")
        old_ratings = self.load_current_ratings()
        logger.info(f"  ✓ Loaded {len(old_ratings)} team ratings\n")

        # 2. Fetch Week 11 results
        logger.info("[2/4] Fetching Week 11 Results (including MNF)...")
        week11_results = await self.fetch_week11_results()
        logger.info(f"  ✓ Fetched {len(week11_results)} game results\n")

        # 3. Apply 90/10 formula
        logger.info("[3/4] Applying 90/10 Formula...")
        new_ratings = self.calculate_new_ratings(old_ratings, week11_results)
        logger.info(f"  ✓ Updated {len(new_ratings)} team ratings\n")

        # 4. Save and display changes
        logger.info("[4/4] Saving Updated Ratings...")
        self.save_ratings(new_ratings)

        # Show significant changes
        self.display_changes(old_ratings, new_ratings)

        return new_ratings

    def load_current_ratings(self) -> Dict[str, float]:
        """Load most recent power ratings"""
        ratings_file = self.data_dir / "power_ratings_nfl_2025.json"

        if not ratings_file.exists():
            logger.warning("  ! No existing ratings found, starting fresh")
            return {}

        with open(ratings_file) as f:
            data = json.load(f)

        return data.get("ratings", {})

    async def fetch_week11_results(self) -> List[Dict]:
        """
        Fetch Week 11 game results including Monday Night Football.

        Uses ESPN API for official scores.
        """
        try:
            import aiohttp

            # ESPN scoreboard API for Week 11
            url = (
                "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            )
            params = {
                "dates": "20241114-20241119",  # Week 11 dates (Thu-Mon)
                "seasontype": 2,
                "week": 11,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.warning(f"  ! ESPN API returned {response.status}")
                        return self.get_week11_fallback()

                    data = await response.json()
                    results = []

                    for event in data.get("events", []):
                        if event["status"]["type"]["completed"]:
                            result = self._parse_game_result(event)
                            results.append(result)

                    # Verify MNF included
                    mnf_found = any(
                        (
                            r["home_team"] == "Philadelphia Eagles"
                            and r["away_team"] == "Dallas Cowboys"
                        )
                        or (
                            r["home_team"] == "Dallas Cowboys"
                            and r["away_team"] == "Philadelphia Eagles"
                        )
                        for r in results
                    )

                    if mnf_found:
                        logger.info("  ✓ Monday Night Football result included!")
                    else:
                        logger.warning("  ! MNF result pending - check manually")

                    return results

        except Exception as e:
            logger.warning(f"  ! Fetch failed: {e}")
            return self.get_week11_fallback()

    def _parse_game_result(self, event: Dict) -> Dict:
        """Parse ESPN game result"""
        competition = event["competitions"][0]

        home_team = next(
            t for t in competition["competitors"] if t["homeAway"] == "home"
        )
        away_team = next(
            t for t in competition["competitors"] if t["homeAway"] == "away"
        )

        return {
            "home_team": home_team["team"]["displayName"],
            "away_team": away_team["team"]["displayName"],
            "home_score": int(home_team["score"]),
            "away_score": int(away_team["score"]),
            "date": event["date"],
            "completed": event["status"]["type"]["completed"],
        }

    def get_week11_fallback(self) -> List[Dict]:
        """
        Fallback Week 11 results if API fails.

        NOTE: Update these with actual scores after MNF!
        """
        logger.info("  → Using fallback data (UPDATE WITH ACTUAL SCORES)")

        return [
            # Thursday Night Football
            {
                "home_team": "Washington Commanders",
                "away_team": "Philadelphia Eagles",
                "home_score": 26,
                "away_score": 18,
            },
            # Sunday games (examples - add all 15 games)
            {
                "home_team": "Pittsburgh Steelers",
                "away_team": "Baltimore Ravens",
                "home_score": 18,
                "away_score": 16,
            },
            {
                "home_team": "Minnesota Vikings",
                "away_team": "Tennessee Titans",
                "home_score": 23,
                "away_score": 13,
            },
            # Monday Night Football (UPDATE AFTER GAME!)
            {
                "home_team": "Dallas Cowboys",
                "away_team": "Houston Texans",
                "home_score": 34,
                "away_score": 10,
            },
        ]

    def calculate_new_ratings(
        self, old_ratings: Dict[str, float], results: List[Dict]
    ) -> Dict[str, float]:
        """
        Apply Billy Walters 90/10 formula.

        Formula:
        New Rating = (0.90 × Old Rating) + (0.10 × True Performance)

        Where True Performance = Points Scored - Points Allowed ± HFA
        """
        new_ratings = old_ratings.copy()

        for game in results:
            home_team = game["home_team"]
            away_team = game["away_team"]
            home_score = game["home_score"]
            away_score = game["away_score"]

            # Get old ratings (default to 0 if new team)
            home_old = old_ratings.get(home_team, 0.0)
            away_old = old_ratings.get(away_team, 0.0)

            # Calculate true performance (adjusted for HFA)
            home_margin = home_score - away_score
            away_margin = away_score - home_score

            # Adjust for home field advantage
            home_true_perf = home_margin + self.home_field_advantage
            away_true_perf = away_margin - self.home_field_advantage

            # Apply 90/10 formula
            home_new = (0.90 * home_old) + (0.10 * home_true_perf)
            away_new = (0.90 * away_old) + (0.10 * away_true_perf)

            new_ratings[home_team] = round(home_new, 2)
            new_ratings[away_team] = round(away_new, 2)

            # Log significant changes
            home_change = home_new - home_old
            away_change = away_new - away_old

            if abs(home_change) > 1.0 or abs(away_change) > 1.0:
                logger.info(
                    f"  {home_team:25} {home_old:+6.2f} → {home_new:+6.2f} ({home_change:+.2f})"
                )
                logger.info(
                    f"  {away_team:25} {away_old:+6.2f} → {away_new:+6.2f} ({away_change:+.2f})"
                )

        return new_ratings

    def save_ratings(self, ratings: Dict[str, float]) -> None:
        """Save updated ratings to file"""
        output = {
            "ratings": ratings,
            "last_updated": datetime.now().isoformat(),
            "week": 12,
            "season": 2025,
            "methodology": "Billy Walters 90/10 Formula",
            "system_constants": {
                "old_rating_weight": 0.9,
                "true_performance_weight": 0.1,
                "home_field_advantage": self.home_field_advantage,
            },
        }

        # Save to main file
        main_file = self.data_dir / "power_ratings_nfl_2025.json"
        with open(main_file, "w") as f:
            json.dump(output, f, indent=2)

        # Save week-specific snapshot
        snapshot_dir = self.data_dir / "power_ratings"
        snapshot_dir.mkdir(exist_ok=True)
        snapshot_file = snapshot_dir / "nfl_2025_week_12.json"
        with open(snapshot_file, "w") as f:
            json.dump(output, f, indent=2)

        logger.info(f"  ✓ Saved to {main_file}")
        logger.info(f"  ✓ Snapshot at {snapshot_file}")

    def display_changes(
        self, old_ratings: Dict[str, float], new_ratings: Dict[str, float]
    ) -> None:
        """Display significant rating changes"""
        logger.info("\n" + "=" * 70)
        logger.info("TOP RATING CHANGES (Week 11 → Week 12)")
        logger.info("=" * 70 + "\n")

        changes = []
        for team in new_ratings:
            old = old_ratings.get(team, 0.0)
            new = new_ratings[team]
            change = new - old
            changes.append((team, old, new, change))

        # Sort by absolute change
        changes.sort(key=lambda x: abs(x[3]), reverse=True)

        print(f"{'Team':<30} {'Old':>8} {'New':>8} {'Change':>8}")
        print("-" * 70)

        for team, old, new, change in changes[:15]:  # Top 15 changes
            symbol = "↑" if change > 0 else "↓"
            print(f"{team:<30} {old:>+7.2f} {new:>+7.2f} {symbol} {abs(change):>6.2f}")

        logger.info("\n" + "=" * 70 + "\n")


async def main():
    """Main execution"""
    updater = PowerRatingsUpdater()

    try:
        await updater.update_for_week12()

        print("[SUCCESS] Power ratings updated for Week 12!")
        print("\n[NEXT STEPS]")
        print("1. Review rating changes above")
        print("2. Verify Monday Night Football result included")
        print("3. Run edge analysis with updated ratings")
        print("4. python analyze_edges_simple.py")
        print()

    except Exception as e:
        logger.error(f"\n[ERROR] Update failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
