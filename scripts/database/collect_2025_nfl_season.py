#!/usr/bin/env python3
"""
2025 NFL Season Data Collector
Acquires comprehensive game data for NFL 2025 season (weeks 1-18)
Includes: Game results, team statistics, venue information, records
Billy Walters Analysis Package for power rating calculations
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import httpx
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


class NFL2025SeasonCollector:
    """Collects 2025 NFL season game data (weeks 1-18)"""

    # 2025 NFL season dates
    SEASON_YEAR = 2025
    SEASON_START = datetime(2025, 9, 4)  # Week 1 starts Sept 4, 2025
    REGULAR_SEASON_WEEKS = 18

    # ESPN API endpoints
    ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    def __init__(self, output_base_dir: str = "data/historical/nfl_2025"):
        """Initialize collector"""
        self.output_dir = Path(output_base_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = None

    async def connect(self):
        """Create async HTTP session"""
        self.session = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()

    async def fetch_week_schedule(
        self, week: int, season_type: int = 2
    ) -> Optional[Dict]:
        """
        Fetch full schedule and results for a specific week
        season_type: 1=preseason, 2=regular, 3=postseason
        """
        if not self.session:
            await self.connect()

        try:
            url = f"{self.ESPN_BASE}/scoreboard"
            params = {
                "week": week,
                "seasontype": season_type,
                "season": self.SEASON_YEAR,
            }

            response = await self.session.get(url, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Week {week}: HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Failed to fetch week {week}: {e}")
            return None

    def parse_game_data(self, event: Dict, week: int) -> Optional[Dict]:
        """
        Extract Billy Walters game data from ESPN event
        Returns: Game record with all required fields
        """
        try:
            # Extract basic game info
            event_id = event.get("id")
            game_date = event.get("date")
            status = event.get("status", {}).get("type", "SCHEDULED").upper()
            short_name = event.get("shortName", "")

            # Extract competitors (teams)
            competitors = event.get("competitors", [])
            if len(competitors) < 2:
                return None

            # Determine home/away
            home_team_data = next(
                (c for c in competitors if c.get("homeAway") == "home"), None
            )
            away_team_data = next(
                (c for c in competitors if c.get("homeAway") == "away"), None
            )

            if not home_team_data or not away_team_data:
                return None

            home_team = home_team_data.get("team", {}).get("displayName")
            away_team = away_team_data.get("team", {}).get("displayName")
            home_team_abbr = home_team_data.get("team", {}).get("abbreviation")
            away_team_abbr = away_team_data.get("team", {}).get("abbreviation")

            if not home_team or not away_team:
                return None

            # Extract scores (NULL if game not played)
            home_score = home_team_data.get("score")
            away_score = away_team_data.get("score")

            # Calculate margin and total
            final_margin = None
            total_points = None
            if home_score is not None and away_score is not None:
                home_score = int(home_score)
                away_score = int(away_score)
                final_margin = home_score - away_score
                total_points = home_score + away_score

            # Extract records
            home_record = home_team_data.get("record", [{}])[0]
            away_record = away_team_data.get("record", [{}])[0]

            home_wins = home_record.get("wins")
            home_losses = home_record.get("losses")
            home_ties = home_record.get("ties", 0)

            away_wins = away_record.get("wins")
            away_losses = away_record.get("losses")
            away_ties = away_record.get("ties", 0)

            # Extract venue info
            venue = event.get("venue", {})
            stadium_name = venue.get("fullName")
            is_indoor = venue.get("indoor", False)
            is_outdoor = not is_indoor

            # Extract broadcast info
            broadcasts = event.get("broadcasts", [])
            network = broadcasts[0].get("names", ["TBD"])[0] if broadcasts else "TBD"

            # Extract attendance (if available)
            attendance = event.get("attendance")

            # Parse game_id
            game_id = f"{home_team_abbr}_{away_team_abbr}_{self.SEASON_YEAR}_W{week}"

            game_record = {
                "game_id": game_id,
                "espn_event_id": event_id,
                "season": self.SEASON_YEAR,
                "week": week,
                "league": "NFL",
                "game_date": game_date,
                "game_date_iso": datetime.fromisoformat(
                    game_date.replace("Z", "+00:00")
                ).isoformat()
                if game_date
                else None,
                # Teams
                "home_team": home_team,
                "home_team_abbr": home_team_abbr,
                "away_team": away_team,
                "away_team_abbr": away_team_abbr,
                # Scores
                "home_score": home_score,
                "away_score": away_score,
                "final_margin": final_margin,
                "total_points": total_points,
                # Records
                "home_wins": home_wins,
                "home_losses": home_losses,
                "home_ties": home_ties,
                "away_wins": away_wins,
                "away_losses": away_losses,
                "away_ties": away_ties,
                # Venue
                "stadium": stadium_name,
                "is_outdoor": is_outdoor,
                "is_indoor": is_indoor,
                # Metadata
                "status": status,
                "network": network,
                "attendance": attendance,
                "short_name": short_name,
            }

            return game_record

        except Exception as e:
            logger.error(f"Failed to parse game data: {e}")
            return None

    async def fetch_team_stats_for_week(
        self, team_abbr: str, week: int
    ) -> Optional[Dict]:
        """
        Fetch team statistics for a specific week
        Uses ESPN team statistics endpoint
        """
        if not self.session:
            await self.connect()

        try:
            # ESPN team statistics endpoint
            url = f"{self.ESPN_BASE}/teams/{team_abbr}/statistics"
            response = await self.session.get(url, timeout=30)

            if response.status_code == 200:
                team_data = response.json()
                stats = self._parse_team_stats(team_data, team_abbr, week)
                return stats
            else:
                logger.debug(f"Team stats for {team_abbr}: HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.debug(f"Failed to fetch team stats {team_abbr}: {e}")
            return None

    def _parse_team_stats(
        self, team_data: Dict, team_abbr: str, week: int
    ) -> Optional[Dict]:
        """Extract team statistics from ESPN response"""
        try:
            team_info = team_data.get("team", {})
            team_name = team_info.get("displayName")

            if not team_name:
                return None

            # Initialize stats structure
            stats = {
                "team_abbr": team_abbr,
                "team_name": team_name,
                "week": week,
                "season": self.SEASON_YEAR,
                # Offensive Stats
                "points_per_game": None,
                "total_points": None,
                "passing_yards_per_game": None,
                "rushing_yards_per_game": None,
                "total_yards_per_game": None,
                # Defensive Stats
                "points_allowed_per_game": None,
                "passing_yards_allowed_per_game": None,
                "rushing_yards_allowed_per_game": None,
                "total_yards_allowed_per_game": None,
                # Advanced Stats
                "turnover_margin": None,
                "third_down_pct": None,
                "takeaways": None,
                "giveaways": None,
            }

            # Extract statistics from ESPN response
            stats_info = team_info.get("statistics", [])

            for stat_group in stats_info:
                stat_type = stat_group.get("type", "").lower()

                # Parse offensive stats
                if (
                    "offense" in stat_type
                    or "passing" in stat_type
                    or "rushing" in stat_type
                ):
                    for stat in stat_group.get("stats", []):
                        label = stat.get("label", "").lower()
                        value = stat.get("value")

                        if value is None:
                            continue

                        if "ppg" in label or ("average" in label and "points" in label):
                            stats["points_per_game"] = value
                        elif "total points" in label:
                            stats["total_points"] = value
                        elif "pass" in label and "avg" in label:
                            stats["passing_yards_per_game"] = value
                        elif "rush" in label and "avg" in label:
                            stats["rushing_yards_per_game"] = value
                        elif "total" in label and "avg" in label:
                            stats["total_yards_per_game"] = value

                # Parse defensive stats
                elif "defense" in stat_type:
                    for stat in stat_group.get("stats", []):
                        label = stat.get("label", "").lower()
                        value = stat.get("value")

                        if value is None:
                            continue

                        if "ppg" in label or ("average" in label and "points" in label):
                            stats["points_allowed_per_game"] = value
                        elif "pass" in label and "avg" in label:
                            stats["passing_yards_allowed_per_game"] = value
                        elif "rush" in label and "avg" in label:
                            stats["rushing_yards_allowed_per_game"] = value
                        elif "total" in label and "avg" in label:
                            stats["total_yards_allowed_per_game"] = value

            return stats

        except Exception as e:
            logger.debug(f"Failed to parse team stats: {e}")
            return None

    async def collect_week_data(self, week: int) -> Dict:
        """Collect all game data for a specific week"""
        logger.info(f"Collecting Week {week} data...")

        week_data = {
            "season": self.SEASON_YEAR,
            "week": week,
            "league": "NFL",
            "timestamp": datetime.now().isoformat(),
            "games": [],
            "team_stats": [],
            "total_games": 0,
            "success_count": 0,
            "error_count": 0,
        }

        # Fetch week schedule
        schedule = await self.fetch_week_schedule(week, season_type=2)

        if not schedule:
            logger.error(f"Failed to fetch Week {week} schedule")
            return week_data

        events = schedule.get("events", [])
        week_data["total_games"] = len(events)

        if not events:
            logger.warning(f"No games found for Week {week}")
            return week_data

        logger.info(f"Found {len(events)} games for Week {week}")

        # Process each game
        for idx, event in enumerate(events, 1):
            try:
                game_data = self.parse_game_data(event, week)

                if game_data:
                    week_data["games"].append(game_data)
                    week_data["success_count"] += 1
                    logger.info(
                        f"[{idx:2d}/{len(events)}] "
                        f"{game_data['away_team_abbr']}@{game_data['home_team_abbr']}... [OK]"
                    )

                    # Fetch team stats for both teams (rate limited)
                    for team_abbr in [
                        game_data["home_team_abbr"],
                        game_data["away_team_abbr"],
                    ]:
                        team_stats = await self.fetch_team_stats_for_week(
                            team_abbr, week
                        )
                        if team_stats:
                            week_data["team_stats"].append(team_stats)

                        # Rate limiting (0.2 seconds between requests)
                        await asyncio.sleep(0.2)
                else:
                    week_data["error_count"] += 1
                    logger.warning(f"[{idx:2d}/{len(events)}] Failed to parse event")

            except Exception as e:
                logger.error(f"Error processing event {idx}: {e}")
                week_data["error_count"] += 1

        return week_data

    def save_week_data(self, week_data: Dict) -> Path:
        """Save collected week data to JSON file"""
        week = week_data["week"]
        season = week_data["season"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"nfl_games_week_{week}_{season}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(week_data, f, indent=2)

        logger.info(f"Saved: {filepath}")
        return filepath

    async def collect_full_season(self) -> Dict:
        """Collect data for all 18 weeks of 2025 NFL season"""
        season_summary = {
            "season": self.SEASON_YEAR,
            "league": "NFL",
            "weeks": [],
            "total_weeks": self.REGULAR_SEASON_WEEKS,
            "start_date": self.SEASON_START.isoformat(),
            "total_games_collected": 0,
            "total_team_stats": 0,
        }

        for week in range(1, self.REGULAR_SEASON_WEEKS + 1):
            separator = "=" * 80
            logger.info(separator)
            logger.info(f"WEEK {week} OF {self.REGULAR_SEASON_WEEKS}")
            logger.info(separator)

            week_data = await self.collect_week_data(week)
            filepath = self.save_week_data(week_data)

            week_summary = {
                "week": week,
                "total_games": week_data["total_games"],
                "success_count": week_data["success_count"],
                "error_count": week_data["error_count"],
                "team_stats_count": len(week_data["team_stats"]),
                "file": str(filepath),
            }
            season_summary["weeks"].append(week_summary)
            season_summary["total_games_collected"] += week_data["success_count"]
            season_summary["total_team_stats"] += len(week_data["team_stats"])

            games = week_data["success_count"]
            total = week_data["total_games"]
            stats = len(week_data["team_stats"])
            result_msg = (
                f"Week {week} Complete: {games}/{total} games, {stats} team stats"
            )
            logger.info(result_msg)

        return season_summary

    def save_season_summary(self, season_summary: Dict) -> Path:
        """Save season collection summary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nfl_2025_season_collection_summary_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(season_summary, f, indent=2)

        logger.info(f"Season summary saved: {filepath}")
        return filepath


async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Collect 2025 NFL season game data (weeks 1-18) "
            "for Billy Walters power rating analysis"
        )
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/historical/nfl_2025",
        help="Output directory for collected data",
    )
    parser.add_argument(
        "--week",
        type=int,
        help="Collect specific week only (1-18)",
    )
    parser.add_argument(
        "--start-week",
        type=int,
        default=1,
        help="Starting week (default: 1)",
    )
    parser.add_argument(
        "--end-week",
        type=int,
        default=18,
        help="Ending week (default: 18)",
    )

    args = parser.parse_args()

    collector = NFL2025SeasonCollector(output_base_dir=args.output_dir)

    logger.info("=" * 80)
    logger.info("2025 NFL SEASON DATA COLLECTOR")
    logger.info("Billy Walters Analysis Package")
    logger.info("=" * 80)
    logger.info(f"Output: {args.output_dir}")

    start_msg = (
        f"Starting 2025 NFL season collection (weeks {args.start_week}-{args.end_week})"
    )
    logger.info(start_msg)

    try:
        if args.week:
            # Collect single week
            logger.info(f"Collecting Week {args.week} only...")
            week_data = await collector.collect_week_data(args.week)
            collector.save_week_data(week_data)
        else:
            # Collect full season
            season_summary = await collector.collect_full_season()
            collector.save_season_summary(season_summary)
            logger.info("2025 NFL season collection complete!")

    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
    except Exception as e:
        logger.error(f"Collection failed: {e}")
    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
