"""
Configuration loader with priority hierarchy.

Priority order (highest to lowest):
1. Environment variables (.env)
2. CLI arguments (handled by caller)
3. User config file (if exists)
4. MCP config file
5. Billy Walters config file
6. Defaults
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .settings import (
    Settings,
    MarketAnalysisConfig,
    MLPowerRatingsConfig,
    SituationalDatabaseConfig,
    AutonomousAgentConfig,
    AgentSafetyConfig,
    MonitoringConfig,
    AlertChannelsConfig,
    MetricsConfig,
    GlobalConfig,
    DevelopmentConfig,
)

logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load JSON file safely.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON dict or None if file doesn't exist or is invalid
    """
    if not file_path.exists():
        logger.debug(f"Config file not found: {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None


def load_billy_walters_config(project_root: Path) -> Optional[Dict[str, Any]]:
    """
    Load Billy Walters methodology config.

    Args:
        project_root: Project root directory

    Returns:
        Config dict or None
    """
    config_path = (
        project_root / "walters_analyzer" / "valuation" / "billy_walters_config.json"
    )
    return load_json_file(config_path)


def load_mcp_config(project_root: Path) -> Optional[Dict[str, Any]]:
    """
    Load Claude MCP config.

    Args:
        project_root: Project root directory

    Returns:
        Config dict or None
    """
    config_path = project_root / ".claude" / "claude-desktop-config.json"
    return load_json_file(config_path)


def merge_mcp_config(settings: Settings, mcp_config: Dict[str, Any]) -> Settings:
    """
    Merge MCP config into settings.

    Args:
        settings: Base settings instance
        mcp_config: MCP config dict

    Returns:
        Updated settings
    """
    if not mcp_config:
        return settings

    # Extract skills config
    if "skills" in mcp_config:
        skills_data = mcp_config["skills"]

        # Market analysis
        if "market-analysis" in skills_data:
            ma_config = skills_data["market-analysis"].get("config", {})
            settings.skills.market_analysis = MarketAnalysisConfig(
                enabled=skills_data["market-analysis"].get("enabled", True),
                sharp_books=ma_config.get(
                    "sharp_books", settings.skills.market_analysis.sharp_books
                ),
                public_books=ma_config.get(
                    "public_books", settings.skills.market_analysis.public_books
                ),
                alert_threshold=ma_config.get(
                    "alert_threshold", settings.skills.market_analysis.alert_threshold
                ),
                monitor_interval=ma_config.get(
                    "monitor_interval", settings.skills.market_analysis.monitor_interval
                ),
            )

        # ML power ratings
        if "ml-power-ratings" in skills_data:
            ml_config = skills_data["ml-power-ratings"].get("config", {})
            settings.skills.ml_power_ratings = MLPowerRatingsConfig(
                enabled=skills_data["ml-power-ratings"].get("enabled", True),
                model=ml_config.get("model", settings.skills.ml_power_ratings.model),
                update_frequency=ml_config.get(
                    "update_frequency",
                    settings.skills.ml_power_ratings.update_frequency,
                ),
                min_games_for_update=ml_config.get(
                    "min_games_for_update",
                    settings.skills.ml_power_ratings.min_games_for_update,
                ),
            )

        # Situational database
        if "situational-database" in skills_data:
            sit_config = skills_data["situational-database"].get("config", {})
            settings.skills.situational_database = SituationalDatabaseConfig(
                enabled=skills_data["situational-database"].get("enabled", True),
                track_situations=sit_config.get(
                    "track_situations",
                    settings.skills.situational_database.track_situations,
                ),
            )

    # Extract autonomous agent config
    if "autonomousAgent" in mcp_config:
        agent_data = mcp_config["autonomousAgent"]
        agent_config = agent_data.get("config", {})
        safety_data = agent_data.get("safety", {})

        settings.autonomous_agent = AutonomousAgentConfig(
            enabled=agent_data.get("enabled", False),
            initial_bankroll=agent_config.get("initial_bankroll", 10000.0),
            max_bet_percentage=agent_config.get("max_bet_percentage", 3.0),
            confidence_threshold=agent_config.get("confidence_threshold", 0.65),
            max_concurrent_bets=agent_config.get("max_concurrent_bets", 10),
            learning_rate=agent_config.get("learning_rate", 0.1),
            memory_buffer_size=agent_config.get("memory_buffer_size", 10000),
            safety=AgentSafetyConfig(
                daily_loss_limit=safety_data.get("daily_loss_limit", 5.0),
                require_confirmation=safety_data.get("require_confirmation", True),
                paper_trading_mode=safety_data.get("paper_trading_mode", True),
            ),
        )

    # Extract data connections
    if "dataConnections" in mcp_config:
        dc_data = mcp_config["dataConnections"]

        # Sportsbooks
        if "sportsbooks" in dc_data:
            sb_data = dc_data["sportsbooks"]
            if "pinnacle" in sb_data:
                settings.data_connections.pinnacle_enabled = sb_data["pinnacle"].get(
                    "enabled", False
                )
                settings.data_connections.pinnacle_api_endpoint = sb_data[
                    "pinnacle"
                ].get("api_endpoint", "https://api.pinnacle.com/")
            if "draftkings" in sb_data:
                settings.data_connections.draftkings_enabled = sb_data[
                    "draftkings"
                ].get("enabled", False)
                settings.data_connections.draftkings_api_endpoint = sb_data[
                    "draftkings"
                ].get("api_endpoint", "https://api.draftkings.com/")

        # Data providers
        if "data_providers" in dc_data:
            dp_data = dc_data["data_providers"]
            if "profootballdoc" in dp_data:
                settings.data_connections.profootballdoc_enabled = dp_data[
                    "profootballdoc"
                ].get("enabled", True)
                if "base_url" in dp_data["profootballdoc"]:
                    settings.data_connections.profootballdoc_base_url = dp_data[
                        "profootballdoc"
                    ]["base_url"]
            if "accuweather" in dp_data:
                settings.data_connections.accuweather_enabled = dp_data[
                    "accuweather"
                ].get("enabled", True)
            if "highlightly" in dp_data:
                settings.data_connections.highlightly_enabled = dp_data[
                    "highlightly"
                ].get("enabled", True)

    # Extract monitoring config
    if "monitoring" in mcp_config:
        mon_data = mcp_config["monitoring"]

        alert_channels_data = mon_data.get("alert_channels", {})
        metrics_data = mon_data.get("metrics", {})

        settings.monitoring = MonitoringConfig(
            performance_tracking=mon_data.get("performance_tracking", True),
            clv_tracking=mon_data.get("clv_tracking", True),
            alert_channels=AlertChannelsConfig(
                console=alert_channels_data.get("console", True),
                file=alert_channels_data.get("file", "./logs/alerts.log"),
                webhook=alert_channels_data.get("webhook"),
            ),
            metrics=MetricsConfig(
                track_roi=metrics_data.get("track_roi", True),
                track_win_rate=metrics_data.get("track_win_rate", True),
                track_clv=metrics_data.get("track_clv", True),
                track_sharp_accuracy=metrics_data.get("track_sharp_accuracy", True),
            ),
        )

    # Extract global settings
    if "globalSettings" in mcp_config:
        global_data = mcp_config["globalSettings"]
        settings.global_config = GlobalConfig(
            auto_start=global_data.get("autoStart", True),
            debug_mode=global_data.get("debugMode", False),
            log_level=global_data.get("logLevel", "info"),
            max_concurrent_requests=global_data.get("maxConcurrentRequests", 10),
            request_timeout=global_data.get("requestTimeout", 30000),
        )

    # Extract development settings
    if "development" in mcp_config:
        dev_data = mcp_config["development"]
        rate_limiting_data = dev_data.get("rate_limiting", {})

        settings.development = DevelopmentConfig(
            test_mode=dev_data.get("test_mode", False),
            mock_data=dev_data.get("mock_data", False),
            cache_ttl=dev_data.get("cache_ttl", 300),
            rate_limiting_enabled=rate_limiting_data.get("enabled", True),
            requests_per_minute=rate_limiting_data.get("requests_per_minute", 60),
        )

    return settings


def load_settings(
    project_root: Optional[Path] = None,
    billy_walters_config_path: Optional[Path] = None,
    mcp_config_path: Optional[Path] = None,
) -> Settings:
    """
    Load unified settings from all sources.

    Args:
        project_root: Project root directory (auto-detected if None)
        billy_walters_config_path: Override Billy Walters config path
        mcp_config_path: Override MCP config path

    Returns:
        Settings instance with merged configuration
    """
    # Determine project root
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent

    # Load base settings (includes .env)
    settings = Settings(project_root=project_root)

    # Store config paths
    settings.billy_walters_config_path = billy_walters_config_path or (
        project_root / "walters_analyzer" / "valuation" / "billy_walters_config.json"
    )
    settings.mcp_config_path = mcp_config_path or (
        project_root / ".claude" / "claude-desktop-config.json"
    )

    # Load Billy Walters config
    bw_config = load_billy_walters_config(project_root)
    if bw_config:
        settings.billy_walters_config = bw_config
        logger.info("Loaded Billy Walters config")

    # Load and merge MCP config
    mcp_config = load_mcp_config(project_root)
    if mcp_config:
        settings = merge_mcp_config(settings, mcp_config)
        logger.info("Loaded and merged MCP config")

    # Create required directories
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    return settings
