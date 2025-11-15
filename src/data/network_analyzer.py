#!/usr/bin/env python3
"""
Network Request Analyzer for Chrome DevTools Data

Analyzes network requests captured by Chrome DevTools monitor:
- Identifies API endpoints
- Detects request patterns
- Identifies rate limits
- Detects performance bottlenecks
- Logs request/response data

Usage:
    from data.network_analyzer import NetworkAnalyzer
    
    analyzer = NetworkAnalyzer(metrics)
    api_endpoints = analyzer.find_api_endpoints()
    bottlenecks = analyzer.find_bottlenecks()
    analyzer.generate_report("output/network_analysis.json")
"""

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class NetworkAnalyzer:
    """
    Analyzer for network request data from Chrome DevTools monitor.
    
    Identifies patterns, bottlenecks, and API endpoints.
    """

    def __init__(self, metrics: Dict[str, Any]):
        """
        Initialize network analyzer.

        Args:
            metrics: Metrics dictionary from ChromeDevToolsMonitor
        """
        self.metrics = metrics
        self.requests = metrics.get("requests", [])
        self.responses = metrics.get("responses", [])
        self.network_metrics = metrics.get("network", {})

    def find_api_endpoints(self) -> List[Dict[str, Any]]:
        """
        Identify API endpoints from network requests.

        Returns:
            List of API endpoint dictionaries
        """
        api_endpoints = []
        
        for request in self.requests:
            url = request.get("url", "")
            method = request.get("method", "GET")
            
            # Identify API endpoints (common patterns)
            is_api = (
                "/api/" in url
                or ".json" in url
                or "/json/" in url
                or url.endswith("/json")
                or "application/json" in request.get("headers", {}).get("accept", "")
            )
            
            if is_api:
                parsed = urlparse(url)
                api_endpoints.append({
                    "url": url,
                    "method": method,
                    "domain": parsed.netloc,
                    "path": parsed.path,
                    "query": parsed.query,
                })
        
        # Deduplicate
        seen = set()
        unique_endpoints = []
        for endpoint in api_endpoints:
            key = (endpoint["method"], endpoint["url"])
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(endpoint)
        
        return unique_endpoints

    def find_rate_limits(self) -> List[Dict[str, Any]]:
        """
        Identify potential rate limiting patterns.

        Returns:
            List of rate limit indicators
        """
        rate_limits = []
        
        # Check for 429 (Too Many Requests) responses
        status_429 = [r for r in self.responses if r.get("status") == 429]
        if status_429:
            rate_limits.append({
                "type": "429_status",
                "count": len(status_429),
                "urls": [r["url"] for r in status_429[:5]],
            })
        
        # Check for retry-after headers
        retry_after = []
        for response in self.responses:
            headers = response.get("headers", {})
            if "retry-after" in headers:
                retry_after.append({
                    "url": response["url"],
                    "retry_after": headers["retry-after"],
                })
        
        if retry_after:
            rate_limits.append({
                "type": "retry_after_header",
                "count": len(retry_after),
                "examples": retry_after[:5],
            })
        
        # Check for frequent requests to same domain
        domain_counts = Counter()
        for request in self.requests:
            try:
                domain = urlparse(request["url"]).netloc
                domain_counts[domain] += 1
            except Exception:
                pass
        
        # Domains with >50 requests might indicate rate limiting issues
        high_frequency_domains = [
            {"domain": domain, "count": count}
            for domain, count in domain_counts.items()
            if count > 50
        ]
        
        if high_frequency_domains:
            rate_limits.append({
                "type": "high_frequency",
                "domains": sorted(high_frequency_domains, key=lambda x: x["count"], reverse=True)[:10],
            })
        
        return rate_limits

    def find_bottlenecks(self) -> List[Dict[str, Any]]:
        """
        Identify performance bottlenecks.

        Returns:
            List of bottleneck indicators
        """
        bottlenecks = []
        
        # Large responses (>1MB)
        large_responses = [
            r for r in self.responses
            if r.get("size_bytes", 0) > 1_000_000
        ]
        
        if large_responses:
            bottlenecks.append({
                "type": "large_responses",
                "count": len(large_responses),
                "examples": [
                    {"url": r["url"], "size_mb": r.get("size_bytes", 0) / 1_000_000}
                    for r in large_responses[:5]
                ],
            })
        
        # Slow responses (>5 seconds) - would need timing data
        # For now, check response count vs duration
        duration = self.metrics.get("duration_seconds", 0)
        request_count = len(self.requests)
        
        if duration > 0 and request_count > 0:
            requests_per_second = request_count / duration
            if requests_per_second < 1:
                bottlenecks.append({
                    "type": "slow_request_rate",
                    "requests_per_second": requests_per_second,
                    "total_requests": request_count,
                    "duration_seconds": duration,
                })
        
        # Failed requests
        failed_requests = [r for r in self.requests if r.get("failed")]
        if failed_requests:
            bottlenecks.append({
                "type": "failed_requests",
                "count": len(failed_requests),
                "examples": [{"url": r["url"], "method": r.get("method")} for r in failed_requests[:5]],
            })
        
        return bottlenecks

    def analyze_request_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns in network requests.

        Returns:
            Dictionary with pattern analysis
        """
        patterns = {
            "request_methods": Counter(),
            "resource_types": Counter(),
            "status_codes": Counter(),
            "domains": Counter(),
        }
        
        for request in self.requests:
            patterns["request_methods"][request.get("method", "UNKNOWN")] += 1
            patterns["resource_types"][request.get("resource_type", "unknown")] += 1
        
        for response in self.responses:
            patterns["status_codes"][response.get("status", 0)] += 1
            try:
                domain = urlparse(response["url"]).netloc
                patterns["domains"][domain] += 1
            except Exception:
                pass
        
        return {
            "request_methods": dict(patterns["request_methods"]),
            "resource_types": dict(patterns["resource_types"]),
            "status_codes": dict(patterns["status_codes"]),
            "top_domains": dict(patterns["domains"].most_common(10)),
        }

    def generate_report(self, filepath: str | Path) -> Path:
        """
        Generate comprehensive network analysis report.

        Args:
            filepath: Path to save report

        Returns:
            Path to saved file
        """
        report = {
            "summary": {
                "total_requests": len(self.requests),
                "total_responses": len(self.responses),
                "duration_seconds": self.metrics.get("duration_seconds", 0),
                "total_bytes": self.network_metrics.get("total_bytes", 0),
            },
            "api_endpoints": self.find_api_endpoints(),
            "rate_limits": self.find_rate_limits(),
            "bottlenecks": self.find_bottlenecks(),
            "patterns": self.analyze_request_patterns(),
            "generated_at": datetime.now().isoformat(),
        }
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Network analysis report saved to {filepath}")
        return filepath

    def print_summary(self) -> None:
        """Print summary of analysis to console."""
        print("\n" + "=" * 70)
        print("NETWORK ANALYSIS SUMMARY")
        print("=" * 70)
        
        print(f"\nTotal Requests: {len(self.requests)}")
        print(f"Total Responses: {len(self.responses)}")
        print(f"Duration: {self.metrics.get('duration_seconds', 0):.2f} seconds")
        print(f"Total Bytes: {self.network_metrics.get('total_bytes', 0) / 1024 / 1024:.2f} MB")
        
        # API Endpoints
        api_endpoints = self.find_api_endpoints()
        if api_endpoints:
            print(f"\nAPI Endpoints Found: {len(api_endpoints)}")
            for endpoint in api_endpoints[:5]:
                print(f"  {endpoint['method']} {endpoint['url'][:80]}")
        
        # Rate Limits
        rate_limits = self.find_rate_limits()
        if rate_limits:
            print("\nRate Limit Indicators:")
            for indicator in rate_limits:
                print(f"  {indicator['type']}: {indicator.get('count', 'N/A')}")
        
        # Bottlenecks
        bottlenecks = self.find_bottlenecks()
        if bottlenecks:
            print("\nPerformance Bottlenecks:")
            for bottleneck in bottlenecks:
                print(f"  {bottleneck['type']}: {bottleneck.get('count', 'N/A')}")
        
        print("\n" + "=" * 70)
