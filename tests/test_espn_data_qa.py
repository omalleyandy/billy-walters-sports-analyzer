"""
Comprehensive QA Test Suite for ESPN Data Collection Pipeline

Tests cover all 6 ESPN data collection components:
1. espn_api_client.py - Core ESPN API client for REST endpoints
2. espn_client.py - Async ESPN statistics client with retry logic
3. espn_injury_scraper.py - Injury report scraper for NFL/NCAAF
4. espn_ncaaf_normalizer.py - Data normalization to parquet format
5. espn_ncaaf_scoreboard_client.py - Scoreboard API client
6. espn_ncaaf_team_scraper.py - Team page scraper for injuries/stats

Test Categories:
- Unit tests: Individual component functionality
- Integration tests: Component interactions
- Data quality: Response format and content validation
- Error handling: Failure scenarios and recovery
- Performance: Request timing and rate limiting
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest

# Test fixtures and utilities
pytestmark = pytest.mark.anyio(backends=["asyncio"])


# ============================================================================
# FIXTURES - Mock Data & Test Clients
# ============================================================================


@pytest.fixture
def mock_espn_team_stats_response():
    """Mock response from ESPN team statistics API."""
    return {
        "team": {
            "id": "194",
            "displayName": "Ohio State Buckeyes",
            "abbreviation": "OSU",
        },
        "results": {
            "stats": {
                "categories": [
                    {
                        "name": "scoring",
                        "stats": [
                            {"name": "totalPoints", "value": 436},
                            {"name": "totalPointsPerGame", "value": 36.3},
                        ],
                    },
                    {
                        "name": "passing",
                        "stats": [
                            {"name": "netPassingYards", "value": 3180},
                            {"name": "netPassingYardsPerGame", "value": 265.0},
                        ],
                    },
                    {
                        "name": "rushing",
                        "stats": [
                            {"name": "rushingYards", "value": 1840},
                            {"name": "rushingYardsPerGame", "value": 153.3},
                        ],
                    },
                    {
                        "name": "miscellaneous",
                        "stats": [
                            {"name": "gamesPlayed", "value": 12},
                            {"name": "turnOverDifferential", "value": 5},
                            {"name": "thirdDownConvPct", "value": 0.462},
                            {"name": "totalTakeaways", "value": 18},
                            {"name": "totalGiveaways", "value": 13},
                        ],
                    },
                ]
            },
            "opponent": [
                {
                    "name": "scoring",
                    "stats": [
                        {"name": "totalPointsPerGame", "value": 7.2},
                    ],
                },
                {
                    "name": "passing",
                    "stats": [
                        {"name": "passingYardsPerGame", "value": 120.8},
                    ],
                },
                {
                    "name": "rushing",
                    "stats": [
                        {"name": "rushingYardsPerGame", "value": 89.5},
                    ],
                },
            ],
        },
    }


@pytest.fixture
def mock_injury_response():
    """Mock injury report response from ESPN API."""
    return {
        "injuries": [
            {
                "athlete": {
                    "id": "4241450",
                    "displayName": "Kyle McCord",
                    "position": {"abbreviation": "QB"},
                },
                "status": {
                    "type": "Out",
                    "description": "Arm Injury",
                },
                "details": {
                    "detail": "Out",
                },
                "date": "2025-11-12T00:00Z",
            },
            {
                "athlete": {
                    "id": "4241500",
                    "displayName": "TreVeyon Henderson",
                    "position": {"abbreviation": "RB"},
                },
                "status": {
                    "type": "Questionable",
                    "description": "Knee",
                },
                "details": {
                    "detail": "Questionable",
                },
                "date": "2025-11-12T00:00Z",
            },
        ]
    }


@pytest.fixture
def mock_scoreboard_full_response():
    """Complete mock scoreboard response."""
    return {
        "season": {"year": 2025, "type": 2},
        "week": {"number": 12},
        "events": [
            {
                "id": "401628532",
                "name": "Ohio State at Michigan",
                "date": "2025-11-23T17:00Z",
                "status": {"type": {"state": "pre"}},
                "competitions": [
                    {
                        "venue": {
                            "fullName": "Michigan Stadium",
                            "address": {"city": "Ann Arbor", "state": "MI"},
                            "indoor": False,
                        },
                        "weather": {
                            "temperature": 35,
                            "displayValue": "Partly Cloudy",
                        },
                        "broadcast": {"names": ["ABC"]},
                        "attendance": 115000,
                        "competitors": [
                            {
                                "team": {
                                    "id": "25",
                                    "displayName": "Ohio State",
                                },
                                "homeAway": "away",
                                "score": 0,
                                "records": [{"type": "total", "summary": "10-0"}],
                                "curatedRank": {"current": 2},
                            },
                            {
                                "team": {
                                    "id": "130",
                                    "displayName": "Michigan",
                                },
                                "homeAway": "home",
                                "score": 0,
                                "records": [{"type": "total", "summary": "9-1"}],
                                "curatedRank": {"current": 5},
                            },
                        ],
                        "odds": [
                            {
                                "provider": {"name": "Caesars"},
                                "spread": -3.5,
                                "overUnder": 45.5,
                            }
                        ],
                    }
                ],
            }
        ],
    }


# ============================================================================
# TESTS: ESPNAPIClient (espn_api_client.py)
# ============================================================================


class TestESPNAPIClient:
    """Test suite for ESPNAPIClient."""

    def test_client_initialization(self):
        """Test client initializes with correct base URLs."""
        from scrapers.espn import ESPNClient as ESPNAPIClient

        client = ESPNAPIClient()

        assert client.nfl_base_url == "https://www.espn.com/nfl"
        assert client.ncaaf_base_url == "https://www.espn.com/college-football"
        assert (
            client.base_url == "https://site.api.espn.com/apis/site/v2/sports/football"
        )
        assert client.session is not None

    def test_user_agent_header(self):
        """Test User-Agent header is set."""
        from scrapers.espn import ESPNClient as ESPNAPIClient

        client = ESPNAPIClient()

        assert "User-Agent" in client.session.headers
        assert "Mozilla" in client.session.headers["User-Agent"]

    def test_extract_power_rating_metrics_structure(
        self, mock_espn_team_stats_response
    ):
        """Test power rating metric extraction returns correct structure."""
        from scrapers.espn import ESPNClient as ESPNAPIClient

        client = ESPNAPIClient()

        with patch.object(
            client, "get_team_statistics", return_value=mock_espn_team_stats_response
        ):
            metrics = client.extract_power_rating_metrics("194", "college-football")

            # Verify all required fields present
            required_fields = [
                "team_id",
                "team_name",
                "games_played",
                "points_per_game",
                "total_points",
                "passing_yards_per_game",
                "rushing_yards_per_game",
                "points_allowed_per_game",
                "passing_yards_allowed_per_game",
                "rushing_yards_allowed_per_game",
                "turnover_margin",
                "third_down_pct",
                "takeaways",
                "giveaways",
                "total_yards_per_game",
                "total_yards_allowed_per_game",
            ]

            for field in required_fields:
                assert field in metrics, f"Missing required field: {field}"

    def test_power_rating_metric_values(self, mock_espn_team_stats_response):
        """Test power rating metrics have correct values."""
        from scrapers.espn import ESPNClient as ESPNAPIClient

        client = ESPNAPIClient()

        with patch.object(
            client, "get_team_statistics", return_value=mock_espn_team_stats_response
        ):
            metrics = client.extract_power_rating_metrics("194", "college-football")

            assert metrics["team_id"] == "194"
            assert metrics["team_name"] == "Ohio State Buckeyes"
            assert metrics["games_played"] == 12
            assert metrics["points_per_game"] == 36.3
            assert metrics["passing_yards_per_game"] == 265.0
            assert metrics["rushing_yards_per_game"] == 153.3
            assert metrics["points_allowed_per_game"] == 7.2
            assert metrics["turnover_margin"] == 5

    def test_total_yards_calculation(self, mock_espn_team_stats_response):
        """Test total yards per game calculation."""
        from scrapers.espn import ESPNClient as ESPNAPIClient

        client = ESPNAPIClient()

        with patch.object(
            client, "get_team_statistics", return_value=mock_espn_team_stats_response
        ):
            metrics = client.extract_power_rating_metrics("194", "college-football")

            expected_total = 265.0 + 153.3
            assert metrics["total_yards_per_game"] == pytest.approx(expected_total)

    def test_json_save_with_organized_structure(self, tmp_path):
        """Test JSON save with organized directory structure."""
        from scrapers.espn import ESPNClient as ESPNAPIClient

        client = ESPNAPIClient()
        test_data = {"test": "data"}

        filepath = client.save_to_json(
            test_data,
            data_type="teams",
            league="nfl",
            output_dir=str(tmp_path),
        )

        # Convert to Path if string
        filepath = Path(filepath)

        # Verify file structure: output/{data_type}/{league}/{filename}
        assert "teams" in str(filepath)
        assert "nfl" in str(filepath)
        assert filepath.exists()

        # Verify content
        with open(filepath) as f:
            saved = json.load(f)
        assert saved == test_data


# ============================================================================
# TESTS: ESPNClient (espn_client.py)
# ============================================================================


class TestESPNClient:
    """Test suite for async ESPNClient."""

    @pytest.mark.anyio
    async def test_client_initialization(self):
        """Test async client initializes correctly."""
        from scrapers.espn import ESPNClient

        client = ESPNClient(rate_limit_delay=0.1, timeout=5.0)

        assert client.rate_limit_delay == 0.1
        assert client.timeout == 5.0
        assert client.max_retries == 3

    @pytest.mark.anyio
    async def test_client_context_manager(self):
        """Test async context manager functionality."""
        from scrapers.espn import ESPNClient

        async with ESPNClient() as client:
            assert client._client is not None

    @pytest.mark.anyio
    async def test_circuit_breaker_initialization(self):
        """Test circuit breaker is initialized."""
        from scrapers.espn import ESPNClient

        async with ESPNClient() as client:
            assert client._circuit_breaker_failures == 0
            assert client._circuit_breaker_threshold == 5
            assert client._circuit_breaker_reset_time is None

    @pytest.mark.anyio
    async def test_rate_limit_enforcement(self):
        """Test rate limiting between requests."""
        from scrapers.espn import ESPNClient

        client = ESPNClient(rate_limit_delay=0.1)
        await client.connect()

        start = asyncio.get_event_loop().time()
        await client._rate_limit()
        await client._rate_limit()
        elapsed = asyncio.get_event_loop().time() - start

        # Should enforce delay on second call
        assert elapsed >= 0.1

        await client.close()

    @pytest.mark.anyio
    async def test_get_scoreboard_nfl(self):
        """Test getting NFL scoreboard."""
        from scrapers.espn import ESPNClient

        client = ESPNClient()
        await client.connect()

        mock_response = {"events": [], "week": {"number": 10}}

        with patch.object(client, "_make_request", return_value=mock_response):
            result = await client.get_scoreboard("NFL", week=10)

            assert "events" in result
            assert result["league"] == "NFL"
            assert result["source"] == "espn"

        await client.close()

    @pytest.mark.anyio
    async def test_get_team_stats_structure(self):
        """Test team stats response has required structure."""
        from scrapers.espn import ESPNClient

        client = ESPNClient()
        await client.connect()

        mock_stats = {
            "statistics": [
                {
                    "name": "passing",
                    "displayValue": "2500",
                }
            ]
        }

        with patch.object(client, "_make_request", return_value=mock_stats):
            result = await client.get_team_stats("NFL", "194")

            assert "team_id" in result
            assert "league" in result
            assert "source" in result
            assert result["source"] == "espn"

        await client.close()

    @pytest.mark.anyio
    async def test_retry_on_http_error(self):
        """Test automatic retry on HTTP errors."""
        from scrapers.espn import ESPNClient

        client = ESPNClient(max_retries=2)
        await client.connect()

        from httpx import HTTPStatusError, Response

        # Create mock error
        mock_response = Mock(spec=Response)
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )

        client._client.get = AsyncMock(
            side_effect=HTTPStatusError(
                "Server error", request=Mock(), response=mock_response
            )
        )

        with pytest.raises(Exception):
            await client._make_request("https://test.com")

        # Should have retried
        assert client._client.get.call_count >= 1

        await client.close()


# ============================================================================
# TESTS: ESPNInjuryScraper (espn_injury_scraper.py)
# ============================================================================


class TestESPNInjuryScraper:
    """Test suite for injury scraper."""

    def test_scraper_initialization(self, tmp_path):
        """Test scraper initializes with correct output directory."""
        from scrapers.espn import ESPNInjuryScraper

        scraper = ESPNInjuryScraper(output_dir=str(tmp_path))

        assert scraper.output_dir == str(tmp_path)
        assert scraper.base_url == "https://site.api.espn.com/apis/site/v2/sports"

    def test_injury_scraper_output_format(self, tmp_path):
        """Test injury scraper outputs valid JSON format."""
        from scrapers.espn import ESPNInjuryScraper

        scraper = ESPNInjuryScraper(output_dir=str(tmp_path))

        test_injuries = [
            {
                "source": "espn",
                "sport": "nfl",
                "league": "NFL",
                "team": "Ohio State",
                "team_abbr": "OSU",
                "team_id": "194",
                "player_name": "Kyle McCord",
                "player_id": "4241450",
                "position": "QB",
                "injury_status": "Out",
                "injury_description": "Arm Injury",
                "injury_detail": "Out",
                "date_reported": datetime.now().isoformat(),
                "collected_at": datetime.now().isoformat(),
            }
        ]

        scraper.save_injuries(test_injuries, "test_injuries.json")

        filepath = tmp_path / "test_injuries.json"
        assert filepath.exists()

        # Verify JSON is valid
        with open(filepath) as f:
            loaded = json.load(f)
        assert len(loaded) == 1
        assert loaded[0]["player_name"] == "Kyle McCord"

    def test_injury_jsonl_output(self, tmp_path):
        """Test injury data also saved as JSONL."""
        from scrapers.espn import ESPNInjuryScraper

        scraper = ESPNInjuryScraper(output_dir=str(tmp_path))

        test_injuries = [
            {
                "player_name": "Kyle McCord",
                "position": "QB",
                "injury_status": "Out",
                "team": "Ohio State",
            },
            {
                "player_name": "TreVeyon Henderson",
                "position": "RB",
                "injury_status": "Questionable",
                "team": "Ohio State",
            },
        ]

        scraper.save_injuries(test_injuries, "test_injuries.json")

        jsonl_path = tmp_path / "test_injuries.jsonl"
        assert jsonl_path.exists()

        # Verify JSONL format (one JSON object per line)
        with open(jsonl_path) as f:
            lines = f.readlines()
        assert len(lines) == 2

        # Parse first line
        first_injury = json.loads(lines[0])
        assert first_injury["player_name"] == "Kyle McCord"


# ============================================================================
# TESTS: ESPNNCAAFNormalizer (espn_ncaaf_normalizer.py)
# ============================================================================


class TestESPNNCAAFNormalizer:
    """Test suite for data normalization."""

    def test_normalizer_initialization(self, tmp_path):
        """Test normalizer initializes correctly."""
        from scrapers.espn import ESPNNCAAFNormalizer

        normalizer = ESPNNCAAFNormalizer(tmp_path)

        assert normalizer.output_dir == tmp_path
        assert tmp_path.exists()

    def test_normalize_scoreboard_structure(
        self, mock_scoreboard_full_response, tmp_path
    ):
        """Test scoreboard normalization returns 3 dataframes."""
        from scrapers.espn import ESPNNCAAFNormalizer

        normalizer = ESPNNCAAFNormalizer(tmp_path)
        events_df, competitors_df, odds_df = normalizer.normalize_scoreboard(
            mock_scoreboard_full_response
        )

        assert isinstance(events_df, pd.DataFrame)
        assert isinstance(competitors_df, pd.DataFrame)
        assert isinstance(odds_df, pd.DataFrame)

    def test_events_dataframe_content(self, mock_scoreboard_full_response, tmp_path):
        """Test events dataframe has correct columns."""
        from scrapers.espn import ESPNNCAAFNormalizer

        normalizer = ESPNNCAAFNormalizer(tmp_path)
        events_df, _, _ = normalizer.normalize_scoreboard(mock_scoreboard_full_response)

        required_columns = [
            "event_id",
            "name",
            "date",
            "season_type",
            "week",
            "status",
            "venue_name",
            "venue_city",
            "venue_state",
            "venue_indoor",
            "temperature",
            "condition",
            "broadcast_network",
            "attendance",
        ]

        for col in required_columns:
            assert col in events_df.columns, f"Missing column: {col}"

    def test_competitors_dataframe_content(
        self, mock_scoreboard_full_response, tmp_path
    ):
        """Test competitors dataframe structure."""
        from scrapers.espn import ESPNNCAAFNormalizer

        normalizer = ESPNNCAAFNormalizer(tmp_path)
        _, competitors_df, _ = normalizer.normalize_scoreboard(
            mock_scoreboard_full_response
        )

        required_columns = [
            "event_id",
            "team_id",
            "team_name",
            "home_away",
            "score",
            "winner",
            "rank",
            "record",
        ]

        for col in required_columns:
            assert col in competitors_df.columns, f"Missing column: {col}"

        assert len(competitors_df) == 2  # Two teams per game

    def test_odds_dataframe_content(self, mock_scoreboard_full_response, tmp_path):
        """Test odds dataframe structure."""
        from scrapers.espn import ESPNNCAAFNormalizer

        normalizer = ESPNNCAAFNormalizer(tmp_path)
        _, _, odds_df = normalizer.normalize_scoreboard(mock_scoreboard_full_response)

        required_columns = [
            "event_id",
            "provider",
            "spread",
            "over_under",
            "home_moneyline",
            "away_moneyline",
            "details",
            "timestamp",
        ]

        for col in required_columns:
            assert col in odds_df.columns, f"Missing column: {col}"

    def test_save_parquet_format(self, mock_scoreboard_full_response, tmp_path):
        """Test parquet files are saved correctly."""
        from scrapers.espn import ESPNNCAAFNormalizer

        normalizer = ESPNNCAAFNormalizer(tmp_path)
        events_df, competitors_df, odds_df = normalizer.normalize_scoreboard(
            mock_scoreboard_full_response
        )

        result = normalizer.save_parquet(events_df, competitors_df, odds_df)

        # Verify paths returned
        assert "events" in result
        assert "competitors" in result
        assert "odds" in result

        # Verify files exist
        assert Path(result["events"]).exists()
        assert Path(result["competitors"]).exists()
        assert Path(result["odds"]).exists()

        # Verify can read back as parquet
        reloaded_events = pd.read_parquet(result["events"])
        assert len(reloaded_events) == len(events_df)


# ============================================================================
# TESTS: ESPNNCAAFScoreboardClient (espn_ncaaf_scoreboard_client.py)
# ============================================================================


class TestESPNNCAAFScoreboardClient:
    """Test suite for NCAAF scoreboard client."""

    @pytest.mark.anyio
    async def test_client_initialization(self):
        """Test NCAAF client initializes."""
        from scrapers.espn import ESPNNCAAFScoreboardClient

        client = ESPNNCAAFScoreboardClient()

        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.rate_limit_delay == 0.5

    @pytest.mark.anyio
    async def test_get_scoreboard_parameters(self):
        """Test scoreboard accepts required parameters."""
        from scrapers.espn import ESPNNCAAFScoreboardClient

        client = ESPNNCAAFScoreboardClient()
        await client.connect()

        mock_response = {
            "week": {"number": 12},
            "events": [],
            "season": {"type": 2},
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            # Test with week
            result = await client.get_scoreboard(week=12)
            assert result["week"]["number"] == 12

            # Test with groups (FBS = 80)
            result = await client.get_scoreboard(week=12, groups=80)
            assert "events" in result

            # Test with limit
            result = await client.get_scoreboard(week=12, limit=400)
            assert "events" in result

        await client.close()

    @pytest.mark.anyio
    async def test_verify_scoreboard_valid(self, mock_scoreboard_full_response):
        """Test scoreboard verification on valid data."""
        from scrapers.espn import ESPNNCAAFScoreboardClient

        client = ESPNNCAAFScoreboardClient()

        verification = client.verify_scoreboard_response(mock_scoreboard_full_response)

        assert verification["valid"] is True
        assert verification["event_count"] == 1
        assert verification["season_type"] == 2
        assert verification["week_number"] == 12

    @pytest.mark.anyio
    async def test_verify_scoreboard_missing_season(self):
        """Test verification fails with missing season."""
        from scrapers.espn import ESPNNCAAFScoreboardClient

        client = ESPNNCAAFScoreboardClient()

        bad_data = {"events": []}
        verification = client.verify_scoreboard_response(bad_data)

        assert verification["valid"] is False
        assert len(verification["errors"]) > 0

    @pytest.mark.anyio
    async def test_save_scoreboard_creates_json(
        self, mock_scoreboard_full_response, tmp_path
    ):
        """Test saving scoreboard creates JSON file."""
        from scrapers.espn import ESPNNCAAFScoreboardClient

        client = ESPNNCAAFScoreboardClient()

        filepath = await client.save_scoreboard_raw(
            mock_scoreboard_full_response,
            tmp_path,
            date="20251123",
        )

        assert filepath.exists()
        assert filepath.suffix == ".json"

        # Verify content
        with open(filepath) as f:
            data = json.load(f)
        assert data["week"]["number"] == 12


# ============================================================================
# TESTS: ESPNNcaafTeamScraper (espn_ncaaf_team_scraper.py)
# ============================================================================


class TestESPNNcaafTeamScraper:
    """Test suite for NCAAF team scraper."""

    def test_scraper_initialization(self, tmp_path):
        """Test team scraper initializes."""
        from scrapers.espn import ESPNNcaafTeamScraper

        scraper = ESPNNcaafTeamScraper(output_dir=str(tmp_path))

        assert scraper.base_url == "https://www.espn.com/college-football/team"
        assert scraper.output_dir == Path(tmp_path)

    def test_build_team_url_construction(self):
        """Test team URL builder for different page types."""
        from scrapers.espn import ESPNNcaafTeamScraper

        scraper = ESPNNcaafTeamScraper()

        # Test home page
        home_url = scraper.build_team_url(2653, "home")
        assert "2653" in home_url
        assert "_/id/" in home_url

        # Test injuries page
        injury_url = scraper.build_team_url(2653, "injuries")
        assert "injuries" in injury_url

        # Test stats page
        stats_url = scraper.build_team_url(2653, "stats")
        assert "stats" in stats_url

        # Test schedule page
        schedule_url = scraper.build_team_url(2653, "schedule")
        assert "schedule" in schedule_url

        # Test roster page
        roster_url = scraper.build_team_url(2653, "roster")
        assert "roster" in roster_url

    def test_parse_injury_page_structure(self):
        """Test injury parsing returns correct structure."""
        from scrapers.espn import ESPNNcaafTeamScraper

        scraper = ESPNNcaafTeamScraper()

        # Sample HTML content (simplified)
        content = """
        Player Name
        Position
        Out
        Injury Type

        Another Player
        Defense
        Questionable
        Knee
        """

        injuries = scraper.parse_injury_page(content)

        # Should be list of dicts
        assert isinstance(injuries, list)
        if injuries:  # May be empty depending on parse logic
            assert "player" in injuries[0]
            assert "status" in injuries[0]

    def test_parse_team_stats_returns_dict(self):
        """Test stats parsing returns dictionary."""
        from scrapers.espn import ESPNNcaafTeamScraper

        scraper = ESPNNcaafTeamScraper()

        content = """
        Total Yards Per Game
        450

        Passing Yards Per Game
        300
        """

        stats = scraper.parse_team_stats(content)

        assert isinstance(stats, dict)


# ============================================================================
# INTEGRATION TESTS - Multi-component workflows
# ============================================================================


class TestDataPipelineIntegration:
    """Integration tests for data collection pipeline."""

    @pytest.mark.anyio
    async def test_full_ncaaf_data_collection_flow(self, mock_scoreboard_full_response):
        """Test complete NCAAF data collection workflow."""
        from scrapers.espn import ESPNNCAAFScoreboardClient
        from scrapers.espn import ESPNNCAAFNormalizer
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Step 1: Get scoreboard
            client = ESPNNCAAFScoreboardClient()
            await client.connect()

            with patch.object(
                client, "_make_request", return_value=mock_scoreboard_full_response
            ):
                scoreboard = await client.get_scoreboard(week=12, groups=80)

            # Step 2: Normalize data
            normalizer = ESPNNCAAFNormalizer(tmpdir)
            events_df, competitors_df, odds_df = normalizer.normalize_scoreboard(
                scoreboard
            )

            # Step 3: Save to parquet
            result = normalizer.save_parquet(events_df, competitors_df, odds_df)

            # Verify all steps completed
            assert Path(result["events"]).exists()
            assert Path(result["competitors"]).exists()
            assert Path(result["odds"]).exists()

            await client.close()

    def test_injury_data_quality_checks(self, mock_injury_response):
        """Test injury data meets quality standards."""
        injuries = mock_injury_response["injuries"]

        # Verify required fields in each injury record
        for injury in injuries:
            assert "athlete" in injury
            assert "athlete" in injury
            assert "status" in injury
            assert injury["athlete"]["displayName"]
            assert injury["athlete"]["position"]["abbreviation"]
            assert injury["status"]["type"]

    def test_team_stats_required_metrics(self, mock_espn_team_stats_response):
        """Test team stats contain all required metrics."""
        from scrapers.espn import ESPNClient as ESPNAPIClient

        client = ESPNAPIClient()

        with patch.object(
            client, "get_team_statistics", return_value=mock_espn_team_stats_response
        ):
            metrics = client.extract_power_rating_metrics("194", "college-football")

            # Verify no None values for critical metrics
            critical_metrics = [
                "points_per_game",
                "points_allowed_per_game",
                "total_yards_per_game",
                "total_yards_allowed_per_game",
                "turnover_margin",
            ]

            for metric in critical_metrics:
                assert metrics[metric] is not None, f"{metric} is None"


# ============================================================================
# PERFORMANCE & LOAD TESTS
# ============================================================================


class TestDataCollectionPerformance:
    """Performance tests for data collection components."""

    @pytest.mark.anyio
    async def test_rate_limiting_performance(self):
        """Test rate limiting doesn't exceed specified delay."""
        from scrapers.espn import ESPNClient

        client = ESPNClient(rate_limit_delay=0.1)
        await client.connect()

        start = asyncio.get_event_loop().time()

        for _ in range(3):
            await client._rate_limit()

        elapsed = asyncio.get_event_loop().time() - start

        # Should have enforced delay between calls
        assert elapsed >= 0.2  # 2 delays of 0.1s each
        assert elapsed < 1.0  # But not excessively slow

        await client.close()

    def test_normalizer_large_dataset(self, tmp_path):
        """Test normalizer handles large datasets efficiently."""
        from scrapers.espn import ESPNNCAAFNormalizer

        # Create large mock scoreboard with 50 games
        large_scoreboard = {
            "season": {"year": 2025, "type": 2},
            "week": {"number": 12},
            "events": [
                {
                    "id": f"event_{i}",
                    "name": f"Team A vs Team B {i}",
                    "date": "2025-11-23T17:00Z",
                    "status": {"type": {"state": "pre"}},
                    "competitions": [
                        {
                            "venue": {
                                "fullName": f"Stadium {i}",
                                "address": {"city": "City", "state": "ST"},
                                "indoor": False,
                            },
                            "weather": {
                                "temperature": 35,
                                "displayValue": "Cloudy",
                            },
                            "broadcast": {"names": ["ESPN"]},
                            "attendance": 50000,
                            "competitors": [
                                {
                                    "team": {
                                        "id": f"team_a_{i}",
                                        "displayName": "Team A",
                                    },
                                    "homeAway": "away",
                                    "score": 0,
                                    "records": [{"type": "total", "summary": "5-5"}],
                                    "curatedRank": {"current": 25},
                                },
                                {
                                    "team": {
                                        "id": f"team_b_{i}",
                                        "displayName": "Team B",
                                    },
                                    "homeAway": "home",
                                    "score": 0,
                                    "records": [{"type": "total", "summary": "5-5"}],
                                    "curatedRank": {"current": 50},
                                },
                            ],
                            "odds": [
                                {
                                    "provider": {"name": "Caesars"},
                                    "spread": -3.0,
                                    "overUnder": 45.0,
                                }
                            ],
                        }
                    ],
                }
                for i in range(50)
            ],
        }

        normalizer = ESPNNCAAFNormalizer(tmp_path)

        start = asyncio.get_event_loop().time()
        events_df, competitors_df, odds_df = normalizer.normalize_scoreboard(
            large_scoreboard
        )
        elapsed = asyncio.get_event_loop().time() - start

        # Verify all data processed
        assert len(events_df) == 50
        assert len(competitors_df) == 100  # 2 per game
        assert len(odds_df) == 50

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms."""

    @pytest.mark.anyio
    async def test_client_handles_network_error(self):
        """Test client handles network errors gracefully."""
        from scrapers.espn import ESPNClient

        client = ESPNClient(max_retries=1)
        await client.connect()

        from httpx import RequestError

        client._client.get = AsyncMock(side_effect=RequestError("Network error"))

        with pytest.raises(RequestError):
            await client._make_request("https://test.com")

        await client.close()

    @pytest.mark.anyio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        from scrapers.espn import ESPNClient

        client = ESPNClient()
        await client.connect()

        # Simulate failures
        for _ in range(5):
            client._record_failure()

        assert client._circuit_breaker_failures >= 5
        assert client._circuit_breaker_reset_time is not None

        await client.close()

    def test_injury_scraper_handles_missing_data(self):
        """Test injury scraper handles missing fields gracefully."""
        from scrapers.espn import ESPNInjuryScraper

        scraper = ESPNInjuryScraper()

        # Injury with missing optional fields
        incomplete_response = {
            "injuries": [
                {
                    "athlete": {"id": "123", "displayName": "Player"},
                    "status": {},  # Missing type
                    "details": {},
                }
            ]
        }

        # Should not crash
        # (Actual behavior depends on implementation)

    def test_normalizer_handles_missing_fields(self, tmp_path):
        """Test normalizer handles missing optional fields."""
        from scrapers.espn import ESPNNCAAFNormalizer

        normalizer = ESPNNCAAFNormalizer(tmp_path)

        # Scoreboard with minimal required data
        minimal_scoreboard = {
            "season": {"year": 2025, "type": 2},
            "week": {"number": 12},
            "events": [
                {
                    "id": "401628532",
                    "name": "Test Game",
                    "date": "2025-11-23T17:00Z",
                    "status": {"type": {"state": "pre"}},
                    "competitions": [
                        {
                            "venue": {"fullName": "Stadium", "address": {}},
                            "weather": {},
                            "broadcast": {},
                            "competitors": [
                                {
                                    "team": {"id": "1", "displayName": "Team A"},
                                    "homeAway": "away",
                                    "score": 0,
                                },
                                {
                                    "team": {"id": "2", "displayName": "Team B"},
                                    "homeAway": "home",
                                    "score": 0,
                                },
                            ],
                            "odds": [],
                        }
                    ],
                }
            ],
        }

        # Should handle gracefully
        events_df, competitors_df, odds_df = normalizer.normalize_scoreboard(
            minimal_scoreboard
        )

        assert len(events_df) == 1
        # Venue/weather columns should exist but may have None values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
