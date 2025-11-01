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
    scrape.add_argument("--output-dir", default="data/overtime_live",
                        help="Output directory for scraped data")
    
    injuries = sub.add_parser("scrape-injuries", help="Scrape injury reports from ESPN")
    injuries.add_argument("--sport", choices=["nfl", "cfb"], default="cfb",
                          help="Sport to scrape: nfl or cfb (college football)")
    injuries.add_argument("--output-dir", default="data/injuries",
                          help="Output directory for injury data")
    
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
        # Determine which spider to run
        if args.live:
            spider_name = "overtime_live"
            print(f"Starting live betting scraper for overtime.ag...")
        else:
            spider_name = "pregame_odds"
            print(f"Starting pre-game odds scraper for overtime.ag ({args.sport})...")
        
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
            print(f"\n✓ Scraping completed. Check {args.output_dir}/ for output files.")
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
        
        print(f"Starting ESPN injury report scraper for {args.sport.upper()}...")
        
        # Build scrapy command with environment variables for ESPN spider
        import os
        env = os.environ.copy()
        env["ESPN_SPORT"] = espn_sport
        env["ESPN_LEAGUE"] = espn_league
        
        # Use proper Scrapy settings (not FEEDS which doesn't support parquet)
        # The InjuryPipeline handles output in both JSONL and Parquet formats
        cmd = [
            "scrapy", "crawl", "espn_injuries",
            "-s", f"INJURY_OUT_DIR={args.output_dir}",
        ]
        
        # Run scrapy
        try:
            result = subprocess.run(cmd, env=env, check=True)
            print(f"\n✓ Injury scraping completed. Check {args.output_dir}/ for output files.")
            sys.exit(result.returncode)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Injury scraping failed with exit code {e.returncode}", file=sys.stderr)
            sys.exit(e.returncode)
        except FileNotFoundError:
            print("ERROR: scrapy command not found. Make sure scrapy is installed.", file=sys.stderr)
            print("Run: uv pip install scrapy scrapy-playwright", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
