"""
CLI Package

Provides both the legacy argparse-based CLI (cli.py) and the new
Typer-based CLI (main.py).

Entry points:
- walters-analyzer: Legacy CLI (cli:main)
- walters: New Typer CLI (cli.main:cli)
"""

from .main import app, cli

__all__ = ["app", "cli"]
