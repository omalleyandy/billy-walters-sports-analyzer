#!/usr/bin/env python3
"""
Week 10 NFL Odds Analysis - Line Movements & Value Detection
Analyzes betting odds, tracks line movements, identifies sharp action, calculates EV
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


# OPENING LINES (from initial scrape)
OPENING_LINES = {
    "Cleveland @ NY Jets": {"spread": -1.5, "total": 37.5, "favorite": "Cleveland"},
    "Jacksonville @ Houston": {"spread": -1.5, "total": 37.5, "favorite": "Houston"},
    "Buffalo @ Miami": {"spread": -8.5, "total": 50.5, "favorite": "Buffalo"},
    "New England @ Tampa Bay": {"spread": -2.5, "total": 48.5, "favorite": "Tampa Bay"},
    "NY Giants @ Chicago": {"spread": -4.5, "total": 44.5, "favorite": "Chicago"},
    "Baltimore @ Minnesota": {"spread": -4.5, "total": 48.5, "favorite": "Baltimore"},
    "New Orleans @ Carolina": {"spread": -5.5, "total": 38.5, "favorite": "Carolina"},
    "Arizona @ Seattle": {"spread": -7.5, "total": 44.5, "favorite": "Seattle"},
    "Detroit @ Washington": {"spread": -7.5, "total": 49.5, "favorite": "Detroit"},
    "LA Rams @ San Francisco": {"spread": -5.5, "total": 49.5, "favorite": "LA Rams"},
    "Pittsburgh @ LA Chargers": {"spread": -2.5, "total": 44.5, "favorite": "LA Chargers"},
    "Philadelphia @ Green Bay": {"spread": -1.5, "total": 45.5, "favorite": "Green Bay"},
}


def load_latest_odds() -> List[Dict]:
    """Load most recent odds data from overtime.ag scrape"""
    odds_file = Path("data/odds/nfl/nfl-odds-20251106-053534.json")

    if not odds_file.exists():
        print(f"[WARNING] Odds file not found: {odds_file}")
        return []

    with open(odds_file, 'r') as f:
        return json.load(f)


def normalize_team_name(name: str) -> str:
    """Normalize team names for matching"""
    mapping = {
        "Las Vegas Raiders": "Las Vegas",
        "Denver Broncos": "Denver",
        "Atlanta Falcons": "Atlanta",
        "Indianapolis Colts": "Indianapolis",
        "Cleveland Browns": "Cleveland",
        "New York Jets": "NY Jets",
        "New Orleans Saints": "New Orleans",
        "Carolina Panthers": "Carolina",
        "Buffalo Bills": "Buffalo",
        "Miami Dolphins": "Miami",
        "New England Patriots": "New England",
        "Tampa Bay Buccaneers": "Tampa Bay",
        "New York Giants": "NY Giants",
        "Chicago Bears": "Chicago",
        "Baltimore Ravens": "Baltimore",
        "Minnesota Vikings": "Minnesota",
        "Arizona Cardinals": "Arizona",
        "Seattle Seahawks": "Seattle",
        "Detroit Lions": "Detroit",
        "Washington Commanders": "Washington",
        "Los Angeles Rams": "LA Rams",
        "San Francisco 49ers": "San Francisco",
        "Pittsburgh Steelers": "Pittsburgh",
        "Los Angeles Chargers": "LA Chargers",
        "Philadelphia Eagles": "Philadelphia",
        "Green Bay Packers": "Green Bay",
        "Jacksonville Jaguars": "Jacksonville",
        "Houston Texans": "Houston",
    }
    return mapping.get(name, name)


def calculate_implied_probability(price: int) -> float:
    """Calculate implied probability from American odds"""
    if price < 0:
        return abs(price) / (abs(price) + 100) * 100
    else:
        return 100 / (price + 100) * 100


def calculate_line_movement(opening: float, current: float) -> Dict:
    """Calculate line movement metrics"""
    movement = current - opening
    pct_change = (movement / abs(opening) * 100) if opening != 0 else 0

    return {
        "movement": movement,
        "percentage": pct_change,
        "direction": "MOVED TOWARD" if movement < 0 else "MOVED AWAY FROM"
    }


def identify_sharp_action(opening_spread: float, current_spread: float,
                         opening_total: float, current_total: float) -> List[str]:
    """Identify indicators of sharp money"""
    indicators = []

    # Reverse line movement (RLM) - line moves against public perception
    spread_move = abs(current_spread - opening_spread)
    if spread_move >= 1.0:
        indicators.append(f"SIGNIFICANT SPREAD MOVE ({spread_move:.1f} pts)")

    # Steam move on totals
    total_move = abs(current_total - opening_total)
    if total_move >= 2.0:
        indicators.append(f"STEAM MOVE ON TOTAL ({total_move:.1f} pts)")

    # Key number movement (3, 7, 10 in NFL)
    key_numbers = [3.0, 7.0, 10.0]
    for key in key_numbers:
        if opening_spread != current_spread:
            if (opening_spread < key <= current_spread) or (current_spread < key <= opening_spread):
                indicators.append(f"CROSSED KEY NUMBER ({key})")

    return indicators


def calculate_expected_value(power_rating_edge: float, market_line: float,
                            juice: int = -110) -> float:
    """
    Calculate expected value (EV) of a bet

    Power rating edge: Difference between our predicted spread and market
    Market line: Current spread
    Juice: Vig/commission (default -110)
    """
    # Simplified EV calculation
    # Positive edge suggests value
    implied_prob = calculate_implied_probability(juice)

    # If our model shows 3+ point edge, estimate true probability higher
    if power_rating_edge >= 3.5:
        estimated_win_prob = 55.0  # Conservative estimate
    elif power_rating_edge >= 5.0:
        estimated_win_prob = 58.0
    elif power_rating_edge >= 7.0:
        estimated_win_prob = 60.0
    else:
        estimated_win_prob = 50.0

    # EV = (Win Probability * Win Amount) - (Loss Probability * Loss Amount)
    win_amount = 100 / (abs(juice) / 100)  # Based on $100 bet
    loss_amount = 100

    ev = (estimated_win_prob/100 * win_amount) - ((100-estimated_win_prob)/100 * loss_amount)
    ev_percentage = (ev / 100) * 100  # As percentage of bet

    return ev_percentage


def analyze_game_odds(game: Dict, power_ratings_edge: float) -> Dict:
    """Comprehensive odds analysis for a single game"""
    away = normalize_team_name(game["teams"]["away"])
    home = normalize_team_name(game["teams"]["home"])
    matchup = f"{away} @ {home}"

    # Current lines
    current_spread = game["markets"]["spread"]["home"]["line"]
    current_total = game["markets"]["total"]["over"]["line"]
    spread_juice = game["markets"]["spread"]["home"]["price"]
    total_juice = game["markets"]["total"]["over"]["price"]

    ml_away = game["markets"]["moneyline"]["away"]["price"]
    ml_home = game["markets"]["moneyline"]["home"]["price"]

    # Opening lines
    opening_data = OPENING_LINES.get(matchup, {})
    opening_spread = opening_data.get("spread", current_spread)
    opening_total = opening_data.get("total", current_total)

    # Line movement
    spread_movement = calculate_line_movement(opening_spread, abs(current_spread))
    total_movement = calculate_line_movement(opening_total, current_total)

    # Sharp action indicators
    sharp_indicators = identify_sharp_action(opening_spread, abs(current_spread),
                                            opening_total, current_total)

    # Implied probabilities
    spread_implied_prob = calculate_implied_probability(spread_juice)
    ml_away_prob = calculate_implied_probability(ml_away)
    ml_home_prob = calculate_implied_probability(ml_home)

    # Expected value
    ev = calculate_expected_value(power_ratings_edge, abs(current_spread), spread_juice)

    return {
        "matchup": matchup,
        "current_lines": {
            "spread": current_spread,
            "total": current_total,
            "ml_away": ml_away,
            "ml_home": ml_home,
        },
        "opening_lines": {
            "spread": opening_spread,
            "total": opening_total,
        },
        "line_movement": {
            "spread": spread_movement,
            "total": total_movement,
        },
        "sharp_indicators": sharp_indicators,
        "implied_probabilities": {
            "spread": spread_implied_prob,
            "ml_away": ml_away_prob,
            "ml_home": ml_home_prob,
            "total_book_edge": ml_away_prob + ml_home_prob - 100,
        },
        "expected_value": ev,
        "power_rating_edge": power_ratings_edge,
    }


def main():
    """Main odds analysis"""
    print("=" * 100)
    print("NFL WEEK 10 ODDS ANALYSIS - LINE MOVEMENTS & VALUE DETECTION")
    print("Date: November 9, 2025")
    print("=" * 100)
    print()

    # Load latest odds
    odds_data = load_latest_odds()

    if not odds_data:
        print("[ERROR] No odds data available")
        return

    print(f"[OK] Loaded {len(odds_data)} games from overtime.ag")
    print()

    # Power rating edges from validated analysis
    POWER_RATING_EDGES = {
        "Detroit @ Washington": 8.4,
        "Jacksonville @ Houston": 8.4,
        "New Orleans @ Carolina": 7.3,
        "Cleveland @ NY Jets": 6.3,
        "Baltimore @ Minnesota": 5.9,
        "LA Rams @ San Francisco": 5.9,
        "Buffalo @ Miami": 4.3,
        "NY Giants @ Chicago": 3.3,
        "New England @ Tampa Bay": 1.0,
        "Pittsburgh @ LA Chargers": 1.7,
        "Philadelphia @ Green Bay": 1.2,
        "Arizona @ Seattle": 0.3,
    }

    # Analyze each game
    print("=" * 100)
    print("GAME-BY-GAME ODDS ANALYSIS")
    print("=" * 100)
    print()

    high_value_bets = []

    for game in odds_data:
        away = normalize_team_name(game["teams"]["away"])
        home = normalize_team_name(game["teams"]["home"])
        matchup = f"{away} @ {home}"

        # Skip if not in our Week 10 list
        edge = POWER_RATING_EDGES.get(matchup)
        if edge is None:
            continue

        analysis = analyze_game_odds(game, edge)

        print(f"GAME: {analysis['matchup']}")
        print("-" * 100)

        # Current lines
        print(f"CURRENT LINES:")
        print(f"  Spread:    {analysis['current_lines']['spread']:+.1f} (juice: {game['markets']['spread']['home']['price']})")
        print(f"  Total:     {analysis['current_lines']['total']:.1f}")
        print(f"  Moneyline: {away} {analysis['current_lines']['ml_away']:+d} | {home} {analysis['current_lines']['ml_home']:+d}")
        print()

        # Line movement
        spread_move = analysis['line_movement']['spread']
        total_move = analysis['line_movement']['total']
        print(f"LINE MOVEMENT:")
        print(f"  Spread:    {analysis['opening_lines']['spread']:+.1f} -> {analysis['current_lines']['spread']:+.1f} ({spread_move['movement']:+.1f} pts)")
        print(f"  Total:     {analysis['opening_lines']['total']:.1f} -> {analysis['current_lines']['total']:.1f} ({total_move['movement']:+.1f} pts)")
        print()

        # Implied probabilities
        probs = analysis['implied_probabilities']
        print(f"IMPLIED PROBABILITIES:")
        print(f"  {away} ML: {probs['ml_away']:.1f}%")
        print(f"  {home} ML: {probs['ml_home']:.1f}%")
        print(f"  Book Edge (vig): {probs['total_book_edge']:.1f}%")
        print()

        # Sharp action
        if analysis['sharp_indicators']:
            print(f"SHARP ACTION INDICATORS:")
            for indicator in analysis['sharp_indicators']:
                print(f"  [!] {indicator}")
            print()

        # Value assessment
        print(f"VALUE ASSESSMENT:")
        print(f"  Power Rating Edge: {analysis['power_rating_edge']:.1f} points")
        print(f"  Expected Value:    {analysis['expected_value']:+.2f}%")

        if analysis['expected_value'] > 2.0:
            print(f"  [OK] POSITIVE EV - VALUE BET")
            high_value_bets.append(analysis)
        elif analysis['expected_value'] > 0:
            print(f"  [~] SLIGHT EDGE - MARGINAL VALUE")
        else:
            print(f"  [X] NEGATIVE EV - NO VALUE")

        print()
        print()

    # Summary
    print("=" * 100)
    print(f"HIGH VALUE BETTING OPPORTUNITIES (EV > 2%)")
    print("=" * 100)
    print()

    if high_value_bets:
        high_value_bets.sort(key=lambda x: x['expected_value'], reverse=True)

        for i, bet in enumerate(high_value_bets, 1):
            print(f"{i}. {bet['matchup']:40s} - Edge: {bet['power_rating_edge']:.1f}pts | EV: {bet['expected_value']:+.2f}%")
    else:
        print("No high-value opportunities identified")

    print()
    print("=" * 100)
    print("BETTING DISCIPLINE REMINDERS:")
    print("  - EV calculations are estimates based on power rating edges")
    print("  - Sharp action indicators suggest where professional money is moving")
    print("  - Key number crossings (3, 7, 10) are significant in NFL betting")
    print("  - Always verify current lines before placing bets")
    print("  - Maximum 3% of bankroll per bet (Kelly Criterion)")
    print("=" * 100)


if __name__ == "__main__":
    main()
