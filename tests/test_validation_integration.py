"""
Test script to verify validation integration.

This tests the validation modules work correctly together.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add hooks to path (now in tests/, need to go up to project root then to .claude/hooks)
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "hooks"))

from validation_logger import ValidationLogger, get_logger
from mcp_validation import (
    validate_odds_data,
    validate_weather_data,
    validate_game_data,
    fetch_and_validate_odds
)

import pytest


@pytest.mark.asyncio
async def test_validation_integration():
    """Test the full validation integration."""
    print("=" * 60)
    print("Validation Integration Test")
    print("=" * 60)

    # Test 1: Valid odds
    print("\n1. Testing valid odds validation...")
    odds_result = await validate_odds_data({
        'spread': -2.5,
        'over_under': 47.5,
        'moneyline_home': -135,
        'moneyline_away': 115
    })
    print(f"   Valid: {odds_result['valid']}")
    assert odds_result['valid'], "Valid odds should pass"

    # Test 2: Invalid odds
    print("\n2. Testing invalid odds validation...")
    invalid_odds_result = await validate_odds_data({
        'spread': -75.5,  # Invalid
        'over_under': 15   # Invalid
    })
    print(f"   Valid: {invalid_odds_result['valid']}")
    print(f"   Errors: {invalid_odds_result.get('errors', [])}")
    assert not invalid_odds_result['valid'], "Invalid odds should fail"
    assert len(invalid_odds_result['errors']) == 2, "Should have 2 errors"

    # Test 3: Valid weather
    print("\n3. Testing valid weather validation...")
    weather_result = await validate_weather_data({
        'temperature': 45,
        'wind_speed': 12,
        'precipitation_probability': 0.3
    })
    print(f"   Valid: {weather_result['valid']}")
    assert weather_result['valid'], "Valid weather should pass"

    # Test 4: Valid game
    print("\n4. Testing valid game validation...")
    game_result = await validate_game_data({
        'game_id': 'NFL_2025_W10_BUF_KC',
        'home_team': 'KC',
        'away_team': 'BUF',
        'game_date': '2025-11-16T13:00:00Z',
        'league': 'NFL'
    })
    print(f"   Valid: {game_result['valid']}")
    assert game_result['valid'], "Valid game should pass"

    # Test 5: Invalid game (missing fields)
    print("\n5. Testing invalid game validation...")
    invalid_game_result = await validate_game_data({
        'game_id': 'NFL_2025_W10_BUF_KC',
        # Missing home_team, away_team, game_date
    })
    print(f"   Valid: {invalid_game_result['valid']}")
    print(f"   Errors: {invalid_game_result.get('errors', [])}")
    assert not invalid_game_result['valid'], "Invalid game should fail"

    # Test 6: Fetch and validate with mock function
    print("\n6. Testing fetch_and_validate_odds...")

    async def mock_fetch_odds(game_id):
        return {
            'spread': -3.5,
            'over_under': 45.5,
            'moneyline_home': -150,
            'moneyline_away': 130
        }

    try:
        validated_odds = await fetch_and_validate_odds(
            'NFL_2025_W10_TEST',
            mock_fetch_odds
        )
        print(f"   Success: Fetched and validated odds")
        print(f"   Spread: {validated_odds['spread']}")
    except ValueError as e:
        print(f"   ERROR: {e}")
        raise

    # Test 7: Fetch and validate should raise on invalid data
    print("\n7. Testing fetch_and_validate_odds with invalid data...")

    async def mock_fetch_invalid_odds(game_id):
        return {
            'spread': -100,  # Invalid
            'over_under': 5   # Invalid
        }

    try:
        await fetch_and_validate_odds(
            'NFL_2025_W10_INVALID',
            mock_fetch_invalid_odds
        )
        print("   ERROR: Should have raised ValueError!")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   Correctly raised ValueError: {str(e)[:80]}...")

    # Get logger statistics
    print("\n" + "=" * 60)
    print("Validation Logger Statistics")
    print("=" * 60)
    logger = get_logger()
    stats = logger.get_statistics()
    print(json.dumps(stats, indent=2))

    print("\n" + "=" * 60)
    print("All Tests Passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_validation_integration())
