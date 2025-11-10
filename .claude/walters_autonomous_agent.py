"""
Billy Walters Autonomous Agent System
Self-learning betting agent with reasoning chains and portfolio optimization
"""

import asyncio
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path

# Machine Learning components
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

# Validation components
try:
    from .hooks.validation_logger import ValidationLogger, get_logger
    from .hooks.mcp_validation import (
        fetch_and_validate_odds,
        fetch_and_validate_weather,
        validate_odds_data,
        validate_game_data
    )
    VALIDATION_AVAILABLE = True
    validation_logger = get_logger()
except ImportError:
    VALIDATION_AVAILABLE = False
    validation_logger = None

# Deep Learning for pattern recognition
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

# ============================================================================
# Agent Decision Models
# ============================================================================

class ConfidenceLevel(Enum):
    """Agent confidence in decisions"""
    VERY_LOW = 0.2
    LOW = 0.4
    MODERATE = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

@dataclass
class ReasoningStep:
    """Single step in agent's reasoning chain"""
    step_number: int
    description: str
    evidence: List[str]
    confidence: float
    impact_on_decision: str

@dataclass
class BettingDecision:
    """Complete betting decision with reasoning"""
    game_id: str
    recommendation: str  # 'bet_home', 'bet_away', 'bet_over', 'bet_under', 'pass'
    confidence: ConfidenceLevel
    stake_percentage: float  # % of bankroll
    reasoning_chain: List[ReasoningStep]
    expected_value: float
    risk_assessment: Dict[str, float]
    timestamp: datetime

@dataclass
class PortfolioState:
    """Current portfolio and risk state"""
    total_bankroll: float
    at_risk: float  # Currently wagered
    daily_pnl: float
    weekly_pnl: float
    open_positions: List[Dict]
    correlation_matrix: Optional[np.ndarray] = None
    var_95: float = 0.0  # Value at Risk (95% confidence)

# ============================================================================
# Cognitive Agent Core
# ============================================================================

class WaltersCognitiveAgent:
    """
    Autonomous betting agent with reasoning and learning capabilities
    Implements Billy Walters' principles with AI enhancement
    """

    def __init__(self, initial_bankroll: float = 10000):
        self.bankroll = initial_bankroll
        self.portfolio = PortfolioState(
            total_bankroll=initial_bankroll,
            at_risk=0,
            daily_pnl=0,
            weekly_pnl=0,
            open_positions=[]
        )

        # Learning components
        self.memory_bank = AgentMemory()
        self.pattern_recognizer = PatternRecognitionEngine()
        self.meta_learner = MetaLearningSystem()

        # Models
        self.outcome_predictor = self._initialize_outcome_model()
        self.value_estimator = self._initialize_value_model()
        self.risk_analyzer = RiskAnalysisEngine()

        # Decision tracking
        self.decision_history: List[BettingDecision] = []
        self.performance_metrics = {}

    def _initialize_outcome_model(self) -> xgb.XGBClassifier:
        """Initialize XGBoost model for game outcome prediction"""
        return xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective='binary:logistic',
            use_label_encoder=False
        )

    def _initialize_value_model(self) -> RandomForestRegressor:
        """Initialize model for expected value estimation"""
        return RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )

    async def make_autonomous_decision(self, game_data: Dict) -> BettingDecision:
        """
        Make fully autonomous betting decision with reasoning
        """
        logger.info(f"Analyzing game: {game_data.get('game_id')}")

        # Validate game data if validation is available
        if VALIDATION_AVAILABLE:
            try:
                validation_result = await validate_game_data(game_data)
                if not validation_result['valid']:
                    logger.warning(
                        f"Game data validation warnings for {game_data.get('game_id')}: "
                        f"{validation_result.get('errors', [])}"
                    )
            except Exception as e:
                logger.warning(f"Could not validate game data: {e}")

        # Step 1: Initial Analysis
        reasoning_chain = []

        # Analyze power ratings
        power_analysis = await self._analyze_power_ratings(game_data)
        reasoning_chain.append(ReasoningStep(
            step_number=1,
            description="Power Rating Analysis",
            evidence=[
                f"Home rating: {power_analysis['home_rating']}",
                f"Away rating: {power_analysis['away_rating']}",
                f"Predicted spread: {power_analysis['predicted_spread']}"
            ],
            confidence=power_analysis['confidence'],
            impact_on_decision=power_analysis['impact']
        ))

        # Step 2: Market Analysis
        market_analysis = await self._analyze_market_conditions(game_data)
        reasoning_chain.append(ReasoningStep(
            step_number=2,
            description="Market Efficiency Check",
            evidence=[
                f"Line movement: {market_analysis['line_movement']}",
                f"Public vs sharp: {market_analysis['public_sharp_split']}",
                f"Key number proximity: {market_analysis['key_number_value']}"
            ],
            confidence=market_analysis['confidence'],
            impact_on_decision=market_analysis['impact']
        ))

        # Step 3: Situational Factors
        situational = await self._analyze_situational_factors(game_data)
        reasoning_chain.append(ReasoningStep(
            step_number=3,
            description="Situational Analysis",
            evidence=[
                f"Rest advantage: {situational['rest_days']}",
                f"Travel impact: {situational['travel_distance']}",
                f"Motivation level: {situational['motivation']}"
            ],
            confidence=situational['confidence'],
            impact_on_decision=situational['impact']
        ))

        # Step 4: Historical Patterns
        patterns = await self.pattern_recognizer.find_similar_games(game_data)
        reasoning_chain.append(ReasoningStep(
            step_number=4,
            description="Historical Pattern Matching",
            evidence=[
                f"Similar games found: {patterns['count']}",
                f"Success rate: {patterns['success_rate']}%",
                f"Average ROI: {patterns['avg_roi']}%"
            ],
            confidence=patterns['confidence'],
            impact_on_decision=patterns['impact']
        ))

        # Step 5: Risk Assessment
        risk = await self.risk_analyzer.assess_risk(game_data, self.portfolio)
        reasoning_chain.append(ReasoningStep(
            step_number=5,
            description="Portfolio Risk Analysis",
            evidence=[
                f"Current exposure: {risk['current_exposure']}%",
                f"Correlation risk: {risk['correlation_risk']}",
                f"Max drawdown potential: {risk['max_drawdown']}%"
            ],
            confidence=risk['confidence'],
            impact_on_decision=risk['impact']
        ))

        # Synthesize decision
        decision = await self._synthesize_decision(
            game_data,
            reasoning_chain,
            [power_analysis, market_analysis, situational, patterns, risk]
        )

        # Learn from decision
        self.decision_history.append(decision)
        await self.meta_learner.learn_from_decision(decision)

        return decision

    async def _analyze_power_ratings(self, game_data: Dict) -> Dict:
        """Analyze team power ratings and predicted outcomes"""
        home_rating = game_data.get('home_rating', 0)
        away_rating = game_data.get('away_rating', 0)
        hfa = game_data.get('home_field_advantage', 2.5)

        predicted_spread = (home_rating - away_rating) + hfa
        market_spread = game_data.get('spread', 0)
        edge = market_spread - predicted_spread

        # Confidence based on edge size
        if abs(edge) > 3:
            confidence = 0.9
            impact = "STRONG - Clear value identified"
        elif abs(edge) > 1.5:
            confidence = 0.7
            impact = "MODERATE - Decent edge present"
        else:
            confidence = 0.4
            impact = "WEAK - Minimal edge"

        return {
            'home_rating': home_rating,
            'away_rating': away_rating,
            'predicted_spread': predicted_spread,
            'edge': edge,
            'confidence': confidence,
            'impact': impact
        }

    async def _analyze_market_conditions(self, game_data: Dict) -> Dict:
        """Analyze market efficiency and sharp money indicators"""
        # Check for line movement
        opening_line = game_data.get('opening_spread', 0)
        current_line = game_data.get('spread', 0)
        line_movement = current_line - opening_line

        # Check public vs sharp split
        public_pct = game_data.get('public_percentage', 50)
        money_pct = game_data.get('money_percentage', 50)

        # Reverse line movement indicator
        reverse_indicator = False
        if public_pct > 65 and money_pct < 40:
            reverse_indicator = True

        # Key number analysis
        key_numbers = [3, 7, 6, 10, 14]
        key_number_value = 0
        for num in key_numbers:
            if abs(abs(current_line) - num) < 0.5:
                key_number_value = 0.1 if num in [3, 7] else 0.05

        confidence = 0.8 if reverse_indicator else 0.6
        impact = "STRONG - Sharp money detected" if reverse_indicator else "MODERATE - Normal market"

        return {
            'line_movement': line_movement,
            'public_sharp_split': f"{public_pct}% public / {money_pct}% money",
            'reverse_indicator': reverse_indicator,
            'key_number_value': key_number_value,
            'confidence': confidence,
            'impact': impact
        }

    async def _analyze_situational_factors(self, game_data: Dict) -> Dict:
        """Analyze rest, travel, and motivational factors"""
        # Rest advantage
        home_rest = game_data.get('home_rest_days', 7)
        away_rest = game_data.get('away_rest_days', 7)
        rest_advantage = home_rest - away_rest

        # Travel impact
        travel_distance = game_data.get('away_travel_distance', 0)
        time_zones_crossed = game_data.get('time_zones_crossed', 0)

        # Motivational spots
        revenge_game = game_data.get('revenge_game', False)
        lookahead_spot = game_data.get('lookahead_spot', False)
        sandwich_spot = game_data.get('sandwich_spot', False)

        # Calculate impact
        impact_score = 0
        if abs(rest_advantage) > 3:
            impact_score += 0.2
        if travel_distance > 2000:
            impact_score += 0.1
        if revenge_game:
            impact_score += 0.15
        if lookahead_spot:
            impact_score -= 0.1
        if sandwich_spot:
            impact_score -= 0.15

        confidence = min(0.8, 0.5 + abs(impact_score))
        impact = f"{'POSITIVE' if impact_score > 0 else 'NEGATIVE'} - Score: {impact_score:.2f}"

        return {
            'rest_days': rest_advantage,
            'travel_distance': travel_distance,
            'motivation': 'High' if revenge_game else 'Normal',
            'impact_score': impact_score,
            'confidence': confidence,
            'impact': impact
        }

    async def _synthesize_decision(self, game_data: Dict,
                                  reasoning_chain: List[ReasoningStep],
                                  analyses: List[Dict]) -> BettingDecision:
        """Synthesize all analyses into final decision"""

        # Weight different factors
        weights = {
            'power_rating': 0.35,
            'market': 0.25,
            'situational': 0.15,
            'patterns': 0.15,
            'risk': 0.10
        }

        # Calculate weighted confidence
        total_confidence = sum(
            analysis['confidence'] * weight
            for analysis, weight in zip(analyses, weights.values())
        )

        # Determine confidence level
        if total_confidence > 0.8:
            confidence_level = ConfidenceLevel.VERY_HIGH
        elif total_confidence > 0.65:
            confidence_level = ConfidenceLevel.HIGH
        elif total_confidence > 0.5:
            confidence_level = ConfidenceLevel.MODERATE
        elif total_confidence > 0.35:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.VERY_LOW

        # Determine recommendation
        edge = analyses[0]['edge']  # Power rating edge
        if abs(edge) < 0.5 or confidence_level == ConfidenceLevel.VERY_LOW:
            recommendation = 'pass'
            stake_percentage = 0
        else:
            if edge > 0:
                recommendation = 'bet_away'
            else:
                recommendation = 'bet_home'

            # Kelly-inspired staking
            stake_percentage = min(3.0, max(0.5, total_confidence * 3))

        # Calculate expected value
        win_probability = 0.5238 + (abs(edge) * 0.025)  # Baseline + edge adjustment
        american_odds = -110  # Standard
        decimal_odds = 1.909
        expected_value = (win_probability * (decimal_odds - 1) - (1 - win_probability)) * 100

        # Risk assessment
        risk_assessment = {
            'confidence': total_confidence,
            'volatility': analyses[4].get('correlation_risk', 0),
            'max_loss': stake_percentage,
            'risk_reward_ratio': expected_value / stake_percentage if stake_percentage > 0 else 0
        }

        return BettingDecision(
            game_id=game_data.get('game_id', 'unknown'),
            recommendation=recommendation,
            confidence=confidence_level,
            stake_percentage=stake_percentage,
            reasoning_chain=reasoning_chain,
            expected_value=expected_value,
            risk_assessment=risk_assessment,
            timestamp=datetime.now()
        )

# ============================================================================
# Pattern Recognition Engine
# ============================================================================

class PatternRecognitionEngine:
    """
    Identifies repeating patterns in betting scenarios
    Uses historical data to find similar game situations
    """

    def __init__(self):
        self.pattern_database = []
        self.pattern_model = None

        if TORCH_AVAILABLE:
            self.neural_pattern_matcher = NeuralPatternMatcher()

    async def find_similar_games(self, game_data: Dict) -> Dict:
        """Find historically similar games and their outcomes"""

        # Extract features
        features = self._extract_features(game_data)

        # Search pattern database
        similar_games = self._search_patterns(features)

        if not similar_games:
            return {
                'count': 0,
                'success_rate': 50,
                'avg_roi': 0,
                'confidence': 0.3,
                'impact': 'NEUTRAL - No similar patterns found'
            }

        # Analyze outcomes
        success_rate = sum(1 for g in similar_games if g['won']) / len(similar_games) * 100
        avg_roi = np.mean([g['roi'] for g in similar_games])

        confidence = min(0.9, 0.4 + (len(similar_games) / 100))

        if success_rate > 60 and avg_roi > 5:
            impact = f"POSITIVE - Strong pattern ({success_rate:.1f}% win rate)"
        elif success_rate < 45 or avg_roi < -5:
            impact = f"NEGATIVE - Poor pattern ({success_rate:.1f}% win rate)"
        else:
            impact = "NEUTRAL - Mixed results"

        return {
            'count': len(similar_games),
            'success_rate': success_rate,
            'avg_roi': avg_roi,
            'confidence': confidence,
            'impact': impact,
            'similar_games': similar_games[:5]  # Top 5 most similar
        }

    def _extract_features(self, game_data: Dict) -> np.ndarray:
        """Extract numerical features from game data"""
        features = [
            game_data.get('spread', 0),
            game_data.get('total', 45),
            game_data.get('home_rating', 0),
            game_data.get('away_rating', 0),
            game_data.get('home_rest_days', 7),
            game_data.get('away_rest_days', 7),
            game_data.get('public_percentage', 50),
            game_data.get('weather_temp', 70) if 'weather_temp' in game_data else 70,
            1 if game_data.get('division_game', False) else 0,
            1 if game_data.get('primetime', False) else 0
        ]
        return np.array(features)

    def _search_patterns(self, features: np.ndarray, top_k: int = 20) -> List[Dict]:
        """Search for similar patterns in database"""
        if not self.pattern_database:
            return []

        # Calculate similarity scores
        similarities = []
        for pattern in self.pattern_database:
            similarity = self._calculate_similarity(features, pattern['features'])
            similarities.append((similarity, pattern))

        # Sort by similarity
        similarities.sort(key=lambda x: x[0], reverse=True)

        # Return top K
        return [pattern for _, pattern in similarities[:top_k]]

    def _calculate_similarity(self, features1: np.ndarray,
                            features2: np.ndarray) -> float:
        """Calculate similarity between two feature vectors"""
        # Euclidean distance normalized to 0-1 similarity
        distance = np.linalg.norm(features1 - features2)
        similarity = 1 / (1 + distance)
        return similarity

# ============================================================================
# Neural Pattern Matcher (if PyTorch available)
# ============================================================================

if TORCH_AVAILABLE:
    class NeuralPatternMatcher(nn.Module):
        """
        Deep learning model for pattern matching
        Learns complex non-linear patterns in betting data
        """

        def __init__(self, input_dim: int = 10, hidden_dim: int = 64):
            super().__init__()

            self.encoder = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, hidden_dim // 4)
            )

            self.decoder = nn.Sequential(
                nn.Linear(hidden_dim // 4, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 1),
                nn.Sigmoid()
            )

        def forward(self, x):
            encoded = self.encoder(x)
            output = self.decoder(encoded)
            return output

        def get_embedding(self, x):
            """Get latent representation for similarity comparison"""
            with torch.no_grad():
                return self.encoder(x)

# ============================================================================
# Meta Learning System
# ============================================================================

class MetaLearningSystem:
    """
    Learns from agent's decisions to improve future performance
    Implements experience replay and strategy evolution
    """

    def __init__(self, buffer_size: int = 10000):
        self.experience_buffer = []
        self.buffer_size = buffer_size
        self.strategies = {}
        self.performance_tracker = {}

    async def learn_from_decision(self, decision: BettingDecision):
        """Learn from a betting decision"""

        # Add to experience buffer
        self.experience_buffer.append({
            'decision': decision,
            'timestamp': datetime.now(),
            'features': self._extract_decision_features(decision)
        })

        # Maintain buffer size
        if len(self.experience_buffer) > self.buffer_size:
            self.experience_buffer.pop(0)

        # Update strategy performance
        strategy_key = self._get_strategy_key(decision)
        if strategy_key not in self.strategies:
            self.strategies[strategy_key] = {
                'count': 0,
                'wins': 0,
                'total_roi': 0,
                'confidence_history': []
            }

        self.strategies[strategy_key]['count'] += 1
        self.strategies[strategy_key]['confidence_history'].append(
            decision.confidence.value
        )

    def _extract_decision_features(self, decision: BettingDecision) -> np.ndarray:
        """Extract features from decision for learning"""
        features = [
            decision.confidence.value,
            decision.stake_percentage,
            decision.expected_value,
            len(decision.reasoning_chain),
            decision.risk_assessment.get('volatility', 0),
            decision.risk_assessment.get('risk_reward_ratio', 0)
        ]
        return np.array(features)

    def _get_strategy_key(self, decision: BettingDecision) -> str:
        """Generate strategy identifier from decision"""
        confidence_bucket = 'high' if decision.confidence.value > 0.7 else 'low'
        stake_bucket = 'large' if decision.stake_percentage > 2 else 'small'
        return f"{confidence_bucket}_{stake_bucket}_{decision.recommendation}"

    async def get_strategy_recommendations(self) -> Dict:
        """Get recommendations based on learned strategies"""

        recommendations = {}
        for strategy, performance in self.strategies.items():
            if performance['count'] > 10:  # Minimum sample size
                win_rate = performance['wins'] / performance['count']
                avg_confidence = np.mean(performance['confidence_history'])

                recommendations[strategy] = {
                    'performance': win_rate,
                    'confidence': avg_confidence,
                    'sample_size': performance['count'],
                    'recommendation': 'USE' if win_rate > 0.55 else 'AVOID'
                }

        return recommendations

# ============================================================================
# Risk Analysis Engine
# ============================================================================

class RiskAnalysisEngine:
    """
    Sophisticated risk management using portfolio theory
    """

    def __init__(self):
        self.correlation_window = 50  # Games for correlation calc
        self.var_confidence = 0.95

    async def assess_risk(self, game_data: Dict,
                         portfolio: PortfolioState) -> Dict:
        """Comprehensive risk assessment"""

        # Current exposure
        current_exposure = (portfolio.at_risk / portfolio.total_bankroll) * 100

        # Check correlation with open positions
        correlation_risk = await self._calculate_correlation_risk(
            game_data,
            portfolio.open_positions
        )

        # Calculate potential drawdown
        max_drawdown = self._calculate_max_drawdown(
            portfolio,
            game_data.get('stake', 0)
        )

        # Determine impact
        if current_exposure > 10:
            confidence = 0.3
            impact = "HIGH RISK - Overexposed"
        elif correlation_risk > 0.5:
            confidence = 0.5
            impact = "MODERATE RISK - High correlation"
        else:
            confidence = 0.8
            impact = "ACCEPTABLE RISK - Within limits"

        return {
            'current_exposure': current_exposure,
            'correlation_risk': correlation_risk,
            'max_drawdown': max_drawdown,
            'confidence': confidence,
            'impact': impact,
            'var_95': self._calculate_var(portfolio)
        }

    async def _calculate_correlation_risk(self, game_data: Dict,
                                        open_positions: List[Dict]) -> float:
        """Calculate correlation with existing positions"""
        if not open_positions:
            return 0.0

        # Simplified correlation based on same teams, similar spreads
        correlation = 0.0

        for position in open_positions:
            # Same team involvement
            if (game_data.get('home_team') in position.get('teams', []) or
                game_data.get('away_team') in position.get('teams', [])):
                correlation += 0.3

            # Similar spread range
            if abs(game_data.get('spread', 0) - position.get('spread', 0)) < 1:
                correlation += 0.1

            # Same bet type
            if game_data.get('bet_type') == position.get('bet_type'):
                correlation += 0.1

        return min(1.0, correlation)

    def _calculate_max_drawdown(self, portfolio: PortfolioState,
                               new_stake: float) -> float:
        """Calculate maximum potential drawdown"""
        # Worst case: all open positions lose
        worst_case_loss = portfolio.at_risk + new_stake
        max_drawdown_pct = (worst_case_loss / portfolio.total_bankroll) * 100
        return max_drawdown_pct

    def _calculate_var(self, portfolio: PortfolioState) -> float:
        """Calculate Value at Risk at 95% confidence"""
        if not portfolio.open_positions:
            return 0.0

        # Simplified VaR calculation
        position_values = [p.get('stake', 0) for p in portfolio.open_positions]

        # Assume normal distribution of returns
        mean_return = -0.05  # Slight negative expectation
        std_dev = 0.15  # Volatility

        # VaR at 95% confidence
        var_95 = np.percentile(position_values, 5) * (1 + mean_return - 1.65 * std_dev)

        return abs(var_95)

# ============================================================================
# Agent Memory System
# ============================================================================

class AgentMemory:
    """
    Long-term memory for the agent
    Stores experiences and learned patterns
    """

    def __init__(self, memory_file: str = "agent_memory.json"):
        self.memory_file = Path(memory_file)
        self.short_term = []  # Recent decisions (last 100)
        self.long_term = {}   # Categorized experiences
        self.load_memory()

    def load_memory(self):
        """Load memory from disk"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                self.long_term = data.get('long_term', {})
                logger.info(f"Loaded {len(self.long_term)} long-term memories")

    def save_memory(self):
        """Persist memory to disk"""
        data = {
            'long_term': self.long_term,
            'saved_at': datetime.now().isoformat()
        }
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def remember_decision(self, decision: BettingDecision, outcome: Optional[Dict] = None):
        """Store a decision in memory"""
        memory = {
            'decision': asdict(decision),
            'outcome': outcome,
            'stored_at': datetime.now().isoformat()
        }

        # Add to short-term
        self.short_term.append(memory)
        if len(self.short_term) > 100:
            self.short_term.pop(0)

        # Categorize for long-term
        category = f"{decision.confidence.name}_{decision.recommendation}"
        if category not in self.long_term:
            self.long_term[category] = []

        self.long_term[category].append(memory)

        # Periodically save
        if len(self.short_term) % 10 == 0:
            self.save_memory()

    def recall_similar_decisions(self, current_context: Dict, limit: int = 5) -> List[Dict]:
        """Recall similar past decisions"""
        similar = []

        for category, memories in self.long_term.items():
            for memory in memories[-50:]:  # Check recent 50 in each category
                similarity = self._calculate_context_similarity(
                    current_context,
                    memory['decision']
                )
                similar.append((similarity, memory))

        # Sort by similarity
        similar.sort(key=lambda x: x[0], reverse=True)

        return [memory for _, memory in similar[:limit]]

    def _calculate_context_similarity(self, context1: Dict, context2: Dict) -> float:
        """Calculate similarity between two contexts"""
        # Simple feature comparison
        features_to_compare = ['confidence', 'stake_percentage', 'expected_value']

        similarity = 0
        for feature in features_to_compare:
            if feature in context1 and feature in context2:
                val1 = context1[feature]
                val2 = context2.get(feature, 0)

                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # Normalize difference to 0-1
                    diff = abs(val1 - val2) / (abs(val1) + abs(val2) + 1)
                    similarity += 1 - diff

        return similarity / len(features_to_compare)

# ============================================================================
# Integration Example
# ============================================================================

async def main():
    """Demonstrate autonomous agent capabilities"""

    # Initialize agent
    agent = WaltersCognitiveAgent(initial_bankroll=10000)

    # Sample game data
    game_data = {
        'game_id': 'KC_vs_BUF_2024',
        'home_team': 'Kansas City Chiefs',
        'away_team': 'Buffalo Bills',
        'spread': -2.5,
        'total': 47.5,
        'home_rating': 8.5,
        'away_rating': 9.0,
        'home_field_advantage': 2.5,
        'opening_spread': -3.5,
        'public_percentage': 68,
        'money_percentage': 45,
        'home_rest_days': 10,
        'away_rest_days': 7,
        'away_travel_distance': 950,
        'division_game': False,
        'primetime': True,
        'revenge_game': True
    }

    # Make autonomous decision
    print("🤖 Autonomous Agent Analysis")
    print("=" * 60)

    decision = await agent.make_autonomous_decision(game_data)

    # Display reasoning chain
    print(f"\n📊 Game: {decision.game_id}")
    print(f"Recommendation: {decision.recommendation.upper()}")
    print(f"Confidence: {decision.confidence.name}")
    print(f"Stake: {decision.stake_percentage:.1f}% of bankroll")
    print(f"Expected Value: {decision.expected_value:.2f}%")

    print("\n🧠 Reasoning Chain:")
    for step in decision.reasoning_chain:
        print(f"\nStep {step.step_number}: {step.description}")
        print(f"  Confidence: {step.confidence:.1%}")
        for evidence in step.evidence:
            print(f"  • {evidence}")
        print(f"  Impact: {step.impact_on_decision}")

    print("\n⚠️ Risk Assessment:")
    for key, value in decision.risk_assessment.items():
        print(f"  {key}: {value:.2f}")

    # Store in memory
    agent.memory_bank.remember_decision(decision)

    # Get strategy recommendations
    strategies = await agent.meta_learner.get_strategy_recommendations()
    if strategies:
        print("\n📈 Learned Strategy Performance:")
        for strategy, performance in strategies.items():
            print(f"  {strategy}: {performance['recommendation']}")

if __name__ == "__main__":
    asyncio.run(main())
