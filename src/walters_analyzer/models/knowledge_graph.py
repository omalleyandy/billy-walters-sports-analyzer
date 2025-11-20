"""
Knowledge Graph implementation for Billy Walters Sports Analyzer.

This module provides graph-based storage and querying for:
- Teams and their power ratings over time
- Games and their relationships
- Matchup evaluations with all adjustments
- Bet recommendations and their outcomes
- Historical performance tracking
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import ValidationError

from walters_analyzer.models.core import (
    BetRecommendation,
    BetSide,
    BetType,
    Game,
    MatchupEvaluation,
    PowerRatingSnapshot,
    Team,
)


class BettingKnowledgeGraph:
    """
    In-memory knowledge graph for tracking relationships between:
    - Teams
    - Games
    - Power Ratings
    - Matchup Evaluations
    - Bet Recommendations
    - Historical Performance
    
    This implements Billy Walters' systematic approach to tracking
    and analyzing betting opportunities.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the knowledge graph.
        
        Args:
            storage_path: Optional path for persisting graph data
        """
        self.storage_path = storage_path
        
        # Core entities
        self.teams: Dict[str, Team] = {}
        self.games: Dict[str, Game] = {}
        self.power_ratings: Dict[str, List[PowerRatingSnapshot]] = defaultdict(list)
        self.evaluations: Dict[str, MatchupEvaluation] = {}
        self.recommendations: Dict[str, BetRecommendation] = {}
        
        # Relationships
        self.team_games: Dict[str, Set[str]] = defaultdict(set)  # team_id -> game_ids
        self.game_evaluations: Dict[str, Set[str]] = defaultdict(set)  # game_id -> evaluation_ids
        self.evaluation_recommendations: Dict[str, Set[str]] = defaultdict(set)  # eval_id -> rec_ids
        
        # Performance tracking
        self.bet_outcomes: Dict[str, Dict[str, Any]] = {}  # recommendation_id -> outcome
        self.closing_lines: Dict[str, float] = {}  # game_id -> closing_spread
        
        # Load existing data if path provided
        if self.storage_path and self.storage_path.exists():
            self.load()
    
    # --- Team Management ---
    
    def add_team(self, team: Team) -> None:
        """Add or update a team in the graph."""
        self.teams[team.team_id] = team
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """Retrieve a team by ID."""
        return self.teams.get(team_id)
    
    def get_all_teams(self) -> List[Team]:
        """Get all teams in the graph."""
        return list(self.teams.values())
    
    # --- Game Management ---
    
    def add_game(self, game: Game) -> None:
        """Add a game and update relationships."""
        self.games[game.game_id] = game
        
        # Update team-game relationships
        self.team_games[game.home_team_id].add(game.game_id)
        self.team_games[game.away_team_id].add(game.game_id)
    
    def get_game(self, game_id: str) -> Optional[Game]:
        """Retrieve a game by ID."""
        return self.games.get(game_id)
    
    def get_team_games(
        self,
        team_id: str,
        season: Optional[int] = None,
        week: Optional[int] = None,
    ) -> List[Game]:
        """Get all games for a team, optionally filtered by season/week."""
        game_ids = self.team_games.get(team_id, set())
        games = [self.games[gid] for gid in game_ids if gid in self.games]
        
        if season:
            games = [g for g in games if g.season == season]
        if week:
            games = [g for g in games if g.week == week]
        
        return sorted(games, key=lambda g: (g.season, g.week, g.kickoff_datetime))
    
    # --- Power Rating Management ---
    
    def add_power_rating(self, rating: PowerRatingSnapshot) -> None:
        """Add a power rating snapshot for a team."""
        self.power_ratings[rating.team_id].append(rating)
        
        # Keep sorted by creation time
        self.power_ratings[rating.team_id].sort(key=lambda r: r.created_at)
    
    def get_latest_power_rating(
        self,
        team_id: str,
        source: Optional[str] = None,
        as_of: Optional[datetime] = None,
    ) -> Optional[PowerRatingSnapshot]:
        """Get the most recent power rating for a team."""
        ratings = self.power_ratings.get(team_id, [])
        
        if source:
            ratings = [r for r in ratings if r.source == source]
        
        if as_of:
            ratings = [r for r in ratings if r.created_at <= as_of]
        
        return ratings[-1] if ratings else None
    
    def get_power_rating_history(
        self,
        team_id: str,
        season: Optional[int] = None,
        source: Optional[str] = None,
    ) -> List[PowerRatingSnapshot]:
        """Get power rating history for a team."""
        ratings = self.power_ratings.get(team_id, [])
        
        if season:
            ratings = [r for r in ratings if r.season == season]
        
        if source:
            ratings = [r for r in ratings if r.source == source]
        
        return ratings
    
    # --- Evaluation Management ---
    
    def add_evaluation(self, evaluation: MatchupEvaluation) -> str:
        """Add a matchup evaluation and update relationships."""
        # Generate ID if not present (using game_id + timestamp)
        eval_id = f"eval_{evaluation.game.game_id}_{int(datetime.utcnow().timestamp())}"
        
        self.evaluations[eval_id] = evaluation
        self.game_evaluations[evaluation.game.game_id].add(eval_id)
        
        return eval_id
    
    def get_evaluation(self, eval_id: str) -> Optional[MatchupEvaluation]:
        """Retrieve an evaluation by ID."""
        return self.evaluations.get(eval_id)
    
    def get_game_evaluations(self, game_id: str) -> List[MatchupEvaluation]:
        """Get all evaluations for a game."""
        eval_ids = self.game_evaluations.get(game_id, set())
        return [self.evaluations[eid] for eid in eval_ids if eid in self.evaluations]
    
    # --- Recommendation Management ---
    
    def add_recommendation(
        self,
        recommendation: BetRecommendation,
        evaluation_id: Optional[str] = None,
    ) -> str:
        """Add a bet recommendation and link to evaluation."""
        # Generate ID if not present
        rec_id = f"rec_{recommendation.game_id}_{int(datetime.utcnow().timestamp())}"
        
        # Ensure we have valid IDs
        if not recommendation.recommendation_id:
            recommendation.recommendation_id = rec_id
        
        self.recommendations[recommendation.recommendation_id] = recommendation
        
        if evaluation_id:
            self.evaluation_recommendations[evaluation_id].add(recommendation.recommendation_id)
        
        return recommendation.recommendation_id
    
    def get_recommendation(self, rec_id: str) -> Optional[BetRecommendation]:
        """Retrieve a recommendation by ID."""
        return self.recommendations.get(rec_id)
    
    def get_active_recommendations(
        self,
        min_edge: float = 5.5,
        max_stake: float = 0.03,
    ) -> List[BetRecommendation]:
        """Get recommendations that meet criteria and haven't been placed."""
        active = []
        
        for rec in self.recommendations.values():
            # Check if bet meets criteria
            if rec.edge_percent < min_edge:
                continue
            if rec.stake_fraction > max_stake:
                continue
            
            # Check if bet hasn't been placed (no outcome recorded)
            if rec.recommendation_id not in self.bet_outcomes:
                active.append(rec)
        
        return sorted(active, key=lambda r: r.edge_percent, reverse=True)
    
    # --- Performance Tracking ---
    
    def record_bet_outcome(
        self,
        recommendation_id: str,
        result: str,  # "win", "loss", "push"
        actual_score_home: Optional[int] = None,
        actual_score_away: Optional[int] = None,
        profit_loss: Optional[float] = None,
    ) -> None:
        """Record the outcome of a bet."""
        self.bet_outcomes[recommendation_id] = {
            "result": result,
            "actual_score_home": actual_score_home,
            "actual_score_away": actual_score_away,
            "profit_loss": profit_loss,
            "recorded_at": datetime.utcnow().isoformat(),
        }
    
    def record_closing_line(self, game_id: str, closing_spread: float) -> None:
        """Record the closing line for CLV calculation."""
        self.closing_lines[game_id] = closing_spread
    
    def calculate_clv(self, recommendation_id: str) -> Optional[float]:
        """Calculate Closing Line Value for a recommendation."""
        rec = self.recommendations.get(recommendation_id)
        if not rec or not rec.line:
            return None
        
        closing = self.closing_lines.get(rec.game_id)
        if closing is None:
            return None
        
        # CLV = closing_line - bet_line (positive is good)
        return closing - rec.line
    
    def get_performance_summary(
        self,
        season: Optional[int] = None,
        week: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get performance summary statistics."""
        # Filter recommendations
        recs = list(self.recommendations.values())
        
        if season or week:
            filtered = []
            for rec in recs:
                game = self.games.get(rec.game_id)
                if game:
                    if season and game.season != season:
                        continue
                    if week and game.week != week:
                        continue
                    filtered.append(rec)
            recs = filtered
        
        # Calculate statistics
        total_bets = len(recs)
        
        # W-L-P record
        wins = sum(1 for r in recs if self.bet_outcomes.get(r.recommendation_id, {}).get("result") == "win")
        losses = sum(1 for r in recs if self.bet_outcomes.get(r.recommendation_id, {}).get("result") == "loss")
        pushes = sum(1 for r in recs if self.bet_outcomes.get(r.recommendation_id, {}).get("result") == "push")
        
        # Profit/Loss
        total_profit = sum(
            self.bet_outcomes.get(r.recommendation_id, {}).get("profit_loss", 0)
            for r in recs
        )
        
        # CLV
        clv_values = [self.calculate_clv(r.recommendation_id) for r in recs]
        clv_values = [v for v in clv_values if v is not None]
        avg_clv = sum(clv_values) / len(clv_values) if clv_values else 0
        
        # Edge distribution
        edge_distribution = {
            "0-5.5%": sum(1 for r in recs if r.edge_percent < 5.5),
            "5.5-7%": sum(1 for r in recs if 5.5 <= r.edge_percent < 7),
            "7-10%": sum(1 for r in recs if 7 <= r.edge_percent < 10),
            "10%+": sum(1 for r in recs if r.edge_percent >= 10),
        }
        
        return {
            "total_bets": total_bets,
            "record": {"wins": wins, "losses": losses, "pushes": pushes},
            "win_rate": wins / (wins + losses) if (wins + losses) > 0 else 0,
            "total_profit": total_profit,
            "roi": (total_profit / (total_bets * 100)) if total_bets > 0 else 0,  # Assuming $100 unit
            "avg_clv": avg_clv,
            "clv_beat_rate": sum(1 for v in clv_values if v > 0) / len(clv_values) if clv_values else 0,
            "edge_distribution": edge_distribution,
        }
    
    # --- Query Methods ---
    
    def find_similar_matchups(
        self,
        game_id: str,
        max_results: int = 5,
    ) -> List[Tuple[Game, MatchupEvaluation]]:
        """Find historically similar matchups based on spreads and totals."""
        target_game = self.games.get(game_id)
        if not target_game:
            return []
        
        # Get the most recent evaluation for this game
        target_evals = self.get_game_evaluations(game_id)
        if not target_evals:
            return []
        
        target_eval = target_evals[-1]  # Most recent
        
        # Find similar games
        similar = []
        
        for other_game_id, other_game in self.games.items():
            if other_game_id == game_id:
                continue
            
            # Must involve at least one of the same teams
            if not (
                target_game.home_team_id in (other_game.home_team_id, other_game.away_team_id) or
                target_game.away_team_id in (other_game.home_team_id, other_game.away_team_id)
            ):
                continue
            
            other_evals = self.get_game_evaluations(other_game_id)
            if not other_evals:
                continue
            
            other_eval = other_evals[-1]
            
            # Calculate similarity based on spread difference
            spread_diff = abs(target_eval.market_spread - other_eval.market_spread)
            
            similar.append((other_game, other_eval, spread_diff))
        
        # Sort by similarity (smaller difference = more similar)
        similar.sort(key=lambda x: x[2])
        
        return [(g, e) for g, e, _ in similar[:max_results]]
    
    # --- Persistence ---
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save the knowledge graph to disk."""
        save_path = path or self.storage_path
        if not save_path:
            raise ValueError("No save path specified")
        
        data = {
            "teams": {tid: t.model_dump() for tid, t in self.teams.items()},
            "games": {gid: g.model_dump() for gid, g in self.games.items()},
            "power_ratings": {
                tid: [r.model_dump() for r in ratings]
                for tid, ratings in self.power_ratings.items()
            },
            "evaluations": {eid: e.model_dump() for eid, e in self.evaluations.items()},
            "recommendations": {rid: r.model_dump() for rid, r in self.recommendations.items()},
            "team_games": {tid: list(gids) for tid, gids in self.team_games.items()},
            "game_evaluations": {gid: list(eids) for gid, eids in self.game_evaluations.items()},
            "evaluation_recommendations": {
                eid: list(rids) for eid, rids in self.evaluation_recommendations.items()
            },
            "bet_outcomes": self.bet_outcomes,
            "closing_lines": self.closing_lines,
        }
        
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def load(self, path: Optional[Path] = None) -> None:
        """Load the knowledge graph from disk."""
        load_path = path or self.storage_path
        if not load_path or not load_path.exists():
            return
        
        with open(load_path) as f:
            data = json.load(f)
        
        # Load teams
        for tid, tdata in data.get("teams", {}).items():
            self.teams[tid] = Team(**tdata)
        
        # Load games
        for gid, gdata in data.get("games", {}).items():
            # Convert datetime strings back to datetime objects
            if "kickoff_datetime" in gdata:
                gdata["kickoff_datetime"] = datetime.fromisoformat(gdata["kickoff_datetime"])
            self.games[gid] = Game(**gdata)
        
        # Load power ratings
        for tid, ratings in data.get("power_ratings", {}).items():
            for rdata in ratings:
                if "created_at" in rdata:
                    rdata["created_at"] = datetime.fromisoformat(rdata["created_at"])
                self.power_ratings[tid].append(PowerRatingSnapshot(**rdata))
        
        # Load evaluations
        for eid, edata in data.get("evaluations", {}).items():
            # Note: This requires proper deserialization of nested objects
            # For now, storing as dict - you may need to enhance this
            self.evaluations[eid] = edata
        
        # Load recommendations
        for rid, rdata in data.get("recommendations", {}).items():
            if "created_at" in rdata:
                rdata["created_at"] = datetime.fromisoformat(rdata["created_at"])
            self.recommendations[rid] = BetRecommendation(**rdata)
        
        # Load relationships
        self.team_games = {tid: set(gids) for tid, gids in data.get("team_games", {}).items()}
        self.game_evaluations = {gid: set(eids) for gid, eids in data.get("game_evaluations", {}).items()}
        self.evaluation_recommendations = {
            eid: set(rids) for eid, rids in data.get("evaluation_recommendations", {}).items()
        }
        
        # Load performance data
        self.bet_outcomes = data.get("bet_outcomes", {})
        self.closing_lines = data.get("closing_lines", {})


# --- Utility Functions ---

def create_recommendation_from_evaluation(
    evaluation: MatchupEvaluation,
    game_id: str,
    evaluation_id: str,
    bankroll: float = 20000.0,
) -> Optional[BetRecommendation]:
    """
    Create a bet recommendation from a matchup evaluation.
    
    This implements Billy Walters' methodology for converting
    edge calculations into actionable bets with strict risk management:
    - Minimum 5.5% edge required for any bet
    - Maximum 3% of bankroll per bet
    - Star rating system: 0 stars (no bet), 1 star (0.5-1%), 2 stars (1-2%), 3 stars (2-3%)
    
    Args:
        evaluation: MatchupEvaluation with edge calculations
        game_id: Game ID for the bet
        evaluation_id: Evaluation ID for traceability
        bankroll: Total bankroll for stake calculation (default $20k)
        
    Returns:
        BetRecommendation if edge >= 5.5%, None otherwise
    """
    # Billy Walters methodology: Minimum 5.5% edge required for betting
    if evaluation.edge_percent < 5.5:
        return None
    
    # Determine bet side based on edge direction
    # Positive edge points favor home team
    if evaluation.edge_points > 0:
        # Positive edge means home team has value
        bet_type = BetType.SPREAD
        side = BetSide.HOME
        line = evaluation.market_spread
    else:
        # Negative edge means away team has value
        bet_type = BetType.SPREAD
        side = BetSide.AWAY
        line = -evaluation.market_spread
    
    # Billy Walters star rating to stake mapping
    # Note: Even 3-star bets capped at 3% maximum (risk management absolute rule)
    star_to_stake = {
        0: 0.000,   # No bet - edge too low
        1: 0.010,   # 1% for 1 star (5.5-7% edge)
        2: 0.020,   # 2% for 2 stars (7-10% edge)
        3: 0.030,   # 3% for 3 stars (10%+ edge) - hard cap
    }
    
    stake_fraction = star_to_stake.get(evaluation.star_rating, 0.0)
    
    # Generate detailed rationale showing methodology
    rationale_parts = []
    
    # 1. Base edge from power ratings
    rationale_parts.append(
        f"Edge: {abs(evaluation.edge_percent):.1f}% from power rating differential "
        f"(home {evaluation.home_rating.rating:+.1f} vs away {evaluation.away_rating.rating:+.1f})"
    )
    
    # 2. Adjustment summary
    if evaluation.adjustments.total_adjustment != 0:
        adj_str = f"{evaluation.adjustments.total_adjustment:+.2f} pts from:"
        parts = []
        if evaluation.adjustments.s_factor_points != 0:
            parts.append(f"S-factors {evaluation.adjustments.s_factor_points:+.2f}")
        if evaluation.adjustments.w_factor_points != 0:
            parts.append(f"Weather {evaluation.adjustments.w_factor_points:+.2f}")
        if evaluation.adjustments.e_factor_points != 0:
            parts.append(f"Emotion {evaluation.adjustments.e_factor_points:+.2f}")
        if evaluation.adjustments.injury_points != 0:
            parts.append(f"Injuries {evaluation.adjustments.injury_points:+.2f}")
        if parts:
            adj_str += " [" + ", ".join(parts) + "]"
        rationale_parts.append(adj_str)
    
    # 3. Key number value
    if line is not None:
        key_numbers = {3, 7, 10, 14}
        abs_line = abs(line)
        if int(abs_line) in key_numbers:
            rationale_parts.append(f"Crossing key number {int(abs_line)}")
    
    # 4. Star rating explanation
    star_explanation = {
        1: "1-star: Minimal edge, small conviction",
        2: "2-star: Clear edge, moderate conviction",
        3: "3-star: Strong edge, high conviction",
    }
    if evaluation.star_rating in star_explanation:
        rationale_parts.append(star_explanation[evaluation.star_rating])
    
    rationale = " | ".join(rationale_parts)
    
    # Create recommendation with all required fields
    rec_id = f"rec_{game_id}_{int(datetime.utcnow().timestamp() * 1000)}"
    
    return BetRecommendation(
        recommendation_id=rec_id,
        game_id=game_id,
        evaluation_id=evaluation_id,
        bet_type=bet_type,
        side=side,
        line=line,
        price=-110,  # Standard -110 juice on spreads
        edge_percentage=evaluation.edge_percent,
        star_rating=evaluation.star_rating,
        stake_fraction=stake_fraction,
        bankroll=bankroll,
        is_play=stake_fraction > 0,  # Only play if stake is positive
        rationale=rationale,
    )


__all__ = [
    "BettingKnowledgeGraph",
    "create_recommendation_from_evaluation",
]
