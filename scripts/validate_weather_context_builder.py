#!/usr/bin/env python3
"""
Task 2.2 - Weather Context Builder Validation Script

Quick validation script that:
1. Runs smoke tests on all W-Factor calculations
2. Tests real NFL stadium/team combinations
3. Validates edge cases
4. Checks performance
5. Reports overall system health

Usage:
    python scripts/validate_weather_context_builder.py

Expected Output:
    ✓ All validations pass
    ✓ All scenarios work correctly
    ✓ Performance within targets
    ✓ System READY FOR PRODUCTION

Version: 1.0
Created: November 20, 2025
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add project to path (Windows-compatible)
project_root = r"C:\Users\omall\Documents\python_projects\billy-walters-sports-analyzer"
sys.path.insert(0, os.path.join(project_root, "src"))

try:
    from walters_analyzer.models.sfactor_data_models import (
        WeatherContext,
        Precipitation,
        WindCondition,
    )
    from walters_analyzer.data_collection.weather_context_builder import (
        WeatherContextBuilder,
        TeamWeatherSuitability,
        WeatherImpactLevel,
        WeatherDataQuality,
        WARM_WEATHER_TEAMS,
    )
except ImportError as e:
    print(f"ERROR: Failed to import modules: {e}")
    print("\nMake sure you're running from the project root:")
    print(f"  cd {project_root}")
    print("  python scripts/validate_weather_context_builder.py")
    sys.exit(1)


# ===== VALIDATION TESTS =====


class WeatherBuilderValidator:
    """Validation test runner for WeatherContextBuilder"""

    def __init__(self):
        try:
            self.builder = WeatherContextBuilder(production_mode=False)
            print("✓ WeatherContextBuilder initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize WeatherContextBuilder: {e}")
            sys.exit(1)

        self.passed = 0
        self.failed = 0
        self.tests_run = 0

    def test(self, name: str, condition: bool, details: str = ""):
        """Run a single validation test"""
        self.tests_run += 1

        if condition:
            self.passed += 1
            status = "✓"
        else:
            self.failed += 1
            status = "✗"

        print(f"  {status} {name}")
        if details:
            print(f"    └─ {details}")

    def run_all(self):
        """Run all validation tests"""
        print("\n" + "=" * 80)
        print("TASK 2.2 VALIDATION SUITE - WEATHER CONTEXT BUILDER")
        print("=" * 80)

        # Phase 1: Basic Functionality
        print("\n[Phase 1] Basic Functionality")
        self.validate_initialization()
        self.validate_indoor_handling()
        self.validate_outdoor_handling()

        # Phase 2: W-Factor Calculations
        print("\n[Phase 2] W-Factor Calculations")
        self.validate_temperature_factors()
        self.validate_wind_factors()
        self.validate_precipitation_factors()

        # Phase 3: Team Suitability
        print("\n[Phase 3] Team Weather Suitability")
        self.validate_warm_teams()
        self.validate_cold_teams()
        self.validate_neutral_teams()

        # Phase 4: Real NFL Scenarios
        print("\n[Phase 4] Real NFL Scenarios")
        self.validate_playoff_scenario()
        self.validate_super_bowl_scenario()
        self.validate_tropical_scenario()

        # Phase 5: Edge Cases
        print("\n[Phase 5] Edge Cases")
        self.validate_edge_cases()

        # Phase 6: Performance
        print("\n[Phase 6] Performance")
        self.validate_performance()

        # Summary
        self.print_summary()

    def validate_initialization(self):
        """Validate builder initializes correctly"""
        try:
            builder = WeatherContextBuilder(production_mode=False)
            self.test(
                "WeatherContextBuilder initializes",
                builder is not None,
                f"Logger: {builder.logger is not None}",
            )
            self.test(
                "Cache starts empty",
                len(builder._cache) == 0,
                f"Cache size: {len(builder._cache)}",
            )
        except Exception as e:
            self.test("WeatherContextBuilder initializes", False, str(e))

    def validate_indoor_handling(self):
        """Validate indoor weather handling"""
        try:
            indoor_weather = WeatherContext(
                game_location="Dallas, TX",
                is_indoor=True,
                temperature_f=70,
                precipitation_type=Precipitation.NONE,
                wind_speed_mph=0,
                forecast_timestamp=datetime.now(),
            )

            wf = self.builder.calculate_wfactors(
                indoor_weather, "Dallas Cowboys", "Philadelphia Eagles"
            )

            self.test(
                "Indoor games marked correctly",
                wf.indoor_game == True,
                f"Indoor flag: {wf.indoor_game}",
            )
            self.test(
                "Indoor has zero W-Factors",
                len(wf.factors) == 0,
                f"Factor count: {len(wf.factors)}",
            )
            self.test(
                "Indoor has zero impact",
                wf.total_impact_spread == 0.0,
                f"Impact: {wf.total_impact_spread}",
            )
        except Exception as e:
            self.test("Indoor weather handling", False, str(e))

    def validate_outdoor_handling(self):
        """Validate outdoor weather handling"""
        try:
            outdoor_weather = WeatherContext(
                game_location="Buffalo, NY",
                is_indoor=False,
                temperature_f=28,
                wind_speed_mph=15,
                precipitation_type=Precipitation.LIGHT_SNOW,
                forecast_timestamp=datetime.now(),
            )

            wf = self.builder.calculate_wfactors(
                outdoor_weather, "Buffalo Bills", "Miami Dolphins"
            )

            self.test(
                "Outdoor games marked correctly",
                wf.indoor_game == False,
                f"Indoor flag: {wf.indoor_game}",
            )
            self.test(
                "Outdoor has W-Factors",
                len(wf.factors) > 0,
                f"Factor count: {len(wf.factors)}",
            )
            self.test(
                "Outdoor has negative impact (cold/wind)",
                wf.total_impact_spread < 0,
                f"Impact: {wf.total_impact_spread:+.1f}",
            )
        except Exception as e:
            self.test("Outdoor weather handling", False, str(e))

    def validate_temperature_factors(self):
        """Validate temperature W-Factor calculations"""
        try:
            # Cold weather
            cold_weather = WeatherContext(
                game_location="Buffalo, NY",
                is_indoor=False,
                temperature_f=20,
                wind_speed_mph=5,
                precipitation_type=Precipitation.NONE,
                forecast_timestamp=datetime.now(),
            )

            wf_cold = self.builder.calculate_wfactors(
                cold_weather, "Buffalo Bills", "Miami Dolphins"
            )

            self.test(
                "Cold weather has temperature factor",
                any("Cold" in f.name for f in wf_cold.factors),
                f"Cold factors: {len([f for f in wf_cold.factors if 'Cold' in f.name])}",
            )

            # Warm-weather team in cold
            self.test(
                "Warm team penalized in cold",
                any("Warm Team" in f.name for f in wf_cold.factors),
                f"Warm team factors: {len([f for f in wf_cold.factors if 'Warm Team' in f.name])}",
            )
        except Exception as e:
            self.test("Temperature factor validation", False, str(e))

    def validate_wind_factors(self):
        """Validate wind W-Factor calculations"""
        try:
            # Moderate wind
            moderate_wind = WeatherContext(
                game_location="Kansas City, MO",
                is_indoor=False,
                temperature_f=55,
                wind_speed_mph=15,
                precipitation_type=Precipitation.NONE,
                forecast_timestamp=datetime.now(),
            )

            wf_moderate_wind = self.builder.calculate_wfactors(
                moderate_wind, "Kansas City Chiefs", "Buffalo Bills"
            )

            self.test(
                "Moderate wind (10-20 MPH) has wind factor",
                any("Moderate" in f.name for f in wf_moderate_wind.factors),
                f"Wind factors: {len([f for f in wf_moderate_wind.factors if 'Wind' in f.name])}",
            )

            # Strong wind
            strong_wind = WeatherContext(
                game_location="Kansas City, MO",
                is_indoor=False,
                temperature_f=55,
                wind_speed_mph=30,
                precipitation_type=Precipitation.NONE,
                forecast_timestamp=datetime.now(),
            )

            wf_strong = self.builder.calculate_wfactors(
                strong_wind, "Kansas City Chiefs", "Buffalo Bills"
            )

            self.test(
                "Strong wind (>20 MPH) has strong impact",
                wf_strong.total_impact_spread < wf_moderate_wind.total_impact_spread,
                f"Moderate: {wf_moderate_wind.total_impact_spread:+.1f}, Strong: {wf_strong.total_impact_spread:+.1f}",
            )
        except Exception as e:
            self.test("Wind factor validation", False, str(e))

    def validate_precipitation_factors(self):
        """Validate precipitation W-Factor calculations"""
        try:
            # Light rain
            rain_weather = WeatherContext(
                game_location="Miami, FL",
                is_indoor=False,
                temperature_f=75,
                wind_speed_mph=5,
                precipitation_type=Precipitation.LIGHT_RAIN,
                forecast_timestamp=datetime.now(),
            )

            wf_rain = self.builder.calculate_wfactors(
                rain_weather, "Miami Dolphins", "Kansas City Chiefs"
            )

            self.test(
                "Light rain has precipitation factor",
                any("Light Rain" in f.name for f in wf_rain.factors),
                f"Rain factors: {len([f for f in wf_rain.factors if 'Rain' in f.name])}",
            )
        except Exception as e:
            self.test("Precipitation factor validation", False, str(e))

    def validate_warm_teams(self):
        """Validate warm-weather team assessment"""
        try:
            cold_weather = WeatherContext(
                game_location="Buffalo, NY",
                is_indoor=False,
                temperature_f=20,
                wind_speed_mph=15,
                precipitation_type=Precipitation.LIGHT_SNOW,
                forecast_timestamp=datetime.now(),
            )

            unfavorable_count = 0
            for team in list(WARM_WEATHER_TEAMS)[:3]:  # Test first 3
                suit = self.builder.assess_team_weather_suitability(team, cold_weather)
                if suit in [
                    TeamWeatherSuitability.UNFAVORABLE,
                    TeamWeatherSuitability.HIGHLY_UNFAVORABLE,
                ]:
                    unfavorable_count += 1

            self.test(
                "Warm teams unfavorable in cold",
                unfavorable_count >= 2,
                f"Unfavorable teams: {unfavorable_count}/3",
            )
        except Exception as e:
            self.test("Warm team validation", False, str(e))

    def validate_cold_teams(self):
        """Validate cold-weather team assessment"""
        try:
            cold_weather = WeatherContext(
                game_location="Buffalo, NY",
                is_indoor=False,
                temperature_f=15,
                wind_speed_mph=20,
                precipitation_type=Precipitation.HEAVY_SNOW,
                forecast_timestamp=datetime.now(),
            )

            suit = self.builder.assess_team_weather_suitability(
                "Buffalo Bills", cold_weather
            )

            is_good = suit in [
                TeamWeatherSuitability.FAVORABLE,
                TeamWeatherSuitability.HIGHLY_FAVORABLE,
            ]

            self.test(
                "Buffalo Bills favorable in cold", is_good, f"Suitability: {suit.value}"
            )
        except Exception as e:
            self.test("Cold team validation", False, str(e))

    def validate_neutral_teams(self):
        """Validate neutral-climate team assessment"""
        try:
            moderate_weather = WeatherContext(
                game_location="Kansas City, MO",
                is_indoor=False,
                temperature_f=55,
                wind_speed_mph=8,
                precipitation_type=Precipitation.NONE,
                forecast_timestamp=datetime.now(),
            )

            suit = self.builder.assess_team_weather_suitability(
                "Kansas City Chiefs", moderate_weather
            )

            self.test(
                "Neutral team in moderate weather",
                suit == TeamWeatherSuitability.NEUTRAL,
                f"Suitability: {suit.value}",
            )
        except Exception as e:
            self.test("Neutral team validation", False, str(e))

    def validate_playoff_scenario(self):
        """Validate playoff cold weather scenario"""
        try:
            playoff_weather = WeatherContext(
                game_location="Buffalo, NY",
                is_indoor=False,
                temperature_f=18,
                feels_like_f=2,
                wind_speed_mph=28,
                precipitation_type=Precipitation.HEAVY_SNOW,
                forecast_timestamp=datetime.now(),
                hours_until_kickoff=2.0,
            )

            wf = self.builder.calculate_wfactors(
                playoff_weather, "Buffalo Bills", "Miami Dolphins"
            )

            self.test(
                "Playoff scenario has multiple factors",
                len(wf.factors) >= 3,
                f"Factor count: {len(wf.factors)}",
            )

            self.test(
                "Playoff scenario favors cold team",
                wf.total_impact_spread < -4.0,
                f"Impact: {wf.total_impact_spread:+.1f}",
            )
        except Exception as e:
            self.test("Playoff scenario validation", False, str(e))

    def validate_super_bowl_scenario(self):
        """Validate Super Bowl dome scenario"""
        try:
            dome_weather = WeatherContext(
                game_location="Las Vegas, NV",
                is_indoor=True,
                temperature_f=72,
                precipitation_type=Precipitation.NONE,
                wind_speed_mph=0,
                forecast_timestamp=datetime.now(),
                hours_until_kickoff=6.0,
            )

            wf = self.builder.calculate_wfactors(
                dome_weather, "Kansas City Chiefs", "San Francisco 49ers"
            )

            self.test(
                "Super Bowl dome has no factors",
                len(wf.factors) == 0,
                f"Factor count: {len(wf.factors)}",
            )

            self.test(
                "Super Bowl dome no weather impact",
                wf.total_impact_spread == 0.0,
                f"Impact: {wf.total_impact_spread}",
            )
        except Exception as e:
            self.test("Super Bowl scenario validation", False, str(e))

    def validate_tropical_scenario(self):
        """Validate tropical weather scenario"""
        try:
            tropical_weather = WeatherContext(
                game_location="Miami, FL",
                is_indoor=False,
                temperature_f=82,
                wind_speed_mph=8,
                precipitation_type=Precipitation.NONE,
                forecast_timestamp=datetime.now(),
                hours_until_kickoff=5.0,
            )

            miami_suit = self.builder.assess_team_weather_suitability(
                "Miami Dolphins", tropical_weather
            )

            self.test(
                "Miami favorable in tropical conditions",
                miami_suit
                in [
                    TeamWeatherSuitability.FAVORABLE,
                    TeamWeatherSuitability.HIGHLY_FAVORABLE,
                ],
                f"Suitability: {miami_suit.value}",
            )
        except Exception as e:
            self.test("Tropical scenario validation", False, str(e))

    def validate_edge_cases(self):
        """Validate edge case handling"""
        try:
            # None temperature
            weather_none_temp = WeatherContext(
                game_location="Unknown",
                is_indoor=False,
                temperature_f=None,
                wind_speed_mph=10,
                precipitation_type=Precipitation.LIGHT_RAIN,
                forecast_timestamp=datetime.now(),
            )

            wf = self.builder.calculate_wfactors(
                weather_none_temp, "Kansas City Chiefs", "Buffalo Bills"
            )

            self.test(
                "Handles None temperature",
                wf is not None,
                "No crash with None temperature",
            )
        except Exception as e:
            self.test("Edge case handling", False, str(e))

    def validate_performance(self):
        """Validate performance targets"""
        try:
            base_weather = WeatherContext(
                game_location="Kansas City, MO",
                is_indoor=False,
                temperature_f=55,
                wind_speed_mph=10,
                precipitation_type=Precipitation.NONE,
                forecast_timestamp=datetime.now(),
            )

            # W-Factor calculation speed
            start = time.time()
            for _ in range(100):
                self.builder.calculate_wfactors(
                    base_weather, "Kansas City Chiefs", "Buffalo Bills"
                )
            wfactor_time = time.time() - start

            self.test(
                "W-Factor calculation speed (<100ms for 100 iterations)",
                wfactor_time < 0.1,
                f"Time: {wfactor_time * 1000:.1f}ms",
            )

            # Team suitability speed
            start = time.time()
            for _ in range(100):
                self.builder.assess_team_weather_suitability(
                    "Miami Dolphins", base_weather
                )
            suitability_time = time.time() - start

            self.test(
                "Team suitability speed (<100ms for 100 iterations)",
                suitability_time < 0.1,
                f"Time: {suitability_time * 1000:.1f}ms",
            )
        except Exception as e:
            self.test("Performance validation", False, str(e))

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"\nTests Run: {self.tests_run}")
        print(f"Passed: {self.passed} ✓")
        print(f"Failed: {self.failed} ✗")

        if self.failed == 0:
            print("\n✓ ALL VALIDATIONS PASSED!")
            print("✓ Weather Context Builder is PRODUCTION-READY")
            return 0
        else:
            print(f"\n✗ {self.failed} VALIDATION(S) FAILED")
            print("✗ Review failures above and fix before production")
            return 1


# ===== MAIN =====

if __name__ == "__main__":
    print("\nStarting Weather Context Builder Validation...")
    print("=" * 80)

    validator = WeatherBuilderValidator()
    exit_code = validator.run_all()

    sys.exit(exit_code)
