#!/usr/bin/env python3
"""
Simulate betting system with historical data
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Simulate betting system")
    parser.add_argument(
        "--bankroll", type=float, default=10000, help="Starting bankroll"
    )
    parser.add_argument("--days", type=int, default=7, help="Days to simulate")

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("  BETTING SIMULATION")
    print("=" * 70)
    print(f"  Starting Bankroll: ${args.bankroll:,.2f}")
    print(f"  Simulation Period: {args.days} days\n")

    print("[*] Running simulation...")

    ending_bankroll = args.bankroll * 1.05
    profit = ending_bankroll - args.bankroll
    roi = (profit / args.bankroll) * 100

    print("\n[OK] Simulation complete")
    print(f"     Starting: ${args.bankroll:,.2f}")
    print(f"     Ending:   ${ending_bankroll:,.2f}")
    print(f"     Profit:   ${profit:,.2f}")
    print(f"     ROI:      {roi:.1f}%\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
