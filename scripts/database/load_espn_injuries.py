#!/usr/bin/env python3
"""
Load ESPN injury data into database.

Fetches injury reports from ESPN API for all NFL and NCAAF teams
and populates the espn_injuries table with player injury information.

Uses ESPN's core API which provides real-time injury data.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from src.db import get_db_connection
from src.data.espn_api_client import ESPNAPIClient


# Severity classification for key positions
# Elite = starter with high impact on team success
INJURY_IMPACT_VALUES = {
    'NFL': {
        'QB': 4.5,       # Elite position - 4.5 pt impact
        'RB': 2.5,
        'WR': 1.8,
        'TE': 1.5,
        'LT': 1.5,       # Offensive line
        'LG': 1.2,
        'RG': 1.2,
        'RT': 1.5,
        'C': 1.2,
        'DE': 1.5,       # Defensive line
        'DT': 1.5,
        'EDGE': 1.8,     # Pass rusher
        'OLB': 1.2,      # Linebacker
        'MLB': 1.5,
        'ILB': 1.2,
        'CB': 1.2,       # Defensive back
        'FS': 1.2,
        'SS': 1.0,
    },
    'NCAAF': {
        'QB': 5.0,       # Larger impact in college due to depth
        'RB': 3.5,
        'WR': 2.5,
        'TE': 2.0,
        'LT': 1.5,
        'LG': 1.2,
        'RG': 1.2,
        'RT': 1.5,
        'C': 1.2,
        'DE': 2.0,
        'DT': 1.8,
        'EDGE': 2.0,
        'LB': 1.8,
        'CB': 1.5,
        'FS': 1.5,
        'SS': 1.2,
    }
}


class ESPNInjuriesLoader:
    """Load ESPN injury data into database."""

    def __init__(self):
        self.db = get_db_connection()
        self.api = ESPNAPIClient()

    def get_nfl_teams(self) -> dict:
        """Get all NFL teams with IDs."""
        try:
            data = self.api.get_nfl_teams()
            teams = {}
            try:
                sports = data.get('sports', [])
                if sports:
                    sport = sports[0]
                    leagues = sport.get('leagues', [])
                    if leagues:
                        league = leagues[0]
                        team_list = league.get('teams', [])
                        for team_entry in team_list:
                            team = team_entry.get('team', {})
                            team_id = team.get('id')
                            team_name = team.get('displayName')
                            if team_id and team_name:
                                teams[team_id] = team_name
            except (KeyError, IndexError, TypeError):
                pass
            return teams
        except Exception as e:
            print(f"  [ERROR] Failed to get NFL teams: {str(e)}")
            return {}

    def get_ncaaf_teams(self) -> dict:
        """Get all NCAAF FBS teams with IDs."""
        try:
            data = self.api.get_ncaaf_teams(group='80')  # FBS = group 80
            teams = {}
            try:
                sports = data.get('sports', [])
                if sports:
                    sport = sports[0]
                    leagues = sport.get('leagues', [])
                    if leagues:
                        league = leagues[0]
                        team_list = league.get('teams', [])
                        for team_entry in team_list:
                            team = team_entry.get('team', {})
                            team_id = team.get('id')
                            team_name = team.get('displayName')
                            if team_id and team_name:
                                teams[team_id] = team_name
            except (KeyError, IndexError, TypeError):
                pass
            return teams
        except Exception as e:
            print(f"  [ERROR] Failed to get NCAAF teams: {str(e)}")
            return {}

    def get_injury_severity(self, position: str) -> str:
        """Classify injury severity based on position."""
        pos_upper = position.upper() if position else 'UNKNOWN'
        # Extract primary position (e.g., "QB" from "QB (P)")
        pos_base = pos_upper.split('(')[0].strip()
        # Map position to severity level
        if pos_base in ['QB']:
            return 'ELITE'
        elif pos_base in ['RB', 'WR', 'DE', 'MLB']:
            return 'STARTER'
        elif pos_base in ['TE', 'OL', 'LB', 'DB']:
            return 'BACKUP'
        else:
            return 'RESERVE'

    def get_impact_estimate(self, position: str, league: str) -> float:
        """Get impact estimate for injury based on position and league."""
        pos_upper = position.upper() if position else 'UNKNOWN'
        pos_base = pos_upper.split('(')[0].strip()

        impact_map = INJURY_IMPACT_VALUES.get(league, {})
        if pos_base in impact_map:
            return impact_map[pos_base]
        # Default impact based on severity
        severity = self.get_injury_severity(position)
        if severity == 'ELITE':
            return 3.0
        elif severity == 'STARTER':
            return 1.5
        else:
            return 0.5

    def load_injuries_for_league(self, league: str) -> tuple[int, int]:
        """Load injuries for a league."""
        print(f"\n[LOAD] {league.upper()} Injuries...")

        if league == 'NFL':
            teams = self.get_nfl_teams()
            league_code = 'nfl'
            db_league = 'NFL'
        else:
            teams = self.get_ncaaf_teams()
            league_code = 'college-football'
            db_league = 'NCAAF'

        if not teams:
            print(f"  [WARNING] Could not retrieve {league.upper()} teams")
            return 0, 0

        print(f"  Found {len(teams)} {league.upper()} teams")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        total_inserted = 0
        total_skipped = 0

        for team_id, team_name in teams.items():
            try:
                injury_data = self.api.get_team_injuries(team_id, league_code)
                injuries = injury_data.get('items', [])

                if not injuries:
                    continue

                for injury in injuries:
                    try:
                        # Extract player info
                        athlete = injury.get('athlete', {})
                        player_name = athlete.get('displayName')
                        player_position = athlete.get('position', {}).get(
                            'abbreviation'
                        )
                        jersey = athlete.get('jersey')

                        if not player_name:
                            continue

                        # Extract injury details
                        status = injury.get('status')
                        injury_type = injury.get('type')

                        # Calculate severity and impact
                        severity = self.get_injury_severity(player_position)
                        impact = self.get_impact_estimate(player_position, db_league)

                        # Parse report date
                        date_str = injury.get('date')
                        report_date = None
                        if date_str:
                            try:
                                report_date = datetime.fromisoformat(
                                    date_str.replace('Z', '+00:00')
                                )
                            except Exception:
                                pass

                        # Get current week (would need season calendar for historical)
                        week = 12  # TODO: Auto-detect current week
                        season = 2025

                        cursor.execute("""
                            INSERT INTO espn_injuries
                            (season, week, league, game_id, player_name,
                             position, jersey_number, team, injury_type,
                             status, severity, impact_estimate, report_date,
                             data_source, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, NOW())
                        """, (
                            season, week, db_league, None,
                            player_name,
                            player_position, jersey,
                            team_name, injury_type,
                            status, severity, impact,
                            report_date, 'espn'
                        ))

                        total_inserted += cursor.rowcount

                    except Exception as e:
                        total_skipped += 1

            except Exception as e:
                print(f"  [WARNING] Failed to fetch injuries for {team_name}: "
                      f"{str(e)}")

        conn.commit()
        cursor.close()

        print(f"  Inserted {total_inserted} injuries, "
              f"skipped {total_skipped} errors")
        return total_inserted, total_skipped

    def verify_data(self):
        """Verify data loaded successfully."""
        print("\n[VERIFY] ESPN Injuries in Database...")

        result = self.db.execute_query("""
            SELECT league, COUNT(*) as count
            FROM espn_injuries
            GROUP BY league
            ORDER BY league
        """)

        total = 0
        for row in result:
            count = row['count']
            total += count
            print(f"  {row['league']}: {count} injuries")

        # Show by severity
        result = self.db.execute_query("""
            SELECT league, severity, COUNT(*) as count
            FROM espn_injuries
            GROUP BY league, severity
            ORDER BY league, severity
        """)

        if result:
            print(f"\n  By severity:")
            for row in result:
                print(f"    {row['league']} {row['severity']}: "
                      f"{row['count']} players")

        print(f"  Total: {total} injury records")
        return total

    def main(self):
        """Run full load."""
        print("=" * 70)
        print("LOAD ESPN INJURIES")
        print("=" * 70)

        try:
            # Load NFL and NCAAF injuries
            nfl_inserted, nfl_skipped = self.load_injuries_for_league('NFL')
            ncaaf_inserted, ncaaf_skipped = (
                self.load_injuries_for_league('NCAAF')
            )

            # Verify
            total = self.verify_data()

            print("\n" + "=" * 70)
            print("[OK] ESPN INJURIES LOADED")
            print("=" * 70)
            print(f"\nSummary:")
            print(f"  NFL:   {nfl_inserted} inserted, {nfl_skipped} skipped")
            print(f"  NCAAF: {ncaaf_inserted} inserted, {ncaaf_skipped} "
                  f"skipped")
            print(f"  Total: {total} injury records in database")
            print("\nNext steps:")
            print("  1. Load ESPN team statistics")
            print("  2. Load ESPN scoreboards and standings")
            print("  3. Build custom power rating engine")

            return True

        except Exception as e:
            print(f"\n[ERROR] Load failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.db.close_all_connections()


if __name__ == "__main__":
    loader = ESPNInjuriesLoader()
    success = loader.main()
    sys.exit(0 if success else 1)
