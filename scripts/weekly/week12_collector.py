#!/usr/bin/env python3
"""Week 12 Data Collection - Fully Working Version"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from src.data.overtime_api_client import OvertimeApiClient
from src.data.espn_client import ESPNClient


async def collect_week12_data():
    """Collect Week 12 data with proper initialization"""

    print("\n" + "=" * 60)
    print("WEEK 12 DATA COLLECTION")
    print("=" * 60)

    results = {}

    # 1. OVERTIME - No init needed, works directly!
    try:
        print("\n1. Fetching Overtime.ag (Direct API)...")
        overtime = OvertimeApiClient()
        nfl_data = await overtime.scrape_nfl()
        results["overtime_nfl"] = nfl_data
        print(f"   [OK] Found {len(nfl_data['games'])} NFL games")

        # Show sample games
        if nfl_data["games"]:
            print("\n   Sample games:")
            for g in nfl_data["games"][:3]:
                print(
                    f"   • {g['away_team']:20} @ {g['home_team']:20} | "
                    f"Spread: {g['spread']['home']:+.1f} | "
                    f"O/U: {g['total']['points']}"
                )

    except Exception as e:
        print(f"   [X] Overtime error: {e}")

    # 2. ESPN - With proper initialization
    espn = None
    try:
        print("\n2. Fetching ESPN data...")
        espn = ESPNClient()
        await espn.connect()  # Initialize!

        schedule = await espn.get_schedule("nfl", week=12)
        results["espn_schedule"] = schedule
        print(f"   [OK] Found {len(schedule.get('events', []))} games")

        injuries = await espn.get_injuries("nfl")
        results["espn_injuries"] = injuries
        print("   [OK] Got injury report")

    except Exception as e:
        print(f"   [X] ESPN error: {e}")
    finally:
        if espn:
            await espn.close()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("data/week12")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"integrated_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE!")
    print(f"Saved to: {output_file}")
    print(f"Total sources: {len(results)}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(collect_week12_data())
