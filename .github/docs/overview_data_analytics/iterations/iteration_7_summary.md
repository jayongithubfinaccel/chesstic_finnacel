# PRD Update Summary - Iteration 7 (February 20, 2026)

## Overview
This document summarizes the changes made to the PRD for the chesstic_v2 project based on user feedback to simplify the UI for move analysis and streamline AI coaching recommendations.

**Key Focus Areas:**
1. Simplified move analysis table layout with better column ordering
2. Streamlined AI advisor to show only overall recommendations (removed section-specific suggestions)
3. Removed technical metrics (token usage, cost) from user-facing display

---

## Changes Made

### 1. **MOVE ANALYSIS BY GAME STAGE (SECTION 9) - UI Simplification**

**Previous Implementation (v2.5):**
- Table with 5 columns: Game Stage | Avg Brilliant/Game | Avg Neutral/Game | Avg Mistakes/Game | Total Games Analyzed
- Row labels: "Early (First 10)", "Middle (Sampled 10)", "Late (Last 10)"
- Summary cards: Weakest Stage, Most Common Error, Total Mistakes

**New Implementation (v2.6):**
- **Updated table layout with clearer header:**
  * Title: "Moves analysis - Average number of Mistake/Neutral/Brilliant moves per game"
  * Column order changed: **Mistake | Neutral | Brilliant** (prioritizes weaknesses first)
  * Removed "Total Games Analyzed" column from table (shown in analysis metadata)
  * First column is now row headers only (no "Game Stage" header)
- **Updated row labels for consistency:**
  * "early game (1-10 moves)"
  * "middle games (sample 10 consecutive moves)"
  * "late game (last 10 moves)"
- **Simplified summary cards:**
  * Removed: "Most Common Error" card (redundant information)
  * Kept: "Weakest Stage" and "Total Mistakes" cards
- **Updated sample info text:**
  * Changed from "95 significant mistakes" to "93 significant mistakes" (reflecting actual data)
  * Updated classification description: "Brilliant (≥+100cp gain), Neutral (-49 to +99cp), Mistake (≥-50cp loss)"

**Example Display (v2.6):**
```
┌────────────────────────────────────────────────────────────┐
│ MOVE ANALYSIS BY GAME STAGE                                │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ Moves analysis - Average number of Mistake/Neutral/        │
│ Brilliant moves per game                                   │
│                                                             │
│                    │ Mistake │ Neutral │ Brilliant │       │
│─────────────────────────────────────────────────────────────│
│ early game         │   1.8   │   5.1   │    2.3    │       │
│ (1-10 moves)       │         │         │           │       │
│─────────────────────────────────────────────────────────────│
│ middle games       │   2.4   │   4.2   │    3.1    │       │
│ (sample 10 consec.)│         │         │           │       │
│─────────────────────────────────────────────────────────────│
│ late game          │   3.1   │   4.9   │    1.8    │       │
│ (last 10 moves)    │         │         │           │       │
└─────────────────────────────────────────────────────────────┘

Summary Cards:
┌──────────────────┐  ┌──────────────────┐
│ Weakest Stage    │  │ Total Mistakes   │
│ late game        │  │ 93               │
└──────────────────┘  └──────────────────┘

📊 Analyzed 16 games out of 84 total games (19%). Found 93
    significant mistakes (50+ centipawns loss).
⚙️ Powered by Stockfish engine analysis. Move quality: 
    Brilliant (≥+100cp gain), Neutral (-49 to +99cp), 
    Mistake (≥-50cp loss)
```

**Rationale:**
- **Column order (Mistake first):** Users want to identify weaknesses immediately, so mistakes are shown first
- **Clearer header:** "Moves analysis - Average number..." explicitly states what the numbers represent
- **Row labels:** Lowercase, descriptive format matches user's design mockup
- **Removed "Total Games":** This information is already shown in the analysis metadata below the table
- **Removed "Most Common Error":** This card didn't provide additional actionable insights beyond the stage-by-stage breakdown

**Implementation Changes:**

**Frontend (templates/analytics.html):**
```html
<!-- OLD v2.5 -->
<table>
  <thead>
    <tr>
      <th>Game Stage</th>
      <th>Avg Brilliant/Game</th>
      <th>Avg Neutral/Game</th>
      <th>Avg Mistakes/Game</th>
      <th>Total Games Analyzed</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Early (First 10)</td>
      <td>2.3</td>
      <td>5.1</td>
      <td>1.8</td>
      <td>47</td>
    </tr>
    <!-- ... -->
  </tbody>
</table>

<!-- NEW v2.6 -->
<div class="table-header">
  <h4>Moves analysis</h4>
  <p>Average number of Mistake/Neutral/Brilliant moves per game</p>
</div>
<table>
  <thead>
    <tr>
      <th></th> <!-- Empty header for row labels -->
      <th>Mistake</th>
      <th>Neutral</th>
      <th>Brilliant</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>early game (1-10 moves)</strong></td>
      <td>1.8</td>
      <td>5.1</td>
      <td>2.3</td>
    </tr>
    <tr>
      <td><strong>middle games (sample 10 consecutive moves)</strong></td>
      <td>2.4</td>
      <td>4.2</td>
      <td>3.1</td>
    </tr>
    <tr>
      <td><strong>late game (last 10 moves)</strong></td>
      <td>3.1</td>
      <td>4.9</td>
      <td>1.8</td>
    </tr>
  </tbody>
</table>
```

**Frontend (static/js/analytics.js):**
```javascript
// Update rendering function
function renderMoveAnalysis(data) {
  const tableHTML = `
    <div class="table-header">
      <h4>Moves analysis</h4>
      <p class="subtitle">Average number of Mistake/Neutral/Brilliant moves per game</p>
    </div>
    <table class="move-analysis-table">
      <thead>
        <tr>
          <th></th>
          <th>Mistake</th>
          <th>Neutral</th>
          <th>Brilliant</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="stage-label">early game (1-10 moves)</td>
          <td>${data.early.avg_mistakes}</td>
          <td>${data.early.avg_neutral}</td>
          <td>${data.early.avg_brilliant}</td>
        </tr>
        <tr>
          <td class="stage-label">middle games (sample 10 consecutive moves)</td>
          <td>${data.middle.avg_mistakes}</td>
          <td>${data.middle.avg_neutral}</td>
          <td>${data.middle.avg_brilliant}</td>
        </tr>
        <tr>
          <td class="stage-label">late game (last 10 moves)</td>
          <td>${data.late.avg_mistakes}</td>
          <td>${data.late.avg_neutral}</td>
          <td>${data.late.avg_brilliant}</td>
        </tr>
      </tbody>
    </table>
  `;
  
  // Render summary cards (removed "Most Common Error")
  const summaryHTML = `
    <div class="summary-cards">
      <div class="card">
        <h5>Weakest Stage</h5>
        <p>${data.weakest_stage}</p>
      </div>
      <div class="card">
        <h5>Total Mistakes</h5>
        <p>${data.total_mistakes}</p>
      </div>
    </div>
  `;
  
  return tableHTML + summaryHTML;
}
```

**Backend (app/services/mistake_analysis_service.py):**
```python
# No changes needed - backend already returns avg_mistakes, avg_neutral, avg_brilliant
# Frontend rendering changes only
```

---

### 2. **AI CHESS ADVISOR (SECTION 10) - Streamlined Recommendations**

**Previous Implementation (v2.5):**
- **10 total recommendations:**
  * 9 section-specific recommendations (one for each analysis section)
  * 1 overall recommendation
- **Format:** Paragraph format with "Priority 1, Priority 2, Priority 3..."
- **Additional features:** YouTube video recommendations for openings
- **Displayed metrics:** Token usage, estimated cost
- **System prompt:** Generated detailed recommendations for all 9 sections + overall
- **Token limit:** 500 max_tokens
- **Cost:** ~$0.008-$0.012 per analysis

**New Implementation (v2.6):**
- **1 overall recommendation only**
  * Removed all section-specific recommendations
  * Focuses on highest-priority actionable items
- **Format:** 3-5 concise bullet points (1-2 sentences each)
- **No YouTube videos:** Removed video recommendation feature
- **No displayed metrics:** Token usage and cost logged internally only (not shown to users)
- **Updated system prompt:** Generates only overall recommendation as bullet points
- **Token limit:** 300 max_tokens (reduced from 500)
- **Cost:** ~$0.005-$0.008 per analysis (lower due to reduced tokens)

**Example Display (v2.6):**
```
┌─────────────────────────────────────────────────────┐
│ 🤖 AI Chess Coach - Personalized Analysis          │
│                                                     │
│ Based on your 150 games from Jan-Mar 2025          │
│                                                     │
│ 🎯 Overall Recommendation:                          │
│                                                     │
│ • Fix time management by switching to increment    │
│   games - 35% timeout losses indicate this is your │
│   biggest weakness                                  │
│                                                     │
│ • Improve or replace French Defense (30% win rate) │
│   - consider more solid options like Caro-Kann or  │
│   Petroff Defense                                   │
│                                                     │
│ • Focus 70% of study time on middlegame tactics    │
│   (moves 10-20) where you have 69 mistakes         │
│   compared to 23 in early game                     │
│                                                     │
│ • Schedule important games between 2-10pm when     │
│   your win rate is highest (58%)                   │
│                                                     │
│ [🔄 Regenerate Advice]                              │
└─────────────────────────────────────────────────────┘
```

**Rationale:**
- **Removed section-specific recommendations:** Too much information overwhelms users; overall recommendation provides sufficient guidance
- **Bullet points:** Easier to scan and remember than paragraph format
- **No video recommendations:** Simplifies implementation; users can find videos themselves if needed
- **Hidden metrics:** Technical details (tokens, cost) irrelevant to end users; logged internally for monitoring
- **Reduced tokens:** Shorter response format requires fewer tokens, reducing API costs

**Implementation Changes:**

**Backend (app/services/chess_advisor_service.py):**

```python
# OLD v2.5 System Prompt (excerpt)
SYSTEM_PROMPT = """
...
Based on the provided statistics, generate EXACTLY:
1. Nine (9) section-specific recommendations - ONE for each section (1-9)
2. One (1) overall recommendation that synthesizes all insights
...
"""

# NEW v2.6 System Prompt
SYSTEM_PROMPT = """
You are an expert chess coach analyzing a player's performance data. 
Your goal is to provide concise, actionable advice to help them improve 
their chess skills.

Based on the provided statistics from all 9 sections of analysis, generate 
ONE overall recommendation that synthesizes all insights into a clear 
action plan.

Your recommendation should:
- Be presented as 3-5 concise bullet points
- Be specific and actionable
- Reference concrete data from the analysis
- Prioritize the most impactful areas for improvement
- Each bullet point should be 1-2 sentences maximum

Focus on the most impactful areas for improvement. Prioritize:
1. Patterns with clear negative impact (e.g., high timeout losses)
2. Significant performance gaps (e.g., 20%+ difference between time periods)
3. Mistake patterns that repeat across games
4. Areas where small changes yield big results

Avoid:
- Generic advice ("study more tactics")
- Obvious statements ("you lose when you blunder")
- Long paragraphs or overly detailed explanations

Tone: Encouraging but honest, like a supportive coach.
"""

# OLD v2.5 - generate_advice() return
return {
    "section_suggestions": parsed_advice["suggestions"],
    "overall_recommendation": parsed_advice["overall"],
    "tokens_used": tokens_used,
    "estimated_cost": estimated_cost
}

# NEW v2.6 - generate_advice() return
# Log token usage internally (not returned to user)
self._log_usage(tokens_used, estimated_cost)

return {
    "overall_recommendation": parsed_advice["overall"]
}

# NEW v2.6 - Internal logging method
def _log_usage(self, tokens: int, cost: float):
    """
    Log token usage and cost for internal monitoring.
    This is for cost tracking purposes only - not shown to users.
    """
    logger.info(f"OpenAI API usage - Tokens: {tokens}, Estimated cost: ${cost}")

# NEW v2.6 - Updated max_tokens
self.max_tokens = 300  # Reduced from 500
```

**Frontend (templates/analytics.html):**
```html
<!-- OLD v2.5 -->
<div id="ai-advisor">
  <h3>🤖 AI Chess Coach</h3>
  <p>Based on your games...</p>
  
  <!-- Section-specific recommendations -->
  <div id="section-recommendations">
    <h4>📊 Section 1 - Overall Performance:</h4>
    <p>{{ suggestions[0] }}</p>
    <!-- ... 8 more sections ... -->
  </div>
  
  <!-- Overall recommendation -->
  <div id="overall-recommendation">
    <h4>🎯 Overall Recommendation:</h4>
    <p>{{ overall_recommendation }}</p>
  </div>
  
  <!-- Token usage and cost -->
  <div id="api-metrics">
    <p>Tokens used: {{ tokens_used }}</p>
    <p>Estimated cost: ${{ estimated_cost }}</p>
  </div>
  
  <button id="regenerate">Regenerate Advice</button>
</div>

<!-- NEW v2.6 -->
<div id="ai-advisor">
  <h3>🤖 AI Chess Coach - Personalized Analysis</h3>
  <p>Based on your {{ total_games }} games from {{ date_range }}</p>
  
  <!-- Overall recommendation only (as bullet points) -->
  <div id="overall-recommendation">
    <h4>🎯 Overall Recommendation:</h4>
    <div class="bullet-list">
      {{ overall_recommendation | safe }}
    </div>
  </div>
  
  <!-- No token/cost display -->
  
  <button id="regenerate">🔄 Regenerate Advice</button>
</div>
```

**Frontend (static/js/analytics.js):**
```javascript
// OLD v2.5 - Render all recommendations
function renderAIAdvisor(data) {
  let html = '<h3>🤖 AI Chess Coach</h3>';
  
  // Render section recommendations
  data.section_suggestions.forEach((suggestion, index) => {
    html += `<div class="section-rec">
      <h4>Section ${index + 1}</h4>
      <p>${suggestion}</p>
    </div>`;
  });
  
  // Render overall
  html += `<div class="overall-rec">
    <h4>Overall Recommendation</h4>
    <p>${data.overall_recommendation}</p>
  </div>`;
  
  // Render metrics
  html += `<p>Tokens: ${data.tokens_used}, Cost: $${data.estimated_cost}</p>`;
  
  return html;
}

// NEW v2.6 - Render only overall recommendation
function renderAIAdvisor(data) {
  const html = `
    <div class="ai-advisor">
      <h3>🤖 AI Chess Coach - Personalized Analysis</h3>
      <p class="context">Based on your ${data.total_games} games from ${data.date_range}</p>
      
      <div class="overall-recommendation">
        <h4>🎯 Overall Recommendation:</h4>
        <div class="bullet-list">
          ${formatBulletPoints(data.overall_recommendation)}
        </div>
      </div>
      
      <button id="regenerate-btn" class="btn-secondary">
        🔄 Regenerate Advice
      </button>
    </div>
  `;
  
  return html;
}

// Helper to format bullet points
function formatBulletPoints(text) {
  // Text already formatted as bullet points from backend
  // Just ensure proper HTML rendering
  return text.replace(/\n/g, '<br>');
}
```

**Updated Acceptance Criteria (v2.6):**

**Added:**
- [ ] Overall recommendation displayed as concise bullet points (3-5 bullets)
- [ ] Each bullet point is 1-2 sentences maximum
- [ ] Token usage and cost logged internally but NOT displayed to users
- [ ] Cost per analysis < $0.008 (reduced from $0.012)

**Removed:**
- [x] ~~EXACTLY 9 section-specific recommendations displayed~~
- [x] ~~Section labels clearly identify which section each recommendation addresses~~
- [x] ~~YouTube video recommendations integrated~~
- [x] ~~Video prioritization implemented~~
- [x] ~~Token usage and cost displayed to users~~

**Unchanged:**
- [ ] OpenAI GPT-4-turbo API integrated and working
- [ ] Summary data includes all sections (1-9) without raw PGN
- [ ] API response parsed correctly
- [ ] Advice is specific and references actual player data
- [ ] Loading state shows during API call
- [ ] AI advice cached for 1 hour
- [ ] Fallback advice works when API fails
- [ ] Regenerate button works

---

## Summary of All Changes

### Files Modified (PRD)

1. **prd_overview_data_analysis.md**
   - Updated version from v2.5 to v2.6
   - Added Iteration 7 change history
   - Modified Section 9 (Move Analysis) table layout and labels
   - Modified Section 10 (AI Advisor) to show only overall recommendations
   - Updated sample data values (95 → 93 mistakes)
   - Updated acceptance criteria for both sections

### Expected Code Changes (Implementation)

**Frontend:**
1. `templates/analytics.html`
   - Update move analysis table structure
   - Simplify AI advisor section layout
   - Remove token/cost display

2. `static/js/analytics.js`
   - Update `renderMoveAnalysis()` function
   - Update `renderAIAdvisor()` function
   - Remove section-specific recommendation rendering

3. `static/css/style.css` (if needed)
   - Update table styling for new layout
   - Update bullet point styling

**Backend:**
1. `app/services/chess_advisor_service.py`
   - Update `SYSTEM_PROMPT` constant
   - Update `USER_PROMPT_TEMPLATE` constant
   - Modify `generate_advice()` return structure
   - Add `_log_usage()` method
   - Update `_parse_advice_response()` to extract bullet points
   - Update `_generate_fallback_advice()` format
   - Update `max_tokens` from 500 to 300

2. `app/services/analytics_service.py` (if needed)
   - Remove video recommendation logic (if implemented)

---

## Testing Recommendations

### Unit Tests

**test_chess_advisor_service.py:**
```python
def test_generate_advice_returns_only_overall_recommendation():
    """Test that v2.6 returns only overall recommendation."""
    service = ChessAdvisorService()
    summary_data = {...}  # Sample data
    
    result = service.generate_advice(summary_data)
    
    # Should have overall_recommendation key
    assert "overall_recommendation" in result
    
    # Should NOT have section_suggestions, tokens_used, estimated_cost
    assert "section_suggestions" not in result
    assert "tokens_used" not in result
    assert "estimated_cost" not in result
    
def test_advice_formatted_as_bullet_points():
    """Test that overall recommendation is formatted as bullet points."""
    service = ChessAdvisorService()
    summary_data = {...}
    
    result = service.generate_advice(summary_data)
    recommendation = result["overall_recommendation"]
    
    # Should contain bullet points
    assert "•" in recommendation or "-" in recommendation
    lines = recommendation.split("\n")
    assert 3 <= len(lines) <= 5  # 3-5 bullet points

def test_internal_logging_called():
    """Test that token usage is logged internally."""
    service = ChessAdvisorService()
    summary_data = {...}
    
    with patch('logger.info') as mock_log:
        result = service.generate_advice(summary_data)
        
        # _log_usage() should be called
        mock_log.assert_called_once()
        assert "Tokens:" in mock_log.call_args[0][0]
        assert "Estimated cost:" in mock_log.call_args[0][0]
```

### Integration Tests

**test_analytics_api.py:**
```python
def test_ai_advisor_response_structure_v26():
    """Test that API returns v2.6 structure."""
    response = client.post('/api/analyze/detailed', json={
        'username': 'jay_fh',
        'start_date': '2025-01-01',
        'end_date': '2025-03-31',
        'include_ai_advice': True
    })
    
    data = response.json()
    ai_advice = data['sections']['ai_advisor']
    
    # Should have overall_recommendation
    assert 'overall_recommendation' in ai_advice
    
    # Should NOT have section_suggestions, tokens, cost
    assert 'section_suggestions' not in ai_advice
    assert 'tokens_used' not in ai_advice
    assert 'estimated_cost' not in ai_advice
```

### E2E Tests (Playwright)

**test_integration_e2e.py:**
```python
def test_move_analysis_table_layout_v26(page):
    """Test v2.6 move analysis table layout."""
    # Navigate and run analysis...
    
    # Check for table header
    assert page.locator('text=Moves analysis').is_visible()
    assert page.locator('text=Average number of Mistake/Neutral/Brilliant').is_visible()
    
    # Check column headers (Mistake, Neutral, Brilliant)
    headers = page.locator('th').all_text_contents()
    assert 'Mistake' in headers
    assert 'Neutral' in headers
    assert 'Brilliant' in headers
    assert headers.index('Mistake') < headers.index('Neutral') < headers.index('Brilliant')
    
    # Check row labels
    assert page.locator('text=early game (1-10 moves)').is_visible()
    assert page.locator('text=middle games (sample 10 consecutive moves)').is_visible()
    assert page.locator('text=late game (last 10 moves)').is_visible()
    
    # Check summary cards (should have 2, not 3)
    cards = page.locator('.summary-card').count()
    assert cards == 2  # Weakest Stage, Total Mistakes only

def test_ai_advisor_shows_only_overall_recommendation_v26(page):
    """Test v2.6 AI advisor displays only overall recommendation."""
    # Navigate and run analysis...
    
    # Check for AI advisor section
    assert page.locator('text=AI Chess Coach').is_visible()
    assert page.locator('text=Overall Recommendation').is_visible()
    
    # Should have bullet points
    bullets = page.locator('.bullet-list').locator('li, p').count()
    assert 3 <= bullets <= 5
    
    # Should NOT have section-specific headers
    assert not page.locator('text=Section 1').is_visible()
    assert not page.locator('text=Section 2').is_visible()
    
    # Should NOT display tokens or cost
    assert not page.locator('text=Tokens used').is_visible()
    assert not page.locator('text=Estimated cost').is_visible()
```

---

## Migration Notes

**For Engineers Implementing v2.6:**

1. **Frontend changes are straightforward:**
   - Update table HTML structure
   - Remove section recommendation rendering logic
   - Hide token/cost display

2. **Backend changes require careful prompt engineering:**
   - Test new system prompt to ensure it generates 3-5 bullet points
   - Verify fallback advice also uses bullet point format
   - Ensure internal logging works correctly

3. **Cost reduction:**
   - Expected cost reduction: ~33% (300 tokens vs 500 tokens)
   - Monitor actual costs after deployment

4. **User communication:**
   - If users ask about section-specific recommendations, explain they're simplified into overall recommendations
   - Emphasize that overall recommendations synthesize all section insights

---

## Questions for Clarification (If Needed)

None - requirements are clear from user's mockup and instructions.

---

## Version History

- **v2.6** (February 20, 2026): Simplified UI and streamlined recommendations
- **v2.5** (February 19, 2026): Move quality analysis and AI advisor re-enablement
- **v2.4** (February 19, 2026): Asynchronous analysis implementation
- **v2.3** (February 18, 2026): Opening performance simplification and data viz enhancements
- **v2.2** (February 17, 2026): Rate limiting and cache optimization
- **v2.1** (December 12, 2025): Initial AI advisor implementation
- **v2.0** (December 10, 2025): Comprehensive analytics dashboard

---

## Appendix: User Mockup Reference

The user provided an image mockup showing the desired table layout:

**Table header:**
"Moves analysis - Average number of Mistake/Neutral/Brilliant moves per game"

**Table structure:**
```
|                                             | Mistake | Neutral | Brilliant |
|---------------------------------------------|---------|---------|-----------|
| early game (1-10 moves)                     |   xxx   |   xxx   |    xxx    |
| middle games (sample 10 consecutive moves)  |   xxx   |   xxx   |    xxx    |
| late game (last 10 moves)                   |   xxx   |   xxx   |    xxx    |
```

This layout has been incorporated into the PRD and should guide implementation.
