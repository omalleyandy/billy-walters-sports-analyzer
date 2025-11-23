#!/usr/bin/env python3
"""
ESPN Team Statistics Integration for Billy Walters Edge Detector

Integrates real-time ESPN team performance metrics into power rating calculations
using the Billy Walters 90/10 update formula:
- 90% weight: Historical power rating (Massey)
- 10% weight: Current season performance (ESPN stats)

Key metrics used:
- Points per game (offensive efficiency)
- Points allowed per game (defensive efficiency)
- Turnover margin (ball security)
- Yards per game (offensive productivity)
- Yards allowed per game (defensive strength)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ESPNDataLoader:
    """Load and manage ESPN team statistics from archived data"""

    def __init__(self, archive_root: str = "data/archive/raw"):
        """
        Initialize ESPN data loader

        Args:
            archive_root: Root directory for archived ESPN data
        """
        self.archive_root = Path(archive_root)
        self.team_stats_cache: Dict[str, Dict] = {}
        self.last_loaded: Optional[datetime] = None

        # Lazy import to avoid circular dependencies
        self._api_client = None

    def find_latest_team_stats(self, league: str = "ncaaf") -> Optional[Path]:
        """
        Find the latest team statistics file for a league

        Args:
            league: "nfl" or "ncaaf"

        Returns:
            Path to latest team stats file, or None if not found
        """
        stats_dir = self.archive_root / league / "team_stats" / "current"

        if not stats_dir.exists():
            logger.warning(f"Team stats directory not found: {stats_dir}")
            return None

        json_files = sorted(stats_dir.glob("team_stats_*.json"), reverse=True)

        if not json_files:
            logger.warning(f"No team stats files found in {stats_dir}")
            return None

        latest = json_files[0]
        logger.debug(f"Found latest team stats: {latest.name}")
        return latest

    def load_team_stats(self, filepath: Path) -> Dict[str, Dict]:
        """
        Load team statistics from ESPN archived file

        Args:
            filepath: Path to team stats JSON file

        Returns:
            Dictionary mapping team names to their statistics
        """
        logger.info(f"Loading ESPN team statistics from {filepath.name}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            stats_dict: Dict[str, Dict] = {}

            # The archived data contains the raw API response
            # Extract stats from each team
            if "sports" not in data:
                logger.error("Invalid ESPN data structure: missing 'sports' key")
                return stats_dict

            sports_list = data.get("sports", [])
            if not sports_list:
                logger.warning("No sports data found")
                return stats_dict

            # Get teams from the league structure
            leagues = sports_list[0].get("leagues", [])
            if not leagues:
                logger.warning("No leagues found")
                return stats_dict

            teams_list = leagues[0].get("teams", [])
            logger.info(f"Processing {len(teams_list)} teams from ESPN data")

            # Process each team
            for team_item in teams_list:
                team_info = team_item.get("team", {})
                team_name = team_info.get("displayName")
                team_id = team_info.get("id")

                if not team_name:
                    continue

                # Store raw team data for reference
                stats_dict[team_name] = {
                    "team_id": team_id,
                    "team_name": team_name,
                    "display_name": team_name,
                    "abbreviation": team_info.get("abbreviation"),
                    "raw_data": team_item,
                }

            self.team_stats_cache = stats_dict
            self.last_loaded = datetime.now()

            logger.info(f"Loaded {len(stats_dict)} teams from ESPN data")
            return stats_dict

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing ESPN team stats: {e}")
            return {}

    def load_team_stats_by_league(self, league: str = "ncaaf") -> Dict[str, Dict]:
        """
        Load latest team statistics for a league

        Args:
            league: "nfl" or "ncaaf"

        Returns:
            Dictionary mapping team names to their statistics
        """
        latest_file = self.find_latest_team_stats(league)

        if not latest_file:
            logger.warning(f"No team stats found for {league}")
            return {}

        return self.load_team_stats(latest_file)

    def extract_team_metrics(self, team_name: str) -> Optional[Dict]:
        """
        Extract performance metrics for a specific team

        Note: The archived data contains the teams list from ESPN.
        Actual statistics are in the ESPN API client's extract_power_rating_metrics()
        method. This method is a placeholder for extracting basic team info.

        Args:
            team_name: Name of team to extract metrics for

        Returns:
            Dictionary of team metrics, or None if not found
        """
        if not self.team_stats_cache:
            logger.warning("Team stats not loaded. Call load_team_stats first.")
            return None

        return self.team_stats_cache.get(team_name)


class PowerRatingEnhancer:
    """
    Enhance power ratings using ESPN team statistics
    Implements Billy Walters' 90/10 formula
    """

    # Baseline metrics for calculation (2024 season averages)
    BASELINE_PPG_NFL = 22.5
    BASELINE_PAPG_NFL = 22.5
    BASELINE_PPG_NCAAF = 28.5
    BASELINE_PAPG_NCAAF = 28.5

    def __init__(self, league: str = "ncaaf"):
        """
        Initialize power rating enhancer

        Args:
            league: "nfl" or "ncaaf"
        """
        self.league = league
        self.loader = ESPNDataLoader()
        self.baseline_ppg = (
            self.BASELINE_PPG_NCAAF if league == "ncaaf" else self.BASELINE_PPG_NFL
        )
        self.baseline_papg = (
            self.BASELINE_PAPG_NCAAF if league == "ncaaf" else self.BASELINE_PAPG_NFL
        )

    def calculate_metric_adjustment(
        self, espn_metrics: Dict, massey_rating: float
    ) -> float:
        """
        Calculate power rating adjustment from ESPN metrics

        Uses Billy Walters' formula:
        adjustment = (PPG - baseline) * 0.15 +
                    (baseline - PAPG) * 0.15 +
                    turnover_margin * 0.3

        Args:
            espn_metrics: ESPN team statistics dictionary
            massey_rating: Baseline Massey power rating

        Returns:
            Power rating adjustment in points
        """
        adjustment = 0.0

        try:
            # Offensive adjustment: points per game
            ppg = espn_metrics.get("points_per_game")
            if ppg is not None:
                ppg_adjustment = (float(ppg) - self.baseline_ppg) * 0.15
                adjustment += ppg_adjustment
                logger.debug(
                    f"PPG adjustment: {ppg:.1f} PPG = {ppg_adjustment:+.2f} pts"
                )

            # Defensive adjustment: points allowed per game
            papg = espn_metrics.get("points_allowed_per_game")
            if papg is not None:
                papg_adjustment = (self.baseline_papg - float(papg)) * 0.15
                adjustment += papg_adjustment
                logger.debug(
                    f"PAPG adjustment: {papg:.1f} PAPG = {papg_adjustment:+.2f} pts"
                )

            # Ball security: turnover margin
            to_margin = espn_metrics.get("turnover_margin")
            if to_margin is not None:
                to_adjustment = float(to_margin) * 0.3
                adjustment += to_adjustment
                logger.debug(
                    f"TO margin adjustment: {to_margin:+.0f} = {to_adjustment:+.2f} pts"
                )

        except (TypeError, ValueError) as e:
            logger.warning(
                f"Error calculating metric adjustment: {e}. Using zero adjustment."
            )

        return adjustment

    def enhance_power_rating(
        self,
        team_name: str,
        massey_rating: float,
        espn_metrics: Optional[Dict] = None,
        weight_espn: float = 0.1,
    ) -> Tuple[float, float]:
        """
        Enhance power rating with ESPN metrics using 90/10 formula

        Formula:
        enhanced_rating = massey_rating * 0.9 + (massey_rating + adjustment) * 0.1

        Args:
            team_name: Team name for logging
            massey_rating: Base Massey power rating (70-100 scale)
            espn_metrics: ESPN team statistics
            weight_espn: Weight for ESPN data (default 0.1 for 90/10)

        Returns:
            Tuple of (enhanced_rating, adjustment)
        """
        if espn_metrics is None:
            return massey_rating, 0.0

        adjustment = self.calculate_metric_adjustment(espn_metrics, massey_rating)
        capped_adjustment = max(-10.0, min(10.0, adjustment))

        # Apply 90/10 formula
        adjusted_rating = massey_rating + capped_adjustment
        enhanced_rating = (
            massey_rating * (1 - weight_espn) + adjusted_rating * weight_espn
        )

        logger.info(
            f"{team_name}: {massey_rating:.1f} "
            f"({adjustment:+.2f} raw, {capped_adjustment:+.2f} capped) "
            f"→ {enhanced_rating:.1f} (90/10)"
        )

        return enhanced_rating, adjustment
