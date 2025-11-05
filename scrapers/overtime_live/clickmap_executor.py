"""
Clickmap YAML Executor for Playwright-based scraping.

Reads YAML clickmaps and executes authentication, navigation, and extraction flows.
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


class ClickmapExecutor:
    """
    Executes clickmap YAML files with Playwright.
    
    Handles:
    - Authentication flows
    - Multi-step navigation (flows)
    - Data extraction
    - Fallback selectors
    """
    
    def __init__(self, clickmap_path: str):
        """
        Initialize executor with a clickmap YAML file.
        
        Args:
            clickmap_path: Path to the YAML clickmap file
        """
        self.clickmap_path = Path(clickmap_path)
        self.config = self._load_clickmap()
        self.logger = None  # Set by spider
    
    def _load_clickmap(self) -> Dict[str, Any]:
        """Load and parse YAML clickmap."""
        with open(self.clickmap_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _log(self, level: str, message: str):
        """Log message through spider logger if available."""
        if self.logger:
            getattr(self.logger, level.lower())(message)
    
    def _get_env_value(self, env_key: str) -> Optional[str]:
        """Get value from environment variable."""
        return os.getenv(env_key)
    
    async def _execute_step(self, page: Page, step: Dict[str, Any]) -> bool:
        """
        Execute a single clickmap step.
        
        Args:
            page: Playwright page
            step: Step definition from YAML
            
        Returns:
            True if step succeeded, False otherwise
        """
        try:
            # Handle different step types
            if 'click_any' in step:
                return await self._click_any(page, step['click_any'])
            
            elif 'fill_first' in step:
                return await self._fill_first(page, step['fill_first'])
            
            elif 'wait_for' in step:
                ms = step['wait_for'].get('ms', 1000)
                await page.wait_for_timeout(ms)
                return True
            
            elif 'wait_for_selector' in step:
                selector = step['wait_for_selector']
                timeout = step.get('timeout', 5000)
                await page.wait_for_selector(selector, timeout=timeout)
                return True
            
            else:
                self._log('warning', f"Unknown step type: {step}")
                return False
                
        except Exception as e:
            self._log('error', f"Step failed: {e}")
            return False
    
    async def _click_any(self, page: Page, selectors: List[str]) -> bool:
        """
        Try clicking any of the provided selectors.
        
        Args:
            page: Playwright page
            selectors: List of selector strings to try
            
        Returns:
            True if any click succeeded
        """
        for selector in selectors:
            try:
                # Parse selector type
                if selector.startswith('role='):
                    # role=button[name="Login"]
                    await page.click(selector, timeout=2000)
                    self._log('info', f"Clicked: {selector}")
                    return True
                    
                elif selector.startswith('text='):
                    # text=/\bLogin\b/i
                    await page.click(selector, timeout=2000)
                    self._log('info', f"Clicked: {selector}")
                    return True
                    
                elif selector.startswith('css='):
                    # css=.btn.btn-login
                    css_sel = selector[4:]
                    await page.click(css_sel, timeout=2000)
                    self._log('info', f"Clicked: {css_sel}")
                    return True
                    
                else:
                    # Assume it's a CSS selector
                    await page.click(selector, timeout=2000)
                    self._log('info', f"Clicked: {selector}")
                    return True
                    
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                self._log('debug', f"Selector {selector} failed: {e}")
                continue
        
        self._log('warning', f"None of the selectors worked: {selectors}")
        return False
    
    async def _fill_first(self, page: Page, fill_config: Dict[str, Any]) -> bool:
        """
        Fill the first matching selector with a value.
        
        Args:
            page: Playwright page
            fill_config: Fill configuration with selector_any and value_env
            
        Returns:
            True if fill succeeded
        """
        selectors = fill_config.get('selector_any', [])
        value_env = fill_config.get('value_env')
        
        if value_env:
            value = self._get_env_value(value_env)
            if not value:
                self._log('warning', f"Environment variable {value_env} not set")
                return False
        else:
            value = fill_config.get('value', '')
        
        for selector in selectors:
            try:
                await page.fill(selector, value, timeout=2000)
                self._log('info', f"Filled {selector}")
                return True
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                self._log('debug', f"Fill failed for {selector}: {e}")
                continue
        
        self._log('warning', f"Could not fill any selector with {value_env}")
        return False
    
    async def authenticate(self, page: Page) -> bool:
        """
        Execute authentication flow from clickmap.
        
        Args:
            page: Playwright page
            
        Returns:
            True if authentication succeeded
        """
        auth_config = self.config.get('auth')
        if not auth_config:
            self._log('info', "No authentication configured")
            return True
        
        steps = auth_config.get('steps', [])
        self._log('info', f"Executing {len(steps)} authentication steps...")
        
        for i, step in enumerate(steps, 1):
            self._log('debug', f"Auth step {i}/{len(steps)}")
            success = await self._execute_step(page, step)
            if not success:
                self._log('warning', f"Auth step {i} failed, continuing...")
        
        return True
    
    async def execute_flow(self, page: Page, flow_name: Optional[str] = None) -> bool:
        """
        Execute a navigation flow from clickmap.
        
        Args:
            page: Playwright page
            flow_name: Name of flow to execute (uses active_flow if None)
            
        Returns:
            True if flow succeeded
        """
        if not flow_name:
            flow_name = self.config.get('active_flow')
        
        if not flow_name:
            self._log('warning', "No flow specified")
            return False
        
        flows = self.config.get('flows', {})
        flow = flows.get(flow_name)
        
        if not flow:
            self._log('error', f"Flow '{flow_name}' not found")
            return False
        
        # Handle flow inheritance (extends)
        if 'extends' in flow:
            parent_name = flow['extends']
            parent_flow = flows.get(parent_name)
            if parent_flow:
                self._log('info', f"Executing parent flow: {parent_name}")
                await self.execute_flow(page, parent_name)
        
        # Execute flow steps
        steps = flow.get('steps', [])
        self._log('info', f"Executing flow '{flow_name}' with {len(steps)} steps...")
        
        for i, step in enumerate(steps, 1):
            self._log('debug', f"Flow step {i}/{len(steps)}")
            success = await self._execute_step(page, step)
            if not success:
                self._log('warning', f"Flow step {i} failed, continuing...")
        
        return True
    
    async def extract_data(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract data from page using clickmap extraction rules.
        
        Args:
            page: Playwright page
            
        Returns:
            List of extracted game/event dictionaries
        """
        extract_config = self.config.get('extract', {})
        if not extract_config:
            self._log('warning', "No extraction config found")
            return []
        
        row_selector = extract_config.get('row_selector', '').strip()
        if not row_selector:
            self._log('error', "No row_selector defined")
            return []
        
        # Get all row elements
        rows = await page.query_selector_all(row_selector)
        self._log('info', f"Found {len(rows)} game rows")
        
        if not rows:
            return []
        
        # Extract fields from each row
        fields = extract_config.get('fields', {})
        meta = extract_config.get('meta', {})
        results = []
        
        for idx, row in enumerate(rows):
            try:
                data = await self._extract_row(row, fields)
                
                # Add metadata
                data['_meta'] = {
                    'book': meta.get('book', 'unknown'),
                    'league': meta.get('league', 'unknown'),
                    'scope': meta.get('scope_from_flow', {}).get(
                        self.config.get('active_flow'), 'GAME'
                    ),
                    'liveplus': meta.get('liveplus', False)
                }
                
                results.append(data)
                
            except Exception as e:
                self._log('error', f"Failed to extract row {idx}: {e}")
                continue
        
        return results
    
    async def _extract_row(self, row, fields: Dict[str, str]) -> Dict[str, Any]:
        """Extract fields from a single row element."""
        data = {}
        
        for field_name, selector_spec in fields.items():
            try:
                # Set a timeout for each field extraction
                value = await asyncio.wait_for(
                    self._extract_field(row, selector_spec),
                    timeout=2.0  # 2 second max per field
                )
                data[field_name] = value
            except asyncio.TimeoutError:
                self._log('debug', f"Field {field_name} timed out")
                data[field_name] = None
            except Exception as e:
                self._log('debug', f"Field {field_name} extraction failed: {e}")
                data[field_name] = None
        
        return data
    
    async def _extract_field(self, element, selector_spec: str) -> Optional[str]:
        """
        Extract a field using selector specification.
        
        Spec format: 'css:selector ::textone' or 'css:selector ::textall'
        """
        if not selector_spec:
            return None
        
        parts = selector_spec.split('::')
        selector = parts[0].strip()
        extract_mode = parts[1].strip() if len(parts) > 1 else 'textone'
        
        # Remove 'css:any' prefix if present
        if selector.startswith('css:any'):
            selector = selector[7:].strip()
        elif selector.startswith('css:'):
            selector = selector[4:].strip()
        
        # Get element(s)
        if extract_mode == 'textall':
            elements = await element.query_selector_all(selector)
            texts = []
            for el in elements:
                text = await el.text_content()
                if text:
                    texts.append(text.strip())
            return ' | '.join(texts) if texts else None
        else:
            el = await element.query_selector(selector)
            if el:
                text = await el.text_content()
                return text.strip() if text else None
        
        return None

