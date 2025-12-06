// Analytics Dashboard JavaScript
// Handles form submission, data fetching, and visualization rendering

// Global variables
let charts = {};
let analysisData = null;

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
}

// Form Submission Handler
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    let timezone = document.getElementById('timezone').value;
    
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
                timezone: timezone
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

// Section 1: Overall Performance Over Time
async function renderOverallPerformance(data) {
    if (!data || !data.daily_stats || data.daily_stats.length === 0) {
        return;
    }
    
    const dates = data.daily_stats.map(d => d.date);
    const wins = data.daily_stats.map(d => d.wins);
    const losses = data.daily_stats.map(d => d.losses);
    const draws = data.daily_stats.map(d => d.draws);
    
    const ctx = document.getElementById('overallPerformanceChart');
    charts.overall = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Wins',
                    data: wins,
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Losses',
                    data: losses,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Draws',
                    data: draws,
                    borderColor: '#95a5a6',
                    backgroundColor: 'rgba(149, 165, 166, 0.1)',
                    tension: 0.3,
                    fill: true
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
                        label: (context) => `${context.dataset.label}: ${context.parsed.y} games`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Games'
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

// Section 2: Color Performance
async function renderColorPerformance(data) {
    if (!data) return;
    
    // Render White performance
    if (data.white && data.white.daily_stats) {
        renderColorChart('whitePerformanceChart', data.white.daily_stats, 'White');
        renderColorStats('whiteStats', data.white);
    }
    
    // Render Black performance
    if (data.black && data.black.daily_stats) {
        renderColorChart('blackPerformanceChart', data.black.daily_stats, 'Black');
        renderColorStats('blackStats', data.black);
    }
}

function renderColorChart(canvasId, dailyStats, color) {
    const dates = dailyStats.map(d => d.date);
    const wins = dailyStats.map(d => d.wins);
    const losses = dailyStats.map(d => d.losses);
    const draws = dailyStats.map(d => d.draws);
    
    const ctx = document.getElementById(canvasId);
    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Wins',
                    data: wins,
                    backgroundColor: '#27ae60'
                },
                {
                    label: 'Losses',
                    data: losses,
                    backgroundColor: '#e74c3c'
                },
                {
                    label: 'Draws',
                    data: draws,
                    backgroundColor: '#95a5a6'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
}

function renderColorStats(elementId, colorData) {
    const element = document.getElementById(elementId);
    const winRate = colorData.win_rate || 0;
    const total = (colorData.daily_stats || []).reduce((sum, d) => 
        sum + d.wins + d.losses + d.draws, 0);
    
    element.innerHTML = `
        <div class="stat-item">
            <span class="stat-label">Win Rate</span>
            <span class="stat-number" style="color: #27ae60;">${winRate.toFixed(1)}%</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Total Games</span>
            <span class="stat-number">${total}</span>
        </div>
    `;
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
    if (winsData) {
        renderTerminationChart('terminationWinsChart', winsData, 'wins');
        renderTerminationLegend('terminationWinsLegend', winsData);
    }
    
    if (lossesData) {
        renderTerminationChart('terminationLossesChart', lossesData, 'losses');
        renderTerminationLegend('terminationLossesLegend', lossesData);
    }
}

function renderTerminationChart(canvasId, data, type) {
    const labels = Object.keys(data).map(key => capitalizeFirst(key));
    const values = Object.values(data).map(v => v.count);
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
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderTerminationLegend(elementId, data) {
    const element = document.getElementById(elementId);
    const colors = ['#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e'];
    
    let html = '';
    Object.entries(data).forEach(([key, value], index) => {
        html += `
            <div class="legend-item">
                <div class="legend-color" style="background-color: ${colors[index]};"></div>
                <span>${capitalizeFirst(key)}: ${value.count} (${value.percentage.toFixed(1)}%)</span>
            </div>
        `;
    });
    
    element.innerHTML = html;
}

// Section 6: Opening Performance
async function renderOpeningPerformance(data) {
    if (!data) return;
    
    if (data.best_openings && data.best_openings.length > 0) {
        renderOpeningsChart('bestOpeningsChart', data.best_openings, true);
        renderOpeningsTable('bestOpeningsTable', data.best_openings);
    }
    
    if (data.worst_openings && data.worst_openings.length > 0) {
        renderOpeningsChart('worstOpeningsChart', data.worst_openings, false);
        renderOpeningsTable('worstOpeningsTable', data.worst_openings);
    }
}

function renderOpeningsChart(canvasId, openings, isBest) {
    const labels = openings.map(o => o.name);
    const winRates = openings.map(o => o.win_rate);
    const color = isBest ? '#27ae60' : '#e74c3c';
    
    const ctx = document.getElementById(canvasId);
    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Win Rate %',
                data: winRates,
                backgroundColor: color
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Win Rate %'
                    }
                }
            }
        }
    });
}

function renderOpeningsTable(elementId, openings) {
    const element = document.getElementById(elementId);
    let html = '';
    
    openings.forEach(opening => {
        html += `
            <div class="opening-row">
                <div class="opening-name">${opening.name}</div>
                <div class="opening-games">${opening.games} games</div>
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
                        <span class="opening-stat-value">${opening.win_rate.toFixed(1)}%</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    element.innerHTML = html;
}

// Section 7: Opponent Strength
async function renderOpponentStrength(data) {
    if (!data) return;
    
    // Render cards
    if (data.lower_rated) renderStrengthCard('lowerRatedCard', data.lower_rated, 'lower');
    if (data.similar_rated) renderStrengthCard('similarRatedCard', data.similar_rated, 'similar');
    if (data.higher_rated) renderStrengthCard('higherRatedCard', data.higher_rated, 'higher');
    
    // Render chart
    renderOpponentStrengthChart(data);
}

function renderStrengthCard(elementId, data, type) {
    const card = document.getElementById(elementId);
    const statsDiv = card.querySelector('.strength-stats');
    
    const winRate = data.win_rate || 0;
    const color = winRate >= 50 ? '#27ae60' : '#e74c3c';
    
    statsDiv.innerHTML = `
        <div class="strength-win-rate" style="color: ${color};">
            ${winRate.toFixed(1)}%
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

function renderOpponentStrengthChart(data) {
    const ctx = document.getElementById('opponentStrengthChart');
    
    const categories = ['Lower Rated', 'Similar Rated', 'Higher Rated'];
    const wins = [
        data.lower_rated?.wins || 0,
        data.similar_rated?.wins || 0,
        data.higher_rated?.wins || 0
    ];
    const losses = [
        data.lower_rated?.losses || 0,
        data.similar_rated?.losses || 0,
        data.higher_rated?.losses || 0
    ];
    const draws = [
        data.lower_rated?.draws || 0,
        data.similar_rated?.draws || 0,
        data.higher_rated?.draws || 0
    ];
    
    charts.opponentStrength = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [
                {
                    label: 'Wins',
                    data: wins,
                    backgroundColor: '#27ae60'
                },
                {
                    label: 'Losses',
                    data: losses,
                    backgroundColor: '#e74c3c'
                },
                {
                    label: 'Draws',
                    data: draws,
                    backgroundColor: '#95a5a6'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
}

// Section 8: Time of Day Performance
async function renderTimeOfDay(data) {
    if (!data) return;
    
    // Render cards
    if (data.morning) renderTimeCard('morningCard', data.morning);
    if (data.afternoon) renderTimeCard('afternoonCard', data.afternoon);
    if (data.night) renderTimeCard('nightCard', data.night);
    
    // Render chart
    renderTimeOfDayChart(data);
}

function renderTimeCard(elementId, data) {
    const card = document.getElementById(elementId);
    const statsDiv = card.querySelector('.time-stats');
    
    const winRate = data.win_rate || 0;
    const color = winRate >= 50 ? '#27ae60' : '#e74c3c';
    
    statsDiv.innerHTML = `
        <div class="time-win-rate" style="color: ${color};">
            ${winRate.toFixed(1)}%
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

function renderTimeOfDayChart(data) {
    const ctx = document.getElementById('timeOfDayChart');
    
    const periods = ['Morning', 'Afternoon', 'Night'];
    const wins = [
        data.morning?.wins || 0,
        data.afternoon?.wins || 0,
        data.night?.wins || 0
    ];
    const losses = [
        data.morning?.losses || 0,
        data.afternoon?.losses || 0,
        data.night?.losses || 0
    ];
    const draws = [
        data.morning?.draws || 0,
        data.afternoon?.draws || 0,
        data.night?.draws || 0
    ];
    
    charts.timeOfDay = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: periods,
            datasets: [
                {
                    label: 'Wins',
                    data: wins,
                    backgroundColor: '#27ae60'
                },
                {
                    label: 'Losses',
                    data: losses,
                    backgroundColor: '#e74c3c'
                },
                {
                    label: 'Draws',
                    data: draws,
                    backgroundColor: '#95a5a6'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
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
