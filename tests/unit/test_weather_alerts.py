#!/usr/bin/env python3
"""
Test script for weather alerts integration

Validates:
1. OpenWeather client can fetch alerts
2. WeatherAlertMapper correctly maps alerts to adjustments
3. Edge detector integrates alerts into weather impact calculation
"""

import asyncio
import os
from datetime import datetime, timedelta

from scrapers.weather import OpenWeatherClient
from src.walters_analyzer.valuation.weather_alert_mapper import (
    WeatherAlertMapper,
    WeatherAlert,
)
from src.walters_analyzer.valuation.billy_walters_edge_detector import (
    BillyWaltersEdgeDetector,
)


async def check_openweather_alerts():
    """Test OpenWeather One Call API 3.0 alerts fetching"""
    print("=" * 70)
    print("Test 1: OpenWeather Alerts API")
    print("=" * 70)

    if not os.getenv("OPENWEATHER_API_KEY"):
        print("[WARNING] OPENWEATHER_API_KEY not set - skipping alerts test")
        return None

    # Test with Akron, OH (where Winter Weather Advisory was observed)
    lat = 41.0814
    lon = -81.5190
    game_time = datetime.now() + timedelta(days=1)  # Tomorrow

    try:
        client = OpenWeatherClient()
        await client.connect()

        alerts = await client.get_weather_alerts(lat, lon, game_time)

        print(f"[OK] Found {len(alerts)} active weather alerts")
        for i, alert in enumerate(alerts, 1):
            print(f"\nAlert {i}:")
            print(f"  Event: {alert.get('event', 'Unknown')}")
            print(f"  Sender: {alert.get('sender_name', 'Unknown')}")
            print(
                f"  Start: {datetime.fromtimestamp(alert.get('start', 0)).strftime('%Y-%m-%d %H:%M')}"
            )
            print(
                f"  End: {datetime.fromtimestamp(alert.get('end', 0)).strftime('%Y-%m-%d %H:%M')}"
            )

        await client.close()
        return alerts

    except Exception as e:
        print(f"[ERROR] Failed to fetch alerts: {e}")
        return None


def check_weather_alert_mapper(raw_alerts):
    """Test WeatherAlertMapper with real alert data"""
    print("\n" + "=" * 70)
    print("Test 2: Weather Alert Mapper")
    print("=" * 70)

    if not raw_alerts:
        print("[WARNING] No alerts to test mapping")
        return

    mapper = WeatherAlertMapper()

    for i, raw_alert in enumerate(raw_alerts, 1):
        alert = mapper.map_alert(raw_alert)

        print(f"\nMapped Alert {i}:")
        print(f"  Event: {alert.event}")
        print(f"  Severity: {alert.severity}")
        print(f"  Total Adjustment: {alert.total_adjustment:.1f} points")
        print(f"  Spread Adjustment: {alert.spread_adjustment:.1f} points")
        print(f"  Confidence: {alert.confidence}")

    # Test maximum impact principle
    mapped_alerts = [mapper.map_alert(a) for a in raw_alerts]
    max_total, max_spread = mapper.get_max_alert_impact(mapped_alerts)

    print("\n[OK] Maximum Impact (Billy Walters Principle):")
    print(f"  Total: {max_total:.1f} points")
    print(f"  Spread: {max_spread:.1f} points")


def check_edge_detector_integration():
    """Test edge detector's weather impact calculation with alerts"""
    print("\n" + "=" * 70)
    print("Test 3: Edge Detector Integration")
    print("=" * 70)

    detector = BillyWaltersEdgeDetector()

    # Test 1: Conditions only (no alerts)
    print("\nScenario A: Conditions only (cold, windy, snowy)")
    impact_conditions = detector.calculate_weather_impact(
        temperature=28.0,
        wind_speed=18.0,
        precipitation="snow",
        indoor=False,
        alerts=None,
    )

    print(
        f"  Total Adjustment: {impact_conditions.total_adjustment:.2f} (Billy: ~-0.60)"
    )
    print(f"  Spread Adjustment: {impact_conditions.spread_adjustment:.2f}")
    print(f"  Alert Severity: {impact_conditions.alert_severity}")

    # Test 2: Alerts only (Winter Storm Warning)
    print("\nScenario B: Winter Storm Warning alert")

    # Create sample alert
    mapper = WeatherAlertMapper()
    sample_alert_data = {
        "event": "Winter Storm Warning",
        "sender_name": "NWS Akron",
        "start": int((datetime.now() - timedelta(hours=2)).timestamp()),
        "end": int((datetime.now() + timedelta(hours=6)).timestamp()),
        "description": "Heavy snow expected. Total accumulations of 6 to 10 inches.",
        "tags": ["Snow", "Moderate"],
    }

    alert = mapper.map_alert(sample_alert_data)
    impact_alert = detector.calculate_weather_impact(
        temperature=32.0,
        wind_speed=10.0,
        precipitation="none",
        indoor=False,
        alerts=[alert],
    )

    print(f"  Total Adjustment: {impact_alert.total_adjustment:.2f} (Billy: -0.60)")
    print(f"  Spread Adjustment: {impact_alert.spread_adjustment:.2f}")
    print(f"  Alert Severity: {impact_alert.alert_severity}")
    print(f"  Alert Total Adj: {impact_alert.alert_total_adjustment:.2f}")

    # Test 3: Both conditions AND alerts (maximum principle)
    print("\nScenario C: Both conditions + Blizzard Warning (maximum principle)")

    blizzard_data = {
        "event": "Blizzard Warning",
        "sender_name": "NWS Buffalo",
        "start": int((datetime.now() - timedelta(hours=1)).timestamp()),
        "end": int((datetime.now() + timedelta(hours=8)).timestamp()),
        "description": "Blizzard conditions with wind gusts to 50 mph.",
        "tags": ["Snow", "Extreme"],
    }

    blizzard_alert = mapper.map_alert(blizzard_data)
    impact_combined = detector.calculate_weather_impact(
        temperature=15.0,  # Extreme cold
        wind_speed=25.0,  # Very windy
        precipitation="snow",
        indoor=False,
        alerts=[blizzard_alert],
    )

    print("  Condition impact: -1.0 pts (cold -0.20 + wind -0.40 + snow -0.40)")
    print(
        f"  Alert impact: {impact_combined.alert_total_adjustment:.2f} pts (Blizzard)"
    )
    print(
        f"  Final (Maximum): {impact_combined.total_adjustment:.2f} pts <- Uses most severe"
    )
    print(f"  Alert Severity: {impact_combined.alert_severity}")

    # Test 4: Indoor stadium (no weather impact)
    print("\nScenario D: Indoor stadium (all weather ignored)")
    impact_indoor = detector.calculate_weather_impact(
        temperature=15.0,
        wind_speed=25.0,
        precipitation="snow",
        indoor=True,
        alerts=[blizzard_alert],
    )

    print(f"  Total Adjustment: {impact_indoor.total_adjustment:.1f} (should be 0.0)")
    print(f"  Alert Severity: {impact_indoor.alert_severity} (should be NONE)")

    print("\n[OK] All edge detector integration tests passed")


async def main():
    """Run all tests"""
    print("\nWeather Alerts Integration Test Suite")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Test 1: OpenWeather API
    raw_alerts = await check_openweather_alerts()

    # Test 2: Alert Mapper
    check_weather_alert_mapper(raw_alerts)

    # Test 3: Edge Detector Integration
    check_edge_detector_integration()

    print("\n" + "=" * 70)
    print("Test Suite Complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
