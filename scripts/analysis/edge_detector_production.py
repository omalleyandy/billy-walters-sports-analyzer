#!/usr/bin/env python3
"""
Production Edge Detection CLI

Complete end-to-end edge detection for NFL and NCAAF:
- Auto-detects current week from system date
- Validates schedule and odds files
- Performs comprehensive game matching
- Detects betting edges with confidence scores
- Outputs results in multiple formats

Usage:
    # Auto-detect week and run NFL edge detection
    python edge_detector_production.py --nfl

    # Detect edges for specific week
    python edge_detector_production.py --ncaaf --week 13

    # Run both leagues
    python edge_detector_production.py --both

    # Output to JSON file
    python edge_detector_production.py --nfl --output edges.json

    # Verbose output with detailed validation
    python edge_detector_production.py --nfl --verbose
"""

import asyncio
import json
import logging
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import List

from walters_analyzer.valuation.edge_detection_orchestrator import (
    EdgeDetectionOrchestrator,
)
from walters_analyzer.valuation.ncaaf_edge_detector import BettingEdge

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class EdgeDetectionCLI:
    """Production CLI for edge detection"""

    def __init__(self, args):
        """Initialize CLI"""
        self.args = args
        self.orchestrator = EdgeDetectionOrchestrator()
        self.project_root = Path(__file__).parent.parent.parent

    async def run(self) -> int:
        """Run edge detection"""
        try:
            if self.args.both:
                # Run both leagues
                nfl_edges = await self.run_league("nfl")
                ncaaf_edges = await self.run_league("ncaaf")
                all_edges = nfl_edges + ncaaf_edges
            elif self.args.nfl:
                all_edges = await self.run_league("nfl")
            else:
                all_edges = await self.run_league("ncaaf")

            # Output results
            self.output_results(all_edges)

            return 0 if all_edges else 1

        except Exception as e:
            logger.error(f"[ERROR] Edge detection failed: {e}")
            return 1

    async def run_league(self, league: str) -> List[BettingEdge]:
        """Run edge detection for a league"""
        logger.info(f"\n{'=' * 70}")
        logger.info(f"STARTING {league.upper()} EDGE DETECTION")
        logger.info(f"{'=' * 70}\n")

        try:
            # Run with optional week override
            week = self.args.week if self.args.week else None
            edges = await self.orchestrator.run_edge_detection(league=league, week=week)

            logger.info(f"\n[OK] Found {len(edges)} {league.upper()} edges")
            return edges

        except Exception as e:
            logger.error(f"[ERROR] {league.upper()} detection failed: {e}")
            return []

    def output_results(self, edges: List[BettingEdge]):
        """Output results in multiple formats"""
        if not edges:
            logger.warning("[WARNING] No edges found")
            return

        # Console output
        self.print_console_output(edges)

        # File output if requested
        if self.args.output:
            self.write_json_output(edges)
            logger.info(f"[OK] Results written to {self.args.output}")

    def print_console_output(self, edges: List[BettingEdge]):
        """Print formatted output to console"""
        logger.info("\n" + "=" * 70)
        logger.info("BETTING EDGES SUMMARY")
        logger.info("=" * 70)

        # Group by league
        nfl_edges = [e for e in edges if "NFL" in str(e.matchup).upper()]
        ncaaf_edges = [e for e in edges if "NFL" not in str(e.matchup).upper()]

        if nfl_edges:
            logger.info(f"\nNFL EDGES ({len(nfl_edges)}):")
            for i, edge in enumerate(
                sorted(
                    nfl_edges,
                    key=lambda e: e.edge_points,
                    reverse=True,
                ),
                1,
            ):
                logger.info(
                    f"  {i}. {edge.matchup}: {edge.edge_points:.1f} pts "
                    f"({edge.edge_strength}) - "
                    f"Bet {edge.recommended_bet.upper() if edge.recommended_bet else 'N/A'}"
                )

        if ncaaf_edges:
            logger.info(f"\nNCAAF EDGES ({len(ncaaf_edges)}):")
            for i, edge in enumerate(
                sorted(
                    ncaaf_edges,
                    key=lambda e: e.edge_points,
                    reverse=True,
                ),
                1,
            ):
                logger.info(
                    f"  {i}. {edge.matchup}: {edge.edge_points:.1f} pts "
                    f"({edge.edge_strength}) - "
                    f"Bet {edge.recommended_bet.upper() if edge.recommended_bet else 'N/A'}"
                )

        logger.info("\n" + "=" * 70 + "\n")

    def write_json_output(self, edges: List[BettingEdge]):
        """Write results to JSON file"""
        output_path = self.project_root / self.args.output

        # Convert edges to dictionaries
        edges_data = []
        for edge in edges:
            edge_dict = {
                "matchup": edge.matchup,
                "week": edge.week,
                "edge_points": edge.edge_points,
                "edge_strength": edge.edge_strength,
                "predicted_spread": edge.predicted_spread,
                "market_spread": edge.market_spread,
                "recommended_bet": edge.recommended_bet,
                "confidence_score": edge.confidence_score,
                "away_team": edge.away_team,
                "home_team": edge.home_team,
                "away_rating": edge.away_rating,
                "home_rating": edge.home_rating,
            }
            edges_data.append(edge_dict)

        # Write to file
        with open(output_path, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total_edges": len(edges),
                    "edges": edges_data,
                },
                f,
                indent=2,
            )


def main():
    """Main entry point"""
    parser = ArgumentParser(
        description="Production Edge Detection CLI",
        formatter_class=lambda prog: parser.Formatter(prog, max_help_position=40),
    )

    # League selection
    league_group = parser.add_mutually_exclusive_group(required=True)
    league_group.add_argument("--nfl", action="store_true", help="Detect NFL edges")
    league_group.add_argument("--ncaaf", action="store_true", help="Detect NCAAF edges")
    league_group.add_argument(
        "--both", action="store_true", help="Detect both NFL and NCAAF edges"
    )

    # Optional parameters
    parser.add_argument(
        "--week",
        type=int,
        help="Specific week (auto-detects if not provided)",
    )
    parser.add_argument("--output", help="Output file path (JSON format)")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output with detailed validation",
    )

    args = parser.parse_args()

    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run CLI
    cli = EdgeDetectionCLI(args)
    exit_code = asyncio.run(cli.run())

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
