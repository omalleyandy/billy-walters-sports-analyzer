#!/usr/bin/env python3
"""
Overtime.ag Manual SignalR 1.x Client
ASP.NET SignalR 1.x implementation (not SignalR Core)
"""

import os
import sys
import json
import time
import logging
import urllib.parse
from datetime import datetime
import requests
import websocket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("signalr_manual.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class SignalR1xClient:
    """Manual ASP.NET SignalR 1.x client implementation"""

    def __init__(self):
        """Initialize SignalR client"""
        self.base_url = "https://ws.ticosports.com"
        self.hub_name = "gbsHub"

        # Get credentials
        self.customer_id = os.getenv("OV_CUSTOMER_ID")
        self.password = os.getenv("OV_PASSWORD")

        # Connection state
        self.connection_token = None
        self.connection_id = None
        self.ws = None
        self.message_id = 0

        # Data storage
        self.games_received = []
        self.messages_received = []

        logger.info(f"Initialized SignalR 1.x client for {self.base_url}")
        logger.info(f"Hub: {self.hub_name}")
        logger.info(f"Customer: {self.customer_id}")

    def negotiate(self) -> bool:
        """
        Negotiate connection with SignalR server

        Returns:
            True if negotiation successful
        """
        logger.info("Negotiating SignalR connection...")

        negotiate_url = f"{self.base_url}/signalr/negotiate"

        # SignalR 1.x negotiation parameters
        params = {
            "clientProtocol": "1.5",
            "connectionData": json.dumps([{"name": self.hub_name}]),
        }

        try:
            r = requests.get(negotiate_url, params=params, timeout=30)

            if r.status_code != 200:
                logger.error(f"Negotiation failed: HTTP {r.status_code}")
                return False

            data = r.json()

            self.connection_token = data.get("ConnectionToken")
            self.connection_id = data.get("ConnectionId")

            logger.info("Negotiation successful!")
            logger.info(f"Connection ID: {self.connection_id}")
            logger.info(f"Protocol Version: {data.get('ProtocolVersion')}")
            logger.info(f"TryWebSockets: {data.get('TryWebSockets')}")

            return True

        except Exception as e:
            logger.error(f"Negotiation error: {e}")
            return False

    def connect(self) -> bool:
        """
        Connect to SignalR WebSocket

        Returns:
            True if connection successful
        """
        if not self.connection_token:
            logger.error("Cannot connect: No connection token (run negotiate first)")
            return False

        logger.info("Connecting to SignalR WebSocket...")

        # Build WebSocket URL
        ws_url = "wss://ws.ticosports.com/signalr/connect"

        params = {
            "transport": "webSockets",
            "clientProtocol": "1.5",
            "connectionToken": self.connection_token,
            "connectionData": json.dumps([{"name": self.hub_name}]),
        }

        # URL encode params
        query_string = urllib.parse.urlencode(params)
        full_url = f"{ws_url}?{query_string}"

        logger.info("WebSocket URL: wss://ws.ticosports.com/signalr/connect?...")

        # Create WebSocket with callbacks
        try:
            self.ws = websocket.WebSocketApp(
                full_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open,
            )

            return True

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            return False

    # WebSocket Callbacks

    def on_open(self, ws):
        """Called when WebSocket connection is established"""
        logger.info("[CONNECTED] WebSocket connection established!")

        # Subscribe to customer and sports immediately
        # (No need to call "Start" method - SignalR 1.x auto-initializes)
        if self.customer_id:
            self.subscribe_customer()

        self.subscribe_sports()

    def on_message(self, ws, message):
        """Called when message received from server"""
        try:
            logger.info(f"[MESSAGE] {message}")

            # Save message
            self.messages_received.append(
                {"timestamp": datetime.utcnow().isoformat(), "raw_message": message}
            )

            # Try to parse as JSON
            try:
                data = json.loads(message)

                # Save parsed message
                self._save_message(data)

                # Handle different message types
                if isinstance(data, dict):
                    # Hub invocation response
                    if "R" in data:  # Result
                        logger.info(f"[RESULT] {json.dumps(data['R'], indent=2)}")

                    # Hub invocation
                    if "M" in data:  # Messages from server
                        for msg in data["M"]:
                            self.handle_hub_invocation(msg)

                    # Initialization message
                    if "S" in data and data["S"] == 1:
                        logger.info("[INITIALIZED] SignalR connection initialized")

            except json.JSONDecodeError:
                # Not JSON, might be keep-alive
                if message.strip() == "{}":
                    logger.debug("[KEEPALIVE]")
                pass

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def on_error(self, ws, error):
        """Called on WebSocket error"""
        logger.error(f"[ERROR] {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket connection closes"""
        logger.warning(f"[CLOSED] Connection closed: {close_status_code} - {close_msg}")

    # SignalR Methods

    def send_message(self, message: dict):
        """Send message to SignalR server"""
        if not self.ws:
            logger.error("Cannot send: WebSocket not connected")
            return

        message_json = json.dumps(message)
        logger.debug(f"[SEND] {message_json}")

        self.ws.send(message_json)

    def invoke_hub_method(self, method: str, args: list):
        """
        Invoke a method on the SignalR hub

        Args:
            method: Method name (e.g., "SubscribeCustomer")
            args: Arguments list
        """
        self.message_id += 1

        message = {
            "H": self.hub_name,  # Hub name
            "M": method,  # Method name
            "A": args,  # Arguments
            "I": self.message_id,  # Message ID
        }

        logger.info(f"[INVOKE] {method}({args})")
        self.send_message(message)

    def subscribe_customer(self):
        """Subscribe as customer"""
        logger.info(f"Subscribing as customer: {self.customer_id}")

        user_data = {"customerId": self.customer_id, "password": self.password}

        self.invoke_hub_method("SubscribeCustomer", [user_data])

    def subscribe_sports(self):
        """Subscribe to NFL and NCAAF"""
        logger.info("Subscribing to sports...")

        # Try different subscription formats
        subscriptions = [
            {"sport": "FOOTBALL", "league": "NFL"},
            {"sport": "FOOTBALL", "league": "NCAAF"},
        ]

        # Use SubscribeSports (plural)
        self.invoke_hub_method("SubscribeSports", [subscriptions])

        # Also try individual subscriptions
        for sub in subscriptions:
            self.invoke_hub_method("SubscribeSport", [sub])

    # Message Handlers

    def handle_hub_invocation(self, msg: dict):
        """Handle hub method invocation from server"""
        method = msg.get("M")  # Method name
        args = msg.get("A", [])  # Arguments

        logger.info(f"[HUB INVOCATION] {method}({len(args)} args)")

        if args:
            for i, arg in enumerate(args):
                logger.info(f"  Arg {i}: {json.dumps(arg, indent=2)[:500]}")

        # Save specific types
        if method and (
            "game" in method.lower()
            or "odds" in method.lower()
            or "line" in method.lower()
        ):
            self.games_received.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "method": method,
                    "data": args,
                }
            )

            self._save_game_data(method, args)

    def _save_message(self, data: dict):
        """Save message to JSON file"""
        os.makedirs("output/signalr/messages", exist_ok=True)

        filename = f"output/signalr/messages/msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {"timestamp": datetime.utcnow().isoformat(), "data": data}, f, indent=2
            )

    def _save_game_data(self, method: str, data: list):
        """Save game-related data"""
        os.makedirs("output/signalr/games", exist_ok=True)

        filename = f"output/signalr/games/{method}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "method": method,
                    "data": data,
                },
                f,
                indent=2,
            )

        logger.info(f"Saved game data to {filename}")

    # Main Loop

    def run(self, duration: int = 300):
        """
        Run the SignalR client

        Args:
            duration: How long to run in seconds
        """
        logger.info("=" * 60)
        logger.info("Overtime.ag Manual SignalR 1.x Client")
        logger.info("=" * 60)

        # Negotiate
        if not self.negotiate():
            logger.error("Negotiation failed, exiting")
            return

        # Connect
        if not self.connect():
            logger.error("Connection failed, exiting")
            return

        logger.info(f"Running for {duration} seconds...")
        logger.info("Press Ctrl+C to stop early")

        # Run WebSocket in thread with timeout
        import threading

        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                time.sleep(1)

                # Status every 30 seconds
                if int(time.time() - start_time) % 30 == 0:
                    logger.info(
                        f"Status: {len(self.messages_received)} messages, {len(self.games_received)} game updates"
                    )

        except KeyboardInterrupt:
            logger.info("\nStopping (Ctrl+C pressed)...")

        finally:
            # Close connection
            if self.ws:
                self.ws.close()

            # Wait for thread
            ws_thread.join(timeout=2)

            # Summary
            logger.info("=" * 60)
            logger.info("Session Summary:")
            logger.info(f"Messages received: {len(self.messages_received)}")
            logger.info(f"Game updates: {len(self.games_received)}")
            logger.info("=" * 60)


def main():
    """Main entry point"""
    client = SignalR1xClient()

    # Default 5 minutes, or pass duration as argument
    duration = 300
    if len(sys.argv) > 1:
        duration = int(sys.argv[1])

    client.run(duration=duration)


if __name__ == "__main__":
    main()
