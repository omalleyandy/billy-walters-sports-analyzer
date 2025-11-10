"""
Unified settings model for Billy Walters Sports Analyzer.
Uses Pydantic for validation and type safety.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ==================== Skills Configuration ====================


class MarketAnalysisConfig(BaseModel):
    """Market analysis skill configuration."""

    enabled: bool = True
    sharp_books: List[str] = Field(
        default_factory=lambda: ["Pinnacle", "Circa", "Bookmaker"]
    )
    public_books: List[str] = Field(
        default_factory=lambda: ["DraftKings", "FanDuel", "BetMGM"]
    )
    alert_threshold: float = 0.7
    monitor_interval: int = 30  # seconds


class MLPowerRatingsConfig(BaseModel):
    """Machine learning power ratings configuration."""

    enabled: bool = True
    model: str = "xgboost"
    update_frequency: str = "weekly"
    min_games_for_update: int = 10


class SituationalDatabaseConfig(BaseModel):
    """Situational database configuration."""

    enabled: bool = True
    track_situations: List[str] = Field(
        default_factory=lambda: [
            "sandwich_spot",
            "lookahead_game",
            "revenge_game",
            "division_rivalry",
            "primetime_under",
        ]
    )


class SkillsConfig(BaseModel):
    """All skills configuration."""

    market_analysis: MarketAnalysisConfig = Field(default_factory=MarketAnalysisConfig)
    ml_power_ratings: MLPowerRatingsConfig = Field(default_factory=MLPowerRatingsConfig)
    situational_database: SituationalDatabaseConfig = Field(
        default_factory=SituationalDatabaseConfig
    )


# ==================== Autonomous Agent Configuration ====================


class AgentSafetyConfig(BaseModel):
    """Safety settings for autonomous agent."""

    daily_loss_limit: float = 5.0  # percentage
    require_confirmation: bool = True
    paper_trading_mode: bool = True


class AutonomousAgentConfig(BaseModel):
    """Autonomous betting agent configuration."""

    enabled: bool = False
    initial_bankroll: float = 10000.0
    max_bet_percentage: float = 3.0
    confidence_threshold: float = 0.65
    max_concurrent_bets: int = 10
    learning_rate: float = 0.1
    memory_buffer_size: int = 10000
    safety: AgentSafetyConfig = Field(default_factory=AgentSafetyConfig)


# ==================== Data Connections Configuration ====================


class SportsbookConfig(BaseModel):
    """Individual sportsbook configuration."""

    enabled: bool = False
    api_endpoint: str = ""
    requires_auth: bool = False


class DataProviderConfig(BaseModel):
    """Individual data provider configuration."""

    enabled: bool = True
    base_url: Optional[str] = None
    requires_key: bool = False


class DataConnectionsConfig(BaseModel):
    """Data connections to sportsbooks and providers."""

    # Sportsbooks
    pinnacle_enabled: bool = False
    pinnacle_api_endpoint: str = "https://api.pinnacle.com/"

    draftkings_enabled: bool = False
    draftkings_api_endpoint: str = "https://api.draftkings.com/"

    # Data providers
    profootballdoc_enabled: bool = True
    profootballdoc_base_url: str = "https://profootballdoc.com/"

    accuweather_enabled: bool = True
    highlightly_enabled: bool = True


# ==================== Monitoring Configuration ====================


class AlertChannelsConfig(BaseModel):
    """Alert notification channels."""

    console: bool = True
    file: str = "./logs/alerts.log"
    webhook: Optional[str] = None


class MetricsConfig(BaseModel):
    """Metrics tracking configuration."""

    track_roi: bool = True
    track_win_rate: bool = True
    track_clv: bool = True
    track_sharp_accuracy: bool = True


class MonitoringConfig(BaseModel):
    """Performance monitoring and tracking."""

    performance_tracking: bool = True
    clv_tracking: bool = True
    alert_channels: AlertChannelsConfig = Field(default_factory=AlertChannelsConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)


# ==================== Global Settings ====================


class GlobalConfig(BaseModel):
    """Global application settings."""

    auto_start: bool = True
    debug_mode: bool = False
    log_level: str = "info"
    max_concurrent_requests: int = 10
    request_timeout: int = 30000  # milliseconds


class DevelopmentConfig(BaseModel):
    """Development and testing settings."""

    test_mode: bool = False
    mock_data: bool = False
    cache_ttl: int = 300  # seconds
    rate_limiting_enabled: bool = True
    requests_per_minute: int = 60


# ==================== Main Settings Class ====================


class Settings(BaseSettings):
    """
    Unified settings for Billy Walters Sports Analyzer.

    Settings are loaded with the following priority (highest to lowest):
    1. Environment variables
    2. CLI arguments (handled separately)
    3. User config file
    4. MCP config file
    5. Billy Walters config file
    6. Defaults
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== Environment Variables ====================

    # Overtime.ag credentials
    ov_customer_id: Optional[str] = Field(default=None, alias="OV_CUSTOMER_ID")
    ov_customer_password: Optional[str] = Field(
        default=None, alias="OV_CUSTOMER_PASSWORD"
    )

    # Proxy
    proxy_url: Optional[str] = Field(default=None, alias="PROXY_URL")

    # API Keys
    walters_api_key: Optional[str] = Field(default=None, alias="WALTERS_API_KEY")
    news_api_key: Optional[str] = Field(default=None, alias="NEWS_API_KEY")
    highlightly_api_key: Optional[str] = Field(
        default=None, alias="HIGHLIGHTLY_API_KEY"
    )
    accuweather_api_key: Optional[str] = Field(
        default=None, alias="ACCUWEATHER_API_KEY"
    )

    # Market Data API Keys
    odds_api_key: Optional[str] = Field(default=None, alias="ODDS_API_KEY")
    pinnacle_api_key: Optional[str] = Field(default=None, alias="PINNACLE_API_KEY")
    draftkings_api_key: Optional[str] = Field(default=None, alias="DRAFTKINGS_API_KEY")

    # Python path
    pythonpath: Optional[str] = Field(default=None, alias="PYTHONPATH")

    # ==================== Configuration Categories ====================

    # Skills
    skills: SkillsConfig = Field(default_factory=SkillsConfig)

    # Autonomous agent
    autonomous_agent: AutonomousAgentConfig = Field(
        default_factory=AutonomousAgentConfig
    )

    # Data connections
    data_connections: DataConnectionsConfig = Field(
        default_factory=DataConnectionsConfig
    )

    # Monitoring
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # Global settings
    global_config: GlobalConfig = Field(default_factory=GlobalConfig)

    # Development settings
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)

    # ==================== Billy Walters Config Data ====================
    # These will be loaded from billy_walters_config.json
    billy_walters_config: Optional[Dict[str, Any]] = None

    # ==================== Path Settings ====================

    # Base paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent
    )
    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "data"
    )
    logs_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "logs"
    )

    # Config file paths
    billy_walters_config_path: Optional[Path] = None
    mcp_config_path: Optional[Path] = None


# ==================== Settings Instance ====================

_settings_instance: Optional[Settings] = None


def get_settings(reload: bool = False) -> Settings:
    """
    Get the global settings instance.

    Args:
        reload: Force reload settings from files

    Returns:
        Settings instance
    """
    global _settings_instance

    if _settings_instance is None or reload:
        from .loader import load_settings

        _settings_instance = load_settings()

    return _settings_instance


def reset_settings():
    """Reset the global settings instance (useful for testing)."""
    global _settings_instance
    _settings_instance = None
