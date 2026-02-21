# Iteration 8 Summary - Enhanced Table Display & Restored Section-Based AI Recommendations

**Date:** February 20, 2026  
**Version:** v2.7  
**Previous Version:** v2.6  
**Status:** In Development

---

## Overview

This iteration addresses two key user feedback items from v2.6:
1. **Mistake Analysis Table:** Add "Number of games" row for better context
2. **AI Chess Coach:** Restore section-specific recommendations while maintaining concise bullet format

### Key Changes
- ✨ Enhanced move analysis table with game count row
- ✨ Restored section-based AI recommendations (9 sections) in bullet format
- ⚡ Increased AI token limit from 300 to 600 tokens
- 🔄 Modified prompts for concise section-specific guidance

---

## Section 9: Move Analysis by Game Stage

### What Changed

**Added "Number of games" row:**
- **Before (v2.6):**
  ```
  | Stage       | Mistake | Neutral | Brilliant |
  |-------------|---------|---------|-----------|
  | early game  | 2.3     | 5.1     | 1.2       |
  | middle game | 3.1     | 4.8     | 0.9       |
  | late game   | 2.8     | 5.3     | 1.5       |
  ```

- **After (v2.7):**
  ```
  | Number of games | XXX |         |           |
  |-----------------|-----|---------|-----------|
  | early game      | 2.3 | 5.1     | 1.2       |
  | middle game     | 3.1 | 4.8     | 0.9       |
  | late game       | 2.8 | 5.3     | 1.5       |
  ```

### Implementation Details

**Frontend (analytics.js):**
```javascript
function renderMistakeTable(data) {
    const tbody = document.getElementById('mistakeTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const sampleInfo = data.sample_info || {};
    const analyzedGames = sampleInfo.analyzed_games || 0;
    
    // NEW: Add "Number of games" row
    const headerRow = document.createElement('tr');
    headerRow.classList.add('games-count-row');
    
    const labelCell = document.createElement('td');
    labelCell.innerHTML = '<strong>Number of games</strong>';
    headerRow.appendChild(labelCell);
    
    const countCell = document.createElement('td');
    countCell.colSpan = 3;
    countCell.innerHTML = `<strong>${analyzedGames}</strong>`;
    headerRow.appendChild(countCell);
    
    tbody.appendChild(headerRow);
    
    // Existing stage rows follow...
    const stages = [
        { key: 'early', display: 'early game (1-10 moves)', class: 'stage-early' },
        { key: 'middle', display: 'middle games (sample 10 consecutive moves)', class: 'stage-middle' },
        { key: 'endgame', display: 'late game (last 10 moves)', class: 'stage-endgame' }
    ];
    
    // ... rest of existing code
}
```

**Template (analytics.html):**
- No structural changes needed (table dynamically populated)
- May add CSS styling for `.games-count-row` class

---

## Section 10: AI Chess Coach

### What Changed

**Restored section-specific recommendations:**
- **v2.6 approach:** Display only overall recommendation
- **v2.7 approach:** Display 9 section-specific recommendations (as bullets) + overall recommendation

### Format Specification

**Section Recommendations (9 sections):**
Each section gets 1-2 concise bullet points:
```
Section 1 - Overall Performance:
• Focus on maintaining your upward rating trend (+85 points in 2 weeks)
• Target 55%+ win rate by reducing timeout losses from 18% to under 10%

Section 2 - Color Performance:
• Practice more games as White (currently 43% win rate vs 67% as Black)

Section 3 - ELO Progression:
• Your rating is trending up - keep playing consistently to reach 1500

... (9 sections total)
```

**Overall Recommendation (synthesized):**
```
Overall Recommendation:
• Schedule more morning games (75% win rate) and avoid late evening (42%)
• Focus on White repertoire improvement - consider studying Italian Game or Ruy Lopez
• Reduce timeout losses by improving time management in complex positions
• Continue your winning streak with Caro-Kann Defense (78% win rate)
```

### Implementation Details

#### Backend (chess_advisor_service.py)

**1. Update System Prompt:**
```python
SYSTEM_PROMPT = """
You are an expert chess coach analyzing a player's performance data. Your goal is to provide 
concise, actionable advice to help them improve their chess skills.

Based on the provided statistics from all 9 sections of analysis, generate:
1. One specific recommendation for EACH of the 9 sections (1-2 bullet points per section)
2. ONE overall recommendation synthesizing all insights (3-5 bullet points)

Format for section recommendations:
- Each section gets 1-2 concise, actionable bullet points
- Focus on the most impactful insight from that specific section
- Be specific with data references (e.g., "win rate dropped from 60% to 45%")

Format for overall recommendation:
- Synthesize the top 3-5 priorities across all sections
- Provide a clear action plan
- Reference concrete data

Prioritize:
1. Patterns with clear negative impact (e.g., high timeout losses)
2. Significant performance gaps (e.g., 20%+ difference)
3. Mistake patterns that repeat
4. Areas where small changes yield big results

Avoid:
- Generic advice ("study more tactics")
- Obvious statements ("you lose when you blunder")
- Long paragraphs

Tone: Encouraging but honest, like a supportive coach.
"""
```

**2. Update User Prompt Template:**
```python
USER_PROMPT_TEMPLATE = """
Analyze this chess player's performance and provide coaching recommendations:

{summary_data_json}

Provide your recommendations in this EXACT format:

**Section 1 - Overall Performance:**
• [Actionable insight 1]
• [Actionable insight 2 if needed]

**Section 2 - Color Performance:**
• [Actionable insight]

**Section 3 - ELO Progression:**
• [Actionable insight]

**Section 4 - Termination Wins:**
• [Actionable insight]

**Section 5 - Termination Losses:**
• [Actionable insight]

**Section 6 - Opening Performance:**
• [Actionable insight]

**Section 7 - Opponent Strength:**
• [Actionable insight]

**Section 8 - Time of Day:**
• [Actionable insight]

**Section 9 - Move Analysis:**
• [Actionable insight]

**Overall Recommendation:**
• [Priority 1 - highest impact action]
• [Priority 2]
• [Priority 3]
• [Optional: Priority 4]
• [Optional: Priority 5]

Keep each bullet point concise (1-2 sentences maximum).
"""
```

**3. Update Token Limit:**
```python
def __init__(self, api_key: str, model: str = 'gpt-4o-mini', 
             max_tokens: int = 600, temperature: float = 0.7):  # Changed from 300 to 600
```

**4. Restore Return Structure:**
```python
def generate_advice(self, analysis_results: Dict, username: str, date_range: str) -> Dict:
    # ... API call logic ...
    
    return {
        'section_suggestions': parsed_advice['suggestions'],  # List of section recommendations
        'overall_recommendation': parsed_advice['overall']      # Overall synthesis
    }
```

**5. Update Parsing Logic:**
```python
def _parse_advice_response(self, response_text: str) -> Dict:
    """
    Parse structured AI response with section headers and bullet points.
    
    Expected format:
    **Section 1 - Overall Performance:**
    • Bullet 1
    • Bullet 2
    
    **Section 2 - Color Performance:**
    • Bullet 1
    ...
    
    Returns:
        {
            'suggestions': [
                {
                    'section_number': 1,
                    'section_name': 'Overall Performance',
                    'bullets': ['Bullet 1', 'Bullet 2']
                },
                ...
            ],
            'overall': '• Bullet 1\n• Bullet 2\n...'
        }
    """
    lines = response_text.strip().split('\n')
    suggestions = []
    overall = ""
    current_section = None
    current_bullets = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section header
        if line.startswith('**Section') and line.endswith(':**'):
            # Save previous section if exists
            if current_section:
                suggestions.append({
                    'section_number': current_section['number'],
                    'section_name': current_section['name'],
                    'bullets': current_bullets
                })
            
            # Parse new section
            section_match = line.replace('**', '').replace(':', '').strip()
            parts = section_match.split(' - ', 1)
            section_num = int(parts[0].replace('Section', '').strip())
            section_name = parts[1].strip() if len(parts) > 1 else ""
            
            current_section = {'number': section_num, 'name': section_name}
            current_bullets = []
            
        elif line.startswith('**Overall Recommendation:**'):
            # Save last section
            if current_section:
                suggestions.append({
                    'section_number': current_section['number'],
                    'section_name': current_section['name'],
                    'bullets': current_bullets
                })
                current_section = None
                current_bullets = []
                
        elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
            # Bullet point
            bullet = line.lstrip('•-* ').strip()
            if current_section is None:
                # Part of overall recommendation
                overall += line + '\n'
            else:
                # Part of section recommendation
                current_bullets.append(bullet)
    
    # Save last section if exists
    if current_section:
        suggestions.append({
            'section_number': current_section['number'],
            'section_name': current_section['name'],
            'bullets': current_bullets
        })
    
    return {
        'suggestions': suggestions,
        'overall': overall.strip()
    }
```

#### Frontend (analytics.js)

**1. Restore renderAIAdvisor() Function:**
```javascript
function renderAIAdvisor(aiData) {
    const loading = document.getElementById('aiLoading');
    const content = document.getElementById('aiContent');
    const error = document.getElementById('aiError');
    
    if (loading) loading.style.display = 'none';
    if (error) error.style.display = 'none';
    
    if (content) {
        content.style.display = 'block';
        
        // v2.7: Render section suggestions AND overall recommendation
        renderAISectionSuggestions(aiData.section_suggestions || []);
        renderAIOverall(aiData.overall_recommendation || '');
    }
}
```

**2. Add renderAISectionSuggestions() Function:**
```javascript
function renderAISectionSuggestions(suggestions) {
    const container = document.getElementById('aiSectionsContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!suggestions || suggestions.length === 0) {
        container.innerHTML = '<p class="no-suggestions">No section-specific suggestions available.</p>';
        return;
    }
    
    suggestions.forEach(section => {
        const sectionDiv = document.createElement('div');
        sectionDiv.classList.add('ai-section-advice');
        
        // Section header
        const header = document.createElement('h5');
        header.textContent = `Section ${section.section_number} - ${section.section_name}`;
        sectionDiv.appendChild(header);
        
        // Bullet list
        const ul = document.createElement('ul');
        section.bullets.forEach(bullet => {
            const li = document.createElement('li');
            li.textContent = bullet;
            ul.appendChild(li);
        });
        sectionDiv.appendChild(ul);
        
        container.appendChild(sectionDiv);
    });
}
```

**3. Update renderAIOverall():**
```javascript
function renderAIOverall(recommendation) {
    const element = document.getElementById('aiOverallRecommendation');
    if (!element) return;
    
    if (recommendation) {
        // Convert newlines to HTML breaks for display
        element.innerHTML = recommendation.replace(/\n/g, '<br>');
    } else {
        element.innerHTML = '• Continue analyzing your games and focus on consistent improvement.';
    }
}
```

#### Template (analytics.html)

**Update AI Advisor Section:**
```html
<!-- Section 10: AI Chess Advisor (v2.7: Section suggestions + Overall) -->
<section class="analytics-section" id="aiAdvisorSection" style="display: none;">
    <div class="section-card ai-advisor-card">
        <div class="section-header">
            <h3>🤖 AI Chess Coach - Personalized Analysis</h3>
            <p class="section-description" id="aiAdvisorContext">Based on your comprehensive performance analysis</p>
        </div>
        
        <!-- Loading State -->
        <div class="ai-loading" id="aiLoading">
            <div class="spinner"></div>
            <p>AI Coach is analyzing your games...</p>
            <p class="ai-loading-detail">This may take up to 15 seconds</p>
        </div>
        
        <!-- AI Advice Content (v2.7: Section suggestions + Overall) -->
        <div class="ai-content" id="aiContent" style="display: none;">
            <!-- Section-Specific Recommendations -->
            <div class="ai-sections">
                <h4>📋 Key Insights by Section:</h4>
                <div id="aiSectionsContainer">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
            
            <!-- Overall Recommendation -->
            <div class="ai-overall">
                <h4>🎯 Overall Recommendation:</h4>
                <div class="ai-recommendation-text" id="aiOverallRecommendation"></div>
            </div>
        </div>
        
        <!-- Error State -->
        <div class="ai-error" id="aiError" style="display: none;">
            <p>⚠️ Unable to generate AI recommendations. Using fallback advice.</p>
        </div>
    </div>
</section>
```

---

## Acceptance Criteria Updates

### Section 9 - Move Analysis by Game Stage (EA-018)

**Updated AC-018-004:** Table Display
- ✅ Must display "Number of games" row as first row with analyzed game count
- ✅ Must show 3 stage rows: early game, middle game, late game
- ✅ Column order must be: Mistake | Neutral | Brilliant
- ✅ Row labels must match: "early game (1-10 moves)", "middle games (sample 10 consecutive moves)", "late game (last 10 moves)"

### Section 10 - AI Chess Advisor (EA-019)

**Updated AC-019-001:** Response Structure
- ✅ Must return both `section_suggestions` (list) and `overall_recommendation` (string)
- ✅ `section_suggestions` must contain 9 section recommendations
- ✅ Each section must have: `section_number`, `section_name`, `bullets` (list of 1-2 items)

**Updated AC-019-002:** Display Format
- ✅ Must display section-specific recommendations grouped by section
- ✅ Each section must show as expandable/collapsed format (optional) or inline
- ✅ Bullets must be displayed as proper HTML lists
- ✅ Overall recommendation must be displayed separately with clear visual distinction

**Updated AC-019-003:** Token Usage
- ✅ max_tokens set to 600 (supports 9 sections + overall)
- ✅ Token usage and cost logged internally (not displayed to users)
- ✅ Expected cost: <$0.015 per request

---

## Testing Plan

### Unit Tests
1. **Backend - chess_advisor_service.py:**
   - Test `_parse_advice_response()` with section-formatted input
   - Verify 9 sections + overall are correctly parsed
   - Test bullet extraction logic

2. **Backend - API response:**
   - Verify `section_suggestions` is a list with 9 items
   - Verify each item has required keys: section_number, section_name, bullets
   - Verify `overall_recommendation` is a string

### Integration Tests
1. **Frontend - Table rendering:**
   - Verify "Number of games" row appears first
   - Verify game count displays correctly
   - Verify 3 stage rows render below

2. **Frontend - AI rendering:**
   - Verify 9 sections render with headers
   - Verify bullets display as list items
   - Verify overall recommendation renders separately

### E2E Tests (Manual)
1. Submit analysis for username "jay_fh", dates 2026-01-31 to 2026-02-14
2. Verify move analysis table shows:
   - First row: "Number of games | 16 | | |"
   - Three stage rows with data
3. Verify AI coach section shows:
   - 9 expandable/collapsed sections OR inline sections
   - Each section has 1-2 bullet points
   - Overall recommendation has 3-5 bullet points
4. Verify no token/cost display

---

## Migration Notes

### From v2.6 to v2.7

**Code Changes:**
1. Update `chess_advisor_service.py`:
   - Change max_tokens from 300 to 600
   - Restore section-based prompts
   - Update parsing logic to extract sections
   - Return both section_suggestions and overall_recommendation

2. Update `analytics.js`:
   - Add number of games row to renderMistakeTable()
   - Restore renderAISectionSuggestions() function
   - Update renderAIAdvisor() to call both rendering functions

3. Update `analytics.html`:
   - Add section suggestions container
   - Keep overall recommendation container

**Data Migration:**
- No database changes required
- API response structure changes (backward compatible)

---

## Rollback Plan

If issues arise with v2.7:
1. Revert `chess_advisor_service.py` to v2.6 (300 tokens, overall only)
2. Revert `analytics.js` renderMistakeTable() to remove games row
3. Revert `analytics.html` to v2.6 structure

All changes are isolated to 3 files, making rollback straightforward.

---

## Performance Impact

**Token Usage:**
- v2.6: ~200-250 tokens per request
- v2.7: ~450-550 tokens per request
- Increase: ~2.2x tokens

**Cost Impact:**
- v2.6: ~$0.005 per request
- v2.7: ~$0.011 per request
- Increase: ~2.2x cost

**User Benefit:**
- Much more comprehensive guidance (9 sections + overall vs just overall)
- Clearer understanding of what to improve in each area
- Still concise with bullet format

---

## Risk Assessment

**Low Risk:**
- Table changes are purely presentational
- Number of games row is informational only

**Medium Risk:**
- AI response parsing more complex (9 sections)
- Token usage doubled (cost increase)
- Longer loading time for AI recommendations (~10-15 seconds vs ~5-7 seconds)

**Mitigation:**
- Extensive testing of parsing logic
- Fallback recommendations if parsing fails
- Loading state shows realistic time estimate
- Cost increase acceptable for better UX

---

## Documentation Updates

- ✅ PRD updated to v2.7 with iteration 8 changes
- ✅ Iteration 8 summary created (this document)
- ⏳ Test results document to be created after implementation
- ⏳ Bug fixes document to be updated if issues found

---

**Document Status:** Complete  
**Next Step:** Implementation
