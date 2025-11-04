"""
Billy Walters Valuation System
Sophisticated injury impact analysis and betting edge detection
"""

from .player_values import PlayerPosition, PlayerValuation
from .injury_impacts import InjuryType, InjuryImpactCalculator
from .market_analysis import MarketAnalyzer
from .config import load_config, get_config
from .core import BillyWaltersValuation

__all__ = [
    'BillyWaltersValuation',
    'PlayerPosition',
    'PlayerValuation',
    'InjuryType',
    'InjuryImpactCalculator',
    'MarketAnalyzer',
    'load_config',
    'get_config',
]

# Version
__version__ = '1.0.0'

