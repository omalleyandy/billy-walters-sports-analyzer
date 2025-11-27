"""
Database Commands - Database operations and maintenance.

Commands:
    walters db migrate  - Run database migrations
    walters db backup   - Backup database
    walters db load     - Load data files into database
    walters db query    - Run ad-hoc queries
    walters db status   - Check database status
"""

import typer
from typing import Optional
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    help="Database operations and maintenance",
    no_args_is_help=True,
)

console = Console()


@app.command("migrate")
def db_migrate(
    direction: str = typer.Argument("up", help="Migration direction: up or down"),
    steps: int = typer.Option(1, "--steps", "-n", help="Number of migrations to run"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show SQL without executing"),
):
    """
    Run database migrations.
    
    Example:
        walters db migrate up
        walters db migrate down --steps 1
        walters db migrate up --dry-run
    """
    console.print(Panel(
        f"[bold]Database Migration[/bold]\n"
        f"Direction: {direction.upper()}\n"
        f"Steps: {steps}",
        title="🔄 Migration",
        border_style="blue",
    ))
    
    # TODO: Implement migration
    console.print("[yellow]Implementation in progress...[/yellow]")
    console.print("[dim]Will run Alembic migrations[/dim]")


@app.command("backup")
def db_backup(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    compress: bool = typer.Option(True, "--compress/--no-compress", help="Compress backup"),
):
    """
    Backup database to file.
    
    Creates a pg_dump of the database with optional compression.
    
    Example:
        walters db backup
        walters db backup --output backups/pre-update.sql
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_path = Path(f"backups/walters_db_{timestamp}.sql")
    if compress:
        default_path = default_path.with_suffix(".sql.gz")
    
    output_path = output or default_path
    
    console.print(Panel(
        f"[bold]Database Backup[/bold]\n"
        f"Output: {output_path}\n"
        f"Compress: {compress}",
        title="💾 Backup",
        border_style="green",
    ))
    
    # TODO: Implement backup using pg_dump
    console.print("[yellow]Implementation in progress...[/yellow]")


@app.command("load")
def db_load(
    data_type: str = typer.Argument(..., help="Data type: odds, injuries, ratings, schedules"),
    source: Path = typer.Argument(..., help="Source file or directory"),
    sport: str = typer.Option("nfl", "--sport", "-s", help="Sport: nfl or ncaaf"),
    replace: bool = typer.Option(False, "--replace", help="Replace existing data"),
):
    """
    Load data files into database.
    
    Supports loading:
    - odds: JSON/CSV odds files
    - injuries: Injury report files  
    - ratings: Power rating files
    - schedules: Schedule files
    
    Example:
        walters db load odds data/odds/nfl/ --sport nfl
        walters db load injuries data/injuries/nfl/latest.json
    """
    console.print(Panel(
        f"[bold]Load Data[/bold]\n"
        f"Type: {data_type}\n"
        f"Source: {source}\n"
        f"Sport: {sport.upper()}\n"
        f"Replace: {replace}",
        title="📥 Data Import",
        border_style="cyan",
    ))
    
    if not source.exists():
        console.print(f"[red]Error: Source not found: {source}[/red]")
        raise typer.Exit(1)
    
    # TODO: Implement data loading
    console.print("[yellow]Implementation in progress...[/yellow]")


@app.command("query")
def db_query(
    sql: str = typer.Argument(..., help="SQL query to execute"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output to CSV file"),
    limit: int = typer.Option(100, "--limit", "-l", help="Row limit for display"),
):
    """
    Run ad-hoc SQL query.
    
    Example:
        walters db query "SELECT * FROM games WHERE week = 13"
        walters db query "SELECT team, rating FROM power_ratings ORDER BY rating DESC" --output ratings.csv
    """
    console.print(f"[dim]Executing: {sql[:80]}{'...' if len(sql) > 80 else ''}[/dim]\n")
    
    # TODO: Implement query execution
    console.print("[yellow]Implementation in progress...[/yellow]")


@app.command("status")
def db_status():
    """
    Check database connection and table status.
    
    Shows:
    - Connection status
    - Table counts
    - Last update timestamps
    - Database size
    """
    console.print(Panel(
        "[bold]Database Status[/bold]",
        title="🔍 DB Check",
        border_style="blue",
    ))
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        db_url = os.getenv("DATABASE_URL")
        
        if not db_url:
            console.print("[yellow]DATABASE_URL not configured in .env[/yellow]")
            return
        
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Get table info
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cur.fetchall()
                
                console.print(f"[green]✓ Connected[/green]")
                console.print(f"\n[bold]Tables ({len(tables)}):[/bold]")
                
                for (table_name,) in tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cur.fetchone()[0]
                    console.print(f"  {table_name}: {count:,} rows")
                    
    except ImportError:
        console.print("[red]psycopg2 not installed[/red]")
        console.print("[dim]Install with: uv add psycopg2-binary[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    app()
