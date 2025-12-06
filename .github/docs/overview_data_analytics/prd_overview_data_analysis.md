# PRD: Enhanced Chess Analytics Dashboard

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
* Validate date range (max 1 year to prevent excessive API calls)
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

* Add timezone detection and selector
* Enhance date picker for better UX
* Add preset date ranges (Last 7 days, Last 30 days, Last 3 months, etc.)
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

**User story:** As a chess player, I want to see which openings I perform best and worst with so I can focus on improving weak openings or exploiting strong ones.

**Implementation:**
* Parse PGN data to extract opening moves (first 5-10 moves)
* Identify opening names using chess opening database/library
* Calculate win rate for each opening (minimum 3 games threshold)
* Display two lists:
  * Top 5 best performing openings (highest win rate)
  * Top 5 worst performing openings (lowest win rate)
* Show: Opening name, games played, wins, losses, draws, win rate
* Horizontal bar chart for visual comparison

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
* Handle openings played fewer than 3 times separately

**Acceptance criteria:**
- [x] PGN data is parsed correctly for each game
- [x] Opening names extracted using Lichess Opening Database
- [x] Opening names displayed without ECO codes (human-readable names only)
- [x] Unknown openings labeled as "Unknown Opening"
- [x] Less than 15% of games categorized as "Unknown Opening"
- [x] Win rates are calculated correctly (wins / total games)
- [x] Only openings with 3+ games are included in rankings
- [x] Top 5 best and worst openings are displayed
- [x] Visual representation (bar chart) is clear
- [x] Games played count is shown for each opening

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
- [x] Game timestamps are converted to user's timezone
- [x] Games are categorized correctly into time periods
- [x] Win rates are calculated for each time period
- [x] Three card grid layout displays data clearly (no bar chart)
- [x] Each card shows: games played, W/L/D counts, win rate %
- [x] Game distribution (how many games in each period) is visible
- [x] User can see their best and worst performing times
- [x] Timezone is displayed clearly to user
- [x] Handles edge cases (games exactly at boundary times)

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

**Implementation:**
* Single Chart.js line chart with two datasets:
  * Line 1: White win rate % (color: white/light gray)
  * Line 2: Black win rate % (color: dark gray/black)
* Two summary cards displayed above chart:
  * White Summary Card: Total games, Win rate %
  * Black Summary Card: Total games, Win rate %
* Tooltips show per-color details: Date, Win Rate %, Wins, Losses, Draws
* Legend clearly distinguishes White vs Black lines

**Acceptance criteria:**
- [ ] Single chart displays two lines (White and Black win rates)
- [ ] Two separate summary cards positioned above chart
- [ ] White summary card shows: total games played as White, win rate %
- [ ] Black summary card shows: total games played as Black, win rate %
- [ ] Chart legend clearly labels White and Black lines
- [ ] Tooltips show color-specific data on hover
- [ ] Visual distinction between White and Black lines is clear
- [ ] Responsive design for mobile devices

---

### Section 4 & 5: Enhanced Termination Type Visualization

**Requirement ID:** EA-015

**User story:** As a chess player, I want to see immediately how many games I won/lost by each termination type without needing to hover.

**Changes from original implementation:**
* Display count labels directly inside pie chart segments
* Reduce need for tooltip interaction
* Improve at-a-glance readability

**Implementation:**
* Chart.js datalabels plugin configuration
* Show counts inside each segment (e.g., "Checkmate: 25")
* Percentages remain in legend or tooltip
* Ensure text is readable on all segment sizes
* Apply to both winning (Section 4) and losing (Section 5) charts

**Acceptance criteria:**
- [ ] Count labels displayed inside pie segments (e.g., "Checkmate: 25")
- [ ] Labels are readable on all segment sizes
- [ ] Percentages available in legend or tooltip
- [ ] Both winning and losing charts use same label format
- [ ] Labels don't overlap or obscure chart
- [ ] Responsive design maintains label readability

---

### Section 6: Opening Names Enhancement

**Requirement ID:** EA-016

**User story:** As a chess player, I want to see familiar opening names (like "Sicilian Defense") instead of ECO codes, so I can immediately recognize the openings.

**Changes from original implementation:**
* Display human-readable opening names only (no ECO codes)
* Integrate with comprehensive opening database
* Minimize "Unknown Opening" classifications

**Implementation:**
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
* Display opening names in bar chart and tables
* Never show ECO codes in UI

**Technical implementation:**
```python
from chess_openings import get_opening_name
import chess.pgn

def identify_opening(pgn_string):
    """Identify opening name from PGN using Lichess database."""
    game = chess.pgn.read_game(StringIO(pgn_string))
    board = game.board()
    moves = []
    
    # Extract up to 10 moves
    for move in list(game.mainline_moves())[:10]:
        moves.append(move.uci())
        board.push(move)
    
    # Try matching with decreasing move counts
    for move_count in [10, 8, 6, 5, 4, 3]:
        opening = get_opening_name(moves[:move_count])
        if opening:
            return opening
    
    return "Unknown Opening"
```

**Acceptance criteria:**
- [x] Lichess Opening Database integrated into backend (pattern-based identification)
- [x] Opening names displayed without ECO codes
- [x] Less than 15% of games categorized as "Unknown Opening" (comprehensive pattern matching)
- [x] Opening names are human-readable (e.g., "Sicilian Defense")
- [x] Fallback algorithm tries shorter move sequences
- [x] Top 5 best and worst openings show proper names
- [x] Bar charts and tables display opening names correctly
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

**TC-016: Unified color performance chart**
* Complete analysis workflow
* Verify Section 2 shows single chart with two lines
* Verify two summary cards displayed above chart
* Verify White summary card shows total games and win rate
* Verify Black summary card shows total games and win rate
* Hover over lines, verify color-specific tooltips

**TC-017: Pie chart count labels**
* Complete analysis workflow
* Verify Section 4 pie chart shows count labels inside segments
* Verify Section 5 pie chart shows count labels inside segments
* Verify labels are readable on all segment sizes
* Verify format is "Category: Count" (e.g., "Checkmate: 25")

**TC-018: Opening names display**
* Complete analysis workflow
* Verify Section 6 shows human-readable opening names
* Verify no ECO codes are displayed
* Verify "Unknown Opening" count is less than 15% of total games
* Verify top 5 best and worst openings have proper names

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

# Tech stack

**Backend**

* Flask (existing)
* Python 3.12
* Chess.com Public API
* `python-chess` library for PGN parsing
* `requests` for API calls
* `pytz` or `zoneinfo` for timezone handling
* SQLAlchemy (optional, for caching)
* Custom caching utilities (existing)

**Frontend**

* Vanilla JavaScript (ES6+)
* Chart.js 4.x for all visualizations
* HTML5 / CSS3
* Fetch API for asynchronous requests
* Intl API for timezone detection

**Testing**

* Playwright for E2E testing
* unittest/pytest for backend unit tests
* Test with real user data (username: 'jay_fh')

**Development tools**

* uv for package management
* Git for version control
* GitHub for repository hosting

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
[Statistics Calculator]
    ↓
[Cache Layer] (optional)
    ↓
JSON Response
    ↓
[Chart.js Visualizations]
    ↓
User sees comprehensive analytics
```

**Data flow:**

1. User enters username, date range on frontend
2. JavaScript detects user's timezone
3. Frontend sends request to `/api/analyze/detailed`
4. Backend validates inputs
5. Backend fetches games from Chess.com API
6. Backend parses PGN data for openings
7. Backend calculates all 8 analytics sections
8. Backend converts timestamps to user timezone
9. Backend returns comprehensive JSON response
10. Frontend renders 8 analytics sections with Chart.js
11. User scrolls through single-page dashboard

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
* All 8 analytics sections render correctly with accurate data
* Timezone conversion works correctly across all time zones
* PGN parsing successfully extracts opening names (>95% success rate)
* API response time < 5 seconds for 3-month analysis
* Zero critical bugs in production for statistical calculations
* All Playwright E2E tests pass

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
- [ ] Analysis completes within 6 seconds for 3-month range
- [ ] Caching reduces redundant API calls
- [ ] Loading states indicate progress
- [ ] No UI lag when scrolling dashboard
- [ ] Charts render smoothly

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
* Game replay with critical moments
* Move-by-move accuracy analysis
* Blunder detection and categorization
* Performance correlation analysis (rating vs time control, etc.)
* Email notifications for milestone achievements
* Social features (compare with friends)
* Integration with other chess platforms (Lichess, Chess24)

---

**Document Version:** 1.0  
**Created:** December 5, 2025  
**Author:** PRD Agent  
**Status:** Ready for Review
