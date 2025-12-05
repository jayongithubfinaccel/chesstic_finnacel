// Analytics page JavaScript for displaying results and charts

document.addEventListener('DOMContentLoaded', () => {
    const resultsSection = document.getElementById('resultsSection');
    const loadingSection = document.getElementById('loadingSection');
    const emptyState = document.getElementById('emptyState');

    // Get results from sessionStorage
    const resultsData = sessionStorage.getItem('analysisResults');

    if (!resultsData) {
        // No results, show empty state
        emptyState.style.display = 'block';
        return;
    }

    try {
        const data = JSON.parse(resultsData);
        
        // Show results section
        resultsSection.style.display = 'block';
        emptyState.style.display = 'none';

        // Display results
        displayPlayerInfo(data);
        displayStatistics(data);
        displayCharts(data);
        displayTimeControls(data);

    } catch (error) {
        console.error('Error parsing results:', error);
        emptyState.style.display = 'block';
    }
});

function displayPlayerInfo(data) {
    const playerInfo = document.getElementById('playerInfo');
    playerInfo.innerHTML = `
        <h3>Analysis for ${data.username}</h3>
        <p>Period: ${formatDate(data.start_date)} to ${formatDate(data.end_date)}</p>
    `;
}

function displayStatistics(data) {
    const stats = data.statistics;
    
    document.getElementById('totalGames').textContent = data.total_games;
    document.getElementById('totalWins').textContent = stats.wins;
    document.getElementById('totalLosses').textContent = stats.losses;
    document.getElementById('totalDraws').textContent = stats.draws;
    document.getElementById('winRate').textContent = stats.win_rate + '%';
}

function displayCharts(data) {
    const stats = data.statistics;

    // Results Distribution Chart
    const resultsCtx = document.getElementById('resultsChart').getContext('2d');
    new Chart(resultsCtx, {
        type: 'doughnut',
        data: {
            labels: ['Wins', 'Losses', 'Draws'],
            datasets: [{
                data: [stats.wins, stats.losses, stats.draws],
                backgroundColor: ['#27ae60', '#e74c3c', '#95a5a6'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Color Performance Chart
    const colorCtx = document.getElementById('colorChart').getContext('2d');
    new Chart(colorCtx, {
        type: 'bar',
        data: {
            labels: ['White', 'Black'],
            datasets: [
                {
                    label: 'Wins',
                    data: [
                        stats.by_color.white.wins,
                        stats.by_color.black.wins
                    ],
                    backgroundColor: '#27ae60'
                },
                {
                    label: 'Losses',
                    data: [
                        stats.by_color.white.losses,
                        stats.by_color.black.losses
                    ],
                    backgroundColor: '#e74c3c'
                },
                {
                    label: 'Draws',
                    data: [
                        stats.by_color.white.draws,
                        stats.by_color.black.draws
                    ],
                    backgroundColor: '#95a5a6'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function displayTimeControls(data) {
    const timeControlStats = document.getElementById('timeControlStats');
    const stats = data.statistics.by_time_control;

    if (Object.keys(stats).length === 0) {
        timeControlStats.innerHTML = '<p>No time control data available</p>';
        return;
    }

    let html = '';
    for (const [timeControl, results] of Object.entries(stats)) {
        const total = results.wins + results.losses + results.draws;
        const winRate = total > 0 ? ((results.wins / total) * 100).toFixed(1) : 0;

        html += `
            <div class="time-control-item">
                <div class="time-control-name">${formatTimeControl(timeControl)}</div>
                <div class="time-control-stats">
                    <span style="color: #27ae60;">✓ ${results.wins}</span>
                    <span style="color: #e74c3c;">✗ ${results.losses}</span>
                    <span style="color: #95a5a6;">= ${results.draws}</span>
                    <span><strong>${winRate}%</strong></span>
                </div>
            </div>
        `;
    }

    timeControlStats.innerHTML = html;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function formatTimeControl(timeControl) {
    // Convert time control like "600" to readable format "10 min"
    if (timeControl === 'unknown') return 'Unknown';
    
    const seconds = parseInt(timeControl);
    if (isNaN(seconds)) return timeControl;

    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return `${minutes} min`;
    } else {
        const hours = Math.floor(minutes / 60);
        const remainingMins = minutes % 60;
        return remainingMins > 0 ? `${hours}h ${remainingMins}m` : `${hours}h`;
    }
}
