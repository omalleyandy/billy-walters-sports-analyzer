"""
E-Factor Calibration & Impact Monitoring

Tracks E-Factor impact on edge predictions and actual results.
Calibrates impact weights based on historical performance.

Responsibilities:
1. Calculate expected vs actual impact (calibration)
2. Track source quality and confidence decay
3. Monitor ROI contribution by E-Factor type
4. Adjust weights for future predictions
5. Provide calibration reports and recommendations

Usage:
    calibrator = EFactorCalibrator(db_path="output/calibration.db")
    await calibrator.initialize()

    # Record prediction with E-Factors
    await calibrator.record_prediction(
        game_id="KC@DAL_W13",
        predicted_edge=8.5,
        efactor_adjustment=-3.0,
        efactor_sources=["injury_qb"],
        actual_outcome="LOSS"
    )

    # Analyze calibration
    report = await calibrator.get_calibration_report()
    print(report)

    await calibrator.close()
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CalibrationRecord:
    """Single prediction with outcome for calibration."""

    game_id: str
    week: int
    timestamp: datetime
    team: str
    league: str

    # Prediction details
    predicted_edge_pct: float
    efactor_adjustment: float
    efactor_sources: List[str]  # ["injury_qb", "coaching", "transaction"]
    sharp_alignment: str  # "CONFIRMS", "CONTRADICTS", "NEUTRAL"
    confidence_level: str  # "HIGH", "MEDIUM", "LOW", "NONE"

    # Actual outcome
    actual_result: Optional[str] = None  # "WIN", "LOSS", "PUSH"
    actual_margin: Optional[float] = None
    closing_line_value: Optional[float] = None

    # Analysis
    edge_accuracy: Optional[float] = None
    ats_result: Optional[bool] = None
    roi_contribution: Optional[float] = None


@dataclass
class CalibrationMetrics:
    """Aggregate calibration metrics."""

    total_predictions: int = 0
    total_outcomes: int = 0

    # Edge accuracy
    avg_predicted_edge: float = 0.0
    avg_actual_margin: float = 0.0
    edge_rmse: float = 0.0  # Root mean squared error

    # Betting performance
    ats_win_rate: float = 0.0
    ats_total_bets: int = 0
    ats_wins: int = 0
    ats_losses: int = 0
    ats_pushes: int = 0

    # ROI tracking
    total_roi: float = 0.0
    roi_per_bet_pct: float = 0.0

    # E-Factor specific
    efactor_impact_avg: float = 0.0
    efactor_impact_max: float = 0.0
    efactor_impact_min: float = 0.0
    efactor_accuracy: float = 0.0

    # Source breakdown
    best_source: Optional[str] = None
    worst_source: Optional[str] = None
    source_scores: Dict[str, float] = None  # type: ignore

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            k: v.isoformat() if isinstance(v, datetime) else v
            for k, v in asdict(self).items()
        }


class EFactorCalibrator:
    """
    Calibrates and monitors E-Factor impact.

    Uses SQLite for persistence and provides analysis methods
    for understanding E-Factor effectiveness.
    """

    def __init__(self, db_path: str = "output/efactor_calibration.db"):
        """Initialize calibrator."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None

    async def initialize(self) -> None:
        """Initialize database and create tables."""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Create records table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS calibration_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT UNIQUE NOT NULL,
                week INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                team TEXT NOT NULL,
                league TEXT NOT NULL,

                predicted_edge_pct REAL NOT NULL,
                efactor_adjustment REAL NOT NULL,
                efactor_sources TEXT NOT NULL,
                sharp_alignment TEXT NOT NULL,
                confidence_level TEXT NOT NULL,

                actual_result TEXT,
                actual_margin REAL,
                closing_line_value REAL,

                edge_accuracy REAL,
                ats_result INTEGER,
                roi_contribution REAL,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create calibration metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS calibration_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                league TEXT NOT NULL,
                filter_type TEXT DEFAULT 'all',

                total_predictions INTEGER,
                total_outcomes INTEGER,
                avg_predicted_edge REAL,
                avg_actual_margin REAL,
                edge_rmse REAL,
                ats_win_rate REAL,
                ats_total_bets INTEGER,
                ats_wins INTEGER,
                ats_losses INTEGER,
                ats_pushes INTEGER,
                total_roi REAL,
                roi_per_bet_pct REAL,
                efactor_impact_avg REAL,
                best_source TEXT,
                worst_source TEXT,
                source_scores TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create index for faster queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_game_id ON calibration_records(game_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_week ON calibration_records(week)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_efactor_sources ON calibration_records(efactor_sources)"
        )

        self.conn.commit()
        logger.info("EFactorCalibrator initialized")

    async def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("EFactorCalibrator closed")

    async def record_prediction(
        self,
        game_id: str,
        week: int,
        team: str,
        league: str,
        predicted_edge_pct: float,
        efactor_adjustment: float,
        efactor_sources: List[str],
        sharp_alignment: str = "NEUTRAL",
        confidence_level: str = "NONE",
    ) -> None:
        """Record a prediction for later calibration."""
        record = CalibrationRecord(
            game_id=game_id,
            week=week,
            timestamp=datetime.now(),
            team=team,
            league=league,
            predicted_edge_pct=predicted_edge_pct,
            efactor_adjustment=efactor_adjustment,
            efactor_sources=efactor_sources,
            sharp_alignment=sharp_alignment,
            confidence_level=confidence_level,
        )

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO calibration_records (
                game_id, week, timestamp, team, league,
                predicted_edge_pct, efactor_adjustment, efactor_sources,
                sharp_alignment, confidence_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.game_id,
                record.week,
                record.timestamp.isoformat(),
                record.team,
                record.league,
                record.predicted_edge_pct,
                record.efactor_adjustment,
                json.dumps(record.efactor_sources),
                record.sharp_alignment,
                record.confidence_level,
            ),
        )
        self.conn.commit()
        logger.debug(f"Recorded prediction for {game_id}")

    async def record_outcome(
        self,
        game_id: str,
        actual_result: str,
        actual_margin: float,
        closing_line_value: float = 0.0,
    ) -> None:
        """Record actual outcome for a game."""
        cursor = self.conn.cursor()

        # Get the prediction
        cursor.execute(
            "SELECT predicted_edge_pct FROM calibration_records WHERE game_id = ?",
            (game_id,),
        )
        row = cursor.fetchone()
        if not row:
            logger.warning(f"No prediction found for {game_id}")
            return

        predicted_edge = row[0]

        # Calculate metrics
        edge_accuracy = abs(predicted_edge - actual_margin)
        ats_result = 1 if actual_margin >= 0 else 0
        roi_contribution = closing_line_value

        # Update record
        cursor.execute(
            """
            UPDATE calibration_records SET
                actual_result = ?,
                actual_margin = ?,
                closing_line_value = ?,
                edge_accuracy = ?,
                ats_result = ?,
                roi_contribution = ?
            WHERE game_id = ?
        """,
            (
                actual_result,
                actual_margin,
                closing_line_value,
                edge_accuracy,
                ats_result,
                roi_contribution,
                game_id,
            ),
        )
        self.conn.commit()
        logger.debug(f"Recorded outcome for {game_id}")

    async def get_calibration_report(
        self, league: str = "nfl", weeks: Optional[int] = None
    ) -> CalibrationMetrics:
        """
        Get calibration metrics.

        Args:
            league: Filter by league ("nfl" or "ncaaf")
            weeks: Only include last N weeks (None = all)

        Returns:
            CalibrationMetrics object
        """
        cursor = self.conn.cursor()

        # Build query
        where_clause = "WHERE league = ?"
        params: List[Any] = [league]

        if weeks:
            cursor.execute(
                "SELECT MAX(week) FROM calibration_records WHERE league = ?", [league]
            )
            max_week = cursor.fetchone()[0]
            if max_week:
                min_week = max_week - weeks + 1
                where_clause += f" AND week >= {min_week}"

        # Get predictions and outcomes
        cursor.execute(
            f"""
            SELECT COUNT(*) FROM calibration_records {where_clause}
        """,
            params,
        )
        total_predictions = cursor.fetchone()[0]

        cursor.execute(
            f"""
            SELECT COUNT(*) FROM calibration_records {where_clause}
            AND actual_result IS NOT NULL
        """,
            params,
        )
        total_outcomes = cursor.fetchone()[0]

        # Edge accuracy metrics
        cursor.execute(
            f"""
            SELECT AVG(predicted_edge_pct), AVG(actual_margin), AVG(edge_accuracy * edge_accuracy)
            FROM calibration_records {where_clause}
            AND actual_result IS NOT NULL
        """,
            params,
        )
        row = cursor.fetchone()
        avg_predicted_edge = row[0] or 0.0
        avg_actual_margin = row[1] or 0.0
        edge_rmse = (row[2] or 0.0) ** 0.5

        # ATS performance
        cursor.execute(
            f"""
            SELECT
                COUNT(*),
                SUM(CASE WHEN ats_result = 1 THEN 1 ELSE 0 END),
                SUM(CASE WHEN ats_result = 0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN actual_margin = 0 THEN 1 ELSE 0 END)
            FROM calibration_records {where_clause}
            AND actual_result IS NOT NULL
        """,
            params,
        )
        row = cursor.fetchone()
        ats_total = row[0] or 0
        ats_wins = row[1] or 0
        ats_losses = row[2] or 0
        ats_pushes = row[3] or 0
        ats_win_rate = (
            (ats_wins / (ats_total - ats_pushes) * 100)
            if (ats_total - ats_pushes) > 0
            else 0.0
        )

        # ROI
        cursor.execute(
            f"""
            SELECT SUM(roi_contribution)
            FROM calibration_records {where_clause}
            AND actual_result IS NOT NULL
        """,
            params,
        )
        total_roi = cursor.fetchone()[0] or 0.0
        roi_per_bet = (total_roi / ats_total * 100) if ats_total > 0 else 0.0

        # E-Factor impact
        cursor.execute(
            f"""
            SELECT AVG(ABS(efactor_adjustment)), MAX(ABS(efactor_adjustment)), MIN(ABS(efactor_adjustment))
            FROM calibration_records {where_clause}
        """,
            params,
        )
        row = cursor.fetchone()
        efactor_impact_avg = row[0] or 0.0
        efactor_impact_max = row[1] or 0.0
        efactor_impact_min = row[2] or 0.0

        # Source quality
        cursor.execute(
            f"""
            SELECT efactor_sources, AVG(CAST(ats_result AS FLOAT))
            FROM calibration_records {where_clause}
            AND actual_result IS NOT NULL
            AND ats_result IS NOT NULL
            GROUP BY efactor_sources
        """,
            params,
        )
        source_scores: Dict[str, float] = {}
        rows = cursor.fetchall()
        for row in rows:
            sources = json.loads(row[0])
            win_rate = row[1] or 0.0
            for source in sources:
                if source not in source_scores:
                    source_scores[source] = []
                source_scores[source].append(win_rate)

        # Average by source
        source_scores = {k: sum(v) / len(v) for k, v in source_scores.items()}

        best_source = (
            max(source_scores, key=source_scores.get) if source_scores else None
        )
        worst_source = (
            min(source_scores, key=source_scores.get) if source_scores else None
        )

        return CalibrationMetrics(
            total_predictions=total_predictions,
            total_outcomes=total_outcomes,
            avg_predicted_edge=avg_predicted_edge,
            avg_actual_margin=avg_actual_margin,
            edge_rmse=edge_rmse,
            ats_win_rate=ats_win_rate,
            ats_total_bets=ats_total,
            ats_wins=ats_wins,
            ats_losses=ats_losses,
            ats_pushes=ats_pushes,
            total_roi=total_roi,
            roi_per_bet_pct=roi_per_bet,
            efactor_impact_avg=efactor_impact_avg,
            efactor_impact_max=efactor_impact_max,
            efactor_impact_min=efactor_impact_min,
            best_source=best_source,
            worst_source=worst_source,
            source_scores=source_scores,
        )

    async def export_report(
        self, filepath: str, league: str = "nfl", weeks: Optional[int] = None
    ) -> Path:
        """Export calibration report to JSON."""
        metrics = await self.get_calibration_report(league=league, weeks=weeks)

        report = {
            "timestamp": datetime.now().isoformat(),
            "league": league,
            "metrics": metrics.to_dict(),
            "recommendations": await self._get_recommendations(metrics),
        }

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"✓ Exported calibration report to {output_path}")
        return output_path

    async def _get_recommendations(self, metrics: CalibrationMetrics) -> Dict[str, Any]:
        """Generate calibration recommendations."""
        recommendations = {}

        # Edge accuracy
        if metrics.edge_rmse > 5.0:
            recommendations["edge_accuracy"] = (
                f"High RMSE ({metrics.edge_rmse:.1f}). Consider re-calibrating "
                "power rating models."
            )
        else:
            recommendations["edge_accuracy"] = (
                f"Good edge accuracy (RMSE: {metrics.edge_rmse:.1f})"
            )

        # E-Factor impact
        if metrics.efactor_impact_avg < 1.0:
            recommendations["efactor_impact"] = (
                "E-Factors have minimal average impact (<1.0 pts). "
                "Consider increasing weights."
            )
        elif metrics.efactor_impact_avg > 5.0:
            recommendations["efactor_impact"] = (
                f"High E-Factor impact ({metrics.efactor_impact_avg:.1f} pts). "
                "Verify impact is justified by outcomes."
            )

        # Source quality
        if metrics.best_source and metrics.source_scores:
            best_score = metrics.source_scores[metrics.best_source]
            if best_score > 0.6:
                recommendations["best_source"] = (
                    f"Source '{metrics.best_source}' performing well "
                    f"({best_score * 100:.1f}% ATS). Consider increasing weight."
                )

        if metrics.worst_source and metrics.source_scores:
            worst_score = metrics.source_scores[metrics.worst_source]
            if worst_score < 0.4:
                recommendations["worst_source"] = (
                    f"Source '{metrics.worst_source}' underperforming "
                    f"({worst_score * 100:.1f}% ATS). Consider decreasing weight."
                )

        # ATS performance
        if metrics.ats_win_rate > 0.55:
            recommendations["ats_performance"] = (
                f"Excellent ATS record ({metrics.ats_win_rate:.1f}%). "
                "Model is working well."
            )
        elif metrics.ats_win_rate < 0.45:
            recommendations["ats_performance"] = (
                f"Poor ATS record ({metrics.ats_win_rate:.1f}%). "
                "Consider reducing bet sizes or recalibrating."
            )

        return recommendations

    async def print_report(
        self, league: str = "nfl", weeks: Optional[int] = None
    ) -> None:
        """Print calibration report to console."""
        metrics = await self.get_calibration_report(league=league, weeks=weeks)

        print(f"\n{'=' * 70}")
        print(f"E-FACTOR CALIBRATION REPORT - {league.upper()}")
        print(f"{'=' * 70}")

        print(f"\n📊 OVERVIEW:")
        print(f"  Predictions: {metrics.total_predictions}")
        print(f"  Outcomes: {metrics.total_outcomes}")
        print(f"  Sample Size: {metrics.total_outcomes}/{metrics.total_predictions}")

        print(f"\n📈 EDGE ACCURACY:")
        print(f"  Predicted Edge (avg): {metrics.avg_predicted_edge:+.1f}%")
        print(f"  Actual Margin (avg): {metrics.avg_actual_margin:+.1f}%")
        print(f"  RMSE: {metrics.edge_rmse:.1f}pts")

        print(f"\n🎯 ATS PERFORMANCE:")
        print(
            f"  Win Rate: {metrics.ats_win_rate:.1f}% ({metrics.ats_wins}-{metrics.ats_losses}-{metrics.ats_pushes})"
        )
        print(f"  Total Bets: {metrics.ats_total_bets}")
        print(f"  ROI: {metrics.roi_per_bet_pct:+.2f}% per bet")

        print(f"\n📰 E-FACTOR IMPACT:")
        print(f"  Average Adjustment: {metrics.efactor_impact_avg:+.2f} pts")
        print(f"  Max Adjustment: {metrics.efactor_impact_max:+.2f} pts")
        print(f"  Min Adjustment: {metrics.efactor_impact_min:+.2f} pts")

        if metrics.source_scores:
            print(f"\n🔍 SOURCE QUALITY:")
            for source, score in sorted(
                metrics.source_scores.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                print(f"  {source}: {score * 100:.1f}%")

        recommendations = await self._get_recommendations(metrics)
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for key, rec in recommendations.items():
                print(f"  • {rec}")


async def main() -> None:
    """Demo usage."""
    calibrator = EFactorCalibrator()
    await calibrator.initialize()

    # Record some sample predictions
    print("Recording sample predictions...")
    await calibrator.record_prediction(
        game_id="KC@DAL_W13",
        week=13,
        team="DAL",
        league="nfl",
        predicted_edge_pct=8.5,
        efactor_adjustment=-3.0,
        efactor_sources=["injury_qb"],
        sharp_alignment="CONTRADICTS",
        confidence_level="MEDIUM",
    )

    await calibrator.record_prediction(
        game_id="GB@DET_W13",
        week=13,
        team="DET",
        league="nfl",
        predicted_edge_pct=6.2,
        efactor_adjustment=1.5,
        efactor_sources=["coaching"],
        sharp_alignment="CONFIRMS",
        confidence_level="HIGH",
    )

    # Record outcomes
    print("Recording outcomes...")
    await calibrator.record_outcome("KC@DAL_W13", "LOSS", -2.5, clv=0.05)
    await calibrator.record_outcome("GB@DET_W13", "WIN", 4.5, clv=-0.02)

    # Get and print report
    await calibrator.print_report(league="nfl")

    # Export report
    await calibrator.export_report(
        "output/efactor_calibration_report.json", league="nfl"
    )

    await calibrator.close()


if __name__ == "__main__":
    asyncio.run(main())
