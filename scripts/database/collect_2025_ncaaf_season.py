#!/usr/bin/env python3
"""
2025 NCAAF Season Data Collector
Acquires team statistics for all 136 FBS teams across weeks 1-16 (2025 season)
Follows Boston College Eagles (Team ID 103) data structure pattern
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


class NCAAF2025SeasonCollector:
    """Collects 2025 NCAAF season team statistics (weeks 1-16)"""

    # 2025 NCAAF season dates
    SEASON_START = datetime(2025, 9, 4)  # Week 1 starts Sept 4, 2025
    WEEKS = 16  # Regular season weeks

    # ESPN API endpoints
    ESPN_TEAM_BASE = (
        "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
    )

    def __init__(self, output_base_dir: str = "data/historical/ncaaf_2025"):
        """Initialize collector"""
        self.output_dir = Path(output_base_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
        self.teams_cache = {}
        self.teams_by_id = {}

    async def connect(self):
        """Create async HTTP session"""
        self.session = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()

    def load_team_references(
        self, teams_file: str = "data/current/espn_teams.json"
    ) -> Dict:
        """Load NCAAF team reference data"""
        teams_path = Path(teams_file)

        if not teams_path.exists():
            logger.error(f"Teams file not found: {teams_path}")
            return {}

        try:
            with open(teams_path) as f:
                data = json.load(f)

            ncaaf_teams = data.get("ncaaf", {})

            # Build bidirectional mapping
            for team_id, team_name in ncaaf_teams.items():
                self.teams_by_id[team_id] = team_name
                self.teams_cache[team_name.lower()] = {
                    "team_id": team_id,
                    "team_name": team_name,
                }

            logger.info(f"Loaded {len(self.teams_by_id)} team references")
            return self.teams_by_id

        except Exception as e:
            logger.error(f"Failed to load teams: {e}")
            return {}

    async def fetch_team_stats_for_week(
        self, team_id: str, week: int, season: int = 2025
    ) -> Optional[Dict]:
        """
        Fetch team statistics for a specific week
        Uses ESPN API structure
        """
        if not self.session:
            await self.connect()

        try:
            # ESPN team endpoint
            url = f"{self.ESPN_TEAM_BASE}/teams/{team_id}"

            response = await self.session.get(url)

            if response.status_code == 200:
                team_data = response.json()
                stats = self._parse_team_stats_for_week(
                    team_data, team_id, week, season
                )
                return stats

            return None

        except Exception as e:
            error_msg = f"Failed to fetch team {team_id} week {week}: {e}"
            logger.debug(error_msg)
            return None

    def _parse_team_stats_for_week(
        self, team_data: Dict, team_id: str, week: int, season: int
    ) -> Optional[Dict]:
        """Parse ESPN team response into Boston College format"""
        try:
            team_info = team_data.get("team", {})

            # Extract team name
            team_name = team_info.get("displayName") or team_info.get("name")

            if not team_name:
                return None

            # Initialize stats structure (matching Boston College example)
            stats = {
                "team_id": team_id,
                "team_name": team_name,
                "week": week,
                "season": season,
                "games_played": None,
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

            # Try to extract statistics from various possible locations
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

                        if "points" in label and "ppg" not in label:
                            stats["total_points"] = value
                        elif "ppg" in label or (
                            "average" in label and "points" in label
                        ):
                            stats["points_per_game"] = value
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
            parse_error = f"Failed to parse team stats: {e}"
            logger.debug(parse_error)
            return None

    async def collect_week_data(self, week: int, teams: List[str]) -> Dict:
        """Collect statistics for all teams for a specific week"""
        logger.info(f"Collecting Week {week} data for {len(teams)} teams...")

        week_data = {
            "season": 2025,
            "week": week,
            "timestamp": datetime.now().isoformat(),
            "teams": [],
            "total_teams": len(teams),
            "success_count": 0,
            "error_count": 0,
        }

        for idx, team_id in enumerate(teams, 1):
            team_name = self.teams_by_id.get(team_id, f"Team {team_id}")

            log_msg = f"[{idx:3d}/{len(teams)}] Week {week}: {team_name}..."
            logger.info(log_msg)

            stats = await self.fetch_team_stats_for_week(team_id, week, season=2025)

            if stats:
                week_data["teams"].append(stats)
                week_data["success_count"] += 1
                logger.info("[OK]")
            else:
                week_data["error_count"] += 1
                logger.info("[SKIP]")

            # Rate limiting (0.3 seconds between requests)
            await asyncio.sleep(0.3)

        return week_data

    def save_week_data(self, week_data: Dict) -> Path:
        """Save collected week data to JSON file"""
        week = week_data["week"]
        season = week_data["season"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"ncaaf_team_stats_week_{week}_{season}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(week_data, f, indent=2)

        logger.info(f"[OK] Saved: {filepath}")
        return filepath

    async def collect_full_season(self) -> Dict:
        """Collect data for all 16 weeks of 2025 NCAAF season"""
        if not self.teams_by_id:
            self.load_team_references()

        if not self.teams_by_id:
            logger.error("No teams loaded. Cannot proceed.")
            return {}

        team_ids = list(self.teams_by_id.keys())
        season_summary = {
            "season": 2025,
            "weeks": [],
            "total_teams": len(team_ids),
            "total_weeks": self.WEEKS,
            "start_date": self.SEASON_START.isoformat(),
        }

        for week in range(1, self.WEEKS + 1):
            separator = "=" * 80
            logger.info(separator)
            week_header = f"WEEK {week} OF {self.WEEKS}"
            logger.info(week_header)
            logger.info(separator)

            week_data = await self.collect_week_data(week, team_ids)
            filepath = self.save_week_data(week_data)

            week_summary = {
                "week": week,
                "total_teams": week_data["total_teams"],
                "success_count": week_data["success_count"],
                "error_count": week_data["error_count"],
                "file": str(filepath),
            }
            season_summary["weeks"].append(week_summary)

            success = week_data["success_count"]
            total = week_data["total_teams"]
            result_msg = f"Week {week} Complete: {success}/{total} teams"
            logger.info(result_msg)

        return season_summary

    def save_season_summary(self, season_summary: Dict) -> Path:
        """Save season collection summary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ncaaf_2025_season_collection_summary_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(season_summary, f, indent=2)

        summary_msg = f"Season summary saved: {filepath}"
        logger.info(summary_msg)
        return filepath


async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Collect 2025 NCAAF season team statistics (weeks 1-16, all 136 FBS teams)"
        )
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/historical/ncaaf_2025",
        help="Output directory for collected data",
    )
    parser.add_argument(
        "--teams-file",
        type=str,
        default="data/current/espn_teams.json",
        help="Teams reference file",
    )
    parser.add_argument(
        "--start-week", type=int, default=1, help="Starting week (default: 1)"
    )
    parser.add_argument(
        "--end-week", type=int, default=16, help="Ending week (default: 16)"
    )

    args = parser.parse_args()

    collector = NCAAF2025SeasonCollector(output_base_dir=args.output_dir)
    collector.load_team_references(teams_file=args.teams_file)

    start_msg = (
        f"Starting 2025 NCAAF season collection "
        f"(weeks {args.start_week}-{args.end_week})"
    )
    logger.info(start_msg)
    logger.info(f"Teams: {len(collector.teams_by_id)} FBS teams")
    logger.info(f"Output: {args.output_dir}")

    season_summary = await collector.collect_full_season()

    if season_summary:
        collector.save_season_summary(season_summary)
        logger.info("2025 NCAAF season collection complete!")
    else:
        logger.error("Failed to collect season data")

    await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
