"""
NCAAF Injury Impact Calculator

College football specific injury values based on:
- Position importance in college game
- Backup quality (much lower than NFL)
- Roster depth (limited compared to NFL)
- Skill gaps between starter and backup

Key differences from NFL:
- QB injuries are more devastating (5.0 pts vs NFL 4.5)
- Backup QBs significantly worse than starters
- Roster depth limited (FCS players don't move up easily)
- Star RB/WR impacts higher due to game design
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class NCAAFInjuryImpacts:
    """Calculate NCAAF-specific injury impacts"""

    # Position-specific injury point values (larger than NFL due to depth)
    POSITION_VALUES = {
        # Quarterbacks (most critical in college)
        "QB": {
            "elite": 5.0,  # Top-tier starter (5-star recruit)
            "starter": 3.5,  # Primary backup
            "backup": 1.0,  # Third string
        },
        # Running Backs (team identity critical)
        "RB": {
            "elite": 3.5,  # Elite every-down back
            "starter": 2.0,  # Good backup
            "backup": 0.5,
        },
        # Wide Receivers (top target)
        "WR": {
            "elite": 2.5,  # #1 WR
            "starter": 1.5,  # #2-3 WR
            "backup": 0.3,
        },
        # Tight Ends (key receiving option)
        "TE": {
            "elite": 2.0,
            "starter": 1.2,
            "backup": 0.3,
        },
        # Offensive Line (group depth critical)
        "OL": {
            "elite": 1.5,  # Key anchor (LT/C)
            "starter": 1.0,  # Good starter
            "backup": 0.3,
        },
        # Defensive Line
        "DL": {
            "elite": 2.0,  # Pass rush leader
            "starter": 1.2,  # Consistent starter
            "backup": 0.3,
        },
        # Linebackers (coverage leaders)
        "LB": {
            "elite": 1.8,  # Coverage leader
            "starter": 1.0,  # Good starter
            "backup": 0.3,
        },
        # Defensive Backs
        "DB": {
            "elite": 1.5,  # Top corner
            "starter": 0.8,
            "backup": 0.2,
        },
    }

    # Severity classifications
    SEVERITY_LEVELS = {
        "out_for_season": 4.5,  # Maximum impact
        "out_4_weeks": 3.5,
        "out_2_weeks": 2.0,
        "out_1_week": 1.0,
        "questionable": 0.3,
    }

    def __init__(self):
        """Initialize NCAAF injury impact calculator"""
        self.logger = logging.getLogger(__name__)

    async def calculate_impact(
        self, away_team: str, home_team: str, injuries_data: Dict[str, List[Dict]]
    ) -> float:
        """
        Calculate net injury impact (away team perspective).

        Positive = away team hurt more (plays toward home)
        Negative = home team hurt more (plays toward away)

        Args:
            away_team: Away team name
            home_team: Home team name
            injuries_data: Dict {team_name: [injuries]}

        Returns:
            Net injury adjustment in points
        """
        try:
            away_injuries = injuries_data.get(away_team, [])
            home_injuries = injuries_data.get(home_team, [])

            away_impact = self._calculate_team_impact(away_team, away_injuries)
            home_impact = self._calculate_team_impact(home_team, home_injuries)

            # Net impact (positive = away team hurt more)
            net_impact = away_impact - home_impact

            if abs(net_impact) > 0.1:
                self.logger.debug(
                    f"{away_team} injury impact: {away_impact:.1f}, "
                    f"{home_team} injury impact: {home_impact:.1f}, "
                    f"Net: {net_impact:.1f}"
                )

            return net_impact

        except Exception as e:
            self.logger.warning(f"Error calculating injury impact: {e}")
            return 0.0

    def _calculate_team_impact(
        self, team: str, injuries: List[Dict]
    ) -> float:
        """
        Calculate total injury impact for a single team.

        Args:
            team: Team name
            injuries: List of injury dicts from ESPN data

        Returns:
            Total impact in points
        """
        if not injuries:
            return 0.0

        total_impact = 0.0

        for injury in injuries:
            try:
                player_name = injury.get("player", "Unknown")
                position = injury.get("position", "").upper()
                status = injury.get("status", "").lower()

                # Get position value
                if position not in self.POSITION_VALUES:
                    # Default to role player
                    base_value = 0.5
                else:
                    base_value = self._get_position_value(position)

                # Determine severity multiplier
                severity = self._classify_severity(status)
                severity_mult = self.SEVERITY_LEVELS.get(severity, 0.0)

                # Calculate impact
                impact = base_value * severity_mult

                if impact > 0:
                    self.logger.debug(
                        f"{team} {player_name} ({position}): "
                        f"{severity} = {impact:.1f} pts"
                    )

                total_impact += impact

            except Exception as e:
                self.logger.warning(f"Error processing injury {injury}: {e}")
                continue

        return total_impact

    def _get_position_value(self, position: str) -> float:
        """
        Get injury value for position.

        Args:
            position: Position code (QB, RB, WR, etc.)

        Returns:
            Base injury value in points
        """
        position_upper = position.upper()

        # Check direct position
        if position_upper in self.POSITION_VALUES:
            # Default to starter level
            return self.POSITION_VALUES[position_upper].get("starter", 1.0)

        # Check position category
        for pos_code, values in self.POSITION_VALUES.items():
            if pos_code in position_upper:
                return values.get("starter", 1.0)

        # Default
        return 0.5

    def _classify_severity(self, status: str) -> str:
        """
        Classify injury severity based on status.

        Args:
            status: Injury status string (Out, Questionable, etc.)

        Returns:
            Severity classification
        """
        status_lower = status.lower()

        if any(x in status_lower for x in ["season", "out for season", "redshirt"]):
            return "out_for_season"
        elif any(x in status_lower for x in ["4 weeks", "month", "extended"]):
            return "out_4_weeks"
        elif any(x in status_lower for x in ["2 weeks", "two weeks"]):
            return "out_2_weeks"
        elif any(x in status_lower for x in ["week", "1 week", "out"]):
            return "out_1_week"
        elif any(
            x in status_lower for x in ["question", "probable", "day-to-day"]
        ):
            return "questionable"
        else:
            return "questionable"

    def get_critical_injuries(
        self, team: str, injuries: List[Dict]
    ) -> List[Dict]:
        """
        Get list of critical injuries (≥2.0 points impact).

        Args:
            team: Team name
            injuries: List of injury dicts

        Returns:
            List of critical injuries
        """
        critical = []

        for injury in injuries:
            try:
                position = injury.get("position", "").upper()
                status = injury.get("status", "").lower()

                base_value = self._get_position_value(position)
                severity = self._classify_severity(status)
                severity_mult = self.SEVERITY_LEVELS.get(severity, 0.0)

                impact = base_value * severity_mult

                if impact >= 2.0:
                    critical.append(
                        {
                            "player": injury.get("player", "Unknown"),
                            "position": position,
                            "status": status,
                            "impact": impact,
                        }
                    )
            except Exception as e:
                self.logger.warning(f"Error classifying injury {injury}: {e}")
                continue

        return critical

    def summarize_injuries(
        self, team: str, injuries: List[Dict]
    ) -> Dict[str, any]:
        """
        Generate injury summary for a team.

        Args:
            team: Team name
            injuries: List of injury dicts

        Returns:
            Summary dict with injury breakdown
        """
        total_impact = self._calculate_team_impact(team, injuries)
        critical = self.get_critical_injuries(team, injuries)

        return {
            "team": team,
            "total_impact": total_impact,
            "critical_injuries": critical,
            "injury_count": len(injuries),
            "severity": self._classify_team_severity(total_impact),
        }

    def _classify_team_severity(self, impact: float) -> str:
        """
        Classify overall team injury severity.

        Args:
            impact: Total injury impact in points

        Returns:
            Severity classification
        """
        if impact >= 10:
            return "CRITICAL"
        elif impact >= 5:
            return "MAJOR"
        elif impact >= 2:
            return "MODERATE"
        elif impact >= 0.5:
            return "MINOR"
        else:
            return "NEGLIGIBLE"
