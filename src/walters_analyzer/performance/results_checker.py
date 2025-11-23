"""
Betting Results Checker
Fetches actual game scores, parses predictions, and calculates performance metrics.
"""

import json
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class GameScore:
    """Actual game score data"""

    game_id: str
    matchup: str
    away_team: str
    home_team: str
    away_score: int
    home_score: int
    status: str  # 'Final', 'In Progress', 'Scheduled'
    game_time: str


@dataclass
class Prediction:
    """Edge detection prediction with recommended bet"""

    game_id: str
    matchup: str
    week: int
    away_team: str
    home_team: str
    predicted_spread: float
    market_spread: float
    market_total: float
    recommended_bet: str  # 'away', 'home', or None
    kelly_fraction: float
    confidence_score: float
    timestamp: str


@dataclass
class GameResult:
    """Combined prediction + actual result"""

    prediction: Prediction
    score: GameScore
    ats_result: Optional[str]  # 'WIN', 'LOSS', 'PUSH'
    ats_margin: float
    profit_loss: float
    roi: float
    margin_error: int


class BettingResultsChecker:
    """Check betting predictions against actual game results"""

    def __init__(self):
        """Initialize results checker"""
        self.client = httpx.Client(timeout=30)
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football"
        self.client.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            }
        )
        self.games: Dict[str, GameScore] = {}
        self.predictions: Dict[str, Prediction] = {}
        self.results: List[GameResult] = []

    def close(self) -> None:
        """Close HTTP client"""
        self.client.close()

    def fetch_nfl_scores(
        self, week: Optional[int] = None, season: int = 2025
    ) -> List[GameScore]:
        """
        Fetch NFL game scores from ESPN API.

        Args:
            week: NFL week number (auto-detect if None)
            season: NFL season year (default: 2025)

        Returns:
            List of GameScore objects
        """
        try:
            url = f"{self.base_url}/nfl/scoreboard"
            if week:
                url += f"?week={week}"

            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()

            scores = []
            for event in data.get("events", []):
                try:
                    competition = event.get("competitions", [{}])[0]
                    competitors = competition.get("competitors", [])

                    if len(competitors) < 2:
                        continue

                    # ESPN API has home first, away second
                    home = competitors[0]
                    away = competitors[1]

                    away_loc = away["team"].get("location", "")
                    home_loc = home["team"].get("location", "")

                    # Extract status properly
                    status_dict = competition.get("status", {})
                    if isinstance(status_dict, dict):
                        status_type = status_dict.get("description", "Scheduled")
                    else:
                        status_type = status_dict.get("type", "Scheduled")

                    score = GameScore(
                        game_id=f"{away_loc}_{home_loc}",
                        matchup=(
                            f"{away['team']['displayName']} @ "
                            f"{home['team']['displayName']}"
                        ),
                        away_team=away["team"]["displayName"],
                        home_team=home["team"]["displayName"],
                        away_score=int(away.get("score", 0)),
                        home_score=int(home.get("score", 0)),
                        status=status_type,
                        game_time=event.get("date", ""),
                    )
                    scores.append(score)
                    self.games[score.game_id] = score
                except (KeyError, ValueError, IndexError) as e:
                    print(f"[WARNING] Failed to parse game: {e}")
                    continue

            return scores

        except httpx.RequestError as e:
            print(f"[ERROR] Failed to fetch NFL scores: {e}")
            return []

    def fetch_ncaaf_scores(
        self, week: Optional[int] = None, season: int = 2025
    ) -> List[GameScore]:
        """
        Fetch NCAAF game scores from ESPN API.

        Args:
            week: NCAAF week number
            season: NCAAF season year (default: 2025)

        Returns:
            List of GameScore objects
        """
        try:
            url = f"{self.base_url}/college-football/scoreboard"
            if week:
                url += f"?week={week}"

            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()

            scores = []
            for event in data.get("events", []):
                try:
                    competition = event.get("competitions", [{}])[0]
                    competitors = competition.get("competitors", [])

                    if len(competitors) < 2:
                        continue

                    # ESPN API has home first, away second
                    home = competitors[0]
                    away = competitors[1]

                    away_loc = away["team"].get("location", "")
                    home_loc = home["team"].get("location", "")

                    # Extract status properly
                    status_dict = competition.get("status", {})
                    if isinstance(status_dict, dict):
                        status_type = status_dict.get("description", "Scheduled")
                    else:
                        status_type = status_dict.get("type", "Scheduled")

                    score = GameScore(
                        game_id=f"{away_loc}_{home_loc}",
                        matchup=(
                            f"{away['team']['displayName']} @ "
                            f"{home['team']['displayName']}"
                        ),
                        away_team=away["team"]["displayName"],
                        home_team=home["team"]["displayName"],
                        away_score=int(away.get("score", 0)),
                        home_score=int(home.get("score", 0)),
                        status=status_type,
                        game_time=event.get("date", ""),
                    )
                    scores.append(score)
                    self.games[score.game_id] = score
                except (KeyError, ValueError, IndexError) as e:
                    print(f"[WARNING] Failed to parse game: {e}")
                    continue

            return scores

        except httpx.RequestError as e:
            print(f"[ERROR] Failed to fetch NCAAF scores: {e}")
            return []

    def load_predictions(self, edge_file: Path) -> List[Prediction]:
        """
        Load edge detection predictions from JSONL file.

        Args:
            edge_file: Path to edge_detection JSONL file

        Returns:
            List of Prediction objects
        """
        predictions = []

        if not edge_file.exists():
            print(f"[WARNING] Predictions file not found: {edge_file}")
            return predictions

        try:
            with open(edge_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        pred = Prediction(
                            game_id=data.get("game_id", ""),
                            matchup=data.get("matchup", ""),
                            week=data.get("week", 0),
                            away_team=data.get("away_team", ""),
                            home_team=data.get("home_team", ""),
                            predicted_spread=float(data.get("predicted_spread", 0)),
                            market_spread=float(data.get("market_spread", 0)),
                            market_total=float(data.get("market_total", 0)),
                            recommended_bet=data.get("recommended_bet", None),
                            kelly_fraction=float(data.get("kelly_fraction", 0)),
                            confidence_score=float(data.get("confidence_score", 0)),
                            timestamp=data.get("timestamp", ""),
                        )
                        predictions.append(pred)
                        self.predictions[pred.game_id] = pred
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"[WARNING] Failed to parse line {line_num}: {e}")
                        continue

            print(f"[OK] Loaded {len(predictions)} predictions")
            return predictions

        except IOError as e:
            print(f"[ERROR] Failed to read predictions file: {e}")
            return []

    def calculate_ats(
        self, pred: Prediction, score: GameScore
    ) -> Tuple[Optional[str], float]:
        """
        Calculate ATS (Against The Spread) result.

        Args:
            pred: Prediction object
            score: Actual game score

        Returns:
            (result: 'WIN'/'LOSS'/'PUSH', margin_error: float)
        """
        actual_margin = score.away_score - score.home_score

        if pred.recommended_bet == "away":
            # Away side: cover if actual_margin + spread > 0
            ats_line = actual_margin + pred.market_spread
            if ats_line > 0:
                result = "WIN"
            elif ats_line < 0:
                result = "LOSS"
            else:
                result = "PUSH"
        elif pred.recommended_bet == "home":
            # Home side: cover if actual_margin + spread < 0
            ats_line = actual_margin + pred.market_spread
            if ats_line < 0:
                result = "WIN"
            elif ats_line > 0:
                result = "LOSS"
            else:
                result = "PUSH"
        else:
            return None, 0

        # Margin error: how far off the prediction was
        margin_error = actual_margin - pred.predicted_spread
        return result, margin_error

    def calculate_profit_loss(
        self, result: Optional[str], kelly: float, bankroll: float = 10000
    ) -> Tuple[float, float]:
        """
        Calculate profit/loss and ROI for a bet.

        Args:
            result: 'WIN', 'LOSS', or 'PUSH'
            kelly: Kelly fraction (e.g., 0.05 for 5%)
            bankroll: Starting bankroll (default: $10,000)

        Returns:
            (profit_loss: float, roi: float)
        """
        risk_amount = bankroll * kelly

        if result == "WIN":
            # Standard odds: -110 pays 0.909 to 1
            profit_loss = risk_amount * 0.909
        elif result == "LOSS":
            profit_loss = -risk_amount
        elif result == "PUSH":
            profit_loss = 0
        else:
            profit_loss = 0

        roi = (profit_loss / risk_amount * 100) if risk_amount > 0 else 0
        return profit_loss, roi

    def _find_matching_score(self, pred: Prediction) -> Optional[GameScore]:
        """
        Find matching game score for a prediction.
        Tries exact match first, then fuzzy match by team names.

        Args:
            pred: Prediction object

        Returns:
            Matching GameScore or None
        """
        # Try exact match
        score = self.games.get(pred.game_id)
        if score:
            return score

        # Try fuzzy match by team names
        pred_away = pred.away_team.lower()
        pred_home = pred.home_team.lower()

        for game_id, score in self.games.items():
            score_away = score.away_team.lower()
            score_home = score.home_team.lower()

            # Check if team names match (handle abbreviations and variations)
            away_match = pred_away in score_away or score_away in pred_away
            home_match = pred_home in score_home or score_home in pred_home

            if away_match and home_match:
                return score

        return None

    def check_results(
        self, league: str = "nfl", week: Optional[int] = None
    ) -> List[GameResult]:
        """
        Check predictions against actual results.

        Args:
            league: 'nfl' or 'ncaaf'
            week: Week number (auto-detect if None)

        Returns:
            List of GameResult objects
        """
        # Fetch actual scores
        if league.lower() == "nfl":
            scores = self.fetch_nfl_scores(week=week)
        else:
            scores = self.fetch_ncaaf_scores(week=week)

        if not scores:
            print(f"[ERROR] No scores found for {league}")
            return []

        print(f"[OK] Fetched {len(scores)} {league.upper()} scores")

        # Load predictions (prefer week-specific file)
        project_root = Path(__file__).parent.parent.parent.parent
        edge_dir = project_root / "output" / "edge_detection"

        if league.lower() == "nfl":
            # Try week-specific file first
            if week:
                week_file = (
                    edge_dir / f"nfl_edges_detected_week_{week}.jsonl"
                )
                if week_file.exists():
                    edge_file = week_file
                else:
                    edge_file = edge_dir / "nfl_edges_detected.jsonl"
            else:
                edge_file = edge_dir / "nfl_edges_detected.jsonl"
        else:
            # Try week-specific file first
            if week:
                week_file = (
                    edge_dir / f"ncaaf_edges_detected_week_{week}.jsonl"
                )
                if week_file.exists():
                    edge_file = week_file
                else:
                    edge_file = edge_dir / "ncaaf_edges_detected.jsonl"
            else:
                edge_file = edge_dir / "ncaaf_edges_detected.jsonl"

        predictions = self.load_predictions(edge_file)

        if not predictions:
            print(f"[ERROR] No predictions found for {league}")
            return []

        # Match predictions to actual scores
        bankroll = 10000
        results = []

        for pred in predictions:
            score = self._find_matching_score(pred)

            if not score:
                print(f"[WARNING] No score found for {pred.matchup}")
                continue

            if score.status not in ["Final", "Final/OT"]:
                print(f"[INFO] Game not final: {pred.matchup}")
                continue

            ats_result, margin_error = self.calculate_ats(pred, score)
            profit_loss, roi = self.calculate_profit_loss(
                ats_result, pred.kelly_fraction, bankroll
            )

            result = GameResult(
                prediction=pred,
                score=score,
                ats_result=ats_result,
                ats_margin=margin_error,
                profit_loss=profit_loss,
                roi=roi,
                margin_error=int(margin_error),
            )
            results.append(result)
            self.results = results

        return results

    def generate_report(
        self, results: List[GameResult], league: str = "nfl", week: int = 0
    ) -> str:
        """
        Generate comprehensive markdown performance report.

        Args:
            results: List of GameResult objects
            league: 'nfl' or 'ncaaf'
            week: Week number

        Returns:
            Markdown formatted report
        """
        if not results:
            return "No results to report"

        # Calculate summary stats
        wins = sum(1 for r in results if r.ats_result == "WIN")
        losses = sum(1 for r in results if r.ats_result == "LOSS")
        pushes = sum(1 for r in results if r.ats_result == "PUSH")
        total_games = len(results)

        win_pct = (wins / total_games * 100) if total_games > 0 else 0
        wins_excl_pushes = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        total_wagered = sum(r.prediction.kelly_fraction * 10000 for r in results)
        total_profit = sum(r.profit_loss for r in results)
        total_roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0

        # Build report
        report = []
        report.append("=" * 70)
        report.append(f"BETTING PERFORMANCE REPORT - {league.upper()} WEEK {week}")
        report.append("=" * 70)
        report.append("")

        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        report.append(
            f"**Report Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report.append(f"**League:** {league.upper()}")
        report.append(f"**Week:** {week}")
        report.append("")

        # Performance Metrics
        report.append("### Performance Metrics")
        report.append("")
        report.append(f"| Metric | Value |")
        report.append(f"|--------|-------|")
        report.append(f"| Total Games | {total_games} |")
        report.append(f"| ATS Wins | {wins} |")
        report.append(f"| ATS Losses | {losses} |")
        report.append(f"| Pushes | {pushes} |")
        report.append(f"| Win % | {win_pct:.1f}% |")
        report.append(f"| Win % (excl. pushes) | {wins_excl_pushes:.1f}% |")
        report.append(f"| Total Wagered | ${total_wagered:,.2f} |")
        report.append(f"| Total Profit/Loss | ${total_profit:,.2f} |")
        report.append(f"| ROI | {total_roi:.2f}% |")
        report.append("")

        # Edge Strength Analysis
        strong_edges = sum(1 for r in results if r.prediction.confidence_score >= 70)
        moderate_edges = sum(
            1 for r in results if 50 <= r.prediction.confidence_score < 70
        )
        weak_edges = sum(1 for r in results if r.prediction.confidence_score < 50)

        report.append("### Edge Strength Analysis")
        report.append("")
        report.append(f"| Category | Count | Win % |")
        report.append(f"|----------|-------|-------|")

        strong_wins = sum(
            1
            for r in results
            if r.prediction.confidence_score >= 70 and r.ats_result == "WIN"
        )
        strong_pct = (strong_wins / strong_edges * 100) if strong_edges > 0 else 0
        report.append(f"| Very Strong (70+) | {strong_edges} | {strong_pct:.0f}% |")

        moderate_wins = sum(
            1
            for r in results
            if 50 <= r.prediction.confidence_score < 70 and r.ats_result == "WIN"
        )
        moderate_pct = (
            (moderate_wins / moderate_edges * 100) if moderate_edges > 0 else 0
        )
        report.append(f"| Strong (50-70) | {moderate_edges} | {moderate_pct:.0f}% |")

        weak_wins = sum(
            1
            for r in results
            if r.prediction.confidence_score < 50 and r.ats_result == "WIN"
        )
        weak_pct = (weak_wins / weak_edges * 100) if weak_edges > 0 else 0
        report.append(f"| Moderate (<50) | {weak_edges} | {weak_pct:.0f}% |")
        report.append("")

        # Game-by-Game Results
        report.append("## Game-by-Game Results")
        report.append("")

        for result in sorted(
            results, key=lambda x: x.prediction.confidence_score, reverse=True
        ):
            p = result.prediction
            s = result.score

            report.append(f"### {s.matchup}")
            report.append("")
            report.append(
                f"**Week:** {p.week} | **Confidence:** {p.confidence_score:.0f}"
            )
            report.append("")

            report.append("| Item | Value |")
            report.append("|------|-------|")
            report.append(f"| Predicted Spread | {p.predicted_spread:.1f} |")
            report.append(f"| Market Spread | {p.market_spread:.1f} |")
            report.append(
                f"| Recommended Bet | {p.recommended_bet.upper() if p.recommended_bet else 'NONE'} |"
            )
            report.append(f"| Actual Score | {s.away_score}-{s.home_score} |")
            report.append(f"| Actual Spread | {s.away_score - s.home_score:.0f} |")
            report.append(f"| ATS Result | **{result.ats_result}** |")
            report.append(f"| Margin Error | {result.margin_error} pts |")
            report.append(f"| Kelly Sizing | {p.kelly_fraction * 100:.1f}% |")
            report.append(f"| Profit/Loss | ${result.profit_loss:,.2f} |")
            report.append(f"| ROI | {result.roi:.1f}% |")
            report.append("")

        # Summary by Edge Strength
        report.append("## Edge Strength Classification")
        report.append("")
        report.append("Per Billy Walters methodology, edges are classified as follows:")
        report.append("")
        report.append("| Classification | Edge Points | Expected WR | Kelly | Result |")
        report.append("|---|---|---|---|---|")

        for r in sorted(
            results,
            key=lambda x: abs(
                x.prediction.edge_points if hasattr(x.prediction, "edge_points") else 0
            ),
            reverse=True,
        ):
            p = r.prediction
            confidence = p.confidence_score
            if confidence >= 70:
                classification = "Very Strong"
            elif confidence >= 50:
                classification = "Strong"
            else:
                classification = "Moderate"

            report.append(
                f"| {classification} | {confidence:.1f} | TBD | "
                f"{p.kelly_fraction * 100:.1f}% | {r.ats_result} |"
            )

        report.append("")

        # Recommendations
        report.append("## Analysis & Recommendations")
        report.append("")

        if total_roi >= 5:
            report.append(
                f"[OK] **Positive Performance:** ROI of {total_roi:.2f}% indicates "
                "successful edge detection."
            )
        elif total_roi >= 0:
            report.append(
                f"[OK] **Breakeven:** ROI of {total_roi:.2f}% - edges were properly "
                "identified but execution was marginal."
            )
        else:
            report.append(
                f"[ERROR] **Negative Performance:** ROI of {total_roi:.2f}% - edges may "
                "not have materialized or market was efficient."
            )

        report.append("")
        report.append("### Methodology Notes")
        report.append("")
        report.append("- **ATS Result:** Spread bet performance (cover vs loss)")
        report.append(
            "- **Margin Error:** Difference between predicted and actual spread"
        )
        report.append("- **Kelly Sizing:** Bet sizing based on edge and bankroll")
        report.append("- **ROI:** Return on investment based on standard -110 odds")

        return "\n".join(report)

    def save_report(self, report: str, league: str = "nfl", week: int = 0) -> Path:
        """
        Save report to file.

        Args:
            report: Markdown formatted report
            league: 'nfl' or 'ncaaf'
            week: Week number

        Returns:
            Path to saved report
        """
        project_root = Path(__file__).parent.parent.parent.parent
        report_dir = project_root / "docs" / "performance_reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"REPORT_{league.upper()}_WEEK{week}_{timestamp}.md"
        filepath = report_dir / filename

        try:
            with open(filepath, "w") as f:
                f.write(report)
            print(f"[OK] Report saved: {filepath}")
            return filepath
        except IOError as e:
            print(f"[ERROR] Failed to save report: {e}")
            raise
