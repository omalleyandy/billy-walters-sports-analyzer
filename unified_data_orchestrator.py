#!/usr/bin/env python3
"""
Billy Walters Unified Data Orchestrator
Coordinates ESPN API and overtime.ag SignalR for complete football data collection
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Import our custom clients
from espn_api_client import ESPNAPIClient
from overtime_signalr_manual import SignalR1xClient

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("orchestrator.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class GameScheduleDetector:
    """Detects if games are currently active based on day/time"""

    @staticmethod
    def is_nfl_game_time() -> bool:
        """Check if it's NFL game time"""
        now = datetime.now()
        day = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour

        # Thursday Night Football (Thursday 8pm-11pm ET)
        if day == 3 and 20 <= hour <= 23:
            return True

        # Sunday games (Sunday 1pm-11pm ET)
        if day == 6 and 13 <= hour <= 23:
            return True

        # Monday Night Football (Monday 8pm-11pm ET)
        if day == 0 and 20 <= hour <= 23:
            return True

        return False

    @staticmethod
    def is_ncaaf_game_time() -> bool:
        """Check if it's NCAAF game time"""
        now = datetime.now()
        day = now.weekday()

        # College football mainly on Saturday (12pm-11pm ET)
        if day == 5 and 12 <= now.hour <= 23:
            return True

        # Some Friday night games (7pm-11pm ET)
        if day == 4 and 19 <= now.hour <= 23:
            return True

        return False

    @staticmethod
    def should_run_live_odds() -> bool:
        """Check if we should run live odds collection"""
        return (
            GameScheduleDetector.is_nfl_game_time()
            or GameScheduleDetector.is_ncaaf_game_time()
        )


class UnifiedDataOrchestrator:
    """
    Master orchestrator that coordinates all data collection:
    - ESPN API for schedules, stats, injuries, scores
    - overtime.ag SignalR for live betting odds
    """

    def __init__(self):
        """Initialize orchestrator"""
        self.espn_client = ESPNAPIClient()
        self.signalr_client = None  # Created when needed
        self.signalr_thread = None

        self.output_base = "output/unified"
        os.makedirs(self.output_base, exist_ok=True)

        logger.info("Unified Data Orchestrator initialized")

    # ESPN Data Collection

    def collect_espn_schedules(self):
        """Collect schedules from ESPN"""
        logger.info("Collecting ESPN schedules...")

        try:
            # NFL Schedule
            nfl_schedule = self.espn_client.get_nfl_scoreboard()
            self._save_data(nfl_schedule, f"{self.output_base}/nfl_schedule.json")

            # NCAAF Schedule
            ncaaf_schedule = self.espn_client.get_ncaaf_scoreboard()
            self._save_data(ncaaf_schedule, f"{self.output_base}/ncaaf_schedule.json")

            logger.info("ESPN schedules collected successfully")
            return True

        except Exception as e:
            logger.error(f"Error collecting ESPN schedules: {e}")
            return False

    def collect_espn_teams(self):
        """Collect team data from ESPN"""
        logger.info("Collecting ESPN teams...")

        try:
            # NFL Teams
            nfl_teams = self.espn_client.get_nfl_teams()
            self._save_data(nfl_teams, f"{self.output_base}/nfl_teams.json")

            # NCAAF Teams (FBS - Group 80)
            ncaaf_teams = self.espn_client.get_ncaaf_teams(group="80")
            self._save_data(ncaaf_teams, f"{self.output_base}/ncaaf_teams.json")

            logger.info("ESPN teams collected successfully")
            return True

        except Exception as e:
            logger.error(f"Error collecting ESPN teams: {e}")
            return False

    def collect_espn_injuries(self, team_ids: List[str], league: str = "nfl"):
        """
        Collect injury reports from ESPN

        Args:
            team_ids: List of ESPN team IDs
            league: 'nfl' or 'college-football'
        """
        logger.info(f"Collecting {league} injuries for {len(team_ids)} teams...")

        injuries = {}
        for team_id in team_ids:
            try:
                injury_data = self.espn_client.get_team_injuries(team_id, league)
                injuries[team_id] = injury_data
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.warning(f"Error collecting injuries for team {team_id}: {e}")
                continue

        self._save_data(injuries, f"{self.output_base}/{league}_injuries.json")
        logger.info(f"Collected injuries for {len(injuries)} teams")

    def collect_espn_live_scores(self):
        """Collect live scores from ESPN"""
        logger.info("Collecting ESPN live scores...")

        try:
            # NFL Scores
            nfl_scores = self.espn_client.get_nfl_scoreboard()
            self._save_data_timestamped(
                nfl_scores, f"{self.output_base}/live/nfl_scores"
            )

            # NCAAF Scores
            ncaaf_scores = self.espn_client.get_ncaaf_scoreboard()
            self._save_data_timestamped(
                ncaaf_scores, f"{self.output_base}/live/ncaaf_scores"
            )

            logger.info("ESPN live scores collected successfully")
            return True

        except Exception as e:
            logger.error(f"Error collecting ESPN live scores: {e}")
            return False

    # SignalR Live Odds Collection

    def start_signalr_collection(self, duration: int = 3600):
        """
        Start SignalR live odds collection in background thread

        Args:
            duration: How long to collect (seconds)
        """
        logger.info("Starting SignalR live odds collection...")

        try:
            self.signalr_client = SignalR1xClient()

            # Run in background thread
            self.signalr_thread = threading.Thread(
                target=self.signalr_client.run, kwargs={"duration": duration}
            )
            self.signalr_thread.daemon = True
            self.signalr_thread.start()

            logger.info(f"SignalR collection started (duration: {duration}s)")
            return True

        except Exception as e:
            logger.error(f"Error starting SignalR collection: {e}")
            return False

    def stop_signalr_collection(self):
        """Stop SignalR collection"""
        if self.signalr_client and self.signalr_client.ws:
            logger.info("Stopping SignalR collection...")
            self.signalr_client.ws.close()

            if self.signalr_thread:
                self.signalr_thread.join(timeout=5)

            logger.info("SignalR collection stopped")

    # Data Management

    def _save_data(self, data: Dict, filepath: str):
        """Save data to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved data to {filepath}")

    def _save_data_timestamped(self, data: Dict, base_path: str):
        """Save data with timestamp in filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"{base_path}_{timestamp}.json"

        self._save_data(data, filepath)

    # Orchestration Modes

    def run_initial_setup(self):
        """
        Initial data collection - run once at startup
        Collects static/slow-changing data
        """
        logger.info("=" * 60)
        logger.info("Running Initial Setup")
        logger.info("=" * 60)

        # Collect teams (needed for injury reports)
        self.collect_espn_teams()

        # Collect schedules
        self.collect_espn_schedules()

        logger.info("Initial setup complete")

    def run_live_game_mode(self, duration: int = 3600):
        """
        Live game mode - runs during active games
        Collects live scores every 15 seconds + SignalR odds

        Args:
            duration: How long to run (seconds)
        """
        logger.info("=" * 60)
        logger.info("Running Live Game Mode")
        logger.info("=" * 60)

        # Start SignalR in background
        self.start_signalr_collection(duration=duration)

        # Poll ESPN every 15 seconds
        start_time = time.time()
        iteration = 0

        try:
            while time.time() - start_time < duration:
                iteration += 1
                logger.info(f"Live update iteration {iteration}")

                # Collect live scores
                self.collect_espn_live_scores()

                # Wait 15 seconds
                time.sleep(15)

        except KeyboardInterrupt:
            logger.info("Live mode interrupted by user")

        finally:
            # Stop SignalR
            self.stop_signalr_collection()

        logger.info("Live game mode complete")

    def run_continuous_mode(self):
        """
        Continuous mode - runs indefinitely
        Smart about when to collect live data
        """
        logger.info("=" * 60)
        logger.info("Running Continuous Mode")
        logger.info("=" * 60)

        # Initial setup
        self.run_initial_setup()

        while True:
            try:
                # Check if games are active
                if GameScheduleDetector.should_run_live_odds():
                    logger.info("Games detected! Starting live collection...")

                    # Run live mode for 1 hour
                    self.run_live_game_mode(duration=3600)

                    logger.info("Live collection finished, resuming monitoring...")

                else:
                    # Not game time - just update schedules periodically
                    logger.info("No active games. Updating schedules...")
                    self.collect_espn_schedules()

                    # Wait 30 minutes before checking again
                    logger.info("Sleeping 30 minutes...")
                    time.sleep(1800)

            except KeyboardInterrupt:
                logger.info("Continuous mode stopped by user")
                break

            except Exception as e:
                logger.error(f"Error in continuous mode: {e}")
                logger.info("Sleeping 5 minutes before retry...")
                time.sleep(300)

        logger.info("Continuous mode complete")

    # Quick Data Access

    def get_current_games(self, league: str = "nfl") -> List[Dict]:
        """
        Get currently active games

        Args:
            league: 'nfl' or 'ncaaf'

        Returns:
            List of active games
        """
        if league == "nfl":
            scoreboard = self.espn_client.get_nfl_scoreboard()
        else:
            scoreboard = self.espn_client.get_ncaaf_scoreboard()

        events = scoreboard.get("events", [])

        # Filter for active games
        active_games = []
        for event in events:
            status = event.get("status", {}).get("type", {}).get("state")
            if status == "in":  # Game is in progress
                active_games.append(event)

        return active_games

    def summarize_data_status(self):
        """Print summary of collected data"""
        logger.info("=" * 60)
        logger.info("Data Collection Summary")
        logger.info("=" * 60)

        files = {
            "NFL Schedule": f"{self.output_base}/nfl_schedule.json",
            "NCAAF Schedule": f"{self.output_base}/ncaaf_schedule.json",
            "NFL Teams": f"{self.output_base}/nfl_teams.json",
            "NCAAF Teams": f"{self.output_base}/ncaaf_teams.json",
        }

        for name, filepath in files.items():
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                logger.info(
                    f"{name}: {size} bytes (updated {modified.strftime('%Y-%m-%d %H:%M:%S')})"
                )
            else:
                logger.info(f"{name}: NOT FOUND")

        # Count live data files
        live_dir = f"{self.output_base}/live"
        if os.path.exists(live_dir):
            live_files = len([f for f in os.listdir(live_dir) if f.endswith(".json")])
            logger.info(f"Live data snapshots: {live_files} files")

        # Count SignalR data
        signalr_dir = "output/signalr"
        if os.path.exists(signalr_dir):
            msg_dir = f"{signalr_dir}/messages"
            game_dir = f"{signalr_dir}/games"

            if os.path.exists(msg_dir):
                msgs = len([f for f in os.listdir(msg_dir) if f.endswith(".json")])
                logger.info(f"SignalR messages: {msgs} files")

            if os.path.exists(game_dir):
                games = len([f for f in os.listdir(game_dir) if f.endswith(".json")])
                logger.info(f"SignalR game updates: {games} files")

        logger.info("=" * 60)


def main():
    """Main entry point with CLI"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Billy Walters Unified Data Orchestrator"
    )
    parser.add_argument(
        "mode", choices=["setup", "live", "continuous"], help="Orchestration mode"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=3600,
        help="Duration for live mode (seconds, default 3600)",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show data summary after completion"
    )

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = UnifiedDataOrchestrator()

    # Run selected mode
    try:
        if args.mode == "setup":
            orchestrator.run_initial_setup()

        elif args.mode == "live":
            orchestrator.run_live_game_mode(duration=args.duration)

        elif args.mode == "continuous":
            orchestrator.run_continuous_mode()

        # Show summary if requested
        if args.summary:
            orchestrator.summarize_data_status()

    except KeyboardInterrupt:
        logger.info("\nStopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
