#!/usr/bin/env python3
"""
Overtime.ag SignalR Client
Connects to ws.ticosports.com SignalR hub to receive live betting odds
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from signalrcore.hub_connection_builder import HubConnectionBuilder

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('signalr_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class OvertimeSignalRClient:
    """SignalR client for overtime.ag live odds"""

    def __init__(self):
        """Initialize SignalR client"""
        # SignalR HTTP URL - library will upgrade to WebSocket automatically
        # Important: Use https:// not wss:// - SignalR negotiates then upgrades
        self.server_url = "https://ws.ticosports.com/signalr"
        self.hub_name = "gbsHub"

        # Get customer credentials
        self.customer_id = os.getenv("OV_CUSTOMER_ID")
        self.password = os.getenv("OV_PASSWORD")

        if not self.customer_id or not self.password:
            logger.warning("OV_CUSTOMER_ID or OV_PASSWORD not found in environment")

        self.connection = None
        self.games_received = []
        self.lines_received = []

        logger.info(f"Initialized SignalR client for {self.server_url}")
        logger.info(f"Hub: {self.hub_name}")
        logger.info(f"Customer: {self.customer_id}")

    def build_connection(self):
        """Build SignalR hub connection"""
        logger.info("Building SignalR connection...")

        self.connection = (
            HubConnectionBuilder()
            .with_url(
                self.server_url,
                options={
                    "skip_negotiation": False,  # Enable negotiation
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                }
            )
            .configure_logging(logging.INFO)
            .with_automatic_reconnect({
                "type": "interval",
                "keep_alive_interval": 10,
                "intervals": [1, 3, 5, 10, 20, 40]
            })
            .build()
        )

        # Register client-side event handlers
        self._register_handlers()

        logger.info("SignalR connection built successfully")

    def _register_handlers(self):
        """Register handlers for server-sent events"""

        # Generic message handler
        self.connection.on("message", self.on_message)

        # Game update handlers (these are guesses based on common patterns)
        self.connection.on("gameUpdate", self.on_game_update)
        self.connection.on("linesUpdate", self.on_lines_update)
        self.connection.on("oddsUpdate", self.on_odds_update)
        self.connection.on("scoreUpdate", self.on_score_update)

        # Customer/subscription handlers
        self.connection.on("subscribed", self.on_subscribed)
        self.connection.on("unsubscribed", self.on_unsubscribed)

        # Error handler
        self.connection.on_error = self.on_error

        # Connection state handlers
        self.connection.on_open = self.on_open
        self.connection.on_close = self.on_close

        logger.info("Registered all event handlers")

    # Event Handlers

    def on_open(self):
        """Called when connection is established"""
        logger.info("[CONNECTION] Connected to SignalR hub!")
        logger.info("Attempting to subscribe to customer and sports...")

        # Try to subscribe as customer
        if self.customer_id:
            try:
                self.subscribe_customer()
            except Exception as e:
                logger.error(f"Failed to subscribe customer: {e}")

        # Subscribe to NFL and NCAAF
        try:
            self.subscribe_sports()
        except Exception as e:
            logger.error(f"Failed to subscribe to sports: {e}")

    def on_close(self):
        """Called when connection is closed"""
        logger.warning("[CONNECTION] Disconnected from SignalR hub")

    def on_error(self, error):
        """Called on connection error"""
        logger.error(f"[ERROR] SignalR error: {error}")

    def on_message(self, message):
        """Generic message handler"""
        logger.info(f"[MESSAGE] {json.dumps(message, indent=2)}")

    def on_game_update(self, data):
        """Handler for game updates"""
        logger.info(f"[GAME UPDATE] {json.dumps(data, indent=2)}")
        self.games_received.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "game_update",
            "data": data
        })
        self._save_data("games", data)

    def on_lines_update(self, data):
        """Handler for betting lines updates"""
        logger.info(f"[LINES UPDATE] {json.dumps(data, indent=2)}")
        self.lines_received.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "lines_update",
            "data": data
        })
        self._save_data("lines", data)

    def on_odds_update(self, data):
        """Handler for odds updates"""
        logger.info(f"[ODDS UPDATE] {json.dumps(data, indent=2)}")
        self._save_data("odds", data)

    def on_score_update(self, data):
        """Handler for score updates"""
        logger.info(f"[SCORE UPDATE] {json.dumps(data, indent=2)}")
        self._save_data("scores", data)

    def on_subscribed(self, data):
        """Handler for successful subscription"""
        logger.info(f"[SUBSCRIBED] Successfully subscribed: {data}")

    def on_unsubscribed(self, data):
        """Handler for unsubscription"""
        logger.info(f"[UNSUBSCRIBED] Unsubscribed: {data}")

    # Server Method Calls

    def subscribe_customer(self):
        """Subscribe as a customer"""
        logger.info(f"Subscribing as customer: {self.customer_id}")

        user_data = {
            "customerId": self.customer_id,
            "password": self.password
        }

        self.connection.send(self.hub_name, "SubscribeCustomer", [user_data])
        logger.info("Sent SubscribeCustomer request")

    def subscribe_sports(self):
        """Subscribe to NFL and NCAAF sports"""
        logger.info("Subscribing to NFL and NCAAF...")

        # Try different subscription formats
        subscriptions = [
            # Format 1: Sport names
            {"sport": "FOOTBALL", "league": "NFL"},
            {"sport": "FOOTBALL", "league": "NCAAF"},

            # Format 2: Sport IDs (common pattern)
            {"sportId": 1},  # Often football is sportId 1
            {"sportId": 2},  # College football might be 2

            # Format 3: Just sport names
            "FOOTBALL",
            "NFL",
            "NCAAF",
        ]

        # Try SubscribeSports (plural)
        try:
            self.connection.send(self.hub_name, "SubscribeSports", [subscriptions])
            logger.info("Sent SubscribeSports request with multiple formats")
        except Exception as e:
            logger.error(f"SubscribeSports failed: {e}")

        # Also try individual subscribeSport calls
        for sub in subscriptions[:2]:  # Try first two formats
            try:
                self.connection.send(self.hub_name, "SubscribeSport", [sub])
                logger.info(f"Sent SubscribeSport request: {sub}")
            except Exception as e:
                logger.error(f"SubscribeSport failed for {sub}: {e}")

    def get_game(self, game_num: int):
        """Get specific game data"""
        logger.info(f"Requesting game {game_num}...")
        self.connection.send(self.hub_name, "GetGame", [game_num])

    def get_game_lines(self, game_num: int, period_num: int = 0, store: str = ""):
        """Get betting lines for a game"""
        logger.info(f"Requesting lines for game {game_num}, period {period_num}...")
        self.connection.send(self.hub_name, "GetGameLines", [game_num, period_num, store])

    # Utility Methods

    def _save_data(self, data_type: str, data: any):
        """Save received data to JSON file"""
        os.makedirs("output/signalr", exist_ok=True)

        filename = f"output/signalr/{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "type": data_type,
                "data": data
            }, f, indent=2)

        logger.info(f"Saved {data_type} data to {filename}")

    def start(self, duration: int = 300):
        """
        Start the SignalR connection and listen for events

        Args:
            duration: How long to listen in seconds (default 5 minutes)
        """
        logger.info("=" * 60)
        logger.info("Overtime.ag SignalR Client Starting")
        logger.info("=" * 60)

        # Build connection
        self.build_connection()

        # Start connection
        logger.info("Starting SignalR connection...")
        self.connection.start()

        logger.info(f"Listening for {duration} seconds...")
        logger.info("Press Ctrl+C to stop early")

        try:
            # Keep connection alive
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(1)

                # Every 30 seconds, log status
                if int(time.time() - start_time) % 30 == 0:
                    logger.info(f"Status: {len(self.games_received)} games, {len(self.lines_received)} line updates received")

        except KeyboardInterrupt:
            logger.info("\nStopping (Ctrl+C pressed)...")

        finally:
            # Stop connection
            logger.info("Closing SignalR connection...")
            self.connection.stop()

            # Summary
            logger.info("=" * 60)
            logger.info("Session Summary:")
            logger.info(f"Games received: {len(self.games_received)}")
            logger.info(f"Lines received: {len(self.lines_received)}")
            logger.info("=" * 60)


def main():
    """Main entry point"""
    client = OvertimeSignalRClient()

    # Listen for 5 minutes by default
    # Increase duration if testing during live games
    duration = 300  # 5 minutes

    if len(sys.argv) > 1:
        duration = int(sys.argv[1])

    client.start(duration=duration)


if __name__ == "__main__":
    main()
