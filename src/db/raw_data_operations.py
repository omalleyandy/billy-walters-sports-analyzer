"""
Raw Data Operations

CRUD operations for raw data tables from data collection pipeline.
"""

from typing import Dict, List, Optional

from .connection import DatabaseConnection
from .raw_data_models import (
    GameSchedule,
    GameResult,
    TeamStats,
    PlayerStats,
    TeamStandings,
    PowerRating,
    BettingOdds,
    SharpMoneySignal,
    WeatherData,
    InjuryReport,
    NewsArticle,
    CollectionSession,
)


class RawDataOperations:
    """CRUD operations for raw data tables."""

    def __init__(self, db: DatabaseConnection):
        """Initialize with database connection."""
        self.db = db

    # ============================================================
    # GAME SCHEDULES
    # ============================================================

    def insert_game_schedule(self, schedule: GameSchedule) -> None:
        """Insert game schedule."""
        query = """
            INSERT OR REPLACE INTO game_schedules (
                game_id, league_id, season, week, away_team_id, home_team_id,
                game_datetime, venue_name, venue_city, is_neutral_site, is_indoor,
                status, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                schedule.game_id,
                schedule.league_id,
                schedule.season,
                schedule.week,
                schedule.away_team_id,
                schedule.home_team_id,
                schedule.game_datetime,
                schedule.venue_name,
                schedule.venue_city,
                schedule.is_neutral_site,
                schedule.is_indoor,
                schedule.status,
                schedule.source,
            ),
            fetch=False,
        )

    def get_game_schedules_by_week(
        self, league_id: int, season: int, week: int
    ) -> List[Dict]:
        """Get games for a specific week."""
        query = """
            SELECT * FROM game_schedules
            WHERE league_id = ? AND season = ? AND week = ?
            ORDER BY game_datetime
        """
        results = self.db.execute_query(query, (league_id, season, week))
        return [dict(row) for row in results] if results else []

    # ============================================================
    # GAME RESULTS
    # ============================================================

    def insert_game_result(self, result: GameResult) -> None:
        """Insert game result."""
        query = """
            INSERT OR REPLACE INTO game_results (
                game_id, league_id, away_team_id, home_team_id,
                away_score, home_score, away_ats, home_ats, over_under,
                attendance, status, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                result.game_id,
                result.league_id,
                result.away_team_id,
                result.home_team_id,
                result.away_score,
                result.home_score,
                result.away_ats,
                result.home_ats,
                result.over_under,
                result.attendance,
                result.status,
                result.source,
            ),
            fetch=False,
        )

    def get_game_result(self, game_id: str) -> Optional[Dict]:
        """Get game result by ID."""
        query = "SELECT * FROM game_results WHERE game_id = ?"
        results = self.db.execute_query(query, (game_id,))
        return dict(results[0]) if results else None

    # ============================================================
    # TEAM STATISTICS
    # ============================================================

    def insert_team_stats(self, stats: TeamStats) -> None:
        """Insert team statistics."""
        query = """
            INSERT OR REPLACE INTO team_stats (
                league_id, team_id, season, week, points_for, passing_yards,
                rushing_yards, total_yards, first_downs, third_down_conversion_pct,
                fourth_down_conversion_pct, turnovers, fumbles, interceptions,
                penalties, penalty_yards, red_zone_efficiency, scoring_efficiency,
                points_against, passing_yards_allowed, rushing_yards_allowed,
                total_yards_allowed, sacks, interceptions_forced, fumbles_forced,
                defensive_touchdowns, red_zone_defense, field_goal_pct,
                extra_point_pct, punting_avg, kickoff_return_avg, punt_return_avg,
                time_of_possession, games_played, games_won, games_lost, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                stats.league_id,
                stats.team_id,
                stats.season,
                stats.week,
                stats.points_for,
                stats.passing_yards,
                stats.rushing_yards,
                stats.total_yards,
                stats.first_downs,
                stats.third_down_conversion_pct,
                stats.fourth_down_conversion_pct,
                stats.turnovers,
                stats.fumbles,
                stats.interceptions,
                stats.penalties,
                stats.penalty_yards,
                stats.red_zone_efficiency,
                stats.scoring_efficiency,
                stats.points_against,
                stats.passing_yards_allowed,
                stats.rushing_yards_allowed,
                stats.total_yards_allowed,
                stats.sacks,
                stats.interceptions_forced,
                stats.fumbles_forced,
                stats.defensive_touchdowns,
                stats.red_zone_defense,
                stats.field_goal_pct,
                stats.extra_point_pct,
                stats.punting_avg,
                stats.kickoff_return_avg,
                stats.punt_return_avg,
                stats.time_of_possession,
                stats.games_played,
                stats.games_won,
                stats.games_lost,
                stats.source,
            ),
            fetch=False,
        )

    def get_team_stats_season(
        self, league_id: int, team_id: int, season: int
    ) -> List[Dict]:
        """Get team stats for entire season."""
        query = """
            SELECT * FROM team_stats
            WHERE league_id = ? AND team_id = ? AND season = ?
            ORDER BY week
        """
        results = self.db.execute_query(query, (league_id, team_id, season))
        return [dict(row) for row in results] if results else []

    # ============================================================
    # POWER RATINGS
    # ============================================================

    def insert_power_rating(self, rating: PowerRating) -> None:
        """Insert power rating."""
        query = """
            INSERT OR REPLACE INTO power_ratings (
                league_id, team_id, season, week, overall_rating,
                offensive_rating, defensive_rating, special_teams_rating,
                strength_of_schedule, strength_of_victory, strength_of_loss,
                recent_form_rating, injury_adjustment, rest_adjustment,
                momentum_adjustment, massey_rating, massey_rank, source, rating_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                rating.league_id,
                rating.team_id,
                rating.season,
                rating.week,
                rating.overall_rating,
                rating.offensive_rating,
                rating.defensive_rating,
                rating.special_teams_rating,
                rating.strength_of_schedule,
                rating.strength_of_victory,
                rating.strength_of_loss,
                rating.recent_form_rating,
                rating.injury_adjustment,
                rating.rest_adjustment,
                rating.momentum_adjustment,
                rating.massey_rating,
                rating.massey_rank,
                rating.source,
                rating.rating_date,
            ),
            fetch=False,
        )

    def get_power_rating(
        self,
        league_id: int,
        team_id: int,
        season: int,
        week: Optional[int] = None,
        source: Optional[str] = None,
    ) -> Optional[Dict]:
        """Get power rating by league, team, season, and optionally week/source."""
        if week and source:
            query = """
                SELECT * FROM power_ratings
                WHERE league_id = ? AND team_id = ? AND season = ? AND week = ? AND source = ?
            """
            results = self.db.execute_query(
                query, (league_id, team_id, season, week, source)
            )
        elif week:
            query = """
                SELECT * FROM power_ratings
                WHERE league_id = ? AND team_id = ? AND season = ? AND week = ?
            """
            results = self.db.execute_query(query, (league_id, team_id, season, week))
        else:
            query = """
                SELECT * FROM power_ratings
                WHERE league_id = ? AND team_id = ? AND season = ?
                ORDER BY week DESC, source
            """
            results = self.db.execute_query(query, (league_id, team_id, season))

        return dict(results[0]) if results else None

    def get_all_power_ratings_week(
        self, league_id: int, season: int, week: int, source: Optional[str] = None
    ) -> List[Dict]:
        """Get all power ratings for a week."""
        if source:
            query = """
                SELECT * FROM power_ratings
                WHERE league_id = ? AND season = ? AND week = ? AND source = ?
                ORDER BY overall_rating DESC
            """
            results = self.db.execute_query(query, (league_id, season, week, source))
        else:
            query = """
                SELECT * FROM power_ratings
                WHERE league_id = ? AND season = ? AND week = ?
                ORDER BY source, overall_rating DESC
            """
            results = self.db.execute_query(query, (league_id, season, week))

        return [dict(row) for row in results] if results else []

    # ============================================================
    # BETTING ODDS
    # ============================================================

    def insert_betting_odds(self, odds: BettingOdds) -> None:
        """Insert betting odds."""
        query = """
            INSERT INTO betting_odds (
                game_id, league_id, week, away_team_id, home_team_id,
                spread, spread_odds, total, total_odds, away_moneyline,
                home_moneyline, line_time, opening_time, closing_time,
                source, sportsbook
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                odds.game_id,
                odds.league_id,
                odds.week,
                odds.away_team_id,
                odds.home_team_id,
                odds.spread,
                odds.spread_odds,
                odds.total,
                odds.total_odds,
                odds.away_moneyline,
                odds.home_moneyline,
                odds.line_time,
                odds.opening_time,
                odds.closing_time,
                odds.source,
                odds.sportsbook,
            ),
            fetch=False,
        )

    def get_betting_odds_game(
        self, game_id: str, source: Optional[str] = None
    ) -> List[Dict]:
        """Get all odds for a game."""
        if source:
            query = """
                SELECT * FROM betting_odds
                WHERE game_id = ? AND source = ?
                ORDER BY line_time DESC
            """
            results = self.db.execute_query(query, (game_id, source))
        else:
            query = """
                SELECT * FROM betting_odds
                WHERE game_id = ?
                ORDER BY source, line_time DESC
            """
            results = self.db.execute_query(query, (game_id,))

        return [dict(row) for row in results] if results else []

    # ============================================================
    # SHARP MONEY SIGNALS
    # ============================================================

    def insert_sharp_money_signal(self, signal: SharpMoneySignal) -> None:
        """Insert sharp money signal."""
        query = """
            INSERT OR REPLACE INTO sharp_money_signals (
                game_id, league_id, week, away_team_id, home_team_id,
                spread_value, spread_side, spread_tickets_pct, spread_money_pct,
                spread_divergence, total_value, total_over_tickets_pct,
                total_over_money_pct, total_divergence, away_tickets_pct,
                away_money_pct, home_tickets_pct, home_money_pct,
                moneyline_divergence, sharp_signal_strength, signal_direction,
                confidence_level, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                signal.game_id,
                signal.league_id,
                signal.week,
                signal.away_team_id,
                signal.home_team_id,
                signal.spread_value,
                signal.spread_side,
                signal.spread_tickets_pct,
                signal.spread_money_pct,
                signal.spread_divergence,
                signal.total_value,
                signal.total_over_tickets_pct,
                signal.total_over_money_pct,
                signal.total_divergence,
                signal.away_tickets_pct,
                signal.away_money_pct,
                signal.home_tickets_pct,
                signal.home_money_pct,
                signal.moneyline_divergence,
                signal.sharp_signal_strength,
                signal.signal_direction,
                signal.confidence_level,
                signal.source,
            ),
            fetch=False,
        )

    def get_sharp_signals_strong(
        self, league_id: int, week: int, min_strength: float = 0.7
    ) -> List[Dict]:
        """Get strong sharp money signals for a week."""
        query = """
            SELECT * FROM sharp_money_signals
            WHERE league_id = ? AND week = ? AND sharp_signal_strength >= ?
            ORDER BY sharp_signal_strength DESC
        """
        results = self.db.execute_query(query, (league_id, week, min_strength))
        return [dict(row) for row in results] if results else []

    # ============================================================
    # WEATHER
    # ============================================================

    def insert_weather_data(self, weather: WeatherData) -> None:
        """Insert weather data."""
        query = """
            INSERT OR REPLACE INTO weather_data (
                game_id, league_id, week, game_datetime, venue_name, venue_city,
                temperature_f, temperature_c, wind_speed_mph, wind_direction,
                precipitation_in, humidity_pct, cloud_cover_pct, feels_like_temp_f,
                uv_index, visibility_mi, conditions, weather_category, source,
                forecast_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                weather.game_id,
                weather.league_id,
                weather.week,
                weather.game_datetime,
                weather.venue_name,
                weather.venue_city,
                weather.temperature_f,
                weather.temperature_c,
                weather.wind_speed_mph,
                weather.wind_direction,
                weather.precipitation_in,
                weather.humidity_pct,
                weather.cloud_cover_pct,
                weather.feels_like_temp_f,
                weather.uv_index,
                weather.visibility_mi,
                weather.conditions,
                weather.weather_category,
                weather.source,
                weather.forecast_time,
            ),
            fetch=False,
        )

    def get_weather_game(self, game_id: str) -> Optional[Dict]:
        """Get weather for a game."""
        query = "SELECT * FROM weather_data WHERE game_id = ?"
        results = self.db.execute_query(query, (game_id,))
        return dict(results[0]) if results else None

    # ============================================================
    # INJURIES
    # ============================================================

    def insert_injury_report(self, injury: InjuryReport) -> None:
        """Insert injury report."""
        query = """
            INSERT INTO injury_reports (
                league_id, team_id, player_name, player_id, position, season,
                week, injury_status, body_part, severity, expected_return,
                out_weeks, is_starter, impact_rating, source, reported_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                injury.league_id,
                injury.team_id,
                injury.player_name,
                injury.player_id,
                injury.position,
                injury.season,
                injury.week,
                injury.injury_status,
                injury.body_part,
                injury.severity,
                injury.expected_return,
                injury.out_weeks,
                injury.is_starter,
                injury.impact_rating,
                injury.source,
                injury.reported_date,
            ),
            fetch=False,
        )

    def get_team_injuries_week(
        self, league_id: int, team_id: int, week: int
    ) -> List[Dict]:
        """Get injury reports for a team in a week."""
        query = """
            SELECT * FROM injury_reports
            WHERE league_id = ? AND team_id = ? AND week = ?
            ORDER BY is_starter DESC, impact_rating DESC
        """
        results = self.db.execute_query(query, (league_id, team_id, week))
        return [dict(row) for row in results] if results else []

    def get_key_injuries_week(self, league_id: int, week: int) -> List[Dict]:
        """Get all key/starter injuries for a league week."""
        query = """
            SELECT * FROM injury_reports
            WHERE league_id = ? AND week = ? AND is_starter = 1
            ORDER BY impact_rating DESC
        """
        results = self.db.execute_query(query, (league_id, week))
        return [dict(row) for row in results] if results else []

    # ============================================================
    # COLLECTION SESSIONS
    # ============================================================

    def insert_collection_session(self, session: CollectionSession) -> None:
        """Insert collection session metadata."""
        query = """
            INSERT INTO collection_sessions (
                league_id, season, week, started_at, completed_at,
                sources_attempted, sources_successful, sources_failed,
                games_collected, stats_records_collected, odds_records_collected,
                weather_records_collected, injuries_collected, status,
                error_messages
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                session.league_id,
                session.season,
                session.week,
                session.started_at,
                session.completed_at,
                session.sources_attempted,
                session.sources_successful,
                session.sources_failed,
                session.games_collected,
                session.stats_records_collected,
                session.odds_records_collected,
                session.weather_records_collected,
                session.injuries_collected,
                session.status,
                session.error_messages,
            ),
            fetch=False,
        )

    def get_recent_sessions(self, league_id: int, limit: int = 10) -> List[Dict]:
        """Get recent collection sessions."""
        query = """
            SELECT * FROM collection_sessions
            WHERE league_id = ?
            ORDER BY started_at DESC
            LIMIT ?
        """
        results = self.db.execute_query(query, (league_id, limit))
        return [dict(row) for row in results] if results else []
