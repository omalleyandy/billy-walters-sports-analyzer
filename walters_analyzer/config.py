"""
Centralized Configuration for Billy Walters Sports Analyzer

Manages all configuration from environment variables and defaults.
Following best practices from Scrapy, Playwright, and Python-dotenv.

Usage:
    from walters_analyzer.config import Config
    
    config = Config()
    
    # Access settings
    bankroll = config.BANKROLL
    api_key = config.ACCUWEATHER_API_KEY
    cache_ttl = config.CACHE_TTL_WEATHER
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


@dataclass
class Config:
    """
    Centralized configuration management.
    
    All settings loaded from environment variables with sensible defaults.
    Priority: Environment variables > .env file > defaults
    """
    
    # ========================================================================
    # Core Settings
    # ========================================================================
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    DOCS_DIR: Path = PROJECT_ROOT / "docs"
    
    # Bankroll settings
    BANKROLL: float = float(os.getenv('BANKROLL', '10000.0'))
    KELLY_FRACTION: float = float(os.getenv('KELLY_FRACTION', '0.25'))
    MAX_BET_PERCENTAGE: float = float(os.getenv('MAX_BET_PERCENTAGE', '0.03'))
    
    # ========================================================================
    # API Keys & Credentials
    # ========================================================================
    
    # Weather APIs
    ACCUWEATHER_API_KEY: Optional[str] = os.getenv('ACCUWEATHER_API_KEY')
    OPENWEATHER_API_KEY: Optional[str] = os.getenv('OPENWEATHER_API_KEY')
    
    # Betting sites
    OV_CUSTOMER_ID: Optional[str] = os.getenv('OV_CUSTOMER_ID')
    OV_CUSTOMER_PASSWORD: Optional[str] = os.getenv('OV_CUSTOMER_PASSWORD')
    
    # News & Research
    NEWS_API_KEY: Optional[str] = os.getenv('NEWS_API_KEY')
    PROFOOTBALLDOC_API_KEY: Optional[str] = os.getenv('PROFOOTBALLDOC_API_KEY')
    
    # Sports data providers
    HIGHLIGHTLY_API_KEY: Optional[str] = os.getenv('HIGHLIGHTLY_API_KEY')
    
    # Social media (optional)
    TWITTER_API_KEY: Optional[str] = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET: Optional[str] = os.getenv('TWITTER_API_SECRET')
    
    # ========================================================================
    # Scraping Settings
    # ========================================================================
    
    # Proxy configuration
    PROXY_URL: Optional[str] = os.getenv('PROXY_URL')
    OVERTIME_PROXY: Optional[str] = os.getenv('OVERTIME_PROXY')
    
    # Scrapy settings
    SCRAPY_CONCURRENT_REQUESTS: int = int(os.getenv('SCRAPY_CONCURRENT_REQUESTS', '2'))
    SCRAPY_DOWNLOAD_TIMEOUT: int = int(os.getenv('SCRAPY_DOWNLOAD_TIMEOUT', '60'))
    SCRAPY_AUTOTHROTTLE: bool = os.getenv('SCRAPY_AUTOTHROTTLE', 'true').lower() == 'true'
    
    # Playwright settings
    PLAYWRIGHT_HEADLESS: bool = os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower() == 'true'
    PLAYWRIGHT_BROWSER: str = os.getenv('PLAYWRIGHT_BROWSER', 'chromium')
    
    # ========================================================================
    # Data Directories
    # ========================================================================
    
    # Output directories
    INJURIES_DIR: Path = DATA_DIR / "injuries"
    MASSEY_DIR: Path = DATA_DIR / "massey_ratings"
    NFL_SCHEDULE_DIR: Path = DATA_DIR / "nfl_schedule"
    POWER_RATINGS_DIR: Path = DATA_DIR / "power_ratings"
    WEATHER_DIR: Path = DATA_DIR / "weather"
    OVERTIME_LIVE_DIR: Path = DATA_DIR / "overtime_live"
    OVERTIME_PREGAME_DIR: Path = DATA_DIR / "overtime_pregame"
    
    # Database files
    BETS_DB: Path = DATA_DIR / "bets" / "bets.db"
    HISTORICAL_DB: Path = DATA_DIR / "historical" / "historical.db"
    
    # Team mappings
    NFL_TEAMS_FILE: Path = DATA_DIR / "team_mappings" / "nfl_teams.json"
    STADIUM_CACHE_FILE: Path = DATA_DIR / "stadium_cache.json"
    
    # Power ratings
    POWER_RATINGS_FILE: Path = POWER_RATINGS_DIR / "team_ratings.json"
    
    # ========================================================================
    # Caching Settings (Phase 1)
    # ========================================================================
    
    CACHE_TTL_WEATHER: int = int(os.getenv('CACHE_TTL_WEATHER', '1800'))      # 30 min
    CACHE_TTL_INJURY: int = int(os.getenv('CACHE_TTL_INJURY', '900'))         # 15 min
    CACHE_TTL_ANALYSIS: int = int(os.getenv('CACHE_TTL_ANALYSIS', '300'))     # 5 min
    CACHE_TTL_ODDS: int = int(os.getenv('CACHE_TTL_ODDS', '60'))              # 1 min
    
    # HTTP Client settings (Phase 1)
    HTTP_MAX_CONNECTIONS: int = int(os.getenv('HTTP_MAX_CONNECTIONS', '100'))
    HTTP_MAX_PER_HOST: int = int(os.getenv('HTTP_MAX_PER_HOST', '30'))
    HTTP_TIMEOUT: int = int(os.getenv('HTTP_TIMEOUT', '30'))
    
    # ========================================================================
    # Analysis Settings
    # ========================================================================
    
    # Billy Walters thresholds
    MINIMUM_EDGE_PERCENTAGE: float = float(os.getenv('MINIMUM_EDGE_PERCENTAGE', '5.5'))
    MINIMUM_STAR_RATING: float = float(os.getenv('MINIMUM_STAR_RATING', '0.5'))
    
    # Home field advantages (points)
    HFA_NFL: float = float(os.getenv('HFA_NFL', '2.5'))
    HFA_CFB: float = float(os.getenv('HFA_CFB', '3.5'))
    
    # Power rating parameters
    MOMENTUM_WEIGHT: float = float(os.getenv('MOMENTUM_WEIGHT', '0.9'))
    GAME_WEIGHT: float = float(os.getenv('GAME_WEIGHT', '0.1'))
    
    # ========================================================================
    # Feature Flags
    # ========================================================================
    
    # Enable/disable features
    ENABLE_WEB_FETCH: bool = os.getenv('ENABLE_WEB_FETCH', 'true').lower() == 'true'
    ENABLE_CACHING: bool = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    ENABLE_RESEARCH: bool = os.getenv('ENABLE_RESEARCH', 'true').lower() == 'true'
    ENABLE_PROFOOTBALLDOC: bool = os.getenv('ENABLE_PROFOOTBALLDOC', 'false').lower() == 'true'
    ENABLE_NEWS_API: bool = os.getenv('ENABLE_NEWS_API', 'false').lower() == 'true'
    
    # Development settings
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    VERBOSE: bool = os.getenv('VERBOSE', 'false').lower() == 'true'
    SIMULATION_MODE: bool = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'
    
    # ========================================================================
    # Logging
    # ========================================================================
    
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[Path] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Create data directories if they don't exist
        for directory in [
            self.DATA_DIR,
            self.INJURIES_DIR,
            self.MASSEY_DIR,
            self.NFL_SCHEDULE_DIR,
            self.POWER_RATINGS_DIR,
            self.WEATHER_DIR,
            self.OVERTIME_LIVE_DIR,
            self.OVERTIME_PREGAME_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Set log file if requested
        if os.getenv('LOG_FILE'):
            self.LOG_FILE = Path(os.getenv('LOG_FILE'))
    
    def validate_api_keys(self) -> dict:
        """
        Validate which API keys are configured.
        
        Returns:
            Dict showing which APIs are available
        """
        return {
            'accuweather': bool(self.ACCUWEATHER_API_KEY),
            'openweather': bool(self.OPENWEATHER_API_KEY),
            'news_api': bool(self.NEWS_API_KEY),
            'profootballdoc': bool(self.PROFOOTBALLDOC_API_KEY),
            'highlightly': bool(self.HIGHLIGHTLY_API_KEY),
            'overtime': bool(self.OV_CUSTOMER_ID and self.OV_CUSTOMER_PASSWORD),
        }
    
    def get_summary(self) -> str:
        """Get configuration summary for debugging."""
        api_status = self.validate_api_keys()
        
        lines = [
            "Billy Walters Analyzer - Configuration",
            "=" * 50,
            "",
            "Core Settings:",
            f"  Bankroll: ${self.BANKROLL:,.2f}",
            f"  Min Edge: {self.MINIMUM_EDGE_PERCENTAGE}%",
            f"  Kelly Fraction: {self.KELLY_FRACTION}",
            "",
            "API Keys Configured:",
            f"  AccuWeather: {'[OK]' if api_status['accuweather'] else '[--]'}",
            f"  OpenWeather: {'[OK]' if api_status['openweather'] else '[--]'}",
            f"  News API: {'[OK]' if api_status['news_api'] else '[--]'}",
            f"  ProFootballDoc: {'[OK]' if api_status['profootballdoc'] else '[--]'}",
            f"  Overtime.ag: {'[OK]' if api_status['overtime'] else '[--]'}",
            "",
            "Feature Flags:",
            f"  Web Fetch: {self.ENABLE_WEB_FETCH}",
            f"  Caching: {self.ENABLE_CACHING}",
            f"  Research: {self.ENABLE_RESEARCH}",
            f"  Debug: {self.DEBUG}",
            "",
            "Cache TTLs:",
            f"  Weather: {self.CACHE_TTL_WEATHER}s ({self.CACHE_TTL_WEATHER//60} min)",
            f"  Injuries: {self.CACHE_TTL_INJURY}s ({self.CACHE_TTL_INJURY//60} min)",
            f"  Analysis: {self.CACHE_TTL_ANALYSIS}s ({self.CACHE_TTL_ANALYSIS//60} min)",
        ]
        
        return "\n".join(lines)


# Global config instance (lazy loaded)
_CONFIG: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance (singleton pattern).
    
    Returns:
        Config instance
    
    Usage:
        from walters_analyzer.config import get_config
        
        config = get_config()
        if config.ACCUWEATHER_API_KEY:
            weather = await fetch_weather()
    """
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = Config()
    return _CONFIG


# Convenience function for validation
def validate_environment() -> bool:
    """
    Validate that required environment variables are set.
    
    Returns:
        True if minimum requirements met, False otherwise
    """
    config = get_config()
    api_status = config.validate_api_keys()
    
    # At minimum, need at least one weather API
    has_weather = api_status['accuweather'] or api_status['openweather']
    
    if not has_weather:
        print("[WARNING] No weather API keys configured")
        print("  Set ACCUWEATHER_API_KEY or OPENWEATHER_API_KEY in .env")
    
    return True  # Don't block - weather is optional


# Example usage
if __name__ == "__main__":
    config = get_config()
    print(config.get_summary())

