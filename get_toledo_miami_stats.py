#!/usr/bin/env python3
"""Get Toledo and Miami (OH) team statistics from ESPN API"""

import sys

sys.path.insert(0, "src")

from data.espn_api_client import ESPNAPIClient

client = ESPNAPIClient()

print("=" * 70)
print("TOLEDO @ MIAMI (OH) - TEAM STATISTICS")
print("=" * 70)

# Toledo (ID: 2649)
print("\n[*] Fetching Toledo Rockets (ID: 2649)...")
try:
    tol_metrics = client.extract_power_rating_metrics(2649, "college-football")

    print("\n" + "=" * 70)
    print("TOLEDO ROCKETS")
    print("=" * 70)
    print(f"Points Per Game:          {tol_metrics.get('points_per_game', 'N/A'):.1f}")
    print(
        f"Total Yards/Game:         {tol_metrics.get('total_yards_per_game', 'N/A'):.1f}"
    )
    print(
        f"Passing Yards/Game:       {tol_metrics.get('passing_yards_per_game', 'N/A'):.1f}"
    )
    print(
        f"Rushing Yards/Game:       {tol_metrics.get('rushing_yards_per_game', 'N/A'):.1f}"
    )
    print(
        f"Points Allowed/Game:      {tol_metrics.get('points_allowed_per_game', 'N/A'):.1f}"
    )
    print(
        f"Yards Allowed/Game:       {tol_metrics.get('total_yards_allowed_per_game', 'N/A'):.1f}"
    )
    print(f"Turnover Margin:          {tol_metrics.get('turnover_margin', 'N/A'):+.0f}")
    print(f"Third Down %:             {tol_metrics.get('third_down_pct', 'N/A'):.1f}%")

    tol_success = True
except Exception as e:
    print(f"[ERROR] Failed to fetch Toledo stats: {e}")
    tol_success = False

# Miami (OH) (ID: 193)
print("\n[*] Fetching Miami (OH) RedHawks (ID: 193)...")
try:
    moh_metrics = client.extract_power_rating_metrics(193, "college-football")

    print("\n" + "=" * 70)
    print("MIAMI (OH) REDHAWKS")
    print("=" * 70)
    print(f"Points Per Game:          {moh_metrics.get('points_per_game', 'N/A'):.1f}")
    print(
        f"Total Yards/Game:         {moh_metrics.get('total_yards_per_game', 'N/A'):.1f}"
    )
    print(
        f"Passing Yards/Game:       {moh_metrics.get('passing_yards_per_game', 'N/A'):.1f}"
    )
    print(
        f"Rushing Yards/Game:       {moh_metrics.get('rushing_yards_per_game', 'N/A'):.1f}"
    )
    print(
        f"Points Allowed/Game:      {moh_metrics.get('points_allowed_per_game', 'N/A'):.1f}"
    )
    print(
        f"Yards Allowed/Game:       {moh_metrics.get('total_yards_allowed_per_game', 'N/A'):.1f}"
    )
    print(f"Turnover Margin:          {moh_metrics.get('turnover_margin', 'N/A'):+.0f}")
    print(f"Third Down %:             {moh_metrics.get('third_down_pct', 'N/A'):.1f}%")

    moh_success = True
except Exception as e:
    print(f"[ERROR] Failed to fetch Miami (OH) stats: {e}")
    moh_success = False

# Matchup Analysis
if tol_success and moh_success:
    print("\n" + "=" * 70)
    print("MATCHUP ANALYSIS")
    print("=" * 70)

    tol_ppg = tol_metrics["points_per_game"]
    moh_ppg = moh_metrics["points_per_game"]
    tol_papg = tol_metrics["points_allowed_per_game"]
    moh_papg = moh_metrics["points_allowed_per_game"]

    print("\nOffense vs Defense:")
    print(
        f"  Toledo Offense ({tol_ppg:.1f} PPG) vs Miami Defense ({moh_papg:.1f} PA/G)"
    )
    print(
        f"  Miami Offense ({moh_ppg:.1f} PPG) vs Toledo Defense ({tol_papg:.1f} PA/G)"
    )

    # Predicted total (BEFORE weather adjustment)
    predicted_total = (tol_ppg + moh_ppg + tol_papg + moh_papg) / 2
    print(f"\nPredicted Total (no weather): {predicted_total:.1f}")
    print("Weather Adjustment: -3.0 points (16 mph wind, 30 mph gusts)")
    print(f"Weather-Adjusted Total: {predicted_total - 3.0:.1f}")
    print("Market Total: 44.0")
    print(f"Edge: {(predicted_total - 3.0) - 44.0:+.1f} points")

    # Point differential (Toledo is road team)
    tol_net = tol_ppg - tol_papg
    moh_net = moh_ppg - moh_papg
    predicted_spread = (tol_net - moh_net) / 2 - 3  # Road team disadvantage

    print(f"\nPredicted Spread: Toledo {predicted_spread:+.1f}")
    print("Market Spread: Toledo -5.5")
    print(f"Edge: {abs(predicted_spread) - 5.5:+.1f} points")

    # Efficiency comparison
    print("\nTeam Efficiency:")
    print(f"  Toledo Net: {tol_net:+.1f} points/game")
    print(f"  Miami Net: {moh_net:+.1f} points/game")
    print(f"  Efficiency Gap: {tol_net - moh_net:+.1f} points")
    print(
        f"  Turnover Margin: Toledo {tol_metrics['turnover_margin']:+.0f} vs Miami {moh_metrics['turnover_margin']:+.0f}"
    )
else:
    print("\n[WARNING] Could not complete matchup analysis due to missing data")
