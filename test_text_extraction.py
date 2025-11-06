#!/usr/bin/env python3
"""
Test the text-based extraction logic for the pregame odds spider.

This simulates the Angular-rendered page structure using document.body.innerText
and validates that the JavaScript extraction code correctly identifies games.
"""

import asyncio
from playwright.async_api import async_playwright


async def test_extraction():
    """Test that the extraction logic works with Angular-rendered text"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Create a mock HTML page that simulates Angular-rendered content
        # The key is that Angular renders text content, not structured DOM
        mock_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
        <div>
        🆕NEW VERSION
        SPORTS
        GAME
        NFL
        Sun Nov 3
        1:00 PM
        109 Las Vegas Raiders
        110 Denver Broncos
        Sun Nov 3
        1:00 PM
        251 Atlanta Falcons
        252 Indianapolis Colts
        Mon Nov 3
        8:15 PM
        475 ARIZONA CARDINALS
        476 DALLAS COWBOYS
        </div>
        <button id="S1_114470298_02">+3½ -113</button>
        <button id="L1_114470298_0">O 54 -103</button>
        <button id="S2_114470298_0">-3½ -107</button>
        <button id="L2_114470298_0">U 54 -117</button>
        <button id="M1_114470298_0">+150</button>
        <button id="M2_114470298_0">-170</button>
        </body>
        </html>
        """

        await page.set_content(mock_html)

        # Run the extraction JavaScript (same as in the spider)
        js_code = """
        () => {
            // Parse document.body.innerText to find rotation numbers and team names
            const allText = document.body.innerText;
            const lines = allText.split('\\n');

            // Step 1: Find all team lines with rotation numbers
            const teamLines = [];
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                const match = line.match(/^(\\d{3,4})\\s+(.+)$/);
                if (match) {
                    const rotation = match[1];
                    const teamName = match[2].trim();

                    // Validate team name
                    if (teamName.length >= 3 && /^[A-Z\\s\\-\\.&']+$/i.test(teamName)) {
                        // Exclude navigation/UI elements
                        if (!teamName.match(/^(NEW VERSION|SPORTS|GAME|PERIOD|FILTER)$/i)) {
                            teamLines.push({ rotation, teamName, lineIndex: i });
                        }
                    }
                }
            }

            console.log(`Found ${teamLines.length} valid team lines`);

            // Step 2: Pair teams into games
            const games = [];
            for (let i = 0; i < teamLines.length - 1; i++) {
                const away = teamLines[i];
                const home = teamLines[i + 1];

                const awayRot = parseInt(away.rotation);
                const homeRot = parseInt(home.rotation);

                if (homeRot === awayRot + 1) {
                    games.push({
                        rotation_number: `${away.rotation}-${home.rotation}`,
                        away_team: away.teamName,
                        home_team: home.teamName,
                    });
                    i++;
                }
            }

            console.log(`Paired ${games.length} games`);

            // Step 3: Extract button data
            const allButtons = document.querySelectorAll('button');
            const buttonMap = {};
            for (const btn of allButtons) {
                const btnId = btn.id || '';
                const btnText = (btn.innerText || '').trim();
                if (btnId && btnText) {
                    buttonMap[btnId] = btnText;
                }
            }

            console.log(`Found ${Object.keys(buttonMap).length} buttons`);

            // Step 4: Parse markets from buttons
            const markets = { spread: {}, total: {}, moneyline: {} };

            const spreadRegex = /^([+\\-]\\d+\\.?\\d?[½]?)\\s+([+\\-]\\d{2,4})$/;
            const totalRegex = /^([OU])\\s+(\\d+\\.?\\d?[½]?)\\s+([+\\-]\\d{2,4})$/i;
            const mlRegex = /^([+\\-]\\d{2,4})$/;

            for (const [btnId, btnText] of Object.entries(buttonMap)) {
                // Spread
                if (btnId.startsWith('S1_')) {
                    const match = btnText.match(spreadRegex);
                    if (match) {
                        markets.spread.away = {
                            line: parseFloat(match[1].replace('½', '.5')),
                            price: parseInt(match[2])
                        };
                    }
                } else if (btnId.startsWith('S2_')) {
                    const match = btnText.match(spreadRegex);
                    if (match) {
                        markets.spread.home = {
                            line: parseFloat(match[1].replace('½', '.5')),
                            price: parseInt(match[2])
                        };
                    }
                }

                // Total
                if (btnId.startsWith('L1_')) {
                    const match = btnText.match(totalRegex);
                    if (match) {
                        markets.total.over = {
                            line: parseFloat(match[2].replace('½', '.5')),
                            price: parseInt(match[3])
                        };
                    }
                } else if (btnId.startsWith('L2_')) {
                    const match = btnText.match(totalRegex);
                    if (match) {
                        markets.total.under = {
                            line: parseFloat(match[2].replace('½', '.5')),
                            price: parseInt(match[3])
                        };
                    }
                }

                // Moneyline
                if (btnId.startsWith('M1_')) {
                    const match = btnText.match(mlRegex);
                    if (match) {
                        markets.moneyline.away = {
                            line: null,
                            price: parseInt(match[1])
                        };
                    }
                } else if (btnId.startsWith('M2_')) {
                    const match = btnText.match(mlRegex);
                    if (match) {
                        markets.moneyline.home = {
                            line: null,
                            price: parseInt(match[1])
                        };
                    }
                }
            }

            return { games, markets, teamLines: teamLines.length, buttonCount: Object.keys(buttonMap).length };
        }
        """

        result = await page.evaluate(js_code)

        await browser.close()

        return result


async def main():
    print("Testing text-based extraction logic...\n")

    result = await test_extraction()

    print(f"✓ Found {result['teamLines']} team lines")
    print(f"✓ Paired {len(result['games'])} games:")
    for game in result['games']:
        print(f"  - {game['rotation_number']}: {game['away_team']} @ {game['home_team']}")

    print(f"\n✓ Found {result['buttonCount']} buttons with IDs")

    markets = result['markets']
    print("\nExtracted markets:")

    if markets['spread'].get('away'):
        print(f"  Spread Away: {markets['spread']['away']['line']:+.1f} ({markets['spread']['away']['price']:+d})")
    if markets['spread'].get('home'):
        print(f"  Spread Home: {markets['spread']['home']['line']:+.1f} ({markets['spread']['home']['price']:+d})")

    if markets['total'].get('over'):
        print(f"  Total Over: {markets['total']['over']['line']:.1f} ({markets['total']['over']['price']:+d})")
    if markets['total'].get('under'):
        print(f"  Total Under: {markets['total']['under']['line']:.1f} ({markets['total']['under']['price']:+d})")

    if markets['moneyline'].get('away'):
        print(f"  Moneyline Away: {markets['moneyline']['away']['price']:+d}")
    if markets['moneyline'].get('home'):
        print(f"  Moneyline Home: {markets['moneyline']['home']['price']:+d}")

    # Validation
    assert len(result['games']) == 3, f"Expected 3 games, got {len(result['games'])}"
    assert result['games'][0]['rotation_number'] == "109-110", "Wrong rotation for game 1"
    assert result['games'][1]['rotation_number'] == "251-252", "Wrong rotation for game 2"
    assert result['games'][2]['rotation_number'] == "475-476", "Wrong rotation for game 3"

    assert "Las Vegas Raiders" in result['games'][0]['away_team'], "Wrong away team for game 1"
    assert "Denver Broncos" in result['games'][0]['home_team'], "Wrong home team for game 1"

    # Market validation
    assert markets['spread']['away']['line'] == 3.5, "Wrong spread away line"
    assert markets['spread']['away']['price'] == -113, "Wrong spread away price"
    assert markets['spread']['home']['line'] == -3.5, "Wrong spread home line"
    assert markets['spread']['home']['price'] == -107, "Wrong spread home price"

    assert markets['total']['over']['line'] == 54.0, "Wrong total over line"
    assert markets['total']['over']['price'] == -103, "Wrong total over price"
    assert markets['total']['under']['line'] == 54.0, "Wrong total under line"
    assert markets['total']['under']['price'] == -117, "Wrong total under price"

    assert markets['moneyline']['away']['price'] == 150, "Wrong moneyline away price"
    assert markets['moneyline']['home']['price'] == -170, "Wrong moneyline home price"

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - Text extraction logic is working!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
