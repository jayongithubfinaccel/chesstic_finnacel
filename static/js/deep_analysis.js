/**
 * Deep Check Analysis — single-column game review.
 * PRD: chess_page_analysis v2.0
 */

// State management per board
const boards = {}; // boardId -> board state

// Piece theme — local images (CDN-independent)
const PIECE_THEME_PRIMARY = '/static/img/chesspieces/wikipedia/{piece}.png';
const PIECE_THEME_FALLBACK = 'https://chessboardjs.com/img/chesspieces/wikipedia/{piece}.png';

// ------------------------------------------------------------------
// Entry point
// ------------------------------------------------------------------

function startDeepAnalysis(username, startDate, endDate) {
    document.getElementById('daSubtitle').textContent =
        `Analyzing games for ${username} (${startDate} to ${endDate})`;

    fetch('/api/deep-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: username,
            start_date: startDate,
            end_date: endDate,
        }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'processing' && data.task_id) {
            pollDeepAnalysis(data.task_id);
        } else if (data.error) {
            showError('Analysis failed', data.error);
        }
    })
    .catch(err => {
        showError('Network error', err.message);
    });
}

function pollDeepAnalysis(taskId) {
    const poll = setInterval(() => {
        fetch(`/api/deep-analysis/status/${taskId}`)
            .then(r => r.json())
            .then(data => {
                if (data.status === 'processing') {
                    const pct = data.progress ? data.progress.percentage : 0;
                    document.getElementById('daProgressFill').style.width = pct + '%';
                    document.getElementById('daProgressText').textContent = pct + '%';
                } else if (data.status === 'completed') {
                    clearInterval(poll);
                    renderAnalysis(data.data);
                } else if (data.status === 'error') {
                    clearInterval(poll);
                    showError('Analysis error', data.error || 'Unknown error');
                } else if (data.status === 'not_found') {
                    clearInterval(poll);
                    showError('Task not found', 'The analysis task could not be found.');
                }
            })
            .catch(() => {
                clearInterval(poll);
                showError('Network error', 'Lost connection to server.');
            });
    }, 2000);
}

// ------------------------------------------------------------------
// Render analysis results
// ------------------------------------------------------------------

function renderAnalysis(data) {
    document.getElementById('daLoading').classList.add('hidden');

    if (!data.games || data.games.length === 0) {
        showError(
            'No qualifying games found',
            `No lost games with middle/endgame mistakes in the selected period (${data.time_control || 'all'} time control). Try a longer date range.`
        );
        return;
    }

    document.getElementById('daSubtitle').textContent =
        `${data.username} \u2022 ${data.time_control} \u2022 ${data.games_qualifying} qualifying lost games (showing top ${data.games.length})`;

    const grid = document.getElementById('daBoardGrid');
    grid.classList.remove('hidden');
    grid.innerHTML = '';

    data.games.forEach((game, index) => {
        const boardId = `board-${index}`;
        const card = createGameCard(boardId, game, index);
        grid.appendChild(card);
        initBoard(boardId, game);
    });
}

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

function formatClockTime(seconds) {
    if (seconds == null) return '';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    return `${m}:${String(s).padStart(2, '0')}`;
}

function formatTimestamp(unixTimestamp) {
    if (!unixTimestamp) return '';
    const d = new Date(unixTimestamp * 1000);
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' };
    return 'Played on ' + d.toLocaleDateString('en-US', options);
}

function hasClockData(moves) {
    return moves && moves.some(m => m.clock_time != null);
}

// ------------------------------------------------------------------
// Create game card DOM
// ------------------------------------------------------------------

function createGameCard(boardId, game, index) {
    const card = document.createElement('div');
    card.className = 'da-game-card';
    card.id = `card-${boardId}`;

    const whiteLabel = `${game.white.username} (${game.white.rating})`;
    const blackLabel = `${game.black.username} (${game.black.rating})`;
    const resultText = game.result || 'lost';
    const stageText = game.critical_move_stage || '';
    const timestampText = formatTimestamp(game.end_time);

    const summaryHtml = game.ai_summary
        ? `<div class="da-ai-summary">${escapeHtml(game.ai_summary)}</div>`
        : '';

    const showTimeChart = hasClockData(game.moves || []);

    card.innerHTML = `
        <div class="da-game-info">
            <div class="da-players">Game ${index + 1}: ${escapeHtml(whiteLabel)} vs ${escapeHtml(blackLabel)}</div>
            <div class="da-game-meta">
                Lost by ${escapeHtml(resultText)} \u2022 Critical mistake at move ${game.critical_move_number} (${escapeHtml(stageText)})
                \u2022 CPL: ${game.critical_cpl}
            </div>
            ${timestampText ? `<div class="da-game-timestamp">${escapeHtml(timestampText)}</div>` : ''}
        </div>
        ${summaryHtml}
        <div class="da-board-area">
            <div class="da-eval-bar" id="eval-bar-${boardId}">
                <div class="da-eval-value" id="eval-value-${boardId}">0.0</div>
                <div class="da-eval-bar-black" id="eval-black-${boardId}" style="flex-grow:50"></div>
                <div class="da-eval-bar-white" id="eval-white-${boardId}" style="flex-grow:50"></div>
            </div>
            <div class="da-board-wrapper">
                <div class="board-container" id="${boardId}"></div>
            </div>
            <div class="da-move-list" id="moves-${boardId}"></div>
        </div>
        <div class="da-best-move" id="best-${boardId}"></div>
        <div class="da-controls">
            <button class="da-nav-btn" onclick="navFirst('${boardId}')" title="First move">\u23EE</button>
            <button class="da-nav-btn" onclick="navPrev('${boardId}')" title="Previous move">\u25C0</button>
            <button class="da-nav-btn" onclick="navNext('${boardId}')" title="Next move">\u25B6</button>
            <button class="da-nav-btn" onclick="navLast('${boardId}')" title="Last move">\u23ED</button>
            <button class="da-nav-btn da-btn-mistake" onclick="navMistake('${boardId}')" title="Go to critical mistake">\u23E9 Mistake</button>
            <button class="da-nav-btn da-btn-back-game" id="back-game-${boardId}" onclick="backToGame('${boardId}')">Back to Game</button>
        </div>
        <div class="da-eval-chart-wrapper">
            <canvas id="chart-${boardId}"></canvas>
        </div>
        <div class="da-time-chart-wrapper ${showTimeChart ? '' : 'hidden'}" id="time-chart-wrap-${boardId}">
            <canvas id="time-chart-${boardId}"></canvas>
        </div>
    `;
    return card;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

// ------------------------------------------------------------------
// Board initialization
// ------------------------------------------------------------------

function initBoard(boardId, game) {
    const playerIsWhite = game.player_color === 'white';
    const orientation = playerIsWhite ? 'white' : 'black';

    const state = {
        boardId: boardId,
        game: game,
        moves: game.moves || [],
        currentPly: 0,
        playerIsWhite: playerIsWhite,
        orientation: orientation,
        exploreMode: false,
        exploreMoves: [],
        exploreBasePly: 0,
        chessGame: new Chess(),
        chessBoard: null,
        evalChart: null,
        timeChart: null,
        criticalPly: findCriticalPly(game),
    };

    boards[boardId] = state;

    const config = {
        draggable: true,
        position: 'start',
        orientation: orientation,
        pieceTheme: PIECE_THEME_PRIMARY,
        onDrop: (source, target) => onPieceDrop(boardId, source, target),
        onDragStart: (source, piece) => onDragStart(boardId, source, piece),
    };

    state.chessBoard = Chessboard(boardId, config);

    // Add fallback for piece images
    addPieceImageFallback(boardId);

    renderMoveList(boardId);
    renderEvalChart(boardId);
    if (hasClockData(state.moves)) {
        renderTimeChart(boardId);
    }

    if (state.criticalPly > 0) {
        goToPly(boardId, state.criticalPly);
    }
}

function addPieceImageFallback(boardId) {
    const container = document.getElementById(boardId);
    if (!container) return;
    const observer = new MutationObserver(() => {
        container.querySelectorAll('img[data-piece]').forEach(img => {
            if (!img.dataset.fallbackSet) {
                img.dataset.fallbackSet = 'true';
                img.onerror = function() {
                    const piece = this.getAttribute('data-piece') || '';
                    if (piece) {
                        this.src = PIECE_THEME_FALLBACK.replace('{piece}', piece);
                    }
                };
            }
        });
    });
    observer.observe(container, { childList: true, subtree: true });
}

function findCriticalPly(game) {
    if (!game.moves) return 0;
    const critMoveNum = game.critical_move_number;
    const playerColor = game.player_color;

    for (let i = 0; i < game.moves.length; i++) {
        const m = game.moves[i];
        if (m.move_number === critMoveNum && m.color === playerColor) {
            return i + 1;
        }
    }
    let maxCpl = 0;
    let maxIdx = 0;
    for (let i = 0; i < game.moves.length; i++) {
        if (game.moves[i].cpl > maxCpl && game.moves[i].is_player) {
            maxCpl = game.moves[i].cpl;
            maxIdx = i + 1;
        }
    }
    return maxIdx;
}

// ------------------------------------------------------------------
// Navigation
// ------------------------------------------------------------------

function goToPly(boardId, ply) {
    const state = boards[boardId];
    if (!state) return;

    ply = Math.max(0, Math.min(ply, state.moves.length));

    state.chessGame = new Chess();
    for (let i = 0; i < ply; i++) {
        state.chessGame.move(state.moves[i].san);
    }

    state.currentPly = ply;
    state.chessBoard.position(state.chessGame.fen(), true);

    // Re-apply fallback after position change
    addPieceImageFallback(boardId);

    updateEvalBar(boardId);
    updateBestMove(boardId);
    highlightCurrentMove(boardId);
    updateChartIndicator(boardId);

    if (state.exploreMode) {
        exitExploreMode(boardId);
    }
}

function navFirst(boardId) { goToPly(boardId, 0); }
function navPrev(boardId) {
    const s = boards[boardId];
    if (s) goToPly(boardId, s.currentPly - 1);
}
function navNext(boardId) {
    const s = boards[boardId];
    if (s) goToPly(boardId, s.currentPly + 1);
}
function navLast(boardId) {
    const s = boards[boardId];
    if (s) goToPly(boardId, s.moves.length);
}
function navMistake(boardId) {
    const s = boards[boardId];
    if (s) goToPly(boardId, s.criticalPly);
}

// ------------------------------------------------------------------
// Eval bar
// ------------------------------------------------------------------

function updateEvalBar(boardId) {
    const state = boards[boardId];
    if (!state) return;

    let cp = 0;
    if (state.currentPly > 0 && state.currentPly <= state.moves.length) {
        cp = state.moves[state.currentPly - 1].eval_after || 0;
    }

    const clamped = Math.max(-1000, Math.min(1000, cp));
    const whitePct = Math.round(50 + (clamped / 1000) * 50);
    const blackPct = 100 - whitePct;

    document.getElementById(`eval-black-${boardId}`).style.flexGrow = blackPct;
    document.getElementById(`eval-white-${boardId}`).style.flexGrow = whitePct;

    let displayVal;
    if (Math.abs(cp) >= 9900) {
        displayVal = cp > 0 ? 'M' : '-M';
    } else {
        displayVal = (cp / 100).toFixed(1);
        if (cp > 0) displayVal = '+' + displayVal;
    }
    document.getElementById(`eval-value-${boardId}`).textContent = displayVal;
}

// ------------------------------------------------------------------
// Best move label
// ------------------------------------------------------------------

function updateBestMove(boardId) {
    const state = boards[boardId];
    const el = document.getElementById(`best-${boardId}`);
    if (!state || !el) return;

    if (state.currentPly > 0 && state.currentPly <= state.moves.length) {
        const m = state.moves[state.currentPly - 1];
        if (m.is_player) {
            const match = m.san === m.best_move_san;
            if (match) {
                el.innerHTML = `Best: ${escapeHtml(m.best_move_san)} <span class="best-match">\u2713 You played the best move!</span>`;
            } else {
                el.innerHTML = `Best: <strong>${escapeHtml(m.best_move_san)}</strong> (you played ${escapeHtml(m.san)}${escapeHtml(m.annotation)})`;
            }
        } else {
            el.textContent = '';
        }
    } else {
        el.textContent = '';
    }
}

// ------------------------------------------------------------------
// Move list (with clock time)
// ------------------------------------------------------------------

function renderMoveList(boardId) {
    const state = boards[boardId];
    const container = document.getElementById(`moves-${boardId}`);
    if (!state || !container) return;

    let html = '';
    for (let i = 0; i < state.moves.length; i += 2) {
        const whiteMove = state.moves[i];
        const blackMove = state.moves[i + 1];
        const moveNum = whiteMove.move_number;

        const wClass = getMoveClass(whiteMove);
        const bClass = blackMove ? getMoveClass(blackMove) : '';

        const wClock = formatClockSpan(whiteMove);
        const bClock = blackMove ? formatClockSpan(blackMove) : '';

        html += `<div class="da-move-row" data-ply="${i + 1}">`;
        html += `<span class="da-move-num">${moveNum}.</span>`;
        html += `<span class="da-move-white ${wClass}" id="move-${boardId}-${i + 1}" onclick="goToPly('${boardId}', ${i + 1})">${escapeHtml(whiteMove.san)}${escapeHtml(whiteMove.annotation)}${wClock}</span>`;
        if (blackMove) {
            html += `<span class="da-move-black ${bClass}" id="move-${boardId}-${i + 2}" onclick="goToPly('${boardId}', ${i + 2})">${escapeHtml(blackMove.san)}${escapeHtml(blackMove.annotation)}${bClock}</span>`;
        }
        html += `</div>`;
    }
    container.innerHTML = html;
}

function formatClockSpan(move) {
    if (move.clock_time == null) return '';
    const timePressure = move.clock_time < 30 ? ' time-pressure' : '';
    return ` <span class="da-move-clock${timePressure}">${formatClockTime(move.clock_time)}</span>`;
}

function getMoveClass(move) {
    if (!move || !move.annotation) return '';
    if (move.annotation === '??') return 'da-move-blunder';
    if (move.annotation === '?') return 'da-move-mistake';
    if (move.annotation === '?!') return 'da-move-inaccuracy';
    if (move.annotation === '!!') return 'da-move-brilliant';
    if (move.annotation === '!') return 'da-move-good';
    return '';
}

function highlightCurrentMove(boardId) {
    const state = boards[boardId];
    if (!state) return;

    const container = document.getElementById(`moves-${boardId}`);
    if (!container) return;
    container.querySelectorAll('.da-move-active').forEach(el => el.classList.remove('da-move-active'));

    if (state.currentPly > 0) {
        const el = document.getElementById(`move-${boardId}-${state.currentPly}`);
        if (el) {
            el.classList.add('da-move-active');
            el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }
}

// ------------------------------------------------------------------
// Eval chart — Lichess-style area chart
// ------------------------------------------------------------------

function renderEvalChart(boardId) {
    const state = boards[boardId];
    if (!state) return;

    const canvas = document.getElementById(`chart-${boardId}`);
    if (!canvas) return;

    const labels = [];
    const dataPoints = [];

    for (let i = 0; i < state.moves.length; i++) {
        const m = state.moves[i];
        labels.push(m.move_number + (m.color === 'black' ? '...' : '.'));
        const evalPawns = (m.eval_after || 0) / 100;
        dataPoints.push(Math.max(-10, Math.min(10, evalPawns)));
    }

    // Custom plugin: vertical line at current ply & red line at critical ply
    const verticalLinePlugin = {
        id: 'verticalLine',
        afterDraw: (chart) => {
            const st = boards[boardId];
            if (!st) return;
            const ctx = chart.ctx;
            const xAxis = chart.scales.x;
            const yAxis = chart.scales.y;

            // Critical mistake line (red)
            if (st.criticalPly > 0 && st.criticalPly <= dataPoints.length) {
                const xCrit = xAxis.getPixelForValue(st.criticalPly - 1);
                ctx.save();
                ctx.strokeStyle = '#e74c3c';
                ctx.lineWidth = 2;
                ctx.setLineDash([4, 3]);
                ctx.beginPath();
                ctx.moveTo(xCrit, yAxis.top);
                ctx.lineTo(xCrit, yAxis.bottom);
                ctx.stroke();
                ctx.restore();
            }

            // Current ply line (blue)
            if (st.currentPly > 0 && st.currentPly <= dataPoints.length) {
                const xCur = xAxis.getPixelForValue(st.currentPly - 1);
                ctx.save();
                ctx.strokeStyle = '#3498db';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(xCur, yAxis.top);
                ctx.lineTo(xCur, yAxis.bottom);
                ctx.stroke();
                ctx.restore();
            }
        },
    };

    state.evalChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'White advantage',
                    data: dataPoints.map(v => Math.max(0, v)),
                    borderColor: 'rgba(200,200,200,0.8)',
                    backgroundColor: 'rgba(240,240,240,0.7)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: 'origin',
                    tension: 0.15,
                },
                {
                    label: 'Black advantage',
                    data: dataPoints.map(v => Math.min(0, v)),
                    borderColor: 'rgba(80,80,80,0.8)',
                    backgroundColor: 'rgba(60,60,60,0.5)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: 'origin',
                    tension: 0.15,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: (items) => items[0] ? `Move ${items[0].label}` : '',
                        label: (ctx) => {
                            const idx = ctx.dataIndex;
                            const val = dataPoints[idx];
                            return `Eval: ${val >= 0 ? '+' : ''}${val.toFixed(1)}`;
                        },
                    },
                    filter: (item) => item.datasetIndex === 0,
                },
            },
            scales: {
                x: { display: false },
                y: {
                    min: -10,
                    max: 10,
                    ticks: { display: false },
                    grid: {
                        color: ctx => ctx.tick.value === 0 ? '#999' : 'transparent',
                    },
                },
            },
            onClick: (evt, elements) => {
                if (elements.length > 0) {
                    const idx = elements[0].index;
                    goToPly(boardId, idx + 1);
                }
            },
        },
        plugins: [verticalLinePlugin],
    });
}

function updateChartIndicator(boardId) {
    const state = boards[boardId];
    if (!state || !state.evalChart) return;
    state.evalChart.update('none'); // trigger redraw for vertical line plugin
}

// ------------------------------------------------------------------
// Time usage chart
// ------------------------------------------------------------------

function renderTimeChart(boardId) {
    const state = boards[boardId];
    if (!state) return;

    const canvas = document.getElementById(`time-chart-${boardId}`);
    if (!canvas) return;

    const labels = [];
    const whiteTime = [];
    const blackTime = [];

    for (let i = 0; i < state.moves.length; i++) {
        const m = state.moves[i];
        const label = m.move_number + (m.color === 'black' ? '...' : '.');
        labels.push(label);
        if (m.color === 'white') {
            whiteTime.push(m.clock_time != null ? m.clock_time : null);
            blackTime.push(null);
        } else {
            whiteTime.push(null);
            blackTime.push(m.clock_time != null ? m.clock_time : null);
        }
    }

    state.timeChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'White',
                    data: whiteTime,
                    borderColor: '#bbb',
                    backgroundColor: 'rgba(200,200,200,0.15)',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1,
                    spanGaps: true,
                },
                {
                    label: 'Black',
                    data: blackTime,
                    borderColor: '#555',
                    backgroundColor: 'rgba(60,60,60,0.15)',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1,
                    spanGaps: true,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: { boxWidth: 12, font: { size: 10 } },
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: (ctx) => {
                            if (ctx.raw == null) return null;
                            return `${ctx.dataset.label}: ${formatClockTime(ctx.raw)}`;
                        },
                    },
                },
            },
            scales: {
                x: { display: false },
                y: {
                    beginAtZero: true,
                    ticks: { display: false },
                    grid: { display: false },
                },
            },
            onClick: (evt, elements) => {
                if (elements.length > 0) {
                    const idx = elements[0].index;
                    goToPly(boardId, idx + 1);
                }
            },
        },
    });
}

// ------------------------------------------------------------------
// Explore mode (piece drop)
// ------------------------------------------------------------------

function onDragStart(boardId, source, piece) {
    const state = boards[boardId];
    if (!state) return false;

    if (state.chessGame.game_over()) return false;
    if ((state.chessGame.turn() === 'w' && piece.search(/^b/) !== -1) ||
        (state.chessGame.turn() === 'b' && piece.search(/^w/) !== -1)) {
        return false;
    }
    return true;
}

function onPieceDrop(boardId, source, target) {
    const state = boards[boardId];
    if (!state) return 'snapback';

    const move = state.chessGame.move({
        from: source,
        to: target,
        promotion: 'q',
    });

    if (move === null) return 'snapback';

    const nextPly = state.currentPly + 1;
    if (!state.exploreMode && nextPly <= state.moves.length) {
        const expectedMove = state.moves[state.currentPly];
        if (expectedMove && move.san === expectedMove.san) {
            state.currentPly = nextPly;
            updateEvalBar(boardId);
            updateBestMove(boardId);
            highlightCurrentMove(boardId);
            updateChartIndicator(boardId);
            return;
        }
    }

    if (!state.exploreMode) {
        state.exploreMode = true;
        state.exploreBasePly = state.currentPly;
        state.exploreMoves = [];
        document.getElementById(`card-${boardId}`).classList.add('da-explore-mode');
        document.getElementById(`back-game-${boardId}`).classList.add('visible');
    }

    if (state.exploreMoves.length >= 5) {
        state.chessGame.undo();
        state.chessBoard.position(state.chessGame.fen(), false);
        return 'snapback';
    }

    state.exploreMoves.push(move);
    evaluateExplorePosition(boardId, state.chessGame.fen());
}

function evaluateExplorePosition(boardId, fen) {
    const state = boards[boardId];
    if (!state) return;

    fetch('/api/evaluate-position', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fen: fen }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.eval !== undefined) {
            const cp = data.eval;
            const clamped = Math.max(-1000, Math.min(1000, cp));
            const whitePct = Math.round(50 + (clamped / 1000) * 50);
            const blackPct = 100 - whitePct;
            document.getElementById(`eval-black-${boardId}`).style.flexGrow = blackPct;
            document.getElementById(`eval-white-${boardId}`).style.flexGrow = whitePct;

            let displayVal;
            if (data.mate) {
                displayVal = data.mate > 0 ? 'M' : '-M';
            } else {
                displayVal = (cp / 100).toFixed(1);
                if (cp > 0) displayVal = '+' + displayVal;
            }
            document.getElementById(`eval-value-${boardId}`).textContent = displayVal;

            const bestEl = document.getElementById(`best-${boardId}`);
            if (bestEl && data.best_move && data.best_move.san) {
                bestEl.innerHTML = `Explore mode \u2022 Best: <strong>${escapeHtml(data.best_move.san)}</strong>`;
            }
        }
    })
    .catch(() => {});
}

function backToGame(boardId) {
    exitExploreMode(boardId);
    goToPly(boardId, boards[boardId].exploreBasePly || boards[boardId].currentPly);
}

function exitExploreMode(boardId) {
    const state = boards[boardId];
    if (!state) return;
    state.exploreMode = false;
    state.exploreMoves = [];
    document.getElementById(`card-${boardId}`).classList.remove('da-explore-mode');
    document.getElementById(`back-game-${boardId}`).classList.remove('visible');
}

// ------------------------------------------------------------------
// Error display
// ------------------------------------------------------------------

function showError(title, message) {
    document.getElementById('daLoading').classList.add('hidden');
    document.getElementById('daBoardGrid').classList.add('hidden');
    const errorDiv = document.getElementById('daError');
    errorDiv.classList.remove('hidden');
    document.getElementById('daErrorTitle').textContent = title;
    document.getElementById('daErrorMessage').textContent = message;
}

// ------------------------------------------------------------------
// Keyboard navigation
// ------------------------------------------------------------------

document.addEventListener('keydown', function(e) {
    const boardIds = Object.keys(boards);
    if (boardIds.length === 0) return;

    const boardId = boardIds[0];

    if (e.key === 'ArrowLeft') { e.preventDefault(); navPrev(boardId); }
    if (e.key === 'ArrowRight') { e.preventDefault(); navNext(boardId); }
    if (e.key === 'Home') { e.preventDefault(); navFirst(boardId); }
    if (e.key === 'End') { e.preventDefault(); navLast(boardId); }
});
