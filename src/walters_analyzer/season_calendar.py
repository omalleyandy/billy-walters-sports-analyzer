"""
NFL and NCAAF season calendar utilities.

Automatically determines current week, season phase, and schedule information
based on the current date.
"""

from datetime import date, timedelta
from enum import Enum


class SeasonPhase(Enum):
    """Phase of the football season."""

    OFFSEASON = "offseason"
    PRESEASON = "preseason"
    REGULAR_SEASON = "regular_season"
    PLAYOFFS = "playoffs"
    SUPER_BOWL = "super_bowl"


class League(Enum):
    """Supported football leagues."""

    NFL = "NFL"
    NCAAF = "NCAAF"


# NFL 2025 Season Key Dates
# Week 1 starts Thursday, September 4, 2025
NFL_2025_WEEK_1_START = date(2025, 9, 4)
NFL_2025_REGULAR_SEASON_WEEKS = 18
NFL_2025_PLAYOFF_START = date(2026, 1, 10)  # Wild Card Weekend
NFL_2025_SUPER_BOWL = date(2026, 2, 8)  # Super Bowl LX

# NCAAF FBS 2025 Season Key Dates
# Week 0 starts Saturday, August 16, 2025 (some teams)
# Week 1 starts Saturday, August 23, 2025 (full slate begins)
# Note: This aligns with ESPN/media week numbering where Nov 22-28 = Week 14 (Rivalry Week)
NCAAF_2025_WEEK_0_START = date(2025, 8, 16)
NCAAF_2025_WEEK_1_START = date(2025, 8, 23)
NCAAF_2025_REGULAR_SEASON_WEEKS = 14  # Through Week 14
NCAAF_2025_CONFERENCE_CHAMPIONSHIP_WEEK = date(2025, 12, 6)
NCAAF_2025_PLAYOFF_START = date(2025, 12, 20)  # First Round
NCAAF_2025_NATIONAL_CHAMPIONSHIP = date(2026, 1, 20)


def get_nfl_week(target_date: date | None = None) -> int | None:
    """
    Calculate the current NFL week based on a date.

    Args:
        target_date: Date to check (defaults to today)

    Returns:
        Week number (1-18) or None if not in regular season

    Examples:
        >>> get_nfl_week(date(2025, 9, 4))  # Week 1 Thursday
        1
        >>> get_nfl_week(date(2025, 9, 7))  # Week 1 Sunday
        1
        >>> get_nfl_week(date(2025, 11, 9))  # Week 10
        10
    """
    if target_date is None:
        target_date = date.today()

    # Check if before season starts
    if target_date < NFL_2025_WEEK_1_START:
        return None

    # Check if after regular season ends
    regular_season_end = NFL_2025_WEEK_1_START + timedelta(
        weeks=NFL_2025_REGULAR_SEASON_WEEKS
    )
    if target_date >= regular_season_end:
        return None

    # Calculate weeks since season start
    days_since_start = (target_date - NFL_2025_WEEK_1_START).days
    week_number = (days_since_start // 7) + 1

    # Cap at 18 weeks
    return min(week_number, NFL_2025_REGULAR_SEASON_WEEKS)


def get_ncaaf_week(target_date: date | None = None) -> int | None:
    """
    Calculate the current NCAAF FBS week based on a date.

    Args:
        target_date: Date to check (defaults to today)

    Returns:
        Week number (0-14) or None if not in regular season
        Note: Week 0 exists for select early games

    Examples:
        >>> get_ncaaf_week(date(2025, 8, 23))  # Week 0
        0
        >>> get_ncaaf_week(date(2025, 8, 30))  # Week 1
        1
        >>> get_ncaaf_week(date(2025, 11, 15))  # Week 12
        12
    """
    if target_date is None:
        target_date = date.today()

    # Check if before season starts
    if target_date < NCAAF_2025_WEEK_0_START:
        return None

    # Check if after regular season ends
    regular_season_end = NCAAF_2025_WEEK_1_START + timedelta(
        weeks=NCAAF_2025_REGULAR_SEASON_WEEKS
    )
    if target_date >= regular_season_end:
        return None

    # Handle Week 0 (before Week 1 start)
    if target_date < NCAAF_2025_WEEK_1_START:
        return 0

    # Calculate weeks since Week 1 start
    days_since_week_1 = (target_date - NCAAF_2025_WEEK_1_START).days
    week_number = (days_since_week_1 // 7) + 1

    # Cap at 14 weeks
    return min(week_number, NCAAF_2025_REGULAR_SEASON_WEEKS)


def get_nfl_season_phase(target_date: date | None = None) -> SeasonPhase:
    """
    Determine the current phase of the NFL season.

    Args:
        target_date: Date to check (defaults to today)

    Returns:
        SeasonPhase enum value
    """
    if target_date is None:
        target_date = date.today()

    # Check Super Bowl
    if target_date == NFL_2025_SUPER_BOWL:
        return SeasonPhase.SUPER_BOWL

    # Check playoffs
    regular_season_end = NFL_2025_WEEK_1_START + timedelta(
        weeks=NFL_2025_REGULAR_SEASON_WEEKS
    )
    if NFL_2025_PLAYOFF_START <= target_date < NFL_2025_SUPER_BOWL:
        return SeasonPhase.PLAYOFFS

    # Check regular season
    if NFL_2025_WEEK_1_START <= target_date < regular_season_end:
        return SeasonPhase.REGULAR_SEASON

    # Check preseason (roughly August)
    preseason_start = NFL_2025_WEEK_1_START - timedelta(days=30)
    if preseason_start <= target_date < NFL_2025_WEEK_1_START:
        return SeasonPhase.PRESEASON

    # Otherwise offseason
    return SeasonPhase.OFFSEASON


def get_ncaaf_season_phase(target_date: date | None = None) -> SeasonPhase:
    """
    Determine the current phase of the NCAAF season.

    Args:
        target_date: Date to check (defaults to today)

    Returns:
        SeasonPhase enum value
    """
    if target_date is None:
        target_date = date.today()

    # Check National Championship
    if target_date == NCAAF_2025_NATIONAL_CHAMPIONSHIP:
        return SeasonPhase.SUPER_BOWL  # Using SUPER_BOWL for championship game

    # Check playoffs
    regular_season_end = NCAAF_2025_WEEK_1_START + timedelta(
        weeks=NCAAF_2025_REGULAR_SEASON_WEEKS
    )
    if NCAAF_2025_PLAYOFF_START <= target_date < NCAAF_2025_NATIONAL_CHAMPIONSHIP:
        return SeasonPhase.PLAYOFFS

    # Check regular season (including Week 0)
    if NCAAF_2025_WEEK_0_START <= target_date < regular_season_end:
        return SeasonPhase.REGULAR_SEASON

    # Check preseason (roughly July-early August)
    preseason_start = NCAAF_2025_WEEK_0_START - timedelta(days=30)
    if preseason_start <= target_date < NCAAF_2025_WEEK_0_START:
        return SeasonPhase.PRESEASON

    # Otherwise offseason
    return SeasonPhase.OFFSEASON


def get_week_date_range(week: int, league: League = League.NFL) -> tuple[date, date]:
    """
    Get the date range (start, end) for a given week.

    NFL weeks run Thursday to Wednesday.
    NCAAF weeks run Saturday to Friday.

    Args:
        week: Week number (1-18 for NFL, 0-14 for NCAAF)
        league: League (NFL or NCAAF)

    Returns:
        Tuple of (start_date, end_date)
    """
    if league == League.NFL:
        if not 1 <= week <= NFL_2025_REGULAR_SEASON_WEEKS:
            raise ValueError(f"Week must be 1-{NFL_2025_REGULAR_SEASON_WEEKS}")

        week_start = NFL_2025_WEEK_1_START + timedelta(weeks=week - 1)
        week_end = week_start + timedelta(days=6)  # Thursday to Wednesday
        return (week_start, week_end)

    elif league == League.NCAAF:
        if not 0 <= week <= NCAAF_2025_REGULAR_SEASON_WEEKS:
            raise ValueError(f"Week must be 0-{NCAAF_2025_REGULAR_SEASON_WEEKS}")

        if week == 0:
            week_start = NCAAF_2025_WEEK_0_START
            week_end = NCAAF_2025_WEEK_1_START - timedelta(days=1)
        else:
            week_start = NCAAF_2025_WEEK_1_START + timedelta(weeks=week - 1)
            week_end = week_start + timedelta(days=6)  # Saturday to Friday

        return (week_start, week_end)

    else:
        raise ValueError(f"Unknown league: {league}")


def format_season_status(
    target_date: date | None = None, league: League = League.NFL
) -> str:
    """
    Get a human-readable status of the current season.

    Args:
        target_date: Date to check (defaults to today)
        league: League to check (NFL or NCAAF)

    Returns:
        Formatted status string

    Examples:
        >>> format_season_status(date(2025, 11, 9), League.NFL)
        'NFL 2025 Regular Season - Week 10 (Nov 6-12, 2025)'
        >>> format_season_status(date(2025, 11, 15), League.NCAAF)
        'NCAAF FBS 2025 Regular Season - Week 12 (Nov 15-21, 2025)'
    """
    if target_date is None:
        target_date = date.today()

    if league == League.NFL:
        phase = get_nfl_season_phase(target_date)
        week = get_nfl_week(target_date)

        if phase == SeasonPhase.REGULAR_SEASON and week:
            start, end = get_week_date_range(week, League.NFL)
            return (
                f"NFL 2025 Regular Season - Week {week} "
                f"({start.strftime('%b %d')}-{end.strftime('%d, %Y')})"
            )
        elif phase == SeasonPhase.PLAYOFFS:
            return "NFL 2025 Playoffs"
        elif phase == SeasonPhase.SUPER_BOWL:
            return f"Super Bowl LX - {NFL_2025_SUPER_BOWL.strftime('%B %d, %Y')}"
        elif phase == SeasonPhase.PRESEASON:
            return "NFL 2025 Preseason"
        else:
            return "NFL Offseason"

    elif league == League.NCAAF:
        phase = get_ncaaf_season_phase(target_date)
        week = get_ncaaf_week(target_date)

        if phase == SeasonPhase.REGULAR_SEASON and week is not None:
            start, end = get_week_date_range(week, League.NCAAF)
            return (
                f"NCAAF FBS 2025 Regular Season - Week {week} "
                f"({start.strftime('%b %d')}-{end.strftime('%d, %Y')})"
            )
        elif phase == SeasonPhase.PLAYOFFS:
            return "NCAAF FBS 2025 College Football Playoff"
        elif phase == SeasonPhase.SUPER_BOWL:
            champ_date = NCAAF_2025_NATIONAL_CHAMPIONSHIP.strftime("%B %d, %Y")
            return f"CFP National Championship - {champ_date}"
        elif phase == SeasonPhase.PRESEASON:
            return "NCAAF FBS 2025 Preseason"
        else:
            return "NCAAF FBS Offseason"

    else:
        raise ValueError(f"Unknown league: {league}")


if __name__ == "__main__":
    # Test with current date
    today = date.today()
    print(f"Today: {today.strftime('%B %d, %Y')}")
    print()
    print("NFL Status:")
    print(f"  {format_season_status(league=League.NFL)}")
    print(f"  Week: {get_nfl_week()}")
    print(f"  Phase: {get_nfl_season_phase().value}")
    print()
    print("NCAAF FBS Status:")
    print(f"  {format_season_status(league=League.NCAAF)}")
    print(f"  Week: {get_ncaaf_week()}")
    print(f"  Phase: {get_ncaaf_season_phase().value}")
