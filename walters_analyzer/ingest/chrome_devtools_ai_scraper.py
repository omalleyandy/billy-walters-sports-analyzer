"""
Enhanced Chrome DevTools Scraper with AI Assistance
Implements Chrome DevTools AI features for maximum capabilities and performance

Features:
- AI-assisted debugging
- Performance monitoring with AI insights
- Network request analysis
- Source code understanding
- Styling diagnostics
- Code suggestions
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ChromeDevToolsAIPerformance:
    """AI-assisted performance monitoring for the scraper"""
    
    def __init__(self):
        self.metrics = {
            'page_load_time': 0.0,
            'dom_content_loaded': 0.0,
            'network_requests': 0,
            'javascript_errors': [],
            'console_warnings': [],
            'performance_insights': []
        }
    
    def analyze_performance_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze performance metrics with AI insights
        
        Returns insights like:
        - Bottlenecks (slow network requests, large payloads)
        - Optimization opportunities
        - Resource loading issues
        """
        insights = []
        
        # Analyze page load time
        if metrics.get('page_load_time', 0) > 3000:
            insights.append({
                'type': 'slow_load',
                'severity': 'high',
                'message': f"Page load time is {metrics['page_load_time']}ms (>3s threshold)",
                'suggestion': "Consider waiting for specific elements instead of full page load"
            })
        
        # Analyze network requests
        if metrics.get('network_requests', 0) > 100:
            insights.append({
                'type': 'excessive_requests',
                'severity': 'medium',
                'message': f"{metrics['network_requests']} network requests detected",
                'suggestion': "Many requests may indicate inefficient scraping. Consider targeted element waiting."
            })
        
        # Analyze JavaScript errors
        if metrics.get('javascript_errors'):
            insights.append({
                'type': 'javascript_errors',
                'severity': 'high',
                'message': f"{len(metrics['javascript_errors'])} JavaScript errors found",
                'errors': metrics['javascript_errors'][:5],  # Top 5 errors
                'suggestion': "JS errors may block odds loading. Check console for betting platform errors."
            })
        
        return {
            'metrics': metrics,
            'insights': insights,
            'performance_score': self._calculate_performance_score(metrics, insights)
        }
    
    def _calculate_performance_score(self, metrics: Dict, insights: List[Dict]) -> int:
        """Calculate performance score (0-100)"""
        score = 100
        
        # Deduct points for issues
        for insight in insights:
            if insight['severity'] == 'high':
                score -= 20
            elif insight['severity'] == 'medium':
                score -= 10
            elif insight['severity'] == 'low':
                score -= 5
        
        return max(0, score)


class ChromeDevToolsAINetwork:
    """AI-assisted network request analysis"""
    
    def __init__(self):
        self.requests = []
        self.patterns = {
            'odds_api': ['/odds', '/markets', '/betting', '/lines'],
            'static_assets': ['.js', '.css', '.png', '.jpg', '.svg'],
            'analytics': ['analytics', 'tracking', 'gtm', 'facebook']
        }
    
    def analyze_network_requests(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze network requests with AI insights
        
        Identifies:
        - Odds API endpoints
        - Slow requests
        - Failed requests
        - Unnecessary requests
        """
        analysis = {
            'total_requests': len(requests),
            'odds_endpoints': [],
            'slow_requests': [],
            'failed_requests': [],
            'unnecessary_requests': [],
            'insights': []
        }
        
        for req in requests:
            url = req.get('url', '')
            duration = req.get('duration', 0)
            status = req.get('status', 200)
            size = req.get('size', 0)
            
            # Identify odds API endpoints
            if any(pattern in url.lower() for pattern in self.patterns['odds_api']):
                analysis['odds_endpoints'].append({
                    'url': url,
                    'method': req.get('method', 'GET'),
                    'status': status,
                    'duration': duration
                })
            
            # Identify slow requests (>1s)
            if duration > 1000:
                analysis['slow_requests'].append({
                    'url': url,
                    'duration': duration,
                    'suggestion': f"Request took {duration}ms. Consider caching or optimizing."
                })
            
            # Identify failed requests
            if status >= 400:
                analysis['failed_requests'].append({
                    'url': url,
                    'status': status,
                    'suggestion': f"Request failed with status {status}. Check authentication/permissions."
                })
            
            # Identify unnecessary requests (analytics, tracking)
            if any(pattern in url.lower() for pattern in self.patterns['analytics']):
                analysis['unnecessary_requests'].append({
                    'url': url,
                    'suggestion': "Analytics request - not needed for scraping. Consider blocking."
                })
        
        # Generate insights
        if analysis['odds_endpoints']:
            analysis['insights'].append({
                'type': 'odds_api_found',
                'message': f"Found {len(analysis['odds_endpoints'])} odds API endpoints",
                'recommendation': "These endpoints may provide structured data alternative to DOM scraping"
            })
        
        if len(analysis['unnecessary_requests']) > 10:
            analysis['insights'].append({
                'type': 'optimization',
                'message': f"{len(analysis['unnecessary_requests'])} unnecessary requests detected",
                'recommendation': "Consider blocking analytics/tracking to improve scraping speed"
            })
        
        return analysis
    
    def suggest_request_interception(self, analysis: Dict[str, Any]) -> List[str]:
        """Suggest request patterns to intercept/block for faster scraping"""
        patterns_to_block = []
        
        # Block analytics
        if len(analysis.get('unnecessary_requests', [])) > 5:
            patterns_to_block.extend(self.patterns['analytics'])
        
        # Block static assets if not needed
        patterns_to_block.extend(self.patterns['static_assets'])
        
        return patterns_to_block


class ChromeDevToolsAISources:
    """AI-assisted source code analysis"""
    
    def __init__(self):
        self.source_cache = {}
    
    def analyze_page_structure(self, html_source: str) -> Dict[str, Any]:
        """
        Analyze HTML structure with AI insights
        
        Identifies:
        - Betting odds containers
        - Dynamic content patterns
        - JavaScript dependencies
        - Data attributes for scraping
        """
        analysis = {
            'odds_containers': [],
            'data_attributes': [],
            'javascript_frameworks': [],
            'insights': []
        }
        
        # Identify odds-related containers
        odds_patterns = [
            r'class="[^"]*odds[^"]*"',
            r'class="[^"]*betting[^"]*"',
            r'class="[^"]*market[^"]*"',
            r'data-game-id=',
            r'data-odds=',
            r'data-line='
        ]
        
        for pattern in odds_patterns:
            matches = re.findall(pattern, html_source, re.IGNORECASE)
            if matches:
                analysis['odds_containers'].extend(matches[:10])  # Top 10
        
        # Identify data attributes
        data_attr_pattern = r'data-[\w-]+='
        data_attrs = set(re.findall(data_attr_pattern, html_source))
        analysis['data_attributes'] = list(data_attrs)[:20]  # Top 20
        
        # Identify JavaScript frameworks
        if 'React' in html_source or 'react' in html_source.lower():
            analysis['javascript_frameworks'].append('React')
        if 'Vue' in html_source or 'vue' in html_source.lower():
            analysis['javascript_frameworks'].append('Vue')
        if 'Angular' in html_source or 'angular' in html_source.lower():
            analysis['javascript_frameworks'].append('Angular')
        
        # Generate insights
        if analysis['data_attributes']:
            analysis['insights'].append({
                'type': 'data_attributes',
                'message': f"Found {len(analysis['data_attributes'])} data attributes",
                'recommendation': "Use data attributes for more reliable element selection"
            })
        
        if analysis['javascript_frameworks']:
            analysis['insights'].append({
                'type': 'framework_detected',
                'message': f"Detected frameworks: {', '.join(analysis['javascript_frameworks'])}",
                'recommendation': "Wait for framework initialization before scraping"
            })
        
        return analysis


class ChromeDevToolsAIDebugger:
    """AI-assisted debugging for scraping issues"""
    
    def __init__(self):
        self.error_history = []
    
    def diagnose_scraping_failure(
        self,
        snapshot: str,
        expected_elements: List[str],
        found_elements: List[str]
    ) -> Dict[str, Any]:
        """
        Diagnose why scraping failed with AI insights
        
        Args:
            snapshot: Accessibility tree snapshot
            expected_elements: Elements we expected to find
            found_elements: Elements we actually found
            
        Returns:
            Diagnosis with actionable recommendations
        """
        diagnosis = {
            'missing_elements': [],
            'potential_causes': [],
            'recommendations': []
        }
        
        # Identify missing elements
        missing = set(expected_elements) - set(found_elements)
        diagnosis['missing_elements'] = list(missing)
        
        # Analyze potential causes
        if 'button' in str(missing):
            diagnosis['potential_causes'].append({
                'cause': 'Dynamic content not loaded',
                'evidence': 'Expected button elements not found',
                'likelihood': 'high'
            })
            diagnosis['recommendations'].append(
                "Wait for dynamic content: Use 'wait_for' with specific text/element"
            )
        
        if not snapshot or len(snapshot) < 100:
            diagnosis['potential_causes'].append({
                'cause': 'Page not fully loaded',
                'evidence': 'Snapshot too small',
                'likelihood': 'high'
            })
            diagnosis['recommendations'].append(
                "Increase wait time or wait for specific loading indicators"
            )
        
        if 'Cloudflare' in snapshot or 'checking your browser' in snapshot.lower():
            diagnosis['potential_causes'].append({
                'cause': 'Cloudflare challenge',
                'evidence': 'Cloudflare text detected in snapshot',
                'likelihood': 'very high'
            })
            diagnosis['recommendations'].append(
                "Cloudflare challenge active. Wait 5-10 seconds for bypass to complete."
            )
        
        return diagnosis
    
    def suggest_wait_strategy(self, page_type: str) -> Dict[str, Any]:
        """Suggest optimal wait strategy based on page type"""
        strategies = {
            'odds_page': {
                'primary': "wait_for with text like first team name",
                'fallback': "wait 3-5 seconds for odds to load",
                'verification': "Check for button elements with odds text"
            },
            'live_betting': {
                'primary': "wait_for 'LIVE' indicator",
                'fallback': "wait for changing odds numbers",
                'verification': "Verify timestamp is updating"
            },
            'login_page': {
                'primary': "wait_for dashboard element",
                'fallback': "wait 2-3 seconds post-login",
                'verification': "Check for logout button or user menu"
            }
        }
        
        return strategies.get(page_type, strategies['odds_page'])


class EnhancedChromeDevToolsOddsExtractor:
    """
    Enhanced odds extractor with AI assistance capabilities
    Extends the base ChromeDevToolsOddsExtractor with AI features
    """
    
    def __init__(self):
        self.performance = ChromeDevToolsAIPerformance()
        self.network = ChromeDevToolsAINetwork()
        self.sources = ChromeDevToolsAISources()
        self.debugger = ChromeDevToolsAIDebugger()
        self.current_date = None
        self.current_time = None
        
        # AI-assisted logging
        self.session_log = {
            'started_at': datetime.utcnow().isoformat(),
            'performance_metrics': [],
            'network_analysis': [],
            'debugging_events': [],
            'success_rate': 0.0
        }
    
    def extract_with_ai_assistance(
        self,
        snapshot_text: str,
        network_requests: Optional[List[Dict]] = None,
        html_source: Optional[str] = None,
        performance_metrics: Optional[Dict] = None
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Extract games with comprehensive AI assistance
        
        Returns:
            Tuple of (games, ai_insights)
        """
        ai_insights = {
            'extraction_success': False,
            'performance_analysis': {},
            'network_analysis': {},
            'source_analysis': {},
            'debugging_info': {},
            'recommendations': []
        }
        
        # Performance analysis
        if performance_metrics:
            ai_insights['performance_analysis'] = self.performance.analyze_performance_metrics(
                performance_metrics
            )
            self.session_log['performance_metrics'].append(ai_insights['performance_analysis'])
        
        # Network analysis
        if network_requests:
            ai_insights['network_analysis'] = self.network.analyze_network_requests(
                network_requests
            )
            self.session_log['network_analysis'].append(ai_insights['network_analysis'])
            
            # Suggest request blocking patterns
            blocking_patterns = self.network.suggest_request_interception(
                ai_insights['network_analysis']
            )
            if blocking_patterns:
                ai_insights['recommendations'].append({
                    'type': 'request_blocking',
                    'patterns': blocking_patterns,
                    'benefit': 'Faster scraping, lower bandwidth'
                })
        
        # Source analysis
        if html_source:
            ai_insights['source_analysis'] = self.sources.analyze_page_structure(html_source)
        
        # Extract games (using base logic)
        games = self._extract_games_from_snapshot(snapshot_text)
        
        # Debugging analysis if extraction failed
        if not games:
            expected_elements = ['button', 'StaticText', 'team name']
            found_elements = re.findall(r'\b\w+\b', snapshot_text[:500])
            
            ai_insights['debugging_info'] = self.debugger.diagnose_scraping_failure(
                snapshot_text,
                expected_elements,
                found_elements
            )
            self.session_log['debugging_events'].append(ai_insights['debugging_info'])
        else:
            ai_insights['extraction_success'] = True
        
        # Update success rate
        total_attempts = (
            len(self.session_log['performance_metrics']) + 
            len(self.session_log['debugging_events'])
        )
        successful_attempts = len([e for e in self.session_log['debugging_events'] 
                                   if e.get('missing_elements') == []])
        if total_attempts > 0:
            self.session_log['success_rate'] = successful_attempts / total_attempts
        
        return games, ai_insights
    
    def _extract_games_from_snapshot(self, snapshot_text: str) -> List[Dict]:
        """Base extraction logic (from original scraper)"""
        from .chrome_devtools_scraper import ChromeDevToolsOddsExtractor
        extractor = ChromeDevToolsOddsExtractor()
        return extractor.extract_games_from_snapshot(snapshot_text)
    
    def get_session_report(self) -> Dict[str, Any]:
        """Generate comprehensive session report with AI insights"""
        return {
            'session_log': self.session_log,
            'summary': {
                'total_extractions': len(self.session_log['performance_metrics']),
                'success_rate': f"{self.session_log['success_rate']:.1%}",
                'avg_performance_score': self._avg_performance_score(),
                'common_issues': self._identify_common_issues()
            },
            'recommendations': self._generate_session_recommendations()
        }
    
    def _avg_performance_score(self) -> float:
        """Calculate average performance score"""
        if not self.session_log['performance_metrics']:
            return 0.0
        scores = [m.get('performance_score', 0) 
                 for m in self.session_log['performance_metrics']]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _identify_common_issues(self) -> List[str]:
        """Identify most common issues across session"""
        issues = []
        for event in self.session_log['debugging_events']:
            for cause in event.get('potential_causes', []):
                issues.append(cause.get('cause', 'Unknown'))
        
        # Return unique issues
        return list(set(issues))[:5]
    
    def _generate_session_recommendations(self) -> List[Dict[str, str]]:
        """Generate recommendations based on session data"""
        recommendations = []
        
        # Performance recommendations
        avg_score = self._avg_performance_score()
        if avg_score < 70:
            recommendations.append({
                'type': 'performance',
                'priority': 'high',
                'message': f"Average performance score is {avg_score:.0f}/100",
                'action': "Review slow requests and consider request blocking"
            })
        
        # Success rate recommendations
        if self.session_log['success_rate'] < 0.8:
            recommendations.append({
                'type': 'reliability',
                'priority': 'high',
                'message': f"Success rate is {self.session_log['success_rate']:.1%}",
                'action': "Review wait strategies and element selectors"
            })
        
        return recommendations


def save_ai_insights_report(insights: Dict[str, Any], output_path: Path) -> None:
    """Save AI insights to JSON file for analysis"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(insights, f, indent=2, default=str)
    logger.info(f"AI insights saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    extractor = EnhancedChromeDevToolsOddsExtractor()
    
    sample_snapshot = """
uid=1_73 StaticText "109"
uid=1_74 StaticText " "
uid=1_75 StaticText "Las Vegas Raiders"
uid=1_76 button "+9 -110"
uid=1_77 button "+380"
uid=1_78 button "O 43 -110"
    """
    
    sample_metrics = {
        'page_load_time': 1200,
        'network_requests': 45,
        'javascript_errors': []
    }
    
    games, insights = extractor.extract_with_ai_assistance(
        sample_snapshot,
        performance_metrics=sample_metrics
    )
    
    print(f"Extracted {len(games)} games")
    print(f"Performance score: {insights['performance_analysis'].get('performance_score', 0)}/100")
    print(f"\nRecommendations:")
    for rec in insights.get('recommendations', []):
        print(f"  - {rec.get('type')}: {rec.get('benefit')}")

