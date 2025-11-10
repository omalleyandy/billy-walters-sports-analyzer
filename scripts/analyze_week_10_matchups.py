#!/usr/bin/env python3
"""
Week 10 NFL Matchup Analysis
Compare Billy Walters power ratings vs market odds for spreads, moneylines, and totals
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

# Market odds from Action Network (November 9, 2025)
WEEK_10_MARKET_ODDS = [
    {
        "away": "Buffalo", "home": "Miami",
        "spread": {"line": -5.5, "favorite": "Miami"},
        "total": 45.5,
        "ml_away": +105, "ml_home": -125
    },
    {
        "away": "NY Giants", "home": "Chicago",
        "spread": {"line": -4.5, "favorite": "Chicago"},
        "total": 42.5,
        "ml_away": +110, "ml_home": -110
    },
    {
        "away": "New Orleans", "home": "Carolina",
        "spread": {"line": -5.5, "favorite": "Carolina"},
        "total": 40.5,
        "ml_away": +110, "ml_home": -130
    },
    {
        "away": "Cleveland", "home": "NY Jets",
        "spread": {"line": -2.0, "favorite": "NY Jets"},
        "total": 42.5,
        "ml_away": +110, "ml_home": -110
    },
    {
        "away": "Jacksonville", "home": "Houston",
        "spread": {"line": -1.0, "favorite": "Houston"},
        "total": 47.0,
        "ml_away": +105, "ml_home": -115
    },
    {
        "away": "New England", "home": "Tampa Bay",
        "spread": {"line": -2.5, "favorite": "Tampa Bay"},
        "total": 42.5,
        "ml_away": +105, "ml_home": -125
    },
    {
        "away": "Baltimore", "home": "Minnesota",
        "spread": {"line": +4.0, "favorite": "Minnesota"},
        "total": 48.5,
        "ml_away": +105, "ml_home": -105
    },
    {
        "away": "Arizona", "home": "Seattle",
        "spread": {"line": -7.0, "favorite": "Seattle"},
        "total": 45.0,
        "ml_away": +110, "ml_home": -110
    },
    {
        "away": "Detroit", "home": "Washington",
        "spread": {"line": -8.0, "favorite": "Washington"},
        "total": 55.5,
        "ml_away": +110, "ml_home": -110
    },
    {
        "away": "LA Rams", "home": "San Francisco",
        "spread": {"line": -5.5, "favorite": "San Francisco"},
        "total": 47.0,
        "ml_away": +110, "ml_home": -110
    },
    {
        "away": "Pittsburgh", "home": "LA Chargers",
        "spread": {"line": -2.5, "favorite": "LA Chargers"},
        "total": 43.5,
        "ml_away": +105, "ml_home": -115
    },
    {
        "away": "Philadelphia", "home": "Green Bay",
        "spread": {"line": +1.0, "favorite": "Green Bay"},
        "total": 43.5,
        "ml_away": -125, "ml_home": +105
    },
]


def load_power_ratings() -> Dict[str, float]:
    """Load Week 9 power ratings"""
    ratings_file = Path("data/power_ratings/nfl_2025_week_09.json")

    with open(ratings_file, 'r') as f:
        data = json.load(f)

    return data['ratings']


def calculate_implied_probability(american_odds: int) -> float:
    """Convert American odds to implied probability"""
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100)


def calculate_predicted_spread(away_rating: float, home_rating: float) -> float:
    """
    Calculate predicted spread using power ratings
    Positive spread = home team favored
    Negative spread = away team favored
    """
    HOME_FIELD_ADVANTAGE = 2.0

    # Predicted margin = home rating - away rating + HFA
    predicted_margin = home_rating - away_rating + HOME_FIELD_ADVANTAGE

    return predicted_margin


def calculate_spread_edge(predicted_spread: float, market_spread: float, favorite: str, home_team: str) -> Tuple[float, str]:
    """
    Calculate edge on spread bet
    Returns: (edge_magnitude, recommendation)
    """
    # Convert market spread to same format as predicted
    # Market spread is given from favorite's perspective
    if favorite == home_team:
        market_line = market_spread  # Home favored
    else:
        market_line = -market_spread  # Away favored

    # Edge = |predicted - market|
    edge = abs(predicted_spread - market_line)

    # Determine recommendation
    if predicted_spread > market_line:
        # Our model thinks home team is stronger than market suggests
        recommendation = f"BET {home_team}"
    else:
        # Our model thinks away team is stronger than market suggests
        recommendation = f"BET AWAY"

    return edge, recommendation


def analyze_moneyline_value(away_rating: float, home_rating: float, ml_away: int, ml_home: int) -> Dict:
    """Analyze moneyline betting value"""
    HOME_FIELD_ADVANTAGE = 2.0

    # Calculate win probability using power ratings
    # Simple logistic model: higher rating differential = higher win probability
    rating_diff = home_rating - away_rating + HOME_FIELD_ADVANTAGE

    # Convert rating differential to win probability (simplified)
    # Each point of differential = ~3% win probability change
    home_win_prob = 0.50 + (rating_diff * 0.03)
    home_win_prob = max(0.01, min(0.99, home_win_prob))  # Clamp between 1% and 99%

    # Market implied probabilities
    market_home_prob = calculate_implied_probability(ml_home)
    market_away_prob = calculate_implied_probability(ml_away)

    # Calculate edge (our probability - market probability)
    home_edge = (home_win_prob - market_home_prob) * 100
    away_edge = ((1 - home_win_prob) - market_away_prob) * 100

    return {
        "model_home_win%": home_win_prob * 100,
        "model_away_win%": (1 - home_win_prob) * 100,
        "market_home_win%": market_home_prob * 100,
        "market_away_win%": market_away_prob * 100,
        "home_edge%": home_edge,
        "away_edge%": away_edge,
        "recommendation": "HOME" if home_edge > 5 else ("AWAY" if away_edge > 5 else "NO BET")
    }


def main():
    """Main analysis"""
    print("=" * 100)
    print("BILLY WALTERS WEEK 10 NFL MATCHUP ANALYSIS")
    print("2025 NFL Season - Spread, Moneyline & Totals Edge Detection")
    print("=" * 100)
    print()

    # Load power ratings
    ratings = load_power_ratings()

    print("CURRENT POWER RATINGS (Week 9):")
    print("-" * 100)
    sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    for i, (team, rating) in enumerate(sorted_ratings[:10], 1):
        print(f"  {i:2d}. {team:20s} {rating:6.2f}")
    print()

    # Analyze each matchup
    print("=" * 100)
    print("WEEK 10 MATCHUP ANALYSIS")
    print("=" * 100)
    print()

    strong_spread_edges = []
    strong_ml_edges = []

    for i, game in enumerate(WEEK_10_MARKET_ODDS, 1):
        away = game['away']
        home = game['home']

        # Get ratings
        away_rating = ratings.get(away, 0.0)
        home_rating = ratings.get(home, 0.0)

        # Calculate predicted spread
        predicted_spread = calculate_predicted_spread(away_rating, home_rating)

        # Get market data
        market_spread = game['spread']['line']
        favorite = game['spread']['favorite']
        market_total = game['total']
        ml_away = game['ml_away']
        ml_home = game['ml_home']

        # Calculate edges
        spread_edge, spread_rec = calculate_spread_edge(predicted_spread, market_spread, favorite, home)
        ml_analysis = analyze_moneyline_value(away_rating, home_rating, ml_away, ml_home)

        # Print matchup header
        print(f"GAME {i}: {away} @ {home}")
        print("-" * 100)

        # Power ratings
        print(f"Power Ratings:  {away} ({away_rating:.2f}) @ {home} ({home_rating:.2f})")

        # SPREAD ANALYSIS
        print(f"\nSPREAD ANALYSIS:")
        print(f"  System Prediction: {home} by {predicted_spread:.1f}")
        print(f"  Market Line:       {favorite} -{market_spread}")
        print(f"  Edge:              {spread_edge:.1f} points")

        if spread_edge >= 3.5:
            print(f"  Recommendation:    [BET] {spread_rec} (STRONG EDGE)")
            strong_spread_edges.append({
                "game": f"{away} @ {home}",
                "edge": spread_edge,
                "rec": spread_rec
            })
        elif spread_edge >= 2.0:
            print(f"  Recommendation:    {spread_rec} (Moderate)")
        else:
            print(f"  Recommendation:    NO BET (Edge too small)")

        # MONEYLINE ANALYSIS
        print(f"\nMONEYLINE ANALYSIS:")
        print(f"  Market Odds:       {away} {ml_away:+d} / {home} {ml_home:+d}")
        print(f"  Model Win Prob:    {away} {ml_analysis['model_away_win%']:.1f}% / {home} {ml_analysis['model_home_win%']:.1f}%")
        print(f"  Market Win Prob:   {away} {ml_analysis['market_away_win%']:.1f}% / {home} {ml_analysis['market_home_win%']:.1f}%")
        print(f"  Edge:              {away} {ml_analysis['away_edge%']:+.1f}% / {home} {ml_analysis['home_edge%']:+.1f}%")

        if abs(ml_analysis['home_edge%']) > 5 or abs(ml_analysis['away_edge%']) > 5:
            if ml_analysis['home_edge%'] > 5:
                print(f"  Recommendation:    [BET] BET {home} ML (STRONG EDGE)")
                strong_ml_edges.append({
                    "game": f"{away} @ {home}",
                    "pick": f"{home} ML",
                    "edge": ml_analysis['home_edge%']
                })
            elif ml_analysis['away_edge%'] > 5:
                print(f"  Recommendation:    [BET] BET {away} ML (STRONG EDGE)")
                strong_ml_edges.append({
                    "game": f"{away} @ {home}",
                    "pick": f"{away} ML",
                    "edge": ml_analysis['away_edge%']
                })
        else:
            print(f"  Recommendation:    NO BET (Edge too small)")

        # TOTALS ANALYSIS
        print(f"\nTOTALS ANALYSIS:")
        print(f"  Market Total:      {market_total}")
        print(f"  (Note: Detailed totals analysis requires offensive/defensive ratings)")

        print()
        print("=" * 100)
        print()

    # SUMMARY
    print("=" * 100)
    print("BETTING RECOMMENDATIONS SUMMARY")
    print("=" * 100)
    print()

    print(f"STRONG SPREAD EDGES (>=3.5 points): {len(strong_spread_edges)}")
    print("-" * 100)
    if strong_spread_edges:
        for i, edge in enumerate(strong_spread_edges, 1):
            print(f"  {i}. {edge['game']:40s} - {edge['rec']:30s} ({edge['edge']:.1f} pt edge)")
    else:
        print("  None found")

    print()
    print(f"STRONG MONEYLINE EDGES (>=5% probability edge): {len(strong_ml_edges)}")
    print("-" * 100)
    if strong_ml_edges:
        for i, edge in enumerate(strong_ml_edges, 1):
            print(f"  {i}. {edge['game']:40s} - {edge['pick']:20s} ({edge['edge']:+.1f}% edge)")
    else:
        print("  None found")

    print()
    print("=" * 100)
    print("BETTING DISCIPLINE REMINDERS:")
    print("  - Maximum 5 bets per week")
    print("  - Kelly sizing: 25% fraction, max 3% per bet")
    print("  - Respect key numbers: 3, 7, 6, 10, 14")
    print("  - Check injury reports before placing bets")
    print("  - Monitor line movement for reverse action")
    print("=" * 100)


if __name__ == "__main__":
    main()
