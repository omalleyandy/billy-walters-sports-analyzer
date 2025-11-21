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


# ==================== Output Directory Configuration ====================


class OutputDirectoryConfig(BaseModel):
    """
    Output directory structure for organized data storage.

    All paths can be overridden via environment variables:
    - OUTPUT_DIR (main output directory)
    - OVERTIME_NFL_DIR, OVERTIME_NCAA_DIR (source-specific)
    - OUTPUT_NFL_SCHEDULE, OUTPUT_NCAA_SCHEDULE (analysis outputs)
    - etc.

    Environment variables take precedence over defaults.
    """

    # Main output directory
    output_dir: Path = Field(default_factory=lambda: Path("output"))

    # Source-specific output directories (NFL)
    overtime_nfl_dir: Path = Field(default_factory=lambda: Path("output/overtime/nfl"))
    liveplus_nfl_dir: Path = Field(default_factory=lambda: Path("output/liveplus/nfl"))
    massey_nfl_dir: Path = Field(default_factory=lambda: Path("output/massey/nfl"))
    espn_nfl_dir: Path = Field(default_factory=lambda: Path("output/espn/nfl"))
    openodds_nfl_dir: Path = Field(default_factory=lambda: Path("output/openodds/nfl"))
    highlightly_nfl_dir: Path = Field(
        default_factory=lambda: Path("output/highlightly/nfl")
    )

    # Source-specific output directories (NCAAF)
    overtime_ncaaf_dir: Path = Field(
        default_factory=lambda: Path("output/overtime/ncaaf")
    )
    liveplus_ncaaf_dir: Path = Field(
        default_factory=lambda: Path("output/liveplus/ncaaf")
    )
    massey_ncaaf_dir: Path = Field(default_factory=lambda: Path("output/massey/ncaaf"))
    espn_ncaaf_dir: Path = Field(default_factory=lambda: Path("output/espn/ncaaf"))
    openodds_ncaaf_dir: Path = Field(
        default_factory=lambda: Path("output/openodds/ncaaf")
    )
    highlightly_ncaaf_dir: Path = Field(
        default_factory=lambda: Path("output/highlightly/ncaaf")
    )

    # Analysis output directories (NFL)
    output_nfl_schedule: Path = Field(
        default_factory=lambda: Path("output/schedule/nfl")
    )
    output_nfl_injuries: Path = Field(
        default_factory=lambda: Path("output/injuries/nfl")
    )
    output_nfl_odds: Path = Field(default_factory=lambda: Path("output/odds/nfl"))
    output_nfl_power_ratings: Path = Field(
        default_factory=lambda: Path("output/power_ratings/nfl")
    )
    output_nfl_cards: Path = Field(default_factory=lambda: Path("output/cards/nfl"))

    # Analysis output directories (NCAAF)
    output_ncaaf_schedule: Path = Field(
        default_factory=lambda: Path("output/schedule/ncaaf")
    )
    output_ncaaf_injuries: Path = Field(
        default_factory=lambda: Path("output/injuries/ncaaf")
    )
    output_ncaaf_odds: Path = Field(default_factory=lambda: Path("output/odds/ncaaf"))
    output_ncaaf_power_ratings: Path = Field(
        default_factory=lambda: Path("output/power_ratings/ncaaf")
    )
    output_ncaaf_cards: Path = Field(default_factory=lambda: Path("output/cards/ncaaf"))

    def get_source_dir(self, source: str, league: str) -> Path:
        """
        Get output directory for a specific source and league.

        Args:
            source: Data source (overtime, massey, espn, etc.)
            league: League (nfl, ncaaf)

        Returns:
            Path to source-specific output directory
        """
        attr_name = f"{source.lower()}_{league.lower()}_dir"
        return getattr(self, attr_name, self.output_dir / source / league)

    def get_analysis_dir(self, analysis_type: str, league: str) -> Path:
        """
        Get output directory for a specific analysis type and league.

        Args:
            analysis_type: Analysis type (schedule, injuries, odds,
                power_ratings, cards)
            league: League (nfl, ncaaf)

        Returns:
            Path to analysis output directory
        """
        attr_name = f"output_{league.lower()}_{analysis_type.lower()}"
        return getattr(
            self, attr_name, self.output_dir / analysis_type / league.lower()
        )

    def ensure_directories_exist(self) -> None:
        """Create all output directories if they don't exist."""
        for field_name, field_value in self.model_dump().items():
            if isinstance(field_value, Path):
                field_value.mkdir(parents=True, exist_ok=True)


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

    # Overtime.ag credentials (supports both OV_PASSWORD and OV_CUSTOMER_PASSWORD)
    ov_customer_id: Optional[str] = Field(default=None, alias="OV_CUSTOMER_ID")
    ov_customer_password: Optional[str] = Field(
        default=None, alias="OV_CUSTOMER_PASSWORD"
    )

    # Proxy configuration (supports both PROXY_URL and OVERTIME_PROXY)
    proxy_url: Optional[str] = Field(default=None, alias="PROXY_URL")

    # Weather API Keys
    accuweather_api_key: Optional[str] = Field(
        default=None, alias="ACCUWEATHER_API_KEY"
    )
    openweather_api_key: Optional[str] = Field(
        default=None, alias="OPENWEATHER_API_KEY"
    )

    # Sports Data Sources
    action_username: Optional[str] = Field(default=None, alias="ACTION_USERNAME")
    action_password: Optional[str] = Field(default=None, alias="ACTION_PASSWORD")

    # Market Data API Keys
    odds_api_key: Optional[str] = Field(default=None, alias="ODDS_API_KEY")
    highlightly_api_key: Optional[str] = Field(
        default=None, alias="HIGHLIGHTLY_API_KEY"
    )
    pinnacle_api_key: Optional[str] = Field(default=None, alias="PINNACLE_API_KEY")
    draftkings_api_key: Optional[str] = Field(default=None, alias="DRAFTKINGS_API_KEY")

    # Overtime.ag Configuration
    overtime_start_url: Optional[str] = Field(
        default="https://overtime.ag", alias="OVERTIME_START_URL"
    )
    overtime_live_url: Optional[str] = Field(default=None, alias="OVERTIME_LIVE_URL")
    overtime_out_dir: Optional[str] = Field(
        default="output/overtime", alias="OVERTIME_OUT_DIR"
    )
    overtime_sport: Optional[str] = Field(default=None, alias="OVERTIME_SPORT")
    overtime_comp: Optional[str] = Field(default=None, alias="OVERTIME_COMP")

    # League identifiers
    sport: str = Field(default="FOOTBALL", alias="SPORT")
    pro_league: str = Field(default="NFL", alias="PRO_LEAGUE")
    college_league: str = Field(default="NCAA", alias="COLLEGE_LEAGUE")

    # Project configuration
    project_root_env: Optional[str] = Field(default=None, alias="PROJ_ROOT")
    pythonpath: Optional[str] = Field(default=None, alias="PYTHONPATH")

    # Development settings from environment
    debug_mode_env: Optional[bool] = Field(default=None, alias="DEBUG_MODE")
    log_level_env: Optional[str] = Field(default=None, alias="LOG_LEVEL")

    # Unused/Planned API Keys (registered but not actively used)
    walters_api_key: Optional[str] = Field(default=None, alias="WALTERS_API_KEY")
    news_api_key: Optional[str] = Field(default=None, alias="NEWS_API_KEY")

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

    # Output directories
    output_dirs: OutputDirectoryConfig = Field(default_factory=OutputDirectoryConfig)

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
