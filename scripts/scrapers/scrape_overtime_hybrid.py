#!/usr/bin/env python3
"""
Run Overtime.ag Hybrid Scraper (Playwright + SignalR)

Combines web scraping (pre-game lines) with real-time WebSocket updates (live odds).

Usage:
    # Basic usage (2 minutes of SignalR listening)
    uv run python scripts/scrape_overtime_hybrid.py

    # Extended listening (10 minutes)
    uv run python scripts/scrape_overtime_hybrid.py --duration 600

    # Headless mode (production)
    uv run python scripts/scrape_overtime_hybrid.py --headless --duration 300

    # Disable SignalR (pre-game only)
    uv run python scripts/scrape_overtime_hybrid.py --no-signalr

    # With proxy
    uv run python scripts/scrape_overtime_hybrid.py --proxy "http://user:pass@proxy:port"
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.overtime_hybrid_scraper import OvertimeHybridScraper


def parse_args():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(
        description="Overtime.ag Hybrid Scraper (Playwright + SignalR)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (2 minutes of live updates)
  uv run python scripts/scrape_overtime_hybrid.py

  # Extended listening (10 minutes)
  uv run python scripts/scrape_overtime_hybrid.py --duration 600

  # Headless mode for production
  uv run python scripts/scrape_overtime_hybrid.py --headless --duration 300

  # Pre-game only (no SignalR)
  uv run python scripts/scrape_overtime_hybrid.py --no-signalr

Timing Recommendations:
  - Pre-game scraping: Tuesday-Wednesday after Monday Night Football
  - Live updates: Sunday/Monday during games (use --duration 3600 or more)
  - Quick check: Default 120 seconds is sufficient for testing
        """,
    )

    parser.add_argument(
        "--customer-id",
        type=str,
        default=None,
        help="Overtime.ag customer ID (defaults to OV_CUSTOMER_ID env var)",
    )

    parser.add_argument(
        "--password",
        type=str,
        default=None,
        help="Overtime.ag password (defaults to OV_PASSWORD env var)",
    )

    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help='Proxy URL with credentials (e.g., "http://user:pass@host:port")',
    )

    parser.add_argument(
        "--no-proxy", action="store_true", help="Disable smart proxy (use no proxy)"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (no visible window)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output/overtime/nfl",
        help="Output directory (default: output/overtime/nfl)",
    )

    parser.add_argument(
        "--no-signalr",
        action="store_true",
        help="Disable SignalR (pre-game scraping only)",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=120,
        help="How long to listen for SignalR updates in seconds (default: 120)",
    )

    return parser.parse_args()


async def main():
    """Main entry point"""

    args = parse_args()

    print("=" * 70)
    print("Overtime.ag Hybrid Scraper")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Customer ID: {args.customer_id or 'from environment'}")
    print(f"  Proxy: {args.proxy or 'smart proxy' if not args.no_proxy else 'none'}")
    print(f"  Headless: {args.headless}")
    print(f"  SignalR: {'enabled' if not args.no_signalr else 'disabled'}")
    if not args.no_signalr:
        print(f"  SignalR duration: {args.duration} seconds")
    print(f"  Output directory: {args.output}")
    print()

    # Create scraper
    scraper = OvertimeHybridScraper(
        customer_id=args.customer_id,
        password=args.password,
        proxy_url=args.proxy if args.proxy else None,
        headless=args.headless,
        output_dir=args.output,
        use_smart_proxy=not args.no_proxy and args.proxy is None,
        enable_signalr=not args.no_signalr,
        signalr_duration=args.duration,
    )

    # Run scraper
    try:
        result = await scraper.scrape()

        print()
        print("=" * 70)
        print("SCRAPING COMPLETE")
        print("=" * 70)
        print()
        print("Results:")
        print(f"  Pre-game games: {len(result['pregame']['games'])}")
        print(f"  Live updates: {len(result['live']['updates'])}")
        print()
        print("Next steps:")
        print("  1. Review output file for data quality")
        print("  2. Run edge detection: /edge-detector")
        print("  3. Generate betting card: /betting-card")
        print()

        return 0

    except KeyboardInterrupt:
        print()
        print("Scraping interrupted by user (Ctrl+C)")
        return 1

    except Exception as e:
        print()
        print(f"[ERROR] Scraping failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
