"""
Performance metrics calculation for backtesting results.

Calculates comprehensive statistics including:
- ROI, win rate, profit
- Sharpe ratio
- Maximum drawdown
- CLV statistics
- Performance by star rating, bet type, etc.
"""

import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict


class PerformanceMetrics:
    """Calculate performance metrics from backtest results."""

    def __init__(self, results: List[Dict]):
        """Initialize with backtest results.

        Args:
            results: List of result dictionaries from backtest
        """
        self.results = results

    def calculate_all_metrics(self) -> Dict:
        """Calculate all performance metrics.

        Returns:
            Dictionary with comprehensive metrics
        """
        if not self.results:
            return self._empty_metrics()

        return {
            'total_games': len(self.results),
            'total_bets': len([r for r in self.results if r.get('bet_placed')]),
            'wins': sum(1 for r in self.results if r.get('bet_won')),
            'losses': sum(1 for r in self.results if not r.get('bet_won')),
            'win_rate': self.calculate_win_rate(),
            'roi': self.calculate_roi(),
            'total_profit': self.calculate_total_profit(),
            'total_staked': self.calculate_total_staked(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'max_drawdown': self.calculate_max_drawdown(),
            'avg_clv': self.calculate_avg_clv(),
            'clv_positive_rate': self.calculate_clv_positive_rate(),
            'performance_by_star': self.calculate_performance_by_star(),
            'performance_by_month': self.calculate_performance_by_month(),
            'longest_win_streak': self.calculate_longest_streak(True),
            'longest_lose_streak': self.calculate_longest_streak(False),
            'average_stake': self.calculate_average_stake(),
            'largest_win': self.calculate_largest_win(),
            'largest_loss': self.calculate_largest_loss(),
        }

    def calculate_win_rate(self) -> float:
        """Calculate win rate percentage.

        Returns:
            Win rate (0-100)
        """
        bets = [r for r in self.results if r.get('bet_placed')]
        if not bets:
            return 0.0

        wins = sum(1 for r in bets if r.get('bet_won'))
        return (wins / len(bets)) * 100

    def calculate_roi(self) -> float:
        """Calculate return on investment percentage.

        Returns:
            ROI percentage
        """
        total_staked = self.calculate_total_staked()
        if total_staked == 0:
            return 0.0

        total_profit = self.calculate_total_profit()
        return (total_profit / total_staked) * 100

    def calculate_total_profit(self) -> float:
        """Calculate total profit/loss.

        Returns:
            Total profit in dollars
        """
        return sum(r.get('bet_profit', 0) for r in self.results)

    def calculate_total_staked(self) -> float:
        """Calculate total amount staked.

        Returns:
            Total staked in dollars
        """
        return sum(r.get('stake', 0) for r in self.results)

    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio.

        Args:
            risk_free_rate: Annual risk-free rate (default 0%)

        Returns:
            Sharpe ratio
        """
        profits = [r.get('bet_profit', 0) for r in self.results]

        if not profits or len(profits) < 2:
            return 0.0

        mean_profit = np.mean(profits)
        std_profit = np.std(profits, ddof=1)

        if std_profit == 0:
            return 0.0

        return (mean_profit - risk_free_rate) / std_profit

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage.

        Returns:
            Max drawdown as percentage
        """
        if not self.results:
            return 0.0

        # Calculate cumulative profits
        cumulative = 0
        peak = 0
        max_dd = 0

        for result in self.results:
            cumulative += result.get('bet_profit', 0)

            if cumulative > peak:
                peak = cumulative

            drawdown = peak - cumulative

            if peak > 0:
                dd_pct = (drawdown / peak) * 100
                max_dd = max(max_dd, dd_pct)

        return max_dd

    def calculate_avg_clv(self) -> float:
        """Calculate average closing line value.

        Returns:
            Average CLV in points
        """
        clv_values = [r.get('clv', 0) for r in self.results if r.get('clv') is not None]

        if not clv_values:
            return 0.0

        return np.mean(clv_values)

    def calculate_clv_positive_rate(self) -> float:
        """Calculate percentage of bets with positive CLV.

        Returns:
            Positive CLV rate (0-100)
        """
        clv_values = [r.get('clv', 0) for r in self.results if r.get('clv') is not None]

        if not clv_values:
            return 0.0

        positive = sum(1 for clv in clv_values if clv > 0)
        return (positive / len(clv_values)) * 100

    def calculate_performance_by_star(self) -> Dict:
        """Calculate performance metrics broken down by star rating.

        Returns:
            Dictionary with metrics per star rating
        """
        by_star = defaultdict(lambda: {'bets': 0, 'wins': 0, 'profit': 0, 'staked': 0})

        for result in self.results:
            star = result.get('star_rating', 0)
            star_key = f"{star:.1f}"

            by_star[star_key]['bets'] += 1
            by_star[star_key]['staked'] += result.get('stake', 0)
            by_star[star_key]['profit'] += result.get('bet_profit', 0)

            if result.get('bet_won'):
                by_star[star_key]['wins'] += 1

        # Calculate rates
        for star_key in by_star:
            stats = by_star[star_key]
            stats['win_rate'] = (stats['wins'] / stats['bets'] * 100) if stats['bets'] > 0 else 0
            stats['roi'] = (stats['profit'] / stats['staked'] * 100) if stats['staked'] > 0 else 0

        return dict(by_star)

    def calculate_performance_by_month(self) -> Dict:
        """Calculate performance metrics by month.

        Returns:
            Dictionary with metrics per month
        """
        by_month = defaultdict(lambda: {'bets': 0, 'wins': 0, 'profit': 0, 'staked': 0})

        for result in self.results:
            date = result.get('result_date', '')
            if date:
                month_key = date[:7]  # YYYY-MM

                by_month[month_key]['bets'] += 1
                by_month[month_key]['staked'] += result.get('stake', 0)
                by_month[month_key]['profit'] += result.get('bet_profit', 0)

                if result.get('bet_won'):
                    by_month[month_key]['wins'] += 1

        # Calculate rates
        for month_key in by_month:
            stats = by_month[month_key]
            stats['win_rate'] = (stats['wins'] / stats['bets'] * 100) if stats['bets'] > 0 else 0
            stats['roi'] = (stats['profit'] / stats['staked'] * 100) if stats['staked'] > 0 else 0

        return dict(by_month)

    def calculate_longest_streak(self, winning: bool = True) -> int:
        """Calculate longest winning or losing streak.

        Args:
            winning: True for win streak, False for lose streak

        Returns:
            Longest streak length
        """
        current_streak = 0
        max_streak = 0

        for result in self.results:
            won = result.get('bet_won', False)

            if (winning and won) or (not winning and not won):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def calculate_average_stake(self) -> float:
        """Calculate average bet stake.

        Returns:
            Average stake in dollars
        """
        stakes = [r.get('stake', 0) for r in self.results]
        return np.mean(stakes) if stakes else 0.0

    def calculate_largest_win(self) -> float:
        """Calculate largest single win.

        Returns:
            Largest win in dollars
        """
        profits = [r.get('bet_profit', 0) for r in self.results]
        return max(profits) if profits else 0.0

    def calculate_largest_loss(self) -> float:
        """Calculate largest single loss.

        Returns:
            Largest loss in dollars (negative)
        """
        profits = [r.get('bet_profit', 0) for r in self.results]
        return min(profits) if profits else 0.0

    def generate_report(self) -> str:
        """Generate formatted text report.

        Returns:
            Multi-line string report
        """
        metrics = self.calculate_all_metrics()

        report = []
        report.append("="*60)
        report.append("BACKTEST PERFORMANCE REPORT")
        report.append("="*60)
        report.append("")

        report.append("OVERALL PERFORMANCE")
        report.append("-"*60)
        report.append(f"Total bets: {metrics['total_bets']}")
        report.append(f"Wins: {metrics['wins']}")
        report.append(f"Losses: {metrics['losses']}")
        report.append(f"Win rate: {metrics['win_rate']:.1f}%")
        report.append(f"Total staked: ${metrics['total_staked']:,.2f}")
        report.append(f"Total profit: ${metrics['total_profit']:,.2f}")
        report.append(f"ROI: {metrics['roi']:.1f}%")
        report.append("")

        report.append("RISK METRICS")
        report.append("-"*60)
        report.append(f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
        report.append(f"Max drawdown: {metrics['max_drawdown']:.1f}%")
        report.append(f"Largest win: ${metrics['largest_win']:,.2f}")
        report.append(f"Largest loss: ${metrics['largest_loss']:,.2f}")
        report.append(f"Average stake: ${metrics['average_stake']:,.2f}")
        report.append("")

        report.append("CLV ANALYSIS")
        report.append("-"*60)
        report.append(f"Average CLV: {metrics['avg_clv']:+.2f} points")
        report.append(f"Positive CLV rate: {metrics['clv_positive_rate']:.1f}%")
        report.append("")

        report.append("STREAKS")
        report.append("-"*60)
        report.append(f"Longest win streak: {metrics['longest_win_streak']}")
        report.append(f"Longest lose streak: {metrics['longest_lose_streak']}")
        report.append("")

        report.append("PERFORMANCE BY STAR RATING")
        report.append("-"*60)
        for star, stats in sorted(metrics['performance_by_star'].items()):
            report.append(f"{star} stars: {stats['bets']} bets, "
                        f"{stats['win_rate']:.1f}% win rate, "
                        f"{stats['roi']:+.1f}% ROI, "
                        f"${stats['profit']:+,.2f} profit")

        report.append("")
        report.append("="*60)

        return "\n".join(report)

    def _empty_metrics(self) -> Dict:
        """Return empty metrics structure.

        Returns:
            Dictionary with zero values
        """
        return {
            'total_games': 0,
            'total_bets': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'roi': 0.0,
            'total_profit': 0.0,
            'total_staked': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'avg_clv': 0.0,
            'clv_positive_rate': 0.0,
            'performance_by_star': {},
            'performance_by_month': {},
            'longest_win_streak': 0,
            'longest_lose_streak': 0,
            'average_stake': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
        }
