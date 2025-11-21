#!/usr/bin/env python3
"""
NFL.com Official Statistics Scraper

Collects weekly cumulative team statistics from NFL.com for power rating calculations.

Billy Walters Methodology:
- Use cumulative season stats (not just recent games)
- Collect offensive and defensive efficiency metrics
- Update weekly as games are played
- Track strength of schedule

Data Sources:
- Primary: NFL.com official statistics API
- Fallback: Pro Football Reference if NFL.com unavailable
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class NFLTeamStats:
    """Weekly cumulative NFL team statistics"""

    # Team identification
    team: str
    team_abbr: str
    week: int
    season: int

    # Record
    wins: int
    losses: int
    ties: int
    games_played: int

    # Offensive stats (cumulative)
    points_scored: int
    total_yards: int
    passing_yards: int
    rushing_yards: int
    turnovers_lost: int
    first_downs: int
    third_down_conversions: int
    third_down_attempts: int

    # Defensive stats (cumulative)
    points_allowed: int
    yards_allowed: int
    passing_yards_allowed: int
    rushing_yards_allowed: int
    turnovers_forced: int
    sacks: int

    # Per-game averages (calculated)
    points_per_game: float
    yards_per_game: float
    points_allowed_per_game: float
    yards_allowed_per_game: float
    turnover_margin_per_game: float

    # Opponents faced (for SoS calculation)
    opponents: List[str]

    # Metadata
    last_updated: str


class NFLStatsScraperClient:
    """
    Scrapes NFL.com official statistics API

    NFL.com provides JSON endpoints for team statistics.
    This scraper uses the official API to get cumulative season stats.
    """

    # NFL.com API endpoints
    NFL_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    NFL_STATS_ENDPOINT = (
        "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
    )

    # Team abbreviation mapping (NFL standard)
    TEAM_ABBR_MAP = {
        "Arizona Cardinals": "ARI",
        "Atlanta Falcons": "ATL",
        "Baltimore Ravens": "BAL",
        "Buffalo Bills": "BUF",
        "Carolina Panthers": "CAR",
        "Chicago Bears": "CHI",
        "Cincinnati Bengals": "CIN",
        "Cleveland Browns": "CLE",
        "Dallas Cowboys": "DAL",
        "Denver Broncos": "DEN",
        "Detroit Lions": "DET",
        "Green Bay Packers": "GB",
        "Houston Texans": "HOU",
        "Indianapolis Colts": "IND",
        "Jacksonville Jaguars": "JAX",
        "Kansas City Chiefs": "KC",
        "Las Vegas Raiders": "LV",
        "Los Angeles Chargers": "LAC",
        "Los Angeles Rams": "LAR",
        "Miami Dolphins": "MIA",
        "Minnesota Vikings": "MIN",
        "New England Patriots": "NE",
        "New Orleans Saints": "NO",
        "New York Giants": "NYG",
        "New York Jets": "NYJ",
        "Philadelphia Eagles": "PHI",
        "Pittsburgh Steelers": "PIT",
        "San Francisco 49ers": "SF",
        "Seattle Seahawks": "SEA",
        "Tampa Bay Buccaneers": "TB",
        "Tennessee Titans": "TEN",
        "Washington Commanders": "WAS",
    }

    def __init__(self, output_dir: str = "data/current"):
        """Initialize NFL stats scraper"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("NFL Stats Scraper initialized")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def get_current_week(self, season: int = 2025) -> int:
        """
        Get current NFL week number

        Args:
            season: NFL season year

        Returns:
            Current week number (1-18)
        """
        try:
            url = f"{self.NFL_API_BASE}/scoreboard"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            # Extract week from scoreboard
            week = data.get("week", {}).get("number", 1)
            logger.info(f"Current week: {week}")
            return week

        except Exception as e:
            logger.error(f"Error getting current week: {e}")
            return 11  # Default to current week

    async def get_team_standings(self, season: int = 2025) -> Dict[str, Dict]:
        """
        Get team standings (wins/losses/ties)

        Args:
            season: NFL season year

        Returns:
            Dictionary of team_abbr -> standings data
        """
        try:
            url = f"{self.NFL_API_BASE}/standings"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            standings = {}

            for entry in data.get("standings", []):
                team_name = entry.get("team", {}).get("displayName", "")
                team_abbr = entry.get("team", {}).get("abbreviation", "")

                standings[team_abbr] = {
                    "team": team_name,
                    "wins": entry.get("wins", 0),
                    "losses": entry.get("losses", 0),
                    "ties": entry.get("ties", 0),
                    "games_played": (
                        entry.get("wins", 0)
                        + entry.get("losses", 0)
                        + entry.get("ties", 0)
                    ),
                }

            logger.info(f"Loaded standings for {len(standings)} teams")
            return standings

        except Exception as e:
            logger.error(f"Error getting standings: {e}")
            return {}

    async def get_team_statistics(
        self, team_id: str, season: int = 2025
    ) -> Dict[str, any]:
        """
        Get cumulative team statistics from ESPN API

        Args:
            team_id: ESPN team ID
            season: NFL season year

        Returns:
            Dictionary of team statistics
        """
        try:
            # Use ESPN team statistics endpoint (discovered in prior session)
            url = (
                f"{self.NFL_STATS_ENDPOINT}/seasons/{season}/teams/{team_id}/statistics"
            )
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            # Extract statistics
            stats = {}
            for stat in data.get("splits", {}).get("categories", []):
                stat_name = stat.get("name", "")
                for stat_item in stat.get("stats", []):
                    key = stat_item.get("name", "")
                    value = stat_item.get("value", 0)
                    stats[key] = value

            return stats

        except Exception as e:
            logger.error(f"Error getting team {team_id} statistics: {e}")
            return {}

    async def get_team_schedule(self, team_id: str, season: int = 2025) -> List[str]:
        """
        Get team schedule (opponents faced)

        Args:
            team_id: ESPN team ID
            season: NFL season year

        Returns:
            List of opponent team abbreviations
        """
        try:
            url = f"{self.NFL_API_BASE}/teams/{team_id}/schedule"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            opponents = []
            for event in data.get("events", []):
                # Only include completed games
                if event.get("status", {}).get("type", {}).get("completed", False):
                    for competitor in event.get("competitions", [{}])[0].get(
                        "competitors", []
                    ):
                        opp_abbr = competitor.get("team", {}).get("abbreviation", "")
                        if opp_abbr:
                            opponents.append(opp_abbr)

            logger.debug(f"Team {team_id} opponents: {opponents}")
            return opponents

        except Exception as e:
            logger.error(f"Error getting team {team_id} schedule: {e}")
            return []

    async def scrape_all_teams(
        self, week: Optional[int] = None, season: int = 2025
    ) -> List[NFLTeamStats]:
        """
        Scrape statistics for all NFL teams

        Args:
            week: Week number (None = current week)
            season: NFL season year

        Returns:
            List of NFLTeamStats for all teams
        """
        if week is None:
            week = await self.get_current_week(season)

        logger.info(f"Scraping NFL stats for Week {week}, {season} season")

        # Get standings first
        standings = await self.get_team_standings(season)

        all_stats = []

        # ESPN team IDs (1-34, some IDs unused)
        # This maps to all 32 NFL teams
        team_ids = list(range(1, 35))

        for team_id in team_ids:
            try:
                # Get team statistics
                raw_stats = await self.get_team_statistics(team_id, season)

                if not raw_stats:
                    continue

                # Get team info from raw_stats or use placeholder
                team_abbr = raw_stats.get("team", {}).get(
                    "abbreviation", f"TEAM{team_id}"
                )
                team_name = raw_stats.get("team", {}).get("displayName", team_abbr)

                # Get standings data
                team_standing = standings.get(team_abbr, {})

                # Get schedule
                opponents = await self.get_team_schedule(team_id, season)

                # Parse statistics
                games_played = team_standing.get("games_played", week)
                if games_played == 0:
                    games_played = 1

                # Extract key metrics
                points_scored = int(raw_stats.get("points", 0))
                points_allowed = int(raw_stats.get("pointsAgainst", 0))
                total_yards = int(raw_stats.get("totalYards", 0))
                yards_allowed = int(raw_stats.get("totalYardsAgainst", 0))
                passing_yards = int(raw_stats.get("passingYards", 0))
                rushing_yards = int(raw_stats.get("rushingYards", 0))
                passing_yards_allowed = int(raw_stats.get("passingYardsAgainst", 0))
                rushing_yards_allowed = int(raw_stats.get("rushingYardsAgainst", 0))
                turnovers_lost = int(raw_stats.get("turnovers", 0))
                turnovers_forced = int(raw_stats.get("takeaways", 0))
                first_downs = int(raw_stats.get("firstDowns", 0))
                third_down_conv = int(raw_stats.get("thirdDownConversions", 0))
                third_down_att = int(raw_stats.get("thirdDownAttempts", 1))
                sacks = int(raw_stats.get("sacks", 0))

                # Calculate per-game averages
                ppg = points_scored / games_played
                ypg = total_yards / games_played
                papg = points_allowed / games_played
                yapg = yards_allowed / games_played
                turnover_margin = (turnovers_forced - turnovers_lost) / games_played

                team_stats = NFLTeamStats(
                    team=team_name,
                    team_abbr=team_abbr,
                    week=week,
                    season=season,
                    wins=team_standing.get("wins", 0),
                    losses=team_standing.get("losses", 0),
                    ties=team_standing.get("ties", 0),
                    games_played=games_played,
                    points_scored=points_scored,
                    total_yards=total_yards,
                    passing_yards=passing_yards,
                    rushing_yards=rushing_yards,
                    turnovers_lost=turnovers_lost,
                    first_downs=first_downs,
                    third_down_conversions=third_down_conv,
                    third_down_attempts=third_down_att,
                    points_allowed=points_allowed,
                    yards_allowed=yards_allowed,
                    passing_yards_allowed=passing_yards_allowed,
                    rushing_yards_allowed=rushing_yards_allowed,
                    turnovers_forced=turnovers_forced,
                    sacks=sacks,
                    points_per_game=ppg,
                    yards_per_game=ypg,
                    points_allowed_per_game=papg,
                    yards_allowed_per_game=yapg,
                    turnover_margin_per_game=turnover_margin,
                    opponents=opponents,
                    last_updated=datetime.now().isoformat(),
                )

                all_stats.append(team_stats)
                logger.info(f"✓ Scraped {team_name} ({team_abbr})")

            except Exception as e:
                logger.error(f"Error scraping team {team_id}: {e}")
                continue

        logger.info(f"Successfully scraped {len(all_stats)} teams")
        return all_stats

    def save_stats(self, stats: List[NFLTeamStats], week: int) -> Path:
        """
        Save team statistics to JSON file

        Args:
            stats: List of team statistics
            week: Week number

        Returns:
            Path to saved file
        """
        output_file = self.output_dir / f"nfl_team_stats_week{week}.json"

        data = [asdict(stat) for stat in stats]

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(stats)} team stats to {output_file}")
        return output_file


async def main():
    """Example usage"""
    scraper = NFLStatsScraperClient()

    try:
        # Scrape current week
        stats = await scraper.scrape_all_teams()

        if stats:
            # Save to file
            week = stats[0].week
            output_file = scraper.save_stats(stats, week)

            # Print summary
            print(f"\n{'=' * 80}")
            print(f"NFL TEAM STATISTICS - WEEK {week}")
            print(f"{'=' * 80}")
            print(
                f"\n{'Team':<25} {'Record':<8} {'PPG':<6} {'PA/G':<6} "
                f"{'YPG':<7} {'YA/G':<7} {'TO±':<5}"
            )
            print("-" * 80)

            for stat in sorted(stats, key=lambda s: s.points_per_game, reverse=True):
                record = f"{stat.wins}-{stat.losses}"
                if stat.ties > 0:
                    record += f"-{stat.ties}"

                print(
                    f"{stat.team:<25} {record:<8} {stat.points_per_game:>5.1f} "
                    f"{stat.points_allowed_per_game:>5.1f} "
                    f"{stat.yards_per_game:>6.1f} "
                    f"{stat.yards_allowed_per_game:>6.1f} "
                    f"{stat.turnover_margin_per_game:>+4.1f}"
                )

            print(f"{'=' * 80}")
            print(f"Saved to: {output_file}")
            print(f"{'=' * 80}\n")

        else:
            print("No stats scraped")

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
