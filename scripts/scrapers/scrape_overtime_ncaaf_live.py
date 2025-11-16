#!/usr/bin/env python3
"""
Run Overtime.ag NCAAF Live Scraper with Line Movement Tracking

Monitors live NCAAF games and tracks spread, total, and moneyline movements.

Usage:
    # Basic usage (3 hours of Saturday games)
    uv run python scripts/scrapers/scrape_overtime_ncaaf_live.py --duration 10800

    # Full Saturday coverage (12 hours)
    uv run python scripts/scrapers/scrape_overtime_ncaaf_live.py --duration 43200 --headless

    # Quick test (5 minutes)
    uv run python scripts/scrapers/scrape_overtime_ncaaf_live.py --duration 300

    # With line movement analysis
    uv run python scripts/scrapers/scrape_overtime_ncaaf_live.py --duration 10800 --analyze-movements

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
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.overtime_hybrid_scraper import OvertimeHybridScraper


class LineMovementTracker:
    """Track and analyze line movements for NCAAF games"""

    def __init__(self):
        """Initialize line movement tracker"""
        self.movements: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.initial_lines: Dict[str, Dict[str, Any]] = {}

    def record_line(self, game_id: str, timestamp: str, line_data: Dict[str, Any]) -> None:
        """
        Record a line snapshot for a game.

        Args:
            game_id: Unique game identifier
            timestamp: ISO timestamp of the line
            line_data: Dictionary with spread, total, moneyline for both teams
        """
        snapshot = {
            "timestamp": timestamp,
            "visitor_spread": line_data.get("visitor_spread"),
            "visitor_spread_odds": line_data.get("visitor_spread_odds"),
            "visitor_moneyline": line_data.get("visitor_moneyline"),
            "home_spread": line_data.get("home_spread"),
            "home_spread_odds": line_data.get("home_spread_odds"),
            "home_moneyline": line_data.get("home_moneyline"),
            "total": line_data.get("total"),
            "total_over_odds": line_data.get("total_over_odds"),
            "total_under_odds": line_data.get("total_under_odds"),
        }

        # Store initial line
        if game_id not in self.initial_lines:
            self.initial_lines[game_id] = snapshot.copy()

        # Record movement
        self.movements[game_id].append(snapshot)

    def analyze_movements(self, game_id: str) -> Dict[str, Any]:
        """
        Analyze line movements for a specific game.

        Args:
            game_id: Game to analyze

        Returns:
            Dictionary with movement analysis
        """
        if game_id not in self.movements or len(self.movements[game_id]) < 2:
            return {"error": "Insufficient data for analysis"}

        initial = self.initial_lines[game_id]
        current = self.movements[game_id][-1]
        history = self.movements[game_id]

        # Calculate changes (use explicit None checks to handle 0 as valid value)
        spread_movement = None
        if initial.get("visitor_spread") is not None and current.get("visitor_spread") is not None:
            spread_movement = current["visitor_spread"] - initial["visitor_spread"]

        total_movement = None
        if initial.get("total") is not None and current.get("total") is not None:
            total_movement = current["total"] - initial["total"]

        ml_movement_visitor = None
        if initial.get("visitor_moneyline") is not None and current.get("visitor_moneyline") is not None:
            ml_movement_visitor = (
                current["visitor_moneyline"] - initial["visitor_moneyline"]
            )

        ml_movement_home = None
        if initial.get("home_moneyline") is not None and current.get("home_moneyline") is not None:
            ml_movement_home = current["home_moneyline"] - initial["home_moneyline"]

        # Detect significant movements
        significant_spread = abs(spread_movement) >= 1.0 if spread_movement is not None else False
        significant_total = abs(total_movement) >= 1.0 if total_movement is not None else False
        significant_ml = (
            (ml_movement_visitor is not None and abs(ml_movement_visitor) >= 20) or
            (ml_movement_home is not None and abs(ml_movement_home) >= 20)
        )

        # Calculate velocity (movements per hour)
        time_span_hours = self._calculate_time_span(
            history[0]["timestamp"], history[-1]["timestamp"]
        )
        movement_count = len(history) - 1

        return {
            "game_id": game_id,
            "initial_line": initial,
            "current_line": current,
            "movements": {
                "spread": spread_movement,
                "total": total_movement,
                "moneyline_visitor": ml_movement_visitor,
                "moneyline_home": ml_movement_home,
            },
            "significant": {
                "spread": significant_spread,
                "total": significant_total,
                "moneyline": significant_ml,
            },
            "velocity": {
                "movements_per_hour": movement_count / time_span_hours if time_span_hours > 0 else 0,
                "total_movements": movement_count,
                "time_span_hours": time_span_hours,
            },
            "history_count": len(history),
        }

    def _calculate_time_span(self, start_iso: str, end_iso: str) -> float:
        """Calculate time span in hours between two ISO timestamps"""
        try:
            start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
            delta = end - start
            return delta.total_seconds() / 3600
        except Exception:
            return 0.0

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tracked movements.

        Returns:
            Dictionary with summary statistics
        """
        total_games = len(self.movements)
        total_movements = sum(len(moves) - 1 for moves in self.movements.values())

        significant_games = []
        for game_id in self.movements:
            analysis = self.analyze_movements(game_id)
            if "significant" in analysis:
                if any(analysis["significant"].values()):
                    significant_games.append(
                        {"game_id": game_id, "analysis": analysis}
                    )

        return {
            "total_games_tracked": total_games,
            "total_line_movements": total_movements,
            "significant_movements": len(significant_games),
            "significant_games": significant_games,
        }

    def save_report(self, output_path: Path) -> None:
        """Save line movement report to JSON file"""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": "overtime.ag/ncaaf",
                "report_type": "line_movement_analysis",
            },
            "summary": self.get_summary(),
            "games": {
                game_id: self.analyze_movements(game_id)
                for game_id in self.movements
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n[OK] Line movement report saved: {output_path}")


class NCAAFLiveScraper:
    """NCAAF-specific live scraper with line movement tracking"""

    def __init__(
        self,
        headless: bool = False,
        duration: int = 10800,
        analyze_movements: bool = True,
        output_dir: str = "output/overtime/ncaaf/live",
    ):
        """
        Initialize NCAAF live scraper.

        Args:
            headless: Run browser in headless mode
            duration: How long to monitor (seconds)
            analyze_movements: Enable line movement analysis
            output_dir: Output directory
        """
        self.headless = headless
        self.duration = duration
        self.analyze_movements = analyze_movements
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.tracker = LineMovementTracker() if analyze_movements else None

    async def run(self) -> Dict[str, Any]:
        """
        Run NCAAF live scraper with line movement tracking.

        Returns:
            Dictionary with scraping results and analysis
        """
        print("=" * 70)
        print("NCAAF Live Odds Scraper with Line Movement Tracking")
        print("=" * 70)
        print()
        print(f"Duration: {self.duration} seconds ({self.duration / 3600:.1f} hours)")
        print(f"Line movement analysis: {'enabled' if self.analyze_movements else 'disabled'}")
        print()

        # Create base scraper
        scraper = OvertimeHybridScraper(
            headless=self.headless,
            output_dir=str(self.output_dir),
            enable_signalr=True,
            signalr_duration=self.duration,
        )

        # Modify scraper to track NCAAF instead of NFL (use lambda to bind scraper instance)
        original_subscribe = scraper._subscribe_sports
        scraper._subscribe_sports = lambda: self._subscribe_ncaaf_sports(scraper)

        # Run scraper
        result = await scraper.scrape()

        # Process live updates for line movements
        if self.analyze_movements and result.get("live", {}).get("updates"):
            print()
            print("=" * 70)
            print("ANALYZING LINE MOVEMENTS")
            print("=" * 70)
            print()

            for update in result["live"]["updates"]:
                self._process_update(update)

            # Generate analysis report
            summary = self.tracker.get_summary()
            print(f"Total games tracked: {summary['total_games_tracked']}")
            print(f"Total line movements: {summary['total_line_movements']}")
            print(f"Significant movements: {summary['significant_movements']}")
            print()

            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.output_dir / f"line_movements_{timestamp}.json"
            self.tracker.save_report(report_path)

            # Print significant movements
            if summary["significant_games"]:
                print("SIGNIFICANT LINE MOVEMENTS DETECTED:")
                print("-" * 70)
                for game_info in summary["significant_games"]:
                    game_id = game_info["game_id"]
                    analysis = game_info["analysis"]
                    movements = analysis["movements"]

                    print(f"\nGame ID: {game_id}")
                    if movements["spread"] is not None:
                        print(f"  Spread movement: {movements['spread']:+.1f}")
                    if movements["total"] is not None:
                        print(f"  Total movement: {movements['total']:+.1f}")
                    if movements["moneyline_visitor"] is not None:
                        print(
                            f"  Moneyline (visitor): {movements['moneyline_visitor']:+d}"
                        )
                    if movements["moneyline_home"] is not None:
                        print(f"  Moneyline (home): {movements['moneyline_home']:+d}")
                print()

        result["line_movement_analysis"] = (
            self.tracker.get_summary() if self.tracker else None
        )
        return result

    def _subscribe_ncaaf_sports(self, scraper: OvertimeHybridScraper) -> None:
        """
        Subscribe to NCAAF sports on SignalR hub (replaces NFL subscription).
        
        Args:
            scraper: The OvertimeHybridScraper instance with signalr_connection
        """
        subscriptions = [
            {"sport": "FOOTBALL", "league": "NCAAF"},
            {"sport": "FOOTBALL", "league": "CFB"},
            {"sportId": 1, "league": "NCAAF"},  # Football often uses sportId 1
            "NCAAF",
            "CFB",
        ]

        try:
            # Send subscription to SignalR using the provided scraper instance
            scraper.signalr_connection.send("SubscribeSports", subscriptions)
            print("   [OK] Subscribed to NCAAF/CFB sports")
        except Exception as e:
            print(f"   [ERROR] SubscribeSports (NCAAF) failed: {e}")
            if hasattr(scraper, 'logger'):
                scraper.logger.error(f"SubscribeSports (NCAAF) failed: {e}")

    def _process_update(self, update: Dict[str, Any]) -> None:
        """Process a live update and extract line data"""
        try:
            update_type = update.get("type")
            data = update.get("data", {})
            timestamp = update.get("timestamp", datetime.now().isoformat())

            # Extract game ID
            game_id = None
            if isinstance(data, dict):
                game_id = data.get("gameId") or data.get("id")

            if not game_id:
                return

            # Extract line data based on update type
            line_data = {}

            if update_type in ["lines_update", "odds_update"]:
                lines = data.get("lines", {})
                visitor = lines.get("visitor", {}) or lines.get("away", {})
                home = lines.get("home", {})

                line_data = {
                    "visitor_spread": visitor.get("spread"),
                    "visitor_spread_odds": visitor.get("spreadOdds"),
                    "visitor_moneyline": visitor.get("moneyline"),
                    "home_spread": home.get("spread"),
                    "home_spread_odds": home.get("spreadOdds"),
                    "home_moneyline": home.get("moneyline"),
                    "total": visitor.get("total") or home.get("total"),
                    "total_over_odds": visitor.get("overOdds") or home.get("overOdds"),
                    "total_under_odds": visitor.get("underOdds")
                    or home.get("underOdds"),
                }

                # Record line if we have valid data
                if any(line_data.values()):
                    self.tracker.record_line(str(game_id), timestamp, line_data)

        except Exception as e:
            print(f"[WARNING] Error processing update: {e}")


def parse_args():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(
        description="NCAAF Live Odds Scraper with Line Movement Tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Saturday afternoon games (3 hours)
  uv run python scripts/scrapers/scrape_overtime_ncaaf_live.py --duration 10800

  # Full Saturday coverage (12 hours, headless)
  uv run python scripts/scrapers/scrape_overtime_ncaaf_live.py --duration 43200 --headless

  # Quick test (5 minutes)
  uv run python scripts/scrapers/scrape_overtime_ncaaf_live.py --duration 300

  # With detailed line movement tracking
  uv run python scripts/scrapers/scrape_overtime_ncaaf_live.py --duration 10800 --analyze-movements

Timing Recommendations:
  - Saturday daytime: 10800 seconds (3 hours) for afternoon games
  - Saturday full day: 43200 seconds (12 hours) for all games
  - MACtion (Tuesday/Wednesday/Thursday): 14400 seconds (4 hours)
        """,
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no visible window)",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=10800,
        help="How long to monitor in seconds (default: 10800 = 3 hours)",
    )

    parser.add_argument(
        "--analyze-movements",
        action="store_true",
        help="Enable line movement analysis (enabled by default, this flag is explicit)",
    )

    parser.add_argument(
        "--no-analyze",
        action="store_true",
        help="Disable line movement analysis",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output/overtime/ncaaf/live",
        help="Output directory (default: output/overtime/ncaaf/live)",
    )

    return parser.parse_args()


async def main():
    """Main entry point"""

    args = parse_args()

    # Analysis is enabled by default unless --no-analyze is provided
    # --analyze-movements is kept for explicit enablement but defaults to enabled anyway
    analyze = not args.no_analyze

    print("=" * 70)
    print("NCAAF Live Odds Scraper")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Duration: {args.duration} seconds ({args.duration / 3600:.1f} hours)")
    print(f"  Headless: {args.headless}")
    print(f"  Line movement analysis: {analyze}")
    print(f"  Output directory: {args.output}")
    print()

    # Create scraper
    scraper = NCAAFLiveScraper(
        headless=args.headless,
        duration=args.duration,
        analyze_movements=analyze,
        output_dir=args.output,
    )

    # Run scraper
    try:
        result = await scraper.run()

        print()
        print("=" * 70)
        print("SCRAPING COMPLETE")
        print("=" * 70)
        print()
        print("Results:")
        print(f"  Pre-game games: {len(result['pregame']['games'])}")
        print(f"  Live updates: {len(result['live']['updates'])}")

        if result.get("line_movement_analysis"):
            analysis = result["line_movement_analysis"]
            print()
            print("Line Movement Analysis:")
            print(f"  Games tracked: {analysis['total_games_tracked']}")
            print(f"  Total movements: {analysis['total_line_movements']}")
            print(f"  Significant movements: {analysis['significant_movements']}")

        print()
        print("Next steps:")
        print("  1. Review line movement report in output directory")
        print("  2. Identify sharp money indicators (reverse line movement)")
        print("  3. Update edge detection with fresh lines")
        print()

        return 0

    except KeyboardInterrupt:
        print()
        print("Scraping interrupted by user (Ctrl+C)")
        return 1

    except Exception as e:
        print()
        print(f"[ERROR] Scraping failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
