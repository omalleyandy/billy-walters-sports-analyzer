"""
MCP Validation Module for Billy Walters Sports Analyzer

Provides async validation functions that integrate with the validate_data.py hook.
Used by the autonomous agent and MCP server for data quality assurance.
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# Handle both direct execution and import
try:
    from .validation_logger import get_logger
except ImportError:
    from validation_logger import get_logger

# Get validation logger
logger = get_logger()

# Path to validation script
VALIDATION_SCRIPT = Path(__file__).parent / "validate_data.py"


async def validate_data(
    data_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate data using the validate_data.py hook.

    Args:
        data_type: Type of data ('odds', 'weather', 'game')
        data: Data to validate

    Returns:
        Validation result dict with 'valid', 'errors', 'message' keys

    Raises:
        ValueError: If validation fails
    """
    # Prepare input for validation script
    validation_input = {
        'type': data_type,
        'data': data
    }

    # Run validation script
    try:
        process = await asyncio.create_subprocess_exec(
            'python',
            str(VALIDATION_SCRIPT),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate(
            input=json.dumps(validation_input).encode()
        )

        # Parse result
        if process.returncode == 0:
            result = json.loads(stdout.decode())
            return result
        else:
            # Validation failed
            result = json.loads(stdout.decode())
            return result

    except Exception as e:
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }


async def fetch_and_validate_odds(
    game_id: str,
    fetch_function: Callable[[str], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Fetch odds data and validate it.

    Args:
        game_id: Unique game identifier
        fetch_function: Async or sync function to fetch odds data

    Returns:
        Validated odds data

    Raises:
        ValueError: If validation fails

    Example:
        async def get_odds(game_id):
            return {'spread': -2.5, 'over_under': 47.5, ...}

        odds = await fetch_and_validate_odds('NFL_2025_W10_BUF_KC', get_odds)
    """
    # Fetch data
    if asyncio.iscoroutinefunction(fetch_function):
        odds_data = await fetch_function(game_id)
    else:
        odds_data = fetch_function(game_id)

    # Validate
    validation_result = await validate_data('odds', odds_data)

    # Log validation
    logger.log_odds_validation(
        game_id=game_id,
        odds_data=odds_data,
        is_valid=validation_result['valid'],
        errors=validation_result.get('errors')
    )

    # Raise error if invalid
    if not validation_result['valid']:
        errors = ', '.join(validation_result.get('errors', []))
        raise ValueError(f"Odds validation failed for {game_id}: {errors}")

    return odds_data


async def fetch_and_validate_weather(
    game_id: str,
    fetch_function: Callable[[str], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Fetch weather data and validate it.

    Args:
        game_id: Unique game identifier
        fetch_function: Async or sync function to fetch weather data

    Returns:
        Validated weather data

    Raises:
        ValueError: If validation fails

    Example:
        async def get_weather(game_id):
            return {'temperature': 45, 'wind_speed': 12, ...}

        weather = await fetch_and_validate_weather('NFL_2025_W10_BUF_KC', get_weather)
    """
    # Fetch data
    if asyncio.iscoroutinefunction(fetch_function):
        weather_data = await fetch_function(game_id)
    else:
        weather_data = fetch_function(game_id)

    # Validate
    validation_result = await validate_data('weather', weather_data)

    # Log validation
    logger.log_weather_validation(
        game_id=game_id,
        weather_data=weather_data,
        is_valid=validation_result['valid'],
        errors=validation_result.get('errors')
    )

    # Raise error if invalid
    if not validation_result['valid']:
        errors = ', '.join(validation_result.get('errors', []))
        raise ValueError(f"Weather validation failed for {game_id}: {errors}")

    return weather_data


async def fetch_and_validate_game(
    game_id: str,
    fetch_function: Callable[[str], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Fetch game data and validate it.

    Args:
        game_id: Unique game identifier
        fetch_function: Async or sync function to fetch game data

    Returns:
        Validated game data

    Raises:
        ValueError: If validation fails

    Example:
        async def get_game(game_id):
            return {
                'game_id': game_id,
                'home_team': 'KC',
                'away_team': 'BUF',
                'game_date': '2025-11-16T13:00:00Z',
                'league': 'NFL'
            }

        game = await fetch_and_validate_game('NFL_2025_W10_BUF_KC', get_game)
    """
    # Fetch data
    if asyncio.iscoroutinefunction(fetch_function):
        game_data = await fetch_function(game_id)
    else:
        game_data = fetch_function(game_id)

    # Validate
    validation_result = await validate_data('game', game_data)

    # Log validation
    logger.log_event(
        event_name='game_validation',
        data_type='game',
        validation_result=validation_result,
        context={
            'game_id': game_id,
            'home_team': game_data.get('home_team'),
            'away_team': game_data.get('away_team'),
            'league': game_data.get('league')
        }
    )

    # Raise error if invalid
    if not validation_result['valid']:
        errors = ', '.join(validation_result.get('errors', []))
        raise ValueError(f"Game validation failed for {game_id}: {errors}")

    return game_data


async def validate_odds_data(odds_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate odds data without fetching.

    Args:
        odds_data: Odds data to validate

    Returns:
        Validation result

    Example:
        result = await validate_odds_data({
            'spread': -2.5,
            'over_under': 47.5,
            'moneyline_home': -135,
            'moneyline_away': 115
        })
    """
    return await validate_data('odds', odds_data)


async def validate_weather_data(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate weather data without fetching.

    Args:
        weather_data: Weather data to validate

    Returns:
        Validation result

    Example:
        result = await validate_weather_data({
            'temperature': 45,
            'wind_speed': 12,
            'precipitation_probability': 0.3
        })
    """
    return await validate_data('weather', weather_data)


async def validate_game_data(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate game data without fetching.

    Args:
        game_data: Game data to validate

    Returns:
        Validation result

    Example:
        result = await validate_game_data({
            'game_id': 'NFL_2025_W10_BUF_KC',
            'home_team': 'KC',
            'away_team': 'BUF',
            'game_date': '2025-11-16T13:00:00Z',
            'league': 'NFL'
        })
    """
    return await validate_data('game', game_data)


# Synchronous wrappers for non-async contexts
def validate_odds_sync(odds_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for validate_odds_data."""
    return asyncio.run(validate_odds_data(odds_data))


def validate_weather_sync(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for validate_weather_data."""
    return asyncio.run(validate_weather_data(weather_data))


def validate_game_sync(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for validate_game_data."""
    return asyncio.run(validate_game_data(game_data))


if __name__ == "__main__":
    # Example usage
    async def example():
        print("=" * 60)
        print("MCP Validation Examples")
        print("=" * 60)

        # Example 1: Validate odds directly
        print("\n1. Validating odds data...")
        odds = {
            'spread': -2.5,
            'over_under': 47.5,
            'moneyline_home': -135,
            'moneyline_away': 115
        }
        result = await validate_odds_data(odds)
        print(f"   Result: {result}")

        # Example 2: Validate invalid odds
        print("\n2. Validating invalid odds data...")
        bad_odds = {
            'spread': -75.5,  # Invalid
            'over_under': 15,  # Invalid
            'moneyline_home': -135,
            'moneyline_away': 115
        }
        result = await validate_odds_data(bad_odds)
        print(f"   Result: {result}")

        # Example 3: Fetch and validate with mock function
        print("\n3. Fetch and validate odds...")

        async def mock_fetch_odds(game_id):
            return {
                'spread': -3.5,
                'over_under': 45.5,
                'moneyline_home': -150,
                'moneyline_away': 130
            }

        try:
            validated_odds = await fetch_and_validate_odds(
                'NFL_2025_W10_BUF_KC',
                mock_fetch_odds
            )
            print(f"   Success: {validated_odds}")
        except ValueError as e:
            print(f"   Error: {e}")

        # Print logger statistics
        print("\n" + "=" * 60)
        print("Validation Statistics")
        print("=" * 60)
        stats = logger.get_statistics()
        print(json.dumps(stats, indent=2))

    asyncio.run(example())
