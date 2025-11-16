#!/usr/bin/env python3
"""Analyze NCAAF Week 12 results"""

# Complete results for all 15 games
games = [
    # MAX BET (3 games)
    {
        'class': 'MAX BET', 'edge': 12.1,
        'pick': 'Sam Houston St -9.5', 'team': 'Sam Houston St',
        'away': 'Delaware', 'home': 'Sam Houston', 'away_score': 23, 'home_score': 26,
        'spread': -9.5, 'is_fav': True
    },
    {
        'class': 'MAX BET', 'edge': 8.4,
        'pick': 'Boston College -16.5', 'team': 'Boston College',
        'away': 'Georgia Tech', 'home': 'Boston College', 'away_score': 36, 'home_score': 34,
        'spread': -16.5, 'is_fav': True
    },
    {
        'class': 'MAX BET', 'edge': 7.0,
        'pick': 'South Carolina +19.0', 'team': 'South Carolina',
        'away': 'South Carolina', 'home': 'Texas A&M', 'away_score': 30, 'home_score': 31,
        'spread': 19.0, 'is_fav': False
    },

    # STRONG (6 games)
    {
        'class': 'STRONG', 'edge': 6.8,
        'pick': 'Wisconsin +29.5', 'team': 'Wisconsin',
        'away': 'Wisconsin', 'home': 'Indiana', 'away_score': 7, 'home_score': 31,
        'spread': 29.5, 'is_fav': False
    },
    {
        'class': 'STRONG', 'edge': 6.5,
        'pick': 'Navy -10.0', 'team': 'Navy',
        'away': 'South Florida', 'home': 'Navy', 'away_score': 38, 'home_score': 41,
        'spread': -10.0, 'is_fav': True
    },
    {
        'class': 'STRONG', 'edge': 6.3,
        'pick': 'UAB -18.5', 'team': 'UAB',
        'away': 'North Texas', 'home': 'UAB', 'away_score': 53, 'home_score': 24,
        'spread': -18.5, 'is_fav': True
    },
    {
        'class': 'STRONG', 'edge': 5.5,
        'pick': 'Alabama -6.0', 'team': 'Alabama',
        'away': 'Oklahoma', 'home': 'Alabama', 'away_score': 23, 'home_score': 21,
        'spread': -6.0, 'is_fav': True
    },
    {
        'class': 'STRONG', 'edge': 4.7,
        'pick': 'Troy +11.0', 'team': 'Troy',
        'away': 'Troy', 'home': 'Old Dominion', 'away_score': None, 'home_score': None,
        'spread': 11.0, 'is_fav': False
    },
    {
        'class': 'STRONG', 'edge': 4.1,
        'pick': 'Maryland +14.5', 'team': 'Maryland',
        'away': 'Maryland', 'home': 'Illinois', 'away_score': 6, 'home_score': 24,
        'spread': 14.5, 'is_fav': False
    },

    # MODERATE (5 games)
    {
        'class': 'MODERATE', 'edge': 3.6,
        'pick': 'LSU -5.5', 'team': 'LSU',
        'away': 'Arkansas', 'home': 'LSU', 'away_score': 22, 'home_score': 23,
        'spread': -5.5, 'is_fav': True
    },
    {
        'class': 'MODERATE', 'edge': 3.1,
        'pick': 'Air Force +7.0', 'team': 'Air Force',
        'away': 'Air Force', 'home': 'Connecticut', 'away_score': 16, 'home_score': 26,
        'spread': 7.0, 'is_fav': False
    },
    {
        'class': 'MODERATE', 'edge': 2.8,
        'pick': 'Memphis +3.0', 'team': 'Memphis',
        'away': 'Memphis', 'home': 'East Carolina', 'away_score': 27, 'home_score': 31,
        'spread': 3.0, 'is_fav': False
    },
    {
        'class': 'MODERATE', 'edge': 2.7,
        'pick': 'Missouri St -4.5', 'team': 'Missouri St',
        'away': 'UTEP', 'home': 'Missouri St', 'away_score': 24, 'home_score': 38,
        'spread': -4.5, 'is_fav': True
    },
    {
        'class': 'MODERATE', 'edge': 2.4,
        'pick': 'Minnesota +25.0', 'team': 'Minnesota',
        'away': 'Minnesota', 'home': 'Oregon', 'away_score': 13, 'home_score': 42,
        'spread': 25.0, 'is_fav': False
    },

    # LEAN (1 game)
    {
        'class': 'LEAN', 'edge': 1.5,
        'pick': 'North Carolina +6.0', 'team': 'North Carolina',
        'away': 'North Carolina', 'home': 'Wake Forest', 'away_score': 12, 'home_score': 28,
        'spread': 6.0, 'is_fav': False
    }
]

print('=' * 80)
print('NCAAF WEEK 12 - Billy Walters Edge Detection Results')
print('Generated: 11/12/2025 | Results as of: 11/15/2025 Evening')
print('=' * 80)
print()

# Calculate results by classification
results_by_class = {}
wins_total = 0
losses_total = 0
pending_total = 0

for g in games:
    if g['away_score'] is None:
        status = 'PENDING'
        pending_total += 1
    else:
        # Calculate margin (positive = home won)
        margin = g['home_score'] - g['away_score']

        if g['is_fav']:
            # Favorite needs to cover the spread
            if g['team'] == g['home']:
                covered = margin > abs(g['spread'])
            else:
                covered = -margin > abs(g['spread'])
        else:
            # Underdog covers if loses by less than spread
            if g['team'] == g['away']:
                covered = margin < g['spread']
            else:
                covered = -margin < g['spread']

        status = 'WIN' if covered else 'LOSS'

        if covered:
            wins_total += 1
        else:
            losses_total += 1

    # Track by classification
    if g['class'] not in results_by_class:
        results_by_class[g['class']] = {'wins': 0, 'losses': 0, 'pending': 0, 'games': []}

    if status == 'WIN':
        results_by_class[g['class']]['wins'] += 1
    elif status == 'LOSS':
        results_by_class[g['class']]['losses'] += 1
    else:
        results_by_class[g['class']]['pending'] += 1

    results_by_class[g['class']]['games'].append((g, status))

# Display results by classification
for classification in ['MAX BET', 'STRONG', 'MODERATE', 'LEAN']:
    if classification not in results_by_class:
        continue

    data = results_by_class[classification]
    wins = data['wins']
    losses = data['losses']
    pending = data['pending']
    total_decided = wins + losses

    print(f'=== {classification} ===')
    if total_decided > 0:
        win_pct = wins / total_decided * 100
        print(f'Record: {wins}-{losses} ({win_pct:.1f}%)')
    else:
        print(f'Record: All games pending')
    print()

    for game, status in data['games']:
        if game['away_score'] is not None:
            score_str = f'{game["away_score"]}-{game["home_score"]}'
        else:
            score_str = 'TBD'

        symbol = '[OK]' if status == 'WIN' else '[X]' if status == 'LOSS' else '[-]'

        print(f'{symbol} {game["pick"]} (Edge: {game["edge"]} pts)')
        print(f'    {game["away"]} @ {game["home"]}: {score_str} - {status}')

    print()

print('=' * 80)
print('OVERALL RESULTS')
print('=' * 80)
total_decided = wins_total + losses_total
if total_decided > 0:
    overall_pct = wins_total / total_decided * 100
    print(f'Record: {wins_total}-{losses_total} ({overall_pct:.1f}%)')
    print(f'Pending: {pending_total} games')
else:
    print('All games pending')
print()

# Billy Walters analysis
print('BILLY WALTERS METHODOLOGY NOTES:')
print('- Success metric is CLV (Closing Line Value), not win percentage')
print('- Expected win rate for these edge sizes: 54-77%')
print('- Sample size of 14-15 games is NOT statistically significant')
print('- Need 200+ bets to evaluate model accuracy')
print('=' * 80)
