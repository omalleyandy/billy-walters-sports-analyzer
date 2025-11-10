import argparse, json, sys, pathlib, subprocess, logging
from walters_analyzer.wkcard import load_card, summarize_card, validate_gates
from walters_analyzer.config import get_settings

def setup_logging(settings):
    """Setup logging based on configuration."""
    log_level = getattr(logging, settings.global_config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.logs_dir / 'walters-analyzer.log')
        ]
    )

def main():
    # Initialize unified settings
    try:
        settings = get_settings()
        setup_logging(settings)
        logger = logging.getLogger(__name__)

        if settings.global_config.debug_mode:
            logger.debug("Debug mode enabled")
            logger.debug(f"Project root: {settings.project_root}")
            logger.debug(f"Skills enabled: market_analysis={settings.skills.market_analysis.enabled}, "
                        f"ml_power_ratings={settings.skills.ml_power_ratings.enabled}, "
                        f"situational_database={settings.skills.situational_database.enabled}")
    except Exception as e:
        print(f"WARNING: Failed to load unified settings: {e}", file=sys.stderr)
        print("Continuing with defaults...", file=sys.stderr)
        settings = None

    parser = argparse.ArgumentParser(prog="walters-analyzer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    wk = sub.add_parser("wk-card", help="Run/preview a wk-card JSON")
    wk.add_argument("--file", required=True, help="Path to wk-card JSON")
    wk.add_argument("--dry-run", action="store_true", help="Preview entries and gating without 'placing'")
    wk.add_argument("--show-bankroll", action="store_true", help="Show bankroll percentages and amounts")
    wk.add_argument("--bankroll", type=float, default=10000.0, help="Starting bankroll amount (default: $10,000)")
    
    # analyze-game: Analyze a single game with full Billy Walters methodology
    analyze = sub.add_parser("analyze-game", help="Analyze a game using Billy Walters methodology")
    analyze.add_argument("--home", required=True, help="Home team name")
    analyze.add_argument("--away", required=True, help="Away team name")
    analyze.add_argument("--spread", type=float, help="Current spread (home team perspective)")
    analyze.add_argument("--total", type=float, help="Current total")
    analyze.add_argument("--home-price", type=int, default=-110, help="Home spread price (default: -110)")
    analyze.add_argument("--away-price", type=int, default=-110, help="Away spread price (default: -110)")
    analyze.add_argument("--venue", help="Stadium/venue name for weather lookup")
    analyze.add_argument("--date", help="Game date (YYYY-MM-DD)")
    analyze.add_argument("--bankroll", type=float, default=10000.0, help="Starting bankroll (default: $10,000)")
    analyze.add_argument("--research", action="store_true", help="Fetch live injury/weather data")
    
    # scrape-ai: Scrape odds with AI-assisted performance monitoring (NEW!)
    scrape_ai = sub.add_parser("scrape-ai", help="Scrape odds with AI performance monitoring (requires MCP chrome-devtools)")
    scrape_ai.add_argument("--sport", choices=["nfl", "ncaaf"], default="nfl",
                          help="Sport to scrape")
    scrape_ai.add_argument("--output-dir", default="data/odds_chrome",
                          help="Output directory for scraped data")
    scrape_ai.add_argument("--no-ai-report", action="store_true",
                          help="Skip AI insights report")
    
    # interactive: Interactive slash command mode (NEW!)
    interactive = sub.add_parser("interactive", help="Enter interactive slash command mode")
    interactive.add_argument("--bankroll", type=float, default=10000.0,
                           help="Starting bankroll (default: $10,000)")
    
    # slash: Execute a single slash command (NEW!)
    slash = sub.add_parser("slash", help="Execute a single slash command")
    slash.add_argument("command", help="Slash command to execute (e.g., '/analyze Chiefs vs Bills -2.5')")
    slash.add_argument("--bankroll", type=float, default=10000.0,
                      help="Starting bankroll (default: $10,000)")
    
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
    
    # scrape-highlightly: Scrape data from Highlightly API
    highlightly = sub.add_parser("scrape-highlightly", help="Scrape NFL/NCAA data from Highlightly API")
    highlightly.add_argument("--endpoint", 
                            choices=["teams", "matches", "highlights", "odds", "bookmakers", 
                                   "standings", "lineups", "players", "last-five", "head-to-head", "all"],
                            required=True,
                            help="API endpoint to scrape")
    highlightly.add_argument("--sport", choices=["nfl", "ncaaf", "both"], default="both",
                            help="Sport to scrape: nfl, ncaaf (college football), or both")
    highlightly.add_argument("--date", 
                            help="Date filter (YYYY-MM-DD format, for matches/highlights)")
    highlightly.add_argument("--match-id", type=int,
                            help="Match ID (for match details, odds, lineups)")
    highlightly.add_argument("--team-id", type=int,
                            help="Team ID (for statistics, last-five games)")
    highlightly.add_argument("--team-id-two", type=int,
                            help="Second team ID (for head-to-head)")
    highlightly.add_argument("--name",
                            help="Search by name (for teams/players)")
    highlightly.add_argument("--season", type=int,
                            help="Season year filter")
    highlightly.add_argument("--output-dir", default=None,
                            help="Output directory (default: data/highlightly/nfl or data/highlightly/ncaaf)")
    highlightly.add_argument("--odds-type", choices=["prematch", "live"], default="prematch",
                            help="Odds type: prematch or live (default: prematch)")
    
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

    # monitor-sharp: Monitor market for sharp money movements
    monitor = sub.add_parser("monitor-sharp", help="Monitor market for sharp money movements")
    monitor.add_argument("--sport",
                        choices=["nfl", "ncaaf", "nba", "mlb", "nhl"],
                        default="nfl",
                        help="Sport to monitor (default: nfl)")
    monitor.add_argument("--game-id",
                        help="Specific game ID to monitor (optional)")
    monitor.add_argument("--duration",
                        type=int,
                        default=120,
                        help="Duration to monitor in minutes (default: 120)")
    monitor.add_argument("--interval",
                        type=int,
                        help="Check interval in seconds (default: from settings)")
    monitor.add_argument("--test",
                        action="store_true",
                        help="Test connection to The Odds API")

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

        # Initialize analyzer if bankroll display requested
        analyzer = None
        if args.show_bankroll:
            from walters_analyzer.core import BillyWaltersAnalyzer
            analyzer = BillyWaltersAnalyzer()
            analyzer.bankroll.bankroll = args.bankroll

        print(summarize_card(card, dry_run=args.dry_run, analyzer=analyzer, show_bankroll=args.show_bankroll))
    
    elif args.cmd == "analyze-game":
        import asyncio
        from datetime import datetime
        from walters_analyzer.core import BillyWaltersAnalyzer
        from walters_analyzer.core.models import GameInput, TeamSnapshot, GameOdds, SpreadLine
        
        async def run_analysis():
            # Build game input
            home_team = TeamSnapshot(name=args.home, injuries=[])
            away_team = TeamSnapshot(name=args.away, injuries=[])
            
            odds = None
            if args.spread is not None:
                odds = GameOdds(
                    spread=SpreadLine(
                        home_spread=args.spread,
                        home_price=args.home_price,
                        away_price=args.away_price
                    )
                )
            
            game = GameInput(
                home_team=home_team,
                away_team=away_team,
                odds=odds,
                kickoff=datetime.fromisoformat(args.date) if args.date else None
            )
            
            # Fetch research data if requested
            if args.research:
                from walters_analyzer.research import ResearchEngine
                
                print("[*] Gathering research data...")
                engine = ResearchEngine()
                
                try:
                    snapshot = await engine.gather_for_game(
                        args.home,
                        args.away,
                        venue=args.venue,
                        date=game.kickoff
                    )
                    
                    # Update game with research data
                    home_team.injuries = snapshot.home_injuries
                    away_team.injuries = snapshot.away_injuries
                    
                    if snapshot.weather:
                        game.weather = snapshot.weather.get('conditions', 'Unknown')
                    
                    print(f"[+] Loaded {len(snapshot.home_injuries)} home injuries")
                    print(f"[+] Loaded {len(snapshot.away_injuries)} away injuries")
                    if snapshot.weather:
                        print(f"[+] Weather: {snapshot.weather.get('conditions', 'N/A')}")
                    print()
                    
                finally:
                    await engine.close()
            
            # Run analysis
            analyzer = BillyWaltersAnalyzer()
            analyzer.bankroll.bankroll = args.bankroll
            
            result = analyzer.analyze(game)
            
            # Display results
            print("=" * 80)
            print(f"BILLY WALTERS GAME ANALYSIS")
            print("=" * 80)
            print()
            print(f"Matchup:  {args.away} @ {args.home}")
            if odds:
                print(f"Spread:   {args.home} {result.market_spread:+.1f} ({args.home_price:+d}/{args.away_price:+d})")
            print()
            
            # Injury reports
            print("HOME TEAM INJURIES:")
            print(f"  Total Impact: {result.home_report.total_points:+.1f} pts")
            if result.home_report.critical_players:
                print(f"  Critical: {', '.join(result.home_report.critical_players)}")
            for note in result.home_report.detailed_notes[:3]:
                print(f"  • {note}")
            print()
            
            print("AWAY TEAM INJURIES:")
            print(f"  Total Impact: {result.away_report.total_points:+.1f} pts")
            if result.away_report.critical_players:
                print(f"  Critical: {', '.join(result.away_report.critical_players)}")
            for note in result.away_report.detailed_notes[:3]:
                print(f"  • {note}")
            print()
            
            # Analysis
            print("ANALYSIS:")
            print(f"  Predicted Spread: {result.predicted_spread:+.1f}")
            print(f"  Market Spread:    {result.market_spread:+.1f}")
            print(f"  Edge:             {result.edge:+.1f} pts")
            print(f"  Confidence:       {result.confidence}")
            print()
            
            # Key numbers
            if result.key_number_alerts:
                print("KEY NUMBER ALERTS:")
                for alert in result.key_number_alerts:
                    icon = "[!]" if alert.crossed else "[*]"
                    print(f"  {icon} {alert.description}")
                print()
            
            # Recommendation
            rec = result.recommendation
            print("=" * 80)
            print(f"RECOMMENDATION: {rec.conviction}")
            print("=" * 80)
            if rec.stake_pct > 0:
                stake_amt = analyzer.bankroll.stake_amount(rec.stake_pct)
                print(f"Bet Type:      {rec.bet_type.upper()}")
                print(f"Team:          {rec.team}")
                print(f"Edge:          {rec.edge:+.1f} pts")
                print(f"Win Prob:      {rec.win_probability:.1%}")
                print(f"Stake:         {rec.stake_pct:.2f}% (${stake_amt:,.2f})")
                print()
                print("Notes:")
                for note in rec.notes:
                    print(f"  • {note}")
            else:
                print("NO PLAY - Edge insufficient for Kelly sizing")
                print()
                if rec.notes:
                    print("Analysis Notes:")
                    for note in rec.notes:
                        print(f"  • {note}")
            print()
        
        asyncio.run(run_analysis())
        sys.exit(0)
    
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
    
    elif args.cmd == "scrape-highlightly":
        import asyncio
        from dotenv import load_dotenv
        from walters_analyzer.feeds.highlightly_client import HighlightlyClient
        from walters_analyzer.feeds.highlightly_storage import save_to_jsonl
        
        # Ensure .env file is loaded
        env_path = pathlib.Path('.env')
        if env_path.exists():
            load_dotenv(env_path)
        else:
            print("⚠️  Warning: .env file not found in project root")
            print("   Make sure HIGHLIGHTLY_API_KEY is set as an environment variable")
        
        async def scrape_highlightly():
            # Determine sports to scrape
            sports = []
            if args.sport == "both":
                sports = ["nfl", "ncaaf"]
            else:
                sports = [args.sport]
            
            # Map sport names for API
            sport_map = {
                "nfl": "NFL",
                "ncaaf": "NCAA"
            }
            
            total_saved = 0
            
            for sport_key in sports:
                league = sport_map[sport_key]
                print(f"\n{'='*60}")
                print(f"Scraping {args.endpoint} data for {league}")
                print(f"{'='*60}\n")
                
                # Set output directory
                output_dir = args.output_dir or f"data/highlightly/{sport_key}"
                
                try:
                    async with HighlightlyClient() as client:
                        
                        # Teams endpoint
                        if args.endpoint in ["teams", "all"]:
                            print(f"📥 Fetching teams...")
                            teams = await client.get_teams(league=league, name=args.name)
                            if teams:
                                save_to_jsonl(teams, "teams", sport_key, output_dir)
                                total_saved += len(teams)
                        
                        # Matches endpoint
                        if args.endpoint in ["matches", "all"]:
                            print(f"📥 Fetching matches...")
                            matches = await client.get_matches(
                                league=league,
                                date=args.date,
                                season=args.season
                            )
                            if matches:
                                extra = args.date or "latest"
                                save_to_jsonl(matches, "matches", sport_key, output_dir, extra)
                                total_saved += len(matches)
                        
                        # Match details (requires match_id)
                        if args.endpoint == "matches" and args.match_id:
                            print(f"📥 Fetching match details for ID {args.match_id}...")
                            match_details = await client.get_match_by_id(args.match_id)
                            if match_details:
                                save_to_jsonl([match_details], "match-details", sport_key, 
                                             output_dir, str(args.match_id))
                                total_saved += 1
                        
                        # Odds endpoint
                        if args.endpoint in ["odds", "all"]:
                            print(f"📥 Fetching odds ({args.odds_type})...")
                            odds = await client.get_odds(
                                match_id=args.match_id,
                                odds_type=args.odds_type,
                                league_name=league,
                                date=args.date
                            )
                            if odds:
                                extra = str(args.match_id) if args.match_id else (args.date or "latest")
                                save_to_jsonl(odds, f"odds-{args.odds_type}", sport_key, 
                                             output_dir, extra)
                                total_saved += len(odds)
                        
                        # Bookmakers endpoint
                        if args.endpoint in ["bookmakers", "all"]:
                            print(f"📥 Fetching bookmakers...")
                            bookmakers = await client.get_bookmakers(name=args.name)
                            if bookmakers:
                                save_to_jsonl(bookmakers, "bookmakers", sport_key, output_dir)
                                total_saved += len(bookmakers)
                        
                        # Highlights endpoint
                        if args.endpoint in ["highlights", "all"]:
                            print(f"📥 Fetching highlights...")
                            highlights = await client.get_highlights(
                                league_name=league,
                                date=args.date,
                                season=args.season,
                                match_id=args.match_id
                            )
                            if highlights:
                                extra = args.date or "latest"
                                save_to_jsonl(highlights, "highlights", sport_key, output_dir, extra)
                                total_saved += len(highlights)
                        
                        # Standings endpoint
                        if args.endpoint in ["standings", "all"]:
                            print(f"📥 Fetching standings...")
                            standings = await client.get_standings(
                                league_type=league,
                                year=args.season
                            )
                            if standings:
                                extra = str(args.season) if args.season else "current"
                                save_to_jsonl([standings], "standings", sport_key, output_dir, extra)
                                total_saved += 1
                        
                        # Lineups endpoint (requires match_id)
                        if args.endpoint == "lineups":
                            if not args.match_id:
                                print("❌ --match-id required for lineups endpoint")
                                sys.exit(1)
                            print(f"📥 Fetching lineups for match {args.match_id}...")
                            lineups = await client.get_lineups(args.match_id)
                            if lineups:
                                save_to_jsonl([lineups], "lineups", sport_key, 
                                             output_dir, str(args.match_id))
                                total_saved += 1
                        
                        # Players endpoint
                        if args.endpoint in ["players", "all"]:
                            print(f"📥 Fetching players...")
                            players = await client.get_players(name=args.name)
                            if players:
                                extra = args.name if args.name else "all"
                                save_to_jsonl(players, "players", sport_key, output_dir, extra)
                                total_saved += len(players)
                        
                        # Last five games (requires team_id)
                        if args.endpoint == "last-five":
                            if not args.team_id:
                                print("❌ --team-id required for last-five endpoint")
                                sys.exit(1)
                            print(f"📥 Fetching last 5 games for team {args.team_id}...")
                            last_five = await client.get_last_five_games(args.team_id)
                            if last_five:
                                save_to_jsonl(last_five, "last-five", sport_key, 
                                             output_dir, str(args.team_id))
                                total_saved += len(last_five)
                        
                        # Head to head (requires team_id and team_id_two)
                        if args.endpoint == "head-to-head":
                            if not args.team_id or not args.team_id_two:
                                print("❌ --team-id and --team-id-two required for head-to-head endpoint")
                                sys.exit(1)
                            print(f"📥 Fetching head-to-head for teams {args.team_id} vs {args.team_id_two}...")
                            h2h = await client.get_head_to_head(args.team_id, args.team_id_two)
                            if h2h:
                                save_to_jsonl(h2h, "head-to-head", sport_key, 
                                             output_dir, f"{args.team_id}-vs-{args.team_id_two}")
                                total_saved += len(h2h)
                
                except Exception as e:
                    print(f"❌ Error scraping {sport_key}: {e}")
                    import traceback
                    traceback.print_exc()
                    sys.exit(1)
            
            print(f"\n{'='*60}")
            print(f"✅ Scraping complete! Total items saved: {total_saved}")
            print(f"{'='*60}\n")
        
        # Run async scraper
        asyncio.run(scrape_highlightly())
        sys.exit(0)
    
    elif args.cmd == "view-odds":
        from .query.odds_viewer import OddsViewer
        from pathlib import Path
        
        # Initialize viewer
        viewer = OddsViewer(data_dir=args.data_dir)
        
        # Load data
        if args.file:
            count = viewer.load_file(Path(args.file), sport=args.sport)
            print(f"[*] Loaded {count} games from {args.file}\n")
        else:
            count = viewer.load_latest(sport=args.sport)
            if count > 0:
                data_path = Path(args.data_dir)
                jsonl_files = sorted(data_path.glob("overtime-live-*.jsonl"), reverse=True)
                if jsonl_files:
                    print(f"[*] Loaded {count} games from {jsonl_files[0].name}\n")
        
        if count == 0:
            print("[!] No games found. Run scraper first:")
            print("    uv run walters-analyzer scrape-overtime --sport nfl")
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
            print(f"[FILTER] Team: '{args.team}'\n")
        
        # Export if requested
        if args.export:
            viewer.export_csv(games, args.export)
        else:
            # Display games
            viewer.display_games(games, show_details=not args.brief)

        sys.exit(0)

    elif args.cmd == "monitor-sharp":
        import asyncio
        from walters_analyzer.feeds.market_monitor import MarketMonitor
        from walters_analyzer.feeds.market_data_client import OddsAPIClient

        # Map sport names to The Odds API sport keys
        sport_map = {
            "nfl": "americanfootball_nfl",
            "ncaaf": "americanfootball_ncaaf",
            "nba": "basketball_nba",
            "mlb": "baseball_mlb",
            "nhl": "icehockey_nhl"
        }

        sport_key = sport_map.get(args.sport, "americanfootball_nfl")

        # Test mode - check API connection
        if args.test:
            print("🔍 Testing connection to The Odds API...")
            print()

            async def test_connection():
                client = OddsAPIClient()
                odds = await client.get_odds(sport_key)

                if not odds:
                    print("❌ Failed to fetch odds. Check your ODDS_API_KEY in .env")
                    print()
                    print("To get an API key:")
                    print("  1. Sign up at https://the-odds-api.com/")
                    print("  2. Copy your API key from the dashboard")
                    print("  3. Add to .env: ODDS_API_KEY=your_key_here")
                    sys.exit(1)

                print(f"✅ Successfully connected!")
                print(f"✅ Fetched odds for {len(set(o['game_id'] for o in odds))} games")
                print()

                # Show sample
                if odds:
                    sample = odds[0]
                    teams = sample.get('teams', {})
                    print("📊 Sample game:")
                    print(f"   {teams.get('away')} @ {teams.get('home')}")
                    print(f"   Book: {sample.get('book')}")

                    spread = sample.get('markets', {}).get('spread', {})
                    if spread.get('home'):
                        line = spread['home'].get('line')
                        print(f"   Spread: {line:+.1f}")

                print()
                print("✅ All systems ready! Remove --test to start monitoring.")

            asyncio.run(test_connection())
            sys.exit(0)

        # Start monitoring
        print("=" * 80)
        print("BILLY WALTERS SHARP MONEY MONITOR")
        print("=" * 80)
        print()
        print(f"Sport:    {args.sport.upper()}")
        print(f"Duration: {args.duration} minutes")

        if args.game_id:
            print(f"Game ID:  {args.game_id}")

        if settings:
            sharp_books = settings.skills.market_analysis.sharp_books
            public_books = settings.skills.market_analysis.public_books
            threshold = settings.skills.market_analysis.alert_threshold

            print(f"\nSharp Books:  {', '.join(sharp_books)}")
            print(f"Public Books: {', '.join(public_books)}")
            print(f"Alert Threshold: {threshold} points")

        print()
        print("Press Ctrl+C to stop monitoring")
        print("=" * 80)
        print()

        async def start_monitoring():
            monitor = MarketMonitor()

            try:
                if args.game_id:
                    await monitor.monitor_game(
                        game_id=args.game_id,
                        sport=sport_key,
                        duration_minutes=args.duration
                    )
                else:
                    await monitor.monitor_sport(
                        sport=sport_key,
                        duration_minutes=args.duration,
                        check_interval=args.interval
                    )

                # Print summary
                summary = monitor.get_alert_summary()
                print("\n" + "=" * 80)
                print("📊 MONITORING SUMMARY")
                print("=" * 80)
                print(f"Total Alerts: {summary.get('total_alerts', 0)}")

                avg_conf = summary.get('avg_confidence', 0)
                if avg_conf > 0:
                    print(f"Average Confidence: {avg_conf:.1f}%")

                top_games = summary.get('most_alerted_games', [])
                if top_games:
                    print("\nMost Active Games:")
                    for game in top_games:
                        print(f"  • {game['matchup']}: {game['alert_count']} alerts")

                print()

            except KeyboardInterrupt:
                print("\n\n🛑 Monitoring stopped by user")

                # Print summary even if interrupted
                summary = monitor.get_alert_summary()
                if summary.get('total_alerts', 0) > 0:
                    print(f"\n📊 Captured {summary['total_alerts']} alerts before stopping")

        asyncio.run(start_monitoring())
        sys.exit(0)
    
    elif args.cmd == "scrape-ai":
        import asyncio
        from walters_analyzer.ingest.scrape_with_ai import MCPChromeDevToolsScraper
        
        async def run_ai_scraping():
            print("=" * 80)
            print("AI-ASSISTED ODDS SCRAPING")
            print("=" * 80)
            print()
            print(f"Sport: {args.sport.upper()}")
            print(f"Output: {args.output_dir}")
            print()
            print("Features:")
            print("  • Performance monitoring with AI insights")
            print("  • Network request analysis")
            print("  • Automatic debugging recommendations")
            print("  • Bottleneck detection")
            print()
            print("=" * 80)
            print()
            
            scraper = MCPChromeDevToolsScraper(output_dir=args.output_dir)
            result = await scraper.scrape_overtime_odds(
                sport=args.sport,
                save_ai_report=not args.no_ai_report
            )
            
            # Print summary
            print()
            print("=" * 80)
            print("SCRAPING RESULTS")
            print("=" * 80)
            print(f"Games extracted: {len(result['games'])}")
            print(f"Timestamp: {result['timestamp']}")
            
            if result.get('ai_insights'):
                insights = result['ai_insights']
                perf_score = insights.get('performance_analysis', {}).get('performance_score', 0)
                print(f"\nPerformance Score: {perf_score}/100")
                
                if perf_score < 70:
                    print("  [WARNING] Low performance score - review AI recommendations")
                elif perf_score < 85:
                    print("  [INFO] Good performance - minor optimizations available")
                else:
                    print("  [OK] Excellent performance")
                
                print(f"\nExtraction: {'SUCCESS' if insights.get('extraction_success') else 'FAILED'}")
                
                recommendations = insights.get('recommendations', [])
                if recommendations:
                    print(f"\nAI Recommendations ({len(recommendations)}):")
                    for rec in recommendations:
                        print(f"  • {rec.get('type')}: {rec.get('benefit')}")
                
                # Show debugging info if extraction failed
                if not insights.get('extraction_success'):
                    debug_info = insights.get('debugging_info', {})
                    if debug_info.get('potential_causes'):
                        print(f"\nPotential Issues:")
                        for cause in debug_info['potential_causes']:
                            print(f"  • {cause.get('cause')} (likelihood: {cause.get('likelihood')})")
                    
                    if debug_info.get('recommendations'):
                        print(f"\nSuggested Fixes:")
                        for rec in debug_info['recommendations']:
                            print(f"  • {rec}")
            
            # Session report
            session_report = scraper.get_session_report()
            print(f"\nSession Stats:")
            print(f"  Success Rate: {session_report['summary']['success_rate']}")
            print(f"  Avg Performance: {session_report['summary']['avg_performance_score']:.1f}/100")
            
            if session_report['summary']['common_issues']:
                print(f"  Common Issues: {', '.join(session_report['summary']['common_issues'][:3])}")
            
            print()
            
            return 0 if len(result['games']) > 0 else 1
        
        exit_code = asyncio.run(run_ai_scraping())
        sys.exit(exit_code)
    
    elif args.cmd == "interactive":
        import asyncio
        from walters_analyzer.slash_commands import SlashCommandHandler, interactive_mode
        
        handler = SlashCommandHandler(bankroll=args.bankroll)
        asyncio.run(interactive_mode(handler))
        sys.exit(0)
    
    elif args.cmd == "slash":
        import asyncio
        import json
        from walters_analyzer.slash_commands import SlashCommandHandler
        
        async def run_slash_command():
            handler = SlashCommandHandler(bankroll=args.bankroll)
            result = await handler.execute(args.command)
            
            # Pretty print result
            print(json.dumps(result, indent=2, default=str))
            
            return 0 if result.get('status') == 'success' else 1
        
        exit_code = asyncio.run(run_slash_command())
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
