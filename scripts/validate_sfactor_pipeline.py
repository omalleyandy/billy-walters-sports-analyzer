#!/usr/bin/env python3
"""
S-Factor Pipeline Validation Script
====================================

Validates the complete S-Factor data collection pipeline using
real NFL Week 12 data. Generates detailed validation report.

Purpose:
- Verify end-to-end functionality
- Test with actual NFL data
- Identify any issues before Week 2
- Generate validation metrics

Output:
- Console report with color coding
- validation_report.json with detailed metrics
- Pass/fail status for each component

Version: 1.0
Created: November 20, 2025
"""

import json
from datetime import date, datetime
from typing import Dict, List, Any
from pathlib import Path

from walters_analyzer.models.sfactor_data_models import TeamContext, ScheduleHistory
from walters_analyzer.data_collection.team_context_builder import TeamContextBuilder
from walters_analyzer.data_collection.schedule_history_calculator import ScheduleHistoryCalculator


class ValidationReport:
    """Generates comprehensive validation report"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {},
            'issues': []
        }
    
    def add_test(self, name: str, passed: bool, details: Dict[str, Any]):
        """Add test result"""
        self.results['tests'][name] = {
            'passed': passed,
            'details': details
        }
    
    def add_issue(self, severity: str, message: str):
        """Add issue found during validation"""
        self.results['issues'].append({
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_summary(self):
        """Generate summary statistics"""
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for t in self.results['tests'].values() if t['passed'])
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'critical_issues': sum(1 for i in self.results['issues'] if i['severity'] == 'CRITICAL'),
            'warnings': sum(1 for i in self.results['issues'] if i['severity'] == 'WARNING')
        }
    
    def save(self, filepath: str):
        """Save report to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def print_console_report(self):
        """Print formatted report to console"""
        print("\n" + "=" * 70)
        print("S-FACTOR PIPELINE VALIDATION REPORT")
        print("=" * 70)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Total Tests: {self.results['summary']['total_tests']}")
        print(f"Passed: {self.results['summary']['passed_tests']}")
        print(f"Failed: {self.results['summary']['failed_tests']}")
        print(f"Pass Rate: {self.results['summary']['pass_rate']:.1f}%")
        print("=" * 70)
        
        # Print test results
        print("\nTEST RESULTS:")
        for name, result in self.results['tests'].items():
            status = "[OK]" if result['passed'] else "[ERROR]"
            print(f"{status} {name}")
            for key, value in result['details'].items():
                print(f"    {key}: {value}")
        
        # Print issues
        if self.results['issues']:
            print("\nISSUES FOUND:")
            for issue in self.results['issues']:
                print(f"  [{issue['severity']}] {issue['message']}")
        else:
            print("\n[OK] No issues found!")
        
        print("\n" + "=" * 70)
        
        # Final status
        if self.results['summary']['failed_tests'] == 0:
            print("[OK] ALL TESTS PASSED - Ready for Week 2!")
        else:
            print(f"[ERROR] {self.results['summary']['failed_tests']} tests failed - Review needed")
        print("=" * 70 + "\n")


def validate_team_context_builder():
    """Validate TeamContextBuilder with real NFL data"""
    report = ValidationReport()
    builder = TeamContextBuilder()
    
    # Test 1: Bills (Elite tier, minor injury)
    print("\n[1/5] Testing Bills team context...")
    buf_data = {
        'team_name': 'Buffalo Bills',
        'abbreviation': 'BUF',
        'power_rating': 7.5,
        'offensive_ranking': 2,
        'defensive_ranking': 5,
        'special_teams_ranking': 8,
        'injuries': [
            {'player': 'Dawson Knox', 'position': 'TE', 'status': 'Questionable', 'impact': -0.5}
        ]
    }
    
    try:
        buf_context = builder.build_team_context(buf_data)
        
        passed = (
            buf_context.team_name == 'Buffalo Bills' and
            buf_context.abbreviation == 'BUF' and
            buf_context.current_power_rating == 7.5 and
            buf_context.quality_tier.value == 'elite' and
            buf_context.total_injury_impact == -0.5
        )
        
        report.add_test(
            'Bills Team Context',
            passed,
            {
                'team': buf_context.team_name,
                'power_rating': buf_context.current_power_rating,
                'tier': buf_context.quality_tier.value,
                'injury_impact': buf_context.total_injury_impact
            }
        )
        
        if not passed:
            report.add_issue('CRITICAL', 'Bills context validation failed')
    
    except Exception as e:
        report.add_test('Bills Team Context', False, {'error': str(e)})
        report.add_issue('CRITICAL', f'Bills context creation failed: {e}')
    
    
    # Test 2: Texans (Major injury - Stroud OUT)
    print("[2/5] Testing Texans with major injury...")
    hou_data = {
        'team_name': 'Houston Texans',
        'abbreviation': 'HOU',
        'power_rating': 2.0,
        'offensive_ranking': 15,
        'defensive_ranking': 8,
        'special_teams_ranking': 12,
        'injuries': [
            {'player': 'C.J. Stroud', 'position': 'QB', 'status': 'Out', 'impact': -7.5}
        ]
    }
    
    try:
        hou_context = builder.build_team_context(hou_data)
        
        # Adjusted rating should drop to -5.5 (2.0 - 7.5)
        adjusted_rating = hou_context.current_power_rating + hou_context.total_injury_impact
        
        passed = (
            hou_context.total_injury_impact == -7.5 and
            adjusted_rating == -5.5 and
            hou_context.key_injuries_count == 1
        )
        
        report.add_test(
            'Texans Major Injury',
            passed,
            {
                'team': hou_context.team_name,
                'base_rating': hou_context.current_power_rating,
                'injury_impact': hou_context.total_injury_impact,
                'adjusted_rating': adjusted_rating
            }
        )
        
        if not passed:
            report.add_issue('WARNING', 'Texans injury calculation may be incorrect')
    
    except Exception as e:
        report.add_test('Texans Major Injury', False, {'error': str(e)})
        report.add_issue('CRITICAL', f'Texans context failed: {e}')
    
    
    # Test 3: Chiefs (Perfect health)
    print("[3/5] Testing Chiefs with no injuries...")
    kc_data = {
        'team_name': 'Kansas City Chiefs',
        'abbreviation': 'KC',
        'power_rating': 8.0,
        'offensive_ranking': 5,
        'defensive_ranking': 3,
        'special_teams_ranking': 10,
        'injuries': []
    }
    
    try:
        kc_context = builder.build_team_context(kc_data)
        
        passed = (
            kc_context.total_injury_impact == 0.0 and
            kc_context.key_injuries_count == 0 and
            kc_context.quality_tier.value == 'elite'
        )
        
        report.add_test(
            'Chiefs Healthy Team',
            passed,
            {
                'team': kc_context.team_name,
                'power_rating': kc_context.current_power_rating,
                'injuries': kc_context.key_injuries_count,
                'health_status': 'HEALTHY'
            }
        )
        
        if not passed:
            report.add_issue('WARNING', 'Chiefs healthy team handling failed')
    
    except Exception as e:
        report.add_test('Chiefs Healthy Team', False, {'error': str(e)})
        report.add_issue('CRITICAL', f'Chiefs context failed: {e}')
    
    return report


def validate_schedule_calculator():
    """Validate ScheduleHistoryCalculator with real games"""
    report = ValidationReport()
    calculator = ScheduleHistoryCalculator()
    
    # Test 4: Bills @ Texans (TNF - 1,200+ mile travel)
    print("[4/5] Testing Bills travel to Houston...")
    buf_schedule = [
        {
            'game_date': date(2025, 11, 21),
            'is_home': False,
            'opponent': 'HOU',
            'opponent_power_rating': 2.0,
            'game_time': 'primetime',
            'days_rest': 7
        }
    ]
    
    try:
        history = calculator.calculate_schedule_history(
            team_abbr='BUF',
            current_date=date(2025, 11, 21),
            recent_games=buf_schedule
        )
        
        # Buffalo to Houston is ~1,200 miles
        passed = (
            history.total_games == 1 and
            history.total_travel_miles > 1000 and
            history.primetime_games_count == 1 and
            history.days_since_last_game == 7
        )
        
        report.add_test(
            'Bills Travel Schedule',
            passed,
            {
                'team': 'BUF',
                'travel_miles': history.total_travel_miles,
                'primetime_games': history.primetime_games_count,
                'rest_days': history.days_since_last_game
            }
        )
        
        if not passed:
            report.add_issue('WARNING', 'Bills schedule calculation may be inaccurate')
    
    except Exception as e:
        report.add_test('Bills Travel Schedule', False, {'error': str(e)})
        report.add_issue('CRITICAL', f'Schedule calculation failed: {e}')
    
    
    # Test 5: Short week detection
    print("[5/5] Testing short week detection...")
    short_week_games = [
        {
            'game_date': date(2025, 11, 17),  # Sunday
            'is_home': True,
            'opponent': 'OPP',
            'opponent_power_rating': 0,
            'game_time': 'afternoon',
            'days_rest': 7
        }
    ]
    
    try:
        history = calculator.calculate_schedule_history(
            team_abbr='BUF',
            current_date=date(2025, 11, 21),  # Thursday
            recent_games=short_week_games
        )
        
        # Sunday to Thursday = 4 days
        passed = (
            history.days_since_last_game == 4 and
            history.has_short_week is True
        )
        
        report.add_test(
            'Short Week Detection',
            passed,
            {
                'days_between_games': history.days_since_last_game,
                'short_week_detected': history.has_short_week
            }
        )
        
        if not passed:
            report.add_issue('WARNING', 'Short week detection may not be working')
    
    except Exception as e:
        report.add_test('Short Week Detection', False, {'error': str(e)})
        report.add_issue('CRITICAL', f'Short week test failed: {e}')
    
    return report


def main():
    """Run all validations and generate report"""
    print("\n" + "=" * 70)
    print("STARTING S-FACTOR PIPELINE VALIDATION")
    print("=" * 70)
    
    # Run validations
    team_report = validate_team_context_builder()
    schedule_report = validate_schedule_calculator()
    
    # Merge reports
    final_report = ValidationReport()
    final_report.results['tests'].update(team_report.results['tests'])
    final_report.results['tests'].update(schedule_report.results['tests'])
    final_report.results['issues'] = team_report.results['issues'] + schedule_report.results['issues']
    
    # Generate summary
    final_report.generate_summary()
    
    # Print console report
    final_report.print_console_report()
    
    # Save detailed report
    output_dir = Path(__file__).parent / 'validation_reports'
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / f'validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    final_report.save(str(report_file))
    
    print(f"[OK] Detailed report saved: {report_file}")
    
    # Return exit code
    return 0 if final_report.results['summary']['failed_tests'] == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
