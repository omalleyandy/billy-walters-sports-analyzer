"""
Validation Logger for Billy Walters Sports Analyzer

Structured logging system for data validation events.
Integrates with validate_data.py hook and tracks validation history.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ValidationLogger:
    """
    Structured logger for validation events.

    Tracks all data validation attempts, successes, and failures
    with detailed context for debugging and quality monitoring.
    """

    def __init__(self, log_dir: str = "logs/validation"):
        """
        Initialize validation logger.

        Args:
            log_dir: Directory to store validation logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup file logging
        self.logger = logging.getLogger("validation")
        self.logger.setLevel(logging.INFO)

        # Create file handler
        log_file = self.log_dir / f"validation_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        # Add handler if not already added
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

        # In-memory event tracking
        self.events: List[Dict[str, Any]] = []
        self.stats = {
            'total_validations': 0,
            'successful': 0,
            'failed': 0,
            'by_type': {}
        }

    def log_event(
        self,
        event_name: str,
        data_type: str,
        validation_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a validation event.

        Args:
            event_name: Name of the event (e.g., 'odds_fetch', 'weather_fetch')
            data_type: Type of data being validated ('odds', 'weather', 'game')
            validation_result: Result from validation with 'valid' key
            context: Additional context (game_id, timestamp, etc.)
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_name': event_name,
            'data_type': data_type,
            'valid': validation_result.get('valid', False),
            'errors': validation_result.get('errors', []),
            'context': context or {}
        }

        # Store event
        self.events.append(event)

        # Update statistics
        self.stats['total_validations'] += 1
        if event['valid']:
            self.stats['successful'] += 1
        else:
            self.stats['failed'] += 1

        # Track by type
        if data_type not in self.stats['by_type']:
            self.stats['by_type'][data_type] = {'success': 0, 'failed': 0}

        if event['valid']:
            self.stats['by_type'][data_type]['success'] += 1
        else:
            self.stats['by_type'][data_type]['failed'] += 1

        # Log to file
        if event['valid']:
            self.logger.info(
                f"{event_name} - {data_type} validation PASSED: {json.dumps(context or {})}"
            )
        else:
            self.logger.error(
                f"{event_name} - {data_type} validation FAILED: "
                f"{validation_result.get('errors', [])} | Context: {json.dumps(context or {})}"
            )

    def log_odds_validation(
        self,
        game_id: str,
        odds_data: Dict[str, Any],
        is_valid: bool,
        errors: Optional[List[str]] = None
    ) -> None:
        """
        Convenience method for logging odds validation.

        Args:
            game_id: Unique game identifier
            odds_data: Odds data that was validated
            is_valid: Whether validation passed
            errors: List of validation errors if any
        """
        validation_result = {
            'valid': is_valid,
            'errors': errors or []
        }

        context = {
            'game_id': game_id,
            'spread': odds_data.get('spread'),
            'over_under': odds_data.get('over_under'),
            'moneyline_home': odds_data.get('moneyline_home'),
            'moneyline_away': odds_data.get('moneyline_away')
        }

        self.log_event('odds_validation', 'odds', validation_result, context)

    def log_weather_validation(
        self,
        game_id: str,
        weather_data: Dict[str, Any],
        is_valid: bool,
        errors: Optional[List[str]] = None
    ) -> None:
        """
        Convenience method for logging weather validation.

        Args:
            game_id: Unique game identifier
            weather_data: Weather data that was validated
            is_valid: Whether validation passed
            errors: List of validation errors if any
        """
        validation_result = {
            'valid': is_valid,
            'errors': errors or []
        }

        context = {
            'game_id': game_id,
            'temperature': weather_data.get('temperature'),
            'wind_speed': weather_data.get('wind_speed'),
            'precipitation_probability': weather_data.get('precipitation_probability')
        }

        self.log_event('weather_validation', 'weather', validation_result, context)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics.

        Returns:
            Dictionary with validation stats
        """
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful'] / self.stats['total_validations'] * 100
                if self.stats['total_validations'] > 0
                else 0
            )
        }

    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent validation events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        return self.events[-limit:]

    def get_failed_validations(self) -> List[Dict[str, Any]]:
        """
        Get all failed validations.

        Returns:
            List of failed validation events
        """
        return [event for event in self.events if not event['valid']]

    def save_report(self, filename: Optional[str] = None) -> Path:
        """
        Save validation report to JSON file.

        Args:
            filename: Optional filename (defaults to timestamped report)

        Returns:
            Path to saved report file
        """
        if filename is None:
            filename = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report_path = self.log_dir / filename

        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'recent_events': self.get_recent_events(50),
            'failed_validations': self.get_failed_validations()
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Validation report saved to {report_path}")
        return report_path


# Global logger instance
_global_logger: Optional[ValidationLogger] = None


def get_logger() -> ValidationLogger:
    """
    Get global validation logger instance.

    Returns:
        Singleton ValidationLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = ValidationLogger()
    return _global_logger


if __name__ == "__main__":
    # Example usage
    logger = ValidationLogger()

    # Test odds validation
    logger.log_odds_validation(
        game_id="NFL_2025_W10_BUF_KC",
        odds_data={
            'spread': -2.5,
            'over_under': 47.5,
            'moneyline_home': -135,
            'moneyline_away': 115
        },
        is_valid=True
    )

    # Test failed validation
    logger.log_odds_validation(
        game_id="NFL_2025_W10_DET_GB",
        odds_data={
            'spread': -75.5,  # Invalid
            'over_under': 15,  # Invalid
            'moneyline_home': -150,
            'moneyline_away': 130
        },
        is_valid=False,
        errors=[
            "Invalid spread: -75.5 (must be between -50 and 50)",
            "Invalid over/under: 15 (must be between 20 and 100)"
        ]
    )

    # Print statistics
    stats = logger.get_statistics()
    print("\nValidation Statistics:")
    print(json.dumps(stats, indent=2))

    # Save report
    report_path = logger.save_report()
    print(f"\nReport saved to: {report_path}")
