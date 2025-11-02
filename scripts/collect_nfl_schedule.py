#!/usr/bin/env python3
"""
ESPN API NFL Schedule/Scores Scraper

Collects NFL game data from ESPN's public API to update Billy Walters power ratings.
Supports backfilling historical data and weekly updates.

Usage:
    # Single week
    python scripts/collect_nfl_schedule.py --week 9 --season 2025

    # Backfill entire season
    python scripts/collect_nfl_schedule.py --season 2025 --start-week 1 --end-week 9

    # Current week (auto-detect)
    python scripts/collect_nfl_schedule.py --season 2025 --current
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp not installed. Run: uv add aiohttp")
    exit(1)


class ESPNNFLScraper:
    """Scraper for ESPN's NFL API."""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

    # Season type mappings
    SEASON_TYPES = {
        "preseason": 1,
        "regular": 2,
        "postseason": 3,
        "offseason": 4
    }

    def __init__(self, output_dir: str = "data/nfl_schedule"):
        """
        Initialize ESPN NFL scraper.

        Args:
            output_dir: Directory to save scraped data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_scoreboard(
        self,
        season: int,
        week: int,
        season_type: str = "regular"
    ) -> Dict[str, Any]:
        """
        Fetch scoreboard data from ESPN API.

        Args:
            season: Season year (e.g., 2025)
            week: Week number (1-18 for regular season)
            season_type: "preseason", "regular", or "postseason"

        Returns:
            Raw JSON response from ESPN API
        """
        url = f"{self.BASE_URL}/scoreboard"
        params = {
            "seasontype": self.SEASON_TYPES.get(season_type, 2),
            "week": week
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"ESPN API returned status {response.status}")

                    data = await response.json()
                    return data
            except Exception as e:
                print(f"ERROR fetching week {week}: {e}")
                return {}

    def parse_games(self, espn_data: Dict[str, Any], season: int, week: int) -> List[Dict[str, Any]]:
        """
        Parse ESPN scoreboard JSON into structured game data.

        Args:
            espn_data: Raw ESPN API response
            season: Season year
            week: Week number

        Returns:
            List of parsed game dictionaries
        """
        games = []

        for event in espn_data.get("events", []):
            try:
                game = self._parse_single_game(event, season, week)
                if game:
                    games.append(game)
            except Exception as e:
                print(f"ERROR parsing game {event.get('id', 'unknown')}: {e}")
                continue

        return games

    def _parse_single_game(self, event: Dict[str, Any], season: int, week: int) -> Optional[Dict[str, Any]]:
        """Parse a single ESPN event into game data."""
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])

        if len(competitors) != 2:
            return None

        # Extract home and away teams
        home_team = None
        away_team = None

        for competitor in competitors:
            team_data = {
                "name": competitor["team"]["displayName"],
                "abbreviation": competitor["team"]["abbreviation"],
                "location": competitor["team"]["location"],
                "score": int(competitor.get("score", 0)),
                "winner": competitor.get("winner", False),
                "record": competitor.get("records", [{}])[0].get("summary", "0-0") if competitor.get("records") else "0-0"
            }

            if competitor["homeAway"] == "home":
                home_team = team_data
            else:
                away_team = team_data

        if not home_team or not away_team:
            return None

        # Extract game metadata
        status = event.get("status", {})
        game_status = status.get("type", {}).get("name", "scheduled")
        is_completed = status.get("type", {}).get("completed", False)

        # Extract odds if available
        odds_data = {}
        if "odds" in competition and competition["odds"]:
            odds = competition["odds"][0]
            odds_data = {
                "spread": odds.get("details", ""),
                "over_under": odds.get("overUnder", 0.0),
                "home_moneyline": odds.get("homeTeamOdds", {}).get("moneyLine"),
                "away_moneyline": odds.get("awayTeamOdds", {}).get("moneyLine")
            }

        # Extract venue information
        venue = competition.get("venue", {})
        venue_data = {
            "name": venue.get("fullName", ""),
            "city": venue.get("address", {}).get("city", ""),
            "state": venue.get("address", {}).get("state", ""),
            "indoor": venue.get("indoor", False)
        }

        # Build complete game data
        game = {
            # Source metadata
            "source": "espn",
            "sport": "nfl",
            "league": "NFL",
            "collected_at": datetime.now().isoformat(),

            # Game identification
            "game_id": f"espn_{event['id']}",
            "espn_event_id": event["id"],
            "season": season,
            "week": week,
            "season_type": "regular",  # TODO: Support other season types

            # Game timing
            "game_date": event["date"],
            "game_time": status.get("type", {}).get("detail", ""),
            "status": game_status,
            "is_completed": is_completed,

            # Teams
            "home_team": home_team["name"],
            "home_abbr": home_team["abbreviation"],
            "home_location": home_team["location"],
            "home_score": home_team["score"],
            "home_winner": home_team["winner"],
            "home_record": home_team["record"],

            "away_team": away_team["name"],
            "away_abbr": away_team["abbreviation"],
            "away_location": away_team["location"],
            "away_score": away_team["score"],
            "away_winner": away_team["winner"],
            "away_record": away_team["record"],

            # Venue
            "venue_name": venue_data["name"],
            "venue_city": venue_data["city"],
            "venue_state": venue_data["state"],
            "is_dome": venue_data["indoor"],

            # Betting data
            "odds_spread": odds_data.get("spread", ""),
            "odds_total": odds_data.get("over_under", 0.0),
            "home_moneyline": odds_data.get("home_moneyline"),
            "away_moneyline": odds_data.get("away_moneyline"),

            # Additional metadata
            "event_name": event.get("name", ""),
            "short_name": event.get("shortName", ""),
        }

        return game

    def save_games(self, games: List[Dict[str, Any]], week: int, season: int) -> Dict[str, Path]:
        """
        Save games to JSONL and JSON formats.

        Args:
            games: List of game dictionaries
            week: Week number
            season: Season year

        Returns:
            Dictionary with file paths {format: path}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSONL format (one game per line, for streaming/processing)
        jsonl_file = self.output_dir / f"nfl_week{week}_{season}_{timestamp}.jsonl"
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for game in games:
                f.write(json.dumps(game) + '\n')

        # JSON format (for human readability)
        json_file = self.output_dir / f"nfl_week{week}_{season}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "season": season,
                    "week": week,
                    "collected_at": datetime.now().isoformat(),
                    "source": "espn_api",
                    "game_count": len(games)
                },
                "games": games
            }, f, indent=2)

        return {
            "jsonl": jsonl_file,
            "json": json_file
        }

    async def scrape_week(self, season: int, week: int) -> List[Dict[str, Any]]:
        """
        Scrape a single week of games.

        Args:
            season: Season year
            week: Week number

        Returns:
            List of game dictionaries
        """
        print(f"Fetching NFL Week {week}, {season} from ESPN API...")

        data = await self.fetch_scoreboard(season, week, "regular")

        if not data:
            print(f"  No data returned for Week {week}")
            return []

        games = self.parse_games(data, season, week)
        print(f"  Found {len(games)} games")

        # Save to files
        files = self.save_games(games, week, season)
        print(f"  Saved to:")
        print(f"    JSONL: {files['jsonl']}")
        print(f"    JSON:  {files['json']}")

        return games

    async def scrape_season(
        self,
        season: int,
        start_week: int = 1,
        end_week: int = 18
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Scrape multiple weeks (backfill mode).

        Args:
            season: Season year
            start_week: First week to scrape
            end_week: Last week to scrape

        Returns:
            Dictionary mapping week number to list of games
        """
        print(f"\n=== Backfilling NFL {season} Season (Weeks {start_week}-{end_week}) ===\n")

        all_games = {}

        for week in range(start_week, end_week + 1):
            games = await self.scrape_week(season, week)
            all_games[week] = games

            # Rate limiting - be respectful to ESPN
            if week < end_week:
                await asyncio.sleep(1)

        # Summary
        total_games = sum(len(games) for games in all_games.values())
        print(f"\n=== Backfill Complete ===")
        print(f"Total weeks: {len(all_games)}")
        print(f"Total games: {total_games}")

        return all_games


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape NFL schedule and scores from ESPN API"
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="NFL season year (default: 2025)"
    )
    parser.add_argument(
        "--week",
        type=int,
        help="Single week to scrape (1-18)"
    )
    parser.add_argument(
        "--start-week",
        type=int,
        default=1,
        help="Start week for backfill (default: 1)"
    )
    parser.add_argument(
        "--end-week",
        type=int,
        default=18,
        help="End week for backfill (default: 18)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/nfl_schedule",
        help="Output directory (default: data/nfl_schedule)"
    )
    parser.add_argument(
        "--current",
        action="store_true",
        help="Scrape current week (auto-detect)"
    )

    args = parser.parse_args()

    scraper = ESPNNFLScraper(output_dir=args.output_dir)

    if args.current:
        # TODO: Implement current week detection from ESPN API
        print("ERROR: --current flag not yet implemented. Please specify --week")
        return

    if args.week:
        # Single week mode
        await scraper.scrape_week(args.season, args.week)
    else:
        # Backfill mode
        await scraper.scrape_season(args.season, args.start_week, args.end_week)


if __name__ == "__main__":
    asyncio.run(main())
