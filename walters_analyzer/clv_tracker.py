"""
Closing Line Value (CLV) Tracker

CLV is the gold standard for measuring betting skill:
- Positive CLV = You're beating the closing line (sharp)
- Negative CLV = You're behind the closing line (recreational)

Billy Walters emphasizes: "If you're consistently beating the closing line,
you will be profitable long-term, even if you have short-term losing streaks."
"""

import sqlite3
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
import json
import os


@dataclass
class BetRecord:
    """Complete record of a single bet."""
    # Primary identifiers
    bet_id: Optional[int] = None
    date_placed: str = ""
    game_date: str = ""
    sport: str = ""
    game: str = ""

    # Bet details
    bet_type: str = ""  # 'spread', 'total', 'moneyline'
    side: str = ""  # 'home', 'away', 'over', 'under'
    your_line: float = 0.0
    opening_line: float = 0.0
    closing_line: Optional[float] = None
    price: int = -110

    # Edge & sizing
    edge_percentage: float = 0.0
    stars: float = 0.0
    bet_amount: float = 0.0
    bankroll_at_bet: float = 0.0

    # Results (filled after game)
    result: Optional[str] = None  # 'win', 'loss', 'push'
    profit: Optional[float] = None
    clv: Optional[float] = None  # Closing line - your line

    # Context
    reasoning: str = ""
    swe_factors: Optional[str] = None  # JSON string of S/W/E factors

    def to_dict(self) -> dict:
        """Convert to dictionary, handling None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class CLVTracker:
    """
    Track Closing Line Value and bet performance over time.

    Database schema tracks:
    - Every bet placed (date, line, price, size)
    - Opening and closing lines
    - Game results and profit/loss
    - CLV for each bet
    - Aggregate statistics
    """

    def __init__(self, db_path: str = "data/bets/bets.db"):
        """
        Initialize CLV tracker with SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Create directory if needed
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.create_tables()

    def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_placed TEXT NOT NULL,
                game_date TEXT NOT NULL,
                sport TEXT NOT NULL,
                game TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                side TEXT NOT NULL,
                your_line REAL NOT NULL,
                opening_line REAL NOT NULL,
                closing_line REAL,
                price INTEGER NOT NULL,
                edge_percentage REAL NOT NULL,
                stars REAL NOT NULL,
                bet_amount REAL NOT NULL,
                bankroll_at_bet REAL NOT NULL,
                result TEXT,
                profit REAL,
                clv REAL,
                reasoning TEXT,
                swe_factors TEXT
            )
        """)

        # Index for fast queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_game_date ON bets(game_date)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sport ON bets(sport)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_result ON bets(result)
        """)

        self.conn.commit()

    def log_bet(
        self,
        game: str,
        game_date: str,
        sport: str,
        bet_type: str,
        side: str,
        your_line: float,
        opening_line: float,
        price: int,
        edge_percentage: float,
        stars: float,
        bet_amount: float,
        bankroll: float,
        reasoning: str = "",
        swe_factors: Optional[dict] = None
    ) -> int:
        """
        Log a new bet when placed.

        Args:
            game: Game description (e.g., "Alabama @ LSU")
            game_date: When game is played (YYYY-MM-DD)
            sport: 'nfl' or 'cfb'
            bet_type: 'spread', 'total', 'moneyline'
            side: 'home', 'away', 'over', 'under'
            your_line: Line you're betting
            opening_line: Opening line when you placed bet
            price: American odds
            edge_percentage: Your calculated edge
            stars: Star rating
            bet_amount: Dollars wagered
            bankroll: Current bankroll
            reasoning: Why you made this bet
            swe_factors: S/W/E factor breakdown (dict)

        Returns:
            bet_id of inserted bet
        """
        cursor = self.conn.execute("""
            INSERT INTO bets (
                date_placed, game_date, sport, game, bet_type, side,
                your_line, opening_line, price, edge_percentage, stars,
                bet_amount, bankroll_at_bet, reasoning, swe_factors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            game_date,
            sport,
            game,
            bet_type,
            side,
            your_line,
            opening_line,
            price,
            edge_percentage,
            stars,
            bet_amount,
            bankroll,
            reasoning,
            json.dumps(swe_factors) if swe_factors else None
        ))

        self.conn.commit()
        return cursor.lastrowid

    def update_closing_line(self, bet_id: int, closing_line: float) -> None:
        """
        Update closing line for a bet (run after game starts).

        Args:
            bet_id: ID of bet to update
            closing_line: Closing line value
        """
        # Get the bet to calculate CLV
        bet = self.get_bet(bet_id)
        if not bet:
            raise ValueError(f"Bet {bet_id} not found")

        # Calculate CLV
        # Positive CLV = you got a better line than close
        # For spreads/totals: your_line vs closing_line
        clv = closing_line - bet['your_line']

        self.conn.execute("""
            UPDATE bets
            SET closing_line = ?, clv = ?
            WHERE bet_id = ?
        """, (closing_line, clv, bet_id))

        self.conn.commit()

    def update_result(
        self,
        bet_id: int,
        result: str,
        profit: float
    ) -> None:
        """
        Update bet result after game completes.

        Args:
            bet_id: ID of bet to update
            result: 'win', 'loss', or 'push'
            profit: Profit/loss amount (negative for loss)
        """
        self.conn.execute("""
            UPDATE bets
            SET result = ?, profit = ?
            WHERE bet_id = ?
        """, (result, profit, bet_id))

        self.conn.commit()

    def get_bet(self, bet_id: int) -> Optional[Dict]:
        """
        Get a single bet by ID.

        Args:
            bet_id: Bet ID

        Returns:
            Dict with bet data or None
        """
        cursor = self.conn.execute("""
            SELECT * FROM bets WHERE bet_id = ?
        """, (bet_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_bets(
        self,
        sport: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all bets, optionally filtered.

        Args:
            sport: Filter by sport
            start_date: Filter by game date (YYYY-MM-DD)
            end_date: Filter by game date (YYYY-MM-DD)

        Returns:
            List of bet dicts
        """
        query = "SELECT * FROM bets WHERE 1=1"
        params = []

        if sport:
            query += " AND sport = ?"
            params.append(sport)

        if start_date:
            query += " AND game_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND game_date <= ?"
            params.append(end_date)

        query += " ORDER BY game_date DESC"

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_clv_stats(
        self,
        sport: Optional[str] = None,
        min_bets: int = 10
    ) -> Dict:
        """
        Calculate CLV statistics.

        Args:
            sport: Filter by sport
            min_bets: Minimum bets required for stats

        Returns:
            Dict with CLV statistics
        """
        query = """
            SELECT
                COUNT(*) as total_bets,
                AVG(clv) as avg_clv,
                MIN(clv) as min_clv,
                MAX(clv) as max_clv,
                SUM(CASE WHEN clv > 0 THEN 1 ELSE 0 END) as positive_clv_count,
                SUM(CASE WHEN clv < 0 THEN 1 ELSE 0 END) as negative_clv_count,
                AVG(CASE WHEN result = 'win' THEN 1.0 ELSE 0.0 END) as win_rate
            FROM bets
            WHERE clv IS NOT NULL
        """
        params = []

        if sport:
            query += " AND sport = ?"
            params.append(sport)

        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()
        stats = dict(row)

        if stats['total_bets'] < min_bets:
            return {
                'error': f'Need at least {min_bets} bets with CLV data',
                'current_bets': stats['total_bets']
            }

        # Calculate percentage beating closing line
        stats['pct_beating_close'] = (
            stats['positive_clv_count'] / stats['total_bets'] * 100
            if stats['total_bets'] > 0 else 0
        )

        return stats

    def get_performance_by_stars(self) -> List[Dict]:
        """
        Get performance breakdown by star rating.

        Returns:
            List of dicts with performance by star level
        """
        cursor = self.conn.execute("""
            SELECT
                stars,
                COUNT(*) as bet_count,
                AVG(clv) as avg_clv,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result = 'push' THEN 1 ELSE 0 END) as pushes,
                SUM(profit) as total_profit,
                AVG(profit) as avg_profit
            FROM bets
            WHERE result IS NOT NULL
            GROUP BY stars
            ORDER BY stars DESC
        """)

        results = []
        for row in cursor.fetchall():
            stats = dict(row)
            total_graded = stats['wins'] + stats['losses']
            stats['win_rate'] = (
                stats['wins'] / total_graded * 100
                if total_graded > 0 else 0
            )
            results.append(stats)

        return results

    def get_performance_by_bet_type(self, sport: Optional[str] = None) -> List[Dict]:
        """
        Get performance breakdown by bet type.

        Args:
            sport: Optional sport filter

        Returns:
            List of dicts with performance by bet type
        """
        query = """
            SELECT
                bet_type,
                COUNT(*) as bet_count,
                AVG(clv) as avg_clv,
                SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
                SUM(profit) as total_profit,
                AVG(profit) as avg_profit
            FROM bets
            WHERE result IS NOT NULL
        """
        params = []

        if sport:
            query += " AND sport = ?"
            params.append(sport)

        query += " GROUP BY bet_type"

        cursor = self.conn.execute(query, params)

        results = []
        for row in cursor.fetchall():
            stats = dict(row)
            total_graded = stats['wins'] + stats['losses']
            stats['win_rate'] = (
                stats['wins'] / total_graded * 100
                if total_graded > 0 else 0
            )
            results.append(stats)

        return results

    def get_roi(self, sport: Optional[str] = None) -> Dict:
        """
        Calculate overall ROI (return on investment).

        Args:
            sport: Optional sport filter

        Returns:
            Dict with ROI stats
        """
        query = """
            SELECT
                SUM(bet_amount) as total_wagered,
                SUM(profit) as total_profit,
                COUNT(*) as total_bets,
                AVG(profit) as avg_profit_per_bet
            FROM bets
            WHERE result IS NOT NULL
        """
        params = []

        if sport:
            query += " AND sport = ?"
            params.append(sport)

        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()
        stats = dict(row)

        if stats['total_wagered']:
            stats['roi'] = (stats['total_profit'] / stats['total_wagered']) * 100
        else:
            stats['roi'] = 0

        return stats

    def get_recent_bets(self, limit: int = 10) -> List[Dict]:
        """
        Get most recent bets.

        Args:
            limit: Number of bets to return

        Returns:
            List of recent bet dicts
        """
        cursor = self.conn.execute("""
            SELECT * FROM bets
            ORDER BY date_placed DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def export_to_csv(self, output_path: str) -> None:
        """
        Export all bets to CSV.

        Args:
            output_path: Path to output CSV file
        """
        import csv

        bets = self.get_all_bets()

        if not bets:
            print("No bets to export")
            return

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=bets[0].keys())
            writer.writeheader()
            writer.writerows(bets)

        print(f"Exported {len(bets)} bets to {output_path}")

    def generate_report(self) -> str:
        """
        Generate comprehensive performance report.

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("BETTING PERFORMANCE REPORT")
        lines.append("=" * 60)

        # Overall ROI
        roi_stats = self.get_roi()
        lines.append(f"\nOVERALL PERFORMANCE:")
        lines.append(f"  Total Bets: {roi_stats['total_bets']}")
        lines.append(f"  Total Wagered: ${roi_stats['total_wagered']:,.2f}")
        lines.append(f"  Total Profit: ${roi_stats['total_profit']:,.2f}")
        lines.append(f"  ROI: {roi_stats['roi']:.2f}%")
        lines.append(f"  Avg Profit/Bet: ${roi_stats['avg_profit_per_bet']:,.2f}")

        # CLV Stats
        clv_stats = self.get_clv_stats()
        if 'error' not in clv_stats:
            lines.append(f"\nCLOSING LINE VALUE (CLV):")
            lines.append(f"  Average CLV: {clv_stats['avg_clv']:.2f} points")
            lines.append(f"  Beating Close: {clv_stats['pct_beating_close']:.1f}%")
            lines.append(f"  Win Rate: {clv_stats['win_rate']*100:.1f}%")

        # Performance by Stars
        star_performance = self.get_performance_by_stars()
        if star_performance:
            lines.append(f"\nPERFORMANCE BY STAR RATING:")
            for stats in star_performance:
                lines.append(
                    f"  {stats['stars']:.1f}★: {stats['wins']}-{stats['losses']} "
                    f"({stats['win_rate']:.1f}% win rate, "
                    f"${stats['total_profit']:,.2f} profit, "
                    f"{stats['avg_clv']:.2f} avg CLV)"
                )

        # Performance by Bet Type
        type_performance = self.get_performance_by_bet_type()
        if type_performance:
            lines.append(f"\nPERFORMANCE BY BET TYPE:")
            for stats in type_performance:
                lines.append(
                    f"  {stats['bet_type'].upper()}: {stats['wins']}-{stats['losses']} "
                    f"({stats['win_rate']:.1f}% win rate, "
                    f"${stats['total_profit']:,.2f} profit)"
                )

        lines.append("=" * 60)

        return "\n".join(lines)

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


# Convenience functions

def create_tracker(db_path: str = "data/bets/bets.db") -> CLVTracker:
    """Create a new CLV tracker instance."""
    return CLVTracker(db_path)


def log_bet_quick(
    tracker: CLVTracker,
    game: str,
    sport: str,
    bet_type: str,
    your_line: float,
    stars: float,
    bet_amount: float,
    bankroll: float
) -> int:
    """Quick bet logging with minimal parameters."""
    return tracker.log_bet(
        game=game,
        game_date=datetime.now().strftime("%Y-%m-%d"),
        sport=sport,
        bet_type=bet_type,
        side="unknown",
        your_line=your_line,
        opening_line=your_line,
        price=-110,
        edge_percentage=0.07,  # Default 7% for 1 star
        stars=stars,
        bet_amount=bet_amount,
        bankroll=bankroll
    )
