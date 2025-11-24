"""
Database Operations

Provides CRUD operations for all database tables.
"""

from typing import Dict, List, Optional

from .connection import DatabaseConnection
from .models import Bet, Game, Injury, Odds, PowerRating, Weather


class DatabaseOperations:
    """High-level database operations."""

    def __init__(self, db: DatabaseConnection):
        """Initialize with database connection."""
        self.db = db

    # ============================================================
    # GAMES
    # ============================================================

    def insert_game(self, game: Game) -> None:
        """Insert game into database."""
        query = """
            INSERT INTO games (
                game_id, season, week, league, game_date,
                home_team, away_team, home_score, away_score,
                final_margin, total_points, status,
                stadium, is_outdoor, is_neutral_site
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (game_id) DO UPDATE SET
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score,
                final_margin = EXCLUDED.final_margin,
                total_points = EXCLUDED.total_points,
                status = EXCLUDED.status,
                updated_at = NOW()
        """

        self.db.execute_query(
            query,
            (
                game.game_id,
                game.season,
                game.week,
                game.league,
                game.game_date,
                game.home_team,
                game.away_team,
                game.home_score,
                game.away_score,
                game.final_margin,
                game.total_points,
                game.status,
                game.stadium,
                game.is_outdoor,
                game.is_neutral_site,
            ),
            fetch=False,
        )

    def get_games_by_week(
        self, season: int, week: int, league: str = "NFL"
    ) -> List[Dict]:
        """Get all games for a specific week."""
        query = """
            SELECT * FROM games
            WHERE season = %s AND week = %s AND league = %s
            ORDER BY game_date
        """
        results = self.db.execute_query(query, (season, week, league))
        return [dict(row) for row in results] if results else []

    def get_game_by_id(self, game_id: str) -> Optional[Dict]:
        """Get game by ID."""
        query = "SELECT * FROM games WHERE game_id = %s"
        results = self.db.execute_query(query, (game_id,))
        return dict(results[0]) if results else None

    def update_game_score(
        self, game_id: str, home_score: int, away_score: int
    ) -> None:
        """Update game final score."""
        query = """
            UPDATE games
            SET home_score = %s,
                away_score = %s,
                final_margin = %s,
                total_points = %s,
                status = 'FINAL',
                updated_at = NOW()
            WHERE game_id = %s
        """
        self.db.execute_query(
            query,
            (
                home_score,
                away_score,
                home_score - away_score,
                home_score + away_score,
                game_id,
            ),
            fetch=False,
        )

    # ============================================================
    # POWER RATINGS
    # ============================================================

    def insert_power_rating(self, rating: PowerRating) -> None:
        """Insert or update power rating."""
        query = """
            INSERT INTO power_ratings (
                season, week, league, team,
                rating, offense_rating, defense_rating, special_teams_rating,
                sos_adjustment, recent_form_adjustment, injury_adjustment,
                source, raw_rating
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
            ON CONFLICT (season, week, league, team, source)
            DO UPDATE SET
                rating = EXCLUDED.rating,
                offense_rating = EXCLUDED.offense_rating,
                defense_rating = EXCLUDED.defense_rating,
                special_teams_rating = EXCLUDED.special_teams_rating,
                sos_adjustment = EXCLUDED.sos_adjustment,
                recent_form_adjustment = EXCLUDED.recent_form_adjustment,
                injury_adjustment = EXCLUDED.injury_adjustment,
                raw_rating = EXCLUDED.raw_rating,
                updated_at = NOW()
        """

        self.db.execute_query(
            query,
            (
                rating.season,
                rating.week,
                rating.league,
                rating.team,
                rating.rating,
                rating.offense_rating,
                rating.defense_rating,
                rating.special_teams_rating,
                rating.sos_adjustment,
                rating.recent_form_adjustment,
                rating.injury_adjustment,
                rating.source,
                rating.raw_rating,
            ),
            fetch=False,
        )

    def get_power_ratings(
        self, season: int, week: int, league: str = "NFL", source: str = "composite"
    ) -> List[Dict]:
        """Get power ratings for a week."""
        query = """
            SELECT * FROM power_ratings
            WHERE season = %s AND week = %s AND league = %s AND source = %s
            ORDER BY rating DESC
        """
        results = self.db.execute_query(query, (season, week, league, source))
        return [dict(row) for row in results] if results else []

    def get_team_rating(
        self, team: str, season: int, week: int, source: str = "composite"
    ) -> Optional[float]:
        """Get specific team rating."""
        query = """
            SELECT rating FROM power_ratings
            WHERE team = %s AND season = %s AND week = %s AND source = %s
        """
        results = self.db.execute_query(query, (team, season, week, source))
        return float(results[0]["rating"]) if results else None

    # ============================================================
    # ODDS
    # ============================================================

    def insert_odds(self, odds: Odds) -> None:
        """Insert odds snapshot."""
        query = """
            INSERT INTO odds (
                game_id, sportsbook, odds_type,
                home_spread, home_spread_juice,
                away_spread, away_spread_juice,
                total, over_juice, under_juice,
                home_moneyline, away_moneyline,
                timestamp, line_movement
            ) VALUES (
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s
            )
        """

        self.db.execute_query(
            query,
            (
                odds.game_id,
                odds.sportsbook,
                odds.odds_type,
                odds.home_spread,
                odds.home_spread_juice,
                odds.away_spread,
                odds.away_spread_juice,
                odds.total,
                odds.over_juice,
                odds.under_juice,
                odds.home_moneyline,
                odds.away_moneyline,
                odds.timestamp,
                odds.line_movement,
            ),
            fetch=False,
        )

    def get_closing_line(self, game_id: str, sportsbook: str = "overtime") -> Optional[Dict]:
        """Get closing line for a game."""
        query = """
            SELECT * FROM odds
            WHERE game_id = %s
                AND sportsbook = %s
                AND odds_type = 'closing'
            ORDER BY timestamp DESC
            LIMIT 1
        """
        results = self.db.execute_query(query, (game_id, sportsbook))
        return dict(results[0]) if results else None

    # ============================================================
    # BETS
    # ============================================================

    def insert_bet(self, bet: Bet) -> None:
        """Insert bet."""
        query = """
            INSERT INTO bets (
                bet_id, game_id,
                bet_type, side, line, juice, sportsbook,
                predicted_line, market_line, edge_points, edge_category, confidence,
                kelly_pct, actual_pct, units, risk_amount,
                closing_line, clv,
                result, profit_loss, roi,
                placed_at, closed_at, graded_at,
                notes, key_factors
            ) VALUES (
                %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
            ON CONFLICT (bet_id) DO UPDATE SET
                closing_line = EXCLUDED.closing_line,
                clv = EXCLUDED.clv,
                result = EXCLUDED.result,
                profit_loss = EXCLUDED.profit_loss,
                roi = EXCLUDED.roi,
                graded_at = EXCLUDED.graded_at,
                updated_at = NOW()
        """

        self.db.execute_query(
            query,
            (
                bet.bet_id,
                bet.game_id,
                bet.bet_type,
                bet.side,
                bet.line,
                bet.juice,
                bet.sportsbook,
                bet.predicted_line,
                bet.market_line,
                bet.edge_points,
                bet.edge_category,
                bet.confidence,
                bet.kelly_pct,
                bet.actual_pct,
                bet.units,
                bet.risk_amount,
                bet.closing_line,
                bet.clv,
                bet.result,
                bet.profit_loss,
                bet.roi,
                bet.placed_at,
                bet.closed_at,
                bet.graded_at,
                bet.notes,
                bet.key_factors,
            ),
            fetch=False,
        )

    def get_bets_by_week(
        self, season: int, week: int, league: str = "NFL"
    ) -> List[Dict]:
        """Get all bets for a specific week."""
        query = """
            SELECT b.*, g.home_team, g.away_team, g.game_date
            FROM bets b
            JOIN games g ON b.game_id = g.game_id
            WHERE g.season = %s AND g.week = %s AND g.league = %s
            ORDER BY b.edge_points DESC
        """
        results = self.db.execute_query(query, (season, week, league))
        return [dict(row) for row in results] if results else []

    def update_bet_result(
        self,
        bet_id: str,
        result: str,
        profit_loss: float,
        closing_line: Optional[float] = None,
    ) -> None:
        """Update bet result after game finishes."""
        # Calculate CLV if closing line provided
        clv = None
        if closing_line:
            bet = self.get_bet_by_id(bet_id)
            if bet:
                our_line = float(bet["line"])
                clv = closing_line - our_line

        # Calculate ROI
        risk = abs(profit_loss) if profit_loss < 0 else profit_loss / 0.909
        roi = (profit_loss / risk * 100) if risk > 0 else 0

        query = """
            UPDATE bets
            SET result = %s,
                profit_loss = %s,
                roi = %s,
                closing_line = %s,
                clv = %s,
                graded_at = NOW(),
                updated_at = NOW()
            WHERE bet_id = %s
        """

        self.db.execute_query(
            query, (result, profit_loss, roi, closing_line, clv, bet_id), fetch=False
        )

    def get_bet_by_id(self, bet_id: str) -> Optional[Dict]:
        """Get bet by ID."""
        query = "SELECT * FROM bets WHERE bet_id = %s"
        results = self.db.execute_query(query, (bet_id,))
        return dict(results[0]) if results else None

    # ============================================================
    # WEATHER
    # ============================================================

    def insert_weather(self, weather: Weather) -> None:
        """Insert weather data."""
        query = """
            INSERT INTO weather (
                game_id,
                temperature, feels_like,
                wind_speed, wind_gust, wind_direction,
                humidity, precipitation_chance, precipitation_type, precipitation_amount,
                visibility, cloud_cover,
                total_adjustment, spread_adjustment,
                weather_severity_score, weather_category,
                source, forecast_type, forecast_hours_ahead, is_actual,
                timestamp
            ) VALUES (
                %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s
            )
        """

        self.db.execute_query(
            query,
            (
                weather.game_id,
                weather.temperature,
                weather.feels_like,
                weather.wind_speed,
                weather.wind_gust,
                weather.wind_direction,
                weather.humidity,
                weather.precipitation_chance,
                weather.precipitation_type,
                weather.precipitation_amount,
                weather.visibility,
                weather.cloud_cover,
                weather.total_adjustment,
                weather.spread_adjustment,
                weather.weather_severity_score,
                weather.weather_category,
                weather.source,
                weather.forecast_type,
                weather.forecast_hours_ahead,
                weather.is_actual,
                weather.timestamp,
            ),
            fetch=False,
        )

    def get_game_weather(
        self, game_id: str, is_actual: bool = True
    ) -> Optional[Dict]:
        """Get weather for a game."""
        query = """
            SELECT * FROM weather
            WHERE game_id = %s AND is_actual = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """
        results = self.db.execute_query(query, (game_id, is_actual))
        return dict(results[0]) if results else None

    # ============================================================
    # INJURIES
    # ============================================================

    def insert_injury(self, injury: Injury) -> None:
        """Insert injury report."""
        query = """
            INSERT INTO injuries (
                game_id, team,
                player_name, position, jersey_number,
                injury_status, injury_type, injury_side,
                impact_points, player_tier, is_key_player,
                reported_date, game_status, last_updated,
                source
            ) VALUES (
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s
            )
            ON CONFLICT (id) DO UPDATE SET
                injury_status = EXCLUDED.injury_status,
                game_status = EXCLUDED.game_status,
                last_updated = NOW(),
                updated_at = NOW()
        """

        self.db.execute_query(
            query,
            (
                injury.game_id,
                injury.team,
                injury.player_name,
                injury.position,
                injury.jersey_number,
                injury.injury_status,
                injury.injury_type,
                injury.injury_side,
                injury.impact_points,
                injury.player_tier,
                injury.is_key_player,
                injury.reported_date,
                injury.game_status,
                injury.last_updated,
                injury.source,
            ),
            fetch=False,
        )

    def get_game_injuries(self, game_id: str, team: Optional[str] = None) -> List[Dict]:
        """Get injuries for a game."""
        if team:
            query = """
                SELECT * FROM injuries
                WHERE game_id = %s AND team = %s
                ORDER BY impact_points DESC NULLS LAST
            """
            results = self.db.execute_query(query, (game_id, team))
        else:
            query = """
                SELECT * FROM injuries
                WHERE game_id = %s
                ORDER BY team, impact_points DESC NULLS LAST
            """
            results = self.db.execute_query(query, (game_id,))

        return [dict(row) for row in results] if results else []

    # ============================================================
    # ANALYTICS
    # ============================================================

    def calculate_weekly_clv(self, season: int, week: int) -> Dict:
        """Calculate CLV metrics for a week."""
        query = """
            SELECT
                COUNT(*) as total_bets,
                AVG(clv) as avg_clv,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY clv) as median_clv,
                SUM(CASE WHEN clv > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as positive_clv_pct,
                SUM(CASE WHEN clv > 0 AND result = 'WIN' THEN 1 ELSE 0 END) as clv_wins,
                SUM(CASE WHEN clv > 0 AND result = 'LOSS' THEN 1 ELSE 0 END) as clv_losses
            FROM bets b
            JOIN games g ON b.game_id = g.game_id
            WHERE g.season = %s AND g.week = %s
                AND b.clv IS NOT NULL
        """

        results = self.db.execute_query(query, (season, week))
        return dict(results[0]) if results else {}

    def get_edge_performance(self, season: int) -> List[Dict]:
        """Get performance by edge category."""
        query = """
            SELECT
                edge_category,
                COUNT(*) as bets,
                AVG(edge_points) as avg_edge,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END)::FLOAT /
                    NULLIF(SUM(CASE WHEN result IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0) * 100 as win_pct,
                AVG(clv) as avg_clv,
                AVG(roi) as avg_roi,
                SUM(profit_loss) as total_profit
            FROM bets b
            JOIN games g ON b.game_id = g.game_id
            WHERE g.season = %s AND result IN ('WIN', 'LOSS', 'PUSH')
            GROUP BY edge_category
            ORDER BY avg_edge DESC
        """

        results = self.db.execute_query(query, (season,))
        return [dict(row) for row in results] if results else []
