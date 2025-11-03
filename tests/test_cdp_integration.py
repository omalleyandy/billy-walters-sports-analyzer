"""
Tests for CDP odds scraper integration.

Tests the integrated CDP network interception and odds change tracking features.
"""

import os
import tempfile
from pathlib import Path

from scrapers.overtime_live.cdp_helpers import (
    OddsChangeDetector,
    SQLiteOddsStorage,
    RedisOddsStorage,
    is_odds_api_response,
    format_odds_display,
)
from scrapers.overtime_live.spiders.overtime_live_spider import OvertimeLiveSpider


def test_spider_initialization():
    """Test spider initializes with monitor parameter."""
    spider = OvertimeLiveSpider(monitor="10")
    assert spider.monitor_interval == 10
    
    spider_no_monitor = OvertimeLiveSpider()
    assert spider_no_monitor.monitor_interval is None


def test_is_odds_api_response():
    """Test URL pattern matching for odds APIs."""
    assert is_odds_api_response("/api/odds") is True
    assert is_odds_api_response("https://overtime.ag/sports/Api/GetCurrent") is True
    assert is_odds_api_response("/sports/Api/Offering.asmx/GetSportOffering") is True
    assert is_odds_api_response("https://example.com/static/css/style.css") is False


def test_sqlite_odds_storage():
    """Test SQLite odds storage operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_odds.db")
        storage = SQLiteOddsStorage(db_path)
        
        # Test store and retrieve
        test_odds = {
            'spread': {'away': {'line': -3.5, 'price': -110}},
            'total': {'over': {'line': 47.5, 'price': -110}}
        }
        storage.store_odds("test_game", test_odds)
        
        retrieved = storage.get_previous_odds("test_game")
        assert retrieved == test_odds
        
        # Test non-existent game
        none_odds = storage.get_previous_odds("nonexistent_game")
        assert none_odds is None
        
        storage.close()


def test_odds_change_detection():
    """Test odds change detection logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = SQLiteOddsStorage(os.path.join(tmpdir, "test.db"))
        detector = OddsChangeDetector(storage, tmpdir)
        
        # First game data (no previous - should not detect change)
        game1 = {
            'game_key': 'test_game',
            'teams': {'away': 'Team A', 'home': 'Team B'},
            'markets': {
                'spread': {'away': {'line': -3.0, 'price': -110}},
                'total': {'over': {'line': 47.0, 'price': -110}},
                'moneyline': {'away': {'price': -150}}
            }
        }
        changed = detector.check_and_log_changes(game1)
        assert changed is False
        
        # Updated game data (should detect change)
        game2 = {
            'game_key': 'test_game',
            'teams': {'away': 'Team A', 'home': 'Team B'},
            'markets': {
                'spread': {'away': {'line': -3.5, 'price': -110}},  # Changed
                'total': {'over': {'line': 47.5, 'price': -110}},   # Changed
                'moneyline': {'away': {'price': -150}}
            }
        }
        changed = detector.check_and_log_changes(game2)
        assert changed is True
        
        # Verify CSV was created
        csv_files = list(Path(tmpdir).glob("odds_changes_*.csv"))
        assert len(csv_files) > 0
        
        storage.close()


def test_format_odds_display():
    """Test odds formatting for console display."""
    game_data = {
        'teams': {'away': 'Alabama', 'home': 'LSU'},
        'markets': {
            'spread': {
                'away': {'line': -3.5, 'price': -110},
                'home': {'line': 3.5, 'price': -110}
            },
            'total': {
                'over': {'line': 47.5, 'price': -110},
                'under': {'line': 47.5, 'price': -110}
            },
            'moneyline': {
                'away': {'price': -150},
                'home': {'price': 130}
            }
        },
        'state': {'quarter': 2, 'clock': '10:32'}
    }
    
    formatted = format_odds_display(game_data)
    assert 'Alabama' in formatted
    assert 'LSU' in formatted
    assert '-3.5' in formatted
    assert '47.5' in formatted
    assert '-150' in formatted


def test_redis_storage_initialization():
    """Test Redis storage initialization (may not be available)."""
    storage = RedisOddsStorage()
    # Should not raise an error even if Redis is unavailable
    # Just check it initializes
    assert hasattr(storage, 'available')
    
    if storage.available:
        # Only test if Redis is actually available
        storage.store_odds("test", {"spread": {"away": {"line": -3.0}}})
        retrieved = storage.get_previous_odds("test")
        assert retrieved is not None
        storage.close()


if __name__ == "__main__":
    # Run basic tests
    print("Testing spider initialization...")
    test_spider_initialization()
    print("[OK] Passed")
    
    print("Testing URL pattern matching...")
    test_is_odds_api_response()
    print("[OK] Passed")
    
    print("Testing SQLite storage...")
    test_sqlite_odds_storage()
    print("[OK] Passed")
    
    print("Testing odds change detection...")
    test_odds_change_detection()
    print("[OK] Passed")
    
    print("Testing odds formatting...")
    test_format_odds_display()
    print("[OK] Passed")
    
    print("Testing Redis storage initialization...")
    test_redis_storage_initialization()
    print("[OK] Passed")
    
    print("\n[SUCCESS] All tests passed!")

