"""
ESPN Data Validation

Validates and sanitizes ESPN API responses with comprehensive quality checks.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ESPNTeamValidated(BaseModel):
    """Validated ESPN team data."""

    id: str
    name: str
    abbreviation: str
    location: str | None = None
    nickname: str | None = None
    logo: str | None = None
    league: str
    source: str = "espn"
    fetch_time: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate team ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Team ID cannot be empty")
        return v.strip()

    @field_validator("name", "abbreviation")
    @classmethod
    def validate_required_string(cls, v: str) -> str:
        """Validate required string fields."""
        if not v or not v.strip():
            raise ValueError(f"Required field cannot be empty: {v}")
        return v.strip()

    @field_validator("league")
    @classmethod
    def validate_league(cls, v: str) -> str:
        """Validate league is NFL or NCAAF."""
        if v not in ["NFL", "NCAAF"]:
            raise ValueError(f"Invalid league: {v}. Must be NFL or NCAAF")
        return v


class ESPNGameValidated(BaseModel):
    """Validated ESPN game data."""

    id: str
    name: str | None = None
    short_name: str | None = None
    date: str
    status: str
    home_team_id: str
    home_team_name: str
    home_team_score: int | None = None
    away_team_id: str
    away_team_name: str
    away_team_score: int | None = None
    venue_name: str | None = None
    venue_city: str | None = None
    venue_state: str | None = None
    is_indoor: bool | None = None
    league: str
    week: int | None = None
    season: int | None = None
    source: str = "espn"
    fetch_time: str

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate game ID."""
        if not v or not v.strip():
            raise ValueError("Game ID cannot be empty")
        return v.strip()

    @field_validator("home_team_score", "away_team_score")
    @classmethod
    def validate_score(cls, v: int | None) -> int | None:
        """Validate scores are realistic."""
        if v is not None:
            if not 0 <= v <= 150:
                raise ValueError(f"Unrealistic score: {v}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate game status."""
        valid_statuses = [
            "scheduled",
            "in_progress",
            "final",
            "postponed",
            "canceled",
            "pre",
            "in",
            "post",
        ]
        if v.lower() not in valid_statuses:
            logger.warning(f"Unknown game status: {v}")
        return v


class ESPNStatsValidated(BaseModel):
    """Validated ESPN team statistics."""

    team_id: str
    team_name: str | None = None
    league: str
    season: int | None = None

    # Offensive stats
    points_per_game: float | None = None
    yards_per_game: float | None = None
    passing_yards_per_game: float | None = None
    rushing_yards_per_game: float | None = None
    turnovers: int | None = None
    third_down_pct: float | None = None
    red_zone_pct: float | None = None

    # Defensive stats
    points_allowed_per_game: float | None = None
    yards_allowed_per_game: float | None = None
    sacks: int | None = None
    interceptions: int | None = None
    fumbles_recovered: int | None = None

    # Record
    wins: int | None = None
    losses: int | None = None
    ties: int | None = None

    source: str = "espn"
    fetch_time: str

    @field_validator("team_id")
    @classmethod
    def validate_team_id(cls, v: str) -> str:
        """Validate team ID."""
        if not v or not v.strip():
            raise ValueError("Team ID cannot be empty")
        return v.strip()

    @field_validator("league")
    @classmethod
    def validate_league(cls, v: str) -> str:
        """Validate league."""
        if v not in ["NFL", "NCAAF"]:
            raise ValueError(f"Invalid league: {v}")
        return v

    @field_validator(
        "points_per_game",
        "yards_per_game",
        "passing_yards_per_game",
        "rushing_yards_per_game",
        "points_allowed_per_game",
        "yards_allowed_per_game",
    )
    @classmethod
    def validate_positive_float(cls, v: float | None) -> float | None:
        """Validate positive float stats."""
        if v is not None and v < 0:
            raise ValueError(f"Stat cannot be negative: {v}")
        return v

    @field_validator("third_down_pct", "red_zone_pct")
    @classmethod
    def validate_percentage(cls, v: float | None) -> float | None:
        """Validate percentage stats."""
        if v is not None:
            if not 0 <= v <= 100:
                raise ValueError(f"Invalid percentage: {v}")
        return v


class DataQualityReport(BaseModel):
    """Data quality assessment report."""

    source: str
    data_type: str
    total_records: int
    valid_records: int
    invalid_records: int
    validation_errors: list[str] = Field(default_factory=list)
    completeness_score: float = 0.0  # 0-100
    quality_score: float = 0.0  # 0-100
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    @property
    def validation_rate(self) -> float:
        """Calculate validation success rate."""
        if self.total_records == 0:
            return 0.0
        return (self.valid_records / self.total_records) * 100

    @property
    def is_acceptable(self) -> bool:
        """Check if data quality is acceptable (>80% validation rate)."""
        return self.validation_rate >= 80.0


class ESPNDataValidator:
    """
    Validates ESPN API responses and generates quality reports.

    Features:
    - Schema validation with Pydantic
    - Completeness checking
    - Data quality scoring
    - Detailed error reporting
    """

    @staticmethod
    def validate_teams(
        raw_data: list[dict[str, Any]],
    ) -> tuple[list[ESPNTeamValidated], DataQualityReport]:
        """
        Validate team data with quality report.

        Args:
            raw_data: Raw team data from ESPN API

        Returns:
            Tuple of (validated_teams, quality_report)
        """
        validated = []
        errors = []

        for i, team_data in enumerate(raw_data):
            try:
                validated_team = ESPNTeamValidated(**team_data)
                validated.append(validated_team)
            except Exception as e:
                error_msg = f"Team {i}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)

        # Calculate completeness
        if validated:
            completeness_scores = []
            for team in validated:
                fields = ["name", "abbreviation", "location", "nickname", "logo"]
                filled = sum(
                    1 for f in fields if getattr(team, f, None) is not None
                )
                completeness_scores.append((filled / len(fields)) * 100)
            completeness = sum(completeness_scores) / len(completeness_scores)
        else:
            completeness = 0.0

        report = DataQualityReport(
            source="espn",
            data_type="teams",
            total_records=len(raw_data),
            valid_records=len(validated),
            invalid_records=len(errors),
            validation_errors=errors[:10],  # Limit to 10 errors
            completeness_score=completeness,
            quality_score=(
                (len(validated) / len(raw_data)) * 100 if raw_data else 0.0
            ),
        )

        return validated, report

    @staticmethod
    def validate_games(
        raw_data: list[dict[str, Any]],
    ) -> tuple[list[ESPNGameValidated], DataQualityReport]:
        """
        Validate game data with quality report.

        Args:
            raw_data: Raw game data from ESPN API

        Returns:
            Tuple of (validated_games, quality_report)
        """
        validated = []
        errors = []

        for i, game_data in enumerate(raw_data):
            try:
                validated_game = ESPNGameValidated(**game_data)
                validated.append(validated_game)
            except Exception as e:
                error_msg = f"Game {i}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)

        # Calculate completeness
        if validated:
            completeness_scores = []
            for game in validated:
                optional_fields = [
                    "venue_name",
                    "venue_city",
                    "venue_state",
                    "week",
                    "season",
                ]
                filled = sum(
                    1
                    for f in optional_fields
                    if getattr(game, f, None) is not None
                )
                completeness_scores.append(
                    (filled / len(optional_fields)) * 100
                )
            completeness = sum(completeness_scores) / len(completeness_scores)
        else:
            completeness = 0.0

        report = DataQualityReport(
            source="espn",
            data_type="games",
            total_records=len(raw_data),
            valid_records=len(validated),
            invalid_records=len(errors),
            validation_errors=errors[:10],
            completeness_score=completeness,
            quality_score=(
                (len(validated) / len(raw_data)) * 100 if raw_data else 0.0
            ),
        )

        return validated, report

    @staticmethod
    def validate_stats(
        raw_data: list[dict[str, Any]],
    ) -> tuple[list[ESPNStatsValidated], DataQualityReport]:
        """
        Validate statistics data with quality report.

        Args:
            raw_data: Raw stats data from ESPN API

        Returns:
            Tuple of (validated_stats, quality_report)
        """
        validated = []
        errors = []

        for i, stats_data in enumerate(raw_data):
            try:
                validated_stats = ESPNStatsValidated(**stats_data)
                validated.append(validated_stats)
            except Exception as e:
                error_msg = f"Stats {i}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)

        # Calculate completeness
        if validated:
            completeness_scores = []
            for stats in validated:
                stat_fields = [
                    "points_per_game",
                    "yards_per_game",
                    "passing_yards_per_game",
                    "rushing_yards_per_game",
                    "points_allowed_per_game",
                    "yards_allowed_per_game",
                ]
                filled = sum(
                    1
                    for f in stat_fields
                    if getattr(stats, f, None) is not None
                )
                completeness_scores.append((filled / len(stat_fields)) * 100)
            completeness = sum(completeness_scores) / len(completeness_scores)
        else:
            completeness = 0.0

        report = DataQualityReport(
            source="espn",
            data_type="statistics",
            total_records=len(raw_data),
            valid_records=len(validated),
            invalid_records=len(errors),
            validation_errors=errors[:10],
            completeness_score=completeness,
            quality_score=(
                (len(validated) / len(raw_data)) * 100 if raw_data else 0.0
            ),
        )

        return validated, report


# Example usage
def example_validation():
    """Example of data validation."""
    # Sample raw data
    teams_data = [
        {
            "id": "1",
            "name": "Kansas City Chiefs",
            "abbreviation": "KC",
            "location": "Kansas City",
            "nickname": "Chiefs",
            "logo": "https://example.com/logo.png",
            "league": "NFL",
            "fetch_time": "2025-01-01T00:00:00",
        },
        {
            "id": "",  # Invalid - empty ID
            "name": "Invalid Team",
            "abbreviation": "INV",
            "league": "NFL",
            "fetch_time": "2025-01-01T00:00:00",
        },
    ]

    # Validate
    validator = ESPNDataValidator()
    validated_teams, report = validator.validate_teams(teams_data)

    print(f"\nValidation Results:")
    print(f"  Total: {report.total_records}")
    print(f"  Valid: {report.valid_records}")
    print(f"  Invalid: {report.invalid_records}")
    print(f"  Validation Rate: {report.validation_rate:.1f}%")
    print(f"  Completeness: {report.completeness_score:.1f}%")
    print(f"  Quality Score: {report.quality_score:.1f}%")
    print(f"  Is Acceptable: {report.is_acceptable}")

    if report.validation_errors:
        print(f"\nErrors:")
        for error in report.validation_errors:
            print(f"  - {error}")


if __name__ == "__main__":
    example_validation()
