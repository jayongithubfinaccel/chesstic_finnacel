# Iteration 13 Summary - YouTube Video Learning for Opening Performance

**Date:** March 7, 2026  
**Version:** PRD v2.12  
**Status:** 📋 Ready for Implementation

---

## Overview

This iteration adds a "Video Learning" button to the Opening Performance section, allowing users to directly access educational chess videos for the openings they play. Videos are sourced from the Remote Chess Academy channel by GM Igor Smirnov (https://www.youtube.com/@GMIgorSmirnov).

**Key changes:**
1. **Video Learning button** — added next to the existing "Example Game" button in each opening row
2. **YouTube channel search URL** — constructed client-side using the opening name, no API key required
3. **Fallback URL** — https://www.youtube.com/watch?v=gxfBW41YD14 for unknown/missing opening names
4. **CSS styling** — blue button variant to visually distinguish from existing link buttons

**Scope:** Frontend only. No backend changes required.

---

## Feature Description

### EA-027: Video Learning Button

When a user reviews their opening statistics in the Opening Performance section, a new "📺 Video Learning" button appears next to the "🔗 Example Game" button on each opening row. Clicking it opens a new browser tab with a YouTube search filtered to the Remote Chess Academy channel, using the opening name as the search query.

**Channel:** Remote Chess Academy by GM Igor Smirnov  
**Channel URL:** https://www.youtube.com/@GMIgorSmirnov  
**Fallback video:** https://www.youtube.com/watch?v=gxfBW41YD14  

---

## Change 1: Video Learning Button — Frontend

### Problem Statement
The Opening Performance section shows statistics and an example game link, but provides no educational path forward. Players can see they play the Sicilian Defense 20 times but have no quick way to find instructional content for that opening.

### Solution
Add a "📺 Video Learning" button that constructs a YouTube channel search URL on the fly using the opening name. No YouTube API key is required — YouTube supports public channel search via URL:

```
https://www.youtube.com/@GMIgorSmirnov/search?query={encoded_opening_name}
```

This surfaces the most relevant videos from the channel for that opening, and stays current as new videos are published.

### Matching Logic

| Scenario | Behaviour |
|---|---|
| Opening name is present | Redirect to channel search URL with opening name as query |
| Opening name is null or empty | Redirect to fallback video URL |
| Channel has no match | YouTube shows its own "no results" or closest match |

### Implementation

#### File: `static/js/analytics.js`

**Step 1 — Add helper function** (place near the top of the opening section, before `renderOpeningsTable`):

```javascript
/**
 * EA-027: Returns YouTube channel search URL for Remote Chess Academy.
 * Falls back to a default video if opening name is missing.
 */
function getVideoLearningUrl(openingName) {
    if (!openingName || openingName.trim() === '') {
        return 'https://www.youtube.com/watch?v=gxfBW41YD14';
    }
    const encoded = encodeURIComponent(openingName.trim());
    return `https://www.youtube.com/@GMIgorSmirnov/search?query=${encoded}`;
}
```

**Step 2 — Add button inside `renderOpeningsTable()`**, next to the existing `example_game_url` link:

```javascript
// Before (existing code):
${opening.example_game_url ? `<a href="${opening.example_game_url}" target="_blank" class="opening-link">🔗 Example Game</a>` : ''}

// After:
${opening.example_game_url ? `<a href="${opening.example_game_url}" target="_blank" class="opening-link">🔗 Example Game</a>` : ''}
<a href="${getVideoLearningUrl(opening.opening)}" target="_blank" class="opening-link opening-link-video">📺 Video Learning</a>
```

> Note: The Video Learning button is always rendered (not conditional) since it always has either the channel search URL or the fallback URL.

#### File: `static/css/style.css`

Add a blue variant style for the Video Learning button beneath existing `.opening-link` styles:

```css
/* EA-027: Video Learning button — blue variant */
.opening-link-video {
    background-color: #3498db;
    color: white !important;
}
.opening-link-video:hover {
    background-color: #2980b9;
    color: white !important;
}
```

---

## No Backend Changes Required

This is a **purely frontend feature**. The YouTube channel search URL is constructed entirely in the browser using the opening name already present in the API response (`opening.opening` field). No new API endpoints, no new config variables, no server-side YouTube API calls.

---

## URL Examples

| Opening | Generated URL |
|---|---|
| Sicilian Defense | `https://www.youtube.com/@GMIgorSmirnov/search?query=Sicilian%20Defense` |
| Queen's Gambit | `https://www.youtube.com/@GMIgorSmirnov/search?query=Queen's%20Gambit` |
| Ruy Lopez | `https://www.youtube.com/@GMIgorSmirnov/search?query=Ruy%20Lopez` |
| King's Indian Defense | `https://www.youtube.com/@GMIgorSmirnov/search?query=King's%20Indian%20Defense` |
| *(empty/null)* | `https://www.youtube.com/watch?v=gxfBW41YD14` |

---

## Files Changed

| File | Change Type | Description |
|---|---|---|
| `static/js/analytics.js` | Modified | Add `getVideoLearningUrl()` helper; add Video Learning button in `renderOpeningsTable()` |
| `static/css/style.css` | Modified | Add `.opening-link-video` blue button style |

---

## Testing Plan

### Manual / Unit Tests

| Test | Expected Result |
|---|---|
| Open analytics page with a username that has opening data | "📺 Video Learning" button appears in every opening row |
| Click "Video Learning" on a White opening | New tab opens with `https://www.youtube.com/@GMIgorSmirnov/search?query=<opening>` |
| Click "Video Learning" on a Black opening | New tab opens with `https://www.youtube.com/@GMIgorSmirnov/search?query=<opening>` |
| Opening name has spaces (e.g., "Queen's Gambit") | URL is properly encoded: `Queen's%20Gambit` |
| Opening name is empty string | Fallback URL `https://www.youtube.com/watch?v=gxfBW41YD14` |
| Inspect button styling | Blue background (#3498db), consistent size with other opening-link buttons |
| Verify no same-tab navigation | Button uses `target="_blank"`, user stays on analytics page |

### E2E Tests (Playwright)

```python
# Suggested Playwright test additions for tests/test_integration_e2e.py

def test_opening_video_learning_button_exists(page):
    """EA-027: Video Learning button renders in opening rows."""
    # ... navigate to analytics page with test username and date range ...
    video_buttons = page.locator('a.opening-link-video')
    assert video_buttons.count() > 0

def test_opening_video_learning_url_format(page):
    """EA-027: Video Learning button URL contains channel search path."""
    first_button = page.locator('a.opening-link-video').first
    href = first_button.get_attribute('href')
    assert '@GMIgorSmirnov/search?query=' in href

def test_opening_video_learning_opens_new_tab(page):
    """EA-027: Video Learning button opens in new tab."""
    first_button = page.locator('a.opening-link-video').first
    assert first_button.get_attribute('target') == '_blank'
```

---

## Acceptance Criteria

- [ ] "📺 Video Learning" button appears next to "🔗 Example Game" button for every opening row
- [ ] Button opens a new browser tab (does not navigate away from the analytics page)
- [ ] URL uses format: `https://www.youtube.com/@GMIgorSmirnov/search?query={encoded_opening_name}`
- [ ] Opening name is properly URL-encoded
- [ ] Fallback to `https://www.youtube.com/watch?v=gxfBW41YD14` when opening name is null or empty
- [ ] Button renders for both White openings table and Black openings table
- [ ] Blue button styling (`.opening-link-video`) distinguishes it visually from the grey/default link button
- [ ] No backend API call or YouTube API key is required

---

## Rollback Plan

Rollback is trivial — remove the `getVideoLearningUrl()` function and the Video Learning `<a>` tag from `renderOpeningsTable()`, and remove the `.opening-link-video` CSS rule. No backend or config changes to revert.

---

## Related PRD Sections

- **PRD v2.12, Iteration 13 changelog entry** — `prd_overview_data_analysis.md`
- **EA-027** — Video Learning button user story and acceptance criteria
- **Section 6: Opening Performance Analysis** (EA-006/EA-016) — parent feature
