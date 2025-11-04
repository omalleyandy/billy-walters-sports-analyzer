"""
Core Billy Walters Valuation System
Combines player valuations, injury impacts, and market analysis
"""

from typing import Dict, List, Optional, Tuple
from .player_values import PlayerValuation
from .injury_impacts import InjuryImpactCalculator, InjuryType
from .market_analysis import MarketAnalyzer


class BillyWaltersValuation:
    """
    Main valuation system combining all Billy Walters methodology
    
    Usage:
        >>> bw = BillyWaltersValuation()
        >>> value = bw.calculate_player_value(position='QB', tier='elite')
        >>> impact = bw.apply_injury_multiplier(value, 'Questionable', 'Ankle')
    """
    
    def __init__(self, sport: str = "NFL"):
        self.sport = sport
        self.player_valuation = PlayerValuation(sport)
        self.injury_calculator = InjuryImpactCalculator()
        self.market_analyzer = MarketAnalyzer()
    
    def calculate_player_value(
        self,
        position: str,
        tier: Optional[str] = None
    ) -> float:
        """
        Calculate player's point spread value
        
        Args:
            position: Player position (QB, RB, WR, etc.)
            tier: Player tier (elite, average, backup, etc.)
        
        Returns:
            Point spread value in points
        """
        return self.player_valuation.calculate_player_value(position, tier)
    
    def apply_injury_multiplier(
        self,
        player_value: float,
        injury_status: str,
        injury_description: str = "",
        days_since_injury: int = 0
    ) -> Tuple[float, float, str]:
        """
        Apply injury impact to player value
        
        Args:
            player_value: Base player value
            injury_status: Status (Out, Questionable, etc.)
            injury_description: Description (Ankle, Hamstring, etc.)
            days_since_injury: Days since injury occurred
        
        Returns:
            Tuple of (adjusted_value, impact, explanation)
        """
        injury_type = self.injury_calculator.parse_injury_status(
            injury_status, 
            injury_description
        )
        
        return self.injury_calculator.calculate_injury_impact(
            player_value,
            injury_type,
            days_since_injury
        )
    
    def calculate_team_impact(
        self,
        injuries: List[Dict],
        team_name: str = ""
    ) -> Dict:
        """
        Calculate comprehensive team injury impact
        
        Args:
            injuries: List of injury dicts from scraped data:
                - player_name: str
                - position: str
                - injury_status: str
                - injury_type: str (optional)
                - tier: str (optional)
            team_name: Team name for reference
        
        Returns:
            Comprehensive impact analysis dictionary
        """
        # Enrich injuries with player values
        enriched_injuries = []
        
        for injury in injuries:
            position = injury.get('position', 'Unknown')
            tier = injury.get('tier')
            
            # If no tier specified, try to determine from depth chart or use default
            if tier is None:
                # For now, assume starters (depth_chart_position=1)
                # This could be enhanced with actual depth chart data
                tier = self.player_valuation.determine_tier_from_depth_chart(
                    position, 
                    depth_chart_position=1
                )
            
            # Calculate player value
            player_value = self.calculate_player_value(position, tier)
            
            # Parse injury type
            injury_status = injury.get('injury_status', 'Questionable')
            injury_desc = injury.get('injury_type', '')
            injury_type = self.injury_calculator.parse_injury_status(
                injury_status,
                injury_desc
            )
            
            enriched_injuries.append({
                'name': injury.get('player_name', 'Unknown'),
                'position': position,
                'value': player_value,
                'injury_type': injury_type,
                'days_since_injury': injury.get('days_since_injury', 0)
            })
        
        # Calculate team impact
        team_analysis = self.injury_calculator.calculate_team_injury_impact(
            enriched_injuries
        )
        
        # Add position group crisis analysis
        position_impacts = {}
        for inj_detail in team_analysis['detailed_breakdown']:
            pos = inj_detail['position']
            impact = inj_detail['impact']
            position_impacts[pos] = position_impacts.get(pos, 0) + impact
        
        crises = self.market_analyzer.analyze_position_group_crisis(
            position_impacts
        )
        
        team_analysis['position_group_crises'] = crises
        team_analysis['team_name'] = team_name
        
        return team_analysis
    
    def analyze_game(
        self,
        home_team: str,
        away_team: str,
        home_injuries: List[Dict],
        away_injuries: List[Dict],
        actual_line_movement: float = 0.0,
        game_context: Dict = None
    ) -> Dict:
        """
        Complete game analysis with betting recommendations
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_injuries: List of home team injuries
            away_injuries: List of away team injuries
            actual_line_movement: How much the line moved (optional)
            game_context: Additional context (division, playoff, weather)
        
        Returns:
            Complete game analysis with betting edge
        """
        # Calculate each team's injury impact
        home_analysis = self.calculate_team_impact(home_injuries, home_team)
        away_analysis = self.calculate_team_impact(away_injuries, away_team)
        
        # Calculate betting edge
        edge_analysis = self.market_analyzer.calculate_betting_edge(
            home_injury_impact=home_analysis['total_impact'],
            away_injury_impact=away_analysis['total_impact'],
            actual_line_movement=actual_line_movement,
            game_context=game_context or {}
        )
        
        # Generate response
        total_game_impact = home_analysis['total_impact'] + away_analysis['total_impact']
        
        response = self.market_analyzer.generate_response(
            total_game_impact,
            {
                'home_team': home_team,
                'away_team': away_team,
                'total_impact': total_game_impact,
                'critical_count': len(home_analysis['critical_injuries']) + len(away_analysis['critical_injuries']),
                'team': home_team if home_analysis['total_impact'] > away_analysis['total_impact'] else away_team,
                'position_group': 'offensive line' if any('O-LINE' in c for c in home_analysis.get('position_group_crises', [])) else 'secondary',
                'market_move': actual_line_movement,
                'critical_players': ', '.join([
                    inj['name'] for inj in (home_analysis['critical_injuries'] + away_analysis['critical_injuries'])[:3]
                ]),
                'injured_count': home_analysis['injury_count'] + away_analysis['injury_count'],
                'specific_impact': edge_analysis['reasoning'],
                'recommendation': edge_analysis['recommended_side'],
                'bet_type': 'spread' if abs(edge_analysis['edge']) > 1 else 'total'
            }
        )
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_analysis': home_analysis,
            'away_analysis': away_analysis,
            'edge_analysis': edge_analysis,
            'assessment': response,
            'total_game_impact': total_game_impact
        }
    
    def format_game_output(self, game_analysis: Dict) -> str:
        """
        Format game analysis in Billy Walters style
        
        Args:
            game_analysis: Output from analyze_game()
        
        Returns:
            Formatted string for display
        """
        home = game_analysis['home_team']
        away = game_analysis['away_team']
        home_data = game_analysis['home_analysis']
        away_data = game_analysis['away_analysis']
        edge = game_analysis['edge_analysis']
        
        lines = []
        lines.append("═" * 80)
        lines.append(f"GAME: {away} @ {home}")
        lines.append("═" * 80)
        
        # Home team injuries
        lines.append(f"\nHOME TEAM ({home}) INJURIES:")
        if home_data['detailed_breakdown']:
            for inj in home_data['detailed_breakdown'][:5]:  # Top 5
                lines.append(
                    f"  • {inj['name']} ({inj['position']}): {inj['explanation']} "
                    f"(-{inj['impact']:.1f} pts from {inj['base_value']:.1f})"
                )
            lines.append(f"  TOTAL IMPACT: -{home_data['total_impact']} points")
        else:
            lines.append("  No significant injuries")
        
        # Position group crises for home
        if home_data.get('position_group_crises'):
            lines.append("\n  Position Group Impact:")
            for crisis in home_data['position_group_crises']:
                lines.append(f"    ⚠️  {crisis}")
        
        # Away team injuries
        lines.append(f"\nAWAY TEAM ({away}) INJURIES:")
        if away_data['detailed_breakdown']:
            for inj in away_data['detailed_breakdown'][:5]:  # Top 5
                lines.append(
                    f"  • {inj['name']} ({inj['position']}): {inj['explanation']} "
                    f"(-{inj['impact']:.1f} pts from {inj['base_value']:.1f})"
                )
            lines.append(f"  TOTAL IMPACT: -{away_data['total_impact']} points")
        else:
            lines.append("  No significant injuries")
        
        # Position group crises for away
        if away_data.get('position_group_crises'):
            lines.append("\n  Position Group Impact:")
            for crisis in away_data['position_group_crises']:
                lines.append(f"    ⚠️  {crisis}")
        
        # Edge analysis
        lines.append("\n" + "─" * 80)
        lines.append("BILLY WALTERS ANALYSIS:")
        lines.append("─" * 80)
        lines.append(f"Net Injury Advantage: {edge['net_injury_impact']:+.1f} points ({edge['reasoning']})")
        lines.append(f"Expected Line Movement: {edge['expected_line_movement']:.1f} points")
        lines.append(f"Actual Line Movement: {edge['actual_line_movement']:.1f} points")
        lines.append(f"EDGE: {edge['edge']:+.1f} points")
        lines.append(f"Confidence: {edge['confidence']}")
        lines.append(f"\nACTION: {edge['action']}")
        lines.append(f"Recommended Bet: {edge['recommended_side']}")
        lines.append(f"Bet Sizing: {edge['bet_sizing']}")
        lines.append(f"{edge['historical_context']}")
        
        return "\n".join(lines)

