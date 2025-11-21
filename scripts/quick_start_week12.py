#!/usr/bin/env python3
"""
Week 12 Quick Start Script
Rapid session initialization with automated readiness checking.

This script provides a fast, guided startup for Week 12 analysis:
- Creates or restores session automatically
- Checks system readiness
- Provides clear next steps
- Validates prerequisites

Usage:
    python scripts/quick_start_week12.py

    # Or with specific bankroll:
    python scripts/quick_start_week12.py --bankroll 25000
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from walters_analyzer.core.session_manager import SessionManager, get_or_create_session
from walters_analyzer.config.settings import Settings


def print_header():
    """Print formatted header"""
    print("\n" + "=" * 70)
    print("   BILLY WALTERS BETTING SYSTEM - WEEK 12 QUICK START")
    print("=" * 70 + "\n")


def print_section(title: str):
    """Print section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def check_power_ratings(session) -> bool:
    """Check if power ratings are updated"""
    # In production, this would check actual power ratings file
    # For now, use session state
    return session.power_ratings_updated


def check_injuries(session) -> bool:
    """Check if injuries have been reviewed"""
    return session.injuries_checked


def check_weather(session) -> bool:
    """Check if weather has been reviewed"""
    return session.weather_checked


def main():
    """Main quick start flow"""

    parser = argparse.ArgumentParser(description="Week 12 Quick Start")
    parser.add_argument(
        "--week", type=int, default=12, help="Week number (default: 12)"
    )
    parser.add_argument(
        "--season", type=int, default=2025, help="Season year (default: 2025)"
    )
    parser.add_argument(
        "--bankroll",
        type=float,
        default=20000.0,
        help="Bankroll amount (default: 20000)",
    )
    parser.add_argument(
        "--force-new", action="store_true", help="Force create new session"
    )
    args = parser.parse_args()

    print_header()

    # Initialize session manager
    data_dir = Path("data")
    session_mgr = SessionManager(data_dir)

    # Check for existing session
    if not args.force_new:
        existing = session_mgr.load_latest_session(week=args.week)

        if existing and existing.season == args.season:
            print(f"[OK] Found existing Week {args.week} session")
            print(f"     Session ID: {existing.session_id}")
            print(f"     Started: {existing.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(
                f"     Last Updated: {existing.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            age_hours = (datetime.now() - existing.last_updated).total_seconds() / 3600
            if age_hours < 24:
                print(f"     Age: {age_hours:.1f} hours (recent)")
            else:
                print(f"     Age: {age_hours / 24:.1f} days")

            print(f"\n     Bankroll: ${existing.bankroll:,.2f}")
            print(f"     Opportunities: {existing.opportunities_identified}")
            print(f"     Bets Placed: {existing.bets_placed}")

            if existing.total_risk_deployed > 0:
                risk_pct = (existing.total_risk_deployed / existing.bankroll) * 100
                print(
                    f"     Risk Deployed: ${existing.total_risk_deployed:,.2f} ({risk_pct:.1f}%)"
                )

            print("\n     Resume this session? [Y/n]: ", end="")
            resume = input().strip().lower()

            if resume in ("", "y", "yes"):
                session = existing
                print("\n[OK] Resuming existing session")
            else:
                print("\n[INFO] Creating new session...")
                session = session_mgr.create_session(
                    args.week, args.season, args.bankroll
                )
        else:
            print(f"[INFO] No existing Week {args.week} session found")
            print("[INFO] Creating new session...")
            session = session_mgr.create_session(args.week, args.season, args.bankroll)
    else:
        print("[INFO] Force creating new session...")
        session = session_mgr.create_session(args.week, args.season, args.bankroll)

    # Display session info
    print_section(f"Week {args.week} Session - {session.session_id}")

    # Readiness checklist
    print_section("Readiness Checklist")

    checklist_items = [
        (
            "Power ratings updated (Week 11 results applied)",
            check_power_ratings(session),
            "CRITICAL",
        ),
        ("Latest injury reports checked", check_injuries(session), "REQUIRED"),
        ("Weather forecasts reviewed", check_weather(session), "RECOMMENDED"),
        ("Opportunities identified", session.opportunities_identified > 0, "GOAL"),
    ]

    all_critical_done = True

    for item, status, priority in checklist_items:
        if status:
            symbol = "[OK]"
        elif priority == "CRITICAL":
            symbol = "[!!!]"
            all_critical_done = False
        elif priority == "REQUIRED":
            symbol = "[TODO]"
            all_critical_done = False
        else:
            symbol = "[--]"

        priority_tag = f"[{priority}]" if priority != "GOAL" else ""
        print(f"{symbol} {item:50} {priority_tag}")

    # Risk summary
    print_section("Risk Management Summary")

    risk_summary = session.get_risk_summary()

    print(f"Current Bankroll: ${risk_summary['bankroll']:,.2f}")
    print(
        f"Total Deployed: ${risk_summary['total_deployed']:,.2f} ({risk_summary['deployment_pct']:.1f}%)"
    )
    print(f"Remaining Capacity: ${risk_summary['remaining_capacity']:,.2f}")
    print(f"Active Bets: {risk_summary['active_bets']}")
    print(f"Pending Opportunities: {risk_summary['pending_opportunities']}")

    if risk_summary["within_limits"]:
        print("\n[OK] Within risk limits (15% weekly max)")
    else:
        print("\n[WARNING] OVER 15% weekly risk limit!")

    # Next steps
    print_section("Next Steps")

    if not session.power_ratings_updated:
        print("[1] UPDATE POWER RATINGS (CRITICAL - Do First!)")
        print("    Command:")
        print("    python billy_walters_power_ratings.py --week 11 --update")
        print()

    if not session.injuries_checked:
        print("[2] CHECK INJURY REPORTS")
        print("    - Visit NFL.com injury reports")
        print("    - Check official team Twitter/X accounts")
        print("    - Review practice participation reports")
        print()

    if not session.weather_checked:
        print("[3] REVIEW WEATHER FORECASTS")
        print("    - Check forecasts for outdoor games")
        print("    - Look for wind, cold, precipitation")
        print("    - Update S-factors accordingly")
        print()

    if session.opportunities_identified == 0:
        print("[4] RUN EDGE ANALYSIS")
        print("    Command:")
        print(
            f"    python analyze_edges.py --week {args.week} --bankroll {args.bankroll:.0f} --min-edge 5.5"
        )
        print()

    print("[5] VIEW OPPORTUNITIES")
    print("    Command:")
    print(f"    python view_opportunities.py --week {args.week}")
    print()

    print("[6] START MONITORING (Optional)")
    print("    Command:")
    print("    python start_monitor.py --interval 60")
    print()

    # Additional resources
    print_section("Documentation & Resources")

    print("Session Continuity:")
    print("  src/walters_analyzer/docs/session_continuity/WEEK12_CONTINUITY.md")
    print()
    print("Quick Reference:")
    print("  src/walters_analyzer/docs/operations/WEEK12_QUICK_START.md")
    print()
    print("Methodology:")
    print("  src/walters_analyzer/docs/methodology/BILLY_WALTERS_PRINCIPLES.md")
    print()

    # Important reminders
    print_section("Critical Reminders")

    print("[WARNING] RISK LIMITS (NON-NEGOTIABLE):")
    print("  - Single bet max: 3% of bankroll ($600 max at $20K)")
    print("  - Weekly exposure max: 15% of bankroll ($3,000 max)")
    print("  - Minimum edge: 5.5% (no exceptions)")
    print("  - Stop-loss: 10% weekly drawdown ($2,000)")
    print()

    print("[PROCESS] Billy Walters Principles:")
    print("  1. Accuracy > Speed - Validate all data")
    print("  2. Math > Intuition - Trust the numbers")
    print("  3. Process > Results - Short-term variance is normal")
    print("  4. Bankroll preservation is SACRED")
    print("  5. Need 100+ bets for statistical validity")
    print()

    print("[TIMING] Betting Strategy:")
    print("  - FAVORITES: Bet early (Tuesday-Thursday)")
    print("  - UNDERDOGS: Bet late (Saturday)")
    print("  - ALWAYS: Shop lines across 5+ books")
    print()

    # Save session
    session_mgr.save_session(session)

    # Final status
    print("=" * 70)

    if all_critical_done and session.opportunities_identified > 0:
        print("[OK] SYSTEM READY - You can start placing bets")
    elif all_critical_done:
        print("[OK] PREREQUISITES MET - Ready to analyze opportunities")
    else:
        print("[TODO] COMPLETE CRITICAL ITEMS FIRST")

    print(f"\nSession saved: {session.session_id}")
    print(f"Data location: {data_dir / 'sessions' / f'{session.session_id}.json'}")
    print("\n" + "=" * 70 + "\n")

    print(f"[OK] Week {args.week} quick start complete!")
    print()


if __name__ == "__main__":
    main()
