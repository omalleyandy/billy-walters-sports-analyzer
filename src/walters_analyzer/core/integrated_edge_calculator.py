"""
Integrated Edge Calculator with Sharp Money Signals

Combines Billy Walters methodology with Action Network sharp money data:
1. Power rating edge (your predicted spread vs market)
2. S-factor adjustments (travel, rest, weather, motivation)
3. Key number premiums (3, 7 value)
4. Sharp money confirmation/contradiction signals

Billy Walters Principle: "The combination of your own analysis plus knowing
where the smart money is going is incredibly powerful."
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class SharpMoneySignal:
    """Sharp money analysis from Action Network data."""
    tickets_pct: int  # % of bets placed
    money_pct: int    # % of money wagered
    divergence: int   # money_pct - tickets_pct
    sharp_side: Optional[str] = None  # Team abbreviation
    line_movement: Optional[float] = None
    
    @property
    def is_sharp_side(self) -> bool:
        """True if this side has sharp money (5+ divergence)."""
        return self.divergence >= 5
    
    @property
    def is_public_side(self) -> bool:
        """True if this is the public side (5+ negative divergence)."""
        return self.divergence <= -5
    
    @property
    def signal_strength(self) -> str:
        """Categorize signal strength."""
        if abs(self.divergence) >= 15:
            return "VERY_STRONG"
        elif abs(self.divergence) >= 10:
            return "STRONG"
        elif abs(self.divergence) >= 5:
            return "MODERATE"
        else:
            return "NONE"


@dataclass
class IntegratedEdgeAnalysis:
    """Complete edge analysis combining power ratings and sharp money."""
    
    # Basic info
    game: str
    our_pick: str
    market_line: float
    
    # Power rating edge components
    base_edge_points: float
    sfactor_adjustment: float
    key_number_premium_pct: float
    
    # Sharp money components
    sharp_signal: Optional[SharpMoneySignal] = None
    sharp_alignment: str = "UNKNOWN"  # "CONFIRMS", "CONTRADICTS", "NEUTRAL"
    sharp_confidence_modifier: float = 0.0  # -0.2 to +0.2
    
    # Combined results
    raw_edge_pct: float = 0.0
    adjusted_edge_pct: float = 0.0
    confidence_level: str = "NONE"
    star_rating: float = 0.0
    recommended_bet_pct: float = 0.0
    
    # Metadata
    crossed_key_numbers: List[int] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class IntegratedEdgeCalculator:
    """
    Combines power rating analysis with sharp money signals.
    
    Integration Formula:
    1. Calculate base edge from power ratings
    2. Add S-factor adjustments (5:1 ratio)
    3. Add key number premiums
    4. Apply sharp money confidence modifier:
       - Sharp confirms our pick: +10-20% confidence boost
       - Sharp contradicts our pick: -10-20% confidence penalty
       - Neutral: No adjustment
    
    Usage:
        calculator = IntegratedEdgeCalculator()
        
        # Load Action Network data
        calculator.load_action_network_data('data/action_network/nfl_odds_latest.json')
        
        # Analyze game
        result = calculator.analyze_game(
            away_team='GB',
            home_team='DET',
            our_spread=-1.0,  # We think DET by 1
            market_spread=-2.5,  # Market has DET by 2.5
            sfactor_points=5.0
        )
        
        print(f"Edge: {result.adjusted_edge_pct:.1f}%")
        print(f"Sharp alignment: {result.sharp_alignment}")
    """
    
    # Key number values (frequency percentages)
    KEY_NUMBERS = {
        3: 0.08,   # 8% - MOST IMPORTANT
        7: 0.06,   # 6% - SECOND MOST IMPORTANT
        6: 0.05,   # 5%
        10: 0.04,  # 4%
        14: 0.05,  # 5%
        1: 0.03, 2: 0.03, 4: 0.03, 5: 0.03, 8: 0.03,
        9: 0.02, 11: 0.02, 12: 0.02, 13: 0.02, 15: 0.02,
        16: 0.03, 17: 0.03, 18: 0.03, 21: 0.03
    }
    
    # Star rating thresholds
    STAR_THRESHOLDS = [
        (5.5, 0.5),
        (7.0, 1.0),
        (9.0, 1.5),
        (11.0, 2.0),
        (13.0, 2.5),
        (15.0, 3.0),
    ]
    
    # Sharp money confidence modifiers
    SHARP_CONFIRM_BOOST = {
        "VERY_STRONG": 0.20,  # +20% when very strong signal confirms
        "STRONG": 0.15,       # +15% when strong signal confirms
        "MODERATE": 0.10,     # +10% when moderate signal confirms
        "NONE": 0.0
    }
    
    SHARP_CONTRADICT_PENALTY = {
        "VERY_STRONG": -0.20,  # -20% when very strong signal contradicts
        "STRONG": -0.15,       # -15% when strong signal contradicts
        "MODERATE": -0.10,     # -10% when moderate signal contradicts
        "NONE": 0.0
    }
    
    def __init__(self):
        self.action_network_data: Dict = {}
        self.game_odds: Dict = {}  # Keyed by "AWAY@HOME"
    
    def load_action_network_data(self, filepath: str | Path) -> int:
        """
        Load Action Network odds data.
        
        Args:
            filepath: Path to Action Network JSON file
            
        Returns:
            Number of games loaded
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"Action Network file not found: {filepath}")
            return 0
        
        with open(filepath) as f:
            self.action_network_data = json.load(f)
        
        # Index games by matchup
        self.game_odds = {}
        for game in self.action_network_data.get('games', []):
            away = game.get('away_team', '')
            home = game.get('home_team', '')
            key = f"{away}@{home}"
            self.game_odds[key] = game
        
        logger.info(f"Loaded {len(self.game_odds)} games from Action Network")
        return len(self.game_odds)
    
    def get_sharp_signal(self, away_team: str, home_team: str, 
                         our_pick_side: str) -> Optional[SharpMoneySignal]:
        """
        Get sharp money signal for a game.
        
        Args:
            away_team: Away team abbreviation
            home_team: Home team abbreviation
            our_pick_side: Which side we're picking ('home' or 'away')
            
        Returns:
            SharpMoneySignal or None if no data
        """
        key = f"{away_team}@{home_team}"
        game_data = self.game_odds.get(key)
        
        if not game_data:
            return None
        
        spread_data = game_data.get('spread', {})
        our_side_data = spread_data.get(our_pick_side, {})
        
        tickets = our_side_data.get('tickets_pct')
        money = our_side_data.get('money_pct')
        
        if tickets is None or money is None:
            return None
        
        return SharpMoneySignal(
            tickets_pct=tickets,
            money_pct=money,
            divergence=money - tickets,
            sharp_side=game_data.get('sharp_side'),
            line_movement=game_data.get('line_movement')
        )
    
    def _calculate_key_number_premium(self, our_line: float, 
                                       market_line: float) -> tuple[float, list[int]]:
        """Calculate premium for crossing key numbers."""
        min_line = min(abs(our_line), abs(market_line))
        max_line = max(abs(our_line), abs(market_line))
        
        crossed = []
        total_premium = 0.0
        
        for number in range(int(min_line) + 1, int(max_line) + 1):
            if number in self.KEY_NUMBERS:
                value = self.KEY_NUMBERS[number]
                
                # Half value if sitting on the number
                if our_line == float(number) or market_line == float(number):
                    value /= 2.0
                
                crossed.append(number)
                total_premium += value
        
        return total_premium * 100, crossed  # Convert to percentage
    
    def _get_star_rating(self, edge_pct: float) -> float:
        """Convert edge percentage to star rating."""
        for threshold, stars in reversed(self.STAR_THRESHOLDS):
            if edge_pct >= threshold:
                return min(stars, 3.0)
        return 0.0
    
    def _get_confidence_level(self, edge_pct: float, crossed_numbers: list, 
                               sharp_alignment: str) -> str:
        """Determine confidence level."""
        if edge_pct < 5.5:
            return "NONE"
        
        base_confidence = "LOW"
        
        if edge_pct >= 12.0:
            base_confidence = "HIGH"
        elif edge_pct >= 8.0:
            base_confidence = "MEDIUM"
        
        # Boost if crossing 3 or 7
        if 3 in crossed_numbers or 7 in crossed_numbers:
            if base_confidence == "LOW":
                base_confidence = "MEDIUM"
            elif base_confidence == "MEDIUM":
                base_confidence = "HIGH"
        
        # Sharp alignment affects confidence
        if sharp_alignment == "CONFIRMS" and base_confidence != "HIGH":
            base_confidence = {"LOW": "MEDIUM", "MEDIUM": "HIGH"}.get(base_confidence, base_confidence)
        elif sharp_alignment == "CONTRADICTS":
            base_confidence = {"HIGH": "MEDIUM", "MEDIUM": "LOW"}.get(base_confidence, base_confidence)
        
        return base_confidence
    
    def analyze_game(
        self,
        away_team: str,
        home_team: str,
        our_spread: float,
        market_spread: float,
        sfactor_points: float = 0.0,
        pick_side: str = "auto"
    ) -> IntegratedEdgeAnalysis:
        """
        Perform integrated edge analysis.
        
        Args:
            away_team: Away team abbreviation
            home_team: Home team abbreviation  
            our_spread: Our predicted spread (negative = home favorite)
            market_spread: Market spread (negative = home favorite)
            sfactor_points: Total S-factor points (raw, will be converted 5:1)
            pick_side: "home", "away", or "auto" to determine from edge
            
        Returns:
            IntegratedEdgeAnalysis with complete breakdown
        """
        warnings = []
        notes = []
        
        # Determine which side we're picking
        if pick_side == "auto":
            # We pick home if our spread is more negative than market
            # (we think home team is stronger)
            if our_spread < market_spread:
                pick_side = "home"
                our_pick = f"{home_team} {our_spread:+.1f}"
            else:
                pick_side = "away"
                our_pick = f"{away_team} {-our_spread:+.1f}"
        elif pick_side == "home":
            our_pick = f"{home_team} {our_spread:+.1f}"
        else:
            our_pick = f"{away_team} {-our_spread:+.1f}"
        
        # Step 1: Calculate base edge from power ratings
        base_edge_points = abs(market_spread - our_spread)
        
        # Step 2: Convert S-factors (5:1 ratio)
        sfactor_adjustment = sfactor_points / 5.0
        
        # Step 3: Calculate key number premium
        key_premium_pct, crossed_numbers = self._calculate_key_number_premium(
            our_spread, market_spread
        )
        
        # Step 4: Calculate raw edge percentage
        total_edge_points = base_edge_points + sfactor_adjustment
        raw_edge_pct = total_edge_points + key_premium_pct
        
        # Step 5: Get sharp money signal
        sharp_signal = self.get_sharp_signal(away_team, home_team, pick_side)
        sharp_alignment = "UNKNOWN"
        sharp_modifier = 0.0
        
        if sharp_signal:
            our_team = home_team if pick_side == "home" else away_team
            
            # Determine alignment
            if sharp_signal.is_sharp_side:
                sharp_alignment = "CONFIRMS"
                sharp_modifier = self.SHARP_CONFIRM_BOOST.get(
                    sharp_signal.signal_strength, 0.0
                )
                notes.append(f"Sharp money CONFIRMS our pick ({sharp_signal.divergence:+d} divergence)")
                
            elif sharp_signal.is_public_side:
                sharp_alignment = "CONTRADICTS"
                sharp_modifier = self.SHARP_CONTRADICT_PENALTY.get(
                    sharp_signal.signal_strength, 0.0
                )
                warnings.append(f"Sharp money CONTRADICTS our pick ({sharp_signal.divergence:+d} divergence)")
                
            else:
                sharp_alignment = "NEUTRAL"
                notes.append(f"Sharp money neutral ({sharp_signal.divergence:+d} divergence)")
            
            # Note line movement
            if sharp_signal.line_movement:
                direction = "toward" if (
                    (sharp_signal.line_movement < 0 and pick_side == "home") or
                    (sharp_signal.line_movement > 0 and pick_side == "away")
                ) else "against"
                notes.append(f"Line moved {abs(sharp_signal.line_movement):.1f} pts {direction} our pick")
        
        # Step 6: Calculate adjusted edge
        adjusted_edge_pct = raw_edge_pct * (1 + sharp_modifier)
        
        # Step 7: Determine confidence and star rating
        confidence = self._get_confidence_level(
            adjusted_edge_pct, crossed_numbers, sharp_alignment
        )
        star_rating = self._get_star_rating(adjusted_edge_pct)
        
        # Step 8: Calculate bet size
        if adjusted_edge_pct < 5.5:
            recommended_bet_pct = 0.0
            warnings.append("Edge below 5.5% minimum - NO BET")
        else:
            # 1% per star, max 3%
            recommended_bet_pct = min(star_rating * 0.01, 0.03)
        
        # Step 9: Add validation warnings
        if adjusted_edge_pct > 15.0:
            warnings.append("Extreme edge (>15%) - verify data accuracy")
        
        if base_edge_points > 7.0 and sharp_alignment != "CONFIRMS":
            warnings.append("Large edge without sharp confirmation - potential value trap")
        
        return IntegratedEdgeAnalysis(
            game=f"{away_team} @ {home_team}",
            our_pick=our_pick,
            market_line=market_spread,
            base_edge_points=base_edge_points,
            sfactor_adjustment=sfactor_adjustment,
            key_number_premium_pct=key_premium_pct,
            sharp_signal=sharp_signal,
            sharp_alignment=sharp_alignment,
            sharp_confidence_modifier=sharp_modifier,
            raw_edge_pct=raw_edge_pct,
            adjusted_edge_pct=adjusted_edge_pct,
            confidence_level=confidence,
            star_rating=star_rating,
            recommended_bet_pct=recommended_bet_pct,
            crossed_key_numbers=crossed_numbers,
            warnings=warnings,
            notes=notes
        )
    
    def analyze_all_games(
        self,
        power_ratings: Dict[str, float],
        home_advantage: float = 2.5,
        min_edge: float = 5.5
    ) -> List[IntegratedEdgeAnalysis]:
        """
        Analyze all games with Action Network data against power ratings.
        
        Args:
            power_ratings: Dict of team abbreviation -> power rating
            home_advantage: Home field advantage points
            min_edge: Minimum edge to include in results
            
        Returns:
            List of analyses sorted by adjusted edge
        """
        results = []
        
        for game_key, game_data in self.game_odds.items():
            away_team = game_data.get('away_team')
            home_team = game_data.get('home_team')
            
            if away_team not in power_ratings or home_team not in power_ratings:
                logger.warning(f"Missing power rating for {game_key}")
                continue
            
            # Calculate our predicted spread
            home_rating = power_ratings[home_team]
            away_rating = power_ratings[away_team]
            our_spread = (away_rating - home_rating) - home_advantage
            
            # Get market spread
            spread_data = game_data.get('spread', {})
            home_spread = spread_data.get('home', {}).get('value')
            
            if home_spread is None:
                continue
            
            # Analyze
            analysis = self.analyze_game(
                away_team=away_team,
                home_team=home_team,
                our_spread=our_spread,
                market_spread=home_spread
            )
            
            if analysis.adjusted_edge_pct >= min_edge:
                results.append(analysis)
        
        # Sort by adjusted edge (descending)
        results.sort(key=lambda x: x.adjusted_edge_pct, reverse=True)
        
        return results
    
    def print_analysis(self, analysis: IntegratedEdgeAnalysis) -> None:
        """Pretty print an analysis."""
        print(f"\n{'='*60}")
        print(f"GAME: {analysis.game}")
        print(f"{'='*60}")
        print(f"OUR PICK: {analysis.our_pick}")
        print(f"Market Line: {analysis.market_line:+.1f}")
        
        print(f"\n📊 EDGE BREAKDOWN:")
        print(f"  Base Edge: {analysis.base_edge_points:.1f} pts")
        print(f"  S-Factor Adj: {analysis.sfactor_adjustment:+.2f} pts")
        print(f"  Key Numbers: {analysis.crossed_key_numbers} (+{analysis.key_number_premium_pct:.1f}%)")
        print(f"  Raw Edge: {analysis.raw_edge_pct:.1f}%")
        
        if analysis.sharp_signal:
            print(f"\n💰 SHARP MONEY:")
            print(f"  Tickets: {analysis.sharp_signal.tickets_pct}%")
            print(f"  Money: {analysis.sharp_signal.money_pct}%")
            print(f"  Divergence: {analysis.sharp_signal.divergence:+d} pts")
            print(f"  Alignment: {analysis.sharp_alignment}")
            print(f"  Modifier: {analysis.sharp_confidence_modifier:+.0%}")
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        print(f"  Adjusted Edge: {analysis.adjusted_edge_pct:.1f}%")
        print(f"  Confidence: {analysis.confidence_level}")
        print(f"  Stars: {'⭐' * int(analysis.star_rating * 2)}")
        print(f"  Bet Size: {analysis.recommended_bet_pct * 100:.1f}% of bankroll")
        
        if analysis.notes:
            print(f"\n📝 NOTES:")
            for note in analysis.notes:
                print(f"  • {note}")
        
        if analysis.warnings:
            print(f"\n⚠️ WARNINGS:")
            for warning in analysis.warnings:
                print(f"  ⚠️ {warning}")


def main():
    """Demo usage."""
    import sys
    from pathlib import Path
    
    print("=" * 70)
    print("INTEGRATED EDGE CALCULATOR - Billy Walters + Sharp Money")
    print("=" * 70)
    
    calculator = IntegratedEdgeCalculator()
    
    # Try to load Action Network data
    data_path = Path(__file__).parent.parent.parent.parent / 'data' / 'action_network' / 'nfl_odds_latest.json'
    
    if data_path.exists():
        games_loaded = calculator.load_action_network_data(data_path)
        print(f"✅ Loaded {games_loaded} games from Action Network")
    else:
        # Try the week13 file we just created
        alt_path = Path(__file__).parent.parent.parent.parent / 'data' / 'action_network' / 'week13_nfl_odds.json'
        if alt_path.exists():
            games_loaded = calculator.load_action_network_data(alt_path)
            print(f"✅ Loaded {games_loaded} games from Week 13 data")
        else:
            print("⚠️ No Action Network data found - running without sharp money signals")
    
    # Demo analysis: GB @ DET
    print("\n" + "=" * 70)
    print("DEMO ANALYSIS: GB @ DET")
    print("=" * 70)
    
    analysis = calculator.analyze_game(
        away_team="GB",
        home_team="DET",
        our_spread=-1.0,  # We think DET by 1 (slight favorite)
        market_spread=-2.5,  # Market has DET by 2.5
        sfactor_points=0.0  # No S-factors for this demo
    )
    
    calculator.print_analysis(analysis)
    
    # Demo with S-factors
    print("\n" + "=" * 70)
    print("DEMO WITH S-FACTORS: KC @ DAL")
    print("=" * 70)
    
    analysis = calculator.analyze_game(
        away_team="KC",
        home_team="DAL",
        our_spread=1.0,  # We think DAL slight underdog (KC by 1)
        market_spread=3.5,  # Market has DAL +3.5 (KC by 3.5)
        sfactor_points=7.5  # Dallas rest advantage, KC travel
    )
    
    calculator.print_analysis(analysis)


if __name__ == "__main__":
    main()
