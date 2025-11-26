"""
NCAAF Edge Detector Tests

Unit and integration tests for the NCAAF edge detection system.
"""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from walters_analyzer.valuation.ncaaf_edge_detector import (
    NCAAFEdgeDetector,
    BettingEdge,
)
from walters_analyzer.valuation.ncaaf_situational_factors import (
    NCAAFSituationalFactors,
)
from walters_analyzer.valuation.ncaaf_injury_impacts import NCAAFInjuryImpacts


class TestNCAAFEdgeDetector:
    """Test main NCAAF edge detector"""

    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return NCAAFEdgeDetector()

    def test_home_field_bonus(self, detector):
        """Test NCAAF home field bonus is 3.5 points"""
        assert detector.HOME_FIELD_BONUS == 3.5

    def test_edge_threshold(self, detector):
        """Test edge threshold is 3.5 points"""
        assert detector.EDGE_THRESHOLD == 3.5

    def test_max_kelly(self, detector):
        """Test max Kelly fraction is 0.25"""
        assert detector.MAX_KELLY == 0.25

    @pytest.mark.asyncio
    async def test_calculate_power_rating_edge(self, detector):
        """Test power rating edge calculation with NCAAF formula"""
        # Ohio State (92.5) vs Michigan (94.2)
        # edge = 92.5 - 94.2 - 3.5 = -5.2 (Michigan favored by 5.2)
        edge = await detector._calculate_power_rating_edge(92.5, 94.2)
        assert abs(edge - (-5.2)) < 0.1

    @pytest.mark.asyncio
    async def test_calculate_power_rating_edge_away_favored(self, detector):
        """Test power rating when away team is favored"""
        # Away (90.0) vs Home (85.0)
        # edge = 90.0 - 85.0 - 3.5 = 1.5 (Away favored by 1.5)
        edge = await detector._calculate_power_rating_edge(90.0, 85.0)
        assert abs(edge - 1.5) < 0.1

    def test_edge_strength_classification(self, detector):
        """Test edge strength classification"""
        assert detector._classify_edge(8.0) == "very_strong"
        assert detector._classify_edge(6.0) == "strong"
        assert detector._classify_edge(4.0) == "medium"
        assert detector._classify_edge(2.0) == "weak"

    def test_indoor_stadium_detection(self, detector):
        """Test detection of indoor stadiums"""
        assert detector._is_indoor_stadium("Duke Blue Devils") is True
        assert detector._is_indoor_stadium("Syracuse Orange") is True
        assert detector._is_indoor_stadium("Miami Hurricanes") is True
        assert detector._is_indoor_stadium("Ohio State Buckeyes") is False
        assert detector._is_indoor_stadium("Michigan Wolverines") is False

    @pytest.mark.asyncio
    async def test_weather_adjustment_no_wind(self, detector):
        """Test weather adjustment with no wind"""
        with patch.object(
            detector.weather_client,
            "get_game_weather",
            return_value={
                "temperature": 65,
                "wind_speed": 5,
                "precipitation_percent": 0,
                "description": "Clear",
            },
        ):
            adjustment = await detector._calculate_weather_adjustment(
                {"home_team": "Ohio State"}
            )
            assert adjustment == 0.0

    @pytest.mark.asyncio
    async def test_weather_adjustment_high_wind(self, detector):
        """Test weather adjustment with high wind (NCAAF-specific)"""
        with patch.object(
            detector.weather_client,
            "get_game_weather",
            return_value={
                "temperature": 65,
                "wind_speed": 25,  # > 20 mph
                "precipitation_percent": 0,
                "description": "Windy",
            },
        ):
            adjustment = await detector._calculate_weather_adjustment(
                {"home_team": "Ohio State"}
            )
            assert adjustment == -6.0  # NCAAF-specific (vs NFL -5.0)

    @pytest.mark.asyncio
    async def test_weather_adjustment_cold_temperature(self, detector):
        """Test weather adjustment with cold temperature"""
        with patch.object(
            detector.weather_client,
            "get_game_weather",
            return_value={
                "temperature": 15,  # < 20°F
                "wind_speed": 5,
                "precipitation_percent": 0,
                "description": "Clear",
            },
        ):
            adjustment = await detector._calculate_weather_adjustment(
                {"home_team": "Ohio State"}
            )
            assert adjustment == -4.0

    @pytest.mark.asyncio
    async def test_weather_adjustment_heavy_snow(self, detector):
        """Test weather adjustment with heavy snow"""
        with patch.object(
            detector.weather_client,
            "get_game_weather",
            return_value={
                "temperature": 25,  # -2.0 for 25-32F
                "wind_speed": 5,
                "precipitation_percent": 70,
                "description": "Heavy Snow",
            },
        ):
            adjustment = await detector._calculate_weather_adjustment(
                {"home_team": "Ohio State"}
            )
            # -2.0 (temp) + -5.0 (snow) = -7.0
            assert adjustment == -7.0


class TestNCAAFSituationalFactors:
    """Test NCAAF situational factors"""

    @pytest.fixture
    def sfactor(self):
        """Create situational factors instance"""
        return NCAAFSituationalFactors()

    def test_rest_advantage_extra(self, sfactor):
        """Test extra rest advantage"""
        adjustment = sfactor._calculate_rest_advantage(9, 7)
        assert adjustment == 1.5

    def test_rest_advantage_short(self, sfactor):
        """Test short rest disadvantage"""
        adjustment = sfactor._calculate_rest_advantage(5, 7)
        assert adjustment == 2.0  # -short_rest becomes positive

    def test_rest_advantage_equal(self, sfactor):
        """Test equal rest"""
        adjustment = sfactor._calculate_rest_advantage(7, 7)
        assert adjustment == 0.0

    def test_travel_long_distance(self, sfactor):
        """Test long distance travel penalty"""
        adjustment = sfactor._calculate_travel_penalty(2000)
        assert adjustment == -1.5

    def test_travel_medium_distance(self, sfactor):
        """Test medium distance travel penalty"""
        adjustment = sfactor._calculate_travel_penalty(800)
        assert adjustment == -0.8

    def test_travel_short_distance(self, sfactor):
        """Test short distance travel penalty"""
        adjustment = sfactor._calculate_travel_penalty(300)
        assert adjustment == -0.3

    def test_travel_home_state(self, sfactor):
        """Test home state travel (no penalty)"""
        adjustment = sfactor._calculate_travel_penalty(50)
        assert adjustment == 0.0

    def test_rivalry_detection(self, sfactor):
        """Test rivalry game detection"""
        assert sfactor._is_rivalry_game("Ohio State", "Michigan") is True
        assert sfactor._is_rivalry_game("Michigan", "Ohio State") is True
        assert sfactor._is_rivalry_game("Alabama", "Auburn") is True
        assert sfactor._is_rivalry_game("Ohio State", "Penn State") is True

    @pytest.mark.asyncio
    async def test_emotional_adjustment_playoff(self, sfactor):
        """Test emotional adjustment for playoff implications"""
        game = {"playoff_implications": True}
        adjustment = await sfactor.emotional_adjustment(game, 13)
        assert adjustment == 1.5

    @pytest.mark.asyncio
    async def test_emotional_adjustment_elimination(self, sfactor):
        """Test emotional adjustment for elimination game"""
        game = {"elimination_game": True}
        adjustment = await sfactor.emotional_adjustment(game, 13)
        assert adjustment == 2.0

    def test_conference_strength_adjustment(self, sfactor):
        """Test conference strength adjustment"""
        # SEC (0.0) vs MAC (-0.5)
        adjustment = sfactor.get_conference_strength_adjustment("SEC", "MAC")
        assert adjustment == 0.5


class TestNCAAFInjuryImpacts:
    """Test NCAAF injury impacts"""

    @pytest.fixture
    def injury_calc(self):
        """Create injury calculator instance"""
        return NCAAFInjuryImpacts()

    def test_qb_elite_value(self, injury_calc):
        """Test elite QB injury value is 5.0 (vs NFL 4.5)"""
        assert injury_calc.POSITION_VALUES["QB"]["elite"] == 5.0

    def test_rb_elite_value(self, injury_calc):
        """Test elite RB injury value"""
        assert injury_calc.POSITION_VALUES["RB"]["elite"] == 3.5

    def test_wr_elite_value(self, injury_calc):
        """Test elite WR injury value"""
        assert injury_calc.POSITION_VALUES["WR"]["elite"] == 2.5

    @pytest.mark.asyncio
    async def test_calculate_impact_no_injuries(self, injury_calc):
        """Test impact calculation with no injuries"""
        impact = await injury_calc.calculate_impact("Ohio State", "Michigan", {})
        assert impact == 0.0

    @pytest.mark.asyncio
    async def test_calculate_impact_away_injured(self, injury_calc):
        """Test impact calculation when away team is injured"""
        injuries = {
            "Ohio State": [
                {
                    "player": "QB1",
                    "position": "QB",
                    "status": "Out",
                }
            ]
        }
        impact = await injury_calc.calculate_impact("Ohio State", "Michigan", injuries)
        # Positive impact = away team hurt more (favors home)
        assert impact > 0.0

    @pytest.mark.asyncio
    async def test_calculate_impact_home_injured(self, injury_calc):
        """Test impact calculation when home team is injured"""
        injuries = {
            "Michigan": [
                {
                    "player": "QB1",
                    "position": "QB",
                    "status": "Out",
                }
            ]
        }
        impact = await injury_calc.calculate_impact("Ohio State", "Michigan", injuries)
        # Negative impact = home team hurt (favors away)
        assert impact < 0.0

    def test_severity_classification_season(self, injury_calc):
        """Test severity classification for season-ending injury"""
        severity = injury_calc._classify_severity("Out for Season")
        assert severity == "out_for_season"

    def test_severity_classification_weeks(self, injury_calc):
        """Test severity classification for week-based injury"""
        assert injury_calc._classify_severity("Out 2 weeks") == "out_2_weeks"
        assert injury_calc._classify_severity("Out 4 weeks") == "out_4_weeks"

    def test_severity_classification_questionable(self, injury_calc):
        """Test severity classification for questionable status"""
        assert injury_calc._classify_severity("Questionable") == "questionable"
        assert injury_calc._classify_severity("Day-to-day") == "questionable"

    def test_team_severity_classification(self, injury_calc):
        """Test overall team severity classification"""
        assert injury_calc._classify_team_severity(12.0) == "CRITICAL"
        assert injury_calc._classify_team_severity(7.0) == "MAJOR"
        assert injury_calc._classify_team_severity(3.0) == "MODERATE"
        assert injury_calc._classify_team_severity(1.0) == "MINOR"
        assert injury_calc._classify_team_severity(0.1) == "NEGLIGIBLE"


class TestBettingEdgeDataclass:
    """Test BettingEdge dataclass"""

    def test_edge_creation(self):
        """Test BettingEdge creation with required fields"""
        edge = BettingEdge(
            game_id="114561232",
            matchup="Ohio State @ Michigan",
            week=13,
            game_time="2025-11-29T15:30:00Z",
            away_team="Ohio State",
            home_team="Michigan",
            away_rating=92.5,
            home_rating=94.2,
            predicted_spread=4.2,
            market_spread=-2.5,
            market_total=52.0,
            edge_points=6.7,
            recommended_bet="away",
            kelly_fraction=0.22,
            confidence_score=67.0,
            timestamp="2025-11-23T05:07:25.113446",
        )

        assert edge.game_id == "114561232"
        assert edge.matchup == "Ohio State @ Michigan"
        assert edge.week == 13
        assert edge.edge_points == 6.7
        assert edge.recommended_bet == "away"

    def test_edge_asdict_conversion(self):
        """Test BettingEdge conversion to dict for JSON serialization"""
        edge = BettingEdge(
            game_id="114561232",
            matchup="Ohio State @ Michigan",
            week=13,
            game_time="2025-11-29T15:30:00Z",
            away_team="Ohio State",
            home_team="Michigan",
            away_rating=92.5,
            home_rating=94.2,
            predicted_spread=4.2,
            market_spread=-2.5,
            market_total=52.0,
            edge_points=6.7,
            recommended_bet="away",
            kelly_fraction=0.22,
            confidence_score=67.0,
            timestamp="2025-11-23T05:07:25.113446",
        )

        from dataclasses import asdict

        edge_dict = asdict(edge)

        assert isinstance(edge_dict, dict)
        assert edge_dict["game_id"] == "114561232"
        assert edge_dict["edge_points"] == 6.7


# Integration tests
class TestNCAAFEdgeDetectorIntegration:
    """Integration tests with mock data"""

    @pytest.fixture
    def detector(self):
        """Create detector with mocked dependencies"""
        return NCAAFEdgeDetector()

    @pytest.mark.asyncio
    async def test_analyze_game_basic(self, detector):
        """Test analyzing a single game"""
        game = {
            "game_id": "114561232",
            "matchup": "Ohio State @ Michigan",
            "away_team": "Ohio State",
            "home_team": "Michigan",
            "game_time": "2025-11-29T15:30:00Z",
            "away_rest_days": 7,
            "home_rest_days": 7,
            "travel_distance_miles": 200,
        }

        ratings = {
            "Ohio State": 92.5,
            "Michigan": 94.2,
        }

        odds = {
            "114561232": {
                "game_id": "114561232",
                "spread": -2.5,
                "total": 52.0,
            }
        }

        injuries = {}

        edge = await detector._analyze_game(game, ratings, odds, injuries, 13)

        assert edge is not None
        assert edge.game_id == "114561232"
        assert edge.away_team == "Ohio State"
        assert edge.home_team == "Michigan"
        assert edge.away_rating == 92.5
        assert edge.home_rating == 94.2


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
