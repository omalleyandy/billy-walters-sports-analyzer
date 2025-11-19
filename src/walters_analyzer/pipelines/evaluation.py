from __future__ import annotations

from typing import Any, Dict

from walters_analyzer.models.core import Game, MatchupEvaluation, Team

Factors = Dict[str, Any]


def evaluate_matchup(
    game: Game,
    home_team: Team,
    away_team: Team,
    factors: Factors,
) -> MatchupEvaluation:
    """Compute a MatchupEvaluation from teams + precomputed factor inputs.

    `factors` is expected to contain:
      - home_factor_points / away_factor_points  (S+W+E combined, in points)
      - market_spread                            (current line)
      - effective_spread                         (model-adjusted spread)
      - edge_percentage                          (converted percent edge)
      - star_rating                              (discrete 0–3 stars)
      - s_home / s_away                          (situational points)
      - w_home / w_away                          (weather points)
      - e_home / e_away                          (emotional/motivational points)
      - notes                                    (optional free-text/list)
    """

    # Base difference from raw power ratings (before S/W/E adjustments).
    base_power_diff = (home_team.power_rating or 0.0) - (away_team.power_rating or 0.0)

    # Factor points are expressed in "S/W/E points" where 5 points = 1 spread pt.
    adjusted_power_home = (home_team.power_rating or 0.0) + (
        factors["home_factor_points"] / 5.0
    )
    adjusted_power_away = (away_team.power_rating or 0.0) + (
        factors["away_factor_points"] / 5.0
    )

    predicted_spread = adjusted_power_home - adjusted_power_away
    market_spread = factors["market_spread"]
    effective_spread = factors["effective_spread"]
    edge_percentage = factors["edge_percentage"]
    star_rating = factors["star_rating"]

    # Threshold is aligned with your edge table (e.g. ≥ 5.5% = playable).
    qualifies_as_play = edge_percentage >= 5.5

    return MatchupEvaluation(
        evaluation_id=f"EVAL-{game.game_id}",
        game_id=game.game_id,
        model_version="bwsa-1.0",
        home_team_id=game.home_team_id,
        away_team_id=game.away_team_id,
        base_power_diff=base_power_diff,
        s_factor_points_home=factors["s_home"],
        s_factor_points_away=factors["s_away"],
        w_factor_points_home=factors["w_home"],
        w_factor_points_away=factors["w_away"],
        e_factor_points_home=factors["e_home"],
        e_factor_points_away=factors["e_away"],
        adjusted_power_home=adjusted_power_home,
        adjusted_power_away=adjusted_power_away,
        predicted_spread=predicted_spread,
        market_spread=market_spread,
        effective_spread=effective_spread,
        edge_percentage=edge_percentage,
        star_rating=star_rating,
        qualifies_as_play=qualifies_as_play,
        notes=factors.get("notes"),
    )
