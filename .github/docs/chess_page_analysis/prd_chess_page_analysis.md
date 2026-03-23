# PRD: Deep Check Analysis — Multi-Board Game Review (v2.0)

## Project overview

This project adds a new "Deep Check Analysis" feature to the Chess Analytics website that enables users to review and learn from their lost games through an interactive analysis page. After entering their Chess.com username on the main analytics page, users click a "Deep Check Analysis" button to be redirected to a dedicated page displaying up to **20 lost games** in a scrollable single-column layout with interactive chessboards.

The system intelligently selects games where the player lost due to errors in the **middle game or endgame** (not opening blunders), presenting each board at the critical position where the player's biggest mistake occurred. Each board includes a full evaluation bar, move list panel with clock times, best move suggestions, an **AI-generated game summary**, a **Lichess-style evaluation chart**, a **time-usage chart**, and the ability for the player to deviate from the moves they played and explore alternative lines with real-time evaluation.

This feature bridges the gap between passive analytics (seeing statistics) and active learning (understanding what went wrong and practicing correct play). By showing up to 20 games in a scrollable layout, players can thoroughly review their losses and identify recurring mistake patterns.

**Skills required:**

* Python (Flask)
* Chess.com API integration (existing)
* python-chess library (PGN parsing, FEN handling, move validation, `%clk` parsing)
* Stockfish UCI protocol (server-side evaluation)
* OpenAI API (`gpt-4o-mini`) for AI game summaries
* chessboard.js v1.0 (board rendering, drag-and-drop)
* chess.js v1.0 (client-side move validation, game state management)
* JavaScript (ES6+) / AJAX / WebSocket or polling
* HTML5/CSS3 (responsive single-column layout)
* Chart.js (evaluation chart + time-usage chart)
* Playwright for E2E testing

---

# PRD change history

## Iteration 1 — March 20, 2026

**Version:** 1.0
**Focus:** Initial PRD creation for Deep Check Analysis feature

### Changes summary
- Initial PRD document created
- Defined 4 milestones for phased delivery
- 14 user stories (DCA-001 through DCA-014)
- Technical architecture and engine recommendation documented
- Testing strategy defined

## Iteration 2 — March 22, 2026

**Version:** 2.0
**Focus:** UI improvements, AI game summary, evaluation chart, 20-game limit, clock time display
**Iteration document:** `iteration_2_ui_and_analysis_improvements.md`

### Changes summary
- **Bug fix:** Chessboard piece images not rendering on some boards — switch CDN and add fallback
- **Layout:** Changed from 2×2 grid to single-column layout (1 game per row, up to 20 games)
- **AI summary:** Added ChatGPT-generated 3–5 sentence narrative summary per game (DCA-015)
- **Game timestamp:** Added display of when each game was played (DCA-016)
- **Eval chart:** Redesigned to Lichess-style area chart (full-width, Y=eval, X=moves)
- **Max games:** Increased from 4 to 20 with progressive loading
- **Clock time:** Parse `%clk` from PGN, display in move list, add time-usage chart (DCA-017, DCA-018)
- Updated DCA-002, DCA-003, DCA-004, DCA-005, DCA-010, DCA-013, DCA-014 acceptance criteria
- Added 4 new user stories: DCA-015, DCA-016, DCA-017, DCA-018
- Added 8 new E2E tests: DCA-E2E-018 through DCA-E2E-025

---

# Key features

## Milestone 1: Game selection engine and API

**Goal:** Build the backend logic that fetches the user's games, identifies lost games with middle/endgame errors, and returns the top **20** candidates with full analysis data (PGN, critical positions, evaluations, best moves, clock times, AI summaries).

### Game fetching and filtering

* Reuse existing `ChessService.get_games_by_month()` and `ChessService.analyze_games()` to fetch games by date range
* Filter for the user's **most played time control** (e.g., if user plays 60% Blitz, select Blitz games only)
  * Determine most common time control by counting games per `time_class` field from Chess.com API
  * Time control categories: `bullet`, `blitz`, `rapid`, `daily`
* Filter for **lost games only** (user's result is `"lose"` / result codes: `checkmated`, `timeout`, `resigned`, `abandoned`)
* Exclude games shorter than 15 total moves (too short to have meaningful middle/endgame content)

### Middle/endgame error detection

* Use existing game stage definitions from `MistakeAnalysisService`:
  * **Early game (opening):** Moves 1–7 per player
  * **Middle game:** Moves 8–20 per player
  * **Endgame:** Moves 21+ per player
* For each lost game, run Stockfish evaluation on all player moves in the middle and endgame stages
* Identify the **critical mistake**: the single move with the largest centipawn loss (CPL) in the middle or endgame
* **Selection criteria for the top 20 games:**
  * Must have at least 1 mistake (CPL ≥ 100) in middle or endgame stage
  * Sort all qualifying games by the magnitude of their biggest middle/endgame mistake (largest CPL first)
  * Select the top 20 games with the largest critical mistakes
  * If fewer than 20 qualifying games exist, show as many as available (1–19 boards)

### Full game evaluation

* For each of the up to 20 selected games, run **complete Stockfish evaluation** on every move (not just sampled moves):
  * Evaluate the position **before** and **after** each player move
  * Calculate centipawn loss per move
  * Identify the **best move** at each position (top 1 principal variation from Stockfish)
  * Store: move SAN, move UCI, FEN before, FEN after, eval before (cp), eval after (cp), best move UCI, best move SAN, CPL, **clock_time** (seconds remaining)
* **Clock time parsing:** Extract `%clk` annotations from PGN move comments (format: `{[%clk H:MM:SS]}`). Store as total seconds remaining. If PGN has no clock data, `clock_time` is `null`.
* Use node-limited search (`ENGINE_NODES=50000`) for server-side batch evaluation (consistent with existing Iteration 12 settings)
* Cache evaluation results per game URL to avoid re-analysis on page refresh

### AI game summary generation

* After completing full evaluation of each game, generate a **3–5 sentence narrative summary** using OpenAI `gpt-4o-mini` (consistent with existing `chess_advisor_service.py` pattern)
* Summary describes:
  * The overall flow of the game (who was winning and when advantage changed)
  * What the critical mistake was and what the best move would have been
  * The consequence of the mistake (material loss, positional collapse, etc.)
* Summary does **NOT** include improvement tips or practice suggestions
* If OpenAI API is unavailable or key not set, fall back to the existing short summary line (no crash)
* Store `ai_summary` string in the game result object

### API endpoint

* **New endpoint:** `POST /api/deep-analysis`
* **Request body:**
  ```json
  {
    "username": "chess_com_username",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
  }
  ```
* **Response structure:**
  ```json
  {
    "username": "username",
    "time_control": "blitz",
    "games_analyzed": 25,
    "games_qualifying": 8,
    "games": [
      {
        "game_url": "https://www.chess.com/game/live/...",
        "white": { "username": "...", "rating": 1200 },
        "black": { "username": "...", "rating": 1250 },
        "player_color": "white",
        "result": "checkmated",
        "time_control": "600",
        "pgn": "1. e4 e5 2. Nf3 ...",
        "total_moves": 42,
        "critical_move_number": 18,
        "critical_move_stage": "middle",
        "critical_cpl": 320,
        "moves": [
          {
            "move_number": 1,
            "color": "white",
            "san": "e4",
            "uci": "e2e4",
            "fen_before": "rnbqkbnr/pppppppp/...",
            "fen_after": "rnbqkbnr/pppppppp/...",
            "eval_before": 20,
            "eval_after": 25,
            "cpl": 0,
            "best_move_san": "e4",
            "best_move_uci": "e2e4",
            "annotation": "",
            "stage": "early"
          }
        ]
      }
    ]
  }
  ```

  **New fields added in v2.0:**

  | Field | Type | Description |
  |---|---|---|
  | `end_time` | integer | Unix timestamp when game ended (from Chess.com API) |
  | `ai_summary` | string | 3–5 sentence AI-generated narrative summary |
  | `moves[].clock_time` | integer or null | Remaining clock time in seconds (from `%clk`), null if unavailable |

* **Background processing:** Since full evaluation of up to 20 games takes time (~60–120 seconds on 1 vCPU), use the existing `task_manager` pattern:
  * POST returns a `task_id` immediately
  * Client polls `GET /api/deep-analysis/status/{task_id}` for progress
  * Progressive delivery: return each game as it completes evaluation

### Move annotation logic

* Annotate each move based on CPL:
  * `""` (no annotation): CPL < 50
  * `"?!"` (inaccuracy): 50 ≤ CPL < 100
  * `"?"` (mistake): 100 ≤ CPL < 200
  * `"??"` (blunder): CPL ≥ 200
  * `"!"` (good move): position improved by ≥ 50 cp and move matches engine's best move
  * `"!!"` (brilliant): position improved by ≥ 100 cp from a losing/equal position to winning

---

## Milestone 2: Deep analysis page UI (single-column layout)

**Goal:** Create the `/deep-analysis` page with a scrollable single-column layout of up to 20 interactive chessboards, each displaying one lost game with full analysis controls, AI summary, and charts.

### Page structure and navigation

* **New Flask route:** `/deep-analysis` renders `templates/deep_analysis.html`
* **Navigation from analytics page:**
  * Add "Deep Check Analysis" button in the analytics dashboard (visible after successful analysis)
  * Button passes `username`, `start_date`, `end_date` as URL query parameters
  * Example: `/deep-analysis?username=hikaru&start_date=2026-03-01&end_date=2026-03-20`
* Page header shows: username, date range, time control selected, number of qualifying lost games

### Single-column board layout

* **All viewports:** Single column, 1 game per row, users scroll vertically to view up to 20 games
* **Desktop (≥1200px):** Full-width card, board + move list side by side, larger boards (~400–450px)
* **Tablet (768–1199px):** Full-width card, board + move list side by side, scaled down
* **Mobile (<768px):** Full-width card, move list below board, compact controls
* Each board panel is a self-contained "game analysis card" containing:
  1. **Game info header:** White vs Black (ratings), result, time control, game stage where critical error occurred
  2. **Game timestamp:** Date and time the game was played (e.g., "Played on Mar 18, 2026 at 3:45 PM")
  3. **AI game summary:** 3–5 sentence narrative generated by ChatGPT describing the game flow, critical mistake, and its consequence
  4. **Chessboard** (chessboard.js): interactive, drag-and-drop enabled
  5. **Evaluation bar** (vertical, left side of board): visual bar + centipawn value
  6. **Move list panel** (right side of board): scrollable move list with annotations and clock times
  7. **Navigation controls** (below board): ⏮ ◀ ▶ ⏭ (first, prev, next, last) + Go to Mistake
  8. **Best move indicator:** highlighted arrow on board showing the engine's recommended move
  9. **Evaluation chart** (below controls): Lichess-style area chart showing eval over the course of the game
  10. **Time-usage chart** (below eval chart): dual-line chart showing remaining clock time for both players

### Chessboard component (per board)

* Built with **chessboard.js** (board rendering) + **chess.js** (move validation)
  * CDN links: chessboard.js v1.0.0, chess.js v1.0 (consistent with chess bot PRD)
  * **Piece image source:** Use jsdelivr CDN (`https://cdn.jsdelivr.net/npm/@chrisoakman/chessboardjs@1.0.0/dist/img/chesspieces/wikipedia/{piece}.png`) with onerror fallback to alternative CDN. Preload piece images in HTML `<head>` to prevent rendering gaps.
* Board size: responsive, fills available space in card (~400–450px on desktop in single-column layout)
* Board orientation: automatically set to player's color (white at bottom if player was white)
* **Piece interaction:**
  * In "replay mode" (default): click forward/backward buttons to step through game moves
  * In "explore mode" (activated by dragging a piece): player can make alternate moves
    * When player deviates, board enters "what-if" branch
    * Evaluation updates in real-time via server call
    * A "Back to Game" button resets to the original game line
* **Visual highlights:**
  * Last move: highlighted squares (light yellow)
  * Critical mistake move: highlighted in red when reached during navigation
  * Best move arrow: green arrow overlay showing engine's recommended move
  * Player's move vs best move comparison when on a mistake position

### Evaluation bar

* Vertical bar on the left side of each board
* Height: matches board height
* White advantage: white section grows from bottom
* Black advantage: black section grows from top
* Centipawn value displayed numerically at the top of the bar
* **Mate display:** "M3" (mate in 3) replaces centipawn when applicable
* Color smooth transitions on each move
* Scale: ±10 pawns (±1000 cp), clamped for display

### Move list panel

* Displayed to the right of the board
* Standard two-column format: move number | white move | black move
* **Clock time displayed** next to each move in smaller font: e.g., `e4 (9:58)`
  * Format: `M:SS` for games under 1 hour, `H:MM:SS` for longer games
  * Moves with less than 30 seconds remaining highlighted in red/orange
  * If PGN has no clock data, clock times are omitted
* Scrollable container with auto-scroll to current move
* **Current move highlighted** with background color
* **Annotations displayed inline** next to moves: `Nf3??`, `Rxe5!`
* **Color-coded moves:**
  * Red background: blunders (`??`)
  * Orange background: mistakes (`?`)
  * Yellow background: inaccuracies (`?!`)
  * Green background: great moves (`!`, `!!`)
  * Default background: normal moves
* Clicking any move in the list jumps the board to that position
* When in "explore mode" (player deviated), show the diverged line in a different color (blue)

### Evaluation chart

* **Lichess/Chess.com-style area chart** below each board’s navigation controls
* Chart dimensions: full card width × ~120px height
* **X-axis:** Move number (sequential)
* **Y-axis:** Evaluation in pawns (±10 range, clamped)
* **Visual style:** Filled area chart — white/light fill for white advantage region, dark fill for black advantage region, separated by the zero-line
* **Current move position** marked with a vertical indicator line
* **Critical mistake** marked with a red vertical line or dot
* Clicking on any point in the chart jumps the board to that move
* Hovering shows tooltip with move number and evaluation
* Chart updates when in explore mode to reflect deviation

### Time-usage chart

* **Step/line chart** displayed below the evaluation chart
* Chart dimensions: full card width × ~80px height
* **X-axis:** Move number
* **Y-axis:** Time remaining (in seconds) for both players
* **Two lines:** White (light color) and Black (dark color)
* Steep drops indicate long thinking — easy to spot visually
* Time below 30 seconds highlighted with a colored zone (time pressure)
* Clicking on the chart jumps the board to that move
* If no clock data available in the PGN, the entire time-usage chart section is hidden (not shown empty)

### Navigation controls

* **⏮ (First):** Jump to the beginning of the game (move 0 / starting position)
* **◀ (Previous):** Go back one half-move
* **▶ (Next):** Go forward one half-move
* **⏭ (Last):** Jump to the end of the game
* **⏩ (Go to Mistake):** Jump directly to the critical mistake position
* Keyboard shortcuts (when board is focused):
  * Left arrow: previous move
  * Right arrow: next move
  * Home: first move
  * End: last move

---

## Milestone 3: Interactive analysis and best move engine

**Goal:** Enable real-time position evaluation when the player deviates from the game, and display best move recommendations for every position.

### Engine recommendation: Lichess Cloud API with Stockfish fallback (hybrid approach)

**Rationale for hybrid approach:**

When the player is **replaying the original game**, all evaluations are pre-computed (from Milestone 1 backend) — no real-time engine needed. The engine is only needed when the player **deviates and explores "what-if" lines**.

| Scenario | Engine | Latency | Notes |
|---|---|---|---|
| Replaying original game moves | Pre-computed (cached from Milestone 1) | 0ms (instant) | All evals stored in API response |
| Player deviates — common position | Lichess Cloud API | 50–200ms | 60–80% hit rate for standard positions |
| Player deviates — rare position | Stockfish (server-side, node-limited) | 200–500ms | Fallback for positions not in Lichess cloud |

**Why this hybrid approach is optimal:**
* **Instant replay:** Pre-computed evals make navigating the original game feel snappy (no API calls)
* **Fast deviation analysis:** Lichess Cloud API covers most standard positions in under 200ms
* **Reliable fallback:** Stockfish handles the remaining 20–40% of positions where Lichess has no data
* **No client-side engine needed:** All computation happens server-side, keeping the frontend lightweight
* **Consistent with existing architecture:** Already using this hybrid in `MistakeAnalysisService`

### Real-time evaluation API

* **New endpoint:** `POST /api/evaluate-position`
* **Request body:**
  ```json
  {
    "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    "depth": 1
  }
  ```
  * `depth`: number of best moves to return (default 1, as per requirement)
* **Response:**
  ```json
  {
    "eval": 35,
    "mate": null,
    "best_move": {
      "uci": "e7e5",
      "san": "e5"
    },
    "pv": ["e7e5", "g1f3", "b8c6"]
  }
  ```
* **Implementation:**
  1. Try Lichess Cloud API first (existing `LichessEvaluationService`)
  2. If miss, use Stockfish with `ENGINE_NODES=50000`
  3. Return result in <500ms
* **Rate limiting:** Max 2 requests/second per client (to prevent abuse when clicking rapidly)

### Best move display on board

* When user is on any position, show the engine's best move as a **green arrow overlay** on the board
* Arrow drawn from the origin square to the destination square of the best move
* Arrow is semi-transparent so it doesn't obscure pieces
* Arrow updates when navigating to a new position
* **Best move label** shown in the move list panel: "Best: Nf3" next to the current position
* If the player's move matches the best move, show a green checkmark ✓

### Explore mode (deviation from game line)

* **Activation:** Player drags a piece to make a custom move (not the game's original move)
* **Board behavior:**
  * Move is validated by chess.js
  * If legal, the board updates to the new position
  * Evaluation bar and centipawn value update via `/api/evaluate-position` call
  * Best move arrow updates for the new position
  * Move list shows the deviation in a blue-highlighted section: "Explored: 18. Nf3 (instead of Bc4??)"
* **Reset:** "Back to Game" button resets the board to the original game line at the current move number
* **Branch depth:** Player can deviate up to 5 moves deep from any position (to prevent excessive server load)
* **Visual indicator:** Board border changes to blue when in "explore mode", returns to default when back in game line

---

## Milestone 4: Polish, performance, and testing

**Goal:** Optimize performance for the 1 vCPU DigitalOcean server, ensure responsive UI, and complete E2E test coverage.

### Performance optimization

* **Batch evaluation caching:**
  * Cache full game evaluations in server memory (keyed by game URL)
  * TTL: 30 minutes (user likely finishes review within this time)
  * Max cache size: 50 games (prevent memory bloat on 1 GB RAM server)
* **Progressive loading:**
  * Show first board as soon as first game is evaluated (~5–10 seconds)
  * Remaining boards populate as their evaluations complete
  * Loading skeleton shown for boards not yet ready
  * Progress indicator: "Analyzing game N of 20..."
* **Evaluation request debounce:**
  * When player clicks navigation rapidly, debounce eval requests (200ms delay)
  * Cancel pending requests when a new position is requested
* **CDN assets:** Load chessboard.js, chess.js, and Chart.js from CDN (no self-hosting overhead)

### Responsive design

* **All viewports:** Single-column layout, 1 game per row, vertical scrolling for up to 20 games
* **Desktop (≥1200px):** Full-width cards, board ~400–450px, move list beside board
* **Tablet (768–1199px):** Full-width cards, board scaled down, move list beside board
* **Mobile (<768px):** Full-width cards, move list below board (collapsed by default, tap to expand)
* Touch support for chessboard.js on mobile (tap-tap to move or drag)

### Error handling

* **No qualifying games:** Show friendly message: "No games found with middle/endgame mistakes in this period. Try a longer date range or different time control."
* **Fewer than 20 games:** Show available boards (1–19), hide remaining slots
* **API timeout:** Show retry button per board
* **Invalid username:** Redirect back to analytics page with error message
* **Engine evaluation failure:** Show "Evaluation unavailable" with last known eval, allow navigation to continue

### Accessibility

* Keyboard navigation for all board controls
* ARIA labels for board squares and pieces
* Screen reader support for move list and evaluation values
* High contrast mode for evaluation bar colors

---

# Tech stack

**Backend**

* Flask (existing)
* python-chess (existing — PGN parsing, FEN handling, board state management)
* Stockfish engine (existing — UCI protocol for evaluations)
* LichessEvaluationService (existing — cloud API for fast evaluations)
* Task manager (existing — background processing with polling)

**Frontend**

* chessboard.js v1.0.0 (board rendering, drag-and-drop) — CDN (jsdelivr, with fallback)
* chess.js v1.0 (client-side move validation, game state) — CDN
* Chart.js v4.4.0 (evaluation chart + time-usage chart) — CDN (existing)
* Vanilla JavaScript (ES6+)
* HTML5/CSS3 (CSS Grid for single-column layout)

**Infrastructure**

* DigitalOcean 1 vCPU / 1 GB RAM (existing server)
* No additional services required
* No database changes (all data from Chess.com API + real-time Stockfish)

---

# System architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Browser)                     │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Board 1 ... Board 20 (scrollable, single column) │  │
│  │  chessboard.js + chess.js per board                │  │
│  │  Chart.js: eval chart + time-usage chart per board │  │
│  └────────────────────────────────────────────────────┘  │
│       │                                                  │
│  ┌────┴───────────────────────────────────────────────┐  │
│  │              deep_analysis.js                      │  │
│  │   (Board manager, move navigation, eval display,   │  │
│  │    explore mode, eval charts, time-usage charts,   │  │
│  │    AI summary display, clock time rendering)       │  │
│  └──────────────────────┬────────────────────────────┘  │
└──────────────────────────┼───────────────────────────────┘
                           │ HTTP (AJAX/fetch)
┌──────────────────────────┼───────────────────────────────┐
│                    Flask Backend                          │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              API Routes (api.py)                 │    │
│  │  POST /api/deep-analysis                        │    │
│  │  GET  /api/deep-analysis/status/{task_id}       │    │
│  │  POST /api/evaluate-position                    │    │
│  └──────────────────┬──────────────────────────────┘    │
│                     │                                    │
│  ┌──────────────────┴──────────────────────────────┐    │
│  │          DeepAnalysisService                     │    │
│  │  - Game selection & filtering                    │    │
│  │  - Full game evaluation pipeline                 │    │
│  │  - Clock time parsing (%clk)                     │    │
│  │  - Critical mistake detection                    │    │
│  │  - Move annotation                               │    │
│  │  - AI summary generation (OpenAI)                │    │
│  └─────────┬──────────────────┬────────────────────┘    │
│            │                  │                          │
│  ┌─────────┴──────┐ ┌────────┴──────────┐              │
│  │ Lichess Cloud  │ │ Stockfish Engine   │              │
│  │ API (fast)     │ │ (fallback, 50K     │              │
│  │ 50-200ms       │ │  nodes, 200-500ms) │              │
│  └────────────────┘ └───────────────────┘              │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │          Existing Services (reused)              │    │
│  │  - ChessService (game fetching from Chess.com)   │    │
│  │  - LichessEvaluationService (cloud eval)         │    │
│  │  - TaskManager (background processing)           │    │
│  │  - OpenAI API (gpt-4o-mini, game summaries)      │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

---

# Website overview

## New page: `/deep-analysis`

### Page layout (desktop, v2.0 — single column)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ♟️ Chess Analytics          Home | Analytics | Deep Analysis                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Deep Check Analysis for hikaru                                              │
│  Mar 1–20, 2026 • Blitz • 36 qualifying lost games (showing top 20)         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │ Game 1: hikaru (1200) vs Magnus (1250)                              │    │
│  │ Lost by checkmate • Critical mistake at move 18 (middle game)       │    │
│  │ Played on Mar 18, 2026 at 3:45 PM                                  │    │
│  │                                                                      │    │
│  │ AI Summary: You had a slight edge out of the opening but lost       │    │
│  │ control in the middle game. On move 18 you played Bc4 instead       │    │
│  │ of Nf3, allowing your opponent to win a piece. After that the       │    │
│  │ position collapsed quickly leading to checkmate on move 32.         │    │
│  │                                                                      │    │
│  │  ┌────┐ ┌──────────────────┐ ┌──────────────────────────────────┐  │    │
│  │  │Eval│ │                  │ │ Move List                        │  │    │
│  │  │Bar │ │   Chess Board    │ │ 1. e4 (9:58)   e5 (9:56)       │  │    │
│  │  │    │ │   (400px)        │ │ 2. Nf3 (9:45)  Nc6 (9:50)      │  │    │
│  │  │+1.2│ │                  │ │ 3. Bb5 (9:30)  a6 (9:44)       │  │    │
│  │  └────┘ └──────────────────┘ └──────────────────────────────────┘  │    │
│  │  Best: Nf3 (you played Bc4??)                                      │    │
│  │  ⏮  ◀  ▶  ⏭  ⏩ Mistake  |  Back to Game                        │    │
│  │                                                                      │    │
│  │  ┌──────────────── Evaluation Chart ──────────────────────────┐    │    │
│  │  │ +5 ┃            ╱╲                                         │    │    │
│  │  │  0 ┃──────────╱──╲────────╲────── (moves) ──────────────── │    │    │
│  │  │ -5 ┃                ╲       ╲  ●(mistake)                  │    │    │
│  │  └────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  ┌──────────────── Time Usage Chart ──────────────────────────┐    │    │
│  │  │ 10m ┃──  White   ──  Black                                 │    │    │
│  │  │  5m ┃   ╲    ╲                                             │    │    │
│  │  │  0m ┃─────────────────────────────── (moves) ──────────── │    │    │
│  │  └────────────────────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  (scroll down for games 2–20)                                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Navigation to this page

* **From analytics dashboard:** "Deep Check Analysis" button appears after successful analysis
* **Direct URL access:** `/deep-analysis?username=hikaru&start_date=2026-03-01&end_date=2026-03-20`

---

# Database schema overview

No new database tables are required. All data is sourced from:

1. **Chess.com API** — Game data (PGN, metadata, results)
2. **Stockfish / Lichess Cloud API** — Real-time evaluations
3. **In-memory cache** — Evaluation results (TTL: 30 min, max 50 games)

---

# Key workflows

## Workflow 1: User navigates to deep analysis

1. User opens analytics page (`/analytics`)
2. User enters Chess.com username and date range
3. User clicks "Analyze Performance" (existing flow)
4. After results load, user sees "Deep Check Analysis" button
5. User clicks the button
6. Browser navigates to `/deep-analysis?username=...&start_date=...&end_date=...`
7. Deep analysis page loads skeleton boards
8. JavaScript calls `POST /api/deep-analysis` with the parameters
9. Backend returns `task_id` immediately
10. Frontend polls `GET /api/deep-analysis/status/{task_id}` every 2 seconds
11. As each game analysis completes, the board renders with data
12. All boards populated within ~60–120 seconds (up to 20 games)

## Workflow 2: User reviews a game (replay mode)

1. Board starts at the critical mistake position (not move 1)
2. Game timestamp and AI summary visible above the board
3. Critical move highlighted in red on the board and in the move list
4. Evaluation bar shows the position's eval
5. Best move arrow shown on the board
6. User clicks ▶ (next) to step through subsequent moves
7. User clicks ◀ (previous) to go back
8. User clicks any move in the move list to jump directly
9. Clock times visible next to each move in the move list
10. Evaluation bar, eval chart indicator, time chart indicator, and best move arrow update with each navigation
11. Eval chart shows a red indicator at the critical mistake point

## Workflow 3: User explores an alternative line (explore mode)

1. User is at any position during replay
2. User drags a piece to make a different move (not the game's original move)
3. chess.js validates the move
4. If legal, board updates to the new position
5. Board border turns blue (explore mode indicator)
6. Frontend calls `POST /api/evaluate-position` with the new FEN
7. Backend returns eval + best move (Lichess Cloud → Stockfish fallback)
8. Evaluation bar, centipawn value, and best move arrow update
9. Move list shows: "Explored: 18. Nf3 (instead of Bc4??)"
10. User can make up to 5 more moves in explore mode
11. User clicks "Back to Game" to return to the original game line

## Workflow 4: Backend game selection

1. Receive username and date range
2. Fetch all games using `ChessService` (existing)
3. Count games per time control → select most common time control
4. Filter: lost games only in the most common time control
5. Exclude games with < 15 total moves
6. For each remaining game, parse PGN with `python-chess`
7. Evaluate all middle + endgame player moves with Stockfish
8. Find the critical mistake (largest CPL in middle/endgame)
9. Filter: only games with CPL ≥ 100 in middle/endgame
10. Sort by critical CPL descending → take top 20
11. For each selected game, run full evaluation on every move (including clock time parsing)
12. Generate AI summary via OpenAI for each game
13. Return all data to frontend

---

# User stories and acceptance criteria

## DCA-001: Deep check analysis button on analytics page

**User story:** As a chess player who has analyzed my games, I want to see a "Deep Check Analysis" button on the analytics dashboard so I can quickly navigate to review my lost games.

**Acceptance criteria:**
- [ ] "Deep Check Analysis" button appears on the analytics dashboard after successful analysis
- [ ] Button is not visible before analysis is run (empty/loading state)
- [ ] Button is styled consistently with existing dashboard buttons (use chess-themed icon, e.g., 🔍♟️)
- [ ] Clicking the button navigates to `/deep-analysis` with query parameters: username, start_date, end_date
- [ ] Button works on both desktop and mobile screens

---

## DCA-002: Game selection — filter lost games with middle/endgame errors

**User story:** As a chess player, I want the system to automatically select games where I lost due to middle or endgame mistakes so I can focus on learning from meaningful errors, not opening blunders.

**Acceptance criteria:**
- [ ] System identifies the user's most played time control and filters by it
- [ ] Only lost games are selected (result: checkmated, timeout, resigned, abandoned)
- [ ] Games with fewer than 15 total moves are excluded
- [ ] Middle game is defined as moves 8–20, endgame as moves 21+ (per player)
- [ ] Only games with at least 1 mistake (CPL ≥ 100) in middle or endgame are included
- [ ] Top 20 games are selected by largest critical CPL in middle/endgame
- [ ] If fewer than 20 qualifying games exist, available games (1–19) are shown

---

## DCA-003: Full game evaluation with move-by-move analysis

**User story:** As a chess player reviewing a lost game, I want to see the evaluation for every move so I can understand exactly where I went wrong and how the position changed throughout the game.

**Acceptance criteria:**
- [ ] Every move in the up to 20 selected games has a pre-computed evaluation (centipawns)
- [ ] Each move includes: SAN notation, FEN before/after, eval before/after, CPL, best move, **clock time** (seconds remaining)
- [ ] Annotations are applied: `?!` (inaccuracy, CPL 50–99), `?` (mistake, CPL 100–199), `??` (blunder, CPL ≥ 200), `!` (good), `!!` (brilliant)
- [ ] Evaluations use node-limited Stockfish (50K nodes) consistent with existing settings
- [ ] Full evaluation of 20 games completes within 120 seconds on 1 vCPU server
- [ ] Clock time parsed from `%clk` annotations in PGN (null if unavailable)

---

## DCA-004: Background processing with progressive delivery

**User story:** As a chess player, I want to see the first game board appear quickly while the remaining games are still being analyzed so I don't have to wait for everything to finish.

**Acceptance criteria:**
- [ ] `POST /api/deep-analysis` returns a `task_id` immediately (no blocking)
- [ ] Client polls `GET /api/deep-analysis/status/{task_id}` every 2 seconds
- [ ] First game board appears within 10 seconds of starting analysis
- [ ] Each subsequent board appears as its evaluation completes
- [ ] Loading skeleton is shown for boards not yet ready
- [ ] Progress indicator shows "Analyzing game N of 20..."

---

## DCA-005: Single-column scrollable layout

**User story:** As a chess player, I want to see my lost games displayed in a single-column scrollable layout so I can review each game with a larger board and more detailed information.

**Acceptance criteria:**
- [ ] All viewports: single-column layout with 1 game per row
- [ ] Desktop (≥1200px): full-width cards, board ~400–450px, move list beside board
- [ ] Tablet (768–1199px): full-width cards, same layout scaled down
- [ ] Mobile (<768px): full-width cards, move list below board
- [ ] Up to 20 game cards rendered, user scrolls vertically
- [ ] Each board operates independently (own navigation, eval bar, move list)
- [ ] If fewer than 20 games available, remaining slots are not shown

---

## DCA-006: Interactive chessboard with navigation controls

**User story:** As a chess player, I want to navigate through each game's moves using forward/backward buttons so I can step through the game at my own pace.

**Acceptance criteria:**
- [ ] Chessboard renders correctly using chessboard.js with drag-and-drop enabled
- [ ] Board orientation matches the player's color (white at bottom if player was white)
- [ ] Navigation buttons: ⏮ (first), ◀ (prev), ▶ (next), ⏭ (last), ⏩ (go to mistake)
- [ ] Keyboard shortcuts work when board is focused (arrow keys, Home, End)
- [ ] Board starts at the critical mistake position (not move 1)
- [ ] "Go to Mistake" button jumps to the critical mistake position at any time
- [ ] Pieces animate smoothly between positions

---

## DCA-007: Evaluation bar with centipawn display

**User story:** As a chess player, I want to see a visual evaluation bar next to each board showing who is winning so I can immediately understand the position's balance.

**Acceptance criteria:**
- [ ] Vertical evaluation bar displayed on the left side of each board
- [ ] Bar height matches board height
- [ ] White advantage shown as white section growing from bottom
- [ ] Black advantage shown as black section growing from top
- [ ] Centipawn value displayed numerically (e.g., "+1.2", "-0.5", "M3")
- [ ] Mate display: "M3" when mate in 3 is detected
- [ ] Bar transitions smoothly when navigating between moves
- [ ] Scale: ±10 pawns (±1000 cp), values beyond are clamped

---

## DCA-008: Move list panel with annotations

**User story:** As a chess player, I want to see the complete move list with color-coded annotations so I can scan for mistakes and good moves at a glance.

**Acceptance criteria:**
- [ ] Move list displayed to the right of the board in two-column format (white | black)
- [ ] Current move highlighted with distinct background color
- [ ] Annotations displayed inline: `Nf3??`, `Rxe5!`
- [ ] Color coding: red (blunder), orange (mistake), yellow (inaccuracy), green (good/brilliant)
- [ ] Move list auto-scrolls to current move
- [ ] Clicking any move in the list jumps the board to that position
- [ ] Scrollable container for games with many moves

---

## DCA-009: Best move indicator on board

**User story:** As a chess player, I want to see the engine's best move displayed as an arrow on the board so I can immediately see what I should have played.

**Acceptance criteria:**
- [ ] Green semi-transparent arrow shows best move on the board (from origin to destination square)
- [ ] Arrow updates when navigating to a new position
- [ ] "Best: Nf3" label shown below the board or in the move list panel
- [ ] If the player's move matches the best move, show a green checkmark ✓
- [ ] Arrow does not obscure pieces (semi-transparent overlay)

---

## DCA-010: Evaluation chart per game

**User story:** As a chess player, I want to see a Lichess-style evaluation chart for each game so I can see the overall flow of the game and where the key turning points were.

**Acceptance criteria:**
- [ ] Lichess-style area chart displayed below each board’s navigation controls (full card width × ~120px)
- [ ] X-axis: move number, Y-axis: evaluation in pawns (±10 range)
- [ ] Filled area style: white/light region for white advantage, dark region for black advantage
- [ ] Current move marked with a vertical indicator line
- [ ] Critical mistake position marked with a red dot or vertical line
- [ ] Clicking on any point in the chart jumps the board to that move
- [ ] Hovering shows tooltip with move number and evaluation
- [ ] Chart updates when in explore mode to reflect deviation

---

## DCA-011: Explore mode — deviate and analyze alternative moves

**User story:** As a chess player, I want to drag a piece to make a different move than what was played so I can explore alternative lines and see the evaluation of what I should have done.

**Acceptance criteria:**
- [ ] Player can drag a piece to make a custom (legal) move on any position
- [ ] Board enters "explore mode" when player deviates from the game line
- [ ] Board border changes to blue in explore mode
- [ ] Evaluation bar updates via `/api/evaluate-position` call
- [ ] Best move arrow updates for the new position
- [ ] Move list shows deviation: "Explored: 18. Nf3 (instead of Bc4??)"
- [ ] "Back to Game" button resets to original game line at current move number
- [ ] Maximum 5 deviation moves allowed (prevents excessive server load)
- [ ] `/api/evaluate-position` responds within 500ms

---

## DCA-012: Real-time position evaluation API

**User story:** As a chess player exploring alternative moves, I want the evaluation to update instantly so I can see the impact of my alternative choices without delay.

**Acceptance criteria:**
- [ ] `POST /api/evaluate-position` accepts FEN and returns eval + best move
- [ ] Uses Lichess Cloud API first, falls back to Stockfish (50K nodes)
- [ ] Response time < 500ms for 95% of requests
- [ ] Rate limited to 2 requests/second per client
- [ ] Returns centipawn score, mate indicator, and best move (UCI + SAN)
- [ ] Handles invalid FEN gracefully with appropriate error response

---

## DCA-013: Error handling and edge cases

**User story:** As a chess player, I want clear feedback when issues occur (no qualifying games, API errors, few games) so I understand what happened and what to do.

**Acceptance criteria:**
- [ ] "No qualifying games" message shown when no lost games with middle/endgame errors are found
- [ ] Suggestion shown: "Try a longer date range or different time period"
- [ ] Fewer than 20 qualifying games: show available boards (1–19), hide unused slots
- [ ] API timeout: show retry button per board
- [ ] Invalid username: redirect to analytics page with error message
- [ ] Engine evaluation failure: show "Eval unavailable" with last known value

---

## DCA-014: Performance and caching

**User story:** As a chess player, I want the page to load quickly and respond instantly when I navigate through moves so the analysis experience feels smooth and interactive.

**Acceptance criteria:**
- [ ] Pre-computed evaluations load instantly (0ms) during game replay
- [ ] First board visible within 10 seconds of page load
- [ ] All 20 boards loaded within 120 seconds
- [ ] Game evaluations cached in server memory (TTL: 30 min, max 50 games)
- [ ] Navigation debounce: 200ms delay prevents excessive requests during rapid clicking
- [ ] CDN assets (chessboard.js, chess.js, Chart.js) cached by browser

---

## DCA-015: AI-generated game summary

**User story:** As a chess player reviewing my lost games, I want to see a short narrative summary of each game so I can quickly understand what happened without stepping through every move.

**Acceptance criteria:**
- [ ] Each game card displays a 3–5 sentence AI-generated summary below the game info header
- [ ] Summary describes the game flow, the critical mistake, and its consequence
- [ ] Summary does NOT include improvement tips or practice suggestions
- [ ] Summary is generated using OpenAI `gpt-4o-mini` model (consistent with existing AI advisor)
- [ ] Summary loads after game evaluation completes (can show "Generating summary..." while loading)
- [ ] If OpenAI API is unavailable or key not set, show the existing short summary line as fallback (no crash)
- [ ] Summary uses plain, conversational English appropriate for all skill levels

---

## DCA-016: Game timestamp display

**User story:** As a chess player, I want to see when each game was played so I can correlate my performance with specific times or sessions.

**Acceptance criteria:**
- [ ] Each game card shows the date and time the game was played
- [ ] Format: "Played on Mar 18, 2026 at 3:45 PM" (or similar readable format)
- [ ] Timestamp derived from `end_time` field in Chess.com API response
- [ ] Displayed in the game info header area

---

## DCA-017: Clock time display per move

**User story:** As a chess player, I want to see the remaining clock time for each move so I can understand how time pressure affected my decisions.

**Acceptance criteria:**
- [ ] Each move in the move list shows remaining clock time (e.g., "e4 (9:58)")
- [ ] Clock time parsed from `%clk` annotation in Chess.com PGN
- [ ] Time shown in `M:SS` or `H:MM:SS` format depending on game duration
- [ ] Moves with less than 30 seconds remaining are highlighted in red/orange
- [ ] If PGN does not contain clock data, gracefully omit (no error)

---

## DCA-018: Time-usage chart

**User story:** As a chess player, I want to see a visual chart of time usage throughout the game so I can identify where I spent too much or too little time and when time pressure started.

**Acceptance criteria:**
- [ ] Time-usage chart displayed below the evaluation chart for each game
- [ ] Chart shows remaining time for both white and black across all moves
- [ ] White line in white/light color, black line in dark color
- [ ] Steep drops in the chart indicate long thinking (easy to spot visually)
- [ ] Time below 30 seconds highlighted/colored differently (time pressure zone)
- [ ] Clicking on the chart jumps the board to that move
- [ ] Chart dimensions: full card width × ~80px height
- [ ] If no clock data available in PGN, chart section is hidden (not shown empty)

---

# Testing strategy

## Phase 1: Unit tests

**Backend (`tests/test_deep_analysis_service.py`):**
- Test game filtering: only lost games selected
- Test time control detection: correctly identifies most common time control
- Test game exclusion: games < 15 moves are excluded
- Test critical mistake detection: finds largest CPL in middle/endgame
- Test top 4 selection: sorted by CPL descending
- Test move annotation: correct symbols applied based on CPL thresholds
- Test full game evaluation: all moves have eval_before, eval_after, best_move
- Test stage classification: moves correctly classified as early/middle/endgame
- Test edge case: fewer than 20 qualifying games
- Test edge case: no qualifying games
- Test clock parsing: `%clk` annotations correctly extracted from PGN
- Test clock missing: graceful handling when PGN has no clock data
- Test AI summary prompt: correct game data included in prompt
- Test AI summary fallback: returns fallback text when OpenAI unavailable
- Test max games 20: verify up to 20 games selected and evaluated
- Test game timestamp: `end_time` included in game results

**Test: `/api/evaluate-position` endpoint:**
- Test valid FEN returns eval + best move
- Test invalid FEN returns error
- Test rate limiting (max 2/sec)
- Test Lichess → Stockfish fallback

## Phase 2: Frontend unit tests

- Test board initialization with chessboard.js
- Test move navigation (forward, backward, first, last, go to mistake)
- Test evaluation bar rendering and updates
- Test move list rendering with annotations and color coding
- Test explore mode activation and "Back to Game" reset
- Test evaluation chart rendering
- Test time-usage chart rendering
- Test clock time display in move list
- Test responsive layout (single column)
- Test AI summary display

## Phase 3: Integration / E2E tests (Playwright)

**Test file:** `tests/test_integration_deep_analysis.py`

| Test ID | Description |
|---|---|
| DCA-E2E-001 | Load analytics page, run analysis, verify "Deep Check Analysis" button appears |
| DCA-E2E-002 | Click button, verify navigation to `/deep-analysis` with correct query params |
| DCA-E2E-003 | Verify page loads with loading skeletons, then boards populate progressively |
| DCA-E2E-004 | Verify single-column layout on desktop viewport |
| DCA-E2E-005 | Verify single-column layout on mobile viewport |
| DCA-E2E-006 | Navigate forward/backward through game moves, verify board updates |
| DCA-E2E-007 | Click "Go to Mistake" button, verify board jumps to critical move |
| DCA-E2E-008 | Verify evaluation bar displays and updates on navigation |
| DCA-E2E-009 | Verify move list scrolls and highlights current move |
| DCA-E2E-010 | Click move in move list, verify board jumps to that position |
| DCA-E2E-011 | Drag piece to make alternative move, verify explore mode activates |
| DCA-E2E-012 | In explore mode, verify eval bar updates with new evaluation |
| DCA-E2E-013 | Click "Back to Game", verify board resets to original game line |
| DCA-E2E-014 | Verify best move arrow renders on the board |
| DCA-E2E-015 | Verify eval chart renders with red dot at critical mistake |
| DCA-E2E-016 | Test with username that has no qualifying games, verify error message |
| DCA-E2E-017 | Verify keyboard navigation (arrow keys on focused board) |
| DCA-E2E-018 | Verify all piece images load on every board |
| DCA-E2E-019 | Verify single-column layout renders correctly with 20 games |
| DCA-E2E-020 | Verify AI summary section renders with text for each game |
| DCA-E2E-021 | Verify game timestamp is displayed on each game card |
| DCA-E2E-022 | Verify eval chart is Lichess-style area chart with click interaction |
| DCA-E2E-023 | Verify clock time appears next to moves in move list |
| DCA-E2E-024 | Verify time-usage chart renders with dual lines |
| DCA-E2E-025 | Verify scrolling through up to 20 game cards |

**Running tests:**
```bash
uv run pytest tests/test_integration_deep_analysis.py -v --headed
```

## Phase 4: Performance tests

- Verify full analysis of 20 games completes within 120 seconds on 1 vCPU
- Verify `/api/evaluate-position` responds within 500ms for 95% of requests
- Verify first board appears within 5 seconds
- Verify server memory stays under 500 MB with 50 cached games
- Verify CDN assets are cached by browser (no re-download on navigation)

---

# Success metrics

* **Engagement:** ≥30% of users who run analytics also click "Deep Check Analysis"
* **Completion:** ≥60% of users who open deep analysis review at least 1 full game (navigate ≥10 moves)
* **Explore mode usage:** ≥20% of users try at least 1 alternative move
* **Performance:** First board visible in ≤10 seconds, all boards in ≤120 seconds
* **Error rate:** <5% of deep analysis requests result in errors
* **User return:** ≥40% of users who use deep analysis return to use it again within 7 days

---

# Client context

The primary users are Chess.com players of all skill levels (beginner to advanced) who want to improve their play by learning from their mistakes. The feature targets the "post-mortem analysis" habit — reviewing lost games to understand what went wrong.

The typical user flow: *play games → check statistics → review lost games → learn correct moves → play better*. This feature fills the "review lost games → learn correct moves" gap that currently requires external tools like Lichess analysis board or Chess.com's premium game review feature.

---

# New files to create

| File | Description |
|---|---|
| `app/services/deep_analysis_service.py` | Backend service: game selection, full evaluation, annotation, **clock parsing, AI summary** |
| `app/routes/deep_analysis.py` | API endpoints: `/api/deep-analysis`, `/api/evaluate-position` |
| `templates/deep_analysis.html` | HTML template for the single-column analysis page |
| `static/js/deep_analysis.js` | Frontend logic: board management, navigation, eval display, explore mode, **eval chart, time chart, AI summary, clock display** |
| `static/css/deep_analysis.css` | Styles for the single-column layout, eval bar, move list, **eval chart, time chart, AI summary** |
| `tests/test_deep_analysis_service.py` | Unit tests for backend service |
| `tests/test_integration_deep_analysis.py` | E2E Playwright tests |

# Modified files

| File | Change |
|---|---|
| `templates/analytics.html` | Add "Deep Check Analysis" button |
| `static/js/analytics.js` | Show/hide button, construct navigation URL |
| `static/css/style.css` | Button styling (if not using separate CSS) |
| `app/routes/__init__.py` | Register new blueprint for deep analysis routes |
| `app/routes/views.py` | Add `/deep-analysis` view route |
| `config.py` | Add deep analysis configuration (cache TTL, max games, etc.) |
