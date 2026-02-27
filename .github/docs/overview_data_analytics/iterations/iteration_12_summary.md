# Iteration 12 Summary - Stockfish Performance Optimization for Low-Resource Server

**Date:** February 27, 2026  
**Version:** PRD v2.11  
**Status:** 📋 Ready for Implementation

---

## Overview

This iteration addresses critical performance issues with the mistake analysis feature on a low-resource production server (DigitalOcean 1 vCPU, 1 GB RAM, Ubuntu 25.04). The Lichess Cloud API approach from Iteration 11 proved slower than pure Stockfish due to frequent timeouts and SSL handshake failures.

**Key changes:**
1. **Disable Lichess Cloud API** by default (keep toggle)
2. **Node-limited Stockfish search** (predictable timing, replaces depth/time)
3. **Pre-collect FENs and batch evaluate** (deduplication, cleaner pipeline)
4. **Reduce analysis scope** (15 moves/game, max 10 games)
5. **Progressive UI** (show results incrementally as each game completes)
6. **Linux Stockfish deployment** (deploy.sh updated for DigitalOcean)

**Target:** ~3 seconds per game, ~30 seconds total for 10 games, first result visible in ~3-5 seconds.

---

## Server Environment

| Spec | Value |
|---|---|
| **Provider** | DigitalOcean |
| **Droplet** | ubuntu-s-1vcpu-512mb-10gb-sgp1-01 |
| **CPU** | 1 vCPU |
| **RAM** | 1 GB |
| **Disk** | 10 GB |
| **OS** | Ubuntu 25.04 x64 |
| **Region** | SGP1 (Singapore) |
| **IP** | 159.65.140.136 |

### Server Constraints
- **No parallelism:** 1 core means parallel Stockfish workers would cause context switching overhead
- **RAM limit:** Flask + Gunicorn + Stockfish must stay under 1 GB total
- **Stockfish binary:** Must use Linux version (`/usr/games/stockfish`), not Windows `.exe`

---

## Change 1: Disable Lichess Cloud API by Default

### Problem Statement
Lichess Cloud API was introduced in Iteration 11 for faster evaluations, but real-world results showed:
- Frequent SSL handshake timeouts (especially from corporate networks)
- 39% miss rate → falls back to Stockfish anyway
- Timeout wait (1-5s) + fallback = **slower than pure Stockfish**
- Net negative performance impact in unreliable network conditions

### Solution
Set `USE_LICHESS_CLOUD=false` by default. Keep the code and toggle for servers with good Lichess connectivity (e.g., DigitalOcean SGP1 may have better connectivity).

### Implementation
**File:** `.env`
```bash
# Changed from true to false
USE_LICHESS_CLOUD=false
```

**File:** `config.py`
```python
# Default changed from True to False
USE_LICHESS_CLOUD = os.environ.get('USE_LICHESS_CLOUD', 'False').lower() == 'true'
```

No code changes to `lichess_evaluation_service.py` or the hybrid path in `mistake_analysis_service.py` — the toggle simply skips the Lichess path.

---

## Change 2: Node-Limited Stockfish Search

### Problem Statement
Current Stockfish settings (`depth=15, time=2.0s`) are problematic:
- **Depth-based search:** Unpredictable timing (simple positions finish in 0.1s, complex ones take 5s+)
- **Time-based limits:** UCI communication overhead adds ~1s per call regardless of time limit
- **Too heavy for 1 vCPU:** depth=15 can take several seconds on weak hardware

### Solution
Switch to `go nodes 50000` — node-limited search provides:
- **Predictable timing:** ~0.05-0.1s per evaluation on any hardware
- **Sufficient accuracy:** 50K nodes catches blunders (≥50cp loss) and mistakes reliably
- **Minimal UCI overhead:** Result returns almost immediately once nodes exhausted

### Implementation

**File:** `config.py`
```python
# New configuration
ENGINE_NODES = int(os.environ.get('ENGINE_NODES', '50000'))
```

**File:** `app/services/mistake_analysis_service.py`
```python
def _evaluate_position(self, board: chess.Board) -> Optional[int]:
    # When using node-limited search
    if self.engine_nodes:
        info = self.engine.analyse(
            board,
            chess.engine.Limit(nodes=self.engine_nodes)
        )
    else:
        # Fallback to depth/time (backward compatibility)
        info = self.engine.analyse(
            board,
            chess.engine.Limit(depth=self.engine_depth, time=self.time_limit)
        )
```

### Performance Comparison

| Method | Time per eval | Predictable? | Accuracy |
|---|---|---|---|
| `depth=15, time=2.0` | 1-5s | No | High |
| `depth=1, time=0.1` (Iter 11 fallback) | ~1s (UCI overhead) | No | Low |
| `nodes=50000` | ~0.05-0.1s | **Yes** | Sufficient |

---

## Change 3: Pre-collect FENs and Batch Evaluate

### Problem Statement
Current flow evaluates positions interleaved with move execution:
```
for each move:
    eval_before = evaluate(board)      # API/engine call
    board.push(move)
    eval_after = evaluate(board)       # API/engine call
    cp_change = eval_after - eval_before
```

This has issues:
- Transposition positions evaluated multiple times
- Engine starts/stops between evaluations (overhead)
- No deduplication of identical positions

### Solution
Refactor to a two-pass approach:

**Pass 1: Collect FENs**
```python
fens_needed = []
for each selected move:
    fens_needed.append(board.fen())   # Before move
    board.push(move)
    fens_needed.append(board.fen())   # After move

# Deduplicate
unique_fens = set(fens_needed)
```

**Pass 2: Batch Evaluate**
```python
eval_cache = {}
for fen in unique_fens:
    eval_cache[fen] = engine.analyse(board_from_fen, Limit(nodes=50000))
```

**Pass 3: Compute Results**
```python
for each move:
    cp_before = eval_cache[fen_before]
    cp_after = eval_cache[fen_after]
    cp_change = cp_after - cp_before
```

### Benefits
- **~10-20% fewer evaluations** from deduplication (transpositions)
- **Engine stays warm:** No start/stop between evals, tight evaluation loop
- **Cleaner separation of concerns:** Collection vs evaluation vs analysis

---

## Change 4: Reduced Analysis Scope

### Problem Statement
Current analysis is too broad for 1 vCPU:
- **30 moves per game** × 2 evals = 60 evaluations per game
- **All games under 50** analyzed (could be 49 games × 60 evals = 2,940 evaluations)
- At ~1s per eval = ~49 minutes worst case

### Solution

#### Move Selection: 15 Moves Per Game (5 + 5 + 5)

**Stage definitions:**
- **Early game:** Moves 1-15 (opening)
- **Middle game:** Moves 16-30 (middlegame)
- **Endgame:** Moves 31+ (endgame)

**Selection algorithm:**
```python
def _select_moves_for_analysis(total_player_moves, moves_per_game=15):
    """
    Select moves across all 3 game stages.
    Target: 5 early + 5 middle + 5 endgame = 15 moves.
    If a stage has fewer than 5 moves, redistribute to other stages.
    """
    stages = {
        'early': [],     # move indices in early game
        'middle': [],    # move indices in middle game
        'endgame': []    # move indices in endgame
    }
    
    # Classify all player moves by stage
    for i in range(total_player_moves):
        move_number = (i * 2 + 1 + 1) // 2  # Approximate full move number
        if move_number <= 15:
            stages['early'].append(i)
        elif move_number <= 30:
            stages['middle'].append(i)
        else:
            stages['endgame'].append(i)
    
    # Allocate 5 per stage, redistribute if needed
    target_per_stage = moves_per_game // 3  # 5
    selected = set()
    overflow = 0
    
    for stage_name in ['early', 'middle', 'endgame']:
        available = stages[stage_name]
        can_select = min(target_per_stage + overflow, len(available))
        
        if len(available) <= can_select:
            selected.update(available)
            overflow += (target_per_stage - len(available))
        else:
            # Evenly space selections
            step = len(available) / can_select
            for j in range(can_select):
                idx = int(j * step)
                selected.add(available[idx])
            overflow = 0
    
    return selected
```

**Examples:**
- 40-move game: 5 from moves 1-15, 5 from moves 16-30, 5 from moves 31-40
- 20-move game: 5 from moves 1-15, 5 from moves 16-20, 5 redistributed (3 to early, 2 to middle)
- 10-move game: all 10 moves analyzed (under 15 total)

#### Game Selection: Max 10 Games

```python
def _select_games_for_analysis(games_data, max_games=10):
    """
    Select up to max_games evenly distributed across the time period.
    If fewer than max_games available, analyze all.
    """
    if len(games_data) <= max_games:
        return games_data
    
    # Sort by timestamp (end_time)
    sorted_games = sorted(games_data, key=lambda g: g.get('end_time', 0))
    
    # Pick evenly spaced games
    step = len(sorted_games) / max_games
    selected = []
    for i in range(max_games):
        idx = int(i * step)
        selected.append(sorted_games[idx])
    
    return selected
```

### Configuration
```bash
MAX_ANALYSIS_GAMES=10    # Cap on games analyzed
MOVES_PER_GAME=15        # Total moves per game (5 early + 5 mid + 5 end)
```

### Impact
- **Evaluations per game:** 30 (15 moves × 2) vs 60 previously → **50% reduction**
- **Max total evaluations:** 300 (10 games × 30) vs 2,940 previously → **~90% reduction**
- **Time at 0.1s/eval:** 300 × 0.1s = **30 seconds** vs 49 minutes previously

---

## Change 5: Progressive UI

### Problem Statement
Users currently wait for ALL games to complete analysis before seeing any results. With 10 games at ~3s each, that's a 30-second black box with only a spinner.

### Solution
Show results incrementally as each game completes analysis.

### Implementation

#### Backend: Polling-Based Progress

**File:** `app/routes/api.py`
```python
@api_bp.route('/api/mistake-analysis/status/<task_id>', methods=['GET'])
def get_mistake_analysis_status(task_id):
    """Poll endpoint for progressive mistake analysis results."""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'status': task['status'],           # 'processing', 'complete'
        'games_analyzed': task['progress'],  # e.g., 3
        'games_total': task['total'],        # e.g., 10
        'partial_results': task['results'],  # Results so far
        'current_game': task.get('current_game_info', '')
    })
```

**Analysis runs in background thread:**
```python
def analyze_with_progress(games, username, task_id):
    for idx, game in enumerate(games):
        result = analyze_single_game(game, username)
        task_manager.update_task(task_id, {
            'progress': idx + 1,
            'results': aggregate_so_far,
            'current_game_info': f'Game {idx + 1} of {len(games)}'
        })
    
    task_manager.update_task(task_id, {'status': 'complete'})
```

#### Frontend: Polling and Incremental Rendering

**File:** `static/js/analytics.js`
```javascript
async function pollMistakeAnalysis(taskId) {
    const pollInterval = setInterval(async () => {
        const response = await fetch(`/api/mistake-analysis/status/${taskId}`);
        const data = await response.json();
        
        // Update progress indicator
        updateProgressBar(data.games_analyzed, data.games_total);
        
        // Render partial results
        if (data.partial_results) {
            renderMistakeAnalysis(data.partial_results);
        }
        
        // Stop polling when complete
        if (data.status === 'complete') {
            clearInterval(pollInterval);
            renderMistakeAnalysis(data.partial_results);
        }
    }, 2000); // Poll every 2 seconds
}
```

#### UI Loading State
**File:** `templates/analytics.html`
```html
<!-- Progressive loading indicator -->
<div id="mistakeAnalysisProgress" style="display: none;">
    <div class="progress-bar">
        <div class="progress-fill" id="analysisProgressFill"></div>
    </div>
    <p id="analysisProgressText">Analyzing game 1 of 10...</p>
</div>
```

### User Experience Flow
1. User clicks "Analyze Performance"
2. Main analytics load immediately (no change)
3. Mistake analysis section shows: "Starting analysis..."
4. After ~3s: "Game 1 of 10 complete" → table and summary start populating
5. Every ~3s: More data arrives, table updates live
6. After ~30s: "Analysis complete" → final results shown
7. User sees useful data from second 3, not second 30

---

## Change 6: Linux Stockfish Deployment

### Problem Statement
Production server runs Ubuntu 25.04. Current `STOCKFISH_PATH` points to Windows binary (`C:\stockfish\stockfish-windows-x86-64-avx2.exe`).

### Solution
Install Stockfish via Ubuntu package manager and update deploy.sh.

### Installation
```bash
# Install Stockfish on Ubuntu
sudo apt-get update
sudo apt-get install -y stockfish

# Verify installation
which stockfish        # /usr/games/stockfish
stockfish <<< "uci"    # Should show "id name Stockfish ..." and "uciok"
```

### Size Impact
- **Stockfish package:** ~5 MB
- **Available disk:** 10 GB
- **Impact:** Negligible (0.05% of disk)

### Configuration
```bash
# Server .env (DigitalOcean Ubuntu)
STOCKFISH_PATH=/usr/games/stockfish

# Local .env (Windows development)
STOCKFISH_PATH=C:\stockfish\stockfish-windows-x86-64-avx2
```

### deploy.sh Updates
The deployment script is updated to:
1. Install `stockfish` package via `apt-get`
2. Verify Stockfish binary is accessible
3. Set correct path in `.env`
4. Include Iteration 12 configuration variables in default `.env`

---

## Combined Performance Analysis

### Evaluation Count Breakdown

| Component | Iteration 11 | Iteration 12 | Reduction |
|---|---|---|---|
| Moves per game | 30 | **15** | 50% |
| Evals per game | ~60 | **~30** | 50% |
| Max games | All under 50 | **10** | ~80% |
| Max total evals | ~2,940 | **~300** | **90%** |
| Time per eval | ~1s | **~0.1s** | **90%** |
| Total time (worst) | ~49 min | **~30s** | **99%** |

### Expected Timeline for 10 Games

```
t=0s    Start analysis
t=3s    Game 1 complete → UI shows first results
t=6s    Game 2 complete → UI updates
t=9s    Game 3 complete → UI updates
...
t=27s   Game 9 complete → UI updates
t=30s   Game 10 complete → Final results shown
```

### RAM Usage Estimate

| Component | Memory |
|---|---|
| Flask + Gunicorn (2 workers) | ~200 MB |
| Stockfish engine (1 instance) | ~50-100 MB |
| Python analysis code | ~50 MB |
| OS overhead | ~200 MB |
| **Total** | **~500-550 MB** |
| **Available** | 1024 MB |
| **Headroom** | ~470 MB ✅ |

---

## Dependencies

### New Dependencies
```toml
# No new Python dependencies required
# Using existing packages:
# - python-chess (already installed for Stockfish UCI)
# - requests (already installed)
# - flask (already installed)
```

### System Dependencies (Linux server)
```bash
# Stockfish chess engine
sudo apt-get install -y stockfish
```

### Configuration Updates
```bash
# .env additions/updates for Iteration 12
USE_LICHESS_CLOUD=false              # Default off
ENGINE_NODES=50000                   # Node-limited search
MAX_ANALYSIS_GAMES=10                # Cap on games analyzed  
MOVES_PER_GAME=15                    # Moves per game (5+5+5)
MISTAKE_ANALYSIS_UI_ENABLED=true     # Re-enable with faster analysis

# Server-specific
STOCKFISH_PATH=/usr/games/stockfish  # Linux path
```

---

## Testing Plan

### Phase 1: Unit Tests
1. Test node-limited Stockfish evaluation returns valid centipawn scores
2. Test FEN pre-collection from PGN (correct positions extracted)
3. Test FEN deduplication (transpositions only evaluated once)
4. Test 15-move selection: 5+5+5 across stages
5. Test move redistribution when stage has fewer than 5 moves
6. Test game selection: max 10, evenly distributed
7. Test progressive callback mechanism fires after each game

### Phase 2: Integration Tests
8. Test full analysis pipeline with node limit on real PGN
9. Test progressive results update correctly after each game
10. Test with edge cases: very short game (5 moves), very long game (80 moves)
11. Test with exactly 10, under 10, and over 10 games
12. Test backward compatibility when ENGINE_NODES is not set (falls back to depth/time)

### Phase 3: Performance Tests
13. **Critical:** Verify ≤0.15s per evaluation with nodes=50000
14. **Critical:** Verify ≤5s per game (15 moves analyzed)
15. **Critical:** Verify ≤45s total for 10 games
16. Test Stockfish memory usage stays under 100MB
17. Verify progressive UI shows first result in ≤5 seconds

### Phase 4: Server Deployment Tests
18. Deploy to DigitalOcean droplet (1 vCPU)
19. Verify Stockfish binary works (`stockfish <<< "uci"`)
20. Run analysis on production server, verify timing
21. Monitor RAM usage stays under 1 GB
22. Test progressive UI end-to-end on production
23. Load test: 2 concurrent users (verify no memory spike)

---

## Migration Checklist

### Code Changes
- [ ] Update `config.py` with ENGINE_NODES, MAX_ANALYSIS_GAMES, MOVES_PER_GAME
- [ ] Refactor `mistake_analysis_service.py`: node-limited search
- [ ] Refactor `mistake_analysis_service.py`: FEN pre-collection and batch evaluate
- [ ] Refactor `mistake_analysis_service.py`: 15-move selection (5+5+5)
- [ ] Refactor `mistake_analysis_service.py`: max 10 game selection
- [ ] Refactor `mistake_analysis_service.py`: progressive callback support
- [ ] Add polling endpoint in `api.py` for progressive results
- [ ] Update `analytics.js`: progressive rendering with polling
- [ ] Update `analytics.html`: progressive loading indicators
- [ ] Update `.env.example` with new variables
- [ ] Update `deploy.sh` with Stockfish installation

### Configuration
- [ ] Update `.env` with Iteration 12 variables
- [ ] Set `USE_LICHESS_CLOUD=false`
- [ ] Set `ENGINE_NODES=50000`
- [ ] Set `MAX_ANALYSIS_GAMES=10`
- [ ] Set `MOVES_PER_GAME=15`
- [ ] Set `MISTAKE_ANALYSIS_UI_ENABLED=true`

### Deployment
- [ ] SSH into DigitalOcean server
- [ ] Run updated `deploy.sh`
- [ ] Verify Stockfish installation: `which stockfish`
- [ ] Verify Stockfish works: `stockfish <<< "uci"`
- [ ] Update server `.env` with Linux Stockfish path
- [ ] Restart chesstic service
- [ ] Test analysis on production
- [ ] Monitor RAM and CPU usage

---

## Risk Assessment

| Risk | Impact | Mitigation |
|---|---|---|
| 50K nodes insufficient for accurate analysis | Misses some mistakes | Can increase to 100K (doubles time to ~0.2s/eval) |
| 15 moves/game misses critical moments | Incomplete analysis | Captures, checks, and trades can be prioritized in future |
| Progressive UI polling adds server load | More API calls | 2-second polling interval, lightweight JSON responses |
| Stockfish not available in Ubuntu 25.04 repos | Deployment fails | Fallback: download binary from stockfish.org |
| 1 GB RAM insufficient | OOM kills | Gunicorn with 1 worker instead of 2 if needed |

---

## Rollback Plan

All changes are configuration-driven with backward compatibility:

```bash
# Revert to Iteration 11 behavior
USE_LICHESS_CLOUD=true           # Re-enable Lichess
ENGINE_NODES=                     # Empty = use depth/time instead
MAX_ANALYSIS_GAMES=999           # Effectively unlimited
MOVES_PER_GAME=30                # Back to 30 moves
ENGINE_DEPTH=15                  # Original depth
ENGINE_TIME_LIMIT=2.0            # Original time limit
```

No code rollback needed — the engine falls back to depth/time when `ENGINE_NODES` is empty.
