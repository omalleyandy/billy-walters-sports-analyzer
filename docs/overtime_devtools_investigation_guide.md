# Overtime.ag Chrome DevTools Investigation Guide

## Purpose
This guide provides step-by-step instructions for using Chrome DevTools to analyze Overtime.ag's network requests, validate the API endpoint, and determine the best scraping approach.

## Prerequisites
- Chrome browser installed
- Overtime.ag account credentials
- Access to https://overtime.ag/sports

## Investigation Steps

### 1. Network Tab Analysis

**Objective**: Identify and validate the API endpoint used by Overtime.ag for odds data.

**Steps**:

1. **Open Chrome DevTools**
   - Navigate to https://overtime.ag/sports
   - Press F12 (or Ctrl+Shift+I / Cmd+Option+I)
   - Click the "Network" tab

2. **Filter Network Requests**
   - Click "XHR" or "Fetch" filter to show only API calls
   - Clear existing network logs (trash icon)

3. **Login to Overtime.ag**
   - Login with your credentials
   - Watch for authentication-related requests

4. **Navigate to NFL Section**
   - Click "NFL-Game/1H/2H/Qrts" section
   - Observe network requests that load odds data

5. **Identify GetSportOffering Endpoint**
   - Look for request to: `Api/Offering.asmx/GetSportOffering`
   - Full URL should be: `https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering`
   - Click on this request to inspect details

6. **Document Request Details**

   **Request Headers** (check for):
   - `Content-Type: application/json` (expected)
   - `Cookie:` (authentication cookies - if present, authentication required)
   - `Authorization:` (auth tokens - if present)
   - `User-Agent:` (browser identification)

   **Request Payload** (copy from DevTools):
   ```json
   {
     "sportType": "Football",
     "sportSubType": "NFL",
     "wagerType": "Straight Bet",
     "hoursAdjustment": 0,
     "periodNumber": 0,
     "gameNum": null,
     "parentGameNum": null,
     "teaserName": "",
     "requestMode": "G"
   }
   ```

   **Response Format** (copy from DevTools):
   - Check response structure
   - Look for: `d.Data.GameLines` array
   - Verify game data fields (Team1ID, Team2ID, Spread1, Spread2, etc.)

7. **Test Authentication Requirements**
   - Right-click the request → "Copy as cURL"
   - Open a new incognito window
   - Open DevTools Console
   - Paste and modify the cURL to test without cookies
   - OR: Try the request without logging in first

8. **Measure Response Time**
   - Look at "Time" column in Network tab
   - Typical response time should be < 5 seconds
   - Check "Size" column for response size

### 2. Sources Tab Analysis

**Objective**: Understand how the website uses the API and identify any JavaScript transformations.

**Steps**:

1. **Find JavaScript Files**
   - Open "Sources" tab
   - Navigate to: `overtime.ag/sports` → `js` folder
   - Look for: `overtime_libs.js` or similar

2. **Search for API Call**
   - Press Ctrl+Shift+F (Cmd+Shift+F on Mac) to open search
   - Search for: `GetSportOffering`
   - Note line numbers and surrounding code

3. **Identify Data Transformation**
   - Set breakpoint on API call
   - Reload page and step through code
   - Observe how raw API response is transformed
   - Document any field mappings

### 3. Console Tab Testing

**Objective**: Test API endpoint directly from browser console.

**Steps**:

1. **Open Console Tab**
   - Press F12 → Console tab

2. **Test API Call**
   ```javascript
   // Test NFL endpoint
   fetch('https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       sportType: "Football",
       sportSubType: "NFL",
       wagerType: "Straight Bet",
       hoursAdjustment: 0,
       periodNumber: 0,
       gameNum: null,
       parentGameNum: null,
       teaserName: "",
       requestMode: "G"
     })
   })
   .then(r => r.json())
   .then(data => {
     console.log('Games found:', data.d.Data.GameLines.length);
     console.log('First game:', data.d.Data.GameLines[0]);
   });
   ```

3. **Test NCAAF Endpoint**
   ```javascript
   // Test NCAAF endpoint
   fetch('https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       sportType: "Football",
       sportSubType: "College Football",
       wagerType: "Straight Bet",
       hoursAdjustment: 0,
       periodNumber: 0,
       gameNum: null,
       parentGameNum: null,
       teaserName: "",
       requestMode: "G"
     })
   })
   .then(r => r.json())
   .then(data => {
     console.log('Games found:', data.d.Data.GameLines.length);
     console.log('First game:', data.d.Data.GameLines[0]);
   });
   ```

4. **Check for Errors**
   - Watch for CORS errors (cross-origin restrictions)
   - Watch for authentication errors (401/403)
   - Watch for rate limiting (429)

### 4. Performance Tab Analysis

**Objective**: Understand page load performance and identify bottlenecks.

**Steps**:

1. **Record Performance Profile**
   - Open Performance tab
   - Click record button (circle icon)
   - Refresh page
   - Wait for odds to load
   - Stop recording

2. **Analyze Network Waterfall**
   - Look for `GetSportOffering` request timing
   - Check if CloudFlare challenge occurs (look for `cf_clearance` cookie)
   - Identify blocking resources

3. **Check for Rate Limiting**
   - Look for multiple rapid API calls
   - Check if any requests fail or get throttled

## Documentation Template

After completing the investigation, document your findings using this template:

```markdown
# Overtime.ag DevTools Analysis Results

**Date**: [YYYY-MM-DD]
**Investigator**: [Your Name]

## Network Analysis

### API Endpoint
- URL: `https://overtime.ag/sports/Api/Offering.asmx/GetSportOffering`
- Method: POST
- Content-Type: application/json

### Authentication Requirements
- [ ] No authentication required
- [ ] Requires cookies (which cookies?)
- [ ] Requires auth token (which header?)

### Request Payload (NFL)
```json
[paste actual payload from DevTools]
```

### Request Payload (NCAAF)
```json
[paste actual payload from DevTools]
```

### Response Structure
```json
[paste sample response from DevTools]
```

### Response Time
- Average: X seconds
- Min: X seconds
- Max: X seconds

### Response Size
- Average: X KB

## Sources Analysis

### JavaScript Files
- Main file: [filename]
- Line number: [where GetSportOffering is called]

### Data Transformation
[Describe how raw API data is transformed]

## Console Testing

### NFL Test Result
- [ ] Successful
- [ ] Failed (reason: ...)
- Games returned: X

### NCAAF Test Result
- [ ] Successful
- [ ] Failed (reason: ...)
- Games returned: X

### Errors Observed
[List any errors]

## Performance Analysis

### Page Load Time
- Total: X seconds
- API call time: X seconds

### CloudFlare Challenge
- [ ] No challenge observed
- [ ] Challenge observed (describe)

### Rate Limiting
- [ ] No rate limiting observed
- [ ] Rate limiting observed (describe)

## Recommendations

### Primary Scraper
- [ ] API Client (scrape_overtime_api.py)
- [ ] Hybrid Scraper (scrape_overtime_hybrid.py)

### Reasoning
[Explain why based on findings]

### Implementation Notes
[Any changes needed to API client based on findings]
```

## Next Steps

After completing this investigation:

1. Save your findings to: `docs/overtime_devtools_analysis_results.md`
2. Test the API scraper: `uv run python scripts/scrapers/scrape_overtime_api.py --nfl --ncaaf`
3. Compare outputs with hybrid scraper
4. Update documentation with final recommendation

## Troubleshooting

### "Request blocked by CORS"
- This is expected when calling from console
- Means authentication might be required
- Try the Python API client instead

### "No games found"
- Check timing: lines only available Tuesday-Thursday
- Verify you're logged in
- Check if games are actually scheduled

### "401 Unauthorized"
- Authentication is required
- Need to include cookies or tokens
- API client may need updates

### "CloudFlare challenge"
- Browser shows "Checking your browser" message
- Indicates anti-bot protection
- May require browser automation (Playwright)

## Chrome DevTools AI Assistance

Chrome has built-in AI assistance for DevTools. To use it:

1. Right-click on network request → "Ask AI"
2. Prompts to try:
   - "Does this request have any notable headers?"
   - "Why is this request taking so long?"
   - "What is this endpoint used for?"

This can help identify authentication requirements and performance issues automatically.

