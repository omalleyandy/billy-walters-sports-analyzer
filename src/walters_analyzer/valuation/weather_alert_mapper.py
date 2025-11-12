#!/usr/bin/env python3
"""
Weather Alert Mapper for Billy Walters System

Maps National Weather Service (NWS) weather alerts to point adjustments
using Billy Walters betting methodology.

Alert data comes from OpenWeather One Call API 3.0 (free tier).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Alert-to-adjustment mapping based on Billy Walters W-Factor methodology
# Billy Walters W-Factors: 0.20-0.60 points (from Advanced Masterclass)
# Format: (total_adjustment, spread_adjustment, confidence)
# Negative values = reduce scoring/favor defense

ALERT_ADJUSTMENTS = {
    # Winter Weather Alerts (Billy Walters: -0.20 to -0.60 pts)
    "Blizzard Warning": (-0.80, -0.30, "HIGH"),  # Extreme: heavy snow + high wind
    "Ice Storm Warning": (-0.70, -0.25, "HIGH"),  # Extreme: ice accumulation
    "Winter Storm Warning": (-0.60, -0.25, "HIGH"),  # Heavy snow (Billy: -0.60)
    "Heavy Snow Warning": (-0.50, -0.20, "HIGH"),  # Heavy snow
    "Winter Weather Advisory": (-0.30, -0.12, "MEDIUM"),  # Light-moderate snow
    "Snow Advisory": (-0.20, -0.10, "MEDIUM"),  # Light snow (Billy: -0.20)
    "Freezing Rain Advisory": (-0.35, -0.15, "MEDIUM"),  # Ice + rain
    "Wind Chill Warning": (-0.25, -0.10, "MEDIUM"),  # Extreme cold + wind
    "Wind Chill Advisory": (-0.15, -0.06, "LOW"),  # Cold + wind
    # Wind Alerts (Billy Walters: -0.20 to -0.40 pts)
    "High Wind Warning": (
        -0.40,
        -0.15,
        "HIGH",
    ),  # Severe wind (Billy: -0.40 for 20+ mph)
    "Wind Advisory": (
        -0.20,
        -0.10,
        "MEDIUM",
    ),  # Moderate wind (Billy: -0.20 for 15+ mph)
    "Extreme Wind Warning": (-0.50, -0.20, "HIGH"),  # Beyond 20mph threshold
    # Precipitation Alerts (Billy Walters: -0.20 to -0.40 pts)
    "Flash Flood Warning": (-0.50, -0.20, "HIGH"),  # Severe rain + field conditions
    "Flood Warning": (-0.40, -0.15, "MEDIUM"),  # Heavy rain
    "Flood Watch": (-0.15, -0.06, "LOW"),  # Moderate rain possibility
    "Heavy Rain Warning": (-0.35, -0.12, "MEDIUM"),  # Heavy rain (Billy: -0.40)
    "Excessive Rainfall": (-0.30, -0.12, "MEDIUM"),  # Moderate-heavy rain
    # Thunderstorm Alerts (Billy Walters: -0.20 to -0.40 pts + delays)
    "Severe Thunderstorm Warning": (
        -0.40,
        -0.15,
        "MEDIUM",
    ),  # Heavy rain + wind + delays
    "Thunderstorm Watch": (-0.20, -0.08, "LOW"),  # Moderate rain possibility
    "Tornado Warning": (-0.60, -0.25, "HIGH"),  # Game delays/suspension
    "Tornado Watch": (-0.25, -0.10, "MEDIUM"),  # Severe weather possible
    # Fog Alerts (Billy Walters: not specified, conservative)
    "Dense Fog Advisory": (-0.15, -0.06, "LOW"),  # Visibility issues
    # Temperature Alerts (Billy Walters: -0.20 pts for extreme)
    "Extreme Cold Warning": (-0.30, -0.12, "HIGH"),  # Below 20°F + wind chill
    "Cold Weather Advisory": (-0.20, -0.08, "MEDIUM"),  # Below 20°F (Billy: -0.20)
    "Excessive Heat Warning": (-0.25, -0.10, "MEDIUM"),  # Above 90°F (Billy: -0.20)
    "Heat Advisory": (-0.15, -0.06, "LOW"),  # Above 90°F
    # Marine/Coastal (Less Relevant, conservative)
    "Gale Warning": (-0.25, -0.10, "MEDIUM"),  # Coastal wind
    "Storm Warning": (-0.40, -0.15, "HIGH"),  # Coastal storm
}


@dataclass
class WeatherAlert:
    """
    Structured weather alert with Billy Walters point adjustments.

    Attributes:
        event: Alert type (e.g., "Winter Storm Warning")
        sender_name: Alert issuer (e.g., "NWS Green Bay")
        start_time: Alert start time
        end_time: Alert end time
        description: Full alert text from NWS
        total_adjustment: Points to subtract from game total (negative = lower scoring)
        spread_adjustment: Points to adjust spread (negative = favor defense/rushing)
        confidence: Confidence level ("HIGH", "MEDIUM", "LOW")
        severity: Billy Walters severity classification
        tags: Alert categories/keywords
    """

    event: str
    sender_name: str
    start_time: datetime
    end_time: datetime
    description: str
    total_adjustment: float
    spread_adjustment: float
    confidence: str
    severity: str
    tags: list[str] = field(default_factory=list)


class WeatherAlertMapper:
    """
    Maps weather alerts to Billy Walters point adjustments.

    Uses Billy Walters methodology:
    - Maximum impact, not additive (alerts already account for conditions)
    - Severity classification (CRITICAL/MAJOR/MODERATE/MINOR)
    - Confidence-weighted adjustments
    """

    def map_alert(self, alert_data: dict[str, Any]) -> WeatherAlert:
        """
        Map raw alert data to Billy Walters WeatherAlert with adjustments.

        Args:
            alert_data: Raw alert from OpenWeather One Call API 3.0
                Required fields: event, sender_name, start, end, description
                Optional fields: tags

        Returns:
            WeatherAlert with Billy Walters point adjustments
        """
        event = alert_data.get("event", "Unknown")
        sender_name = alert_data.get("sender_name", "Unknown")
        start_time = datetime.fromtimestamp(alert_data.get("start", 0))
        end_time = datetime.fromtimestamp(alert_data.get("end", 0))
        description = alert_data.get("description", "")
        tags = alert_data.get("tags", [])

        # Get adjustment values from mapping table
        total_adj, spread_adj, confidence = self._get_adjustment(event)

        # Classify severity using Billy Walters thresholds
        severity = self._classify_severity(total_adj)

        return WeatherAlert(
            event=event,
            sender_name=sender_name,
            start_time=start_time,
            end_time=end_time,
            description=description,
            total_adjustment=total_adj,
            spread_adjustment=spread_adj,
            confidence=confidence,
            severity=severity,
            tags=tags,
        )

    def _get_adjustment(self, event: str) -> tuple[float, float, str]:
        """
        Get point adjustments for alert type.

        Args:
            event: Alert event name

        Returns:
            Tuple of (total_adjustment, spread_adjustment, confidence)
        """
        # Exact match
        if event in ALERT_ADJUSTMENTS:
            return ALERT_ADJUSTMENTS[event]

        # Fuzzy matching for variations (Billy Walters W-Factor aligned)
        event_lower = event.lower()

        # Winter storm variations
        if "blizzard" in event_lower:
            return (-0.80, -0.30, "HIGH")
        elif "ice storm" in event_lower:
            return (-0.70, -0.25, "HIGH")
        elif "winter storm" in event_lower:
            return (-0.60, -0.25, "HIGH")
        elif "winter weather" in event_lower or "snow advisory" in event_lower:
            return (-0.30, -0.12, "MEDIUM")

        # Wind variations
        elif "high wind" in event_lower or "extreme wind" in event_lower:
            return (-0.40, -0.15, "HIGH")
        elif "wind advisory" in event_lower or "wind warning" in event_lower:
            return (-0.20, -0.10, "MEDIUM")

        # Precipitation variations
        elif "flash flood" in event_lower:
            return (-0.50, -0.20, "HIGH")
        elif "flood warning" in event_lower:
            return (-0.40, -0.15, "MEDIUM")
        elif "heavy rain" in event_lower:
            return (-0.35, -0.12, "MEDIUM")

        # Thunderstorm variations
        elif "severe thunderstorm" in event_lower:
            return (-0.40, -0.15, "MEDIUM")
        elif "tornado warning" in event_lower:
            return (-0.60, -0.25, "HIGH")

        # Temperature variations
        elif "extreme cold" in event_lower or "wind chill warning" in event_lower:
            return (-0.30, -0.12, "HIGH")
        elif "excessive heat" in event_lower:
            return (-0.25, -0.10, "MEDIUM")

        # Default for unknown alerts (conservative - Billy Walters minimum)
        return (-0.10, -0.05, "LOW")

    def _classify_severity(self, total_adjustment: float) -> str:
        """
        Classify alert severity using Billy Walters W-Factor thresholds.

        Billy Walters W-Factors: 0.20-0.60 points typical range
        Matches injury impact system for consistency.

        Args:
            total_adjustment: Total point adjustment (negative)

        Returns:
            Severity classification: CRITICAL/MAJOR/MODERATE/MINOR/NEGLIGIBLE
        """
        # Use absolute value for comparison (adjustments are negative)
        abs_impact = abs(total_adjustment)

        if abs_impact >= 0.60:
            return "CRITICAL"  # Blizzard, Tornado, Extreme Wind (0.60-0.80 pts)
        elif abs_impact >= 0.40:
            return "MAJOR"  # Winter Storm, High Wind, Flash Flood (0.40-0.60 pts)
        elif abs_impact >= 0.20:
            return "MODERATE"  # Advisories, Moderate Winds (0.20-0.40 pts)
        elif abs_impact >= 0.10:
            return "MINOR"  # Watches, Light Advisories (0.10-0.20 pts)
        else:
            return "NEGLIGIBLE"  # <0.10 pts

    def get_max_alert_impact(self, alerts: list[WeatherAlert]) -> tuple[float, float]:
        """
        Get maximum impact from list of alerts.

        Billy Walters principle: Use MAXIMUM impact, not additive.
        Alerts already account for underlying conditions.

        Args:
            alerts: List of WeatherAlert objects

        Returns:
            Tuple of (max_total_adjustment, max_spread_adjustment)
        """
        if not alerts:
            return (0.0, 0.0)

        # Find most severe total adjustment (most negative)
        max_total = min(alert.total_adjustment for alert in alerts)

        # Find most severe spread adjustment (most negative)
        max_spread = min(alert.spread_adjustment for alert in alerts)

        return (max_total, max_spread)

    def filter_alerts_by_confidence(
        self, alerts: list[WeatherAlert], min_confidence: str = "LOW"
    ) -> list[WeatherAlert]:
        """
        Filter alerts by minimum confidence level.

        Args:
            alerts: List of WeatherAlert objects
            min_confidence: Minimum confidence level ("HIGH", "MEDIUM", "LOW")

        Returns:
            Filtered list of alerts meeting confidence threshold
        """
        confidence_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        min_level = confidence_order.get(min_confidence, 1)

        return [
            alert
            for alert in alerts
            if confidence_order.get(alert.confidence, 0) >= min_level
        ]


# Example usage and testing
def example_usage():
    """Example of mapping alerts to Billy Walters adjustments"""
    mapper = WeatherAlertMapper()

    # Example alert data from OpenWeather One Call API 3.0
    sample_alert = {
        "sender_name": "NWS Green Bay",
        "event": "Winter Storm Warning",
        "start": 1731672000,  # Unix timestamp
        "end": 1731715200,
        "description": (
            "...WINTER STORM WARNING IN EFFECT FROM 6 AM TO 6 PM CST FRIDAY... "
            "Heavy snow expected. Total accumulations of 6 to 10 inches."
        ),
        "tags": ["Snow", "Moderate"],
    }

    # Map to Billy Walters adjustment
    alert = mapper.map_alert(sample_alert)

    print("Weather Alert Analysis:")
    print(f"  Event: {alert.event}")
    print(f"  Severity: {alert.severity}")
    print(f"  Total Impact: {alert.total_adjustment} points")
    print(f"  Spread Impact: {alert.spread_adjustment} points")
    print(f"  Confidence: {alert.confidence}")
    print(f"\n  Interpretation:")
    print(f"  - Game total likely {abs(alert.total_adjustment):.1f} points LOWER")
    print(f"  - Favors defense and rushing teams")
    print(f"  - Fade pass-heavy offenses")
    print(f"  - Consider betting UNDER")


if __name__ == "__main__":
    example_usage()
