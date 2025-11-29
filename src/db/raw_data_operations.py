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
    PlayerValuation,
    PracticeReport,
    GameSWEFactors,
    TeamTrends,
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

    # ============================================================
    # TIER 1 CRITICAL TABLES (Billy Walters Methodology Support)
    # ============================================================

    # PLAYER VALUATIONS
    # ============================================================

    def insert_player_valuation(self, valuation: PlayerValuation) -> None:
        """Insert player valuation."""
        query = """
            INSERT OR REPLACE INTO player_valuations (
                league_id, team_id, player_id, player_name, position,
                season, week, point_value, snap_count_pct, impact_rating,
                is_starter, depth_chart_position, notes, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                valuation.league_id,
                valuation.team_id,
                valuation.player_id,
                valuation.player_name,
                valuation.position,
                valuation.season,
                valuation.week,
                valuation.point_value,
                valuation.snap_count_pct,
                valuation.impact_rating,
                valuation.is_starter,
                valuation.depth_chart_position,
                valuation.notes,
                valuation.source,
            ),
            fetch=False,
        )

    def get_player_valuation(
        self,
        league_id: int,
        team_id: int,
        season: int,
        week: Optional[int] = None,
        player_id: Optional[str] = None,
    ) -> Optional[Dict]:
        """Get player valuation by league, team, season, week, player."""
        if player_id and week:
            query = """
                SELECT * FROM player_valuations
                WHERE league_id = ? AND team_id = ? AND season = ?
                AND week = ? AND player_id = ?
            """
            results = self.db.execute_query(
                query, (league_id, team_id, season, week, player_id)
            )
        else:
            query = """
                SELECT * FROM player_valuations
                WHERE league_id = ? AND team_id = ? AND season = ?
            """
            results = self.db.execute_query(query, (league_id, team_id, season))

        return dict(results[0]) if results else None

    def get_team_valuations_by_week(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> List[Dict]:
        """Get all player valuations for a team in a week."""
        query = """
            SELECT * FROM player_valuations
            WHERE league_id = ? AND team_id = ? AND season = ? AND week = ?
            ORDER BY point_value DESC
        """
        results = self.db.execute_query(query, (league_id, team_id, season, week))
        return [dict(row) for row in results] if results else []

    def get_starters_by_position(
        self, league_id: int, team_id: int, season: int, week: int, position: str
    ) -> List[Dict]:
        """Get starters at a specific position."""
        query = """
            SELECT * FROM player_valuations
            WHERE league_id = ? AND team_id = ? AND season = ? AND week = ?
            AND position = ? AND is_starter = 1
            ORDER BY point_value DESC
        """
        results = self.db.execute_query(
            query, (league_id, team_id, season, week, position)
        )
        return [dict(row) for row in results] if results else []

    def update_player_snap_count(
        self, league_id: int, team_id: int, player_id: str, snap_count_pct: float
    ) -> None:
        """Update player snap count percentage."""
        query = """
            UPDATE player_valuations
            SET snap_count_pct = ?
            WHERE league_id = ? AND team_id = ? AND player_id = ?
        """
        self.db.execute_query(
            query, (snap_count_pct, league_id, team_id, player_id), fetch=False
        )

    # PRACTICE REPORTS
    # ============================================================

    def insert_practice_report(self, report: PracticeReport) -> None:
        """Insert practice report."""
        query = """
            INSERT OR REPLACE INTO practice_reports (
                league_id, team_id, player_id, player_name, season, week,
                practice_date, day_of_week, participation, severity, notes,
                trend, sessions_participated, source, reported_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                report.league_id,
                report.team_id,
                report.player_id,
                report.player_name,
                report.season,
                report.week,
                report.practice_date,
                report.day_of_week,
                report.participation,
                report.severity,
                report.notes,
                report.trend,
                report.sessions_participated,
                report.source,
                None,  # reported_date set to NOW by DB
            ),
            fetch=False,
        )

    def get_practice_reports_by_week(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> List[Dict]:
        """Get practice reports for a team in a week."""
        query = """
            SELECT * FROM practice_reports
            WHERE league_id = ? AND team_id = ? AND season = ? AND week = ?
            ORDER BY practice_date DESC
        """
        results = self.db.execute_query(query, (league_id, team_id, season, week))
        return [dict(row) for row in results] if results else []

    def get_player_practice_history(
        self,
        league_id: int,
        team_id: int,
        player_id: str,
        season: int,
        week_start: int,
        week_end: int,
    ) -> List[Dict]:
        """Get practice history for a player across multiple weeks."""
        query = """
            SELECT * FROM practice_reports
            WHERE league_id = ? AND team_id = ? AND player_id = ?
            AND season = ? AND week BETWEEN ? AND ?
            ORDER BY practice_date DESC
        """
        results = self.db.execute_query(
            query, (league_id, team_id, player_id, season, week_start, week_end)
        )
        return [dict(row) for row in results] if results else []

    def get_wednesday_status(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> List[Dict]:
        """Get Wednesday practice status (Billy's key signal)."""
        query = """
            SELECT * FROM practice_reports
            WHERE league_id = ? AND team_id = ? AND season = ? AND week = ?
            AND day_of_week = 2
            ORDER BY player_name
        """
        results = self.db.execute_query(query, (league_id, team_id, season, week))
        return [dict(row) for row in results] if results else []

    def update_practice_trend(
        self,
        league_id: int,
        team_id: int,
        player_id: str,
        season: int,
        week: int,
        trend: str,
    ) -> None:
        """Update practice trend for a player."""
        query = """
            UPDATE practice_reports
            SET trend = ?
            WHERE league_id = ? AND team_id = ? AND player_id = ?
            AND season = ? AND week = ?
        """
        self.db.execute_query(
            query,
            (trend, league_id, team_id, player_id, season, week),
            fetch=False,
        )

    # GAME SWE FACTORS
    # ============================================================

    def insert_game_swe_factors(self, factors: GameSWEFactors) -> None:
        """Insert game SWE factors."""
        query = """
            INSERT OR REPLACE INTO game_swe_factors (
                league_id, game_id, season, week, away_team_id, home_team_id,
                special_factor_description, special_adjustment, special_examples,
                weather_factor_description, weather_adjustment, temperature_impact,
                wind_impact, precipitation_impact,
                emotional_factor_description, emotional_adjustment,
                motivation_level, momentum_direction,
                total_adjustment, confidence_level, notes, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                factors.league_id,
                factors.game_id,
                factors.season,
                factors.week,
                factors.away_team_id,
                factors.home_team_id,
                factors.special_factor_description,
                factors.special_adjustment,
                factors.special_examples,
                factors.weather_factor_description,
                factors.weather_adjustment,
                factors.temperature_impact,
                factors.wind_impact,
                factors.precipitation_impact,
                factors.emotional_factor_description,
                factors.emotional_adjustment,
                factors.motivation_level,
                factors.momentum_direction,
                factors.total_adjustment,
                factors.confidence_level,
                factors.notes,
                factors.source,
            ),
            fetch=False,
        )

    def get_game_swe_factors(self, league_id: int, game_id: str) -> Optional[Dict]:
        """Get SWE factors for a game."""
        query = """
            SELECT * FROM game_swe_factors
            WHERE league_id = ? AND game_id = ?
        """
        results = self.db.execute_query(query, (league_id, game_id))
        return dict(results[0]) if results else None

    def get_swe_factors_by_week(
        self, league_id: int, season: int, week: int
    ) -> List[Dict]:
        """Get SWE factors for all games in a week."""
        query = """
            SELECT * FROM game_swe_factors
            WHERE league_id = ? AND season = ? AND week = ?
            ORDER BY game_id
        """
        results = self.db.execute_query(query, (league_id, season, week))
        return [dict(row) for row in results] if results else []

    def get_weather_impact(self, league_id: int, game_id: str) -> Optional[float]:
        """Get weather adjustment for a game."""
        query = """
            SELECT weather_adjustment FROM game_swe_factors
            WHERE league_id = ? AND game_id = ?
        """
        results = self.db.execute_query(query, (league_id, game_id))
        return results[0]["weather_adjustment"] if results else None

    def get_emotional_factors(
        self, league_id: int, team_id: int, week: int
    ) -> Optional[Dict]:
        """Get emotional factors for a team in a week."""
        query = """
            SELECT emotional_factor_description, emotional_adjustment,
                   motivation_level, momentum_direction
            FROM game_swe_factors
            WHERE league_id = ? AND week = ?
            AND (away_team_id = ? OR home_team_id = ?)
        """
        results = self.db.execute_query(query, (league_id, week, team_id, team_id))
        return dict(results[0]) if results else None

    # TEAM TRENDS
    # ============================================================

    def insert_team_trends(self, trends: TeamTrends) -> None:
        """Insert team trends."""
        query = """
            INSERT OR REPLACE INTO team_trends (
                league_id, team_id, season, week,
                streak_direction, streak_length, recent_form_pct,
                playoff_position, playoff_probability, divisional_rank,
                conference_rank, emotional_state, desperation_level,
                revenge_factor, rest_advantage, home_field_consistency,
                situational_strength, notes, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(
            query,
            (
                trends.league_id,
                trends.team_id,
                trends.season,
                trends.week,
                trends.streak_direction,
                trends.streak_length,
                trends.recent_form_pct,
                trends.playoff_position,
                trends.playoff_probability,
                trends.divisional_rank,
                trends.conference_rank,
                trends.emotional_state,
                trends.desperation_level,
                trends.revenge_factor,
                trends.rest_advantage,
                trends.home_field_consistency,
                trends.situational_strength,
                trends.notes,
                trends.source,
            ),
            fetch=False,
        )

    def get_team_trends(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> Optional[Dict]:
        """Get team trends for a specific week."""
        query = """
            SELECT * FROM team_trends
            WHERE league_id = ? AND team_id = ? AND season = ? AND week = ?
        """
        results = self.db.execute_query(query, (league_id, team_id, season, week))
        return dict(results[0]) if results else None

    def get_streak_info(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> Optional[Dict]:
        """Get streak information for a team."""
        query = """
            SELECT streak_direction, streak_length, recent_form_pct
            FROM team_trends
            WHERE league_id = ? AND team_id = ? AND season = ? AND week = ?
        """
        results = self.db.execute_query(query, (league_id, team_id, season, week))
        return dict(results[0]) if results else None

    def get_playoff_context(self, league_id: int, season: int, week: int) -> List[Dict]:
        """Get playoff context for all teams in a week."""
        query = """
            SELECT team_id, playoff_position, playoff_probability,
                   divisional_rank, conference_rank
            FROM team_trends
            WHERE league_id = ? AND season = ? AND week = ?
            ORDER BY playoff_probability DESC
        """
        results = self.db.execute_query(query, (league_id, season, week))
        return [dict(row) for row in results] if results else []

    def calculate_desperation(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> Optional[int]:
        """Get desperation level for a team (must-win detection)."""
        query = """
            SELECT desperation_level FROM team_trends
            WHERE league_id = ? AND team_id = ? AND season = ? AND week = ?
        """
        results = self.db.execute_query(query, (league_id, team_id, season, week))
        return results[0]["desperation_level"] if results else None

    def get_recent_form(
        self, league_id: int, team_id: int, season: int, week: int
    ) -> Optional[float]:
        """Get recent form percentage for a team."""
        query = """
            SELECT recent_form_pct FROM team_trends
            WHERE league_id = ? AND team_id = ? AND season = ? AND week = ?
        """
        results = self.db.execute_query(query, (league_id, team_id, season, week))
        return results[0]["recent_form_pct"] if results else None

    # ============================================================
    # BILLY WALTERS METHODOLOGY REFERENCE TABLES (Read-Only Lookups)
    # ============================================================

    def get_point_value_percentage(self, point_spread: float) -> Optional[float]:
        """Get value percentage for a point spread.

        From Billy Walters' Advanced Master Class - The Value of Points.
        Example: 3-point spread = 8% value, 7-point spread = 6% value.

        Args:
            point_spread: The point spread (1-21)

        Returns:
            Value percentage (e.g., 0.08 for 8%)
        """
        query = """
            SELECT value_percentage FROM lookup_point_values
            WHERE point_spread = ?
        """
        results = self.db.execute_query(query, (point_spread,))
        if results:
            return results[0]["value_percentage"] / 100.0
        return None

    def get_all_point_values(self) -> List[Dict]:
        """Get all point value data for reference."""
        query = "SELECT * FROM lookup_point_values ORDER BY point_spread"
        results = self.db.execute_query(query, ())
        return [dict(row) for row in results] if results else []

    def get_play_strength(self, edge_percentage: float) -> Optional[float]:
        """Get play strength (stars) for a calculated edge percentage.

        From Billy Walters' Strength of Play Guidelines - maps edge % to stars.
        Example: 7% edge = 1.0 star, 15% edge = 3.0 stars.

        Args:
            edge_percentage: Total calculated edge as percentage (e.g., 0.14 for 14%)

        Returns:
            Star rating (0.5 to 3.0), or None if below minimum
        """
        pct = edge_percentage * 100  # Convert to percentage

        query = """
            SELECT play_strength_stars FROM lookup_play_strength_guidelines
            WHERE min_percentage <= ?
            ORDER BY min_percentage DESC
            LIMIT 1
        """
        results = self.db.execute_query(query, (pct,))
        return results[0]["play_strength_stars"] if results else None

    def get_play_strength_table(self) -> List[Dict]:
        """Get complete play strength guidelines table."""
        query = """
            SELECT * FROM lookup_play_strength_guidelines
            ORDER BY min_percentage
        """
        results = self.db.execute_query(query, ())
        return [dict(row) for row in results] if results else []

    def get_odds_adjusted_spread(
        self, posted_spread: float, bet_price: str
    ) -> Optional[float]:
        """Get effective spread at 110/100 vig for given odds.

        From Billy Walters' odds adjustment table - accounts for different vig levels.
        Example: 3-point spread @ -120 = 3.25 effective spread.

        Args:
            posted_spread: The posted point spread
            bet_price: Odds string (e.g., '-115', '+105', '100')

        Returns:
            Effective implied spread at standard 110/100 vig
        """
        query = """
            SELECT implied_spread_at_110 FROM lookup_odds_to_spread_conversion
            WHERE posted_spread = ? AND bet_price_text = ?
        """
        results = self.db.execute_query(query, (posted_spread, bet_price))
        if results:
            return results[0]["implied_spread_at_110"]
        return None

    def get_odds_conversion_table(self) -> List[Dict]:
        """Get complete odds to spread conversion table."""
        query = """
            SELECT * FROM lookup_odds_to_spread_conversion
            ORDER BY posted_spread, bet_price_text
        """
        results = self.db.execute_query(query, ())
        return [dict(row) for row in results] if results else []

    def get_moneyline(self, point_spread: float) -> Optional[tuple]:
        """Get moneyline equivalents (favorite, dog) for a point spread.

        From Billy Walters' Moneyline Conversion Table.
        Example: 3-point spread = -170 favorite, +141 dog.

        Args:
            point_spread: The point spread

        Returns:
            Tuple of (favorite_moneyline, dog_moneyline), or None
        """
        query = """
            SELECT favorite_moneyline, dog_moneyline
            FROM lookup_moneyline_conversion
            WHERE point_spread = ?
        """
        results = self.db.execute_query(query, (point_spread,))
        if results:
            return (
                results[0]["favorite_moneyline"],
                results[0]["dog_moneyline"],
            )
        return None

    def get_moneyline_table(self) -> List[Dict]:
        """Get complete moneyline conversion table."""
        query = """
            SELECT * FROM lookup_moneyline_conversion
            ORDER BY point_spread
        """
        results = self.db.execute_query(query, ())
        return [dict(row) for row in results] if results else []

    def calculate_edge_percentage(self, spreads: List[float]) -> float:
        """Calculate cumulative edge percentage from point spreads.

        Adds up the value percentages for each spread point.
        Example: spreads [5, 6, 7] = 3% + 5% + 6% = 14%

        Args:
            spreads: List of point spreads to sum

        Returns:
            Total edge percentage (0-100)
        """
        total_pct = 0.0
        for spread in spreads:
            val = self.get_point_value_percentage(spread)
            if val is not None:
                total_pct += val * 100

        return total_pct

    def get_buying_power_cost(self, point_spread: float) -> Optional[str]:
        """Get the recommended max cost to buy a half point.

        From Billy Walters' Buying Points section.
        Most valuable for points 3 and 7.

        Args:
            point_spread: The point spread

        Returns:
            Cost description (e.g., '$20 off tie, $22 on to tie' for 3)
        """
        query = """
            SELECT dollar_value_buy_half_point FROM lookup_point_values
            WHERE point_spread = ?
        """
        results = self.db.execute_query(query, (point_spread,))
        if results:
            return results[0]["dollar_value_buy_half_point"]
        return None
