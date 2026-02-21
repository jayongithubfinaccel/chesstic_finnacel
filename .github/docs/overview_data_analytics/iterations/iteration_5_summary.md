# PRD Update Summary - Iteration 5 (February 18, 2026)

## Overview
This document summarizes the changes made to the PRD for the chesstic_v2 project based on user feedback to improve data visualization clarity, add more detailed statistics, and refine analysis logic.

**Key Focus Areas:**
1. Enhanced color performance statistics with actual W/L/D counts
2. Simplified termination type visualizations
3. Improved opening performance analysis with Lichess integration and game examples
4. Refined mistake analysis logic based on dataset size

---

## Changes Made

### 1. **PERFORMANCE BY COLOR (SECTION 2) - Enhanced Statistics Display**

**Previous Implementation:**
- Two summary cards showing only total games and win rate %
- Chart with two lines (White and Black win rates over time)

**New Implementation:**
- **Enhanced summary cards with complete statistics:**
  * White Summary Card: Total games, **Wins, Losses, Draws**, Win rate %
  * Black Summary Card: Total games, **Wins, Losses, Draws**, Win rate %
- Chart remains the same (two lines for White and Black win rates)

**Example Display:**
```
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ ♔ PLAYING AS WHITE           │  │ ♚ PLAYING AS BLACK           │
│                              │  │                              │
│ Total games: 42              │  │ Total games: 38              │
│ Wins: 24                     │  │ Wins: 18                     │
│ Losses: 15                   │  │ Losses: 17                   │
│ Draws: 3                     │  │ Draws: 3                     │
│ Win Rate: 57.1%              │  │ Win Rate: 47.4%              │
└──────────────────────────────┘  └──────────────────────────────┘
```

**Rationale:**
- Users want to see absolute numbers in addition to percentages
- Complete statistics provide better context without hovering over charts
- Helps users quickly understand their performance with each color

**Implementation Changes:**
```python
# Backend: Return W/L/D counts in summary
{
    "white": {
        "total_games": 42,
        "wins": 24,
        "losses": 15,
        "draws": 3,
        "win_rate": 57.1,
        "daily_stats": [...]
    },
    "black": {
        "total_games": 38,
        "wins": 18,
        "losses": 17,
        "draws": 3,
        "win_rate": 47.4,
        "daily_stats": [...]
    }
}

# Frontend: Display all statistics in summary cards
```

---

### 2. **TERMINATION TYPE VISUALIZATION (SECTIONS 4 & 5) - Simplified Display**

**Previous Implementation:**
- Pie charts with count labels inside segments
- Legend showing category names and percentages

**New Implementation:**
- **Numbers only inside pie chart segments** (e.g., "25" not "Checkmate: 25")
- **No legend displayed** (reduces visual clutter)
- Hover tooltip still shows full details: Category name, Count, Percentage

**Example Display:**
```
     HOW YOU WIN                     HOW YOU LOSE
     
    ┌───────────┐                  ┌───────────┐
    │    45%    │                  │    35%    │
    │    32     │  Checkmate       │    28     │  Timeout
    └───────────┘                  └───────────┘
    
    ┌───────────┐                  ┌───────────┐
    │    30%    │                  │    25%    │
    │    21     │  Resignation     │    20     │  Resignation
    └───────────┘                  └───────────┘
    
[Tooltip on hover: "Checkmate: 32 games (45%)"]
```

**Rationale:**
- Cleaner, more minimalist design
- Numbers are the most important information at a glance
- Legend is redundant when tooltips provide full context

**Implementation Changes:**
```javascript
// Chart.js configuration
{
    plugins: {
        legend: {
            display: false  // Hide legend
        },
        datalabels: {
            formatter: (value) => value,  // Show only number, not "Category: number"
            color: '#fff',
            font: { size: 16, weight: 'bold' }
        },
        tooltip: {
            callbacks: {
                label: (context) => {
                    const label = context.label || '';
                    const value = context.parsed;
                    const percentage = ((value / total) * 100).toFixed(1);
                    return `${label}: ${value} games (${percentage}%)`;
                }
            }
        }
    }
}
```

---

### 3. **OPENING PERFORMANCE (SECTION 6) - Enhanced Analysis with Lichess & Chess.com Integration**

**Previous Implementation (Iteration 4):**
- Top 10 most common openings by frequency
- Display: Opening name, Games played, Win rate %, W-L-D counts
- No move sequences or position visualization

**New Implementation:**
- **Analyze first 6 full moves** (12 individual moves) of each opening
- **Display first 6 moves** in standard chess notation (e.g., "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6")
- **Generate Lichess position URL** for each opening (view position on Lichess board editor)
- **Provide 1 example game URL from Chess.com** for each opening
- **Separate analysis by color** (White openings vs Black openings)

**Example Display:**
```
┌────────────────────────────────────────────────────────────────┐
│ ♔ TOP 10 MOST COMMON OPENINGS (AS WHITE)                       │
├────────────────────────────────────────────────────────────────┤
│ 1. Sicilian Defense: Alapin Variation                          │
│    Games: 12 | Win Rate: 58.3% (7W-4L-1D)                     │
│    Moves: 1. e4 c5 2. c3 Nf6 3. e5 Nd5 4. d4 cxd4 5. cxd4 d6  │
│    📊 View Position on Lichess                                 │
│    ♟️ Example Game on Chess.com                                │
├────────────────────────────────────────────────────────────────┤
│ 2. Italian Game                                                 │
│    Games: 10 | Win Rate: 70.0% (7W-2L-1D)                     │
│    Moves: 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. c3 Nf6 5. d4 exd4 │
│    📊 View Position on Lichess                                 │
│    ♟️ Example Game on Chess.com                                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ ♚ TOP 10 MOST COMMON OPENINGS (AS BLACK)                       │
├────────────────────────────────────────────────────────────────┤
│ 1. French Defense                                               │
│    Games: 8 | Win Rate: 37.5% (3W-4L-1D)                      │
│    Moves: 1. e4 e6 2. d4 d5 3. Nc3 Nf6 4. Bg5 Be7 5. e5 Nfd7  │
│    📊 View Position on Lichess                                 │
│    ♟️ Example Game on Chess.com                                │
└────────────────────────────────────────────────────────────────┘
```

**Rationale:**
- **First 6 moves analysis matches notebook implementation** (user requested consistency)
- **Lichess URL** allows users to visually see the opening position on an interactive board
- **Chess.com example game** provides real game context for learning
- **Separate by color** helps users understand their repertoire for each side
- **Most common openings** (not best/worst) focuses on what users actually play

**Implementation Details:**

**Backend Changes:**
```python
def _analyze_opening_performance(self, games: List[Dict]) -> Dict:
    """Analyze openings with first 6 moves and URLs."""
    
    # Group by color
    for game in games:
        opening = game['opening_name']
        player_color = game['player_color']
        
        # Track statistics
        stats[opening]['games'] += 1
        stats[opening]['wins/losses/draws'] += ...
        
        # Store sample PGN and game URL for each opening
        if stats[opening]['sample_pgn'] is None:
            stats[opening]['sample_pgn'] = game['pgn']
            stats[opening]['example_game_url'] = game['url']  # NEW
    
    # For each opening, extract:
    # 1. First 6 full moves (12 individual moves)
    first_moves = self._extract_first_six_moves(sample_pgn)
    
    # 2. FEN position after 6 moves
    fen = self._get_opening_position_fen(sample_pgn)
    
    # 3. Generate Lichess URL
    lichess_url = f"https://lichess.org/editor/{urllib.parse.quote(fen)}"
    
    # 4. Chess.com game URL with position
    example_game_url = stats[opening]['example_game_url']
    
    return {
        'opening': opening_name,
        'games': count,
        'wins': w, 'losses': l, 'draws': d,
        'win_rate': wr,
        'first_moves': first_moves,        # NEW
        'lichess_url': lichess_url,        # NEW
        'example_game_url': example_game_url  # NEW
    }
```

**Frontend Changes:**
```javascript
// Display opening with expandable details
openings.forEach(opening => {
    html += `
        <div class="opening-card">
            <h4>${opening.opening}</h4>
            <p>Games: ${opening.games} | Win Rate: ${opening.win_rate}%</p>
            <p class="moves">${opening.first_moves}</p>
            <div class="opening-links">
                <a href="${opening.lichess_url}" target="_blank">
                    📊 View Position on Lichess
                </a>
                <a href="${opening.example_game_url}" target="_blank">
                    ♟️ Example Game
                </a>
            </div>
        </div>
    `;
});
```

**Data Structure:**
```json
{
    "opening_performance": {
        "white": [
            {
                "opening": "Sicilian Defense: Alapin Variation",
                "games": 12,
                "wins": 7,
                "losses": 4,
                "draws": 1,
                "win_rate": 58.3,
                "first_moves": "1. e4 c5 2. c3 Nf6 3. e5 Nd5 4. d4 cxd4 5. cxd4 d6",
                "lichess_url": "https://lichess.org/editor/rnbqkb1r%2Fpp2pppp%2F3p4%2F2pnP3%2F3P4%2F8%2FPP3PPP%2FRNBQKBNR_w_KQkq_-_0_1",
                "example_game_url": "https://www.chess.com/game/live/123456789"
            }
        ],
        "black": [...]
    }
}
```

---

### 4. **MISTAKE ANALYSIS BY GAME STAGE (SECTION 9) - Refined Sampling Logic**

**Previous Implementation:**
- Fixed 2-game analysis for 1-minute target
- Same logic regardless of total games
- 20% sample with min 10, max 50 games (outdated from iteration 4)

**New Implementation:**
- **If total games < 50: Analyze ALL games**
- **If total games ≥ 50: Use current sample size logic (20%, min 10, max 50)**

**Logic Flow:**
```python
def select_games_for_analysis(total_games):
    if total_games < 50:
        # Analyze everything for comprehensive results
        return all_games
    else:
        # Use 20% sampling strategy
        sample_size = max(10, min(50, int(total_games * 0.20)))
        return stratified_sample(all_games, sample_size)
```

**Examples:**
- **10 games total → Analyze 10 games** (100%)
- **30 games total → Analyze 30 games** (100%)
- **49 games total → Analyze 49 games** (100%)
- **50 games total → Analyze 10 games** (20%, hits minimum)
- **100 games total → Analyze 20 games** (20%)
- **300 games total → Analyze 50 games** (16.7%, hits maximum)

**Rationale:**
1. **Small datasets need full analysis** for statistical confidence
2. **Large datasets use sampling** for performance (still meets 1-minute goal with 30-day limit)
3. **Better accuracy** for users with moderate activity
4. **Maintains performance** for very active players

**Performance Impact with 30-Day Limit:**
- With 30-day max, typical users have 20-50 games
- Most users will get full analysis or close to it
- Very active users (50+ games in 30 days) still get representative sample

**Implementation Changes:**
```python
def _analyze_mistake_patterns(self, games: List[Dict]) -> Dict:
    """Analyze mistakes with dynamic sampling based on dataset size."""
    
    total_games = len(games)
    
    # Filter cached vs uncached
    uncached_games = [g for g in games if not self._is_cached(g)]
    
    # Determine games to analyze
    if total_games < 50:
        games_to_analyze = uncached_games
        analysis_note = f"Comprehensive analysis of {len(uncached_games)} games"
    else:
        # Use 20% sampling with min/max bounds
        sample_size = max(10, min(50, int(len(uncached_games) * 0.20)))
        games_to_analyze = self._stratified_sample(uncached_games, sample_size)
        analysis_note = f"Analysis based on {sample_size} games ({sample_size/total_games*100:.1f}% sample)"
    
    # Run engine analysis
    results = self._run_stockfish_analysis(games_to_analyze)
    
    return {
        'results': results,
        'analysis_note': analysis_note,
        'total_games': total_games,
        'analyzed_games': len(games_to_analyze)
    }
```

**User-Facing Display:**
```
┌──────────────────────────────────────────────────────┐
│ 🔍 MISTAKE ANALYSIS BY GAME STAGE                    │
│                                                       │
│ Comprehensive analysis of 35 games                   │  ← <50 games
│                                                       │
│ OR                                                    │
│                                                       │
│ Analysis based on 15 games (20% sample)              │  ← ≥50 games
└──────────────────────────────────────────────────────┘
```

---

## Updated Requirements Summary

### Section 2 (EA-014) - Performance by Color
**Added:**
- Display actual W/L/D counts in summary cards (not just total games and win rate)

**Acceptance Criteria Updates:**
- [ ] White summary card shows: total games, **wins, losses, draws**, win rate %
- [ ] Black summary card shows: total games, **wins, losses, draws**, win rate %

---

### Section 4 & 5 (EA-015) - Termination Type Visualization
**Changed:**
- Show only numbers inside pie segments (remove category labels)
- Hide legend completely
- Full details available in hover tooltip

**Acceptance Criteria Updates:**
- [ ] Pie segments show **numbers only** (e.g., "32" not "Checkmate: 32")
- [ ] **Legend is hidden** (no legend displayed)
- [ ] Hover tooltip shows: Category name, Count, Percentage

---

### Section 6 (EA-016) - Opening Performance Analysis
**Added:**
- First 6 moves display in standard notation
- Lichess board editor URL for position visualization
- Chess.com example game URL for each opening
- Separate display for White and Black openings

**Changed:**
- From: "Top 10 Most Common Openings" (combined)
- To: "Top 10 Most Common Openings (As White)" and "Top 10 Most Common Openings (As Black)" (separated)

**Acceptance Criteria Updates:**
- [ ] Display first 6 full moves (12 individual moves) for each opening
- [ ] Moves shown in standard notation (e.g., "1. e4 e5 2. Nf3 Nc6...")
- [ ] Lichess URL generated and clickable for each opening
- [ ] Chess.com example game URL provided for each opening
- [ ] Openings displayed separately for White and Black
- [ ] URLs open in new tab

---

### Section 9 (EA-018) - Mistake Analysis by Game Stage
**Changed:**
- From: Fixed 2-game analysis for all datasets
- To: Dynamic logic based on dataset size
  * <50 games: Analyze all
  * ≥50 games: Use 20% sampling (min 10, max 50)

**Acceptance Criteria Updates:**
- [ ] If total games < 50: All games analyzed
- [ ] If total games ≥ 50: 20% sample with min 10, max 50
- [ ] Display shows: "Comprehensive analysis of X games" (if <50)
- [ ] Display shows: "Analysis based on X games (Y% sample)" (if ≥50)
- [ ] Sampling uses stratified random selection

---

## Implementation Priority

**Priority 1 (Highest Impact):**
1. Section 6 - Opening performance enhancements (Lichess + Chess.com URLs)
2. Section 9 - Mistake analysis logic refinement

**Priority 2 (Medium Impact):**
3. Section 2 - Color performance statistics enhancement
4. Sections 4 & 5 - Termination type visualization simplification

---

## Testing Updates

See updated test cases in main PRD:
- **TC-016:** Enhanced color performance cards with W/L/D counts
- **TC-017:** Simplified pie chart display (numbers only, no legend)
- **TC-018:** Opening performance with moves, Lichess URL, example game URL
- **TC-021:** Mistake analysis with dynamic sampling logic

---

## Files to Update

1. **Backend:**
   - `app/services/analytics_service.py`
     * `_analyze_color_performance()` - Add W/L/D to summary
     * `_analyze_opening_performance()` - Add first 6 moves, URLs, separate by color
     * `_analyze_mistake_patterns()` - Implement <50 vs ≥50 logic

2. **Frontend:**
   - `templates/analytics.html` - Update summary card templates
   - `static/js/analytics.js` - Update chart configurations, opening display
   - `static/css/style.css` - Style opening links and cards

3. **Documentation:**
   - `prd_overview_data_analysis.md` - Update all affected sections
   - This iteration summary document

4. **Tests:**
   - `tests/test_analytics_service.py` - Update unit tests
   - `tests/e2e/test_analytics.py` - Update E2E tests

---

## Migration Notes

**Backward Compatibility:**
- Frontend must handle both old and new response formats during transition
- Cached analysis results remain valid (no data structure changes for cache)

**Deployment:**
- Deploy backend changes first
- Deploy frontend changes second
- Clear browser cache if testing locally

---

**Document Version:** Iteration 5  
**Created:** February 18, 2026  
**Author:** PRD Agent  
**Status:** Ready for Implementation
