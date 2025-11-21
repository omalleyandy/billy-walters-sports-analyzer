#!/usr/bin/env python3
"""Week 12 Collection - Working Version"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from src.data.overtime_api_client import OvertimeApiClient


async def collect_week12_working():
    """Collect Week 12 with what works"""

    print("\n" + "=" * 60)
    print("WEEK 12 NFL DATA COLLECTION")
    print("Billy Walters System - Integrated APIs")
    print("=" * 60)

    results = {}

    # OVERTIME - Your BEST source!
    print("\n1. Overtime.ag (Direct API - No CloudFlare!)...")
    overtime = OvertimeApiClient()

    # Get NFL
    nfl_data = await overtime.scrape_nfl()
    results["nfl"] = nfl_data
    print(f"   [OK] NFL: {len(nfl_data['games'])} games")

    # Get NCAAF too
    ncaaf_data = await overtime.scrape_ncaaf()
    results["ncaaf"] = ncaaf_data
    print(f"   [OK] NCAAF: {len(ncaaf_data['games'])} games")

    # Display all NFL games for analysis
    print("\n" + "=" * 60)
    print("NFL WEEK 12 GAMES (from Overtime.ag)")
    print("=" * 60)
    for i, g in enumerate(nfl_data["games"], 1):
        print(
            f"{i:2}. {g['away_team']:20} @ {g['home_team']:20} | "
            f"Spread: {g['spread']['home']:+5.1f} | "
            f"O/U: {g['total']['points']:5.1f} | "
            f"ML: {g['moneyline']['away']:+4}/{g['moneyline']['home']:+4}"
        )

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("data/week12")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"odds_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n[OK] Saved to: {output_file}")
    print(
        f"[OK] Total games: {len(nfl_data['games'])} NFL, {len(ncaaf_data['games'])} NCAAF"
    )

    return results


if __name__ == "__main__":
    asyncio.run(collect_week12_working())
