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
    
    weather = sub.add_parser("scrape-weather", help="Fetch weather data from AccuWeather API")
    weather.add_argument("--card", type=str, 
                        help="Path to wk-card JSON to fetch weather for all games")
    weather.add_argument("--stadium", type=str,
                        help="Stadium name (use with --location)")
    weather.add_argument("--location", type=str,
                        help="City/location for weather search")
    weather.add_argument("--dome", action="store_true",
                        help="Stadium is indoor (weather irrelevant)")
    weather.add_argument("--sport", choices=["nfl", "cfb"], default="cfb",
                        help="Sport type")
    weather.add_argument("--output-dir", default="data/weather",
                        help="Output directory for weather data")
    
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
    
    elif args.cmd == "scrape-weather":
        from walters_analyzer.weather_fetcher import fetch_game_weather
        from walters_analyzer.weather_pipeline import WeatherDataPipeline
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        pipeline = WeatherDataPipeline(output_dir=args.output_dir)
        
        # Determine sport format
        sport = "college_football" if args.sport == "cfb" else "nfl"
        
        if args.card:
            # Fetch weather for all games in a card
            card_path = pathlib.Path(args.card)
            if not card_path.exists():
                console.print(f"[red]ERROR: Card not found: {card_path}[/red]")
                sys.exit(2)
            
            card = load_card(card_path)
            console.print(f"[cyan]Fetching weather for {len(card.get('games', []))} games from card...[/cyan]")
            
            for game in card.get("games", []):
                stadium = game.get("stadium", "Unknown")
                matchup = game.get("matchup", "Unknown")
                is_dome = game.get("dome", False)
                
                console.print(f"\n[yellow]→[/yellow] {matchup} @ {stadium}")
                
                if is_dome:
                    console.print("  [dim]Indoor stadium - weather irrelevant[/dim]")
                
                # Extract location from stadium or matchup
                # Simple heuristic: use stadium name for search
                location = stadium
                
                weather_data = fetch_game_weather(
                    stadium=stadium,
                    location=location,
                    is_dome=is_dome,
                    game_date=card.get("date"),
                    game_time=game.get("kickoff_et"),
                    sport=sport,
                    use_cache=True
                )
                
                if weather_data:
                    pipeline.add_item(weather_data)
                    
                    # Display summary
                    impact = weather_data.get("weather_impact_score", 0)
                    temp = weather_data.get("temperature_f")
                    wind = weather_data.get("wind_speed_mph")
                    precip = weather_data.get("precipitation_prob")
                    adjustment = weather_data.get("betting_adjustment", "N/A")
                    
                    impact_color = "green" if impact < 20 else "yellow" if impact < 50 else "red"
                    
                    console.print(f"  [bold]Weather:[/bold] {weather_data.get('weather_description')}")
                    console.print(f"  Temp: {temp}°F | Wind: {wind} mph | Precip: {precip}%")
                    console.print(f"  [{impact_color}]Impact Score: {impact}[/{impact_color}] | {adjustment}")
                else:
                    console.print("  [red]Failed to fetch weather data[/red]")
        
        elif args.stadium and args.location:
            # Fetch weather for a single game/location
            console.print(f"[cyan]Fetching weather for {args.stadium}...[/cyan]")
            
            weather_data = fetch_game_weather(
                stadium=args.stadium,
                location=args.location,
                is_dome=args.dome,
                sport=sport,
                use_cache=True
            )
            
            if weather_data:
                pipeline.add_item(weather_data)
                
                # Display detailed report
                table = Table(title=f"Weather Report: {args.stadium}")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Location", weather_data.get("location", "N/A"))
                table.add_row("Conditions", weather_data.get("weather_description", "N/A"))
                table.add_row("Temperature", f"{weather_data.get('temperature_f')}°F")
                table.add_row("Feels Like", f"{weather_data.get('feels_like_f')}°F")
                table.add_row("Wind Speed", f"{weather_data.get('wind_speed_mph')} mph")
                table.add_row("Wind Gusts", f"{weather_data.get('wind_gust_mph')} mph")
                table.add_row("Precipitation", f"{weather_data.get('precipitation_prob')}%")
                table.add_row("Precip Type", weather_data.get("precipitation_type", "None"))
                
                impact = weather_data.get("weather_impact_score", 0)
                impact_str = f"{impact}/100"
                if impact > 75:
                    impact_str += " (EXTREME)"
                elif impact > 50:
                    impact_str += " (HIGH)"
                elif impact > 20:
                    impact_str += " (MODERATE)"
                else:
                    impact_str += " (LOW)"
                
                table.add_row("Impact Score", impact_str)
                table.add_row("Betting Adjustment", weather_data.get("betting_adjustment", "N/A"))
                
                console.print(table)
            else:
                console.print("[red]Failed to fetch weather data[/red]")
                sys.exit(1)
        else:
            console.print("[red]ERROR: Must provide either --card or both --stadium and --location[/red]")
            parser.print_help()
            sys.exit(2)
        
        # Write output files
        if pipeline.buffer:
            try:
                jsonl_path, parquet_path = pipeline.write_files()
                console.print(f"\n[green]✓ Weather data written:[/green]")
                console.print(f"  - JSONL: {jsonl_path}")
                console.print(f"  - Parquet: {parquet_path}")
            except Exception as e:
                console.print(f"[red]ERROR writing output files: {e}[/red]")
                sys.exit(1)
        else:
            console.print("[yellow]No weather data to write[/yellow]")

if __name__ == "__main__":
    main()
