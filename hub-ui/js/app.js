const API_BASE = 'http://localhost:8000';
let authToken = null;
let pollInterval = null;

// DOM Elements
const loginView = document.getElementById('login-view');
const dashboardView = document.getElementById('dashboard-view');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const logoutBtn = document.getElementById('logout-btn');
const refreshBtn = document.getElementById('refresh-btn');

const kpiTransactions = document.getElementById('kpi-transactions');
const kpiShifts = document.getElementById('kpi-shifts');
const simContainer = document.getElementById('sim-container');

// Event Listeners
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const user = document.getElementById('admin-user').value;
    const pin = document.getElementById('admin-pin').value;
    
    loginError.textContent = 'Authenticating...';
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, pin: pin })
        });
        
        if (!response.ok) {
            throw new Error('Invalid credentials');
        }
        
        const data = await response.json();
        authToken = data.access_token;
        loginError.textContent = '';
        
        // Transition to Dashboard
        loginView.classList.remove('active');
        dashboardView.classList.add('active');
        
        startPolling();
    } catch (err) {
        loginError.textContent = err.message;
    }
});

logoutBtn.addEventListener('click', () => {
    stopPolling();
    authToken = null;
    dashboardView.classList.remove('active');
    loginView.classList.add('active');
    document.getElementById('admin-pin').value = '';
});

refreshBtn.addEventListener('click', () => {
    fetchDashboardData();
    refreshBtn.style.transform = 'rotate(180deg)';
    setTimeout(() => refreshBtn.style.transform = 'none', 500);
});

// Polling Logic
function startPolling() {
    fetchDashboardData();
    pollInterval = setInterval(fetchDashboardData, 5000);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

async function fetchDashboardData() {
    if (!authToken) return;
    
    try {
        const response = await fetch(`${API_BASE}/dashboard/summary`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.status === 401 || response.status === 403) {
            logoutBtn.click();
            return;
        }
        
        const data = await response.json();
        updateDashboard(data);
    } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
    }
}

function updateDashboard(data) {
    // Animate numbers up if they changed (simple implementation)
    kpiTransactions.textContent = data.total_transactions.toLocaleString();
    kpiShifts.textContent = data.active_shifts.toLocaleString();
    
    // Render SIM Cards
    if (!data.sim_health || data.sim_health.length === 0) {
        simContainer.innerHTML = '<div class="loading-shimmer">No SIM channels detected.</div>';
        return;
    }
    
    simContainer.innerHTML = data.sim_health.map(sim => `
        <div class="sim-card">
            <div class="sim-header">
                <div>
                    <div class="sim-network">${sim.network}</div>
                    <div class="sim-phone">${sim.phone}</div>
                </div>
                <div class="sim-status status-${sim.status.toLowerCase()}">${sim.status}</div>
            </div>
            <div class="sim-balance-label">Float Balance</div>
            <div class="sim-balance">K ${parseFloat(sim.balance).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
        </div>
    `).join('');
}
