"""
Action Network Odds Data Parser

Parses the Action Network JSON data format to extract:
- Game information (teams, records, schedules)
- Odds from multiple sportsbooks (spreads, moneylines, totals)
- Betting percentages (tickets vs money) for sharp money detection
- Line movement data

This is a critical component for Billy Walters methodology:
- Tickets = public/recreational betting volume
- Money = actual dollars wagered
- Divergence between tickets and money indicates sharp action

Billy Walters Principle: "When the public is heavily on one side but the money
isn't following, professional bettors are on the other side."
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class BettingPercentages:
    """Betting percentages for sharp money analysis."""

    tickets_percent: Optional[int] = None  # % of total bets
    money_percent: Optional[int] = None  # % of total money

    @property
    def sharp_divergence(self) -> Optional[float]:
        """
        Calculate divergence between tickets and money.

        Positive = more money than tickets (sharp side)
        Negative = more tickets than money (public side)

        Billy Walters used 5+ point divergence as significant.
        """
        if self.tickets_percent is None or self.money_percent is None:
            return None
        return self.money_percent - self.tickets_percent

    @property
    def is_sharp_side(self) -> bool:
        """True if money percentage exceeds tickets by 5+ points."""
        div = self.sharp_divergence
        return div is not None and div >= 5

    @property
    def is_public_side(self) -> bool:
        """True if tickets exceed money percentage by 5+ points."""
        div = self.sharp_divergence
        return div is not None and div <= -5


@dataclass
class OddsLine:
    """Individual odds line (spread, moneyline, or total)."""

    line_type: str  # 'spread', 'moneyline', 'total'
    side: str  # 'home', 'away', 'over', 'under'
    value: Optional[float] = None  # spread value or total number
    odds: int = -110  # American odds
    team_abbr: Optional[str] = None
    betting: BettingPercentages = field(default_factory=BettingPercentages)
    book_id: Optional[int] = None
    book_name: Optional[str] = None


@dataclass
class TeamInfo:
    """Team information from Action Network."""

    id: int
    full_name: str
    display_name: str
    abbr: str
    location: str
    wins: int
    losses: int
    ties: int = 0
    conference: Optional[str] = None
    division: Optional[str] = None
    logo_url: Optional[str] = None

    @property
    def record(self) -> str:
        """Format W-L-T record."""
        if self.ties > 0:
            return f"{self.wins}-{self.losses}-{self.ties}"
        return f"{self.wins}-{self.losses}"


@dataclass
class GameOdds:
    """Complete odds for a single game."""

    game_id: int
    away_team: TeamInfo
    home_team: TeamInfo
    start_time: datetime
    week: int
    season: int
    broadcast: Optional[str] = None

    # Consensus lines (aggregated from all books)
    consensus_spread: Optional[OddsLine] = None
    consensus_spread_away: Optional[OddsLine] = None
    consensus_moneyline_home: Optional[OddsLine] = None
    consensus_moneyline_away: Optional[OddsLine] = None
    consensus_total_over: Optional[OddsLine] = None
    consensus_total_under: Optional[OddsLine] = None

    # Opening lines (for line movement tracking)
    opening_spread: Optional[float] = None
    opening_total: Optional[float] = None

    # All book lines (for line shopping)
    all_spreads: list = field(default_factory=list)
    all_moneylines: list = field(default_factory=list)
    all_totals: list = field(default_factory=list)

    @property
    def spread_line(self) -> Optional[float]:
        """Get consensus spread value (home team perspective)."""
        if self.consensus_spread:
            return self.consensus_spread.value
        return None

    @property
    def total_line(self) -> Optional[float]:
        """Get consensus total value."""
        if self.consensus_total_over:
            return self.consensus_total_over.value
        return None

    @property
    def spread_sharp_side(self) -> Optional[str]:
        """Determine which spread side sharps favor."""
        if self.consensus_spread and self.consensus_spread.betting.is_public_side:
            return (
                self.consensus_spread_away.team_abbr
                if self.consensus_spread_away
                else "AWAY"
            )
        if (
            self.consensus_spread_away
            and self.consensus_spread_away.betting.is_sharp_side
        ):
            return self.consensus_spread_away.team_abbr
        if self.consensus_spread and self.consensus_spread.betting.is_sharp_side:
            return self.consensus_spread.team_abbr
        return None

    @property
    def line_movement(self) -> Optional[float]:
        """Calculate line movement from open."""
        if self.opening_spread is not None and self.spread_line is not None:
            return self.spread_line - self.opening_spread
        return None


class ActionNetworkParser:
    """
    Parser for Action Network odds JSON data.

    Usage:
        parser = ActionNetworkParser()
        games = parser.parse_file('action_network_odds.json')

        for game in games:
            print(f"{game.away_team.abbr} @ {game.home_team.abbr}")
            print(f"Spread: {game.home_team.abbr} {game.spread_line}")
            if game.spread_sharp_side:
                print(f"Sharp side: {game.spread_sharp_side}")
    """

    CONSENSUS_BOOK_ID = "15"  # Action Network consensus
    OPENING_BOOK_ID = "30"  # Opening lines

    def __init__(self):
        self.books: dict[str, dict] = {}
        self.games: list[GameOdds] = []
        self.league: Optional[str] = None
        self.data_timestamp: Optional[datetime] = None

    def parse_file(self, filepath: str | Path) -> list[GameOdds]:
        """Parse an Action Network JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return self.parse_data(data)

    def parse_data(self, data: dict) -> list[GameOdds]:
        """Parse Action Network JSON data structure."""
        page_props = data.get("pageProps", {})

        # Extract metadata
        self.league = page_props.get("league", "unknown")
        self.books = page_props.get("allBooks", {})

        # Extract timestamp
        sb_response = page_props.get("scoreboardResponse", {})
        received_at = sb_response.get("receivedAt")
        if received_at:
            self.data_timestamp = datetime.fromtimestamp(received_at / 1000)

        # Parse games
        self.games = []
        for game_data in sb_response.get("games", []):
            game = self._parse_game(game_data)
            if game:
                self.games.append(game)

        return self.games

    def _parse_game(self, game_data: dict) -> Optional[GameOdds]:
        """Parse a single game's data."""
        try:
            teams = game_data.get("teams", [])
            if len(teams) < 2:
                return None

            away_team = self._parse_team(teams[0])
            home_team = self._parse_team(teams[1])

            # Parse start time
            start_time_str = game_data.get("start_time", "")
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))

            # Parse broadcast
            broadcast_info = game_data.get("broadcast", {})
            broadcast = (
                broadcast_info.get("network")
                if isinstance(broadcast_info, dict)
                else None
            )

            game = GameOdds(
                game_id=game_data.get("id", 0),
                away_team=away_team,
                home_team=home_team,
                start_time=start_time,
                week=game_data.get("week", 0),
                season=game_data.get("season", 0),
                broadcast=broadcast,
            )

            # Parse markets (odds)
            markets = game_data.get("markets", {})
            self._parse_markets(game, markets, away_team, home_team)

            return game

        except Exception as e:
            print(f"Error parsing game: {e}")
            return None

    def _parse_team(self, team_data: dict) -> TeamInfo:
        """Parse team information."""
        standings = team_data.get("standings", {})
        return TeamInfo(
            id=team_data.get("id", 0),
            full_name=team_data.get("full_name", ""),
            display_name=team_data.get("display_name", ""),
            abbr=team_data.get("abbr", ""),
            location=team_data.get("location", ""),
            wins=standings.get("win", 0),
            losses=standings.get("loss", 0),
            ties=standings.get("ties", 0),
            conference=team_data.get("conference_type"),
            division=team_data.get("division_type"),
            logo_url=team_data.get("logo"),
        )

    def _parse_markets(
        self, game: GameOdds, markets: dict, away_team: TeamInfo, home_team: TeamInfo
    ) -> None:
        """Parse all markets (odds) for a game."""
        # Parse consensus odds
        consensus = markets.get(self.CONSENSUS_BOOK_ID, {})
        if consensus:
            inner = list(consensus.values())[0] if consensus else {}
            self._parse_book_odds(
                game,
                inner,
                away_team,
                home_team,
                is_consensus=True,
                book_name="Consensus",
            )

        # Parse opening lines
        opening = markets.get(self.OPENING_BOOK_ID, {})
        if opening:
            inner = list(opening.values())[0] if opening else {}
            self._parse_opening_lines(game, inner)

        # Parse all other books
        for book_id, book_data in markets.items():
            if book_id in [self.CONSENSUS_BOOK_ID, self.OPENING_BOOK_ID]:
                continue
            book_info = self.books.get(book_id, {})
            book_name = book_info.get("display_name", f"Book {book_id}")
            inner = list(book_data.values())[0] if book_data else {}
            self._parse_book_odds(
                game,
                inner,
                away_team,
                home_team,
                is_consensus=False,
                book_name=book_name,
                book_id=int(book_id),
            )

    def _parse_book_odds(
        self,
        game: GameOdds,
        odds_data: dict,
        away_team: TeamInfo,
        home_team: TeamInfo,
        is_consensus: bool,
        book_name: str,
        book_id: Optional[int] = None,
    ) -> None:
        """Parse odds from a single book."""
        # Spreads
        for spread in odds_data.get("spread", []):
            line = self._parse_odds_line(spread, "spread", away_team, home_team)
            line.book_name = book_name
            line.book_id = book_id

            if is_consensus:
                if line.side == "home":
                    game.consensus_spread = line
                else:
                    game.consensus_spread_away = line
            else:
                game.all_spreads.append(line)

        # Moneylines
        for ml in odds_data.get("moneyline", []):
            line = self._parse_odds_line(ml, "moneyline", away_team, home_team)
            line.book_name = book_name
            line.book_id = book_id

            if is_consensus:
                if line.side == "home":
                    game.consensus_moneyline_home = line
                else:
                    game.consensus_moneyline_away = line
            else:
                game.all_moneylines.append(line)

        # Totals
        for total in odds_data.get("total", []):
            line = self._parse_odds_line(total, "total", away_team, home_team)
            line.book_name = book_name
            line.book_id = book_id

            if is_consensus:
                if line.side == "over":
                    game.consensus_total_over = line
                else:
                    game.consensus_total_under = line
            else:
                game.all_totals.append(line)

    def _parse_opening_lines(self, game: GameOdds, odds_data: dict) -> None:
        """Parse opening lines for line movement tracking."""
        for spread in odds_data.get("spread", []):
            if spread.get("side") == "home":
                game.opening_spread = spread.get("value")
                break

        for total in odds_data.get("total", []):
            if total.get("side") == "over":
                game.opening_total = total.get("value")
                break

    def _parse_odds_line(
        self, line_data: dict, line_type: str, away_team: TeamInfo, home_team: TeamInfo
    ) -> OddsLine:
        """Parse a single odds line."""
        side = line_data.get("side", "")
        team_abbr = None

        if line_type in ["spread", "moneyline"]:
            team_abbr = home_team.abbr if side == "home" else away_team.abbr

        # Parse betting percentages
        bet_info = line_data.get("bet_info", {})
        betting = BettingPercentages(
            tickets_percent=bet_info.get("tickets", {}).get("percent"),
            money_percent=bet_info.get("money", {}).get("percent"),
        )

        return OddsLine(
            line_type=line_type,
            side=side,
            value=line_data.get("value"),
            odds=line_data.get("odds", -110),
            team_abbr=team_abbr,
            betting=betting,
        )

    def get_sharp_plays(self, min_divergence: float = 5.0) -> list[dict]:
        """
        Find games where sharp money diverges from public.

        Billy Walters methodology: Look for 5+ point divergence
        between tickets and money as indicator of sharp action.

        Returns list of potential sharp plays with analysis.
        """
        sharp_plays = []

        for game in self.games:
            # Check spread
            if game.consensus_spread and game.consensus_spread_away:
                home_div = game.consensus_spread.betting.sharp_divergence
                away_div = game.consensus_spread_away.betting.sharp_divergence

                if home_div is not None and away_div is not None:
                    if away_div >= min_divergence:
                        sharp_plays.append(
                            {
                                "game": f"{game.away_team.abbr} @ {game.home_team.abbr}",
                                "type": "spread",
                                "pick": f"{game.away_team.abbr} {game.consensus_spread_away.value:+.1f}",
                                "tickets_pct": game.consensus_spread_away.betting.tickets_percent,
                                "money_pct": game.consensus_spread_away.betting.money_percent,
                                "divergence": away_div,
                                "signal": "SHARP - Money exceeds tickets",
                            }
                        )
                    elif home_div >= min_divergence:
                        sharp_plays.append(
                            {
                                "game": f"{game.away_team.abbr} @ {game.home_team.abbr}",
                                "type": "spread",
                                "pick": f"{game.home_team.abbr} {game.consensus_spread.value:+.1f}",
                                "tickets_pct": game.consensus_spread.betting.tickets_percent,
                                "money_pct": game.consensus_spread.betting.money_percent,
                                "divergence": home_div,
                                "signal": "SHARP - Money exceeds tickets",
                            }
                        )
                    elif away_div <= -min_divergence:
                        # Public on away, sharps fading
                        sharp_plays.append(
                            {
                                "game": f"{game.away_team.abbr} @ {game.home_team.abbr}",
                                "type": "spread",
                                "pick": f"{game.home_team.abbr} {game.consensus_spread.value:+.1f}",
                                "tickets_pct": game.consensus_spread.betting.tickets_percent,
                                "money_pct": game.consensus_spread.betting.money_percent,
                                "divergence": home_div,
                                "signal": "FADE PUBLIC - Tickets exceed money on other side",
                            }
                        )
                    elif home_div <= -min_divergence:
                        # Public on home, sharps fading
                        sharp_plays.append(
                            {
                                "game": f"{game.away_team.abbr} @ {game.home_team.abbr}",
                                "type": "spread",
                                "pick": f"{game.away_team.abbr} {game.consensus_spread_away.value:+.1f}",
                                "tickets_pct": game.consensus_spread_away.betting.tickets_percent,
                                "money_pct": game.consensus_spread_away.betting.money_percent,
                                "divergence": away_div,
                                "signal": "FADE PUBLIC - Tickets exceed money on other side",
                            }
                        )

        return sorted(sharp_plays, key=lambda x: abs(x["divergence"]), reverse=True)

    def get_best_lines(
        self, game: GameOdds, line_type: str = "spread", side: str = "home"
    ) -> list[tuple[str, float, int]]:
        """
        Find best available lines across all books for line shopping.

        Returns: List of (book_name, value, odds) sorted by best value
        """
        if line_type == "spread":
            lines = [l for l in game.all_spreads if l.side == side]
        elif line_type == "total":
            lines = [l for l in game.all_totals if l.side == side]
        else:
            lines = [l for l in game.all_moneylines if l.side == side]

        # Sort by best value (for spreads: most points if underdog, least if fav)
        results = [(l.book_name, l.value, l.odds) for l in lines]

        if line_type == "spread" and results:
            # Higher value is better for underdogs, lower for favorites
            results.sort(key=lambda x: (x[1] or 0, x[2]), reverse=True)
        elif line_type == "moneyline":
            results.sort(key=lambda x: x[2], reverse=True)  # Higher odds better

        return results[:5]  # Top 5 books

    def to_summary_dict(self) -> dict:
        """Export parsed data as summary dictionary for analysis."""
        return {
            "league": self.league,
            "timestamp": self.data_timestamp.isoformat()
            if self.data_timestamp
            else None,
            "game_count": len(self.games),
            "games": [
                {
                    "game_id": g.game_id,
                    "matchup": f"{g.away_team.abbr} @ {g.home_team.abbr}",
                    "away_team": g.away_team.abbr,
                    "home_team": g.home_team.abbr,
                    "away_record": g.away_team.record,
                    "home_record": g.home_team.record,
                    "week": g.week,
                    "start_time": g.start_time.isoformat(),
                    "spread": g.spread_line,
                    "total": g.total_line,
                    "opening_spread": g.opening_spread,
                    "line_movement": g.line_movement,
                    "spread_home_tix_pct": g.consensus_spread.betting.tickets_percent
                    if g.consensus_spread
                    else None,
                    "spread_home_money_pct": g.consensus_spread.betting.money_percent
                    if g.consensus_spread
                    else None,
                    "spread_away_tix_pct": g.consensus_spread_away.betting.tickets_percent
                    if g.consensus_spread_away
                    else None,
                    "spread_away_money_pct": g.consensus_spread_away.betting.money_percent
                    if g.consensus_spread_away
                    else None,
                    "sharp_side": g.spread_sharp_side,
                }
                for g in self.games
            ],
            "sharp_plays": self.get_sharp_plays(),
        }


def main():
    """Demo usage of ActionNetworkParser."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python action_network_parser.py <json_file>")
        return

    parser = ActionNetworkParser()
    games = parser.parse_file(sys.argv[1])

    print(f"\n{'=' * 70}")
    print(f"ACTION NETWORK {parser.league.upper()} DATA")
    print(f"Timestamp: {parser.data_timestamp}")
    print(f"Games: {len(games)}")
    print(f"{'=' * 70}")

    # Show all games
    for game in games:
        print(
            f"\n{game.away_team.abbr} ({game.away_team.record}) @ "
            f"{game.home_team.abbr} ({game.home_team.record})"
        )
        print(f"  Week {game.week} | {game.start_time.strftime('%a %m/%d %I:%M%p')}")

        if game.consensus_spread:
            s = game.consensus_spread
            sa = game.consensus_spread_away
            print(f"  Spread: {game.home_team.abbr} {s.value:+.1f} ({s.odds})")
            print(
                f"    Home: {s.betting.tickets_percent}% tix / {s.betting.money_percent}% $"
            )
            if sa:
                print(
                    f"    Away: {sa.betting.tickets_percent}% tix / {sa.betting.money_percent}% $"
                )

    # Show sharp plays
    print(f"\n{'=' * 70}")
    print("SHARP MONEY SIGNALS (5+ point divergence)")
    print(f"{'=' * 70}")

    sharp_plays = parser.get_sharp_plays(min_divergence=5.0)
    for play in sharp_plays:
        print(f"\n{play['game']}")
        print(f"  Pick: {play['pick']}")
        print(f"  Tickets: {play['tickets_pct']}% | Money: {play['money_pct']}%")
        print(f"  Divergence: {play['divergence']:+.0f} points")
        print(f"  Signal: {play['signal']}")


if __name__ == "__main__":
    main()
