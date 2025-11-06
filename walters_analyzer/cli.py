import argparse, json, sys, pathlib, subprocess
from walters_analyzer.wkcard import load_card, summarize_card, validate_gates

def main():
    parser = argparse.ArgumentParser(prog="walters-analyzer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    wk = sub.add_parser("wk-card", help="Run/preview a wk-card JSON")
    wk.add_argument("--file", required=True, help="Path to wk-card JSON")
    wk.add_argument("--dry-run", action="store_true", help="Preview entries and gating without 'placing'")
    
    scrape = sub.add_parser("scrape-overtime", help="Scrape odds from overtime.ag")
    scrape.add_argument("--sport", choices=["nfl", "cfb", "both"], default="both", 
                        help="Sport to scrape: nfl, cfb (college football), or both")
    scrape.add_argument("--live", action="store_true", 
                        help="Scrape live betting odds instead of pre-game")
    scrape.add_argument("--output-dir", default=None,
                        help="Output directory for scraped data (default: data/odds/nfl or data/odds/ncaaf)")
    
    injuries = sub.add_parser("scrape-injuries", help="Scrape injury reports from ESPN")
    injuries.add_argument("--sport", choices=["nfl", "cfb"], default="cfb",
                          help="Sport to scrape: nfl or cfb (college football)")
    injuries.add_argument("--output-dir", default=None,
                          help="Output directory for injury data (default: data/injuries/nfl or data/injuries/ncaaf)")
    
    # view-odds: View scraped pregame odds
    vo = sub.add_parser("view-odds", help="View scraped pregame odds from overtime.ag")
    vo.add_argument("--data-dir", default="data/overtime_live",
                   help="Directory containing scraped data")
    vo.add_argument("--file", help="Specific JSONL file to load")
    vo.add_argument("--sport", choices=["nfl", "college_football"],
                   help="Filter by sport")
    vo.add_argument("--date", help="Filter by date (YYYY-MM-DD)")
    vo.add_argument("--today", action="store_true",
                   help="Show today's games")
    vo.add_argument("--upcoming", type=int, metavar="DAYS",
                   help="Show games in next N days (default: 7)", const=7, nargs="?")
    vo.add_argument("--team", help="Filter by team name (partial match)")
    vo.add_argument("--compare", metavar="TEAM",
                   help="Compare lines for a team across games")
    vo.add_argument("--summary", action="store_true",
                   help="Show summary only (no detailed odds)")
    vo.add_argument("--brief", action="store_true",
                   help="Brief output (game info only, no odds)")
    vo.add_argument("--export", metavar="FILE",
                   help="Export filtered results to CSV file")
    
    args = parser.parse_args()

    if args.cmd == "wk-card":
        p = pathlib.Path(args.file)
        if not p.exists():
            print(f"ERROR: card not found: {p}", file=sys.stderr)
            sys.exit(2)

        card = load_card(p)
        problems = validate_gates(card)
        if problems:
            print("GATE CHECKS FAILED:")
            for pr in problems:
                print(f" - {pr}")
            sys.exit(1)

        print(summarize_card(card, dry_run=args.dry_run))
    
    elif args.cmd == "scrape-overtime":
        # Set default output directory based on sport
        if args.output_dir is None:
            if args.sport == "nfl":
                args.output_dir = "data/odds/nfl"
            elif args.sport == "cfb":
                args.output_dir = "data/odds/ncaaf"
            else:  # both
                args.output_dir = "data/odds"  # Will separate by sport in pipeline
        
        # Determine which spider to run
        if args.live:
            spider_name = "overtime_live"
            print(f"Starting live betting scraper for overtime.ag...")
        else:
            spider_name = "pregame_odds"
            print(f"Starting pre-game odds scraper for overtime.ag ({args.sport})...")
        
        print(f"Output directory: {args.output_dir}")
        
        # Build scrapy command
        cmd = [
            "scrapy", "crawl", spider_name,
            "-s", f"OVERTIME_OUT_DIR={args.output_dir}"
        ]
        
        # Add sport argument for pregame spider
        if not args.live:
            cmd.extend(["-a", f"sport={args.sport}"])
        
        # Run scrapy
        try:
            result = subprocess.run(cmd, check=True)
            try:
                print(f"\n[OK] Scraping completed. Check {args.output_dir}/ for output files.")
            except UnicodeEncodeError:
                print(f"\n[OK] Scraping completed. Check {args.output_dir}/ for output files.")
            sys.exit(result.returncode)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Scraping failed with exit code {e.returncode}", file=sys.stderr)
            sys.exit(e.returncode)
        except FileNotFoundError:
            print("ERROR: scrapy command not found. Make sure scrapy is installed.", file=sys.stderr)
            print("Run: uv pip install scrapy scrapy-playwright", file=sys.stderr)
            sys.exit(1)
    
    elif args.cmd == "scrape-injuries":
        # Map sport argument to ESPN's URL format
        sport_map = {
            "nfl": ("football", "nfl"),
            "cfb": ("football", "college-football")
        }
        espn_sport, espn_league = sport_map[args.sport]
        
        # Set default output directory based on sport
        if args.output_dir is None:
            if args.sport == "nfl":
                args.output_dir = "data/injuries/nfl"
            else:  # cfb
                args.output_dir = "data/injuries/ncaaf"
        
        print(f"Starting ESPN injury report scraper for {args.sport.upper()}...")
        print(f"Output directory: {args.output_dir}")
        
        # Build scrapy command with environment variables for ESPN spider
        import os
        env = os.environ.copy()
        env["ESPN_SPORT"] = espn_sport
        env["ESPN_LEAGUE"] = espn_league
        
        # Use sport-specific filename prefix
        filename_prefix = "nfl-injuries" if args.sport == "nfl" else "ncaaf-injuries"
        
        cmd = [
            "scrapy", "crawl", "espn_injuries",
            "-s", f"FEEDS[{args.output_dir}/{filename_prefix}-%(time)s.jsonl]=jsonlines",
            "-s", f"FEEDS[{args.output_dir}/{filename_prefix}-%(time)s.parquet]=parquet",
        ]
        
        # Run scrapy
        try:
            result = subprocess.run(cmd, env=env, check=True)
            try:
                print(f"\n[OK] Injury scraping completed. Check {args.output_dir}/ for output files.")
            except UnicodeEncodeError:
                print(f"\n[OK] Injury scraping completed. Check {args.output_dir}/ for output files.")
            sys.exit(result.returncode)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Injury scraping failed with exit code {e.returncode}", file=sys.stderr)
            sys.exit(e.returncode)
        except FileNotFoundError:
            print("ERROR: scrapy command not found. Make sure scrapy is installed.", file=sys.stderr)
            print("Run: uv pip install scrapy scrapy-playwright", file=sys.stderr)
            sys.exit(1)
    
    elif args.cmd == "view-odds":
        from .query.odds_viewer import OddsViewer
        from pathlib import Path
        
        # Initialize viewer
        viewer = OddsViewer(data_dir=args.data_dir)
        
        # Load data
        if args.file:
            count = viewer.load_file(Path(args.file), sport=args.sport)
            print(f"📂 Loaded {count} games from {args.file}\n")
        else:
            count = viewer.load_latest(sport=args.sport)
            if count > 0:
                data_path = Path(args.data_dir)
                jsonl_files = sorted(data_path.glob("overtime-live-*.jsonl"), reverse=True)
                if jsonl_files:
                    print(f"📂 Loaded {count} games from {jsonl_files[0].name}\n")
        
        if count == 0:
            print("❌ No games found. Run scraper first:")
            print("   uv run walters-analyzer scrape-overtime --sport nfl")
            sys.exit(1)
        
        # Show summary if requested
        if args.summary:
            viewer.display_summary()
            sys.exit(0)
        
        # Compare mode
        if args.compare:
            viewer.compare_lines(args.compare)
            sys.exit(0)
        
        # Filter games
        games = viewer.games
        
        if args.today:
            games = viewer.get_today_games()
            print("📅 Today's games:\n")
        elif args.upcoming is not None:
            days = args.upcoming if args.upcoming else 7
            games = viewer.get_upcoming_games(days=days)
            print(f"📅 Upcoming games (next {days} days):\n")
        elif args.date:
            games = viewer.filter_by_date(args.date)
            print(f"📅 Games on {args.date}:\n")
        
        if args.team:
            games = [g for g in games if any(
                args.team.lower() in team.lower()
                for team in [g.get("teams", {}).get("away", ""), g.get("teams", {}).get("home", "")]
            )]
            print(f"🔍 Filtered for team: '{args.team}'\n")
        
        # Export if requested
        if args.export:
            viewer.export_csv(games, args.export)
        else:
            # Display games
            viewer.display_games(games, show_details=not args.brief)
        
        sys.exit(0)

if __name__ == "__main__":
    main()
