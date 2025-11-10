"""
Unified configuration system for Billy Walters Sports Analyzer.

Consolidates settings from:
- Environment variables (.env)
- Billy Walters methodology config (JSON)
- Claude MCP config (JSON)
- Command-line arguments
"""

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
