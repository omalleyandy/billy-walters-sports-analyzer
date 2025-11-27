"""
Scrape Commands - Data collection from various sources.

Commands:
    walters scrape overtime       - Scrape Overtime.ag odds
    walters scrape espn           - Scrape ESPN data
    walters scrape massey         - Scrape Massey ratings
    walters scrape action-network - Scrape Action Network signals
    walters scrape all            - Run all scrapers
"""

import typer
from typing import Optional
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

app = typer.Typer(
    help="Scrape data from various sources",
    no_args_is_help=True,
)

console = Console()


@app.command("overtime")
def scrape_overtime(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl, ncaaf, or all"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser headless"),
    use_proxy: bool = typer.Option(False, "--proxy/--no-proxy", help="Use proxy from environment"),
    format: str = typer.Option("json", "--format", "-f", help="Output format: json, csv, table"),
):
    """
    Scrape odds from Overtime.ag using Playwright.
    
    This uses the overtime_ag_client package for reliable scraping
    with CloudFlare bypass.
    
    Example:
        walters scrape overtime --sport nfl --format table
    """
    console.print(Panel(
        f"[bold]Overtime.ag Scraper[/bold]\n"
        f"Sport: {sport.upper()} | Headless: {headless} | Proxy: {use_proxy}",
        title="🎰 Scraping Odds",
        border_style="green",
    ))
    
    import asyncio
    import os
    
    async def run_scrape():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing browser...", total=None)
            
            try:
                # Try to import the overtime_ag_client
                from overtime_ag_client import OvertimeClient
                
                progress.update(task, description="Starting browser...")
                
                # Only use proxy if explicitly requested
                proxy = None
                if use_proxy:
                    proxy = os.environ.get("OVERTIME_PROXY") or os.environ.get("PROXY_URL")
                    if proxy:
                        console.print(f"[dim]Using proxy: {proxy[:40]}...[/dim]")
                
                async with OvertimeClient(headless=headless, proxy=proxy) as client:
                    progress.update(task, description="Logging in to Overtime.ag...")
                    await client.login()
                    
                    if sport.lower() == "all":
                        # Scrape both
                        progress.update(task, description="Scraping NFL...")
                        nfl_data = await client.get_nfl_odds()
                        
                        progress.update(task, description="Scraping NCAAF...")
                        ncaaf_data = await client.get_ncaaf_odds()
                        
                        all_games = nfl_data.games + ncaaf_data.games
                    elif sport.lower() == "nfl":
                        progress.update(task, description="Scraping NFL...")
                        scoreboard = await client.get_nfl_odds()
                        all_games = scoreboard.games
                    else:
                        progress.update(task, description="Scraping NCAAF...")
                        scoreboard = await client.get_ncaaf_odds()
                        all_games = scoreboard.games
                    
                    progress.update(task, description=f"[green]✓ Scraped {len(all_games)} games[/green]")
                    
                    return all_games
                    
            except ImportError:
                progress.update(task, description="[yellow]overtime_ag_client not installed[/yellow]")
                console.print("\n[red]Error:[/red] overtime_ag_client package not found")
                console.print("[dim]Install with: uv add ../overtime_ag_client[/dim]")
                return []
            except Exception as e:
                progress.update(task, description=f"[red]Error: {e}[/red]")
                import traceback
                console.print(f"\n[red]Error details:[/red] {traceback.format_exc()}")
                return []
    
    games = asyncio.run(run_scrape())
    
    if not games:
        console.print("[yellow]No games scraped. Check connection and try again.[/yellow]")
        return
    
    # Display results based on format
    if format == "table":
        table = Table(title=f"Overtime.ag Odds - {sport.upper()}")
        table.add_column("Game", style="cyan")
        table.add_column("Spread", justify="right")
        table.add_column("Total", justify="right")
        table.add_column("ML Away", justify="right")
        table.add_column("ML Home", justify="right")
        
        for game in games:
            # Extract odds from game object
            spread = game.odds.spread if game.odds else "N/A"
            total = game.odds.total if game.odds else "N/A"
            ml_away = game.odds.away_ml if game.odds else "N/A"
            ml_home = game.odds.home_ml if game.odds else "N/A"
            
            table.add_row(
                f"{game.away_team} @ {game.home_team}",
                str(spread),
                str(total),
                str(ml_away),
                str(ml_home),
            )
        
        console.print(table)
    
    elif format == "json":
        import json
        output_path = output_dir or Path(f"data/odds/{sport}")
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_path / f"overtime_{sport}_{timestamp}.json"
        
        # Convert games to dict
        games_data = [g.to_dict() if hasattr(g, 'to_dict') else str(g) for g in games]
        
        with open(filename, 'w') as f:
            json.dump(games_data, f, indent=2, default=str)
        
        console.print(f"[green]Saved to {filename}[/green]")
    
    console.print(f"\n[bold]Total games scraped: {len(games)}[/bold]")


@app.command("espn")
def scrape_espn(
    data_type: str = typer.Argument(..., help="Data type: injuries, schedule, stats, standings"),
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    team: Optional[str] = typer.Option(None, "--team", "-t", help="Specific team"),
    week: Optional[int] = typer.Option(None, "--week", "-w", help="Week number"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """
    Scrape data from ESPN API.
    
    Data types:
    - injuries: Current injury reports
    - schedule: Game schedules
    - stats: Team/player statistics
    - standings: Current standings
    
    Example:
        walters scrape espn injuries --sport nfl
        walters scrape espn schedule --sport nfl --week 13
    """
    console.print(Panel(
        f"[bold]ESPN {data_type.title()} Scraper[/bold]\n"
        f"Sport: {sport.upper()}",
        title="📊 ESPN Data",
        border_style="blue",
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Fetching {data_type}...", total=None)
        
        try:
            if data_type == "injuries":
                from walters_analyzer.feeds.espn_client import ESPNClient
                # TODO: Implement injury fetching
                progress.update(task, description="[yellow]Implementation in progress[/yellow]")
                
            elif data_type == "schedule":
                # TODO: Implement schedule fetching
                progress.update(task, description="[yellow]Implementation in progress[/yellow]")
                
            elif data_type == "stats":
                # TODO: Implement stats fetching
                progress.update(task, description="[yellow]Implementation in progress[/yellow]")
                
            elif data_type == "standings":
                # TODO: Implement standings fetching
                progress.update(task, description="[yellow]Implementation in progress[/yellow]")
            
            else:
                console.print(f"[red]Unknown data type: {data_type}[/red]")
                console.print("[dim]Valid types: injuries, schedule, stats, standings[/dim]")
                raise typer.Exit(1)
                
        except ImportError as e:
            progress.update(task, description=f"[red]Missing dependency: {e}[/red]")


@app.command("massey")
def scrape_massey(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    save_to_db: bool = typer.Option(False, "--save-db", help="Save to database"),
):
    """
    Scrape power ratings from Massey Ratings.
    
    Massey provides composite ratings from multiple computer systems,
    which we use as a baseline for our power rating calculations.
    
    Example:
        walters scrape massey --sport nfl --save-db
    """
    console.print(Panel(
        f"[bold]Massey Ratings Scraper[/bold]\n"
        f"Sport: {sport.upper()}",
        title="📈 Power Ratings",
        border_style="cyan",
    ))
    
    # TODO: Implement Massey scraping
    console.print("[yellow]Implementation in progress...[/yellow]")
    console.print("[dim]Will scrape composite power ratings from masseyratings.com[/dim]")


@app.command("action-network")
def scrape_action_network(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser headless"),
):
    """
    Scrape sharp signals from Action Network.
    
    Collects:
    - Money percentages
    - Ticket percentages  
    - Line movement history
    - Sharp vs public splits
    
    Example:
        walters scrape action-network --sport nfl
    """
    console.print(Panel(
        f"[bold]Action Network Scraper[/bold]\n"
        f"Sport: {sport.upper()}",
        title="💰 Sharp Signals",
        border_style="magenta",
    ))
    
    # TODO: Implement Action Network scraping
    console.print("[yellow]Implementation in progress...[/yellow]")
    console.print("[dim]Will scrape money%/ticket% divergence data[/dim]")


@app.command("all")
def scrape_all(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Base output directory"),
    parallel: bool = typer.Option(False, "--parallel", "-p", help="Run scrapers in parallel"),
):
    """
    Run all scrapers for comprehensive data collection.
    
    Runs in sequence (or parallel with --parallel):
    1. Overtime.ag odds
    2. ESPN injuries/schedule
    3. Massey ratings
    4. Action Network signals (if credentials available)
    
    Example:
        walters scrape all --sport nfl --parallel
    """
    console.print(Panel(
        f"[bold]Full Data Collection[/bold]\n"
        f"Sport: {sport.upper()} | Parallel: {parallel}",
        title="🚀 Scrape All Sources",
        border_style="green",
    ))
    
    scrapers = [
        ("Overtime.ag", "odds"),
        ("ESPN Injuries", "injuries"),
        ("ESPN Schedule", "schedule"),
        ("Massey Ratings", "power ratings"),
        ("Action Network", "sharp signals"),
    ]
    
    table = Table(title="Scraper Status")
    table.add_column("Source", style="cyan")
    table.add_column("Data Type")
    table.add_column("Status", justify="center")
    table.add_column("Records")
    
    for source, data_type in scrapers:
        # TODO: Actually run each scraper
        table.add_row(source, data_type, "[yellow]Pending[/yellow]", "-")
    
    console.print(table)
    console.print("\n[yellow]Full implementation in progress...[/yellow]")


if __name__ == "__main__":
    app()
