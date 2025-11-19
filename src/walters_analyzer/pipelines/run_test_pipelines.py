from __future__ import annotations

from datetime import datetime, timezone

from walters_analyzer.models.core import (
    AdjustmentBreakdown,
    BetRecommendation,
    Game,
    MatchupEvaluation,
    PowerRatingSnapshot,
    Team,
)


def run_pipeline() -> None:
    """
    Synthetic end-to-end test of the core models and pipeline wiring.
    """
    # ---------------------------------------------------------------
    # 1. Fake data — this simulates what your scrapers will produce.
    # ---------------------------------------------------------------
    now_utc = datetime.now(timezone.utc)

    home = Team(
        team_id="DET",
        name="Detroit Lions",
        conference="NFC",
        division="NFC North",
        power_rating=6.1,
        rating_source="massey",
        rating_as_of=now_utc,
    )

    away = Team(
        team_id="PHI",
        name="Philadelphia Eagles",
        conference="NFC",
        division="NFC East",
        power_rating=3.5,
        rating_source="massey",
        rating_as_of=now_utc,
    )

    game = Game(
        game_id="2025-WK11-DET-PHI",
        week=11,
        season=2025,
        home_team_id="DET",
        away_team_id="PHI",
        kickoff_datetime=datetime(2025, 11, 23, 18, 25, tzinfo=timezone.utc),
        stadium="Ford Field",
        surface_type="turf",
        timezone="America/Detroit",
    )

    home_rating = PowerRatingSnapshot(
        team_id="DET",
        season=2025,
        week=11,
        rating=home.power_rating,
        source="massey",
    )

    away_rating = PowerRatingSnapshot(
        team_id="PHI",
        season=2025,
        week=11,
        rating=away.power_rating,
        source="massey",
    )

    # ---------------------------------------------------------------
    # 2. Base model calculation (Billy Walters pipeline skeleton).
    # ---------------------------------------------------------------
    home_field_edge = 2.5
    base_spread = (home_rating.rating - away_rating.rating) + home_field_edge

    adjustments = AdjustmentBreakdown(
        s_factor_points=0.25,  # small rest advantage
        w_factor_points=0.0,  # dome stadium
        e_factor_points=0.0,  # neutral motivation
        injury_points=-0.5,  # small QB/OL downgrade
    )

    effective_spread = base_spread + adjustments.total_adjustment

    # For testing assume the market spread is DET -2.0
    market_spread = -2.0

    edge_points = effective_spread - market_spread
    # Simple fake conversion to a "percent edge" just for sanity checks.
    edge_percent = abs(edge_points) * 0.9
    star_rating = 1 if edge_percent > 3 else 0

    evaluation = MatchupEvaluation(
        game=game,
        home_team=home,
        away_team=away,
        home_rating=home_rating,
        away_rating=away_rating,
        home_field_edge=home_field_edge,
        base_spread=base_spread,
        adjustments=adjustments,
        market_spread=market_spread,
        effective_spread=effective_spread,
        edge_points=edge_points,
        edge_percent=edge_percent,
        star_rating=star_rating,
        notes=["Test run only."],
    )

    # ---------------------------------------------------------------
    # 3. Convert evaluation → BetRecommendation
    # ---------------------------------------------------------------
    recommendation = BetRecommendation(
        game_id=game.game_id,
        bet_type="spread",
        side="home",
        line=market_spread,
        odds=-110,
        edge_percent=edge_percent,
        star_rating=star_rating,
        stake_fraction=0.02,
        rationale=(
            "Synthetic test recommendation to confirm the models and pipeline wiring."
        ),
    )

    # ---------------------------------------------------------------
    # 4. Print everything (LLM-ready JSON)
    # ---------------------------------------------------------------
    print("\n=== MATCHUP EVALUATION ===")
    print(evaluation.model_dump_json(indent=2))

    print("\n=== BET RECOMMENDATION ===")
    print(recommendation.model_dump_json(indent=2))


if __name__ == "__main__":
    run_pipeline()
