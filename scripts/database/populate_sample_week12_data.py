#!/usr/bin/env python3
"""
Populate Billy Walters Analytics Database with Sample Week 12 Data

This script inserts realistic Week 12 NFL data including:
- Game schedule
- Power ratings (Massey composite)
- Opening and closing odds
- Sample betting edges and results
- Weather conditions
- Sample situational factors
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db import get_db_connection


def insert_week12_games(db):
    """Insert Week 12 NFL games (Nov 20-24, 2025)."""
    print("\n[1/5] Inserting Week 12 Games...")

    games = [
        {
            "game_id": "BUF_KC_2025_W12",
            "season": 2025,
            "week": 12,
            "league": "NFL",
            "game_date": "2025-11-23 13:00:00",
            "home_team": "Kansas City Chiefs",
            "away_team": "Buffalo Bills",
            "stadium": "Arrowhead Stadium",
            "is_outdoor": True,
        },
        {
            "game_id": "SF_GB_2025_W12",
            "season": 2025,
            "week": 12,
            "league": "NFL",
            "game_date": "2025-11-23 16:05:00",
            "home_team": "Green Bay Packers",
            "away_team": "San Francisco 49ers",
            "stadium": "Lambeau Field",
            "is_outdoor": True,
        },
        {
            "game_id": "DET_CHI_2025_W12",
            "season": 2025,
            "week": 12,
            "league": "NFL",
            "game_date": "2025-11-27 12:30:00",
            "home_team": "Detroit Lions",
            "away_team": "Chicago Bears",
            "stadium": "Ford Field",
            "is_outdoor": False,
        },
        {
            "game_id": "DAL_NYG_2025_W12",
            "season": 2025,
            "week": 12,
            "league": "NFL",
            "game_date": "2025-11-27 16:30:00",
            "home_team": "Dallas Cowboys",
            "away_team": "New York Giants",
            "stadium": "AT&T Stadium",
            "is_outdoor": True,
        },
        {
            "game_id": "MIA_TB_2025_W12",
            "season": 2025,
            "week": 12,
            "league": "NFL",
            "game_date": "2025-11-27 20:20:00",
            "home_team": "Tampa Bay Buccaneers",
            "away_team": "Miami Dolphins",
            "stadium": "Raymond James Stadium",
            "is_outdoor": True,
        },
        {
            "game_id": "NE_LAR_2025_W12",
            "season": 2025,
            "week": 12,
            "league": "NFL",
            "game_date": "2025-11-23 10:00:00",
            "home_team": "Los Angeles Rams",
            "away_team": "New England Patriots",
            "stadium": "SoFi Stadium",
            "is_outdoor": True,
        },
    ]

    for game in games:
        db.execute_query(
            """
            INSERT INTO games
            (game_id, season, week, league, game_date, home_team, away_team,
             stadium, is_outdoor, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (
                game["game_id"],
                game["season"],
                game["week"],
                game["league"],
                game["game_date"],
                game["home_team"],
                game["away_team"],
                game["stadium"],
                game["is_outdoor"],
                "SCHEDULED",
            ),
            fetch=False,
        )

    print(f"[OK] Inserted {len(games)} games")


def insert_power_ratings(db):
    """Insert composite power ratings for Week 12 teams."""
    print("\n[2/5] Inserting Power Ratings...")

    ratings = [
        # BUF vs KC
        ("Buffalo Bills", 2025, 12, "NFL", 92.5),
        ("Kansas City Chiefs", 2025, 12, "NFL", 88.0),
        # SF vs GB
        ("San Francisco 49ers", 2025, 12, "NFL", 89.0),
        ("Green Bay Packers", 2025, 12, "NFL", 85.5),
        # DET vs CHI
        ("Detroit Lions", 2025, 12, "NFL", 91.0),
        ("Chicago Bears", 2025, 12, "NFL", 80.0),
        # DAL vs NYG
        ("Dallas Cowboys", 2025, 12, "NFL", 87.0),
        ("New York Giants", 2025, 12, "NFL", 78.5),
        # MIA vs TB
        ("Miami Dolphins", 2025, 12, "NFL", 84.5),
        ("Tampa Bay Buccaneers", 2025, 12, "NFL", 82.0),
        # NE vs LAR
        ("New England Patriots", 2025, 12, "NFL", 76.0),
        ("Los Angeles Rams", 2025, 12, "NFL", 86.5),
    ]

    for team, season, week, league, rating in ratings:
        db.execute_query(
            """
            INSERT INTO power_ratings
            (season, week, league, team, rating, source, raw_rating,
             offense_rating, defense_rating, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (season, week, league, team, rating, "composite", rating, rating + 2, rating - 2),
            fetch=False,
        )

    print(f"[OK] Inserted {len(ratings)} power ratings")


def insert_odds(db):
    """Insert opening and closing odds for Week 12 games."""
    print("\n[3/5] Inserting Odds...")

    odds_data = [
        # BUF vs KC: Buffalo +3.0, KC -3.0
        ("BUF_KC_2025_W12", "overtime", "opening", -3.0, -110, 41.0, -110),
        ("BUF_KC_2025_W12", "overtime", "closing", -2.5, -110, 41.5, -110),
        # SF vs GB: SF -3.5, GB +3.5
        ("SF_GB_2025_W12", "overtime", "opening", 3.5, -110, 45.5, -110),
        ("SF_GB_2025_W12", "overtime", "closing", 3.0, -110, 46.0, -110),
        # DET vs CHI: DET -10.5, CHI +10.5
        ("DET_CHI_2025_W12", "overtime", "opening", -10.5, -110, 45.0, -110),
        ("DET_CHI_2025_W12", "overtime", "closing", -10.0, -110, 44.5, -110),
        # DAL vs NYG: DAL -8.5, NYG +8.5
        ("DAL_NYG_2025_W12", "overtime", "opening", -8.5, -110, 43.0, -110),
        ("DAL_NYG_2025_W12", "overtime", "closing", -8.0, -110, 43.5, -110),
        # MIA vs TB: TB -2.5, MIA +2.5
        ("MIA_TB_2025_W12", "overtime", "opening", -2.5, -110, 42.0, -110),
        ("MIA_TB_2025_W12", "overtime", "closing", -2.0, -110, 42.5, -110),
        # NE vs LAR: LAR -10.0, NE +10.0
        ("NE_LAR_2025_W12", "overtime", "opening", -10.0, -110, 44.0, -110),
        ("NE_LAR_2025_W12", "overtime", "closing", -10.5, -110, 43.5, -110),
    ]

    for game_id, sportsbook, odds_type, spread, juice, total, total_juice in odds_data:
        db.execute_query(
            """
            INSERT INTO odds
            (game_id, sportsbook, odds_type, home_spread, home_spread_juice,
             total, over_juice, under_juice, timestamp, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (game_id, sportsbook, odds_type, spread, juice, total, total_juice, total_juice),
            fetch=False,
        )

    print(f"[OK] Inserted {len(odds_data)} odds records")


def insert_sample_bets(db):
    """Insert sample bets with edge analysis."""
    print("\n[4/5] Inserting Sample Bets...")

    bets = [
        {
            "bet_id": "2025_W12_BUF_SPREAD",
            "game_id": "BUF_KC_2025_W12",
            "bet_type": "spread",
            "side": "Buffalo Bills",
            "line": 3.0,
            "predicted_line": 4.5,
            "market_line": 3.0,
            "edge_points": 1.5,
            "edge_category": "WEAK",
            "confidence": 65,
            "units": 2.0,
            "risk_amount": 220.0,
        },
        {
            "bet_id": "2025_W12_DET_SPREAD",
            "game_id": "DET_CHI_2025_W12",
            "bet_type": "spread",
            "side": "Detroit Lions",
            "line": -10.5,
            "predicted_line": -11.0,
            "market_line": -10.5,
            "edge_points": 0.5,
            "edge_category": "WEAK",
            "confidence": 58,
            "units": 1.0,
            "risk_amount": 110.0,
        },
        {
            "bet_id": "2025_W12_SF_SPREAD",
            "game_id": "SF_GB_2025_W12",
            "bet_type": "spread",
            "side": "San Francisco 49ers",
            "line": -3.5,
            "predicted_line": -3.5,
            "market_line": -3.5,
            "edge_points": 0.0,
            "edge_category": "WEAK",
            "confidence": 52,
            "units": 0.0,
            "risk_amount": 0.0,
        },
        {
            "bet_id": "2025_W12_DAL_SPREAD",
            "game_id": "DAL_NYG_2025_W12",
            "bet_type": "spread",
            "side": "Dallas Cowboys",
            "line": -8.5,
            "predicted_line": -8.5,
            "market_line": -8.5,
            "edge_points": 0.0,
            "edge_category": "WEAK",
            "confidence": 55,
            "units": 0.0,
            "risk_amount": 0.0,
        },
        {
            "bet_id": "2025_W12_TB_TOTAL",
            "game_id": "MIA_TB_2025_W12",
            "bet_type": "total",
            "side": "OVER",
            "line": 42.0,
            "predicted_line": 41.5,
            "market_line": 42.0,
            "edge_points": 0.5,
            "edge_category": "WEAK",
            "confidence": 54,
            "units": 0.5,
            "risk_amount": 55.0,
        },
    ]

    for bet in bets:
        if bet["units"] > 0:  # Only insert bets with units
            db.execute_query(
                """
                INSERT INTO bets
                (bet_id, game_id, bet_type, side, line, juice, sportsbook,
                 predicted_line, market_line, edge_points, edge_category,
                 confidence, units, risk_amount, result, placed_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
                """,
                (
                    bet["bet_id"],
                    bet["game_id"],
                    bet["bet_type"],
                    bet["side"],
                    bet["line"],
                    -110,
                    "overtime",
                    bet["predicted_line"],
                    bet["market_line"],
                    bet["edge_points"],
                    bet["edge_category"],
                    bet["confidence"],
                    bet["units"],
                    bet["risk_amount"],
                    "PENDING",
                ),
                fetch=False,
            )

    print(f"[OK] Inserted {len([b for b in bets if b['units'] > 0])} sample bets")


def insert_weather_data(db):
    """Insert sample weather conditions."""
    print("\n[5/5] Inserting Weather Data...")

    weather = [
        # BUF vs KC - Cold with wind
        ("BUF_KC_2025_W12", 34.0, 32.0, 12.5, 18.0, "W", 65, 10, "none", None, 10.0, 45, "GOOD", -1.0, -0.5),
        # SF vs GB - Cold Wisconsin
        ("SF_GB_2025_W12", 28.0, 24.0, 18.0, 25.0, "NW", 55, 5, "none", None, 8.0, 60, "MODERATE", -2.0, -1.0),
        # DET vs CHI - Mild indoor
        ("DET_CHI_2025_W12", None, None, None, None, None, None, None, None, None, None, None, "IDEAL", 0.0, 0.0),
        # DAL vs NYG - Clear
        ("DAL_NYG_2025_W12", 48.0, 46.0, 8.0, 12.0, "S", 50, 0, "none", None, 10.0, 30, "GOOD", 0.0, 0.0),
        # MIA vs TB - Warm
        ("MIA_TB_2025_W12", 72.0, 70.0, 6.0, 10.0, "E", 70, 5, "none", None, 10.0, 20, "IDEAL", 0.0, 0.0),
        # NE vs LAR - Mild
        ("NE_LAR_2025_W12", 60.0, 58.0, 4.0, 8.0, "W", 45, 0, "none", None, 10.0, 10, "IDEAL", 0.0, 0.0),
    ]

    for game_id, temp, feels_like, wind, gust, direction, humidity, precip_chance, precip_type, precip_amt, vis, cloud, category, total_adj, spread_adj in weather:
        if temp is not None:  # Only insert if outdoor
            db.execute_query(
                """
                INSERT INTO weather
                (game_id, temperature, feels_like, wind_speed, wind_gust, wind_direction,
                 humidity, precipitation_chance, precipitation_type, visibility, cloud_cover,
                 weather_category, total_adjustment, spread_adjustment, weather_severity_score,
                 source, forecast_type, is_actual, timestamp, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (
                    game_id, temp, feels_like, wind, gust, direction,
                    humidity, precip_chance, precip_type, vis, cloud,
                    category, total_adj, spread_adj, 20,
                    "accuweather", "forecast", False,
                ),
                fetch=False,
            )

    print(f"[OK] Inserted {len([w for w in weather if w[1] is not None])} weather records")


def main():
    """Main function to populate database."""
    print("=" * 60)
    print("BILLY WALTERS ANALYTICS - POPULATE WEEK 12 DATA")
    print("=" * 60)

    try:
        db = get_db_connection()
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        return False

    try:
        insert_week12_games(db)
        insert_power_ratings(db)
        insert_odds(db)
        insert_sample_bets(db)
        insert_weather_data(db)

        print("\n" + "=" * 60)
        print("[OK] WEEK 12 DATA POPULATED SUCCESSFULLY!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run sample queries to see the data")
        print("2. View betting card with edges")
        print("3. Simulate game results and CLV tracking")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to populate data: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close_all_connections()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
