#!/usr/bin/env python3
"""
Historical NCAAF Data Collector
Acquires team statistics for all 136 FBS teams across multiple seasons/weeks
Compatible with Boston College example pattern (14 stat fields per team per week)
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import httpx


class HistoricalNCAAFCollector:
    """Collects historical NCAAF team statistics"""

    def __init__(self, output_dir: str = "data/historical"):
        """Initialize collector"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = None

    async def connect(self):
        """Create async HTTP session"""
        self.session = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()

    def get_espn_team_stats_url(self, team_id: str, season: int) -> str:
        """Build ESPN team statistics URL"""
        return f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}"

    async def fetch_team_stats(
        self, team_id: str, team_name: str, season: int
    ) -> Optional[Dict]:
        """Fetch team statistics from ESPN for a given season"""
        if not self.session:
            await self.connect()

        url = self.get_espn_team_stats_url(team_id, season)

        try:
            response = await self.session.get(url)
            if response.status_code == 200:
                data = response.json()

                # Extract statistics from ESPN response
                team_data = data.get("team", {})
                stats = self._parse_team_stats(team_data, team_id, team_name, season)

                return stats
        except Exception as e:
            print(f"[WARNING] Failed to fetch {team_name} ({team_id}): {e}")
            return None

        return None

    def _parse_team_stats(
        self, team_data: Dict, team_id: str, team_name: str, season: int
    ) -> Dict:
        """Parse ESPN team data into standardized format"""
        stats = {
            "team_id": team_id,
            "team_name": team_name,
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

        # Try to extract from statistics if available
        # This is a template - actual extraction depends on ESPN API structure
        return stats

    async def collect_season(self, season: int, teams: List[Dict]) -> Dict:
        """Collect statistics for all teams in a season"""
        print(f"[INFO] Collecting {season} NCAAF season data for {len(teams)} teams...")

        season_data = {
            "season": season,
            "timestamp": datetime.now().isoformat(),
            "teams": [],
            "total_teams": len(teams),
            "success_count": 0,
            "error_count": 0,
        }

        for idx, team in enumerate(teams, 1):
            team_id = team.get("team_id")
            team_name = team.get("team_name")

            if not team_id or not team_name:
                continue

            print(f"[{idx:3d}/{len(teams)}] Collecting {team_name}...", end=" ")

            stats = await self.fetch_team_stats(team_id, team_name, season)

            if stats:
                season_data["teams"].append(stats)
                season_data["success_count"] += 1
                print("[OK]")
            else:
                season_data["error_count"] += 1
                print("[SKIP]")

            # Rate limiting
            await asyncio.sleep(0.2)

        return season_data

    def save_season_data(self, season_data: Dict) -> Path:
        """Save collected season data to JSON file"""
        season = season_data["season"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ncaaf_team_stats_{season}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(season_data, f, indent=2)

        print(f"[OK] Saved: {filepath}")
        return filepath

    def load_teams_from_file(self, filepath: str) -> List[Dict]:
        """Load team list from existing file"""
        with open(filepath) as f:
            data = json.load(f)
        return data.get("ncaaf", []) if isinstance(data, dict) else data

    async def collect_multiple_seasons(self, seasons: List[int], teams: List[Dict]):
        """Collect data for multiple seasons"""
        print(f"[INFO] Starting historical data collection for seasons: {seasons}")

        for season in seasons:
            season_data = await self.collect_season(season, teams)
            self.save_season_data(season_data)
            print(
                f"[OK] {season} season complete: {season_data['success_count']}/{season_data['total_teams']}"
            )

        await self.close()


async def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Collect historical NCAAF data")
    parser.add_argument(
        "--seasons",
        type=int,
        nargs="+",
        default=[2005, 2010, 2015, 2020, 2025],
        help="Seasons to collect (default: 2005 2010 2015 2020 2025)",
    )
    parser.add_argument(
        "--teams-file",
        type=str,
        default="data/current/espn_teams.json",
        help="Teams reference file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/historical",
        help="Output directory for historical data",
    )

    args = parser.parse_args()

    # Load teams
    teams_path = Path(args.teams_file)
    if not teams_path.exists():
        print(f"[ERROR] Teams file not found: {teams_path}")
        return

    with open(teams_path) as f:
        all_teams = json.load(f)

    teams = all_teams.get("ncaaf", [])
    if not teams:
        print("[ERROR] No NCAAF teams found in file")
        return

    # Collect data
    collector = HistoricalNCAAFCollector(output_dir=args.output_dir)
    await collector.collect_multiple_seasons(args.seasons, teams)


if __name__ == "__main__":
    asyncio.run(main())
