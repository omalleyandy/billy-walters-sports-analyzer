"""
Billy Walters Player Valuation & Injury Impact System
Based on Advanced Master Class Methodology

This module implements Billy Walters' sophisticated approach to:
1. Player valuations with specific point spreads
2. Injury impact calculations beyond generic warnings
3. Quantitative assessment of game dynamics
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import math
from datetime import datetime, timedelta

class InjuryStatus(Enum):
    """Billy Walters injury classification system"""
    OUT = "out"
    DOUBTFUL = "doubtful"
    QUESTIONABLE = "questionable"
    PROBABLE = "probable"
    HEALTHY = "healthy"
    DAY_TO_DAY = "day-to-day"
    INJURED_RESERVE = "IR"

class PlayerPosition(Enum):
    """NFL positions with valuation weights"""
    QB = "quarterback"
    RB = "running_back"
    WR = "wide_receiver"
    TE = "tight_end"
    OL = "offensive_line"
    DL = "defensive_line"
    LB = "linebacker"
    CB = "cornerback"
    S = "safety"
    K = "kicker"
    P = "punter"

@dataclass
class PlayerValue:
    """Billy Walters player valuation model"""
    name: str
    position: PlayerPosition
    team: str
    base_value: float  # Points above replacement
    injury_status: InjuryStatus
    games_missed: int = 0
    snap_percentage: float = 0.0
    performance_trend: float = 0.0  # -1 to 1 scale
    
    def calculate_actual_value(self) -> float:
        """
        Calculate player's actual value based on Billy Walters' formula:
        - Starting QB: 7-14 points
        - Elite QB: Up to 17 points
        - Star RB: 4-7 points
        - WR1: 3-5 points
        - Elite Pass Rusher: 3-4 points
        - Shutdown Corner: 2.5-3.5 points
        - Offensive Line (unit): 3-6 points
        """
        # Base injury multiplier from Billy Walters' system
        injury_multipliers = {
            InjuryStatus.OUT: 0.0,
            InjuryStatus.DOUBTFUL: 0.15,
            InjuryStatus.QUESTIONABLE: 0.45,
            InjuryStatus.PROBABLE: 0.75,
            InjuryStatus.HEALTHY: 1.0,
            InjuryStatus.DAY_TO_DAY: 0.65,
            InjuryStatus.INJURED_RESERVE: 0.0
        }
        
        injury_factor = injury_multipliers.get(self.injury_status, 0.5)
        
        # Snap count adjustment (Walters emphasizes actual playing time)
        snap_adjustment = self.snap_percentage / 100.0 if self.snap_percentage > 0 else 1.0
        
        # Recent performance trend adjustment
        trend_adjustment = 1.0 + (self.performance_trend * 0.25)
        
        # Games missed decay factor (players lose value after missing games)
        missed_game_decay = math.exp(-0.15 * self.games_missed)
        
        return self.base_value * injury_factor * snap_adjustment * trend_adjustment * missed_game_decay

@dataclass
class InjuryImpact:
    """Billy Walters injury impact assessment"""
    player: PlayerValue
    replacement_value: float  # Value of backup player
    scheme_fit_loss: float  # How much the scheme suffers (0-1)
    unit_cohesion_impact: float  # Impact on unit performance (0-1)
    
    def calculate_total_impact(self) -> Dict[str, float]:
        """
        Calculate the true impact of an injury using Billy Walters' methodology
        Returns specific point spread adjustments, not generic warnings
        """
        player_value = self.player.calculate_actual_value()
        
        # Direct value loss
        direct_loss = self.player.base_value - self.replacement_value
        
        # Scheme impact (some players are irreplaceable in certain schemes)
        scheme_adjustment = direct_loss * self.scheme_fit_loss
        
        # Unit cohesion (especially important for OL)
        cohesion_adjustment = direct_loss * self.unit_cohesion_impact * 0.5
        
        # Position-specific multipliers from Billy Walters
        position_multipliers = {
            PlayerPosition.QB: 1.5,    # QB injuries have outsized impact
            PlayerPosition.OL: 1.3,    # OL injuries affect entire offense
            PlayerPosition.CB: 1.2,    # CB injuries can be exploited
            PlayerPosition.LB: 1.1,    # LB injuries affect run defense
            PlayerPosition.RB: 0.9,    # RBs are more replaceable
            PlayerPosition.WR: 0.95,   # WRs depend on scheme
            PlayerPosition.TE: 0.85,   # TEs are often replaceable
            PlayerPosition.DL: 1.15,   # Pass rush is critical
            PlayerPosition.S: 1.05,    # Safety help is important
            PlayerPosition.K: 1.0,     # Kickers are binary
            PlayerPosition.P: 0.7      # Punters least impactful
        }
        
        position_mult = position_multipliers.get(self.player.position, 1.0)
        
        # Calculate final point spread adjustment
        total_impact = (direct_loss + scheme_adjustment + cohesion_adjustment) * position_mult
        
        # Calculate confidence level based on injury certainty
        confidence = {
            InjuryStatus.OUT: 1.0,
            InjuryStatus.DOUBTFUL: 0.85,
            InjuryStatus.QUESTIONABLE: 0.5,
            InjuryStatus.PROBABLE: 0.25,
            InjuryStatus.DAY_TO_DAY: 0.4,
            InjuryStatus.INJURED_RESERVE: 1.0,
            InjuryStatus.HEALTHY: 0.0
        }.get(self.player.injury_status, 0.5)
        
        return {
            "point_spread_adjustment": round(total_impact, 2),
            "confidence_level": confidence,
            "direct_value_loss": round(direct_loss, 2),
            "scheme_impact": round(scheme_adjustment, 2),
            "unit_impact": round(cohesion_adjustment, 2),
            "recommendation": self._get_betting_recommendation(total_impact, confidence)
        }
    
    def _get_betting_recommendation(self, impact: float, confidence: float) -> str:
        """Generate specific betting recommendation based on impact"""
        if confidence < 0.3:
            return f"Monitor status - low confidence ({confidence:.1%})"
        
        if abs(impact) < 1.0:
            return f"Minimal impact ({impact:+.1f} points) - no line adjustment needed"
        elif abs(impact) < 2.5:
            return f"Moderate impact ({impact:+.1f} points) - consider if line moves {impact:+.1f}"
        elif abs(impact) < 4.0:
            return f"Significant impact ({impact:+.1f} points) - STRONG PLAY if line doesn't adjust"
        else:
            return f"MAJOR impact ({impact:+.1f} points) - MAX BET opportunity if line is stale"

class TeamInjuryAnalyzer:
    """Analyze cumulative injury impact for entire team"""
    
    def __init__(self, team_name: str):
        self.team_name = team_name
        self.injuries: List[InjuryImpact] = []
        
    def add_injury(self, injury: InjuryImpact):
        """Add an injury to analyze"""
        self.injuries.append(injury)
    
    def calculate_cumulative_impact(self) -> Dict[str, any]:
        """
        Calculate total team impact using Billy Walters' approach
        Accounts for injury clustering and compound effects
        """
        if not self.injuries:
            return {
                "total_impact": 0,
                "injury_count": 0,
                "key_injuries": [],
                "recommendation": "Team at full strength"
            }
        
        # Sum individual impacts
        total_impact = sum(inj.calculate_total_impact()["point_spread_adjustment"] 
                          for inj in self.injuries)
        
        # Check for injury clustering (multiple injuries in same unit)
        position_groups = {
            "offensive_line": [PlayerPosition.OL],
            "defensive_line": [PlayerPosition.DL],
            "secondary": [PlayerPosition.CB, PlayerPosition.S],
            "linebackers": [PlayerPosition.LB],
            "receivers": [PlayerPosition.WR, PlayerPosition.TE],
            "backfield": [PlayerPosition.RB]
        }
        
        cluster_multiplier = 1.0
        for group_name, positions in position_groups.items():
            group_injuries = [inj for inj in self.injuries 
                             if inj.player.position in positions]
            if len(group_injuries) >= 2:
                # Multiple injuries in same unit compound the effect
                cluster_multiplier += 0.15 * (len(group_injuries) - 1)
        
        # Apply clustering effect
        adjusted_impact = total_impact * cluster_multiplier
        
        # Identify key injuries (> 2 point impact)
        key_injuries = [
            {
                "player": inj.player.name,
                "position": inj.player.position.value,
                "impact": inj.calculate_total_impact()["point_spread_adjustment"]
            }
            for inj in self.injuries
            if abs(inj.calculate_total_impact()["point_spread_adjustment"]) >= 2.0
        ]
        
        # Generate specific recommendation
        if abs(adjusted_impact) < 3:
            recommendation = f"Minor injury impact ({adjusted_impact:+.1f} pts) - line likely accurate"
        elif abs(adjusted_impact) < 6:
            recommendation = f"Moderate injury burden ({adjusted_impact:+.1f} pts) - fade if line hasn't moved"
        elif abs(adjusted_impact) < 10:
            recommendation = f"SEVERE injury situation ({adjusted_impact:+.1f} pts) - STRONG FADE"
        else:
            recommendation = f"CATASTROPHIC injuries ({adjusted_impact:+.1f} pts) - MAX BET AGAINST"
        
        return {
            "total_impact": round(adjusted_impact, 2),
            "injury_count": len(self.injuries),
            "clustering_multiplier": round(cluster_multiplier, 2),
            "key_injuries": key_injuries,
            "unit_impacts": self._calculate_unit_impacts(),
            "recommendation": recommendation
        }
    
    def _calculate_unit_impacts(self) -> Dict[str, float]:
        """Calculate impact by unit"""
        units = {
            "passing_game": [PlayerPosition.QB, PlayerPosition.WR, PlayerPosition.TE, PlayerPosition.OL],
            "running_game": [PlayerPosition.RB, PlayerPosition.OL],
            "pass_defense": [PlayerPosition.CB, PlayerPosition.S, PlayerPosition.DL],
            "run_defense": [PlayerPosition.LB, PlayerPosition.DL]
        }
        
        unit_impacts = {}
        for unit_name, positions in units.items():
            unit_injuries = [inj for inj in self.injuries 
                            if inj.player.position in positions]
            if unit_injuries:
                impact = sum(inj.calculate_total_impact()["point_spread_adjustment"] 
                           for inj in unit_injuries)
                unit_impacts[unit_name] = round(impact, 2)
        
        return unit_impacts

# Example usage showing Billy Walters' specific valuations
def demonstrate_injury_analysis():
    """Show how to properly value injuries with specific examples"""
    
    # Example: Star QB injury
    mahomes = PlayerValue(
        name="Patrick Mahomes",
        position=PlayerPosition.QB,
        team="Chiefs",
        base_value=14.5,  # Elite QB value
        injury_status=InjuryStatus.QUESTIONABLE,
        games_missed=0,
        snap_percentage=98,
        performance_trend=0.8
    )
    
    mahomes_injury = InjuryImpact(
        player=mahomes,
        replacement_value=4.5,  # Backup QB value
        scheme_fit_loss=0.8,   # System heavily relies on Mahomes
        unit_cohesion_impact=0.6  # Affects entire offense
    )
    
    print("=== Billy Walters Injury Valuation System ===\n")
    print(f"Player: {mahomes.name} ({mahomes.position.value})")
    print(f"Status: {mahomes.injury_status.value}")
    print(f"Base Value: {mahomes.base_value} points")
    
    impact = mahomes_injury.calculate_total_impact()
    print(f"\nInjury Impact Analysis:")
    print(f"  Point Spread Adjustment: {impact['point_spread_adjustment']:+.2f} points")
    print(f"  Confidence Level: {impact['confidence_level']:.1%}")
    print(f"  Direct Value Loss: {impact['direct_value_loss']:.2f} points")
    print(f"  Scheme Impact: {impact['scheme_impact']:.2f} points")
    print(f"  Unit Impact: {impact['unit_impact']:.2f} points")
    print(f"  Betting Recommendation: {impact['recommendation']}")
    
    # Example: Multiple offensive line injuries
    print("\n=== Offensive Line Injury Cluster Analysis ===\n")
    
    team_analyzer = TeamInjuryAnalyzer("Chiefs")
    
    # Add OL injuries
    for i, (name, value) in enumerate([
        ("Joe Thuney", 3.5),
        ("Creed Humphrey", 4.0),
        ("Trey Smith", 3.0)
    ]):
        player = PlayerValue(
            name=name,
            position=PlayerPosition.OL,
            team="Chiefs",
            base_value=value,
            injury_status=InjuryStatus.QUESTIONABLE if i == 0 else InjuryStatus.OUT,
            snap_percentage=95,
            performance_trend=0.2
        )
        injury = InjuryImpact(
            player=player,
            replacement_value=1.5,
            scheme_fit_loss=0.7,
            unit_cohesion_impact=0.9  # OL cohesion critical
        )
        team_analyzer.add_injury(injury)
    
    team_impact = team_analyzer.calculate_cumulative_impact()
    print(f"Team: {team_analyzer.team_name}")
    print(f"Total Injuries: {team_impact['injury_count']}")
    print(f"Cumulative Impact: {team_impact['total_impact']:+.2f} points")
    print(f"Clustering Multiplier: {team_impact['clustering_multiplier']}x")
    print(f"Recommendation: {team_impact['recommendation']}")
    print(f"\nUnit Impacts:")
    for unit, impact in team_impact['unit_impacts'].items():
        print(f"  {unit}: {impact:+.2f} points")

if __name__ == "__main__":
    demonstrate_injury_analysis()
