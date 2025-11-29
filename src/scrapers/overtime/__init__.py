"""
Overtime.ag Scraper Module

Direct API client for fetching pregame odds from Overtime.ag.
Uses reverse-engineered API endpoint (no browser automation needed).

Features:
    - Fast: ~2-3 seconds per league
    - No authentication required
    - UTC datetime parsing from .NET timestamps
    - Week extraction from NFL comments
    - Eastern Time conversion for display

Client:
    OvertimeApiClient: Direct API client (v2.1.0)
"""

from scrapers.overtime.api_client import OvertimeApiClient

__all__ = [
    "OvertimeApiClient",
]
