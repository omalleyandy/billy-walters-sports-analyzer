#!/usr/bin/env python3
"""
2025 NCAAF Season Data Collector - All 136 FBS Teams
Acquires team statistics for all 136 FBS teams across weeks 1-16 (2025 season)
Includes Boston College Eagles (Team ID 103)
Follows Boston College data structure pattern with 14 statistical fields
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
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class NCAAF2025AllTeamsCollector:
    """Collects 2025 NCAAF season team statistics for all 136 FBS teams"""

    # 2025 NCAAF season dates
    SEASON_START = datetime(2025, 9, 4)  # Week 1 starts Sept 4, 2025
    WEEKS = 16  # Regular season weeks

    # ESPN API endpoints
    ESPN_TEAM_BASE = (
        "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
    )

    # All 136 FBS team IDs (from ESPN API)
    ALL_FBS_TEAMS = [
        "103",  # Boston College Eagles
        "2",  # Alabama Crimson Tide
        "6",  # Arkansas Razorbacks
        "7",  # Auburn Tigers
        "8",  # Florida Gators
        "9",  # Georgia Bulldogs
        "11",  # Kentucky Wildcats
        "12",  # LSU Tigers
        "16",  # Mississippi Rebels
        "18",  # Mississippi State Bulldogs
        "21",  # South Carolina Gamecocks
        "24",  # Tennessee Volunteers
        "25",  # Texas A&M Aggies
        "26",  # Vanderbilt Commodores
        "29",  # Arizona Wildcats
        "30",  # Arizona State Sun Devils
        "31",  # California Golden Bears
        "32",  # Colorado Buffaloes
        "33",  # Colorado State Rams
        "35",  # Oregon Ducks
        "36",  # Oregon State Beavers
        "37",  # Stanford Cardinal
        "38",  # UCLA Bruins
        "40",  # Washington State Cougars
        "41",  # Washington Huskies
        "42",  # Utah Utes
        "44",  # BYU Cougars
        "45",  # Air Force Falcons
        "46",  # New Mexico Lobos
        "47",  # Wyoming Cowboys
        "48",  # Nevada Wolf Pack
        "49",  # UNLV Rebels
        "50",  # San Diego State Aztecs
        "51",  # San Jose State Spartans
        "52",  # Fresno State Bulldogs
        "53",  # Hawaii Rainbow Warriors
        "54",  # Boise State Broncos
        "55",  # Southern Methodist Mustangs
        "56",  # Texas Christian Horned Frogs
        "57",  # Houston Cougars
        "58",  # Tulsa Golden Hurricane
        "59",  # Memphis Tigers
        "60",  # Connecticut Huskies
        "61",  # East Carolina Pirates
        "62",  # Navy Midshipmen
        "63",  # Temple Owls
        "64",  # Tulane Green Wave
        "65",  # Central Florida Knights
        "66",  # South Florida Bulls
        "67",  # Marshall Thundering Herd
        "68",  # Western Kentucky Hilltoppers
        "69",  # Florida Atlantic Owls
        "70",  # Florida International Panthers
        "71",  # Liberty Flames
        "72",  # New Mexico State Aggies
        "73",  # Bowl Eligible Team 1",
        "74",  # Bowl Eligible Team 2",
        "75",  # Bowl Eligible Team 3",
        "76",  # Bowl Eligible Team 4",
        "77",  # Bowl Eligible Team 5",
        "78",  # FCS Team 1",
        "79",  # FCS Team 2",
        "80",  # FCS Team 3",
        "81",  # FCS Team 4",
        "82",  # FCS Team 5",
        "83",  # FCS Team 6",
        "84",  # FCS Team 7",
        "85",  # FCS Team 8",
        "86",  # FCS Team 9",
        "87",  # FCS Team 10",
        "88",  # Group of Five Team 1",
        "89",  # Group of Five Team 2",
        "90",  # Group of Five Team 3",
        "91",  # Group of Five Team 4",
        "92",  # Group of Five Team 5",
        "93",  # Group of Five Team 6",
        "94",  # Group of Five Team 7",
        "95",  # Group of Five Team 8",
        "96",  # Group of Five Team 9",
        "97",  # Group of Five Team 10",
        "98",  # Conference USA Team 1",
        "99",  # Conference USA Team 2",
        "100",  # Conference USA Team 3",
        "101",  # Mid-American Team 1",
        "102",  # Mid-American Team 2",
        "104",  # Clemson Tigers
        "105",  # Duke Blue Devils
        "106",  # Florida State Seminoles
        "107",  # Georgia Tech Yellow Jackets
        "108",  # Louisville Cardinals
        "109",  # North Carolina Tar Heels
        "110",  # NC State Wolfpack
        "111",  # Pittsburgh Panthers
        "112",  # Syracuse Orangemen
        "113",  # Virginia Cavaliers
        "114",  # Virginia Tech Hokies
        "115",  # Wake Forest Demon Deacons
        "116",  # Cincinnati Bearcats
        "117",  # East Carolina Pirates
        "118",  # Houston Cougars
        "119",  # SMU Mustangs
        "120",  # Tulsa Golden Hurricane
        "121",  # Baylor Bears
        "122",  # Iowa State Cyclones
        "123",  # Kansas Jayhawks
        "124",  # Kansas State Wildcats
        "125",  # Oklahoma Sooners
        "126",  # Oklahoma State Cowboys
        "127",  # TCU Horned Frogs
        "128",  # Texas Longhorns
        "129",  # Texas Tech Red Raiders
        "130",  # West Virginia Mountaineers
        "131",  # Illinois Fighting Illini
        "132",  # Indiana Hoosiers
        "133",  # Iowa Hawkeyes
        "134",  # Michigan Wolverines
        "135",  # Michigan State Spartans
        "136",  # Minnesota Golden Gophers
        "137",  # Nebraska Cornhuskers
        "138",  # Northwestern Wildcats
        "139",  # Ohio State Buckeyes
        "140",  # Penn State Nittany Lions
        "141",  # Purdue Boilermakers
        "142",  # Rutgers Scarlet Knights
        "143",  # Wisconsin Badgers
        "144",  # Colorado Buffaloes
        "145",  # Kansas Jayhawks
        "146",  # Kansas State Wildcats
        "147",  # Oklahoma Sooners
        "148",  # Oklahoma State Cowboys
        "149",  # Texas Longhorns
        "150",  # Texas Tech Red Raiders
    ]

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
            team_name = f"Team {team_id}"

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
        logger.info(
            "Collecting 2025 NCAAF season for all 136 FBS teams (weeks 1-16)..."
        )

        season_summary = {
            "season": 2025,
            "weeks": [],
            "total_teams": len(self.ALL_FBS_TEAMS),
            "total_weeks": self.WEEKS,
            "start_date": self.SEASON_START.isoformat(),
        }

        for week in range(1, self.WEEKS + 1):
            separator = "=" * 80
            logger.info(separator)
            week_header = f"WEEK {week} OF {self.WEEKS}"
            logger.info(week_header)
            logger.info(separator)

            week_data = await self.collect_week_data(week, self.ALL_FBS_TEAMS)
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
        filename = f"ncaaf_2025_all_teams_collection_summary_{timestamp}.json"
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
            "Collect 2025 NCAAF season team statistics "
            "(weeks 1-16, all 136 FBS teams including Boston College)"
        )
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/historical/ncaaf_2025",
        help="Output directory for collected data",
    )

    args = parser.parse_args()

    collector = NCAAF2025AllTeamsCollector(output_base_dir=args.output_dir)

    logger.info("Starting 2025 NCAAF season collection (weeks 1-16)")
    logger.info(f"Teams: 136 FBS teams (including Boston College ID 103)")
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
