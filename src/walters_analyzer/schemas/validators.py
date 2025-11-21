# ============================================================================
# Schema Validators for Billy Walters Sports Betting System
# ============================================================================

from typing import Any
from pydantic import BaseModel, field_validator
from walters_analyzer.models.core import BetRecommendation


class SchemaValidator:
    """
    Generic schema validator for bet recommendations.

    Validates both dictionaries and BetRecommendation objects against
    Billy Walters methodology rules:
    - Minimum 5.5% edge to place a bet
    - Maximum 3% stake per bet
    - Maximum 15% total portfolio exposure
    """

    def validate_bet_recommendation(self, rec_dict: dict) -> list[str]:
        """
        Validate a bet recommendation dictionary.

        Returns: List of error messages (empty if valid)
        """
        errors = []

        # Check required fields
        required_fields = [
            "recommendation_id",
            "game_id",
            "edge_percentage",
            "stake_fraction",
            "is_play",
        ]

        for field in required_fields:
            if field not in rec_dict:
                errors.append(f"Missing required field: {field}")

        if errors:
            return errors

        # Validate edge percentage
        edge = rec_dict.get("edge_percentage", 0)
        if not isinstance(edge, (int, float)):
            type_name = type(edge).__name__
            errors.append(f"edge_percentage must be numeric, got {type_name}")
        elif edge < 0:
            errors.append("edge_percentage cannot be negative")

        # Validate stake fraction
        stake = rec_dict.get("stake_fraction", 0)
        if not isinstance(stake, (int, float)):
            stake_type = type(stake).__name__
            errors.append(f"stake_fraction must be numeric, got {stake_type}")
        elif not 0 <= stake <= 0.03:
            errors.append(f"stake_fraction {stake:.2%} must be between 0 and 3%")

        # Validate is_play flag
        is_play = rec_dict.get("is_play", False)
        if is_play and edge < 5.5:
            errors.append(f"Cannot play with edge {edge}% < 5.5% minimum")

        # Validate bankroll if provided
        bankroll = rec_dict.get("bankroll")
        if bankroll:
            stake_amount = stake * bankroll
            max_stake = 0.03 * bankroll
            if stake_amount > max_stake:
                msg = f"Stake ${stake_amount:.2f} exceeds 3% max (${max_stake:.2f})"
                errors.append(msg)

        return errors

    def validate(self, rec: BetRecommendation) -> list[str]:
        """
        Validate a BetRecommendation object.

        Returns: List of error messages (empty if valid)
        """
        errors = []

        # Check edge percentage >= 5.5% for plays
        if rec.is_play and rec.edge_percentage < 5.5:
            errors.append(
                f"Cannot play with edge {rec.edge_percentage}% < 5.5% minimum"
            )

        # Check stake fraction <= 3%
        if rec.stake_fraction > 0.03:
            errors.append(f"Stake fraction {rec.stake_fraction:.2%} exceeds 3% max")

        # Check bankroll constraint
        if rec.bankroll and rec.bankroll > 0:
            stake_amount = rec.stake_fraction * rec.bankroll
            max_stake = 0.03 * rec.bankroll
            if stake_amount > max_stake:
                msg = f"Stake ${stake_amount:.2f} exceeds 3% max (${max_stake:.2f})"
                errors.append(msg)

        # Check recommendation_id exists
        if not rec.recommendation_id or not rec.recommendation_id.strip():
            errors.append("recommendation_id cannot be empty")

        return errors

    def validate_portfolio(self, portfolio: list[BetRecommendation]) -> dict[str, Any]:
        """
        Validate a portfolio of bet recommendations.

        Returns: Dict with validation results
        """
        results = {
            "errors": [],
            "warnings": [],
            "total_exposure_pct": 0.0,
            "max_single_bet_pct": 0.0,
            "num_bets": len(portfolio),
        }

        if not portfolio:
            return results

        # Get bankroll from first bet (assume all same)
        bankroll = portfolio[0].bankroll or 20000

        total_exposure = 0.0
        max_exposure = 0.0

        for i, rec in enumerate(portfolio):
            # Validate individual bet
            errors = self.validate(rec)
            if errors:
                results["errors"].extend([f"Bet {i + 1}: {e}" for e in errors])

            # Track exposure
            exposure_dollars = rec.stake_fraction * bankroll
            total_exposure += exposure_dollars
            max_exposure = max(max_exposure, exposure_dollars)

        # Calculate percentages
        results["total_exposure_pct"] = (total_exposure / bankroll) * 100
        results["max_single_bet_pct"] = (max_exposure / bankroll) * 100

        # Check limits
        if results["total_exposure_pct"] > 15.0:
            exposure_pct = results["total_exposure_pct"]
            results["errors"].append(
                f"Total exposure {exposure_pct:.1f}% exceeds 15% limit"
            )

        if results["max_single_bet_pct"] > 3.0:
            max_bet_pct = results["max_single_bet_pct"]
            results["errors"].append(
                f"Max single bet {max_bet_pct:.1f}% exceeds 3% limit"
            )

        if 10.0 < results["total_exposure_pct"] <= 15.0:
            exposure_pct = results["total_exposure_pct"]
            results["warnings"].append(
                f"Total exposure {exposure_pct:.1f}% is high (near 15% limit)"
            )

        return results


class BetRecommendationValidator(BaseModel):
    """
    Validates BetRecommendation objects for betting compliance.

    Rules enforced:
    - recommendation_id: Must be non-empty string
    - edge_percentage: Must be >= 5.5% for is_play=True
    - stake_fraction: Must be <= 3% of bankroll (hard cap)
    - bankroll: If provided, stake_fraction * bankroll <= 0.03 * bankroll
    - is_play: Only True if edge_percentage >= 5.5%
    """

    recommendation_id: str
    edge_percentage: float
    stake_fraction: float
    bankroll: float | None = None
    is_play: bool

    @field_validator("recommendation_id")
    @classmethod
    def validate_recommendation_id(cls, v: str) -> str:
        """Recommendation ID must be non-empty."""
        if not v or not v.strip():
            raise ValueError("recommendation_id cannot be empty")
        return v.strip()

    @field_validator("edge_percentage")
    @classmethod
    def validate_edge_percentage(cls, v: float) -> float:
        """Edge percentage must be non-negative."""
        if v < 0:
            raise ValueError("edge_percentage cannot be negative")
        return v

    @field_validator("stake_fraction")
    @classmethod
    def validate_stake_fraction(cls, v: float) -> float:
        """Stake fraction must be between 0 and 0.03 (3%)."""
        if not 0 <= v <= 0.03:
            raise ValueError("stake_fraction must be between 0 and 0.03 (3% max)")
        return v

    @field_validator("is_play")
    @classmethod
    def validate_is_play(cls, v: bool, info) -> bool:
        """
        is_play can only be True if edge_percentage >= 5.5%.

        Billy Walters methodology requires minimum 5.5% edge to make a bet.
        """
        if v and info.data.get("edge_percentage", 0) < 5.5:
            raise ValueError(
                f"is_play can only be True if edge_percentage >= 5.5%. "
                f"Current edge: {info.data.get('edge_percentage', 0)}%"
            )
        return v

    def validate_full_recommendation(self, rec: BetRecommendation) -> tuple[bool, str]:
        """
        Validate a BetRecommendation object against all Billy Walters rules.

        Returns: (is_valid: bool, message: str)
        """
        errors = []

        # Check 1: recommendation_id exists
        if not rec.recommendation_id or not rec.recommendation_id.strip():
            errors.append("recommendation_id must be non-empty")

        # Check 2: edge_percentage >= 5.5% for bets
        if rec.is_play and rec.edge_percentage < 5.5:
            errors.append(
                f"Cannot play with edge {rec.edge_percentage}% < 5.5% minimum"
            )

        # Check 3: stake_fraction <= 3%
        # Check 4: If bankroll provided, verify stake amount
        if rec.bankroll and rec.bankroll > 0:
            stake_amount = rec.stake_fraction * rec.bankroll
            max_stake = 0.03 * rec.bankroll
            if stake_amount > max_stake:
                msg = f"Stake ${stake_amount:.2f} exceeds 3% max (${max_stake:.2f})"
                errors.append(msg)

        if errors:
            message = " | ".join(errors)
            return (False, message)

        return (True, "All validation checks passed")


# Export validators
__all__ = ["SchemaValidator", "BetRecommendationValidator"]
