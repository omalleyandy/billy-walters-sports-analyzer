from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------------------


class BetType(str, Enum):
    """What kind of bet this recommendation refers to."""

    SPREAD = "spread"
    MONEYLINE = "moneyline"
    TOTAL = "total"
    NONE = "none"


class BetSide(str, Enum):
    """
    Primary side of the bet.

    For spreads/moneylines: home/away
    For totals: over/under
    """

    HOME = "home"
    AWAY = "away"
    OVER = "over"
    UNDER = "under"
    NONE = "none"


# ------------------------------------------------------------------------------
# Core entities
# ------------------------------------------------------------------------------


class Team(BaseModel):
    """
    Canonical NFL team representation for the analyzer.

    Backed by unified schedule + ratings (Massey/Sagarin/custom).
    """

    model_config = ConfigDict(extra="forbid")

    team_id: str = Field(
        ...,
        description="Canonical team identifier (e.g. DET, PHI, KC, or unified internal id).",
    )
    name: str = Field(..., description="Display name, e.g. 'Detroit Lions'.")
    conference: str | None = Field(
        None,
        description="Conference name, e.g. 'NFC' or 'AFC'.",
    )
    division: str | None = Field(
        None,
        description="Division name, e.g. 'NFC North'.",
    )

    # Optional "current" rating attached to the team for convenience
    power_rating: float | None = Field(
        None,
        description="Current power rating in spread points (0 = league average).",
    )
    rating_source: str | None = Field(
        None,
        description="Source of power rating, e.g. 'massey', 'sagarin', 'custom'.",
    )
    rating_as_of: datetime | None = Field(
        None,
        description="Timestamp when power_rating was last updated.",
    )


class Game(BaseModel):
    """
    Single NFL game instance for a given season/week.
    Mirrors the Entity.Game node in the knowledge graph.
    """

    model_config = ConfigDict(extra="forbid")

    game_id: str = Field(
        ...,
        description="Stable game identifier (e.g. ESPN/Overtime unified id).",
    )
    week: int = Field(..., ge=1, le=22, description="Week number (includes playoffs).")
    season: int = Field(..., ge=1990, description="Season year, e.g. 2025.")

    home_team_id: str = Field(..., description="Team.team_id for the home team.")
    away_team_id: str = Field(..., description="Team.team_id for the away team.")

    kickoff_datetime: datetime = Field(
        ...,
        description="Kickoff in UTC or clearly documented timezone.",
    )
    stadium: str | None = Field(None, description="Stadium name, if known.")
    surface_type: str | None = Field(
        None,
        description="Field surface type, e.g. 'turf', 'grass'.",
    )
    timezone: str | None = Field(
        None,
        description="IANA timezone for local kickoff, e.g. 'America/New_York'.",
    )


class PowerRatingSnapshot(BaseModel):
    """
    Snapshot of a single team's rating at a given moment.

    This is the main junction between external ratings (Massey etc.)
    and your internal pipeline.
    """

    model_config = ConfigDict(extra="forbid")

    team_id: str = Field(..., description="Team.team_id this rating applies to.")
    season: int = Field(..., ge=1990)
    week: int | None = Field(
        None,
        ge=0,
        description="Week number; 0 or None for pre-season / aggregate.",
    )

    rating: float = Field(
        ...,
        description="Power rating in spread points relative to league average.",
    )
    source: str = Field(
        "massey",
        description="Origin of the rating: 'massey', 'sagarin', 'custom', etc.",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this snapshot was generated/ingested.",
    )


# ------------------------------------------------------------------------------
# Matchup evaluation + edge calculation
# ------------------------------------------------------------------------------


class AdjustmentBreakdown(BaseModel):
    """
    Structured breakdown of S/W/E + injury adjustments in *spread points*.

    Positive values move the number toward the home team,
    negative values toward the away team.
    """

    model_config = ConfigDict(extra="forbid")

    s_factor_points: float = Field(
        0.0,
        description="Situational factors (rest, travel, schedule spots) in spread points.",
    )
    w_factor_points: float = Field(
        0.0,
        description="Weather factors (wind, temp, precipitation) in spread points.",
    )
    e_factor_points: float = Field(
        0.0,
        description="Emotional/motivational factors in spread points.",
    )
    injury_points: float = Field(
        0.0,
        description="Net injury impact differential (home minus away) in spread points.",
    )

    @property
    def total_adjustment(self) -> float:
        """Sum of all adjustments in spread points."""
        return (
            self.s_factor_points
            + self.w_factor_points
            + self.e_factor_points
            + self.injury_points
        )


class MatchupEvaluation(BaseModel):
    """
    Full evaluation of a single game: base spread, adjustments, edge, stars.

    This is the main object you'll pass into the LLM or write out as JSON
    for wk-card generation.
    """

    model_config = ConfigDict(extra="forbid")

    game: Game = Field(..., description="Game metadata.")
    home_team: Team = Field(..., description="Resolved home team.")
    away_team: Team = Field(..., description="Resolved away team.")

    home_rating: PowerRatingSnapshot = Field(
        ...,
        description="Power rating snapshot used for the home team.",
    )
    away_rating: PowerRatingSnapshot = Field(
        ...,
        description="Power rating snapshot used for the away team.",
    )

    # Core prediction mechanics
    home_field_edge: float = Field(
        2.5,
        description="Home field advantage in spread points (positive favors home).",
    )
    base_spread: float = Field(
        ...,
        description=(
            "Model spread before S/W/E/injury adjustments. "
            "Defined as (home_rating.rating - away_rating.rating) + home_field_edge."
        ),
    )

    adjustments: AdjustmentBreakdown = Field(
        default_factory=AdjustmentBreakdown,
        description="S/W/E + injury adjustments in spread points.",
    )

    # Market + effective number
    market_spread: float = Field(
        ...,
        description="Current market spread expressed as home minus away (e.g. -3.5 means home is -3.5).",
    )
    effective_spread: float = Field(
        ...,
        description=(
            "Final model number after adjustments. "
            "Typically base_spread + adjustments.total_adjustment."
        ),
    )

    edge_points: float = Field(
        ...,
        description="Difference between effective_spread and market_spread in spread points.",
    )
    edge_percent: float = Field(
        ...,
        ge=0.0,
        description="Estimated edge as a percentage (e.g. 6.5 = 6.5% edge).",
    )

    star_rating: int = Field(
        ...,
        ge=0,
        le=3,
        description="0-3 star rating following your Billy Walters rubric.",
    )

    notes: Sequence[str] | None = Field(
        None,
        description="Optional human-readable notes (weather flags, injury details, etc.).",
    )


# ------------------------------------------------------------------------------
# Bet recommendation (output of the pipeline)
# ALIGNED WITH: schemas/bet_recommendation.schema.json
# ------------------------------------------------------------------------------


class BetRecommendation(BaseModel):
    """
    Plain-language, stake-aware recommendation for a single game.

    Thin "view model" that can be rendered to markdown, JSON, or CLI.
    This model aligns exactly with bet_recommendation.schema.json
    
    Schema requirements:
    - recommendation_id: Unique identifier (required)
    - game_id: Reference to Game (required)
    - evaluation_id: Reference to MatchupEvaluation (optional)
    - bet_type: 'spread', 'moneyline', 'total', 'none' (required)
    - side: 'home', 'away', 'over', 'under', 'none' (required)
    - line: Spread/total number (optional)
    - price: American odds like -110 (optional)
    - edge_percentage: Edge as percent (required)
    - star_rating: 0-3 stars (required)
    - stake_fraction: 0-0.03 of bankroll (required)
    - bankroll: Dollar amount (optional)
    - is_play: Boolean, whether to actually bet (required)
    - rationale: Text explanation (required)
    """

    model_config = ConfigDict(extra="forbid")

    # Primary identifiers
    recommendation_id: str = Field(
        ...,
        description="Unique identifier for this recommendation (e.g. rec_game123_1234567890).",
    )
    game_id: str = Field(
        ...,
        description="Game.game_id this bet refers to.",
    )
    evaluation_id: str | None = Field(
        None,
        description="ID of the MatchupEvaluation that generated this recommendation.",
    )
    
    # Bet specification
    bet_type: BetType = Field(
        ...,
        description="Spread, moneyline, total, or none.",
    )
    side: BetSide = Field(
        ...,
        description="Home/away for spreads/ML; over/under for totals.",
    )

    # Market terms
    line: float | None = Field(
        None,
        description="Point spread or total line associated with this bet.",
    )
    price: int | None = Field(
        None,
        description="American odds (e.g. -110, +120). Optional but useful for Kelly.",
    )

    # Edge and staking (uses edge_percentage to match schema)
    edge_percentage: float = Field(
        ...,
        ge=0.0,
        description="Estimated edge in percent (from MatchupEvaluation.edge_percent).",
    )
    star_rating: int = Field(
        ...,
        ge=0,
        le=3,
        description="0-3 star rating summarizing conviction level.",
    )
    stake_fraction: float = Field(
        ...,
        ge=0.0,
        le=0.03,
        description="Fraction of bankroll to stake on this recommendation (max 3%).",
    )
    
    # Optional bankroll reference
    bankroll: float | None = Field(
        None,
        description="Bankroll amount this recommendation is based on.",
    )
    
    # Action flag
    is_play: bool = Field(
        ...,
        description="Whether this recommendation should be acted on (requires 5.5%+ edge).",
    )

    # Narrative
    rationale: str = Field(
        ...,
        description="Human-readable rationale summarizing why this edge exists.",
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this recommendation was generated.",
    )
    
    # =========================================================================
    # Backward compatibility properties
    # =========================================================================
    # These allow code written for the old API to still work
    
    @property
    def edge_percent(self) -> float:
        """
        Backward compatibility for edge_percent (uses edge_percentage internally).
        
        The schema uses 'edge_percentage', but some code may reference 'edge_percent'.
        This property makes both work transparently.
        """
        return self.edge_percentage
    
    @property
    def odds(self) -> int | None:
        """
        Backward compatibility for odds (uses price internally).
        
        The schema uses 'price', but some code may reference 'odds'.
        This property makes both work transparently.
        """
        return self.price


# ------------------------------------------------------------------------------
# Convenience exports
# ------------------------------------------------------------------------------


__all__ = [
    "BetRecommendation",
    "BetSide",
    "BetType",
    "Game",
    "MatchupEvaluation",
    "AdjustmentBreakdown",
    "PowerRatingSnapshot",
    "Team",
]
