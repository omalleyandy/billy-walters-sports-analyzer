"""
CLI Commands Package

Each module exports a typer.Typer() app that gets registered with the main CLI.

Available command groups:
- analyze: Edge detection, game analysis, injury/weather impact
- scrape: Data collection from various sources
- clv: Closing Line Value tracking
- status: System health checks
- power_ratings: Power ratings management
- db: Database operations
- monitor: Line movement monitoring
"""

from . import analyze
from . import scrape
from . import clv
from . import status
from . import power_ratings
from . import db
from . import monitor

__all__ = [
    "analyze",
    "scrape", 
    "clv",
    "status",
    "power_ratings",
    "db",
    "monitor",
]
