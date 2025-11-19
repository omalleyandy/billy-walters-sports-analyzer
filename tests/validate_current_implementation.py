"""
Validate current scraper implementation against recommended locators.

This script analyzes the current pregame_odds_spider.py implementation
and identifies gaps and improvement opportunities.
"""

import re
from pathlib import Path


class ImplementationValidator:
    """Validates current implementation against best practices."""

    def __init__(self):
        self.spider_path = (
            Path(__file__).parent.parent
            / "scrapers"
            / "overtime_live"
            / "spiders"
            / "pregame_odds_spider.py"
        )
        self.findings = []
        self.recommendations = []

    def analyze_spider(self):
        """Analyze the spider implementation."""
        print("=" * 80)
        print("OVERTIME.AG SCRAPER IMPLEMENTATION VALIDATION")
        print("=" * 80)

        with open(self.spider_path, "r") as f:
            content = f.read()

        # Check for login implementation
        self._check_login_locators(content)

        # Check for period selection
        self._check_period_selection(content)

        # Check for container validation
        self._check_container_validation(content)

        # Check for button extraction
        self._check_button_extraction(content)

        # Check for market validation
        self._check_market_validation(content)

        # Generate report
        self._print_report()

    def _check_login_locators(self, content: str):
        """Check login implementation."""
        print("\n1. Login Locators")
        print("-" * 80)

        # Check for Customer Id input
        if "Customer Id" in content or "txtLoginName" in content:
            print("  [OK] Customer ID input locator found")
            if "placeholder='Customer Id'" in content:
                print("    Using: placeholder='Customer Id'")
            self.findings.append("[OK] Login: Customer ID locator present")
        else:
            print("  [X] Customer ID input locator NOT found")
            self.findings.append("[X] Login: Customer ID locator missing")
            self.recommendations.append(
                "Add Customer ID locator: //input[@placeholder='Customer Id']"
            )

        # Check for Password input
        if "Password" in content or "txtPassword" in content:
            print("  [OK] Password input locator found")
            if "placeholder='Password'" in content:
                print("    Using: placeholder='Password'")
            self.findings.append("[OK] Login: Password locator present")
        else:
            print("  [X] Password input locator NOT found")
            self.findings.append("[X] Login: Password locator missing")
            self.recommendations.append(
                "Add Password locator: //input[@placeholder='Password']"
            )

        # Check for Login button
        if "btn-login" in content or "Login" in content:
            print("  [OK] Login button locator found")
            if "btn-login" in content:
                print("    Using: btn-login class")
            self.findings.append("[OK] Login: Login button locator present")
        else:
            print("  [X] Login button locator NOT found")
            self.findings.append("[X] Login: Login button locator missing")
            self.recommendations.append(
                "Add Login button locator: //button[@class='btn btn-default btn-login ng-binding']"
            )

    def _check_period_selection(self, content: str):
        """Check for period selection implementation."""
        print("\n2. Period Selection")
        print("-" * 80)

        periods = {
            "Game": ["Game", "GAME", "full_game"],
            "1st Half": ["1st Half", "1ST HALF", "first_half"],
            "1st Quarter": ["1st Quarter", "1ST QUARTER", "first_quarter"],
            "Team Totals": ["Team Totals", "TEAM TOTALS", "team_totals"],
        }

        found_any = False
        for period_name, keywords in periods.items():
            if any(kw in content for kw in keywords):
                print(f"  [OK] {period_name} period selection found")
                self.findings.append(f"[OK] Period: {period_name} implemented")
                found_any = True
            else:
                print(f"  [X] {period_name} period selection NOT found")
                self.findings.append(f"[X] Period: {period_name} missing")

        if not found_any:
            print("\n  [WARNING] CRITICAL: No period selection implemented!")
            print("    Missing markets: 1st Half, Quarters, Team Totals")
            print("    Estimated data loss: ~70% of available betting markets")
            self.recommendations.append(
                "PRIORITY 1: Implement period selection to capture 1st Half, Quarter, and Team Total lines"
            )

    def _check_container_validation(self, content: str):
        """Check for container validation."""
        print("\n3. Container Validation")
        print("-" * 80)

        # Check for GameLines container
        if "#GameLines" in content or "GameLines" in content:
            print("  [OK] GameLines container referenced")
            self.findings.append("[OK] Container: GameLines referenced")

            # Check if it's used for validation
            if "wait_for_selector" in content and "GameLines" in content:
                print("    [OK] Using wait_for_selector for GameLines")
                self.findings.append(
                    "[OK] Container: Proper validation with wait_for_selector"
                )
            else:
                print("    [WARNING] GameLines not used with wait_for_selector")
                self.findings.append("[WARNING] Container: No proper validation")
                self.recommendations.append(
                    "Add container validation: await page.wait_for_selector('#GameLines', state='visible')"
                )
        else:
            print("  [X] GameLines container NOT referenced")
            self.findings.append("[X] Container: GameLines not referenced")
            self.recommendations.append("Add GameLines container locator: #GameLines")

        # Check for timeout-based waiting
        if "wait_for_timeout" in content:
            timeout_matches = re.findall(r"wait_for_timeout\((\d+)\)", content)
            if timeout_matches:
                timeouts = [int(t) for t in timeout_matches]
                max_timeout = max(timeouts)
                print(f"  [WARNING] Using wait_for_timeout with max {max_timeout}ms")
                print(
                    "    Recommendation: Replace with wait_for_selector for better reliability"
                )
                self.findings.append(
                    f"[WARNING] Wait: Using timeout-based waiting ({max_timeout}ms)"
                )
                self.recommendations.append(
                    f"Replace wait_for_timeout({max_timeout}) with wait_for_selector('#GameLines', state='visible')"
                )

    def _check_button_extraction(self, content: str):
        """Check button extraction implementation."""
        print("\n4. Button Extraction")
        print("-" * 80)

        button_ids = ["S1_", "S2_", "M1_", "M2_", "L1_", "L2_"]

        for btn_id in button_ids:
            if btn_id in content:
                print(f"  [OK] {btn_id} button extraction found")
                self.findings.append(f"[OK] Buttons: {btn_id} implemented")
            else:
                print(f"  [X] {btn_id} button extraction NOT found")
                self.findings.append(f"[X] Buttons: {btn_id} missing")
                self.recommendations.append(
                    f"Add button extraction for: button[id^='{btn_id}']"
                )

        # Check for button-to-game association
        if "evaluate" in content and "querySelectorAll" in content:
            print("\n  Button Collection Method:")
            if "button[id^=" in content:
                print("    [OK] Using ID prefix selectors")
                self.findings.append("[OK] Buttons: Using ID prefix selectors")
            else:
                print("    ? Using custom method")
                self.findings.append("? Buttons: Custom extraction method")

            # Check if buttons are associated with specific games
            if "event_id" in content or "eventId" in content:
                print("    [OK] Button-to-game association via event ID")
                self.findings.append("[OK] Buttons: Proper event ID association")
            else:
                print("    [WARNING] No explicit button-to-game association")
                print("      Risk: Buttons may be incorrectly assigned to games")
                self.findings.append("[WARNING] Buttons: No event ID association")
                self.recommendations.append(
                    "Add button-to-game association using event IDs from button IDs"
                )

    def _check_market_validation(self, content: str):
        """Check for market validation."""
        print("\n5. Market Validation")
        print("-" * 80)

        markets = ["Spread", "Money Line", "Totals"]

        for market in markets:
            if market in content:
                print(f"  [OK] {market} market referenced")
                self.findings.append(f"[OK] Market: {market} referenced")
            else:
                print(f"  ? {market} market not explicitly referenced")
                self.findings.append(f"? Market: {market} not explicitly referenced")

        # Check for market header validation
        if "normalize-space()='Spread'" in content or 'has-text("Spread")' in content:
            print("\n  [OK] Market header validation implemented")
            self.findings.append("[OK] Market: Header validation implemented")
        else:
            print("\n  [WARNING] No market header validation")
            print("    Recommendation: Validate market headers before extraction")
            self.findings.append("[WARNING] Market: No header validation")
            self.recommendations.append(
                "Add market header validation: verify Spread, Money Line, Totals headers are present"
            )

    def _print_report(self):
        """Print validation report."""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        # Count findings
        success = sum(1 for f in self.findings if f.startswith("[OK]"))
        warning = sum(1 for f in self.findings if f.startswith("[WARNING]"))
        missing = sum(1 for f in self.findings if f.startswith("[X]"))
        unknown = sum(1 for f in self.findings if f.startswith("?"))

        print("\nFindings:")
        print(f"  [OK] Implemented: {success}")
        print(f"  [WARNING] Needs Improvement: {warning}")
        print(f"  [X] Missing: {missing}")
        print(f"  ? Unknown/Custom: {unknown}")

        total = success + warning + missing + unknown
        if total > 0:
            score = (success + warning * 0.5) / total * 100
            print(f"\nImplementation Score: {score:.1f}%")

        if self.recommendations:
            print("\n" + "-" * 80)
            print("RECOMMENDATIONS")
            print("-" * 80)
            for i, rec in enumerate(self.recommendations, 1):
                print(f"\n{i}. {rec}")

        print("\n" + "=" * 80)


def main():
    """Run validation."""
    validator = ImplementationValidator()
    validator.analyze_spider()


if __name__ == "__main__":
    main()
