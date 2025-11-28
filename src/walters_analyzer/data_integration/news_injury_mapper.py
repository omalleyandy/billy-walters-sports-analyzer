"""
News & Injury Data Mapper for E-Factor Integration

Converts raw news feed items and injury data into E-Factor parameters.
Maps coaching changes, personnel moves, injuries, and morale indicators
to quantifiable adjustments for the E-Factor calculator.

Mapping Logic:
- Coaching changes → coaching_change_this_week, interim_coach, team_response
- Key player injuries → key_player_out parameter, position-specific impact
- Personnel trades/releases → morale shift parameter
- Injury cascades → position_group_health parameter
- Playoff implications → can_clinch_playoff, risk_elimination parameters
- Winning/losing streaks → games_won, games_lost parameters

Usage:
    mapper = NewsInjuryMapper()

    # Map news items to E-Factor parameters
    efactor_inputs = mapper.map_news_to_efactor(news_items, game)

    # Map injuries to E-Factor impacts
    injury_adjustments = mapper.map_injuries_to_efactor(injuries, team)

    # Get morale shift from personnel changes
    morale = mapper.calculate_morale_shift(transactions, team)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from walters_analyzer.data_integration.news_feed_aggregator import (
    FeedItem,
    NewsCategory,
)

logger = logging.getLogger(__name__)


class Position(str):
    """Player positions for impact assessment."""

    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    OL = "OL"  # Offensive line
    DL = "DL"  # Defensive line
    EDGE = "EDGE"  # Edge rusher
    LB = "LB"
    DB = "DB"
    CB = "CB"
    S = "S"


class PlayerTier(str):
    """Player importance tier."""

    ELITE = "elite"  # Hall of Fame caliber
    STAR = "star"  # Pro Bowl, top 5 at position
    STARTER = "starter"  # Regular starter
    BACKUP = "backup"  # Backup/rotational
    DEPTH = "depth"  # Depth chart


@dataclass
class EFactorInputs:
    """E-Factor parameters mapped from news/injury data."""

    # Revenge game factors
    played_earlier: bool = False
    earlier_loss_margin: Optional[int] = None

    # Lookahead spot factors
    next_opponent_strength: Optional[float] = None
    next_game_playoff_implications: bool = False

    # Letdown spot factors
    coming_off_big_win: bool = False
    big_win_margin: Optional[int] = None

    # Coaching change factors (FROM NEWS)
    coaching_change_this_week: bool = False
    interim_coach: bool = True
    team_response: str = "neutral"  # "positive", "neutral", "negative"
    coaching_stability_score: float = 1.0  # 0.0 to 2.0

    # Playoff importance factors
    can_clinch_playoff: bool = False
    risk_elimination: bool = False
    playoff_position: str = "none"

    # Streaks (from recent results)
    games_won: int = 0
    games_lost: int = 0

    # NEW: Injury and personnel factors
    key_player_out: bool = False
    key_player_position: Optional[str] = None
    key_player_tier: Optional[str] = None
    key_player_impact: float = 0.0  # -8.0 to 0.0

    position_group_health: float = 1.0  # 0.6 to 1.0
    position_group_injuries: int = 0

    # NEW: Personnel change factors
    recent_transaction: bool = False
    transaction_type: str = ""  # "trade", "release", "signing"
    transaction_impact: float = 0.0  # -4.0 to 2.0

    morale_shift: float = 0.0  # -1.0 to 1.0


@dataclass
class InjuryData:
    """Injury information for a team."""

    team: str
    position: str
    player_name: str
    injury_type: str
    status: str  # "out", "doubtful", "questionable", "probable"
    practice_status: str  # "dnp", "limited", "full"
    days_out: int = 0
    is_key_player: bool = False
    tier: PlayerTier = PlayerTier.BACKUP


class NewsInjuryMapper:
    """Maps news and injury data to E-Factor parameters."""

    # Key player impact by position and tier
    KEY_PLAYER_IMPACT = {
        Position.QB: {
            PlayerTier.ELITE: -8.0,
            PlayerTier.STAR: -7.5,
            PlayerTier.STARTER: -6.0,
            PlayerTier.BACKUP: -2.0,
        },
        Position.RB: {
            PlayerTier.ELITE: -5.0,
            PlayerTier.STAR: -4.5,
            PlayerTier.STARTER: -3.0,
            PlayerTier.BACKUP: -1.0,
        },
        Position.WR: {
            PlayerTier.ELITE: -4.0,
            PlayerTier.STAR: -3.5,
            PlayerTier.STARTER: -2.0,
            PlayerTier.BACKUP: -0.5,
        },
        Position.EDGE: {
            PlayerTier.ELITE: -4.5,
            PlayerTier.STAR: -4.0,
            PlayerTier.STARTER: -2.5,
            PlayerTier.BACKUP: -0.5,
        },
        Position.CB: {
            PlayerTier.ELITE: -4.0,
            PlayerTier.STAR: -3.5,
            PlayerTier.STARTER: -2.0,
            PlayerTier.BACKUP: -0.5,
        },
    }

    # Injury severity modifiers
    INJURY_SEVERITY = {
        "out": 1.0,  # Full impact
        "out for season": 1.0,
        "doubtful": 0.9,
        "questionable": 0.5,
        "probable": 0.2,
        "dnp": 1.0,
        "limited": 0.6,
        "full": 0.0,
    }

    # Transaction impact by type and importance
    TRANSACTION_IMPACT = {
        "trade": {
            "elite": -4.0,
            "star": -3.0,
            "starter": -1.5,
            "backup": -0.5,
        },
        "release": {
            "elite": -3.5,
            "star": -2.5,
            "starter": -1.0,
            "backup": -0.2,
        },
        "signing": {
            "elite": 2.0,
            "star": 1.5,
            "starter": 0.8,
            "backup": 0.2,
        },
    }

    # Coaching change impact by time elapsed
    COACHING_STABILITY = {
        0: 0.6,  # Just happened - maximum disruption
        1: 0.7,
        2: 0.8,
        3: 0.85,
        4: 0.9,
        5: 0.95,
        6: 0.97,
        7: 1.0,  # After one week, stability returns
    }

    def __init__(self):
        """Initialize mapper."""
        self.known_key_players: Dict[str, List[str]] = {
            # NFL star QBs
            "KC": ["patrick mahomes"],
            "BUF": ["josh allen"],
            "DAL": ["dak prescott"],
            "PHI": ["jalen hurts"],
            "SF": ["brock purdy"],
            "LV": ["derek carr"],
            "LAC": ["justin herbert"],
            "MIA": ["tua tagovailoa"],
            "NYG": ["daniel jones"],
            "WAS": ["marcus mariota"],
            "GB": ["jordan love"],
            "MIN": ["kirk cousins"],
            "DET": ["jared goff"],
            "CHI": ["caleb williams"],
            "TB": ["baker mayfield"],
            "NO": ["derek carr"],
            "ATL": ["marcus mariota"],
            "CAR": ["bryce young"],
            "CIN": ["joe burrow"],
            "BAL": ["lamar jackson"],
            "PIT": ["kenny pickett"],
            "CLE": ["deshaun watson"],
            "IND": ["anthony richardson"],
            "TEN": ["will levis"],
            "HOU": ["c.j. stroud"],
            "DEN": ["russell wilson"],
            "LAR": ["matthew stafford"],
            "SEA": ["geno smith"],
            "NYJ": ["aaron rodgers"],
            "NE": ["mac jones"],
        }

    def map_news_to_efactor(
        self, news_items: List[FeedItem], team: str
    ) -> Dict[str, Any]:
        """
        Map news items to E-Factor parameters.

        Args:
            news_items: News items from aggregator
            team: Team code (e.g., "DAL")

        Returns:
            Dict of E-Factor parameter updates
        """
        efactor_data: Dict[str, Any] = {}

        for item in news_items:
            if not item.is_valid:
                continue

            if item.category == NewsCategory.COACHING_CHANGE:
                coaching_data = self._parse_coaching_change(item)
                efactor_data.update(coaching_data)

            elif item.category == NewsCategory.TRANSACTION:
                trans_data = self._parse_transaction(item)
                efactor_data.update(trans_data)

            elif item.category == NewsCategory.PLAYOFF_IMPLICATION:
                playoff_data = self._parse_playoff_implication(item)
                efactor_data.update(playoff_data)

        return efactor_data

    def map_injuries_to_efactor(
        self, injuries: List[InjuryData], team: str
    ) -> Dict[str, Any]:
        """
        Map injury data to E-Factor parameters.

        Args:
            injuries: Injury data for team
            team: Team code

        Returns:
            Dict of E-Factor parameter updates
        """
        efactor_data: Dict[str, Any] = {
            "key_player_out": False,
            "key_player_position": None,
            "key_player_tier": None,
            "key_player_impact": 0.0,
            "position_group_health": 1.0,
            "position_group_injuries": 0,
        }

        if not injuries:
            return efactor_data

        # Find key player injuries
        for injury in injuries:
            if injury.is_key_player and injury.status == "out":
                efactor_data["key_player_out"] = True
                efactor_data["key_player_position"] = injury.position
                efactor_data["key_player_tier"] = injury.tier

                # Get impact value
                impact = self.KEY_PLAYER_IMPACT.get(injury.position, {}).get(
                    injury.tier, -2.0
                )
                severity = self.INJURY_SEVERITY.get(injury.status, 0.5)
                efactor_data["key_player_impact"] = impact * severity

                logger.info(
                    f"Key player out: {injury.player_name} ({injury.position}) "
                    f"impact: {efactor_data['key_player_impact']:.1f}pts"
                )
                break

        # Calculate position group health
        position_injury_count: Dict[str, int] = {}
        for injury in injuries:
            if injury.status in ["out", "doubtful"]:
                position_injury_count[injury.position] = (
                    position_injury_count.get(injury.position, 0) + 1
                )

        efactor_data["position_group_injuries"] = len(
            [inj for inj in injuries if inj.status in ["out", "doubtful"]]
        )

        # Multiple injuries in key position groups = major impact
        if position_injury_count.get(Position.OL, 0) >= 2:
            efactor_data["position_group_health"] = 0.75

        elif position_injury_count.get(Position.EDGE, 0) >= 2:
            efactor_data["position_group_health"] = 0.80

        elif position_injury_count.get(Position.DB, 0) >= 2:
            efactor_data["position_group_health"] = 0.80

        elif efactor_data["position_group_injuries"] >= 3:
            efactor_data["position_group_health"] = 0.85

        return efactor_data

    def _parse_coaching_change(self, item: FeedItem) -> Dict[str, Any]:
        """
        Parse coaching change news item.

        Args:
            item: News item about coaching change

        Returns:
            Dict with coaching change parameters
        """
        data: Dict[str, Any] = {
            "coaching_change_this_week": True,
            "interim_coach": False,
            "team_response": "neutral",
            "coaching_stability_score": 1.0,
        }

        title_lower = item.title.lower()
        content_lower = f"{item.title} {item.summary}".lower()

        # Detect interim vs permanent
        if "interim" in title_lower or "interim" in content_lower:
            data["interim_coach"] = True
            data["coaching_stability_score"] = 0.6

        # Detect team response
        if any(
            word in content_lower
            for word in ["rally", "energized", "unite", "motivated"]
        ):
            data["team_response"] = "positive"
            data["coaching_stability_score"] = 0.8

        elif any(
            word in content_lower
            for word in ["confusion", "uncertainty", "frustration", "turmoil"]
        ):
            data["team_response"] = "negative"
            data["coaching_stability_score"] = 0.4

        logger.info(
            f"Coaching change detected: interim={data['interim_coach']}, "
            f"response={data['team_response']}"
        )

        return data

    def _parse_transaction(self, item: FeedItem) -> Dict[str, Any]:
        """
        Parse transaction (trade/release/signing) news item.

        Args:
            item: News item about transaction

        Returns:
            Dict with transaction parameters
        """
        data: Dict[str, Any] = {
            "recent_transaction": True,
            "transaction_type": "trade",
            "transaction_impact": 0.0,
            "morale_shift": 0.0,
        }

        title_lower = item.title.lower()

        # Detect transaction type
        if "trade" in title_lower:
            data["transaction_type"] = "trade"
            data["transaction_impact"] = -2.0  # Negative morale from losing player
            data["morale_shift"] = -0.3

        elif "release" in title_lower or "released" in title_lower:
            data["transaction_type"] = "release"
            data["transaction_impact"] = -1.0
            data["morale_shift"] = -0.2

        elif "sign" in title_lower or "signed" in title_lower:
            data["transaction_type"] = "signing"
            data["transaction_impact"] = 1.0  # Positive from adding player
            data["morale_shift"] = 0.2

        # Check if star player involved
        content_lower = f"{item.title} {item.summary}".lower()
        if any(
            word in content_lower for word in ["star", "pro bowl", "all-pro", "elite"]
        ):
            data["transaction_impact"] *= 1.5
            data["morale_shift"] *= 1.5

        logger.info(
            f"Transaction detected: {data['transaction_type']}, "
            f"impact: {data['transaction_impact']:.1f}pts"
        )

        return data

    def _parse_playoff_implication(self, item: FeedItem) -> Dict[str, Any]:
        """
        Parse playoff implication news item.

        Args:
            item: News item about playoff

        Returns:
            Dict with playoff parameters
        """
        data: Dict[str, Any] = {
            "can_clinch_playoff": False,
            "risk_elimination": False,
            "playoff_position": "fighting",
        }

        content_lower = f"{item.title} {item.summary}".lower()

        if "clinch" in content_lower:
            data["can_clinch_playoff"] = True
            data["playoff_position"] = "clinching"

        elif "elimination" in content_lower or "eliminated" in content_lower:
            data["risk_elimination"] = True
            data["playoff_position"] = "eliminated"

        elif "wild card" in content_lower:
            data["playoff_position"] = "wildcard"

        logger.info(f"Playoff implication detected: {data['playoff_position']}")

        return data

    def calculate_morale_shift(
        self,
        transactions: List[FeedItem],
        injuries: List[InjuryData],
        team: str,
    ) -> float:
        """
        Calculate overall morale shift from transactions and injuries.

        Args:
            transactions: Transaction news items
            injuries: Injury data
            team: Team code

        Returns:
            Morale shift value (-1.0 to 1.0)
        """
        morale = 0.0

        # Transaction impact
        for item in transactions:
            if item.category == NewsCategory.TRANSACTION:
                trans_data = self._parse_transaction(item)
                morale += trans_data.get("morale_shift", 0.0)

        # Injury impact on morale
        key_injuries = len([inj for inj in injuries if inj.is_key_player])
        if key_injuries > 0:
            morale -= min(key_injuries * 0.3, 0.9)

        # Clamp to [-1.0, 1.0]
        return max(-1.0, min(1.0, morale))

    def estimate_confidence_shift(
        self,
        news_items: List[FeedItem],
        recent_results: List[Dict[str, Any]],
    ) -> float:
        """
        Estimate team confidence shift from news and results.

        Args:
            news_items: All news items
            recent_results: Last 3-4 game results

        Returns:
            Confidence shift (-1.0 to 1.0)
        """
        confidence = 0.0

        # Positive news indicators
        positive_keywords = [
            "dominating",
            "explosive",
            "unstoppable",
            "historic",
            "record",
            "elite",
        ]
        negative_keywords = [
            "struggling",
            "collapse",
            "dysfunction",
            "crisis",
            "tumultuous",
            "chaotic",
        ]

        for item in news_items:
            content_lower = f"{item.title} {item.summary}".lower()
            for keyword in positive_keywords:
                if keyword in content_lower:
                    confidence += 0.1

            for keyword in negative_keywords:
                if keyword in content_lower:
                    confidence -= 0.1

        # Recent results impact
        if recent_results:
            wins = len([r for r in recent_results if r.get("win", False)])
            losses = len([r for r in recent_results if not r.get("win", False)])

            if wins >= 2:
                confidence += 0.2

            if losses >= 2:
                confidence -= 0.2

        # Clamp to [-1.0, 1.0]
        return max(-1.0, min(1.0, confidence))


def main() -> None:
    """Example usage."""
    mapper = NewsInjuryMapper()

    # Example injury data
    injuries = [
        InjuryData(
            team="DAL",
            position="QB",
            player_name="Dak Prescott",
            injury_type="ankle",
            status="out",
            practice_status="dnp",
            is_key_player=True,
            tier=PlayerTier.ELITE,
        ),
        InjuryData(
            team="DAL",
            position="WR",
            player_name="CeeDee Lamb",
            injury_type="hamstring",
            status="doubtful",
            practice_status="limited",
            is_key_player=True,
            tier=PlayerTier.STAR,
        ),
    ]

    # Map to E-Factor
    efactor_inputs = mapper.map_injuries_to_efactor(injuries, "DAL")
    print("Injury E-Factor Inputs:")
    for key, value in efactor_inputs.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
