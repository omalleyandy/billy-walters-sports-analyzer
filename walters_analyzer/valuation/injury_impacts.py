"""
Injury impact calculations based on Billy Walters' methodology
Converts injury status to specific capacity percentages and point spread impacts
"""

from enum import Enum
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from .config import get_injury_multipliers


class InjuryType(Enum):
    """Injury types with corresponding capacity impacts"""
    CONCUSSION = "Concussion"
    HAMSTRING = "Hamstring"
    KNEE_SPRAIN = "Knee Sprain"
    ACL = "ACL"
    MCL = "MCL"
    ANKLE_SPRAIN = "Ankle Sprain"
    HIGH_ANKLE = "High Ankle Sprain"
    GROIN = "Groin"
    QUADRICEPS = "Quadriceps"
    CALF = "Calf"
    ACHILLES = "Achilles"
    SHOULDER = "Shoulder"
    ELBOW = "Elbow"
    WRIST = "Wrist"
    HAND = "Hand"
    BACK = "Back"
    RIBS = "Ribs"
    HIP = "Hip"
    
    # Status designations
    QUESTIONABLE = "Questionable"
    DOUBTFUL = "Doubtful"
    OUT = "Out"
    IR = "Injured Reserve"
    
    # Unknown
    UNKNOWN = "Unknown"


class InjuryImpactCalculator:
    """Calculate injury impacts on player performance and point spreads"""
    
    def __init__(self):
        self.injury_multipliers = get_injury_multipliers()
    
    def parse_injury_status(self, status: str, description: str = "") -> InjuryType:
        """
        Parse injury status text to determine injury type
        
        Args:
            status: Injury status (Out, Questionable, etc.)
            description: Injury description (Ankle, Hamstring, etc.)
        
        Returns:
            InjuryType enum
        """
        # Combine status and description for parsing
        full_text = f"{status} {description}".lower()
        
        # Check for specific injury types first
        if 'acl' in full_text:
            return InjuryType.ACL
        elif 'mcl' in full_text:
            return InjuryType.MCL
        elif 'high ankle' in full_text:
            return InjuryType.HIGH_ANKLE
        elif 'ankle' in full_text:
            return InjuryType.ANKLE_SPRAIN
        elif 'hamstring' in full_text or 'hammy' in full_text:
            return InjuryType.HAMSTRING
        elif 'knee' in full_text:
            return InjuryType.KNEE_SPRAIN
        elif 'concussion' in full_text:
            return InjuryType.CONCUSSION
        elif 'groin' in full_text:
            return InjuryType.GROIN
        elif 'quad' in full_text:
            return InjuryType.QUADRICEPS
        elif 'calf' in full_text:
            return InjuryType.CALF
        elif 'achilles' in full_text:
            return InjuryType.ACHILLES
        elif 'shoulder' in full_text:
            return InjuryType.SHOULDER
        elif 'elbow' in full_text:
            return InjuryType.ELBOW
        elif 'wrist' in full_text:
            return InjuryType.WRIST
        elif 'hand' in full_text or 'finger' in full_text:
            return InjuryType.HAND
        elif 'back' in full_text:
            return InjuryType.BACK
        elif 'rib' in full_text or 'ribs' in full_text:
            return InjuryType.RIBS
        elif 'hip' in full_text:
            return InjuryType.HIP
        
        # Check status designations
        status_lower = status.lower()
        if 'out' in status_lower and 'doubtful' not in status_lower:
            return InjuryType.OUT
        elif 'injured reserve' in status_lower or 'ir' == status_lower:
            return InjuryType.IR
        elif 'doubtful' in status_lower:
            return InjuryType.DOUBTFUL
        elif 'questionable' in status_lower or 'probable' in status_lower:
            return InjuryType.QUESTIONABLE
        
        return InjuryType.UNKNOWN
    
    def calculate_injury_impact(
        self,
        player_value: float,
        injury_type: InjuryType,
        days_since_injury: int = 0
    ) -> Tuple[float, float, str]:
        """
        Calculate the impact of an injury on player value
        
        Args:
            player_value: Base player value in points
            injury_type: Type of injury
            days_since_injury: Days since injury occurred
        
        Returns:
            Tuple of (adjusted_value, impact, explanation)
            - adjusted_value: Current player value with injury
            - impact: Points lost due to injury
            - explanation: Human-readable explanation
        """
        if injury_type == InjuryType.UNKNOWN:
            # Default to questionable if unknown
            injury_type = InjuryType.QUESTIONABLE
        
        injury_key = injury_type.name
        if injury_key not in self.injury_multipliers:
            # Default to questionable multiplier
            injury_data = self.injury_multipliers.get('QUESTIONABLE', {
                'immediate': 0.92,
                'recovery_days': 0,
                'lingering': 0.98,
                'reinjury_risk': 1.0
            })
        else:
            injury_data = self.injury_multipliers[injury_key]
        
        immediate_capacity = injury_data.get('immediate', 0.92)
        recovery_days = injury_data.get('recovery_days', 0)
        lingering_capacity = injury_data.get('lingering', 0.98)
        
        # Calculate current capacity based on recovery timeline
        if injury_type == InjuryType.OUT:
            current_capacity = 0.0
            explanation = f"OUT - Full {player_value:.1f} point impact"
        elif injury_type == InjuryType.IR:
            current_capacity = 0.0
            explanation = f"Injured Reserve - Full {player_value:.1f} point impact"
        elif days_since_injury < recovery_days:
            # Still in recovery phase
            if recovery_days > 0:
                recovery_progress = days_since_injury / recovery_days
                current_capacity = immediate_capacity + (1.0 - immediate_capacity) * recovery_progress
            else:
                current_capacity = immediate_capacity
            
            capacity_pct = int(current_capacity * 100)
            explanation = (
                f"{injury_type.value}: {capacity_pct}% capacity "
                f"(Day {days_since_injury}/{recovery_days})"
            )
        elif days_since_injury < recovery_days + 14:
            # Post-recovery lingering effects (2 weeks after recovery)
            weeks_post = (days_since_injury - recovery_days) / 7
            current_capacity = lingering_capacity + (1.0 - lingering_capacity) * (weeks_post / 2)
            capacity_pct = int(current_capacity * 100)
            explanation = f"{injury_type.value}: Post-recovery at {capacity_pct}% capacity"
        else:
            # Fully recovered
            current_capacity = 1.0
            explanation = "Fully recovered"
        
        # Calculate adjusted value and impact
        adjusted_value = player_value * current_capacity
        impact = player_value - adjusted_value
        
        return adjusted_value, impact, explanation
    
    def calculate_team_injury_impact(
        self,
        injured_players: list
    ) -> Dict:
        """
        Calculate total team impact from multiple injuries
        
        Args:
            injured_players: List of dicts with player info:
                - name: Player name
                - position: Position
                - value: Base player value
                - injury_type: InjuryType enum
                - days_since_injury: Days since injury (optional)
        
        Returns:
            Dictionary with comprehensive injury analysis
        """
        total_impact = 0.0
        critical_injuries = []
        moderate_injuries = []
        minor_injuries = []
        detailed_breakdown = []
        
        for player in injured_players:
            player_value = player.get('value', 1.0)
            injury_type = player.get('injury_type', InjuryType.QUESTIONABLE)
            days_since = player.get('days_since_injury', 0)
            
            adjusted_value, impact, explanation = self.calculate_injury_impact(
                player_value, injury_type, days_since
            )
            
            total_impact += impact
            
            player_detail = {
                'name': player.get('name', 'Unknown'),
                'position': player.get('position', 'Unknown'),
                'base_value': player_value,
                'adjusted_value': adjusted_value,
                'impact': impact,
                'explanation': explanation,
                'injury_type': injury_type.value
            }
            
            detailed_breakdown.append(player_detail)
            
            # Categorize by severity
            if impact >= 2.0:
                critical_injuries.append(player_detail)
            elif impact >= 0.8:
                moderate_injuries.append(player_detail)
            elif impact > 0:
                minor_injuries.append(player_detail)
        
        # Determine severity level
        if total_impact >= 7.0:
            severity = "CRITICAL"
            confidence = "HIGH"
        elif total_impact >= 4.0:
            severity = "MAJOR"
            confidence = "HIGH"
        elif total_impact >= 2.0:
            severity = "MODERATE"
            confidence = "MEDIUM"
        elif total_impact >= 1.0:
            severity = "MINOR"
            confidence = "MEDIUM"
        else:
            severity = "NEGLIGIBLE"
            confidence = "LOW"
        
        return {
            'total_impact': round(total_impact, 1),
            'severity': severity,
            'confidence': confidence,
            'critical_injuries': critical_injuries,
            'moderate_injuries': moderate_injuries,
            'minor_injuries': minor_injuries,
            'detailed_breakdown': detailed_breakdown,
            'injury_count': len(injured_players)
        }
    
    def get_recovery_timeline(self, injury_type: InjuryType) -> int:
        """Get expected recovery days for an injury type"""
        injury_key = injury_type.name
        if injury_key in self.injury_multipliers:
            return self.injury_multipliers[injury_key].get('recovery_days', 0)
        return 0
    
    def get_reinjury_risk(self, injury_type: InjuryType) -> float:
        """Get reinjury risk multiplier for an injury type"""
        injury_key = injury_type.name
        if injury_key in self.injury_multipliers:
            return self.injury_multipliers[injury_key].get('reinjury_risk', 1.0)
        return 1.0

