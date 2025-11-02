"""
Historical game database for backtesting and validation.

This module manages the SQLite database that stores historical NFL/CFB games,
odds, injuries, weather, and predictions for backtesting the Billy Walters methodology.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import sqlite3
import json


class HistoricalDatabase:
    """Manages historical game data for backtesting."""

    def __init__(self, db_path: str = "data/historical/historical_games.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create all necessary tables if they don't exist."""
        cursor = self.conn.cursor()

        # Historical games table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id TEXT PRIMARY KEY,
                sport TEXT NOT NULL,
                season INTEGER NOT NULL,
                week INTEGER,
                game_date TEXT NOT NULL,
                game_time TEXT,
                away_team TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_score INTEGER,
                home_score INTEGER,
                venue TEXT,
                is_dome INTEGER DEFAULT 0,
                is_neutral INTEGER DEFAULT 0,
                is_playoff INTEGER DEFAULT 0,
                is_divisional INTEGER DEFAULT 0,
                game_status TEXT DEFAULT 'scheduled',
                data_source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Historical odds table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS odds (
                odds_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                sportsbook TEXT,
                odds_type TEXT NOT NULL,
                line_type TEXT,
                away_line REAL,
                away_price INTEGER,
                home_line REAL,
                home_price INTEGER,
                total_line REAL,
                over_price INTEGER,
                under_price INTEGER,
                timestamp TEXT NOT NULL,
                is_opening INTEGER DEFAULT 0,
                is_closing INTEGER DEFAULT 0,
                data_source TEXT,
                FOREIGN KEY (game_id) REFERENCES games (game_id)
            )
        """)

        # Historical injuries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS injuries (
                injury_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                team TEXT NOT NULL,
                player_name TEXT NOT NULL,
                position TEXT,
                injury_status TEXT,
                injury_type TEXT,
                report_date TEXT NOT NULL,
                impact_score REAL,
                data_source TEXT,
                FOREIGN KEY (game_id) REFERENCES games (game_id)
            )
        """)

        # Historical weather table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                temperature REAL,
                feels_like REAL,
                wind_speed REAL,
                wind_gust REAL,
                wind_direction TEXT,
                precipitation_prob INTEGER,
                precipitation_type TEXT,
                humidity INTEGER,
                cloud_cover INTEGER,
                visibility REAL,
                weather_description TEXT,
                weather_impact_score REAL,
                forecast_time TEXT NOT NULL,
                data_source TEXT,
                FOREIGN KEY (game_id) REFERENCES games (game_id)
            )
        """)

        # Historical predictions table (track our model's predictions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                prediction_date TEXT NOT NULL,
                model_version TEXT,
                away_power_rating REAL,
                home_power_rating REAL,
                pre_situational_margin REAL,
                situational_adjustment REAL,
                weather_adjustment REAL,
                emotional_adjustment REAL,
                final_predicted_margin REAL,
                predicted_total REAL,
                bet_recommendation TEXT,
                bet_side TEXT,
                bet_line REAL,
                bet_price INTEGER,
                star_rating REAL,
                suggested_stake REAL,
                win_probability REAL,
                expected_value REAL,
                edge_points REAL,
                factors_json TEXT,
                FOREIGN KEY (game_id) REFERENCES games (game_id)
            )
        """)

        # Results tracking table (track actual outcomes vs predictions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,
                bet_placed INTEGER DEFAULT 0,
                actual_margin REAL,
                actual_total REAL,
                bet_won INTEGER,
                bet_profit REAL,
                clv REAL,
                closing_line REAL,
                closing_price INTEGER,
                result_date TEXT,
                notes TEXT,
                FOREIGN KEY (prediction_id) REFERENCES predictions (prediction_id),
                FOREIGN KEY (game_id) REFERENCES games (game_id)
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_date
            ON games (game_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_season_week
            ON games (season, week)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_teams
            ON games (away_team, home_team)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_odds_game
            ON odds (game_id, is_opening, is_closing)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_game
            ON predictions (game_id)
        """)

        self.conn.commit()

    def insert_game(self, game_data: Dict[str, Any]) -> str:
        """Insert a historical game.

        Args:
            game_data: Dictionary with game information

        Returns:
            game_id of inserted game
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO games (
                game_id, sport, season, week, game_date, game_time,
                away_team, home_team, away_score, home_score,
                venue, is_dome, is_neutral, is_playoff, is_divisional,
                game_status, data_source, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            game_data['game_id'],
            game_data.get('sport', 'NFL'),
            game_data['season'],
            game_data.get('week'),
            game_data['game_date'],
            game_data.get('game_time'),
            game_data['away_team'],
            game_data['home_team'],
            game_data.get('away_score'),
            game_data.get('home_score'),
            game_data.get('venue'),
            game_data.get('is_dome', 0),
            game_data.get('is_neutral', 0),
            game_data.get('is_playoff', 0),
            game_data.get('is_divisional', 0),
            game_data.get('game_status', 'scheduled'),
            game_data.get('data_source', 'manual')
        ))
        self.conn.commit()
        return game_data['game_id']

    def insert_odds(self, odds_data: Dict[str, Any]) -> int:
        """Insert historical odds.

        Args:
            odds_data: Dictionary with odds information

        Returns:
            odds_id of inserted odds
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO odds (
                game_id, sportsbook, odds_type, line_type,
                away_line, away_price, home_line, home_price,
                total_line, over_price, under_price,
                timestamp, is_opening, is_closing, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            odds_data['game_id'],
            odds_data.get('sportsbook', 'unknown'),
            odds_data.get('odds_type', 'spread'),
            odds_data.get('line_type', 'standard'),
            odds_data.get('away_line'),
            odds_data.get('away_price'),
            odds_data.get('home_line'),
            odds_data.get('home_price'),
            odds_data.get('total_line'),
            odds_data.get('over_price'),
            odds_data.get('under_price'),
            odds_data.get('timestamp', datetime.now().isoformat()),
            odds_data.get('is_opening', 0),
            odds_data.get('is_closing', 0),
            odds_data.get('data_source', 'manual')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def insert_injury(self, injury_data: Dict[str, Any]) -> int:
        """Insert historical injury.

        Args:
            injury_data: Dictionary with injury information

        Returns:
            injury_id of inserted injury
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO injuries (
                game_id, team, player_name, position,
                injury_status, injury_type, report_date,
                impact_score, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            injury_data['game_id'],
            injury_data['team'],
            injury_data['player_name'],
            injury_data.get('position'),
            injury_data.get('injury_status'),
            injury_data.get('injury_type'),
            injury_data.get('report_date', datetime.now().isoformat()),
            injury_data.get('impact_score'),
            injury_data.get('data_source', 'manual')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def insert_weather(self, weather_data: Dict[str, Any]) -> int:
        """Insert historical weather.

        Args:
            weather_data: Dictionary with weather information

        Returns:
            weather_id of inserted weather
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO weather (
                game_id, temperature, feels_like, wind_speed, wind_gust,
                wind_direction, precipitation_prob, precipitation_type,
                humidity, cloud_cover, visibility, weather_description,
                weather_impact_score, forecast_time, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            weather_data['game_id'],
            weather_data.get('temperature'),
            weather_data.get('feels_like'),
            weather_data.get('wind_speed'),
            weather_data.get('wind_gust'),
            weather_data.get('wind_direction'),
            weather_data.get('precipitation_prob'),
            weather_data.get('precipitation_type'),
            weather_data.get('humidity'),
            weather_data.get('cloud_cover'),
            weather_data.get('visibility'),
            weather_data.get('weather_description'),
            weather_data.get('weather_impact_score'),
            weather_data.get('forecast_time', datetime.now().isoformat()),
            weather_data.get('data_source', 'manual')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def insert_prediction(self, prediction_data: Dict[str, Any]) -> int:
        """Insert model prediction for backtesting.

        Args:
            prediction_data: Dictionary with prediction information

        Returns:
            prediction_id of inserted prediction
        """
        cursor = self.conn.cursor()

        # Serialize factors to JSON
        factors_json = json.dumps(prediction_data.get('factors', {}))

        cursor.execute("""
            INSERT INTO predictions (
                game_id, prediction_date, model_version,
                away_power_rating, home_power_rating,
                pre_situational_margin, situational_adjustment,
                weather_adjustment, emotional_adjustment,
                final_predicted_margin, predicted_total,
                bet_recommendation, bet_side, bet_line, bet_price,
                star_rating, suggested_stake, win_probability,
                expected_value, edge_points, factors_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction_data['game_id'],
            prediction_data.get('prediction_date', datetime.now().isoformat()),
            prediction_data.get('model_version', 'v1.0'),
            prediction_data.get('away_power_rating'),
            prediction_data.get('home_power_rating'),
            prediction_data.get('pre_situational_margin'),
            prediction_data.get('situational_adjustment', 0),
            prediction_data.get('weather_adjustment', 0),
            prediction_data.get('emotional_adjustment', 0),
            prediction_data.get('final_predicted_margin'),
            prediction_data.get('predicted_total'),
            prediction_data.get('bet_recommendation'),
            prediction_data.get('bet_side'),
            prediction_data.get('bet_line'),
            prediction_data.get('bet_price'),
            prediction_data.get('star_rating'),
            prediction_data.get('suggested_stake'),
            prediction_data.get('win_probability'),
            prediction_data.get('expected_value'),
            prediction_data.get('edge_points'),
            factors_json
        ))
        self.conn.commit()
        return cursor.lastrowid

    def insert_result(self, result_data: Dict[str, Any]) -> int:
        """Insert backtest result.

        Args:
            result_data: Dictionary with result information

        Returns:
            result_id of inserted result
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO results (
                prediction_id, game_id, bet_placed,
                actual_margin, actual_total, bet_won, bet_profit,
                clv, closing_line, closing_price, result_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result_data['prediction_id'],
            result_data['game_id'],
            result_data.get('bet_placed', 0),
            result_data.get('actual_margin'),
            result_data.get('actual_total'),
            result_data.get('bet_won'),
            result_data.get('bet_profit'),
            result_data.get('clv'),
            result_data.get('closing_line'),
            result_data.get('closing_price'),
            result_data.get('result_date', datetime.now().isoformat()),
            result_data.get('notes')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_games(self, season: Optional[int] = None, week: Optional[int] = None) -> List[Dict]:
        """Get historical games.

        Args:
            season: Filter by season (optional)
            week: Filter by week (optional)

        Returns:
            List of game dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM games WHERE 1=1"
        params = []

        if season:
            query += " AND season = ?"
            params.append(season)
        if week is not None:
            query += " AND week = ?"
            params.append(week)

        query += " ORDER BY game_date, game_time"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_odds(self, game_id: str, is_opening: bool = None, is_closing: bool = None) -> List[Dict]:
        """Get odds for a game.

        Args:
            game_id: Game identifier
            is_opening: Filter for opening odds (optional)
            is_closing: Filter for closing odds (optional)

        Returns:
            List of odds dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM odds WHERE game_id = ?"
        params = [game_id]

        if is_opening is not None:
            query += " AND is_opening = ?"
            params.append(1 if is_opening else 0)
        if is_closing is not None:
            query += " AND is_closing = ?"
            params.append(1 if is_closing else 0)

        query += " ORDER BY timestamp"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_injuries(self, game_id: str) -> List[Dict]:
        """Get injuries for a game.

        Args:
            game_id: Game identifier

        Returns:
            List of injury dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM injuries WHERE game_id = ?", (game_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_weather(self, game_id: str) -> Optional[Dict]:
        """Get weather for a game.

        Args:
            game_id: Game identifier

        Returns:
            Weather dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM weather WHERE game_id = ? ORDER BY forecast_time DESC LIMIT 1", (game_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_predictions(self, game_id: str) -> List[Dict]:
        """Get predictions for a game.

        Args:
            game_id: Game identifier

        Returns:
            List of prediction dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE game_id = ? ORDER BY prediction_date", (game_id,))
        predictions = [dict(row) for row in cursor.fetchall()]

        # Parse factors JSON
        for pred in predictions:
            if pred.get('factors_json'):
                pred['factors'] = json.loads(pred['factors_json'])

        return predictions

    def get_results(self, prediction_id: Optional[int] = None, season: Optional[int] = None) -> List[Dict]:
        """Get backtest results.

        Args:
            prediction_id: Filter by prediction_id (optional)
            season: Filter by season (optional)

        Returns:
            List of result dictionaries
        """
        cursor = self.conn.cursor()

        if prediction_id:
            query = """
                SELECT r.*, g.season, g.week, g.away_team, g.home_team
                FROM results r
                JOIN games g ON r.game_id = g.game_id
                WHERE r.prediction_id = ?
            """
            cursor.execute(query, (prediction_id,))
        elif season:
            query = """
                SELECT r.*, g.season, g.week, g.away_team, g.home_team
                FROM results r
                JOIN games g ON r.game_id = g.game_id
                WHERE g.season = ?
                ORDER BY g.game_date
            """
            cursor.execute(query, (season,))
        else:
            query = """
                SELECT r.*, g.season, g.week, g.away_team, g.home_team
                FROM results r
                JOIN games g ON r.game_id = g.game_id
                ORDER BY g.game_date
            """
            cursor.execute(query)

        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
