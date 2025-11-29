"""
Massey Ratings Scraper Module

Power ratings collection from MasseyRatings.com for
edge calculation in the Billy Walters methodology.

Features:
    - Playwright-based browser automation
    - Network interception for API monitoring
    - Supports NFL and NCAAF ratings
"""

from scrapers.massey.ratings_scraper import MasseyRatingsScraper

__all__ = [
    "MasseyRatingsScraper",
]
