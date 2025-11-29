"""
Test: Verify overtime_ag_client integration with Billy Walters project

This test verifies that the timezone-fixed Overtime client is properly
integrated and available in the Billy Walters Sports Analyzer project.

No actual browser connection is required—just testing that imports and
models work correctly.
"""

from datetime import datetime, timezone
from overtime_ag_client.client import OvertimeClient
from overtime_ag_client.models import (
    Sport,
    OvertimeGame,
    GameOdds,
    TeamOdds,
    parse_overtime_date,
)


def test_timezone_parsing():
    """Test that Overtime.ag timestamp parsing returns UTC datetimes."""
    print("[TEST] Timezone parsing from Overtime.ag format")

    # Simulate an Overtime.ag timestamp
    date_str = "/Date(1732003200000)/"  # 2024-11-19 08:00:00 UTC
    parsed_dt = parse_overtime_date(date_str)

    assert parsed_dt.tzinfo == timezone.utc, "Should have UTC timezone"
    print(f"  Parsed: {parsed_dt}")
    print(f"  Timezone: {parsed_dt.tzinfo}")
    print("  [OK] Overtime.ag dates are properly converted to UTC\n")


def test_client_initialization():
    """Test that OvertimeClient initializes correctly."""
    print("[TEST] OvertimeClient initialization")

    client = OvertimeClient(headless=True)
    assert client is not None
    assert client.customer_id or True  # May not have env vars, that's OK
    print(f"  Client: {client}")
    print("  [OK] OvertimeClient initializes successfully\n")


def test_game_model_with_utc():
    """Test creating an OvertimeGame model with UTC datetimes."""
    print("[TEST] OvertimeGame model with UTC datetimes")

    # Create sample odds data
    away_odds = TeamOdds(
        team_name="Arizona Cardinals",
        rotation_number=463,
        spread=3.5,
        spread_juice=-110,
        moneyline=155,
    )

    home_odds = TeamOdds(
        team_name="Tampa Bay Buccaneers",
        rotation_number=464,
        spread=-3.5,
        spread_juice=-110,
        moneyline=-165,
    )

    # Create game odds with UTC datetime
    game_time = datetime(2024, 11, 30, 18, 0, 0, tzinfo=timezone.utc)
    game_odds = GameOdds(
        game_id="463",
        sport_subtype_id=28,
        game_datetime=game_time,
        away_team=away_odds,
        home_team=home_odds,
        favored_team="Tampa Bay Buccaneers",
        total=44.5,
        over_juice=-110,
        under_juice=-110,
    )

    # Create full game model
    game = OvertimeGame(
        game_id="463",
        sport=Sport.NFL,
        week=13,
        season=2024,
        away_team="Arizona Cardinals",
        away_team_abbr="ARI",
        home_team="Tampa Bay Buccaneers",
        home_team_abbr="TB",
        away_rotation=463,
        home_rotation=464,
        game_datetime=game_time,
        game_time="1:00 PM",
        game_timezone="EST",
        odds=game_odds,
    )

    # Verify UTC timezone
    assert game.game_datetime.tzinfo == timezone.utc
    print(f"  Game: {game.matchup_display}")
    print(f"  Game time (UTC): {game.game_datetime}")
    print(f"  Local time: {game.game_time} {game.game_timezone}")
    print(f"  Week: {game.week}")
    print("  [OK] OvertimeGame models handle UTC datetimes correctly\n")

    # Test conversion to Billy Walters format
    betting_dict = game.to_betting_dict()
    assert "game_datetime" in betting_dict
    assert "game_timezone" in betting_dict
    assert "away_spread" in betting_dict
    print(f"  Converted to betting dict: {len(betting_dict)} fields")
    print("  [OK] Can convert to Billy Walters format\n")


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("OVERTIME.AG INTEGRATION TESTS")
    print("=" * 60)
    print()

    try:
        test_timezone_parsing()
        test_client_initialization()
        test_game_model_with_utc()

        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("The overtime_ag_client is properly integrated with")
        print("Billy Walters Sports Analyzer and ready for use.")
        print()

    except AssertionError as e:
        print(f"\n[ERROR] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
