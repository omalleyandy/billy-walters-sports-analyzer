"""
NFL Edge Detection Script

Applies Billy Walters methodology with three key fixes:
1. HFA = 2.0 (Billy Walters' current value)
2. Market respect threshold (skip edges >10 pts)
3. Bias correction (0.85x favorites, 1.15x underdogs)

Usage:
    uv run python scripts/analysis/analyze_nfl_edges.py
    uv run python scripts/analysis/analyze_nfl_edges.py --min-edge 3.5
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class NFLEdgeDetector:
    """
    NFL Edge Detection using Billy Walters methodology with fixes.

    Key differences from NCAAF:
    - Home Field Advantage: 2.0 points (vs NCAAF 2.5)
    - Min Edge: 3.5 points (vs NCAAF 1.5) - NFL market is more efficient
    - Key Numbers: 3, 7, 6, 10, 14 (critical for NFL)
    """

    # NFL-specific constants (Billy Walters methodology)
    HFA = 2.0  # Billy Walters uses 2.0 for NFL (recent <1.0 with COVID)
    MIN_EDGE = 3.5  # Higher threshold for efficient NFL market
    MARKET_RESPECT_THRESHOLD = 10.0  # FIX 2: Skip edges >10 pts

    # Billy Walters edge thresholds
    THRESHOLDS = {
        "MAX": 7.0,  # 5% Kelly, 77% win rate
        "STRONG": 4.0,  # 3% Kelly, 64% win rate
        "MODERATE": 2.0,  # 2% Kelly, 58% win rate
        "LEAN": 1.5,  # 1% Kelly, 54% win rate
    }

    # NFL key numbers (in order of importance)
    KEY_NUMBERS = [3, 7, 6, 10, 14]

    def __init__(self):
        """Initialize edge detector."""
        self.power_ratings: Dict[str, float] = {}
        self.games: List[Dict] = []

        # NFL team name mapping (Overtime full names → Massey city names)
        self.team_mapping = {
            "Arizona Cardinals": "Arizona",
            "Atlanta Falcons": "Atlanta",
            "Baltimore Ravens": "Baltimore",
            "Buffalo Bills": "Buffalo",
            "Carolina Panthers": "Carolina",
            "Chicago Bears": "Chicago",
            "Cincinnati Bengals": "Cincinnati",
            "Cleveland Browns": "Cleveland",
            "Dallas Cowboys": "Dallas",
            "Denver Broncos": "Denver",
            "Detroit Lions": "Detroit",
            "Green Bay Packers": "Green Bay",
            "Houston Texans": "Houston",
            "Indianapolis Colts": "Indianapolis",
            "Jacksonville Jaguars": "Jacksonville",
            "Kansas City Chiefs": "Kansas City",
            "Las Vegas Raiders": "Las Vegas",
            "Los Angeles Chargers": "LA Chargers",
            "Los Angeles Rams": "LA Rams",
            "Miami Dolphins": "Miami",
            "Minnesota Vikings": "Minnesota",
            "New England Patriots": "New England",
            "New Orleans Saints": "New Orleans",
            "New York Giants": "NY Giants",
            "New York Jets": "NY Jets",
            "Philadelphia Eagles": "Philadelphia",
            "Pittsburgh Steelers": "Pittsburgh",
            "San Francisco 49ers": "San Francisco",
            "Seattle Seahawks": "Seattle",
            "Tampa Bay Buccaneers": "Tampa Bay",
            "Tennessee Titans": "Tennessee",
            "Washington Commanders": "Washington",
        }

    def normalize_team_name(self, overtime_name: str) -> str:
        """Convert Overtime full name to Massey city name."""
        return self.team_mapping.get(overtime_name, overtime_name)

    def load_power_ratings(self, filepath: Path) -> int:
        """
        Load Massey power ratings for NFL.

        Args:
            filepath: Path to ratings JSON file

        Returns:
            Number of teams loaded
        """
        with open(filepath) as f:
            data = json.load(f)

        for team in data["teams"]:
            team_name = team["team"]
            power_rating = float(team["rating"]) if team["rating"] else 70.0
            self.power_ratings[team_name] = power_rating

        print(f"[OK] Loaded {len(self.power_ratings)} NFL power ratings")
        return len(self.power_ratings)

    def load_odds(self, filepath: Path) -> int:
        """
        Load odds from Overtime.ag (Billy Walters format).

        Args:
            filepath: Path to odds JSON file

        Returns:
            Number of games loaded
        """
        with open(filepath) as f:
            data = json.load(f)

        self.games = data["games"]
        print(f"[OK] Loaded {len(self.games)} NFL games")
        return len(self.games)

    def calculate_predicted_line(
        self, home_team: str, away_team: str
    ) -> Optional[float]:
        """
        Calculate predicted spread using power ratings.

        Formula: (Home Rating - Away Rating) + HFA

        Args:
            home_team: Home team name (Overtime format)
            away_team: Away team name (Overtime format)

        Returns:
            Predicted spread (negative = home favored) or None if ratings missing
        """
        # Normalize team names to Massey format
        home_normalized = self.normalize_team_name(home_team)
        away_normalized = self.normalize_team_name(away_team)

        home_rating = self.power_ratings.get(home_normalized)
        away_rating = self.power_ratings.get(away_normalized)

        if home_rating is None or away_rating is None:
            return None

        # Power rating differential
        diff = home_rating - away_rating

        # Add home field advantage (FIX 1: Using 2.0 not 2.5)
        predicted = diff + self.HFA

        return -predicted  # Negative = home favored

    def apply_bias_correction(self, predicted: float, market: float) -> float:
        """
        FIX 3: Apply systematic bias correction for favorites/underdogs

        Analysis shows favorites overestimated by ~2.4 pts
        Apply 15% haircut to favorites, 15% boost to underdogs

        Args:
            predicted: Our predicted spread
            market: Market spread

        Returns:
            Corrected predicted spread
        """
        betting_favorite = (predicted > market and predicted < 0) or (
            predicted < market and predicted > 0
        )

        if betting_favorite:
            # We think favorite should be favored by more than market
            # Apply 15% haircut to favorite's strength
            return predicted * 0.85
        else:
            # We think underdog is undervalued
            # Apply 15% boost to underdog's strength
            return predicted * 1.15

    def check_key_number_crossing(
        self, predicted: float, market: float
    ) -> tuple[bool, Optional[int]]:
        """
        Check if prediction crosses a key number vs market.

        Key numbers in NFL (importance order): 3, 7, 6, 10, 14

        Returns:
            (crosses_key, key_number)
        """
        for key_num in self.KEY_NUMBERS:
            if min(predicted, market) < key_num < max(predicted, market):
                return (True, key_num)

        return (False, None)

    def classify_edge(self, edge: float) -> tuple[str, float, str]:
        """
        Classify edge size into Billy Walters categories.

        Args:
            edge: Edge size in points

        Returns:
            Tuple of (classification, kelly_pct, win_rate)
        """
        abs_edge = abs(edge)

        if abs_edge >= self.THRESHOLDS["MAX"]:
            return "MAX BET", 5.0, "77%"
        elif abs_edge >= self.THRESHOLDS["STRONG"]:
            return "STRONG", 3.0, "64%"
        elif abs_edge >= self.THRESHOLDS["MODERATE"]:
            return "MODERATE", 2.0, "58%"
        elif abs_edge >= self.THRESHOLDS["LEAN"]:
            return "LEAN", 1.0, "54%"
        else:
            return "NO PLAY", 0.0, "52%"

    def detect_edges(self, min_edge: float = MIN_EDGE) -> List[Dict]:
        """
        Detect betting edges across all NFL games.

        Args:
            min_edge: Minimum edge size to report (default 3.5 for NFL)

        Returns:
            List of games with detected edges
        """
        edges = []

        for game in self.games:
            home_team = game["home_team"]
            away_team = game["away_team"]

            # Calculate predicted line
            predicted = self.calculate_predicted_line(home_team, away_team)

            if predicted is None:
                print(f"[WARNING] Missing power ratings for {away_team} @ {home_team}")
                continue

            # Get market line
            market_spread = game["spread"]["home"]

            # FIX 3: Apply bias correction
            betting_favorite = (predicted > market_spread and predicted < 0) or (
                predicted < market_spread and predicted > 0
            )

            if betting_favorite:
                predicted_corrected = predicted * 0.85
            else:
                predicted_corrected = predicted * 1.15

            # Calculate edge (using corrected prediction)
            edge = predicted_corrected - market_spread

            # FIX 2: Market respect - skip if edge is too large
            if abs(edge) > self.MARKET_RESPECT_THRESHOLD:
                print(
                    f"[MARKET RESPECT] Skipping {away_team} @ {home_team}: "
                    f"Edge of {abs(edge):.1f} pts is too large (market likely right)"
                )
                continue

            # Only report if meets minimum threshold
            if abs(edge) < min_edge:
                continue

            # Check key number crossing
            crosses_key, key_number = self.check_key_number_crossing(
                predicted_corrected, market_spread
            )

            # Classify edge
            classification, kelly_pct, win_rate = self.classify_edge(edge)

            if classification == "NO PLAY":
                continue

            # Determine recommendation
            if edge < 0:
                # Predicted home wins by more than market
                recommendation = f"Take {home_team} {market_spread}"
            else:
                # Predicted away covers more than market
                recommendation = f"Take {away_team} +{abs(market_spread)}"

            edge_data = {
                "game_id": game["game_id"],
                "away_team": away_team,
                "home_team": home_team,
                "game_time": game["game_time"],
                "predicted_line": round(predicted_corrected, 1),
                "market_line": market_spread,
                "edge": round(edge, 1),
                "edge_abs": round(abs(edge), 1),
                "classification": classification,
                "kelly_pct": kelly_pct,
                "win_rate": win_rate,
                "recommendation": recommendation,
                "rotation_numbers": game.get("rotation_numbers", {}),
                "total": game["total"]["points"],
                "crosses_key_number": crosses_key,
                "key_number": key_number,
            }

            edges.append(edge_data)

        # Sort by absolute edge size (descending)
        edges.sort(key=lambda x: x["edge_abs"], reverse=True)

        return edges

    def print_report(self, edges: List[Dict], output_file: Optional[Path] = None):
        """
        Print formatted edge detection report.

        Args:
            edges: List of detected edges
            output_file: Optional file to write report
        """
        lines = []

        lines.append("=" * 80)
        lines.append("BILLY WALTERS NFL EDGE DETECTION REPORT - WEEK 11")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")

        if not edges:
            lines.append(
                "[INFO] No edges detected meeting minimum threshold (3.5 points)"
            )
            lines.append("[INFO] NFL market is highly efficient - this is normal")
            lines.append("")
        else:
            # Group by classification
            by_classification = {}
            for edge in edges:
                classification = edge["classification"]
                by_classification.setdefault(classification, []).append(edge)

            # Print each classification group
            for classification in ["MAX BET", "STRONG", "MODERATE", "LEAN"]:
                if classification not in by_classification:
                    continue

                games = by_classification[classification]
                lines.append(f"=== {classification} ({len(games)} games) ===")
                lines.append("")

                for edge in games:
                    lines.append(f"Game: {edge['away_team']} @ {edge['home_team']}")
                    lines.append(f"Time: {edge['game_time']}")
                    lines.append(
                        f"Rotation: {edge['rotation_numbers'].get('team1')}/{edge['rotation_numbers'].get('team2')}"
                    )
                    lines.append(
                        f"Predicted Line: {edge['home_team']} {edge['predicted_line']}"
                    )
                    lines.append(
                        f"Market Line: {edge['home_team']} {edge['market_line']}"
                    )
                    lines.append(f"Edge: {edge['edge']} points")
                    lines.append(f"Recommendation: {edge['recommendation']}")
                    lines.append(f"Kelly %: {edge['kelly_pct']}% of bankroll")
                    lines.append(f"Expected Win Rate: {edge['win_rate']}")

                    if edge["crosses_key_number"]:
                        lines.append(
                            f"[KEY NUMBER] Crosses {edge['key_number']} - EXTRA VALUE!"
                        )

                    lines.append(f"Total: {edge['total']}")
                    lines.append("")

        lines.append("=" * 80)
        lines.append("BILLY WALTERS NFL METHODOLOGY (WITH FIXES)")
        lines.append("=" * 80)
        lines.append(
            f"Home Field Advantage: {self.HFA} points (Billy Walters current value)"
        )
        lines.append(f"Minimum Edge: {self.MIN_EDGE} points (higher than NCAAF 1.5)")
        lines.append("Market Respect: Skip edges >10 points (market likely right)")
        lines.append("Bias Correction: 0.85x favorites, 1.15x underdogs")
        lines.append("")
        lines.append("Edge Thresholds:")
        lines.append("  MAX BET (7+ pts): 5% Kelly, 77% historical win rate")
        lines.append("  STRONG (4-7 pts): 3% Kelly, 64% historical win rate")
        lines.append("  MODERATE (2-4 pts): 2% Kelly, 58% historical win rate")
        lines.append("  LEAN (1.5-2 pts): 1% Kelly, 54% historical win rate")
        lines.append("")
        lines.append("NFL Key Numbers: 3 (most common), 7, 6, 10, 14")
        lines.append("Success Metric: Closing Line Value (CLV), not win/loss %")
        lines.append("Target: 52.38% win rate to break even, 53-55% for profit")
        lines.append("=" * 80)

        # Print to console
        report = "\n".join(lines)
        print(report)

        # Save to file
        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            print(f"\n[OK] Report saved to {output_file}")

    def save_json(self, edges: List[Dict], output_file: Path):
        """
        Save edges to JSON file.

        Args:
            edges: List of detected edges
            output_file: Output file path
        """
        output = {
            "metadata": {
                "league": "NFL",
                "week": 11,
                "generated_at": datetime.now().isoformat(),
                "hfa": self.HFA,
                "min_edge": self.MIN_EDGE,
                "edges_found": len(edges),
                "methodology": "Billy Walters with 3 fixes",
            },
            "edges": edges,
        }

        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)

        print(f"[OK] Edges saved to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="NFL Edge Detection using Billy Walters methodology"
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=3.5,
        help="Minimum edge size to report (default: 3.5)",
    )
    parser.add_argument(
        "--power-ratings",
        type=Path,
        help="Path to power ratings file (default: latest in output/massey/)",
    )
    parser.add_argument(
        "--odds",
        type=Path,
        help="Path to odds file (default: latest in output/overtime/nfl/pregame/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/edge_detection/nfl_edges.txt"),
        help="Output file for report",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("output/edge_detection/nfl_edges.json"),
        help="Output file for JSON",
    )

    args = parser.parse_args()

    # Find latest files if not specified
    if args.power_ratings is None:
        massey_dir = Path("output/massey")
        nfl_files = sorted(massey_dir.glob("nfl_ratings_*.json"), reverse=True)
        if not nfl_files:
            print("[ERROR] No NFL power ratings found in output/massey/")
            return 1
        args.power_ratings = nfl_files[0]

    if args.odds is None:
        odds_dir = Path("output/overtime/nfl/pregame")
        odds_files = sorted(odds_dir.glob("api_walters_*.json"), reverse=True)
        if not odds_files:
            print("[ERROR] No NFL odds found in output/overtime/nfl/pregame/")
            return 1
        args.odds = odds_files[0]

    print("[*] NFL Edge Detection - Billy Walters Methodology")
    print(f"    Power Ratings: {args.power_ratings}")
    print(f"    Odds: {args.odds}")
    print(f"    Minimum Edge: {args.min_edge}")
    print()

    # Initialize detector
    detector = NFLEdgeDetector()

    # Load data
    detector.load_power_ratings(args.power_ratings)
    detector.load_odds(args.odds)
    print()

    # Detect edges
    edges = detector.detect_edges(min_edge=args.min_edge)

    # Generate report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    detector.print_report(edges, args.output)
    print()

    # Save JSON
    args.json.parent.mkdir(parents=True, exist_ok=True)
    detector.save_json(edges, args.json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
