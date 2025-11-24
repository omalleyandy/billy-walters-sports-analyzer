#!/usr/bin/env python3
"""
2024 NFL Season Data Collector (Testing Alternative)
Acquires 2024 NFL game data for development and testing
This is a complete dataset since 2024 season is finished
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


class NFL2024SeasonCollector:
    """Collects 2024 NFL season game data (weeks 1-18)"""

    # 2024 NFL season dates
    SEASON_YEAR = 2024
    SEASON_START = datetime(2024, 9, 5)  # Week 1 starts Sept 5, 2024
    REGULAR_SEASON_WEEKS = 18

    # ESPN API endpoints
    ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    def __init__(self, output_base_dir: str = "data/historical/nfl_2024"):
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
            params = {"week": week, "seasontype": season_type, "season": self.SEASON_YEAR}

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

            # Extract statistics if available
            statistics = team_data.get("statistics", [])
            if statistics:
                stats_dict = statistics[0]  # Current season stats

                # Extract relevant metrics
                for stat in stats_dict.get("stats", []):
                    label = stat.get("label", "").lower()
                    value = stat.get("value")

                    if "points" in label and "allowed" not in label:
                        stats["points_per_game"] = value
                    elif "total points" in label:
                        stats["total_points"] = value
                    elif "passing yards" in label and "allowed" not in label:
                        stats["passing_yards_per_game"] = value
                    elif "rushing yards" in label and "allowed" not in label:
                        stats["rushing_yards_per_game"] = value
                    elif "total yards" in label and "allowed" not in label:
                        stats["total_yards_per_game"] = value
                    elif "points allowed" in label:
                        stats["points_allowed_per_game"] = value
                    elif "passing yards allowed" in label:
                        stats["passing_yards_allowed_per_game"] = value
                    elif "rushing yards allowed" in label:
                        stats["rushing_yards_allowed_per_game"] = value
                    elif "total yards allowed" in label:
                        stats["total_yards_allowed_per_game"] = value
                    elif "turnover margin" in label:
                        stats["turnover_margin"] = value
                    elif "third down" in label:
                        stats["third_down_pct"] = value

            return stats

        except Exception as e:
            logger.error(f"Failed to parse team stats: {e}")
            return None

    async def collect_week(self, week: int) -> Dict:
        """Collect all data for a single week"""
        logger.info("=" * 80)
        logger.info(f"WEEK {week} OF {self.REGULAR_SEASON_WEEKS}")
        logger.info("=" * 80)
        logger.info(f"Collecting Week {week} data...")

        week_data = {
            "week": week,
            "season": self.SEASON_YEAR,
            "games": [],
            "team_stats": [],
            "collection_time": datetime.now().isoformat(),
        }

        # Fetch schedule
        schedule = await self.fetch_week_schedule(week)
        if not schedule:
            logger.error(f"Failed to fetch Week {week} schedule")
            return week_data

        # Parse games
        events = schedule.get("events", [])
        for event in events:
            game = self.parse_game_data(event, week)
            if game:
                week_data["games"].append(game)

        logger.info(f"Games parsed: {len(week_data['games'])}/{len(events)}")

        # Fetch team stats for teams in this week
        teams_in_week = set()
        for game in week_data["games"]:
            teams_in_week.add(game["home_team_abbr"])
            teams_in_week.add(game["away_team_abbr"])

        for team_abbr in sorted(teams_in_week):
            await asyncio.sleep(0.2)  # Rate limiting
            stats = await self.fetch_team_stats_for_week(team_abbr, week)
            if stats:
                week_data["team_stats"].append(stats)

        logger.info(f"Games: {len(week_data['games'])}/{len(events)} loaded, "
                    f"{len(week_data['team_stats'])} team stats")

        # Save week data
        week_file = (
            self.output_dir
            / f"nfl_games_week_{week}_{self.SEASON_YEAR}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(week_file, "w") as f:
            json.dump(week_data, f, indent=2)
        logger.info(f"Saved: {week_file}")

        logger.info(
            f"Week {week} Complete: {len(week_data['games'])}/{len(events)} games, "
            f"{len(week_data['team_stats'])} team stats"
        )
        logger.info("=" * 80)

        return week_data

    async def collect_season(self):
        """Collect entire season"""
        logger.info("=" * 80)
        logger.info("2024 NFL SEASON DATA COLLECTOR")
        logger.info("Billy Walters Analysis Package")
        logger.info("=" * 80)
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Starting 2024 NFL season collection (weeks 1-{self.REGULAR_SEASON_WEEKS})")
        logger.info("=" * 80)

        season_summary = {
            "season": self.SEASON_YEAR,
            "weeks_collected": 0,
            "total_games": 0,
            "total_team_stats": 0,
            "weeks": [],
            "collection_start": datetime.now().isoformat(),
        }

        await self.connect()

        try:
            for week in range(1, self.REGULAR_SEASON_WEEKS + 1):
                week_data = await self.collect_week(week)
                season_summary["weeks_collected"] += 1
                season_summary["total_games"] += len(week_data["games"])
                season_summary["total_team_stats"] += len(week_data["team_stats"])
                season_summary["weeks"].append(
                    {
                        "week": week,
                        "games": len(week_data["games"]),
                        "team_stats": len(week_data["team_stats"]),
                    }
                )

                # Small delay between weeks
                if week < self.REGULAR_SEASON_WEEKS:
                    await asyncio.sleep(0.5)

        finally:
            await self.close()

        # Save season summary
        season_summary["collection_end"] = datetime.now().isoformat()
        summary_file = (
            self.output_dir
            / f"nfl_2024_season_collection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(summary_file, "w") as f:
            json.dump(season_summary, f, indent=2)
        logger.info(f"Season summary saved: {summary_file}")

        logger.info("=" * 80)
        logger.info("2024 NFL season collection complete!")
        logger.info(f"Total games: {season_summary['total_games']}")
        logger.info(f"Total team stats: {season_summary['total_team_stats']}")
        logger.info("=" * 80)


async def main():
    """Main entry point"""
    collector = NFL2024SeasonCollector()
    await collector.collect_season()


if __name__ == "__main__":
    asyncio.run(main())
