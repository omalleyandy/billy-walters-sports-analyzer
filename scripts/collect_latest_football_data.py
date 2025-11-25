#!/usr/bin/env python3
"""
Collect up-to-date data from ESPN.com, NFL.com, Massey Ratings, and Overtime.ag.

Outputs one JSON snapshot per league (NFL, NCAAF) containing:
- ESPN scoreboard + teams
- Overtime.ag odds (raw + Billy Walters format)
- Massey Ratings power numbers
- NFL.com schedule (NFL only)
"""

import asyncio
import json
import logging
import sys
from argparse import ArgumentParser
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

from src.data.espn_client import ESPNClient  # noqa: E402
from src.data.massey_ratings_scraper import MasseyRatingsScraper  # noqa: E402
from src.data.nfl_com_client import NFLComClient  # noqa: E402
from src.data.overtime_api_client import OvertimeApiClient  # noqa: E402

logger = logging.getLogger("collect_latest_football_data")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


async def collect_league_snapshot(
    league: str, week: int | None, season: int | None, nfl_token: str | None
) -> dict[str, Any]:
    """Collect a snapshot for a single league."""
    snapshot: dict[str, Any] = {
        "league": league,
        "requested_week": week,
        "requested_season": season,
        "collected_at": datetime.now(UTC).isoformat(),
        "sources": {},
    }

    # ESPN - scoreboard + teams (used to infer current week/season)
    resolved_week = week
    resolved_season = season
    try:
        async with ESPNClient() as espn:
            scoreboard = await espn.get_scoreboard(league, week=week, season=season)
            teams = await espn.get_teams(league)

        resolved_week = resolved_week or scoreboard.get("week", {}).get("number")
        resolved_season = resolved_season or scoreboard.get("season", {}).get("year")

        snapshot["sources"]["espn"] = {
            "scoreboard": scoreboard,
            "teams": teams,
        }
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error(f"ESPN {league} fetch failed: {exc}")
        snapshot["sources"]["espn"] = {"error": str(exc)}

    # Overtime.ag - odds
    try:
        overtime_client = OvertimeApiClient()
        sport_sub_type = "NFL" if league == "NFL" else "College Football"
        overtime_raw = await overtime_client.fetch_games(
            sport_type="Football",
            sport_sub_type=sport_sub_type,
        )
        snapshot["sources"]["overtime"] = {
            "raw": overtime_raw,
            "walters_format": overtime_client.convert_to_billy_walters_format(
                overtime_raw, league
            ),
        }
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error(f"Overtime.ag {league} fetch failed: {exc}")
        snapshot["sources"]["overtime"] = {"error": str(exc)}

    # Massey Ratings - power numbers
    try:
        scraper = MasseyRatingsScraper()
        if league == "NFL":
            massey = await scraper.scrape_nfl_ratings(save=False)
        else:
            massey = await scraper.scrape_ncaaf_ratings(save=False)
        snapshot["sources"]["massey"] = massey
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error(f"Massey Ratings {league} fetch failed: {exc}")
        snapshot["sources"]["massey"] = {"error": str(exc)}

    # NFL.com - official schedule (NFL only)
    if league == "NFL":
        if resolved_week and resolved_season:
            try:
                nfl_client = NFLComClient(auth_token=nfl_token)
                try:
                    schedule = await nfl_client.get_schedule(
                        season=resolved_season, week=resolved_week
                    )
                finally:
                    await nfl_client.close()

                snapshot["sources"]["nfl_com"] = {
                    "season": resolved_season,
                    "week": resolved_week,
                    "games": [game.model_dump(mode="json") for game in schedule],
                }
            except Exception as exc:  # pragma: no cover - network dependent
                logger.error(f"NFL.com schedule fetch failed: {exc}")
                snapshot["sources"]["nfl_com"] = {"error": str(exc)}
        else:
            snapshot["sources"]["nfl_com"] = {
                "error": "No week/season available to fetch NFL.com schedule",
                "resolved_week": resolved_week,
                "resolved_season": resolved_season,
            }
    else:
        snapshot["sources"]["nfl_com"] = {
            "note": "NFL.com schedule not applicable to NCAAF"
        }

    return snapshot


def parse_args():
    """Parse CLI arguments."""
    parser = ArgumentParser(
        description=(
            "Collect latest NFL/NCAAF data from ESPN, NFL.com, "
            "Massey Ratings, and Overtime.ag"
        )
    )
    parser.add_argument(
        "--league",
        choices=["NFL", "NCAAF", "both"],
        default="both",
        help="Which league to collect (default: both)",
    )
    parser.add_argument(
        "--week",
        type=int,
        help="Target week (defaults to current per ESPN scoreboard)",
    )
    parser.add_argument(
        "--season",
        type=int,
        help="Season year (used for NFL.com schedule; inferred if omitted)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/unified"),
        help="Directory to write snapshot JSON files",
    )
    parser.add_argument(
        "--nfl-token",
        type=str,
        help="Bearer token for NFL.com API (or set NFL_COM_AUTH_TOKEN env var)",
    )
    return parser.parse_args()


async def main() -> dict[str, str]:
    """Entry point."""
    args = parse_args()
    leagues = ["NFL", "NCAAF"] if args.league == "both" else [args.league]
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Debug token handling
    nfl_token = args.nfl_token
    if nfl_token:
        # Show first/last few chars for security (don't log full token)
        token_preview = (
            f"{nfl_token[:4]}...{nfl_token[-4:]}" if len(nfl_token) > 8 else "***"
        )
        logger.info(f"NFL token provided via --nfl-token: {token_preview}")
    else:
        import os

        env_token = os.getenv("NFL_COM_AUTH_TOKEN") or os.getenv("NFL_COM_BEARER_TOKEN")
        if env_token:
            token_preview = (
                f"{env_token[:4]}...{env_token[-4:]}" if len(env_token) > 8 else "***"
            )
            logger.info(f"NFL token found in environment: {token_preview}")
            nfl_token = env_token
        else:
            logger.warning(
                "No NFL token provided. Set --nfl-token or NFL_COM_AUTH_TOKEN env var"
            )

    written: dict[str, str] = {}
    for league in leagues:
        logger.info(f"Collecting latest data for {league}...")
        snapshot = await collect_league_snapshot(
            league, args.week, args.season, nfl_token
        )

        out_file = output_dir / f"latest_{league.lower()}.json"
        out_file.write_text(json.dumps(snapshot, indent=2))
        written[league] = str(out_file)
        logger.info(f"Wrote {league} snapshot to {out_file}")

    return written


if __name__ == "__main__":
    asyncio.run(main())
