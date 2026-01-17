// Main JavaScript for Chess Analytics

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analyzeForm');
    
    if (form) {
        // Set default dates
        const today = new Date();
        const thirtyDaysAgo = new Date(today);
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        
        document.getElementById('endDate').valueAsDate = today;
        document.getElementById('startDate').valueAsDate = thirtyDaysAgo;
        
        // Set max date to today
        document.getElementById('endDate').max = today.toISOString().split('T')[0];
        document.getElementById('startDate').max = today.toISOString().split('T')[0];
        
        // Form submission
        form.addEventListener('submit', handleFormSubmit);
    }
});

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    // Validate dates
    if (new Date(startDate) > new Date(endDate)) {
        showError('Start date must be before end date');
        return;
    }
    
    // Show loading, hide results and errors
    showLoading();
    hideError();
    hideResults();
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze games');
        }
        
        displayResults(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.querySelector('.btn-primary').disabled = true;
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
    document.querySelector('.btn-primary').disabled = false;
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

function hideError() {
    document.getElementById('error').classList.add('hidden');
}

function hideResults() {
    document.getElementById('results').classList.add('hidden');
}

function showResults() {
    document.getElementById('results').classList.remove('hidden');
}

function displayResults(data) {
    const stats = data.statistics;
    
    // Update main stats
    document.getElementById('totalGames').textContent = data.total_games;
    document.getElementById('wins').textContent = stats.wins;
    document.getElementById('losses').textContent = stats.losses;
    document.getElementById('draws').textContent = stats.draws;
    document.getElementById('winRate').textContent = stats.win_rate + '%';
    
    // Display color stats
    displayColorStats(stats.by_color);
    
    // Display time control stats
    displayTimeControlStats(stats.by_time_control);
    
    // Show results section
    showResults();
    
    // Scroll to results
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

function displayColorStats(colorStats) {
    const container = document.getElementById('colorStats');
    container.innerHTML = '';
    
    ['white', 'black'].forEach(color => {
        const stats = colorStats[color];
        const total = stats.wins + stats.losses + stats.draws;
        const winRate = total > 0 ? ((stats.wins / total) * 100).toFixed(1) : 0;
        
        const div = document.createElement('div');
        div.className = 'stat-item';
        div.innerHTML = `
            <div class="stat-item-header">${capitalize(color)}</div>
            <div class="stat-item-details">
                <span>Wins: ${stats.wins}</span>
                <span>Losses: ${stats.losses}</span>
                <span>Draws: ${stats.draws}</span>
                <span>Win Rate: ${winRate}%</span>
            </div>
        `;
        container.appendChild(div);
    });
}

function displayTimeControlStats(timeControlStats) {
    const container = document.getElementById('timeControlStats');
    container.innerHTML = '';
    
    // Sort by total games (descending)
    const sorted = Object.entries(timeControlStats).sort((a, b) => {
        const totalA = a[1].wins + a[1].losses + a[1].draws;
        const totalB = b[1].wins + b[1].losses + b[1].draws;
        return totalB - totalA;
    });
    
    sorted.forEach(([timeControl, stats]) => {
        const total = stats.wins + stats.losses + stats.draws;
        const winRate = total > 0 ? ((stats.wins / total) * 100).toFixed(1) : 0;
        
        const div = document.createElement('div');
        div.className = 'stat-item';
        div.innerHTML = `
            <div class="stat-item-header">${formatTimeControl(timeControl)}</div>
            <div class="stat-item-details">
                <span>Games: ${total}</span>
                <span>Wins: ${stats.wins}</span>
                <span>Losses: ${stats.losses}</span>
                <span>Win Rate: ${winRate}%</span>
            </div>
        `;
        container.appendChild(div);
    });
    
    if (sorted.length === 0) {
        container.innerHTML = '<p>No time control data available</p>';
    }
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatTimeControl(timeControl) {
    // Convert time control like "600" to "10 min"
    if (timeControl === 'unknown') return 'Unknown';
    
    const seconds = parseInt(timeControl);
    if (isNaN(seconds)) return timeControl;
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return `${minutes} min`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    
    if (remainingMinutes === 0) {
        return `${hours}h`;
    }
    
    return `${hours}h ${remainingMinutes}m`;
}
