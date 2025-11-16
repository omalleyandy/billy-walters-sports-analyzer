"""
Integration tests for subagent outputs.

Tests each of the 6 subagent outputs against Billy Walters methodology requirements.
"""

import json
import pytest
from pathlib import Path
from datetime import date, datetime, timezone
from typing import Dict, List

# Add src to path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.season_calendar import get_nfl_week, get_week_date_range, League


@pytest.fixture
def current_week():
    """Get current NFL week."""
    week = get_nfl_week()
    if week is None:
        pytest.skip("NFL season not active")
    return week


@pytest.fixture
def data_dir():
    """Get data directory."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "data" / "current"


@pytest.fixture
def output_dir():
    """Get output directory."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "output" / "overtime" / "nfl" / "pregame"


class TestSubagent1Schedule:
    """Tests for Subagent 1: Schedule & Game Info."""

    def test_schedule_file_exists(self, current_week, data_dir):
        """Test schedule file exists."""
        file_path = data_dir / f"nfl_week_{current_week}_schedule.json"
        if not file_path.exists():
            pytest.skip(f"Schedule file not found: {file_path}")
        assert file_path.exists()

    def test_schedule_valid_json(self, current_week, data_dir):
        """Test schedule file is valid JSON."""
        file_path = data_dir / f"nfl_week_{current_week}_schedule.json"
        if not file_path.exists():
            pytest.skip(f"Schedule file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_schedule_structure(self, current_week, data_dir):
        """Test schedule has required structure."""
        file_path = data_dir / f"nfl_week_{current_week}_schedule.json"
        if not file_path.exists():
            pytest.skip(f"Schedule file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        required_keys = ["week", "season", "scraped_at", "games"]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"

        assert data["week"] == current_week
        assert isinstance(data["games"], list)

    def test_schedule_game_count(self, current_week, data_dir):
        """Test schedule has reasonable game count."""
        file_path = data_dir / f"nfl_week_{current_week}_schedule.json"
        if not file_path.exists():
            pytest.skip(f"Schedule file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        games = data["games"]
        assert 13 <= len(games) <= 16, f"Expected 13-16 games, got {len(games)}"

    def test_schedule_game_ids(self, current_week, data_dir):
        """Test all game_ids are valid and unique."""
        file_path = data_dir / f"nfl_week_{current_week}_schedule.json"
        if not file_path.exists():
            pytest.skip(f"Schedule file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        game_ids = []
        for game in data["games"]:
            assert "game_id" in game, "Game missing game_id"
            game_id = game["game_id"]
            assert game_id.startswith(f"NFL_2025_{current_week}_"), (
                f"Invalid game_id format: {game_id}"
            )
            assert game_id not in game_ids, f"Duplicate game_id: {game_id}"
            game_ids.append(game_id)

    def test_schedule_stadium_dome_flags(self, current_week, data_dir):
        """Test all stadiums have is_dome flag (critical for weather)."""
        file_path = data_dir / f"nfl_week_{current_week}_schedule.json"
        if not file_path.exists():
            pytest.skip(f"Schedule file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        for game in data["games"]:
            assert "stadium" in game, f"Game {game.get('game_id')} missing stadium"
            stadium = game["stadium"]
            assert isinstance(stadium, dict), "Stadium must be a dictionary"
            assert "is_dome" in stadium, (
                f"Stadium missing 'is_dome' flag (critical for weather)"
            )


class TestSubagent2BettingLines:
    """Tests for Subagent 2: Betting Lines."""

    def test_betting_lines_file_exists(self, current_week, output_dir):
        """Test betting lines CSV exists."""
        pattern = f"api_walters_week_{current_week}_*.csv"
        matching_files = list(output_dir.glob(pattern))
        if not matching_files:
            pytest.skip(f"No betting lines CSV found: {pattern}")
        assert len(matching_files) > 0

    def test_betting_lines_valid_csv(self, current_week, output_dir):
        """Test betting lines CSV is valid."""
        import pandas as pd

        pattern = f"api_walters_week_{current_week}_*.csv"
        matching_files = list(output_dir.glob(pattern))
        if not matching_files:
            pytest.skip(f"No betting lines CSV found: {pattern}")

        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_csv(latest_file)
        assert not df.empty

    def test_betting_lines_required_columns(self, current_week, output_dir):
        """Test betting lines have required columns."""
        import pandas as pd

        pattern = f"api_walters_week_{current_week}_*.csv"
        matching_files = list(output_dir.glob(pattern))
        if not matching_files:
            pytest.skip(f"No betting lines CSV found: {pattern}")

        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_csv(latest_file)

        required_columns = [
            "game_id",
            "away_team",
            "home_team",
            "spread",
            "total",
        ]
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

    def test_betting_lines_reasonable_values(self, current_week, output_dir):
        """Test betting lines have reasonable values."""
        import pandas as pd

        pattern = f"api_walters_week_{current_week}_*.csv"
        matching_files = list(output_dir.glob(pattern))
        if not matching_files:
            pytest.skip(f"No betting lines CSV found: {pattern}")

        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_csv(latest_file)

        # Validate spreads
        if "spread" in df.columns:
            invalid_spreads = df[(df["spread"] < -50) | (df["spread"] > 50)]
            assert invalid_spreads.empty, f"Unrealistic spreads: {len(invalid_spreads)}"

        # Validate totals
        if "total" in df.columns:
            invalid_totals = df[(df["total"] < 20) | (df["total"] > 100)]
            assert invalid_totals.empty, f"Unrealistic totals: {len(invalid_totals)}"


class TestSubagent3Weather:
    """Tests for Subagent 3: Weather Data."""

    def test_weather_file_exists(self, current_week, data_dir):
        """Test weather file exists."""
        file_path = data_dir / f"nfl_week_{current_week}_weather.json"
        if not file_path.exists():
            pytest.skip(f"Weather file not found: {file_path}")
        assert file_path.exists()

    def test_weather_valid_json(self, current_week, data_dir):
        """Test weather file is valid JSON."""
        file_path = data_dir / f"nfl_week_{current_week}_weather.json"
        if not file_path.exists():
            pytest.skip(f"Weather file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_weather_dome_stadiums_null(self, current_week, data_dir):
        """Test dome stadiums have weather: null."""
        file_path = data_dir / f"nfl_week_{current_week}_weather.json"
        if not file_path.exists():
            pytest.skip(f"Weather file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        for game in data.get("games", []):
            if game.get("is_dome"):
                assert game.get("weather") is None, (
                    f"Dome stadium {game.get('game_id')} should have weather: null"
                )

    def test_weather_outdoor_stadiums_have_data(self, current_week, data_dir):
        """Test outdoor stadiums have weather data."""
        file_path = data_dir / f"nfl_week_{current_week}_weather.json"
        if not file_path.exists():
            pytest.skip(f"Weather file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        for game in data.get("games", []):
            if "is_dome" in game and not game.get("is_dome"):
                assert "weather" in game and game["weather"] is not None, (
                    f"Outdoor stadium {game.get('game_id')} missing weather data"
                )


class TestSubagent4TeamSituational:
    """Tests for Subagent 4: Team Situational Analysis."""

    def test_team_situational_file_exists(self, current_week, data_dir):
        """Test team situational file exists."""
        file_path = data_dir / f"nfl_week_{current_week}_team_situational.json"
        if not file_path.exists():
            pytest.skip(f"Team situational file not found: {file_path}")
        assert file_path.exists()

    def test_power_ratings_range(self, current_week, data_dir):
        """Test power ratings are in valid range (70-100)."""
        file_path = data_dir / f"nfl_week_{current_week}_team_situational.json"
        if not file_path.exists():
            pytest.skip(f"Team situational file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        for team in data.get("teams", []):
            if "power_rating" in team and "overall" in team["power_rating"]:
                rating = team["power_rating"]["overall"]
                assert 70 <= rating <= 100, (
                    f"Power rating {rating} outside valid range (70-100)"
                )

    def test_s_factor_caps(self, current_week, data_dir):
        """Test S-factor adjustments within caps."""
        file_path = data_dir / f"nfl_week_{current_week}_team_situational.json"
        if not file_path.exists():
            pytest.skip(f"Team situational file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        # Check team-level S-factors
        for team in data.get("teams", []):
            if "situational_factors" in team:
                sf = team["situational_factors"]
                if "total_s_factor_adjustment" in sf:
                    adj = sf["total_s_factor_adjustment"]
                    assert abs(adj) <= 2.0, (
                        f"S-factor adjustment {adj} exceeds ±2.0 cap"
                    )

        # Check game-level net S-factors
        for game in data.get("games", []):
            if "matchup_situational" in game:
                ms = game["matchup_situational"]
                if "net_s_factor" in ms:
                    net = ms["net_s_factor"]
                    assert abs(net) <= 3.0, f"Net S-factor {net} exceeds ±3.0 cap"


class TestSubagent5PlayerSituational:
    """Tests for Subagent 5: Player Situational Analysis."""

    def test_player_situational_file_exists(self, current_week, data_dir):
        """Test player situational file exists."""
        file_path = data_dir / f"nfl_week_{current_week}_player_situational.json"
        if not file_path.exists():
            pytest.skip(f"Player situational file not found: {file_path}")
        assert file_path.exists()

    def test_player_impact_caps(self, current_week, data_dir):
        """Test cumulative player impact within caps."""
        file_path = data_dir / f"nfl_week_{current_week}_player_situational.json"
        if not file_path.exists():
            pytest.skip(f"Player situational file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        for team in data.get("teams", []):
            if "cumulative_player_impact" in team:
                impact = team["cumulative_player_impact"]
                assert abs(impact) <= 3.0, (
                    f"Cumulative player impact {impact} exceeds ±3.0 cap"
                )


class TestSubagent6Injuries:
    """Tests for Subagent 6: Injury Reports."""

    def test_injury_file_exists(self, current_week, data_dir):
        """Test injury file exists."""
        file_path = data_dir / f"nfl_week_{current_week}_injuries.json"
        if not file_path.exists():
            pytest.skip(f"Injury file not found: {file_path}")
        assert file_path.exists()

    def test_injury_status_values(self, current_week, data_dir):
        """Test injury status values are valid."""
        file_path = data_dir / f"nfl_week_{current_week}_injuries.json"
        if not file_path.exists():
            pytest.skip(f"Injury file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        valid_statuses = ["out", "doubtful", "questionable", "probable"]
        for team in data.get("teams", []):
            for injury in team.get("injuries", []):
                if "status" in injury:
                    status = injury["status"]
                    assert status in valid_statuses, f"Invalid injury status: {status}"

    def test_injury_impact_caps(self, current_week, data_dir):
        """Test injury impacts within caps."""
        file_path = data_dir / f"nfl_week_{current_week}_injuries.json"
        if not file_path.exists():
            pytest.skip(f"Injury file not found: {file_path}")

        with open(file_path) as f:
            data = json.load(f)

        # Check team-level injury impacts
        for team in data.get("teams", []):
            if "injury_summary" in team:
                summary = team["injury_summary"]
                if "cumulative_point_impact" in summary:
                    impact = summary["cumulative_point_impact"]
                    assert abs(impact) <= 3.0, (
                        f"Injury impact {impact} exceeds ±3.0 cap"
                    )

        # Check game-level net injury adjustments
        for game in data.get("games", []):
            if "injury_matchup" in game:
                im = game["injury_matchup"]
                if "net_injury_adjustment" in im:
                    net = im["net_injury_adjustment"]
                    assert abs(net) <= 5.0, (
                        f"Net injury adjustment {net} exceeds ±5.0 cap"
                    )


class TestCrossValidation:
    """Cross-validation tests across subagent outputs."""

    def test_game_ids_match_schedule(self, current_week, data_dir, output_dir):
        """Test game_ids match between schedule and betting lines."""
        # Load schedule
        schedule_path = data_dir / f"nfl_week_{current_week}_schedule.json"
        if not schedule_path.exists():
            pytest.skip("Schedule file not found")

        with open(schedule_path) as f:
            schedule_data = json.load(f)

        schedule_game_ids = {g["game_id"] for g in schedule_data.get("games", [])}

        # Load betting lines
        import pandas as pd

        pattern = f"api_walters_week_{current_week}_*.csv"
        matching_files = list(output_dir.glob(pattern))
        if not matching_files:
            pytest.skip("Betting lines file not found")

        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_csv(latest_file)
        odds_game_ids = set(df["game_id"].unique())

        # Should have substantial overlap (some games may be missing if not yet posted)
        overlap = schedule_game_ids & odds_game_ids
        assert len(overlap) >= len(schedule_game_ids) * 0.8, (
            f"Less than 80% game overlap: {len(overlap)}/{len(schedule_game_ids)}"
        )
