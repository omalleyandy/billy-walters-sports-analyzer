#!/usr/bin/env python3
"""
Weekly Production Workflow CLI

Simplified wrapper for running complete Billy Walters weekly workflows.

Quick Examples:
    # Complete workflow (data + edges + results + CLV)
    python weekly_workflow.py --nfl --full

    # Just edge detection and results
    python weekly_workflow.py --ncaaf --edges --results

    # Specific week
    python weekly_workflow.py --nfl --full --week 13

    # Save report
    python weekly_workflow.py --nfl --full --output week_13_report.json
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from walters_analyzer.workflows.weekly_orchestrator import (
    WeeklyWorkflowOrchestrator,
)

if __name__ == "__main__":
    asyncio.run(WeeklyWorkflowOrchestrator.main())
