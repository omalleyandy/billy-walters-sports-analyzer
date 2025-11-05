"""
Collect historical NFL odds data for backtesting.

This script fetches historical odds (spreads, totals, moneylines) from
Pro Football Reference and other sources, focusing on opening and closing lines.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import time
import click
import re
from walters.historical_db import HistoricalDatabase


class ProFootballReferenceOddsCollector:
    """Collect historical odds from Pro Football Reference."""

    BASE_URL = "https://www.pro-football-reference.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_season_odds(self, season: int) -> List[Dict]:
        """Get odds for entire season.

        Args:
            season: Year (e.g., 2024)

        Returns:
            List of odds dictionaries
        """
        odds_data = []

        # Regular season weeks
        for week in range(1, 19):  # NFL has 18 weeks now
            click.echo(f"Fetching Week {week}...")
            week_odds = self.get_week_odds(season, week, is_playoff=False)
            odds_data.extend(week_odds)
            time.sleep(3)  # Respectful rate limiting

        # Playoffs
        playoff_weeks = ['WildCard', 'Division', 'ConfChamp', 'SuperBowl']
        for playoff_week in playoff_weeks:
            click.echo(f"Fetching {playoff_week}...")
            week_odds = self.get_playoff_week_odds(season, playoff_week)
            odds_data.extend(week_odds)
            time.sleep(3)

        return odds_data

    def get_week_odds(self, season: int, week: int, is_playoff: bool = False) -> List[Dict]:
        """Get odds for a specific week.

        Args:
            season: Year
            week: Week number
            is_playoff: Whether this is a playoff week

        Returns:
            List of odds dictionaries
        """
        try:
            url = f"{self.BASE_URL}/years/{season}/games.htm"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'games'})

            if not table:
                click.echo(f"No games table found for {season} week {week}", err=True)
                return []

            odds_data = []
            current_week = 0

            for row in table.find_all('tr'):
                # Check for week header
                week_header = row.find('th', {'data-stat': 'week_num'})
                if week_header and week_header.text.strip().isdigit():
                    current_week = int(week_header.text.strip())

                # Skip if not the week we want
                if current_week != week:
                    continue

                # Parse game row
                cells = row.find_all(['th', 'td'])
                if len(cells) < 10:
                    continue

                try:
                    game_data = self._parse_game_row(cells, season, week)
                    if game_data:
                        odds_data.extend(game_data)
                except Exception as e:
                    continue

            return odds_data

        except Exception as e:
            click.echo(f"Error fetching week {week}: {e}", err=True)
            return []

    def get_playoff_week_odds(self, season: int, playoff_round: str) -> List[Dict]:
        """Get playoff odds.

        Args:
            season: Year
            playoff_round: 'WildCard', 'Division', 'ConfChamp', or 'SuperBowl'

        Returns:
            List of odds dictionaries
        """
        # Similar to get_week_odds but for playoffs
        return []

    def _parse_game_row(self, cells: List, season: int, week: int) -> Optional[List[Dict]]:
        """Parse a game row to extract odds.

        Args:
            cells: Table cells from the row
            season: Season year
            week: Week number

        Returns:
            List of odds dictionaries (opening and closing)
        """
        try:
            # Pro Football Reference format:
            # Week, Day, Date, Time, Winner/Loser, @, Loser/Winner, PtsW, PtsL, YdsW, TOW, YdsL, TOL
            # Note: Spread data might be in different columns depending on page structure

            game_date = None
            away_team = None
            home_team = None
            spread = None

            # This is a simplified parser - actual PFR structure varies
            # You may need to adjust based on actual HTML structure

            for cell in cells:
                data_stat = cell.get('data-stat', '')

                if data_stat == 'game_date':
                    game_date = cell.text.strip()
                elif data_stat == 'loser':
                    # In PFR, @ indicates away team
                    away_team = cell.text.strip()
                elif data_stat == 'winner':
                    home_team = cell.text.strip()
                elif data_stat == 'vegas_line':
                    spread_text = cell.text.strip()
                    if spread_text and spread_text != '':
                        # Parse spread (e.g., "-7.5", "PK")
                        spread = self._parse_spread(spread_text)

            if not all([game_date, away_team, home_team]):
                return None

            # Create game ID
            game_id = f"pfr_{season}_{week}_{away_team}_{home_team}".replace(' ', '_')

            odds_list = []

            # Add closing line (what PFR typically shows)
            if spread is not None:
                closing_odds = {
                    'game_id': game_id,
                    'sportsbook': 'consensus',
                    'odds_type': 'spread',
                    'line_type': 'standard',
                    'away_line': spread if spread > 0 else abs(spread),
                    'away_price': -110,
                    'home_line': abs(spread) if spread < 0 else -spread,
                    'home_price': -110,
                    'total_line': None,
                    'over_price': None,
                    'under_price': None,
                    'timestamp': f"{game_date}T12:00:00",
                    'is_opening': 0,
                    'is_closing': 1,
                    'data_source': 'pro_football_reference'
                }
                odds_list.append(closing_odds)

            return odds_list if odds_list else None

        except Exception as e:
            return None

    def _parse_spread(self, spread_text: str) -> Optional[float]:
        """Parse spread text to float.

        Args:
            spread_text: Spread string (e.g., "-7.5", "PK")

        Returns:
            Float spread or None
        """
        if not spread_text or spread_text in ['', 'PK', 'pk']:
            return 0.0

        # Remove any non-numeric characters except . and -
        spread_clean = re.sub(r'[^\d.-]', '', spread_text)

        try:
            return float(spread_clean)
        except:
            return None


class SportsOddsHistoryCollector:
    """Collect historical odds from Sports Odds History API (sportsoddshistory.com)."""

    BASE_URL = "https://www.sportsoddshistory.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_season_odds(self, season: int) -> List[Dict]:
        """Get odds for entire season from Sports Odds History.

        Note: This site requires web scraping. Structure may change.

        Args:
            season: Year

        Returns:
            List of odds dictionaries
        """
        click.echo("Sports Odds History scraping not yet implemented")
        click.echo("Alternative: Manually download CSV from sportsoddshistory.com")
        return []


def parse_csv_odds(csv_path: str, season: int) -> List[Dict]:
    """Parse odds from manually downloaded CSV.

    Args:
        csv_path: Path to CSV file
        season: Season year

    Returns:
        List of odds dictionaries
    """
    import csv

    odds_data = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # CSV format varies by source - adjust field names as needed
            game_id = f"csv_{season}_{row.get('Week', '')}_{row.get('AwayTeam', '')}_{row.get('HomeTeam', '')}".replace(' ', '_')

            # Opening odds
            if row.get('OpenSpread'):
                opening_odds = {
                    'game_id': game_id,
                    'sportsbook': row.get('Sportsbook', 'consensus'),
                    'odds_type': 'spread',
                    'line_type': 'standard',
                    'away_line': float(row.get('OpenSpread', 0)),
                    'away_price': int(row.get('OpenAwayPrice', -110)),
                    'home_line': -float(row.get('OpenSpread', 0)),
                    'home_price': int(row.get('OpenHomePrice', -110)),
                    'total_line': float(row.get('OpenTotal', 0)) if row.get('OpenTotal') else None,
                    'over_price': int(row.get('OpenOverPrice', -110)) if row.get('OpenOverPrice') else None,
                    'under_price': int(row.get('OpenUnderPrice', -110)) if row.get('OpenUnderPrice') else None,
                    'timestamp': row.get('GameDate', datetime.now().isoformat()),
                    'is_opening': 1,
                    'is_closing': 0,
                    'data_source': 'csv_import'
                }
                odds_data.append(opening_odds)

            # Closing odds
            if row.get('CloseSpread'):
                closing_odds = {
                    'game_id': game_id,
                    'sportsbook': row.get('Sportsbook', 'consensus'),
                    'odds_type': 'spread',
                    'line_type': 'standard',
                    'away_line': float(row.get('CloseSpread', 0)),
                    'away_price': int(row.get('CloseAwayPrice', -110)),
                    'home_line': -float(row.get('CloseSpread', 0)),
                    'home_price': int(row.get('CloseHomePrice', -110)),
                    'total_line': float(row.get('CloseTotal', 0)) if row.get('CloseTotal') else None,
                    'over_price': int(row.get('CloseOverPrice', -110)) if row.get('CloseOverPrice') else None,
                    'under_price': int(row.get('CloseUnderPrice', -110)) if row.get('CloseUnderPrice') else None,
                    'timestamp': row.get('GameDate', datetime.now().isoformat()),
                    'is_opening': 0,
                    'is_closing': 1,
                    'data_source': 'csv_import'
                }
                odds_data.append(closing_odds)

    return odds_data


@click.command()
@click.option('--source', default='pfr', type=click.Choice(['pfr', 'csv']),
              help='Data source: pfr (Pro Football Reference) or csv (manual CSV)')
@click.option('--start-season', default=2020, type=int,
              help='Starting season year')
@click.option('--end-season', default=2024, type=int,
              help='Ending season year')
@click.option('--csv-path', type=click.Path(exists=True),
              help='Path to CSV file (if source=csv)')
@click.option('--db-path', default='data/historical/historical_games.db',
              help='Path to historical database')
@click.option('--dry-run', is_flag=True,
              help='Print data without saving to database')
def main(source: str, start_season: int, end_season: int,
         csv_path: Optional[str], db_path: str, dry_run: bool):
    """Collect historical NFL odds data."""

    click.echo(f"Collecting odds from {source.upper()}")
    click.echo(f"Seasons: {start_season} to {end_season}")

    if source == 'csv' and not csv_path:
        click.echo("Error: --csv-path required when source=csv", err=True)
        return

    if not dry_run:
        db = HistoricalDatabase(db_path)
        click.echo(f"Database initialized at: {db_path}")

    total_odds = 0

    if source == 'pfr':
        collector = ProFootballReferenceOddsCollector()

        for season in range(start_season, end_season + 1):
            click.echo(f"\n{'='*60}")
            click.echo(f"Season: {season}")
            click.echo(f"{'='*60}")

            odds_list = collector.get_season_odds(season)
            click.echo(f"Found {len(odds_list)} odds entries")

            for odds in odds_list:
                if dry_run:
                    click.echo(f"  {odds['game_id']}: {odds['odds_type']} {odds['away_line']}/{odds['home_line']}")
                else:
                    try:
                        db.insert_odds(odds)
                        total_odds += 1
                    except Exception as e:
                        click.echo(f"Error inserting odds: {e}", err=True)

    elif source == 'csv':
        for season in range(start_season, end_season + 1):
            click.echo(f"\n{'='*60}")
            click.echo(f"Season: {season}")
            click.echo(f"{'='*60}")

            odds_list = parse_csv_odds(csv_path, season)
            click.echo(f"Found {len(odds_list)} odds entries")

            for odds in odds_list:
                if dry_run:
                    click.echo(f"  {odds['game_id']}: {odds['odds_type']}")
                else:
                    try:
                        db.insert_odds(odds)
                        total_odds += 1
                    except Exception as e:
                        click.echo(f"Error inserting odds: {e}", err=True)

    if not dry_run:
        db.close()
        click.echo(f"\n{'='*60}")
        click.echo(f"Successfully inserted {total_odds} odds entries")
    else:
        click.echo(f"\nDry run complete.")

    click.echo("\n" + "="*60)
    click.echo("NOTE: For comprehensive historical odds data, consider:")
    click.echo("1. sportsoddshistory.com - Download CSV files")
    click.echo("2. sportsbookreviewsonline.com - Historical consensus lines")
    click.echo("3. Manual data entry for key games")


if __name__ == '__main__':
    main()
