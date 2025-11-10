"""
Configuration loader for Billy Walters valuation system.

This module now uses the unified configuration system but maintains
backward compatibility with the original API.
"""

import json
from pathlib import Path
from typing import Dict, Any

# Import unified config system
from walters_analyzer.config import get_settings

# Legacy cache for backward compatibility
_config_cache: Dict[str, Any] = {}


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load Billy Walters configuration from JSON file.

    This function now uses the unified config system but maintains
    backward compatibility.

    Args:
        config_path: Optional path to config file. If None, uses default location.

    Returns:
        Dictionary containing all configuration values
    """
    global _config_cache

    # Use unified settings if no custom path specified
    if config_path is None:
        settings = get_settings()
        if settings.billy_walters_config:
            return settings.billy_walters_config

        # Fall back to default location
        config_path = Path(__file__).parent / "billy_walters_config.json"
    else:
        config_path = Path(config_path)

    # Cache the config
    cache_key = str(config_path)
    if cache_key not in _config_cache:
        with open(config_path, "r") as f:
            _config_cache[cache_key] = json.load(f)

    return _config_cache[cache_key]


def get_config() -> Dict[str, Any]:
    """
    Get the cached configuration (loads default if not loaded).

    Now uses unified config system.
    """
    return load_config()


def get_position_values(sport: str = "NFL") -> Dict[str, Dict[str, float]]:
    """Get position values for a specific sport"""
    config = get_config()
    return config.get("position_values", {}).get(sport, {})


def get_injury_multipliers() -> Dict[str, Dict[str, float]]:
    """Get injury type multipliers"""
    config = get_config()
    return config.get("injury_multipliers", {})


def get_betting_thresholds() -> Dict[str, float]:
    """Get betting thresholds"""
    config = get_config()
    return config.get("betting_thresholds", {})


def get_market_adjustments() -> Dict[str, float]:
    """Get market adjustment factors"""
    config = get_config()
    return config.get("market_adjustments", {})


def get_response_templates() -> Dict[str, Dict[str, Any]]:
    """Get response templates for different impact levels"""
    config = get_config()
    return config.get("responses", {})


# ==================== New unified config access ====================


def get_settings_instance():
    """
    Get the unified settings instance.

    Use this for accessing all configuration including MCP settings,
    skills, monitoring, etc.

    Returns:
        Settings instance with all configuration
    """
    return get_settings()
