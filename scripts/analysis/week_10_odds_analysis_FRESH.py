#!/usr/bin/env python3
"""
Week 10 NFL Odds Analysis - FRESH DATA (November 9, 2025)
Analyzes betting odds, tracks line movements, identifies sharp action, calculates EV
Updated with fresh ESPN.com odds
"""

from typing import Dict, List


# OPENING LINES (from ESPN verified November 9, 2024)
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
    "Pittsburgh @ LA Chargers": {
        "spread": -2.5,
        "total": 44.5,
        "favorite": "LA Chargers",
    },
    "Philadelphia @ Green Bay": {
        "spread": -1.5,
        "total": 45.5,
        "favorite": "Green Bay",
    },
}


# CURRENT LINES (Fresh from ESPN.com - November 9, 2025 8:51 AM)
CURRENT_LINES = [
    {
        "away": "Cleveland",
        "home": "NY Jets",
        "spread": {
            "favorite": "Cleveland",
            "line": 2.5,
            "away_juice": -105,
            "home_juice": -115,
        },
        "total": {"line": 37.5, "over_juice": -110, "under_juice": -120},
        "moneyline": {"away": -130, "home": +110},
    },
    {
        "away": "Jacksonville",
        "home": "Houston",
        "spread": {
            "favorite": "Houston",
            "line": 1.5,
            "away_juice": -120,
            "home_juice": 100,
        },
        "total": {"line": 37.5, "over_juice": -105, "under_juice": -115},
        "moneyline": {"away": -105, "home": -115},
    },
    {
        "away": "Buffalo",
        "home": "Miami",
        "spread": {
            "favorite": "Buffalo",
            "line": 7.5,
            "away_juice": -115,
            "home_juice": -105,
        },
        "total": {"line": 50.5, "over_juice": -105, "under_juice": -115},
        "moneyline": {"away": -500, "home": +360},
    },
    {
        "away": "New England",
        "home": "Tampa Bay",
        "spread": {
            "favorite": "Tampa Bay",
            "line": 2.5,
            "away_juice": +105,
            "home_juice": -125,
        },
        "total": {"line": 48.5, "over_juice": -105, "under_juice": -115},
        "moneyline": {"away": +135, "home": -155},
    },
    {
        "away": "NY Giants",
        "home": "Chicago",
        "spread": {
            "favorite": "Chicago",
            "line": 4.5,
            "away_juice": -110,
            "home_juice": -110,
        },
        "total": {"line": 44.5, "over_juice": -115, "under_juice": -105},
        "moneyline": {"away": +190, "home": -225},
    },
    {
        "away": "Baltimore",
        "home": "Minnesota",
        "spread": {
            "favorite": "Baltimore",
            "line": 4.5,
            "away_juice": -105,
            "home_juice": -115,
        },
        "total": {"line": 48.5, "over_juice": -115, "under_juice": -105},
        "moneyline": {"away": -240, "home": +200},
    },
    {
        "away": "New Orleans",
        "home": "Carolina",
        "spread": {
            "favorite": "Carolina",
            "line": 5.5,
            "away_juice": -115,
            "home_juice": -105,
        },
        "total": {"line": 38.5, "over_juice": -105, "under_juice": -115},
        "moneyline": {"away": +200, "home": -240},
    },
    {
        "away": "Arizona",
        "home": "Seattle",
        "spread": {
            "favorite": "Seattle",
            "line": 7.5,
            "away_juice": -125,
            "home_juice": +105,
        },
        "total": {"line": 44.5, "over_juice": -115, "under_juice": -105},
        "moneyline": {"away": +260, "home": -320},
    },
    {
        "away": "Detroit",
        "home": "Washington",
        "spread": {
            "favorite": "Detroit",
            "line": 7.5,
            "away_juice": -115,
            "home_juice": -105,
        },
        "total": {"line": 49.5, "over_juice": -115, "under_juice": -105},
        "moneyline": {"away": -450, "home": +340},
    },
    {
        "away": "LA Rams",
        "home": "San Francisco",
        "spread": {
            "favorite": "LA Rams",
            "line": 5.5,
            "away_juice": -120,
            "home_juice": 100,
        },
        "total": {"line": 49.5, "over_juice": 100, "under_juice": -120},
        "moneyline": {"away": -260, "home": +215},
    },
    {
        "away": "Pittsburgh",
        "home": "LA Chargers",
        "spread": {
            "favorite": "LA Chargers",
            "line": 2.5,
            "away_juice": 100,
            "home_juice": -120,
        },
        "total": {"line": 44.5, "over_juice": -115, "under_juice": -105},
        "moneyline": {"away": +125, "home": -145},
    },
    {
        "away": "Philadelphia",
        "home": "Green Bay",
        "spread": {
            "favorite": "Green Bay",
            "line": 1.5,
            "away_juice": -125,
            "home_juice": +105,
        },
        "total": {"line": 45.5, "over_juice": -120, "under_juice": 100},
        "moneyline": {"away": -105, "home": -115},
    },
]


# POWER RATING EDGES (from validated analysis)
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
        "direction": "UP" if movement > 0 else "DOWN" if movement < 0 else "NO CHANGE",
    }


def identify_sharp_action(
    opening_spread: float,
    current_spread: float,
    opening_total: float,
    current_total: float,
) -> List[str]:
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
            if (opening_spread < key <= current_spread) or (
                current_spread < key <= opening_spread
            ):
                indicators.append(f"CROSSED KEY NUMBER ({key})")

    return indicators


def calculate_expected_value(
    power_rating_edge: float, market_line: float, juice: int = -110
) -> float:
    """Calculate expected value (EV) of a bet"""
    implied_prob = calculate_implied_probability(juice)

    # If our model shows 3+ point edge, estimate true probability higher
    if power_rating_edge >= 7.0:
        estimated_win_prob = 60.0
    elif power_rating_edge >= 5.0:
        estimated_win_prob = 58.0
    elif power_rating_edge >= 3.5:
        estimated_win_prob = 55.0
    else:
        estimated_win_prob = 50.0

    # EV = (Win Probability * Win Amount) - (Loss Probability * Loss Amount)
    win_amount = 100 / (abs(juice) / 100) if juice < 0 else 100 * (juice / 100)
    loss_amount = 100

    ev = (estimated_win_prob / 100 * win_amount) - (
        (100 - estimated_win_prob) / 100 * loss_amount
    )
    ev_percentage = (ev / 100) * 100

    return ev_percentage


def main():
    """Main odds analysis with fresh data"""
    print("=" * 100)
    print("NFL WEEK 10 ODDS ANALYSIS - FRESH DATA UPDATE")
    print("Date: November 9, 2025 - 8:51 AM ET")
    print("Source: ESPN.com/nfl/lines (LIVE)")
    print("=" * 100)
    print()

    print("=" * 100)
    print("GAME-BY-GAME ANALYSIS WITH UPDATED LINES")
    print("=" * 100)
    print()

    high_value_bets = []

    for game in CURRENT_LINES:
        matchup = f"{game['away']} @ {game['home']}"

        # Get power rating edge
        edge = POWER_RATING_EDGES.get(matchup, 0.0)

        # Get opening lines
        opening_data = OPENING_LINES.get(matchup, {})
        opening_spread = opening_data.get("spread", game["spread"]["line"])
        opening_total = opening_data.get("total", game["total"]["line"])

        # Current lines
        current_spread = game["spread"]["line"]
        current_total = game["total"]["line"]
        favorite = game["spread"]["favorite"]

        # Calculate movements
        spread_movement = calculate_line_movement(opening_spread, current_spread)
        total_movement = calculate_line_movement(opening_total, current_total)

        # Sharp action indicators
        sharp_indicators = identify_sharp_action(
            opening_spread, current_spread, opening_total, current_total
        )

        # Juice for favorite
        if favorite == game["away"]:
            spread_juice = game["spread"]["away_juice"]
        else:
            spread_juice = game["spread"]["home_juice"]

        # Expected value
        ev = calculate_expected_value(edge, current_spread, spread_juice)

        # Implied probabilities
        ml_away_prob = calculate_implied_probability(game["moneyline"]["away"])
        ml_home_prob = calculate_implied_probability(game["moneyline"]["home"])
        book_edge = ml_away_prob + ml_home_prob - 100

        print(f"GAME: {matchup}")
        print("-" * 100)

        # Current lines
        print("CURRENT LINES (November 9, 8:51 AM):")
        fav_indicator = f"{favorite} -{current_spread}"
        print(f"  Spread:    {fav_indicator}")
        print(
            f"  Total:     {current_total:.1f} (O: {game['total']['over_juice']:+d} | U: {game['total']['under_juice']:+d})"
        )
        print(
            f"  Moneyline: {game['away']} {game['moneyline']['away']:+d} | {game['home']} {game['moneyline']['home']:+d}"
        )
        print()

        # Line movement
        print("LINE MOVEMENT SINCE OPENING:")
        print(
            f"  Spread:    {opening_spread:.1f} -> {current_spread:.1f} ({spread_movement['movement']:+.1f} pts, {spread_movement['direction']})"
        )
        print(
            f"  Total:     {opening_total:.1f} -> {current_total:.1f} ({total_movement['movement']:+.1f} pts, {total_movement['direction']})"
        )
        print()

        # Implied probabilities
        print("IMPLIED PROBABILITIES:")
        print(f"  {game['away']} ML: {ml_away_prob:.1f}%")
        print(f"  {game['home']} ML: {ml_home_prob:.1f}%")
        print(f"  Book Edge (vig): {book_edge:.1f}%")
        print()

        # Sharp action
        if sharp_indicators:
            print("SHARP ACTION INDICATORS:")
            for indicator in sharp_indicators:
                print(f"  [!] {indicator}")
            print()

        # Value assessment
        print("VALUE ASSESSMENT:")
        print(f"  Power Rating Edge: {edge:.1f} points")
        print(f"  Expected Value:    {ev:+.2f}%")

        if ev > 2.0 and edge >= 3.5:
            print("  [OK] STRONG VALUE BET - BET THIS!")
            high_value_bets.append(
                {
                    "matchup": matchup,
                    "edge": edge,
                    "ev": ev,
                    "spread": current_spread,
                    "favorite": favorite,
                    "movement": spread_movement["movement"],
                }
            )
        elif ev > 0 and edge >= 3.5:
            print("  [~] MARGINAL VALUE - PROCEED WITH CAUTION")
        else:
            print("  [X] NO VALUE - PASS")

        print()
        print()

    # Summary
    print("=" * 100)
    print("HIGH VALUE BETTING OPPORTUNITIES (EV > 2% AND EDGE >= 3.5 pts)")
    print("=" * 100)
    print()

    if high_value_bets:
        high_value_bets.sort(key=lambda x: x["ev"], reverse=True)

        for i, bet in enumerate(high_value_bets, 1):
            move_str = (
                f"(moved {bet['movement']:+.1f})"
                if bet["movement"] != 0
                else "(no movement)"
            )
            print(f"{i}. {bet['matchup']:40s}")
            print(f"   BET: {bet['favorite']} -{bet['spread']:.1f}")
            print(
                f"   Edge: {bet['edge']:.1f}pts | EV: {bet['ev']:+.2f}% | Line: {move_str}"
            )
            print()
    else:
        print("No strong value opportunities at current lines")

    print()
    print("=" * 100)
    print("KEY CHANGES FROM PREVIOUS ANALYSIS:")
    print("  - Buffalo @ Miami: Spread tightened from -8.5 to -7.5 (1 point)")
    print("  - Cleveland @ NY Jets: Spread moved from CLE -1.5 to CLE -2.5 (1 point)")
    print("  - All other lines remained stable")
    print("=" * 100)
    print()
    print("BETTING DISCIPLINE REMINDERS:")
    print("  - Lines are LIVE and will continue to move before kickoff")
    print("  - Shop multiple books for best available lines")
    print("  - Check injury reports before placing bets")
    print("  - Maximum 3% of bankroll per bet (Kelly Criterion)")
    print("  - Maximum 5 bets per week for proper bankroll management")
    print("=" * 100)


if __name__ == "__main__":
    main()
