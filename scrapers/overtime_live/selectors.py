"""
All DOM selectors live here so you can tweak quickly if Overtime changes markup.
The spider tries PREFERRED selectors first, then falls back to a defensive parse.
"""

LIVE_ROUTE = "https://overtime.ag/sports#/integrations/liveBetting"

# Section heading to scope the board
COLLEGE_FOOTBALL_HEADING = "COLLEGE FOOTBALL"

# Preferred CSS anchors (best effort; adjust with DevTools if site updates):
# Container that holds all college football rows after expanding the section
BOARD_CONTAINER = "div:has-text('COLLEGE FOOTBALL') >> xpath=../.."

# A single game “row” (teams + markets). This is intentionally lax.
GAME_ROW = "[class*=row],[class*=event],[class*=market]"  # pick whichever matches in your DOM

# Inside a row, elements that resemble team names:
TEAM_NAME_CANDIDATE = "div:has-text(' @ '), span, a, strong"

# Market boxes often look like pill/box buttons; we’ll scrape numbers from visible text.
PRICE_BOXES = "button, div, span"
