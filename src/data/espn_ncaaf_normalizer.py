"""
ESPN NCAAF Data Normalizer

Normalizes ESPN scoreboard JSON into parquet tables for efficient analysis.

Storage Pipeline:
    1. Raw JSON saved under data/raw/espn/scoreboard/{date}/{timestamp}_scoreboard.json
    2. Normalized into 3 parquet tables:
       - events.parquet (game-level data)
       - competitors.parquet (team-level data)
       - odds.parquet (betting lines)
    3. Cached per event_id for fast /analyze-game --research

Tables:
    - events: event_id, name, date, status, season_type, week, venue, weather
    - competitors: event_id, team_id, team_name, home_away, score, record, rank
    - odds: event_id, provider, spread, over_under, moneyline, timestamp
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd


class ESPNNCAAFNormalizer:
    """
    Normalizes ESPN NCAAF scoreboard data into parquet tables.

    Supports:
    - Event normalization (game-level)
    - Competitor normalization (team-level)
    - Odds normalization (betting lines)
    - Win probability tracking
    """

    def __init__(self, output_dir: Path):
        """
        Initialize normalizer.

        Args:
            output_dir: Directory for parquet output (e.g., data/normalized/espn)
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def normalize_scoreboard(
        self, scoreboard: dict
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Normalize scoreboard JSON into 3 dataframes.

        Args:
            scoreboard: Scoreboard API response

        Returns:
            Tuple of (events_df, competitors_df, odds_df)
        """
        events_data = []
        competitors_data = []
        odds_data = []

        season = scoreboard.get("season", {})
        week = scoreboard.get("week", {})
        season_type = season.get("type")
        week_number = week.get("number")

        for event in scoreboard.get("events", []):
            event_id = event.get("id")
            event_name = event.get("name")
            event_date = event.get("date")
            status = event.get("status", {})
            status_type = status.get("type", {}).get("state")
            status_detail = status.get("type", {}).get("detail")

            # Get competition (first one, usually only one for CFB)
            competitions = event.get("competitions", [])
            if not competitions:
                continue

            comp = competitions[0]

            # Event-level data
            venue = comp.get("venue", {})
            weather = comp.get("weather", {})
            broadcast = (
                comp.get("broadcasts", [{}])[0] if comp.get("broadcasts") else {}
            )

            event_row = {
                "event_id": event_id,
                "name": event_name,
                "date": event_date,
                "season_type": season_type,
                "week": week_number,
                "status": status_type,
                "status_detail": status_detail,
                "venue_name": venue.get("fullName"),
                "venue_city": venue.get("address", {}).get("city"),
                "venue_state": venue.get("address", {}).get("state"),
                "venue_indoor": venue.get("indoor"),
                "temperature": weather.get("temperature"),
                "condition": weather.get("displayValue"),
                "broadcast_network": broadcast.get("names", [None])[0]
                if broadcast.get("names")
                else None,
                "attendance": comp.get("attendance"),
            }
            events_data.append(event_row)

            # Competitor-level data
            for competitor in comp.get("competitors", []):
                team = competitor.get("team", {})
                team_id = team.get("id")
                team_name = team.get("displayName")
                home_away = competitor.get("homeAway")
                score = competitor.get("score")

                # Records
                records = competitor.get("records", [])
                overall_record = None
                if records:
                    for record in records:
                        if record.get("type") == "total":
                            overall_record = record.get("summary")
                            break

                # Rank
                rank = competitor.get("curatedRank", {}).get("current")

                competitor_row = {
                    "event_id": event_id,
                    "team_id": team_id,
                    "team_name": team_name,
                    "home_away": home_away,
                    "score": score,
                    "winner": competitor.get("winner"),
                    "rank": rank,
                    "record": overall_record,
                }
                competitors_data.append(competitor_row)

            # Odds data
            for odd in comp.get("odds", []):
                provider = odd.get("provider", {})
                provider_name = provider.get("name")

                odds_row = {
                    "event_id": event_id,
                    "provider": provider_name,
                    "spread": odd.get("spread"),
                    "over_under": odd.get("overUnder"),
                    "home_moneyline": odd.get("homeTeamOdds", {}).get("moneyLine"),
                    "away_moneyline": odd.get("awayTeamOdds", {}).get("moneyLine"),
                    "details": odd.get("details"),
                    "timestamp": datetime.now().isoformat(),
                }
                odds_data.append(odds_row)

        # Create dataframes
        events_df = pd.DataFrame(events_data)
        competitors_df = pd.DataFrame(competitors_data)
        odds_df = pd.DataFrame(odds_data)

        return events_df, competitors_df, odds_df

    def normalize_game_summary(self, summary: dict, event_id: str) -> dict:
        """
        Normalize game summary into structured data.

        Args:
            summary: Game summary API response
            event_id: ESPN event ID

        Returns:
            Dictionary with normalized summary data
        """
        normalized = {
            "event_id": event_id,
            "box_score": self._extract_box_score(summary),
            "drives": self._extract_drives(summary),
            "scoring_plays": self._extract_scoring_plays(summary),
            "injuries": self._extract_injuries(summary),
            "betting_splits": self._extract_betting_splits(summary),
        }

        return normalized

    def _extract_box_score(self, summary: dict) -> Optional[pd.DataFrame]:
        """Extract box score statistics."""
        box_score = summary.get("boxscore", {})
        teams = box_score.get("teams", [])

        if not teams:
            return None

        stats_data = []

        for team in teams:
            team_id = team.get("team", {}).get("id")
            team_name = team.get("team", {}).get("displayName")

            for stat in team.get("statistics", []):
                stat_name = stat.get("name")
                stat_value = stat.get("displayValue")

                stats_data.append(
                    {
                        "team_id": team_id,
                        "team_name": team_name,
                        "stat_name": stat_name,
                        "stat_value": stat_value,
                    }
                )

        return pd.DataFrame(stats_data) if stats_data else None

    def _extract_drives(self, summary: dict) -> Optional[pd.DataFrame]:
        """Extract drive data."""
        drives = summary.get("drives", {}).get("previous", [])

        if not drives:
            return None

        drive_data = []

        for drive in drives:
            drive_data.append(
                {
                    "drive_id": drive.get("id"),
                    "team_id": drive.get("team", {}).get("id"),
                    "start_period": drive.get("start", {})
                    .get("period", {})
                    .get("number"),
                    "start_clock": drive.get("start", {})
                    .get("clock", {})
                    .get("displayValue"),
                    "start_yardline": drive.get("start", {}).get("yardLine"),
                    "end_period": drive.get("end", {}).get("period", {}).get("number"),
                    "end_clock": drive.get("end", {})
                    .get("clock", {})
                    .get("displayValue"),
                    "end_yardline": drive.get("end", {}).get("yardLine"),
                    "plays": drive.get("offensivePlays"),
                    "yards": drive.get("yards"),
                    "result": drive.get("result"),
                }
            )

        return pd.DataFrame(drive_data)

    def _extract_scoring_plays(self, summary: dict) -> Optional[pd.DataFrame]:
        """Extract scoring plays."""
        scoring_plays = summary.get("scoringPlays", [])

        if not scoring_plays:
            return None

        play_data = []

        for play in scoring_plays:
            play_data.append(
                {
                    "play_id": play.get("id"),
                    "team_id": play.get("team", {}).get("id"),
                    "period": play.get("period", {}).get("number"),
                    "clock": play.get("clock", {}).get("displayValue"),
                    "score_value": play.get("scoreValue"),
                    "text": play.get("text"),
                    "type": play.get("type", {}).get("text"),
                }
            )

        return pd.DataFrame(play_data)

    def _extract_injuries(self, summary: dict) -> Optional[pd.DataFrame]:
        """Extract injury data."""
        injuries = summary.get("injuries", [])

        if not injuries:
            return None

        injury_data = []

        for team_injuries in injuries:
            team_id = team_injuries.get("team", {}).get("id")

            for injury in team_injuries.get("injuries", []):
                injury_data.append(
                    {
                        "team_id": team_id,
                        "player_name": injury.get("athlete", {}).get("displayName"),
                        "position": injury.get("position", {}).get("abbreviation"),
                        "status": injury.get("status"),
                        "details": injury.get("details", {}).get("type"),
                    }
                )

        return pd.DataFrame(injury_data)

    def _extract_betting_splits(self, summary: dict) -> Optional[dict]:
        """Extract betting splits data."""
        pickcenter = summary.get("pickcenter", [])

        if not pickcenter:
            return None

        splits = {}

        for item in pickcenter:
            provider = item.get("provider", {}).get("name")
            details = item.get("details")

            if details:
                splits[provider] = details

        return splits

    def save_parquet(
        self,
        events_df: pd.DataFrame,
        competitors_df: pd.DataFrame,
        odds_df: pd.DataFrame,
        date: Optional[str] = None,
    ) -> dict:
        """
        Save normalized dataframes to parquet.

        Args:
            events_df: Events dataframe
            competitors_df: Competitors dataframe
            odds_df: Odds dataframe
            date: Date string (YYYYMMDD) for subdirectory

        Returns:
            Dictionary with file paths
        """
        # Create date subdirectory
        if date:
            save_dir = self.output_dir / date
        else:
            save_dir = self.output_dir / datetime.now().strftime("%Y%m%d")

        save_dir.mkdir(parents=True, exist_ok=True)

        # Save parquet files
        events_path = save_dir / "events.parquet"
        competitors_path = save_dir / "competitors.parquet"
        odds_path = save_dir / "odds.parquet"

        events_df.to_parquet(events_path, index=False)
        competitors_df.to_parquet(competitors_path, index=False)
        odds_df.to_parquet(odds_path, index=False)

        return {
            "events": str(events_path),
            "competitors": str(competitors_path),
            "odds": str(odds_path),
        }

    def load_parquet(
        self, date: str
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load parquet files for a specific date.

        Args:
            date: Date string (YYYYMMDD)

        Returns:
            Tuple of (events_df, competitors_df, odds_df)
        """
        load_dir = self.output_dir / date

        events_df = pd.read_parquet(load_dir / "events.parquet")
        competitors_df = pd.read_parquet(load_dir / "competitors.parquet")
        odds_df = pd.read_parquet(load_dir / "odds.parquet")

        return events_df, competitors_df, odds_df

    def compare_odds_with_overtime(
        self,
        espn_odds_df: pd.DataFrame,
        overtime_data: dict,
    ) -> pd.DataFrame:
        """
        Compare ESPN odds with Overtime.ag lines for edge detection.

        Args:
            espn_odds_df: ESPN odds dataframe
            overtime_data: Overtime.ag odds dictionary

        Returns:
            Comparison dataframe with differences
        """
        # This will be implemented to support bankroll logic
        # comparing ESPN lines (Caesars, ESPN BET, etc.) against Overtime lines
        # to identify value opportunities

        # Placeholder for now
        comparison_data = []

        for _, row in espn_odds_df.iterrows():
            event_id = row["event_id"]

            # Find matching Overtime game
            # (requires team name mapping between ESPN and Overtime)

            comparison_data.append(
                {
                    "event_id": event_id,
                    "espn_spread": row["spread"],
                    "espn_total": row["over_under"],
                    "overtime_spread": None,  # To be implemented
                    "overtime_total": None,  # To be implemented
                    "spread_diff": None,
                    "total_diff": None,
                }
            )

        return pd.DataFrame(comparison_data)
