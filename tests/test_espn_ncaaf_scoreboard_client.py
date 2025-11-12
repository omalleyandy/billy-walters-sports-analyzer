"""
Tests for ESPN NCAAF Scoreboard Client

Tests cover:
- API client initialization and connection
- Scoreboard fetching with various parameters
- Game summary, play-by-play, and win probability fetching
- Data verification and validation
- File I/O operations
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.data.espn_ncaaf_scoreboard_client import ESPNNCAAFScoreboardClient

# Configure pytest-anyio to only use asyncio
pytestmark = pytest.mark.anyio(backends=["asyncio"])


@pytest.fixture
def client():
    """Create test client."""
    return ESPNNCAAFScoreboardClient(timeout=10, max_retries=2)


@pytest.fixture
def mock_scoreboard_response():
    """Mock scoreboard API response."""
    return {
        "leagues": [{"id": "23", "name": "NCAA Football"}],
        "season": {"year": 2025, "type": 2, "slug": "regular-season"},
        "week": {"number": 12},
        "events": [
            {
                "id": "401628532",
                "name": "Ohio State at Michigan",
                "date": "2025-11-23T17:00Z",
                "status": {
                    "type": {
                        "state": "pre",
                        "detail": "Sat, Nov 23 at 12:00 PM EST",
                    }
                },
                "competitions": [
                    {
                        "competitors": [
                            {
                                "team": {"id": "130", "displayName": "Ohio State"},
                                "homeAway": "away",
                                "score": "0",
                                "curatedRank": {"current": 2},
                                "records": [{"type": "total", "summary": "10-0"}],
                            },
                            {
                                "team": {"id": "130", "displayName": "Michigan"},
                                "homeAway": "home",
                                "score": "0",
                                "curatedRank": {"current": 5},
                                "records": [{"type": "total", "summary": "9-1"}],
                            },
                        ],
                        "odds": [
                            {
                                "provider": {"name": "Caesars"},
                                "spread": -3.5,
                                "overUnder": 45.5,
                                "details": "OSU -3.5",
                            }
                        ],
                        "venue": {
                            "fullName": "Michigan Stadium",
                            "address": {"city": "Ann Arbor", "state": "MI"},
                            "indoor": False,
                        },
                        "weather": {
                            "temperature": 35,
                            "displayValue": "Partly Cloudy",
                        },
                    }
                ],
            }
        ],
    }


@pytest.fixture
def mock_game_summary():
    """Mock game summary response."""
    return {
        "boxscore": {
            "teams": [
                {
                    "team": {"id": "130", "displayName": "Ohio State"},
                    "statistics": [
                        {"name": "totalYards", "displayValue": "425"},
                        {"name": "passingYards", "displayValue": "280"},
                    ],
                }
            ]
        },
        "drives": {
            "previous": [
                {
                    "id": "1",
                    "team": {"id": "130"},
                    "start": {
                        "period": {"number": 1},
                        "clock": {"displayValue": "15:00"},
                    },
                    "end": {
                        "period": {"number": 1},
                        "clock": {"displayValue": "12:30"},
                    },
                    "offensivePlays": 8,
                    "yards": 75,
                    "result": "TD",
                }
            ]
        },
        "scoringPlays": [
            {
                "id": "1",
                "team": {"id": "130"},
                "period": {"number": 1},
                "clock": {"displayValue": "12:30"},
                "scoreValue": 7,
                "text": "15 yd pass from C.J. Stroud",
                "type": {"text": "Touchdown"},
            }
        ],
    }


@pytest.mark.anyio
async def test_client_initialization(client):
    """Test client initializes correctly."""
    assert client.timeout == 10
    assert client.max_retries == 2
    assert client.client is None


@pytest.mark.anyio
async def test_client_connect(client):
    """Test client connection."""
    await client.connect()
    assert client.client is not None
    await client.close()


@pytest.mark.anyio
async def test_client_context_manager(client):
    """Test client as context manager."""
    async with client as c:
        assert c.client is not None
    assert client.client is None


@pytest.mark.anyio
async def test_get_scoreboard_with_week(client, mock_scoreboard_response):
    """Test fetching scoreboard by week."""
    await client.connect()

    with patch.object(client, "_make_request", return_value=mock_scoreboard_response):
        scoreboard = await client.get_scoreboard(week=12)

        assert scoreboard["week"]["number"] == 12
        assert len(scoreboard["events"]) == 1
        assert scoreboard["events"][0]["id"] == "401628532"

    await client.close()


@pytest.mark.anyio
async def test_get_scoreboard_with_date(client, mock_scoreboard_response):
    """Test fetching scoreboard by date."""
    await client.connect()

    with patch.object(client, "_make_request", return_value=mock_scoreboard_response):
        scoreboard = await client.get_scoreboard(date="20251123")

        assert "events" in scoreboard
        assert len(scoreboard["events"]) == 1

    await client.close()


@pytest.mark.anyio
async def test_get_scoreboard_with_groups(client, mock_scoreboard_response):
    """Test fetching scoreboard with custom groups."""
    await client.connect()

    with patch.object(client, "_make_request", return_value=mock_scoreboard_response):
        scoreboard = await client.get_scoreboard(week=12, groups=80, limit=400)

        assert "events" in scoreboard

    await client.close()


@pytest.mark.anyio
async def test_get_game_summary(client, mock_game_summary):
    """Test fetching game summary."""
    await client.connect()

    with patch.object(client, "_make_request", return_value=mock_game_summary):
        summary = await client.get_game_summary("401628532")

        assert "boxscore" in summary
        assert "drives" in summary
        assert "scoringPlays" in summary

    await client.close()


@pytest.mark.anyio
async def test_get_play_by_play(client):
    """Test fetching play-by-play data."""
    await client.connect()

    mock_plays = {
        "items": [
            {
                "id": "1",
                "text": "1st and 10",
                "type": {"text": "Rush"},
            }
        ]
    }

    with patch.object(client, "_make_request", return_value=mock_plays):
        plays = await client.get_play_by_play("401628532")

        assert "items" in plays

    await client.close()


@pytest.mark.anyio
async def test_get_win_probability(client):
    """Test fetching win probability."""
    await client.connect()

    mock_win_prob = {
        "homeWinPercentage": 65.5,
        "awayWinPercentage": 34.5,
    }

    with patch.object(client, "_make_request", return_value=mock_win_prob):
        win_prob = await client.get_win_probability("401628532")

        assert "homeWinPercentage" in win_prob

    await client.close()


@pytest.mark.anyio
async def test_get_complete_game_data(client, mock_game_summary):
    """Test fetching complete game data."""
    await client.connect()

    mock_plays = {"items": []}
    mock_win_prob = {"homeWinPercentage": 50.0}

    with (
        patch.object(
            client,
            "get_game_summary",
            return_value=mock_game_summary,
        ),
        patch.object(
            client,
            "get_play_by_play",
            return_value=mock_plays,
        ),
        patch.object(
            client,
            "get_win_probability",
            return_value=mock_win_prob,
        ),
    ):
        game_data = await client.get_complete_game_data("401628532")

        assert game_data["event_id"] == "401628532"
        assert "summary" in game_data
        assert "plays" in game_data
        assert "win_probability" in game_data
        assert "fetched_at" in game_data

    await client.close()


def test_verify_scoreboard_response(client, mock_scoreboard_response):
    """Test scoreboard verification."""
    verification = client.verify_scoreboard_response(mock_scoreboard_response)

    assert verification["valid"] is True
    assert verification["event_count"] == 1
    assert verification["season_type"] == 2
    assert verification["week_number"] == 12
    assert "Caesars" in verification["providers"]


def test_verify_scoreboard_missing_season(client):
    """Test verification with missing season data."""
    bad_scoreboard = {"events": []}

    verification = client.verify_scoreboard_response(bad_scoreboard)

    assert verification["valid"] is False
    assert "Missing season information" in verification["errors"]


def test_verify_scoreboard_postponed_games(client, mock_scoreboard_response):
    """Test verification with postponed games."""
    # Add status to competition level
    mock_scoreboard_response["events"][0]["competitions"][0]["status"] = {
        "type": {"state": "postponed"}
    }

    verification = client.verify_scoreboard_response(mock_scoreboard_response)

    assert "1 postponed games" in verification["warnings"]


@pytest.mark.anyio
async def test_save_scoreboard_raw(client, mock_scoreboard_response, tmp_path):
    """Test saving raw scoreboard JSON."""
    output_dir = tmp_path / "raw"

    filepath = await client.save_scoreboard_raw(
        mock_scoreboard_response,
        output_dir,
        date="20251123",
    )

    assert filepath.exists()
    assert filepath.suffix == ".json"

    with open(filepath) as f:
        saved_data = json.load(f)

    assert saved_data["week"]["number"] == 12


@pytest.mark.anyio
async def test_save_game_data_raw(client, tmp_path):
    """Test saving complete game data."""
    output_dir = tmp_path / "raw"

    game_data = {
        "event_id": "401628532",
        "summary": {"boxscore": {}},
        "plays": {"items": []},
        "win_probability": {},
        "fetched_at": datetime.now().isoformat(),
    }

    filepath = await client.save_game_data_raw(
        game_data,
        output_dir,
        date="20251123",
    )

    assert filepath.exists()
    assert "401628532" in str(filepath)

    with open(filepath) as f:
        saved_data = json.load(f)

    assert saved_data["event_id"] == "401628532"


@pytest.mark.anyio
async def test_request_retry_logic(client):
    """Test request retry with exponential backoff."""
    await client.connect()

    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json = Mock(return_value={"success": True})

    # Mock httpx.HTTPError instead of generic Exception
    from httpx import HTTPError

    # First call fails, second succeeds
    client.client.get = AsyncMock(
        side_effect=[HTTPError("Network error"), mock_response]
    )

    result = await client._make_request("https://test.com")

    assert result == {"success": True}
    assert client.client.get.call_count == 2

    await client.close()


@pytest.mark.anyio
async def test_request_max_retries_exceeded(client):
    """Test request fails after max retries."""
    await client.connect()

    from httpx import HTTPError

    client.client.get = AsyncMock(side_effect=HTTPError("Network error"))

    with pytest.raises(HTTPError):
        await client._make_request("https://test.com")

    assert client.client.get.call_count == client.max_retries

    await client.close()


@pytest.mark.anyio
async def test_request_without_connection(client):
    """Test request fails if client not connected."""
    with pytest.raises(RuntimeError, match="Client not connected"):
        await client._make_request("https://test.com")
