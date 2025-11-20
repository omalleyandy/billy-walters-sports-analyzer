"""
NCAAF Edge Detection Script

Quick implementation of Billy Walters edge detection for NCAA College Football.
Uses existing power ratings and odds data with NCAAF-specific adjustments.

Usage:
    uv run python scripts/analyze_ncaaf_edges.py
    uv run python scripts/analyze_ncaaf_edges.py --min-edge 2.0
    uv run python scripts/analyze_ncaaf_edges.py --game-ids 303 304
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class NCAAFEdgeDetector:
    """
    NCAAF Edge Detection using Billy Walters methodology.

    Key differences from NFL:
    - Home Field Advantage: 3.5 points (vs NFL 2.5)
    - Power rating scale: ~60-90 (vs NFL 70-100)
    - Conference factors more important
    - Injury data less reliable
    """

    # NCAAF-specific constants
    HFA = 3.5  # Home field advantage (higher than NFL)
    MIN_EDGE = 1.5  # Minimum edge for a play (same as NFL)

    # Billy Walters edge thresholds (same as NFL)
    THRESHOLDS = {
        "MAX": 7.0,  # 5% Kelly, 77% win rate
        "STRONG": 4.0,  # 3% Kelly, 64% win rate
        "MODERATE": 2.0,  # 2% Kelly, 58% win rate
        "LEAN": 1.5,  # 1% Kelly, 54% win rate
    }

    def __init__(self):
        """Initialize edge detector."""
        self.power_ratings: Dict[str, float] = {}
        self.games: List[Dict] = []
        self.team_mapping: Dict[str, str] = {}
        self._load_team_mapping()

    def _load_team_mapping(self):
        """Load team name mapping from Overtime.ag to Massey format."""
        mapping_file = (
            Path(__file__).parent.parent / "src/data/ncaaf_team_name_mapping.json"
        )

        try:
            with open(mapping_file) as f:
                data = json.load(f)
                self.team_mapping = data["overtime_to_massey"]
            print(f"[OK] Loaded {len(self.team_mapping)} team name mappings")
        except FileNotFoundError:
            print(f"[WARNING] Team mapping file not found: {mapping_file}")
            print("[WARNING] Using direct team names (may result in mismatches)")

    def _normalize_team_name(self, overtime_name: str) -> str:
        """
        Normalize Overtime.ag team name to Massey format.

        Args:
            overtime_name: Team name from Overtime.ag

        Returns:
            Normalized team name for Massey ratings lookup
        """
        return self.team_mapping.get(overtime_name, overtime_name)

    def load_power_ratings(self, filepath: Path) -> int:
        """
        Load Massey power ratings for NCAAF.

        Args:
            filepath: Path to ratings JSON file

        Returns:
            Number of teams loaded
        """
        with open(filepath) as f:
            data = json.load(f)

        for team in data["teams"]:
            team_name = team["team"]
            power_rating = float(team["powerRating"])
            self.power_ratings[team_name] = power_rating

        print(f"[OK] Loaded {len(self.power_ratings)} NCAAF power ratings")
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
        print(f"[OK] Loaded {len(self.games)} NCAAF games")
        return len(self.games)

    def calculate_predicted_line(
        self, home_team: str, away_team: str
    ) -> Optional[float]:
        """
        Calculate predicted spread using power ratings.

        Formula: (Home Rating - Away Rating) + HFA

        Args:
            home_team: Home team name (Overtime.ag format)
            away_team: Away team name (Overtime.ag format)

        Returns:
            Predicted spread (negative = home favored) or None if ratings missing
        """
        # Normalize team names to Massey format
        home_normalized = self._normalize_team_name(home_team)
        away_normalized = self._normalize_team_name(away_team)

        home_rating = self.power_ratings.get(home_normalized)
        away_rating = self.power_ratings.get(away_normalized)

        if home_rating is None or away_rating is None:
            return None

        # Power rating differential
        diff = home_rating - away_rating

        # Add home field advantage
        predicted = diff + self.HFA

        return -predicted  # Negative = home favored

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

    def detect_edges(
        self, min_edge: float = MIN_EDGE, game_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Detect betting edges across all games.

        Args:
            min_edge: Minimum edge size to report (default 1.5)
            game_ids: Optional list of rotation numbers to filter (e.g., [303, 304])

        Returns:
            List of games with detected edges
        """
        edges = []

        for game in self.games:
            # Filter by rotation numbers if specified
            if game_ids is not None:
                rot_nums = game.get("rotation_numbers", {})
                team1 = rot_nums.get("team1")
                team2 = rot_nums.get("team2")
                if team1 not in game_ids and team2 not in game_ids:
                    continue

            home_team = game["home_team"]
            away_team = game["away_team"]

            # Calculate predicted line
            predicted = self.calculate_predicted_line(home_team, away_team)

            if predicted is None:
                print(f"[WARNING] Missing power ratings for {away_team} @ {home_team}")
                continue

            # Get market line
            market_spread = game["spread"]["home"]

            # Calculate edge
            edge = predicted - market_spread

            # Only report if meets minimum threshold
            if abs(edge) < min_edge:
                continue

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

            edges.append(
                {
                    "game_id": game["game_id"],
                    "away_team": away_team,
                    "home_team": home_team,
                    "game_time": game["game_time"],
                    "predicted_line": round(predicted, 1),
                    "market_line": market_spread,
                    "edge": round(edge, 1),
                    "edge_abs": round(abs(edge), 1),
                    "classification": classification,
                    "kelly_pct": kelly_pct,
                    "win_rate": win_rate,
                    "recommendation": recommendation,
                    "rotation_numbers": game.get("rotation_numbers", {}),
                    "total": game["total"]["points"],
                }
            )

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
        lines.append("BILLY WALTERS NCAAF EDGE DETECTION REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")

        if not edges:
            lines.append("[INFO] No edges detected meeting minimum threshold")
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
                    lines.append(f"Total: {edge['total']}")
                    lines.append("")

        lines.append("=" * 80)
        lines.append("BILLY WALTERS METHODOLOGY")
        lines.append("=" * 80)
        lines.append(f"Home Field Advantage: {self.HFA} points (higher than NFL 2.5)")
        lines.append(f"Minimum Edge: {self.MIN_EDGE} points")
        lines.append("")
        lines.append("Edge Thresholds:")
        lines.append("  MAX BET (7+ pts): 5% Kelly, 77% historical win rate")
        lines.append("  STRONG (4-7 pts): 3% Kelly, 64% historical win rate")
        lines.append("  MODERATE (2-4 pts): 2% Kelly, 58% historical win rate")
        lines.append("  LEAN (1.5-2 pts): 1% Kelly, 54% historical win rate")
        lines.append("")
        lines.append("Success Metric: Closing Line Value (CLV), not win/loss %")
        lines.append("Target CLV: +1.5 points average (professional threshold)")
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
                "league": "NCAAF",
                "generated_at": datetime.now().isoformat(),
                "hfa": self.HFA,
                "min_edge": self.MIN_EDGE,
                "edges_found": len(edges),
            },
            "edges": edges,
        }

        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)

        print(f"[OK] Edges saved to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="NCAAF Edge Detection using Billy Walters methodology"
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=1.5,
        help="Minimum edge size to report (default: 1.5)",
    )
    parser.add_argument(
        "--game-ids",
        type=int,
        nargs="+",
        help="Filter by rotation numbers (e.g., 303 304)",
    )
    parser.add_argument(
        "--power-ratings",
        type=Path,
        help="Path to power ratings file (default: latest in output/massey/)",
    )
    parser.add_argument(
        "--odds",
        type=Path,
        help="Path to odds file (default: latest in output/overtime/ncaaf/pregame/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/edge_detection/ncaaf_edges.txt"),
        help="Output file for report",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("output/edge_detection/ncaaf_edges.json"),
        help="Output file for JSON",
    )

    args = parser.parse_args()

    # Find latest files if not specified
    if args.power_ratings is None:
        massey_dir = Path("output/massey")
        ncaaf_files = sorted(massey_dir.glob("ncaaf_ratings_*.json"), reverse=True)
        if not ncaaf_files:
            print("[ERROR] No NCAAF power ratings found in output/massey/")
            return 1
        args.power_ratings = ncaaf_files[0]

    if args.odds is None:
        odds_dir = Path("output/overtime/ncaaf/pregame")
        odds_files = sorted(odds_dir.glob("api_walters_*.json"), reverse=True)
        if not odds_files:
            print("[ERROR] No NCAAF odds found in output/overtime/ncaaf/pregame/")
            return 1
        args.odds = odds_files[0]

    print("[*] NCAAF Edge Detection")
    print(f"    Power Ratings: {args.power_ratings}")
    print(f"    Odds: {args.odds}")
    print(f"    Minimum Edge: {args.min_edge}")
    if args.game_ids:
        print(f"    Filter: Rotation numbers {args.game_ids}")
    print()

    # Initialize detector
    detector = NCAAFEdgeDetector()

    # Load data
    detector.load_power_ratings(args.power_ratings)
    detector.load_odds(args.odds)
    print()

    # Detect edges
    edges = detector.detect_edges(min_edge=args.min_edge, game_ids=args.game_ids)

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
