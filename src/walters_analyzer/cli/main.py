"""
Billy Walters Sports Analyzer - Main CLI Application

This is the new unified CLI using Typer for cleaner subcommand handling.
The old argparse-based cli.py is preserved for backward compatibility.

Usage:
    walters analyze edges --sport nfl --week 13
    walters scrape overtime --sport nfl
    walters clv record --game "DET vs CHI" --line -3.5
    walters status
    walters power-ratings update --week 13
"""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel

# Import command groups
from .commands import analyze, scrape, clv, power_ratings, db, monitor

# Create main app
app = typer.Typer(
    name="walters",
    help="Billy Walters Sports Analyzer - Professional betting analysis system",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
    add_completion=True,
)

console = Console()

# Register command groups
app.add_typer(analyze.app, name="analyze", help="Analyze games, edges, injuries, weather")
app.add_typer(scrape.app, name="scrape", help="Scrape data from various sources")
app.add_typer(clv.app, name="clv", help="Closing Line Value tracking")
app.add_typer(power_ratings.app, name="power-ratings", help="Power ratings management")
app.add_typer(db.app, name="db", help="Database operations")
app.add_typer(monitor.app, name="monitor", help="Line movement monitoring")


@app.command()
def status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status"),
    check_data: bool = typer.Option(True, "--check-data/--no-check-data", help="Check data freshness"),
):
    """
    Check system health and data freshness.
    
    Shows status of:
    - Data sources (freshness, last update)
    - Database connection
    - API keys configured
    - Current week/season context
    """
    from .commands.status import run_status_check
    run_status_check(verbose=verbose, check_data=check_data)


@app.command()
def version():
    """Show version information."""
    from walters_analyzer import __version__
    
    console.print(Panel(
        f"[bold blue]Billy Walters Sports Analyzer[/bold blue]\n"
        f"Version: [green]{__version__}[/green]\n\n"
        f"[dim]Professional betting analysis system implementing\n"
        f"Billy Walters methodology for edge detection.[/dim]",
        title="walters-analyzer",
        border_style="blue",
    ))


@app.command()
def quickstart(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    week: Optional[int] = typer.Option(None, "--week", "-w", help="Week number (auto-detect if not specified)"),
):
    """
    Quick start workflow for weekly analysis.
    
    This command runs the standard weekly workflow:
    1. Check system status
    2. Scrape latest odds
    3. Update power ratings
    4. Find betting edges
    5. Generate recommendations
    """
    from .commands.quickstart import run_quickstart
    run_quickstart(sport=sport, week=week)


@app.callback()
def main_callback(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """
    Billy Walters Sports Analyzer - Professional betting analysis.
    
    A mathematics-based sports betting system implementing Billy Walters'
    proven methodology. Focuses on edge detection, risk management, and
    disciplined bankroll management.
    
    [bold]Core Principles:[/bold]
    • Minimum 5.5% edge required for any bet
    • Maximum 3% of bankroll on single bet  
    • Track Closing Line Value (CLV) as primary metric
    • Process over results - need 100+ bets for validity
    
    [bold]Quick Start:[/bold]
        walters quickstart --sport nfl --week 13
    
    [bold]Common Commands:[/bold]
        walters analyze edges --sport nfl
        walters scrape overtime --sport nfl
        walters clv record --game "DET vs CHI"
        walters status --verbose
    """
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        console.print("[yellow]Debug mode enabled[/yellow]")
    
    # Store debug flag in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
