// Analytics Dashboard JavaScript
// Handles form submission, data fetching, and visualization rendering

// Global variables
let charts = {};
let analysisData = null;

// Configure Chart.js defaults - disable datalabels plugin by default
Chart.register(ChartDataLabels);
Chart.defaults.set('plugins.datalabels', {
    display: false  // Disable by default, enable only for specific charts
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
});

function initializeDashboard() {
    // Set up form handlers
    const form = document.getElementById('analyticsForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // Set up date presets
    const presetButtons = document.querySelectorAll('.btn-preset');
    presetButtons.forEach(btn => {
        btn.addEventListener('click', handleDatePreset);
    });

    // PRD v2.2: Add real-time date range validation
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    if (startDateInput && endDateInput) {
        startDateInput.addEventListener('change', validateDateRange);
        endDateInput.addEventListener('change', validateDateRange);
    }

    // Auto-detect and set timezone
    detectAndSetTimezone();

    // Set default dates
    setDefaultDates();

    // Show empty state initially
    showEmptyState();
}

// Timezone Detection
function detectAndSetTimezone() {
    try {
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const timezoneSelect = document.getElementById('timezone');
        
        // Check if detected timezone is in the list
        const option = Array.from(timezoneSelect.options).find(opt => opt.value === timezone);
        
        if (option) {
            timezoneSelect.value = timezone;
        } else {
            // Add detected timezone as an option
            const newOption = new Option(`${timezone} (Auto-detected)`, timezone);
            timezoneSelect.insertBefore(newOption, timezoneSelect.firstChild);
            timezoneSelect.value = timezone;
        }
    } catch (error) {
        console.error('Error detecting timezone:', error);
    }
}

// Set Default Dates (Last 30 days)
function setDefaultDates() {
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    document.getElementById('endDate').valueAsDate = today;
    document.getElementById('startDate').valueAsDate = thirtyDaysAgo;
    
    // Set max date to today
    document.getElementById('endDate').max = today.toISOString().split('T')[0];
    document.getElementById('startDate').max = today.toISOString().split('T')[0];
}

// Handle Date Presets
function handleDatePreset(e) {
    const days = parseInt(e.target.dataset.days);
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - days);
    
    document.getElementById('endDate').valueAsDate = today;
    document.getElementById('startDate').valueAsDate = startDate;
    
    // PRD v2.2: Validate after preset selection
    validateDateRange();
}

// PRD v2.2: Validate date range (30-day maximum)
function validateDateRange() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const errorDiv = document.getElementById('dateRangeError');
    const submitBtn = document.getElementById('analyzeBtn');
    
    if (!startDate || !endDate) {
        errorDiv.style.display = 'none';
        submitBtn.disabled = false;
        return true;
    }
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    const today = new Date();
    today.setHours(23, 59, 59, 999); // End of today
    
    // Check if start is after end
    if (start > end) {
        errorDiv.textContent = 'Start date must be before end date';
        errorDiv.style.display = 'block';
        submitBtn.disabled = true;
        return false;
    }
    
    // Check if end date is in the future
    if (end > today) {
        errorDiv.textContent = 'End date cannot be in the future';
        errorDiv.style.display = 'block';
        submitBtn.disabled = true;
        return false;
    }
    
    // Check if range exceeds 30 days
    const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
    if (daysDiff > 30) {
        errorDiv.textContent = "Please select a date range of 30 days or less. For best results, use 'Last 7 days' or 'Last 30 days'.";
        errorDiv.style.display = 'block';
        submitBtn.disabled = true;
        return false;
    }
    
    // Valid range
    errorDiv.style.display = 'none';
    submitBtn.disabled = false;
    return true;
}

// Form Submission Handler
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    let timezone = document.getElementById('timezone').value;
    
    // PRD v2.2: Validate date range before submission
    if (!validateDateRange()) {
        return;
    }
    
    // Validate dates
    if (new Date(startDate) > new Date(endDate)) {
        showError('Start date must be before end date');
        return;
    }
    
    // Check date range (max 1 year)
    const daysDiff = (new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24);
    if (daysDiff > 365) {
        showError('Date range cannot exceed 1 year');
        return;
    }
    
    // Handle auto-detect timezone
    if (timezone === 'auto') {
        timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    }
    
    // Hide error and empty state
    hideError();
    hideEmptyState();
    hideDashboard();
    
    // Show loading state
    showLoading();
    
    try {
        // Simulate progress updates
        updateProgress(20, 'Fetching game data...');
        
        const response = await fetch('/api/analyze/detailed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                start_date: startDate,
                end_date: endDate,
                timezone: timezone,
                include_mistake_analysis: true,  // Enable Stockfish analysis
                include_ai_advice: true  // v2.5: Enable AI advisor
            })
        });
        
        updateProgress(60, 'Processing analytics...');
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze games');
        }
        
        updateProgress(90, 'Rendering visualizations...');
        
        // Store data globally
        analysisData = data;
        
        // Render dashboard
        await renderDashboard(data);
        
        updateProgress(100, 'Complete!');
        
        // Hide loading and show dashboard
        setTimeout(() => {
            hideLoading();
            showDashboard();
            scrollToDashboard();
        }, 500);
        
    } catch (error) {
        hideLoading();
        showError(error.message);
        showEmptyState();
    }
}

// Progress Updates
function updateProgress(percentage, message) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const loadingMessage = document.getElementById('loadingMessage');
    
    if (progressFill) progressFill.style.width = percentage + '%';
    if (progressText) progressText.textContent = percentage + '%';
    if (loadingMessage) loadingMessage.textContent = message;
}

// UI State Management
function showLoading() {
    document.getElementById('loadingState').classList.remove('hidden');
    document.getElementById('analyzeBtn').disabled = true;
}

function hideLoading() {
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('analyzeBtn').disabled = false;
    updateProgress(0, 'Fetching game data...');
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = '❌ ' + message;
    errorDiv.classList.remove('hidden');
    
    // Auto-hide after 10 seconds
    setTimeout(() => hideError(), 10000);
}

function hideError() {
    document.getElementById('error').classList.add('hidden');
}

function showEmptyState() {
    document.getElementById('emptyState').classList.remove('hidden');
}

function hideEmptyState() {
    document.getElementById('emptyState').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('dashboardResults').classList.remove('hidden');
}

function hideDashboard() {
    document.getElementById('dashboardResults').classList.add('hidden');
}

function scrollToDashboard() {
    const dashboard = document.getElementById('dashboardResults');
    if (dashboard) {
        dashboard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Main Dashboard Renderer
async function renderDashboard(data) {
    // Destroy existing charts
    destroyAllCharts();
    
    // Render header
    renderAnalysisHeader(data);
    
    // Render each section
    await renderOverallPerformance(data.sections.overall_performance);
    await renderColorPerformance(data.sections.color_performance);
    await renderEloProgression(data.sections.elo_progression);
    await renderTerminations(data.sections.termination_wins, data.sections.termination_losses);
    await renderOpeningPerformance(data.sections.opening_performance);
    await renderOpponentStrength(data.sections.opponent_strength);
    await renderTimeOfDay(data.sections.time_of_day);
    
    // Milestone 8: Mistake Analysis (if available)
    if (data.sections.mistake_analysis) {
        // Check if analysis is still processing
        if (data.sections.mistake_analysis.status === 'processing') {
            await showMistakeAnalysisLoading(data.sections.mistake_analysis);
        } else {
            await renderMistakeAnalysis(data.sections.mistake_analysis);
        }
    }
    
    // Milestone 9: AI Chess Advisor (if available)
    if (data.sections.ai_advice) {
        await renderAIAdvisor(data.sections.ai_advice, data);
    }
}

// Render Analysis Header
function renderAnalysisHeader(data) {
    document.getElementById('displayUsername').textContent = data.username;
    document.getElementById('displayPeriod').textContent = 
        `${formatDate(data.start_date)} - ${formatDate(data.end_date)}`;
    document.getElementById('displayTimezone').textContent = data.timezone;
    document.getElementById('displayTotalGames').textContent = 
        `${data.total_games} games analyzed`;
}

// Section 1: Overall Performance Over Time (Win Rate %)
async function renderOverallPerformance(data) {
    if (!data || !data.daily_stats || data.daily_stats.length === 0) {
        return;
    }
    
    const dates = data.daily_stats.map(d => d.date);
    const wins = data.daily_stats.map(d => d.wins);
    const losses = data.daily_stats.map(d => d.losses);
    const draws = data.daily_stats.map(d => d.draws);
    
    // Calculate win rate percentage for each day
    const winRates = data.daily_stats.map(d => {
        const total = d.wins + d.losses + d.draws;
        return total > 0 ? ((d.wins / total) * 100).toFixed(1) : 0;
    });
    
    const ctx = document.getElementById('overallPerformanceChart');
    charts.overall = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Win Rate %',
                    data: winRates,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: (context) => formatDate(context[0].label),
                        label: (context) => {
                            const index = context.dataIndex;
                            return [
                                `Win Rate: ${context.parsed.y}%`,
                                `Wins: ${wins[index]}`,
                                `Losses: ${losses[index]}`,
                                `Draws: ${draws[index]}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Win Rate %'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}

// Section 2: Color Performance (Unified Chart)
async function renderColorPerformance(data) {
    if (!data) return;
    
    // Render summary cards
    if (data.white) {
        renderColorSummary('whiteSummary', data.white, 'white');
    }
    if (data.black) {
        renderColorSummary('blackSummary', data.black, 'black');
    }
    
    // Render unified chart with both colors
    if (data.white && data.black && data.white.daily_stats && data.black.daily_stats) {
        renderUnifiedColorChart(data);
    }
}

function renderColorSummary(elementId, colorData, color) {
    const element = document.getElementById(elementId);
    const winRate = colorData.win_rate || 0;
    
    // Iteration 5: Use explicit W/L/D counts from backend
    const total = colorData.total_games || 0;
    const wins = colorData.wins || 0;
    const losses = colorData.losses || 0;
    const draws = colorData.draws || 0;
    
    const textColor = color === 'black' ? '#ffffff' : '#2c3e50';
    
    element.innerHTML = `
        <div class="color-stat-item">
            <span class="color-stat-label" style="color: ${textColor};">Total Games</span>
            <span class="color-stat-value" style="color: ${textColor};">${total}</span>
        </div>
        <div class="color-stat-item">
            <span class="color-stat-label" style="color: ${textColor};">Win Rate</span>
            <span class="color-stat-value" style="color: ${color === 'white' ? '#27ae60' : '#2ecc71'};">${winRate.toFixed(1)}%</span>
        </div>
        <div class="color-stat-item">
            <span class="color-stat-label" style="color: ${textColor};">Wins</span>
            <span class="color-stat-value" style="color: ${color === 'white' ? '#27ae60' : '#2ecc71'};">${wins}</span>
        </div>
        <div class="color-stat-item">
            <span class="color-stat-label" style="color: ${textColor};">Losses</span>
            <span class="color-stat-value" style="color: ${color === 'white' ? '#e74c3c' : '#c0392b'};">${losses}</span>
        </div>
        <div class="color-stat-item">
            <span class="color-stat-label" style="color: ${textColor};">Draws</span>
            <span class="color-stat-value" style="color: ${color === 'white' ? '#f39c12' : '#e67e22'};">${draws}</span>
        </div>
    `;
}

function renderUnifiedColorChart(data) {
    // Get all unique dates from both colors
    const whiteDates = data.white.daily_stats.map(d => d.date);
    const blackDates = data.black.daily_stats.map(d => d.date);
    const allDates = [...new Set([...whiteDates, ...blackDates])].sort();
    
    // Calculate win rates for each color by date
    const whiteWinRates = allDates.map(date => {
        const stat = data.white.daily_stats.find(d => d.date === date);
        if (!stat) return null;
        const total = stat.wins + stat.losses + stat.draws;
        return total > 0 ? ((stat.wins / total) * 100).toFixed(1) : 0;
    });
    
    const blackWinRates = allDates.map(date => {
        const stat = data.black.daily_stats.find(d => d.date === date);
        if (!stat) return null;
        const total = stat.wins + stat.losses + stat.draws;
        return total > 0 ? ((stat.wins / total) * 100).toFixed(1) : 0;
    });
    
    // Store detailed data for tooltips
    const whiteDetails = allDates.map(date => {
        const stat = data.white.daily_stats.find(d => d.date === date);
        return stat || { wins: 0, losses: 0, draws: 0 };
    });
    
    const blackDetails = allDates.map(date => {
        const stat = data.black.daily_stats.find(d => d.date === date);
        return stat || { wins: 0, losses: 0, draws: 0 };
    });
    
    const ctx = document.getElementById('colorPerformanceChart');
    charts.colorPerformance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allDates,
            datasets: [
                {
                    label: 'White Win Rate',
                    data: whiteWinRates,
                    borderColor: '#95a5a6',
                    backgroundColor: 'rgba(149, 165, 166, 0.1)',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#ecf0f1',
                    pointBorderColor: '#95a5a6',
                    pointBorderWidth: 2
                },
                {
                    label: 'Black Win Rate',
                    data: blackWinRates,
                    borderColor: '#34495e',
                    backgroundColor: 'rgba(52, 73, 94, 0.1)',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#2c3e50',
                    pointBorderColor: '#34495e',
                    pointBorderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: (context) => formatDate(context[0].label),
                        label: (context) => {
                            const index = context.dataIndex;
                            const isWhite = context.datasetIndex === 0;
                            const details = isWhite ? whiteDetails[index] : blackDetails[index];
                            const color = isWhite ? 'White' : 'Black';
                            
                            return [
                                `${color} Win Rate: ${context.parsed.y}%`,
                                `Wins: ${details.wins}`,
                                `Losses: ${details.losses}`,
                                `Draws: ${details.draws}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Win Rate %'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}

// Section 3: Elo Progression
async function renderEloProgression(data) {
    if (!data || !data.data_points || data.data_points.length === 0) {
        return;
    }
    
    const dates = data.data_points.map(d => d.date);
    const ratings = data.data_points.map(d => d.rating);
    
    const ctx = document.getElementById('eloProgressionChart');
    charts.elo = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Elo Rating',
                data: ratings,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.3,
                fill: true,
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: (context) => formatDate(context[0].label),
                        label: (context) => `Rating: ${context.parsed.y}`
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Rating'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
    
    // Render stats
    const statsElement = document.getElementById('eloStats');
    const change = data.rating_change || 0;
    const changeColor = change >= 0 ? '#27ae60' : '#e74c3c';
    const changeSign = change >= 0 ? '+' : '';
    
    statsElement.innerHTML = `
        <div class="stat-item">
            <span class="stat-label">Rating Change</span>
            <span class="stat-number" style="color: ${changeColor};">
                ${changeSign}${change}
            </span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Start Rating</span>
            <span class="stat-number">${ratings[0]}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">End Rating</span>
            <span class="stat-number">${ratings[ratings.length - 1]}</span>
        </div>
    `;
}

// Section 4 & 5: Terminations
async function renderTerminations(winsData, lossesData) {
    if (winsData && winsData.breakdown) {
        renderTerminationChart('terminationWinsChart', winsData.breakdown, winsData.total_wins);
        renderTerminationLegend('terminationWinsLegend', winsData.breakdown, winsData.total_wins);
    }
    
    if (lossesData && lossesData.breakdown) {
        renderTerminationChart('terminationLossesChart', lossesData.breakdown, lossesData.total_losses);
        renderTerminationLegend('terminationLossesLegend', lossesData.breakdown, lossesData.total_losses);
    }
}

function renderTerminationChart(canvasId, breakdown, total) {
    const labels = Object.keys(breakdown).map(key => capitalizeFirst(key));
    const values = Object.values(breakdown);
    const colors = [
        '#3498db',
        '#e74c3c',
        '#f39c12',
        '#9b59b6',
        '#1abc9c',
        '#34495e'
    ];
    
    const ctx = document.getElementById(canvasId);
    charts[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors.slice(0, labels.length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                },
                datalabels: {
                    color: '#fff',
                    font: {
                        weight: 'bold',
                        size: 14
                    },
                    formatter: (value, context) => {
                        // Iteration 5: Show only the count (number)
                        return value;
                    },
                    // Only show label if segment is large enough
                    display: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        const percentage = (value / total) * 100;
                        return percentage > 5; // Show label if > 5% of total
                    }
                }
            }
        }
    });
}

function renderTerminationLegend(elementId, breakdown, total) {
    const element = document.getElementById(elementId);
    const colors = ['#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e'];
    
    let html = '';
    Object.entries(breakdown).forEach(([key, count], index) => {
        const percentage = (count / total) * 100;
        html += `
            <div class="legend-item">
                <div class="legend-color" style="background-color: ${colors[index]};"></div>
                <span>${capitalizeFirst(key)}: ${count} (${percentage.toFixed(1)}%)</span>
            </div>
        `;
    });
    
    element.innerHTML = html;
}

// Section 6: Opening Performance
async function renderOpeningPerformance(data) {
    if (!data) return;
    
    // v2.5: Backend returns separate lists for white and black
    // {white: [...], black: [...]} where each is top 5 most common by frequency
    const whiteOpenings = data.white || [];
    const blackOpenings = data.black || [];
    
    // Render white openings section
    if (whiteOpenings.length > 0) {
        const whiteContainer = document.getElementById('whiteOpeningsSection');
        if (whiteContainer) {
            whiteContainer.style.display = 'block';
            const title = whiteContainer.querySelector('.section-title');
            if (title) {
                title.textContent = `♔ Top ${whiteOpenings.length} Most Common Openings (White)`;
            }
            renderOpeningsTable('whiteOpeningsTable', whiteOpenings, 'white');
        }
    }
    
    // Render black openings section
    if (blackOpenings.length > 0) {
        const blackContainer = document.getElementById('blackOpeningsSection');
        if (blackContainer) {
            blackContainer.style.display = 'block';
            const title = blackContainer.querySelector('.section-title');
            if (title) {
                title.textContent = `♚ Top ${blackOpenings.length} Most Common Openings (Black)`;
            }
            renderOpeningsTable('blackOpeningsTable', blackOpenings, 'black');
        }
    }
}

function renderOpeningsTable(elementId, openings, color) {
    // Iteration 5: Display first 6 moves, Lichess URL, and Chess.com game URL
    const element = document.getElementById(elementId);
    if (!element) return;
    
    let html = '';
    
    openings.forEach((opening, index) => {
        const colorIcon = color === 'white' ? '♔' : '♚';
        html += `
            <div class="opening-row">
                <div class="opening-header">
                    <div class="opening-name">${colorIcon} ${opening.opening}</div>
                    <div class="opening-games">${opening.games} games</div>
                </div>
                <div class="opening-details">
                    <div class="opening-moves">
                        <strong>First 6 Moves:</strong> ${opening.first_moves || 'N/A'}
                    </div>
                    <div class="opening-links">
                        ${opening.lichess_url ? `<a href="${opening.lichess_url}" target="_blank" class="opening-link">🔗 View on Lichess</a>` : ''}
                        ${opening.example_game_url ? `<a href="${opening.example_game_url}" target="_blank" class="opening-link">🔗 Example Game</a>` : ''}
                    </div>
                </div>
                <div class="opening-stats">
                    <div class="opening-stat">
                        <span class="opening-stat-label">W</span>
                        <span class="opening-stat-value" style="color: #27ae60;">${opening.wins}</span>
                    </div>
                    <div class="opening-stat">
                        <span class="opening-stat-label">L</span>
                        <span class="opening-stat-value" style="color: #e74c3c;">${opening.losses}</span>
                    </div>
                    <div class="opening-stat">
                        <span class="opening-stat-label">D</span>
                        <span class="opening-stat-value" style="color: #95a5a6;">${opening.draws}</span>
                    </div>
                    <div class="opening-stat">
                        <span class="opening-stat-label">Win Rate</span>
                        <span class="opening-stat-value">${(opening.win_rate || 0).toFixed(1)}%</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    element.innerHTML = html;
}

// Section 7: Opponent Strength
async function renderOpponentStrength(data) {
    if (!data || !data.by_rating_diff) return;
    
    const categories = data.by_rating_diff;
    
    // Render cards for each category that has games
    if (categories.much_lower && categories.much_lower.games > 0) {
        renderStrengthCard('muchLowerRatedCard', categories.much_lower, 'much_lower');
    }
    if (categories.lower && categories.lower.games > 0) {
        renderStrengthCard('lowerRatedCard', categories.lower, 'lower');
    }
    if (categories.similar && categories.similar.games > 0) {
        renderStrengthCard('similarRatedCard', categories.similar, 'similar');
    }
    if (categories.higher && categories.higher.games > 0) {
        renderStrengthCard('higherRatedCard', categories.higher, 'higher');
    }
    if (categories.much_higher && categories.much_higher.games > 0) {
        renderStrengthCard('muchHigherRatedCard', categories.much_higher, 'much_higher');
    }
}

function renderStrengthCard(elementId, data, type) {
    const card = document.getElementById(elementId);
    if (!card) {
        console.warn(`Element '${elementId}' not found in DOM, skipping render`);
        return;
    }
    
    const statsDiv = card.querySelector('.strength-stats');
    if (!statsDiv) {
        console.warn(`Stats div not found in '${elementId}'`);
        return;
    }
    
    const winRate = data.win_rate || 0;
    const color = winRate >= 50 ? '#27ae60' : '#e74c3c';
    
    statsDiv.innerHTML = `
        <div class="strength-win-rate" style="color: ${color};">
            ${(winRate || 0).toFixed(1)}%
        </div>
        <div class="strength-stat-row">
            <span>Games:</span>
            <strong>${data.games}</strong>
        </div>
        <div class="strength-stat-row">
            <span>Wins:</span>
            <strong style="color: #27ae60;">${data.wins}</strong>
        </div>
        <div class="strength-stat-row">
            <span>Losses:</span>
            <strong style="color: #e74c3c;">${data.losses}</strong>
        </div>
        <div class="strength-stat-row">
            <span>Draws:</span>
            <strong style="color: #95a5a6;">${data.draws}</strong>
        </div>
    `;
}

// Note: Bar chart removed for Section 7 per Milestone 7 requirements
// Only card-based display is used

// Section 8: Time of Day Performance
async function renderTimeOfDay(data) {
    if (!data) return;
    
    // PRD v2.1: Display timezone in Section 8 header
    const timezoneSelect = document.getElementById('timezone');
    let timezone = timezoneSelect ? timezoneSelect.value : 'auto';
    
    if (timezone === 'auto') {
        timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    }
    
    // Display timezone abbreviation
    const timezoneDisplay = document.getElementById('timezoneDisplay');
    if (timezoneDisplay) {
        // Get timezone abbreviation (e.g., EST, PST, GMT+8)
        const date = new Date();
        const shortTz = date.toLocaleString('en-US', { 
            timeZone: timezone, 
            timeZoneName: 'short' 
        }).split(' ').pop();
        
        timezoneDisplay.textContent = `(${shortTz})`;
    }
    
    // Render cards for each time period that has games
    if (data.morning && data.morning.games > 0) {
        renderTimeCard('morningCard', data.morning);
    }
    if (data.afternoon && data.afternoon.games > 0) {
        renderTimeCard('afternoonCard', data.afternoon);
    }
    if (data.evening && data.evening.games > 0) {
        renderTimeCard('eveningCard', data.evening);
    }
    if (data.night && data.night.games > 0) {
        renderTimeCard('nightCard', data.night);
    }
}

function renderTimeCard(elementId, data) {
    const card = document.getElementById(elementId);
    if (!card) {
        console.warn(`Element '${elementId}' not found in DOM, skipping render`);
        return;
    }
    
    const statsDiv = card.querySelector('.time-stats');
    if (!statsDiv) {
        console.warn(`Stats div not found in '${elementId}'`);
        return;
    }
    
    const winRate = data.win_rate || 0;
    const color = winRate >= 50 ? '#27ae60' : '#e74c3c';
    
    statsDiv.innerHTML = `
        <div class="time-win-rate" style="color: ${color};">
            ${(winRate || 0).toFixed(1)}%
        </div>
        <div class="time-stat-row">
            <span>Games:</span>
            <strong>${data.games}</strong>
        </div>
        <div class="time-stat-row">
            <span>Wins:</span>
            <strong style="color: #27ae60;">${data.wins}</strong>
        </div>
        <div class="time-stat-row">
            <span>Losses:</span>
            <strong style="color: #e74c3c;">${data.losses}</strong>
        </div>
        <div class="time-stat-row">
            <span>Draws:</span>
            <strong style="color: #95a5a6;">${data.draws}</strong>
        </div>
    `;
}

// Note: Bar chart removed for Section 8 per Milestone 7 requirements
// Only card-based display is used

// ==================== MILESTONE 8: MISTAKE ANALYSIS RENDERING ====================

// Milestone 8: Mistake Analysis - Async Loading
async function showMistakeAnalysisLoading(processingInfo) {
    const section = document.getElementById('mistakeAnalysisSection');
    if (!section) return;
    
    // Show section
    section.style.display = 'block';
    
    // Clear any existing content
    const sampleInfo = document.getElementById('mistakeAnalysisSampleInfo');
    const summaryCards = section.querySelector('.mistake-summary-cards');
    const tableContainer = section.querySelector('.table-container');
    
    if (sampleInfo) {
        sampleInfo.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <span class="loading-text">
                    ${processingInfo.message} (Estimated: ${processingInfo.estimated_time})
                </span>
            </div>
        `;
        sampleInfo.className = 'alert alert-info';
    }
    
    // Hide summary cards and table while loading
    if (summaryCards) summaryCards.style.display = 'none';
    if (tableContainer) tableContainer.style.display = 'none';
    
    // Start polling for results
    startMistakeAnalysisPolling(processingInfo.task_id);
}

// Poll for mistake analysis results
function startMistakeAnalysisPolling(taskId, intervalMs = 2000) {
    console.log(`Starting polling for task ${taskId}`);
    
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/analyze/mistake-status/${taskId}`);
            const result = await response.json();
            
            if (result.status === 'completed') {
                // Stop polling
                clearInterval(pollInterval);
                console.log('Mistake analysis completed!');
                
                // Render results
                await renderMistakeAnalysis(result.data);
                
                // Show success message briefly
                const sampleInfo = document.getElementById('mistakeAnalysisSampleInfo');
                if (sampleInfo) {
                    const originalContent = sampleInfo.innerHTML;
                    sampleInfo.innerHTML = '<span style="color: green;">✓ Analysis complete!</span>';
                    sampleInfo.className = 'alert alert-success';
                    
                    // Restore normal display after 2 seconds
                    setTimeout(() => {
                        renderMistakeSampleInfo(result.data);
                    }, 2000);
                }
                
            } else if (result.status === 'processing') {
                // Update progress message
                const loadingText = document.querySelector('.loading-text');
                if (loadingText) {
                    const progress = result.progress;
                    loadingText.textContent = `Analyzing games: ${progress.current}/${progress.total} (${progress.percentage}%) - ${result.estimated_remaining} remaining`;
                }
                
            } else if (result.status === 'error') {
                // Stop polling
                clearInterval(pollInterval);
                console.error('Mistake analysis failed:', result.error);
                
                // Show error message
                const sampleInfo = document.getElementById('mistakeAnalysisSampleInfo');
                if (sampleInfo) {
                    sampleInfo.innerHTML = `<span style="color: red;">❌ Analysis failed: ${result.error}</span>`;
                    sampleInfo.className = 'alert alert-danger';
                }
                
            } else if (result.status === 'not_found') {
                // Task expired or doesn't exist
                clearInterval(pollInterval);
                console.error('Task not found');
                
                const sampleInfo = document.getElementById('mistakeAnalysisSampleInfo');
                if (sampleInfo) {
                    sampleInfo.innerHTML = '<span style="color: orange;">⚠️ Analysis task expired. Please refresh and try again.</span>';
                    sampleInfo.className = 'alert alert-warning';
                }
            }
            
        } catch (error) {
            // Stop polling on network error
            clearInterval(pollInterval);
            console.error('Error polling for mistake analysis:', error);
            
            const sampleInfo = document.getElementById('mistakeAnalysisSampleInfo');
            if (sampleInfo) {
                sampleInfo.innerHTML = '<span style="color: red;">❌ Network error while checking analysis status</span>';
                sampleInfo.className = 'alert alert-danger';
            }
        }
    }, intervalMs);
}

async function renderMistakeAnalysis(data) {
    const section = document.getElementById('mistakeAnalysisSection');
    if (!section) return;
    
    // Show section
    section.style.display = 'block';
    
    // Render sample info
    renderMistakeSampleInfo(data);
    
    // Render summary cards
    renderMistakeSummary(data);
    
    // Render mistake table
    renderMistakeTable(data);
}

function renderMistakeSampleInfo(data) {
    const sampleInfo = document.getElementById('mistakeAnalysisSampleInfo');
    if (!sampleInfo) return;
    
    const sample_info = data.sample_info || {};
    const totalGames = sample_info.total_games || 0;
    const analyzedGames = sample_info.analyzed_games || 0;
    const samplePercentage = sample_info.sample_percentage || 0;
    
    // Only show if we have data
    if (totalGames > 0) {
        // Count how many games actually have mistakes
        const totalMistakes = (data.early?.inaccuracies || 0) + (data.early?.mistakes || 0) + (data.early?.blunders || 0) +
                              (data.middle?.inaccuracies || 0) + (data.middle?.mistakes || 0) + (data.middle?.blunders || 0) +
                              (data.endgame?.inaccuracies || 0) + (data.endgame?.mistakes || 0) + (data.endgame?.blunders || 0);
        
        let infoText = `📊 Analyzed ${analyzedGames} game${analyzedGames !== 1 ? 's' : ''} out of ${totalGames} total games`;
        if (samplePercentage > 0 && samplePercentage < 100) {
            infoText += ` (${samplePercentage}%)`;
        }
        infoText += `.`;
        
        // Add information about mistakes found if relevant
        if (totalMistakes > 0) {
            infoText += ` Found ${totalMistakes} significant mistake${totalMistakes !== 1 ? 's' : ''} (50+ centipawns loss).`;
        } else {
            infoText += ` No significant mistakes found (50+ centipawns loss).`;
        }
        
        sampleInfo.textContent = infoText;
    } else {
        sampleInfo.textContent = '📊 No games analyzed.';
    }
}

function renderMistakeSummary(data) {
    // Show summary cards (in case they were hidden during loading)
    const summaryCards = document.getElementById('mistakeSummary');
    if (summaryCards) {
        summaryCards.style.display = 'flex';
    }
    
    // Weakest stage
    const weakestStage = document.getElementById('weakestStage');
    if (weakestStage) {
        // v2.6: Format with lowercase as per PRD
        const stageFormatted = (data.weakest_stage || 'N/A').toLowerCase();
        weakestStage.textContent = stageFormatted;
    }
    
    // v2.6: Removed "Most Common Error" card - no longer displayed
    
    // Total mistakes
    const totalMistakes = document.getElementById('totalMistakes');
    if (totalMistakes) {
        const total = (data.early?.inaccuracies || 0) + (data.early?.mistakes || 0) + (data.early?.blunders || 0) +
                      (data.middle?.inaccuracies || 0) + (data.middle?.mistakes || 0) + (data.middle?.blunders || 0) +
                      (data.endgame?.inaccuracies || 0) + (data.endgame?.mistakes || 0) + (data.endgame?.blunders || 0);
        totalMistakes.textContent = total;
    }
}

function identifyMostCommonError(data) {
    let maxCount = 0;
    let maxError = 'None detected';
    
    const stages = [
        { name: 'early', display: 'early game' },
        { name: 'middle', display: 'middlegame' },
        { name: 'endgame', display: 'endgame' }
    ];
    
    const errorTypes = [
        { key: 'blunders', display: 'blunders' },
        { key: 'mistakes', display: 'mistakes' },
        { key: 'inaccuracies', display: 'inaccuracies' }
    ];
    
    stages.forEach(stage => {
        errorTypes.forEach(error => {
            const count = data[stage.name]?.[error.key] || 0;
            if (count > maxCount) {
                maxCount = count;
                maxError = `${error.display} in ${stage.display}`;
            }
        });
    });
    
    return maxError;
}

function renderMistakeTable(data) {
    const tbody = document.getElementById('mistakeTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    // Show table container (in case it was hidden during loading)
    const tableContainer = document.querySelector('.table-container');
    if (tableContainer) {
        tableContainer.style.display = 'block';
    }
    
    const sampleInfo = data.sample_info || {};
    const analyzedGames = sampleInfo.analyzed_games || 0;
    
    // v2.7: Add "Number of games" row as first row
    const headerRow = document.createElement('tr');
    headerRow.classList.add('games-count-row');
    
    const labelCell = document.createElement('td');
    labelCell.innerHTML = '<strong>Number of games</strong>';
    headerRow.appendChild(labelCell);
    
    const countCell = document.createElement('td');
    countCell.colSpan = 3;
    countCell.classList.add('games-count-value');
    countCell.innerHTML = `<strong>${analyzedGames}</strong>`;
    headerRow.appendChild(countCell);
    
    tbody.appendChild(headerRow);
    
    // v2.6: Updated stage labels and display order
    const stages = [
        { key: 'early', display: 'early game (1-10 moves)', class: 'stage-early' },
        { key: 'middle', display: 'middle games (sample 10 consecutive moves)', class: 'stage-middle' },
        { key: 'endgame', display: 'late game (last 10 moves)', class: 'stage-endgame' }
    ];
    
    stages.forEach(stage => {
        const stageData = data[stage.key] || {};
        const row = document.createElement('tr');
        
        // Game Stage label
        const stageCell = document.createElement('td');
        stageCell.innerHTML = `<span class="stage-name ${stage.class}">${stage.display}</span>`;
        row.appendChild(stageCell);
        
        // v2.6: Column order changed to Mistake | Neutral | Brilliant
        
        // Avg Mistakes/Game (FIRST column - prioritize weaknesses)
        const mistakeCell = document.createElement('td');
        const avgMistakes = stageData.avg_mistakes_per_game || 0;
        mistakeCell.innerHTML = getMoveQualityHTML(avgMistakes, 'mistake');
        row.appendChild(mistakeCell);
        
        // Avg Neutral/Game (SECOND column)
        const neutralCell = document.createElement('td');
        const avgNeutral = stageData.avg_neutral_per_game || 0;
        neutralCell.innerHTML = getMoveQualityHTML(avgNeutral, 'neutral');
        row.appendChild(neutralCell);
        
        // Avg Brilliant/Game (THIRD column)
        const brilliantCell = document.createElement('td');
        const avgBrilliant = stageData.avg_brilliant_per_game || 0;
        brilliantCell.innerHTML = getMoveQualityHTML(avgBrilliant, 'brilliant');
        row.appendChild(brilliantCell);
        
        // v2.6: Removed "Total Games Analyzed" column - shown in sample info instead
        
        tbody.appendChild(row);
    });
}

function getMoveQualityHTML(avg, type) {
    const value = avg.toFixed(1);
    let className = 'move-quality';
    
    if (type === 'brilliant') {
        // Higher is better for brilliant moves
        if (avg >= 2.0) {
            className += ' quality-high';
        } else if (avg >= 1.0) {
            className += ' quality-medium';
        } else {
            className += ' quality-low';
        }
    } else if (type === 'mistake') {
        // Lower is better for mistakes
        if (avg >= 3.0) {
            className += ' quality-high-bad';  // Many mistakes
        } else if (avg >= 1.5) {
            className += ' quality-medium-bad';
        } else {
            className += ' quality-low-good';  // Few mistakes
        }
    } else {
        // Neutral moves - no color coding needed
        className += ' quality-neutral';
    }
    
    return `<span class="${className}">${value}</span>`;
}

function getMistakeCountHTML(count, isBlunder = false) {
    if (count === 0) {
        return `<span class="mistake-count mistake-count-low">${count}</span>`;
    } else if (isBlunder || count >= 10) {
        return `<span class="mistake-count mistake-count-high">${count}</span>`;
    } else if (count >= 5) {
        return `<span class="mistake-count mistake-count-medium">${count}</span>`;
    } else {
        return `<span class="mistake-count">${count}</span>`;
    }
}

function getCPLossHTML(cpLoss) {
    let className = 'cp-loss';
    const loss = cpLoss || 0;
    if (loss >= 80) {
        className += ' cp-loss-high';
    } else if (loss >= 50) {
        className += ' cp-loss-medium';
    } else {
        className += ' cp-loss-low';
    }
    
    return `<span class="${className}">-${loss.toFixed(1)}</span>`;
}

// ==================== MILESTONE 9: AI ADVISOR RENDERING ====================

async function renderAIAdvisor(aiData, fullData) {
    const section = document.getElementById('aiAdvisorSection');
    if (!section) return;
    
    // Show section
    section.style.display = 'block';
    
    // Update context description
    const contextElement = document.getElementById('aiAdvisorContext');
    if (contextElement && fullData.total_games) {
        contextElement.textContent = `Based on your ${fullData.total_games} games from ${fullData.start_date} to ${fullData.end_date}`;
    }
    
    // Hide loading, show content
    const loading = document.getElementById('aiLoading');
    const content = document.getElementById('aiContent');
    const error = document.getElementById('aiError');
    
    if (loading) loading.style.display = 'none';
    if (error) error.style.display = 'none';
    
    if (content) {
        content.style.display = 'block';
        
        // v2.8: Render section suggestions only (no overall recommendation)
        renderAISectionSuggestions(aiData.section_suggestions || []);
    }
}

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

function renderAISuggestions(suggestions) {
    const list = document.getElementById('aiSuggestionsList');
    if (!list) return;
    
    list.innerHTML = '';
    
    if (!suggestions || suggestions.length === 0) {
        list.innerHTML = '<li>No specific suggestions available at this time.</li>';
        return;
    }
    
    suggestions.forEach(suggestion => {
        const li = document.createElement('li');
        
        // Handle both structured format (new) and plain string format (fallback)
        if (typeof suggestion === 'object' && suggestion.advice) {
            // Structured format: {section_number, section_name, advice}
            const sectionLabel = `<strong>Section ${suggestion.section_number} (${suggestion.section_name}):</strong> `;
            li.innerHTML = sectionLabel + suggestion.advice;
        } else {
            // Plain string format (legacy)
            li.textContent = suggestion;
        }
        
        list.appendChild(li);
    });
}

function renderAIOverall(recommendation) {
    const element = document.getElementById('aiOverallRecommendation');
    if (!element) return;
    
    // v2.6: Recommendation is already formatted as bullet points from backend
    if (recommendation) {
        // Convert newlines to HTML breaks for display
        element.innerHTML = recommendation.replace(/\n/g, '<br>');
    } else {
        element.innerHTML = '• Continue analyzing your games and focus on consistent improvement.';
    }
}

function renderAICostInfo(tokens, cost) {
    const costInfo = document.getElementById('aiCostInfo');
    if (!costInfo) return;
    
    // Only show in development mode (you can add a config flag)
    const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    if (isDev) {
        document.getElementById('tokensUsed').textContent = tokens;
        document.getElementById('estimatedCost').textContent = (cost || 0).toFixed(4);
        costInfo.style.display = 'block';
    }
}

// Utility Functions
function destroyAllCharts() {
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    charts = {};
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    });
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
