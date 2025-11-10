#!/usr/bin/env python3
"""
Live Odds Monitoring Service
Tracks betting lines at regular intervals and detects sharp action
"""

import os
import json
import time
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()


class LiveOddsMonitor:
    """Monitor betting odds for specific matchups"""

    def __init__(self, interval_seconds: int = 900):
        self.interval = interval_seconds  # Default 15 minutes
        self.running = False
        self.monitored_games = []
        self.odds_history = []
        self.api_key = os.getenv("ODDS_API_KEY")

        if not self.api_key:
            raise ValueError("ODDS_API_KEY not found in environment")

        # Set up graceful shutdown
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def fetch_current_odds(self) -> list[dict]:
        """Fetch current NFL odds from The Odds API"""
        url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"

        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
            "dateFormat": "iso",
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Check API quota
            remaining = response.headers.get("x-requests-remaining")
            used = response.headers.get("x-requests-used")
            print(f"[API] Fetched {len(data)} games (quota: {used}/{500})")

            return data

        except Exception as e:
            print(f"[ERROR] Failed to fetch odds: {e}")
            return []

    def filter_game(self, games: list[dict], team1: str, team2: str) -> Optional[dict]:
        """Find a specific game by team names"""
        team1_lower = team1.lower()
        team2_lower = team2.lower()

        for game in games:
            away = game["away_team"].lower()
            home = game["home_team"].lower()

            if (team1_lower in away or team1_lower in home) and (
                team2_lower in away or team2_lower in home
            ):
                return game

        return None

    def detect_line_movement(self, current: dict, previous: dict) -> dict:
        """Detect and quantify line movements"""
        movements = {
            "spread": 0,
            "total": 0,
            "moneyline_away": 0,
            "moneyline_home": 0,
            "significant": False,
        }

        # Get first bookmaker data
        curr_bm = current.get("bookmakers", [{}])[0]
        prev_bm = previous.get("bookmakers", [{}])[0]

        if not curr_bm or not prev_bm:
            return movements

        # Compare spreads
        for market in curr_bm.get("markets", []):
            if market["key"] == "spreads":
                curr_home_spread = next(
                    (
                        o["point"]
                        for o in market["outcomes"]
                        if o["name"] == current["home_team"]
                    ),
                    None,
                )

                for prev_market in prev_bm.get("markets", []):
                    if prev_market["key"] == "spreads":
                        prev_home_spread = next(
                            (
                                o["point"]
                                for o in prev_market["outcomes"]
                                if o["name"] == previous["home_team"]
                            ),
                            None,
                        )

                        if curr_home_spread and prev_home_spread:
                            movements["spread"] = curr_home_spread - prev_home_spread

            # Compare totals
            elif market["key"] == "totals":
                curr_total = next(
                    (o["point"] for o in market["outcomes"] if o["name"] == "Over"),
                    None,
                )

                for prev_market in prev_bm.get("markets", []):
                    if prev_market["key"] == "totals":
                        prev_total = next(
                            (
                                o["point"]
                                for o in prev_market["outcomes"]
                                if o["name"] == "Over"
                            ),
                            None,
                        )

                        if curr_total and prev_total:
                            movements["total"] = curr_total - prev_total

        # Flag significant movements
        if abs(movements["spread"]) >= 0.5 or abs(movements["total"]) >= 0.5:
            movements["significant"] = True

        return movements

    def monitor_game(self, team1: str, team2: str):
        """Monitor a specific game at regular intervals"""
        print("=" * 80)
        print(f"LIVE ODDS MONITOR - {team1.upper()} vs {team2.upper()}")
        print("=" * 80)
        print(f"Interval: {self.interval} seconds ({self.interval // 60} minutes)")
        print("Press Ctrl+C to stop\n")

        self.running = True
        previous_odds = None
        check_count = 0

        while self.running:
            check_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"[{timestamp}] Check #{check_count}")

            # Fetch current odds
            all_games = self.fetch_current_odds()
            current_game = self.filter_game(all_games, team1, team2)

            if not current_game:
                print(f"[WARNING] Game not found: {team1} vs {team2}")
                time.sleep(self.interval)
                continue

            # Display current odds
            self.display_game_odds(current_game)

            # Detect movements
            if previous_odds:
                movements = self.detect_line_movement(current_game, previous_odds)

                if movements["significant"]:
                    print("\n[ALERT] SIGNIFICANT LINE MOVEMENT DETECTED!")
                    if movements["spread"]:
                        direction = (
                            "toward favorite"
                            if movements["spread"] < 0
                            else "toward dog"
                        )
                        print(f"  Spread: {movements['spread']:+.1f} ({direction})")
                    if movements["total"]:
                        direction = "DOWN" if movements["total"] < 0 else "UP"
                        print(f"  Total: {movements['total']:+.1f} ({direction})")

            # Store history
            self.odds_history.append(
                {
                    "timestamp": timestamp,
                    "game": current_game,
                    "movements": movements if previous_odds else None,
                }
            )

            previous_odds = current_game

            # Save history to file
            self.save_history(team1, team2)

            print(f"\nNext check in {self.interval} seconds...\n")
            time.sleep(self.interval)

    def display_game_odds(self, game: dict):
        """Display current odds for a game"""
        print(f"\n{game['away_team']} @ {game['home_team']}")

        bookmaker = game.get("bookmakers", [{}])[0]
        if not bookmaker:
            print("  No odds available")
            return

        for market in bookmaker.get("markets", []):
            if market["key"] == "spreads":
                away_spread = next(
                    (o for o in market["outcomes"] if o["name"] == game["away_team"]),
                    None,
                )
                home_spread = next(
                    (o for o in market["outcomes"] if o["name"] == game["home_team"]),
                    None,
                )

                if away_spread and home_spread:
                    print(
                        f"  Spread: {away_spread['point']:+.1f} ({away_spread['price']:+d}) / "
                        f"{home_spread['point']:+.1f} ({home_spread['price']:+d})"
                    )

            elif market["key"] == "totals":
                over = next(
                    (o for o in market["outcomes"] if o["name"] == "Over"), None
                )
                under = next(
                    (o for o in market["outcomes"] if o["name"] == "Under"), None
                )

                if over and under:
                    print(
                        f"  Total: O/U {over['point']} ({over['price']:+d}/{under['price']:+d})"
                    )

            elif market["key"] == "h2h":
                away_ml = next(
                    (o for o in market["outcomes"] if o["name"] == game["away_team"]),
                    None,
                )
                home_ml = next(
                    (o for o in market["outcomes"] if o["name"] == game["home_team"]),
                    None,
                )

                if away_ml and home_ml:
                    print(f"  ML: {away_ml['price']:+d} / {home_ml['price']:+d}")

    def save_history(self, team1: str, team2: str):
        """Save odds history to file"""
        output_dir = Path("data/odds/monitoring")
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{team1.replace(' ', '_')}_vs_{team2.replace(' ', '_')}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.odds_history, f, indent=2, default=str)

    def stop(self, signum=None, frame=None):
        """Stop monitoring gracefully"""
        print("\n\n[STOPPING] Shutting down monitor...")
        self.running = False

        if self.odds_history:
            print(f"Captured {len(self.odds_history)} odds snapshots")
            print("History saved to data/odds/monitoring/")

        sys.exit(0)


def get_instant_odds(team1: str, team2: str):
    """Get current odds for a matchup immediately (one-time check)"""
    print("=" * 80)
    print(f"INSTANT ODDS CHECK - {team1.upper()} vs {team2.upper()}")
    print("=" * 80)

    monitor = LiveOddsMonitor()

    # Fetch current odds
    all_games = monitor.fetch_current_odds()
    game = monitor.filter_game(all_games, team1, team2)

    if not game:
        print(f"\n[ERROR] Game not found: {team1} vs {team2}")
        print("\nAvailable games:")
        for g in all_games:
            print(f"  - {g['away_team']} @ {g['home_team']}")
        return None

    # Display odds
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nCurrent odds as of {timestamp}:")
    monitor.display_game_odds(game)

    # Check for recent history
    history_file = Path(
        f"data/odds/monitoring/{team1.replace(' ', '_')}_vs_{team2.replace(' ', '_')}.json"
    )

    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)

        if len(history) > 1:
            previous = history[-2]["game"]
            movements = monitor.detect_line_movement(game, previous)

            print(f"\nLine movement since last check ({history[-2]['timestamp']}):")
            if movements["significant"]:
                if movements["spread"]:
                    print(f"  Spread: {movements['spread']:+.1f}")
                if movements["total"]:
                    print(f"  Total: {movements['total']:+.1f}")
            else:
                print("  No significant movement")

    print()
    return game


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monitor live betting odds")
    parser.add_argument("team1", help="First team name (partial match ok)")
    parser.add_argument("team2", help="Second team name (partial match ok)")
    parser.add_argument(
        "--interval",
        type=int,
        default=900,
        help="Monitoring interval in seconds (default: 900 = 15 min)",
    )
    parser.add_argument(
        "--now", action="store_true", help="Get instant odds (one-time check)"
    )

    args = parser.parse_args()

    if args.now:
        # One-time instant check
        get_instant_odds(args.team1, args.team2)
    else:
        # Continuous monitoring
        monitor = LiveOddsMonitor(interval_seconds=args.interval)
        monitor.monitor_game(args.team1, args.team2)
