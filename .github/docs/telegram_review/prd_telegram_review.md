# PRD: Telegram Daily/Weekly Chess Review (v1.0)

## Project overview

This feature sends the player two automated Telegram messages summarizing their own recent Chess.com games:

- **Daily review** — every day, covering the games played in the last 1 day (H-1).
- **Weekly review** — every Monday, covering the games played in the last 7 days (H-7).

Both messages answer the same two questions, split by color (White/Black):

1. **How did I win/lose?** — checkmate, timeout, resignation, abandoned, etc.
2. **Which openings do I win/lose the most?** — grouped by the literal move order at four different depths (first 4, 5, 6, and 7 full moves), each entry labeled with its recognized opening name.

This is a personal analytics tool for a single fixed Chess.com account; there is no multi-user support and no persistence layer (games are fetched fresh from the Chess.com API on every run, exactly as the rest of the app already does).

**Skills required:**

* Python
* Chess.com API integration (existing `ChessService`)
* PGN parsing (`python-chess`, existing `AnalyticsService`)
* Telegram Bot API
* Windows Task Scheduler

---

# PRD change history

## Iteration 1 - September 12, 2026

**Version:** 1.0
**Focus:** Initial implementation — daily/weekly Telegram review

### Context

**User need:** The player wants a lightweight, push-based way to review their own recent games without opening the analytics dashboard — specifically, why they're winning/losing (the termination reason) and which openings are working or not, broken down by color.

**Key decision:** Reuse the existing `ChessService` (Chess.com API client) and `AnalyticsService` (game enrichment, termination classification, opening detection) as much as possible rather than building a parallel data pipeline. Only two small pieces were missing from the app entirely: a Telegram sender, and a way to schedule/trigger the two jobs (there is no DB, scheduler, or Telegram integration anywhere in the codebase prior to this).

### Changes summary

**Change 1 - Bug fix in `ChessService.analyze_games` (blocking fix):**
The existing inline date filter compared game timestamps against `end_date` at exact midnight (`start <= game_date <= end`), which meant a single-day query (`start_date == end_date`, exactly what the daily H-1 job needs) would match essentially zero games. A correct helper, `_filter_games_by_date`, already existed in the same file but wasn't used by `analyze_games`. Fixed `analyze_games` to use the same inclusive-end-of-day semantics (`game_date < end_date + 1 day`). This only makes results more correct and has no negative effect on existing multi-day queries.

**Change 2 - Generalized move-prefix extraction in `AnalyticsService`:**
- `_extract_first_six_moves(pgn_string)` → `_extract_first_n_moves(pgn_string, num_full_moves)`. The one existing call site (`_analyze_opening_performance`, used by the live analytics dashboard) was updated to pass `num_full_moves=6` explicitly, preserving prior behavior.
- **Correctness fix included in the generalization:** the old implementation silently returned however many plies existed if a game was shorter than the requested length, making a 3-full-move game indistinguishable from a genuine 6-full-move prefix. The generalized version returns `None` when the game ended before reaching the requested length, so short games are excluded from that length's grouping rather than miscounted into it.

**Change 3 - New `AnalyticsService._analyze_opening_by_prefix_length(games, num_full_moves)`:**
Groups enriched games by `(player_color, first_n_moves_text)` — the literal move order (e.g. `"1. e4 e5 2. Nf3 Nc6"`), not the opening name — and labels each group with its recognized opening name (via the existing `_extract_opening_name`). Returns, per color, the top 5 groups ranked by raw game count with wins/losses/draws/win_rate. Called once per length in `{4, 5, 6, 7}`. Because each length is graded independently and short games are excluded (Change 2), the total games counted per color can only shrink as the length grows — never grow, and never silently merge a short game into a longer bucket.

**Change 4 - New `app/services/telegram_service.py` (`TelegramService`):**
Thin wrapper around `requests.post` to the Telegram Bot API's `sendMessage` endpoint. `requests` is already a project dependency.

**Change 5 - New `app/services/game_review_service.py` (`GameReviewService`, `format_review_message`):**
`GameReviewService.build_review(username, start_date, end_date, timezone)` composes `ChessService.analyze_games` + `AnalyticsService._parse_and_enrich_games` + the per-color termination breakdowns (`_analyze_termination_wins`/`_analyze_termination_losses`, called once per color on a color-filtered game list) + the four prefix-length opening breakdowns into one summary dict. `format_review_message(summary, title)` renders that summary as a Telegram message; used identically by both the daily and weekly job (only the title/date-range text differs).

**Change 6 - New `scripts/telegram_review.py` CLI:**
`python scripts/telegram_review.py --mode daily|weekly`. Computes the date window (daily = yesterday only; weekly = the 7 days ending yesterday), loads `.env` explicitly from the project root, builds the review, and sends it via `TelegramService`.

**Change 7 - Config additions (`.env.example`, `config.py`):**
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `CHESS_USERNAME`, `REVIEW_TIMEZONE` (default `UTC`).

### Message format

Identical structure for daily and weekly (only the header/date-range text differs):

```
📊 Daily Chess Review — 2026-09-11 (the_chesstic)
Games played: 8  |  4W - 3L - 1D

⚪ White — 2W - 2L
  🏁 Won by: Resignation 1, Checkmate 1
  💀 Lost by: Timeout 1, Checkmate 1

⚫ Black — 2W - 1L - 1D
  🏁 Won by: Resignation 1, Timeout 1
  💀 Lost by: Timeout 1

♟️ White — Opening (first 4 moves)
  • 1.e4 e5 2.Nf3 Nc6 (Italian Game): 3 games (2W-1L, 67%)
  • 1.e4 c5 2.Nf3 d6 (Sicilian Defense): 1 game (1W-0L, 100%)

♟️ White — Opening (first 5 moves)
  • 1.e4 e5 2.Nf3 Nc6 3.Bc4 (Italian Game): 3 games (2W-1L, 67%)

♟️ White — Opening (first 6 moves)
  • 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 (Italian Game): 2 games (1W-1L, 50%)

♟️ White — Opening (first 7 moves)
  • 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.c3 (Italian Game): 2 games (1W-1L, 50%)

⚫ Black — Opening (first 4 moves)
  • 1.e4 c5 2.Nf3 d6 (Sicilian Defense): 2 games (1W-1L, 50%)

⚫ Black — Opening (first 5 moves)
  • 1.e4 c5 2.Nf3 d6 3.d4 (Sicilian Defense): 2 games (1W-1L, 50%)

⚫ Black — Opening (first 6 moves)
  • 1.e4 c5 2.Nf3 d6 3.d4 cxd4 (Sicilian Defense): 2 games (1W-1L, 50%)

⚫ Black — Opening (first 7 moves)
  • 1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 (Sicilian Defense): 2 games (1W-1L, 50%)
```

Weekly review uses the same layout, aggregated over the 7-day window, titled "Weekly Chess Review — 2026-09-05 to 2026-09-11". Each of the 8 opening sections (4 lengths × 2 colors) shows up to 5 move-order groups; a section is omitted if empty. If zero games were played in the window, a short "No games played between X and Y" message is sent instead.

### User stories

**Requirement ID:** TR-001

**User story:** As the player, I want a daily Telegram message summarizing yesterday's games (how I won/lost, and my most-played openings by color) so I can review my play without opening the dashboard.

**Acceptance criteria:**
- [ ] A message is sent once per day covering exactly the previous calendar day (H-1) in `REVIEW_TIMEZONE`
- [ ] Win/loss termination breakdown (checkmate/timeout/resignation/abandoned/etc.) is shown separately for White and Black
- [ ] Opening breakdown is shown for each of first-4/5/6/7-move lengths, separately for White and Black, each entry showing move order + recognized opening name + W-L-D + win rate
- [ ] A day with zero games sends a short "no games played" message instead of an empty/malformed report

**Requirement ID:** TR-002

**User story:** As the player, I want a weekly Telegram message every Monday summarizing the last 7 days of games, in the same format as the daily review, so I can see patterns over a longer window.

**Acceptance criteria:**
- [ ] A message is sent every Monday covering the 7 days ending the previous day (H-7 through H-1)
- [ ] Same content/format as the daily review, aggregated over the window

### Technical impact

**New files:**
- `app/services/telegram_service.py`
- `app/services/game_review_service.py`
- `scripts/telegram_review.py`
- `tests/test_game_review_service.py`

**Modified files:**
- `app/services/analytics_service.py` — generalized `_extract_first_six_moves` into `_extract_first_n_moves`; added `_analyze_opening_by_prefix_length`
- `app/services/chess_service.py` — fixed inclusive end-of-day date filtering in `analyze_games`
- `config.py`, `.env.example` — new Telegram/review config

**No changes required:**
- Existing API routes, templates, or frontend JS (this feature has no web UI)
- Existing `AnalyticsService.analyze_detailed` output shape (all changes are additive; the one behavior-affecting change — the truncation fix — only affects the rare case of a named-opening group whose first-occurrence sample game ended before move 6)

### Testing strategy

**Automated (new, narrow):** `tests/test_game_review_service.py` covers `_extract_first_n_moves` (including the short-game exclusion), `_analyze_opening_by_prefix_length` (merge-then-split behavior across lengths, win/loss counts), and `format_review_message` (color/termination sections, opening sections, the no-games case) — all against fixed sample PGNs, no live Chess.com or Telegram calls.

**Manual, end-to-end:** Run `scripts/telegram_review.py --mode daily` and `--mode weekly` against a real `.env` pointed at a test Telegram chat; confirm totals match actual Chess.com history for the window.

**Manual, ops:** Confirm both Windows Task Scheduler jobs fire on schedule and successfully deliver a message.

**Out of scope:** No CI pipeline changes (none exist in this repo today); no changes to unrelated existing tests.

### Ops: Windows Task Scheduler setup

Run once from an elevated PowerShell prompt on the machine that will send the reviews (adjust the path if the project isn't at `C:\anaconda_backup\Project\chesstic_v2`):

```
schtasks /create /tn "Chesstic Daily Review" ^
  /tr "\"C:\anaconda_backup\Project\chesstic_v2\.venv\Scripts\python.exe\" \"C:\anaconda_backup\Project\chesstic_v2\scripts\telegram_review.py\" --mode daily" ^
  /sc daily /st 08:00 /rl LIMITED

schtasks /create /tn "Chesstic Weekly Review" ^
  /tr "\"C:\anaconda_backup\Project\chesstic_v2\.venv\Scripts\python.exe\" \"C:\anaconda_backup\Project\chesstic_v2\scripts\telegram_review.py\" --mode weekly" ^
  /sc weekly /d MON /st 08:00 /rl LIMITED
```

To have either task run whether or not the machine is logged in, add `/ru <username> /rp <password>` (Task Scheduler will prompt for and store the password) and omit `/it`. Verify a task fires on demand with `schtasks /run /tn "Chesstic Daily Review"`, then check the target Telegram chat.

### Setup checklist (one-time)

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram → copy the bot token into `TELEGRAM_BOT_TOKEN`.
2. Send the bot any message, then call `https://api.telegram.org/bot<token>/getUpdates` and read `chat.id` from the response → set `TELEGRAM_CHAT_ID`.
3. Set `CHESS_USERNAME` to the Chess.com username to review, and `REVIEW_TIMEZONE` to an IANA timezone string (e.g. `Asia/Jakarta`).
4. Register the two Task Scheduler jobs above.

## Iteration 2 - September 12, 2026 (same day)

**Version:** 1.1
**Focus:** Two bugs surfaced by running both jobs for real against a live account, both fixed.

### Bug 1 - Markdown parse error on any message containing an underscore

**Symptom:** `scripts/telegram_review.py --mode daily` failed with `400 Client Error: Bad Request ... sendMessage`.

**Root cause:** `TelegramService.send_message` defaulted to `parse_mode='Markdown'`. The message title includes the Chess.com username in parentheses (e.g. `(the_chesstic)`); Telegram's legacy Markdown parser treats a lone `_` as an unclosed italic marker and rejects the whole message. The report has no actual need for bold/italic formatting, so this would recur for any username, opening name, or PGN annotation containing `_`, `*`, `` ` ``, `[`, or `]`.

**Fix:** Changed `send_message`'s default `parse_mode` to `None` (plain text). [telegram_service.py](../../../app/services/telegram_service.py)

### Bug 2 - Weekly message exceeds Telegram's 4096-character limit

**Symptom:** `--mode weekly` failed the same way once run against a real week with 31 games — the rendered message was 4495 characters, over Telegram's per-message limit.

**Fix:** Added `TelegramService.send_long_message`, which splits an over-long message into multiple `sendMessage` calls on line boundaries (never cutting a single opening/termination entry in half), and switched `scripts/telegram_review.py` to call it instead of `send_message`. A week with many games or many distinct openings now arrives as 2+ sequential Telegram messages instead of failing outright.

### Testing added

`tests/test_telegram_service.py` — chunking behaves correctly for short and long text (line-boundary-safe splitting), `send_long_message` issues one API call per chunk, and returns `False` if any chunk fails to send. Verified live end-to-end against the real bot/chat/account for both `--mode daily` (2 games) and `--mode weekly` (31 games, arrived as 2 messages).
