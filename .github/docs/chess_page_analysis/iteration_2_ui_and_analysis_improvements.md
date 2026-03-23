# Deep Check Analysis — Iteration 2: UI and analysis improvements

**Version:** 2.0
**Date:** March 22, 2026
**Parent PRD:** `prd_chess_page_analysis.md`
**Scope:** 5 changes — piece image fix, single-column layout with AI summary, evaluation chart, 20-game limit, clock time display

---

## Change summary

| # | Change | Category | Milestone impact |
|---|---|---|---|
| 1 | Fix chessboard piece images not rendering | Bug fix | M2 |
| 2 | Single-column layout + AI game summary + game timestamp | UI redesign + new feature | M2, M3 |
| 3 | Lichess-style evaluation chart (Y=eval, X=moves) | UI enhancement | M2 |
| 4 | Increase max games from 4 to 20 (full evaluation) | Backend + UI | M1, M2 |
| 5 | Parse and display remaining clock time per move with time-usage chart | New feature | M1, M2 |

---

## Change 1: Fix chessboard piece images not rendering

### Problem

Some chess pieces do not render on the board. The current `pieceTheme` URL (`https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/img/chesspieces/wikipedia/{piece}.png`) intermittently fails to load certain piece images. This is visible on the board where squares that should have pieces appear empty.

### Root cause

The unpkg CDN sometimes returns 404 or stale cache for individual piece image files. The `{piece}` placeholder in chessboard.js expects filenames like `wK.png`, `bQ.png`, etc. — some of these may fail to load from unpkg without error handling or a fallback.

### Solution

- Switch piece image source to the **cdnjs** or **jsdelivr** CDN which has more reliable caching
- Add an `onerror` fallback on piece images to retry from an alternative CDN
- Alternatively, use inline SVG piece definitions which eliminate external image dependencies entirely

### Acceptance criteria

- [ ] All 12 piece types (wK, wQ, wR, wB, wN, wP, bK, bQ, bR, bB, bN, bP) render correctly on all boards
- [ ] Pieces render on page load without requiring manual refresh
- [ ] Fallback mechanism ensures pieces still render if primary CDN fails
- [ ] Verified on Chrome, Firefox, and Edge

### Files affected

| File | Change |
|---|---|
| `static/js/deep_analysis.js` | Update `pieceTheme` URL and add fallback logic |
| `templates/deep_analysis.html` | Optional: preload piece images in `<head>` |

---

## Change 2: Single-column layout with AI game summary and game timestamp

### Problem

The current 2×2 grid makes each board too small to read comfortably. The user wants a single-column layout (1 game per row) with richer context: an AI-generated narrative summary and the game timestamp.

### Solution — Layout

- Change the board grid from 2 columns to **1 column** (full-width cards)
- Each game card takes the full viewport width, allowing larger boards and more readable move lists
- Users scroll vertically to view all games
- Responsive breakpoints:
  - **Desktop (≥1200px):** Single column, board + move list side by side within the card
  - **Tablet (768–1199px):** Single column, same layout scaled down
  - **Mobile (<768px):** Single column, move list below board

### Solution — AI game summary

- After the deep analysis backend completes evaluation for each game, send the move-by-move evaluation data to the **OpenAI API** (using existing `chess_advisor_service.py` pattern) to generate a **3–5 sentence narrative summary** of the game
- The summary should describe:
  - The overall flow of the game (who was winning and when it changed)
  - What the critical mistake was and what the best move would have been
  - The consequence of the mistake (material loss, positional collapse, etc.)
- The summary should **NOT** include improvement tips or practice suggestions
- Use `gpt-4o-mini` model for cost efficiency (consistent with existing AI advisor)
- Display the summary in a dedicated section within each game card, below the game info header

**Prompt template (per game):**

```
You are a chess analyst. Summarize this game in 3-5 sentences for a player reviewing their loss.
Describe the flow of the game, the critical mistake, and its consequence. Do not give improvement tips.

Player: {username} ({player_color}, {player_rating})
Opponent: {opponent_username} ({opponent_rating})
Result: {result}
Time control: {time_control}
Critical mistake: Move {critical_move_number} ({critical_move_stage}) - played {played_move} instead of {best_move}
CPL at critical move: {critical_cpl}
Key evaluation changes: {eval_summary}
```

**Response format:** Plain text, 3–5 sentences.

### Solution — Game timestamp

- Extract `end_time` from the Chess.com game data (Unix timestamp, already available in game metadata)
- Display the date and time the game was played (formatted in user's timezone if available, otherwise UTC)
- Show in the game info header line: e.g., "Played on Mar 18, 2026 at 3:45 PM"

### User stories affected

| ID | Story | Change |
|---|---|---|
| DCA-005 | 2×2 multi-board grid layout | Changed to single-column layout |
| NEW: DCA-015 | AI game summary | New user story |
| NEW: DCA-016 | Game timestamp display | New user story |

### DCA-015: AI-generated game summary

**User story:** As a chess player reviewing my lost games, I want to see a short narrative summary of each game so I can quickly understand what happened without stepping through every move.

**Acceptance criteria:**
- [ ] Each game card displays a 3–5 sentence AI-generated summary below the game info header
- [ ] Summary describes the game flow, the critical mistake, and its consequence
- [ ] Summary does NOT include improvement tips or practice suggestions
- [ ] Summary is generated using OpenAI `gpt-4o-mini` model
- [ ] Summary loads after game evaluation completes (can show "Generating summary..." while loading)
- [ ] If OpenAI API is unavailable, show the existing short summary line as fallback (no crash)
- [ ] Summary uses plain, conversational English appropriate for all skill levels

### DCA-016: Game timestamp display

**User story:** As a chess player, I want to see when each game was played so I can correlate my performance with specific times or sessions.

**Acceptance criteria:**
- [ ] Each game card shows the date and time the game was played
- [ ] Format: "Played on Mar 18, 2026 at 3:45 PM" (or similar readable format)
- [ ] Timestamp derived from `end_time` field in Chess.com API response
- [ ] Displayed in the game info header area

### Files affected

| File | Change |
|---|---|
| `static/css/deep_analysis.css` | Change grid to single-column, add summary section styles |
| `static/js/deep_analysis.js` | Update `createGameCard()`, add AI summary rendering, add timestamp |
| `app/routes/api.py` | Add game summary generation call to OpenAI after evaluation |
| `app/services/deep_analysis_service.py` | Include `end_time` and summary prompt data in game results |
| `config.py` | Reuse existing `OPENAI_API_KEY`, `OPENAI_MODEL` settings |

---

## Change 3: Lichess-style evaluation chart

### Problem

The current evaluation chart is a small Chart.js line chart (~300×80px) below each board. The user wants a more prominent **Lichess/Chess.com-style** evaluation chart where:
- **Y-axis** = evaluation (in pawns, clamped ±10)
- **X-axis** = move number (sequential)
- The chart clearly shows the ebb and flow of the position across the entire game

### Solution

- Replace the current mini eval chart with a **larger, more prominent evaluation chart** inside each game card
- Chart dimensions: full card width × ~120px height
- **Visual style:**
  - Area chart (filled) — white area below the zero line, dark area above (from black's perspective)
  - Or: line chart with green fill for white advantage, red fill for black advantage
  - Critical mistake position marked with a prominent **red vertical line or dot**
  - Current move position marked with a **vertical indicator line**
- **Interactivity:**
  - Clicking on any point in the chart jumps the board to that move
  - Hovering shows tooltip with move number and evaluation
- Place the chart **below the board area** (above the navigation controls) for visual prominence

### Acceptance criteria

- [ ] Evaluation chart spans the full width of the game card
- [ ] Y-axis shows evaluation in pawns (±10 range, clamped)
- [ ] X-axis shows move numbers
- [ ] Chart uses filled area style (white/dark regions) similar to Lichess
- [ ] Critical mistake is marked with a red indicator on the chart
- [ ] Current move position has a vertical indicator line
- [ ] Clicking the chart jumps the board to that move
- [ ] Chart is at least 120px tall for readability
- [ ] Chart renders for all games (1–20)

### Files affected

| File | Change |
|---|---|
| `static/js/deep_analysis.js` | Rewrite `renderEvalChart()` to Lichess-style area chart |
| `static/css/deep_analysis.css` | Update chart wrapper dimensions and styles |

---

## Change 4: Increase max games from 4 to 20

### Problem

The current implementation analyzes only 4 games. The user wants to analyze up to **20 lost games** with full move-by-move evaluation.

### Solution

- Change `DEEP_ANALYSIS_MAX_GAMES` default from `4` to `20`
- Update the `max_games` parameter in `DeepAnalysisService.__init__()` default
- The backend will continue to use full Stockfish evaluation per game (not strategic sampling)
- Since 20 games × full evaluation takes significantly longer (~60–120 seconds):
  - Use progressive delivery: frontend renders each game card as soon as its evaluation completes
  - Loading skeleton shows for games still being analyzed
  - Progress indicator: "Analyzing game 5 of 20..."
- Users scroll vertically to view all 20 game cards

### Performance considerations

- 20 games × ~5 seconds per game = ~100 seconds total on 1 vCPU
- Progressive delivery ensures usable content appears within 5–10 seconds
- Background task already supports progress polling (existing `task_manager` pattern)
- Evaluation caching prevents re-analysis on page refresh

### Acceptance criteria

- [ ] Up to 20 qualifying lost games are analyzed (sorted by critical CPL descending)
- [ ] Game cards render progressively as each game evaluation completes
- [ ] Progress indicator shows "Analyzing game N of 20..."
- [ ] Loading skeleton shown for games not yet ready
- [ ] Scrollable page layout accommodates all 20 games
- [ ] If fewer than 20 qualifying games, show all available
- [ ] Config value `DEEP_ANALYSIS_MAX_GAMES` updated to 20

### Files affected

| File | Change |
|---|---|
| `config.py` | Change `DEEP_ANALYSIS_MAX_GAMES` default to `20` |
| `app/services/deep_analysis_service.py` | Update `max_games` default to `20` |
| `app/routes/api.py` | No change needed (already uses config value) |
| `static/js/deep_analysis.js` | Update progress messaging, handle 20 card rendering |

---

## Change 5: Parse and display remaining clock time per move

### Problem

The user wants to see how much time was remaining on each player's clock at every move, and visualize time usage patterns.

### Solution — Clock data parsing

- Chess.com PGN includes clock annotations in the format: `1. e4 {[%clk 0:09:58]} 1... e5 {[%clk 0:09:56]}`
- Parse the `%clk` annotation from each move's comment in the PGN using `python-chess`'s `node.comment` field
- Extract hours:minutes:seconds and convert to total seconds remaining
- Include `clock_time` (seconds remaining) in each move's data returned by the API

### Solution — Clock display in move list

- Show the remaining clock time next to each move in the move list: e.g., `e4 (9:58)`
- Use a subtle, smaller font for the clock time to avoid cluttering the move list
- Color code time pressure: when remaining time drops below 30 seconds, show in red/orange

### Solution — Time-usage chart

- Add a **time-usage bar chart** or **step chart** below the evaluation chart
- **X-axis:** Move number
- **Y-axis:** Time remaining (in seconds) for both players
- Two lines/bars: one for white, one for black
- This shows at a glance where each player spent the most time (steep drops = long thinks) and when time pressure began
- Chart dimensions: full card width × ~80px height
- Clicking on the chart jumps the board to that move (same as eval chart)

### User stories

### DCA-017: Clock time display per move

**User story:** As a chess player, I want to see the remaining clock time for each move so I can understand how time pressure affected my decisions.

**Acceptance criteria:**
- [ ] Each move in the move list shows remaining clock time (e.g., "e4 (9:58)")
- [ ] Clock time parsed from `%clk` annotation in Chess.com PGN
- [ ] Time shown in `M:SS` or `H:MM:SS` format depending on game duration
- [ ] Moves with less than 30 seconds remaining are highlighted in red/orange
- [ ] If PGN does not contain clock data, gracefully omit (no error)

### DCA-018: Time-usage chart

**User story:** As a chess player, I want to see a visual chart of time usage throughout the game so I can identify where I spent too much or too little time and when time pressure started.

**Acceptance criteria:**
- [ ] Time-usage chart displayed below the evaluation chart for each game
- [ ] Chart shows remaining time for both white and black across all moves
- [ ] White line/bar in white/light color, black line/bar in dark color
- [ ] Steep drops in the chart indicate long thinking (easy to spot visually)
- [ ] Time below 30 seconds highlighted/colored differently (time pressure zone)
- [ ] Clicking on the chart jumps the board to that move
- [ ] Chart dimensions: full card width × ~80px height
- [ ] If no clock data available, chart section is hidden (not shown empty)

### Files affected

| File | Change |
|---|---|
| `app/services/deep_analysis_service.py` | Parse `%clk` from PGN comments, add `clock_time` to move data |
| `static/js/deep_analysis.js` | Display clock in move list, render time-usage chart |
| `static/css/deep_analysis.css` | Style clock time display and time chart |

---

## Updated game card layout (single column, desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ Game 1: jay_fh (1942) vs natali123 (2028)                                       │
│ Lost by checkmate • Critical mistake at move 38 (endgame)                        │
│ Played on Mar 18, 2026 at 3:45 PM                                               │
│                                                                                  │
│ ┌──────────────────────────────────────────────────────────────────────────────┐ │
│ │ AI Summary: You held a slight advantage through the middle game but started │ │
│ │ losing ground after move 30. The critical blunder came on move 38 where you │ │
│ │ played Qxg5 instead of Rd7, allowing your opponent to force a checkmate     │ │
│ │ sequence. After Qxg5, your king was exposed with no defensive resources.    │ │
│ └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌────┐ ┌──────────────────────┐ ┌───────────────────────────────────────────┐  │
│  │Eval│ │                      │ │ Move List                                 │  │
│  │Bar │ │                      │ │ 1. d4 (9:58)    d5 (9:56)                │  │
│  │    │ │     Chess Board      │ │ 2. e3 (9:45)    Nc6 (9:50)              │  │
│  │+1.2│ │     (larger size)    │ │ 3. c4! (9:30)   e6 (9:44)              │  │
│  │    │ │                      │ │ 4. Nc3 (9:20)   Nf6 (9:38)             │  │
│  │    │ │                      │ │ ...                                      │  │
│  └────┘ └──────────────────────┘ └───────────────────────────────────────────┘  │
│                                                                                  │
│  Best: Rd7 (you played Qxg5??)                                                  │
│  ⏮  ◀  ▶  ⏭  ⏩ Mistake  |  Back to Game                                     │
│                                                                                  │
│  ┌──────────────────── Evaluation Chart ─────────────────────────────────────┐  │
│  │  +5 ┃                 ╱╲                                                  │  │
│  │   0 ┃────────────────╱──╲───────────╲──────── (move numbers) ──────────── │  │
│  │  -5 ┃                     ╲          ╲  ●(critical mistake)               │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌──────────────────── Time Usage Chart ─────────────────────────────────────┐  │
│  │  10m ┃──  White ──  Black                                                 │  │
│  │   5m ┃   ╲    ╲                                                           │  │
│  │   0m ┃─────────────────────────────────── (move numbers) ──────────────── │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

(scroll down for games 2–20)
```

---

## API response changes

### Updated `POST /api/deep-analysis` response per game object

New fields added to each game in the response:

```json
{
  "end_time": 1710784234,
  "ai_summary": "You held a slight advantage through the middle game...",
  "moves": [
    {
      "move_number": 1,
      "color": "white",
      "san": "e4",
      "clock_time": 598,
      ...existing fields...
    }
  ]
}
```

| New field | Type | Description |
|---|---|---|
| `end_time` | integer | Unix timestamp when the game ended (from Chess.com API) |
| `ai_summary` | string | 3–5 sentence AI-generated narrative summary of the game |
| `moves[].clock_time` | integer or null | Remaining clock time in seconds at this move (from `%clk`), null if not available |

---

## Testing strategy for iteration 2

### Unit tests

| Test | Description |
|---|---|
| test_clock_parsing | Verify `%clk` annotations are correctly parsed from PGN comments |
| test_clock_missing | Verify graceful handling when PGN has no clock data |
| test_ai_summary_prompt | Verify prompt includes correct game data (player, move, CPL) |
| test_ai_summary_fallback | Verify fallback text when OpenAI API is unavailable |
| test_max_games_20 | Verify up to 20 games are selected and evaluated |
| test_game_timestamp | Verify `end_time` is included in game results |

### Frontend verification

| Test | Description |
|---|---|
| Piece rendering | All 12 piece types render on all boards |
| Single-column layout | Cards display in single column at all viewports |
| AI summary display | Summary text visible below game header |
| Eval chart | Lichess-style area chart renders with click-to-navigate |
| Clock display | Clock time shown next to moves, red highlight under 30s |
| Time chart | Time-usage chart renders with dual lines (white/black) |
| 20 games scroll | Page scrolls smoothly through 20 game cards |
| Progressive loading | Games appear one by one as evaluation completes |

### E2E tests (Playwright)

| Test ID | Description |
|---|---|
| DCA-E2E-018 | Verify all piece images load on every board |
| DCA-E2E-019 | Verify single-column layout on desktop |
| DCA-E2E-020 | Verify AI summary section renders with text |
| DCA-E2E-021 | Verify game timestamp is displayed |
| DCA-E2E-022 | Verify eval chart is Lichess-style with click interaction |
| DCA-E2E-023 | Verify clock time appears in move list |
| DCA-E2E-024 | Verify time-usage chart renders |
| DCA-E2E-025 | Verify scrolling through up to 20 games |

---

## Implementation order

1. **Fix piece images** (Change 1) — quick fix, unblocks all other visual testing
2. **Single-column layout + timestamp** (Change 2 partial) — layout restructure first
3. **Clock time parsing** (Change 5 backend) — data pipeline change
4. **20 games** (Change 4) — config + backend change
5. **Evaluation chart redesign** (Change 3) — frontend chart rewrite
6. **Time-usage chart** (Change 5 frontend) — additional chart
7. **AI game summary** (Change 2 partial) — requires OpenAI API call, add last to avoid slowing development

---
