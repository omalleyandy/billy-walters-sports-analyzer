"""
Enhanced Research Engine - Multi-source data coordinator

Integrates:
- Your existing Scrapy spiders (via ScrapyBridge)
- API calls (Weather, News, ProFootballDoc)
- Phase 1 components (HTTP client, caching, models)

Usage:
    from walters.research import ResearchEngine
    
    engine = ResearchEngine()
    
    # Comprehensive injury analysis (multi-source)
    analysis = await engine.comprehensive_injury_research(
        "Kansas City Chiefs",
        use_scrapy=True,  # Load your ESPN Scrapy data
        use_simulation=False  # Or True for demo
    )
    
    print(f"Impact: {analysis['total_impact']:+.1f} points")
    print(f"Sources: {', '.join(analysis['sources_used'])}")
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.http_client import async_get
from ..core.cache import cache_weather_data, cache_injury_data
from ..core.models import InjuryReport

from .scrapy_bridge import ScrapyBridge

logger = logging.getLogger(__name__)


class ResearchEngine:
    """
    Multi-source research engine for Billy Walters methodology.
    
    Coordinates data from:
    1. Your Scrapy spiders (ESPN, Massey, Overtime) - via ScrapyBridge
    2. Weather APIs (AccuWeather, OpenWeather)
    3. ProFootballDoc (medical analysis) - when added
    4. News API (breaking news) - optional
    
    All with Phase 1 benefits:
    - HTTP connection pooling
    - Automatic caching
    - Unified data models
    """
    
    def __init__(self, enable_web_fetch: bool = True):
        """
        Initialize research engine.
        
        Args:
            enable_web_fetch: Enable live web/API fetching (vs simulation)
        """
        self.enable_web_fetch = enable_web_fetch
        self.scrapy = ScrapyBridge()
        
        # Future: Add ProFootballDoc, News API clients here
    
    @cache_injury_data(ttl=900)  # Cache for 15 minutes
    async def comprehensive_injury_research(
        self,
        team: str,
        use_scrapy: bool = True,
        use_simulation: bool = False
    ) -> Dict[str, Any]:
        """
        Perform comprehensive injury research from multiple sources.
        
        Args:
            team: Team name (e.g., "Kansas City Chiefs")
            use_scrapy: Load data from your existing ESPN Scrapy spider
            use_simulation: Use simulated data for demo (useful for testing)
        
        Returns:
            Comprehensive analysis dict with:
                - total_impact: Point spread impact
                - impact_level: HEALTHY, MINOR, MODERATE, SEVERE
                - betting_advice: Billy Walters recommendation
                - injury_count: Number of injuries
                - high_confidence_count: High confidence injuries
                - sources_used: List of data sources
                - detailed_injuries: Full injury details
                - position_breakdown: Injuries by position group
        
        Example:
            engine = ResearchEngine()
            analysis = await engine.comprehensive_injury_research(
                "Kansas City Chiefs",
                use_scrapy=True
            )
            
            print(f"Total Impact: {analysis['total_impact']:+.1f} points")
            print(f"Recommendation: {analysis['betting_advice']}")
        """
        print(f"\n[RESEARCH] Comprehensive injury analysis: {team}")
        print("-" * 60)
        
        all_injuries: List[InjuryReport] = []
        sources_used = []
        
        # Source 1: Your existing ESPN Scrapy spider
        if use_scrapy and not use_simulation:
            print("  [1/3] Loading ESPN injury data (Scrapy)...")
            try:
                # Load latest scraped data
                scrapy_injuries = self.scrapy.load_latest_injuries(sport="nfl")
                
                # Filter for this specific team
                team_injuries = self.scrapy.filter_by_team(scrapy_injuries, team)
                
                if team_injuries:
                    # Convert to InjuryReport format
                    espn_reports = self.scrapy.convert_to_injury_reports(team_injuries)
                    all_injuries.extend(espn_reports)
                    sources_used.append("ESPN (Scrapy)")
                    print(f"        Found {len(espn_reports)} ESPN injuries")
                else:
                    print(f"        No injuries found for {team} in ESPN data")
                
            except Exception as e:
                print(f"        Warning: {e}")
        
        # Source 2: ProFootballDoc (future)
        print("  [2/3] ProFootballDoc medical analysis...")
        print("        [dim](Not yet implemented - coming soon!)[/dim]")
        
        # Source 3: News API (future)
        print("  [3/3] News API monitoring...")
        print("        [dim](Optional feature - can add if needed)[/dim]")
        
        # If no real data, use simulation for demo
        if not all_injuries and use_simulation:
            print("\n  [DEMO] Using simulated data for demonstration...")
            all_injuries = self._generate_simulated_injuries(team)
            sources_used.append("Simulated Data (for demo)")
        
        # Generate comprehensive analysis
        if all_injuries:
            print(f"\n  [ANALYSIS] Aggregating {len(all_injuries)} injuries...")
            analysis = self._generate_comprehensive_analysis(
                team, all_injuries, sources_used
            )
        else:
            # Return empty analysis
            analysis = {
                'team': team,
                'total_impact': 0.0,
                'impact_level': 'UNKNOWN',
                'betting_advice': 'No injury data available',
                'injury_count': 0,
                'high_confidence_count': 0,
                'sources_used': [],
                'detailed_injuries': [],
                'position_breakdown': {},
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"  [RESULT] Total impact: {analysis['total_impact']:+.1f} points")
        print(f"           Impact level: {analysis['impact_level']}")
        print(f"           Sources: {', '.join(analysis['sources_used']) if analysis['sources_used'] else 'None'}")
        print("-" * 60)
        
        return analysis
    
    def _generate_comprehensive_analysis(
        self,
        team: str,
        injuries: List[InjuryReport],
        sources: List[str]
    ) -> Dict[str, Any]:
        """
        Generate Billy Walters injury impact analysis.
        
        Methodology:
        - Confidence-weighted impact aggregation
        - Position group breakdown
        - Impact level assessment
        - Betting recommendations
        """
        # Calculate total impact (confidence-weighted)
        total_impact = 0.0
        high_confidence_injuries = []
        
        for injury in injuries:
            # Weight impact by confidence (Billy Walters approach)
            weighted_impact = injury.point_value * injury.confidence
            total_impact += weighted_impact
            
            # Track high confidence injuries (>70%)
            if injury.confidence >= 0.7:
                high_confidence_injuries.append(injury)
        
        # Position group breakdown (offense vs defense impact)
        position_groups = {
            'Offense': [],
            'Defense': [],
            'Special Teams': []
        }
        
        for injury in injuries:
            if injury.position in ['QB', 'RB', 'WR', 'TE', 'OL']:
                position_groups['Offense'].append(injury)
            elif injury.position in ['DE', 'DT', 'LB', 'CB', 'S', 'DB']:
                position_groups['Defense'].append(injury)
            else:
                position_groups['Special Teams'].append(injury)
        
        # Billy Walters impact assessment
        if total_impact <= -3.0:
            impact_level = "SEVERE"
            betting_advice = "Consider fading team or reducing position size significantly"
        elif total_impact <= -1.5:
            impact_level = "MODERATE"
            betting_advice = "Factor 1-2 points into line analysis"
        elif total_impact <= -0.5:
            impact_level = "MINOR"
            betting_advice = "Minimal adjustment needed (0.5 points)"
        else:
            impact_level = "HEALTHY"
            betting_advice = "No significant injury discount required"
        
        return {
            'team': team,
            'total_impact': round(total_impact, 2),
            'impact_level': impact_level,
            'betting_advice': betting_advice,
            'injury_count': len(injuries),
            'high_confidence_count': len(high_confidence_injuries),
            'sources_used': sources,
            'position_breakdown': {
                group: len(inj_list) for group, inj_list in position_groups.items()
            },
            'detailed_injuries': [
                {
                    'player': inj.player_name,
                    'position': inj.position,
                    'injury': inj.injury_type,
                    'status': inj.status,
                    'severity': inj.severity,
                    'confidence': round(inj.confidence, 2),
                    'source': inj.source,
                    'impact': round(inj.point_value, 1)
                }
                for inj in injuries
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_simulated_injuries(self, team: str) -> List[InjuryReport]:
        """Generate realistic simulated injuries for demo purposes."""
        return [
            InjuryReport(
                player_name="Patrick Mahomes",
                position="QB",
                injury_type="High ankle sprain",
                status="Questionable",
                point_value=-3.0,
                severity="SIGNIFICANT",
                confidence=0.85,
                source="Simulated (Demo)",
                prognosis="Game-time decision, may play through pain",
                timestamp=datetime.now()
            ),
            InjuryReport(
                player_name="Travis Kelce",
                position="TE",
                injury_type="Knee bruise",
                status="Probable",
                point_value=-0.8,
                severity="MINOR",
                confidence=0.75,
                source="Simulated (Demo)",
                prognosis="Expected to play",
                timestamp=datetime.now()
            ),
            InjuryReport(
                player_name="Chris Jones",
                position="DE",
                injury_type="Shoulder",
                status="Questionable",
                point_value=-2.0,
                severity="MODERATE",
                confidence=0.70,
                source="Simulated (Demo)",
                prognosis="Limited in practice",
                timestamp=datetime.now()
            )
        ]
    
    @cache_weather_data(ttl=1800)
    async def fetch_weather_data(
        self,
        city: str,
        state: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch weather data.
        
        This delegates to your existing weather_fetcher.py.
        In the future, this can coordinate multiple weather sources.
        
        Args:
            city: City name
            state: State abbreviation (improves accuracy)
            date: Game date (YYYY-MM-DD)
        
        Returns:
            Weather data dict
        """
        # Future: Delegate to your weather_fetcher.py
        # For now, return placeholder
        return {
            'city': city,
            'state': state,
            'temperature': None,
            'conditions': 'Weather integration pending',
            'source': 'Placeholder'
        }


# Example usage
if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    async def test_engine():
        """Test ResearchEngine."""
        console.print(Panel.fit(
            "[bold cyan]Testing ResearchEngine[/bold cyan]\n"
            "Multi-source injury analysis",
            border_style="cyan"
        ))
        
        engine = ResearchEngine()
        
        # Test with simulation (since we don't have ESPN data yet)
        console.print("\n[bold]Testing with simulated data...[/bold]")
        
        analysis = await engine.comprehensive_injury_research(
            "Kansas City Chiefs",
            use_scrapy=False,  # No scrapy data yet
            use_simulation=True  # Use demo data
        )
        
        # Display results
        console.print(f"\n[bold cyan]Analysis Results:[/bold cyan]")
        console.print(f"  Team: {analysis['team']}")
        console.print(f"  Total Impact: [red]{analysis['total_impact']:+.1f}[/red] points")
        console.print(f"  Impact Level: [yellow]{analysis['impact_level']}[/yellow]")
        console.print(f"  Recommendation: {analysis['betting_advice']}")
        console.print(f"  Sources: {', '.join(analysis['sources_used'])}")
        
        console.print(f"\n[bold]Detailed Injuries ({analysis['injury_count']} total):[/bold]")
        for inj in analysis['detailed_injuries']:
            console.print(
                f"  - {inj['player']} ({inj['position']}): {inj['injury']}"
            )
            console.print(
                f"    Status: {inj['status']} | "
                f"Impact: {inj['impact']:+.1f} | "
                f"Confidence: {inj['confidence']:.0%}"
            )
        
        console.print("\n" + "=" * 60)
        console.print("[bold green][SUCCESS] ResearchEngine working![/bold green]")
    
    asyncio.run(test_engine())

