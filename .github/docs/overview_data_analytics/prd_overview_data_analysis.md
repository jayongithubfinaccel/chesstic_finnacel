# PRD: Enhanced Chess Analytics Dashboard (v2.10)

## Project overview

This project enhances the existing Chess Analytics website by adding comprehensive statistical analysis and visualizations for Chess.com players. The enhanced dashboard will provide deep insights into player performance across multiple dimensions including win/loss trends, color performance, rating progression, game termination patterns, opening repertoire analysis, opponent strength analysis, and time-of-day performance patterns.

The current implementation provides basic statistics (total wins, losses, draws, and win rates). This enhancement will transform the analytics page into a comprehensive dashboard with 8 detailed analysis sections, enabling players to identify strengths, weaknesses, and patterns in their gameplay over any selected time period.

The system will fetch game data from the Chess.com Public API, process and analyze it server-side, and present interactive visualizations on a clean, modern single-page dashboard. All timestamps will be converted to the user's local timezone for accurate time-based analysis.

**Skills required:**

* Python (Flask)
* Chess.com API integration
* PGN parsing (python-chess library)
* Data analysis and statistics
* Chart.js for visualizations
* JavaScript (ES6+)
* HTML5/CSS3 (modern, clean UI design)
* Timezone handling (both server and client-side)
* SQLite/caching for optimization
* Playwright for E2E testing
* Google Tag Manager integration

---

# PRD change history

This section tracks all iterations and modifications to the PRD document. Engineers should review this section to understand the latest changes and their context.

## Iteration 11 - February 26, 2026

**Version:** 2.10  
**Focus:** Performance optimization & configuration enhancement

### Changes Summary

**Change 1 - Lichess Cloud Evaluation API Integration (EA-018 Enhancement):**
- **Switched:** From local Stockfish execution to Lichess Cloud Evaluation API for move analysis
  - **Problem:** Stockfish.exe is too slow (~45-60 seconds per game, ~20-30 minutes for 30 games)
  - **Initial Target:** 2 seconds per game (60 seconds total for 30 games) ❌ Optimistic
  - **Actual Achieved:** **45-50 seconds per game (1.2-1.5x improvement)** ✅ Realistic
  - **Solution:** Hybrid Lichess Cloud API + ultra-fast Stockfish fallback
- **Implementation approach:** Hybrid model with optimized fallback
  - **Step 1:** Try Lichess Cloud API first (60-80% hit rate, 0.01-0.05s)
  - **Step 2:** Ultra-fast Stockfish fallback (depth=1, time=0.1s, ~1s per evaluation due to UCI overhead)
  - **Actual measured performance:** ~18-20 seconds core analysis + sampling overhead
  - **Total for 30 games:** ~15-20 minutes (vs 20-30 minutes baseline) ✅ 2x improvement
- **Performance Analysis (Measured):**
  - **Lichess hits (61% typical):** 27 positions × 0.03s = ~0.81s (ultra-fast)
  - **Stockfish fallback (39%):** 17 positions × 1.0s = ~17s (UCI communication overhead)
  - **Key insight:** Stockfish UCI protocol has ~1s overhead per call (unavoidable)
  - **Conclusion:** 1.5-2x improvement is realistic and valuable for UX
- **Benefits:**
  - ⚡ **1.5-2x faster** than pure Stockfish (realistic measurement)
  - 💰 **Free** unlimited API calls to Lichess  
  - 🌐 **No local computation** for 60%+ of positions
  - 📊 **60-80% coverage** in Lichess cloud database (varies by game)
  - ✅ **Battle-tested** accuracy (Stockfish 14+ on cloud servers)
- **Fallback strategy:**
  - Keep existing Stockfish code intact (not removed)
  - Ultra-fast fallback: depth=1 when Lichess enabled (vs depth=8 in pure mode)
  - If Lichess API unavailable: system uses 100% Stockfish automatically
  - No manual intervention required  
  - Performance degrades gracefully to previous baseline
- **Configuration:**
  - New setting: `USE_LICHESS_CLOUD=True` (enable cloud API, default: True)
  - New setting: `LICHESS_API_TIMEOUT=1.0` (1s timeout for fast failover)
  - Optimized Stockfish fallback: `ENGINE_DEPTH=8`, `ENGINE_TIME_LIMIT=0.2`
  - Fallback uses depth=1 only when Lichess enabled for ultra-fast evaluation
- **Monitoring:**
  - Track Lichess API hit rate (expected: 60-80%, varies by game)
  - Monitor analysis completion time per game (target: ≤50s)
  - Log fallback usage percentage  
  - Alert if performance degrades below baseline

**Change 2 - Analytics Tracking Configuration (EA-020 Enhancement):**
- **Added:** Dual Google Analytics (GA4) and Google Tag Manager (GTM) support
  - **Google Analytics 4:** `G-VMYYSZC29R` - Direct analytics tracking
  - **Google Tag Manager:** `GT-NFBTKHBS` - Tag management and additional tracking
  - **Rationale:** Comprehensive analytics with both direct GA4 and GTM flexibility
- **Moved:** Configuration from hardcoded templates to `.env` file
  - **Old approach:** Tracking IDs directly embedded in HTML templates
  - **New approach:** Read from environment variables (`GA_MEASUREMENT_ID`, `GTM_CONTAINER_ID`)
- **Implementation:**
  - Add `GA_MEASUREMENT_ID`, `GTM_CONTAINER_ID`, and `GTM_ENABLED` to `config.py`
  - Pass variables from views.py to templates via render_template()
  - Update templates to use Jinja2 variables with conditional rendering
  - Both GA4 and GTM scripts injected when configured
- **Benefits:**
  - ✅ **Dual tracking:** GA4 for core analytics + GTM for flexible tag management
  - ✅ **Easy configuration:** Change IDs without touching code
  - ✅ **Environment-specific:** Different IDs for dev/staging/production
  - ✅ **Quick disable:** Set `GTM_ENABLED=False` to turn off tracking
  - ✅ **Security:** Keep tracking IDs out of version control
- **Configuration:**
  - New setting: `GTM_ENABLED=True` (enable/disable tracking)
  - New setting: `GTM_CONTAINER_ID=GT-NFBTKHBS` (GTM container ID)
  - New setting: `GA_MEASUREMENT_ID=G-VMYYSZC29R` (GA4 measurement ID)
- **Backward compatible:** Existing deployments continue to work

**Change 3 - Homepage Redirect (UX Enhancement):**
- **Changed:** Root URL (`/`) now redirects directly to `/analytics` dashboard
  - **Rationale:** Analytics dashboard is the primary and only interface
  - **Implementation:** Flask redirect in views.py from index() to analytics()
  - **Benefit:** Users land directly on functional page, no extra navigation needed
- **Impact:** Seamless UX, analytics page is the homepage

**Change 4 - Mistake Analysis UI Toggle (EA-021 Configuration):**
- **Added:** Configuration to show/hide mistake analysis section due to performance concerns
  - **Problem:** Lichess Cloud API is slower than expected in real-world conditions (network latency, SSL handshake)
  - **Impact:** Analysis may take longer with Lichess API enabled depending on network conditions
  - **Solution:** Allow users to hide mistake analysis section entirely via `.env` configuration
- **Implementation:**
  - Add `MISTAKE_ANALYSIS_UI_ENABLED` to `config.py` (default: False)
  - Pass variable from views.py to analytics.html template
  - Wrap mistake analysis section (#mistakeAnalysisSection) in Jinja2 conditional
  - JavaScript already has null checks, no changes needed
- **Benefits:**
  - ✅ **Performance control:** Users can disable slow feature if needed
  - ✅ **Quick toggle:** Enable/disable without code changes
  - ✅ **Graceful degradation:** UI adapts cleanly when section is hidden
  - ✅ **Default hidden:** Conservative approach until performance improves
- **Configuration:**
  - New setting: `MISTAKE_ANALYSIS_UI_ENABLED=False` (show/hide UI section)
  - Recommended: Keep `False` until network performance improves
  - Backend still functional: Users can enable if they accept slower analysis
- **Rationale:** Provides control over user experience when performance doesn't meet expectations

### Performance Targets

**Per Game Analysis:**
- Maximum time: **2 seconds** (30 moves analyzed)
- Expected time: **~1.9 seconds**
  - Lichess Cloud (80% of moves): 24 × 0.03s = 0.72s
  - Stockfish fallback (20% of moves): 6 × 0.2s = 1.2s

**Total Analysis (30 games):**
- Maximum time: **60 seconds**
- Expected time: **~57 seconds**
- Speedup vs current: **2.5-3x faster**

### Technical Impact

**New Files:**
- `app/services/lichess_evaluation_service.py` - Lichess Cloud API integration
- `tests/test_lichess_evaluation_service.py` - Unit tests for Lichess service
- `tests/test_performance_lichess.py` - Performance validation tests
- `.github/docs/overview_data_analytics/iterations/iteration_11_summary.md` - Full iteration documentation

**Modified Files:**
- `app/services/mistake_analysis_service.py` - Integrate Lichess Cloud API with Stockfish fallback
- `app/routes/views.py` - Pass GTM configuration and mistake analysis UI flag to templates
- `config.py` - Add Lichess, GTM, GA4, and mistake analysis UI configuration settings
- `.env` - Add all configuration variables for iteration 11
- `.env.example` - Add Lichess, GTM, GA4, and mistake analysis UI environment variables
- `templates/index.html` - Use Jinja2 variables for GTM configuration
- `templates/analytics.html` - Use Jinja2 variables for GTM/GA4 configuration + conditional mistake analysis section
- `tests/test_views.py` - Add tests for GTM configuration rendering
- `prd_overview_data_analysis.md` - Document iteration changes (this file)

**Configuration Changes:**
```bash
# .env additions/updates
USE_LICHESS_CLOUD=True
LICHESS_API_TIMEOUT=1.0
ENGINE_DEPTH=8
ENGINE_TIME_LIMIT=0.2

# Analytics tracking
GTM_ENABLED=True
GTM_CONTAINER_ID=GT-NFBTKHBS
GA_MEASUREMENT_ID=G-VMYYSZC29R

# Mistake analysis UI control (new in Change 4)
MISTAKE_ANALYSIS_UI_ENABLED=False  # Default: hidden due to performance
```

### Testing Strategy

**Phase 1: Unit Tests**
- Test Lichess API service with standard positions
- Test timeout handling and error cases
- Test GTM/GA4 configuration rendering
- Test GTM/GA4 enable/disable functionality
- Test mistake analysis UI visibility toggle

**Phase 2: Integration Tests**
- Test mistake analysis with Lichess + Stockfish hybrid
- Test GTM/GA4 script injection in templates
- Test fallback behavior when Lichess API unavailable
- Test analytics page with MISTAKE_ANALYSIS_UI_ENABLED=True/False

**Phase 3: Performance Tests**
- ~~**Critical:** Verify 30 moves analyzed in ≤2 seconds per game~~ ❌ Not achievable (UCI overhead)
- **Realistic target:** Verify 1.5-2x improvement over pure Stockfish
- Measure Lichess API hit rate (target: 60-80%)
- Monitor per-game analysis time (target: ≤50 seconds)

**Phase 4: Production Verification**
- Monitor analysis time in production
- Monitor Lichess API success rate
- Verify GTM tracking in Google Analytics
- Verify GA4 tracking in Google Analytics
- Test mistake analysis section visibility control
- Check for API rate limiting issues

### Deployment Notes

**Pre-deployment checklist:**
- [ ] Update `.env` with new configuration variables
- [ ] Run all unit and integration tests
- [ ] Run performance tests to validate 2s per game target
- [ ] Verify Lichess API connectivity
- [ ] Backup current configuration

**Rollback plan:**
- Set `USE_LICHESS_CLOUD=False` to disable cloud API
- Set `GTM_ENABLED=False` to disable tracking
- No code rollback required (fallbacks built-in)

### Documentation Updates
- ✅ Created `iteration_11_summary.md` with complete implementation details
- ✅ Updated PRD version from 2.9 to 2.10
- ✅ Added Iteration 11 changelog entry
- [ ] Update `documentation.md` with changes summary
- [ ] Update `milestone_progress.md` if applicable
- [ ] Update `DEPLOYMENT_GUIDE.md` with new environment variables

---

## Iteration 10 - February 20, 2026

**Version:** 2.9  
**Focus:** Google Tag Manager integration for visitor tracking

### Changes Summary

**New Feature - Website Analytics Tracking (EA-020):**
- **Added:** Google Tag Manager (GTM) integration across all pages
  - **Purpose:** Track website visitors, page views, and user interactions
  - **Tag IDs:** 
    * Primary: G-VMYYSZC29R (Google Analytics 4)
    * Container: GT-NFBTKHBS (GTM Container)
  - **Implementation:**
    * Add GTM script in `<head>` section of all HTML templates
    * Add noscript fallback immediately after `<body>` tag
    * No backend changes required
  - **Affected templates:**
    * `templates/index.html` (home page)
    * `templates/analytics.html` (analytics dashboard)
  - **Rationale:** 
    * Understand user behavior and traffic patterns
    * Track page views, session duration, and user flow
    * Measure feature adoption and usage metrics
    * Make data-driven decisions for future improvements
- **Privacy considerations:**
  - GTM respects user privacy settings and DNT (Do Not Track) headers
  - No personally identifiable information (PII) is tracked
  - Only aggregated analytics data is collected
- **Testing:**
  - Verify GTM tags fire correctly on both pages
  - Test with GTM Preview mode to validate tracking
  - Ensure page load performance is not impacted

### Technical Impact
- Frontend (index.html): Add GTM script tags in <head> and noscript after <body>
- Frontend (analytics.html): Add GTM script tags in <head> and noscript after <body>
- No backend changes required
- No JavaScript changes required (GTM handles tracking automatically)

---

## Iteration 9 - February 20, 2026

**Version:** 2.8  
**Focus:** Simplified AI recommendations - section insights only

### Changes Summary

**Section 10 - AI Chess Advisor (EA-019):**
- **Removed:** Overall Recommendation section
  - **v2.7 approach:** Display 9 section-specific recommendations + 1 overall recommendation
  - **v2.8 approach:** Display ONLY 9 section-specific recommendations (no overall synthesis)
  - **Rationale:** Section-specific insights are more actionable; overall recommendation was redundant
- **UI simplification:**
  - Removed "🎯 Overall Recommendation" heading and content area
  - Kept "📋 Key Insights by Section" as the only AI output
  - Each section still shows 1-2 concise bullet points
- **Backend changes:**
  - Updated `SYSTEM_PROMPT` to generate only section recommendations (not overall)
  - Updated `USER_PROMPT_TEMPLATE` to remove overall recommendation format
  - Removed `overall_recommendation` from API response structure
  - Returns only `section_suggestions` (list of 9 section dicts)
- **Token optimization:**
  - max_tokens remains 600 (sufficient for 9 sections with 1-2 bullets each)
  - Reduced prompt complexity and API response parsing

### Technical Impact
- Frontend (analytics.html): Remove overall recommendation div
- Frontend (analytics.js): Remove `renderAIOverall()` call
- Backend (chess_advisor_service.py): Update prompts, remove overall parsing/generation
- Backend (chess_advisor_service.py): Update `_generate_fallback_advice()` to exclude overall

---

## Iteration 8 - February 20, 2026

**Version:** 2.7  
**Focus:** Enhanced table display and restored section-based AI recommendations

### Changes Summary

**Section 9 - Move Analysis by Game Stage (EA-018):**
- **Added:** "Number of games" row to table
  - **Old format:** Table showed only move quality rows (early/middle/late game)
  - **New format:** First row shows "Number of games: [X]" before move quality rows
  - **Rationale:** Provides immediate context for sample size, matches user template mockup
- **Display format:** 
  ```
  Number of games | XXX |     |          |
  early game      | 2.3 | 5.1 | 1.2     |
  middle game     | 3.1 | 4.8 | 0.9     |
  late game       | 2.8 | 5.3 | 1.5     |
  ```

**Section 10 - AI Chess Advisor (EA-019):**
- **Restored:** Section-specific recommendations with concise bullet format
  - **v2.6 approach:** Display only overall recommendation (removed 9 section suggestions)
  - **v2.7 approach:** Display section-specific recommendations AS bullet points + overall recommendation
  - **Rationale:** Users want section-specific guidance but in concise format
- **Format change:** Each section recommendation is now 1-2 bullet points (not paragraphs)
  - **Example:**
    * **Section 1 - Overall Performance:**
      - Focus on maintaining your upward rating trend (+85 points)
      - Target 55%+ win rate by reducing timeout losses
    * **Section 2 - Color Performance:**
      - Practice more games as White (currently 20% lower win rate than Black)
- **Updated:** System prompt to generate concise bullet recommendations per section
  - Each section gets 1-2 actionable bullet points maximum
  - Overall recommendation remains 3-5 bullets
- **Updated:** Token limit from 300 to 600
  - **Old:** max_tokens=300 (only overall recommendation)
  - **New:** max_tokens=600 (9 sections + overall, but concise bullets)
  - **Rationale:** More comprehensive guidance requires more tokens, but still efficient
- **Updated:** API response structure
  - **Old (v2.6):** Returns only `overall_recommendation`
  - **New (v2.7):** Returns `section_suggestions` (list of dicts with section info and bullet points) + `overall_recommendation`
  - **Rationale:** Matches frontend display structure
- **Display structure:**
  - Key suggestions from each section (9 sections)
  - Overall recommendation synthesizing all insights
  - Format: Clean bullet lists, no token/cost display

### Technical Impact
- Frontend (analytics.html): Add "Number of games" row to table, restore section suggestions area
- Frontend (analytics.js): Add number of games row rendering, restore section suggestions rendering with bullet format
- Backend (chess_advisor_service.py): Restore section-based prompt and parsing logic
- Backend (chess_advisor_service.py): Update max_tokens from 300 to 600
- Backend (chess_advisor_service.py): Modify prompts to generate 1-2 bullets per section
- Backend (chess_advisor_service.py): Return both section_suggestions and overall_recommendation

---

## Iteration 7 - February 20, 2026

**Version:** 2.6  
**Focus:** Simplified UI for move analysis and streamlined AI recommendations

### Changes Summary

**Section 9 - Move Analysis by Game Stage (EA-018):**
- **Updated:** Table layout and column order for better clarity
  - **Old format:** Game Stage | Avg Brilliant/Game | Avg Neutral/Game | Avg Mistakes/Game | Total Games Analyzed
  - **New format:** Table with header "Moves analysis - Average number of Mistake/Neutral/Brilliant moves per game"
    * Column order: Mistake | Neutral | Brilliant (prioritizes identifying weaknesses first)
    * Removed "Total Games Analyzed" column from main table (shown in analysis info below)
  - **Rationale:** Matches user's preferred layout, puts focus on mistakes first for actionable insights
- **Updated:** Row labels for consistency
  - **Old:** "Early (First 10)", "Middle (Sampled 10)", "Late (Last 10)"
  - **New:** "early game (1-10 moves)", "middle games (sample 10 consecutive moves)", "late game (last 10 moves)"
  - **Rationale:** More descriptive, lowercase format matches user mockup
- **Simplified:** Visual summary cards
  - **Removed:** "Most Common Error" card (redundant with stage analysis)
  - **Kept:** "Weakest Stage" and "Total Mistakes" cards
  - **Rationale:** Reduces visual clutter, focuses on key metrics
- **Updated:** Sample info text to reflect v2.5 classification (Brilliant/Neutral/Mistake)

**Section 10 - AI Chess Advisor (EA-019):**
- **Removed:** Section-specific recommendations (9 individual section suggestions)
  - **Old:** Displayed 9 section-specific recommendations + 1 overall recommendation
  - **New:** Display only overall recommendation
  - **Rationale:** Reduces information overload, focuses on actionable priorities
- **Updated:** Overall recommendation format
  - **Old:** Paragraph format with "Priority 1, Priority 2, Priority 3..."
  - **New:** Concise bullet points (3-5 bullets, 1-2 sentences each)
  - **Rationale:** Easier to scan and digest, more actionable
- **Removed:** Token usage and estimated cost display
  - **Old:** Displayed "tokens_used" and "estimated_cost" in UI
  - **New:** Token usage logged internally only, not shown to users
  - **Rationale:** Technical metrics not relevant to end users
- **Removed:** YouTube video recommendations
  - **Old:** Integrated video links for opening performance
  - **New:** Overall recommendation text only
  - **Rationale:** Simplifies implementation, focuses on core coaching advice
- **Updated:** System prompt to generate only overall recommendation
  - **Old:** Generated 10 recommendations (9 sections + 1 overall)
  - **New:** Generates 1 overall recommendation as bullet points
  - **Rationale:** Reduces API token usage, more focused advice
- **Updated:** Token limit from 500 to 300
  - **Old:** max_tokens=500
  - **New:** max_tokens=300
  - **Rationale:** Shorter response format requires fewer tokens, reduces cost
- **Updated:** API response structure
  - **Old:** Returns `section_suggestions`, `overall_recommendation`, `tokens_used`, `estimated_cost`
  - **New:** Returns only `overall_recommendation`
  - **Rationale:** Simplified data structure matches simplified UI
- **Updated:** Acceptance criteria
  - Removed criteria for section-specific recommendations
  - Removed criteria for YouTube video integration
  - Updated cost target from <$0.012 to <$0.008 (lower token usage)
  - Clarified that token usage is logged internally, not displayed

### Technical Impact
- Frontend (analytics.html): Update move analysis table structure and column order
- Frontend (analytics.js): Remove section-specific recommendation rendering logic
- Frontend (analytics.js): Update AI advisor to display only bullet point format
- Backend (chess_advisor_service.py): Modify system prompt and user prompt template
- Backend (chess_advisor_service.py): Update `generate_advice()` return structure
- Backend (chess_advisor_service.py): Add internal logging method `_log_usage()`
- Backend (chess_advisor_service.py): Update `_parse_advice_response()` to extract bullet points
- Backend: Reduce max_tokens from 500 to 300

---

## Iteration 6 - February 19, 2026

**Version:** 2.5  
**Focus:** Move quality analysis, opening performance refinement, and AI advisor re-enablement

### Changes Summary

**Section 6 - Opening Performance Analysis (EA-016):**
- **Simplified:** Display top 5 openings instead of top 10
  - **Old:** Top 10 openings combined or by color
  - **New:** Top 5 openings for White, Top 5 for Black separately
  - **Rationale:** Focused display reduces cognitive load, easier pattern recognition
- **Updated:** Backend to limit results to 5 per color
- **Updated:** Frontend display to show "Top 5" instead of "Top 10"

**Section 9 - Move Analysis by Game Stage (EA-018):**
- **Renamed:** "Mistake Analysis" → "Move Analysis by Game Stage"
  - **Rationale:** Positive framing - analyze all move qualities, not just mistakes
- **Major Enhancement:** Track move quality across all categories
  - **Added:** Brilliant moves (≥+100 CP gain)
  - **Added:** Neutral moves (-49 to +99 CP range)
  - **Changed:** Mistake moves (≥-50 CP loss, combining old inaccuracies/mistakes/blunders)
  - **Old metrics:** Inaccuracies (50-100 CP), Mistakes (100-200 CP), Blunders (200+ CP)
  - **New metrics:** 
    * Brilliant moves: ≥+100 CP gain
    * Neutral moves: -49 to +99 CP (neither gains nor loses significantly)
    * Mistake moves: ≤-50 CP loss (combining all error types)
- **Display format:** Average count per game for each category
  - Example: "Early Game: 2.3 brilliant, 5.1 neutral, 1.8 mistakes per game"
  - **Rationale:** Game-level aggregation more meaningful than total counts
- **Game stage definitions remain unchanged:**
  - Early: First 10 moves per player
  - Late: Last 10 moves per player
  - Middle: 10 consecutive sampled moves from middle of game
- **Updated:** Backend tracking logic to classify all moves into 3 categories
- **Updated:** Frontend UI to display 3 metrics (brilliant/neutral/mistake) per stage
- **Updated:** Summary cards to show strengths (brilliant) alongside weaknesses (mistakes)

**Section 10 - AI Chess Advisor (EA-010):**
- **Re-enabled:** AI advice section in frontend
  - **Changed:** `include_ai_advice: false` → `include_ai_advice: true` 
  - **Status:** Feature fully implemented but disabled by default
  - **OpenAI API:** Key present in .env file, GPT-4o-mini configured
  - **Rationale:** User request to restore personalized coaching recommendations

### Technical Impact
- Backend: Modify `MistakeAnalysisService.analyze_game_mistakes()` to track move quality
- Backend: Modify `AnalyticsService._analyze_opening_performance()` to limit to top 5
- Frontend: Update analytics.js move analysis rendering
- Frontend: Change `include_ai_advice` flag to `true` in two locations
- HTML: Update section titles and metric labels

---

## Iteration 5 - February 18, 2026

**Version:** 2.3  
**Focus:** Enhanced data visualization clarity, detailed statistics, and refined analysis logic

### Changes Summary

**Section 2 - Performance by Color (EA-014):**
- **Enhanced:** Summary cards now display complete statistics
  - **Added:** Actual win, loss, and draw counts in addition to totals and win rates
  - **Old:** Total games, Win rate %
  - **New:** Total games, Wins, Losses, Draws, Win rate %
  - **Example:** "Total games: 42 | Wins: 24 | Losses: 15 | Draws: 3 | Win Rate: 57.1%"
  - **Rationale:** Users want absolute numbers for better context without hovering
- **Updated:** Acceptance criteria to include W/L/D counts in summary cards

**Sections 4 & 5 - Termination Type Visualization (EA-015):**
- **Simplified:** Pie chart display for cleaner, minimalist design
  - **Changed:** Show only numbers inside segments (e.g., "32" instead of "Checkmate: 32")
  - **Removed:** Legend completely (reduces visual clutter)
  - **Maintained:** Full details in hover tooltips (Category name, Count, Percentage)
  - **Rationale:** Numbers are most important at a glance, legend is redundant with tooltips
- **Updated:** Chart.js configuration to hide legend and show numeric values only
- **Updated:** Acceptance criteria to reflect simplified display

**Section 6 - Opening Performance Analysis (EA-016):**
- **Enhanced:** Comprehensive opening analysis matching notebook implementation
  - **Added:** Display first 6 full moves (12 individual moves) in standard notation
  - **Added:** Lichess board editor URL for position visualization
  - **Added:** Chess.com example game URL for each opening
  - **Changed:** Separate displays for White and Black openings (not combined)
  - **Format:** "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5"
  - **URLs:** Lichess shows position after 6 moves, Chess.com shows real game example
  - **Rationale:** 
    * Matches notebook analysis consistency (user request)
    * Visual learning with Lichess board
    * Real game context with Chess.com examples
    * Color separation helps understand repertoire
- **Implementation:** Enhanced `_analyze_opening_performance()` with URL generation
- **Updated:** Acceptance criteria with move display and URL requirements
- **Updated:** Test case TC-018 to verify moves, URLs, and color separation

**Section 9 - Mistake Analysis Optimization (EA-018):**
- **Refined:** Dynamic sampling logic based on dataset size
  - **Old:** Fixed 2-game analysis for all datasets (iteration 4 approach)
  - **New:** Smart logic based on total games:
    * If <50 games: Analyze ALL games (comprehensive analysis)
    * If ≥50 games: Use 20% sampling (min 10, max 50 games)
  - **Examples:**
    * 10 games → Analyze 10 (100%)
    * 30 games → Analyze 30 (100%)
    * 50 games → Analyze 10 (20%)
    * 100 games → Analyze 20 (20%)
    * 300 games → Analyze 50 (16.7%, max)
  - **Rationale:**
    * Small datasets need full analysis for statistical confidence
    * Large datasets use sampling for performance
    * With 30-day limit, most users have 20-50 games (full or near-full analysis)
    * Better accuracy for moderate activity users
- **Performance optimized:** Stockfish engine settings refined for 2-3x speed improvement
  - **Depth:** 12 → 8 (70% faster per position)
  - **Time limit:** 1.5s → 0.5s (67% faster)
  - **Early stop:** 500 CP → 300 CP (stops obvious blunders sooner)
  - **NEW:** Skip analyzing positions with >600 CP advantage (game already decided)
  - **Opening moves:** Kept in analysis (players make mistakes in early game)
  - **Result:** ~15 seconds → ~5-7 seconds per game, 85% accuracy retained
- **LATEST OPTIMIZATION (February 18, 2026):** Strategic Move Sampling
  - **Depth:** 8 → 10 (better accuracy on sampled moves)
  - **Strategy:** Analyze maximum 30 moves per game instead of all moves
    * First 10 player moves (opening phase - critical for learning)
    * Last 10 player moves (endgame phase - conversion/defense)
    * Middle 10 moves sampled evenly (middlegame - representative sampling)
  - **Coverage examples:**
    * 20-move game: Analyze all 20 moves (100%)
    * 40-move game: Analyze 30 moves (75% - first 10 + middle 10 + last 10)
    * 60-move game: Analyze 30 moves (50% - strategic sampling)
    * 80-move game: Analyze 30 moves (37.5% - strategic sampling)
  - **Performance:** ~5-7 seconds → ~2-3 seconds per game (additional 2x faster)
  - **Accuracy:** ~85% → ~90% (better depth on critical moves)
  - **Rationale:**
    * Opening (first 10): Most mistakes happen here, critical for pattern learning
    * Endgame (last 10): Technique evaluation, winning/losing decisions
    * Middlegame (sampled 10): Representative coverage without analyzing every move
    * Combined gain: 3-4x faster than initial v2.3 implementation
- **Display changes:**
  * <50 games: "Comprehensive analysis of X games"
  * ≥50 games: "Analysis based on X games (Y% sample)"
- **Updated:** Implementation with conditional sampling logic and optimized engine settings
- **Updated:** Acceptance criteria with dataset size thresholds
- **Updated:** Test case TC-021 to verify dynamic sampling

**Testing Updates:**
- **Modified:** TC-016 to verify W/L/D counts in color performance cards
- **Modified:** TC-017 to verify numbers-only display and hidden legend
- **Modified:** TC-018 to verify first 6 moves, Lichess URL, Chess.com URL, color separation
- **Modified:** TC-021 to verify <50 vs ≥50 game sampling logic

**Documentation:**
- **Updated:** Document version from 2.2 to 2.3
- **Updated:** "Last Updated" date to February 18, 2026
- **Added:** Changelog entry for version 2.3

### Implementation Notes for Engineers

**Priority 1 - Section 6 (Opening Performance):**
- Implement first 6 moves extraction (already exists in `_extract_first_six_moves()`)
- Generate Lichess URL: `https://lichess.org/editor/{urllib.parse.quote(fen)}`
- Store example game URL when tracking opening statistics
- Separate White and Black openings in response structure
- Update frontend to display moves and clickable URLs

**Priority 2 - Section 9 (Mistake Analysis):**
- Implement conditional logic: `if len(games) < 50: analyze_all else: sample_20_percent`
- Update analysis note display based on dataset size
- Maintain stratified sampling for ≥50 game datasets

**Priority 3 - Section 2 (Color Performance):**
- Add W/L/D counts to color performance summary calculation
- Update API response structure with wins, losses, draws fields
- Update frontend summary card template

**Priority 4 - Sections 4 & 5 (Termination Visualization):**
- Update Chart.js config: `legend: { display: false }`
- Update datalabels: `formatter: (value) => value` (number only)
- Ensure tooltip shows full details

---

## Iteration 4 - December 31, 2025

**Version:** 2.2  
**Focus:** Performance optimization, user-centric opening analysis, and date range restrictions

### Changes Summary

**Global Change - Date Range Restrictions:**
- **Added:** Maximum date range validation (30 days)
  - **Allowed periods:** "Last 7 days" or "Last 30 days" (preset options)
  - **Custom range:** Maximum 30 days allowed
  - **Rationale:** 
    * Ensures analysis completes within 1 minute (performance goal)
    * Focuses user on recent, actionable data
    * Reduces API load and server costs
- **Error handling:**
  - If user selects >30 days: Display error message
  - Message: "Please select a date range of 30 days or less. For best results, use 'Last 7 days' or 'Last 30 days'."
  - Prevent form submission until valid range selected
- **UI changes:**
  - Add prominent preset buttons: [Last 7 Days] [Last 30 Days]
  - Date picker allows custom range but validates on submit
  - Show helper text: "Max 30 days for optimal performance"
- **Performance impact:**
  - 7 days: ~5-15 games → 1-3 analyzed → ~30-60 seconds
  - 30 days: ~20-50 games → 4-10 analyzed → ~45-90 seconds
  - Target: <1 minute for 95% of analyses

**Section 6 - Opening Performance Analysis (EA-006):**
- **Changed:** Complete redesign from best/worst openings to frequency-based analysis
  - **Old:** "Top Best Openings" / "Top Worst Openings" with minimum 3 games threshold
  - **New:** "Top 10 Most Common Openings" with win rate analysis
  - **Rationale:** 
    * Users care more about their frequently-played openings than rare high-performing ones
    * Better insight into repertoire patterns and where to focus improvement
    * Avoids misleading stats from small sample sizes (e.g., 100% win rate from 1 game)
- **Removed:** Best/worst categorization, 3-game minimum threshold
- **Removed:** First 6 moves display and interactive chess board (complexity not justified for frequency view)
- **Added:** Single table/chart showing top 10 openings by frequency
- **Display:** Opening name, games played count, win rate %, win-loss-draw breakdown
- **Sorting:** Descending by games played (most to least common)
- **Updated:** Acceptance criteria to reflect frequency-based display
- **Updated:** Test case TC-018 to verify top 10 frequency ranking

**Section 9 - Mistake Analysis Optimization (EA-018):**
- **Added:** Intelligent sampling strategy for performance optimization
  - **Problem:** Full analysis takes ~66 minutes for 50 games (2s × 40 moves × 50)
  - **Solution:** Multi-tier approach with 20% sampling
- **Sampling algorithm:**
  * Always analyze 20% of total games (random stratified sample)
  * Stratification: Ensure sample includes games from all time periods and outcomes
  * Minimum 10 games analyzed, maximum 50 games (even if 20% exceeds this)
  * Cache all analyzed games permanently
  * Over time, coverage increases without repeating work
- **User communication:**
  * Display: "Analysis based on X games (Y% of total)"
  * Confidence indicator: "High confidence" (>50 games) / "Good confidence" (20-50) / "Limited data" (<20)
  * Tooltip: "For faster results, we analyze a representative sample. Results are cached and improve over time."
- **Research-based approach:**
  * Based on statistical sampling principles (20% sample provides ~90% accuracy for pattern detection)
  * Chess mistake patterns are consistent across games (validated in chess education research)
  * Focus on PATTERN identification (which stages have issues) not absolute counts
- **Alternative considered:** Critical position analysis (analyze only tactical positions)
  * Rejected: Requires pre-classification of positions, adds complexity
  * Sampling is simpler, well-understood, and statistically sound
- **Performance improvement:**
  * Before: 66 minutes for 50 games
  * After: ~13 minutes for 10 games (20% sample) on first run
  * Subsequent runs: <5 seconds (cached)
  * User acceptable: <15 minutes for initial analysis
- **Updated:** Implementation details with sampling logic
- **Updated:** Acceptance criteria with sampling requirements
- **Updated:** Test cases to verify sampling and confidence indicators

**Testing Updates:**
- **Modified:** TC-018 to verify top 10 most common openings (not best/worst)
- **Added:** TC-021A to verify sampling strategy (20%, stratified, min/max limits)
- **Added:** TC-021B to verify confidence indicators based on sample size
- **Added:** TC-021C to verify cache persistence across analyses

**Documentation:**
- **Updated:** Document version from 2.1 to 2.2
- **Updated:** "Last Updated" date to December 31, 2025
- **Added:** Changelog entry for version 2.2

### Implementation Notes for Engineers

**Priority 1 - Section 9 (Mistake Analysis Optimization):**
- Implement stratified random sampling (20% of games)
- Sample stratification by: date (even distribution across period) + outcome (W/L/D ratio maintained)
- Min 10 games, max 50 games analyzed per request
- Cache structure: Store analyzed games by game URL + analysis timestamp
- Display sample size and confidence level prominently
- Add tooltip explaining sampling approach

**Priority 2 - Section 6 (Opening Performance Redesign):**
- Remove best/worst categorization logic
- Remove 3-game minimum filter
- Remove move sequence display and chess board components
- Implement frequency-based sorting (descending by games played)
- Display top 10 only (or fewer if player has <10 unique openings)
- Show: Opening name, Games played, Win rate %, W-L-D counts
- Update frontend to single table or horizontal bar chart

---

## Iteration 3 - December 26, 2025

**Version:** 2.1  
**Focus:** UI refinements, data enhancements, and YouTube integration

### Changes Summary

**Section 6 - Opening Performance Analysis (EA-006):**
- **Changed:** Removed "Top 5" restriction from opening display headings
  - **Old:** "Top 5 Best Openings" / "Top 5 Worst Openings"
  - **New:** "Top Best Openings" / "Top Worst Openings" (dynamic count)
  - **Rationale:** Flexible display when fewer than 5 openings meet criteria
- **Added:** First 6 chess moves display requirement
  - Display moves in standard chess notation (e.g., "1. e4 e5 2. Nf3 Nc6 3. Bb5")
  - Shows moves for each opening listed in top best/worst categories
- **Added:** Interactive chess board display
  - Visual board showing position after move 6 for each opening
  - Helps users visualize and learn opening positions
- **Updated:** Acceptance criteria to reflect dynamic count and new display requirements

**Section 8 - Time of Day Performance (EA-008):**
- **Enhanced:** Timezone conversion verification requirements
  - Added explicit requirement for backend to receive timezone parameter
  - Emphasized UTC to user local timezone conversion before categorization
  - Added requirement for timezone display in Section 8 header
  - Added manual testing requirements across multiple timezones (EST, PST, GMT+8)
  - **Rationale:** Ensure accurate time-based analysis for users worldwide
- **Updated:** Acceptance criteria with specific timezone verification checkpoints
- **Status:** Changed critical timezone-related criteria from completed to pending verification

**Section 9 - Mistake Analysis by Game Stage (EA-018):**
- **Refined:** Critical mistake game link selection criteria
  - **Old:** "Link to game with biggest blunder in this stage"
  - **New:** Must meet ALL criteria:
    * Player LOST the game (not won, not drawn)
    * Game ended by RESIGNATION (not timeout or abandonment)
    * Contains biggest CP drop in stage across qualifying games
    * CP drop must be "significant" (threshold determined from data analysis)
    * Link opens game on Chess.com at exact mistake position
  - **Rationale:** Provide most relevant examples for learning from mistakes
- **Added:** Algorithm requirement to determine "significant" CP drop threshold from data
- **Added:** Fallback display "No qualifying game" when no games meet all criteria
- **Updated:** Acceptance criteria with detailed game link requirements
- **Updated:** Test case TC-021 to verify new criteria

**Section 10 - AI Chess Advisor (EA-019):**
- **Restructured:** Recommendation format from flexible to fixed structure
  - **Old:** "Up to 7 section-specific suggestions" + 1 overall
  - **New:** EXACTLY 9 section-specific recommendations (one per section 1-9) + 1 overall
  - **Rationale:** Ensure comprehensive coverage of all analytics sections
- **Added:** YouTube video integration for opening tutorials
  - Video source prioritization: ChessNetwork > GMHikaru > GothamChess > Chessbrahs
  - Show 1 video recommendation per frequently-played opening (3+ games)
  - Implementation options: Curated database (recommended) OR YouTube/Google API search
  - Video format: "[Opening Name]: [Video Title] by [Channel] - [Watch Link]"
- **Updated:** System prompt to generate exactly 9+1 recommendations with clear section labels
- **Updated:** User prompt template with specific format for all 9 sections + overall
- **Updated:** Token budget from 500 to 800 (cost estimate: $0.008-$0.012, still under target)
- **Added:** Rate limiting for YouTube API if used (max 100 searches/day)
- **Updated:** UI mockup to show structured 9+1 format with video links
- **Updated:** Acceptance criteria with YouTube integration requirements
- **Updated:** Test cases TC-024 and TC-025 to verify 9+1 structure and video links
- **Updated:** EA-019 user story acceptance criteria

**Testing Updates:**
- **Modified:** TC-018 to verify dynamic opening count and chess notation display
- **Enhanced:** TC-024 to verify exact count of 9+1 recommendations with section labels
- **Enhanced:** TC-025 to verify YouTube video recommendations and channel priority

**Documentation:**
- **Updated:** Document version from 2.0 to 2.1
- **Updated:** "Last Updated" date to December 26, 2025
- **Added:** Changelog entry for version 2.1

### Implementation Notes for Engineers

**Priority 1 - Section 10 (AI Advisor):**
- Requires OpenAI API integration updates (system and user prompts)
- YouTube video database creation OR API integration needed
- Parser updates for structured 9+1 response format
- Frontend UI updates for new display structure

**Priority 2 - Section 9 (Mistake Analysis):**
- Filter algorithm for game selection (lost by resignation only)
- CP drop threshold calculation from data distribution
- Game link generation with position parameters

**Priority 3 - Section 6 (Opening Performance):**
- Remove hardcoded "5" from UI labels
- Chess notation formatting for first 6 moves
- Chess board component integration (interactive display)

**Priority 4 - Section 8 (Time of Day):**
- Verification testing across multiple timezones
- Ensure timezone parameter flows from frontend to backend
- Add timezone display to Section 8 UI header

---

## Iteration 2 - December 12, 2025

**Version:** 2.0  
**Focus:** Advanced analysis features with AI/ML integration

### Changes Summary

**New Milestone Added: Milestone 8 - Game Stage Mistake Analysis**
- **Added:** Section 9 - Mistake Analysis by Game Stage (EA-018)
  - Chess engine integration using Stockfish 15+
  - Mistake classification: Inaccuracies (50-100 CP), Mistakes (100-200 CP), Blunders (200+ CP)
  - Game stage categorization: Early (1-7 moves), Middle (8-20 moves), Endgame (21+ moves)
  - Missed opportunity detection
  - Performance optimization with caching and parallel processing
  - Table visualization with critical mistake game links
- **Added:** Test cases TC-021, TC-022, TC-023 for engine analysis functionality

**New Milestone Added: Milestone 9 - AI-Powered Chess Advisor**
- **Added:** Section 10 - AI Chess Advisor Recommendations (EA-019)
  - OpenAI GPT-4-turbo API integration
  - Personalized coaching advice based on all 9 sections
  - Summary data preparation (no raw PGN sent)
  - System prompt design for expert chess coach persona
  - Cost control: <$0.01 per analysis target
  - Caching strategy (1-hour TTL)
  - Fallback to rule-based advice on API failure
- **Added:** Test cases TC-024 through TC-030 for AI advisor functionality

**Tech Stack Updates:**
- **Added:** `python-chess` library for Stockfish integration
- **Added:** `openai` Python library for GPT-4 API
- **Added:** Stockfish chess engine (local installation)
- **Added:** Redis recommendation for caching engine analysis and AI advice
- **Added:** Multiprocessing for parallel game analysis

**System Architecture Updates:**
- **Added:** Mistake Analysis Engine component
- **Added:** Stockfish Engine integration
- **Added:** AI Advisor Service component
- **Added:** OpenAI GPT-4 API integration
- **Updated:** Cache layer to include engine analysis and AI advice

**Success Metrics Updates:**
- **Added:** API response time target: <10 seconds (including engine analysis)
- **Added:** Stockfish analysis accuracy validation requirement
- **Added:** AI advisor relevance assessment (qualitative)
- **Added:** AI API cost metric: <$0.01 per analysis
- **Updated:** Total test cases from 20 to 30

**Documentation:**
- **Updated:** Document version from 1.0 to 2.0
- **Updated:** Total sections from 8 to 10
- **Updated:** "Last Updated" date to December 12, 2025

---

## Iteration 1 - December 5-6, 2025

**Version:** 1.0  
**Focus:** Core analytics infrastructure and UI enhancements

### Initial PRD Creation (December 5, 2025)

**Milestones 1-6 Defined:**
- Milestone 1: Core analytics infrastructure and data processing
- Milestone 2: Backend API endpoints
- Milestone 3: Frontend dashboard UI foundation
- Milestone 4: Analytics visualizations - Part 1 (Sections 1-3)
- Milestone 5: Analytics visualizations - Part 2 (Sections 4-6)
- Milestone 6: Analytics visualizations - Part 3 (Sections 7-8)

**Initial Sections (EA-001 through EA-012):**
- Section 1: Overall performance over time
- Section 2: Color performance over time
- Section 3: Elo rating progression
- Section 4: How I win games (termination types)
- Section 5: How I lose games (termination types)
- Section 6: Opening performance analysis
- Section 7: Opponent strength analysis
- Section 8: Time of day performance

**Test Cases Defined:**
- TC-001 through TC-014: Core analytics workflow and visualization tests

### Milestone 7 Added (December 6, 2025)

**UI Enhancement and Visualization Updates:**
- **Modified:** Section 1 (EA-013) - Simplified to single win rate line chart
- **Modified:** Section 2 (EA-014) - Unified White/Black performance in single chart with summary cards
- **Enhanced:** Sections 4 & 5 (EA-015) - Added count labels inside pie chart segments
- **Enhanced:** Section 6 (EA-016) - Integrated Lichess Opening Database for human-readable names
- **Simplified:** Sections 7 & 8 (EA-017) - Replaced bar charts with card-based display

**Test Cases Added:**
- TC-015 through TC-020: UI enhancement verification tests

**Milestone Completion:**
- Marked Milestones 1-6 as completed (December 6, 2025)
- Marked Milestone 7 as completed (December 6, 2025)

**File Naming:**
- Renamed from initial draft to `prd_overview_data_analysis.md`

---

## How to Use This Section

**For Engineers:**
1. Always check this section first when returning to the PRD
2. Review the latest iteration to understand recent changes
3. Pay attention to "Implementation Notes" for priority guidance
4. Check "Rationale" fields to understand why changes were made

**For Product Managers:**
1. Document all PRD changes in this section immediately after approval
2. Include clear before/after comparisons for modified requirements
3. Provide rationale for significant changes
4. Link to relevant discussions or decisions

**For QA/Testers:**
1. Review changed sections to update test plans
2. Check test case modifications (TC-XXX references)
3. Verify acceptance criteria updates

---

# Key features

## Milestone 1: Core analytics infrastructure and data processing

**Status:** ✅ Completed  
**Completion Date:** December 6, 2025

### Enhanced data fetching and parsing

* Extend `ChessService` to fetch complete game data including PGN
* Implement PGN parser to extract opening moves and names
* Extract and normalize all game metadata (ratings, termination types, timestamps)
* Add timezone conversion utilities for timestamp handling
* Implement efficient caching strategy for analyzed data

### Data analysis engine

* Create `AnalyticsService` for statistical calculations
* Implement daily aggregation functions for time-series data
* Build opening name extraction from PGN (first 5-10 moves)
* Calculate Elo differentials for opponent strength analysis
* Process termination types from game metadata
* Handle time-of-day categorization with timezone awareness

### Database schema enhancements

* Consider caching layer for processed analytics (optional)
* Store analysis metadata to avoid redundant API calls
* Design efficient data structures for quick retrieval

---

## Milestone 2: Backend API endpoints

**Status:** ✅ Completed  
**Completion Date:** December 6, 2025

### Analytics API endpoint

* Create `/api/analyze/detailed` endpoint
* Accept parameters: `username`, `start_date`, `end_date`, `timezone`
* Return comprehensive analysis results for all 8 sections
* Implement proper error handling and validation
* Add rate limiting to prevent API abuse

### Response structure

```json
{
  "username": "jay_fh",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "timezone": "America/New_York",
  "total_games": 150,
  "sections": {
    "overall_performance": {...},
    "color_performance": {...},
    "elo_progression": {...},
    "termination_wins": {...},
    "termination_losses": {...},
    "opening_performance": {...},
    "opponent_strength": {...},
    "time_of_day": {...}
  }
}
```

### Validation and error handling

* Validate username exists on Chess.com
* **Validate date range:**
  - **Maximum:** 30 days (required for performance)
  - **Minimum:** 1 day
  - Calculate: `(end_date - start_date).days <= 30`
  - Error response if exceeded:
    ```json
    {
      "error": "date_range_exceeded",
      "message": "Please select a date range of 30 days or less. For best results, use 'Last 7 days' or 'Last 30 days'.",
      "max_days": 30,
      "requested_days": 45
    }
    ```
* Validate timezone string
* Handle API rate limits gracefully
* Return meaningful error messages

---

## Milestone 3: Frontend dashboard UI foundation

**Status:** ✅ Completed  
**Completion Date:** December 6, 2025

### Page layout and structure

* Design single-page scrollable dashboard layout
* Implement responsive grid system for analytics cards
* Create reusable card component structure
* Add loading states for asynchronous data fetching
* Implement error state displays

### UI design system

* Clean, modern aesthetic inspired by referenced Dribbble designs
* Consistent color scheme:
  * Wins: Green (#27ae60)
  * Losses: Red (#e74c3c)
  * Draws: Gray (#95a5a6)
  * Neutral/Info: Blue (#3498db)
* Card-based layout with subtle shadows and rounded corners
* Generous whitespace and clear typography
* Smooth transitions and animations

### User input enhancement

* **Timezone selector dropdown:**
  - **Purpose:** Allows users to select their timezone for accurate time-based analysis
  - **Implementation:** HTML `<select>` dropdown with common timezones
  - **Options include:** 
    * Auto-detect (uses browser's timezone)
    * Major world timezones (America/New_York, America/Los_Angeles, Europe/London, Asia/Tokyo, Asia/Singapore, Asia/Jakarta, etc.)
  - **Default:** Auto-detect user's browser timezone
  - **Display format:** City name with timezone abbreviation (e.g., "Asia/Jakarta (WIB, GMT+7)")
  - **Backend parameter:** Send selected timezone string (e.g., "Asia/Jakarta") to API
  - **Impact on analysis:** 
    * Affects Time of Day Performance categorization (Section 8)
    * Ensures game timestamps are converted to user's local time
    * Example: A game played at 23:00 UTC appears as:
      - 18:00 (evening) in America/New_York (GMT-5)
      - 07:00 (morning) in Asia/Jakarta (GMT+7)
  - **UI placement:** Next to date range inputs in form
  - **Label:** "Timezone"
* **Date range selection with presets:**
  - **Preset buttons (prominent):** [Last 7 Days] [Last 30 Days]
  - Custom date picker (with validation)
  - Helper text: "Maximum 30 days for optimal performance"
  - Real-time validation: Show error if range > 30 days
  - Disable submit button until valid range selected
* **Date range validation:**
  - Frontend: Check `(end_date - start_date).days <= 30` before submission
  - Show error message below date picker if exceeded
  - Suggest using preset buttons for best results
* Show analysis metadata (total games, date range, timezone)

---

## Milestone 4: Analytics visualizations - Part 1

**Status:** ✅ Completed  
**Completion Date:** December 6, 2025

### Section 1: Overall win/loss performance over time

**Requirement ID:** EA-001

**User story:** As a chess player, I want to see my win rate trends over time so I can track my overall performance improvement.

**Implementation:**
* Line chart showing daily win rate percentage (0-100%)
* X-axis: Date (daily intervals)
* Y-axis: Win Rate %
* Single line showing win rate percentage over time
* Interactive tooltips showing: Date, Win Rate %, Wins count, Losses count, Draws count
* Clean visualization focusing on performance trend

**Acceptance criteria:**
- [x] Chart displays daily win rate percentage as line graph
- [x] Y-axis shows "Win Rate %" (0-100% scale)
- [x] Dates are shown in user's local timezone
- [x] Chart is responsive and readable on mobile devices
- [x] Tooltips show: Date, Win Rate %, Wins, Losses, Draws on hover
- [x] Empty dates (no games) are handled gracefully
- [x] Chart legend is clear and positioned appropriately

---

### Section 2: Color performance over time

**Requirement ID:** EA-002

**User story:** As a chess player, I want to see my performance as White versus Black over time so I can identify if I'm stronger with one color.

**Implementation:**
* Single line chart with TWO lines showing win rate percentage for White and Black
* X-axis: Date (daily intervals)
* Y-axis: Win Rate %
* Two lines: White win rate and Black win rate
* Two separate summary cards above chart:
  * Card 1: White summary (total games, win rate %)
  * Card 2: Black summary (total games, win rate %)
* Interactive tooltips showing: Date, Win Rate %, Wins, Losses, Draws per color
* Clear visual distinction between White and Black lines

**Acceptance criteria:**
- [x] Single chart with two lines (White and Black win rates)
- [x] Two separate summary cards displayed above chart
- [x] White summary card shows: total games and win rate %
- [x] Black summary card shows: total games and win rate %
- [x] Daily aggregation of win rate by color
- [x] Win rate percentages displayed in tooltips on hover
- [x] Visual comparison between colors is clear
- [x] Tooltips include: Date, Win Rate %, Wins, Losses, Draws per color
- [x] Data accurately distinguishes player's color in each game

---

### Section 3: Elo rating progression over time

**Requirement ID:** EA-003

**User story:** As a chess player, I want to see my Elo rating changes over the selected period so I can track my rating improvement or decline.

**Implementation:**
* Line chart showing Elo rating progression
* X-axis: Date (daily)
* Y-axis: Elo rating
* Extract rating from each game's metadata
* Plot rating after each game
* Show trend line or moving average (7-day)
* Display rating change (+/- from start to end)
* Handle multiple time controls separately if needed

**Acceptance criteria:**
- [x] Chart displays Elo rating for each game date
- [x] Rating values are extracted correctly from game data
- [x] Positive and negative rating changes are visually distinct
- [x] Summary shows net rating change for the period
- [x] Chart handles missing data points appropriately
- [x] Separate views or filters for different time controls (blitz, rapid, bullet)

---

## Milestone 5: Analytics visualizations - Part 2

**Status:** ✅ Completed  
**Completion Date:** December 6, 2025

### Section 4: Termination types - Winning games

**Requirement ID:** EA-004

**User story:** As a chess player, I want to know how I typically win games (checkmate, timeout, resignation, etc.) so I can understand my winning patterns.

**Implementation:**
* Pie/doughnut chart showing distribution of winning termination types
* Categories: Checkmate, Timeout, Resignation, Abandoned, Other
* Parse termination type from game metadata (`white.result` / `black.result`)
* Display count labels inside pie segments (e.g., "Checkmate: 25")
* Show percentages in chart legend or tooltip
* Table showing detailed breakdown with game counts

**Acceptance criteria:**
- [x] All winning games are categorized by termination type
- [x] Chart displays accurate percentages
- [x] Count labels displayed inside pie segments (e.g., "Checkmate: 25")
- [x] Only includes games where the user won (result = "win")
- [x] All possible termination types are handled
- [x] Visual representation is clear and readable
- [x] Clicking segments shows example games (optional enhancement)

---

### Section 5: Termination types - Losing games

**Requirement ID:** EA-005

**User story:** As a chess player, I want to know how I typically lose games so I can identify patterns and improve my weaknesses.

**Implementation:**
* Pie/doughnut chart showing distribution of losing termination types
* Categories: Checkmate, Timeout, Resignation, Abandoned, Other
* Parse termination type from game metadata
* Display count labels inside pie segments (e.g., "Checkmate: 20")
* Show percentages in chart legend or tooltip
* Table showing detailed breakdown with game counts

**Acceptance criteria:**
- [x] All losing games are categorized by termination type
- [x] Chart displays accurate percentages
- [x] Count labels displayed inside pie segments (e.g., "Checkmate: 20")
- [x] Only includes games where opponent won (result = "lose")
- [x] All possible termination types are handled
- [x] Visual representation is clear and readable
- [x] Comparison with winning terminations is easily visible

---

### Section 6: Chess opening performance

**Requirement ID:** EA-006

**User story:** As a chess player, I want to see my most frequently played openings and their performance so I can focus my improvement efforts on the openings I actually use.

**Implementation:**
* Parse PGN data to extract opening moves (first 5-10 moves)
* Identify opening names using chess opening database/library
* Calculate games played and win rate for each opening
* Display single table/chart:
  * **Top 10 Most Common Openings** (sorted by games played, descending)
  * Show: Opening name, Games played, Win rate %, W-L-D counts
  * If player has <10 unique openings, show all available
* Visual representation: Horizontal bar chart showing games played with win rate overlay OR table with color-coded win rates
* No minimum game threshold (show actual usage patterns)
* Focus on frequency over performance (helps identify repertoire gaps)

**Technical notes:**
* Use `python-chess` library for PGN parsing
* Use chess opening database for name identification:
  * Primary: Lichess Opening Database (comprehensive, open-source)
  * Fallback: python-chess-opening-names package
* Opening identification algorithm:
  * Parse first 5-10 moves from PGN
  * Match move sequence against opening database
  * Return human-readable opening name (e.g., "Sicilian Defense", "French Defense")
* Handle unknown openings:
  * Label as "Unknown Opening" when no match found
  * Target: <15% of games categorized as "Unknown Opening"
  * Log unidentified move sequences for future database improvements
* Sort by frequency: Count games per opening, display top 10
* Include all openings in count (no minimum threshold)

**Acceptance criteria:**
- [x] PGN data is parsed correctly for each game
- [x] Opening names extracted using Lichess Opening Database
- [x] Opening names displayed without ECO codes (human-readable names only)
- [x] Unknown openings labeled as "Unknown Opening"
- [x] Less than 15% of games categorized as "Unknown Opening"
- [x] Win rates are calculated correctly (wins / total games)
- [ ] Top 10 most common openings displayed (sorted by games played, descending)
- [ ] Display shows: Opening name, Games played, Win rate %, W-L-D counts
- [ ] If fewer than 10 unique openings, display all available
- [ ] Sorting is descending by games played (most to least common)
- [ ] Visual representation (bar chart or table) is clear
- [x] Games played count is shown for each opening
- [ ] Color-coded win rates (green >55%, neutral 45-55%, red <45%)

---

## Milestone 6: Analytics visualizations - Part 3

**Status:** ✅ Completed  
**Completion Date:** December 6, 2025

### Section 7: Opponent strength analysis

**Requirement ID:** EA-007

**User story:** As a chess player, I want to see my win rate against opponents of different strength levels so I can understand how I perform against weaker, similar, and stronger players.

**Implementation:**
* Calculate Elo differential for each game (opponent rating - player rating)
* Categorize games into three groups:
  * Lower rated: Opponent Elo < Player Elo - 100
  * Similar rated: Player Elo - 100 ≤ Opponent Elo ≤ Player Elo + 100
  * Higher rated: Opponent Elo > Player Elo + 100
* Calculate win/loss/draw counts and win rate for each category
* Display as three separate cards (grid layout) - NO bar chart
* Each card shows:
  * Category name (Lower/Similar/Higher rated)
  * Total games played
  * Win/Loss/Draw counts
  * Win rate percentage
  * Average Elo differential
* Include average Elo differential for each category

**Acceptance criteria:**
- [x] Elo differentials are calculated correctly
- [x] Games are categorized accurately into three strength groups
- [x] Win rates are calculated for each category
- [x] Three card grid layout displays data clearly (no bar chart)
- [x] Each card shows: games played, W/L/D counts, win rate %, avg Elo diff
- [x] Game counts are displayed for each category
- [x] Handles cases where player or opponent rating is missing
- [x] Summary insight: "You perform best against [category]"

---

### Section 8: Time of day performance

**Requirement ID:** EA-008

**User story:** As a chess player, I want to see when I play best during the day so I can schedule important games during my peak performance times.

**Implementation:**
* Convert all game timestamps to user's local timezone
* Categorize games by time of day:
  * Morning: 6:00 AM - 2:00 PM
  * Afternoon: 2:00 PM - 10:00 PM
  * Night: 10:00 PM - 6:00 AM
* Calculate win/loss/draw counts and win rate for each period
* Display as three separate cards (grid layout) - NO bar chart
* Each card shows:
  * Time period name (Morning/Afternoon/Night)
  * Total games played
  * Win/Loss/Draw counts
  * Win rate percentage
* Show games played distribution across time periods

**Technical notes:**
* Use JavaScript `Intl` API for timezone detection
* Server should accept timezone parameter and convert timestamps
* Consider daylight saving time changes

**Acceptance criteria:**
- [ ] Game timestamps are converted to user's timezone (CRITICAL: verify implementation)
- [ ] Backend receives timezone parameter from frontend
- [ ] All game timestamps converted from UTC to user timezone before categorization
- [ ] Time period categorization uses converted local time (not UTC)
- [ ] Games are categorized correctly into time periods based on LOCAL time
- [x] Win rates are calculated for each time period
- [x] Three card grid layout displays data clearly (no bar chart)
- [x] Each card shows: games played, W/L/D counts, win rate %
- [x] Game distribution (how many games in each period) is visible
- [x] User can see their best and worst performing times
- [ ] Timezone is displayed clearly to user in Section 8 header
- [x] Handles edge cases (games exactly at boundary times)
- [ ] Manual verification: test with different timezones (EST, PST, GMT+8) to confirm correct categorization

---

## Milestone 7: UI Enhancement and Visualization Updates

**Status:** ✅ Completed  
**Completion Date:** December 6, 2025

### Overview
This milestone focuses on refining and enhancing the user interface and data visualizations based on user feedback and usability testing. The goal is to create a cleaner, more intuitive dashboard that presents data in the most actionable format.

### Section 1: Enhanced Overall Performance Visualization

**Requirement ID:** EA-013

**User story:** As a chess player, I want to see my win rate trend clearly without clutter, so I can quickly assess my performance trajectory.

**Changes from original implementation:**
* Replace three-line chart (wins/losses/draws) with single win rate percentage line
* Move detailed counts to hover tooltips only
* Focus visualization on performance trend rather than raw numbers

**Implementation:**
* Update Chart.js configuration to show single line (win rate %)
* Y-axis range: 0-100% (win rate percentage)
* X-axis: Dates in user's local timezone
* Tooltip displays: Date, Win Rate %, Wins, Losses, Draws
* Remove win/loss/draw lines from main chart
* Maintain responsive design

**Acceptance criteria:**
- [ ] Single line chart displays win rate percentage over time
- [ ] Y-axis labeled "Win Rate %" with 0-100% scale
- [ ] Hover tooltip shows: Date, Win Rate %, Wins, Losses, Draws
- [ ] Chart is cleaner and easier to read at a glance
- [ ] Mobile responsive design maintained
- [ ] Performance is smooth with large datasets

---

### Section 2: Unified Color Performance Chart

**Requirement ID:** EA-014

**User story:** As a chess player, I want to compare my White and Black performance directly on one chart, with clear summary statistics for each color.

**Changes from original implementation:**
* Combine White and Black charts into single chart with two lines
* Add two separate summary cards above chart
* Show win rate trends for both colors simultaneously
* **Display complete W/L/D statistics in summary cards** (Iteration 5)

**Implementation:**
* Single Chart.js line chart with two datasets:
  * Line 1: White win rate % (color: white/light gray)
  * Line 2: Black win rate % (color: dark gray/black)
* Two summary cards displayed above chart:
  * White Summary Card: Total games, **Wins, Losses, Draws**, Win rate %
  * Black Summary Card: Total games, **Wins, Losses, Draws**, Win rate %
* Tooltips show per-color details: Date, Win Rate %, Wins, Losses, Draws
* Legend clearly distinguishes White vs Black lines

**Example summary card display:**
```
♔ PLAYING AS WHITE
Total games: 42
Wins: 24
Losses: 15
Draws: 3
Win Rate: 57.1%
```

**Acceptance criteria:**
- [ ] Single chart displays two lines (White and Black win rates)
- [ ] Two separate summary cards positioned above chart
- [ ] White summary card shows: total games played as White, **wins, losses, draws**, win rate %
- [ ] Black summary card shows: total games played as Black, **wins, losses, draws**, win rate %
- [ ] Chart legend clearly labels White and Black lines
- [ ] Tooltips show color-specific data on hover
- [ ] Visual distinction between White and Black lines is clear
- [ ] Responsive design for mobile devices
- [ ] W/L/D counts are clearly displayed and accurate

---

### Section 4 & 5: Enhanced Termination Type Visualization

**Requirement ID:** EA-015

**User story:** As a chess player, I want to see immediately how many games I won/lost by each termination type without needing to hover.

**Changes from original implementation:**
* Display count labels directly inside pie chart segments
* Reduce need for tooltip interaction
* Improve at-a-glance readability
* **Simplified to numbers only, no legend** (Iteration 5)

**Implementation:**
* Chart.js datalabels plugin configuration
* Show **numbers only** inside each segment (e.g., "25" not "Checkmate: 25")
* **Legend hidden completely** (cleaner, minimalist design)
* Full details available in hover tooltip: Category name, Count, Percentage
* Ensure text is readable on all segment sizes
* Apply to both winning (Section 4) and losing (Section 5) charts

**Chart.js configuration:**
```javascript
{
    plugins: {
        legend: {
            display: false  // Hide legend (Iteration 5)
        },
        datalabels: {
            formatter: (value) => value,  // Show only number
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

**Acceptance criteria:**
- [ ] **Numbers only** displayed inside pie segments (e.g., "25" not category labels)
- [ ] Labels are readable on all segment sizes
- [ ] **Legend is hidden** (not displayed)
- [ ] Hover tooltip shows: Category name, Count, Percentage
- [ ] Both winning and losing charts use same label format
- [ ] Labels don't overlap or obscure chart
- [ ] Responsive design maintains label readability
- [ ] Chart remains clear and intuitive without legend

---

### Section 6: Opening Performance Analysis with Enhanced Visualization (Updated v2.5)

**Requirement ID:** EA-016

**User story:** As a chess player, I want to see my most common openings with detailed move sequences and interactive links, so I can understand and improve my opening repertoire.

**Changes from original implementation:**
* Display human-readable opening names only (no ECO codes)
* Integrate with comprehensive opening database
* Minimize "Unknown Opening" classifications
* **Show first 6 full moves in standard notation** (Iteration 5)
* **Provide Lichess board editor URL for position visualization** (Iteration 5)
* **Include Chess.com example game URL** (Iteration 5)
* **Separate White and Black openings** (Iteration 5)
* **Limit to Top 5 per color** (Iteration 6 / v2.5)

**Implementation:**

**Opening identification:**
* Integrate Lichess Opening Database
  * Database URL: https://github.com/lichess-org/chess-openings
  * Contains 3000+ opening variations with names
  * Regularly updated and maintained
* Parsing algorithm:
  1. Extract first 5-10 moves from PGN
  2. Convert to UCI notation
  3. Match against Lichess opening database
  4. Return full opening name (e.g., "Sicilian Defense: Najdorf Variation")
  5. If no match, label as "Unknown Opening"
* Quality threshold: <15% of games as "Unknown Opening"
* Fallback options if match confidence is low:
  * Try shorter move sequences (5 moves, 4 moves, 3 moves)
  * Match to parent opening family
* Never show ECO codes in UI

**Move sequence and URL generation:**
* Extract first 6 full moves (12 individual moves) from PGN
* Display in standard chess notation: "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5"
* Generate FEN position after 6 moves
* Create Lichess URL: `https://lichess.org/editor/{urllib.parse.quote(fen)}`
* Store Chess.com game URL as example game

**Display structure:**
* Separate sections for "Top 5 Most Common Openings (As White)" and "Top 5 Most Common Openings (As Black)"
* Each opening shows:
  - Opening name
  - Games played, Win rate %, W-L-D breakdown
  - First 6 moves in standard notation
  - "📊 View Position on Lichess" (clickable link)
  - "♟️ Example Game on Chess.com" (clickable link)
* Sort by games played (descending) within each color

**Technical implementation:**
```python
import urllib.parse
from chess_openings import get_opening_name
import chess.pgn

def _analyze_opening_performance(self, games: List[Dict]) -> Dict:
    """Analyze openings with first 6 moves and URLs."""
    white_stats = defaultdict(lambda: {
        'games': 0, 'wins': 0, 'losses': 0, 'draws': 0,
        'sample_pgn': None, 'example_game_url': None
    })
    black_stats = defaultdict(lambda: {
        'games': 0, 'wins': 0, 'losses': 0, 'draws': 0,
        'sample_pgn': None, 'example_game_url': None
    })
    
    for game in games:
        opening = game['opening_name']
        color = game['player_color']
        stats = white_stats if color == 'white' else black_stats
        
        stats[opening]['games'] += 1
        # Track W/L/D...
        
        # Store sample PGN and game URL for first occurrence
        if stats[opening]['sample_pgn'] is None:
            stats[opening]['sample_pgn'] = game['pgn']
            stats[opening]['example_game_url'] = game['url']
    
    def process_color_openings(opening_stats):
        results = []
        for opening, stats in opening_stats.items():
            # Extract first 6 moves
            first_moves = self._extract_first_six_moves(stats['sample_pgn'])
            
            # Get FEN after 6 moves
            fen = self._get_opening_position_fen(stats['sample_pgn'])
            
            # Generate Lichess URL
            lichess_url = f"https://lichess.org/editor/{urllib.parse.quote(fen)}"
            
            results.append({
                'opening': opening,
                'games': stats['games'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'draws': stats['draws'],
                'win_rate': round(stats['wins'] / stats['games'] * 100, 2),
                'first_moves': first_moves,
                'lichess_url': lichess_url,
                'example_game_url': stats['example_game_url']
            })
        
        # Sort by games played (descending)
        results.sort(key=lambda x: x['games'], reverse=True)
        return results[:5]  # Top 5 (v2.5)
    
    return {
        'white': process_color_openings(white_stats),
        'black': process_color_openings(black_stats)
    }
```

**Frontend display example:**
```html
<div class="opening-section">
    <h3>♔ TOP 5 MOST COMMON OPENINGS (AS WHITE)</h3>
    
    <div class="opening-card">
        <h4>1. Sicilian Defense: Alapin Variation</h4>
        <p>Games: 12 | Win Rate: 58.3% (7W-4L-1D)</p>
        <p class="moves">1. e4 c5 2. c3 Nf6 3. e5 Nd5 4. d4 cxd4 5. cxd4 d6</p>
        <div class="opening-links">
            <a href="https://lichess.org/editor/..." target="_blank">
                📊 View Position on Lichess
            </a>
            <a href="https://www.chess.com/game/live/..." target="_blank">
                ♟️ Example Game
            </a>
        </div>
    </div>
</div>

<div class="opening-section">
    <h3>♚ TOP 5 MOST COMMON OPENINGS (AS BLACK)</h3>
    <!-- Similar structure -->
</div>
```

**Acceptance criteria:**
- [x] Lichess Opening Database integrated into backend (pattern-based identification)
- [x] Opening names displayed without ECO codes
- [x] Less than 15% of games categorized as "Unknown Opening"
- [x] Opening names are human-readable (e.g., "Sicilian Defense")
- [x] Fallback algorithm tries shorter move sequences
- [ ] **First 6 full moves (12 individual moves) displayed for each opening**
- [ ] **Moves shown in standard notation** (e.g., "1. e4 e5 2. Nf3 Nc6...")
- [ ] **Lichess board editor URL generated and clickable** for each opening
- [ ] **Chess.com example game URL provided** for each opening
- [ ] **Openings displayed separately: White and Black sections**
- [x] **Top 5 openings per color** (or fewer if player has <5 unique openings) **(Updated v2.5)**
- [x] Sorted by games played (descending) within each color
- [ ] Win rate and W-L-D counts displayed for each opening
- [ ] URLs open in new tab
- [ ] Links are clearly labeled and functional
- [x] Unknown openings clearly labeled as "Unknown Opening"
- [x] Database updates don't break existing functionality

---

### Section 7 & 8: Simplified Card-Based Display

**Requirement ID:** EA-017

**User story:** As a chess player, I want to see my opponent strength and time-of-day statistics in a simple, easy-to-scan format without unnecessary charts.

**Changes from original implementation:**
* Remove bar charts from Sections 7 and 8
* Display data in clean card grid format only
* Reduce visual complexity while maintaining information density

**Implementation:**

**Section 7: Opponent Strength Analysis**
* Three cards in horizontal grid layout:
  * Card 1: Lower Rated Opponents
  * Card 2: Similar Rated Opponents  
  * Card 3: Higher Rated Opponents
* Each card displays:
  * Category title with icon
  * Total games played
  * Win/Loss/Draw counts
  * Win rate percentage (large, prominent)
  * Average Elo differential
* Remove `opponentStrengthChart` entirely
* Keep grid responsive (stacks on mobile)

**Section 8: Time of Day Performance**
* Three cards in horizontal grid layout:
  * Card 1: Morning (6am-2pm)
  * Card 2: Afternoon (2pm-10pm)
  * Card 3: Night (10pm-6am)
* Each card displays:
  * Time period title with icon
  * Total games played
  * Win/Loss/Draw counts
  * Win rate percentage (large, prominent)
* Remove `timeOfDayChart` entirely
* Keep grid responsive (stacks on mobile)

**Card design specifications:**
* Consistent styling with existing UI design system
* Card padding: 20px
* Win rate displayed prominently (32px font size)
* Color coding: Green for high win rates (>55%), neutral for medium (45-55%), red for low (<45%)
* Subtle hover effects
* Box shadow: 0 2px 8px rgba(0,0,0,0.1)

**Acceptance criteria:**
- [ ] Section 7 displays three cards (no bar chart)
- [ ] Section 8 displays three cards (no bar chart)
- [ ] Each card shows: title, games played, W/L/D counts, win rate %
- [ ] Section 7 cards also show average Elo differential
- [ ] Cards use consistent design system
- [ ] Grid layout is responsive (horizontal on desktop, stacked on mobile)
- [ ] Win rate percentages are prominently displayed
- [ ] Color coding helps identify strong/weak performance areas
- [ ] No references to removed bar charts in code or UI
- [ ] Performance is smooth with all card interactions

---

### Testing for Milestone 7

**Updated E2E test cases:**

**TC-015: Enhanced overall performance chart**
* Complete analysis workflow
* Verify Section 1 shows single win rate line
* Verify Y-axis shows "Win Rate %"
* Hover over data point, verify tooltip shows: Date, Win Rate %, Wins, Losses, Draws
* Verify chart is cleaner and easier to read

**TC-016: Unified color performance chart with W/L/D counts**
* Complete analysis workflow
* Verify Section 2 shows single chart with two lines
* Verify two summary cards displayed above chart
* **Verify White summary card shows: total games, wins, losses, draws, win rate**
* **Verify Black summary card shows: total games, wins, losses, draws, win rate**
* **Verify W/L/D counts are accurate** (e.g., "42 games: 24W-15L-3D")
* Hover over lines, verify color-specific tooltips
* Verify all statistics display correctly on mobile

**TC-017: Simplified pie chart display**
* Complete analysis workflow
* **Verify Section 4 pie chart shows numbers only inside segments** (e.g., "32" not "Checkmate: 32")
* **Verify Section 5 pie chart shows numbers only inside segments**
* **Verify legend is hidden** (not displayed for both charts)
* Verify labels are readable on all segment sizes
* **Hover over segment, verify tooltip shows: Category name, Count, Percentage** (e.g., "Checkmate: 32 games (45%)")
* Verify chart is clean and intuitive without legend

**TC-018: Opening performance with moves and URLs**
* Complete analysis workflow
* **Verify Section 6 has two separate sections: "Top 10 Most Common Openings (As White)" and "Top 10 Most Common Openings (As Black)"**
* **Verify each section displays up to 10 openings** (or fewer if player has <10)
* Verify openings sorted by games played (descending order) within each color
* Verify most-played opening appears first in each section
* Verify each opening shows: Name, Games played, Win rate %, W-L-D counts
* **Verify first 6 full moves displayed** in standard notation (e.g., "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6...")
* **Verify Lichess board editor URL present and clickable** for each opening
* **Verify Chess.com example game URL present and clickable** for each opening
* **Click Lichess link, verify it opens Lichess board editor with correct position** (new tab)
* **Click Chess.com link, verify it opens game on Chess.com** (new tab)
* Verify human-readable opening names (no ECO codes)
* Verify "Unknown Opening" count is less than 15% of total games
* Verify White and Black sections are visually distinct

**TC-019: Simplified opponent strength display**
* Complete analysis workflow
* Verify Section 7 shows three cards (no bar chart)
* Verify each card shows: title, games, W/L/D, win rate %, avg Elo diff
* Verify cards are responsive on mobile
* Verify no bar chart elements present in DOM

**TC-020: Simplified time of day display**
* Complete analysis workflow
* Verify Section 8 shows three cards (no bar chart)
* Verify each card shows: time period, games, W/L/D, win rate %
* Verify cards are responsive on mobile
* Verify no bar chart elements present in DOM

---

## Milestone 8: Game stage mistake analysis

**Status:** 🔄 In Progress  
**Start Date:** December 12, 2025

### Overview

This milestone introduces comprehensive mistake analysis across different game stages (early, middle, endgame) using chess engine evaluation. The system will analyze each move using Stockfish engine to identify mistakes, blunders, and inaccuracies, categorize them by game stage, and present insights to help players understand where they struggle most.

### Section 9: Move analysis by game stage (Updated v2.5)

**Requirement ID:** EA-018

**User story:** As a chess player, I want to understand the quality of my moves in different game stages so I can recognize both my strengths (brilliant moves) and weaknesses (mistakes) and focus my training accordingly.

**Game stage definitions (using strategic sampling - v2.3):**
* **Early game:** First 10 player moves (opening phase)
* **Middle game:** 10 consecutive sampled moves from middle of game (tactical phase)
* **Late game:** Last 10 player moves (endgame/conversion phase)

**Move quality classification (v2.5 - Simplified):**
* **Brilliant moves:** Evaluation gain of ≥100 centipawns (+100 CP or more)
  - Significantly improves position
  - Finds tactical shots, winning attacks, or strong defenses
* **Neutral moves:** Evaluation change between -49 and +99 centipawns
  - Neither gains nor loses significantly
  - Standard continuation, maintains position
* **Mistake moves:** Evaluation loss of ≥50 centipawns (-50 CP or worse)
  - Combines old categories (inaccuracies/mistakes/blunders)
  - Significantly worsens position
  - Simplified classification for clearer insights

**Rationale for simplified classification:**
- Focus on actionable insights: "Am I making good moves or bad moves?"
- Positive framing: Track brilliant moves (strengths) alongside mistakes (weaknesses)
- Reduces cognitive load: 3 categories instead of 5
- Game-level metrics: "Average 2.3 brilliant moves per game in early stage"

**Implementation:**

**Backend analysis engine:**
* Integrate Stockfish chess engine (python-chess library includes Stockfish interface)
* For each game in dataset:
  1. Parse PGN and replay game move-by-move
  2. Run Stockfish evaluation after each move (depth 15-18 for balance of speed/accuracy)
  3. Calculate evaluation difference between moves
  4. Classify mistakes based on centipawn thresholds
  5. Categorize each mistake by game stage (move number)
  6. Detect missed opportunities: opponent mistake followed by suboptimal player response
* Aggregate statistics:
  - Total mistakes/blunders/inaccuracies per stage
  - Average centipawn loss per stage
  - Most critical mistakes (biggest evaluation drops)
  - Games with most mistakes per stage
  - Missed opportunity count per stage

**Performance optimization:**
* **Date range restriction:** Maximum 30 days to ensure fast analysis (<1 minute target)
* Cache engine analysis results per game (store in database/Redis with game URL as key)
* Use **dynamic sampling strategy based on dataset size** (Iteration 5):
  - **If total games < 50:** Analyze ALL games (comprehensive analysis)
  - **If total games ≥ 50:** Use 20% sampling strategy:
    * Sample size: 20% of total (with stratification)
    * Minimum: 10 games
    * Maximum: 50 games
    * Stratification: Even distribution across time period and outcomes (W/L/D)
  - **Examples:**
    * 10 games total → Analyze 10 games (100%)
    * 30 games total → Analyze 30 games (100%)
    * 49 games total → Analyze 49 games (100%)
    * 50 games total → Analyze 50 games (20%, minimum)
    * 100 games total → Analyze 20 games (20%)
    * 300 games total → Analyze 50 games (16.7%, maximum)
  - **Rationale:**
    * Small datasets need full analysis for statistical confidence
    * Large datasets use sampling for performance
    * With 30-day limit, typical users have 20-50 games (full or near-full analysis)
    * Better accuracy for users with moderate activity
* **Progressive improvement:** Cache persists across analyses
  - First analysis: Sample selected based on logic above
  - Second analysis (new date range): Only new games analyzed
  - Over time: Coverage increases without redundant analysis
* **Optimized Stockfish settings (PRD v2.3 - February 18, 2026):**
  - **Analysis depth: 10** (balanced for accuracy on sampled moves)
  - **Time limit: 0.5 seconds per position**
  - Only analyze player moves (skip opponent moves)
  - **Early stop threshold: 300 CP** (stops obvious blunders sooner)
  - **Skip evaluation threshold: 600 CP** (skip heavily winning/losing positions)
  - **Strategic Move Sampling (NEW - February 18, 2026):**
    * **First 10 moves:** Always analyze (opening phase - critical for pattern learning)
    * **Middle game:** Sample 10 moves evenly distributed (tactical phase - representative sampling)
    * **Last 10 moves:** Always analyze (endgame phase - critical conversion/defense)
    * **Maximum:** 30 moves analyzed per game (regardless of game length)
    * **Rationale:**
      - Opening (moves 1-10): Most learning happens here, beginners make critical mistakes
      - Endgame (last 10): Winning/losing phase, technique evaluation critical
      - Middle game: Sample 10 moves evenly (every Nth move for representativeness)
      - Games <30 moves: Analyze all moves
      - Average game ~40 moves: Analyze 30/40 = 75% coverage at critical phases
  - **Performance gain:** ~3-4x faster than full analysis (per game: 5-7s → 2-3s)
  - **Accuracy:** ~90% retained (all critical phases covered, middle game represented)
  - **Example coverage:**
    * 20-move game: Analyze all 20 moves (100%)
    * 40-move game: Analyze first 10 + middle 10 + last 10 = 30 moves (75%)
    * 60-move game: Analyze first 10 + middle 10 (sampled) + last 10 = 30 moves (50%)
    * 80-move game: Analyze first 10 + middle 10 (sampled) + last 10 = 30 moves (37.5%)
* **User communication:**
  - If <50 games: "Comprehensive analysis of X games"
  - If ≥50 games: "Analysis based on X games (Y% sample)"
  - Tooltip remains consistent: "Results are cached and improve over time"
* **Statistical justification:**
  - <50 games: Full analysis provides maximum confidence
  - ≥50 games: 20% stratified sample provides ~90% accuracy for pattern detection
  - Focus: Identify which stages have issues (pattern identification)
  - Chess mistake patterns are consistent across games (validated in research)

**Sampling algorithm pseudocode:**
```python
def select_games_for_analysis(all_games, cache, date_range_days):
    """
    Select games for engine analysis based on dynamic sampling logic.
    
    Logic (Iteration 5):
    - If total games < 50: Analyze ALL uncached games
    - If total games >= 50: Use 20% sampling (min 10, max 50)
    """
    # Validate date range first
    if date_range_days > 30:
        raise ValueError("Date range must be 30 days or less")
    
    # Remove already-analyzed games
    uncached_games = [g for g in all_games if g['url'] not in cache]
    total_games = len(all_games)
    
    # Dynamic sampling based on dataset size
    if total_games < 50:
        # Analyze all uncached games for comprehensive results
        games_to_analyze = uncached_games
        analysis_note = f"Comprehensive analysis of {len(uncached_games)} games"
    else:
        # Use 20% sampling with min/max bounds
        sample_size = max(10, min(50, int(len(uncached_games) * 0.20)))
        
        if sample_size == 0:
            # All games cached
            return [], "Analysis complete (all games cached)"
        
        # Stratified sampling: distribute across time period
        sorted_games = sorted(uncached_games, key=lambda g: g['date'])
        
        # Select evenly distributed games
        step = len(sorted_games) / sample_size
        selected = [sorted_games[int(i * step)] for i in range(sample_size)]
        
        games_to_analyze = selected
        percentage = (sample_size / total_games * 100)
        analysis_note = f"Analysis based on {sample_size} games ({percentage:.1f}% sample)"
    
    return games_to_analyze, analysis_note
```

**Frontend visualization (v2.6):**

**Table display:**

**Moves analysis** - Average number of Mistake/Neutral/Brilliant moves per game

| | Mistake | Neutral | Brilliant |
|------------|---------|---------|-----------|
| early game (1-10 moves) | 1.8 | 5.1 | 2.3 |
| middle games (sample 10 consecutive moves) | 2.4 | 4.2 | 3.1 |
| late game (last 10 moves) | 3.1 | 4.9 | 1.8 |

**Table details:**
* **Mistake:** Average count of mistake moves (≤-50 CP loss) per game in this stage
* **Neutral:** Average count of neutral moves (-49 to +99 CP) per game in this stage
* **Brilliant:** Average count of brilliant moves (≥+100 CP gain) per game in this stage

**Visual summary cards:**
* **Weakest Stage:** "late game" (stage with highest avg mistakes per game)
* **Total Mistakes:** "93" (sum of all mistakes across all stages and games)

**Sample info text:**
* "📊 Analyzed 16 games out of 84 total games (19%). Found 93 significant mistakes (50+ centipawns loss)."
* "⚙️ Powered by Stockfish engine analysis. Move quality: Brilliant (≥+100cp gain), Neutral (-49 to +99cp), Mistake (≥-50cp loss)"

**Technical implementation:**

```python
import chess
import chess.engine
import chess.pgn
from io import StringIO

def analyze_game_mistakes(pgn_string, stockfish_path="/usr/games/stockfish"):
    """
    Analyze a single game for mistakes across all stages.
    
    Returns dict with mistake analysis per stage.
    """
    game = chess.pgn.read_game(StringIO(pgn_string))
    board = game.board()
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    
    mistakes = {
        "early": {"inaccuracies": 0, "mistakes": 0, "blunders": 0, "missed_opps": 0, "cp_loss": []},
        "middle": {"inaccuracies": 0, "mistakes": 0, "blunders": 0, "missed_opps": 0, "cp_loss": []},
        "endgame": {"inaccuracies": 0, "mistakes": 0, "blunders": 0, "missed_opps": 0, "cp_loss": []}
    }
    
    prev_eval = None
    move_number = 0
    player_color = chess.WHITE  # Adjust based on player's color
    
    for move in game.mainline_moves():
        move_number += 1
        
        # Determine game stage
        if move_number <= 14:  # 7 full moves
            stage = "early"
        elif move_number <= 40:  # Up to move 20
            stage = "middle"
        else:
            stage = "endgame"
        
        # Only analyze player's moves
        if board.turn == player_color:
            # Get evaluation before move
            info = engine.analyse(board, chess.engine.Limit(depth=15))
            current_eval = info["score"].relative.score(mate_score=10000)
            
            # Make the move
            board.push(move)
            
            # Get evaluation after move
            info = engine.analyse(board, chess.engine.Limit(depth=15))
            new_eval = info["score"].relative.score(mate_score=10000)
            
            # Calculate centipawn loss (from player's perspective)
            if prev_eval is not None and current_eval is not None and new_eval is not None:
                cp_loss = current_eval - new_eval
                
                # Classify mistake
                if cp_loss >= 200:
                    mistakes[stage]["blunders"] += 1
                    mistakes[stage]["cp_loss"].append(cp_loss)
                elif cp_loss >= 100:
                    mistakes[stage]["mistakes"] += 1
                    mistakes[stage]["cp_loss"].append(cp_loss)
                elif cp_loss >= 50:
                    mistakes[stage]["inaccuracies"] += 1
                    mistakes[stage]["cp_loss"].append(cp_loss)
            
            prev_eval = new_eval
        else:
            # Opponent's move - check for missed opportunities
            board.push(move)
    
    engine.quit()
    return mistakes

def aggregate_mistake_analysis(games_data):
    """
    Aggregate mistake analysis across all games.
    """
    aggregated = {
        "early": {"total_moves": 0, "inaccuracies": 0, "mistakes": 0, "blunders": 0, 
                  "missed_opps": 0, "cp_losses": [], "worst_game": None},
        "middle": {"total_moves": 0, "inaccuracies": 0, "mistakes": 0, "blunders": 0,
                   "missed_opps": 0, "cp_losses": [], "worst_game": None},
        "endgame": {"total_moves": 0, "inaccuracies": 0, "mistakes": 0, "blunders": 0,
                    "missed_opps": 0, "cp_losses": [], "worst_game": None}
    }
    
    for game_data in games_data:
        game_mistakes = analyze_game_mistakes(game_data["pgn"])
        
        for stage in ["early", "middle", "endgame"]:
            aggregated[stage]["inaccuracies"] += game_mistakes[stage]["inaccuracies"]
            aggregated[stage]["mistakes"] += game_mistakes[stage]["mistakes"]
            aggregated[stage]["blunders"] += game_mistakes[stage]["blunders"]
            aggregated[stage]["cp_losses"].extend(game_mistakes[stage]["cp_loss"])
    
    # Calculate averages
    for stage in ["early", "middle", "endgame"]:
        cp_losses = aggregated[stage]["cp_losses"]
        aggregated[stage]["avg_cp_loss"] = sum(cp_losses) / len(cp_losses) if cp_losses else 0
    
    return aggregated
```

**API endpoint update:**
* Extend `/api/analyze/detailed` response to include `mistake_analysis` section
* Add query parameter `include_engine_analysis=true` (default: true)
* Show loading progress for engine analysis

**Acceptance criteria:**
- [ ] Date range validation: Maximum 30 days enforced (frontend + backend)
- [ ] Error message shown if user attempts >30 day range
- [ ] Preset buttons "Last 7 Days" and "Last 30 Days" prominent in UI
- [ ] Stockfish engine integrated and working
- [ ] **Dynamic sampling logic implemented:**
  * If total games < 50: Analyze ALL uncached games
  * If total games ≥ 50: Use 20% sampling (min 10, max 50)
- [ ] **Display shows appropriate message:**
  * <50 games: "Comprehensive analysis of X games"
  * ≥50 games: "Analysis based on X games (Y% sample)"
- [ ] Stratified sampling maintains time distribution for ≥50 game datasets
- [ ] Sample games analyzed for mistakes across three stages
- [ ] Mistakes correctly classified (inaccuracy/mistake/blunder)
- [ ] Game stages correctly categorized (early/middle/endgame)
- [x] **Move quality classification implemented (v2.5):**
  * Brilliant moves: ≥+100 CP evaluation gain tracked
  * Neutral moves: -49 to +99 CP evaluation change tracked
  * Mistake moves: ≤-50 CP evaluation loss tracked
- [x] **Table displays per-game average metrics (v2.5):**
  * Avg Brilliant/Game column showing average count per game
  * Avg Neutral/Game column showing average count per game
  * Avg Mistakes/Game column showing average count per game
  * Total Games Analyzed column showing sample size
- [x] **Game stage labels updated (v2.5):**
  * "Early (First 10)" for opening phase
  * "Middle (Sampled 10)" for middle game phase
  * "Late (Last 10)" for endgame phase
- [x] Centipawn loss calculated accurately
- [ ] Missed opportunities detected (opponent mistake + player's response)
- [ ] Table displays all required columns with accurate data
- [ ] Critical mistake game links meet ALL criteria:
  * Player lost by resignation (filtered out timeouts/abandonment)
  * Biggest CP drop in stage (threshold determined from data analysis)
  * Link opens Chess.com game at mistake position
- [ ] Algorithm determines "significant" CP drop threshold from data distribution
- [ ] If no qualifying game found for a stage, display "No qualifying game" instead of link
- [ ] Average CP loss calculated per stage
- [ ] Visual summary identifies weakest stage
- [ ] Engine analysis cached permanently (keyed by game URL)
- [ ] Cache persists across multiple analyses (progressive improvement)
- [ ] Loading indicator shows analysis progress ("Analyzing game X of Y")

**Asynchronous Analysis (PRD v2.4 - February 19, 2026):**

To improve user experience, mistake analysis now runs **asynchronously in the background** while users can view all other analytics sections immediately.

**Motivation:**
* Even with optimizations, Stockfish analysis takes 2-3 seconds per game
* For 10-20 games, this means 20-60 seconds of waiting before seeing ANY results
* Users should be able to view basic statistics immediately while engine analysis completes

**Implementation approach:**

**1. Immediate Response (Fast sections returned first):**
```json
{
  "sections": {
    "overall_performance": {...},
    "color_performance": {...},
    "elo_progression": {...},
    "termination_wins": {...},
    "termination_losses": {...},
    "opening_performance": {...},
    "opponent_strength": {...},
    "time_of_day": {...},
    "mistake_analysis": {
      "status": "processing",
      "task_id": "abc123-def456-789",
      "estimated_time": "30-60 seconds",
      "message": "Analyzing X games for mistakes..."
    }
  }
}
```

**2. Background Processing:**
* Flask spawns background thread for Stockfish analysis
* Thread ID stored in task storage (in-memory dict with TTL)
* Analysis runs independently without blocking response

**3. Status Polling Endpoint:**
```http
GET /api/analyze/mistake-status/<task_id>

Response (processing):
{
  "status": "processing",
  "progress": {
    "current": 5,
    "total": 10,
    "percentage": 50
  },
  "estimated_remaining": "15 seconds"
}

Response (completed):
{
  "status": "completed",
  "data": {
    "by_stage": {
      "early": {...},
      "middle": {...},
      "endgame": {...}
    },
    "weakest_stage": "middle",
    "total_games_analyzed": 10,
    "sample_percentage": 100
  }
}

Response (error):
{
  "status": "error",
  "error": "Stockfish engine not found"
}
```

**4. Frontend Polling Logic:**
* When initial response received, check if `mistake_analysis.status === "processing"`
* Show loading spinner in mistake analysis card
* Poll status endpoint every 2 seconds
* Update UI when `status === "completed"`
* Show error message if `status === "error"`

**Technical implementation:**

```python
# app/routes/api.py - Background thread handler
import threading
import uuid
from datetime import datetime, timedelta

# Task storage (in-memory with TTL)
_background_tasks = {}
_task_results = {}
_task_cleanup_ttl = 3600  # 1 hour

def cleanup_old_tasks():
    """Remove completed tasks older than TTL"""
    current_time = datetime.now()
    for task_id in list(_task_results.keys()):
        task = _task_results[task_id]
        if (current_time - task['completed_at']).total_seconds() > _task_cleanup_ttl:
            del _task_results[task_id]

def run_mistake_analysis_background(task_id, games, username, analytics_service):
    """Run Stockfish analysis in background thread"""
    try:
        _background_tasks[task_id] = {
            'status': 'processing',
            'progress': {'current': 0, 'total': len(games)}
        }
        
        # Run analysis
        result = analytics_service.mistake_analyzer.aggregate_mistake_analysis(
            games, username
        )
        
        # Store result
        _task_results[task_id] = {
            'status': 'completed',
            'data': result,
            'completed_at': datetime.now()
        }
        
        # Remove from active tasks
        del _background_tasks[task_id]
        
    except Exception as e:
        _task_results[task_id] = {
            'status': 'error',
            'error': str(e),
            'completed_at': datetime.now()
        }
        if task_id in _background_tasks:
            del _background_tasks[task_id]

# In analyze_detailed endpoint:
if include_mistake_analysis:
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Start background thread
    thread = threading.Thread(
        target=run_mistake_analysis_background,
        args=(task_id, games, username, analytics_service)
    )
    thread.daemon = True
    thread.start()
    
    # Return immediate response with task ID
    sections['mistake_analysis'] = {
        'status': 'processing',
        'task_id': task_id,
        'estimated_time': f"{len(games) * 2}-{len(games) * 3} seconds"
    }
```

**Benefits:**
* **Page load time:** 30-60s → 5-10s (instant for non-engine sections)
* **Better UX:** Users can browse statistics while analysis runs
* **Progressive enhancement:** Basic stats first, detailed analysis follows
* **No external dependencies:** Uses Python threading (built-in)
* **Scalable:** Can upgrade to Celery/Redis later if needed

**Acceptance criteria:**
- [ ] Initial API response returns within 5-10 seconds (non-engine sections only)
- [ ] `mistake_analysis` section includes `status: "processing"` and `task_id`
- [ ] Background thread spawned successfully for Stockfish analysis
- [ ] Status endpoint `/api/analyze/mistake-status/<task_id>` returns correct status
- [ ] Frontend polls status endpoint every 2 seconds
- [ ] Loading spinner shown in mistake analysis card during processing
- [ ] Results automatically populate when analysis completes
- [ ] Error message shown if analysis fails
- [ ] Task cleanup removes old results after 1 hour TTL
- [ ] Multiple simultaneous analyses supported (different task IDs)
- [ ] Handles games without engine analysis gracefully
- [ ] Works for games from player's perspective (both White and Black)
- [ ] User can run multiple short-period analyses to see patterns over time

---

## Milestone 9: AI-powered chess advisor

**Status:** 🔄 In Progress  
**Start Date:** December 12, 2025

### Overview

This milestone integrates OpenAI's GPT-4 API to provide personalized, actionable coaching advice based on comprehensive analysis of all dashboard sections. The AI advisor synthesizes data from performance trends, opening repertoire, mistake patterns, time-of-day performance, and more to deliver targeted recommendations for improvement.

### Section 10: AI chess advisor recommendations

**Requirement ID:** EA-019

**User story:** As a chess player, I want to receive personalized coaching advice based on my complete performance analysis so I can focus my training on the most impactful areas for improvement.

**Implementation:**

**Data preparation:**
* Aggregate summary statistics from all sections (1-9)
* Do NOT send raw PGN data (too large, privacy concern)
* Send only processed metrics and insights

**Summary data structure:**
```json
{
  "username": "jay_fh",
  "date_range": "Jan 1 - Mar 31, 2025",
  "total_games": 150,
  "overall_stats": {
    "win_rate": 52.3,
    "rating_change": +25,
    "rating_trend": "improving"
  },
  "color_performance": {
    "white_win_rate": 54.2,
    "black_win_rate": 50.1,
    "stronger_color": "white"
  },
  "termination_patterns": {
    "most_common_win_method": "checkmate",
    "most_common_loss_method": "timeout",
    "timeout_loss_percentage": 35
  },
  "opening_performance": {
    "best_openings": ["Italian Game (75% win rate)", "Queen's Gambit (70%)"],
    "worst_openings": ["French Defense (30% win rate)", "Caro-Kann (35%)"],
    "opening_diversity": "moderate"
  },
  "opponent_strength": {
    "best_against": "lower_rated",
    "struggle_against": "higher_rated",
    "lower_rated_wr": 68,
    "similar_rated_wr": 52,
    "higher_rated_wr": 38
  },
  "time_performance": {
    "best_time": "afternoon",
    "worst_time": "night",
    "afternoon_wr": 58,
    "morning_wr": 51,
    "night_wr": 45
  },
  "mistake_analysis": {
    "weakest_stage": "middle",
    "early_game_mistakes": 23,
    "middle_game_mistakes": 69,
    "endgame_mistakes": 41,
    "most_common_error": "mistakes in middlegame",
    "missed_opportunities": 33,
    "avg_cp_loss": {
      "early": -45,
      "middle": -78,
      "endgame": -92
    }
  }
}
```

**OpenAI API integration:**

**Model selection:** GPT-4 (or GPT-4-turbo for faster response)
* **GPT-4:** More thorough analysis, higher quality advice (~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens)
* **GPT-4-turbo:** Faster, slightly lower cost (~$0.01 per 1K input tokens, ~$0.03 per 1K output tokens)
* **Recommendation:** Start with GPT-4-turbo to keep costs < $0.01 per analysis

**System prompt design:**

```python
SYSTEM_PROMPT = """
You are an expert chess coach analyzing a player's performance data. Your goal is to provide 
concise, actionable advice to help them improve their chess skills.

Based on the provided statistics from all 9 sections of analysis, generate ONE specific 
recommendation for EACH of the 9 sections (1-2 bullet points per section).

Your recommendations should:
- Be presented as 1-2 concise bullet points per section
- Be specific and actionable
- Reference concrete data from the analysis
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

Keep each bullet point concise (1-2 sentences maximum).
"""
```

**API implementation:**

```python
import openai
import json
import os

class ChessAdvisorService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self.model = "gpt-4-turbo"  # or "gpt-4"
        self.max_tokens = 600  # Sufficient for 9 section recommendations (v2.7+)
    
    def generate_advice(self, summary_data: dict) -> dict:
        """
        Generate personalized chess coaching advice using GPT-4 (v2.8).
        
        Args:
            summary_data: Aggregated statistics from all analysis sections
            
        Returns:
            dict with 'section_suggestions' (list of 9 section dicts with bullets)
        """
        try:
            # Prepare user prompt
            user_prompt = USER_PROMPT_TEMPLATE.format(
                summary_data_json=json.dumps(summary_data, indent=2)
            )
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,  # Balanced creativity and consistency
                presence_penalty=0.1,  # Slight penalty for repetition
                frequency_penalty=0.1
            )
            
            # Parse response
            advice_text = response.choices[0].message.content
            
            # Extract section recommendations
            parsed_advice = self._parse_advice_response(advice_text)
            
            # Log token usage for internal monitoring (not returned to user)
            tokens_used = response.usage.total_tokens
            estimated_cost = self._calculate_cost(tokens_used)
            self._log_usage(tokens_used, estimated_cost)  # Internal logging only
            
            return {
                "section_suggestions": parsed_advice["suggestions"]
            }
            
        except Exception as e:
            # Fallback to generic advice if API fails
            return self._generate_fallback_advice(summary_data)
    
    def _parse_advice_response(self, response_text: str) -> dict:
        """
        Parse GPT response into structured format (v2.8: sections only).
        """
        lines = response_text.strip().split("\n")
        suggestions = []
        
        current_section = None
        current_bullets = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section header (e.g., **Section 1 - Overall Performance:**)
            if line.startswith('**Section') and (':' in line or ':**' in line):
                # Save previous section if exists
                if current_section:
                    suggestions.append({
                        'section_number': current_section['number'],
                        'section_name': current_section['name'],
                        'bullets': current_bullets.copy()
                    })
                
                # Parse new section
                section_match = line.replace('**', '').replace(':', '').strip()
                parts = section_match.split(' - ', 1)
                
                try:
                    section_num_str = parts[0].replace('Section', '').strip()
                    section_num = int(section_num_str)
                    section_name = parts[1].strip() if len(parts) > 1 else f"Section {section_num}"
                    
                    current_section = {'number': section_num, 'name': section_name}
                    current_bullets = []
                except (ValueError, IndexError):
                    continue
                    
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                # Bullet point - only for sections
                if current_section is not None:
                    bullet = line.lstrip('•-* ').strip()
                    current_bullets.append(bullet)
        
        # Save last section if exists
        if current_section:
            suggestions.append({
                'section_number': current_section['number'],
                'section_name': current_section['name'],
                'bullets': current_bullets.copy()
            })
        
        return {
            "suggestions": suggestions
        }
    
    def _calculate_cost(self, tokens: int) -> float:
        """
        Calculate estimated cost based on token usage.
        GPT-4-turbo pricing: ~$0.01 input + ~$0.03 output per 1K tokens
        """
        # Rough estimate: assume 60% input, 40% output
        input_tokens = tokens * 0.6
        output_tokens = tokens * 0.4
        
        cost = (input_tokens / 1000 * 0.01) + (output_tokens / 1000 * 0.03)
        return round(cost, 4)
    
    def _log_usage(self, tokens: int, cost: float):
        """
        Log token usage and cost for internal monitoring.
        This is for cost tracking purposes only - not shown to users.
        """
        # Implementation: Log to file, database, or monitoring service
        logger.info(f"OpenAI API usage - Tokens: {tokens}, Estimated cost: ${cost}")
    
    def _generate_fallback_advice(self, summary_data: dict) -> dict:
        """
        Generate rule-based section advice if API fails (v2.8).
        """
        section_suggestions = []
        
        # Generate simple advice for each of the 9 sections
        section_suggestions.append({
            'section_number': 1,
            'section_name': 'Overall Performance',
            'bullets': ['Focus on consistency to improve overall win rate']
        })
        
        section_suggestions.append({
            'section_number': 2,
            'section_name': 'Color Performance',
            'bullets': ['Work on your weaker color to balance performance']
        })
        
        section_suggestions.append({
            'section_number': 3,
            'section_name': 'ELO Progression',
            'bullets': ['Analyze your losses to identify rating improvement areas']
        })
        
        section_suggestions.append({
            'section_number': 4,
            'section_name': 'Termination Wins',
            'bullets': ['Continue capitalizing on opponent mistakes']
        })
        
        section_suggestions.append({
            'section_number': 5,
            'section_name': 'Termination Losses',
            'bullets': ['Reduce timeout losses through better time management']
        })
        
        section_suggestions.append({
            'section_number': 6,
            'section_name': 'Opening Performance',
            'bullets': ['Review or replace your weakest openings']
        })
        
        section_suggestions.append({
            'section_number': 7,
            'section_name': 'Opponent Strength',
            'bullets': ['Challenge yourself by playing varied opponent strengths']
        })
        
        section_suggestions.append({
            'section_number': 8,
            'section_name': 'Time of Day',
            'bullets': ['Play more games during your best-performing time periods']
        })
        
        section_suggestions.append({
            'section_number': 9,
            'section_name': 'Move Analysis',
            'bullets': ['Practice tactics to reduce mistakes in your weakest game stage']
        })
        
        return {
            "section_suggestions": section_suggestions
        }
```

**YouTube video recommendations:**
* Integrate YouTube video links for opening-specific learning
* For player's most frequently played openings (top 3-5), provide educational video links
* **Video source prioritization (highest to lowest):**
  1. ChessNetwork
  2. GMHikaru  
  3. GothamChess (Levy Rozman)
  4. Chessbrahs
* **Implementation approach:**
  * **Option 1 (Recommended):** Curated database/config file
    - Create JSON/YAML config mapping opening names to YouTube video URLs
    - Manually curate high-quality instructional videos
    - Regularly update with new content
    - Fast, reliable, no API costs
  * **Option 2:** Google/YouTube API search
    - Use YouTube Data API v3 to search for videos
    - Search query: "[opening_name] tutorial [prioritized_channel]"
    - Cache results to minimize API calls
    - Fallback to lower priority channels if no results
* Show 1 video recommendation per opening
* Video recommendation format: "[Opening Name]: [Video Title] by [Channel] - [Watch Link]"
* Only show videos for openings player frequently uses (3+ games)

**Example curated video database structure:**
```json
{
  "Sicilian Defense": {
    "channel": "ChessNetwork",
    "title": "Sicilian Defense - Introduction",
    "url": "https://youtube.com/watch?v=...",
    "duration": "15:30"
  },
  "Italian Game": {
    "channel": "GMHikaru",
    "title": "The Italian Game Explained",
    "url": "https://youtube.com/watch?v=...",
    "duration": "12:45"
  }
}
```

**Rate limiting and cost control:**
* Max tokens per request: 800 (increased to accommodate 9+1 recommendations)
* Cache AI advice for same analysis parameters (1 hour TTL)
* Estimated cost per analysis: $0.008-$0.012 (still under 1 cent target with increased tokens)
* Monitor monthly API costs, implement usage alerts
* Fallback to rule-based advice if API quota exceeded
* If using YouTube API: max 100 searches per day (stay within free tier)

**Frontend implementation:**

**Section position:** Bottom of dashboard (after all analytics sections)

**UI design:**
```
┌─────────────────────────────────────────────┐
│ 🤖 AI Chess Coach - Personalized Analysis  │
│                                             │
│ Based on your 150 games from Jan-Mar 2025  │
│                                             │
│ 🎯 Overall Recommendation:                  │
│                                             │
│ • Fix time management by switching to       │
│   increment games - 35% timeout losses      │
│   indicate this is your biggest weakness    │
│                                             │
│ • Improve or replace French Defense (30%   │
│   win rate) - consider more solid options  │
│   like Caro-Kann or Petroff Defense        │
│                                             │
│ • Focus 70% of study time on middlegame    │
│   tactics (moves 10-20) where you have 69  │
│   mistakes compared to 23 in early game    │
│                                             │
│ • Schedule important games between 2-10pm  │
│   when your win rate is highest (58%)      │
│                                             │
│ [🔄 Regenerate Advice]                      │
└─────────────────────────────────────────────┘
```

**Loading state:**
* Show spinner with message: "AI Coach is analyzing your games..."
* Display progress: "This may take up to 10 seconds"
* If takes longer than 10 seconds, show: "Almost done..."
* Timeout after 15 seconds with error message and fallback advice

**Error handling:**
* API failure → Show fallback rule-based advice
* Timeout → Show partial results with notice
* Rate limit exceeded → Show cached advice or generic tips
* Invalid response → Parse what's possible, show partial advice

**Acceptance criteria:**
- [ ] OpenAI GPT-4-turbo API integrated and working
- [ ] System prompt produces relevant, actionable advice
- [ ] Summary data includes all sections (1-9) without raw PGN
- [ ] API response parsed correctly into structured format
- [ ] Overall recommendation displayed as concise bullet points (3-5 bullets)
- [ ] Each bullet point is specific and references actual player data
- [ ] Bullet points are actionable and prioritized by impact
- [ ] No section-specific recommendations displayed (removed as per v2.6)
- [ ] No YouTube video recommendations in AI section (simplified in v2.6)
- [ ] Loading state shows during API call (< 10 seconds)
- [ ] Cost per analysis < $0.008 (reduced token limit to 300)
- [ ] AI advice cached for 1 hour (same parameters)
- [ ] Fallback advice works when API fails (bullet point format)
- [ ] Error states handled gracefully
- [ ] Section appears at bottom of dashboard
- [ ] Regenerate button works (calls API again)
- [ ] Token usage and cost logged internally for monitoring (NOT displayed to users)
- [ ] Privacy: No raw PGN data sent to OpenAI
- [ ] Rate limiting prevents excessive API calls
- [ ] UI is responsive on mobile devices

---

### Testing for Milestones 8 & 9

**TC-020A: Date range validation**
* Attempt to select date range of 45 days
* Verify error message displayed: "Please select a date range of 30 days or less"
* Verify submit button is disabled
* Change to 30 days, verify error clears and submit enabled
* Change to 7 days, verify works correctly
* Verify preset buttons "Last 7 Days" and "Last 30 Days" work instantly

**TC-020B: Date range edge cases**
* Test exactly 30 days: Should work
* Test 31 days: Should show error
* Test 0 days (same start and end): Should show error (minimum 1 day)
* Test future dates: Should show error
* Test start date after end date: Should show error

**TC-021: Mistake analysis with dynamic sampling logic**
* Complete analysis workflow with engine analysis enabled
* **Test Scenario 1: Small dataset (<50 games)**
  - Use "Last 7 Days" preset (assume ~30 games)
  - Verify loading indicator shows "Analyzing game X of Y"
  - Verify display shows: "Comprehensive analysis of 30 games"
  - Verify ALL 30 games are analyzed (no sampling)
* **Test Scenario 2: Large dataset (≥50 games)**
  - Use "Last 30 Days" preset (assume ~60 games)
  - Verify display shows: "Analysis based on X games (Y% sample)"
  - Verify 20% of games analyzed (12 games in this case, min 10, max 50)
  - Verify tooltip explains sampling strategy
* Common verifications for both scenarios:
  - Verify Section 9 displays mistake analysis table
  - Verify table shows three rows (early/middle/endgame)
  - Verify mistake counts (inaccuracies/mistakes/blunders) are present
  - Verify average CP loss calculated per stage
  - Verify links to critical mistake games work
  - Verify weakest stage identified correctly
  - Click on game link, verify it opens correct game on Chess.com

**TC-021A: Dynamic sampling strategy verification**
* **Small dataset test (<50 games):**
  - Analyze period with 35 total games
  - Verify ALL 35 games analyzed
  - Verify display: "Comprehensive analysis of 35 games"
  - Note analysis time
* **Large dataset test (≥50 games):**
  - Analyze period with 100 total games
  - Verify 20 games analyzed (20% sample)
  - Verify display: "Analysis based on 20 games (20% sample)"
  - Verify games distributed across time period
  - Note analysis time
* **Boundary test (exactly 50 games):**
  - Analyze period with exactly 50 games
  - Verify 10 games analyzed (20%, hits minimum)
  - Verify display: "Analysis based on 10 games (20% sample)"
* **Run analysis again for same date range:**
  - Verify same games used (cached), no re-analysis
  - Verify cached analysis time <5 seconds

**TC-021B: Progressive cache improvement with dynamic sampling**
* **Day 1: Small dataset analysis**
  - Analyze Last 7 Days (30 games total)
  - Verify all 30 games analyzed (comprehensive)
  - Note which games were analyzed
  - Note analysis time
* **Day 2: Repeat same period**
  - Analyze Last 7 Days again (same period)
  - Verify analysis completes in <5 seconds (fully cached)
  - Verify no new analysis performed
* **Day 3: Expand to large dataset**
  - Analyze Last 30 Days (80 games total, includes previous 30)
  - Verify previous 30 games NOT re-analyzed (cached)
  - Verify 16 games analyzed from new 50 games (20% of new games)
  - Verify display: "Analysis based on X games (Y% sample)"
  - Verify total time reasonable (only new games analyzed)

**TC-021C: Dataset size thresholds verification**
* **Scenario 1: 10 total games**
  - Verify 10 games analyzed (100%)
  - Verify display: "Comprehensive analysis of 10 games"
* **Scenario 2: 49 total games (boundary)**
  - Verify 49 games analyzed (100%, just under threshold)
  - Verify display: "Comprehensive analysis of 49 games"
* **Scenario 3: 50 total games (boundary)**
  - Verify 10 games analyzed (20%, hits minimum)
  - Verify display: "Analysis based on 10 games (20% sample)"
* **Scenario 4: 100 total games**
  - Verify 20 games analyzed (20%)
  - Verify display: "Analysis based on 20 games (20% sample)"
* **Scenario 5: 300 total games**
  - Verify 50 games analyzed (16.7%, hits maximum)
  - Verify display: "Analysis based on 50 games (16.7% sample)"
* **Scenario 6: All cached**
  - Verify <5 seconds response time
  - Verify no new analysis performed

**TC-022: Engine analysis caching**
* Run analysis for date range with 50 games
* Note analysis time
* Run same analysis again immediately
* Verify second analysis is significantly faster (< 5 seconds)
* Verify results are identical
* Verify cache hit logged in backend

**TC-023: Missed opportunity detection**
* Verify missed opportunities column shows count > 0
* Manually review 2-3 games to validate opponent mistakes detected
* Verify player's suboptimal response identified

**TC-024: AI advisor basic functionality**
* Complete full analysis workflow
* Verify Section 10 (AI Coach) appears at bottom
* Verify loading indicator shows "AI Coach is analyzing..."
* Verify advice appears within 10 seconds
* Verify EXACTLY 9 section-specific recommendations displayed
* Verify each recommendation clearly labeled with section number and name
* Verify recommendations appear in order (Section 1 through Section 9)
* Verify 1 overall recommendation displayed at the end
* Verify advice references actual player data (percentages, numbers)
* Verify YouTube video links present for player's common openings
* Verify video links are clickable
* Count recommendations: should be 9 section-specific + 1 overall = 10 total

**TC-025: AI advisor advice quality**
* Read all suggestions provided
* Verify advice is specific (not generic)
* Verify advice references concrete stats (e.g., "35% timeout losses")
* Verify advice is actionable (tells player what to do)
* Verify no raw PGN data visible in network requests (check DevTools)
* Verify advice makes sense given the displayed analytics
* Verify each of 9 sections has received a recommendation
* Verify no section is skipped or duplicated
* Verify YouTube video recommendations match player's opening repertoire
* Verify video channel priority followed (ChessNetwork > GMHikaru > GothamChess > Chessbrahs)
* Click video link, verify it opens YouTube video in new tab
* Verify video is relevant to the opening mentioned

**TC-026: AI advisor error handling**
* Disconnect internet before clicking analyze
* Verify fallback advice displayed
* Verify error message shown
* Reconnect and verify API call works
* Test with invalid API key (backend config)
* Verify graceful degradation to rule-based advice

**TC-027: AI advisor caching**
* Complete analysis for username + date range
* Note the specific advice given
* Immediately run same analysis again
* Verify identical advice returned (cached)
* Verify second response is faster (< 2 seconds)
* Wait 1 hour, run again
* Verify new API call made (cache expired)

**TC-028: AI advisor regenerate**
* Complete analysis and receive AI advice
* Click "Regenerate Advice" button
* Verify new API call made
* Verify new advice displayed (may be similar but timestamp updated)
* Verify loading state shown during regeneration

**TC-029: Cost monitoring**
* Complete 10 analyses with AI advisor
* Check backend logs for token usage
* Verify total cost < $0.10 for 10 analyses
* Verify average cost per analysis < $0.01

**TC-030: End-to-end full dashboard**
* Complete analysis with all sections (1-10)
* Verify all sections render without errors
* Verify smooth scrolling through entire dashboard
* Verify AI advice synthesizes data from all sections
* Verify loading states don't block other sections
* Verify mobile responsive design for all new sections
* Verify no JavaScript console errors

---

# Tech stack

**Backend**

* Flask (existing)
* Python 3.12
* Chess.com Public API
* `python-chess` library for PGN parsing and Stockfish integration
* `requests` for API calls
* `pytz` or `zoneinfo` for timezone handling
* `openai` Python library for GPT-4 API integration
* Stockfish chess engine (local installation)
* SQLAlchemy (optional, for caching)
* Redis (recommended for caching engine analysis and AI advice)
* Custom caching utilities (existing)

**Frontend**

* Vanilla JavaScript (ES6+)
* Chart.js 4.x for all visualizations
* HTML5 / CSS3
* Fetch API for asynchronous requests
* Intl API for timezone detection

**AI/ML Services**

* OpenAI GPT-4-turbo API for chess coaching advice
* Stockfish 15+ chess engine for move analysis
* Multiprocessing for parallel game analysis

**Testing**

* Playwright for E2E testing
* unittest/pytest for backend unit tests
* Test with real user data (username: 'jay_fh')
* OpenAI API cost monitoring and logging

**Development tools**

* uv for package management
* Git for version control
* GitHub for repository hosting
* Stockfish executable (system dependency)
* OpenAI API cost monitoring and logging

**Development tools**

* uv for package management
* Git for version control
* GitHub for repository hosting
* Stockfish executable (system dependency)

---

# System architecture

```
User Browser
    ↓
[Analytics Page]
    ↓ (Fetch with timezone)
Flask API Routes
    ↓
[Analytics Service]
    ↓
[Chess Service] ← → [Chess.com API]
    ↓
[PGN Parser]
    ↓
[Mistake Analysis Engine] ← → [Stockfish Engine]
    ↓
[Statistics Calculator]
    ↓
[AI Advisor Service] ← → [OpenAI GPT-4 API]
    ↓
[Cache Layer] (Redis - engine analysis + AI advice)
    ↓
JSON Response
    ↓
[Chart.js Visualizations + AI Recommendations]
    ↓
User sees comprehensive analytics with AI coaching
```

**Data flow:**

1. User enters username, date range on frontend
2. JavaScript detects user's timezone
3. Frontend sends request to `/api/analyze/detailed`
4. Backend validates inputs
5. Backend fetches games from Chess.com API
6. Backend parses PGN data for openings
7. Backend runs Stockfish engine analysis for mistake detection (cached if available)
8. Backend calculates all analytics sections (1-9)
9. Backend prepares summary data for AI advisor
10. Backend calls OpenAI GPT-4 API for personalized coaching advice
11. Backend converts timestamps to user timezone
12. Backend returns comprehensive JSON response (including AI advice)
13. Frontend renders all sections with Chart.js
14. Frontend displays AI coaching recommendations at bottom
15. User scrolls through complete analytics dashboard with AI insights

---

# Website overview

The analytics dashboard will be a single-page scrollable experience with a clean, modern design inspired by contemporary dashboard aesthetics.

## Page structure

```
┌─────────────────────────────────────────────┐
│ Navigation Bar                              │
│ [Logo] [Home] [Analytics]                   │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ Analysis Header Card                        │
│ Username: jay_fh                            │
│ Period: Jan 1 - Mar 31, 2025               │
│ Timezone: America/New_York                  │
│ Total Games: 150                            │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Section 1: Overall Performance Over Time    │
│ [Line Chart: Wins/Losses/Draws]            │
└─────────────────────────────────────────────┘

┌──────────────────────┬──────────────────────┐
│ Section 2a:          │ Section 2b:          │
│ White Performance    │ Black Performance    │
│ [Chart]              │ [Chart]              │
└──────────────────────┴──────────────────────┘

┌─────────────────────────────────────────────┐
│ Section 3: Elo Rating Progression           │
│ [Line Chart with trend]                     │
└─────────────────────────────────────────────┘

┌──────────────────────┬──────────────────────┐
│ Section 4:           │ Section 5:           │
│ How You Win          │ How You Lose         │
│ [Doughnut Chart]     │ [Doughnut Chart]     │
└──────────────────────┴──────────────────────┘

┌─────────────────────────────────────────────┐
│ Section 6: Opening Performance              │
│ Top 5 Best Openings                         │
│ [Horizontal bar chart]                      │
│ Top 5 Worst Openings                        │
│ [Horizontal bar chart]                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Section 7: Opponent Strength Analysis       │
│ [Grouped bar chart or 3 cards]             │
│ Lower | Similar | Higher                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Section 8: Time of Day Performance          │
│ [Grouped bar chart or 3 cards]             │
│ Morning | Afternoon | Night                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Section 9: Mistake Analysis by Game Stage   │
│ [Table: Early/Middle/Endgame mistakes]     │
│ Inaccuracies | Mistakes | Blunders          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Section 10: AI Chess Coach                  │
│ 🤖 Personalized Recommendations             │
│ • Section-specific suggestions (up to 7)    │
│ • Overall recommendation                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Footer                                      │
└─────────────────────────────────────────────┘
```

## Design specifications

**Layout:**
* Maximum content width: 1200px
* Card padding: 24px
* Card margin: 20px bottom
* Border radius: 12px
* Box shadow: 0 2px 8px rgba(0,0,0,0.1)

**Typography:**
* Headings: Sans-serif, bold, 24px
* Subheadings: Sans-serif, semibold, 18px
* Body text: Sans-serif, regular, 14px
* Chart labels: 12px

**Color palette:**
* Background: #f8f9fa
* Card background: #ffffff
* Primary: #3498db
* Success/Win: #27ae60
* Danger/Loss: #e74c3c
* Neutral/Draw: #95a5a6
* Text: #2c3e50
* Text light: #7f8c8d

**Responsive breakpoints:**
* Desktop: > 1024px (2-column grid where applicable)
* Tablet: 768px - 1024px (mixed layout)
* Mobile: < 768px (single column)

---

# Database schema overview

## Optional: analytics_cache table

If implementing caching for performance optimization:

| Field | Type | Description |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY | Unique identifier |
| username | TEXT | Chess.com username |
| start_date | TEXT | Analysis start date |
| end_date | TEXT | Analysis end date |
| timezone | TEXT | User timezone |
| analysis_data | TEXT (JSON) | Cached analysis results |
| created_at | TIMESTAMP | Cache creation time |
| expires_at | TIMESTAMP | Cache expiration time |

**Notes:**
* Cache TTL: 1 hour
* Invalidate on new analysis request with same parameters
* Consider Redis for better performance

---

# Key workflows

## Main analytics workflow

1. User navigates to `/analytics` page
2. User enters Chess.com username (e.g., 'jay_fh')
3. User selects date range (or uses preset)
4. JavaScript detects timezone automatically (with option to change)
5. User clicks "Analyze"
6. Frontend shows loading state
7. Frontend sends POST request to `/api/analyze/detailed`
8. Backend validates inputs
9. Backend checks cache for existing analysis (optional)
10. Backend fetches games from Chess.com API (monthly batches)
11. Backend filters games by date range
12. Backend parses PGN data for each game
13. Backend calculates all 8 analytics sections:
    - Daily aggregations for time-series
    - Color-based statistics
    - Elo tracking and progression
    - Termination type categorization
    - Opening extraction and performance
    - Opponent strength categorization
    - Time-of-day categorization
14. Backend converts timestamps to user timezone
15. Backend returns comprehensive JSON
16. Frontend renders all 8 sections with Chart.js
17. User scrolls through analytics dashboard
18. User can export or share results (future enhancement)

---

## Opening analysis workflow

1. For each game in filtered dataset:
2. Extract PGN string from game data
3. Parse PGN using `python-chess` library
4. Extract first 5-10 moves
5. Identify opening name using opening book/database
6. Store opening name with game result
7. Group games by opening name
8. Calculate statistics per opening:
   - Total games played
   - Wins, losses, draws
   - Win rate percentage
9. Filter openings with 3+ games
10. Sort by win rate
11. Select top 5 and bottom 5
12. Return formatted data for visualization

---

## Timezone handling workflow

1. Frontend detects timezone using `Intl.DateTimeFormat().resolvedOptions().timeZone`
2. Display detected timezone to user with option to change
3. Send timezone string to backend with analysis request
4. Backend receives timezone parameter
5. For each game timestamp (UTC):
   - Convert to user's timezone using `pytz` or `zoneinfo`
   - Extract hour for time-of-day categorization
   - Extract date for daily aggregation
6. Return localized timestamps in JSON response
7. Frontend displays all times in user's timezone
8. Display timezone prominently in header

---

# Client context

This enhanced analytics dashboard is designed for chess players who actively play on Chess.com and want deeper insights into their performance. The primary users are:

* **Casual chess enthusiasts** who want to track improvement over time
* **Competitive players** analyzing strengths and weaknesses to prepare for tournaments
* **Chess coaches** reviewing student performance patterns
* **Data-minded players** who enjoy detailed statistics and visualizations

The system provides actionable insights that players can use to:
* Identify which openings to study or avoid
* Determine optimal playing times
* Understand termination patterns (time management issues, tactical weaknesses)
* Track rating progression and goal achievement
* Adjust strategies based on opponent strength

The test user 'jay_fh' represents a typical user who wants comprehensive analysis of their Chess.com games with accurate, timezone-aware statistics presented in a clean, modern interface.

---

# Success metrics

**Functional metrics:**
* All 10 analytics sections render correctly with accurate data
* Timezone conversion works correctly across all time zones
* PGN parsing successfully extracts opening names (>95% success rate)
* API response time < 10 seconds for 3-month analysis (including engine analysis)
* Stockfish engine analysis accuracy validated against manual review
* AI advisor provides relevant, actionable advice (qualitative assessment)
* AI API cost per analysis < $0.01
* Zero critical bugs in production for statistical calculations
* All Playwright E2E tests pass (30 test cases)

**User experience metrics:**
* Dashboard loads and renders within 6 seconds
* Charts are interactive and responsive
* Mobile-friendly design (all sections usable on mobile)
* Clear, actionable insights presented
* Minimal user confusion (no support requests about data accuracy)

**Technical quality metrics:**
* Code coverage >80% for analytics service
* Proper error handling for all edge cases
* Efficient caching reduces redundant API calls
* Clean, maintainable code following PEP 8
* Comprehensive documentation in docstrings

**Accuracy metrics:**
* Statistical calculations verified against manual calculations
* Test user data ('jay_fh') displays correctly
* No data misclassification (wins/losses/draws accurate)
* Opening names match actual openings played
* Timezone conversions produce correct local times

---

# Testing and validation

## Testing requirements

All features must be thoroughly tested to ensure data accuracy and proper functionality. Testing will be performed at multiple levels:

### Unit testing

**Backend (Python):**
* Test `AnalyticsService` statistical calculations
  - Verify win/loss/draw counting is accurate
  - Test daily aggregation functions
  - Validate Elo differential calculations
  - Test termination type categorization
  - Verify time-of-day categorization with various timezones
* Test PGN parsing functions
  - Verify opening extraction from various PGN formats
  - Handle malformed PGN data gracefully
  - Test opening name identification
* Test timezone conversion utilities
  - Verify UTC to local timezone conversion
  - Test with multiple timezones (EST, PST, UTC, GMT+8, etc.)
  - Handle daylight saving time transitions
* Test data validation functions
  - Username validation
  - Date range validation
  - Timezone string validation

**Test data:**
* Use real games from 'jay_fh' account
* Create synthetic test games covering edge cases
* Test with empty datasets (no games in period)
* Test with single game
* Test with large datasets (500+ games)

### Integration testing

* Test full workflow from API request to JSON response
* Verify Chess.com API integration
* Test caching layer functionality
* Verify error handling for API failures
* Test rate limiting behavior

### End-to-end testing with Playwright

**Test cases:**

**TC-001: Full analytics workflow**
* Navigate to analytics page
* Enter username 'jay_fh'
* Select date range (last 3 months)
* Click analyze button
* Verify all 8 sections render
* Verify charts display data
* Verify no JavaScript errors

**TC-002: Overall performance chart**
* Complete analysis workflow
* Verify Section 1 (Overall Performance) displays
* Verify line chart has three lines (wins, losses, draws)
* Verify x-axis shows dates
* Verify y-axis shows game counts
* Hover over data point, verify tooltip appears
* Verify data matches expected values

**TC-003: Color performance analysis**
* Complete analysis workflow
* Verify Section 2 displays two charts/sections
* Verify White performance chart shows data
* Verify Black performance chart shows data
* Verify win rates are displayed
* Verify data is correctly separated by color

**TC-004: Elo rating progression**
* Complete analysis workflow
* Verify Section 3 displays line chart
* Verify rating values are displayed on y-axis
* Verify dates on x-axis
* Verify rating change summary is shown
* Verify data points correspond to actual games

**TC-005: Termination types (wins)**
* Complete analysis workflow
* Verify Section 4 displays doughnut/pie chart
* Verify all winning games are categorized
* Verify percentages add up to 100%
* Verify chart legend is readable
* Click chart segment, verify interaction (if implemented)

**TC-006: Termination types (losses)**
* Complete analysis workflow
* Verify Section 5 displays doughnut/pie chart
* Verify all losing games are categorized
* Verify percentages add up to 100%
* Verify chart legend is readable

**TC-007: Opening performance**
* Complete analysis workflow
* Verify Section 6 displays two lists
* Verify "Top 5 Best Openings" shows 5 or fewer items
* Verify "Top 5 Worst Openings" shows 5 or fewer items
* Verify opening names are displayed (no ECO codes)
* Verify win rates are calculated correctly
* Verify game counts are shown

**TC-008: Opponent strength analysis**
* Complete analysis workflow
* Verify Section 7 displays three categories
* Verify "Lower rated" category shows data
* Verify "Similar rated" category shows data
* Verify "Higher rated" category shows data
* Verify win rates are displayed for each
* Verify game counts are shown

**TC-009: Time of day performance**
* Complete analysis workflow
* Verify Section 8 displays three time periods
* Verify Morning (6am-2pm) data is shown
* Verify Afternoon (2pm-10pm) data is shown
* Verify Night (10pm-6am) data is shown
* Verify timezone is displayed
* Verify win rates are calculated correctly

**TC-010: Timezone handling**
* Change browser timezone setting
* Complete analysis workflow
* Verify detected timezone is correct
* Verify time-of-day categorization is accurate
* Verify timestamps in charts match user timezone

**TC-011: Empty dataset handling**
* Enter username with no games in date range
* Verify appropriate message is displayed
* Verify no JavaScript errors occur
* Verify empty state is user-friendly

**TC-012: Error handling**
* Enter invalid username
* Verify error message is displayed
* Enter invalid date range (end before start)
* Verify validation error is shown
* Test with network disconnected
* Verify graceful error handling

**TC-013: Responsive design**
* Complete analysis workflow on desktop (1920x1080)
* Verify all sections are visible and properly laid out
* Resize to tablet (768px width)
* Verify layout adapts appropriately
* Resize to mobile (375px width)
* Verify all sections are accessible and scrollable
* Verify charts are readable on small screens

**TC-014: Performance**
* Complete analysis with 3-month date range
* Verify page loads within 6 seconds
* Verify no lag when scrolling
* Verify charts render smoothly
* Monitor network requests for efficiency

### Manual verification with test user

**Using username: 'jay_fh'**

1. **Data accuracy verification:**
   - Randomly select 10 games from Chess.com website
   - Verify these games appear in correct analytics sections
   - Manually calculate win rate for a specific date range
   - Compare with dashboard output
   - Verify opening names match actual games played

2. **Statistical validation:**
   - Verify total game count matches sum of wins+losses+draws
   - Verify percentages add up correctly
   - Verify win rates are calculated as wins/(wins+losses+draws)
   - Verify Elo differences are calculated correctly
   - Spot check 5 random game categorizations

3. **Timezone verification:**
   - Select games played at known times
   - Verify time-of-day categorization is correct
   - Test with different timezone settings
   - Verify daylight saving time handling

4. **Edge cases:**
   - Test with date range containing 0 games
   - Test with date range containing 1 game
   - Test with very short date range (1 day)
   - Test with maximum date range (1 year)

### Pre-deployment checklist

Before deploying changes to production:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All Playwright E2E tests pass
- [ ] Manual verification with 'jay_fh' completed
- [ ] Data accuracy spot-checked and verified
- [ ] Tested on Chrome, Firefox, Safari
- [ ] Tested on mobile devices (iOS and Android)
- [ ] Timezone handling verified with at least 3 different timezones
- [ ] Error handling tested for all failure scenarios
- [ ] Performance benchmarks met (< 6 second load time)
- [ ] Code reviewed by at least one other developer
- [ ] Documentation updated (API docs, README)
- [ ] No console errors or warnings in browser
- [ ] Caching functionality verified (if implemented)
- [ ] Rate limiting tested and working

### Continuous validation

After deployment:
* Monitor error logs for unexpected issues
* Track API response times
* Gather user feedback on data accuracy
* Periodically re-verify with test user 'jay_fh'
* Update test cases as new edge cases are discovered

---

# User stories and acceptance criteria summary

## EA-001: Overall performance over time
**As a** chess player  
**I want to** see my win/loss/draw trends over time  
**So that** I can track my overall performance improvement

**Acceptance criteria:**
- [ ] Daily aggregated line chart displays wins, losses, and draws
- [ ] Dates are in user's local timezone
- [ ] Chart is responsive on all devices
- [ ] Interactive tooltips show details
- [ ] Empty dates are handled gracefully

---

## EA-002: Color performance analysis
**As a** chess player  
**I want to** see my performance as White vs Black over time  
**So that** I can identify color-specific strengths and weaknesses

**Acceptance criteria:**
- [ ] Separate visualizations for White and Black
- [ ] Daily aggregation by color
- [ ] Win rate percentages clearly displayed
- [ ] Visual comparison between colors is intuitive
- [ ] Data correctly distinguishes player's color per game

---

## EA-003: Elo rating progression
**As a** chess player  
**I want to** see my Elo rating changes over time  
**So that** I can track my rating improvement or decline

**Acceptance criteria:**
- [ ] Line chart shows Elo rating over time
- [ ] Rating values extracted correctly from games
- [ ] Net rating change displayed prominently
- [ ] Handles different time controls separately
- [ ] Trend line or moving average shown

---

## EA-004: How I win games
**As a** chess player  
**I want to** know how I typically win games  
**So that** I can understand my winning patterns

**Acceptance criteria:**
- [ ] All winning games categorized by termination type
- [ ] Accurate percentages displayed
- [ ] Only includes games where user won
- [ ] All termination types handled
- [ ] Clear visual representation

---

## EA-005: How I lose games
**As a** chess player  
**I want to** know how I typically lose games  
**So that** I can identify and improve weaknesses

**Acceptance criteria:**
- [ ] All losing games categorized by termination type
- [ ] Accurate percentages displayed
- [ ] Only includes games where user lost
- [ ] All termination types handled
- [ ] Easy comparison with winning terminations

---

## EA-006: Opening performance analysis
**As a** chess player  
**I want to** see which openings I perform best and worst with  
**So that** I can focus my study and exploit my strengths

**Acceptance criteria:**
- [ ] PGN data parsed correctly
- [ ] Opening names extracted accurately (no ECO codes)
- [ ] Win rates calculated correctly
- [ ] Only openings with 3+ games included
- [ ] Top 5 best and worst openings displayed
- [ ] Games played count shown per opening

---

## EA-007: Opponent strength analysis
**As a** chess player  
**I want to** see my win rate against different opponent strengths  
**So that** I can understand my performance at different levels

**Acceptance criteria:**
- [ ] Elo differentials calculated correctly
- [ ] Games categorized into Lower/Similar/Higher rated
- [ ] Win rates calculated per category
- [ ] Visual representation is clear
- [ ] Game counts displayed per category
- [ ] Handles missing ratings gracefully

---

## EA-008: Time of day performance
**As a** chess player  
**I want to** see when I play best during the day  
**So that** I can schedule important games during peak times

**Acceptance criteria:**
- [ ] Timestamps converted to user's local timezone
- [ ] Games categorized into Morning/Afternoon/Night
- [ ] Win rates calculated per time period
- [ ] Games played distribution is visible
- [ ] Timezone displayed clearly to user
- [ ] Handles boundary times correctly

---

## EA-009: Input validation and error handling
**As a** user  
**I want to** receive clear feedback on invalid inputs  
**So that** I understand what went wrong and can correct it

**Acceptance criteria:**
- [ ] Invalid username shows clear error message
- [ ] Invalid date range is rejected with helpful message
- [ ] API failures display user-friendly error
- [ ] Network errors handled gracefully
- [ ] Empty datasets show appropriate message

---

## EA-010: Responsive dashboard design
**As a** user  
**I want to** access the analytics dashboard on any device  
**So that** I can review my stats on desktop, tablet, or mobile

**Acceptance criteria:**
- [ ] Single-page scrollable layout on all devices
- [ ] Charts are readable on mobile screens
- [ ] All sections accessible on small screens
- [ ] Touch-friendly interactions on mobile
- [ ] Consistent design across breakpoints

---

## EA-011: Timezone detection and configuration
**As a** user  
**I want to** see all times in my local timezone  
**So that** time-based analysis is accurate for my location

**Acceptance criteria:**
- [ ] Timezone automatically detected
- [ ] User can change timezone if needed
- [ ] Timezone clearly displayed in header
- [ ] All timestamps converted correctly
- [ ] Daylight saving time handled properly

---

## EA-012: Performance and caching
**As a** user  
**I want to** receive analysis results quickly  
**So that** I don't have to wait long for insights

**Acceptance criteria:**
- [ ] Analysis completes within 10 seconds for 3-month range (including AI advisor)
- [ ] Caching reduces redundant API calls
- [ ] Loading states indicate progress
- [ ] No UI lag when scrolling dashboard
- [ ] Charts render smoothly

---

## EA-018: Mistake analysis by game stage
**As a** chess player  
**I want to** identify which game stage I make the most mistakes in  
**So that** I can focus my training on specific phases of play

**Acceptance criteria:**
- [ ] Stockfish engine analyzes all games for mistakes
- [ ] Mistakes categorized by game stage (early/middle/endgame)
- [ ] Mistakes classified as inaccuracy/mistake/blunder
- [ ] Centipawn loss calculated and displayed
- [ ] Missed opportunities detected and counted
- [ ] Table displays all required data columns
- [ ] Links to critical mistake games work
- [ ] Engine analysis cached for performance
- [ ] Loading indicator shows analysis progress

---

## EA-019: AI-powered chess advisor
**As a** chess player  
**I want to** receive personalized coaching advice based on my complete analysis  
**So that** I know exactly what to work on to improve

**Acceptance criteria:**
- [ ] OpenAI GPT-4 API integrated
- [ ] Summary data includes insights from all sections (no raw PGN)
- [ ] AI generates EXACTLY 9 section-specific recommendations (one per section 1-9)
- [ ] Each section recommendation has 1-2 concise bullet points
- [ ] Each recommendation clearly labeled with section name
- [ ] Advice is specific and actionable
- [ ] Advice references actual player statistics
- [ ] Cost per analysis < $0.012
- [ ] Response time < 10 seconds
- [ ] Loading state shown during AI processing
- [ ] Fallback advice works if API fails (includes all 9 sections)
- [ ] AI advice cached for 1 hour
- [ ] Section appears at bottom of dashboard
- [ ] No overall recommendation displayed (removed in v2.8)

---

## EA-020: Website analytics tracking with Google Tag Manager
**As a** website owner  
**I want to** track visitor behavior and page views using Google Tag Manager  
**So that** I can understand user engagement and make data-driven product decisions

**Acceptance criteria:**
- [ ] Google Tag Manager (GTM) script added to all HTML templates
- [ ] GTM container ID GT-NFBTKHBS properly configured
- [ ] Google Analytics 4 tag G-VMYYSZC29R integrated
- [ ] GTM script placed in `<head>` section of all pages
- [ ] Noscript fallback added immediately after `<body>` tag for non-JavaScript users
- [ ] Both index.html and analytics.html templates updated
- [ ] GTM tags fire correctly on page load (verified in GTM Preview mode)
- [ ] Page load performance not impacted (< 100ms additional load time)
- [ ] No personally identifiable information (PII) tracked
- [ ] GTM respects Do Not Track (DNT) browser settings
- [ ] Analytics data visible in Google Analytics dashboard within 24 hours
- [ ] Track page views for both home page and analytics dashboard
- [ ] No backend code changes required
- [ ] Testing includes verification with GTM debugger

---

# Implementation notes

## PGN parsing approach

Use `python-chess` library for robust PGN parsing:

```python
import chess.pgn
from io import StringIO

def extract_opening_name(pgn_string):
    """Extract opening name from PGN."""
    pgn = StringIO(pgn_string)
    game = chess.pgn.read_game(pgn)
    
    # Get first 5-10 moves
    board = game.board()
    moves = []
    for move in list(game.mainline_moves())[:10]:
        moves.append(board.san(move))
        board.push(move)
    
    # Look up opening name based on move sequence
    opening_name = identify_opening(moves)
    return opening_name
```

Consider using an opening book database or API for accurate opening identification.

---

## Chart.js configuration examples

**Line chart for daily performance:**
```javascript
new Chart(ctx, {
  type: 'line',
  data: {
    labels: dates,  // ['2025-01-01', '2025-01-02', ...]
    datasets: [
      {
        label: 'Wins',
        data: winsData,
        borderColor: '#27ae60',
        fill: false
      },
      {
        label: 'Losses',
        data: lossesData,
        borderColor: '#e74c3c',
        fill: false
      },
      {
        label: 'Draws',
        data: drawsData,
        borderColor: '#95a5a6',
        fill: false
      }
    ]
  },
  options: {
    responsive: true,
    plugins: {
      tooltip: {
        mode: 'index',
        intersect: false
      }
    },
    scales: {
      x: {
        display: true,
        title: { display: true, text: 'Date' }
      },
      y: {
        display: true,
        title: { display: true, text: 'Games' },
        beginAtZero: true
      }
    }
  }
});
```

---

## API response example

```json
{
  "username": "jay_fh",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "timezone": "America/New_York",
  "total_games": 150,
  "sections": {
    "overall_performance": {
      "daily_stats": [
        {"date": "2025-01-01", "wins": 3, "losses": 2, "draws": 1},
        {"date": "2025-01-02", "wins": 2, "losses": 3, "draws": 0}
      ]
    },
    "color_performance": {
      "white": {
        "daily_stats": [...],
        "win_rate": 52.5
      },
      "black": {
        "daily_stats": [...],
        "win_rate": 48.3
      }
    },
    "elo_progression": {
      "data_points": [
        {"date": "2025-01-01", "rating": 1500},
        {"date": "2025-01-02", "rating": 1505}
      ],
      "rating_change": +25
    },
    "termination_wins": {
      "checkmate": {"count": 25, "percentage": 50},
      "timeout": {"count": 15, "percentage": 30},
      "resignation": {"count": 10, "percentage": 20}
    },
    "termination_losses": {
      "checkmate": {"count": 20, "percentage": 40},
      "timeout": {"count": 20, "percentage": 40},
      "resignation": {"count": 10, "percentage": 20}
    },
    "opening_performance": {
      "best_openings": [
        {
          "name": "Italian Game",
          "games": 12,
          "wins": 9,
          "losses": 2,
          "draws": 1,
          "win_rate": 75.0
        }
      ],
      "worst_openings": [...]
    },
    "opponent_strength": {
      "lower_rated": {
        "games": 40,
        "wins": 28,
        "losses": 8,
        "draws": 4,
        "win_rate": 70.0
      },
      "similar_rated": {...},
      "higher_rated": {...}
    },
    "time_of_day": {
      "morning": {
        "games": 45,
        "wins": 25,
        "losses": 15,
        "draws": 5,
        "win_rate": 55.6
      },
      "afternoon": {...},
      "night": {...}
    }
  }
}
```

---

# Development roadmap

**Phase 1: Backend foundation (Week 1)**
* Enhance ChessService with PGN fetching
* Implement AnalyticsService with all calculation functions
* Add timezone conversion utilities
* Create comprehensive unit tests
* Implement caching strategy

**Phase 2: API development (Week 1-2)**
* Create `/api/analyze/detailed` endpoint
* Implement request validation
* Add error handling
* Test with 'jay_fh' data
* Optimize for performance

**Phase 3: Frontend structure (Week 2)**
* Design dashboard layout
* Implement CSS framework
* Create card components
* Add loading and error states
* Implement responsive design

**Phase 4: Visualizations Part 1 (Week 2-3)**
* Section 1: Overall performance chart
* Section 2: Color performance charts
* Section 3: Elo progression chart
* Test and refine interactions

**Phase 5: Visualizations Part 2 (Week 3)**
* Section 4: Winning terminations
* Section 5: Losing terminations
* Section 6: Opening performance
* Implement opening parser

**Phase 6: Visualizations Part 3 (Week 3-4)**
* Section 7: Opponent strength analysis
* Section 8: Time of day performance
* Integrate timezone handling throughout

**Phase 7: Testing and refinement (Week 4)**
* Write Playwright E2E tests
* Perform manual verification with 'jay_fh'
* Fix bugs and edge cases
* Optimize performance
* Refine UI/UX

**Phase 8: Deployment (Week 4)**
* Pre-deployment checklist
* Deploy to production
* Monitor for issues
* Gather user feedback
* Document lessons learned

---

# Future enhancements

Not included in this PRD but potential future additions:

* Export analytics as PDF report
* Share analytics via unique URL
* Compare performance across multiple time periods
* Head-to-head comparison against specific opponents
* Advanced opening tree visualization
* Game replay with critical moments highlighting mistakes
* Move-by-move accuracy analysis with interactive board
* Performance correlation analysis (rating vs time control, etc.)
* Email notifications for milestone achievements
* Social features (compare with friends)
* Integration with other chess platforms (Lichess, Chess24)
* AI-powered opening recommendations based on playing style
* Deeper engine analysis (depth 20+) for premium users
* Video lessons recommendations based on weaknesses
* Progress tracking over multiple months with trend analysis

---

**Document Version:** 2.9  
**Created:** December 5, 2025  
**Last Updated:** February 20, 2026  
**Author:** PRD Agent  
**Status:** Updated with Google Tag Manager integration for visitor tracking

---

## Changelog

**Version 2.9 (February 20, 2026):**
* **New Feature:** Google Tag Manager (GTM) integration for website analytics
* **GTM Container ID:** GT-NFBTKHBS
* **GA4 Measurement ID:** G-VMYYSZC29R
* **Implementation:** Added GTM script tags to both `index.html` and `analytics.html` templates
* **User Story:** Added EA-020 for website analytics tracking
* **Tracking:** Page views, user sessions, traffic sources, and engagement metrics
* **Privacy:** No PII tracking, respects DNT settings
* **Impact:** Frontend-only changes, no backend modifications required
* Created iteration_10_summary.md document

**Version 2.8 (February 20, 2026):**
* **Section 10 (AI Chess Advisor):** Removed overall recommendation section
* **Simplified UI:** Display only 9 section-specific recommendations (1-2 bullets each)
* **Token optimization:** Reduced prompt complexity while maintaining comprehensive guidance
* Updated acceptance criteria to remove overall recommendation requirement
* Created iteration_9_summary.md document

**Version 2.7 (February 20, 2026):**
* **Section 9 (Move Analysis):** Added "Number of games" row to table display
* **Section 10 (AI Chess Advisor):** Restored section-specific recommendations with concise bullet format
* **Enhanced structure:** Display 9 section-specific recommendations (1-2 bullets each) + overall recommendation
* **Token adjustment:** Increased max_tokens from 300 to 600 to accommodate section guidance
* Updated acceptance criteria for both sections
* Created iteration_8_summary.md document

**Version 2.6 (February 20, 2026):**
* **Section 9 (Move Analysis):** Simplified table layout, reordered columns (Mistake | Neutral | Brilliant)
* **Section 10 (AI Chess Advisor):** Simplified to display only overall recommendation (removed section-specific)
* **Token optimization:** Reduced max_tokens from 500 to 300
* **UI simplification:** Removed token usage and cost display from frontend
* Updated acceptance criteria and test cases
* Created iteration_7_summary.md document

**Version 2.5 (February 19, 2026):**
* **Section 6 (Opening Performance):** Simplified to Top 5 openings (was Top 10)
* **Section 9:** Renamed "Mistake Analysis" to "Move Analysis by Game Stage"
* **Section 9:** Enhanced to track Brilliant/Neutral/Mistake moves (was only tracking mistake types)
* **Section 10 (AI Chess Advisor):** Re-enabled AI advice section in frontend
* Updated acceptance criteria and test cases
* Created iteration_6_summary.md document

**Version 2.4 (February 19, 2026):**
* **Section 9 (Mistake Analysis):** Added asynchronous background processing for Stockfish analysis
* **New API endpoint:** `/api/analyze/mistake-status/<task_id>` for polling analysis status
* **UX improvement:** Users can view all other analytics immediately (5-10s) while mistake analysis runs in background (30-60s)
* **Technical approach:** Background threading with in-memory task storage and 1-hour TTL
* Updated acceptance criteria for async functionality
* Added frontend polling requirements

**Version 2.3 (February 18, 2026):**
* **Enhanced Section 2 (Color Performance):** Added W/L/D counts to summary cards in addition to total games and win rate
* **Simplified Sections 4 & 5 (Termination Types):** Changed pie charts to show numbers only (no category labels), hidden legend for cleaner design
* **Enhanced Section 6 (Opening Performance):** 
  - Added display of first 6 full moves in standard notation
  - Added Lichess board editor URL for position visualization
  - Added Chess.com example game URL for each opening
  - Separated White and Black openings into distinct sections
* **Refined Section 9 (Mistake Analysis):** Implemented dynamic sampling logic based on dataset size:
  - <50 games: Analyze ALL games (comprehensive analysis)
  - ≥50 games: Use 20% sampling (min 10, max 50 games)
* Updated test cases TC-016, TC-017, TC-018, TC-021 (and sub-tests) to reflect new requirements
* Updated acceptance criteria across affected sections
* Created iteration_5_summary.md document

**Version 2.2 (December 31, 2025):**
* **Global Change:** Added maximum 30-day date range restriction for performance
* **Section 6 (Opening Performance):** Complete redesign from best/worst to frequency-based (Top 10 Most Common)
* **Section 9 (Mistake Analysis):** Added intelligent 20% sampling strategy with min/max bounds
* Updated test cases and acceptance criteria
* Created iteration_4_summary.md document

**Version 2.1 (December 26, 2025):**
* Updated Section 6: Changed "Top 5" to dynamic "Top Best/Worst" openings display
* Updated Section 6: Added chess move notation (first 6 moves) and interactive board display
* Updated Section 8: Added explicit timezone conversion verification requirements
* Updated Section 9: Refined critical mistake game link criteria (lost by resignation, significant CP drop)
* Updated Section 10: Restructured to require EXACTLY 9 section-specific recommendations + 1 overall
* Updated Section 10: Integrated YouTube video recommendations for opening learning
* Added video source prioritization: ChessNetwork > GMHikaru > GothamChess > Chessbrahs
* Updated test cases to verify new requirements
* Updated acceptance criteria across multiple sections

**Version 2.0 (December 12, 2025):**
* Added Milestone 8: Game Stage Mistake Analysis (Section 9)
* Added Milestone 9: AI-Powered Chess Advisor (Section 10)
* Integrated Stockfish engine for move analysis
* Integrated OpenAI GPT-4 API for personalized coaching
* Added 10 new E2E test cases (TC-021 through TC-030)
* Updated system architecture diagram
* Updated tech stack with AI/ML dependencies
* Updated success metrics and acceptance criteria
* Total sections: 10 (previously 8)
* Total test cases: 30 (previously 20)

**Version 1.0 (December 5, 2025):**
* Initial PRD with 8 analytics sections
* 7 milestones defined
* Complete technical specifications
* 20 E2E test cases
