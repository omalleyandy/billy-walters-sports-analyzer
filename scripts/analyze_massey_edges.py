#!/usr/bin/env python3
"""
Massey Ratings Edge Analyzer

Combines Massey Ratings predictions with market odds from overtime.ag
to identify betting edges using Billy Walters methodology.

Usage:
    python scripts/analyze_massey_edges.py
    python scripts/analyze_massey_edges.py --min-edge 2.5
    python scripts/analyze_massey_edges.py --confidence high
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

try:
    import pandas as pd
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Run: uv sync --extra scraping")
    sys.exit(1)


def load_latest_massey_games(data_dir: Path) -> pd.DataFrame:
    """Load the most recent Massey games predictions."""
    massey_files = sorted(data_dir.glob("massey-games-*.parquet"))
    if not massey_files:
        print(f"ERROR: No Massey games data found in {data_dir}")
        print("Run: uv run walters-analyzer scrape-massey --data-type games")
        sys.exit(1)
    
    latest_file = massey_files[-1]
    print(f"Loading Massey predictions from: {latest_file.name}")
    return pd.read_parquet(latest_file)


def load_latest_market_odds(data_dir: Path) -> pd.DataFrame:
    """Load the most recent market odds from overtime.ag."""
    market_files = sorted(data_dir.glob("overtime-live-*.csv"))
    if not market_files:
        print(f"WARNING: No market odds found in {data_dir}")
        print("Run: uv run walters-analyzer scrape-overtime --sport cfb")
        return None
    
    latest_file = market_files[-1]
    print(f"Loading market odds from: {latest_file.name}")
    return pd.read_csv(latest_file)


def calculate_edges(massey_df: pd.DataFrame, market_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate betting edges by comparing Massey predictions to market odds.
    
    Billy Walters methodology:
    - 2+ point spread edge = betting opportunity
    - 3+ point total edge = betting opportunity
    - Higher confidence with larger edges
    """
    edges = []
    
    for idx, game in massey_df.iterrows():
        away = game['away_team']
        home = game['home_team']
        massey_spread = game['predicted_spread']
        massey_total = game['predicted_total']
        
        edge_data = {
            'date': game.get('game_date'),
            'time': game.get('game_time'),
            'away_team': away,
            'home_team': home,
            'away_rank': game.get('away_rank'),
            'home_rank': game.get('home_rank'),
            'predicted_away_score': game.get('predicted_away_score'),
            'predicted_home_score': game.get('predicted_home_score'),
            'massey_spread': massey_spread,
            'massey_total': massey_total,
            'massey_confidence': game.get('confidence'),
            'market_spread': None,
            'market_total': None,
            'spread_edge': None,
            'total_edge': None,
            'spread_recommendation': 'No market data',
            'total_recommendation': 'No market data',
            'edge_confidence': 'Unknown',
        }
        
        # Try to find matching game in market odds
        if market_df is not None:
            # Simple team name matching (may need fuzzy matching for production)
            match = market_df[
                (market_df['away_team'].str.contains(away.split()[0], case=False, na=False)) &
                (market_df['home_team'].str.contains(home.split()[0], case=False, na=False))
            ]
            
            if len(match) > 0:
                market_game = match.iloc[0]
                market_spread = market_game.get('spread_home_line')
                market_total = market_game.get('total_over_line')
                
                edge_data['market_spread'] = market_spread
                edge_data['market_total'] = market_total
                
                # Calculate spread edge
                if massey_spread is not None and market_spread is not None:
                    spread_edge = abs(massey_spread - market_spread)
                    edge_data['spread_edge'] = spread_edge
                    
                    if spread_edge >= 3.0:
                        edge_data['edge_confidence'] = 'High'
                        if massey_spread < market_spread:
                            edge_data['spread_recommendation'] = f"BET HOME ({home})"
                        else:
                            edge_data['spread_recommendation'] = f"BET AWAY ({away})"
                    elif spread_edge >= 2.0:
                        edge_data['edge_confidence'] = 'Medium'
                        if massey_spread < market_spread:
                            edge_data['spread_recommendation'] = f"Consider HOME ({home})"
                        else:
                            edge_data['spread_recommendation'] = f"Consider AWAY ({away})"
                    else:
                        edge_data['spread_recommendation'] = 'No edge'
                
                # Calculate total edge
                if massey_total is not None and market_total is not None:
                    total_edge = abs(massey_total - market_total)
                    edge_data['total_edge'] = total_edge
                    
                    if total_edge >= 4.0:
                        edge_data['edge_confidence'] = 'High'
                        if massey_total < market_total:
                            edge_data['total_recommendation'] = "BET UNDER"
                        else:
                            edge_data['total_recommendation'] = "BET OVER"
                    elif total_edge >= 3.0:
                        edge_data['edge_confidence'] = 'Medium' if edge_data['edge_confidence'] == 'Unknown' else edge_data['edge_confidence']
                        if massey_total < market_total:
                            edge_data['total_recommendation'] = "Consider UNDER"
                        else:
                            edge_data['total_recommendation'] = "Consider OVER"
                    else:
                        if edge_data['total_recommendation'] == 'No market data':
                            edge_data['total_recommendation'] = 'No edge'
        
        edges.append(edge_data)
    
    return pd.DataFrame(edges)


def main():
    parser = argparse.ArgumentParser(description="Analyze Massey Ratings for betting edges")
    parser.add_argument("--min-edge", type=float, default=2.0,
                       help="Minimum edge in points to display (default: 2.0)")
    parser.add_argument("--confidence", choices=["high", "medium", "low", "all"],
                       default="all",
                       help="Filter by edge confidence level")
    parser.add_argument("--massey-dir", type=Path, default=Path("data/massey_ratings"),
                       help="Directory containing Massey data")
    parser.add_argument("--market-dir", type=Path, default=Path("data/overtime_live"),
                       help="Directory containing market odds")
    args = parser.parse_args()
    
    console = Console()
    
    # Load data
    massey_df = load_latest_massey_games(args.massey_dir)
    market_df = load_latest_market_odds(args.market_dir)
    
    # Calculate edges
    console.print("\n[cyan]Analyzing betting edges...[/cyan]\n")
    edges_df = calculate_edges(massey_df, market_df)
    
    # Filter by minimum edge
    if market_df is not None:
        filtered_edges = edges_df[
            (edges_df['spread_edge'] >= args.min_edge) |
            (edges_df['total_edge'] >= args.min_edge)
        ]
    else:
        # Without market data, just show all Massey predictions
        filtered_edges = edges_df
    
    # Filter by confidence if specified
    if args.confidence != "all":
        conf_map = {"high": "High", "medium": "Medium", "low": "Low"}
        filtered_edges = filtered_edges[
            filtered_edges['edge_confidence'] == conf_map[args.confidence]
        ]
    
    # Display results
    if len(filtered_edges) == 0:
        console.print("[yellow]No edges found with current filters[/yellow]")
        console.print(f"Try lowering --min-edge (current: {args.min_edge})")
        return
    
    # Create Rich table for display
    table = Table(title=f"🎯 Betting Edges ({len(filtered_edges)} games)")
    table.add_column("Matchup", style="cyan", no_wrap=False)
    table.add_column("Massey\nSpread", justify="right", style="yellow")
    table.add_column("Market\nSpread", justify="right")
    table.add_column("Edge", justify="right", style="green")
    table.add_column("Massey\nTotal", justify="right", style="yellow")
    table.add_column("Market\nTotal", justify="right")
    table.add_column("Total\nEdge", justify="right", style="green")
    table.add_column("Recommendation", style="bold")
    
    for _, edge in filtered_edges.iterrows():
        matchup = f"{edge['away_team']} @ {edge['home_team']}"
        
        # Format spread edge
        spread_edge_str = f"{edge['spread_edge']:.1f}" if edge['spread_edge'] else "—"
        if edge['spread_edge'] and edge['spread_edge'] >= 3.0:
            spread_edge_str = f"[bold green]{spread_edge_str}[/bold green]"
        elif edge['spread_edge'] and edge['spread_edge'] >= 2.0:
            spread_edge_str = f"[green]{spread_edge_str}[/green]"
        
        # Format total edge
        total_edge_str = f"{edge['total_edge']:.1f}" if edge['total_edge'] else "—"
        if edge['total_edge'] and edge['total_edge'] >= 4.0:
            total_edge_str = f"[bold green]{total_edge_str}[/bold green]"
        elif edge['total_edge'] and edge['total_edge'] >= 3.0:
            total_edge_str = f"[green]{total_edge_str}[/green]"
        
        # Build recommendation
        recs = []
        if edge['spread_recommendation'] and edge['spread_recommendation'] not in ['No edge', 'No market data']:
            recs.append(edge['spread_recommendation'])
        if edge['total_recommendation'] and edge['total_recommendation'] not in ['No edge', 'No market data']:
            recs.append(edge['total_recommendation'])
        
        recommendation = " | ".join(recs) if recs else "—"
        
        table.add_row(
            matchup,
            f"{edge['massey_spread']:.1f}" if edge['massey_spread'] else "—",
            f"{edge['market_spread']:.1f}" if edge['market_spread'] else "—",
            spread_edge_str,
            f"{edge['massey_total']:.1f}" if edge['massey_total'] else "—",
            f"{edge['market_total']:.1f}" if edge['market_total'] else "—",
            total_edge_str,
            recommendation,
        )
    
    console.print(table)
    
    # Show summary stats
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total games analyzed: {len(edges_df)}")
    console.print(f"  Games with {args.min_edge}+ point edge: {len(filtered_edges)}")
    
    if market_df is not None:
        high_conf = len(filtered_edges[filtered_edges['edge_confidence'] == 'High'])
        med_conf = len(filtered_edges[filtered_edges['edge_confidence'] == 'Medium'])
        console.print(f"  High confidence edges: {high_conf}")
        console.print(f"  Medium confidence edges: {med_conf}")
    
    # Billy Walters reminder
    console.print("\n[yellow]⚠️  Remember to check before betting:[/yellow]")
    console.print("  1. Injury reports (key players out?)")
    console.print("  2. Weather conditions (wind, rain, cold?)")
    console.print("  3. Line movement (steam? reverse line movement?)")
    console.print("  4. Public betting % (fade the public)")
    console.print("  5. Your own model's prediction")
    
    # Save to file for reference
    output_file = args.massey_dir / f"edge_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filtered_edges.to_csv(output_file, index=False)
    console.print(f"\n[green]Saved analysis to: {output_file}[/green]")


if __name__ == "__main__":
    main()

