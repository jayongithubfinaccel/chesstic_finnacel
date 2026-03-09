# Iteration 14 Summary - Unified Performance Chart & Placeholder Update

**Date:** March 9, 2026  
**Version:** PRD v2.13  
**Status:** 📋 Ready for Implementation

---

## Overview

This iteration consolidates the performance visualizations by merging Section 1 (Overall Performance) and Section 2 (Color Performance) into a single unified chart displaying three lines: overall win rate, White win rate, and Black win rate. Additionally, the username placeholder is updated from "jay_fh" to "hikaru" (GM Hikaru Nakamura's username) for better user guidance.

**Key changes:**
1. **Unified performance chart** — merge Section 1 and Section 2 into single chart with 3 lines
2. **Updated placeholder** — change "e.g., jay_fh" to "e.g., hikaru"
3. **Section renumbering** — sections 3-10 become sections 2-9

**Scope:** Frontend only. No backend changes required.

---

## Feature Description

### EA-028: Unified Performance Chart

Previously, users had to scroll between Section 1 (Overall Performance with win rate %) and Section 2 (Color Performance with White/Black win rates) to compare their overall and color-specific performance. This created visual fragmentation and required mental comparison across two separate charts.

The new unified chart displays all three metrics in a single visualization:
- **Overall win rate** (blue line, #3498db) — shows aggregate performance across all games
- **White win rate** (light gray line, #95a5a6) — shows performance when playing as White
- **Black win rate** (dark gray line, #34495e) — shows performance when playing as Black

White and Black summary cards remain above the chart to provide aggregate statistics.

### EA-029: Username Placeholder Update

The placeholder text "e.g., jay_fh" is updated to "e.g., hikaru" — a more recognizable Chess.com username belonging to GM Hikaru Nakamura. This provides better user guidance and a more professional appearance.

---

## Change 1: Unified Performance Chart — Frontend

### Problem Statement
Having two separate sections for overall and color-specific performance causes:
- **Visual fragmentation** — users must scroll to compare metrics
- **Cognitive load** — mental comparison required across separate charts
- **Wasted space** — two chart containers for related data
- **Inconsistent design** — Section 1 shows 1 line, Section 2 shows 2 lines

### Solution
Merge both sections into a single chart with three lines:
1. Calculate overall win rate from `data.daily_stats`
2. Reuse existing White/Black win rate calculations from Section 2
3. Add overall win rate as third dataset in Chart.js configuration
4. Update tooltips to distinguish between overall/White/Black
5. Remove Section 1 HTML entirely
6. Update Section 2 heading to reflect unified data

### Visual Design

**Chart configuration:**
- 3 line datasets with distinct colors:
  - Overall: Blue (#3498db) with light fill
  - White: Light gray (#95a5a6)
  - Black: Dark gray (#34495e)
- Chart legend displays all three labels
- Y-axis: "Win Rate %" (0-100% scale)
- X-axis: Date labels
- Responsive design maintained

**Summary cards:**
- White summary card (existing)
- Black summary card (existing)
- Overall statistics displayed in header card or new summary card (optional)

### Implementation

#### File: `templates/analytics.html`

**Step 1 — Remove Section 1 HTML entirely**

Delete the entire section containing `overallPerformanceChart`:

```html
<!-- REMOVE THIS ENTIRE SECTION -->
<section class="analytics-section">
    <div class="section-card">
        <div class="section-header">
            <h3>📈 Overall Performance Over Time</h3>
            <p class="section-description">Track your win rate percentage trend over the analysis period</p>
        </div>
        <div class="chart-container">
            <canvas id="overallPerformanceChart"></canvas>
        </div>
    </div>
</section>
```

**Step 2 — Update Section 2 heading and description**

```html
<!-- UPDATE Section 2 (was Section 3) -->
<section class="analytics-section">
    <div class="section-card">
        <div class="section-header">
            <h3>📈 Performance Over Time</h3>
            <p class="section-description">Track your overall and color-specific win rates over time</p>
        </div>
        
        <!-- Existing summary cards -->
        <div class="color-summary-grid">
            <div class="color-summary-card white-card">
                <h4>⚪ White</h4>
                <div class="color-stats" id="whiteSummary"></div>
            </div>
            <div class="color-summary-card black-card">
                <h4>⚫ Black</h4>
                <div class="color-stats" id="blackSummary"></div>
            </div>
        </div>
        
        <!-- Unified chart (existing canvas, now with 3 lines) -->
        <div class="chart-container">
            <canvas id="colorPerformanceChart"></canvas>
        </div>
    </div>
</section>
```

**Step 3 — Update username placeholder**

```html
<!-- BEFORE: -->
<input type="text" id="username" name="username" placeholder="e.g., jay_fh" required>

<!-- AFTER: -->
<input type="text" id="username" name="username" placeholder="e.g., hikaru" required>
```

#### File: `static/js/analytics.js`

**Step 1 — Remove `renderOverallPerformance()` function call**

In the `renderDashboard()` function, remove the call to `renderOverallPerformance()`:

```javascript
async function renderDashboard(data) {
    // ... existing code ...
    
    // REMOVE THIS LINE:
    // await renderOverallPerformance(data.sections.overall_performance);
    
    // Keep this line (now renders unified chart):
    await renderColorPerformance(data.sections.color_performance);
    
    // ... rest of function ...
}
```

**Step 2 — Update `renderUnifiedColorChart()` to include overall win rate**

Modify the existing `renderUnifiedColorChart()` function to add a third dataset:

```javascript
function renderUnifiedColorChart(data) {
    // Existing code to get all dates
    const allDates = Array.from(new Set([
        ...data.white.daily_stats.map(d => d.date),
        ...data.black.daily_stats.map(d => d.date)
    ])).sort();
    
    // NEW: Calculate overall win rate from main data
    // Assuming data.overall_daily_stats exists in the API response
    // OR calculate by combining white + black data
    const overallWinRates = allDates.map(date => {
        const whiteStat = data.white.daily_stats.find(d => d.date === date);
        const blackStat = data.black.daily_stats.find(d => d.date === date);
        
        const whiteWins = whiteStat ? whiteStat.wins : 0;
        const whiteLosses = whiteStat ? whiteStat.losses : 0;
        const whiteDraws = whiteStat ? whiteStat.draws : 0;
        const blackWins = blackStat ? blackStat.wins : 0;
        const blackLosses = blackStat ? blackStat.losses : 0;
        const blackDraws = blackStat ? blackStat.draws : 0;
        
        const totalWins = whiteWins + blackWins;
        const totalLosses = whiteLosses + blackLosses;
        const totalDraws = whiteDraws + blackDraws;
        const totalGames = totalWins + totalLosses + totalDraws;
        
        return totalGames > 0 ? ((totalWins / totalGames) * 100).toFixed(1) : 0;
    });
    
    // Store detailed data for overall tooltips
    const overallDetails = allDates.map(date => {
        const whiteStat = data.white.daily_stats.find(d => d.date === date);
        const blackStat = data.black.daily_stats.find(d => d.date === date);
        
        return {
            wins: (whiteStat?.wins || 0) + (blackStat?.wins || 0),
            losses: (whiteStat?.losses || 0) + (blackStat?.losses || 0),
            draws: (whiteStat?.draws || 0) + (blackStat?.draws || 0)
        };
    });
    
    // Existing White and Black calculations
    const whiteWinRates = allDates.map(date => {
        const stat = data.white.daily_stats.find(d => d.date === date);
        if (!stat) return 0;
        const total = stat.wins + stat.losses + stat.draws;
        return total > 0 ? ((stat.wins / total) * 100).toFixed(1) : 0;
    });
    
    const blackWinRates = allDates.map(date => {
        const stat = data.black.daily_stats.find(d => d.date === date);
        if (!stat) return 0;
        const total = stat.wins + stat.losses + stat.draws;
        return total > 0 ? ((stat.wins / total) * 100).toFixed(1) : 0;
    });
    
    // Existing White and Black detail arrays
    const whiteDetails = allDates.map(date => {
        const stat = data.white.daily_stats.find(d => d.date === date);
        return stat || { wins: 0, losses: 0, draws: 0 };
    });
    
    const blackDetails = allDates.map(date => {
        const stat = data.black.daily_stats.find(d => d.date === date);
        return stat || { wins: 0, losses: 0, draws: 0 };
    });
    
    const ctx = document.getElementById('colorPerformanceChart');
    charts.colorPerformance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allDates,
            datasets: [
                // NEW: Overall win rate line
                {
                    label: 'Overall Win Rate',
                    data: overallWinRates,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                // Existing White line
                {
                    label: 'White Win Rate',
                    data: whiteWinRates,
                    borderColor: '#95a5a6',
                    backgroundColor: 'rgba(149, 165, 166, 0.1)',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                // Existing Black line
                {
                    label: 'Black Win Rate',
                    data: blackWinRates,
                    borderColor: '#34495e',
                    backgroundColor: 'rgba(52, 73, 94, 0.1)',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        boxWidth: 40,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        title: (context) => formatDate(context[0].label),
                        label: (context) => {
                            const index = context.dataIndex;
                            const datasetIndex = context.datasetIndex;
                            
                            // Determine which line was hovered
                            let details, label;
                            if (datasetIndex === 0) {
                                // Overall
                                details = overallDetails[index];
                                label = 'Overall';
                            } else if (datasetIndex === 1) {
                                // White
                                details = whiteDetails[index];
                                label = 'White';
                            } else {
                                // Black
                                details = blackDetails[index];
                                label = 'Black';
                            }
                            
                            return [
                                `${label} Win Rate: ${context.parsed.y}%`,
                                `Wins: ${details.wins}`,
                                `Losses: ${details.losses}`,
                                `Draws: ${details.draws}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Win Rate %'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}
```

**Step 3 — Delete `renderOverallPerformance()` function**

The entire function can be removed since its functionality is now merged into `renderUnifiedColorChart()`.

#### File: `static/css/style.css`

**Optional — Adjust section spacing**

If needed, adjust spacing to account for the removed section:

```css
/* Ensure proper spacing after removing Section 1 */
.analytics-section:first-of-type {
    margin-top: 2rem;
}
```

---

## Change 2: Update Username Placeholder — Frontend

### Problem Statement
The current placeholder "e.g., jay_fh" is not widely recognizable and may confuse new users about what type of username to enter.

### Solution
Update placeholder to "e.g., hikaru" — GM Hikaru Nakamura's Chess.com username, which is:
- Widely recognized in the chess community
- Active Chess.com user with public profile
- Professional and aspirational reference

### Implementation

Already shown in HTML changes above (Step 3).

---

## Section Renumbering

With Section 1 removed and merged into Section 2, all subsequent sections shift up by one:

| Old Section | New Section | Title |
|---|---|---|
| Section 1 | *(removed)* | Overall Performance Over Time |
| Section 2 | Section 1 | Performance Over Time (Unified) |
| Section 3 | Section 2 | Elo Rating Progression |
| Sections 4 & 5 | Sections 3 & 4 | How You Win / How You Lose |
| Section 6 | Section 5 | Opening Performance |
| Section 7 | Section 6 | Opponent Strength Analysis |
| Section 8 | Section 7 | Time of Day Performance |
| Section 9 | Section 8 | Mistake Analysis by Game Stage |
| Section 10 | Section 9 | AI Chess Coach |

**Note:** This renumbering is primarily for documentation clarity. The actual HTML structure order automatically handles the visual numbering. Update any hardcoded section references in comments or documentation.

---

## No Backend Changes Required

This is a **purely frontend feature**. The data required for the overall win rate is already available in the analytics response:
- `data.sections.overall_performance.daily_stats` (existing)
- OR calculated by combining White and Black daily stats

No new API fields, no new config variables, no backend service changes.

---

## Files Changed

| File | Change Type | Description |
|---|---|---|
| `templates/analytics.html` | Modified | Remove Section 1, update Section 2 heading, update placeholder |
| `static/js/analytics.js` | Modified | Remove `renderOverallPerformance()` function and call; add overall dataset to `renderUnifiedColorChart()` |
| `static/css/style.css` | Modified (optional) | Adjust section spacing if needed |
| `prd_overview_data_analysis.md` | Modified | Add Iteration 14, update version to 2.13, update diagram |

---

## Testing Plan

### Manual / Unit Tests

| Test | Expected Result |
|---|---|
| Load analytics page with valid username | Section 1 no longer exists; Section 2 is the first section |
| Verify unified chart renders | Chart displays 3 lines: Overall (blue), White (gray), Black (dark) |
| Verify chart legend | Legend shows "Overall Win Rate", "White Win Rate", "Black Win Rate" |
| Hover over Overall line | Tooltip shows: Date, Overall Win Rate %, Wins, Losses, Draws |
| Hover over White line | Tooltip shows: Date, White Win Rate %, Wins, Losses, Draws |
| Hover over Black line | Tooltip shows: Date, Black Win Rate %, Wins, Losses, Draws |
| Verify summary cards | White and Black summary cards display above chart with correct stats |
| Check placeholder text | Username input shows "e.g., hikaru" |
| Test mobile responsiveness | Chart remains readable and responsive on small screens |
| Verify no JavaScript errors | Console shows no errors during render |

### E2E Tests (Playwright)

```python
# Suggested Playwright test additions for tests/test_integration_e2e.py

def test_unified_performance_chart_renders(page):
    """EA-028: Unified chart with 3 lines renders correctly."""
    # ... navigate to analytics page with test username and date range ...
    
    # Verify Section 1 (old Overall Performance) does not exist
    section_1 = page.locator('canvas#overallPerformanceChart')
    assert section_1.count() == 0
    
    # Verify Section 2 chart exists
    unified_chart = page.locator('canvas#colorPerformanceChart')
    assert unified_chart.count() == 1
    
def test_unified_chart_has_three_lines(page):
    """EA-028: Chart displays Overall, White, and Black lines."""
    # Use Chart.js API to verify 3 datasets
    dataset_count = page.evaluate('''
        const chart = Chart.getChart('colorPerformanceChart');
        return chart ? chart.data.datasets.length : 0;
    ''')
    assert dataset_count == 3

def test_unified_chart_legend_labels(page):
    """EA-028: Legend shows correct labels for 3 lines."""
    labels = page.evaluate('''
        const chart = Chart.getChart('colorPerformanceChart');
        return chart ? chart.data.datasets.map(ds => ds.label) : [];
    ''')
    assert 'Overall Win Rate' in labels
    assert 'White Win Rate' in labels
    assert 'Black Win Rate' in labels

def test_username_placeholder_updated(page):
    """EA-029: Username placeholder is 'hikaru'."""
    page.goto('/analytics')
    placeholder = page.get_attribute('input#username', 'placeholder')
    assert placeholder == 'e.g., hikaru'
```

---

## Acceptance Criteria

### EA-028: Unified Performance Chart

- [ ] Section 1 (Overall Performance Over Time) is removed from the analytics page
- [ ] Section 2 (now first section) displays a unified chart with 3 lines
- [ ] Chart legend clearly distinguishes: Overall Win Rate, White Win Rate, Black Win Rate
- [ ] Overall line styled with blue color (#3498db)
- [ ] White line styled with light gray (#95a5a6)
- [ ] Black line styled with dark gray (#34495e)
- [ ] Tooltips show metric-specific data on hover (date, win rate %, W/L/D)
- [ ] White and Black summary cards remain above the chart
- [ ] Chart maintains responsive design on all screen sizes
- [ ] No JavaScript console errors during render

### EA-029: Username Placeholder

- [ ] Username input placeholder text is "e.g., hikaru"
- [ ] Placeholder displays correctly on page load
- [ ] No functional changes to form validation or submission

---

## Rollback Plan

Rollback is straightforward:

1. **Restore Section 1 HTML** — add back the `overallPerformanceChart` section in `templates/analytics.html`
2. **Restore `renderOverallPerformance()` function** — uncomment or restore function in `analytics.js`
3. **Restore function call** — add back `await renderOverallPerformance(...)` in `renderDashboard()`
4. **Remove overall dataset** — remove the third dataset from `renderUnifiedColorChart()`
5. **Revert placeholder** — change "hikaru" back to "jay_fh" (if desired)

No backend or config changes to revert.

---

## Benefits

1. **Reduced visual clutter** — fewer sections, single comprehensive chart
2. **Easier comparison** — all three metrics visible at once
3. **Better UX** — less scrolling, immediate insights
4. **Consistent design** — unified chart matches modern dashboard patterns
5. **Professional appearance** — recognizable placeholder improves first impressions

---

## Related PRD Sections

- **PRD v2.13, Iteration 14 changelog entry** — `prd_overview_data_analysis.md`
- **EA-028** — Unified Performance Chart user story
- **EA-029** — Username Placeholder Update user story
- **Website Overview / Page Structure** — Updated diagram showing merged sections
