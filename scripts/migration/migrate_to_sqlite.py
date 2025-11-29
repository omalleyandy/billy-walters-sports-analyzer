"""
Migration utility to convert JSON edges and CLV data to SQLite.

Usage:
    uv run python scripts/migration/migrate_to_sqlite.py --league nfl --week 13
    uv run python scripts/migration/migrate_to_sqlite.py --league ncaaf --all-weeks
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from db import get_db_connection
from db.models import Edge, CLVPlay, EdgeSession, CLVSession
from db.operations import DatabaseOperations


LEAGUE_MAP = {"nfl": 1, "ncaaf": 2}


def get_league_id(league_name: str) -> int:
    """Get league ID from name."""
    league_id = LEAGUE_MAP.get(league_name.lower())
    if not league_id:
        raise ValueError(f"Unknown league: {league_name}")
    return league_id


def migrate_edges(
    ops: DatabaseOperations, league: str, week: Optional[int] = None
) -> None:
    """Migrate edge detection JSON files to SQLite."""
    league_id = get_league_id(league)
    edge_dir = Path("output/edge_detection")

    if not edge_dir.exists():
        print(f"[ERROR] Edge detection directory not found: {edge_dir}")
        return

    # Find edge detection files
    if week:
        pattern = f"*edges_week_{week}.json"
        files = list(edge_dir.glob(pattern))
    else:
        files = list(edge_dir.glob(f"{league.lower()}_edges.json"))

    for edge_file in files:
        print(f"\n[INFO] Processing edges: {edge_file.name}")

        with open(edge_file) as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        edges = data.get("edges", [])

        if not edges:
            print(f"[WARNING] No edges found in {edge_file.name}")
            continue

        # Insert session metadata
        session = EdgeSession(
            league_id=league_id,
            week=metadata.get("week", 0),
            edges_found=metadata.get("edges_found", len(edges)),
            min_edge=metadata.get("min_edge"),
            hfa=metadata.get("hfa"),
            generated_at=metadata.get("generated_at"),
        )
        ops.insert_edge_session(session)
        print(f"[OK] Edge session inserted: week {session.week}")

        # Insert edges
        inserted = 0
        for edge_data in edges:
            try:
                edge = Edge(
                    game_id=edge_data.get("game_id"),
                    league_id=league_id,
                    week=metadata.get("week", 0),
                    away_team=edge_data.get("away_team"),
                    home_team=edge_data.get("home_team"),
                    game_time=edge_data.get("game_time"),
                    predicted_line=float(edge_data.get("predicted_line", 0)),
                    market_line=float(edge_data.get("market_line", 0)),
                    edge=float(edge_data.get("edge", 0)),
                    edge_abs=float(edge_data.get("edge_abs", 0)),
                    classification=edge_data.get("classification"),
                    kelly_pct=float(edge_data.get("kelly_pct"))
                    if edge_data.get("kelly_pct")
                    else None,
                    win_rate=edge_data.get("win_rate"),
                    recommendation=edge_data.get("recommendation"),
                    rotation_team1=edge_data.get("rotation_numbers", {}).get("team1"),
                    rotation_team2=edge_data.get("rotation_numbers", {}).get("team2"),
                    total=float(edge_data.get("total"))
                    if edge_data.get("total")
                    else None,
                    generated_at=metadata.get("generated_at"),
                )
                ops.insert_edge(edge)
                inserted += 1
            except Exception as e:
                print(f"[WARNING] Failed to insert edge: {e}")
                continue

        print(f"[OK] Inserted {inserted} edges")


def migrate_clv(
    ops: DatabaseOperations, league: str, week: Optional[int] = None
) -> None:
    """Migrate CLV tracking JSON files to SQLite."""
    league_id = get_league_id(league)
    clv_dir = Path("output/clv_tracking")

    if not clv_dir.exists():
        print(f"[ERROR] CLV tracking directory not found: {clv_dir}")
        return

    # Find CLV tracking files
    if week:
        pattern = f"{league.lower()}_week_{week}_plays.json"
        files = list(clv_dir.glob(pattern))
    else:
        files = list(clv_dir.glob(f"{league.lower()}_week_*_plays.json"))

    for clv_file in files:
        print(f"\n[INFO] Processing CLV plays: {clv_file.name}")

        with open(clv_file) as f:
            data = json.load(f)

        metadata = {k: v for k, v in data.items() if k != "plays"}
        plays = data.get("plays", [])

        if not plays:
            print(f"[WARNING] No plays found in {clv_file.name}")
            continue

        # Insert session metadata
        session = CLVSession(
            league_id=league_id,
            week=metadata.get("week", 0),
            total_max_bet=metadata.get("total_max_bet"),
            total_units_recommended=metadata.get("total_units_recommended"),
            status=metadata.get("status"),
            generated_at=metadata.get("generated"),
        )
        ops.insert_clv_session(session)
        print(f"[OK] CLV session inserted: week {session.week}")

        # Insert plays
        inserted = 0
        for play_data in plays:
            try:
                play = CLVPlay(
                    game_id=play_data.get(
                        "game_id",
                        f"{play_data.get('away_team', '')}_{play_data.get('home_team', '')}",
                    ),
                    league_id=league_id,
                    week=metadata.get("week", 0),
                    rank=play_data.get("rank"),
                    matchup=play_data.get("matchup"),
                    game_time=play_data.get("game_time"),
                    pick=play_data.get("pick"),
                    pick_side=play_data.get("pick_side"),
                    spread=float(play_data.get("spread", 0)),
                    total=float(play_data.get("total"))
                    if play_data.get("total")
                    else None,
                    market_spread=float(play_data.get("market_spread"))
                    if play_data.get("market_spread")
                    else None,
                    edge=float(play_data.get("edge"))
                    if play_data.get("edge")
                    else None,
                    confidence=play_data.get("confidence"),
                    kelly=float(play_data.get("kelly"))
                    if play_data.get("kelly")
                    else None,
                    units_recommended=float(play_data.get("units_recommended"))
                    if play_data.get("units_recommended")
                    else None,
                    away_team=play_data.get("away_team"),
                    home_team=play_data.get("home_team"),
                    away_power=float(play_data.get("away_power"))
                    if play_data.get("away_power")
                    else None,
                    home_power=float(play_data.get("home_power"))
                    if play_data.get("home_power")
                    else None,
                    opening_odds=float(play_data.get("opening_odds"))
                    if play_data.get("opening_odds")
                    else None,
                    opening_line=float(play_data.get("opening_line"))
                    if play_data.get("opening_line")
                    else None,
                    closing_odds=float(play_data.get("closing_odds"))
                    if play_data.get("closing_odds")
                    else None,
                    closing_line=float(play_data.get("closing_line"))
                    if play_data.get("closing_line")
                    else None,
                    result=play_data.get("result"),
                    clv=float(play_data.get("clv")) if play_data.get("clv") else None,
                    notes=play_data.get("notes"),
                    status=play_data.get("status"),
                )
                ops.insert_clv_play(play)
                inserted += 1
            except Exception as e:
                print(f"[WARNING] Failed to insert CLV play: {e}")
                continue

        print(f"[OK] Inserted {inserted} CLV plays")


@click.command()
@click.option(
    "--league",
    type=click.Choice(["nfl", "ncaaf"], case_sensitive=False),
    required=True,
    help="League (NFL or NCAAF)",
)
@click.option(
    "--week",
    type=int,
    default=None,
    help="Specific week to migrate",
)
@click.option(
    "--all-weeks",
    is_flag=True,
    help="Migrate all weeks",
)
@click.option(
    "--data-type",
    type=click.Choice(["edges", "clv", "both"], case_sensitive=False),
    default="both",
    help="What data to migrate",
)
def main(league: str, week: Optional[int], all_weeks: bool, data_type: str):
    """Migrate JSON betting data to SQLite database."""
    print("\n" + "=" * 70)
    print("MIGRATION: JSON to SQLite")
    print("=" * 70)

    # Initialize database
    db = get_db_connection()
    db.create_pool()
    ops = DatabaseOperations(db)

    # Migrate edges
    if data_type.lower() in ("edges", "both"):
        migrate_edges(ops, league, week)

    # Migrate CLV
    if data_type.lower() in ("clv", "both"):
        migrate_clv(ops, league, week)

    print("\n" + "=" * 70)
    print("[OK] Migration complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
