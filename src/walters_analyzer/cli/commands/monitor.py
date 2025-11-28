"""
Monitor Commands - Line movement and market monitoring.

Commands:
    walters monitor start    - Start continuous line monitoring
    walters monitor alerts   - View recent alerts
    walters monitor game     - Monitor specific game
"""

import typer
from typing import Optional
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    help="Line movement and market monitoring",
    no_args_is_help=True,
)

console = Console()


@app.command("start")
def monitor_start(
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    interval: int = typer.Option(
        60, "--interval", "-i", help="Check interval in seconds"
    ),
    duration: int = typer.Option(
        120, "--duration", "-d", help="Duration in minutes (0 = indefinite)"
    ),
    alert_threshold: float = typer.Option(
        0.5, "--threshold", "-t", help="Alert threshold in points"
    ),
    sms: bool = typer.Option(False, "--sms", help="Enable SMS alerts"),
):
    """
    Start continuous line monitoring.

    Monitors for:
    - Line movements exceeding threshold
    - Steam moves (rapid line changes)
    - Sharp book vs public book divergence
    - Reverse line movement

    Example:
        walters monitor start --sport nfl --interval 30
        walters monitor start --sport nfl --sms --threshold 1.0
    """
    console.print(
        Panel(
            f"[bold]Line Monitor[/bold]\n\n"
            f"Sport: {sport.upper()}\n"
            f"Interval: {interval}s\n"
            f"Duration: {duration}min {'(indefinite)' if duration == 0 else ''}\n"
            f"Alert Threshold: {alert_threshold} pts\n"
            f"SMS Alerts: {'Enabled' if sms else 'Disabled'}",
            title="📡 Starting Monitor",
            border_style="green",
        )
    )

    console.print("\n[yellow]Press Ctrl+C to stop monitoring[/yellow]\n")

    # TODO: Implement continuous monitoring
    # This would use the existing continuous_scraper.py logic

    try:
        import time

        check_count = 0
        start_time = datetime.now()

        while True:
            check_count += 1
            elapsed = (datetime.now() - start_time).total_seconds() / 60

            console.print(
                f"[dim][{datetime.now().strftime('%H:%M:%S')}] Check #{check_count} - {elapsed:.1f}min elapsed[/dim]"
            )

            # TODO: Actual line checking logic
            # For now, just simulate

            if duration > 0 and elapsed >= duration:
                console.print(
                    f"\n[green]Duration reached ({duration}min). Stopping.[/green]"
                )
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        console.print(
            f"\n[yellow]Monitoring stopped after {check_count} checks[/yellow]"
        )


@app.command("alerts")
def monitor_alerts(
    sport: Optional[str] = typer.Option(None, "--sport", "-s", help="Filter by sport"),
    hours: int = typer.Option(24, "--hours", "-h", help="Hours to look back"),
    min_movement: float = typer.Option(0.0, "--min", help="Minimum movement to show"),
):
    """
    View recent line movement alerts.

    Example:
        walters monitor alerts --sport nfl --hours 12
        walters monitor alerts --min 1.0
    """
    console.print(
        Panel(
            f"[bold]Recent Alerts[/bold]\nLast {hours} hours",
            title="🚨 Line Movement Alerts",
            border_style="yellow",
        )
    )

    # TODO: Load alerts from storage
    table = Table(title="Line Movements")
    table.add_column("Time", style="dim")
    table.add_column("Game", style="cyan")
    table.add_column("Type")
    table.add_column("Movement", justify="right")
    table.add_column("Details")

    # Placeholder
    table.add_row(
        "14:32",
        "DET @ CHI",
        "[yellow]STEAM[/yellow]",
        "[red]-1.5[/red]",
        "DET -6.5 → -5.0",
    )

    console.print(table)
    console.print("\n[yellow]Full implementation in progress...[/yellow]")


@app.command("game")
def monitor_game(
    game: str = typer.Argument(..., help="Game to monitor (e.g., 'DET @ CHI')"),
    interval: int = typer.Option(
        30, "--interval", "-i", help="Check interval in seconds"
    ),
):
    """
    Monitor a specific game for line changes.

    Example:
        walters monitor game "DET @ CHI" --interval 30
    """
    console.print(
        Panel(
            f"[bold]Monitoring: {game}[/bold]\nInterval: {interval}s",
            title="🎯 Single Game Monitor",
            border_style="cyan",
        )
    )

    console.print("\n[yellow]Press Ctrl+C to stop[/yellow]\n")

    # TODO: Implement single-game monitoring
    console.print("[yellow]Implementation in progress...[/yellow]")


@app.command("config")
def monitor_config(
    show: bool = typer.Option(True, "--show/--edit", help="Show or edit config"),
):
    """
    View or edit monitoring configuration.

    Configuration includes:
    - Sharp books list
    - Public books list
    - Alert thresholds
    - SMS settings
    """
    console.print(
        Panel(
            "[bold]Monitor Configuration[/bold]",
            title="⚙️ Settings",
            border_style="blue",
        )
    )

    try:
        from walters_analyzer.config import get_settings

        settings = get_settings()

        ma = settings.skills.market_analysis

        console.print(f"\n[bold]Sharp Books:[/bold]")
        for book in ma.sharp_books:
            console.print(f"  • {book}")

        console.print(f"\n[bold]Public Books:[/bold]")
        for book in ma.public_books:
            console.print(f"  • {book}")

        console.print(f"\n[bold]Thresholds:[/bold]")
        console.print(f"  Alert: {ma.alert_threshold} points")
        console.print(
            f"  Steam: {ma.steam_move_threshold} points in {ma.steam_move_window}s"
        )

    except Exception as e:
        console.print(f"[yellow]Could not load settings: {e}[/yellow]")
        console.print("[dim]Using defaults[/dim]")


if __name__ == "__main__":
    app()
