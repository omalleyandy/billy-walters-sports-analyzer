#!/usr/bin/env python3
"""
Chrome DevTools Protocol (CDP) Monitor for Performance and Network Analysis

Provides Chrome DevTools Protocol integration for monitoring:
- Network requests and responses
- Performance metrics (load times, request counts, response sizes)
- WebSocket connections
- Resource loading

Usage:
    # In a Playwright scraper:
    from data.chrome_devtools_monitor import ChromeDevToolsMonitor
    
    monitor = ChromeDevToolsMonitor(page)
    await monitor.start_monitoring()
    # ... do scraping ...
    metrics = await monitor.stop_monitoring()
    monitor.save_metrics("output/performance.json")
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

logger = logging.getLogger(__name__)


class ChromeDevToolsMonitor:
    """
    Chrome DevTools Protocol monitor for Playwright pages.
    
    Tracks network activity, performance metrics, and resource loading.
    """

    def __init__(self, page: Page, enable_network: bool = True, enable_performance: bool = True):
        """
        Initialize Chrome DevTools monitor.

        Args:
            page: Playwright page object
            enable_network: Enable network request tracking
            enable_performance: Enable performance metrics collection
        """
        self.page = page
        self.enable_network = enable_network
        self.enable_performance = enable_performance
        
        # Data storage
        self.requests: List[Dict[str, Any]] = []
        self.responses: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.network_metrics: Dict[str, Any] = {
            "total_requests": 0,
            "total_bytes": 0,
            "requests_by_type": {},
            "requests_by_domain": {},
        }
        
        # Start time for monitoring
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    async def start_monitoring(self) -> None:
        """Start monitoring network and performance."""
        self.start_time = datetime.now()
        
        if self.enable_network:
            # Set up network request/response handlers
            self.page.on("request", self._on_request)
            self.page.on("response", self._on_response)
            self.page.on("requestfailed", self._on_request_failed)
        
        if self.enable_performance:
            # Enable performance tracking
            await self.page.context.tracing.start(screenshots=False, snapshots=False)
        
        logger.info("Chrome DevTools monitoring started")

    async def stop_monitoring(self) -> Dict[str, Any]:
        """
        Stop monitoring and return collected metrics.

        Returns:
            Dictionary with all collected metrics
        """
        self.end_time = datetime.now()
        
        # Calculate duration
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        
        # Collect performance metrics if enabled
        if self.enable_performance:
            await self._collect_performance_metrics()
        
        # Compile final metrics
        metrics = {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "network": {
                **self.network_metrics,
                "request_count": len(self.requests),
                "response_count": len(self.responses),
            },
            "performance": self.performance_metrics,
            "requests": self.requests[:100],  # Limit to first 100 requests
            "responses": self.responses[:100],  # Limit to first 100 responses
        }
        
        logger.info(f"Monitoring stopped. Collected {len(self.requests)} requests, {len(self.responses)} responses")
        
        return metrics

    def _on_request(self, request) -> None:
        """Handle network request event."""
        request_data = {
            "url": request.url,
            "method": request.method,
            "headers": request.headers,
            "post_data": request.post_data,
            "resource_type": request.resource_type,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.requests.append(request_data)
        self.network_metrics["total_requests"] += 1
        
        # Track by resource type
        resource_type = request.resource_type
        self.network_metrics["requests_by_type"][resource_type] = (
            self.network_metrics["requests_by_type"].get(resource_type, 0) + 1
        )
        
        # Track by domain
        try:
            from urllib.parse import urlparse
            domain = urlparse(request.url).netloc
            self.network_metrics["requests_by_domain"][domain] = (
                self.network_metrics["requests_by_domain"].get(domain, 0) + 1
            )
        except Exception:
            pass

    def _on_response(self, response) -> None:
        """Handle network response event."""
        response_data = {
            "url": response.url,
            "status": response.status,
            "status_text": response.status_text,
            "headers": response.headers,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Get response size if available
        try:
            content_length = response.headers.get("content-length")
            if content_length:
                response_data["size_bytes"] = int(content_length)
                self.network_metrics["total_bytes"] += int(content_length)
        except Exception:
            pass
        
        self.responses.append(response_data)

    def _on_request_failed(self, request) -> None:
        """Handle failed request event."""
        failure_data = {
            "url": request.url,
            "method": request.method,
            "failure_text": request.failure if hasattr(request, "failure") else None,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.requests.append({**failure_data, "failed": True})

    async def _collect_performance_metrics(self) -> None:
        """Collect performance metrics from browser."""
        try:
            # Get performance metrics via CDP
            cdp_session = await self.page.context.new_cdp_session(self.page)
            
            # Get performance timing
            performance_timing = await cdp_session.send("Performance.getMetrics")
            
            self.performance_metrics = {
                "metrics": performance_timing.get("metrics", []),
            }
            
            await cdp_session.detach()
        except Exception as e:
            logger.warning(f"Could not collect performance metrics: {e}")
            self.performance_metrics = {"error": str(e)}

    def save_metrics(self, filepath: str | Path) -> Path:
        """
        Save collected metrics to JSON file.

        Args:
            filepath: Path to save metrics

        Returns:
            Path to saved file
        """
        metrics = {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0,
            "network": {
                **self.network_metrics,
                "request_count": len(self.requests),
                "response_count": len(self.responses),
            },
            "performance": self.performance_metrics,
            "sample_requests": self.requests[:50],  # Save sample of requests
            "sample_responses": self.responses[:50],  # Save sample of responses
        }
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics saved to {filepath}")
        return filepath

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of collected metrics.

        Returns:
            Dictionary with summary statistics
        """
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        
        return {
            "duration_seconds": duration,
            "total_requests": len(self.requests),
            "total_responses": len(self.responses),
            "total_bytes": self.network_metrics.get("total_bytes", 0),
            "requests_by_type": self.network_metrics.get("requests_by_type", {}),
            "top_domains": dict(
                sorted(
                    self.network_metrics.get("requests_by_domain", {}).items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:10]
            ),
        }
