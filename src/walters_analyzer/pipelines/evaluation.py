from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from walters_analyzer.models.core import (
    AdjustmentBreakdown,
    Game,
    MatchupEvaluation,
    PowerRatingSnapshot,
    Team,
)

Factors = Dict[str, Any]


def evaluate_matchup(
    game: Game,
    home_team: Team,
    away_team: Team,
    factors: Factors,
    home_rating_snapshot: Optional[PowerRatingSnapshot] = None,
    away_rating_snapshot: Optional[PowerRatingSnapshot] = None,
) -> MatchupEvaluation:
    """Compute a MatchupEvaluation from teams + precomputed factor inputs.

    `factors` is expected to contain:
      - home_factor_points / away_factor_points  (S+W+E combined, in points)
      - market_spread                            (current line)
      - s_home / s_away                          (situational points)
      - w_home / w_away                          (weather points)
      - e_home / e_away                          (emotional/motivational points)
      - injury_home / injury_away                (injury impact points)
      - notes                                    (optional free-text/list)
    """

    # Create rating snapshots if not provided
    if not home_rating_snapshot:
        home_rating_snapshot = PowerRatingSnapshot(
            team_id=home_team.team_id,
            season=game.season,
            week=game.week,
            rating=home_team.power_rating or 0.0,
            source=home_team.rating_source or "custom",
            created_at=datetime.utcnow(),
        )
    
    if not away_rating_snapshot:
        away_rating_snapshot = PowerRatingSnapshot(
            team_id=away_team.team_id,
            season=game.season,
            week=game.week,
            rating=away_team.power_rating or 0.0,
            source=away_team.rating_source or "custom",
            created_at=datetime.utcnow(),
        )

    # Home field edge (default 2.5 points)
    home_field_edge = factors.get("home_field_edge", 2.5)
    
    # Base spread calculation: (home_rating - away_rating) + home_field_advantage
    base_spread = (home_rating_snapshot.rating - away_rating_snapshot.rating) + home_field_edge
    
    # Create adjustment breakdown
    # S/W/E factors are in "factor points" where 5 points = 1 spread point
    s_factor_conversion = 5.0  # Billy Walters: 5 S-factor points = 1 spread point
    
    adjustments = AdjustmentBreakdown(
        s_factor_points=(factors.get("s_home", 0.0) - factors.get("s_away", 0.0)) / s_factor_conversion,
        w_factor_points=(factors.get("w_home", 0.0) - factors.get("w_away", 0.0)) / s_factor_conversion,
        e_factor_points=(factors.get("e_home", 0.0) - factors.get("e_away", 0.0)) / s_factor_conversion,
        injury_points=(factors.get("injury_home", 0.0) - factors.get("injury_away", 0.0)),
    )
    
    # Effective spread after all adjustments
    effective_spread = base_spread + adjustments.total_adjustment
    
    # Market spread (current betting line)
    market_spread = factors["market_spread"]
    
    # Edge calculation in spread points
    edge_points = market_spread - effective_spread  # Positive = value on home team
    
    # Convert edge points to percentage (approximate conversion)
    # Using standard 52.38% breakeven for -110 odds
    # Each point of edge ≈ 2-3% win probability improvement
    edge_percent = abs(edge_points) * 2.5  # Conservative estimate
    
    # Override with explicit edge percentage if provided
    if "edge_percentage" in factors:
        edge_percent = factors["edge_percentage"]
    
    # Star rating based on edge percentage (Billy Walters system)
    # 0 stars: < 5.5% edge (no bet)
    # 1 star: 5.5-7% edge (0.5-1% bankroll)
    # 2 stars: 7-10% edge (1-2% bankroll)
    # 3 stars: > 10% edge (2-3% bankroll)
    if edge_percent < 5.5:
        star_rating = 0
    elif edge_percent < 7.0:
        star_rating = 1
    elif edge_percent < 10.0:
        star_rating = 2
    else:
        star_rating = 3
    
    # Override with explicit star rating if provided
    if "star_rating" in factors:
        star_rating = factors["star_rating"]
    
    # Build notes list
    notes = factors.get("notes", [])
    if isinstance(notes, str):
        notes = [notes]
    
    return MatchupEvaluation(
        game=game,
        home_team=home_team,
        away_team=away_team,
        home_rating=home_rating_snapshot,
        away_rating=away_rating_snapshot,
        home_field_edge=home_field_edge,
        base_spread=base_spread,
        adjustments=adjustments,
        market_spread=market_spread,
        effective_spread=effective_spread,
        edge_points=edge_points,
        edge_percent=edge_percent,
        star_rating=star_rating,
        notes=notes,
    )
