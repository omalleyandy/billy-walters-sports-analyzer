import math

import pytest

from walters_analyzer.core import (
    BillyWaltersAnalyzer,
    GameInput,
    GameOdds,
    SpreadLine,
    TeamSnapshot,
    american_to_decimal,
    expected_value,
    implied_probability,
    kelly_fraction,
)
from walters_analyzer.core.point_analyzer import PointAnalyzer


def test_calculator_helpers():
    assert american_to_decimal(-110) == pytest.approx(1.9091, rel=1e-3)
    assert implied_probability(-110) == pytest.approx(0.5238, rel=1e-3)
    assert expected_value(0.55, -110) > 0
    assert kelly_fraction(0.55, -110, fraction=0.5) == pytest.approx(0.0275, rel=1e-2)


def test_point_analyzer_flags_key_numbers():
    analyzer = PointAnalyzer()
    alerts = analyzer.evaluate(projected_spread=-5.5, market_spread=-2.5)
    hit_numbers = {alert.number for alert in alerts}
    assert 3 in hit_numbers and 6 in hit_numbers


def test_billy_walters_analyzer_outputs_recommendation():
    matchup = GameInput(
        home_team=TeamSnapshot(
            name="Kansas City Chiefs",
            injuries=[
                {"player_name": "Patrick Mahomes", "position": "QB", "injury_status": "Questionable", "tier": "elite"}
            ],
        ),
        away_team=TeamSnapshot(
            name="Buffalo Bills",
            injuries=[
                {"player_name": "Josh Allen", "position": "QB", "injury_status": "Out", "tier": "elite"},
                {"player_name": "Stefon Diggs", "position": "WR", "injury_status": "Out", "tier": "elite"},
            ],
        ),
        odds=GameOdds(spread=SpreadLine(home_spread=-2.5, home_price=-110, away_price=-110)),
    )

    analyzer = BillyWaltersAnalyzer()
    analysis = analyzer.analyze(matchup)

    assert analysis.recommendation.team in {"Kansas City Chiefs", "Buffalo Bills"}
    assert analysis.recommendation.stake_pct >= 0
    assert math.isclose(abs(analysis.edge), abs(analysis.recommendation.edge))
