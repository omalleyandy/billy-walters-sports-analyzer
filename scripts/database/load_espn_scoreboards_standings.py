#!/usr/bin/env python3
"""
Load ESPN scoreboards and standings into database.

Fetches game scores and team standings from ESPN API
and populates espn_scoreboards and espn_standings tables.

Scoreboards = game results and in-progress game status
Standings = team records, win percentages, conference standing
"""

import sys
import os
from datetime import datetime

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.db import get_db_connection
from src.data.espn_api_client import ESPNAPIClient


class ESPNScoreboardsStandingsLoader:
    """Load ESPN scoreboards and standings into database."""

    def __init__(self):
        self.db = get_db_connection()
        self.api = ESPNAPIClient()

    def load_scoreboards_for_league(self, league: str) -> tuple[int, int]:
        """Load scoreboards (game results) for a league."""
        print(f"\n[LOAD] {league.upper()} Scoreboards...")

        try:
            if league == "NFL":
                scoreboard_data = self.api.get_nfl_scoreboard()
                db_league = "NFL"
            else:
                scoreboard_data = self.api.get_ncaaf_scoreboard()
                db_league = "NCAAF"

            events = scoreboard_data.get("events", [])
            if not events:
                print(f"  [WARNING] No games found in scoreboard")
                return 0, 0

            print(f"  Found {len(events)} games")

            conn = self.db.get_connection()
            cursor = conn.cursor()

            inserted = 0
            skipped = 0

            for event in events:
                try:
                    # Extract game info
                    game_id = event.get("id")
                    date_str = event.get("date")
                    week_info = event.get("week", {})
                    week = (
                        week_info.get("number")
                        if isinstance(week_info, dict)
                        else int(week_info)
                        if isinstance(week_info, (int, str))
                        else 1
                    )
                    season_data = event.get("season")
                    season = (
                        season_data.get("year")
                        if isinstance(season_data, dict)
                        else int(season_data)
                        if season_data
                        else 2025
                    )

                    # Parse game time
                    game_time = None
                    if date_str:
                        try:
                            game_time = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        except Exception:
                            pass

                    # Get teams and scores
                    competitors = event.get("competitions", [])
                    if not competitors:
                        skipped += 1
                        continue

                    competition = competitors[0]
                    teams = competition.get("competitors", [])
                    if len(teams) < 2:
                        skipped += 1
                        continue

                    home_team = away_team = None
                    home_score = away_score = None
                    for team in teams:
                        team_name = team.get("team", {}).get("displayName")
                        score = team.get("score")
                        if team.get("homeAway") == "home":
                            home_team = team_name
                            home_score = int(score) if score else None
                        elif team.get("homeAway") == "away":
                            away_team = team_name
                            away_score = int(score) if score else None

                    if not home_team or not away_team:
                        skipped += 1
                        continue

                    # Calculate totals and margin
                    total_points = None
                    final_margin = None
                    if home_score is not None and away_score is not None:
                        total_points = home_score + away_score
                        final_margin = home_score - away_score

                    # Get game status
                    status_info = event.get("status", {})
                    status = status_info.get("type", {}).get("name")
                    quarter = status_info.get("period")
                    time_remaining = status_info.get("displayClock")

                    cursor.execute(
                        """
                        INSERT INTO espn_scoreboards
                        (game_id, season, week, league, home_team, away_team,
                         home_score, away_score, total_points, final_margin,
                         status, quarter, time_remaining, game_time,
                         data_source, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, NOW())
                    """,
                        (
                            game_id,
                            season,
                            week,
                            db_league,
                            home_team,
                            away_team,
                            home_score,
                            away_score,
                            total_points,
                            final_margin,
                            status,
                            quarter,
                            time_remaining,
                            game_time,
                            "espn",
                        ),
                    )

                    inserted += cursor.rowcount

                except Exception as e:
                    skipped += 1

            conn.commit()
            cursor.close()

            print(f"  Inserted {inserted} scoreboards, skipped {skipped} errors")
            return inserted, skipped

        except Exception as e:
            print(f"  [ERROR] Failed to load scoreboards: {str(e)}")
            return 0, 0

    def load_standings_for_league(self, league: str) -> tuple[int, int]:
        """Load standings for a league."""
        print(f"\n[LOAD] {league.upper()} Standings...")

        try:
            if league == "NFL":
                standings_data = self.api.get_nfl_standings()
                db_league = "NFL"
            else:
                standings_data = self.api.get_ncaaf_standings()
                db_league = "NCAAF"

            # Extract standings groups (divisions/conferences)
            groups = standings_data.get("groups", [])
            if not groups:
                print(f"  [WARNING] No standings groups found")
                return 0, 0

            conn = self.db.get_connection()
            cursor = conn.cursor()

            inserted = 0
            skipped = 0
            week = 12  # TODO: Auto-detect current week
            season = 2025

            for group in groups:
                # Extract division/conference info
                group_name = group.get("name")  # e.g., "AFC West"
                teams = group.get("standings", [])

                for team_entry in teams:
                    try:
                        team_info = team_entry.get("team", {})
                        team_name = team_info.get("displayName")
                        conf = team_entry.get("conferenceAssignedId")
                        div = team_entry.get("divisionAssignedId")

                        # Extract records
                        stats_data = team_entry.get("stats", [])
                        wins = losses = ties = win_pct = None
                        home_w = home_l = away_w = away_l = None
                        streak_type = streak_count = None

                        for stat in stats_data:
                            stat_type = stat.get("name")
                            if stat_type == "Wins":
                                wins = int(stat.get("displayValue", 0))
                            elif stat_type == "Losses":
                                losses = int(stat.get("displayValue", 0))
                            elif stat_type == "Ties":
                                ties = int(stat.get("displayValue", 0))
                            elif stat_type == "Winning Percentage":
                                try:
                                    win_pct = float(stat.get("displayValue", 0))
                                except (ValueError, TypeError):
                                    win_pct = None
                            elif stat_type == "Home Wins":
                                home_w = int(stat.get("displayValue", 0))
                            elif stat_type == "Home Losses":
                                home_l = int(stat.get("displayValue", 0))
                            elif stat_type == "Away Wins":
                                away_w = int(stat.get("displayValue", 0))
                            elif stat_type == "Away Losses":
                                away_l = int(stat.get("displayValue", 0))
                            elif stat_type == "Streak":
                                streak_str = stat.get("displayValue", "")
                                if streak_str:
                                    if streak_str.startswith("W"):
                                        streak_type = "W"
                                        try:
                                            streak_count = int(streak_str[1:])
                                        except ValueError:
                                            pass
                                    elif streak_str.startswith("L"):
                                        streak_type = "L"
                                        try:
                                            streak_count = int(streak_str[1:])
                                        except ValueError:
                                            pass

                        if not team_name or wins is None:
                            skipped += 1
                            continue

                        cursor.execute(
                            """
                            INSERT INTO espn_standings
                            (season, week, league, team, conference, division,
                             wins, losses, ties, win_percentage,
                             home_wins, home_losses, away_wins, away_losses,
                             streak_type, streak_count, data_source, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    %s, %s, %s, %s, %s, %s, %s, NOW())
                        """,
                            (
                                season,
                                week,
                                db_league,
                                team_name,
                                group_name,
                                div,
                                wins,
                                losses,
                                ties,
                                win_pct,
                                home_w,
                                home_l,
                                away_w,
                                away_l,
                                streak_type,
                                streak_count,
                                "espn",
                            ),
                        )

                        inserted += cursor.rowcount

                    except Exception as e:
                        skipped += 1

            conn.commit()
            cursor.close()

            print(f"  Inserted {inserted} standings, skipped {skipped} errors")
            return inserted, skipped

        except Exception as e:
            print(f"  [ERROR] Failed to load standings: {str(e)}")
            return 0, 0

    def verify_data(self):
        """Verify data loaded successfully."""
        print("\n[VERIFY] ESPN Scoreboards and Standings...")

        # Scoreboards
        result = self.db.execute_query("""
            SELECT league, COUNT(*) as count
            FROM espn_scoreboards
            GROUP BY league
        """)

        print("\nScoreboards by league:")
        sb_total = 0
        for row in result:
            count = row["count"]
            sb_total += count
            print(f"  {row['league']}: {count} games")

        # Standings
        result = self.db.execute_query("""
            SELECT league, COUNT(*) as count
            FROM espn_standings
            GROUP BY league
        """)

        print("\nStandings by league:")
        st_total = 0
        for row in result:
            count = row["count"]
            st_total += count
            print(f"  {row['league']}: {count} teams")

        print(
            f"\nTotal: {sb_total} scoreboards + {st_total} standings = "
            f"{sb_total + st_total} records"
        )
        return sb_total + st_total

    def main(self):
        """Run full load."""
        print("=" * 70)
        print("LOAD ESPN SCOREBOARDS & STANDINGS")
        print("=" * 70)

        try:
            # Load scoreboards
            nfl_sb, nfl_sb_skip = self.load_scoreboards_for_league("NFL")
            ncaaf_sb, ncaaf_sb_skip = self.load_scoreboards_for_league("NCAAF")

            # Load standings
            nfl_st, nfl_st_skip = self.load_standings_for_league("NFL")
            ncaaf_st, ncaaf_st_skip = self.load_standings_for_league("NCAAF")

            # Verify
            total = self.verify_data()

            print("\n" + "=" * 70)
            print("[OK] ESPN SCOREBOARDS & STANDINGS LOADED")
            print("=" * 70)
            print(f"\nSummary:")
            print(
                f"  Scoreboards: {nfl_sb + ncaaf_sb} loaded, "
                f"{nfl_sb_skip + ncaaf_sb_skip} skipped"
            )
            print(
                f"  Standings:   {nfl_st + ncaaf_st} loaded, "
                f"{nfl_st_skip + ncaaf_st_skip} skipped"
            )
            print(f"  Total:       {total} records")
            print("\nNext steps:")
            print("  1. Build custom Billy Walters power rating engine")
            print("  2. Generate custom ratings for all teams")
            print("  3. Validate vs Massey ratings")

            return True

        except Exception as e:
            print(f"\n[ERROR] Load failed: {str(e)}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            self.db.close_all_connections()


if __name__ == "__main__":
    loader = ESPNScoreboardsStandingsLoader()
    success = loader.main()
    sys.exit(0 if success else 1)
