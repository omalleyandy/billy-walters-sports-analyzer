"""
Collect historical NFL game data for backtesting.

This script fetches historical NFL game results from 2020-2024 seasons
using ESPN's API and stores them in the historical database.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import click
from walters.historical_db import HistoricalDatabase


class ESPNGameCollector:
    """Collect historical games from ESPN API."""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_season_schedule(self, sport: str = "nfl", season: int = 2024) -> List[Dict]:
        """Get all games for a season.

        Args:
            sport: 'nfl' or 'college-football'
            season: Year (e.g., 2024)

        Returns:
            List of game dictionaries
        """
        games = []

        # ESPN API uses season type: 1=preseason, 2=regular, 3=postseason
        for season_type in [2, 3]:  # Regular season and playoffs
            click.echo(f"Fetching {season} season type {season_type}...")

            url = f"{self.BASE_URL}/{sport}/scoreboard"
            params = {
                'seasontype': season_type,
                'dates': season,
                'limit': 1000
            }

            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if 'events' in data:
                    for event in data['events']:
                        game = self._parse_espn_game(event, sport, season, season_type)
                        if game:
                            games.append(game)

                time.sleep(1)  # Rate limiting

            except Exception as e:
                click.echo(f"Error fetching {season} type {season_type}: {e}", err=True)
                continue

        return games

    def get_week_schedule(self, sport: str = "nfl", season: int = 2024, week: int = 1) -> List[Dict]:
        """Get games for a specific week.

        Args:
            sport: 'nfl' or 'college-football'
            season: Year (e.g., 2024)
            week: Week number

        Returns:
            List of game dictionaries
        """
        games = []

        url = f"{self.BASE_URL}/{sport}/scoreboard"
        params = {
            'seasontype': 2,  # Regular season
            'week': week,
            'dates': season
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'events' in data:
                for event in data['events']:
                    game = self._parse_espn_game(event, sport, season, 2, week)
                    if game:
                        games.append(game)

        except Exception as e:
            click.echo(f"Error fetching week {week}: {e}", err=True)

        return games

    def _parse_espn_game(self, event: Dict, sport: str, season: int,
                        season_type: int, week: Optional[int] = None) -> Optional[Dict]:
        """Parse ESPN game event into our format.

        Args:
            event: ESPN event dictionary
            sport: Sport type
            season: Season year
            season_type: Season type (2=regular, 3=playoff)
            week: Week number (optional)

        Returns:
            Parsed game dictionary or None
        """
        try:
            game_id = event['id']
            game_date = event['date'][:10]  # YYYY-MM-DD
            game_time = event['date'][11:19]  # HH:MM:SS

            # Get teams
            competitions = event.get('competitions', [])
            if not competitions:
                return None

            competition = competitions[0]
            competitors = competition.get('competitors', [])

            if len(competitors) != 2:
                return None

            # ESPN lists home team first usually
            home_team = None
            away_team = None

            for comp in competitors:
                team_name = comp['team']['abbreviation']
                if comp.get('homeAway') == 'home':
                    home_team = team_name
                    home_score = comp.get('score')
                else:
                    away_team = team_name
                    away_score = comp.get('score')

            # Venue info
            venue = competition.get('venue', {}).get('fullName')
            is_neutral = competition.get('neutralSite', False)

            # Status
            status = event.get('status', {}).get('type', {}).get('name', 'scheduled')
            game_status = 'completed' if status == 'STATUS_FINAL' else 'scheduled'

            # Playoff detection
            is_playoff = season_type == 3

            # If week not provided, try to extract from event
            if week is None:
                week = event.get('week', {}).get('number')

            # Divisional game detection (would need team division lookup)
            is_divisional = False  # TODO: Add division lookup

            return {
                'game_id': f"espn_{game_id}",
                'sport': 'NFL' if sport == 'nfl' else 'CFB',
                'season': season,
                'week': week,
                'game_date': game_date,
                'game_time': game_time,
                'away_team': away_team,
                'home_team': home_team,
                'away_score': int(away_score) if away_score else None,
                'home_score': int(home_score) if home_score else None,
                'venue': venue,
                'is_dome': 0,  # TODO: Add dome detection
                'is_neutral': 1 if is_neutral else 0,
                'is_playoff': 1 if is_playoff else 0,
                'is_divisional': 1 if is_divisional else 0,
                'game_status': game_status,
                'data_source': 'espn_api'
            }

        except Exception as e:
            click.echo(f"Error parsing game: {e}", err=True)
            return None


@click.command()
@click.option('--sport', default='nfl', type=click.Choice(['nfl', 'college-football']),
              help='Sport to collect data for')
@click.option('--start-season', default=2020, type=int,
              help='Starting season year')
@click.option('--end-season', default=2024, type=int,
              help='Ending season year')
@click.option('--week', type=int,
              help='Specific week to collect (optional)')
@click.option('--db-path', default='data/historical/historical_games.db',
              help='Path to historical database')
@click.option('--dry-run', is_flag=True,
              help='Print data without saving to database')
def main(sport: str, start_season: int, end_season: int,
         week: Optional[int], db_path: str, dry_run: bool):
    """Collect historical NFL/CFB game data from ESPN."""

    click.echo(f"Collecting {sport.upper()} games from {start_season} to {end_season}")

    collector = ESPNGameCollector()

    if not dry_run:
        db = HistoricalDatabase(db_path)
        click.echo(f"Database initialized at: {db_path}")

    total_games = 0

    for season in range(start_season, end_season + 1):
        click.echo(f"\n{'='*60}")
        click.echo(f"Season: {season}")
        click.echo(f"{'='*60}")

        if week is not None:
            # Collect specific week
            games = collector.get_week_schedule(sport, season, week)
            click.echo(f"Found {len(games)} games for week {week}")
        else:
            # Collect entire season
            games = collector.get_season_schedule(sport, season)
            click.echo(f"Found {len(games)} games for season")

        # Insert into database or print
        for game in games:
            if dry_run:
                click.echo(f"  {game['game_date']} - {game['away_team']} @ {game['home_team']}")
                if game['away_score'] is not None:
                    click.echo(f"    Score: {game['away_score']}-{game['home_score']}")
            else:
                try:
                    db.insert_game(game)
                    total_games += 1
                except Exception as e:
                    click.echo(f"Error inserting game {game['game_id']}: {e}", err=True)

    if not dry_run:
        db.close()
        click.echo(f"\n{'='*60}")
        click.echo(f"Successfully inserted {total_games} games into database")
        click.echo(f"Database: {db_path}")
    else:
        click.echo(f"\nDry run complete. Found {len(games)} games.")


if __name__ == '__main__':
    main()
