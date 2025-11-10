"""
Billy Walters Injury Scraper Integration
Connects scraped injury data to specific point spread valuations

This module bridges the gap between raw injury reports and
Billy Walters' quantitative betting edge calculations.
"""

import json
from typing import Dict, List, Optional
from pathlib import Path

from billy_walters_injury_valuation import (
    PlayerValue,
    InjuryStatus,
    PlayerPosition,
    InjuryImpact,
    TeamInjuryAnalyzer,
)

# Billy Walters' position-to-value mapping based on historical data
POSITION_VALUE_RANGES = {
    "QB": {
        "elite": (12.0, 17.0),  # Mahomes, Allen, Burrow
        "starter": (7.0, 12.0),  # Average starting QB
        "backup": (2.0, 5.0),  # Backup QB
    },
    "RB": {
        "elite": (5.0, 7.0),  # CMC, Henry, Chubb
        "starter": (3.0, 5.0),  # RB1
        "backup": (1.0, 2.5),  # RB2/RB3
    },
    "WR": {
        "elite": (4.0, 5.5),  # Jefferson, Chase, Hill
        "wr1": (3.0, 4.0),  # WR1
        "wr2": (2.0, 3.0),  # WR2
        "slot": (1.5, 2.5),  # Slot/WR3
    },
    "TE": {
        "elite": (3.5, 4.5),  # Kelce, Andrews
        "starter": (2.0, 3.0),  # TE1
        "backup": (0.5, 1.5),  # TE2
    },
    "OL": {
        "all_pro": (4.0, 5.0),  # All-Pro lineman
        "starter": (2.5, 3.5),  # Starting lineman
        "backup": (1.0, 2.0),  # Backup
    },
    "DL": {
        "elite_rusher": (3.5, 4.5),  # Garrett, Watt, Bosa
        "starter": (2.0, 3.0),  # Starting DL
        "rotational": (1.0, 2.0),  # Rotational
    },
    "LB": {
        "all_pro": (3.0, 4.0),  # All-Pro LB
        "starter": (2.0, 3.0),  # Starting LB
        "backup": (0.5, 1.5),  # Backup
    },
    "CB": {
        "shutdown": (3.0, 3.5),  # Shutdown corner
        "cb1": (2.5, 3.0),  # CB1
        "cb2": (1.5, 2.5),  # CB2
        "nickel": (1.0, 2.0),  # Nickel/Dime
    },
    "S": {
        "all_pro": (2.5, 3.5),  # All-Pro safety
        "starter": (1.5, 2.5),  # Starting safety
        "backup": (0.5, 1.5),  # Backup
    },
    "K": {
        "elite": (1.5, 2.0),  # Elite kicker
        "average": (0.5, 1.0),  # Average kicker
    },
    "P": {
        "elite": (1.0, 1.5),  # Elite punter
        "average": (0.3, 0.7),  # Average punter
    },
}


class InjuryDataEnricher:
    """Enriches scraped injury data with Billy Walters valuations"""

    def __init__(self, player_rankings_file: Optional[str] = None):
        """
        Initialize with optional player rankings data

        Args:
            player_rankings_file: Path to JSON file with player rankings/values
        """
        self.player_rankings = {}
        if player_rankings_file and Path(player_rankings_file).exists():
            with open(player_rankings_file, "r") as f:
                self.player_rankings = json.load(f)

    def parse_injury_status(self, status_text: str) -> InjuryStatus:
        """Convert scraped injury status to Billy Walters classification"""
        status_lower = status_text.lower().strip()

        # Direct mappings
        if "out" in status_lower:
            return InjuryStatus.OUT
        elif "doubtful" in status_lower:
            return InjuryStatus.DOUBTFUL
        elif "questionable" in status_lower or "gtd" in status_lower:
            return InjuryStatus.QUESTIONABLE
        elif "probable" in status_lower:
            return InjuryStatus.PROBABLE
        elif "ir" in status_lower or "injured reserve" in status_lower:
            return InjuryStatus.INJURED_RESERVE
        elif "day-to-day" in status_lower or "day to day" in status_lower:
            return InjuryStatus.DAY_TO_DAY
        else:
            return InjuryStatus.HEALTHY

    def parse_position(self, position_text: str) -> PlayerPosition:
        """Convert scraped position to enum"""
        pos_upper = position_text.upper().strip()

        position_map = {
            "QB": PlayerPosition.QB,
            "RB": PlayerPosition.RB,
            "WR": PlayerPosition.WR,
            "TE": PlayerPosition.TE,
            "OL": PlayerPosition.OL,
            "OT": PlayerPosition.OL,
            "OG": PlayerPosition.OL,
            "C": PlayerPosition.OL,
            "G": PlayerPosition.OL,
            "T": PlayerPosition.OL,
            "DL": PlayerPosition.DL,
            "DE": PlayerPosition.DL,
            "DT": PlayerPosition.DL,
            "NT": PlayerPosition.DL,
            "EDGE": PlayerPosition.DL,
            "LB": PlayerPosition.LB,
            "ILB": PlayerPosition.LB,
            "OLB": PlayerPosition.LB,
            "MLB": PlayerPosition.LB,
            "CB": PlayerPosition.CB,
            "DB": PlayerPosition.CB,
            "S": PlayerPosition.S,
            "FS": PlayerPosition.S,
            "SS": PlayerPosition.S,
            "K": PlayerPosition.K,
            "P": PlayerPosition.P,
        }

        for key, value in position_map.items():
            if key in pos_upper:
                return value

        return PlayerPosition.WR  # Default fallback

    def estimate_player_value(
        self, player_name: str, position: PlayerPosition, team: str, snap_pct: float = 0
    ) -> float:
        """
        Estimate player value using Billy Walters' methodology

        Uses:
        1. Known player rankings if available
        2. Snap count percentage
        3. Position-based estimates
        """
        # Check if we have specific player data
        player_key = f"{player_name}_{team}".lower()
        if player_key in self.player_rankings:
            return self.player_rankings[player_key]["value"]

        # Estimate based on snap percentage and position
        pos_key = position.name
        if snap_pct > 80:
            tier = "elite" if snap_pct > 95 else "starter"
        elif snap_pct > 50:
            tier = "starter"
        else:
            tier = "backup"

        # Get value range for position and tier
        if pos_key in POSITION_VALUE_RANGES:
            ranges = POSITION_VALUE_RANGES[pos_key]
            if tier in ranges:
                low, high = ranges[tier]
                # Use snap percentage to interpolate within range
                value = low + (high - low) * (snap_pct / 100)
                return round(value, 1)

        # Default fallback values by position
        default_values = {
            PlayerPosition.QB: 7.0,
            PlayerPosition.RB: 3.0,
            PlayerPosition.WR: 2.5,
            PlayerPosition.TE: 2.0,
            PlayerPosition.OL: 3.0,
            PlayerPosition.DL: 2.5,
            PlayerPosition.LB: 2.5,
            PlayerPosition.CB: 2.5,
            PlayerPosition.S: 2.0,
            PlayerPosition.K: 1.0,
            PlayerPosition.P: 0.5,
        }

        return default_values.get(position, 2.0)

    def process_injury_report(self, injury_data: Dict) -> InjuryImpact:
        """
        Process a single injury report into Billy Walters valuation

        Args:
            injury_data: Dict with keys: player_name, position, team, status,
                        snap_pct (optional), games_missed (optional)

        Returns:
            InjuryImpact object with calculated values
        """
        # Parse basic data
        position = self.parse_position(injury_data.get("position", ""))
        injury_status = self.parse_injury_status(injury_data.get("status", ""))
        snap_pct = injury_data.get("snap_pct", 75.0)  # Default 75% if not provided

        # Create player value object
        player = PlayerValue(
            name=injury_data["player_name"],
            position=position,
            team=injury_data["team"],
            base_value=self.estimate_player_value(
                injury_data["player_name"], position, injury_data["team"], snap_pct
            ),
            injury_status=injury_status,
            games_missed=injury_data.get("games_missed", 0),
            snap_percentage=snap_pct,
            performance_trend=injury_data.get("trend", 0.0),
        )

        # Estimate replacement value (typically 40-60% of starter)
        replacement_factor = {
            PlayerPosition.QB: 0.35,  # Huge dropoff at QB
            PlayerPosition.RB: 0.70,  # RBs more replaceable
            PlayerPosition.WR: 0.60,  # Depth usually available
            PlayerPosition.TE: 0.65,  # TEs often replaceable
            PlayerPosition.OL: 0.45,  # Big dropoff on OL
            PlayerPosition.DL: 0.55,  # Rotation exists
            PlayerPosition.LB: 0.55,  # Some depth usually
            PlayerPosition.CB: 0.40,  # Huge dropoff at CB
            PlayerPosition.S: 0.50,  # Moderate dropoff
            PlayerPosition.K: 0.80,  # Kickers replaceable
            PlayerPosition.P: 0.85,  # Punters very replaceable
        }.get(position, 0.5)

        replacement_value = player.base_value * replacement_factor

        # Calculate scheme and cohesion impacts
        scheme_fit_loss = 0.3  # Default moderate impact
        unit_cohesion_impact = 0.2  # Default low impact

        # Adjust for key positions
        if position == PlayerPosition.QB:
            scheme_fit_loss = 0.7  # QBs critical to scheme
        elif position == PlayerPosition.OL:
            unit_cohesion_impact = 0.8  # OL cohesion critical
        elif position == PlayerPosition.CB:
            scheme_fit_loss = 0.5  # Scheme can be exploited

        return InjuryImpact(
            player=player,
            replacement_value=replacement_value,
            scheme_fit_loss=scheme_fit_loss,
            unit_cohesion_impact=unit_cohesion_impact,
        )

    def analyze_game_injuries(
        self, home_injuries: List[Dict], away_injuries: List[Dict]
    ) -> Dict:
        """
        Analyze injuries for both teams and provide betting recommendations

        This is where Billy Walters' edge comes from - precise quantification
        instead of generic warnings
        """
        # Process home team injuries
        home_analyzer = TeamInjuryAnalyzer("Home Team")
        for injury_data in home_injuries:
            impact = self.process_injury_report(injury_data)
            home_analyzer.add_injury(impact)

        # Process away team injuries
        away_analyzer = TeamInjuryAnalyzer("Away Team")
        for injury_data in away_injuries:
            impact = self.process_injury_report(injury_data)
            away_analyzer.add_injury(impact)

        # Calculate impacts
        home_impact = home_analyzer.calculate_cumulative_impact()
        away_impact = away_analyzer.calculate_cumulative_impact()

        # Calculate net impact (negative favors away, positive favors home)
        net_impact = away_impact["total_impact"] - home_impact["total_impact"]

        # Generate Billy Walters-style recommendation
        recommendation = self._generate_recommendation(
            net_impact, home_impact, away_impact
        )

        return {
            "home_team_impact": home_impact,
            "away_team_impact": away_impact,
            "net_impact": round(net_impact, 2),
            "adjusted_spread": self._calculate_adjusted_spread(net_impact),
            "recommendation": recommendation,
            "confidence": self._calculate_confidence(home_impact, away_impact),
            "key_matchup_advantages": self._identify_key_advantages(
                home_impact, away_impact
            ),
        }

    def _generate_recommendation(
        self, net_impact: float, home_impact: Dict, away_impact: Dict
    ) -> str:
        """Generate specific Billy Walters-style betting recommendation"""

        # Check for significant edges
        if abs(net_impact) < 1.5:
            return "No significant injury edge - pass or small position only"

        if net_impact > 0:  # Home team advantage from injuries
            if net_impact > 7:
                return f"MAXIMUM BET HOME: Away team decimated (+{net_impact:.1f} point advantage)"
            elif net_impact > 4:
                return f"STRONG PLAY HOME: Significant injury edge (+{net_impact:.1f} points)"
            elif net_impact > 2.5:
                return f"BET HOME: Clear injury advantage (+{net_impact:.1f} points)"
            else:
                return f"LEAN HOME: Slight injury edge (+{net_impact:.1f} points)"
        else:  # Away team advantage
            if abs(net_impact) > 7:
                return f"MAXIMUM BET AWAY: Home team decimated ({net_impact:.1f} point advantage)"
            elif abs(net_impact) > 4:
                return f"STRONG PLAY AWAY: Significant injury edge ({net_impact:.1f} points)"
            elif abs(net_impact) > 2.5:
                return f"BET AWAY: Clear injury advantage ({net_impact:.1f} points)"
            else:
                return f"LEAN AWAY: Slight injury edge ({net_impact:.1f} points)"

    def _calculate_adjusted_spread(self, net_impact: float) -> str:
        """Calculate what the spread should be adjusted to"""
        if abs(net_impact) < 0.5:
            return "No adjustment needed"

        direction = "home" if net_impact > 0 else "away"
        adjustment = abs(net_impact)

        return f"Adjust {adjustment:.1f} points toward {direction}"

    def _calculate_confidence(self, home_impact: Dict, away_impact: Dict) -> str:
        """Calculate confidence level in the injury analysis"""
        total_injuries = home_impact["injury_count"] + away_impact["injury_count"]

        if total_injuries == 0:
            return "N/A - No injuries"
        elif total_injuries < 3:
            return "HIGH - Clear injury picture"
        elif total_injuries < 6:
            return "MEDIUM - Multiple factors at play"
        else:
            return "LOWER - Many variables, monitor closely"

    def _identify_key_advantages(
        self, home_impact: Dict, away_impact: Dict
    ) -> List[str]:
        """Identify specific matchup advantages from injuries"""
        advantages = []

        # Compare unit impacts
        home_units = home_impact.get("unit_impacts", {})
        away_units = away_impact.get("unit_impacts", {})

        # Check passing game advantage
        home_pass = home_units.get("passing_game", 0)
        away_pass_d = away_units.get("pass_defense", 0)
        if abs(home_pass - away_pass_d) > 2:
            if home_pass > away_pass_d:
                advantages.append(
                    "Away passing attack advantage due to home secondary injuries"
                )
            else:
                advantages.append(
                    "Home passing attack advantage due to away secondary injuries"
                )

        # Check running game advantage
        home_run = home_units.get("running_game", 0)
        away_run_d = away_units.get("run_defense", 0)
        if abs(home_run - away_run_d) > 2:
            if home_run > away_run_d:
                advantages.append(
                    "Away ground game advantage due to home front-7 injuries"
                )
            else:
                advantages.append(
                    "Home ground game advantage due to away front-7 injuries"
                )

        return (
            advantages if advantages else ["No significant unit mismatches identified"]
        )


# Example implementation
def demonstrate_enhanced_analysis():
    """Show the difference between generic and Billy Walters analysis"""

    print("=== Billy Walters Enhanced Injury Analysis ===\n")

    # Sample scraped injury data
    home_injuries = [
        {
            "player_name": "Dak Prescott",
            "position": "QB",
            "team": "Cowboys",
            "status": "Questionable",
            "snap_pct": 98,
            "games_missed": 0,
        },
        {
            "player_name": "Tyron Smith",
            "position": "OT",
            "team": "Cowboys",
            "status": "Out",
            "snap_pct": 85,
            "games_missed": 2,
        },
    ]

    away_injuries = [
        {
            "player_name": "Deebo Samuel",
            "position": "WR",
            "team": "49ers",
            "status": "Questionable",
            "snap_pct": 75,
            "games_missed": 1,
        }
    ]

    # Process with Billy Walters system
    enricher = InjuryDataEnricher()
    analysis = enricher.analyze_game_injuries(home_injuries, away_injuries)

    print("GENERIC SYSTEM OUTPUT:")
    print("  'High total injuries - unpredictable game, be cautious!'")
    print("  'Both teams have injuries, anything could happen!'")

    print("\nBILLY WALTERS SYSTEM OUTPUT:")
    print(f"  Net Impact: {analysis['net_impact']:+.1f} points")
    print(f"  Adjusted Spread: {analysis['adjusted_spread']}")
    print(f"  Recommendation: {analysis['recommendation']}")
    print(f"  Confidence: {analysis['confidence']}")
    print("  Key Advantages:")
    for advantage in analysis["key_matchup_advantages"]:
        print(f"    - {advantage}")

    print("\n=== Detailed Breakdown ===")
    print("\nHome Team (Cowboys):")
    home = analysis["home_team_impact"]
    print(f"  Total Impact: {home['total_impact']:+.1f} points")
    print(f"  Key Injuries: {len(home['key_injuries'])}")
    for injury in home["key_injuries"]:
        print(
            f"    - {injury['player']} ({injury['position']}): {injury['impact']:+.1f} pts"
        )

    print("\nAway Team (49ers):")
    away = analysis["away_team_impact"]
    print(f"  Total Impact: {away['total_impact']:+.1f} points")
    print(f"  Injuries: {away['injury_count']}")


if __name__ == "__main__":
    demonstrate_enhanced_analysis()
