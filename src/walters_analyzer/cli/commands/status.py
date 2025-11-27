"""
Status Command - System health and data freshness checks.

Commands:
    walters status          - Quick status check
    walters status --verbose - Detailed status with all checks
"""

import typer
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(
    help="System health and data freshness checks",
)

console = Console()


def run_status_check(verbose: bool = False, check_data: bool = True):
    """Run comprehensive status check."""
    
    console.print(Panel(
        "[bold]Billy Walters System Status[/bold]",
        title="🔍 Health Check",
        border_style="blue",
    ))
    
    checks = []
    
    # 1. Check configuration
    console.print("\n[bold]Configuration:[/bold]")
    try:
        from walters_analyzer.config import get_settings
        settings = get_settings()
        console.print("  [green]✓[/green] Settings loaded")
        checks.append(("Configuration", True))
        
        if verbose:
            console.print(f"    Project root: {settings.project_root}")
            console.print(f"    Data directory: {settings.data_dir}")
    except Exception as e:
        console.print(f"  [red]✗[/red] Settings failed: {e}")
        checks.append(("Configuration", False))
    
    # 2. Check database connection
    console.print("\n[bold]Database:[/bold]")
    try:
        import psycopg2
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        db_url = os.getenv("DATABASE_URL")
        
        if db_url:
            # Try to connect
            conn = psycopg2.connect(db_url)
            conn.close()
            console.print("  [green]✓[/green] PostgreSQL connected")
            checks.append(("Database", True))
        else:
            console.print("  [yellow]○[/yellow] DATABASE_URL not configured")
            checks.append(("Database", None))
    except ImportError:
        console.print("  [yellow]○[/yellow] psycopg2 not installed")
        checks.append(("Database", None))
    except Exception as e:
        console.print(f"  [red]✗[/red] Database error: {e}")
        checks.append(("Database", False))
    
    # 3. Check API keys
    console.print("\n[bold]API Keys:[/bold]")
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    api_keys = [
        ("ANTHROPIC_API_KEY", "Anthropic"),
        ("OPENWEATHER_API_KEY", "OpenWeather"),
        ("ODDS_API_KEY", "The Odds API"),
        ("HIGHLIGHTLY_API_KEY", "Highlightly"),
        ("FIRECRAWL_API_KEY", "Firecrawl"),
    ]
    
    for env_var, name in api_keys:
        value = os.getenv(env_var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            console.print(f"  [green]✓[/green] {name}: {masked}")
        else:
            console.print(f"  [yellow]○[/yellow] {name}: not configured")
    
    # 4. Check data freshness
    if check_data:
        console.print("\n[bold]Data Freshness:[/bold]")
        
        data_paths = [
            ("data/odds/nfl", "NFL Odds"),
            ("data/odds/ncaaf", "NCAAF Odds"),
            ("data/injuries/nfl", "NFL Injuries"),
            ("data/power_ratings", "Power Ratings"),
            ("data/clv/bets.json", "CLV Tracking"),
        ]
        
        for path_str, name in data_paths:
            path = Path(path_str)
            if path.exists():
                if path.is_file():
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                else:
                    # Get most recent file in directory
                    files = list(path.glob("*.*"))
                    if files:
                        mtime = max(datetime.fromtimestamp(f.stat().st_mtime) for f in files)
                    else:
                        console.print(f"  [yellow]○[/yellow] {name}: empty directory")
                        continue
                
                age = datetime.now() - mtime
                age_str = format_age(age)
                
                if age < timedelta(hours=24):
                    console.print(f"  [green]✓[/green] {name}: {age_str} ago")
                    checks.append((name, True))
                elif age < timedelta(days=7):
                    console.print(f"  [yellow]○[/yellow] {name}: {age_str} ago (stale)")
                    checks.append((name, None))
                else:
                    console.print(f"  [red]✗[/red] {name}: {age_str} ago (very stale)")
                    checks.append((name, False))
            else:
                console.print(f"  [dim]○[/dim] {name}: not found")
    
    # 5. Check current week/season context
    console.print("\n[bold]Season Context:[/bold]")
    try:
        from walters_analyzer.utils.nfl_calendar import get_current_week
        week_info = get_current_week()
        console.print(f"  Current Week: {week_info.get('week', 'Unknown')}")
        console.print(f"  Season: {week_info.get('season', 'Unknown')}")
    except ImportError:
        # Manual calculation
        today = datetime.now()
        # NFL regular season typically starts first Thursday after Labor Day
        # Rough estimate for 2024/2025 season
        if today.month >= 9 or today.month <= 2:
            season = today.year if today.month >= 9 else today.year - 1
            console.print(f"  Season: {season} (estimated)")
        else:
            console.print("  [dim]Off-season[/dim]")
    
    # Summary
    console.print("\n" + "=" * 50)
    passed = sum(1 for _, status in checks if status is True)
    failed = sum(1 for _, status in checks if status is False)
    skipped = sum(1 for _, status in checks if status is None)
    
    if failed == 0:
        console.print(f"[green]✓ All checks passed ({passed} ok, {skipped} skipped)[/green]")
    else:
        console.print(f"[red]✗ {failed} checks failed[/red] ({passed} ok, {skipped} skipped)")
    
    # Recommendations
    if verbose:
        console.print("\n[bold]Recommendations:[/bold]")
        
        # Check for stale data
        stale_checks = [name for name, status in checks if status is None]
        if stale_checks:
            console.print(f"  [yellow]→[/yellow] Update stale data: {', '.join(stale_checks)}")
            console.print("    Run: walters scrape all --sport nfl")
        
        failed_checks = [name for name, status in checks if status is False]
        if failed_checks:
            console.print(f"  [red]→[/red] Fix failures: {', '.join(failed_checks)}")


def format_age(delta: timedelta) -> str:
    """Format a timedelta as human-readable age."""
    if delta < timedelta(minutes=1):
        return "just now"
    elif delta < timedelta(hours=1):
        mins = int(delta.total_seconds() / 60)
        return f"{mins}m"
    elif delta < timedelta(days=1):
        hours = int(delta.total_seconds() / 3600)
        return f"{hours}h"
    elif delta < timedelta(days=7):
        days = delta.days
        return f"{days}d"
    else:
        weeks = delta.days // 7
        return f"{weeks}w"


@app.callback(invoke_without_command=True)
def status_default(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status"),
    check_data: bool = typer.Option(True, "--check-data/--no-check-data", help="Check data freshness"),
):
    """
    Check system health and data freshness.
    
    Example:
        walters status
        walters status --verbose
    """
    if ctx.invoked_subcommand is None:
        run_status_check(verbose=verbose, check_data=check_data)


if __name__ == "__main__":
    app()
