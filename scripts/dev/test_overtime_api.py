"""
Test the reverse-engineered Overtime.ag API endpoint.

This script tests the discovered API endpoint that bypasses Playwright/CloudFlare:
POST https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering

Based on data/overtime_libs.js line 4278 ServiceCaller wiring.
"""

import json
import pathlib
from datetime import datetime

import requests


def test_overtime_api(sport_type: str = "Football", sport_sub_type: str = "NFL"):
    """
    Test the Overtime.ag API endpoint.

    Args:
        sport_type: "Football" (NFL/NCAAF)
        sport_sub_type: "NFL" or "College Football"
    """
    url = "https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering"

    payload = {
        "sportType": sport_type,
        "sportSubType": sport_sub_type,
        "wagerType": "Straight Bet",
        "hoursAdjustment": 0,
        "periodNumber": 0,
        "gameNum": None,
        "parentGameNum": None,
        "teaserName": "",
        "requestMode": "G",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    }

    print("\n[TEST] Overtime.ag API Endpoint")
    print(f"Sport: {sport_type} - {sport_sub_type}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()

        data = resp.json()

        # Check response structure
        print("[OK] Response received")
        print(f"Status: {resp.status_code}")

        if "d" in data:
            print("\n[STRUCTURE]")
            print("  'd' key present: Yes")

            if "Data" in data["d"]:
                print("  'Data' key present: Yes")

                if "GameLines" in data["d"]["Data"]:
                    games = data["d"]["Data"]["GameLines"]
                    print("  'GameLines' key present: Yes")
                    print(f"  Games found: {len(games)}")

                    # Save full response
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_dir = pathlib.Path("output/overtime_api_test")
                    output_dir.mkdir(parents=True, exist_ok=True)

                    full_path = output_dir / f"overtime_api_full_{timestamp}.json"
                    full_path.write_text(json.dumps(data, indent=2))
                    print(f"\n[SAVED] Full response: {full_path}")

                    # Save just games
                    games_path = output_dir / f"overtime_api_games_{timestamp}.json"
                    games_path.write_text(json.dumps(games, indent=2))
                    print(f"[SAVED] Games only: {games_path}")

                    # Show sample game
                    if games:
                        print("\n[SAMPLE GAME]")
                        sample = games[0]
                        print(json.dumps(sample, indent=2)[:500] + "...")

                        # Show available keys
                        print("\n[AVAILABLE KEYS]")
                        for key in sample.keys():
                            print(f"  - {key}")

                    return games
                else:
                    print("  'GameLines' key present: No")
                    print(f"  Available keys: {list(data['d']['Data'].keys())}")
            else:
                print("  'Data' key present: No")
                print(f"  Available keys: {list(data['d'].keys())}")
        else:
            print("\n[ERROR] Unexpected response structure")
            print(f"Available keys: {list(data.keys())}")

        return None

    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Request failed: {e}")
        return None


def compare_with_current_scraper():
    """Compare API response with current Playwright scraper output."""
    print("\n" + "=" * 60)
    print("COMPARISON: API vs Playwright Scraper")
    print("=" * 60)

    # Find latest Playwright scraper output
    playoff_dir = pathlib.Path("output/overtime/nfl/pregame")
    if playoff_dir.exists():
        files = sorted(playoff_dir.glob("overtime_nfl_walters_*.json"), reverse=True)
        if files:
            latest = files[0]
            print(f"\n[CURRENT SCRAPER] Latest output: {latest.name}")

            with open(latest) as f:
                playwright_data = json.load(f)

            print(f"Games found: {len(playwright_data)}")

            if playwright_data:
                print("\n[SAMPLE GAME - Playwright]")
                print(json.dumps(playwright_data[0], indent=2)[:500] + "...")
        else:
            print("\n[WARNING] No Playwright scraper output found")
    else:
        print("\n[WARNING] Playoff directory does not exist")


if __name__ == "__main__":
    # Test NFL
    print("\n" + "=" * 60)
    print("TEST 1: NFL")
    print("=" * 60)
    nfl_games = test_overtime_api("Football", "NFL")

    # Test NCAAF
    print("\n" + "=" * 60)
    print("TEST 2: NCAAF")
    print("=" * 60)
    ncaaf_games = test_overtime_api("Football", "College Football")

    # Compare with current scraper
    compare_with_current_scraper()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"NFL games found: {len(nfl_games) if nfl_games else 0}")
    print(f"NCAAF games found: {len(ncaaf_games) if ncaaf_games else 0}")

    if nfl_games or ncaaf_games:
        print("\n[SUCCESS] API endpoint working!")
        print("Next steps: Build OvertimeApiClient and update /scrape-overtime command")
    else:
        print("\n[FAIL] No games found - may need authentication")
