"""
Billy Walters Risk Management Configuration
FIXES: Critical bet sizing issue (5% → 3% max)
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class BillyWaltersRiskConfig:
    """
    Risk management parameters aligned with Billy Walters methodology
    
    CRITICAL CHANGES FROM YOUR CURRENT CONFIG:
    - max_bet_percentage: 0.05 → 0.03 (3% hard cap)
    - Added weekly_exposure_limit: 0.15 (15% max per week)
    - Added stop_loss_trigger: 0.10 (10% drawdown = stop betting)
    """
    
    # BETTING THRESHOLDS
    min_edge_spread: float = 5.5  # Minimum edge percentage for any bet
    min_edge_total: float = 5.5   # Same for totals
    min_confidence: float = 0.55  # Minimum confidence score
    
    # BET SIZING (CRITICAL - BILLY WALTERS RULES)
    kelly_fraction: float = 0.25  # Conservative Kelly (25%)
    max_bet_percentage: float = 0.03  # [*] HARD CAP: 3% per bet (NOT 5%)
    base_unit_size: float = 0.01  # 1% per star
    max_stars: float = 3.0  # No bet can exceed 3 stars
    
    # WEEKLY LIMITS
    weekly_exposure_limit: float = 0.15  # Max 15% of bankroll per week
    max_bets_per_week: int = 10  # Quality over quantity
    
    # DRAWDOWN PROTECTION
    stop_loss_trigger: float = 0.10  # Stop at 10% weekly drawdown
    recovery_threshold: float = 0.05  # Resume when loss < 5%
    
    # STAR SYSTEM MAPPING
    star_to_percentage = {
        0.5: 0.005,  # 0.5%
        1.0: 0.010,  # 1.0%
        1.5: 0.015,  # 1.5%
        2.0: 0.020,  # 2.0%
        2.5: 0.025,  # 2.5%
        3.0: 0.030,  # 3.0% (MAXIMUM)
    }
    
    def validate_bet_size(
        self, 
        bet_amount: float, 
        bankroll: float, 
        weekly_exposure: float = 0.0
    ) -> tuple[bool, str]:
        """
        Validate if bet size complies with Billy Walters rules
        
        Args:
            bet_amount: Proposed bet in dollars
            bankroll: Current bankroll
            weekly_exposure: Current week's total exposure (0.0 to 1.0)
            
        Returns:
            Tuple of (is_valid, reason)
        """
        bet_pct = bet_amount / bankroll
        
        # Rule 1: No single bet > 3%
        if bet_pct > self.max_bet_percentage:
            return False, (
                f"[ERROR] Bet exceeds 3% maximum "
                f"({bet_pct*100:.1f}% > {self.max_bet_percentage*100:.1f}%)"
            )
        
        # Rule 2: Weekly exposure must stay under 15%
        new_weekly_exposure = weekly_exposure + bet_pct
        if new_weekly_exposure > self.weekly_exposure_limit:
            return False, (
                f"[ERROR] Weekly exposure would exceed 15% "
                f"({new_weekly_exposure*100:.1f}% > "
                f"{self.weekly_exposure_limit*100:.1f}%)"
            )
        
        # Rule 3: Check if in stop-loss mode (would need to track this separately)
        # This would be implemented in the main system
        
        return True, "[*] Bet size compliant with Billy Walters rules"
    
    def calculate_safe_bet_size(
        self, 
        stars: float, 
        bankroll: float,
        current_weekly_exposure: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate safe bet size using Billy Walters star system
        
        Args:
            stars: Star rating (0.5 to 3.0)
            bankroll: Current bankroll
            current_weekly_exposure: Current week's exposure as percentage
            
        Returns:
            Dict with bet_amount, bet_pct, and remaining_weekly_capacity
        """
        # Get percentage from star system
        bet_pct = self.star_to_percentage.get(stars, 0.0)
        
        # Apply hard caps
        bet_pct = min(bet_pct, self.max_bet_percentage)  # 3% max per bet
        
        # Check weekly limit
        remaining_weekly = self.weekly_exposure_limit - current_weekly_exposure
        bet_pct = min(bet_pct, remaining_weekly)
        
        # Calculate dollar amount
        bet_amount = bankroll * bet_pct
        
        return {
            'bet_amount': bet_amount,
            'bet_pct': bet_pct,
            'remaining_weekly_capacity': remaining_weekly - bet_pct,
            'stars': stars
        }


class WeeklyExposureTracker:
    """
    Track weekly betting exposure to enforce 15% limit
    """
    
    def __init__(self):
        self.bets_this_week: list[Dict] = []
        self.total_exposure: float = 0.0
        self.current_bankroll: float = 0.0
        
    def add_bet(self, bet_amount: float, bankroll: float, game_info: Dict):
        """Add a bet to weekly tracking"""
        bet_pct = bet_amount / bankroll
        
        self.bets_this_week.append({
            'amount': bet_amount,
            'percentage': bet_pct,
            'game': game_info,
            'bankroll_at_bet': bankroll
        })
        
        self.total_exposure += bet_pct
        self.current_bankroll = bankroll
        
    def get_remaining_capacity(self, limit: float = 0.15) -> float:
        """Get remaining betting capacity for the week"""
        return max(0.0, limit - self.total_exposure)
    
    def can_place_bet(self, bet_amount: float, bankroll: float) -> bool:
        """Check if bet would exceed weekly limit"""
        bet_pct = bet_amount / bankroll
        return (self.total_exposure + bet_pct) <= 0.15
    
    def get_weekly_summary(self) -> Dict:
        """Get summary of week's betting activity"""
        return {
            'total_bets': len(self.bets_this_week),
            'total_exposure_pct': self.total_exposure * 100,
            'remaining_capacity_pct': self.get_remaining_capacity() * 100,
            'max_single_bet_remaining': min(0.03, self.get_remaining_capacity()),
            'bets': self.bets_this_week
        }
    
    def reset_week(self):
        """Reset for new week"""
        self.bets_this_week = []
        self.total_exposure = 0.0


# EXAMPLE USAGE
if __name__ == "__main__":
    print("=" * 80)
    print("BILLY WALTERS RISK MANAGEMENT - CORRECTED CONFIGURATION")
    print("=" * 80)
    
    config = BillyWaltersRiskConfig()
    tracker = WeeklyExposureTracker()
    bankroll = 20000.0
    
    print(f"\n[MONEY] Starting Bankroll: ${bankroll:,.0f}")
    print(f"[LIST] Max Single Bet: {config.max_bet_percentage*100:.1f}% = ${bankroll*config.max_bet_percentage:,.0f}")
    print(f"[CHART] Max Weekly Exposure: {config.weekly_exposure_limit*100:.1f}% = ${bankroll*config.weekly_exposure_limit:,.0f}")
    
    # Simulate Week 12 betting decisions
    print("\n" + "=" * 80)
    print("WEEK 12 BET SIMULATION")
    print("=" * 80)
    
    week12_opportunities = [
        {"game": "IND @ KC", "stars": 2.5, "edge": 8.2},
        {"game": "LAR @ TB", "stars": 2.0, "edge": 6.8},
        {"game": "CIN vs NE", "stars": 1.5, "edge": 5.9},
        {"game": "GB vs MIN", "stars": 1.0, "edge": 4.5},
        {"game": "BUF @ HOU", "stars": 0.5, "edge": 4.2},
    ]
    
    for opp in week12_opportunities:
        print(f"\n[TARGET] {opp['game']}")
        print(f"   Edge: {opp['edge']}% | Stars: {opp['stars']}")
        
        # Calculate bet size
        bet_info = config.calculate_safe_bet_size(
            stars=opp['stars'],
            bankroll=bankroll,
            current_weekly_exposure=tracker.total_exposure
        )
        
        # Validate
        is_valid, reason = config.validate_bet_size(
            bet_amount=bet_info['bet_amount'],
            bankroll=bankroll,
            weekly_exposure=tracker.total_exposure
        )
        
        if is_valid:
            tracker.add_bet(bet_info['bet_amount'], bankroll, opp)
            print(f"   [*] BET: ${bet_info['bet_amount']:.0f} ({bet_info['bet_pct']*100:.1f}%)")
            print(f"   [CHART] Weekly exposure: {tracker.total_exposure*100:.1f}%")
        else:
            print(f"   [ERROR] SKIP: {reason}")
    
    # Weekly summary
    print("\n" + "=" * 80)
    print("WEEK 12 SUMMARY")
    print("=" * 80)
    summary = tracker.get_weekly_summary()
    print(f"Total Bets: {summary['total_bets']}")
    print(f"Total Exposure: {summary['total_exposure_pct']:.1f}%")
    print(f"Remaining Capacity: {summary['remaining_capacity_pct']:.1f}%")
    print(f"[*] Within 15% limit: {summary['total_exposure_pct'] <= 15.0}")
    
    print("\n" + "=" * 80)
    print("[*] CRITICAL CHANGE REQUIRED")
    print("=" * 80)
    print("UPDATE YOUR config_manager.py:")
    print("  OLD: max_bet_percentage: float = 0.05")
    print("  NEW: max_bet_percentage: float = 0.03")
    print("=" * 80)
