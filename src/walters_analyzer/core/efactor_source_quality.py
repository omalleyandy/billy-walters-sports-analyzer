"""
E-Factor Source Quality & Confidence Scoring

Tracks and scores reliability of news/injury data sources.
Dynamically adjusts confidence in E-Factors based on source quality.

Metrics tracked per source:
1. **Accuracy**: How accurate are injury prognoses?
2. **Coverage**: % of relevant events detected
3. **Latency**: Time to detection
4. **Consistency**: Reliability over time
5. **Alignment**: Agreement between sources on same event

Usage:
    quality_tracker = SourceQualityTracker()

    # Record observation: What source said vs what happened
    quality_tracker.record_observation(
        source_name="espn_injuries",
        event_id="DAL_Prescott_W13",
        predicted_days_out=8,
        actual_days_out=7,
        was_accurate=True
    )

    # Get source quality score
    score = quality_tracker.get_source_score("espn_injuries")
    print(f"ESPN Injuries: {score.overall_score:.2f}")

    # Adjust E-Factor confidence
    confidence_adjustment = quality_tracker.get_confidence_adjustment(
        sources=["espn_injuries"],
        base_confidence=0.9
    )
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SourceObservation:
    """Single observation of a source for tracking accuracy."""

    source_name: str
    event_id: str
    timestamp: datetime
    event_type: str  # "injury", "coaching", "transaction"
    observation: Dict[str, Any]  # What source reported
    actual_outcome: Optional[Dict[str, Any]] = None  # What actually happened
    accuracy_score: Optional[float] = None  # 0.0-1.0
    latency_hours: Optional[float] = None


@dataclass
class SourceQualityMetrics:
    """Quality metrics for a single source."""

    source_name: str
    observations_count: int = 0
    accurate_count: int = 0
    accuracy_rate: float = 0.0

    # Coverage
    events_detected: int = 0
    events_missed: int = 0
    coverage_rate: float = 0.0

    # Latency
    avg_latency_hours: float = 0.0
    median_latency_hours: float = 0.0

    # Consistency
    recent_accuracy: float = 0.0  # Last 10 observations
    accuracy_variance: float = 0.0
    consistency_score: float = 0.0

    # Alignment with other sources
    avg_source_agreement: float = 0.0
    conflict_count: int = 0

    # Overall score
    overall_score: float = 0.0  # Weighted average
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            k: v.isoformat() if isinstance(v, datetime) else v
            for k, v in asdict(self).items()
        }


class SourceQualityTracker:
    """
    Tracks and scores data source quality.

    Uses historical observations to build reliability scores
    and confidence adjustments for E-Factor predictions.
    """

    def __init__(self, data_dir: str = "output/source_quality"):
        """Initialize tracker."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.observations: List[SourceObservation] = []
        self.metrics: Dict[str, SourceQualityMetrics] = {}
        self.source_agreements: Dict[str, Dict[str, int]] = {}  # Pairwise agreements

    def record_observation(
        self,
        source_name: str,
        event_id: str,
        event_type: str,
        observation: Dict[str, Any],
        actual_outcome: Optional[Dict[str, Any]] = None,
        accuracy_score: Optional[float] = None,
        latency_hours: Optional[float] = None,
    ) -> None:
        """
        Record an observation for a source.

        Args:
            source_name: Name of source (e.g., "espn_injuries")
            event_id: Unique event identifier
            event_type: Type of event ("injury", "coaching", "transaction")
            observation: What the source reported
            actual_outcome: What actually happened
            accuracy_score: Accuracy of observation (0.0-1.0)
            latency_hours: Time from event to detection
        """
        obs = SourceObservation(
            source_name=source_name,
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=event_type,
            observation=observation,
            actual_outcome=actual_outcome,
            accuracy_score=accuracy_score,
            latency_hours=latency_hours,
        )

        self.observations.append(obs)

        # Update metrics
        self._update_metrics(source_name, obs)
        logger.debug(f"Recorded observation for {source_name}: {event_id}")

    def record_outcome(
        self,
        event_id: str,
        actual_outcome: Dict[str, Any],
        accurate_sources: List[str],
        conflicting_sources: List[str] = None,
    ) -> None:
        """
        Record actual outcome and which sources were accurate.

        Args:
            event_id: Unique event identifier
            actual_outcome: What actually happened
            accurate_sources: Sources that predicted correctly
            conflicting_sources: Sources that predicted wrong
        """
        if conflicting_sources is None:
            conflicting_sources = []

        # Find observations for this event
        for obs in self.observations:
            if obs.event_id == event_id:
                obs.actual_outcome = actual_outcome

                if obs.source_name in accurate_sources:
                    obs.accuracy_score = 1.0
                elif obs.source_name in conflicting_sources:
                    obs.accuracy_score = 0.0
                else:
                    obs.accuracy_score = 0.5

                # Update metrics
                self._update_metrics(obs.source_name, obs)

        # Record source agreements
        for source1 in accurate_sources:
            for source2 in accurate_sources:
                if source1 != source2:
                    self._record_agreement(source1, source2, True)

        for source1 in accurate_sources:
            for source2 in conflicting_sources:
                self._record_agreement(source1, source2, False)

    def _update_metrics(self, source_name: str, observation: SourceObservation) -> None:
        """Update metrics for a source."""
        if source_name not in self.metrics:
            self.metrics[source_name] = SourceQualityMetrics(source_name=source_name)

        metrics = self.metrics[source_name]
        metrics.observations_count += 1

        if observation.accuracy_score is not None:
            if observation.accuracy_score >= 0.8:
                metrics.accurate_count += 1

            # Exponential moving average for recent accuracy
            alpha = 0.1
            metrics.recent_accuracy = (
                alpha * observation.accuracy_score
                + (1 - alpha) * metrics.recent_accuracy
            )

        if observation.latency_hours is not None:
            alpha = 0.1
            metrics.avg_latency_hours = (
                alpha * observation.latency_hours
                + (1 - alpha) * metrics.avg_latency_hours
            )

        # Recalculate rates
        if metrics.observations_count > 0:
            metrics.accuracy_rate = metrics.accurate_count / metrics.observations_count
            metrics.coverage_rate = (
                metrics.events_detected
                / (metrics.events_detected + metrics.events_missed)
                if (metrics.events_detected + metrics.events_missed) > 0
                else 0.0
            )

        metrics.last_updated = datetime.now()

        # Calculate overall score
        self._calculate_overall_score(metrics)

    def _record_agreement(self, source1: str, source2: str, agreed: bool) -> None:
        """Record agreement between two sources."""
        key = f"{min(source1, source2)}_{max(source1, source2)}"

        if key not in self.source_agreements:
            self.source_agreements[key] = {"agreed": 0, "disagreed": 0}

        if agreed:
            self.source_agreements[key]["agreed"] += 1
        else:
            self.source_agreements[key]["disagreed"] += 1

    def _calculate_overall_score(self, metrics: SourceQualityMetrics) -> None:
        """Calculate weighted overall score for a source."""
        # Weights
        weights = {
            "accuracy": 0.40,
            "coverage": 0.25,
            "latency": 0.15,
            "recency": 0.15,
            "alignment": 0.05,
        }

        # Normalize latency (lower is better)
        # Assume good latency is < 1 hour, bad is > 24 hours
        latency_score = max(0.0, 1.0 - (metrics.avg_latency_hours / 24.0))

        # Normalize coverage
        coverage_score = metrics.coverage_rate

        # Alignment score
        alignment_score = metrics.avg_source_agreement

        # Recent accuracy (more important than overall)
        recency_score = metrics.recent_accuracy

        # Weighted score
        overall = (
            weights["accuracy"] * metrics.accuracy_rate
            + weights["coverage"] * coverage_score
            + weights["latency"] * latency_score
            + weights["recency"] * recency_score
            + weights["alignment"] * alignment_score
        )

        metrics.overall_score = max(0.0, min(1.0, overall))

    def get_source_score(self, source_name: str) -> SourceQualityMetrics:
        """Get quality metrics for a source."""
        if source_name not in self.metrics:
            logger.warning(f"No metrics found for {source_name}")
            return SourceQualityMetrics(source_name=source_name)

        return self.metrics[source_name]

    def get_confidence_adjustment(
        self, sources: List[str], base_confidence: float = 0.9
    ) -> float:
        """
        Get confidence adjustment based on source quality.

        Args:
            sources: List of sources contributing to E-Factor
            base_confidence: Base confidence before adjustment

        Returns:
            Adjusted confidence (0.0-1.0)
        """
        if not sources:
            return base_confidence

        # Average score of all sources
        scores = []
        for source in sources:
            score = self.get_source_score(source)
            scores.append(score.overall_score)

        avg_score = sum(scores) / len(scores) if scores else 0.5

        # Apply quality adjustment
        # If source is poor (< 0.5), reduce confidence
        # If source is good (> 0.7), increase confidence
        adjustment = (avg_score - 0.5) * 0.2  # -0.1 to +0.1 range

        adjusted = base_confidence + adjustment
        return max(0.0, min(1.0, adjusted))

    def get_source_comparison(self) -> Dict[str, float]:
        """Get all source quality scores for comparison."""
        comparison = {}
        for source_name, metrics in self.metrics.items():
            comparison[source_name] = metrics.overall_score

        return dict(sorted(comparison.items(), key=lambda x: x[1], reverse=True))

    def export_report(
        self, filepath: str = "output/source_quality_report.json"
    ) -> Path:
        """Export quality report to JSON."""
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "timestamp": datetime.now().isoformat(),
            "sources": {
                name: metrics.to_dict() for name, metrics in self.metrics.items()
            },
            "source_agreements": self.source_agreements,
            "comparison": self.get_source_comparison(),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"✓ Exported source quality report to {output_path}")
        return output_path

    def print_report(self) -> None:
        """Print quality report to console."""
        print("\n" + "=" * 70)
        print("SOURCE QUALITY REPORT")
        print("=" * 70)

        # Sort by overall score
        sorted_sources = sorted(
            self.metrics.items(),
            key=lambda x: x[1].overall_score,
            reverse=True,
        )

        print(f"\n{'Source':<30} {'Score':<10} {'Accuracy':<12} {'Coverage':<10}")
        print("-" * 70)

        for source_name, metrics in sorted_sources:
            score = metrics.overall_score
            accuracy = metrics.accuracy_rate
            coverage = metrics.coverage_rate

            # Color coding (text representation)
            if score >= 0.8:
                status = "✓"
            elif score >= 0.6:
                status = "○"
            else:
                status = "✗"

            print(
                f"{source_name:<30} {score:.2f} {status:<8} "
                f"{accuracy:>6.1%}        {coverage:>6.1%}"
            )

        print("\n" + "=" * 70)
        print("RECOMMENDATIONS")
        print("=" * 70)

        for source_name, metrics in sorted_sources:
            if metrics.overall_score < 0.6:
                print(f"⚠️  {source_name}: Score < 0.6 - Consider deprioritizing")
            elif metrics.accuracy_rate < 0.5:
                print(
                    f"⚠️  {source_name}: Poor accuracy ({metrics.accuracy_rate:.1%}) - Investigate"
                )
            elif metrics.avg_latency_hours > 12:
                print(
                    f"⚠️  {source_name}: High latency ({metrics.avg_latency_hours:.1f} hrs) - Check data pipeline"
                )

        best_source = sorted_sources[0] if sorted_sources else None
        if best_source:
            print(
                f"\n✓ Best performer: {best_source[0]} ({best_source[1].overall_score:.2f})"
            )


async def main() -> None:
    """Demo usage."""
    tracker = SourceQualityTracker()

    print("\n" + "=" * 70)
    print("SOURCE QUALITY TRACKING")
    print("=" * 70)

    # Record some observations
    print("\nRecording observations...")

    tracker.record_observation(
        source_name="espn_injuries",
        event_id="DAL_Prescott_W13",
        event_type="injury",
        observation={"player": "Dak Prescott", "status": "out"},
        actual_outcome={"player": "Dak Prescott", "status": "out"},
        accuracy_score=1.0,
        latency_hours=0.5,
    )

    tracker.record_observation(
        source_name="espn_injuries",
        event_id="DAL_Prescott_W13",
        event_type="injury",
        observation={"player": "Dak Prescott", "recovery_days": 10},
        actual_outcome={"player": "Dak Prescott", "recovery_days": 7},
        accuracy_score=0.7,
        latency_hours=0.5,
    )

    tracker.record_observation(
        source_name="nfl_injuries",
        event_id="DAL_Prescott_W13",
        event_type="injury",
        observation={"player": "Dak Prescott", "status": "out"},
        actual_outcome={"player": "Dak Prescott", "status": "out"},
        accuracy_score=1.0,
        latency_hours=0.2,
    )

    # Record outcome and agreement
    tracker.record_outcome(
        event_id="DAL_Prescott_W13",
        actual_outcome={"player": "Dak Prescott", "status": "out"},
        accurate_sources=["espn_injuries", "nfl_injuries"],
    )

    # Print report
    tracker.print_report()

    # Get confidence adjustment
    confidence = tracker.get_confidence_adjustment(
        sources=["espn_injuries", "nfl_injuries"]
    )
    print(f"\nConfidence adjustment: {confidence:.2f}")

    # Export
    tracker.export_report()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
