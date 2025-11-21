"""
CLV Storage System - Persistent Tracking of Betting CLV

This module implements dual persistence for CLV tracking:
- JSON: Current bets (mutable, updated as information arrives)
- CSV: Historical log (append-only, immutable audit trail)

Together they provide:
1. Real-time updates to bet records
2. Immutable audit trail for historical analysis
3. Weekly/season summary generation
4. Export capabilities for external analysis

Billy Walters Principle: "If you consistently beat the closing line,
you've identified true market inefficiencies and will be profitable
long-term regardless of short-term win-loss record."
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict
import json
import csv
from datetime import datetime, date
import logging

from src.walters_analyzer.models.clv_tracking_module import (
    CLVTracking,
    CLVSummary,
    CLVOutcome,
    CLVAnalyzer,
)

logger = logging.getLogger(__name__)


class CLVStorage:
    """
    Persistent storage for CLV tracking records.

    Implements dual persistence strategy:
    - JSON file: Current/active bets (mutable, enables updates)
    - CSV file: Historical log (append-only, immutable audit trail)

    This allows bets to be updated as information arrives (opening line →
    closing line → final result) while maintaining an immutable historical
    record of all changes.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize CLV storage.

        Args:
            data_dir: Path to data directory. Defaults to
                     src/walters_analyzer/data/clv/
        """
        if data_dir is None:
            # Use project-relative path
            data_dir = Path(__file__).parent.parent / "data" / "clv"
        else:
            data_dir = Path(data_dir)

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.bets_json = self.data_dir / "bets.json"
        self.history_csv = self.data_dir / "bets_history.csv"
        self.summaries_json = self.data_dir / "summaries.json"

        logger.info(f"CLVStorage initialized at {self.data_dir}")

    def save_bet(self, bet: CLVTracking) -> None:
        """
        Save or update CLV tracking record.

        Saves to JSON (mutable) and appends record to CSV (immutable).

        Args:
            bet: CLVTracking record to save

        Raises:
            ValueError: If bet data is invalid
            IOError: If file write fails
        """
        if not isinstance(bet, CLVTracking):
            raise ValueError(f"Expected CLVTracking, got {type(bet)}")

        # Load existing bets
        bets = self._load_all_bets()

        # Update or add
        bets[bet.recommendation_id] = bet.model_dump(mode="json")

        # Save to JSON
        try:
            self._save_json(self.bets_json, bets)
            logger.debug(f"Saved bet {bet.recommendation_id} to JSON")
        except IOError as e:
            logger.error(f"Failed to save JSON: {e}")
            raise

        # Append to CSV history
        try:
            self._append_to_csv(bet)
            logger.debug(f"Appended bet {bet.recommendation_id} to CSV")
        except IOError as e:
            logger.error(f"Failed to append to CSV: {e}")
            raise

        logger.info(f"✓ Saved bet {bet.recommendation_id}")

    def load_bet(self, recommendation_id: str) -> Optional[CLVTracking]:
        """
        Load single bet from storage.

        Args:
            recommendation_id: Unique bet identifier

        Returns:
            CLVTracking object if found, None otherwise

        Raises:
            ValueError: If stored data is malformed
        """
        bets = self._load_all_bets()

        if recommendation_id not in bets:
            logger.warning(f"Bet {recommendation_id} not found")
            return None

        try:
            return CLVTracking(**bets[recommendation_id])
        except Exception as e:
            logger.error(f"Failed to load bet {recommendation_id}: {e}")
            raise ValueError(f"Malformed bet data for {recommendation_id}") from e

    def list_all(self) -> List[CLVTracking]:
        """
        Get all bets from storage.

        Returns:
            List of all CLVTracking records
        """
        bets = self._load_all_bets()
        return [CLVTracking(**data) for data in bets.values()]

    def list_pending(self, limit: Optional[int] = None) -> List[CLVTracking]:
        """
        Get all unresolved bets.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of unresolved CLVTracking records
        """
        bets = self._load_all_bets()
        pending = [
            CLVTracking(**data)
            for data in bets.values()
            if data["clv_outcome"] == "pending"
        ]

        if limit:
            pending = pending[:limit]

        logger.info(f"Found {len(pending)} pending bets")
        return pending

    def list_by_week(self, week: int, season: int = 2025) -> List[CLVTracking]:
        """
        Get all bets from specific week.

        Args:
            week: Week number (1-17 for NFL)
            season: Year (default 2025)

        Returns:
            List of CLVTracking records for week
        """
        bets = self._load_all_bets()
        week_bets = [
            CLVTracking(**data)
            for data in bets.values()
            if f"_{season}_W{week}_" in data["game_id"]
        ]

        logger.info(f"Found {len(week_bets)} bets in week {week}")
        return week_bets

    def update_closing_line(
        self, recommendation_id: str, closing_line: float
    ) -> Optional[CLVTracking]:
        """
        Update bet with market closing line.

        Automatically calculates CLV (Closing Line Value) based on
        opening line vs. closing line.

        Args:
            recommendation_id: Bet identifier
            closing_line: Market closing spread/line

        Returns:
            Updated CLVTracking record, or None if not found
        """
        bet = self.load_bet(recommendation_id)
        if not bet:
            return None

        if not isinstance(closing_line, (int, float)):
            raise ValueError(f"closing_line must be numeric, got {type(closing_line)}")

        # Update fields
        bet.closing_line = float(closing_line)
        bet.closing_date = datetime.utcnow()

        # Calculate CLV
        clv_points, outcome = CLVAnalyzer.calculate_clv(bet.opening_line, closing_line)
        bet.clv_points = clv_points
        bet.clv_outcome = outcome
        bet.beat_closing_line = clv_points > 0

        # Save updated bet
        self.save_bet(bet)

        logger.info(
            f"Updated closing line for {recommendation_id}: "
            f"{bet.opening_line:+.1f} → {closing_line:+.1f}, "
            f"CLV {clv_points:+.1f} ({outcome.value})"
        )

        return bet

    def update_result(
        self, recommendation_id: str, final_line: float, did_bet_win: bool
    ) -> Optional[CLVTracking]:
        """
        Complete bet record with game result.

        Args:
            recommendation_id: Bet identifier
            final_line: Final game result (spread)
            did_bet_win: Whether bet was successful

        Returns:
            Completed CLVTracking record, or None if not found
        """
        bet = self.load_bet(recommendation_id)
        if not bet:
            return None

        if not isinstance(final_line, (int, float)):
            raise ValueError(f"final_line must be numeric, got {type(final_line)}")

        if not isinstance(did_bet_win, bool):
            raise ValueError(f"did_bet_win must be bool, got {type(did_bet_win)}")

        # Update fields
        bet.final_line = float(final_line)
        bet.did_bet_win = did_bet_win

        # Save completed bet
        self.save_bet(bet)

        result_str = "WIN" if did_bet_win else "LOSS"
        logger.info(
            f"Updated result for {recommendation_id}: {result_str}, "
            f"final line {final_line:+.1f}"
        )

        return bet

    def get_summary(self, week: Optional[int] = None, season: int = 2025) -> CLVSummary:
        """
        Generate summary for period.

        Args:
            week: If provided, summarize only that week
            season: Season year (default 2025)

        Returns:
            CLVSummary with all metrics
        """
        if week:
            bets_list = self.list_by_week(week, season)
            period_str = f"Week {week}"
        else:
            bets_list = self.list_all()
            period_str = f"Season {season}"

        summary = CLVReporter.generate_summary(bets_list)
        logger.info(
            f"Generated summary for {period_str}: {summary.clv_percentage:.1f}% CLV"
        )

        return summary

    def delete_bet(self, recommendation_id: str) -> bool:
        """
        Delete a bet record (use with caution).

        Args:
            recommendation_id: Bet to delete

        Returns:
            True if deleted, False if not found
        """
        bets = self._load_all_bets()

        if recommendation_id not in bets:
            logger.warning(f"Bet {recommendation_id} not found for deletion")
            return False

        deleted_bet = bets.pop(recommendation_id)
        self._save_json(self.bets_json, bets)

        logger.warning(f"Deleted bet {recommendation_id} (CSV history preserved)")
        return True

    def export_to_csv(
        self, filename: str, week: Optional[int] = None, season: int = 2025
    ) -> Path:
        """
        Export bets to CSV file.

        Args:
            filename: Output file path
            week: If provided, export only that week
            season: Season year

        Returns:
            Path to created CSV file
        """
        if week:
            bets = self.list_by_week(week, season)
        else:
            bets = self.list_all()

        output_path = Path(filename)

        with open(output_path, "w", newline="") as f:
            fieldnames = [
                "recommendation_id",
                "game_id",
                "opening_line",
                "closing_line",
                "final_line",
                "clv_points",
                "clv_outcome",
                "did_bet_win",
                "beat_closing_line",
                "edge_percentage",
                "stake_fraction",
                "bankroll",
                "bet_side",
                "bet_type",
                "opening_date",
                "closing_date",
                "created_at",
                "notes",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for bet in bets:
                writer.writerow(
                    {
                        "recommendation_id": bet.recommendation_id,
                        "game_id": bet.game_id,
                        "opening_line": bet.opening_line,
                        "closing_line": bet.closing_line,
                        "final_line": bet.final_line,
                        "clv_points": bet.clv_points,
                        "clv_outcome": bet.clv_outcome.value
                        if bet.clv_outcome
                        else None,
                        "did_bet_win": bet.did_bet_win,
                        "beat_closing_line": bet.beat_closing_line,
                        "edge_percentage": bet.edge_percentage,
                        "stake_fraction": bet.stake_fraction,
                        "bankroll": bet.bankroll,
                        "bet_side": bet.bet_side,
                        "bet_type": bet.bet_type,
                        "opening_date": bet.opening_date.isoformat(),
                        "closing_date": bet.closing_date.isoformat()
                        if bet.closing_date
                        else None,
                        "created_at": bet.created_at.isoformat(),
                        "notes": bet.notes or "",
                    }
                )

        logger.info(f"Exported {len(bets)} bets to {output_path}")
        return output_path

    # ========== Private Methods ==========

    def _load_all_bets(self) -> Dict[str, dict]:
        """Load all bets from JSON file."""
        if not self.bets_json.exists():
            return {}

        try:
            content = self.bets_json.read_text()
            return json.loads(content) if content else {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise ValueError("Corrupted JSON file") from e

    def _save_json(self, path: Path, data: dict) -> None:
        """Save data to JSON file."""
        try:
            path.write_text(json.dumps(data, indent=2, default=str))
        except IOError as e:
            logger.error(f"Failed to write JSON to {path}: {e}")
            raise

    def _append_to_csv(self, bet: CLVTracking) -> None:
        """Append bet record to CSV history (immutable log)."""
        file_exists = self.history_csv.exists()

        fieldnames = [
            "recommendation_id",
            "game_id",
            "opening_line",
            "closing_line",
            "final_line",
            "clv_points",
            "clv_outcome",
            "did_bet_win",
            "beat_closing_line",
            "edge_percentage",
            "stake_fraction",
            "bankroll",
            "bet_side",
            "bet_type",
            "opening_date",
            "closing_date",
            "created_at",
            "updated_at",
            "notes",
        ]

        try:
            with open(self.history_csv, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow(
                    {
                        "recommendation_id": bet.recommendation_id,
                        "game_id": bet.game_id,
                        "opening_line": bet.opening_line,
                        "closing_line": bet.closing_line,
                        "final_line": bet.final_line,
                        "clv_points": bet.clv_points,
                        "clv_outcome": bet.clv_outcome.value
                        if bet.clv_outcome
                        else None,
                        "did_bet_win": bet.did_bet_win,
                        "beat_closing_line": bet.beat_closing_line,
                        "edge_percentage": bet.edge_percentage,
                        "stake_fraction": bet.stake_fraction,
                        "bankroll": bet.bankroll,
                        "bet_side": bet.bet_side,
                        "bet_type": bet.bet_type,
                        "opening_date": bet.opening_date.isoformat(),
                        "closing_date": bet.closing_date.isoformat()
                        if bet.closing_date
                        else None,
                        "created_at": bet.created_at.isoformat(),
                        "updated_at": bet.updated_at.isoformat(),
                        "notes": bet.notes or "",
                    }
                )
        except IOError as e:
            logger.error(f"Failed to write CSV: {e}")
            raise


class CLVReporter:
    """
    Analysis and reporting for CLV tracking.

    Generates summary statistics and assessments based on CLV data.

    Key Metric: **CLV Percentage**
    - Target: >55% of bets beat closing line
    - Meaning: Consistently identifying value before market professionals
    - Correlation: Positive CLV ≈ Long-term profitability
    """

    @staticmethod
    def generate_summary(bets: List[CLVTracking]) -> CLVSummary:
        """
        Generate summary statistics from bet records.

        Args:
            bets: List of CLVTracking records to summarize

        Returns:
            CLVSummary with comprehensive metrics
        """
        if not bets:
            return CLVSummary(
                total_bets=0,
                bets_resolved=0,
                bets_pending=0,
                bets_beating_closing=0,
                clv_percentage=0.0,
                average_clv_points=0.0,
                wins=0,
                losses=0,
                win_rate=0.0,
                total_wagered=0.0,
                gross_winnings=0.0,
                gross_losses=0.0,
                net_profit_loss=0.0,
                roi=0.0,
                clv_roi_correlation="Insufficient data",
                assessment="No bets to analyze",
                tracked_date=date.today(),
            )

        # Filter resolved bets (have both closing and final lines)
        resolved = [b for b in bets if b.is_resolved]
        pending = [b for b in bets if not b.is_resolved]

        # If no resolved bets yet
        if not resolved:
            return CLVSummary(
                total_bets=len(bets),
                bets_resolved=0,
                bets_pending=len(pending),
                bets_beating_closing=0,
                clv_percentage=0.0,
                average_clv_points=0.0,
                wins=0,
                losses=0,
                win_rate=0.0,
                total_wagered=sum(b.bankroll * b.stake_fraction for b in bets),
                gross_winnings=0.0,
                gross_losses=0.0,
                net_profit_loss=0.0,
                roi=0.0,
                clv_roi_correlation="Pending resolution",
                assessment="Waiting for game results",
                tracked_date=date.today(),
            )

        # Calculate CLV metrics
        beating_closing = sum(1 for b in resolved if b.beat_closing_line is True)
        clv_pct = (beating_closing / len(resolved) * 100) if resolved else 0.0
        avg_clv = (
            sum(b.clv_points for b in resolved if b.clv_points is not None)
            / len([b for b in resolved if b.clv_points is not None])
            if any(b.clv_points is not None for b in resolved)
            else 0.0
        )

        # Calculate win/loss metrics
        wins = sum(1 for b in resolved if b.did_bet_win is True)
        losses = sum(1 for b in resolved if b.did_bet_win is False)
        win_rate = (wins / len(resolved) * 100) if resolved else 0.0

        # Calculate profit/loss
        total_wagered = sum(b.bankroll * b.stake_fraction for b in resolved)
        gross_wins = sum(
            b.bankroll * b.stake_fraction for b in resolved if b.did_bet_win is True
        )
        gross_losses = sum(
            b.bankroll * b.stake_fraction for b in resolved if b.did_bet_win is False
        )
        net_profit = gross_wins - gross_losses
        roi = (net_profit / total_wagered * 100) if total_wagered > 0 else 0.0

        # Assessment
        if clv_pct > 55:
            if roi > 0:
                assessment = "STRONG - Beating closing lines and profitable"
            else:
                assessment = "STRONG CLV - Beating lines, variance affecting wins"
        elif clv_pct >= 50:
            assessment = "GOOD - Near break-even CLV, monitor for improvement"
        else:
            assessment = "NEEDS REVIEW - Below 50% CLV, methodology issue"

        # CLV-ROI correlation
        clv_positive = clv_pct > 55
        roi_positive = roi > 0

        if clv_positive and roi_positive:
            clv_roi_corr = "Strong positive - System working as expected"
        elif clv_positive and not roi_positive:
            clv_roi_corr = "CLV good, ROI affected by variance (normal short-term)"
        elif not clv_positive and roi_positive:
            clv_roi_corr = "ROI positive but CLV concerning - luck not skill"
        else:
            clv_roi_corr = "Both negative - Process review needed"

        return CLVSummary(
            total_bets=len(bets),
            bets_resolved=len(resolved),
            bets_pending=len(pending),
            bets_beating_closing=beating_closing,
            clv_percentage=clv_pct,
            average_clv_points=avg_clv,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            total_wagered=total_wagered,
            gross_winnings=gross_wins,
            gross_losses=gross_losses,
            net_profit_loss=net_profit,
            roi=roi,
            clv_roi_correlation=clv_roi_corr,
            assessment=assessment,
            tracked_date=date.today(),
        )


__all__ = ["CLVStorage", "CLVReporter"]
