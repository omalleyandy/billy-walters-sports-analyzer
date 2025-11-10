#!/usr/bin/env python3
"""
Watch for sharp money alerts in real-time
"""
import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except AttributeError:
        pass

alerts_file = Path("logs/alerts.log")
print("=" * 80)
print("WATCHING FOR SHARP MONEY ALERTS")
print("=" * 80)
print(f"Monitoring: {alerts_file}")
print("Press Ctrl+C to stop")
print("=" * 80)
print()

# Track last position in file
last_pos = 0
alert_count = 0

try:
    while True:
        if alerts_file.exists():
            # Read new content
            with open(alerts_file, 'r') as f:
                f.seek(last_pos)
                new_lines = f.readlines()
                last_pos = f.tell()

            # Process new alerts
            for line in new_lines:
                if line.strip():
                    alert_count += 1
                    try:
                        alert = json.loads(line)

                        print("\n" + "=" * 80)
                        print(f"ALERT #{alert_count} - {datetime.now().strftime('%H:%M:%S')}")
                        print("=" * 80)

                        teams = alert.get('teams', {})
                        print(f"Game:      {teams.get('away', 'Unknown')} @ {teams.get('home', 'Unknown')}")
                        print(f"Direction: {alert.get('direction', 'Unknown')}")
                        print(f"Sharp Line Movement:  {alert.get('sharp_movement', 0):+.1f} points")
                        print(f"Public Line Movement: {alert.get('public_movement', 0):+.1f} points")
                        print(f"Divergence: {alert.get('divergence', 0):+.1f} points")

                        sharp_line = alert.get('current_sharp_line')
                        if sharp_line is not None:
                            print(f"Current Sharp Line: {sharp_line:.1f}")

                        confidence = alert.get('confidence', 0)
                        print(f"Confidence: {confidence:.0f}%")

                        # Show which books were analyzed
                        books = alert.get('books_analyzed', {})
                        sharp_books = books.get('sharp', [])
                        public_books = books.get('public', [])

                        if sharp_books:
                            print(f"Sharp Books: {', '.join(sharp_books)}")
                        if public_books:
                            print(f"Public Books: {', '.join(public_books)}")

                        print(f"Time: {alert.get('timestamp', 'Unknown')}")
                        print("=" * 80)

                        # Interpretation
                        if confidence > 150:
                            print("ACTION: STRONG SIGNAL - Consider betting")
                        elif confidence > 100:
                            print("ACTION: MODERATE SIGNAL - Wait for confirmation")
                        else:
                            print("ACTION: WEAK SIGNAL - Monitor only")

                        print()

                    except json.JSONDecodeError:
                        print(f"[Invalid JSON] {line.strip()}")

        # Wait before checking again
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\nStopped watching alerts.")
    print(f"Total alerts captured: {alert_count}")
