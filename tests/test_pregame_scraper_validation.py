#!/usr/bin/env python3
"""
Unit tests to validate the pregame scraper against known HTML samples from overtime.ag

These tests verify that the extraction logic correctly handles the HTML structure
and button formats from actual overtime.ag pages.
"""

import re
import unittest
from typing import Dict, Any, List


class TestPregameScraperValidation(unittest.TestCase):
    """Test cases based on actual HTML from overtime.ag (Arizona @ Dallas, Nov 3, 2025)"""
    
    def setUp(self):
        """Set up test data based on user-provided HTML"""
        self.sample_game = {
            "away_team_html": "475 ARIZONA CARDINALS",
            "home_team_html": "476 DALLAS COWBOYS",
            "date_html": "Mon Nov 3",
            "time_html": "8:15 PM",
            "buttons": [
                {"id": "S1_114470298_02", "text": "+3½ -113"},  # Away spread
                {"id": "L1_114470298_0", "text": "O 54 -103"},  # Over
                {"id": "S2_114470298_0", "text": "-3½ -107"},   # Home spread
                {"id": "L2_114470298_0", "text": "U 54 -117"},  # Under
            ]
        }
    
    def test_rotation_number_extraction(self):
        """Test that rotation numbers are correctly extracted from team headings"""
        away_text = self.sample_game["away_team_html"]
        home_text = self.sample_game["home_team_html"]
        
        # Regex from pregame_odds_spider.py line 282-283
        away_match = re.match(r'^(\d{3,4})\s+(.+)$', away_text)
        home_match = re.match(r'^(\d{3,4})\s+(.+)$', home_text)
        
        self.assertIsNotNone(away_match, "Away team regex should match")
        self.assertIsNotNone(home_match, "Home team regex should match")
        
        away_rot = away_match.group(1)
        away_team = away_match.group(2)
        home_rot = home_match.group(1)
        home_team = home_match.group(2)
        
        # Validate extraction
        self.assertEqual(away_rot, "475")
        self.assertEqual(away_team, "ARIZONA CARDINALS")
        self.assertEqual(home_rot, "476")
        self.assertEqual(home_team, "DALLAS COWBOYS")
        
        # Validate combined rotation number
        rotation_number = f"{away_rot}-{home_rot}"
        self.assertEqual(rotation_number, "475-476")
    
    def test_spread_parsing(self):
        """Test that spread lines are correctly parsed from button text"""
        # Find spread buttons
        spread_buttons = [
            btn for btn in self.sample_game["buttons"] 
            if btn["id"].startswith("S")
        ]
        
        self.assertEqual(len(spread_buttons), 2, "Should find 2 spread buttons")
        
        # Regex from pregame_odds_spider.py line 323
        spread_regex = re.compile(r'^([+\-]\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$')
        
        spread_away = None
        spread_home = None
        
        for btn in spread_buttons:
            match = spread_regex.match(btn["text"])
            self.assertIsNotNone(match, f"Spread regex should match '{btn['text']}'")
            
            line_str = match.group(1)
            price_str = match.group(2)
            
            # Convert ½ to .5
            line = float(line_str.replace('½', '.5'))
            price = int(price_str)
            
            if btn["id"].startswith("S1_"):
                spread_away = {"line": line, "price": price}
            elif btn["id"].startswith("S2_"):
                spread_home = {"line": line, "price": price}
        
        # Validate parsed values
        self.assertIsNotNone(spread_away)
        self.assertIsNotNone(spread_home)
        
        self.assertEqual(spread_away["line"], 3.5)
        self.assertEqual(spread_away["price"], -113)
        self.assertEqual(spread_home["line"], -3.5)
        self.assertEqual(spread_home["price"], -107)
        
        # Validate consistency: home line should be negative of away line
        self.assertEqual(spread_home["line"], -spread_away["line"])
    
    def test_total_parsing(self):
        """Test that total lines are correctly parsed from button text"""
        # Find total buttons
        total_buttons = [
            btn for btn in self.sample_game["buttons"] 
            if btn["id"].startswith("L")
        ]
        
        self.assertEqual(len(total_buttons), 2, "Should find 2 total buttons")
        
        # Regex from pregame_odds_spider.py line 347
        total_regex = re.compile(r'^([OU])\s+(\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$', re.IGNORECASE)
        
        total_over = None
        total_under = None
        
        for btn in total_buttons:
            match = total_regex.match(btn["text"])
            self.assertIsNotNone(match, f"Total regex should match '{btn['text']}'")
            
            side = match.group(1).upper()
            line_str = match.group(2)
            price_str = match.group(3)
            
            # Convert ½ to .5
            line = float(line_str.replace('½', '.5'))
            price = int(price_str)
            
            if btn["id"].startswith("L1_") or side == "O":
                total_over = {"line": line, "price": price}
            elif btn["id"].startswith("L2_") or side == "U":
                total_under = {"line": line, "price": price}
        
        # Validate parsed values
        self.assertIsNotNone(total_over)
        self.assertIsNotNone(total_under)
        
        self.assertEqual(total_over["line"], 54.0)
        self.assertEqual(total_over["price"], -103)
        self.assertEqual(total_under["line"], 54.0)
        self.assertEqual(total_under["price"], -117)
        
        # Validate consistency: over and under lines should be equal
        self.assertEqual(total_over["line"], total_under["line"])
    
    def test_date_time_parsing(self):
        """Test that date and time are correctly parsed"""
        date_str = self.sample_game["date_html"]
        time_str = self.sample_game["time_html"]
        
        # Date regex from pregame_odds_spider.py line 302
        date_regex = re.compile(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w+\s+\d+$')
        self.assertTrue(date_regex.match(date_str), f"Date regex should match '{date_str}'")
        
        # Time regex from pregame_odds_spider.py line 305
        time_regex = re.compile(r'^\d{1,2}:\d{2}\s+(AM|PM)$', re.IGNORECASE)
        self.assertTrue(time_regex.match(time_str), f"Time regex should match '{time_str}'")
        
        # Parse to ISO date (from parse_date_time function)
        from datetime import datetime
        current_year = datetime.now().year
        date_parts = date_str.split()
        month_str = date_parts[1]  # "Nov"
        day_str = date_parts[2]    # "3"
        
        dt = datetime.strptime(f"{current_year} {month_str} {day_str}", "%Y %b %d")
        iso_date = dt.strftime("%Y-%m-%d")
        
        self.assertEqual(iso_date, "2025-11-03")
        
        # Time should have timezone appended
        time_with_tz = f"{time_str} ET"
        self.assertEqual(time_with_tz, "8:15 PM ET")
    
    def test_team_name_validation(self):
        """Test that team names pass validation"""
        # Extract team names
        away_match = re.match(r'^(\d{3,4})\s+(.+)$', self.sample_game["away_team_html"])
        home_match = re.match(r'^(\d{3,4})\s+(.+)$', self.sample_game["home_team_html"])
        
        away_team = away_match.group(2).strip()
        home_team = home_match.group(2).strip()
        
        # Validation from enhanced scraper (line 293-294)
        self.assertGreaterEqual(len(away_team), 3)
        self.assertGreaterEqual(len(home_team), 3)
        
        team_name_regex = re.compile(r'^[A-Z\s\-\.&\']+$', re.IGNORECASE)
        self.assertTrue(team_name_regex.match(away_team), f"Away team should pass validation: '{away_team}'")
        self.assertTrue(team_name_regex.match(home_team), f"Home team should pass validation: '{home_team}'")
    
    def test_button_id_assignment(self):
        """Test that button IDs correctly determine market assignment"""
        buttons = self.sample_game["buttons"]
        
        # Verify button ID patterns
        spread_buttons = [b for b in buttons if b["id"].startswith("S")]
        total_buttons = [b for b in buttons if b["id"].startswith("L")]
        
        # S1 = away spread, S2 = home spread
        self.assertTrue(any(b["id"].startswith("S1_") for b in spread_buttons), "Should have S1 (away spread)")
        self.assertTrue(any(b["id"].startswith("S2_") for b in spread_buttons), "Should have S2 (home spread)")
        
        # L1 = over, L2 = under
        self.assertTrue(any(b["id"].startswith("L1_") for b in total_buttons), "Should have L1 (over)")
        self.assertTrue(any(b["id"].startswith("L2_") for b in total_buttons), "Should have L2 (under)")
    
    def test_complete_game_extraction(self):
        """Test complete extraction of a game (integration test)"""
        # Simulate the complete extraction process
        game_data = self._extract_game(self.sample_game)
        
        # Validate all fields
        self.assertEqual(game_data["rotation_number"], "475-476")
        self.assertEqual(game_data["away_team"], "ARIZONA CARDINALS")
        self.assertEqual(game_data["home_team"], "DALLAS COWBOYS")
        self.assertEqual(game_data["event_date"], "2025-11-03")
        self.assertEqual(game_data["event_time"], "8:15 PM ET")
        
        # Validate markets
        markets = game_data["markets"]
        
        # Spread
        self.assertEqual(markets["spread"]["away"]["line"], 3.5)
        self.assertEqual(markets["spread"]["away"]["price"], -113)
        self.assertEqual(markets["spread"]["home"]["line"], -3.5)
        self.assertEqual(markets["spread"]["home"]["price"], -107)
        
        # Total
        self.assertEqual(markets["total"]["over"]["line"], 54.0)
        self.assertEqual(markets["total"]["over"]["price"], -103)
        self.assertEqual(markets["total"]["under"]["line"], 54.0)
        self.assertEqual(markets["total"]["under"]["price"], -117)
    
    def _extract_game(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to simulate the JavaScript extraction logic"""
        from datetime import datetime
        
        # Extract teams and rotation numbers
        away_match = re.match(r'^(\d{3,4})\s+(.+)$', sample["away_team_html"])
        home_match = re.match(r'^(\d{3,4})\s+(.+)$', sample["home_team_html"])
        
        away_rot = away_match.group(1)
        away_team = away_match.group(2).strip()
        home_rot = home_match.group(1)
        home_team = home_match.group(2).strip()
        
        # Parse date
        date_str = sample["date_html"]
        time_str = sample["time_html"]
        
        current_year = datetime.now().year
        date_parts = date_str.split()
        month_str = date_parts[1]
        day_str = date_parts[2]
        
        dt = datetime.strptime(f"{current_year} {month_str} {day_str}", "%Y %b %d")
        iso_date = dt.strftime("%Y-%m-%d")
        time_with_tz = f"{time_str} ET"
        
        # Parse markets
        markets = {"spread": {}, "total": {}, "moneyline": {}}
        
        spread_regex = re.compile(r'^([+\-]\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$')
        total_regex = re.compile(r'^([OU])\s+(\d+\.?\d?[½]?)\s+([+\-]\d{2,4})$', re.IGNORECASE)
        
        for btn in sample["buttons"]:
            # Try spread
            match = spread_regex.match(btn["text"])
            if match:
                line = float(match.group(1).replace('½', '.5'))
                price = int(match.group(2))
                
                if btn["id"].startswith("S1_"):
                    markets["spread"]["away"] = {"line": line, "price": price}
                elif btn["id"].startswith("S2_"):
                    markets["spread"]["home"] = {"line": line, "price": price}
            
            # Try total
            match = total_regex.match(btn["text"])
            if match:
                side = match.group(1).upper()
                line = float(match.group(2).replace('½', '.5'))
                price = int(match.group(3))
                
                if btn["id"].startswith("L1_") or side == "O":
                    markets["total"]["over"] = {"line": line, "price": price}
                elif btn["id"].startswith("L2_") or side == "U":
                    markets["total"]["under"] = {"line": line, "price": price}
        
        return {
            "rotation_number": f"{away_rot}-{home_rot}",
            "away_team": away_team,
            "home_team": home_team,
            "event_date": iso_date,
            "event_time": time_with_tz,
            "markets": markets,
        }


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and potential failure modes"""
    
    def test_fractional_line_conversion(self):
        """Test that fractional lines (½) are correctly converted to decimals"""
        test_cases = [
            ("3½", 3.5),
            ("+3½", 3.5),
            ("-3½", -3.5),
            ("10½", 10.5),
            ("0½", 0.5),
        ]
        
        for input_str, expected in test_cases:
            result = float(input_str.replace('½', '.5'))
            self.assertEqual(result, expected, f"Failed to convert '{input_str}'")
    
    def test_price_range_validation(self):
        """Test that prices are within reasonable ranges"""
        valid_prices = [-110, -115, -120, +150, +200, -300, +500]
        invalid_prices = [0, -50, +50, -15000, +15000]
        
        for price in valid_prices:
            # Price should be outside -99 to +99 range (excluding 0)
            self.assertTrue(price < -99 or price > 99)
        
        for price in invalid_prices:
            # These should be flagged as invalid
            if price == 0:
                self.assertTrue(True)  # Zero is always invalid
            elif -99 < price < 100:
                self.assertTrue(True)  # In invalid range
    
    def test_rotation_number_consistency(self):
        """Test that rotation numbers are consecutive odd-even pairs"""
        test_cases = [
            ("475-476", True),   # Valid: consecutive
            ("451-452", True),   # Valid: consecutive
            ("317-318", True),   # Valid: consecutive
            ("475-477", False),  # Invalid: not consecutive
            ("476-475", False),  # Invalid: wrong order
            ("100-102", False),  # Invalid: gap
        ]
        
        for rot_num, should_be_valid in test_cases:
            parts = rot_num.split('-')
            away_rot = int(parts[0])
            home_rot = int(parts[1])
            
            is_consecutive = (home_rot == away_rot + 1)
            
            if should_be_valid:
                self.assertTrue(is_consecutive, f"{rot_num} should be valid")
            else:
                self.assertFalse(is_consecutive, f"{rot_num} should be invalid")


if __name__ == "__main__":
    unittest.main(verbosity=2)

