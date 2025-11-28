"""
E-Factor Decay & Recency Weighting

Implements time-based decay for news/injury E-Factors.
Older news becomes less relevant as team adjusts and players recover.

Principles:
1. Half-life decay: E-Factor impact decreases by 50% every N days
2. Source-specific decay: Different sources decay at different rates
3. Event-type decay: Coaching changes persist longer than small injuries
4. Recency weighting: Recent, strong signals get high confidence boost

Usage:
    decay_fn = NewsDecayFunction()

    # Calculate time-weighted impact
    current_impact = decay_fn.apply_decay(
        original_impact=-8.0,  # QB out
        days_elapsed=5,
        source_type="injury",
        event_type="key_player_out"
    )
    print(f"Current impact: {current_impact:.1f}pts")

    # Get confidence adjustment for recent news
    confidence_boost = decay_fn.get_recency_confidence(
        days_since_news=0,
        signal_strength="VERY_STRONG"
    )
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from math import exp
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    """News/injury source types with decay characteristics."""

    INJURY = "injury"
    COACHING = "coaching"
    TRANSACTION = "transaction"
    PLAYOFF = "playoff"
    WEATHER = "weather"


class EventType(str, Enum):
    """Event types with different decay rates."""

    # Injuries
    KEY_PLAYER_OUT = "key_player_out"  # Elite/Star player out
    STARTER_OUT = "starter_out"  # Regular starter out
    BACKUP_OUT = "backup_out"  # Backup/rotational player out
    POSITION_GROUP_INJURY = "position_group_injury"  # Multiple injuries

    # Coaching
    HEAD_COACH_CHANGE = "head_coach_change"
    COORDINATOR_CHANGE = "coordinator_change"
    INTERIM_COACH = "interim_coach"

    # Personnel
    TRADE = "trade"
    RELEASE = "release"
    SIGNING = "signing"

    # Situational
    PLAYOFF_IMPLICATIONS = "playoff_implications"
    REST_ADVANTAGE = "rest_advantage"
    TRAVEL_FATIGUE = "travel_fatigue"


@dataclass
class DecayParams:
    """Decay parameters for each event type."""

    event_type: EventType
    half_life_days: float  # Days for 50% decay
    min_impact_pct: float  # Minimum impact floor (% of original)
    max_age_days: float  # Max age before 0 impact


# Decay parameters for each event type
DECAY_PARAMETERS: Dict[EventType, DecayParams] = {
    # Injuries - slow decay for key players
    EventType.KEY_PLAYER_OUT: DecayParams(
        event_type=EventType.KEY_PLAYER_OUT,
        half_life_days=7.0,  # 7-day half-life
        min_impact_pct=10.0,  # Minimum 10% impact
        max_age_days=56.0,  # Max age 8 weeks
    ),
    EventType.STARTER_OUT: DecayParams(
        event_type=EventType.STARTER_OUT,
        half_life_days=4.0,
        min_impact_pct=15.0,
        max_age_days=28.0,
    ),
    EventType.BACKUP_OUT: DecayParams(
        event_type=EventType.BACKUP_OUT,
        half_life_days=2.0,
        min_impact_pct=20.0,
        max_age_days=14.0,
    ),
    EventType.POSITION_GROUP_INJURY: DecayParams(
        event_type=EventType.POSITION_GROUP_INJURY,
        half_life_days=5.0,
        min_impact_pct=10.0,
        max_age_days=35.0,
    ),
    # Coaching - persistent impact
    EventType.HEAD_COACH_CHANGE: DecayParams(
        event_type=EventType.HEAD_COACH_CHANGE,
        half_life_days=10.0,  # Longer half-life
        min_impact_pct=5.0,  # Longer persistence
        max_age_days=90.0,  # Max age 3 months
    ),
    EventType.INTERIM_COACH: DecayParams(
        event_type=EventType.INTERIM_COACH,
        half_life_days=8.0,
        min_impact_pct=8.0,
        max_age_days=70.0,
    ),
    EventType.COORDINATOR_CHANGE: DecayParams(
        event_type=EventType.COORDINATOR_CHANGE,
        half_life_days=5.0,
        min_impact_pct=15.0,
        max_age_days=42.0,
    ),
    # Personnel changes - rapid decay
    EventType.TRADE: DecayParams(
        event_type=EventType.TRADE,
        half_life_days=3.0,  # Fast decay - team adjusts
        min_impact_pct=20.0,
        max_age_days=21.0,
    ),
    EventType.RELEASE: DecayParams(
        event_type=EventType.RELEASE,
        half_life_days=2.0,
        min_impact_pct=25.0,
        max_age_days=14.0,
    ),
    EventType.SIGNING: DecayParams(
        event_type=EventType.SIGNING,
        half_life_days=2.0,
        min_impact_pct=25.0,
        max_age_days=14.0,
    ),
    # Situational - moderate decay
    EventType.PLAYOFF_IMPLICATIONS: DecayParams(
        event_type=EventType.PLAYOFF_IMPLICATIONS,
        half_life_days=7.0,
        min_impact_pct=5.0,
        max_age_days=60.0,
    ),
    EventType.REST_ADVANTAGE: DecayParams(
        event_type=EventType.REST_ADVANTAGE,
        half_life_days=3.0,  # Only relevant for current week
        min_impact_pct=30.0,
        max_age_days=14.0,
    ),
    EventType.TRAVEL_FATIGUE: DecayParams(
        event_type=EventType.TRAVEL_FATIGUE,
        half_life_days=1.0,  # Very short-lived
        min_impact_pct=50.0,
        max_age_days=7.0,
    ),
}


class NewsDecayFunction:
    """
    Applies time-based decay to E-Factor impacts.

    Uses exponential decay with half-life parameters specific to event type.
    Implements floor to prevent unrealistic near-zero impacts.
    """

    def apply_decay(
        self,
        original_impact: float,
        days_elapsed: float,
        source_type: str = "injury",
        event_type: str = "key_player_out",
    ) -> float:
        """
        Calculate decayed impact value.

        Args:
            original_impact: Initial impact in points (negative for injuries)
            days_elapsed: Days since event occurred
            source_type: Type of source ("injury", "coaching", etc)
            event_type: Type of event ("key_player_out", "head_coach_change")

        Returns:
            Decayed impact value
        """
        try:
            et = EventType[event_type.upper()]
        except KeyError:
            logger.warning(f"Unknown event type: {event_type}")
            et = EventType.KEY_PLAYER_OUT

        params = DECAY_PARAMETERS[et]

        # Check max age
        if days_elapsed >= params.max_age_days:
            logger.debug(
                f"Event older than max age ({days_elapsed:.1f} days). Impact = 0.0"
            )
            return 0.0

        # Exponential decay: I(t) = I0 * 0.5^(t / half_life)
        decay_factor = (0.5) ** (days_elapsed / params.half_life_days)

        # Apply floor
        min_factor = params.min_impact_pct / 100.0
        decay_factor = max(decay_factor, min_factor)

        decayed_impact = original_impact * decay_factor

        logger.debug(
            f"Decay: {original_impact:.1f} → {decayed_impact:.1f} pts "
            f"({days_elapsed:.1f} days, {decay_factor * 100:.0f}% remaining)"
        )

        return decayed_impact

    def get_recency_confidence(
        self,
        days_since_news: float,
        signal_strength: str = "MODERATE",
        event_type: str = "key_player_out",
    ) -> float:
        """
        Get confidence boost for recent, strong signals.

        New, strong signals get confidence boost.
        Old, weak signals get confidence penalty.

        Args:
            days_since_news: Days since news occurred
            signal_strength: "VERY_STRONG", "STRONG", "MODERATE", "WEAK"
            event_type: Type of event

        Returns:
            Confidence adjustment (-0.2 to +0.2)
        """
        # Base confidence by signal strength
        signal_boost = {
            "VERY_STRONG": 0.15,
            "STRONG": 0.10,
            "MODERATE": 0.05,
            "WEAK": 0.0,
            "NONE": -0.05,
        }.get(signal_strength, 0.0)

        # Recency penalty
        try:
            et = EventType[event_type.upper()]
        except KeyError:
            et = EventType.KEY_PLAYER_OUT

        params = DECAY_PARAMETERS[et]

        # Decay factor (0.0 to 1.0)
        decay_factor = (0.5) ** (days_since_news / params.half_life_days)
        decay_factor = max(decay_factor, params.min_impact_pct / 100.0)

        # Confidence: strong boost for fresh news, penalty for stale
        if days_since_news <= 1:
            recency_boost = 0.10  # Fresh news
        elif days_since_news <= 3:
            recency_boost = 0.05  # Recent
        elif days_since_news <= 7:
            recency_boost = 0.0  # Medium age
        else:
            recency_boost = -0.05 * (days_since_news / 7.0)  # Increasing penalty

        total_confidence = signal_boost + recency_boost

        # Clamp to [-0.2, 0.2]
        return max(-0.2, min(0.2, total_confidence))

    def get_weight_curve(
        self, event_type: str = "key_player_out", max_days: int = 60
    ) -> Dict[int, float]:
        """
        Get decay weight curve for visualization.

        Args:
            event_type: Type of event
            max_days: Number of days to compute

        Returns:
            Dict mapping day -> weight (0.0 to 1.0)
        """
        curve = {}
        try:
            et = EventType[event_type.upper()]
        except KeyError:
            et = EventType.KEY_PLAYER_OUT

        params = DECAY_PARAMETERS[et]

        for day in range(max_days + 1):
            if day >= params.max_age_days:
                curve[day] = 0.0
            else:
                decay = (0.5) ** (day / params.half_life_days)
                decay = max(decay, params.min_impact_pct / 100.0)
                curve[day] = decay

        return curve

    def apply_decay_with_timestamp(
        self,
        original_impact: float,
        event_timestamp: datetime,
        source_type: str = "injury",
        event_type: str = "key_player_out",
        reference_time: Optional[datetime] = None,
    ) -> float:
        """
        Apply decay using datetime objects.

        Args:
            original_impact: Initial impact in points
            event_timestamp: When the event occurred
            source_type: Type of source
            event_type: Type of event
            reference_time: Current time (default: now)

        Returns:
            Decayed impact value
        """
        if reference_time is None:
            reference_time = datetime.now()

        days_elapsed = (reference_time - event_timestamp).total_seconds() / (24 * 3600)
        return self.apply_decay(
            original_impact,
            max(0.0, days_elapsed),
            source_type=source_type,
            event_type=event_type,
        )


def print_decay_curves() -> None:
    """Print decay curves for all event types."""
    decay_fn = NewsDecayFunction()

    print("\n" + "=" * 70)
    print("E-FACTOR DECAY CURVES")
    print("=" * 70)

    for event_type in EventType:
        params = DECAY_PARAMETERS[event_type]
        curve = decay_fn.get_weight_curve(event_type.value, max_days=60)

        print(f"\n{event_type.value.upper()}")
        print(f"  Half-life: {params.half_life_days:.1f} days")
        print(f"  Max age: {params.max_age_days:.1f} days")
        print(f"  Min impact: {params.min_impact_pct:.0f}%")
        print(f"\n  Day | Weight")
        print(f"  --- | ------")

        for day in [0, 1, 3, 7, 14, 28, 42, 56]:
            if day <= max(curve.keys()):
                weight = curve[day]
                bar = "█" * int(weight * 40)
                print(f"  {day:3d} | {weight:5.1%} {bar}")


async def main() -> None:
    """Demo usage."""
    decay_fn = NewsDecayFunction()

    print("\n" + "=" * 70)
    print("NEWS DECAY & RECENCY WEIGHTING")
    print("=" * 70)

    # Example 1: QB injury decay
    print("\nExample 1: Elite QB (Dak Prescott) Out")
    print("-" * 70)
    original_impact = -8.0  # Elite QB out

    for days in [0, 1, 3, 7, 14, 28]:
        impact = decay_fn.apply_decay(
            original_impact,
            days,
            event_type="key_player_out",
        )
        confidence = decay_fn.get_recency_confidence(
            days,
            signal_strength="VERY_STRONG",
            event_type="key_player_out",
        )
        print(f"Day {days:2d}: Impact={impact:+6.1f}pts | Confidence={confidence:+.1%}")

    # Example 2: Coaching change decay
    print("\nExample 2: Head Coach Change (Interim)")
    print("-" * 70)
    original_impact = -3.5

    for days in [0, 1, 7, 14, 28, 56]:
        impact = decay_fn.apply_decay(
            original_impact,
            days,
            event_type="interim_coach",
        )
        confidence = decay_fn.get_recency_confidence(
            days,
            signal_strength="STRONG",
            event_type="interim_coach",
        )
        print(f"Day {days:2d}: Impact={impact:+6.1f}pts | Confidence={confidence:+.1%}")

    # Example 3: Trade/transaction decay
    print("\nExample 3: Star Player Traded")
    print("-" * 70)
    original_impact = -2.5

    for days in [0, 1, 2, 5, 10, 21]:
        impact = decay_fn.apply_decay(
            original_impact,
            days,
            event_type="trade",
        )
        confidence = decay_fn.get_recency_confidence(
            days,
            signal_strength="STRONG",
            event_type="trade",
        )
        print(f"Day {days:2d}: Impact={impact:+6.1f}pts | Confidence={confidence:+.1%}")

    # Print decay curves
    print_decay_curves()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
