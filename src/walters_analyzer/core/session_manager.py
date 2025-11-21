"""
Session Management System
Provides continuity across analysis sessions with state tracking and recovery.

This module implements the session management system that enables:
- Creating new analysis sessions with full context
- Saving session state incrementally
- Restoring previous sessions seamlessly
- Tracking analysis progress and completion
- Maintaining continuity across interruptions
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """
    Complete context for a betting analysis session.

    Tracks all state necessary to resume work after interruption:
    - Session identification and timing
    - Week and season being analyzed
    - Current bankroll state
    - Active bets and opportunities
    - Analysis completion status
    - Session notes and decisions

    Attributes:
        session_id: Unique identifier (format: SEASON_weekWEEK_TIMESTAMP)
        start_time: When session was created
        last_updated: Most recent update timestamp
        week: NFL/NCAAF week number being analyzed
        season: Year of the season
        bankroll: Current bankroll amount
        active_bets: List of bet IDs currently active
        pending_opportunities: List of opportunity IDs awaiting decision
        power_ratings_updated: Whether Week N-1 ratings applied
        injuries_checked: Whether latest injury reports reviewed
        weather_checked: Whether weather forecasts reviewed
        opportunities_identified: Count of 5.5%+ edge opportunities
        bets_placed: Count of bets actually placed
        total_risk_deployed: Total $ at risk across all bets
        notes: List of timestamped session notes
        metadata: Additional flexible metadata
    """

    session_id: str
    start_time: datetime
    last_updated: datetime
    week: int
    season: int
    bankroll: float
    active_bets: List[str] = field(default_factory=list)
    pending_opportunities: List[str] = field(default_factory=list)
    power_ratings_updated: bool = False
    injuries_checked: bool = False
    weather_checked: bool = False
    opportunities_identified: int = 0
    bets_placed: int = 0
    total_risk_deployed: float = 0.0
    notes: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_note(self, note: str, category: str = "general") -> None:
        """Add a timestamped note to the session"""
        self.notes.append(
            {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "note": note,
            }
        )
        self.last_updated = datetime.now()

    def mark_power_ratings_updated(self) -> None:
        """Mark that power ratings have been updated"""
        self.power_ratings_updated = True
        self.add_note("Power ratings updated with Week {week-1} results", "analysis")

    def mark_injuries_checked(self) -> None:
        """Mark that injury reports have been checked"""
        self.injuries_checked = True
        self.add_note("Latest injury reports reviewed", "data")

    def mark_weather_checked(self) -> None:
        """Mark that weather forecasts have been reviewed"""
        self.weather_checked = True
        self.add_note("Weather forecasts checked for outdoor games", "data")

    def add_opportunity(self, opportunity_id: str) -> None:
        """Add a new betting opportunity"""
        if opportunity_id not in self.pending_opportunities:
            self.pending_opportunities.append(opportunity_id)
            self.opportunities_identified += 1
            self.last_updated = datetime.now()

    def place_bet(self, bet_id: str, amount: float) -> None:
        """Record that a bet has been placed"""
        if bet_id in self.pending_opportunities:
            self.pending_opportunities.remove(bet_id)

        self.active_bets.append(bet_id)
        self.bets_placed += 1
        self.total_risk_deployed += amount
        self.last_updated = datetime.now()

        # Risk management check
        risk_pct = (self.total_risk_deployed / self.bankroll) * 100
        if risk_pct > 15.0:
            logger.warning(
                f"Weekly risk exposure {risk_pct:.1f}% exceeds 15% limit!",
                extra={"session_id": self.session_id, "risk_pct": risk_pct},
            )

    def is_ready_for_analysis(self) -> tuple:
        """
        Check if session is ready for edge analysis.

        Returns:
            (ready, blocking_items) tuple where:
            - ready: True if all prerequisites met
            - blocking_items: List of items preventing readiness
        """
        blocking = []

        if not self.power_ratings_updated:
            blocking.append("Power ratings need Week {week-1} update")

        if not self.injuries_checked:
            blocking.append("Latest injury reports not checked")

        if not self.weather_checked:
            blocking.append("Weather forecasts not reviewed")

        return (len(blocking) == 0, blocking)

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk management summary"""
        risk_pct = (self.total_risk_deployed / self.bankroll) * 100
        remaining_capacity = self.bankroll * 0.15 - self.total_risk_deployed

        return {
            "total_deployed": self.total_risk_deployed,
            "deployment_pct": risk_pct,
            "bankroll": self.bankroll,
            "remaining_capacity": max(0, remaining_capacity),
            "within_limits": risk_pct <= 15.0,
            "active_bets": len(self.active_bets),
            "pending_opportunities": len(self.pending_opportunities),
        }


class SessionManager:
    """
    Manages betting analysis sessions with full state persistence.

    Provides:
    - Session creation with proper initialization
    - Incremental state saving
    - Session restoration from disk
    - Historical session lookup
    - State validation and recovery

    Usage:
        >>> manager = SessionManager(Path("data"))
        >>> session = manager.create_session(week=12, season=2025, bankroll=20000.0)
        >>> session.add_note("Starting Week 12 analysis")
        >>> manager.save_session(session)
        >>>
        >>> # Later, in new conversation:
        >>> restored = manager.load_latest_session()
        >>> print(f"Resuming Week {restored.week} analysis")
    """

    def __init__(self, data_dir: Path):
        """
        Initialize session manager.

        Args:
            data_dir: Root data directory (sessions stored in data_dir/sessions/)
        """
        self.data_dir = Path(data_dir)
        self.sessions_dir = self.data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "SessionManager initialized", extra={"sessions_dir": str(self.sessions_dir)}
        )

    def create_session(
        self,
        week: int,
        season: int,
        bankroll: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionContext:
        """
        Create a new betting analysis session.

        Args:
            week: NFL/NCAAF week number
            season: Year of the season
            bankroll: Starting bankroll for session
            metadata: Optional additional context

        Returns:
            New SessionContext ready for use

        Example:
            >>> session = manager.create_session(12, 2025, 20000.0)
            >>> session.session_id
            '2025_week12_20251120_143015'
        """
        now = datetime.now()
        session_id = f"{season}_week{week}_{now.strftime('%Y%m%d_%H%M%S')}"

        session = SessionContext(
            session_id=session_id,
            start_time=now,
            last_updated=now,
            week=week,
            season=season,
            bankroll=bankroll,
            metadata=metadata or {},
        )

        # Save immediately
        self.save_session(session)

        logger.info(
            f"Created new session: {session_id}",
            extra={"week": week, "season": season, "bankroll": bankroll},
        )

        return session

    def save_session(self, session: SessionContext) -> None:
        """
        Save session state to disk.

        Uses JSON format for human readability and easy inspection.
        Creates backup of existing file before overwriting.

        Args:
            session: SessionContext to save
        """
        session.last_updated = datetime.now()
        session_file = self.sessions_dir / f"{session.session_id}.json"

        # Create backup if file exists
        if session_file.exists():
            backup_file = session_file.with_suffix(".json.backup")
            session_file.replace(backup_file)

        # Convert dataclass to dict with datetime handling
        session_dict = asdict(session)
        session_dict["start_time"] = session.start_time.isoformat()
        session_dict["last_updated"] = session.last_updated.isoformat()

        # Write atomically
        temp_file = session_file.with_suffix(".json.tmp")
        with open(temp_file, "w") as f:
            json.dump(session_dict, f, indent=2, default=str)
        temp_file.replace(session_file)

        logger.debug(
            f"Saved session: {session.session_id}", extra={"file": str(session_file)}
        )

    def load_session(self, session_id: str) -> Optional[SessionContext]:
        """
        Load a specific session by ID.

        Args:
            session_id: Unique session identifier

        Returns:
            SessionContext if found, None otherwise
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            logger.warning(f"Session not found: {session_id}")
            return None

        try:
            with open(session_file) as f:
                data = json.load(f)

            # Convert ISO format strings back to datetime
            data["start_time"] = datetime.fromisoformat(data["start_time"])
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])

            session = SessionContext(**data)

            logger.info(f"Loaded session: {session_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to load session: {session_id}", exc_info=True)
            return None

    def load_latest_session(
        self, week: Optional[int] = None
    ) -> Optional[SessionContext]:
        """
        Load the most recent session, optionally filtered by week.

        Args:
            week: If provided, only return sessions for this week

        Returns:
            Most recent SessionContext or None if no sessions exist
        """
        sessions = sorted(
            self.sessions_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for session_file in sessions:
            if session_file.name.endswith(".backup") or session_file.name.endswith(
                ".tmp"
            ):
                continue

            session = self.load_session(session_file.stem)
            if session is None:
                continue

            if week is None or session.week == week:
                logger.info(
                    f"Loaded latest session: {session.session_id}",
                    extra={
                        "week": session.week,
                        "age_hours": (
                            datetime.now() - session.last_updated
                        ).total_seconds()
                        / 3600,
                    },
                )
                return session

        logger.info("No sessions found")
        return None

    def list_sessions(
        self, week: Optional[int] = None, season: Optional[int] = None, limit: int = 10
    ) -> List[SessionContext]:
        """
        List recent sessions with optional filtering.

        Args:
            week: Filter by week number
            season: Filter by season year
            limit: Maximum sessions to return

        Returns:
            List of SessionContext objects, most recent first
        """
        sessions = []
        session_files = sorted(
            self.sessions_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for session_file in session_files:
            if session_file.name.endswith(".backup") or session_file.name.endswith(
                ".tmp"
            ):
                continue

            if len(sessions) >= limit:
                break

            session = self.load_session(session_file.stem)
            if session is None:
                continue

            # Apply filters
            if week is not None and session.week != week:
                continue
            if season is not None and session.season != season:
                continue

            sessions.append(session)

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its backup.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted, False if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"
        backup_file = session_file.with_suffix(".json.backup")

        deleted = False

        if session_file.exists():
            session_file.unlink()
            deleted = True

        if backup_file.exists():
            backup_file.unlink()

        if deleted:
            logger.info(f"Deleted session: {session_id}")
        else:
            logger.warning(f"Session not found for deletion: {session_id}")

        return deleted


# Convenience functions for common operations


def get_or_create_session(
    data_dir: Path, week: int, season: int, bankroll: float
) -> SessionContext:
    """
    Get existing session for week or create new one.

    Convenience function that checks for existing session for the
    specified week and returns it, or creates a new one if none exists.

    Args:
        data_dir: Data directory path
        week: Week number
        season: Season year
        bankroll: Bankroll amount (used if creating new)

    Returns:
        SessionContext for the week
    """
    manager = SessionManager(data_dir)

    # Check for existing session
    existing = manager.load_latest_session(week=week)
    if existing and existing.season == season:
        logger.info(f"Using existing Week {week} session: {existing.session_id}")
        return existing

    # Create new
    logger.info(f"Creating new Week {week} session")
    return manager.create_session(week, season, bankroll)
