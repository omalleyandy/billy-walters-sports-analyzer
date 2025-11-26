#!/usr/bin/env python3
"""
Generate Custom Billy Walters Power Ratings from ESPN Component Data

Reads from ESPN category tables and generates proprietary power ratings
without relying on Massey composite. Uses Massey only as fallback/validation.

Process:
1. Load ESPN team statistics (offensive/defensive metrics)
2. Load ESPN injury data (injury impact calculation)
3. Load ESPN standings (recent performance/momentum)
4. Calculate custom power ratings for each team
5. Compare with Massey ratings for validation
6. Store in power_ratings table with source='custom_espn'
"""

import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.db import get_db_connection
from src.walters_analyzer.valuation.custom_power_rating_engine import (
    CustomPowerRatingEngine,
    League,
    OffensiveMetrics,
    DefensiveMetrics,
    InjuryImpact,
    TeamStatus,
)


class CustomPowerRatingGenerator:
    """Generate custom power ratings from ESPN component data."""

    def __init__(self):
        self.db = get_db_connection()
        self.nfl_engine = CustomPowerRatingEngine(league=League.NFL)
        self.ncaaf_engine = CustomPowerRatingEngine(league=League.NCAAF)

    def load_team_stats(self, league: str) -> dict:
        """Load team statistics from espn_team_stats table."""
        print(f"\n[LOAD] ESPN Team Statistics ({league.upper()})...")

        result = self.db.execute_query(
            f"""
            SELECT team, week, season,
                   points_per_game, total_yards_per_game,
                   passing_yards_per_game, rushing_yards_per_game,
                   completion_percentage, yards_per_attempt,
                   touchdowns_passing, touchdowns_rushing,
                   interceptions, fumbles,
                   points_allowed_per_game, yards_allowed_per_game,
                   passing_yards_allowed_per_game,
                   rushing_yards_allowed_per_game, sacks,
                   interceptions_gained, fumbles_recovered,
                   turnover_margin, third_down_percentage,
                   fourth_down_percentage, red_zone_percentage
            FROM espn_team_stats
            WHERE league = %s
            ORDER BY week DESC, team
        """,
            (league.upper(),),
        )

        stats_by_team = {}
        for row in result:
            team = row["team"]
            # Use most recent week data
            if team not in stats_by_team:
                stats_by_team[team] = row

        print(f"  Loaded stats for {len(stats_by_team)} {league.upper()} teams")
        return stats_by_team

    def load_injury_data(self, league: str) -> dict:
        """Load injury data from espn_injuries table."""
        print(f"\n[LOAD] ESPN Injury Data ({league.upper()})...")

        result = self.db.execute_query(
            f"""
            SELECT team, week, season,
                   player_name, position, status, severity,
                   impact_estimate
            FROM espn_injuries
            WHERE league = %s AND status NOT IN ('ACTIVE', 'LIKELY')
            ORDER BY week DESC, team, impact_estimate DESC
        """,
            (league.upper(),),
        )

        injuries_by_team = {}
        for row in result:
            team = row["team"]
            if team not in injuries_by_team:
                injuries_by_team[team] = []
            injuries_by_team[team].append(row)

        print(
            f"  Loaded injury data for {len(injuries_by_team)} {league.upper()} teams"
        )
        return injuries_by_team

    def load_team_standings(self, league: str) -> dict:
        """Load team standings from espn_standings table."""
        print(f"\n[LOAD] ESPN Standings ({league.upper()})...")

        result = self.db.execute_query(
            f"""
            SELECT team, week, season,
                   wins, losses, ties,
                   home_wins, home_losses,
                   away_wins, away_losses,
                   streak_type, streak_count
            FROM espn_standings
            WHERE league = %s
            ORDER BY week DESC, team
        """,
            (league.upper(),),
        )

        standings_by_team = {}
        for row in result:
            team = row["team"]
            # Use most recent week data
            if team not in standings_by_team:
                standings_by_team[team] = row

        print(f"  Loaded standings for {len(standings_by_team)} {league.upper()} teams")
        return standings_by_team

    def load_massey_ratings(self, league: str) -> dict:
        """Load Massey ratings for comparison."""
        print(f"\n[LOAD] Massey Ratings ({league.upper()}) for Comparison...")

        result = self.db.execute_query(
            f"""
            SELECT team, week, season, rating
            FROM massey_ratings
            WHERE league = %s
            ORDER BY week DESC, team
        """,
            (league.upper(),),
        )

        massey_by_team = {}
        for row in result:
            team = row["team"]
            # Use most recent week data
            if team not in massey_by_team:
                massey_by_team[team] = row["rating"]

        print(
            f"  Loaded Massey ratings for {len(massey_by_team)} {league.upper()} teams"
        )
        return massey_by_team

    def calculate_injury_impact(
        self, team: str, injuries: list, league: str
    ) -> InjuryImpact:
        """Calculate injury impact for a team."""
        if league == "NFL":
            injury_impacts = CustomPowerRatingEngine.NFL_INJURY_IMPACTS
        else:
            injury_impacts = CustomPowerRatingEngine.NCAAF_INJURY_IMPACTS

        impact = InjuryImpact()

        for injury in injuries:
            position = injury.get("position", "UNKNOWN")
            severity = injury.get("severity", "BACKUP")
            impact_estimate = injury.get("impact_estimate", 0.0)

            # Count by tier
            if severity == "ELITE":
                impact.elite_players_out += 1
            elif severity == "STARTER":
                impact.starter_players_out += 1
            else:
                impact.backup_players_out += 1

            # Add position-specific impact
            if position in injury_impacts:
                tier_impacts = injury_impacts[position]
                impact.total_impact_points += tier_impacts.get(severity, 0.0)
            else:
                impact.total_impact_points += impact_estimate or 0.0

        # Determine overall injury level
        if impact.elite_players_out >= 2 or impact.total_impact_points >= 8:
            impact.injury_level = "SEVERE"
        elif impact.elite_players_out >= 1 or impact.total_impact_points >= 4:
            impact.injury_level = "MODERATE"
        elif impact.starter_players_out >= 2 or impact.total_impact_points >= 2:
            impact.injury_level = "MINOR"
        else:
            impact.injury_level = "HEALTHY"

        return impact

    def generate_ratings_for_league(self, league: str) -> tuple[int, int]:
        """Generate power ratings for a league."""
        print(f"\n[GENERATE] Custom Power Ratings ({league.upper()})...")

        # Load all component data
        team_stats = self.load_team_stats(league)
        injury_data = self.load_injury_data(league)
        standings = self.load_team_standings(league)
        massey_ratings = self.load_massey_ratings(league)

        # Select engine
        engine = self.nfl_engine if league == "NFL" else self.ncaaf_engine

        # Get reference week and season
        ref_week = 1
        ref_season = 2025
        if team_stats:
            sample = next(iter(team_stats.values()))
            ref_week = sample.get("week", 1)
            ref_season = sample.get("season", 2025)

        print(f"  Generating ratings for Week {ref_week}, Season {ref_season}")

        inserted = 0
        skipped = 0

        conn = self.db.get_connection()
        cursor = conn.cursor()

        for team, stats in team_stats.items():
            try:
                # Build offensive metrics
                offensive = OffensiveMetrics(
                    points_per_game=stats.get("points_per_game"),
                    total_yards_per_game=stats.get("total_yards_per_game"),
                    passing_yards_per_game=stats.get("passing_yards_per_game"),
                    rushing_yards_per_game=stats.get("rushing_yards_per_game"),
                    completion_percentage=stats.get("completion_percentage"),
                    yards_per_attempt=stats.get("yards_per_attempt"),
                    touchdowns_passing=stats.get("touchdowns_passing"),
                    touchdowns_rushing=stats.get("touchdowns_rushing"),
                    interceptions=stats.get("interceptions"),
                    fumbles=stats.get("fumbles"),
                )

                # Build defensive metrics
                defensive = DefensiveMetrics(
                    points_allowed_per_game=stats.get("points_allowed_per_game"),
                    yards_allowed_per_game=stats.get("yards_allowed_per_game"),
                    passing_yards_allowed_per_game=stats.get(
                        "passing_yards_allowed_per_game"
                    ),
                    rushing_yards_allowed_per_game=stats.get(
                        "rushing_yards_allowed_per_game"
                    ),
                    sacks=stats.get("sacks"),
                    interceptions_gained=stats.get("interceptions_gained"),
                    fumbles_recovered=stats.get("fumbles_recovered"),
                    turnover_margin=stats.get("turnover_margin"),
                    third_down_percentage=stats.get("third_down_percentage"),
                    fourth_down_percentage=stats.get("fourth_down_percentage"),
                    red_zone_percentage=stats.get("red_zone_percentage"),
                )

                # Build injury impact
                team_injuries = injury_data.get(team, [])
                injury = self.calculate_injury_impact(team, team_injuries, league)

                # Build team status
                team_standing = standings.get(team, {})
                status = TeamStatus(
                    wins=team_standing.get("wins", 0),
                    losses=team_standing.get("losses", 0),
                    streak_type=team_standing.get("streak_type", ""),
                    streak_count=team_standing.get("streak_count", 0),
                    home_wins=team_standing.get("home_wins", 0),
                    home_losses=team_standing.get("home_losses", 0),
                    away_wins=team_standing.get("away_wins", 0),
                    away_losses=team_standing.get("away_losses", 0),
                )

                # Calculate rating
                massey_rating = massey_ratings.get(team)
                power_rating = engine.calculate_overall_rating(
                    team_name=team,
                    offensive=offensive,
                    defensive=defensive,
                    injury=injury,
                    status=status,
                    week=ref_week,
                    season=ref_season,
                    massey_rating=massey_rating,
                )

                # Store in database
                cursor.execute(
                    """
                    INSERT INTO power_ratings
                    (season, week, league, team, rating, source,
                     raw_rating, confidence, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (season, week, league, team, source)
                    DO UPDATE SET
                        rating = EXCLUDED.rating,
                        raw_rating = EXCLUDED.raw_rating,
                        updated_at = NOW()
                """,
                    (
                        power_rating.season,
                        power_rating.week,
                        power_rating.league.value,
                        power_rating.team,
                        power_rating.overall_rating,
                        power_rating.data_source,
                        power_rating.overall_rating,
                        power_rating.confidence_score,
                    ),
                )

                inserted += 1

            except Exception as e:
                print(f"  [ERROR] {team}: {str(e)}")
                skipped += 1

        conn.commit()
        cursor.close()

        print(f"  Inserted {inserted} custom ratings, skipped {skipped} teams")
        return inserted, skipped

    def verify_ratings(self):
        """Verify ratings generated and show summary."""
        print("\n[VERIFY] Custom Power Ratings...")

        result = self.db.execute_query("""
            SELECT league, source, COUNT(*) as count,
                   AVG(rating) as avg_rating,
                   MIN(rating) as min_rating,
                   MAX(rating) as max_rating
            FROM power_ratings
            WHERE source = 'custom_espn'
            GROUP BY league, source
            ORDER BY league
        """)

        for row in result:
            print(
                f"  {row['league']} (Custom): {row['count']} teams, "
                f"Avg={row['avg_rating']:.2f}, "
                f"Range={row['min_rating']:.2f}-{row['max_rating']:.2f}"
            )

        # Show top 3 teams
        result = self.db.execute_query("""
            SELECT league, team, rating
            FROM power_ratings
            WHERE source = 'custom_espn'
            ORDER BY league, rating DESC
            LIMIT 6
        """)

        if result:
            print("\n  Top Teams (Custom Ratings):")
            current_league = None
            for row in result:
                if row["league"] != current_league:
                    current_league = row["league"]
                    print(f"    {current_league}:")
                print(f"      {row['team']}: {row['rating']:.2f}")

    def main(self):
        """Run full custom rating generation."""
        print("=" * 70)
        print("GENERATE CUSTOM BILLY WALTERS POWER RATINGS")
        print("=" * 70)

        try:
            # Generate NFL ratings
            nfl_inserted, nfl_skipped = self.generate_ratings_for_league("NFL")

            # Generate NCAAF ratings
            ncaaf_inserted, ncaaf_skipped = self.generate_ratings_for_league("NCAAF")

            # Verify
            self.verify_ratings()

            print("\n" + "=" * 70)
            print("[OK] CUSTOM POWER RATINGS GENERATED")
            print("=" * 70)
            print(f"\nSummary:")
            print(f"  NFL:   {nfl_inserted} ratings, {nfl_skipped} skipped")
            print(f"  NCAAF: {ncaaf_inserted} ratings, {ncaaf_skipped} skipped")
            print(f"\nYour custom ratings are now in the database!")
            print("Next steps:")
            print("  1. Compare custom vs Massey ratings for accuracy")
            print("  2. Use custom ratings for edge detection")
            print("  3. Validate CLV performance weekly")

            return True

        except Exception as e:
            print(f"\n[ERROR] Generation failed: {str(e)}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            self.db.close_all_connections()


if __name__ == "__main__":
    generator = CustomPowerRatingGenerator()
    success = generator.main()
    sys.exit(0 if success else 1)
