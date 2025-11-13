#!/usr/bin/env python3
"""Get Northern Illinois and UMass team statistics from ESPN API"""

import sys
sys.path.insert(0, 'src')

from data.espn_api_client import ESPNAPIClient

client = ESPNAPIClient()

print("=" * 70)
print("NORTHERN ILLINOIS @ MASSACHUSETTS - TEAM STATISTICS")
print("=" * 70)

# Northern Illinois (ID: 2459)
print("\n[*] Fetching Northern Illinois Huskies (ID: 2459)...")
try:
    niu_metrics = client.extract_power_rating_metrics(2459, 'college-football')

    print("\n" + "=" * 70)
    print("NORTHERN ILLINOIS HUSKIES")
    print("=" * 70)
    print(f"Points Per Game:          {niu_metrics.get('points_per_game', 'N/A'):.1f}")
    print(f"Total Yards/Game:         {niu_metrics.get('total_yards_per_game', 'N/A'):.1f}")
    print(f"Passing Yards/Game:       {niu_metrics.get('passing_yards_per_game', 'N/A'):.1f}")
    print(f"Rushing Yards/Game:       {niu_metrics.get('rushing_yards_per_game', 'N/A'):.1f}")
    print(f"Points Allowed/Game:      {niu_metrics.get('points_allowed_per_game', 'N/A'):.1f}")
    print(f"Yards Allowed/Game:       {niu_metrics.get('total_yards_allowed_per_game', 'N/A'):.1f}")
    print(f"Turnover Margin:          {niu_metrics.get('turnover_margin', 'N/A'):+.0f}")
    print(f"Third Down %:             {niu_metrics.get('third_down_pct', 'N/A'):.1f}%")

    niu_success = True
except Exception as e:
    print(f"[ERROR] Failed to fetch NIU stats: {e}")
    niu_success = False

# Massachusetts (ID: 113)
print("\n[*] Fetching Massachusetts Minutemen (ID: 113)...")
try:
    umass_metrics = client.extract_power_rating_metrics(113, 'college-football')

    print("\n" + "=" * 70)
    print("MASSACHUSETTS MINUTEMEN")
    print("=" * 70)
    print(f"Points Per Game:          {umass_metrics.get('points_per_game', 'N/A'):.1f}")
    print(f"Total Yards/Game:         {umass_metrics.get('total_yards_per_game', 'N/A'):.1f}")
    print(f"Passing Yards/Game:       {umass_metrics.get('passing_yards_per_game', 'N/A'):.1f}")
    print(f"Rushing Yards/Game:       {umass_metrics.get('rushing_yards_per_game', 'N/A'):.1f}")
    print(f"Points Allowed/Game:      {umass_metrics.get('points_allowed_per_game', 'N/A'):.1f}")
    print(f"Yards Allowed/Game:       {umass_metrics.get('total_yards_allowed_per_game', 'N/A'):.1f}")
    print(f"Turnover Margin:          {umass_metrics.get('turnover_margin', 'N/A'):+.0f}")
    print(f"Third Down %:             {umass_metrics.get('third_down_pct', 'N/A'):.1f}%")

    umass_success = True
except Exception as e:
    print(f"[ERROR] Failed to fetch UMass stats: {e}")
    umass_success = False

# Matchup Analysis
if niu_success and umass_success:
    print("\n" + "=" * 70)
    print("MATCHUP ANALYSIS")
    print("=" * 70)

    niu_ppg = niu_metrics['points_per_game']
    umass_ppg = umass_metrics['points_per_game']
    niu_papg = niu_metrics['points_allowed_per_game']
    umass_papg = umass_metrics['points_allowed_per_game']

    print(f"\nOffense vs Defense:")
    print(f"  NIU Offense ({niu_ppg:.1f} PPG) vs UMass Defense ({umass_papg:.1f} PA/G)")
    print(f"  UMass Offense ({umass_ppg:.1f} PPG) vs NIU Defense ({niu_papg:.1f} PA/G)")

    # Predicted total
    predicted_total = (niu_ppg + umass_ppg + niu_papg + umass_papg) / 2
    print(f"\nPredicted Total: {predicted_total:.1f}")
    print(f"Market Total: 43.0")
    print(f"Edge: {predicted_total - 43.0:+.1f} points")

    # Point differential
    niu_net = niu_ppg - niu_papg
    umass_net = umass_ppg - umass_papg
    predicted_spread = (niu_net - umass_net) / 2 - 3  # Road adjustment

    print(f"\nPredicted Spread: NIU {predicted_spread:+.1f}")
    print(f"Market Spread: NIU -9.0")
    print(f"Edge: {abs(predicted_spread) - 9.0:+.1f} points")
else:
    print("\n[WARNING] Could not complete matchup analysis due to missing data")
