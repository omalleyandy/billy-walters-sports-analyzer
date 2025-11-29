"""
Raw Data Models

Pydantic models for all raw data tables from the data collection pipeline.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GameSchedule(BaseModel):
    """Game schedule model."""

    game_id: str
    league_id: int
    season: int
    week: int
    away_team_id: int
    home_team_id: int
    game_datetime: str
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    is_neutral_site: bool = False
    is_indoor: bool = False
    status: Optional[str] = None
    source: Optional[str] = None


class GameResult(BaseModel):
    """Game result and box score model."""

    game_id: str
    league_id: int
    away_team_id: int
    home_team_id: int
    away_score: Optional[int] = None
    home_score: Optional[int] = None
    away_ats: Optional[bool] = None
    home_ats: Optional[bool] = None
    over_under: Optional[bool] = None
    attendance: Optional[int] = None
    status: Optional[str] = None
    source: Optional[str] = None


class TeamStats(BaseModel):
    """Team statistics model (offensive, defensive, special teams)."""

    league_id: int
    team_id: int
    season: int
    week: Optional[int] = None

    # Offensive stats
    points_for: Optional[float] = None
    passing_yards: Optional[float] = None
    rushing_yards: Optional[float] = None
    total_yards: Optional[float] = None
    first_downs: Optional[int] = None
    third_down_conversion_pct: Optional[float] = None
    fourth_down_conversion_pct: Optional[float] = None
    turnovers: Optional[int] = None
    fumbles: Optional[int] = None
    interceptions: Optional[int] = None
    penalties: Optional[int] = None
    penalty_yards: Optional[int] = None
    red_zone_efficiency: Optional[float] = None
    scoring_efficiency: Optional[float] = None

    # Defensive stats
    points_against: Optional[float] = None
    passing_yards_allowed: Optional[float] = None
    rushing_yards_allowed: Optional[float] = None
    total_yards_allowed: Optional[float] = None
    sacks: Optional[int] = None
    interceptions_forced: Optional[int] = None
    fumbles_forced: Optional[int] = None
    defensive_touchdowns: Optional[int] = None
    red_zone_defense: Optional[float] = None

    # Special teams
    field_goal_pct: Optional[float] = None
    extra_point_pct: Optional[float] = None
    punting_avg: Optional[float] = None
    kickoff_return_avg: Optional[float] = None
    punt_return_avg: Optional[float] = None

    # Game metrics
    time_of_possession: Optional[float] = None
    games_played: Optional[int] = None
    games_won: Optional[int] = None
    games_lost: Optional[int] = None

    source: Optional[str] = None


class PlayerStats(BaseModel):
    """Player statistics model."""

    league_id: int
    team_id: int
    player_name: str
    player_id: Optional[str] = None
    position: Optional[str] = None
    season: int
    week: Optional[int] = None

    # Passing
    pass_attempts: Optional[int] = None
    completions: Optional[int] = None
    passing_yards: Optional[int] = None
    passing_touchdowns: Optional[int] = None
    interceptions: Optional[int] = None

    # Rushing
    rush_attempts: Optional[int] = None
    rushing_yards: Optional[int] = None
    rushing_touchdowns: Optional[int] = None

    # Receiving
    receptions: Optional[int] = None
    receiving_yards: Optional[int] = None
    receiving_touchdowns: Optional[int] = None

    # Defense
    tackles: Optional[int] = None
    sacks: Optional[float] = None
    pass_breakups: Optional[int] = None
    forced_fumbles: Optional[int] = None

    # Kicking
    field_goals_made: Optional[int] = None
    field_goals_attempted: Optional[int] = None
    extra_points_made: Optional[int] = None

    source: Optional[str] = None


class TeamStandings(BaseModel):
    """Team standings and records model."""

    league_id: int
    team_id: int
    season: int
    week: Optional[int] = None

    wins: Optional[int] = None
    losses: Optional[int] = None
    ties: Optional[int] = None
    win_percentage: Optional[float] = None
    points_for: Optional[int] = None
    points_against: Optional[int] = None
    point_differential: Optional[int] = None
    division_rank: Optional[int] = None
    conference_rank: Optional[int] = None
    overall_rank: Optional[int] = None

    source: Optional[str] = None


class PowerRating(BaseModel):
    """Power rating model (Massey and other sources)."""

    league_id: int
    team_id: int
    season: int
    week: Optional[int] = None

    # Overall rating
    overall_rating: Optional[float] = None
    offensive_rating: Optional[float] = None
    defensive_rating: Optional[float] = None
    special_teams_rating: Optional[float] = None

    # Advanced metrics
    strength_of_schedule: Optional[float] = None
    strength_of_victory: Optional[float] = None
    strength_of_loss: Optional[float] = None
    recent_form_rating: Optional[float] = None

    # Adjustments
    injury_adjustment: Optional[float] = None
    rest_adjustment: Optional[float] = None
    momentum_adjustment: Optional[float] = None

    # Massey specific
    massey_rating: Optional[float] = None
    massey_rank: Optional[int] = None

    source: Optional[str] = None
    rating_date: Optional[str] = None


class BettingOdds(BaseModel):
    """Betting odds from multiple sources model."""

    game_id: str
    league_id: int
    week: Optional[int] = None

    away_team_id: Optional[int] = None
    home_team_id: Optional[int] = None
    spread: Optional[float] = None
    spread_odds: Optional[float] = None
    total: Optional[float] = None
    total_odds: Optional[float] = None
    away_moneyline: Optional[int] = None
    home_moneyline: Optional[int] = None

    line_time: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None

    source: Optional[str] = None
    sportsbook: Optional[str] = None


class SharpMoneySignal(BaseModel):
    """Sharp money signal model (Action Network)."""

    game_id: str
    league_id: int
    week: Optional[int] = None

    away_team_id: Optional[int] = None
    home_team_id: Optional[int] = None

    # Spread analysis
    spread_value: Optional[float] = None
    spread_side: Optional[str] = None
    spread_tickets_pct: Optional[float] = None
    spread_money_pct: Optional[float] = None
    spread_divergence: Optional[float] = None

    # Total analysis
    total_value: Optional[float] = None
    total_over_tickets_pct: Optional[float] = None
    total_over_money_pct: Optional[float] = None
    total_divergence: Optional[float] = None

    # Moneyline analysis
    away_tickets_pct: Optional[float] = None
    away_money_pct: Optional[float] = None
    home_tickets_pct: Optional[float] = None
    home_money_pct: Optional[float] = None
    moneyline_divergence: Optional[float] = None

    # Interpretation
    sharp_signal_strength: Optional[float] = None
    signal_direction: Optional[str] = None
    confidence_level: Optional[float] = None

    source: Optional[str] = None


class WeatherData(BaseModel):
    """Weather data model."""

    game_id: str
    league_id: int
    week: Optional[int] = None

    game_datetime: Optional[str] = None
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None

    # Current conditions
    temperature_f: Optional[float] = None
    temperature_c: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    wind_direction: Optional[str] = None
    precipitation_in: Optional[float] = None
    humidity_pct: Optional[float] = None
    cloud_cover_pct: Optional[float] = None

    # Advanced metrics
    feels_like_temp_f: Optional[float] = None
    uv_index: Optional[float] = None
    visibility_mi: Optional[float] = None

    # Conditions
    conditions: Optional[str] = None
    weather_category: Optional[str] = None

    source: Optional[str] = None
    forecast_time: Optional[str] = None


class InjuryReport(BaseModel):
    """Injury report model."""

    league_id: int
    team_id: int
    player_name: str
    player_id: Optional[str] = None
    position: Optional[str] = None
    season: int
    week: Optional[int] = None

    injury_status: Optional[str] = None
    body_part: Optional[str] = None
    severity: Optional[str] = None
    expected_return: Optional[str] = None
    out_weeks: Optional[int] = None

    is_starter: bool = False
    impact_rating: Optional[float] = None

    source: Optional[str] = None
    reported_date: Optional[str] = None


class NewsArticle(BaseModel):
    """News article model."""

    league_id: int
    team_id: Optional[int] = None

    title: str
    content: Optional[str] = None
    article_url: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None

    category: Optional[str] = None
    sentiment: Optional[str] = None
    impact_level: Optional[str] = None

    relevant_teams: Optional[str] = None
    relevant_keywords: Optional[str] = None

    published_at: Optional[str] = None


class CollectionSession(BaseModel):
    """Data collection session metadata model."""

    league_id: int
    season: Optional[int] = None
    week: Optional[int] = None

    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    sources_attempted: Optional[str] = None
    sources_successful: Optional[str] = None
    sources_failed: Optional[str] = None

    games_collected: Optional[int] = None
    stats_records_collected: Optional[int] = None
    odds_records_collected: Optional[int] = None
    weather_records_collected: Optional[int] = None
    injuries_collected: Optional[int] = None

    status: Optional[str] = None
    error_messages: Optional[str] = None
