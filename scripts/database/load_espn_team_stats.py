#!/usr/bin/env python3
"""
Load ESPN team statistics into database.

Fetches offensive and defensive statistics from ESPN API for all NFL and NCAAF teams
and populates the espn_team_stats table with per-game averages and efficiency metrics.

Uses ESPN's site API which provides comprehensive team statistics.
"""

import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.db import get_db_connection
from src.data.espn_api_client import ESPNAPIClient


class ESPNTeamStatsLoader:
    """Load ESPN team statistics into database."""

    def __init__(self):
        self.db = get_db_connection()
        self.api = ESPNAPIClient()

    def get_nfl_teams(self) -> dict:
        """Get all NFL teams with IDs."""
        try:
            data = self.api.get_nfl_teams()
            teams = {}
            try:
                sports = data.get("sports", [])
                if sports:
                    sport = sports[0]
                    leagues = sport.get("leagues", [])
                    if leagues:
                        league = leagues[0]
                        team_list = league.get("teams", [])
                        for team_entry in team_list:
                            team = team_entry.get("team", {})
                            team_id = team.get("id")
                            team_name = team.get("displayName")
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
            data = self.api.get_ncaaf_teams(group="80")  # FBS = group 80
            teams = {}
            try:
                sports = data.get("sports", [])
                if sports:
                    sport = sports[0]
                    leagues = sport.get("leagues", [])
                    if leagues:
                        league = leagues[0]
                        team_list = league.get("teams", [])
                        for team_entry in team_list:
                            team = team_entry.get("team", {})
                            team_id = team.get("id")
                            team_name = team.get("displayName")
                            if team_id and team_name:
                                teams[team_id] = team_name
            except (KeyError, IndexError, TypeError):
                pass
            return teams
        except Exception as e:
            print(f"  [ERROR] Failed to get NCAAF teams: {str(e)}")
            return {}

    def extract_stat(self, stats: dict, category: str, name: str) -> float | None:
        """Extract a statistic from stats dictionary."""
        try:
            if category not in stats:
                return None
            cat_stats = stats[category]
            if isinstance(cat_stats, list):
                for stat in cat_stats:
                    if stat.get("name") == name:
                        val = stat.get("displayValue")
                        if val:
                            return float(val.replace(",", ""))
            elif isinstance(cat_stats, dict):
                for stat in cat_stats.get("stats", []):
                    if stat.get("name") == name:
                        val = stat.get("displayValue")
                        if val:
                            return float(val.replace(",", ""))
            return None
        except Exception:
            return None

    def load_team_stats_for_league(self, league: str) -> tuple[int, int]:
        """Load team stats for a league."""
        print(f"\n[LOAD] {league.upper()} Team Statistics...")

        if league == "NFL":
            teams = self.get_nfl_teams()
            db_league = "NFL"
        else:
            teams = self.get_ncaaf_teams()
            db_league = "NCAAF"

        if not teams:
            print(f"  [WARNING] Could not retrieve {league.upper()} teams")
            return 0, 0

        print(f"  Found {len(teams)} {league.upper()} teams")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        total_inserted = 0
        total_skipped = 0
        failed_teams = []

        for team_id, team_name in teams.items():
            try:
                stats_data = self.api.get_team_statistics(team_id, league)
                stats = stats_data.get("stats", {})

                if not stats:
                    total_skipped += 1
                    continue

                # Extract offensive stats
                ppg = self.extract_stat(stats, "Offense", "Points per game")
                total_yards = self.extract_stat(
                    stats, "Offense", "Total Yards per game"
                )
                pass_yards = self.extract_stat(
                    stats, "Offense", "Passing Yards per game"
                )
                rush_yards = self.extract_stat(
                    stats, "Offense", "Rushing Yards per game"
                )
                comp_pct = self.extract_stat(stats, "Offense", "Completions per game")
                ypa = self.extract_stat(stats, "Offense", "Yards per Attempt")
                pass_td = self.extract_stat(stats, "Offense", "Passing Touchdowns")
                rush_td = self.extract_stat(stats, "Offense", "Rushing Touchdowns")
                int_thrown = self.extract_stat(stats, "Offense", "Interceptions")
                fumbles = self.extract_stat(stats, "Offense", "Fumbles")

                # Extract defensive stats
                papg = self.extract_stat(stats, "Defense", "Points allowed per game")
                yards_allowed = self.extract_stat(
                    stats, "Defense", "Yards Allowed per game"
                )
                pass_yards_allowed = self.extract_stat(
                    stats, "Defense", "Passing Yards Allowed per game"
                )
                rush_yards_allowed = self.extract_stat(
                    stats, "Defense", "Rushing Yards Allowed per game"
                )
                sacks = self.extract_stat(stats, "Defense", "Sacks")
                int_gained = self.extract_stat(stats, "Defense", "Interceptions")
                fr = self.extract_stat(stats, "Defense", "Fumble Recoveries")

                # Extract efficiency metrics
                to_margin = self.extract_stat(stats, "Efficiency", "Turnover Margin")
                third_down_pct = self.extract_stat(stats, "Efficiency", "Third Down %")
                fourth_down_pct = self.extract_stat(
                    stats, "Efficiency", "Fourth Down %"
                )
                rz_pct = self.extract_stat(stats, "Efficiency", "Red Zone %")

                # Get current week (would need season calendar for historical)
                week = 12  # TODO: Auto-detect current week
                season = 2025

                cursor.execute(
                    """
                    INSERT INTO espn_team_stats
                    (season, week, league, team,
                     points_per_game, total_yards_per_game,
                     passing_yards_per_game, rushing_yards_per_game,
                     passes_completed, passes_attempted,
                     completion_percentage, yards_per_attempt,
                     touchdowns_passing, touchdowns_rushing,
                     interceptions, fumbles,
                     points_allowed_per_game, yards_allowed_per_game,
                     passing_yards_allowed_per_game,
                     rushing_yards_allowed_per_game, sacks,
                     interceptions_gained, fumbles_recovered,
                     turnover_margin, third_down_percentage,
                     fourth_down_percentage, red_zone_percentage,
                     data_source, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                    (
                        season,
                        week,
                        db_league,
                        team_name,
                        ppg,
                        total_yards,
                        pass_yards,
                        rush_yards,
                        comp_pct,
                        None,
                        None,
                        ypa,
                        pass_td,
                        rush_td,
                        int_thrown,
                        fumbles,
                        papg,
                        yards_allowed,
                        pass_yards_allowed,
                        rush_yards_allowed,
                        sacks,
                        int_gained,
                        fr,
                        to_margin,
                        third_down_pct,
                        fourth_down_pct,
                        rz_pct,
                        "espn",
                    ),
                )

                total_inserted += cursor.rowcount

            except Exception as e:
                total_skipped += 1
                failed_teams.append((team_name, str(e)))

        conn.commit()
        cursor.close()

        print(
            f"  Inserted {total_inserted} team statistics, "
            f"skipped {total_skipped} errors"
        )
        if failed_teams and total_inserted == 0:
            print(f"  Failed teams (first 3):")
            for team, err in failed_teams[:3]:
                print(f"    {team}: {err}")
        return total_inserted, total_skipped

    def verify_data(self):
        """Verify data loaded successfully."""
        print("\n[VERIFY] ESPN Team Statistics in Database...")

        result = self.db.execute_query("""
            SELECT league, COUNT(*) as count
            FROM espn_team_stats
            GROUP BY league
            ORDER BY league
        """)

        total = 0
        for row in result:
            count = row["count"]
            total += count
            print(f"  {row['league']}: {count} teams")

        # Show top teams by PPG
        result = self.db.execute_query("""
            SELECT league, team, points_per_game
            FROM espn_team_stats
            WHERE points_per_game IS NOT NULL
            ORDER BY points_per_game DESC
            LIMIT 3
        """)

        if result:
            print(f"\n  Top 3 by Points Per Game:")
            for row in result:
                ppg = row.get("points_per_game", 0)
                print(f"    {row['league']}: {row['team']} ({ppg:.1f} PPG)")

        print(f"  Total: {total} teams loaded")
        return total

    def main(self):
        """Run full load."""
        print("=" * 70)
        print("LOAD ESPN TEAM STATISTICS")
        print("=" * 70)

        try:
            # Load NFL and NCAAF stats
            nfl_inserted, nfl_skipped = self.load_team_stats_for_league("NFL")
            ncaaf_inserted, ncaaf_skipped = self.load_team_stats_for_league("NCAAF")

            # Verify
            total = self.verify_data()

            print("\n" + "=" * 70)
            print("[OK] ESPN TEAM STATISTICS LOADED")
            print("=" * 70)
            print(f"\nSummary:")
            print(f"  NFL:   {nfl_inserted} inserted, {nfl_skipped} skipped")
            print(f"  NCAAF: {ncaaf_inserted} inserted, {ncaaf_skipped} skipped")
            print(f"  Total: {total} teams with statistics")
            print("\nNext steps:")
            print("  1. Load ESPN scoreboards")
            print("  2. Load ESPN standings")
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
    loader = ESPNTeamStatsLoader()
    success = loader.main()
    sys.exit(0 if success else 1)
