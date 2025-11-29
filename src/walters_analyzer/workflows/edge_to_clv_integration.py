"""
Edge Detection to CLV Tracking Integration.

Bridges edge detection results with CLV tracking system:
1. Takes detected edges from EdgeDetectionOrchestrator
2. Creates betting records with opening odds/spreads
3. Updates with closing odds when games conclude
4. Calculates CLV and ROI metrics
5. Generates performance reports

This ensures complete pipeline from prediction to performance measurement.
"""

import json
import logging
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from walters_analyzer.valuation.edge_detection_orchestrator import BettingEdge

logger = logging.getLogger(__name__)


@dataclass
class BettingRecord:
    """Single betting record for CLV tracking."""

    bet_id: str  # Unique identifier
    matchup: str  # "Away @ Home"
    league: str  # NFL or NCAAF
    week: int  # Week number
    game_date: str  # ISO format date
    bet_type: str  # "spread", "moneyline", "total"
    pick: str  # Our selection (team or O/U)
    opening_odds: float  # Our odds at time of edge detection
    opening_spread: float  # Opening spread/line
    closing_odds: Optional[float] = None
    closing_spread: Optional[float] = None
    result: Optional[str] = None  # "WIN", "LOSS", "PUSH"
    confidence: float = 0.0  # Our confidence 0-100
    edge_points: float = 0.0  # Edge in points
    kelly_fraction: float = 0.0  # Recommended Kelly %
    units_bet: float = 1.0  # Units wagered
    clv: Optional[float] = None  # Closing Line Value
    roi: Optional[float] = None  # Return on Investment %
    notes: str = ""  # Additional notes
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def calculate_clv(self) -> None:
        """Calculate CLV if closing odds available."""
        if self.closing_odds is not None and self.opening_odds is not None:
            # CLV = (Opening Odds - Closing Odds) / 100
            self.clv = (self.opening_odds - self.closing_odds) / 100.0
            self.updated_at = datetime.now().isoformat()

    def calculate_roi(self, win_amount: Optional[float] = None) -> None:
        """
        Calculate ROI if result available.

        Args:
            win_amount: Dollar amount won (if not standard -110/-110)
        """
        if self.result is None:
            return

        if self.result == "WIN":
            if win_amount:
                roi = (win_amount / self.units_bet) * 100
            else:
                # Standard -110/-110 odds: win $91 per $100
                roi = ((self.units_bet * 0.909) / self.units_bet) * 100
            self.roi = roi
        elif self.result == "LOSS":
            self.roi = -100.0  # Lost full bet
        elif self.result == "PUSH":
            self.roi = 0.0  # Break even

        self.updated_at = datetime.now().isoformat()


@dataclass
class EdgeToCLVResult:
    """Result of edge-to-CLV conversion."""

    records_created: int
    total_edge_value: float
    average_edge: float
    records: List[BettingRecord] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class EdgeToCLVIntegrator:
    """Converts detected edges to CLV betting records."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize integrator.

        Args:
            project_root: Root project directory
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.clv_dir = self.project_root / "output" / "clv_tracking"
        self.clv_dir.mkdir(parents=True, exist_ok=True)

    def convert_edges_to_records(
        self,
        edges: List[BettingEdge],
        league: str,
        week: int,
        game_date: str,
    ) -> EdgeToCLVResult:
        """
        Convert detected edges to betting records.

        Args:
            edges: List of BettingEdge objects from EdgeDetectionOrchestrator
            league: "nfl" or "ncaaf"
            week: Week number
            game_date: Game date (YYYY-MM-DD)

        Returns:
            EdgeToCLVResult with created records
        """
        records = []
        total_edge = 0.0
        errors = []

        logger.info(f"Converting {len(edges)} edges to CLV records...")

        for edge in edges:
            try:
                # Create record from edge
                record = self._edge_to_record(edge, league, week, game_date)
                records.append(record)
                total_edge += edge.edge_points

                logger.debug(
                    f"Created record: {record.matchup} ({record.edge_points:.1f}pt edge)"
                )

            except Exception as e:
                error_msg = f"Failed to convert edge for {edge.matchup}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Calculate statistics
        avg_edge = total_edge / len(records) if records else 0.0

        result = EdgeToCLVResult(
            records_created=len(records),
            total_edge_value=total_edge,
            average_edge=avg_edge,
            records=records,
            errors=errors,
        )

        logger.info(
            f"[OK] Converted {len(records)} edges to CLV records "
            f"(total: {total_edge:.1f}pt, avg: {avg_edge:.1f}pt)"
        )

        return result

    def _edge_to_record(
        self,
        edge: BettingEdge,
        league: str,
        week: int,
        game_date: str,
    ) -> BettingRecord:
        """
        Convert single BettingEdge to BettingRecord.

        Args:
            edge: BettingEdge object
            league: "nfl" or "ncaaf"
            week: Week number
            game_date: Game date

        Returns:
            BettingRecord
        """
        # Create unique bet ID
        bet_id = f"{league}_{week}_{edge.matchup.replace(' @ ', '_').replace(' ', '_')}"

        # Extract pick from recommended_bet
        pick = edge.recommended_bet.upper()  # "HOME" or "AWAY" or "OVER"/"UNDER"

        # Parse matchup
        parts = edge.matchup.split(" @ ")
        if len(parts) == 2:
            away, home = parts
        else:
            away = "Unknown"
            home = "Unknown"

        # Determine our odds (assume -110 standard)
        opening_odds = -110.0

        # Spread from market_spread
        opening_spread = edge.market_spread if hasattr(edge, "market_spread") else 0.0

        record = BettingRecord(
            bet_id=bet_id,
            matchup=edge.matchup,
            league=league.upper(),
            week=week,
            game_date=game_date,
            bet_type="spread",  # Default to spread
            pick=pick,
            opening_odds=opening_odds,
            opening_spread=opening_spread,
            confidence=edge.confidence_score
            if hasattr(edge, "confidence_score")
            else 0.0,
            edge_points=edge.edge_points,
            kelly_fraction=self._calculate_kelly(edge.edge_points),
            units_bet=self._calculate_units(edge.edge_points),
            notes=f"Power ratings: Away {edge.away_rating:.1f}, Home {edge.home_rating:.1f}",
        )

        return record

    def _calculate_kelly(self, edge_points: float) -> float:
        """
        Calculate Kelly fraction based on edge size.

        Billy Walters methodology:
        - 7+ points: 5% Kelly
        - 4-7 points: 3% Kelly
        - 2-4 points: 2% Kelly
        - 1-2 points: 1% Kelly
        """
        if edge_points >= 7.0:
            return 0.05
        elif edge_points >= 4.0:
            return 0.03
        elif edge_points >= 2.0:
            return 0.02
        elif edge_points >= 1.0:
            return 0.01
        else:
            return 0.0

    def _calculate_units(self, edge_points: float) -> float:
        """
        Calculate units to bet based on edge.

        Standard: 0.5 to 2 units depending on edge strength.
        """
        kelly = self._calculate_kelly(edge_points)
        if kelly <= 0:
            return 0.0
        return min(kelly * 2, 2.0)  # Cap at 2 units

    def save_records(
        self,
        records: List[BettingRecord],
        league: str,
        week: int,
    ) -> Path:
        """
        Save records to file.

        Args:
            records: List of BettingRecord objects
            league: "nfl" or "ncaaf"
            week: Week number

        Returns:
            Path to saved file
        """
        filename = f"{league}_week_{week}_betting_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.clv_dir / filename

        with open(filepath, "w") as f:
            json.dump(
                [asdict(r) for r in records],
                f,
                indent=2,
                default=str,
            )

        logger.info(f"Saved {len(records)} records to {filepath}")
        return filepath

    def load_records(self, filepath: Path) -> List[BettingRecord]:
        """Load records from file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        records = []
        for item in data:
            record = BettingRecord(**item)
            records.append(record)

        return records

    def update_with_closing_odds(
        self,
        records: List[BettingRecord],
        closing_odds_map: Dict[str, float],
        closing_spread_map: Dict[str, float],
    ) -> List[BettingRecord]:
        """
        Update records with closing odds and spreads.

        Args:
            records: List of BettingRecord objects
            closing_odds_map: Dict mapping matchup to closing odds
            closing_spread_map: Dict mapping matchup to closing spread

        Returns:
            Updated records with CLV calculated
        """
        for record in records:
            if record.matchup in closing_odds_map:
                record.closing_odds = closing_odds_map[record.matchup]
                record.calculate_clv()

            if record.matchup in closing_spread_map:
                record.closing_spread = closing_spread_map[record.matchup]

            record.updated_at = datetime.now().isoformat()

        return records

    def generate_clv_report(self, records: List[BettingRecord]) -> Dict:
        """Generate CLV performance report."""
        if not records:
            return {
                "total_records": 0,
                "records_with_clv": 0,
                "average_clv": None,
                "positive_clv_count": 0,
                "positive_clv_rate": 0.0,
            }

        records_with_clv = [r for r in records if r.clv is not None]
        clv_values = [r.clv for r in records_with_clv]

        positive_clv = sum(1 for clv in clv_values if clv > 0)
        average_clv = sum(clv_values) / len(clv_values) if clv_values else None

        return {
            "total_records": len(records),
            "records_with_clv": len(records_with_clv),
            "average_clv": average_clv,
            "positive_clv_count": positive_clv,
            "positive_clv_rate": (positive_clv / len(records_with_clv) * 100)
            if records_with_clv
            else 0.0,
            "min_clv": min(clv_values) if clv_values else None,
            "max_clv": max(clv_values) if clv_values else None,
        }


def main():
    """Example usage."""
    from walters_analyzer.valuation.edge_detection_orchestrator import (
        EdgeDetectionOrchestrator,
        BettingEdge,
    )

    # Create test edge
    test_edge = BettingEdge(
        matchup="Test @ Example",
        week=13,
        edge_points=5.5,
        edge_strength="strong",
        predicted_spread=-3.0,
        market_spread=2.5,
        recommended_bet="home",
        confidence_score=80.0,
        away_team="Test",
        home_team="Example",
        away_rating=85.0,
        home_rating=90.5,
    )

    # Initialize integrator
    integrator = EdgeToCLVIntegrator()

    # Convert edges to records
    result = integrator.convert_edges_to_records(
        edges=[test_edge],
        league="nfl",
        week=13,
        game_date="2025-11-28",
    )

    print(f"Created {result.records_created} records")
    print(f"Total edge value: {result.total_edge_value:.1f}pt")

    # Save records
    filepath = integrator.save_records(result.records, "nfl", 13)
    print(f"Saved to {filepath}")

    # Generate report
    report = integrator.generate_clv_report(result.records)
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
