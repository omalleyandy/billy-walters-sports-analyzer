#!/usr/bin/env python3
"""
Tests for Action Network Sitemap Scraper

Tests URL extraction, categorization, regex patterns, and JSONL output.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from src.data.action_network_sitemap_scraper import (
    ActionNetworkSitemapScraper,
)


@pytest.fixture
def scraper():
    """Create scraper instance for testing."""
    return ActionNetworkSitemapScraper(output_base="/tmp/action_network_test")


@pytest.fixture
def sample_sitemap_index_xml():
    """Sample sitemap index XML."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap>
        <loc>https://www.actionnetwork.com/sitemap-general.xml</loc>
    </sitemap>
    <sitemap>
        <loc>https://www.actionnetwork.com/sitemap-nfl.xml</loc>
    </sitemap>
    <sitemap>
        <loc>https://www.actionnetwork.com/sitemap-ncaaf.xml</loc>
    </sitemap>
</sitemapindex>"""


@pytest.fixture
def sample_sitemap_urls_xml():
    """Sample sitemap with various URLs."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://www.actionnetwork.com/nfl-game/chiefs-vs-bills-november-2024</loc>
        <lastmod>2024-11-15</lastmod>
    </url>
    <url>
        <loc>https://www.actionnetwork.com/nfl/odds</loc>
        <lastmod>2024-11-15</lastmod>
    </url>
    <url>
        <loc>https://www.actionnetwork.com/nfl/futures</loc>
        <lastmod>2024-11-15</lastmod>
    </url>
    <url>
        <loc>https://www.actionnetwork.com/ncaaf-game/ohio-state-vs-michigan</loc>
        <lastmod>2024-11-15</lastmod>
    </url>
    <url>
        <loc>https://www.actionnetwork.com/ncaaf/odds</loc>
        <lastmod>2024-11-15</lastmod>
    </url>
    <url>
        <loc>https://www.actionnetwork.com/sports-betting-dfs-strategy-nfl-nba</loc>
        <lastmod>2024-11-15</lastmod>
    </url>
    <url>
        <loc>https://www.actionnetwork.com/nfl-betting-tips-over-under-total</loc>
        <lastmod>2024-11-15</lastmod>
    </url>
</urlset>"""


class TestSitemapParsing:
    """Test XML parsing functionality."""

    def test_parse_sitemap_index(self, scraper, sample_sitemap_index_xml):
        """Test parsing sitemap index."""
        urls = scraper.parse_sitemap_index(sample_sitemap_index_xml)

        assert len(urls) == 3
        assert "https://www.actionnetwork.com/sitemap-general.xml" in urls
        assert "https://www.actionnetwork.com/sitemap-nfl.xml" in urls
        assert "https://www.actionnetwork.com/sitemap-ncaaf.xml" in urls

    def test_parse_sitemap_urls(self, scraper, sample_sitemap_urls_xml):
        """Test parsing sitemap URLs."""
        urls = scraper.parse_sitemap_urls(sample_sitemap_urls_xml)

        assert len(urls) == 7
        assert any("nfl-game" in url for url in urls)
        assert any("ncaaf-game" in url for url in urls)
        assert any("nfl/odds" in url for url in urls)

    def test_parse_invalid_xml(self, scraper):
        """Test parsing invalid XML."""
        urls = scraper.parse_sitemap_index("<invalid>xml</invalid>")
        assert urls == []


class TestURLCategorization:
    """Test URL categorization logic."""

    def test_nfl_game_detection(self, scraper):
        """Test NFL game URL detection."""
        assert scraper.nfl_game_pattern.search("/nfl-game/chiefs-vs-bills")
        assert scraper.nfl_game_pattern.search("/NFL-GAME/chiefs-vs-bills")
        assert not scraper.nfl_game_pattern.search("/nfl/odds")

    def test_ncaaf_game_detection(self, scraper):
        """Test NCAAF game URL detection."""
        assert scraper.ncaaf_game_pattern.search("/ncaaf-game/ohio-state-vs-michigan")
        assert scraper.ncaaf_game_pattern.search("/NCAAF-GAME/ohio-state-vs-michigan")
        assert not scraper.ncaaf_game_pattern.search("/ncaaf/odds")

    def test_nfl_futures_categorization(self, scraper):
        """Test NFL futures categorization."""
        category = scraper.categorize_nfl_url(
            "https://www.actionnetwork.com/nfl/futures"
        )
        assert category == "futures"

    def test_nfl_odds_categorization(self, scraper):
        """Test NFL odds categorization."""
        category = scraper.categorize_nfl_url("https://www.actionnetwork.com/nfl/odds")
        assert category == "odds"

    def test_nfl_teaser_categorization(self, scraper):
        """Test NFL teasers categorization."""
        category = scraper.categorize_nfl_url(
            "https://www.actionnetwork.com/nfl-betting-tips-over-under-total"
        )
        assert category == "teasers-nfl-betting-tips-over-under-total"

    def test_nfl_strategy_categorization(self, scraper):
        """Test NFL strategy categorization."""
        category = scraper.categorize_nfl_url(
            "https://www.actionnetwork.com/sports-betting-dfs-strategy-nfl-nba"
        )
        assert category == "sports-betting-dfs-strategy-nfl-nba-information-news"

    def test_ncaaf_futures_categorization(self, scraper):
        """Test NCAAF futures categorization."""
        category = scraper.categorize_ncaaf_url(
            "https://www.actionnetwork.com/ncaaf/futures"
        )
        assert category == "futures"

    def test_ncaaf_odds_categorization(self, scraper):
        """Test NCAAF odds categorization."""
        category = scraper.categorize_ncaaf_url(
            "https://www.actionnetwork.com/ncaaf/odds"
        )
        assert category == "odds"

    def test_uncategorized_url(self, scraper):
        """Test URL that doesn't match any category."""
        category = scraper.categorize_nfl_url(
            "https://www.actionnetwork.com/some-random-page"
        )
        assert category is None


class TestURLProcessing:
    """Test URL processing and collection."""

    def test_process_urls_nfl_games(self, scraper):
        """Test processing NFL game URLs."""
        urls = [
            "https://www.actionnetwork.com/nfl-game/chiefs-vs-bills",
            "https://www.actionnetwork.com/nfl-game/49ers-vs-cowboys",
        ]
        scraper.process_urls(urls)

        assert len(scraper.nfl_games) == 2
        assert (
            "https://www.actionnetwork.com/nfl-game/chiefs-vs-bills"
            in scraper.nfl_games
        )

    def test_process_urls_ncaaf_games(self, scraper):
        """Test processing NCAAF game URLs."""
        urls = [
            "https://www.actionnetwork.com/ncaaf-game/ohio-state-vs-michigan",
            "https://www.actionnetwork.com/ncaaf-game/alabama-vs-georgia",
        ]
        scraper.process_urls(urls)

        assert len(scraper.ncaaf_games) == 2
        assert (
            "https://www.actionnetwork.com/ncaaf-game/ohio-state-vs-michigan"
            in scraper.ncaaf_games
        )

    def test_process_urls_categories(self, scraper):
        """Test processing URLs with categories."""
        urls = [
            "https://www.actionnetwork.com/nfl/odds",
            "https://www.actionnetwork.com/nfl/futures",
            "https://www.actionnetwork.com/ncaaf/odds",
        ]
        scraper.process_urls(urls)

        assert len(scraper.nfl_category_pages["odds"]) == 1
        assert len(scraper.nfl_category_pages["futures"]) == 1
        assert len(scraper.ncaaf_category_pages["odds"]) == 1

    def test_process_urls_mixed(self, scraper):
        """Test processing mixed URL types."""
        urls = [
            "https://www.actionnetwork.com/nfl-game/chiefs-vs-bills",
            "https://www.actionnetwork.com/nfl/odds",
            "https://www.actionnetwork.com/ncaaf-game/ohio-state-vs-michigan",
            "https://www.actionnetwork.com/ncaaf/futures",
        ]
        scraper.process_urls(urls)

        assert len(scraper.nfl_games) == 1
        assert len(scraper.ncaaf_games) == 1
        assert len(scraper.nfl_category_pages["odds"]) == 1
        assert len(scraper.ncaaf_category_pages["futures"]) == 1


class TestJSONLOutput:
    """Test JSONL record generation."""

    def test_build_jsonl_record_game(self, scraper):
        """Test building JSONL record for game."""
        record = scraper._build_jsonl_record(
            "https://www.actionnetwork.com/nfl-game/chiefs-vs-bills",
            "nfl",
            "game",
            None,
        )

        assert record["url"] == (
            "https://www.actionnetwork.com/nfl-game/chiefs-vs-bills"
        )
        assert record["league"] == "nfl"
        assert record["content_type"] == "game"
        assert record["category"] is None
        assert "scraped_at" in record
        assert record["domain"] == "www.actionnetwork.com"
        assert record["slug"] == "chiefs-vs-bills"

    def test_build_jsonl_record_category(self, scraper):
        """Test building JSONL record for category page."""
        record = scraper._build_jsonl_record(
            "https://www.actionnetwork.com/nfl/odds",
            "nfl",
            "category",
            "odds",
        )

        assert record["content_type"] == "category"
        assert record["category"] == "odds"
        assert record["slug"] == "odds"

    def test_jsonl_record_has_required_fields(self, scraper):
        """Test JSONL record has all required fields."""
        record = scraper._build_jsonl_record(
            "https://www.actionnetwork.com/nfl-game/test",
            "nfl",
            "game",
            None,
        )

        required_fields = [
            "url",
            "league",
            "content_type",
            "category",
            "path",
            "path_parts",
            "slug",
            "scraped_at",
            "domain",
        ]

        for field in required_fields:
            assert field in record, f"Missing required field: {field}"

    def test_jsonl_record_datetime_format(self, scraper):
        """Test JSONL record has valid ISO datetime."""
        record = scraper._build_jsonl_record(
            "https://www.actionnetwork.com/nfl-game/test",
            "nfl",
            "game",
            None,
        )

        # Should not raise exception
        datetime.fromisoformat(record["scraped_at"])


class TestPatternMatching:
    """Test regex pattern matching edge cases."""

    def test_case_insensitive_matching(self, scraper):
        """Test case-insensitive pattern matching."""
        assert scraper.nfl_game_pattern.search("/NFL-GAME/test")
        assert scraper.nfl_game_pattern.search("/nfl-game/test")
        assert scraper.nfl_game_pattern.search("/Nfl-Game/test")

    def test_nested_path_matching(self, scraper):
        """Test matching in nested paths."""
        urls = [
            "/nfl-game/chiefs-vs-bills",
            "/games/nfl-game/2024/chiefs-vs-bills",
            "/archive/nfl-game/chiefs-vs-bills",
        ]

        nfl_games = [u for u in urls if scraper.nfl_game_pattern.search(u)]
        assert len(nfl_games) == 3

    def test_category_pattern_specificity(self, scraper):
        """Test category patterns don't overlap."""
        urls = {
            "https://www.actionnetwork.com/nfl/odds": "odds",
            "https://www.actionnetwork.com/nfl/futures": "futures",
            "https://www.actionnetwork.com/nfl-betting-tips": (
                "teasers-nfl-betting-tips-over-under-total"
            ),
        }

        for url, expected_category in urls.items():
            category = scraper.categorize_nfl_url(url)
            assert category == expected_category, (
                f"URL {url} categorized as {category}, expected {expected_category}"
            )


class TestOutputDirectories:
    """Test output directory creation."""

    def test_output_dirs_created(self, scraper):
        """Test output directories are created."""

        assert Path(scraper.output_base).exists()
        assert Path(f"{scraper.output_base}/nfl").exists()
        assert Path(f"{scraper.output_base}/ncaaf").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
