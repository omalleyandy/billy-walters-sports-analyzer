"""
Sharp Money Integration Module.

Implements Billy Walters' core principle: "Follow the money, not the tickets."

Combines:
1. Power rating-based edges (our proprietary analysis)
2. Action Network sharp money signals (professional betting divergence)
3. Dynamic adjustments based on signal strength and agreement

Key Concept:
- Tickets % = volume of bets placed (public action)
- Money % = dollar amount wagered (professional/sharp action)
- Divergence = Money% - Tickets% indicates which side the pros are on

Integration Logic:
- Sharp signal confirmation: Boosts edge confidence by 10-20%
- Sharp signal contradiction: Reduces edge confidence by 10-20%
- No signal: Leaves edge unchanged
- Strong signals (15%+ divergence): Highest priority

Success Metric: Track ROI by edge strength + sharp confirmation combination.
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from walters_analyzer.valuation.edge_detection_orchestrator import BettingEdge

logger = logging.getLogger(__name__)


class SignalStrength(str, Enum):
    """Sharp money signal strength."""

    VERY_STRONG = "very_strong"  # 15%+ divergence
    STRONG = "strong"  # 10-14% divergence
    MODERATE = "moderate"  # 5-9% divergence
    WEAK = "weak"  # <5% divergence
    NONE = "none"  # No clear signal


class SignalAgreement(str, Enum):
    """Agreement between power rating and sharp money."""

    CONFIRMATION = "confirmation"  # Both agree on same side
    CONTRADICTION = "contradiction"  # Disagree on side
    NONE = "none"  # No signal available


@dataclass
class SharpMoneySignal:
    """Sharp money signal from Action Network."""

    matchup: str  # "Away @ Home"
    league: str  # NFL or NCAAF
    public_tickets: float  # Public bet % (0-100)
    public_money: float  # Professional/sharp money % (0-100)
    divergence: float  # abs(money % - tickets %)
    signal_strength: SignalStrength
    recommended_side: Optional[str] = None  # "away", "home", "over", "under"
    source: str = "action_network"
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AdjustedEdge:
    """Edge after sharp money adjustment."""

    original_edge: BettingEdge
    sharp_signal: Optional[SharpMoneySignal]
    signal_agreement: SignalAgreement
    confidence_adjustment: float  # % adjustment (-20 to +20)
    adjusted_confidence: float  # Original confidence after adjustment
    adjusted_edge_points: Optional[float] = None  # Edge adjusted by sharp signal
    reasoning: str = ""


class SharpMoneyIntegrator:
    """Integrates sharp money signals with power rating edges."""

    # Thresholds for each league (due to market liquidity differences)
    NFL_THRESHOLDS = {
        "very_strong": 15.0,  # 15%+ divergence
        "strong": 10.0,  # 10-14%
        "moderate": 5.0,  # 5-9%
    }

    NCAAF_THRESHOLDS = {
        "very_strong": 40.0,  # 40%+ divergence (less efficient market)
        "strong": 30.0,  # 30-39%
        "moderate": 20.0,  # 20-29%
    }

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize integrator."""
        self.project_root = project_root or Path(__file__).parent.parent.parent.parent
        self.action_network_dir = self.project_root / "output" / "action_network"
        self.thresholds = None

    def load_sharp_signals(
        self, league: str, week: Optional[int] = None
    ) -> Dict[str, SharpMoneySignal]:
        """
        Load sharp money signals from Action Network data.

        Args:
            league: "nfl" or "ncaaf"
            week: Optional week number for filtering

        Returns:
            Dict mapping matchup to SharpMoneySignal
        """
        signals = {}

        # Set thresholds based on league
        self.thresholds = (
            self.NFL_THRESHOLDS if league.lower() == "nfl" else self.NCAAF_THRESHOLDS
        )

        # Try to load from latest Action Network file
        latest_file = self._find_latest_action_network_file(league)
        if not latest_file:
            logger.warning(f"No Action Network data found for {league}")
            return signals

        try:
            with open(latest_file, "r") as f:
                data = json.load(f)

            # Extract games from Action Network format
            games = data.get("games", [])
            for game in games:
                signal = self._parse_action_network_game(game, league)
                if signal:
                    signals[signal.matchup] = signal

            logger.info(f"Loaded {len(signals)} sharp money signals from {league}")

        except Exception as e:
            logger.error(f"Failed to load sharp signals: {str(e)}")

        return signals

    def integrate_with_edges(
        self,
        edges: List[BettingEdge],
        sharp_signals: Dict[str, SharpMoneySignal],
        league: str,
    ) -> List[AdjustedEdge]:
        """
        Integrate sharp money signals with detected edges.

        Args:
            edges: List of detected edges
            sharp_signals: Dict of sharp money signals
            league: "nfl" or "ncaaf"

        Returns:
            List of AdjustedEdge with confidence adjustments
        """
        self.thresholds = (
            self.NFL_THRESHOLDS if league.lower() == "nfl" else self.NCAAF_THRESHOLDS
        )

        adjusted = []

        for edge in edges:
            signal = sharp_signals.get(edge.matchup)
            adjustment = self._calculate_adjustment(edge, signal, league)
            adjusted.append(adjustment)

        return adjusted

    def _calculate_adjustment(
        self,
        edge: BettingEdge,
        signal: Optional[SharpMoneySignal],
        league: str,
    ) -> AdjustedEdge:
        """
        Calculate confidence adjustment based on sharp signal agreement.

        Args:
            edge: Detected edge
            signal: Sharp money signal (if available)
            league: "nfl" or "ncaaf"

        Returns:
            AdjustedEdge with calculated adjustments
        """
        if not signal:
            return AdjustedEdge(
                original_edge=edge,
                sharp_signal=None,
                signal_agreement=SignalAgreement.NONE,
                confidence_adjustment=0.0,
                adjusted_confidence=edge.confidence_score,
                reasoning="No sharp money signal available",
            )

        # Check if signal agrees with our edge
        agreement = self._check_agreement(edge, signal)
        logger.debug(
            f"{edge.matchup}: Edge recommends {edge.recommended_bet}, "
            f"Sharp signals {signal.recommended_side}, "
            f"Agreement: {agreement.value}"
        )

        # Calculate adjustment based on agreement and strength
        if agreement == SignalAgreement.CONFIRMATION:
            # Sharp confirms our edge - boost confidence
            adjustment = self._get_adjustment_for_strength(signal.signal_strength, +1)
            reasoning = (
                f"Sharp signal CONFIRMS edge ({signal.divergence:.1f}% divergence)"
            )
        elif agreement == SignalAgreement.CONTRADICTION:
            # Sharp contradicts our edge - reduce confidence
            adjustment = self._get_adjustment_for_strength(signal.signal_strength, -1)
            reasoning = (
                f"Sharp signal CONTRADICTS edge ({signal.divergence:.1f}% divergence)"
            )
        else:
            adjustment = 0.0
            reasoning = "Edge and sharp signal target different outcomes"

        adjusted_confidence = max(0.0, min(100.0, edge.confidence_score + adjustment))

        return AdjustedEdge(
            original_edge=edge,
            sharp_signal=signal,
            signal_agreement=agreement,
            confidence_adjustment=adjustment,
            adjusted_confidence=adjusted_confidence,
            adjusted_edge_points=self._adjust_edge_points(edge.edge_points, adjustment),
            reasoning=reasoning,
        )

    def _check_agreement(
        self, edge: BettingEdge, signal: SharpMoneySignal
    ) -> SignalAgreement:
        """Check if edge and signal recommend the same side."""
        edge_side = edge.recommended_bet.lower()  # "home", "away", etc.
        signal_side = (
            signal.recommended_side.lower() if signal.recommended_side else None
        )

        if not signal_side:
            return SignalAgreement.NONE

        # Map edge recommendation to side
        if edge_side in ["home", "over"]:
            edge_targets_home = True
        elif edge_side in ["away", "under"]:
            edge_targets_home = False
        else:
            return SignalAgreement.NONE

        # Map signal to side
        if signal_side in ["home", "over"]:
            signal_targets_home = True
        elif signal_side in ["away", "under"]:
            signal_targets_home = False
        else:
            return SignalAgreement.NONE

        # Compare
        if edge_targets_home == signal_targets_home:
            return SignalAgreement.CONFIRMATION
        else:
            return SignalAgreement.CONTRADICTION

    def _get_adjustment_for_strength(
        self, strength: SignalStrength, direction: int
    ) -> float:
        """Get confidence adjustment based on signal strength."""
        # direction: +1 for confirmation, -1 for contradiction
        adjustments = {
            SignalStrength.VERY_STRONG: 20.0,
            SignalStrength.STRONG: 15.0,
            SignalStrength.MODERATE: 10.0,
            SignalStrength.WEAK: 5.0,
            SignalStrength.NONE: 0.0,
        }
        return adjustments.get(strength, 0.0) * direction

    def _adjust_edge_points(self, original_edge: float, adjustment: float) -> float:
        """Adjust edge points based on confidence adjustment."""
        # Scale: 10% confidence boost ~= 0.5pt edge boost
        return original_edge + (adjustment / 20.0)

    def _find_latest_action_network_file(self, league: str) -> Optional[Path]:
        """Find latest Action Network data file."""
        if not self.action_network_dir.exists():
            return None

        # Look for latest odds file
        pattern = f"*{league.lower()}*odds*.json"
        files = list(self.action_network_dir.glob(pattern))

        if not files:
            # Also try other naming patterns
            files = list(self.action_network_dir.glob(f"*{league.lower()}*.json"))

        if files:
            # Return most recent file
            return max(files, key=lambda p: p.stat().st_mtime)

        return None

    def _parse_action_network_game(
        self, game_data: Dict, league: str
    ) -> Optional[SharpMoneySignal]:
        """Parse game data from Action Network API response."""
        try:
            matchup = game_data.get("matchup")
            if not matchup:
                return None

            # Extract betting percentages
            public_tickets = float(game_data.get("public_tickets", 0))
            public_money = float(game_data.get("public_money", 0))

            # Calculate divergence
            divergence = abs(public_money - public_tickets)

            # Determine signal strength
            thresholds = (
                self.NFL_THRESHOLDS
                if league.lower() == "nfl"
                else self.NCAAF_THRESHOLDS
            )

            if divergence >= thresholds["very_strong"]:
                strength = SignalStrength.VERY_STRONG
            elif divergence >= thresholds["strong"]:
                strength = SignalStrength.STRONG
            elif divergence >= thresholds["moderate"]:
                strength = SignalStrength.MODERATE
            elif divergence > 0:
                strength = SignalStrength.WEAK
            else:
                strength = SignalStrength.NONE

            # Determine which side sharp is on
            if public_money > public_tickets:
                # Sharp is betting the over/favorite/home
                recommended_side = game_data.get("sharp_side", "home")
            else:
                # Sharp is betting the under/underdog/away
                recommended_side = game_data.get("sharp_side", "away")

            return SharpMoneySignal(
                matchup=matchup,
                league=league.upper(),
                public_tickets=public_tickets,
                public_money=public_money,
                divergence=divergence,
                signal_strength=strength,
                recommended_side=recommended_side,
            )

        except Exception as e:
            logger.debug(f"Failed to parse game: {str(e)}")
            return None

    def generate_sharp_money_report(self, adjusted_edges: List[AdjustedEdge]) -> Dict:
        """Generate report on sharp money signal integration."""
        with_signals = [a for a in adjusted_edges if a.sharp_signal is not None]
        confirmed = [
            a
            for a in with_signals
            if a.signal_agreement == SignalAgreement.CONFIRMATION
        ]
        contradicted = [
            a
            for a in with_signals
            if a.signal_agreement == SignalAgreement.CONTRADICTION
        ]

        avg_adjustment = (
            sum(a.confidence_adjustment for a in with_signals) / len(with_signals)
            if with_signals
            else 0.0
        )

        return {
            "total_edges": len(adjusted_edges),
            "edges_with_signal": len(with_signals),
            "confirmed": len(confirmed),
            "contradicted": len(contradicted),
            "no_signal": len(adjusted_edges) - len(with_signals),
            "average_confidence_adjustment": avg_adjustment,
            "confirmation_rate": (
                len(confirmed) / len(with_signals) * 100 if with_signals else 0.0
            ),
        }


def main():
    """Example usage."""
    # Create example edges and signals
    from walters_analyzer.valuation.edge_detection_orchestrator import BettingEdge

    edge = BettingEdge(
        matchup="Kansas City @ Buffalo",
        week=13,
        edge_points=8.5,
        edge_strength="very_strong",
        predicted_spread=-2.5,
        market_spread=6.0,
        recommended_bet="away",
        confidence_score=95.0,
        away_team="Kansas City",
        home_team="Buffalo",
        away_rating=88.5,
        home_rating=81.0,
    )

    signal = SharpMoneySignal(
        matchup="Kansas City @ Buffalo",
        league="NFL",
        public_tickets=45.0,
        public_money=60.0,
        divergence=15.0,
        signal_strength=SignalStrength.VERY_STRONG,
        recommended_side="away",
    )

    integrator = SharpMoneyIntegrator()
    signals = {"Kansas City @ Buffalo": signal}

    adjusted = integrator.integrate_with_edges([edge], signals, "nfl")
    print(f"Original confidence: {edge.confidence_score}%")
    print(f"Adjusted confidence: {adjusted[0].adjusted_confidence}%")
    print(f"Agreement: {adjusted[0].signal_agreement.value}")
    print(f"Adjustment: {adjusted[0].confidence_adjustment:+.1f}%")


if __name__ == "__main__":
    main()
