"""
Backtesting framework for Billy Walters sports betting methodology.

This module provides tools to validate the betting strategy against historical data,
calculate performance metrics, and optimize factor weights.
"""

from .engine import BacktestEngine
from .metrics import PerformanceMetrics
from .validation import StrategyValidator

__all__ = ['BacktestEngine', 'PerformanceMetrics', 'StrategyValidator']
