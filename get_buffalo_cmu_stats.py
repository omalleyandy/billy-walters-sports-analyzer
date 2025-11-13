#!/usr/bin/env python3
"""Get Buffalo and Central Michigan team statistics from ESPN API"""

import sys
sys.path.insert(0, 'src')

from data.espn_api_client import ESPNAPIClient

client = ESPNAPIClient()

print("=" * 70)
print("BUFFALO @ CENTRAL MICHIGAN - TEAM STATISTICS")
print("=" * 70)

# Buffalo (ID: 2084)
print("\n[*] Fetching Buffalo Bulls (ID: 2084)...")
try:
    buf_metrics = client.extract_power_rating_metrics(2084, 'college-football')

    print("\n" + "=" * 70)
    print("BUFFALO BULLS")
    print("=" * 70)
    print(f"Points Per Game:          {buf_metrics.get('points_per_game', 'N/A'):.1f}")
    print(f"Total Yards/Game:         {buf_metrics.get('total_yards_per_game', 'N/A'):.1f}")
    print(f"Passing Yards/Game:       {buf_metrics.get('passing_yards_per_game', 'N/A'):.1f}")
    print(f"Rushing Yards/Game:       {buf_metrics.get('rushing_yards_per_game', 'N/A'):.1f}")
    print(f"Points Allowed/Game:      {buf_metrics.get('points_allowed_per_game', 'N/A'):.1f}")
    print(f"Yards Allowed/Game:       {buf_metrics.get('total_yards_allowed_per_game', 'N/A'):.1f}")
    print(f"Turnover Margin:          {buf_metrics.get('turnover_margin', 'N/A'):+.0f}")
    print(f"Third Down %:             {buf_metrics.get('third_down_pct', 'N/A'):.1f}%")

    buf_success = True
except Exception as e:
    print(f"[ERROR] Failed to fetch Buffalo stats: {e}")
    buf_success = False

# Central Michigan (ID: 2117)
print("\n[*] Fetching Central Michigan Chippewas (ID: 2117)...")
try:
    cmu_metrics = client.extract_power_rating_metrics(2117, 'college-football')

    print("\n" + "=" * 70)
    print("CENTRAL MICHIGAN CHIPPEWAS")
    print("=" * 70)
    print(f"Points Per Game:          {cmu_metrics.get('points_per_game', 'N/A'):.1f}")
    print(f"Total Yards/Game:         {cmu_metrics.get('total_yards_per_game', 'N/A'):.1f}")
    print(f"Passing Yards/Game:       {cmu_metrics.get('passing_yards_per_game', 'N/A'):.1f}")
    print(f"Rushing Yards/Game:       {cmu_metrics.get('rushing_yards_per_game', 'N/A'):.1f}")
    print(f"Points Allowed/Game:      {cmu_metrics.get('points_allowed_per_game', 'N/A'):.1f}")
    print(f"Yards Allowed/Game:       {cmu_metrics.get('total_yards_allowed_per_game', 'N/A'):.1f}")
    print(f"Turnover Margin:          {cmu_metrics.get('turnover_margin', 'N/A'):+.0f}")
    print(f"Third Down %:             {cmu_metrics.get('third_down_pct', 'N/A'):.1f}%")

    cmu_success = True
except Exception as e:
    print(f"[ERROR] Failed to fetch CMU stats: {e}")
    cmu_success = False

# Matchup Analysis
if buf_success and cmu_success:
    print("\n" + "=" * 70)
    print("MATCHUP ANALYSIS")
    print("=" * 70)

    buf_ppg = buf_metrics['points_per_game']
    cmu_ppg = cmu_metrics['points_per_game']
    buf_papg = buf_metrics['points_allowed_per_game']
    cmu_papg = cmu_metrics['points_allowed_per_game']

    print(f"\nOffense vs Defense:")
    print(f"  Buffalo Offense ({buf_ppg:.1f} PPG) vs CMU Defense ({cmu_papg:.1f} PA/G)")
    print(f"  CMU Offense ({cmu_ppg:.1f} PPG) vs Buffalo Defense ({buf_papg:.1f} PA/G)")

    # Predicted total
    predicted_total = (buf_ppg + cmu_ppg + buf_papg + cmu_papg) / 2
    print(f"\nPredicted Total: {predicted_total:.1f}")
    print(f"Market Total: 45.0")
    print(f"Edge: {predicted_total - 45.0:+.1f} points")

    # Point differential (Buffalo is road team)
    buf_net = buf_ppg - buf_papg
    cmu_net = cmu_ppg - cmu_papg
    predicted_spread = (buf_net - cmu_net) / 2 - 3  # Road team disadvantage

    print(f"\nPredicted Spread: Buffalo {predicted_spread:+.1f}")
    print(f"Market Spread: Buffalo +2.0")
    print(f"Edge: {abs(predicted_spread) - 2.0:+.1f} points")

    # Efficiency comparison
    print(f"\nTeam Efficiency:")
    print(f"  Buffalo Net: {buf_net:+.1f} points/game")
    print(f"  CMU Net: {cmu_net:+.1f} points/game")
    print(f"  Turnover Margin: Buffalo {buf_metrics['turnover_margin']:+.0f} vs CMU {cmu_metrics['turnover_margin']:+.0f}")
else:
    print("\n[WARNING] Could not complete matchup analysis due to missing data")
