"""
Real-time market monitoring for sharp money detection
"""

import asyncio
import sys
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import io

    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except AttributeError:
        pass  # Already wrapped or not applicable

from walters_analyzer.config import get_settings
from walters_analyzer.feeds.market_data_client import OddsAPIClient


class MarketMonitor:
    """
    Monitor line movements across sharp and public books
    to detect reverse line movement and sharp money

    Billy Walters Strategy:
    - Markets underreact to injury news by ~15%
    - Sharp books (Pinnacle, Circa) move faster than public books
    - Reverse line movement = sharp money indicator
    """

    def __init__(self):
        self.settings = get_settings()
        self.line_history = defaultdict(list)
        self.alerts = []

        # Use The Odds API as primary data source
        self.client = OddsAPIClient()

    async def monitor_sport(
        self,
        sport: str = "americanfootball_nfl",
        duration_minutes: int = 60,
        check_interval: Optional[int] = None,
    ):
        """
        Monitor all games for a sport

        Args:
            sport: Sport key (americanfootball_nfl, americanfootball_ncaaf, etc.)
            duration_minutes: How long to monitor (default: 60)
            check_interval: Seconds between checks (default: from settings)

        Example:
            monitor = MarketMonitor()
            await monitor.monitor_sport("americanfootball_nfl", duration_minutes=120)
        """
        if check_interval is None:
            check_interval = self.settings.skills.market_analysis.monitor_interval

        end_time = datetime.now() + timedelta(minutes=duration_minutes)

        print(f"🔍 Monitoring {sport} for {duration_minutes} minutes...")
        print(f"   Checking every {check_interval} seconds")
        print(
            f"   Alert threshold: {self.settings.skills.market_analysis.alert_threshold} points"
        )
        print()

        iteration = 0

        while datetime.now() < end_time:
            iteration += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Check #{iteration}")

            # Fetch current odds
            odds = await self.client.get_odds(sport)

            if not odds:
                print("   ⚠️  No odds data received")
            else:
                print(f"   ✓ Fetched odds for {len(odds)} book/game combinations")

                # Process each game
                games = self._group_by_game(odds)
                print(f"   ✓ Monitoring {len(games)} games")

                for game_id, game_odds in games.items():
                    # Analyze for sharp money
                    alert = self._detect_sharp_money(game_id, game_odds)

                    if alert:
                        self._send_alert(alert)

            # Wait before next check
            print(f"   ⏱️  Waiting {check_interval} seconds...\n")
            await asyncio.sleep(check_interval)

        print(f"\n✅ Monitoring complete. Total alerts: {len(self.alerts)}")

    async def monitor_game(
        self,
        game_id: str,
        sport: str = "americanfootball_nfl",
        duration_minutes: int = 60,
    ):
        """
        Monitor a specific game for line movements

        Args:
            game_id: Game identifier
            sport: Sport key
            duration_minutes: How long to monitor
        """
        interval = self.settings.skills.market_analysis.monitor_interval
        end_time = datetime.now() + timedelta(minutes=duration_minutes)

        print(f"🔍 Monitoring game {game_id} for {duration_minutes} minutes...")

        while datetime.now() < end_time:
            # Fetch all odds for sport
            all_odds = await self.client.get_odds(sport)

            # Filter for this game
            game_odds = [o for o in all_odds if o["game_id"] == game_id]

            if game_odds:
                # Analyze for sharp money
                alert = self._detect_sharp_money(game_id, game_odds)

                if alert:
                    self._send_alert(alert)
            else:
                print(f"⚠️  No odds found for game {game_id}")

            # Wait before next check
            await asyncio.sleep(interval)

    def _group_by_game(self, odds: List[Dict]) -> Dict[str, List[Dict]]:
        """Group odds by game ID"""
        games = defaultdict(list)

        for odd in odds:
            game_id = odd.get("game_id")
            if game_id:
                games[game_id].append(odd)

        return games

    def _detect_sharp_money(
        self, game_id: str, game_odds: List[Dict]
    ) -> Optional[Dict]:
        """
        Detect reverse line movement (sharp money indicator)

        Logic:
        1. Separate sharp books from public books
        2. Compare current lines to previous snapshot
        3. If sharp books moved but public books didn't = sharp money
        4. If line movement exceeds threshold = alert

        Returns:
            Alert dict if sharp money detected, None otherwise
        """
        # Store current odds snapshot
        timestamp = datetime.now()
        self.line_history[game_id].append({"timestamp": timestamp, "odds": game_odds})

        # Need at least 2 snapshots to detect movement
        if len(self.line_history[game_id]) < 2:
            return None

        # Get previous and current snapshots
        previous = self.line_history[game_id][-2]
        current = self.line_history[game_id][-1]

        # Separate sharp vs public books
        sharp_books = self.settings.skills.market_analysis.sharp_books
        public_books = self.settings.skills.market_analysis.public_books

        # Calculate sharp book line movement
        prev_sharp = self._avg_line(previous["odds"], sharp_books)
        curr_sharp = self._avg_line(current["odds"], sharp_books)
        sharp_movement = curr_sharp - prev_sharp if prev_sharp and curr_sharp else 0

        # Calculate public book line movement
        prev_public = self._avg_line(previous["odds"], public_books)
        curr_public = self._avg_line(current["odds"], public_books)
        public_movement = (
            curr_public - prev_public if prev_public and curr_public else 0
        )

        # Check for reverse line movement or significant sharp movement
        threshold = self.settings.skills.market_analysis.alert_threshold

        # Get game info
        game_info = game_odds[0] if game_odds else {}
        teams = game_info.get("teams", {})

        if abs(sharp_movement) >= threshold:
            # Significant sharp money detected
            divergence = sharp_movement - public_movement

            return {
                "type": "sharp_money",
                "game_id": game_id,
                "teams": teams,
                "sharp_movement": round(sharp_movement, 2),
                "public_movement": round(public_movement, 2),
                "divergence": round(divergence, 2),
                "current_sharp_line": round(curr_sharp, 1) if curr_sharp else None,
                "current_public_line": round(curr_public, 1) if curr_public else None,
                "direction": self._get_direction(sharp_movement, teams),
                "confidence": min(abs(sharp_movement) / threshold * 100, 100),
                "timestamp": timestamp.isoformat(),
                "books_analyzed": {
                    "sharp": [
                        o["book"] for o in current["odds"] if o["book"] in sharp_books
                    ],
                    "public": [
                        o["book"] for o in current["odds"] if o["book"] in public_books
                    ],
                },
            }

        return None

    def _avg_line(self, odds: List[Dict], books: List[str]) -> Optional[float]:
        """Calculate average spread line for specified books"""
        lines = []

        for odd in odds:
            book = odd.get("book")
            if book in books:
                spread = odd.get("markets", {}).get("spread", {})
                home_line = spread.get("home", {}).get("line")

                if home_line is not None:
                    lines.append(home_line)

        return sum(lines) / len(lines) if lines else None

    def _get_direction(self, movement: float, teams: Dict) -> str:
        """Get human-readable direction of line movement"""
        home = teams.get("home", "Home")
        away = teams.get("away", "Away")

        if movement > 0:
            return f"SHARP MONEY ON {home.upper()} (line moved toward {away.upper()})"
        elif movement < 0:
            return f"SHARP MONEY ON {away.upper()} (line moved toward {home.upper()})"
        else:
            return "NO MOVEMENT"

    def _send_alert(self, alert: Dict):
        """Send alert to configured channels"""
        self.alerts.append(alert)
        channels = self.settings.monitoring.alert_channels

        # Console alert
        if channels.console:
            self._print_alert(alert)

        # File alert
        if channels.file:
            self._log_alert(alert, channels.file)

        # Webhook alert (if configured)
        if channels.webhook:
            self._send_webhook_alert(alert, channels.webhook)

    def _print_alert(self, alert: Dict):
        """Print alert to console"""
        print("\n" + "=" * 80)
        print("🚨 SHARP MONEY ALERT")
        print("=" * 80)

        teams = alert.get("teams", {})
        print(
            f"Game:      {teams.get('away', 'Unknown')} @ {teams.get('home', 'Unknown')}"
        )
        print(f"Direction: {alert.get('direction')}")
        print(f"Sharp Line Movement:  {alert.get('sharp_movement'):+.1f} points")
        print(f"Public Line Movement: {alert.get('public_movement'):+.1f} points")
        print(f"Divergence: {alert.get('divergence'):+.1f} points")
        print(f"Current Sharp Line: {alert.get('current_sharp_line')}")
        print(f"Confidence: {alert.get('confidence', 0):.0f}%")

        sharp_books = alert.get("books_analyzed", {}).get("sharp", [])
        public_books = alert.get("books_analyzed", {}).get("public", [])

        if sharp_books:
            print(f"Sharp Books: {', '.join(sharp_books)}")
        if public_books:
            print(f"Public Books: {', '.join(public_books)}")

        print(f"Time: {alert.get('timestamp')}")
        print("=" * 80 + "\n")

    def _log_alert(self, alert: Dict, log_file: str):
        """Log alert to file"""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, "a") as f:
            f.write(json.dumps(alert) + "\n")

    def _send_webhook_alert(self, alert: Dict, webhook_url: str):
        """Send alert to webhook (async)"""
        # TODO: Implement webhook notification
        # Could use Discord, Slack, Telegram, etc.
        pass

    def get_alert_summary(self) -> Dict:
        """Get summary of all alerts"""
        if not self.alerts:
            return {"total_alerts": 0}

        return {
            "total_alerts": len(self.alerts),
            "alerts_by_type": self._count_by_field("type"),
            "most_alerted_games": self._top_games(),
            "avg_confidence": sum(a.get("confidence", 0) for a in self.alerts)
            / len(self.alerts),
        }

    def _count_by_field(self, field: str) -> Dict:
        """Count alerts by a specific field"""
        counts = defaultdict(int)
        for alert in self.alerts:
            value = alert.get(field, "unknown")
            counts[value] += 1
        return dict(counts)

    def _top_games(self, n: int = 5) -> List[Dict]:
        """Get games with most alerts"""
        game_counts = defaultdict(int)
        game_info = {}

        for alert in self.alerts:
            game_id = alert.get("game_id")
            game_counts[game_id] += 1

            if game_id not in game_info:
                teams = alert.get("teams", {})
                game_info[game_id] = {
                    "game_id": game_id,
                    "matchup": f"{teams.get('away')} @ {teams.get('home')}",
                }

        top_games = sorted(game_counts.items(), key=lambda x: x[1], reverse=True)[:n]

        return [
            {**game_info[game_id], "alert_count": count} for game_id, count in top_games
        ]


# Example usage
async def main():
    """Example: Monitor NFL games for sharp money"""
    monitor = MarketMonitor()

    # Monitor NFL for 2 hours
    await monitor.monitor_sport(sport="americanfootball_nfl", duration_minutes=120)

    # Print summary
    summary = monitor.get_alert_summary()
    print("\n📊 MONITORING SUMMARY")
    print("=" * 80)
    print(f"Total Alerts: {summary.get('total_alerts')}")
    print(f"Average Confidence: {summary.get('avg_confidence', 0):.1f}%")

    top_games = summary.get("most_alerted_games", [])
    if top_games:
        print("\nMost Active Games:")
        for game in top_games:
            print(f"  • {game['matchup']}: {game['alert_count']} alerts")


if __name__ == "__main__":
    asyncio.run(main())
