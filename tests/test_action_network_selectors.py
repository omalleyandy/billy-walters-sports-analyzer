"""
Selector Validation Tests for Action Network Scraper.

Tests multi-selector fallback logic and validates selector configuration.
Helps detect CSS/DOM changes early before production failures.

Usage:
    uv run pytest tests/test_action_network_selectors.py -v
    uv run pytest tests/test_action_network_selectors.py::test_selectors_loaded -v
"""

import json
from pathlib import Path

import pytest

from src.data.action_network_client import ActionNetworkClient


class TestSelectorConfiguration:
    """Tests for selector configuration loading and validation."""

    def test_selectors_config_file_exists(self) -> None:
        """Test that selector configuration file exists."""
        config_file = (
            Path(__file__).parent.parent / "src/data/action_network_selectors.json"
        )
        assert config_file.exists(), f"Config file not found: {config_file}"

    def test_selectors_config_valid_json(self) -> None:
        """Test that selector configuration is valid JSON."""
        config_file = (
            Path(__file__).parent.parent / "src/data/action_network_selectors.json"
        )
        with open(config_file) as f:
            config = json.load(f)
            assert "selectors" in config, "Missing 'selectors' key"
            assert isinstance(config["selectors"], dict), "Selectors must be a dict"

    def test_selectors_loaded(self) -> None:
        """Test that ActionNetworkClient loads selectors."""
        selectors = ActionNetworkClient.SELECTORS
        assert selectors, "Selectors dict is empty"
        assert isinstance(selectors, dict), "Selectors must be a dict"

    def test_required_selector_keys(self) -> None:
        """Test that all required selector keys are present."""
        selectors = ActionNetworkClient.SELECTORS
        required_keys = [
            "login_button",
            "username_input",
            "password_input",
            "submit_button",
            "sport_nfl",
            "sport_ncaaf",
            "odds_tab",
        ]

        for key in required_keys:
            assert key in selectors, f"Missing required selector: {key}"

    def test_selectors_are_lists(self) -> None:
        """Test that selectors are lists (multi-selector support)."""
        selectors = ActionNetworkClient.SELECTORS
        for key, value in selectors.items():
            assert isinstance(value, list), (
                f"Selector '{key}' must be a list, got {type(value)}"
            )
            assert len(value) > 0, f"Selector '{key}' list is empty"

    def test_selector_entries_are_strings(self) -> None:
        """Test that selector list entries are strings."""
        selectors = ActionNetworkClient.SELECTORS
        for key, selector_list in selectors.items():
            for i, selector in enumerate(selector_list):
                assert isinstance(selector, str), (
                    f"Selector '{key}[{i}]' must be string, got {type(selector)}"
                )
                assert len(selector) > 0, f"Selector '{key}[{i}]' is empty"

    def test_primary_selectors_specific(self) -> None:
        """Test that primary selectors are specific (most likely to work)."""
        selectors = ActionNetworkClient.SELECTORS
        # Primary selector (index 0) should be most specific
        # (have auto-generated classes or full paths)

        assert ".css-" in selectors["login_button"][0], (
            "Primary login selector should include CSS-in-JS class"
        )

    def test_fallback_selectors_generic(self) -> None:
        """Test that fallback selectors are more generic."""
        selectors = ActionNetworkClient.SELECTORS
        # Fallback selectors (index > 0) should be less specific
        # (use class wildcards, type selectors, etc.)

        fallback_has_wildcard = any(
            "*" in selector for selector in selectors["login_button"][1:]
        )
        assert fallback_has_wildcard, (
            "Fallback selectors should use wildcards for generality"
        )

    def test_xpath_selectors_valid_format(self) -> None:
        """Test that XPath selectors are properly formatted."""
        selectors = ActionNetworkClient.SELECTORS
        for key, selector_list in selectors.items():
            for selector in selector_list:
                if selector.startswith("//"):
                    # XPath selector - validate basic structure
                    assert "]" in selector, f"XPath '{selector}' has invalid structure"


class TestSelectorFallbackLogic:
    """Tests for the _try_selectors() fallback mechanism."""

    @pytest.mark.asyncio
    async def test_try_selectors_method_exists(self) -> None:
        """Test that _try_selectors method exists."""
        client = ActionNetworkClient.__new__(ActionNetworkClient)
        assert hasattr(client, "_try_selectors"), "Missing _try_selectors method"

    @pytest.mark.asyncio
    async def test_try_selectors_accepts_multiple_selectors(self) -> None:
        """Test that _try_selectors accepts multiple selector strategies."""
        # This is a documentation test showing intended usage
        selectors = ActionNetworkClient.SELECTORS
        assert isinstance(selectors["login_button"], list)
        assert len(selectors["login_button"]) >= 2


class TestSelectorConfigValidation:
    """Tests for selector configuration content validation."""

    def test_config_has_version(self) -> None:
        """Test that config includes version info."""
        config_file = (
            Path(__file__).parent.parent / "src/data/action_network_selectors.json"
        )
        with open(config_file) as f:
            config = json.load(f)
            assert "version" in config, "Config missing 'version' field"
            assert isinstance(config["version"], str), "Version must be string"

    def test_config_has_description(self) -> None:
        """Test that config includes description."""
        config_file = (
            Path(__file__).parent.parent / "src/data/action_network_selectors.json"
        )
        with open(config_file) as f:
            config = json.load(f)
            assert "description" in config, "Config missing 'description' field"

    def test_selector_list_precedence(self) -> None:
        """Test that selector lists follow precedence (specific to generic)."""
        selectors = ActionNetworkClient.SELECTORS
        login_selectors = selectors["login_button"]

        # First selector should be most specific (CSS-in-JS classes)
        assert ".css-" in login_selectors[0], (
            "Primary selector should have CSS-in-JS classes"
        )

        # Later selectors should be more generic
        has_attr_wildcard = any("[class*=" in s for s in login_selectors[1:])
        assert has_attr_wildcard, "Fallback selectors should use attribute wildcards"


class TestSelectorCoverage:
    """Tests to ensure all required elements have selectors."""

    def test_login_flow_selectors(self) -> None:
        """Test that login flow has complete selector coverage."""
        selectors = ActionNetworkClient.SELECTORS
        login_elements = [
            "login_button",
            "username_input",
            "password_input",
            "submit_button",
        ]
        for element in login_elements:
            assert element in selectors, (
                f"Missing selector for login element: {element}"
            )
            assert len(selectors[element]) > 0, f"Empty selector list for: {element}"

    def test_navigation_selectors(self) -> None:
        """Test that navigation has complete selector coverage."""
        selectors = ActionNetworkClient.SELECTORS
        nav_elements = [
            "sport_nfl",
            "sport_ncaaf",
            "odds_tab",
        ]
        for element in nav_elements:
            assert element in selectors, (
                f"Missing selector for navigation element: {element}"
            )
            assert len(selectors[element]) > 0, f"Empty selector list for: {element}"

    def test_odds_table_selectors(self) -> None:
        """Test that odds table extraction has selector coverage."""
        selectors = ActionNetworkClient.SELECTORS
        table_elements = [
            "odds_table",
            "game_row",
            "team_name",
        ]
        for element in table_elements:
            # These are optional if hardcoded in extraction logic
            # but should be present in config for maintainability
            if element in selectors:
                assert isinstance(selectors[element], list)
                assert len(selectors[element]) > 0


class TestSelectorMaintenance:
    """Tests for selector maintenance and monitoring."""

    def test_last_validated_timestamp(self) -> None:
        """Test that config includes last validation timestamp."""
        config_file = (
            Path(__file__).parent.parent / "src/data/action_network_selectors.json"
        )
        with open(config_file) as f:
            config = json.load(f)
            assert "last_validated" in config, "Missing 'last_validated' field"

    def test_selector_notes_provided(self) -> None:
        """Test that config includes maintenance notes."""
        config_file = (
            Path(__file__).parent.parent / "src/data/action_network_selectors.json"
        )
        with open(config_file) as f:
            config = json.load(f)
            assert "notes" in config, "Config missing 'notes' section"
            notes = config["notes"]
            assert isinstance(notes, dict), "Notes must be a dict"
            assert "maintenance" in notes, "Missing maintenance notes"

    def test_selector_strategy_documented(self) -> None:
        """Test that fallback strategy is documented."""
        config_file = (
            Path(__file__).parent.parent / "src/data/action_network_selectors.json"
        )
        with open(config_file) as f:
            config = json.load(f)
            notes = config.get("notes", {})
            assert "fallback_strategy" in notes, (
                "Missing fallback strategy documentation"
            )
