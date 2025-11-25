"""
Results Validator - Compare Predictions vs Actual Scores

Loads edge detection predictions and compares against actual NFL game results
to calculate:
- Against The Spread (ATS) performance
- Win/Loss accuracy
- Closing Line Value (CLV)
- ROI based on Kelly sizing
- Confidence score validation

Usage:
    validator = ResultsValidator()
    results = await validator.validate_week(season=2025, week=12)
    report = await validator.generate_report(results)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class PredictionResult(BaseModel):
    """Individual prediction result"""

    matchup: str
    week: int
    away_team: str
    home_team: str
    predicted_spread: float
    market_spread: float
    predicted_total: Optional[float] = None
    market_total: Optional[float] = None
    away_score: Optional[int] = None
    home_score: Optional[int] = None
    recommended_bet: str  # "home" or "away"
    kelly_fraction: float
    confidence_score: float
    edge_strength: str

    # Results
    actual_margin: Optional[int] = None
    ats_result: Optional[str] = None  # "WIN", "LOSS", "PUSH"
    straight_up: Optional[str] = None  # "WIN", "LOSS"
    closing_line_value: Optional[float] = None
    game_status: str = "pending"

    @property
    def is_completed(self) -> bool:
        """Check if game result is available"""
        return self.away_score is not None and self.home_score is not None


class ResultsValidator:
    """
    Validates predictions against actual game results.

    Loads edge detection predictions and compares with actual scores
    to measure model accuracy and CLV.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize results validator.

        Args:
            project_root: Root directory of project
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent.parent

        self.project_root = project_root
        self.edges_dir = project_root / "output" / "edge_detection"
        self.reports_dir = project_root / "docs" / "performance_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def load_week_edges(self, week: int) -> List[Dict[str, Any]]:
        """
        Load edge detection results for a specific week.

        Args:
            week: Week number (1-18)

        Returns:
            List of edge dictionaries
        """
        # Try multiple file naming patterns
        possible_files = [
            self.edges_dir / f"nfl_edges_detected_week_{week}.jsonl",
            self.edges_dir / f"nfl_edges_week_{week}.jsonl",
            self.edges_dir / "nfl_edges_detected.jsonl",
        ]

        edges = []
        for filepath in possible_files:
            if filepath.exists():
                logger.info(f"Loading edges from {filepath}")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                edges.append(json.loads(line))
                    return edges
                except Exception as e:
                    logger.warning(f"Error loading {filepath}: {e}")
                    continue

        logger.warning(f"No edge file found for Week {week}")
        return edges

    def load_week_scores(self, week: int) -> Dict[str, Dict[str, Any]]:
        """
        Load actual game scores for a specific week.

        Args:
            week: Week number (1-18)

        Returns:
            Dictionary mapping matchup to score data
        """
        # Try to load from saved scores
        scores_file = (
            self.project_root
            / "output"
            / "nfl_scores"
            / f"scores_2025_week_{week:02d}.json"
        )

        scores = {}
        if scores_file.exists():
            logger.info(f"Loading scores from {scores_file}")
            try:
                with open(scores_file, "r", encoding="utf-8") as f:
                    score_list = json.load(f)
                    for score in score_list:
                        # Store by both abbreviated and full keys
                        abbr_key = f"{score['away_team']}_{score['home_team']}"
                        scores[abbr_key] = score
            except Exception as e:
                logger.warning(f"Error loading scores: {e}")

        return scores

    @staticmethod
    def team_abbr_from_name(team_name: str) -> str:
        """
        Convert full team name to abbreviation.

        Args:
            team_name: Full team name (e.g., "New England")

        Returns:
            Team abbreviation (e.g., "NE")
        """
        team_map = {
            "New England": "NE",
            "New York Giants": "NYG",
            "New York Jets": "NYJ",
            "San Francisco": "SF",
            "Los Angeles Rams": "LAR",
            "Los Angeles Chargers": "LAC",
            "Green Bay": "GB",
            "Kansas City": "KC",
            "Las Vegas": "LV",
            "New Orleans": "NO",
            "Tampa Bay": "TB",
            "Pittsburgh": "PIT",
            "Chicago": "CHI",
            "Cincinnati": "CIN",
            "Minnesota": "MIN",
            "Indianapolis": "IND",
            "Cleveland": "CLE",
            "Atlanta": "ATL",
            "Detroit": "DET",
            "Philadelphia": "PHI",
            "Dallas": "DAL",
            "Baltimore": "BAL",
            "Tennessee": "TEN",
            "Seattle": "SEA",
            "Arizona": "ARI",
            "Jacksonville": "JAX",
            "Buffalo": "BUF",
            "Houston": "HOU",
            "Denver": "DEN",
            "Carolina": "CAR",
            "Washington": "WAS",
            "Miami": "MIA",
        }
        return team_map.get(team_name, team_name[:2].upper())

    async def validate_week(self, week: int) -> List[PredictionResult]:
        """
        Validate all predictions for a specific week.

        Args:
            week: Week number (1-18)

        Returns:
            List of PredictionResult objects
        """
        edges = self.load_week_edges(week)
        scores = self.load_week_scores(week)

        results = []

        for edge in edges:
            # Create prediction result from edge
            pred = PredictionResult(
                matchup=edge.get("matchup", ""),
                week=edge.get("week", week),
                away_team=edge.get("away_team", ""),
                home_team=edge.get("home_team", ""),
                predicted_spread=edge.get("predicted_spread", 0.0),
                market_spread=edge.get("market_spread", 0.0),
                market_total=edge.get("market_total"),
                recommended_bet=edge.get("recommended_bet", ""),
                kelly_fraction=edge.get("kelly_fraction", 0.0),
                confidence_score=edge.get("confidence_score", 0.0),
                edge_strength=edge.get("edge_strength", "unknown"),
            )

            # Look for matching score - try both full name and abbreviation
            away_abbr = self.team_abbr_from_name(pred.away_team)
            home_abbr = self.team_abbr_from_name(pred.home_team)
            score_key = f"{away_abbr}_{home_abbr}"

            if score_key in scores:
                score_data = scores[score_key]
                pred.away_score = score_data.get("away_score")
                pred.home_score = score_data.get("home_score")
                pred.game_status = score_data.get("game_status", "unknown")

                # Calculate results
                if pred.is_completed:
                    pred.actual_margin = pred.home_score - pred.away_score

                    # ATS result
                    if pred.recommended_bet == "home":
                        spread_line = pred.market_spread
                        if pred.actual_margin > spread_line:
                            pred.ats_result = "WIN"
                        elif pred.actual_margin < spread_line:
                            pred.ats_result = "LOSS"
                        else:
                            pred.ats_result = "PUSH"
                    elif pred.recommended_bet == "away":
                        spread_line = -pred.market_spread
                        if pred.actual_margin < spread_line:
                            pred.ats_result = "WIN"
                        elif pred.actual_margin > spread_line:
                            pred.ats_result = "LOSS"
                        else:
                            pred.ats_result = "PUSH"

                    # Straight up result
                    if pred.actual_margin > 0:
                        pred.straight_up = (
                            "HOME" if pred.recommended_bet == "home" else "LOSS"
                        )
                    else:
                        pred.straight_up = (
                            "AWAY" if pred.recommended_bet == "away" else "LOSS"
                        )

                    # CLV (simplified - need actual closing line)
                    pred.closing_line_value = pred.market_spread - pred.predicted_spread

            results.append(pred)

        logger.info(
            f"Validated {len(results)} predictions for Week {week} "
            f"({len([r for r in results if r.is_completed])} completed)"
        )
        return results

    def calculate_performance_stats(
        self, results: List[PredictionResult]
    ) -> Dict[str, Any]:
        """
        Calculate overall performance statistics.

        Args:
            results: List of PredictionResult objects

        Returns:
            Dictionary with performance metrics
        """
        completed = [r for r in results if r.is_completed]

        if not completed:
            return {
                "total_games": 0,
                "completed_games": 0,
                "ats_wins": 0,
                "ats_losses": 0,
                "ats_pushes": 0,
                "ats_win_pct": 0.0,
                "roi": 0.0,
            }

        ats_wins = sum(1 for r in completed if r.ats_result == "WIN")
        ats_losses = sum(1 for r in completed if r.ats_result == "LOSS")
        ats_pushes = sum(1 for r in completed if r.ats_result == "PUSH")

        ats_win_pct = (
            ats_wins / (ats_wins + ats_losses) * 100
            if (ats_wins + ats_losses) > 0
            else 0.0
        )

        # Calculate ROI (simplified - assumes -110 odds)
        total_wagered = 0.0
        total_profit = 0.0

        for result in completed:
            if result.ats_result and result.kelly_fraction > 0:
                # Assume standard -110 odds
                odds_payout = 0.909  # -110 pays 0.909 to 1

                bet_amount = result.kelly_fraction / 100  # as percentage
                if result.ats_result == "WIN":
                    total_profit += bet_amount * odds_payout
                elif result.ats_result == "LOSS":
                    total_profit -= bet_amount
                # PUSH = 0

                total_wagered += bet_amount

        roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0.0

        return {
            "total_games": len(results),
            "completed_games": len(completed),
            "pending_games": len(results) - len(completed),
            "ats_wins": ats_wins,
            "ats_losses": ats_losses,
            "ats_pushes": ats_pushes,
            "ats_record": f"{ats_wins}-{ats_losses}-{ats_pushes}",
            "ats_win_pct": round(ats_win_pct, 1),
            "roi": round(roi, 1),
            "avg_confidence": round(
                sum(r.confidence_score for r in completed) / len(completed), 1
            ),
        }

    async def generate_report(self, results: List[PredictionResult], week: int) -> str:
        """
        Generate markdown report of results.

        Args:
            results: List of PredictionResult objects
            week: Week number

        Returns:
            Markdown report string
        """
        stats = self.calculate_performance_stats(results)
        completed = [r for r in results if r.is_completed]

        report = []
        report.append("# NFL Week Results Validation Report\n")
        report.append(f"**Week:** {week}\n")
        report.append(
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        report.append("---\n")

        # Summary
        report.append("## Summary\n")
        report.append(f"- **ATS Record:** {stats['ats_record']}\n")
        report.append(f"- **Win %:** {stats['ats_win_pct']}%\n")
        report.append(
            f"- **Games Completed:** {stats['completed_games']}/{stats['total_games']}\n"
        )
        report.append(f"- **ROI:** {stats['roi']}%\n")
        report.append(f"- **Avg Confidence:** {stats['avg_confidence']}\n")
        report.append("\n")

        # Detailed results
        report.append("## Game Results\n\n")
        for result in completed:
            status_icon = (
                "✅"
                if result.ats_result == "WIN"
                else "❌"
                if result.ats_result == "LOSS"
                else "➡️"
            )
            report.append(f"{status_icon} **{result.matchup}**\n")
            report.append(
                f"   Score: {result.away_team} {result.away_score} @ {result.home_team} {result.home_score}\n"
            )
            report.append(
                f"   Margin: {result.actual_margin:+d} | Spread: {result.market_spread:+.1f}\n"
            )
            report.append(
                f"   Bet: {result.recommended_bet} | Result: {result.ats_result}\n"
            )
            report.append(
                f"   Edge: {result.edge_strength} | Confidence: {result.confidence_score:.1f}\n\n"
            )

        # Pending games
        pending = [r for r in results if not r.is_completed]
        if pending:
            report.append("## Pending Games\n\n")
            for result in pending:
                report.append(f"⏳ **{result.matchup}**\n")
                report.append(f"   Status: {result.game_status}\n")
                report.append("\n")

        return "".join(report)

    async def save_report(self, report: str, week: int, season: int = 2025) -> Path:
        """
        Save report to file.

        Args:
            report: Markdown report content
            week: Week number
            season: Season year

        Returns:
            Path to saved report
        """
        filename = f"nfl_week_{week:02d}_results_report.md"
        filepath = self.reports_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Saved report to {filepath}")
        return filepath
