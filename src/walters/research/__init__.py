"""
Research Module - Multi-source data gathering for Billy Walters methodology.

Integrates:
- Your existing Scrapy spiders (ESPN, Massey, Overtime)
- New API calls (ProFootballDoc, News, Weather)
- Phase 1 components (HTTP client, caching, models)

Usage:
    from walters.research import ScrapyBridge, ResearchEngine

    # Load existing Scrapy data
    bridge = ScrapyBridge()
    injuries = bridge.load_latest_injuries(sport="nfl")

    # Use with ResearchEngine
    engine = ResearchEngine()
    analysis = await engine.comprehensive_injury_research("Kansas City Chiefs")
"""

__all__ = [
    'ScrapyBridge',
    'ResearchEngine',
]

from .scrapy_bridge import ScrapyBridge
from .engine import ResearchEngine
