# Testing Strategy to Prevent Backend-Frontend Mismatches

## Problem We Faced
The recent bug where `querySelector` failed on null elements happened because:
1. **Backend** returned 4 time periods (morning, afternoon, **evening**, night) and 5 opponent categories
2. **Frontend HTML** only had 3 time cards and 3 opponent cards
3. **Unit tests** passed because we tested backend and frontend separately
4. **Integration was never tested end-to-end**

## Solution: Multi-Layer Testing Approach

### 1. **Contract Testing (Schema Validation)**
**File:** `tests/test_contract_validation.py`

**Purpose:** Ensure backend API responses match frontend expectations

**Preparation:**
1. Please read prd_overview_data_analytics.md and iteration folder beofrehand

**Tools:**
- `Pydantic` - Python schema validation library
- Define expected data structures as Pydantic models
- Validate every API response against these schemas

**Benefits:**
- Catches missing fields immediately
- Validates data types
- Ensures nested structure correctness
- Can be part of CI/CD pipeline

**Example:**
```python
class TerminationData(BaseModel):
    total_wins: int
    breakdown: Dict[str, int]  # Frontend expects dict, not nested objects

# This would fail if backend returns wrong structure
validated = TerminationData(**api_response["termination_wins"])
```

**Run with:**
```bash
pytest tests/test_contract_validation.py -v
```

---

### 2. **End-to-End Testing (E2E with Playwright)**
**File:** `tests/test_integration_e2e.py`

**Purpose:** Test actual user workflows in a real browser

**Tools:**
- `Playwright` - Browser automation library (already in your project!)
- Tests real browser interactions
- Catches JavaScript errors
- Validates DOM elements exist

**Benefits:**
- Tests complete flow: UI → API → Rendering
- Catches querySelector errors before users see them
- Verifies charts render correctly
- Detects console.error messages

**Example:**
```python
def test_all_sections_render(page):
    page.fill("#username", "jay_fh")
    page.click("button[type='submit']")
    
    # Would have caught: eveningCard not in DOM
    expect(page.locator("#eveningCard")).to_be_visible()
```

**Run with:**
```bash
# Make sure Flask server is running first
pytest tests/test_integration_e2e.py -v --headed  # See browser
pytest tests/test_integration_e2e.py -v           # Headless for CI/CD
```

---

### 3. **Type Safety (Optional but Recommended)**

#### Backend: Pydantic Models
Already using in contract tests, can extend to API routes:

```python
from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    username: str
    start_date: str
    end_date: str
    timezone: str = "UTC"

@api_bp.route('/analyze/detailed', methods=['POST'])
def analyze_detailed():
    request_data = AnalyzeRequest(**request.json)  # Auto-validates
    # ... rest of code
```

#### Frontend: TypeScript (Future Enhancement)
Convert `analytics.js` → `analytics.ts`:

```typescript
interface TerminationData {
    total_wins: number;
    breakdown: Record<string, number>;
}

interface ApiResponse {
    sections: {
        termination_wins: TerminationData;
        termination_losses: TerminationData;
        // ... compiler ensures all fields exist
    }
}
```

---

### 4. **Visual Regression Testing (Advanced)**

**Tool:** `playwright-pytest` with screenshot comparison

**Purpose:** Catch UI rendering issues automatically

```python
def test_dashboard_screenshot(page, base_url):
    page.goto(f"{base_url}/")
    # ... fill form and submit
    
    # Compare with baseline screenshot
    screenshot = page.screenshot()
    assert screenshot == baseline_screenshot
```

---

## Recommended Testing Workflow

### During Development
```bash
# 1. Run unit tests (fast)
pytest tests/test_analytics_service.py -v

# 2. Run contract validation (catches schema issues)
pytest tests/test_contract_validation.py -v

# 3. Run E2E tests (catches integration issues)
pytest tests/test_integration_e2e.py -v --headed
```

### Before Committing
```bash
# Run all tests
pytest tests/ -v

# Check for console errors
pytest tests/test_integration_e2e.py::TestAnalyticsDashboard::test_form_submission_and_rendering -v
```

### In CI/CD Pipeline
```bash
# GitHub Actions workflow
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Start Flask server
        run: flask run &
        
      - name: Run tests
        run: |
          pytest tests/test_analytics_service.py -v
          pytest tests/test_contract_validation.py -v
          pytest tests/test_integration_e2e.py -v --headed=false
```

---

## Tools Summary

| Tool | Purpose | When to Use | Catches |
|------|---------|-------------|---------|
| **Pytest** | Unit tests | Always | Logic errors, calculation bugs |
| **Pydantic** | Schema validation | API responses | Missing fields, wrong types |
| **Playwright** | E2E browser tests | Before releases | Integration issues, JS errors |
| **TypeScript** | Static typing | New features | Type mismatches at compile time |
| **Visual Regression** | UI consistency | Critical pages | Layout/styling breaks |

---

## Quick Setup

### Install Required Packages
```bash
# Already have Playwright in pyproject.toml
uv add pydantic pytest-playwright

# Install Playwright browsers
playwright install chromium
```

### Run Sample Test
```bash
# Terminal 1: Start Flask server
uv run python run.py

# Terminal 2: Run E2E tests
uv run pytest tests/test_integration_e2e.py -v
```

---

## Benefits of This Approach

✅ **Catches Issues Early**
- Contract tests catch schema mismatches before code reaches production
- E2E tests catch querySelector errors during development

✅ **Confidence in Refactoring**
- Change backend structure? Contract tests tell you what breaks
- Modify frontend? E2E tests verify everything still works

✅ **Documentation**
- Pydantic models serve as living API documentation
- Playwright tests document expected user workflows

✅ **Faster Debugging**
- Test failures point directly to the problem
- No more "works on my machine" issues

---

## What Would Have Prevented Our Bug?

The `querySelector` error would have been caught by:

1. **E2E Test** - `test_all_sections_render()`
   ```python
   expect(page.locator("#eveningCard")).to_be_visible()
   # ❌ FAIL: Element not found
   ```

2. **Contract Test** - `test_time_of_day_structure()`
   ```python
   required_periods = ["morning", "afternoon", "evening", "night"]
   # ✓ Backend has 4 periods
   
   # HTML check would show: only 3 cards exist
   # ❌ Mismatch detected!
   ```

3. **Console Error Detection**
   ```python
   console_errors = []
   page.on("console", lambda msg: console_errors.append(msg))
   # ❌ FAIL: "Cannot read properties of null (reading 'querySelector')"
   ```

---

## Next Steps

1. ✅ **Immediate:** Run the contract validation tests I created
2. ✅ **This Week:** Set up Playwright E2E tests for critical workflows  
3. 📋 **This Month:** Add contract tests to CI/CD pipeline
4. 📋 **Future:** Consider TypeScript migration for type safety

**The key insight:** Test the integration, not just the parts!

---

## Reference Test Case - Known Good Data

This section documents a verified test case with known expected outputs. Use this to validate that the system is working correctly after any changes.

### Test Input

**Username:** `jay_fh`  
**Date Range:** `2026-01-31` to `2026-02-14` (15 days)  
**Timezone:** `Asia/Jakarta` (WIB, GMT+7) ✅  
**Total Games:** 84 games

**⚠️ IMPORTANT:** Time of Day results are timezone-dependent. This test case uses **Asia/Jakarta (GMT+7)** timezone. If you use a different timezone, the time period distributions will be completely different. For consistent testing, always use Asia/Jakarta timezone with this dataset.

---

### Expected Outputs by Section

#### 1. Overall Performance
- **Total Games:** 84
- **Wins:** 45 (53.6%)
- **Losses:** 38 (45.2%)
- **Draws:** 1 (1.2%)

---

#### 2. Performance by Color

**White:**
- **Games:** 42
- **Win Rate:** 50.0%
- **Wins:** 21
- **Losses:** 20
- **Draws:** 1

**Black:**
- **Games:** 42
- **Win Rate:** 57.1% (backend may return 57.14% due to rounding precision)
- **Wins:** 24
- **Losses:** 18
- **Draws:** 0

---

#### 3. How You Win (Termination - Wins)

**Total Wins:** 45

**Breakdown:**
- **resignation:** 25 (55.6%)
- **checkmate:** 10 (22.2%)
- **timeout:** 9 (20.0%)
- **abandoned:** 1 (2.2%)

**Note:** Backend returns termination types in lowercase.

---

#### 4. How You Lose (Termination - Losses)

**Total Losses:** 38

**Breakdown:**
- **resignation:** 24 (63.2%)
- **timeout:** 9 (23.7%)
- **checkmate:** 3 (7.9%)
- **abandoned:** 2 (5.3%)

**Note:** Backend returns termination types in lowercase.

---

#### 5. Opening Performance

Should show separate sections for:
- Most common openings (combined white + black)
- Best performing openings
- Worst performing openings

**Note:** Specific opening names may vary, but should have valid win rates and game counts.

---

#### 6. Opponent Strength Analysis

**Categories with Data:**

**Similar Rated** (±99 rating difference):
- **Games:** 83
- **Win Rate:** 54.2%
- **Wins:** 45
- **Losses:** 37
- **Draws:** 1

**Higher Rated** (+100 to +199 rating difference):
- **Games:** 1
- **Win Rate:** 0.0%
- **Wins:** 0
- **Losses:** 1
- **Draws:** 0

**Lower Rated** (-100 to -199):
- Should show 0 games or not display (if card has null check)

**Much Lower Rated** (<-200):
- Should show 0 games or not display (if card has null check)

**Much Higher Rated** (>+200):
- Should show 0 games or not display (if card has null check)

**Note:** These 84 games are primarily against similarly-rated opponents, with only 1 game against higher-rated.

---

#### 7. Time of Day Performance

**Timezone Used:** Asia/Jakarta (WIB, GMT+7)

**Morning** (6:00 AM - 12:00 PM):
- **Games:** 9
- **Win Rate:** 66.7%
- **Wins:** 6
- **Losses:** 3
- **Draws:** 0

**Afternoon** (12:00 PM - 6:00 PM):
- **Games:** 45
- **Win Rate:** 55.6%
- **Wins:** 25
- **Losses:** 20
- **Draws:** 0

**Evening** (6:00 PM - 10:00 PM):
- **Games:** 15
- **Win Rate:** 46.7%
- **Wins:** 7
- **Losses:** 8
- **Draws:** 0

**Night** (10:00 PM - 6:00 AM):
- **Games:** 15
- **Win Rate:** 46.7%
- **Wins:** 7
- **Losses:** 7
- **Draws:** 1

**Total Across All Periods:** 9 + 45 + 15 + 15 = 84 ✓

**⚠️ Timezone Impact Example:**
- With **Asia/Jakarta (GMT+7):** Morning: 9, Afternoon: 45, Evening: 15, Night: 15
- With **America/New_York (GMT-5):** Morning: 23, Afternoon: 7, Evening: 2, Night: 52
- **12-hour time difference** completely changes the categorization!

---

#### 8. Mistake Analysis by Game Stage

**Status:** ✅ Fixed - Stockfish 16.1 installed and configured

**Configuration:**
- **Stockfish Path:** `stockfish.exe` in project root directory
- **Engine Depth:** 12 (optimized for speed)
- **Time Limit:** 1.5 seconds per position
- **Enabled:** True

**Setup Instructions:**
1. Stockfish 16.1 executable is already downloaded and placed in project root
2. Configuration updated in [config.py](config.py) to use local path
3. Engine analysis enabled by default for mistake analysis

**Expected (when enabled):**
- Opening mistakes (moves 1-7)
- Middlegame mistakes (moves 8-20)
- Endgame mistakes (moves 21+)
- Average centipawn loss by stage
- Inaccuracies, Mistakes, and Blunders counts
- Critical mistake game links

**Note:** Mistake analysis requires games to be analyzed with Stockfish, which takes approximately 1-2 seconds per game. The server uses a sampling strategy (20% of games) for performance. Results are cached for future requests.

---

### Validation Checklist

When running tests with this data, verify:

✅ **Data Totals Match:**
- [ ] Total games = 84
- [ ] Wins + Losses + Draws = 84
- [ ] White games + Black games = 84
- [ ] Time period totals = 84
- [ ] Opponent strength totals = 84

✅ **Win Rates Calculated Correctly:**
- [ ] Overall win rate ≈ 53.6%
- [ ] White win rate = 50.0%
- [ ] Black win rate = 57.1%
- [ ] Time/opponent win rates match expected values

✅ **No JavaScript Errors:**
- [ ] Console shows no errors
- [ ] All sections render (except Mistake Analysis)
- [ ] Charts display correctly
- [ ] Legends show proper data

✅ **UI Elements Present:**
- [ ] 4 time of day cards (morning, afternoon, evening, night)
- [ ] 3 opponent strength cards displayed (similar, higher; lower cards may be empty)
- [ ] 2 termination pie charts (wins and losses)
- [ ] Opening performance tables

---

### Running the Test

#### Manual Testing

1. Start Flask server:
   ```bash
   uv run python run.py
   ```

2. Open browser to `http://127.0.0.1:5000`

3. Fill form:
   - Username: `jay_fh`
   - Start Date: `2026-01-31`
   - End Date: `2026-02-14`
   - Timezone: `America/New_York` (or any)

4. Click "Analyze Performance"

5. Verify each section matches expected outputs above

#### Automated Testing

```bash
# Contract validation (checks API structure)
uv run pytest tests/test_contract_validation.py -v

# E2E testing (checks full workflow)
uv run pytest tests/test_integration_e2e.py::TestAnalyticsDashboard::test_all_sections_render -v

# Backend validation (checks calculations)
uv run pytest tests/test_analytics_debug.py -v
```

#### Quick Verification Script

Create and run this to quickly verify totals:

```python
# test_quick_verify.py
import requests

response = requests.post(
    "http://127.0.0.1:5000/api/analyze/detailed",
    json={
        "username": "jay_fh",
        "start_date": "2026-01-31",
        "end_date": "2026-02-14",
        "timezone": "America/New_York",
        "include_mistake_analysis": False,
        "include_ai_advice": False
    }
)

data = response.json()
sections = data['sections']

print(f"✓ Total Games: {data['total_games']}")
print(f"✓ White Games: {sections['color_performance']['white']['total']}")
print(f"✓ Black Games: {sections['color_performance']['black']['total']}")
print(f"✓ Termination Wins: {sections['termination_wins']['total_wins']}")
print(f"✓ Termination Losses: {sections['termination_losses']['total_losses']}")

time_total = sum(
    sections['time_of_day'][period]['games'] 
    for period in ['morning', 'afternoon', 'evening', 'night']
)
print(f"✓ Time of Day Total: {time_total}")

opponent_total = sum(
    sections['opponent_strength']['by_rating_diff'][cat]['games']
    for cat in ['much_lower', 'lower', 'similar', 'higher', 'much_higher']
)
print(f"✓ Opponent Strength Total: {opponent_total}")

assert data['total_games'] == 84, "Total games mismatch!"
assert time_total == 84, "Time of day total mismatch!"
assert opponent_total == 84, "Opponent strength total mismatch!"

print("\n🎉 All totals validated!")
```

Run with:
```bash
uv run python test_quick_verify.py
```

---

### Notes on Test Data

- **Dataset:** This is real data from Chess.com user `jay_fh` for the specified date range
- **Consistency:** Backend calculations have been verified to match this data
- **Use Case:** Use this as a regression test - any code changes should still produce these exact results
- **Known Issues:** Mistake Analysis section requires Stockfish and is currently not implemented

---

### Test History

**Last Verified:** February 16, 2026  
**Status:** ✅ All sections working except Mistake Analysis  
**Known Issues:**
- Mistake Analysis requires Stockfish setup
- Lower Rated card may be blank (0 games in this dataset)
- Much Lower Rated and Much Higher Rated cards may be blank (0 games in this dataset)
