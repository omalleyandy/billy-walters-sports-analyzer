"""
Comprehensive backtest script for overtime.ag Playwright scraper locators.

This script validates that our scraper can correctly identify and extract data from all
key UI elements on the overtime.ag sports betting page.

Tests cover:
- Login elements
- Sport selection (NFL, College FB)
- Period buttons (Game, 1st Half, etc.)
- Game lines container
- Date/time elements
- Team information (rotation numbers, names, logos)
- Market buttons (Spread, Moneyline, Totals)
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from playwright.async_api import (
    async_playwright,
)


class LocatorBacktestResult:
    """Stores results for a locator test."""

    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.locators = []
        self.results = []
        self.best_locator = None
        self.extraction_result = None

    def add_locator(
        self,
        locator_type: str,
        locator_str: str,
        found: bool,
        count: int = 0,
        error: str = None,
    ):
        """Add a locator test result."""
        self.locators.append(locator_str)
        self.results.append(
            {
                "type": locator_type,
                "locator": locator_str,
                "found": found,
                "count": count,
                "error": error,
            }
        )

        # Track the best working locator
        if found and count > 0 and not self.best_locator:
            self.best_locator = locator_str

    def set_extraction_result(self, data):
        """Set the extracted data."""
        self.extraction_result = data

    def is_successful(self) -> bool:
        """Check if at least one locator worked."""
        return any(r["found"] and r["count"] > 0 for r in self.results)


class OvertimeLocatorBacktest:
    """Comprehensive backtest for overtime.ag locators."""

    def __init__(self):
        self.results = []
        self.page = None
        self.context = None
        self.browser = None

    async def setup(self):
        """Initialize Playwright and navigate to overtime.ag."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = await self.context.new_page()

        # Enable console logging
        self.page.on("console", lambda msg: print(f"Browser: {msg.text}"))

        return self.page

    async def teardown(self):
        """Clean up resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def login(self, username: str, password: str) -> bool:
        """Test login locators and perform login."""
        print("\n=== Testing Login Locators ===")

        try:
            await self.page.goto(
                "https://www.overtime.ag/sports/", wait_until="domcontentloaded"
            )
            await self.page.wait_for_timeout(3000)

            # Test Customer ID input
            customer_id_result = LocatorBacktestResult("Customer ID Input", "Login")
            customer_id_locators = [
                ("getByRole", "page.getByRole('textbox', { name: 'Customer Id' })"),
                ("getByLabel", "page.getByLabel('Customer Id')"),
                ("id", "page.locator('#txtLoginName')"),
            ]

            for loc_type, loc_str in customer_id_locators:
                try:
                    if loc_type == "getByRole":
                        locator = self.page.get_by_role("textbox", name="Customer Id")
                    elif loc_type == "getByLabel":
                        locator = self.page.get_by_label("Customer Id")
                    elif loc_type == "id":
                        locator = self.page.locator("#txtLoginName")

                    count = await locator.count()
                    visible = await locator.is_visible() if count > 0 else False
                    customer_id_result.add_locator(loc_type, loc_str, visible, count)
                    print(f"  [OK] {loc_str}: found={visible}, count={count}")
                except Exception as e:
                    customer_id_result.add_locator(loc_type, loc_str, False, 0, str(e))
                    print(f"  [X] {loc_str}: {e}")

            self.results.append(customer_id_result)

            # Test Password input
            password_result = LocatorBacktestResult("Password Input", "Login")
            password_locators = [
                ("getByRole", "page.getByRole('textbox', { name: 'Password' })"),
                ("getByLabel", "page.getByLabel('Password')"),
                ("id", "page.locator('#txtPassword')"),
            ]

            for loc_type, loc_str in password_locators:
                try:
                    if loc_type == "getByRole":
                        locator = self.page.get_by_role("textbox", name="Password")
                    elif loc_type == "getByLabel":
                        locator = self.page.get_by_label("Password")
                    elif loc_type == "id":
                        locator = self.page.locator("#txtPassword")

                    count = await locator.count()
                    visible = await locator.is_visible() if count > 0 else False
                    password_result.add_locator(loc_type, loc_str, visible, count)
                    print(f"  [OK] {loc_str}: found={visible}, count={count}")
                except Exception as e:
                    password_result.add_locator(loc_type, loc_str, False, 0, str(e))
                    print(f"  [X] {loc_str}: {e}")

            self.results.append(password_result)

            # Test Login button
            login_btn_result = LocatorBacktestResult("Login Button", "Login")
            login_btn_locators = [
                ("getByRole", "page.getByRole('button', { name: 'Login' })"),
                ("id", "page.locator('#btnDoLogin')"),
                ("text", "page.get_by_text('Login')"),
            ]

            for loc_type, loc_str in login_btn_locators:
                try:
                    if loc_type == "getByRole":
                        locator = self.page.get_by_role("button", name="Login")
                    elif loc_type == "id":
                        locator = self.page.locator("#btnDoLogin")
                    elif loc_type == "text":
                        locator = self.page.get_by_text("Login")

                    count = await locator.count()
                    visible = await locator.is_visible() if count > 0 else False
                    login_btn_result.add_locator(loc_type, loc_str, visible, count)
                    print(f"  [OK] {loc_str}: found={visible}, count={count}")
                except Exception as e:
                    login_btn_result.add_locator(loc_type, loc_str, False, 0, str(e))
                    print(f"  [X] {loc_str}: {e}")

            self.results.append(login_btn_result)

            # Perform actual login
            if customer_id_result.best_locator and password_result.best_locator:
                await self.page.fill("#txtLoginName", username)
                await self.page.fill("#txtPassword", password)
                await self.page.click("#btnDoLogin")
                await self.page.wait_for_timeout(3000)
                print("\n[OK] Login completed")
                return True
            else:
                print("\n[X] Cannot proceed with login - locators not found")
                return False

        except Exception as e:
            print(f"\n[X] Login failed: {e}")
            return False

    async def test_sport_selection_locators(self):
        """Test sport selection locators (NFL, College FB)."""
        print("\n=== Testing Sport Selection Locators ===")

        # Test NFL locators
        nfl_result = LocatorBacktestResult("NFL Sport Selection", "Sport Selection")
        nfl_locators = [
            ("getByLabel", "page.getByLabel('NFL-Game/1H/2H/Qrts')"),
            (
                "getByLabel_exact",
                "page.getByLabel('NFL-Game/1H/2H/Qrts', { exact: true })",
            ),
            ("getByText", "page.getByText('NFL-Game/1H/2H/Qrts')"),
            (
                "getByText_exact",
                "page.getByText('NFL-Game/1H/2H/Qrts', { exact: true })",
            ),
            (
                "locator_hasText",
                "page.locator('label:has-text(\"NFL-Game/1H/2H/Qrts\")')",
            ),
            (
                "xpath",
                "page.locator(\"//label[normalize-space()='NFL-Game/1H/2H/Qrts']\")",
            ),
        ]

        for loc_type, loc_str in nfl_locators:
            try:
                if loc_type == "getByLabel":
                    locator = self.page.get_by_label("NFL-Game/1H/2H/Qrts")
                elif loc_type == "getByLabel_exact":
                    locator = self.page.get_by_label("NFL-Game/1H/2H/Qrts", exact=True)
                elif loc_type == "getByText":
                    locator = self.page.get_by_text("NFL-Game/1H/2H/Qrts")
                elif loc_type == "getByText_exact":
                    locator = self.page.get_by_text("NFL-Game/1H/2H/Qrts", exact=True)
                elif loc_type == "locator_hasText":
                    locator = self.page.locator('label:has-text("NFL-Game/1H/2H/Qrts")')
                elif loc_type == "xpath":
                    locator = self.page.locator(
                        "//label[normalize-space()='NFL-Game/1H/2H/Qrts']"
                    )

                count = await locator.count()
                nfl_result.add_locator(loc_type, loc_str, count > 0, count)
                print(f"  {'[OK]' if count > 0 else '[X]'} {loc_str}: count={count}")
            except Exception as e:
                nfl_result.add_locator(loc_type, loc_str, False, 0, str(e))
                print(f"  [X] {loc_str}: {e}")

        self.results.append(nfl_result)

        # Test College FB locators
        cfb_result = LocatorBacktestResult(
            "College FB Sport Selection", "Sport Selection"
        )
        cfb_locators = [
            ("getByLabel", "page.getByLabel('COLLEGE FB(1H/2H/Q)')"),
            (
                "getByLabel_exact",
                "page.getByLabel('COLLEGE FB(1H/2H/Q)', { exact: true })",
            ),
            ("getByText", "page.getByText('COLLEGE FB(1H/2H/Q)')"),
            (
                "getByText_exact",
                "page.getByText('COLLEGE FB(1H/2H/Q)', { exact: true })",
            ),
            (
                "locator_hasText",
                "page.locator('label:has-text(\"COLLEGE FB(1H/2H/Q)\")')",
            ),
            (
                "xpath",
                "page.locator(\"//label[normalize-space()='COLLEGE FB(1H/2H/Q)']\")",
            ),
        ]

        for loc_type, loc_str in cfb_locators:
            try:
                if loc_type == "getByLabel":
                    locator = self.page.get_by_label("COLLEGE FB(1H/2H/Q)")
                elif loc_type == "getByLabel_exact":
                    locator = self.page.get_by_label("COLLEGE FB(1H/2H/Q)", exact=True)
                elif loc_type == "getByText":
                    locator = self.page.get_by_text("COLLEGE FB(1H/2H/Q)")
                elif loc_type == "getByText_exact":
                    locator = self.page.get_by_text("COLLEGE FB(1H/2H/Q)", exact=True)
                elif loc_type == "locator_hasText":
                    locator = self.page.locator('label:has-text("COLLEGE FB(1H/2H/Q)")')
                elif loc_type == "xpath":
                    locator = self.page.locator(
                        "//label[normalize-space()='COLLEGE FB(1H/2H/Q)']"
                    )

                count = await locator.count()
                cfb_result.add_locator(loc_type, loc_str, count > 0, count)
                print(f"  {'[OK]' if count > 0 else '[X]'} {loc_str}: count={count}")
            except Exception as e:
                cfb_result.add_locator(loc_type, loc_str, False, 0, str(e))
                print(f"  [X] {loc_str}: {e}")

        self.results.append(cfb_result)

    async def test_period_buttons(self):
        """Test period selection buttons (Game, 1st Half, etc.)."""
        print("\n=== Testing Period Button Locators ===")

        # Test Game button
        game_result = LocatorBacktestResult("Game Period Button", "Period Selection")
        game_locators = [
            ("getByRole", "page.getByRole('button', { name: 'Game' })"),
            ("getByRole_regex", "page.getByRole('button', { name: /Game/i })"),
            ("locator_hasText", "page.locator('button:has-text(\"GAME\")')"),
            ("xpath", "page.locator(\"//button[normalize-space()='Game']\")"),
        ]

        for loc_type, loc_str in game_locators:
            try:
                if loc_type == "getByRole":
                    locator = self.page.get_by_role("button", name="Game")
                elif loc_type == "getByRole_regex":
                    locator = self.page.get_by_role("button").filter(has_text="Game")
                elif loc_type == "locator_hasText":
                    locator = self.page.locator('button:has-text("GAME")')
                elif loc_type == "xpath":
                    locator = self.page.locator("//button[normalize-space()='Game']")

                count = await locator.count()
                game_result.add_locator(loc_type, loc_str, count > 0, count)
                print(f"  {'[OK]' if count > 0 else '[X]'} {loc_str}: count={count}")
            except Exception as e:
                game_result.add_locator(loc_type, loc_str, False, 0, str(e))
                print(f"  [X] {loc_str}: {e}")

        self.results.append(game_result)

        # Test 1st Half button
        half_result = LocatorBacktestResult(
            "1st Half Period Button", "Period Selection"
        )
        half_locators = [
            ("getByRole", "page.getByRole('button', { name: '1st Half' })"),
            ("locator_hasText", "page.locator('button:has-text(\"1ST HALF\")')"),
            ("xpath", "page.locator(\"//button[normalize-space()='1st Half']\")"),
            ("css", "page.locator(\"div[id='GameLines'] button:nth-child(2)\")"),
        ]

        for loc_type, loc_str in half_locators:
            try:
                if loc_type == "getByRole":
                    locator = self.page.get_by_role("button", name="1st Half")
                elif loc_type == "locator_hasText":
                    locator = self.page.locator('button:has-text("1ST HALF")')
                elif loc_type == "xpath":
                    locator = self.page.locator(
                        "//button[normalize-space()='1st Half']"
                    )
                elif loc_type == "css":
                    locator = self.page.locator(
                        "div[id='GameLines'] button:nth-child(2)"
                    )

                count = await locator.count()
                half_result.add_locator(loc_type, loc_str, count > 0, count)
                print(f"  {'[OK]' if count > 0 else '[X]'} {loc_str}: count={count}")
            except Exception as e:
                half_result.add_locator(loc_type, loc_str, False, 0, str(e))
                print(f"  [X] {loc_str}: {e}")

        self.results.append(half_result)

        # Test Team Totals button
        tt_result = LocatorBacktestResult("Team Totals Button", "Period Selection")
        tt_locators = [
            ("getByRole", "page.getByRole('button', { name: 'TEAM TOTALS' })"),
            ("getByText", "page.getByText('TEAM TOTALS', { exact: true })"),
            ("locator_hasText", "page.locator('button:has-text(\"TEAM TOTALS\")')"),
            ("xpath", "page.locator(\"//button[normalize-space()='TEAM TOTALS']\")"),
        ]

        for loc_type, loc_str in tt_locators:
            try:
                if loc_type == "getByRole":
                    locator = self.page.get_by_role("button", name="TEAM TOTALS")
                elif loc_type == "getByText":
                    locator = self.page.get_by_text("TEAM TOTALS", exact=True)
                elif loc_type == "locator_hasText":
                    locator = self.page.locator('button:has-text("TEAM TOTALS")')
                elif loc_type == "xpath":
                    locator = self.page.locator(
                        "//button[normalize-space()='TEAM TOTALS']"
                    )

                count = await locator.count()
                tt_result.add_locator(loc_type, loc_str, count > 0, count)
                print(f"  {'[OK]' if count > 0 else '[X]'} {loc_str}: count={count}")
            except Exception as e:
                tt_result.add_locator(loc_type, loc_str, False, 0, str(e))
                print(f"  [X] {loc_str}: {e}")

        self.results.append(tt_result)

    async def test_game_container_locators(self):
        """Test game lines container locators."""
        print("\n=== Testing Game Container Locators ===")

        container_result = LocatorBacktestResult("GameLines Container", "Container")
        container_locators = [
            ("id", "page.locator('#GameLines')"),
            ("css", "page.locator('div.inset.page-content.ng-scope')"),
            ("xpath", "page.locator(\"//div[@id='GameLines']\")"),
        ]

        for loc_type, loc_str in container_locators:
            try:
                if loc_type == "id":
                    locator = self.page.locator("#GameLines")
                elif loc_type == "css":
                    locator = self.page.locator("div.inset.page-content.ng-scope")
                elif loc_type == "xpath":
                    locator = self.page.locator("//div[@id='GameLines']")

                count = await locator.count()
                visible = await locator.is_visible() if count > 0 else False
                container_result.add_locator(loc_type, loc_str, visible, count)
                print(
                    f"  {'[OK]' if visible else '[X]'} {loc_str}: visible={visible}, count={count}"
                )
            except Exception as e:
                container_result.add_locator(loc_type, loc_str, False, 0, str(e))
                print(f"  [X] {loc_str}: {e}")

        self.results.append(container_result)

    async def test_game_data_extraction(self):
        """Test extraction of game data (dates, teams, odds)."""
        print("\n=== Testing Game Data Extraction ===")

        # Wait for Angular to render
        await self.page.wait_for_timeout(10000)

        # Test market header locators
        spread_header = LocatorBacktestResult("Spread Header", "Market Headers")
        spread_locators = [
            ("getByText", "page.getByText('Spread', { exact: true })"),
            ("xpath", "page.locator(\"//span[normalize-space()='Spread']\")"),
        ]

        for loc_type, loc_str in spread_locators:
            try:
                if loc_type == "getByText":
                    locator = self.page.get_by_text("Spread", exact=True)
                elif loc_type == "xpath":
                    locator = self.page.locator("//span[normalize-space()='Spread']")

                count = await locator.count()
                spread_header.add_locator(loc_type, loc_str, count > 0, count)
                print(f"  {'[OK]' if count > 0 else '[X]'} {loc_str}: count={count}")
            except Exception as e:
                spread_header.add_locator(loc_type, loc_str, False, 0, str(e))
                print(f"  [X] {loc_str}: {e}")

        self.results.append(spread_header)

        # Test Money Line header
        ml_header = LocatorBacktestResult("Money Line Header", "Market Headers")
        ml_locators = [
            ("getByText", "page.getByText('Money Line', { exact: true })"),
            ("xpath", "page.locator(\"//span[normalize-space()='Money Line']\")"),
        ]

        for loc_type, loc_str in ml_locators:
            try:
                if loc_type == "getByText":
                    locator = self.page.get_by_text("Money Line", exact=True)
                elif loc_type == "xpath":
                    locator = self.page.locator(
                        "//span[normalize-space()='Money Line']"
                    )

                count = await locator.count()
                ml_header.add_locator(loc_type, loc_str, count > 0, count)
                print(f"  {'[OK]' if count > 0 else '[X]'} {loc_str}: count={count}")
            except Exception as e:
                ml_header.add_locator(loc_type, loc_str, False, 0, str(e))
                print(f"  [X] {loc_str}: {e}")

        self.results.append(ml_header)

        # Test Totals header
        totals_header = LocatorBacktestResult("Totals Header", "Market Headers")
        totals_locators = [
            ("getByText", "page.getByText('Totals', { exact: true })"),
            ("xpath", "page.locator(\"//span[normalize-space()='Totals']\")"),
        ]

        for loc_type, loc_str in totals_locators:
            try:
                if loc_type == "getByText":
                    locator = self.page.get_by_text("Totals", exact=True)
                elif loc_type == "xpath":
                    locator = self.page.locator("//span[normalize-space()='Totals']")

                count = await locator.count()
                totals_header.add_locator(loc_type, loc_str, count > 0, count)
                print(f"  {'[OK]' if count > 0 else '[X]'} {loc_str}: count={count}")
            except Exception as e:
                totals_header.add_locator(loc_type, loc_str, False, 0, str(e))
                print(f"  [X] {loc_str}: {e}")

        self.results.append(totals_header)

        # Test team name extraction
        print("\n  Testing team name extraction...")
        team_result = LocatorBacktestResult("Team Names", "Game Data")
        try:
            # Get all text content
            text_content = await self.page.evaluate("document.body.innerText")
            lines = text_content.split("\n")

            # Find team names with rotation numbers
            import re

            teams_found = []
            for line in lines:
                match = re.match(r"^(\d{3,4})\s+(.+)$", line.strip())
                if match:
                    rotation = match.group(1)
                    team = match.group(2)
                    if len(team) >= 3 and not any(c in team for c in ["[*]", "[*]"]):
                        teams_found.append({"rotation": rotation, "team": team})

            team_result.add_locator(
                "text_parsing",
                "document.body.innerText parsing",
                len(teams_found) > 0,
                len(teams_found),
            )
            team_result.set_extraction_result(teams_found[:10])  # Show first 10
            print(f"    [OK] Found {len(teams_found)} teams via text parsing")
            for i, team in enumerate(teams_found[:5]):
                print(f"      {team['rotation']}: {team['team']}")
        except Exception as e:
            team_result.add_locator(
                "text_parsing", "document.body.innerText parsing", False, 0, str(e)
            )
            print(f"    [X] Text parsing failed: {e}")

        self.results.append(team_result)

        # Test button-based odds extraction
        print("\n  Testing button-based odds extraction...")
        odds_result = LocatorBacktestResult("Odds Buttons", "Game Data")

        button_prefixes = {
            "S1": "Away Spread",
            "S2": "Home Spread",
            "M1": "Away Moneyline",
            "M2": "Home Moneyline",
            "L1": "Over",
            "L2": "Under",
        }

        all_buttons = {}
        for prefix, desc in button_prefixes.items():
            try:
                buttons = await self.page.locator(f'button[id^="{prefix}_"]').all()
                all_buttons[prefix] = len(buttons)
                odds_result.add_locator(
                    "button_id",
                    f"button[id^='{prefix}_']",
                    len(buttons) > 0,
                    len(buttons),
                )
                print(
                    f"    {'[OK]' if len(buttons) > 0 else '[X]'} {desc} buttons: {len(buttons)}"
                )

                # Extract first few button values
                if buttons:
                    sample_values = []
                    for btn in buttons[:3]:
                        try:
                            text = await btn.inner_text()
                            sample_values.append(text)
                        except:
                            pass
                    if sample_values:
                        print(f"      Sample values: {', '.join(sample_values)}")
            except Exception as e:
                odds_result.add_locator(
                    "button_id", f"button[id^='{prefix}_']", False, 0, str(e)
                )
                print(f"    [X] {desc} buttons: {e}")

        odds_result.set_extraction_result(all_buttons)
        self.results.append(odds_result)

    def generate_report(self) -> dict:
        """Generate comprehensive backtest report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "successful": sum(1 for r in self.results if r.is_successful()),
                "failed": sum(1 for r in self.results if not r.is_successful()),
            },
            "categories": {},
            "recommendations": [],
        }

        # Group by category
        for result in self.results:
            if result.category not in report["categories"]:
                report["categories"][result.category] = []

            report["categories"][result.category].append(
                {
                    "name": result.name,
                    "successful": result.is_successful(),
                    "best_locator": result.best_locator,
                    "locators_tested": len(result.locators),
                    "working_locators": sum(
                        1 for r in result.results if r["found"] and r["count"] > 0
                    ),
                    "extraction_result": result.extraction_result,
                }
            )

        # Generate recommendations
        for result in self.results:
            if not result.is_successful():
                report["recommendations"].append(
                    f"[WARNING] {result.name}: No working locators found"
                )
            elif result.best_locator:
                working_count = sum(
                    1 for r in result.results if r["found"] and r["count"] > 0
                )
                if working_count == 1:
                    report["recommendations"].append(
                        f"[WARNING] {result.name}: Only 1 working locator (fragile)"
                    )

        return report

    def print_report(self, report: dict):
        """Print formatted backtest report."""
        print("\n" + "=" * 80)
        print("OVERTIME.AG SCRAPER BACKTEST REPORT")
        print("=" * 80)
        print(f"\nTimestamp: {report['timestamp']}")
        print("\nSummary:")
        print(f"  Total Tests: {report['summary']['total_tests']}")
        print(f"  Successful: {report['summary']['successful']} [OK]")
        print(f"  Failed: {report['summary']['failed']} [X]")
        print(
            f"  Success Rate: {report['summary']['successful'] / report['summary']['total_tests'] * 100:.1f}%"
        )

        print("\n" + "-" * 80)
        print("Results by Category:")
        print("-" * 80)

        for category, tests in report["categories"].items():
            print(f"\n{category}:")
            for test in tests:
                status = "[OK]" if test["successful"] else "[X]"
                print(f"  {status} {test['name']}")
                print(f"      Locators tested: {test['locators_tested']}")
                print(f"      Working locators: {test['working_locators']}")
                if test["best_locator"]:
                    print(f"      Best locator: {test['best_locator']}")
                if test["extraction_result"]:
                    print(f"      Extraction result: {test['extraction_result']}")

        if report["recommendations"]:
            print("\n" + "-" * 80)
            print("Recommendations:")
            print("-" * 80)
            for rec in report["recommendations"]:
                print(f"  {rec}")

        print("\n" + "=" * 80)


async def main():
    """Run the comprehensive backtest."""
    # Get credentials from environment (same as spider)
    username = os.getenv("OV_CUSTOMER_ID")
    password = os.getenv("OV_CUSTOMER_PASSWORD") or os.getenv("OV_PASSWORD")

    if not username or not password:
        print(
            "ERROR: OV_CUSTOMER_ID and OV_CUSTOMER_PASSWORD must be set in environment"
        )
        print("Set them in your .env file or export them:")
        print("  export OV_CUSTOMER_ID='your_customer_id'")
        print("  export OV_CUSTOMER_PASSWORD='your_password'")
        sys.exit(1)

    backtest = OvertimeLocatorBacktest()

    try:
        # Setup
        await backtest.setup()

        # Run tests
        await backtest.login(username, password)
        await backtest.test_sport_selection_locators()
        await backtest.test_period_buttons()
        await backtest.test_game_container_locators()
        await backtest.test_game_data_extraction()

        # Generate and print report
        report = backtest.generate_report()
        backtest.print_report(report)

        # Save report to file
        import json

        report_path = Path(__file__).parent.parent / "backtest_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n[OK] Report saved to: {report_path}")

    finally:
        await backtest.teardown()


if __name__ == "__main__":
    asyncio.run(main())
