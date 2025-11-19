from typing import Dict, Any


def evaluate_matchup(game: Game,
                     home_team: Team,
                     away_team: Team,
                     factors: Dict[str, Any]) -> MatchupEvaluation:
    # factors holds s/w/e and market info from your engine
    base_power_diff = (home_team.power_rating or 0.0) - (away_team.power_rating or 0.0)

    adjusted_power_home = (home_team.power_rating or 0.0) + factors["home_factor_points"] / 5.0
    adjusted_power_away = (away_team.power_rating or 0.0) + factors["away_factor_points"] / 5.0

    predicted_spread = adjusted_power_home - adjusted_power_away
    market_spread = factors["market_spread"]
    effective_spread = factors["effective_spread"]
    edge_percentage = factors["edge_percentage"]
    star_rating = factors["star_rating"]
    qualifies_as_play = edge_percentage >= 5.5  # from your edge threshold table

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