#!/usr/bin/env python3
"""
Simple CLV Tracking Script
Easier to use than the module-based CLI
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run
from walters_analyzer.cli.clv_cli import main

if __name__ == '__main__':
    main()
