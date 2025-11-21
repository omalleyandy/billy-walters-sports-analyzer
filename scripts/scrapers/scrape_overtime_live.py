#!/usr/bin/env python3
"""
Overtime.ag On-Demand Live Odds Scraper (NFL & NCAAF)

Run this anytime during live games to monitor real-time odds and line movements.
Works for both NFL and NCAAF games.

Quick Start:
    # NFL Sunday (3 hours of games)
    uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 10800

    # NCAAF Saturday (4 hours)
    uv run python scripts/scrapers/scrape_overtime_live.py --ncaaf --duration 14400

    # Both leagues (for simultaneous games)
    uv run python scripts/scrapers/scrape_overtime_live.py --nfl --ncaaf --duration 14400

    # Quick check (5 minutes)
    uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 300

    # Background mode (headless, saves output, no console spam)
    uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 10800 --headless --quiet

Author: Billy Walters Sports Analyzer
Created: 2025-11-14
"""

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.overtime_hybrid_scraper import OvertimeHybridScraper


class LiveOddsMonitor:
    """
    On-demand live odds monitor with line movement tracking.

    Monitors Overtime.ag during live games and tracks all line changes
    for spread, total, and moneyline across NFL and NCAAF.
    """

    def __init__(
        self,
        leagues: List[str],
        duration: int = 3600,
        headless: bool = False,
        output_dir: str = "output/overtime/live",
        quiet: bool = False,
    ):
        """
        Initialize live odds monitor.

        Args:
            leagues: List of leagues to monitor (e.g., ["NFL", "NCAAF"])
            duration: How long to monitor in seconds
            headless: Run browser in headless mode
            output_dir: Output directory
            quiet: Suppress console output (except errors)
        """
        self.leagues = leagues
        self.duration = duration
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.quiet = quiet

        # Line tracking
        self.line_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.game_info: Dict[str, Dict[str, Any]] = {}
        self.significant_movements: List[Dict[str, Any]] = []

    async def run(self) -> Dict[str, Any]:
        """
        Run live odds monitoring.

        Returns:
            Dictionary with monitoring results and analysis
        """
        self._print("=" * 70)
        self._print("Overtime.ag On-Demand Live Odds Monitor")
        self._print("=" * 70)
        self._print("")
        self._print(f"Leagues: {', '.join(self.leagues)}")
        self._print(f"Duration: {self.duration}s ({self.duration / 3600:.1f} hours)")
        self._print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._print("")

        # Create base scraper
        scraper = OvertimeHybridScraper(
            headless=self.headless,
            output_dir=str(self.output_dir),
            enable_signalr=True,
            signalr_duration=self.duration,
        )

        # Customize SignalR subscription for requested leagues
        original_subscribe = scraper._subscribe_sports
        scraper._subscribe_sports = lambda: self._subscribe_leagues(
            scraper, original_subscribe
        )

        # Monkey-patch handlers to capture line updates
        self._install_custom_handlers(scraper)

        # Run scraper
        result = await scraper.scrape()

        # Analyze results
        self._print("")
        self._print("=" * 70)
        self._print("ANALYZING RESULTS")
        self._print("=" * 70)

        analysis = self._analyze_movements()

        # Save reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save detailed line history
        history_file = self.output_dir / f"line_history_{timestamp}.json"
        self._save_line_history(history_file)

        # Save movement summary
        summary_file = self.output_dir / f"movement_summary_{timestamp}.json"
        self._save_summary(summary_file, analysis)

        # Display summary
        self._print_summary(analysis)

        return {
            "metadata": result.get("metadata", {}),
            "pregame": result.get("pregame", {}),
            "live": result.get("live", {}),
            "analysis": analysis,
            "output_files": {
                "line_history": str(history_file),
                "movement_summary": str(summary_file),
            },
        }

    def _subscribe_leagues(self, scraper: OvertimeHybridScraper, original_fn) -> None:
        """Subscribe to requested leagues on SignalR"""
        subscriptions = []

        if "NFL" in self.leagues:
            subscriptions.extend(
                [
                    {"sport": "FOOTBALL", "league": "NFL"},
                    {"sportId": 1, "league": "NFL"},
                    "NFL",
                ]
            )

        if "NCAAF" in self.leagues or "CFB" in self.leagues:
            subscriptions.extend(
                [
                    {"sport": "FOOTBALL", "league": "NCAAF"},
                    {"sport": "FOOTBALL", "league": "CFB"},
                    {"sportId": 1, "league": "NCAAF"},
                    "NCAAF",
                    "CFB",
                ]
            )

        try:
            scraper.signalr_connection.send("SubscribeSports", subscriptions)
            self._print(f"[OK] Subscribed to: {', '.join(self.leagues)}")
        except Exception as e:
            self._print(f"[ERROR] Subscription failed: {e}")

    def _install_custom_handlers(self, scraper: OvertimeHybridScraper) -> None:
        """Install custom handlers to capture and process line updates"""

        # Store original handlers
        original_lines = scraper._on_lines_update
        original_odds = scraper._on_odds_update
        original_game = scraper._on_game_update

        # Wrap with our tracking logic
        def track_lines_update(data: Any) -> None:
            self._process_line_update(data)
            original_lines(data)

        def track_odds_update(data: Any) -> None:
            self._process_line_update(data)
            original_odds(data)

        def track_game_update(data: Any) -> None:
            self._process_game_update(data)
            original_game(data)

        # Replace handlers
        scraper._on_lines_update = track_lines_update
        scraper._on_odds_update = track_odds_update
        scraper._on_game_update = track_game_update

    def _process_line_update(self, data: Any) -> None:
        """Process line update and track changes"""
        try:
            if not isinstance(data, dict):
                return

            game_id = str(data.get("gameId") or data.get("id") or "unknown")
            timestamp = datetime.now().isoformat()

            lines = data.get("lines", {})
            visitor = lines.get("visitor", {}) or lines.get("away", {})
            home = lines.get("home", {})

            line_snapshot = {
                "timestamp": timestamp,
                "visitor_spread": self._safe_float(visitor.get("spread")),
                "visitor_spread_odds": self._safe_int(visitor.get("spreadOdds")),
                "visitor_moneyline": self._safe_int(visitor.get("moneyline")),
                "home_spread": self._safe_float(home.get("spread")),
                "home_spread_odds": self._safe_int(home.get("spreadOdds")),
                "home_moneyline": self._safe_int(home.get("moneyline")),
                "total": self._safe_float(visitor.get("total") or home.get("total")),
                "total_over_odds": self._safe_int(
                    visitor.get("overOdds") or home.get("overOdds")
                ),
                "total_under_odds": self._safe_int(
                    visitor.get("underOdds") or home.get("underOdds")
                ),
            }

            # Skip if no meaningful data
            if not any(v is not None for v in line_snapshot.values() if v != timestamp):
                return

            # Check for significant movement
            if self.line_history.get(game_id):
                last_line = self.line_history[game_id][-1]
                movement = self._calculate_movement(last_line, line_snapshot)

                if movement["significant"]:
                    self.significant_movements.append(
                        {
                            "game_id": game_id,
                            "timestamp": timestamp,
                            "movement": movement,
                            "teams": self.game_info.get(game_id, {}).get("teams"),
                        }
                    )

                    if not self.quiet:
                        teams = self.game_info.get(game_id, {}).get("teams", "Unknown")
                        self._print(f"\n[MOVEMENT] {teams}")
                        if movement["spread"] is not None:
                            self._print(f"  Spread: {movement['spread']:+.1f}")
                        if movement["total"] is not None:
                            self._print(f"  Total: {movement['total']:+.1f}")
                        if movement["moneyline_visitor"] is not None:
                            self._print(
                                f"  ML Visitor: {movement['moneyline_visitor']:+d}"
                            )

            # Record line
            self.line_history[game_id].append(line_snapshot)

        except Exception as e:
            if not self.quiet:
                self._print(f"[WARNING] Error processing line update: {e}")

    def _process_game_update(self, data: Any) -> None:
        """Process game update to track team names and scores"""
        try:
            if not isinstance(data, dict):
                return

            game_id = str(data.get("gameId") or data.get("id") or "unknown")

            visitor_data = data.get("visitor", {})
            home_data = data.get("home", {})

            visitor_name = visitor_data.get("name") or visitor_data.get("team")
            home_name = home_data.get("name") or home_data.get("team")

            if visitor_name and home_name:
                self.game_info[game_id] = {
                    "teams": f"{visitor_name} @ {home_name}",
                    "visitor": visitor_name,
                    "home": home_name,
                    "status": data.get("status", "unknown"),
                }

        except Exception as e:
            if not self.quiet:
                self._print(f"[WARNING] Error processing game update: {e}")

    def _calculate_movement(self, old: Dict, new: Dict) -> Dict[str, Any]:
        """Calculate movement between two line snapshots"""
        spread_move = None
        total_move = None
        ml_visitor_move = None
        ml_home_move = None

        if (
            old.get("visitor_spread") is not None
            and new.get("visitor_spread") is not None
        ):
            spread_move = new["visitor_spread"] - old["visitor_spread"]

        if old.get("total") is not None and new.get("total") is not None:
            total_move = new["total"] - old["total"]

        if (
            old.get("visitor_moneyline") is not None
            and new.get("visitor_moneyline") is not None
        ):
            ml_visitor_move = new["visitor_moneyline"] - old["visitor_moneyline"]

        if (
            old.get("home_moneyline") is not None
            and new.get("home_moneyline") is not None
        ):
            ml_home_move = new["home_moneyline"] - old["home_moneyline"]

        # Determine if significant
        significant = (
            (spread_move is not None and abs(spread_move) >= 0.5)
            or (total_move is not None and abs(total_move) >= 0.5)
            or (ml_visitor_move is not None and abs(ml_visitor_move) >= 10)
            or (ml_home_move is not None and abs(ml_home_move) >= 10)
        )

        return {
            "spread": spread_move,
            "total": total_move,
            "moneyline_visitor": ml_visitor_move,
            "moneyline_home": ml_home_move,
            "significant": significant,
        }

    def _analyze_movements(self) -> Dict[str, Any]:
        """Analyze all tracked movements"""
        games_tracked = len(self.line_history)
        total_updates = sum(len(history) for history in self.line_history.values())

        games_with_movement = []
        for game_id, history in self.line_history.items():
            if len(history) < 2:
                continue

            initial = history[0]
            current = history[-1]

            movement = self._calculate_movement(initial, current)

            game_analysis = {
                "game_id": game_id,
                "teams": self.game_info.get(game_id, {}).get("teams", "Unknown"),
                "initial_line": initial,
                "current_line": current,
                "movement": movement,
                "update_count": len(history),
            }

            games_with_movement.append(game_analysis)

        return {
            "games_tracked": games_tracked,
            "total_line_updates": total_updates,
            "significant_movements": len(self.significant_movements),
            "games_with_movement": len(games_with_movement),
            "games": games_with_movement,
            "significant_events": self.significant_movements,
        }

    def _save_line_history(self, output_path: Path) -> None:
        """Save complete line history"""
        data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "leagues": self.leagues,
                "duration_seconds": self.duration,
            },
            "games": {
                game_id: {
                    "info": self.game_info.get(game_id, {}),
                    "history": history,
                }
                for game_id, history in self.line_history.items()
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        self._print(f"[OK] Saved line history: {output_path}")

    def _save_summary(self, output_path: Path, analysis: Dict[str, Any]) -> None:
        """Save movement summary"""
        data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "leagues": self.leagues,
                "duration_seconds": self.duration,
            },
            "summary": {
                "games_tracked": analysis["games_tracked"],
                "total_line_updates": analysis["total_line_updates"],
                "significant_movements": analysis["significant_movements"],
            },
            "games": analysis["games"],
            "significant_events": analysis["significant_events"],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        self._print(f"[OK] Saved movement summary: {output_path}")

    def _print_summary(self, analysis: Dict[str, Any]) -> None:
        """Print summary to console"""
        self._print("")
        self._print("=" * 70)
        self._print("SUMMARY")
        self._print("=" * 70)
        self._print(f"Games tracked: {analysis['games_tracked']}")
        self._print(f"Total line updates: {analysis['total_line_updates']}")
        self._print(f"Significant movements: {analysis['significant_movements']}")
        self._print("")

        if analysis["games"]:
            self._print("GAMES WITH LINE MOVEMENTS:")
            self._print("-" * 70)
            for game in analysis["games"]:
                teams = game.get("teams", "Unknown")
                movement = game.get("movement", {})

                self._print(f"\n{teams}")
                self._print(f"  Updates: {game['update_count']}")

                if movement.get("spread") is not None:
                    self._print(f"  Spread movement: {movement['spread']:+.1f}")
                if movement.get("total") is not None:
                    self._print(f"  Total movement: {movement['total']:+.1f}")
                if movement.get("moneyline_visitor") is not None:
                    self._print(f"  ML Visitor: {movement['moneyline_visitor']:+d}")
                if movement.get("moneyline_home") is not None:
                    self._print(f"  ML Home: {movement['moneyline_home']:+d}")

    def _print(self, message: str) -> None:
        """Print message unless quiet mode enabled"""
        if not self.quiet:
            print(message)

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """Safely convert to float"""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        """Safely convert to int"""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Overtime.ag On-Demand Live Odds Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # NFL Sunday afternoon (3 hours)
  uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 10800

  # NCAAF Saturday (4 hours)
  uv run python scripts/scrapers/scrape_overtime_live.py --ncaaf --duration 14400

  # Both leagues (simultaneous games)
  uv run python scripts/scrapers/scrape_overtime_live.py --nfl --ncaaf --duration 14400

  # Monday Night Football (4 hours)
  uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 14400 --headless

  # Quick check (5 minutes)
  uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 300

  # Background monitoring (headless, quiet)
  uv run python scripts/scrapers/scrape_overtime_live.py --nfl --duration 10800 --headless --quiet

Timing Guide:
  - NFL Sunday early games: 3-4 hours (10800-14400 seconds)
  - NFL Sunday full day: 10-12 hours (36000-43200 seconds)
  - NCAAF Saturday: 4-12 hours (14400-43200 seconds)
  - MACtion weeknight: 3-4 hours (10800-14400 seconds)
  - Monday Night Football: 4 hours (14400 seconds)
        """,
    )

    parser.add_argument(
        "--nfl",
        action="store_true",
        help="Monitor NFL games",
    )

    parser.add_argument(
        "--ncaaf",
        action="store_true",
        help="Monitor NCAAF games",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=3600,
        help="How long to monitor in seconds (default: 3600 = 1 hour)",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (recommended for background)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output (except errors and final summary)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output/overtime/live",
        help="Output directory (default: output/overtime/live)",
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    # Determine leagues
    leagues = []
    if args.nfl:
        leagues.append("NFL")
    if args.ncaaf:
        leagues.append("NCAAF")

    if not leagues:
        print("[ERROR] Must specify at least one league: --nfl or --ncaaf")
        print("Run with --help for usage examples")
        return 1

    # Create monitor
    monitor = LiveOddsMonitor(
        leagues=leagues,
        duration=args.duration,
        headless=args.headless,
        output_dir=args.output,
        quiet=args.quiet,
    )

    # Run monitor
    try:
        result = await monitor.run()

        print()
        print("=" * 70)
        print("MONITORING COMPLETE")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Review line movement reports in output directory")
        print("  2. Compare to your edge detector picks")
        print("  3. Look for reverse line movement (RLM) opportunities")
        print()

        return 0

    except KeyboardInterrupt:
        print()
        print("Monitoring stopped by user (Ctrl+C)")
        return 1

    except Exception as e:
        print()
        print(f"[ERROR] Monitoring failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
