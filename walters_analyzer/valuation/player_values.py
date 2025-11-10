"""
Player position definitions and valuation calculations
Based on Billy Walters' methodology for quantifying player impact on point spreads
"""

from enum import Enum
from typing import Dict, Optional
from .config import get_position_values


class PlayerPosition(Enum):
    """NFL Player positions"""
    # Offense
    QB = "Quarterback"
    RB = "Running Back"
    WR = "Wide Receiver"
    TE = "Tight End"
    OL = "Offensive Line"
    LT = "Left Tackle"
    RT = "Right Tackle"
    C = "Center"
    G = "Guard"
    
    # Defense
    DL = "Defensive Line"
    DE = "Defensive End"
    DT = "Defensive Tackle"
    LB = "Linebacker"
    DB = "Defensive Back"
    CB = "Cornerback"
    S = "Safety"
    
    # Special Teams
    K = "Kicker"
    P = "Punter"
    
    # Generic/Unknown
    UNKNOWN = "Unknown"


class PlayerTier(Enum):
    """Player tier classifications"""
    # QB Tiers
    ELITE_QB = "elite"
    ABOVE_AVERAGE_QB = "above_average"
    AVERAGE_QB = "average"
    BACKUP_QB = "backup"
    
    # Skill Position Tiers
    ELITE_SKILL = "elite"
    ABOVE_AVERAGE_SKILL = "above_average"
    AVERAGE_SKILL = "average"
    BACKUP_SKILL = "backup"
    
    # WR Specific
    WR1 = "wr1"
    WR2 = "wr2"
    WR3 = "wr3"
    SLOT = "slot"
    
    # OL Specific
    LEFT_TACKLE = "left_tackle"
    CENTER = "center"
    GUARD = "guard"
    RIGHT_TACKLE = "right_tackle"
    
    # Defensive Specific
    ELITE_RUSHER = "elite_rusher"
    SHUTDOWN_CORNER = "shutdown_corner"
    CB1 = "cb1"
    CB2 = "cb2"
    NICKEL = "nickel"
    
    # Default
    AVERAGE = "average"


class PlayerValuation:
    """Calculate player spread value based on position and tier"""
    
    def __init__(self, sport: str = "NFL"):
        self.sport = sport
        self.position_values = get_position_values(sport)
    
    def calculate_player_value(
        self, 
        position: str, 
        tier: Optional[str] = None
    ) -> float:
        """
        Calculate a player's point spread value
        
        Args:
            position: Player position (QB, RB, WR, etc.)
            tier: Player tier (elite, average, backup, etc.)
        
        Returns:
            Point spread impact value
        
        Examples:
            >>> valuation = PlayerValuation()
            >>> valuation.calculate_player_value("QB", "elite")
            4.5
            >>> valuation.calculate_player_value("RB", "average")
            1.2
        """
        # Normalize position
        position = self._normalize_position(position)
        
        # Get position group values
        position_group = self._get_position_group(position)
        if position_group not in self.position_values:
            return 1.0  # Default value
        
        tier_values = self.position_values[position_group]
        
        # If no tier specified, use average
        if tier is None:
            tier = self._get_default_tier(position)
        
        # Get value for this tier
        value = tier_values.get(tier, tier_values.get('average', 1.0))
        
        return float(value)
    
    def _normalize_position(self, position: str) -> str:
        """Normalize position string"""
        position = position.upper().strip()
        
        # Map common variations
        position_map = {
            'QUARTERBACK': 'QB',
            'RUNNING BACK': 'RB',
            'RUNNINGBACK': 'RB',
            'WIDE RECEIVER': 'WR',
            'WIDERECEIVER': 'WR',
            'TIGHT END': 'TE',
            'TIGHTEND': 'TE',
            'OFFENSIVE LINE': 'OL',
            'OFFENSIVE LINEMAN': 'OL',
            'LEFT TACKLE': 'LT',
            'RIGHT TACKLE': 'RT',
            'CENTER': 'C',
            'GUARD': 'G',
            'DEFENSIVE LINE': 'DL',
            'DEFENSIVE END': 'DE',
            'DEFENSIVE TACKLE': 'DT',
            'LINEBACKER': 'LB',
            'CORNERBACK': 'CB',
            'CORNER BACK': 'CB',
            'SAFETY': 'S',
            'KICKER': 'K',
            'PUNTER': 'P',
        }
        
        return position_map.get(position, position)
    
    def _get_position_group(self, position: str) -> str:
        """Get position group for config lookup"""
        # Map positions to config keys
        group_map = {
            'QB': 'QUARTERBACK',
            'RB': 'RUNNING_BACK',
            'WR': 'WIDE_RECEIVER',
            'TE': 'TIGHT_END',
            'OL': 'OFFENSIVE_LINE',
            'LT': 'OFFENSIVE_LINE',
            'RT': 'OFFENSIVE_LINE',
            'C': 'OFFENSIVE_LINE',
            'G': 'OFFENSIVE_LINE',
            'DL': 'DEFENSIVE_LINE',
            'DE': 'DEFENSIVE_LINE',
            'DT': 'DEFENSIVE_LINE',
            'LB': 'LINEBACKER',
            'DB': 'DEFENSIVE_BACK',
            'CB': 'DEFENSIVE_BACK',
            'S': 'DEFENSIVE_BACK',
            'K': 'SPECIAL_TEAMS',
            'P': 'SPECIAL_TEAMS',
        }
        
        return group_map.get(position, 'UNKNOWN')
    
    def _get_default_tier(self, position: str) -> str:
        """Get default tier for a position when not specified"""
        if position == 'QB':
            return 'elite'  # Assume starter QB
        elif position in ['RB', 'WR', 'TE']:
            return 'above_average'
        elif position in ['LT', 'C']:
            return 'left_tackle' if position == 'LT' else 'center'
        elif position in ['CB', 'S']:
            return 'cb1'
        elif position in ['DE', 'DT']:
            return 'above_average'
        else:
            return 'average'
    
    def determine_tier_from_depth_chart(
        self, 
        position: str, 
        depth_chart_position: int = 1
    ) -> str:
        """
        Determine player tier based on depth chart position
        
        Args:
            position: Player position
            depth_chart_position: Position on depth chart (1 = starter)
        
        Returns:
            Tier string (elite, average, backup, etc.)
        """
        position = self._normalize_position(position)
        
        if position == 'QB':
            if depth_chart_position == 1:
                return 'elite'
            else:
                return 'backup'
        
        elif position == 'RB':
            if depth_chart_position == 1:
                return 'elite'
            elif depth_chart_position == 2:
                return 'above_average'
            else:
                return 'backup'
        
        elif position == 'WR':
            if depth_chart_position == 1:
                return 'wr1'
            elif depth_chart_position == 2:
                return 'wr2'
            else:
                return 'wr3'
        
        elif position == 'TE':
            if depth_chart_position == 1:
                return 'elite'
            else:
                return 'average'
        
        elif position in ['LT', 'C', 'RT', 'G', 'OL']:
            # For O-line, use specific position tiers
            if position == 'LT':
                return 'left_tackle'
            elif position == 'C':
                return 'center'
            elif position == 'G':
                return 'guard'
            elif position == 'RT':
                return 'right_tackle'
            else:
                return 'guard'
        
        elif position in ['CB', 'DB']:
            if depth_chart_position == 1:
                return 'shutdown_corner'
            elif depth_chart_position == 2:
                return 'cb1'
            else:
                return 'cb2'
        
        elif position in ['DE', 'DT', 'DL']:
            if depth_chart_position == 1:
                return 'elite_rusher'
            else:
                return 'above_average'
        
        else:
            return 'average'

