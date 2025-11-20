#!/usr/bin/env python3
"""
SMS Alert Module for Billy Walters Betting System
Sends text message notifications via Twilio for high-value betting opportunities
"""

import os
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("[WARNING]  Twilio not installed. Run: pip install twilio")

try:
    from logging_framework import get_logger
    logger = get_logger("sms_alerts")
except ImportError:
    import logging
    logger = logging.getLogger("sms_alerts")


@dataclass
class SMSConfig:
    """SMS configuration from environment variables"""
    account_sid: str
    auth_token: str
    from_number: str
    to_numbers: List[str]
    enabled: bool = True
    max_message_length: int = 160
    
    @classmethod
    def from_env(cls):
        """Load SMS config from environment variables"""
        to_numbers_str = os.getenv('SMS_ALERT_NUMBERS', '')
        to_numbers = [n.strip() for n in to_numbers_str.split(',') if n.strip()]
        
        return cls(
            account_sid=os.getenv('TWILIO_ACCOUNT_SID', ''),
            auth_token=os.getenv('TWILIO_AUTH_TOKEN', ''),
            from_number=os.getenv('TWILIO_FROM_NUMBER', ''),
            to_numbers=to_numbers,
            enabled=os.getenv('SMS_ALERTS_ENABLED', 'false').lower() == 'true'
        )
    
    def is_configured(self) -> bool:
        """Check if SMS is properly configured"""
        return bool(
            self.account_sid and 
            self.auth_token and 
            self.from_number and 
            self.to_numbers
        )


class SMSAlertManager:
    """Manages SMS text message alerts for betting opportunities"""
    
    def __init__(self, config: Optional[SMSConfig] = None):
        """Initialize SMS alert manager"""
        self.config = config or SMSConfig.from_env()
        self.client = None
        
        if not TWILIO_AVAILABLE:
            logger.warning("Twilio not available - SMS alerts disabled")
            self.config.enabled = False
            return
        
        if self.config.is_configured():
            try:
                self.client = Client(
                    self.config.account_sid,
                    self.config.auth_token
                )
                logger.info("SMS alerts initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.config.enabled = False
        else:
            logger.warning("SMS alerts not configured - missing credentials")
            self.config.enabled = False
    
    def _format_opportunity_sms(self, opportunity) -> str:
        """Format betting opportunity as concise SMS message"""
        game = f"{opportunity.away_team[:3]}-{opportunity.home_team[:3]}"
        rec = opportunity.recommendation
        bet = opportunity.bet_type
        
        if bet == "SPREAD":
            line = f"{rec[:3]}{opportunity.vegas_line:+.1f}"
        elif bet == "TOTAL":
            line = f"{'O' if rec == 'OVER' else 'U'}{opportunity.vegas_line:.1f}"
        else:
            line = f"ML {rec[:3]}"
        
        edge = opportunity.edge
        edge_pct = opportunity.edge_percentage
        priority = opportunity.priority_score
        
        # Calculate bet size (assuming $20k bankroll)
        bet_amount = int(20000 * opportunity.kelly_size)
        
        message = (
            f"[HOT] {game}: {line} | "
            f"Edge:{edge:+.1f}({edge_pct:.1f}%) | "
            f"${bet_amount} | "
            f"P:{priority:.0f}"
        )
        
        return message[:160]
    
    def send_opportunity_alert(self, opportunity) -> bool:
        """Send SMS alert for a single high-value opportunity"""
        if not self.config.enabled or not self.client:
            logger.debug("SMS alerts disabled or not configured")
            return False
        
        message_text = self._format_opportunity_sms(opportunity)
        success_count = 0
        
        for to_number in self.config.to_numbers:
            if not to_number.strip():
                continue
                
            try:
                message = self.client.messages.create(
                    body=message_text,
                    from_=self.config.from_number,
                    to=to_number.strip()
                )
                
                logger.info(
                    f"SMS sent successfully to {to_number}",
                    extra={
                        'message_sid': message.sid,
                        'game': f"{opportunity.away_team}@{opportunity.home_team}"
                    }
                )
                success_count += 1
                
            except TwilioRestException as e:
                logger.error(f"Twilio API error: {e.msg} (code: {e.code})")
            except Exception as e:
                logger.error(f"Failed to send SMS to {to_number}: {e}")
        
        return success_count > 0
    
    def send_test_message(self, to_number: Optional[str] = None) -> bool:
        """Send a test SMS to verify configuration"""
        if not self.config.enabled or not self.client:
            logger.error("SMS not configured - cannot send test message")
            return False
        
        test_numbers = [to_number] if to_number else self.config.to_numbers
        message_text = (
            f"[*] Billy Walters Betting System SMS Test\n"
            f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
            f"Alerts: ACTIVE [*]"
        )
        
        success = False
        for number in test_numbers:
            if not number.strip():
                continue
                
            try:
                message = self.client.messages.create(
                    body=message_text,
                    from_=self.config.from_number,
                    to=number.strip()
                )
                
                logger.info(f"Test SMS sent successfully to {number}")
                print(f"[*] Test SMS sent to {number}")
                success = True
                
            except TwilioRestException as e:
                logger.error(f"Test SMS failed: {e.msg}")
                print(f"[ERROR] Test SMS failed to {number}: {e.msg}")
            except Exception as e:
                logger.error(f"Test SMS error: {e}")
                print(f"[ERROR] Test SMS error: {e}")
        
        return success


if __name__ == "__main__":
    """Test SMS functionality"""
    print("\n" + "="*60)
    print("SMS ALERTS TEST")
    print("="*60 + "\n")
    
    if not TWILIO_AVAILABLE:
        print("[ERROR] Twilio not installed. Install with:")
        print("   pip install twilio")
        exit(1)
    
    # Load config
    config = SMSConfig.from_env()
    
    if not config.is_configured():
        print("[ERROR] SMS not configured. Please set environment variables:")
        print("   - TWILIO_ACCOUNT_SID")
        print("   - TWILIO_AUTH_TOKEN")
        print("   - TWILIO_FROM_NUMBER")
        print("   - SMS_ALERT_NUMBERS (comma-separated)")
        print("   - SMS_ALERTS_ENABLED=true")
        exit(1)
    
    print(f"[*] SMS Configuration Found")
    print(f"   From: {config.from_number}")
    print(f"   To: {', '.join(config.to_numbers)}")
    print(f"   Enabled: {config.enabled}\n")
    
    # Initialize manager
    manager = SMSAlertManager(config)
    
    # Send test message
    if input("Send test SMS? (y/n): ").lower() == 'y':
        success = manager.send_test_message()
        if success:
            print("\n[*] Test completed successfully")
        else:
            print("\n[ERROR] Test failed - check logs for details")
