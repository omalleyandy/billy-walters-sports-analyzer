"""
Database Operations

CRUD operations for edges and CLV tracking using SQLite.
"""

from typing import Dict, List, Optional

from .connection import DatabaseConnection
from .models import Edge, CLVPlay, EdgeSession, CLVSession


class DatabaseOperations:
    """High-level database operations."""

    def __init__(self, db: DatabaseConnection):
        """Initialize with database connection."""
        self.db = db

    # ============================================================
    # EDGES
    # ============================================================

    def insert_edge(self, edge: Edge) -> None:
        """Insert detected edge into database."""
        query = """
            INSERT INTO edges (
                game_id, league_id, week, away_team, home_team, game_time,
                predicted_line, market_line, edge, edge_abs,
                classification, kelly_pct, win_rate, recommendation,
                rotation_team1, rotation_team2, total, generated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute_query(
            query,
            (
                edge.game_id,
                edge.league_id,
                edge.week,
                edge.away_team,
                edge.home_team,
                edge.game_time,
                edge.predicted_line,
                edge.market_line,
                edge.edge,
                edge.edge_abs,
                edge.classification,
                edge.kelly_pct,
                edge.win_rate,
                edge.recommendation,
                edge.rotation_team1,
                edge.rotation_team2,
                edge.total,
                edge.generated_at,
            ),
            fetch=False,
        )

    def get_edges_by_week(self, league_id: int, week: int) -> List[Dict]:
        """Get all edges for a specific week."""
        query = """
            SELECT * FROM edges
            WHERE league_id = ? AND week = ?
            ORDER BY edge_abs DESC
        """
        results = self.db.execute_query(query, (league_id, week))
        return [dict(row) for row in results] if results else []

    def get_edges_by_classification(
        self, league_id: int, week: int, classification: str
    ) -> List[Dict]:
        """Get edges by classification level."""
        query = """
            SELECT * FROM edges
            WHERE league_id = ? AND week = ? AND classification = ?
            ORDER BY edge_abs DESC
        """
        results = self.db.execute_query(query, (league_id, week, classification))
        return [dict(row) for row in results] if results else []

    def get_edge_by_game(self, game_id: str, league_id: int) -> Optional[Dict]:
        """Get edge for specific game."""
        query = """
            SELECT * FROM edges
            WHERE game_id = ? AND league_id = ?
        """
        results = self.db.execute_query(query, (game_id, league_id))
        return dict(results[0]) if results else None

    def delete_edges_for_week(self, league_id: int, week: int) -> None:
        """Delete all edges for a week (for re-detection)."""
        query = "DELETE FROM edges WHERE league_id = ? AND week = ?"
        self.db.execute_query(query, (league_id, week), fetch=False)

    # ============================================================
    # CLV PLAYS
    # ============================================================

    def insert_clv_play(self, play: CLVPlay) -> None:
        """Insert CLV tracking play into database."""
        query = """
            INSERT INTO clv_plays (
                game_id, league_id, week, rank, matchup, game_time,
                pick, pick_side, spread, total, market_spread, edge,
                confidence, kelly, units_recommended, away_team, home_team,
                away_power, home_power, opening_odds, opening_line,
                opening_datetime, closing_odds, closing_line, closing_datetime,
                result, clv, notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute_query(
            query,
            (
                play.game_id,
                play.league_id,
                play.week,
                play.rank,
                play.matchup,
                play.game_time,
                play.pick,
                play.pick_side,
                play.spread,
                play.total,
                play.market_spread,
                play.edge,
                play.confidence,
                play.kelly,
                play.units_recommended,
                play.away_team,
                play.home_team,
                play.away_power,
                play.home_power,
                play.opening_odds,
                play.opening_line,
                play.opening_datetime,
                play.closing_odds,
                play.closing_line,
                play.closing_datetime,
                play.result,
                play.clv,
                play.notes,
                play.status,
            ),
            fetch=False,
        )

    def get_clv_plays_by_week(self, league_id: int, week: int) -> List[Dict]:
        """Get all CLV plays for a specific week."""
        query = """
            SELECT * FROM clv_plays
            WHERE league_id = ? AND week = ?
            ORDER BY rank
        """
        results = self.db.execute_query(query, (league_id, week))
        return [dict(row) for row in results] if results else []

    def update_clv_play_result(
        self,
        game_id: str,
        league_id: int,
        result: str,
        clv: Optional[float] = None,
    ) -> None:
        """Update CLV play with result and CLV."""
        query = """
            UPDATE clv_plays
            SET result = ?, clv = ?, status = 'COMPLETED'
            WHERE game_id = ? AND league_id = ?
        """
        self.db.execute_query(
            query,
            (result, clv, game_id, league_id),
            fetch=False,
        )

    def update_clv_play_closing_odds(
        self,
        game_id: str,
        league_id: int,
        closing_odds: float,
        closing_line: float,
    ) -> None:
        """Update CLV play with closing odds."""
        query = """
            UPDATE clv_plays
            SET closing_odds = ?, closing_line = ?, closing_datetime = datetime('now')
            WHERE game_id = ? AND league_id = ?
        """
        self.db.execute_query(
            query,
            (closing_odds, closing_line, game_id, league_id),
            fetch=False,
        )

    def get_clv_plays_by_status(self, league_id: int, status: str) -> List[Dict]:
        """Get CLV plays by status (e.g., READY TO PLAY, COMPLETED)."""
        query = """
            SELECT * FROM clv_plays
            WHERE league_id = ? AND status = ?
            ORDER BY week DESC, rank
        """
        results = self.db.execute_query(query, (league_id, status))
        return [dict(row) for row in results] if results else []

    def delete_clv_plays_for_week(self, league_id: int, week: int) -> None:
        """Delete all CLV plays for a week."""
        query = "DELETE FROM clv_plays WHERE league_id = ? AND week = ?"
        self.db.execute_query(query, (league_id, week), fetch=False)

    # ============================================================
    # EDGE SESSIONS
    # ============================================================

    def insert_edge_session(self, session: EdgeSession) -> None:
        """Insert edge detection session metadata."""
        query = """
            INSERT INTO edge_sessions (
                league_id, week, edges_found, min_edge, hfa, generated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                session.league_id,
                session.week,
                session.edges_found,
                session.min_edge,
                session.hfa,
                session.generated_at,
            ),
            fetch=False,
        )

    def get_edge_session(self, league_id: int, week: int) -> Optional[Dict]:
        """Get edge session metadata."""
        query = """
            SELECT * FROM edge_sessions
            WHERE league_id = ? AND week = ?
        """
        results = self.db.execute_query(query, (league_id, week))
        return dict(results[0]) if results else None

    # ============================================================
    # CLV SESSIONS
    # ============================================================

    def insert_clv_session(self, session: CLVSession) -> None:
        """Insert CLV tracking session metadata."""
        query = """
            INSERT INTO clv_sessions (
                league_id, week, total_max_bet, total_units_recommended,
                status, generated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                session.league_id,
                session.week,
                session.total_max_bet,
                session.total_units_recommended,
                session.status,
                session.generated_at,
            ),
            fetch=False,
        )

    def get_clv_session(self, league_id: int, week: int) -> Optional[Dict]:
        """Get CLV tracking session metadata."""
        query = """
            SELECT * FROM clv_sessions
            WHERE league_id = ? AND week = ?
        """
        results = self.db.execute_query(query, (league_id, week))
        return dict(results[0]) if results else None

    # ============================================================
    # UTILITIES
    # ============================================================

    def get_league_id(self, league_name: str) -> Optional[int]:
        """Get league ID by name."""
        query = "SELECT id FROM leagues WHERE name = ?"
        results = self.db.execute_query(query, (league_name,))
        return results[0]["id"] if results else None

    def get_or_create_team(self, league_id: int, team_name: str) -> int:
        """Get team ID or create if missing."""
        query = "SELECT id FROM teams WHERE league_id = ? AND name = ?"
        results = self.db.execute_query(query, (league_id, team_name))

        if results:
            return results[0]["id"]

        # Create team if missing
        insert_query = "INSERT INTO teams (league_id, name) VALUES (?, ?)"
        self.db.execute_query(insert_query, (league_id, team_name), fetch=False)

        # Get the ID of newly created team
        results = self.db.execute_query(query, (league_id, team_name))
        return results[0]["id"] if results else None

    def get_clv_summary(self, league_id: int, limit: int = 10) -> List[Dict]:
        """Get CLV summary for recent plays."""
        query = """
            SELECT
                week,
                COUNT(*) as plays,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
                ROUND(AVG(clv), 2) as avg_clv,
                ROUND(SUM(clv), 2) as total_clv
            FROM clv_plays
            WHERE league_id = ? AND result IS NOT NULL
            GROUP BY week
            ORDER BY week DESC
            LIMIT ?
        """
        results = self.db.execute_query(query, (league_id, limit))
        return [dict(row) for row in results] if results else []
