"""High-level Billy Walters analysis engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from walters_analyzer.valuation.core import BillyWaltersValuation

from .bankroll import BankrollManager
from .config import AnalyzerConfig
from .models import (
    BetRecommendation,
    GameAnalysis,
    GameInput,
    InjuryBreakdown,
    KeyNumberAlert,
)
from .point_analyzer import PointAnalyzer


class BillyWaltersAnalyzer:
    """Turns raw injury + market data into actionable recommendations."""

    def __init__(
        self,
        config: Optional[AnalyzerConfig] = None,
        valuation: Optional[BillyWaltersValuation] = None,
        bankroll: Optional[BankrollManager] = None,
        point_analyzer: Optional[PointAnalyzer] = None,
    ) -> None:
        self.config = config or AnalyzerConfig.from_settings()
        self.valuation = valuation or BillyWaltersValuation()
        self.bankroll = bankroll or BankrollManager(
            initial_bankroll=self.config.bankroll,
            max_risk_pct=self.config.max_bet_pct,
            min_bet_pct=self.config.min_bet_pct,
            fractional_kelly=self.config.fractional_kelly,
        )
        self.point_analyzer = point_analyzer or PointAnalyzer(self.config.key_numbers)

    def analyze(self, matchup: GameInput) -> GameAnalysis:
        """Analyze a single matchup."""
        home_report = self._build_injury_report(matchup.home_team.name, matchup.home_team.injuries)
        away_report = self._build_injury_report(matchup.away_team.name, matchup.away_team.injuries)

        predicted_spread = self.valuation.calculate_predicted_spread(
            matchup.home_team.name,
            matchup.away_team.name,
            list(matchup.home_team.injuries),
            list(matchup.away_team.injuries),
        )
        if predicted_spread is None:
            predicted_spread = away_report.total_points - home_report.total_points

        market_spread = matchup.odds.spread.home_spread if matchup.odds else 0.0
        edge = round(predicted_spread - market_spread, 1)
        injury_advantage = round(away_report.total_points - home_report.total_points, 1)

        win_probability = self._edge_to_probability(edge)
        odds_price = self._pick_price(edge, matchup)
        stake_pct = self.bankroll.recommend_pct(win_probability, odds_price)
        conviction = self._confidence_label(abs(edge))

        key_alerts = self.point_analyzer.evaluate(predicted_spread, market_spread)
        notes = [
            f"Net injury advantage: {injury_advantage:+.1f} pts",
            f"Predicted spread {predicted_spread:+.1f} vs market {market_spread:+.1f}",
        ] + [alert.description for alert in key_alerts]

        team = matchup.home_team.name if edge >= 0 else matchup.away_team.name
        recommendation = BetRecommendation(
            bet_type="spread",
            team=team,
            edge=edge,
            win_probability=win_probability,
            stake_pct=stake_pct,
            conviction=conviction,
            notes=notes,
        )

        if stake_pct > 0:
            self.bankroll.register_bet(stake_pct, odds_price, win_probability)

        return GameAnalysis(
            matchup=matchup,
            predicted_spread=predicted_spread,
            predicted_total=None,
            injury_advantage=injury_advantage,
            market_spread=market_spread,
            edge=edge,
            confidence=conviction,
            home_report=home_report,
            away_report=away_report,
            key_number_alerts=key_alerts,
            recommendation=recommendation,
        )

    def analyze_many(self, matchups: Iterable[GameInput]) -> List[GameAnalysis]:
        """Convenience helper for batch workflows."""
        return [self.analyze(matchup) for matchup in matchups]

    def _build_injury_report(self, team_name: str, injuries) -> InjuryBreakdown:
        analysis = self.valuation.calculate_team_impact(list(injuries), team_name)
        critical = [inj["name"] for inj in analysis.get("critical_injuries", [])]
        detailed = [
            f"{inj['name']} ({inj['position']}): -{inj['impact']:.1f} pts"
            for inj in analysis.get("detailed_breakdown", [])[:5]
        ]
        return InjuryBreakdown(
            team=team_name,
            total_points=round(analysis.get("total_impact", 0.0), 1),
            critical_players=critical,
            detailed_notes=detailed,
            position_group_crises=analysis.get("position_group_crises", []),
        )

    def _edge_to_probability(self, edge: float) -> float:
        abs_edge = abs(edge)
        if abs_edge >= 3.0:
            base = 0.64
        elif abs_edge >= 2.0:
            base = 0.58
        elif abs_edge >= 1.0:
            base = 0.54
        else:
            base = 0.52
        return round(base, 3)

    def _pick_price(self, edge: float, matchup: GameInput) -> int:
        if matchup.odds:
            if edge >= 0:
                return matchup.odds.spread.home_price
            return matchup.odds.spread.away_price
        return -110

    def _confidence_label(self, abs_edge: float) -> str:
        for threshold, label in self.config.confidence_buckets:
            if abs_edge >= threshold:
                return label
        return "No Play"
