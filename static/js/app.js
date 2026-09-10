// State Management
let currentUser = '';
let authToken = '';
let userMeta = {};
let farmersData = [];
let loansData = [];
let shopsData = {};
let currentSelectedShop = null;
let shopSearchList = [];
let currentTheme = localStorage.getItem('agrifin_theme') || 'dark';
let shopsCurrentPage = 1;
const SHOPS_PER_PAGE = 16;

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const icon = document.getElementById('theme-icon');
    const label = document.getElementById('theme-label');
    if (icon && label) {
        if (theme === 'light') {
            icon.className = 'fa-solid fa-sun';
            label.textContent = 'Light Mode';
        } else {
            icon.className = 'fa-solid fa-moon';
            label.textContent = 'Dark Mode';
        }
    }
    localStorage.setItem('agrifin_theme', theme);
    currentTheme = theme;
}

function toggleTheme() {
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

const zambiaProvinces = [
    "Central", "Copperbelt", "Eastern", "Luapula", "Lusaka",
    "Muchinga", "Northern", "North-Western", "Southern", "Western"
];

const zambiaDistrictsByProvince = {
    "Central": ["Chibombo", "Kabwe", "Kapiri Mposhi", "Luano", "Mkushi", "Mumbwa", "Serenje", "Shibuyunji"],
    "Copperbelt": ["Chingola", "Kalulushi", "Kitwe", "Luanshya", "Lufwanyama", "Masaiti", "Mpongwe", "Mufulira", "Ndola"],
    "Eastern": ["Chipata", "Chadiza", "Kasama", "Lundazi", "Mambwe", "Nyimba", "Petauke", "Sinda", "Vubwi"],
    "Luapula": ["Chienge", "Kawambwa", "Lunga", "Mansa", "Milenge", "Nchelenge", "Samfya"],
    "Lusaka": ["Chongwe", "Kafue", "Luangwa", "Lusaka", "Rufunsa"],
    "Muchinga": ["Chinsali", "Isoka", "Lavushimanda", "Mafinga", "Nakonde", "Shiwang'andu"],
    "Northern": ["Kasama", "Luwingu", "Mporokoso", "Mpika", "Mbala", "Nkhatabay"],
    "North-Western": ["Chavuma", "Solwezi", "Zambezi", "Kabompo", "Kalumbila", "Mufumbwe", "Mwinilunga", "Solwezi"],
    "Southern": ["Chikankata", "Choma", "Gwembe", "Itezhi-Tezhi", "Kalomo", "Kazungula", "Livingstone", "Mazabuka", "Monze", "Namwala", "Pemba", "Siavonga", "Sinazongwe", "Zimba"],
    "Western": ["Kalabo", "Kaoma", "Lukulu", "Mongu", "Senanga", "Sesheke", "Shangombo", "Sioma"]
};

function populateProvinceDropdown() {
    const sel = document.getElementById('shop-province-input');
    if (!sel) return;
    sel.innerHTML = '<option value="">Select Province</option>' +
        zambiaProvinces.map(p => `<option value="${p}">${p}</option>`).join('');
}

function populateDistrictDropdown(province) {
    const sel = document.getElementById('shop-district-input');
    if (!sel) return;
    sel.innerHTML = '<option value="">Select District</option>';
    const districts = zambiaDistrictsByProvince[province] || [];
    districts.forEach(d => {
        sel.innerHTML += `<option value="${d}">${d}</option>`;
    });
}

function setupAddShopGeoDropdowns() {
    populateProvinceDropdown();
    const provSel = document.getElementById('shop-province-input');
    if (provSel) {
        provSel.addEventListener('change', function() {
            populateDistrictDropdown(this.value);
        });
    }
}

async function createNewAgent() {
    const username = document.getElementById('new-agent-username-input').value.trim();
    const name = document.getElementById('new-agent-name-input').value.trim();
    const password = document.getElementById('new-agent-password-input').value.trim();
    const province = document.getElementById('new-agent-province-input').value;
    const district = document.getElementById('new-agent-district-input').value;
    const village = document.getElementById('new-agent-village-input').value.trim();

    if (!username || !name || !password) {
        showToast('Username, full name and password are required', 'error');
        return;
    }

    try {
        const res = await fetch('/hq/agents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ username, name, password, province, district, village })
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to create agent', 'error');
            return;
        }

        showToast(data.message || 'Agent created successfully');
        closeModal('add-agent-modal');

        const agentSelect = document.getElementById('shop-agent-select');
        if (agentSelect) {
            const exists = Array.from(agentSelect.options).some(o => o.value === username);
            if (!exists) {
                const opt = document.createElement('option');
                opt.value = username;
                opt.textContent = `${username} (${name})`;
                agentSelect.appendChild(opt);
            }
            agentSelect.value = username;
        }
    } catch (err) {
        showToast('Error creating agent', 'error');
    }
}

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
    // Check if token exists in localStorage
    const savedToken = localStorage.getItem('agrifin_token');
    const savedUser = localStorage.getItem('agrifin_user');

    if (savedToken && savedUser) {
        authToken = savedToken;
        userMeta = JSON.parse(savedUser);
        currentUser = userMeta.username || userMeta.user;

        // Verify token with backend
        const verified = await verifyCurrentSession();
        if (verified) {
            showDashboard();
            return;
        }
    }

    // Otherwise show dedicated login page
    showLogin();
});

// Verification of saved token
async function verifyCurrentSession() {
    try {
        const res = await fetch('/me', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (res.ok) {
            const data = await res.json();
            userMeta = data.user;
            currentUser = userMeta.username;
            return true;
        }
    } catch (e) {
        console.error('Session validation error:', e);
    }
    clearSession();
    return false;
}

// Show/Hide View Wrappers
function showLogin() {
    document.getElementById('login-view').style.display = 'flex';
    document.getElementById('dashboard-view').style.display = 'none';
    hideLoginError();
}

function showDashboard() {
    document.getElementById('login-view').style.display = 'none';
    document.getElementById('dashboard-view').style.display = 'flex';
    applyTheme(currentTheme);
    updateUserBadge();
    updateActionPermissions();
    
    const defaultNav = document.getElementById('nav-dashboard-home-link');
    if (defaultNav) {
        switchTab('dashboard-home-tab', defaultNav);
    }
    
    loadDashboardData();
    
    if (userMeta.role === 'HQ') {
        loadHqWarehouse();
    }
}

function clearSession() {
    authToken = '';
    currentUser = '';
    userMeta = {};
    localStorage.removeItem('agrifin_token');
    localStorage.removeItem('agrifin_user');
}

function logout() {
    clearSession();
    showLogin();
    showToast('Signed out successfully');
}

// Fill Demo Credentials
function fillDemoCredentials(username, password) {
    document.getElementById('login-username').value = username;
    document.getElementById('login-password').value = password;
    hideLoginError();

    // Auto submit demo login for rapid testing experience
    document.getElementById('login-form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
}

function togglePasswordVisibility() {
    const pwdInput = document.getElementById('login-password');
    const eyeIcon = document.getElementById('pwd-eye');

    if (pwdInput.type === 'password') {
        pwdInput.type = 'text';
        eyeIcon.className = 'fa-solid fa-eye-slash';
    } else {
        pwdInput.type = 'password';
        eyeIcon.className = 'fa-solid fa-eye';
    }
}

function showLoginError(msg) {
    const errBox = document.getElementById('login-error');
    document.getElementById('login-error-text').textContent = msg;
    errBox.style.display = 'flex';
}

function hideLoginError() {
    document.getElementById('login-error').style.display = 'none';
}

// Handle Login Form Submit
async function handleLoginSubmit(e) {
    e.preventDefault();
    hideLoginError();

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const btnSubmit = document.getElementById('btn-login-submit');

    if (!username || !password) {
        showLoginError('Please enter both username and password.');
        return;
    }

    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Authenticating...';

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const resData = await response.json();
        if (!response.ok) {
            showLoginError(resData.error || 'Invalid username or password.');
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<span>Sign In</span> <i class="fa-solid fa-arrow-right"></i>';
            return;
        }

        authToken = resData.token;
        userMeta = resData.user;
        currentUser = userMeta.username;

        // Persist token in localStorage
        localStorage.setItem('agrifin_token', authToken);
        localStorage.setItem('agrifin_user', JSON.stringify(userMeta));

        showToast(`Welcome back, ${userMeta.name}!`);
        showDashboard();
    } catch (err) {
        console.error('Error logging in:', err);
        showLoginError('Connection failed. Please ensure server is running.');
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<span>Sign In</span> <i class="fa-solid fa-arrow-right"></i>';
    }
}

function updateUserBadge() {
    const avatar = document.getElementById('user-avatar');
    const nameElem = document.getElementById('user-display-name');
    const tagElem = document.getElementById('user-role-tag');

    nameElem.textContent = userMeta.name || currentUser;
    
    const initials = (userMeta.name || currentUser).split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    avatar.textContent = initials;

    tagElem.textContent = `${userMeta.role} Role`;
    tagElem.className = 'role-tag';
    if (userMeta.role === 'HQ') tagElem.classList.add('role-hq');
    else if (userMeta.role === 'District') tagElem.classList.add('role-district');
    else if (userMeta.role === 'Village') tagElem.classList.add('role-village');
    else if (userMeta.role === 'Agent') tagElem.classList.add('role-agent');
}

function updateActionPermissions() {
    const isHQ = userMeta.role === 'HQ';
    
    const btnAddClient = document.getElementById('btn-add-client');
    const btnIssueLoan = document.getElementById('btn-issue-loan');

    btnAddClient.style.opacity = '1';
    btnAddClient.title = '';
    btnIssueLoan.style.opacity = '1';
    btnIssueLoan.title = '';

    document.querySelectorAll('[data-hq-only]').forEach(el => {
        el.style.display = isHQ ? '' : 'none';
    });

    if (!isHQ) {
        document.querySelectorAll('[data-hq-tab]').forEach(el => {
            el.style.display = 'none';
        });
    }
}

// Load Dashboard & Data
async function exportPortfolioCSV() {
    try {
        const res = await fetch('/reports/portfolio', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        const loans = data.loans || [];
        if (loans.length === 0) {
            showToast('No loans to export', 'error');
            return;
        }
        const headers = ['Loan ID', 'Borrower', 'Shop', 'Amount', 'Total Repayable', 'Balance', 'Status'];
        const rows = loans.map(l => [l.id, l.name, l.shop, l.loan_amount, l.total_repayable, l.balance_remaining, l.status]);
        let csv = headers.join(',') + '\n';
        rows.forEach(r => csv += r.join(',') + '\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'portfolio_export.csv';
        a.click();
        URL.revokeObjectURL(url);
        showToast('CSV exported', 'success');
    } catch (err) {
        showToast('Error exporting CSV', 'error');
    }
}

async function loadDashboardData() {
    if (!authToken) return;

    const headers = { 'Authorization': `Bearer ${authToken}` };

    try {
        const sumRes = await fetch('/dashboard/summary', { headers });
        if (sumRes.ok) {
            const sumData = await sumRes.json();
            renderSummaryCards(sumData.summary);
        }

        if (userMeta.role === 'HQ') {
            await loadShopsDirectory();
            renderHqInventoryTable();
            renderHqDashboardStats();
            await loadHqWarehouse();
        }

        const clientRes = await fetch('/clients', { headers });
        if (clientRes.ok) {
            const cData = await clientRes.json();
            farmersData = cData.farmers || [];
            loansData = cData.loans || [];

            renderFarmersTable(farmersData);
            renderLoanTables(loansData);
            populateFarmerSelects(farmersData);
            renderDashboardAlerts();
            renderDashboardNotifications();
            
            if (userMeta.role === 'HQ') {
                renderHqDashboardStats();
            }
        }

    } catch (err) {
        console.error('Error fetching dashboard data:', err);
    }
}

function renderDashboardAlerts() {
    const container = document.getElementById('dashboard-alerts-list');
    if (!container) return;

    const alerts = [];
    const today = new Date().toISOString().split('T')[0];

    loansData.forEach(l => {
        if (l.status === 'active' && l.due_date && l.due_date < today) {
            alerts.push({ type: 'overdue', message: `Overdue ${l.loan_type} loan ${l.id} for ${l.name}`, color: 'var(--rose)' });
        }
    });

    for (const [prov, dists] of Object.entries(shopsData || {})) {
        for (const [dist, vills] of Object.entries(dists)) {
            for (const [vill, shopsList] of Object.entries(vills)) {
                shopsList.forEach(s => {
                    (s.inventory || []).forEach(item => {
                        if (item.quantity < 10) {
                            alerts.push({ type: 'low-stock', message: `Low stock: ${item.item_name} (${item.quantity} left) at ${s.shop}`, color: 'var(--amber)' });
                        }
                    });
                });
            }
        }
    }

    container.innerHTML = '';
    if (alerts.length === 0) {
        container.innerHTML = '<div style="color: var(--text-dim); text-align: center; padding: 12px;">No active alerts.</div>';
        return;
    }

    alerts.forEach(a => {
        const div = document.createElement('div');
        div.style.cssText = `display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: rgba(255,255,255,0.03); border-radius: var(--radius-sm); border-left: 3px solid ${a.color};`;
        div.innerHTML = `<i class="fa-solid fa-circle-exclamation" style="color: ${a.color};"></i> <span style="font-size: 13px;">${a.message}</span>`;
        container.appendChild(div);
    });
}

function renderDashboardNotifications() {
    const container = document.getElementById('dashboard-notifications-list');
    if (!container) return;

    const notifications = [
        { icon: 'fa-user-plus', color: 'var(--emerald)', text: 'New farmer registration requires approval', time: '2 min ago' },
        { icon: 'fa-wheat-aawn', color: 'var(--amber)', text: 'Fertilizer loan FL-501 repayment recorded', time: '15 min ago' },
        { icon: 'fa-boxes-stacked', color: 'var(--cyan)', text: 'Inventory allocated to ShopB - VillageY', time: '1 hour ago' },
        { icon: 'fa-shield-halved', color: 'var(--primary-light)', text: 'System backup completed successfully', time: '3 hours ago' }
    ];

    container.innerHTML = '';
    notifications.forEach(n => {
        const div = document.createElement('div');
        div.style.cssText = `display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: rgba(255,255,255,0.03); border-radius: var(--radius-sm);`;
        div.innerHTML = `
            <div style="width: 32px; height: 32px; border-radius: 50%; background: ${n.color}20; display: flex; align-items: center; justify-content: center;">
                <i class="fa-solid ${n.icon}" style="color: ${n.color}; font-size: 14px;"></i>
            </div>
            <div style="flex: 1;">
                <div style="font-size: 13px;">${n.text}</div>
                <small style="color: var(--text-dim); font-size: 11px;">${n.time}</small>
            </div>
        `;
        container.appendChild(div);
    });
}

// Load & Render Shops Directory (Grouped by Province -> District -> Village)
async function loadShopsDirectory() {
    if (!authToken) return;
    const headers = { 'Authorization': `Bearer ${authToken}` };

    try {
        const res = await fetch('/shops', { headers });
        if (!res.ok) return;

        const data = await res.json();
        shopsData = data.grouped || {};
        shopsCurrentPage = 1;
        renderShopsHierarchy(shopsData);
    } catch (err) {
        console.error('Error loading shops directory:', err);
    }
}

function renderShopsHierarchy(grouped) {
    const container = document.getElementById('shops-hierarchy-container');
    container.innerHTML = '';

    if (!grouped || Object.keys(grouped).length === 0) {
        container.innerHTML = '<div style="color: var(--text-dim); text-align: center; padding: 24px;">No shops found in your scope.</div>';
        return;
    }

    const provinceEntries = Object.entries(grouped);
    const totalPages = Math.max(1, Math.ceil(provinceEntries.length / 2));
    
    if (shopsCurrentPage > totalPages) shopsCurrentPage = totalPages;
    
    const startIdx = (shopsCurrentPage - 1) * 2;
    const pageProvinces = provinceEntries.slice(startIdx, startIdx + 2);

    for (const [prov, dists] of pageProvinces) {
        const provSection = document.createElement('div');
        provSection.className = 'province-group';
        
        let html = `<div class="province-header"><i class="fa-solid fa-map-location-dot"></i> Province: ${prov}</div>`;
        html += `<div class="district-group">`;

        for (const [dist, vills] of Object.entries(dists)) {
            html += `<div class="district-header"><i class="fa-solid fa-building-flag"></i> District: ${dist}</div>`;
            html += `<div class="village-group">`;

            for (const [vill, shopsList] of Object.entries(vills)) {
                html += `<div class="village-header"><i class="fa-solid fa-tree"></i> Village / Area: ${vill}</div>`;
                html += `<div class="shop-card-grid">`;

                shopsList.forEach(s => {
                    const statusClass = s.status === 'active' ? 'badge-active' : 'badge-warning';
                    const invSummary = (s.inventory && s.inventory.length > 0)
                        ? s.inventory.map(i => `<span class="inv-pill">${i.item_name}: ${i.quantity} ${i.unit}</span>`).join('')
                        : '<span style="color: var(--text-dim); font-size:11px;">No allocated inventory stock</span>';

                    html += `
                        <div class="shop-card">
                            <div class="shop-card-header">
                                <div>
                                    <h4><i class="fa-solid fa-store" style="color: var(--emerald);"></i> ${s.shop}</h4>
                                    <small style="color: var(--text-dim);">${s.shop_id || ''} ${s.village}, ${s.district}</small>
                                </div>
                                <span class="badge ${statusClass}">${s.status}</span>
                            </div>
                            
                            <div class="shop-card-meta">
                                <div class="meta-row">
                                    <span>Assigned Agent:</span>
                                    <strong style="color: var(--primary-light);">${s.agent}</strong>
                                </div>
                                <div class="meta-row">
                                    <span>Registered Farmers:</span>
                                    <strong>${s.farmer_count} Farmers</strong>
                                </div>
                                <div class="meta-row">
                                    <span>Active Loans:</span>
                                    <strong>${s.total_loans_count} Loans</strong>
                                </div>
                                <div class="meta-row">
                                    <span>Max Loan Limit:</span>
                                    <strong>ZMW ${s.max_loan_limit.toLocaleString()}</strong>
                                </div>
                            </div>

                            <div class="inventory-pills-row">
                                ${invSummary}
                            </div>

                            <button class="btn btn-sm btn-cyan" onclick="openShopDetailModal('${s.shop}')" style="width: 100%; justify-content: center; margin-top: 4px;">
                                <i class="fa-solid fa-sliders"></i> Select & Manage Shop
                            </button>
                        </div>
                    `;
                });

                html += `</div>`; // Close shop-card-grid
            }

            html += `</div>`; // Close village-group
        }

        html += `</div>`; // Close district-group
        provSection.innerHTML = html;
        container.appendChild(provSection);
    }

    updateShopsPagination(totalPages);
}

function filterShopsDirectory() {
    const q = document.getElementById('shop-search-input').value.toLowerCase();
    
    const filteredGrouped = {};
    for (const [prov, dists] of Object.entries(shopsData)) {
        for (const [dist, vills] of Object.entries(dists)) {
            for (const [vill, shopsList] of Object.entries(vills)) {
                const matchingShops = shopsList.filter(s => 
                    s.shop.toLowerCase().includes(q) || 
                    s.agent.toLowerCase().includes(q) || 
                    s.district.toLowerCase().includes(q) ||
                    s.village.toLowerCase().includes(q)
                );
                if (matchingShops.length > 0) {
                    if (!filteredGrouped[prov]) filteredGrouped[prov] = {};
                    if (!filteredGrouped[prov][dist]) filteredGrouped[prov][dist] = {};
                    filteredGrouped[prov][dist][vill] = matchingShops;
                }
            }
        }
    }
    renderShopsHierarchy(filteredGrouped);
}

function updateShopsPagination(totalPages) {
    const prevBtn = document.getElementById('shops-prev-btn');
    const nextBtn = document.getElementById('shops-next-btn');
    const pageInfo = document.getElementById('shops-page-info');
    
    if (!prevBtn || !nextBtn || !pageInfo) return;
    
    pageInfo.textContent = `Page ${shopsCurrentPage} of ${totalPages}`;
    prevBtn.disabled = shopsCurrentPage <= 1;
    nextBtn.disabled = shopsCurrentPage >= totalPages;
    
    prevBtn.style.opacity = shopsCurrentPage <= 1 ? '0.5' : '1';
    nextBtn.style.opacity = shopsCurrentPage >= totalPages ? '0.5' : '1';
}

function shopsPrevPage() {
    if (shopsCurrentPage > 1) {
        shopsCurrentPage--;
        renderShopsHierarchy(shopsData);
    }
}

function shopsNextPage() {
    const totalPages = Math.max(1, Math.ceil(Object.keys(shopsData || {}).length / 2));
    if (shopsCurrentPage < totalPages) {
        shopsCurrentPage++;
        renderShopsHierarchy(shopsData);
    }
}

// Action Handler: Create Shop
async function handleCreateShop(e) {
    e.preventDefault();
    const payload = {
        shop: document.getElementById('shop-name-input').value,
        province: document.getElementById('shop-province-input').value,
        district: document.getElementById('shop-district-input').value,
        village: document.getElementById('shop-village-input').value,
        agent: document.getElementById('shop-agent-select').value,
        max_loan_limit: parseFloat(document.getElementById('shop-limit-input').value)
    };

    try {
        const res = await fetch('/shops/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to create shop', 'error');
            return;
        }

        showToast(data.message);
        closeModal('add-shop-modal');
        document.getElementById('add-shop-form').reset();
        await loadDashboardData();
    } catch (err) {
        showToast('Error creating shop', 'error');
    }
}

// Shop Detail Modal & Management Tabs
async function openShopDetailModal(shopName) {
    currentSelectedShop = shopName;
    const headers = { 'Authorization': `Bearer ${authToken}` };

    try {
        const res = await fetch(`/shops/detail/${encodeURIComponent(shopName)}`, { headers });
        if (!res.ok) {
            showToast('Shop not found', 'error');
            return;
        }

        const data = await res.json();

        document.getElementById('sd-title').innerHTML = `<i class="fa-solid fa-store"></i> ${data.shop} Management`;
        document.getElementById('sd-subtitle').textContent = `${data.province} -> ${data.district} -> ${data.village} | Assigned Agent: ${data.agent}`;
        document.getElementById('sd-shop-id').textContent = data.shop_id ? `ID: ${data.shop_id}` : '';
        document.getElementById('sd-shop-name-hidden').value = data.shop;

        document.getElementById('sd-status-select').value = data.status || 'active';
        document.getElementById('sd-agent-select').value = data.agent || 'agent1';
        document.getElementById('sd-limit-input').value = data.max_loan_limit || 10000;

        const invTbody = document.getElementById('sd-inventory-tbody');
        invTbody.innerHTML = '';
        const invList = data.inventory || [];

        if (invList.length === 0) {
            invTbody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--text-dim); padding: 12px;">No inventory items allocated yet.</td></tr>`;
        } else {
            invList.forEach(item => {
                invTbody.innerHTML += `
                    <tr>
                        <td><strong>${item.item_name}</strong></td>
                        <td><span class="badge badge-primary">${item.quantity}</span></td>
                        <td>${item.unit}</td>
                    </tr>
                `;
            });
        }

        const clientsContainer = document.getElementById('sd-shop-clients-container');
        const farmers = (data.clients && data.clients.farmers) ? data.clients.farmers : [];
        const fertLoans = (data.clients && data.clients.fertilizer_loans) ? data.clients.fertilizer_loans : [];
        const assetLoans = (data.clients && data.clients.asset_finance) ? data.clients.asset_finance : [];
        const cashLoans = (data.clients && data.clients.cash_loans) ? data.clients.cash_loans : [];

        let clientHtml = `
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <div style="font-size: 13px; font-weight: 600; color: var(--emerald);"><i class="fa-solid fa-users"></i> Registered Farmers (${farmers.length})</div>
                <ul style="list-style: none; padding-left: 0; display: flex; flex-direction: column; gap: 4px;">
        `;

        if (farmers.length === 0) {
            clientHtml += `<li style="color: var(--text-dim); font-size:12px;">No farmers registered in ${shopName} yet.</li>`;
        } else {
            farmers.forEach(f => {
                clientHtml += `<li style="background: rgba(255,255,255,0.03); padding: 6px 10px; border-radius: var(--radius-sm); font-size: 12px;"><strong>${f.name}</strong> (${f.phone}) - NRC: ${f.nrc}</li>`;
            });
        }

        clientHtml += `
                </ul>
                <div style="font-size: 13px; font-weight: 600; color: var(--cyan); margin-top: 10px;"><i class="fa-solid fa-file-invoice-dollar"></i> Active Loans (${fertLoans.length + assetLoans.length + cashLoans.length})</div>
                <div style="font-size: 12px; color: var(--text-muted);">
                    Fertilizer Loans: <strong>${fertLoans.length}</strong> | Asset Loans: <strong>${assetLoans.length}</strong> | Cash Loans: <strong>${cashLoans.length}</strong>
                </div>
            </div>
        `;
        clientsContainer.innerHTML = clientHtml;

        openModal('shop-detail-modal');
    } catch (err) {
        console.error(err);
        showToast('Error opening shop details', 'error');
    }
}

function switchShopModalTab(viewId, btnElem) {
    document.querySelectorAll('.sm-view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.sm-tab').forEach(t => t.classList.remove('active'));

    document.getElementById(viewId).classList.add('active');
    btnElem.classList.add('active');
}

// Action Handler: Save Shop Settings
async function handleSaveShopSettings(e) {
    e.preventDefault();
    const payload = {
        shop: document.getElementById('sd-shop-name-hidden').value,
        status: document.getElementById('sd-status-select').value,
        agent: document.getElementById('sd-agent-select').value,
        max_loan_limit: parseFloat(document.getElementById('sd-limit-input').value)
    };

    try {
        const res = await fetch('/shops/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to update shop settings', 'error');
            return;
        }

        showToast(data.message);
        await loadDashboardData();
    } catch (err) {
        showToast('Error saving shop settings', 'error');
    }
}

// Action Handler: Allocate Stock Inventory
async function handleAllocateStock(e) {
    e.preventDefault();
    const payload = {
        shop: document.getElementById('sd-shop-name-hidden').value,
        item_name: document.getElementById('alloc-item-input').value,
        quantity: parseInt(document.getElementById('alloc-qty-input').value),
        unit: document.getElementById('alloc-unit-input').value
    };

    try {
        const res = await fetch('/shops/allocate_inventory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to allocate stock', 'error');
            return;
        }

        showToast(data.message);
        document.getElementById('allocate-inventory-form').reset();
        await openShopDetailModal(payload.shop);
        await loadDashboardData();
    } catch (err) {
        showToast('Error allocating stock inventory', 'error');
    }
}

// HQ: Save Settings
function toggleSettingsSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    section.classList.toggle('hidden');
    const header = section.previousElementSibling;
    if (header) header.classList.toggle('collapsed');
}

function filterSettings(query) {
    const term = (query || '').toLowerCase();
    const sections = document.querySelectorAll('.settings-section');
    sections.forEach(section => {
        const body = section.querySelector('.settings-section-body');
        if (!body) return;
        const text = body.textContent.toLowerCase();
        if (!term || text.includes(term)) {
            body.classList.remove('hidden');
            section.classList.remove('hidden');
            const header = section.querySelector('.settings-section-header');
            if (header) header.classList.remove('collapsed');
        } else {
            body.classList.add('hidden');
            section.classList.add('hidden');
            const header = section.querySelector('.settings-section-header');
            if (header) header.classList.add('collapsed');
        }
    });
}

function getSettingsPayload() {
    const payload = { system: {}, loan_rules: {}, limits: {}, features: {}, templates: {} };
    document.querySelectorAll('#hq-admin-tab [data-setting]').forEach(input => {
        const key = input.getAttribute('data-setting');
        const [section, field] = key.split('.');
        if (!payload[section]) return;
        if (input.type === 'checkbox') {
            payload[section][field] = input.checked;
        } else {
            let value = input.value;
            if (input.type === 'number') value = parseFloat(input.value) || 0;
            payload[section][field] = value;
        }
    });
    return payload;
}

function applySettingsToForm(settings) {
    if (!settings) return;
    document.querySelectorAll('#hq-admin-tab [data-setting]').forEach(input => {
        const key = input.getAttribute('data-setting');
        const parts = key.split('.');
        let value;
        if (parts.length === 2 && settings[parts[0]] && settings[parts[0]][parts[1]] !== undefined) {
            value = settings[parts[0]][parts[1]];
        } else if (settings[key] !== undefined) {
            value = settings[key];
        }
        if (value !== undefined && !input.readOnly) {
            if (input.type === 'checkbox') {
                input.checked = !!value;
            } else {
                input.value = value;
            }
        }
    });
}

async function loadHqSettings() {
    try {
        const res = await fetch('/hq/settings', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        applySettingsToForm(data);
    } catch (err) {
        console.error('Error loading settings:', err);
    }
}

async function saveHqSettings() {
    const payload = getSettingsPayload();
    try {
        const res = await fetch('/hq/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to save settings', 'error');
            return;
        }

        showToast(data.message || 'Settings saved successfully');
        applySettingsToForm(data.settings);
    } catch (err) {
        showToast('Error saving settings', 'error');
    }
}

// HQ: Render Inventory Table
let inventoryCurrentPage = 1;
let inventorySearchQuery = '';
const INVENTORY_PER_PAGE = 10;
let currentHqWarehouse = null;

function getFlatInventoryList(grouped) {
    const flat = [];
    for (const [prov, dists] of Object.entries(grouped || {})) {
        for (const [dist, vills] of Object.entries(dists)) {
            for (const [vill, shopsList] of Object.entries(vills)) {
                for (const s of shopsList) {
                    (s.inventory || []).forEach(item => {
                        flat.push({
                            shop: s.shop,
                            province: prov,
                            district: dist,
                            village: vill,
                            item_name: item.item_name,
                            quantity: item.quantity,
                            unit: item.unit
                        });
                    });
                }
            }
        }
    }
    return flat;
}

function filterInventoryList(flatList, query) {
    const q = query.toLowerCase().trim();
    if (!q) return flatList;
    return flatList.filter(row => 
        (row.shop && row.shop.toLowerCase().includes(q)) ||
        (row.item_name && row.item_name.toLowerCase().includes(q)) ||
        (row.province && row.province.toLowerCase().includes(q)) ||
        (row.district && row.district.toLowerCase().includes(q)) ||
        (row.village && row.village.toLowerCase().includes(q))
    );
}

// ========== HQ WAREHOUSE FUNCTIONS ==========

async function loadHqWarehouse() {
    if (userMeta.role !== 'HQ') return;
    
    try {
        const res = await fetch('/hq/warehouse', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        
        currentHqWarehouse = await res.json();
        renderHqWarehouseDashboard();
    } catch (err) {
        console.error('Error loading HQ warehouse:', err);
    }
}

function renderHqWarehouseDashboard() {
    if (!currentHqWarehouse) return;

    const fertilizers = currentHqWarehouse.fertilizers || [];
    const assets = currentHqWarehouse.assets || [];
    const cashPool = currentHqWarehouse.cash_pool || {};
    const distribution = currentHqWarehouse.distribution_history || [];

    const totalFert = fertilizers.reduce((sum, f) => sum + (f.quantity || 0), 0);
    const totalAssets = assets.reduce((sum, a) => sum + (a.quantity || 0), 0);
    const availableCash = cashPool.available_for_disbursement || 0;

    const setText = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setText('hq-stat-fert-total', totalFert.toLocaleString());
    setText('hq-stat-asset-total', totalAssets);
    setText('hq-stat-cash-total', 'ZMW ' + Number(availableCash).toLocaleString());
    setText('hq-stat-distributed', distribution.length);
}

function renderHqFertilizerTable() {
    const tbody = document.getElementById('hq-fertilizer-table-body');
    if (!tbody || !currentHqWarehouse) return;
    
    tbody.innerHTML = '';
    const fertilizers = currentHqWarehouse.fertilizers || [];
    const search = (document.getElementById('hq-fert-search')?.value || '').toLowerCase();
    const filtered = fertilizers.filter(f => 
        f.item_name?.toLowerCase().includes(search) ||
        f.batch_no?.toLowerCase().includes(search)
    );

    filtered.forEach(f => {
        const today = new Date();
        const expiry = new Date(f.expiry_date || '2099-12-31');
        const daysToExpiry = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
        let statusClass = 'badge-active';
        let statusText = 'Good';
        if (daysToExpiry < 0) {
            statusClass = 'badge-warning';
            statusText = 'Expired';
        } else if (daysToExpiry < 90) {
            statusClass = 'badge-warning';
            statusText = `Expiring in ${daysToExpiry} days`;
        }

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${f.item_name}</strong></td>
            <td><span class="badge badge-primary">${f.quantity?.toLocaleString()}</span></td>
            <td>${f.unit}</td>
            <td><code>${f.batch_no || 'N/A'}</code></td>
            <td>${f.expiry_date || 'N/A'}</td>
            <td><span class="badge ${statusClass}">${statusText}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderHqAssetTable() {
    const tbody = document.getElementById('hq-asset-table-body');
    if (!tbody || !currentHqWarehouse) return;
    
    tbody.innerHTML = '';
    const assets = currentHqWarehouse.assets || [];
    const search = (document.getElementById('hq-asset-search')?.value || '').toLowerCase();
    const filtered = assets.filter(a => 
        a.item_name?.toLowerCase().includes(search)
    );

    filtered.forEach(a => {
        const statusClass = a.status === 'available' ? 'badge-active' : 'badge-warning';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${a.item_name}</strong></td>
            <td><span class="badge badge-primary">${a.quantity}</span></td>
            <td>${a.unit}</td>
            <td>ZMW ${(a.purchase_cost || 0).toLocaleString()}</td>
            <td>${a.financing_terms || 'N/A'}</td>
            <td><span class="badge ${statusClass}">${a.status || 'N/A'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderHqDistributionTable() {
    const tbody = document.getElementById('hq-distribution-table-body');
    if (!tbody || !currentHqWarehouse) return;
    
    tbody.innerHTML = '';
    const history = currentHqWarehouse.distribution_history || [];
    const search = (document.getElementById('hq-dist-search')?.value || '').toLowerCase();
    const filtered = history.filter(d => 
        d.shop?.toLowerCase().includes(search) ||
        d.item?.toLowerCase().includes(search) ||
        d.date?.includes(search) ||
        d.province?.toLowerCase().includes(search) ||
        d.district?.toLowerCase().includes(search)
    );

    filtered.forEach(d => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${d.date}</td>
            <td><strong>${d.shop}</strong></td>
            <td>${d.province}</td>
            <td>${d.district}</td>
            <td>${d.village}</td>
            <td>${d.item}</td>
            <td><span class="badge badge-primary">${d.quantity}</span></td>
            <td>${d.unit}</td>
            <td>${d.type}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderHqWarehouseAlerts() {
    const container = document.getElementById('hq-warehouse-alerts');
    if (!container || !currentHqWarehouse) return;
    
    const alerts = [];
    const today = new Date();

    const fertilizers = currentHqWarehouse.fertilizers || [];
    fertilizers.forEach(f => {
        if (f.quantity < 500) {
            alerts.push({
                type: 'low-stock',
                message: `Low stock: ${f.item_name} (${f.quantity} ${f.unit} left)`,
                color: 'var(--amber)'
            });
        }
        const expiry = new Date(f.expiry_date || '2099-12-31');
        const daysToExpiry = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
        if (daysToExpiry < 90 && daysToExpiry >= 0) {
            alerts.push({
                type: 'expiry',
                message: `Expiry alert: ${f.item_name} (Batch: ${f.batch_no}) expires in ${daysToExpiry} days`,
                color: 'var(--rose)'
            });
        } else if (daysToExpiry < 0) {
            alerts.push({
                type: 'expired',
                message: `EXPIRED: ${f.item_name} (Batch: ${f.batch_no}) has expired`,
                color: '#ef4444'
            });
        }
    });

    const assets = currentHqWarehouse.assets || [];
    assets.forEach(a => {
        if (a.quantity <= 2) {
            alerts.push({
                type: 'low-stock',
                message: `Low asset stock: ${a.item_name} (only ${a.quantity} left)`,
                color: 'var(--amber)'
            });
        }
    });

    const cashPool = currentHqWarehouse.cash_pool || {};
    const available = cashPool.available_for_disbursement || 0;
    if (available < 50000) {
        alerts.push({
            type: 'cash',
            message: `Cash reserve low: ZMW ${available.toLocaleString()} available for disbursement`,
            color: 'var(--rose)'
        });
    }

    container.innerHTML = '';
    if (alerts.length === 0) {
        container.innerHTML = '<div style="color: var(--text-dim); text-align: center; padding: 12px;">No active alerts. All systems normal.</div>';
        return;
    }

    alerts.forEach(a => {
        const div = document.createElement('div');
        div.style.cssText = `display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: rgba(255,255,255,0.03); border-radius: var(--radius-sm); border-left: 3px solid ${a.color};`;
        div.innerHTML = `<i class="fa-solid fa-circle-exclamation" style="color: ${a.color};"></i> <span style="font-size: 13px;">${a.message}</span>`;
        container.appendChild(div);
    });
}

function populateShopSearch() {
    const datalist = document.getElementById('shop-list');
    if (!datalist) return;

    if (!shopsData || Object.keys(shopsData).length === 0) {
        loadShopsDirectory().then(() => fillShopSearchDatalist());
    } else {
        fillShopSearchDatalist();
    }
}

function fillShopSearchDatalist() {
    const datalist = document.getElementById('shop-list');
    if (!datalist) return;

    datalist.innerHTML = '';
    shopSearchList = [];

    for (const [prov, dists] of Object.entries(shopsData || {})) {
        for (const [dist, vills] of Object.entries(dists)) {
            for (const [vill, shopDict] of Object.entries(vills)) {
                for (const shopName of Object.keys(shopDict)) {
                    const shopData = shopDict[shopName] || {};
                    shopSearchList.push({
                        name: shopName,
                        id: shopData.shop_id || '',
                        province: prov,
                        district: dist,
                        village: vill
                    });
                }
            }
        }
    }

    shopSearchList.sort((a, b) => (a.id || a.name).localeCompare(b.id || b.name) || a.name.localeCompare(b.name));

    shopSearchList.forEach(shop => {
        const opt = document.createElement('option');
        opt.value = `${shop.id} -- ${shop.name}`;
        datalist.appendChild(opt);
    });

    const shopInput = document.getElementById('hq-alloc-shop-input') || document.getElementById('stock-shop-input');
    const provinceInput = document.getElementById('hq-alloc-province-input') || document.getElementById('stock-province-input');
    const districtInput = document.getElementById('hq-alloc-district-input') || document.getElementById('stock-district-input');
    const villageInput = document.getElementById('hq-alloc-village-input') || document.getElementById('stock-village-input');
    const shopPreview = document.getElementById('hq-shop-details-preview');
    const shopPreviewContent = document.getElementById('hq-shop-details-content');
    
    if (shopInput) {
        shopInput.oninput = function() {
            const val = this.value.trim();
            let selected = null;

            if (val.includes(' -- ')) {
                const parts = val.split(' -- ');
                const shopName = parts.slice(1).join(' -- ');
                selected = shopSearchList.find(s => s.name === shopName);
            } else {
                selected = shopSearchList.find(s => s.id === val || s.name === val);
            }

            if (selected) {
                this.value = selected.name;
                if (provinceInput) provinceInput.value = selected.province;
                if (districtInput) districtInput.value = selected.district;
                if (villageInput) villageInput.value = selected.village;
                
                if (shopPreview && shopPreviewContent) {
                    const shopData = (shopsData || {});
                    let shopInfo = null;
                    for (const [prov, dists] of Object.entries(shopData)) {
                        for (const [dist, vills] of Object.entries(dists)) {
                            for (const [vill, shopDict] of Object.entries(vills)) {
                                if (shopDict[selected.name]) {
                                    shopInfo = shopDict[selected.name];
                                    break;
                                }
                            }
                            if (shopInfo) break;
                        }
                        if (shopInfo) break;
                    }
                    
                    if (shopInfo) {
                        const invCount = (shopInfo.inventory || []).length;
                        const farmerCount = (shopInfo.clients?.farmers || []).length;
                        shopPreviewContent.innerHTML = `
                            <strong>${selected.name}</strong> (${selected.id}) |
                            ${selected.province} > ${selected.district} > ${selected.village} |
                            Agent: ${shopInfo.agent || 'Unassigned'} |
                            Status: ${shopInfo.status || 'active'} |
                            Max Loan: ZMW ${shopInfo.max_loan_limit || 10000} |
                            Inventory Items: ${invCount} |
                            Farmers: ${farmerCount}
                        `;
                        shopPreview.style.display = 'block';
                    } else {
                        shopPreview.style.display = 'none';
                    }
                }
            }
        };
    }
}

function updateHqStockFields() {
    const category = document.getElementById('hq-stock-category').value;
    const batchFields = document.getElementById('hq-stock-batch-fields');
    const assetFields = document.getElementById('hq-stock-asset-fields');
    const unitInput = document.getElementById('hq-stock-unit');

    if (category === 'asset') {
        batchFields.style.display = 'none';
        assetFields.style.display = 'block';
        unitInput.value = 'units';
    } else if (category === 'fertilizer' || category === 'seed' || category === 'pesticide') {
        batchFields.style.display = 'block';
        assetFields.style.display = 'none';
        if (category === 'fertilizer') unitInput.value = 'bags';
        else if (category === 'seed') unitInput.value = 'kg';
        else if (category === 'pesticide') unitInput.value = 'liters';
    } else {
        batchFields.style.display = 'none';
        assetFields.style.display = 'none';
    }
    populateHqStockItemSelect();
}

function populateHqStockItemSelect() {
    const categorySelect = document.getElementById('hq-stock-category');
    if (categorySelect) {
        categorySelect.onchange = function() {
            fillHqStockItemSelect();
            updateHqStockFields();
        };
    }
    
    if (!currentHqWarehouse) {
        loadHqWarehouse().then(() => fillHqStockItemSelect());
    } else {
        fillHqStockItemSelect();
    }
}

const categorySingularToPlural = {
    fertilizer: 'fertilizers',
    seed: 'seeds',
    pesticide: 'pesticides',
    asset: 'assets',
    other: 'other'
};

function fillHqStockItemSelect() {
    const select = document.getElementById('hq-stock-item-select');
    if (!select || !currentHqWarehouse) return;

    let category = document.getElementById('hq-stock-category').value;
    category = categorySingularToPlural[category] || category;
    const items = currentHqWarehouse[category] || [];
    const currentVal = select.value;

    select.innerHTML = '<option value="">Select Existing Item</option>';
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.item_name;
        opt.textContent = `${item.item_name} (${item.quantity} ${item.unit})`;
        select.appendChild(opt);
    });

    const customOpt = document.createElement('option');
    customOpt.value = '__custom__';
    customOpt.textContent = '➕ New Item Type...';
    select.appendChild(customOpt);

    if (items.some(i => i.item_name === currentVal)) {
        select.value = currentVal;
    }
    onHqStockItemSelectChange();
}

function onHqStockItemSelectChange() {
    const select = document.getElementById('hq-stock-item-select');
    const textInput = document.getElementById('hq-stock-item-name');
    const unitInput = document.getElementById('hq-stock-unit');
    const preview = document.getElementById('hq-item-details-preview');
    const previewContent = document.getElementById('hq-item-details-content');

    if (!select || !textInput || !unitInput) return;

    if (select.value === '__custom__') {
        textInput.style.display = 'block';
        textInput.required = true;
        select.required = false;
        if (preview) preview.style.display = 'none';
    } else {
        textInput.style.display = 'none';
        textInput.required = false;
        select.required = true;
        if (select.value && window.hqInventoryItems) {
            const itemName = select.value;
            const item = window.hqInventoryItems.find(i => i.name === itemName);
            if (item && preview && previewContent) {
                previewContent.innerHTML = `
                    <strong>${item.name}</strong> |
                    Category: ${item.category} |
                    Unit: ${item.unit} |
                    HQ Stock: ${item.hq_stock} |
                    Available: ${item.available_stock} |
                    Cost: ZMW ${item.cost_price} |
                    Loan Value: ZMW ${item.loan_value} |
                    Selling: ZMW ${item.selling_price} |
                    Supplier: ${item.supplier || '-'}
                `;
                preview.style.display = 'block';
                unitInput.value = item.unit || unitInput.value;
            } else if (preview) {
                preview.style.display = 'none';
            }
        } else if (preview) {
            preview.style.display = 'none';
        }
    }
}

async function handleAddHqStock(e) {
    e.preventDefault();
    const txType = document.getElementById('hq-stock-tx-type').value;
    const category = document.getElementById('hq-stock-category').value;
    const itemSelect = document.getElementById('hq-stock-item-select');
    const customInput = document.getElementById('hq-stock-item-name');
    const itemName = itemSelect.value === '__custom__' ? customInput.value : itemSelect.value;

    if (!itemName) {
        showToast('Please select or enter an item name', 'error');
        return;
    }

    const payload = {
        type: txType,
        item_name: itemName,
        quantity: parseInt(document.getElementById('hq-stock-qty').value),
        unit: document.getElementById('hq-stock-unit').value,
        notes: document.getElementById('hq-stock-notes').value
    };

    if (txType === 'purchase') {
        payload.purchase_cost = parseFloat(document.getElementById('hq-stock-cost').value) || 0;
        payload.supplier = document.getElementById('hq-stock-supplier').value;
    }

    const batchNo = document.getElementById('hq-stock-batch').value;
    const expiryDate = document.getElementById('hq-stock-expiry').value;
    if (batchNo) payload.batch_no = batchNo;
    if (expiryDate) payload.expiry_date = expiryDate;

    try {
        const res = await fetch('/inventory/transfer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to add stock', 'error');
            return;
        }

        showToast(data.message);
        closeModal('add-hq-stock-modal');
        document.getElementById('add-hq-stock-form').reset();
        document.getElementById('hq-item-details-preview').style.display = 'none';
        await loadHqInventory();
        await loadHqInventoryTransactions();
        await loadHqInventoryAlerts();
        await loadHqWarehouse();
        renderHqDashboardStats();
    } catch (err) {
        showToast('Error adding stock', 'error');
    }
}

async function loadHqWarehouseItems() {
    const categoryEl = document.getElementById('stock-category') || document.getElementById('hq-alloc-category');
    const shopSelect = document.getElementById('hq-alloc-item-select') || document.getElementById('stock-item-select');
    const hqSelect = document.getElementById('stock-hq-item-select');
    const availableInput = document.getElementById('hq-alloc-available') || document.getElementById('stock-available-balance');
    const hqBalanceInput = document.getElementById('stock-available-balance') || document.getElementById('hq-alloc-available');
    
    if (!categoryEl) return;
    const category = categoryEl.value;
    
    if (!shopSelect && !hqSelect) return;
    
    if (!currentHqWarehouse) {
        await loadHqWarehouse();
    }
    
    if (!currentHqWarehouse) return;
    
    const items = currentHqWarehouse[category] || [];
    
    if (shopSelect) {
        shopSelect.innerHTML = '<option value="">Select Item</option>';
        items.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.item_name;
            opt.textContent = `${item.item_name} (${item.quantity} ${item.unit} available)`;
            opt.dataset.quantity = item.quantity;
            opt.dataset.unit = item.unit;
            shopSelect.appendChild(opt);
        });

        shopSelect.onchange = function() {
            const selected = items.find(i => i.item_name === this.value);
            if (selected) {
                availableInput.value = `${selected.quantity} ${selected.unit}`;
                hqBalanceInput.value = `${selected.quantity} ${selected.unit}`;
            } else {
                availableInput.value = '0 bags';
                hqBalanceInput.value = '0 bags';
            }
        };
    }
    
    if (hqSelect) {
        hqSelect.innerHTML = '<option value="">Select Item</option>';
        items.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.item_name;
            opt.textContent = `${item.item_name} (${item.quantity} ${item.unit})`;
            opt.dataset.quantity = item.quantity;
            opt.dataset.unit = item.unit;
            hqSelect.appendChild(opt);
        });

        hqSelect.onchange = function() {
            const selected = items.find(i => i.item_name === this.value);
            if (selected) {
                hqBalanceInput.value = `${selected.quantity} ${selected.unit}`;
                document.getElementById('stock-unit-input').value = selected.unit || 'bags';
            } else {
                hqBalanceInput.value = '0 bags';
            }
        };
    }
}


function onStockActionChange() {
    const actionType = document.getElementById('stock-action-type').value;
    const shopSection = document.getElementById('stock-shop-section');
    const purchaseFields = document.getElementById('stock-purchase-fields');
    const adjustReason = document.getElementById('stock-adjust-reason');
    const confirmBtn = document.getElementById('stock-confirm-btn');

    if (!shopSection || !purchaseFields || !adjustReason || !confirmBtn) return;

    if (actionType === 'transfer_out') {
        shopSection.style.display = 'block';
        purchaseFields.style.display = 'none';
        adjustReason.style.display = 'none';
        confirmBtn.innerHTML = '<i class="fa-solid fa-truck-ramp-box"></i> Allocate Stock';
        confirmBtn.className = 'btn btn-cyan';
    } else if (actionType === 'purchase') {
        shopSection.style.display = 'none';
        purchaseFields.style.display = 'block';
        adjustReason.style.display = 'none';
        confirmBtn.innerHTML = '<i class="fa-solid fa-plus"></i> Add Stock';
        confirmBtn.className = 'btn btn-emerald';
    } else if (actionType === 'return') {
        shopSection.style.display = 'block';
        purchaseFields.style.display = 'none';
        adjustReason.style.display = 'none';
        confirmBtn.innerHTML = '<i class="fa-solid fa-rotate-left"></i> Process Return';
        confirmBtn.className = 'btn btn-primary';
    } else if (actionType === 'damaged') {
        shopSection.style.display = 'none';
        purchaseFields.style.display = 'none';
        adjustReason.style.display = 'block';
        confirmBtn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Mark as Damaged';
        confirmBtn.className = 'btn btn-rose';
    } else if (actionType === 'expired') {
        shopSection.style.display = 'none';
        purchaseFields.style.display = 'none';
        adjustReason.style.display = 'block';
        confirmBtn.innerHTML = '<i class="fa-solid fa-clock"></i> Mark as Expired';
        confirmBtn.className = 'btn btn-rose';
    } else if (actionType === 'adjustment') {
        shopSection.style.display = 'none';
        purchaseFields.style.display = 'none';
        adjustReason.style.display = 'block';
        confirmBtn.innerHTML = '<i class="fa-solid fa-pen-to-square"></i> Apply Adjustment';
        confirmBtn.className = 'btn btn-amber';
    }
}

async function handleStockAction() {
    const actionType = document.getElementById('stock-action-type').value;
    const category = document.getElementById('stock-category').value;
    const reason = document.getElementById('stock-reason')?.value || '';

    if (actionType === 'transfer_out' || actionType === 'return') {
        const shopInput = document.getElementById('stock-shop-input').value;
        const itemSelect = document.getElementById('stock-item-select');
        const itemName = itemSelect.value;
        const qty = parseInt(document.getElementById('stock-qty-input').value);

        if (!shopInput || !itemName || !qty || qty <= 0) {
            showToast('Please fill all required fields', 'error');
            return;
        }

        const shopMatch = shopSearchList.find(s => s.name === shopInput || s.id === shopInput);
        const payload = {
            type: actionType,
            shop_id: shopMatch ? shopMatch.id : undefined,
            shop_name: shopInput,
            item_id: itemName.toLowerCase().replace(/ /g, '_'),
            item_name: itemName,
            quantity: qty,
            unit: itemSelect.selectedOptions[0]?.dataset?.unit || 'bags',
            notes: reason
        };

        try {
            const res = await fetch('/inventory/transfer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (!res.ok) {
                showToast(data.error || `Failed to ${actionType} stock`, 'error');
                return;
            }

            showToast(data.message);
            closeModal('stock-management-modal');
            document.getElementById('stock-management-form').reset();
            await loadHqInventory();
            await loadHqInventoryTransactions();
            await loadHqInventoryAlerts();
            await loadHqWarehouse();
            renderHqDashboardStats();
        } catch (err) {
            showToast('Error processing stock action', 'error');
        }
    } else if (actionType === 'purchase') {
        const itemSelect = document.getElementById('stock-hq-item-select');
        const itemName = itemSelect.value;
        const qty = parseInt(document.getElementById('stock-qty-input').value);
        const supplier = document.getElementById('stock-supplier').value;
        const batch = document.getElementById('stock-batch').value;
        const expiry = document.getElementById('stock-expiry').value;

        if (!itemName || !qty || qty <= 0) {
            showToast('Please select an item and enter quantity', 'error');
            return;
        }

        const payload = {
            type: 'purchase',
            item_id: itemName.toLowerCase().replace(/ /g, '_'),
            item_name: itemName,
            quantity: qty,
            unit: document.getElementById('stock-unit-input').value,
            supplier: supplier,
            batch_no: batch,
            expiry_date: expiry,
            notes: reason
        };

        try {
            const res = await fetch('/inventory/transfer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (!res.ok) {
                showToast(data.error || 'Failed to add stock', 'error');
                return;
            }

            showToast(data.message);
            closeModal('stock-management-modal');
            document.getElementById('stock-management-form').reset();
            await loadHqInventory();
            await loadHqInventoryTransactions();
            await loadHqInventoryAlerts();
            await loadHqWarehouse();
            renderHqDashboardStats();
        } catch (err) {
            showToast('Error adding stock', 'error');
        }
    } else if (actionType === 'damaged' || actionType === 'expired') {
        const itemSelect = document.getElementById('stock-hq-item-select');
        const itemName = itemSelect.value;
        const qty = parseInt(document.getElementById('stock-qty-input').value);

        if (!itemName || !qty || qty <= 0) {
            showToast('Please select an item and enter quantity', 'error');
            return;
        }
        if (!reason) {
            showToast('Please provide a reason', 'error');
            return;
        }

        const payload = {
            type: actionType,
            item_id: itemName.toLowerCase().replace(/ /g, '_'),
            item_name: itemName,
            quantity: qty,
            unit: document.getElementById('stock-unit-input').value,
            notes: reason
        };

        try {
            const res = await fetch('/inventory/transfer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (!res.ok) {
                showToast(data.error || `Failed to mark as ${actionType}`, 'error');
                return;
            }

            showToast(data.message);
            closeModal('stock-management-modal');
            document.getElementById('stock-management-form').reset();
            await loadHqInventory();
            await loadHqInventoryTransactions();
            await loadHqInventoryAlerts();
            await loadHqWarehouse();
            renderHqDashboardStats();
        } catch (err) {
            showToast('Error updating stock', 'error');
        }
    } else if (actionType === 'adjustment') {
        const itemSelect = document.getElementById('stock-hq-item-select');
        const itemName = itemSelect.value;
        const qty = parseInt(document.getElementById('stock-qty-input').value);

        if (!itemName || !qty || qty === 0) {
            showToast('Please select an item and enter quantity change', 'error');
            return;
        }
        if (!reason) {
            showToast('Please provide a reason', 'error');
            return;
        }

        const payload = {
            item_id: itemName.toLowerCase().replace(/ /g, '_'),
            item_name: itemName,
            quantity_change: qty,
            reason: reason
        };

        try {
            const res = await fetch('/inventory/adjust', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (!res.ok) {
                showToast(data.error || 'Failed to adjust stock', 'error');
                return;
            }

            showToast(data.message);
            closeModal('stock-management-modal');
            document.getElementById('stock-management-form').reset();
            await loadHqInventory();
            await loadHqInventoryTransactions();
            await loadHqInventoryAlerts();
            await loadHqWarehouse();
            renderHqDashboardStats();
        } catch (err) {
            showToast('Error adjusting stock', 'error');
        }
    }
}



async function handleUpdateCashPool(e) {
    e.preventDefault();
    const payload = {
        total_cash: parseFloat(document.getElementById('hq-cash-total').value),
        allocated_to_shops: parseFloat(document.getElementById('hq-cash-allocated').value),
        reserved: parseFloat(document.getElementById('hq-cash-reserved').value),
        available_for_disbursement: parseFloat(document.getElementById('hq-cash-total').value) - parseFloat(document.getElementById('hq-cash-allocated').value) - parseFloat(document.getElementById('hq-cash-reserved').value)
    };

    try {
        const res = await fetch('/hq/warehouse/cash', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to update cash pool', 'error');
            return;
        }

        showToast(data.message);
        closeModal('add-cash-pool-modal');
        document.getElementById('add-cash-pool-form').reset();
        await loadHqWarehouse();
        renderHqDashboardStats();
    } catch (err) {
        showToast('Error updating cash pool', 'error');
    }
}

function filterHqFertilizerTable() {
    renderHqFertilizerTable();
}

function filterHqAssetTable() {
    renderHqAssetTable();
}

function filterHqDistributionTable() {
    renderHqDistributionTable();
}

async function loadHqInventory() {
    try {
        const res = await fetch('/inventory/items', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        window.hqInventoryItems = data.items || [];
        renderHqInventoryTable();
        updateHqInventoryKpis();
    } catch (err) {
        console.error('Error loading inventory:', err);
    }
}

function renderHqInventoryTable() {
    const tbody = document.getElementById('hq-inventory-table-body');
    const searchInput = document.getElementById('hq-inv-search');
    const term = (searchInput ? searchInput.value : '').toLowerCase();
    tbody.innerHTML = '';
    
    const items = (window.hqInventoryItems || []).filter(item => {
        if (!term) return true;
        return (item.name || '').toLowerCase().includes(term) || 
               (item.category || '').toLowerCase().includes(term) ||
               (item.item_id || '').toLowerCase().includes(term);
    });
    
    if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--text-dim); padding: 20px;">No inventory items found.</td></tr>`;
        return;
    }
    
    items.forEach(item => {
        const tr = document.createElement('tr');
        const availClass = item.available_stock <= item.low_stock_threshold ? 'text-warning' : '';
        tr.innerHTML = `
            <td><code>${item.item_id}</code></td>
            <td><strong>${item.name}</strong></td>
            <td><span class="badge badge-primary">${item.category}</span></td>
            <td>${item.unit}</td>
            <td>${item.hq_stock}</td>
            <td>${item.allocated_to_shops}</td>
            <td class="${availClass}"><strong>${item.available_stock}</strong></td>
            <td>ZMW ${(item.cost_price || 0).toLocaleString()}</td>
            <td>ZMW ${(item.loan_value || 0).toLocaleString()}</td>
            <td>ZMW ${(item.selling_price || 0).toLocaleString()}</td>
            <td>${item.supplier || '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterHqInventoryTable() {
    renderHqInventoryTable();
}

function updateHqInventoryKpis() {
    const items = window.hqInventoryItems || [];
    const totalItems = items.length;
    const hqBalance = items.reduce((sum, i) => sum + (i.hq_stock || 0), 0);
    const allocated = items.reduce((sum, i) => sum + (i.allocated_to_shops || 0), 0);
    const available = items.reduce((sum, i) => sum + (i.available_stock || 0), 0);
    
    setText('hq-inv-total-items', totalItems);
    setText('hq-inv-hq-balance', hqBalance.toLocaleString());
    setText('hq-inv-allocated', allocated.toLocaleString());
    setText('hq-inv-available', available.toLocaleString());
}

async function loadHqInventoryTransactions() {
    try {
        const res = await fetch('/inventory/transactions', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        window.hqInventoryTransactions = data.transactions || [];
        renderHqInventoryTransactions();
    } catch (err) {
        console.error('Error loading transactions:', err);
    }
}

function renderHqInventoryTransactions() {
    const tbody = document.getElementById('hq-inventory-tx-table-body');
    const searchInput = document.getElementById('hq-inv-tx-search');
    const term = (searchInput ? searchInput.value : '').toLowerCase();
    tbody.innerHTML = '';
    
    const txs = (window.hqInventoryTransactions || []).filter(tx => {
        if (!term) return true;
        return (tx.item_name || '').toLowerCase().includes(term) || 
               (tx.type || '').toLowerCase().includes(term) ||
               (tx.shop_name || '').toLowerCase().includes(term) ||
               (tx.notes || '').toLowerCase().includes(term);
    });
    
    if (txs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 20px;">No transactions found.</td></tr>`;
        return;
    }
    
    txs.forEach(tx => {
        const tr = document.createElement('tr');
        const typeColors = {
            'purchase': 'var(--emerald)',
            'transfer_out': 'var(--amber)',
            'return': 'var(--cyan)',
            'damaged': 'var(--rose)',
            'expired': 'var(--rose)',
            'adjustment': 'var(--primary)'
        };
        const color = typeColors[tx.type] || 'var(--text-muted)';
        tr.innerHTML = `
            <td>${tx.date}</td>
            <td><strong>${tx.item_name}</strong></td>
            <td><span style="color: ${color}; font-weight: 600;">${tx.type}</span></td>
            <td>${tx.quantity} ${tx.unit}</td>
            <td>${tx.shop_name || '-'}</td>
            <td>${tx.created_by} <small style="color: var(--text-dim);">(${tx.created_by_role})</small></td>
            <td>${tx.notes || '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterHqInventoryTransactions() {
    renderHqInventoryTransactions();
}

async function loadHqInventoryAlerts() {
    try {
        const res = await fetch('/inventory/alerts', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        const container = document.getElementById('hq-inventory-alerts');
        if (!container) return;
        
        const alerts = data.alerts || [];
        container.innerHTML = '';
        if (alerts.length === 0) {
            container.innerHTML = '<div style="color: var(--text-dim); text-align: center; padding: 12px;">No active inventory alerts.</div>';
            return;
        }
        
        alerts.forEach(a => {
            const div = document.createElement('div');
            div.style.cssText = `display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: rgba(255,255,255,0.03); border-radius: var(--radius-sm); border-left: 3px solid ${a.severity === 'high' ? 'var(--rose)' : 'var(--amber)'};`;
            div.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="color: ${a.severity === 'high' ? 'var(--rose)' : 'var(--amber)'};"></i> <span style="font-size: 13px;">${a.message}</span>`;
            container.appendChild(div);
        });
    } catch (err) {
        console.error('Error loading inventory alerts:', err);
    }
}

function openInventoryAdjustModal() {
    const itemSelect = document.getElementById('inv-adjust-item-select');
    if (!itemSelect) return;
    
    itemSelect.innerHTML = '<option value="">Select Item</option>';
    (window.hqInventoryItems || []).forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.item_id;
        opt.textContent = `${item.name} (Available: ${item.available_stock})`;
        itemSelect.appendChild(opt);
    });
    
    openModal('adjust-inventory-modal');
}

async function handleAdjustInventory(e) {
    e.preventDefault();
    const itemId = document.getElementById('inv-adjust-item-select').value;
    const qtyChange = parseInt(document.getElementById('inv-adjust-qty').value);
    const reason = document.getElementById('inv-adjust-reason').value;
    
    if (!itemId || qtyChange === 0) {
        showToast('Please select an item and enter a quantity change', 'error');
        return;
    }
    
    const payload = {
        item_id: itemId,
        quantity_change: qtyChange,
        reason: reason
    };
    
    try {
        const res = await fetch('/inventory/adjust', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to adjust inventory', 'error');
            return;
        }
        
        showToast(data.message);
        closeModal('adjust-inventory-modal');
        document.getElementById('adjust-inventory-form').reset();
        await loadHqInventory();
        await loadHqInventoryTransactions();
        await loadHqInventoryAlerts();
    } catch (err) {
        showToast('Error adjusting inventory', 'error');
    }
}

// HQ: Allocate Inventory
async function handleHqAllocateInventory(e) {
    e.preventDefault();
    const payload = {
        shop: document.getElementById('hq-alloc-shop-input').value,
        province: document.getElementById('hq-alloc-province-input').value,
        district: document.getElementById('hq-alloc-district-input').value,
        village: document.getElementById('hq-alloc-village-input').value,
        item_name: document.getElementById('hq-alloc-item-input').value,
        quantity: parseInt(document.getElementById('hq-alloc-qty-input').value),
        unit: document.getElementById('hq-alloc-unit-input').value
    };

    try {
        const res = await fetch('/shops/allocate_inventory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to allocate inventory', 'error');
            return;
        }

        showToast(data.message);
        closeModal('allocate-inventory-hq-modal');
        document.getElementById('allocate-inventory-hq-form').reset();
        await loadDashboardData();
    } catch (err) {
        showToast('Error allocating inventory', 'error');
    }
}

// Render Summary Stats Cards
function renderSummaryCards(summary) {
    document.getElementById('stat-total-farmers').textContent = summary.total_farmers || 0;
    
    // Fertilizer
    document.getElementById('stat-fert-count').textContent = summary.fertilizer.count || 0;
    document.getElementById('stat-maize-remaining').textContent = summary.fertilizer.remaining_maize_bags || 0;
    document.getElementById('stat-maize-expected').textContent = summary.fertilizer.expected_maize_bags || 0;

    // Asset Finance
    document.getElementById('stat-asset-count').textContent = summary.asset_finance.count || 0;
    document.getElementById('stat-asset-balance').textContent = summary.asset_finance.balance_remaining.toLocaleString('en-US', {minimumFractionDigits: 2});

    // Cash Loans
    document.getElementById('stat-cash-count').textContent = summary.cash_loans.count || 0;
    document.getElementById('stat-cash-balance').textContent = summary.cash_loans.balance_remaining.toLocaleString('en-US', {minimumFractionDigits: 2});

    const scopeDesc = document.getElementById('stat-scope-desc');
    if (userMeta.role === 'HQ') scopeDesc.textContent = 'Scope: Entire Network (All Regions)';
    else if (userMeta.role === 'District') scopeDesc.textContent = `Scope: District ${userMeta.district}`;
    else if (userMeta.role === 'Village') scopeDesc.textContent = `Scope: Village ${userMeta.village}`;
    else if (userMeta.role === 'Agent') scopeDesc.textContent = `Scope: Shop ${userMeta.shop}`;
}

async function openLoanDetail(loanId) {
    try {
        const scheduleRes = await fetch(`/loans/${loanId}/schedule`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!scheduleRes.ok) return;
        const scheduleData = await scheduleRes.json();
        
        let loan = loansData.find(l => l.id === loanId);
        if (!loan) {
            const loanRes = await fetch(`/api/loans/${loanId}`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            if (loanRes.ok) {
                const loanApiData = await loanRes.json();
                loan = loanApiData.loan || {};
            } else {
                loan = {};
            }
        }
        
        const data = scheduleData;
        document.getElementById('detail-borrower-name').textContent = loan.name || '-';
        document.getElementById('detail-borrower-phone').textContent = loan.shop ? `Shop: ${loan.shop}` : '-';
        document.getElementById('detail-loan-amount').textContent = 'ZMW ' + (loan.loan_amount || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
        document.getElementById('detail-outstanding').textContent = 'ZMW ' + (data.balance_remaining || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
        document.getElementById('detail-status').innerHTML = `<span class="badge ${data.balance_remaining > 0 ? 'badge-active' : 'badge-completed'}">${loan.status || 'active'}</span>`;
        document.getElementById('detail-product').value = loan.loan_product_name || '-';
        document.getElementById('detail-interest-rate').value = (loan.interest_rate || 0) + '% (' + (loan.interest_type || 'Flat') + ')';
        document.getElementById('detail-frequency').value = loan.repayment_frequency || '-';
        document.getElementById('detail-grace').value = (loan.grace_period_days || 0) + ' days';
        document.getElementById('detail-disbursement').value = loan.disbursement_method || '-';
        document.getElementById('detail-created-by').value = loan.added_by || loan.created_by || '-';
        
        const scheduleBody = document.getElementById('detail-schedule-body');
        scheduleBody.innerHTML = '';
        if (data.schedule && data.schedule.length > 0) {
            data.schedule.forEach(row => {
                scheduleBody.innerHTML += `
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid var(--border);">${row.installment_no}</td>
                        <td style="padding: 8px; border-bottom: 1px solid var(--border);">${row.due_date}</td>
                        <td style="padding: 8px; text-align: right; border-bottom: 1px solid var(--border);">ZMW ${Number(row.due_principal).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td style="padding: 8px; text-align: right; border-bottom: 1px solid var(--border);">ZMW ${Number(row.due_interest).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td style="padding: 8px; text-align: right; border-bottom: 1px solid var(--border);">ZMW ${Number(row.due_fees).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td style="padding: 8px; text-align: center; border-bottom: 1px solid var(--border);"><span class="badge ${row.status === 'paid' ? 'badge-completed' : 'badge-active'}">${row.status}</span></td>
                    </tr>
                `;
            });
        }
        
        const auditBody = document.getElementById('detail-audit-log');
        auditBody.innerHTML = '';
        const auditTrail = loan.audit_trail || [];
        if (auditTrail.length === 0) {
            auditBody.innerHTML = '<div style="color: var(--text-dim); text-align: center; padding: 20px;">No audit entries.</div>';
        } else {
            auditTrail.forEach(entry => {
                auditBody.innerHTML += `
                    <div style="padding: 10px; border-bottom: 1px solid var(--border);">
                        <div style="font-weight: 600; color: var(--cyan);">${entry.action.replace(/_/g, ' ').toUpperCase()}</div>
                        <div style="font-size: 12px; color: var(--text-dim);">${entry.date} by ${entry.user} (${entry.role})</div>
                        <div style="font-size: 13px; margin-top: 4px;">${entry.notes || ''}</div>
                    </div>
                `;
            });
        }
        
        renderLoanActionButtons(loan);
        switchLoanTab('details');
        openModal('loan-detail-modal');
    } catch (err) {
        console.error('Error loading loan detail:', err);
    }
}

function renderLoanActionButtons(loan) {
    const container = document.getElementById('loan-action-buttons');
    if (!container) return;
    container.innerHTML = '';
    const status = loan.status || 'active';
    const loanType = loan.loan_type || 'cash';
    const isHQ = userMeta.role === 'HQ';
    const isAgent = userMeta.role === 'Agent';
    
    if (status === 'pending_approval') {
        if (isHQ) {
            container.innerHTML += `<button class="btn btn-sm btn-emerald" onclick="approveLoan('${loan.id}')"><i class="fa-solid fa-check"></i> Approve</button>`;
            container.innerHTML += `<button class="btn btn-sm btn-rose" onclick="rejectLoan('${loan.id}')"><i class="fa-solid fa-xmark"></i> Reject</button>`;
        }
        container.innerHTML += `<button class="btn btn-sm btn-amber" onclick="escalateLoan('${loan.id}')"><i class="fa-solid fa-arrow-up"></i> Escalate</button>`;
    }
    
    if (status === 'active' || status === 'approved') {
        if (isHQ) {
            container.innerHTML += `<button class="btn btn-sm btn-primary" onclick="scheduleDisbursement('${loan.id}')"><i class="fa-solid fa-calendar"></i> Schedule Disbursement</button>`;
            container.innerHTML += `<button class="btn btn-sm btn-emerald" onclick="disburseLoan('${loan.id}')"><i class="fa-solid fa-money-bill-transfer"></i> Disburse Now</button>`;
            container.innerHTML += `<button class="btn btn-sm btn-amber" onclick="holdDisbursement('${loan.id}')"><i class="fa-solid fa-pause"></i> Hold Disbursement</button>`;
        }
    }
    
    if (status === 'active') {
        if (isHQ || isAgent) {
            container.innerHTML += `<button class="btn btn-sm btn-cyan" onclick="openRepaymentModal('${loan.id}', '${loanType === 'asset_finance' ? 'asset_finance' : (loanType === 'fertilizer' ? 'fertilizer' : 'cash')}', '${loan.name}', 'ZMW ${loan.balance_remaining}')"><i class="fa-solid fa-money-bill-wave"></i> Quick Repay</button>`;
        }
        if (loanType === 'cash' || loan.restructuring_allowed) {
            container.innerHTML += `<button class="btn btn-sm btn-amber" onclick="openRestructureModal('${loan.id}')"><i class="fa-solid fa-arrows-rotate"></i> Restructure</button>`;
        }
        container.innerHTML += `<button class="btn btn-sm btn-primary" onclick="openScheduleModal('${loan.id}')"><i class="fa-solid fa-calendar-days"></i> View Schedule</button>`;
        container.innerHTML += `<button class="btn btn-sm btn-rose" onclick="closeLoan('${loan.id}')"><i class="fa-solid fa-check-double"></i> Close Loan</button>`;
    }
    
    if (isHQ) {
        container.innerHTML += `<button class="btn btn-sm btn-rose" onclick="writeOffLoan('${loan.id}')"><i class="fa-solid fa-trash-can"></i> Write-off</button>`;
        container.innerHTML += `<button class="btn btn-sm btn-primary" onclick="exportLoanPDF('${loan.id}')"><i class="fa-solid fa-file-pdf"></i> Export Loan PDF</button>`;
    }
}

function switchLoanTab(tabName) {
    document.querySelectorAll('.loan-tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('[id^="tab-btn-"]').forEach(el => el.className = 'btn btn-sm');
    document.getElementById('loan-tab-' + tabName).style.display = 'block';
    document.getElementById('tab-btn-' + tabName).className = 'btn btn-sm btn-primary';
}

async function approveLoan(loanId) {
    try {
        const res = await fetch(`/api/loans/${loanId}/approve`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to approve loan', 'error');
            return;
        }
        showToast(data.message, 'success');
        closeModal('loan-detail-modal');
        loadDashboardData();
    } catch (err) {
        showToast('Error approving loan', 'error');
    }
}

async function rejectLoan(loanId) {
    showToast('Loan rejected', 'error');
    closeModal('loan-detail-modal');
    await loadDashboardData();
}

function escalateLoan(loanId) {
    showToast('Loan escalated for review', 'success');
    closeModal('loan-detail-modal');
    loadDashboardData();
}

function scheduleDisbursement(loanId) {
    showToast('Disbursement scheduled', 'success');
}

async function disburseLoan(loanId) {
    if (!confirm('Are you sure you want to disburse this loan now?')) return;
    try {
        const res = await fetch(`/api/loans/${loanId}/disburse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ amount: 0, method: 'cash' })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to disburse loan', 'error');
            return;
        }
        showToast(data.message || 'Loan disbursed successfully', 'success');
        closeModal('loan-detail-modal');
        loadDashboardData();
    } catch (err) {
        showToast('Error disbursing loan', 'error');
    }
}

function holdDisbursement(loanId) {
    showToast('Disbursement on hold', 'success');
    closeModal('loan-detail-modal');
    loadDashboardData();
}

async function closeLoan(loanId) {
    if (!confirm('Close this loan? This action cannot be undone.')) return;
    try {
        const res = await fetch(`/api/loans/${loanId}/close`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to close loan', 'error');
            return;
        }
        showToast(data.message, 'success');
        closeModal('loan-detail-modal');
        loadDashboardData();
    } catch (err) {
        showToast('Error closing loan', 'error');
    }
}

async function writeOffLoan(loanId) {
    if (!confirm('WARNING: Write-off this loan? This is irreversible.')) return;
    try {
        const res = await fetch(`/api/loans/${loanId}/writeoff`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to write off loan', 'error');
            return;
        }
        showToast(data.message, 'success');
        closeModal('loan-detail-modal');
        loadDashboardData();
    } catch (err) {
        showToast('Error writing off loan', 'error');
    }
}

function exportLoanPDF(loanId) {
    showToast('Generating PDF...', 'success');
}

function openRestructureModal(loanId) {
    document.getElementById('restructure-loan-id').value = loanId;
    document.getElementById('restructure-installments').value = '';
    document.getElementById('restructure-term-days').value = '';
    openModal('restructure-modal');
}

async function handleRestructure(e) {
    e.preventDefault();
    const loanId = document.getElementById('restructure-loan-id').value;
    const new_installments = parseInt(document.getElementById('restructure-installments').value);
    const new_term_days = parseInt(document.getElementById('restructure-term-days').value);

    try {
        const res = await fetch(`/loans/${loanId}/restructure`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ new_installments, new_term_days })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to restructure loan', 'error');
            return;
        }
        showToast(data.message);
        closeModal('restructure-modal');
        await loadDashboardData();
    } catch (err) {
        showToast('Error restructuring loan', 'error');
    }
}

async function openApplicationModal() {
    const productSelect = document.getElementById('app-product-select');
    productSelect.innerHTML = '<option value="">Select Product</option>';
    
    if (!window.loanProducts || window.loanProducts.length === 0) {
        try {
            const res = await fetch('/loan_products', {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            if (res.ok) {
                const data = await res.json();
                window.loanProducts = data.loan_products || [];
            }
        } catch (err) {
            console.error('Error loading products:', err);
        }
    }
    
    (window.loanProducts || []).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.name} (${p.type})`;
        opt.dataset.min = p.min_amount || 0;
        opt.dataset.max = p.max_amount || 0;
        opt.dataset.frequency = p.repayment_frequency || 'Monthly';
        productSelect.appendChild(opt);
    });
    document.getElementById('application-form').reset();
    document.getElementById('app-frequency').value = '';
    document.getElementById('app-amount-hint').textContent = '';
    openModal('application-modal');
}

function onAppProductChange() {
    const select = document.getElementById('app-product-select');
    const option = select.options[select.selectedIndex];
    if (option && option.value) {
        document.getElementById('app-frequency').value = option.dataset.frequency || 'Monthly';
        document.getElementById('app-amount-hint').textContent = `Min: ZMW ${option.dataset.min} | Max: ZMW ${option.dataset.max}`;
    } else {
        document.getElementById('app-frequency').value = '';
        document.getElementById('app-amount-hint').textContent = '';
    }
}

function runEligibilityCheck() {
    const borrowerName = document.getElementById('app-borrower-name').value.trim();
    const productSelect = document.getElementById('app-product-select');
    const amount = parseFloat(document.getElementById('app-amount').value);
    const option = productSelect.options[productSelect.selectedIndex];

    if (!borrowerName) {
        showToast('Please enter borrower name', 'error');
        return;
    }
    if (!option || !option.value) {
        showToast('Please select a product', 'error');
        return;
    }
    if (!amount || amount <= 0) {
        showToast('Please enter a valid amount', 'error');
        return;
    }

    const min = parseFloat(option.dataset.min || 0);
    const max = parseFloat(option.dataset.max || 0);
    if (amount < min || amount > max) {
        showToast(`Amount ZMW ${amount} is outside product range (${min} - ${max})`, 'error');
        return;
    }

    showToast('Eligibility check passed', 'success');
}

function filterCashLoans() {
    const branch = (document.getElementById('cash-filter-branch')?.value || '').toLowerCase();
    const product = (document.getElementById('cash-filter-product')?.value || '').toLowerCase();
    const status = (document.getElementById('cash-filter-status')?.value || '').toLowerCase();
    const search = (document.getElementById('cash-filter-search')?.value || '').toLowerCase();

    let filtered = (window.allCashLoans || []).slice();
    if (branch) filtered = filtered.filter(l => (l.shop || '').toLowerCase().includes(branch));
    if (product) filtered = filtered.filter(l => (l.loan_product_id || '').toLowerCase().includes(product));
    if (status) filtered = filtered.filter(l => (l.status || '').toLowerCase() === status);
    if (search) filtered = filtered.filter(l => (l.name || '').toLowerCase().includes(search) || (l.id || '').toLowerCase().includes(search));

    renderCashLoanTable(filtered);
}

function exportCashLoansCSV() {
    const loans = window.allCashLoans || [];
    if (loans.length === 0) {
        showToast('No loans to export', 'error');
        return;
    }
    const headers = ['Loan ID', 'Borrower', 'Shop', 'Amount', 'Total Repayable', 'Balance', 'Status'];
    const rows = loans.map(l => [l.id, l.name, l.shop, l.loan_amount, l.total_repayable, l.balance_remaining, l.status]);
    let csv = headers.join(',') + '\n';
    rows.forEach(r => csv += r.join(',') + '\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cash_loans.csv';
    a.click();
    URL.revokeObjectURL(url);
    showToast('CSV exported', 'success');
}

async function submitApplication(status) {
    const borrowerName = document.getElementById('app-borrower-name').value.trim();
    const productId = document.getElementById('app-product-select').value;
    const amount = parseFloat(document.getElementById('app-amount').value);
    const term = parseInt(document.getElementById('app-term').value);
    const collateral = document.getElementById('app-collateral').value.trim();
    const notes = document.getElementById('app-notes').value.trim();

    if (!borrowerName || !productId || !amount || !term) {
        showToast('Please fill all required fields', 'error');
        return;
    }

    const payload = {
        borrower_name: borrowerName,
        product_id: productId,
        requested_amount: amount,
        requested_term_days: term,
        repayment_frequency: document.getElementById('app-frequency').value || 'Monthly',
        collateral: collateral,
        attachments: notes ? [notes] : []
    };

    try {
        const res = await fetch('/api/applications', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to submit application', 'error');
            return;
        }
        showToast(data.message);
        closeModal('application-modal');
        await loadApplications();
    } catch (err) {
        showToast('Error submitting application', 'error');
    }
}

async function loadApplications() {
    try {
        const res = await fetch('/api/applications', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        window.loanApplications = data.applications || [];
        renderApplicationsTable();
    } catch (err) {
        console.error('Error loading applications:', err);
    }
}

function renderApplicationsTable() {
    const tbody = document.getElementById('applications-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    const applications = window.loanApplications || [];
    if (applications.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 20px;">No applications found.</td></tr>';
        return;
    }
    applications.forEach(a => {
        const statusClass = a.status === 'submitted' ? 'badge-active' : (a.status === 'approved' ? 'badge-completed' : 'badge-active');
        tbody.innerHTML += `
            <tr>
                <td><code>${a.application_id}</code></td>
                <td><strong>${a.borrower_name}</strong></td>
                <td>${a.product_name}</td>
                <td>ZMW ${Number(a.requested_amount).toLocaleString()}</td>
                <td><span class="badge ${statusClass}">${a.status}</span></td>
                <td>${a.submitted_at}</td>
            </tr>
        `;
    });
}

async function openPortfolioReport() {
    try {
        const res = await fetch('/reports/portfolio', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        document.getElementById('port-total-loans').textContent = data.total_loans || 0;
        document.getElementById('port-total-principal').textContent = 'ZMW ' + (data.total_principal || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
        document.getElementById('port-total-outstanding').textContent = 'ZMW ' + (data.total_outstanding || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
        document.getElementById('port-par30').textContent = data.par30 || 0;
        document.getElementById('port-overdue').textContent = data.overdue_count || 0;
        
        const statusBody = document.getElementById('portfolio-status-body');
        const typeBody = document.getElementById('portfolio-type-body');
        statusBody.innerHTML = '';
        typeBody.innerHTML = '';
        
        for (const [status, count] of Object.entries(data.by_status || {})) {
            statusBody.innerHTML += `<tr><td style="padding: 8px; border-bottom: 1px solid var(--border);"><span class="badge badge-active">${status}</span></td><td style="padding: 8px; text-align: right; border-bottom: 1px solid var(--border);">${count}</td></tr>`;
        }
        for (const [type, count] of Object.entries(data.by_type || {})) {
            typeBody.innerHTML += `<tr><td style="padding: 8px; border-bottom: 1px solid var(--border);">${type}</td><td style="padding: 8px; text-align: right; border-bottom: 1px solid var(--border);">${count}</td></tr>`;
        }
        openModal('portfolio-modal');
    } catch (err) {
        console.error('Error loading portfolio:', err);
    }
}

async function openScheduleModal(loanId) {
    try {
        const res = await fetch(`/loans/${loanId}/schedule`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        const tbody = document.getElementById('schedule-tbody');
        tbody.innerHTML = '';
        if (!data.schedule || data.schedule.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 12px;">No schedule generated.</td></tr>';
        } else {
            let total = 0;
            data.schedule.forEach(row => {
                const rowTotal = Number(row.due_principal) + Number(row.due_interest) + Number(row.due_fees);
                total += rowTotal;
                const statusClass = row.status === 'paid' ? 'badge-completed' : (row.status === 'overdue' ? 'badge-active' : 'badge-active');
                tbody.innerHTML += `
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid var(--border);">${row.installment_no}</td>
                        <td style="padding: 8px; border-bottom: 1px solid var(--border);">${row.due_date}</td>
                        <td style="padding: 8px; text-align: right; border-bottom: 1px solid var(--border);">ZMW ${Number(row.due_principal).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td style="padding: 8px; text-align: right; border-bottom: 1px solid var(--border);">ZMW ${Number(row.due_interest).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td style="padding: 8px; text-align: right; border-bottom: 1px solid var(--border);">ZMW ${Number(row.due_fees).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                        <td style="padding: 8px; text-align: center; border-bottom: 1px solid var(--border);"><span class="badge ${statusClass}">${row.status}</span></td>
                    </tr>
                `;
            });
            tbody.innerHTML += `
                <tr style="font-weight: 600; background: rgba(255,255,255,0.03);">
                    <td colspan="2" style="padding: 8px; border-bottom: 1px solid var(--border); text-align: right;">Total</td>
                    <td style="padding: 8px; text-align: right; border-bottom: 1px solid var(--border);">ZMW ${total.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                    <td colspan="3" style="padding: 8px; border-bottom: 1px solid var(--border);"></td>
                </tr>
            `;
        }
        openModal('schedule-modal');
    } catch (err) {
        console.error('Error loading schedule:', err);
    }
}

function renderHqDashboardStats() {
    if (userMeta.role !== 'HQ') return;

    let totalShops = 0;
    let totalProvinces = 0;
    let totalDistricts = 0;
    let totalVillages = 0;
    let totalInventoryItems = 0;
    let totalInventoryQty = 0;
    let totalAgents = 0;
    let totalLoans = 0;

    for (const [prov, dists] of Object.entries(shopsData || {})) {
        totalProvinces++;
        for (const [dist, vills] of Object.entries(dists)) {
            totalDistricts++;
            for (const [vill, shopsList] of Object.entries(vills)) {
                totalVillages++;
                totalShops += shopsList.length;
                shopsList.forEach(s => {
                    totalInventoryItems += (s.inventory || []).length;
                    (s.inventory || []).forEach(item => {
                        totalInventoryQty += item.quantity || 0;
                    });
                    if (s.agent && s.agent !== 'Unassigned') totalAgents++;
                    totalLoans += (s.total_loans_count || 0);
                });
            }
        }
    }

    const setText = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setText('stat-total-shops', totalShops);
    setText('stat-total-provinces', totalProvinces);
    setText('stat-total-districts', totalDistricts);
    setText('stat-total-villages', totalVillages);
    setText('stat-total-inventory', totalInventoryItems);
    setText('stat-total-inventory-qty', totalInventoryQty.toLocaleString());
    setText('stat-total-agents', totalAgents);
    setText('stat-total-loans', totalLoans);

    if (currentHqWarehouse) {
        const fertilizers = currentHqWarehouse.fertilizers || [];
        const assets = currentHqWarehouse.assets || [];
        const cashPool = currentHqWarehouse.cash_pool || {};
        const distribution = currentHqWarehouse.distribution_history || [];

        const totalFert = fertilizers.reduce((sum, f) => sum + (f.quantity || 0), 0);
        const totalAssets = assets.reduce((sum, a) => sum + (a.quantity || 0), 0);
        const availableCash = cashPool.available_for_disbursement || 0;

        const fertEl = document.getElementById('hq-stat-fert-total');
        if (fertEl) fertEl.textContent = totalFert.toLocaleString();

        const assetEl = document.getElementById('hq-stat-asset-total');
        if (assetEl) assetEl.textContent = totalAssets;

        const cashEl = document.getElementById('hq-stat-cash-total');
        if (cashEl) cashEl.textContent = 'ZMW ' + Number(availableCash).toLocaleString();

        const distEl = document.getElementById('hq-stat-distributed');
        if (distEl) distEl.textContent = distribution.length;
    }
}

// Render Farmers Table
function renderFarmersTable(farmers) {
    const tbody = document.getElementById('farmers-table-body');
    tbody.innerHTML = '';

    if (farmers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 20px;">No registered farmers found.</td></tr>`;
        return;
    }

    farmers.forEach(f => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><code>${f.id}</code></td>
            <td><strong>${f.name}</strong></td>
            <td>${f.phone}<br><small style="color: var(--text-dim);">${f.nrc}</small></td>
            <td><span class="badge badge-primary">${f.shop}</span></td>
            <td>${f.village}</td>
            <td>${f.district}</td>
            <td>${f.registered_at || 'N/A'}</td>
            <td>
                <button class="btn btn-sm btn-emerald" onclick="quickIssueForFarmer('${f.name}')">
                    <i class="fa-solid fa-plus"></i> Issue Loan
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterFarmersTable() {
    const q = document.getElementById('farmer-search-input').value.toLowerCase();
    const filtered = farmersData.filter(f => f.name.toLowerCase().includes(q) || f.phone.includes(q) || f.id.toLowerCase().includes(q));
    renderFarmersTable(filtered);
}

// Render Loan Tables
function renderLoanTables(loans) {
    const fertTbody = document.getElementById('fert-loans-table-body');
    const assetTbody = document.getElementById('asset-loans-table-body');
    const cashTbody = document.getElementById('cash-loans-table-body');

    fertTbody.innerHTML = '';
    assetTbody.innerHTML = '';
    cashTbody.innerHTML = '';

    const fertLoans = loans.filter(l => l.loan_type === 'fertilizer');
    const assetLoans = loans.filter(l => l.loan_type === 'asset_finance');
    const cashLoans = loans.filter(l => l.loan_type === 'cash');

    // 1. Fertilizer Table
    if (fertLoans.length === 0) {
        fertTbody.innerHTML = `<tr><td colspan="12" style="text-align: center; color: var(--text-dim); padding: 20px;">No fertilizer loans found.</td></tr>`;
    } else {
        fertLoans.forEach(l => {
            const isDone = l.status === 'completed';
            const compoundDBags = l.compound_d_bags || 0;
            const ureaBags = l.urea_bags || 0;
            const totalBags = l.fertilizer_bags || (compoundDBags + ureaBags);
            fertTbody.innerHTML += `
                <tr>
                    <td><code>${l.id}</code></td>
                    <td><button class="btn btn-sm btn-primary" onclick="openLoanDetail('${l.id}')"><i class="fa-solid fa-eye"></i> Open</button></td>
                    <td><strong>${l.name}</strong><br><small style="color: var(--text-dim);">${l.shop}</small></td>
                    <td>${l.fertilizer_type}</td>
                    <td><strong>${compoundDBags}</strong></td>
                    <td><strong>${ureaBags}</strong></td>
                    <td><strong>${totalBags}</strong></td>
                    <td>ZMW ${l.downpayment_cash}</td>
                    <td>${l.repayment_ratio}</td>
                    <td>${l.expected_maize_bags} Bags</td>
                    <td><strong style="color: ${isDone ? 'var(--emerald)' : 'var(--amber)'};">${l.balance_remaining} Bags</strong></td>
                    <td><span class="badge ${isDone ? 'badge-completed' : 'badge-active'}">${l.status}</span></td>
                    <td>
                        ${!isDone ? `<button class="btn btn-sm btn-emerald" onclick="openRepaymentModal('${l.id}', 'fertilizer', '${l.name}', '${l.balance_remaining} Bags')"><i class="fa-solid fa-wheat-awn"></i> Repay Maize</button>` : '<span style="color: var(--emerald); font-weight:600;"><i class="fa-solid fa-check-double"></i> Settled</span>'}
                        <br>
                        <button class="btn btn-sm btn-primary" onclick="openScheduleModal('${l.id}')" style="margin-top: 4px;"><i class="fa-solid fa-calendar-days"></i> Schedule</button>
                        ${(l.loan_type === 'cash' || l.restructuring_allowed) ? `<br><button class="btn btn-sm btn-rose" onclick="openRestructureModal('${l.id}')" style="margin-top: 4px;"><i class="fa-solid fa-arrows-rotate"></i> Restructure</button>` : ''}
                    </td>
                </tr>
            `;
        });
    }

    // 2. Asset Finance Table
    if (assetLoans.length === 0) {
        assetTbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-dim); padding: 20px;">No asset finance loans found.</td></tr>`;
    } else {
        assetLoans.forEach(l => {
            const isDone = l.status === 'completed';
            assetTbody.innerHTML += `
                <tr>
                    <td><code>${l.id}</code></td>
                    <td><button class="btn btn-sm btn-primary" onclick="openLoanDetail('${l.id}')"><i class="fa-solid fa-eye"></i> Open</button></td>
                    <td><strong>${l.name}</strong><br><small style="color: var(--text-dim);">${l.shop}</small></td>
                    <td>${l.asset_type}</td>
                    <td>ZMW ${l.asset_value.toLocaleString()}</td>
                    <td>ZMW ${l.downpayment_cash.toLocaleString()} (${l.downpayment_percent}%)</td>
                    <td>${l.interest_rate}%</td>
                    <td>ZMW ${l.total_repayable.toLocaleString()}</td>
                    <td><strong style="color: ${isDone ? 'var(--emerald)' : 'var(--amber)'};">ZMW ${l.balance_remaining.toLocaleString()}</strong></td>
                    <td><span class="badge ${isDone ? 'badge-completed' : 'badge-active'}">${l.status}</span></td>
                    <td>
                        ${!isDone ? `<button class="btn btn-sm btn-cyan" onclick="openRepaymentModal('${l.id}', 'asset_finance', '${l.name}', 'ZMW ${l.balance_remaining}')"><i class="fa-solid fa-cash-register"></i> Repay</button>` : '<span style="color: var(--emerald); font-weight:600;"><i class="fa-solid fa-check-double"></i> Settled</span>'}
                        <br>
                        <button class="btn btn-sm btn-primary" onclick="openScheduleModal('${l.id}')" style="margin-top: 4px;"><i class="fa-solid fa-calendar-days"></i> Schedule</button>
                        ${(l.loan_type === 'cash' || l.restructuring_allowed) ? `<br><button class="btn btn-sm btn-rose" onclick="openRestructureModal('${l.id}')" style="margin-top: 4px;"><i class="fa-solid fa-arrows-rotate"></i> Restructure</button>` : ''}
                    </td>
                </tr>
            `;
        });
    }

    // 3. Cash Loans Table
    window.allCashLoans = cashLoans.slice();
    filterCashLoans();
}

function renderCashLoanTable(cashLoans) {
    const cashTbody = document.getElementById('cash-loans-table-body');
    cashTbody.innerHTML = '';
    if (cashLoans.length === 0) {
        cashTbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-dim); padding: 20px;">No cash loans found.</td></tr>`;
    } else {
        cashLoans.forEach(l => {
            const isDone = l.status === 'completed';
            cashTbody.innerHTML += `
                <tr>
                    <td><code>${l.id}</code></td>
                    <td><button class="btn btn-sm btn-primary" onclick="openLoanDetail('${l.id}')"><i class="fa-solid fa-eye"></i> Open</button></td>
                    <td><strong>${l.name}</strong><br><small style="color: var(--text-dim);">${l.shop}</small></td>
                    <td>ZMW ${l.loan_amount.toLocaleString()}</td>
                    <td>${l.interest_rate}%</td>
                    <td>ZMW ${l.total_repayable.toLocaleString()}</td>
                    <td><strong style="color: ${isDone ? 'var(--emerald)' : 'var(--amber)'};">ZMW ${l.balance_remaining.toLocaleString()}</strong></td>
                    <td>${l.due_date || 'N/A'}</td>
                    <td><span class="badge ${isDone ? 'badge-completed' : 'badge-active'}">${l.status}</span></td>
                    <td>
                        ${!isDone ? `<button class="btn btn-sm btn-amber" onclick="openRepaymentModal('${l.id}', 'cash', '${l.name}', 'ZMW ${l.balance_remaining}')"><i class="fa-solid fa-money-bill-wave"></i> Repay</button>` : '<span style="color: var(--emerald); font-weight:600;"><i class="fa-solid fa-check-double"></i> Settled</span>'}
                        <br>
                        <button class="btn btn-sm btn-primary" onclick="openScheduleModal('${l.id}')" style="margin-top: 4px;"><i class="fa-solid fa-calendar-days"></i> Schedule</button>
                        ${(l.loan_type === 'cash' || l.restructuring_allowed) ? `<br><button class="btn btn-sm btn-rose" onclick="openRestructureModal('${l.id}')" style="margin-top: 4px;"><i class="fa-solid fa-arrows-rotate"></i> Restructure</button>` : ''}
                    </td>
                </tr>
            `;
        });
    }
}

// Populate Farmer Select Elements in Modals
function populateFarmerSelects(farmers) {
    const selects = ['fert-farmer-select', 'asset-farmer-select', 'cash-farmer-select'];
    selects.forEach(id => {
        const elem = document.getElementById(id);
        if (!elem) return;
        elem.innerHTML = '';

        if (farmers.length === 0) {
            elem.innerHTML = '<option value="">-- No Farmers Registered Yet --</option>';
            return;
        }

        farmers.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.name;
            opt.textContent = `${f.name} (${f.shop} - ${f.village})`;
            elem.appendChild(opt);
        });
    });
}

// Action Handlers: Register Farmer
async function handleRegisterFarmer(e) {
    e.preventDefault();
    if (userMeta.role !== 'Agent') {
        showToast('Only Agents can register farmers!', 'error');
        return;
    }

    const payload = {
        client_name: document.getElementById('form-farmer-name').value,
        phone: document.getElementById('form-farmer-phone').value,
        nrc: document.getElementById('form-farmer-nrc').value,
        province: document.getElementById('form-farmer-province').value,
        district: document.getElementById('form-farmer-district').value,
        village: document.getElementById('form-farmer-village').value,
        shop: document.getElementById('form-farmer-shop').value
    };

    try {
        const res = await fetch('/add_client', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to add client', 'error');
            return;
        }

        showToast(data.message);
        closeModal('add-client-modal');
        document.getElementById('add-farmer-form').reset();
        await loadDashboardData();
    } catch (err) {
        console.error(err);
        showToast('Server error registering farmer', 'error');
    }
}

// Action Handlers: Issue Fertilizer Loan
async function handleIssueFertilizerLoan(e) {
    e.preventDefault();
    const fertilizerType = document.getElementById('fert-type-select').value;
    const compoundDBags = parseInt(document.getElementById('fert-compound-d-bags').value) || 0;
    const ureaBags = parseInt(document.getElementById('fert-urea-bags').value) || 0;
    const totalBags = compoundDBags + ureaBags;
    
    if (totalBags <= 0) {
        showToast('Please enter at least one fertilizer bag quantity', 'error');
        return;
    }
    
    const payload = {
        client_name: document.getElementById('fert-farmer-select').value,
        fertilizer_type: fertilizerType,
        compound_d_bags: compoundDBags,
        urea_bags: ureaBags,
        fertilizer_bags: totalBags,
        repayment_ratio: document.getElementById('fert-ratio-input').value,
        downpayment_cash: parseInt(document.getElementById('fert-downpayment-input').value)
    };

    try {
        const res = await fetch('/fertilizer_loans/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to issue fertilizer loan', 'error');
            return;
        }

        showToast(data.message);
        closeModal('issue-fert-modal');
        await loadDashboardData();
    } catch (err) {
        showToast('Error issuing fertilizer loan', 'error');
    }
}

// Action Handlers: Issue Asset Loan
async function handleIssueAssetLoan(e) {
    e.preventDefault();
    const payload = {
        client_name: document.getElementById('asset-farmer-select').value,
        asset_type: document.getElementById('asset-type-input').value,
        asset_value: parseFloat(document.getElementById('asset-value-input').value),
        downpayment_percent: parseFloat(document.getElementById('asset-downpayment-percent').value),
        interest_rate: parseFloat(document.getElementById('asset-interest-rate').value)
    };

    try {
        const res = await fetch('/asset_finance_loans/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to issue asset loan', 'error');
            return;
        }

        showToast(data.message);
        closeModal('issue-asset-modal');
        await loadDashboardData();
    } catch (err) {
        showToast('Error issuing asset loan', 'error');
    }
}

// Action Handlers: Issue Cash Loan
async function handleIssueCashLoan(e) {
    e.preventDefault();
    const payload = {
        client_name: document.getElementById('cash-farmer-select').value,
        loan_amount: parseFloat(document.getElementById('cash-amount-input').value),
        interest_rate: parseFloat(document.getElementById('cash-interest-input').value),
        purpose: document.getElementById('cash-purpose-input').value
    };

    try {
        const res = await fetch('/cash_loans/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to issue cash loan', 'error');
            return;
        }

        showToast(data.message);
        closeModal('issue-cash-modal');
        await loadDashboardData();
    } catch (err) {
        showToast('Error issuing cash loan', 'error');
    }
}

// Repayment Modal & Execution
function openRepaymentModal(loanId, category, farmerName, balanceDesc) {
    document.getElementById('repay-loan-id').value = loanId;
    document.getElementById('repay-loan-category').value = category;

    document.getElementById('repay-meta-id').textContent = loanId;
    document.getElementById('repay-meta-farmer').textContent = farmerName;
    document.getElementById('repay-meta-balance').textContent = balanceDesc;

    const label = document.getElementById('repay-amount-label');
    label.textContent = category === 'fertilizer' ? 'Repayment Quantity (Maize Bags) *' : 'Repayment Amount (ZMW Cash) *';

    const loanObj = loansData.find(l => l.id === loanId);
    const historyList = document.getElementById('repay-history-list');
    historyList.innerHTML = '';

    const history = loanObj ? (loanObj.repayment_history || (loanObj.installments ? loanObj.installments.repayment_history : [])) : [];
    if (!history || history.length === 0) {
        historyList.innerHTML = '<div style="color: var(--text-dim); text-align:center; padding: 4px;">No prior payments recorded.</div>';
    } else {
        history.forEach(h => {
            const amtStr = h.bags !== null && h.bags !== undefined ? `${h.bags} Maize Bags` : `ZMW ${h.amount}`;
            historyList.innerHTML += `
                <div class="history-item">
                    <span>${h.date} - ${h.notes || 'Repayment'}</span>
                    <strong>${amtStr}</strong>
                </div>
            `;
        });
    }

    document.getElementById('repay-allocation-preview').style.display = 'none';
    document.getElementById('repayment-action').textContent = 'Record Repayment';
    openModal('repayment-modal');
}

function showRepaymentPreview(loanId, amount) {
    if (!amount || amount <= 0) {
        document.getElementById('repay-allocation-preview').style.display = 'none';
        return;
    }
    fetch(`/loans/${loanId}/schedule`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
    })
    .then(res => res.json())
    .then(data => {
        const loan = loansData.find(l => l.id === loanId) || {};
        const penalties = loan.penalties || [];
        let remaining = amount;
        let fees = 0, penalty = 0, interest = 0, principal = 0;
        
        if (data.schedule) {
            for (const row of data.schedule) {
                if (remaining <= 0) break;
                if (row.status === 'due') {
                    if (row.due_fees > 0) { const take = Math.min(remaining, row.due_fees); fees += take; remaining -= take; }
                    if (remaining > 0 && row.due_interest > 0) { const take = Math.min(remaining, row.due_interest); interest += take; remaining -= take; }
                    if (remaining > 0 && row.due_principal > 0) { const take = Math.min(remaining, row.due_principal); principal += take; remaining -= take; }
                }
            }
            for (const p of penalties) {
                if (remaining <= 0) break;
                const take = Math.min(remaining, p.amount || 0);
                penalty += take;
                remaining -= take;
            }
            if (remaining > 0) principal += remaining;
        }
        
        document.getElementById('alloc-preview-fees').textContent = 'ZMW ' + fees.toFixed(2);
        document.getElementById('alloc-preview-penalty').textContent = 'ZMW ' + penalty.toFixed(2);
        document.getElementById('alloc-preview-interest').textContent = 'ZMW ' + interest.toFixed(2);
        document.getElementById('alloc-preview-principal').textContent = 'ZMW ' + principal.toFixed(2);
        document.getElementById('repay-allocation-preview').style.display = 'block';
    })
    .catch(err => console.error('Error previewing allocation:', err));
}

async function handleRecordRepayment(e) {
    e.preventDefault();
    const loanId = document.getElementById('repay-loan-id').value;
    const amount = parseFloat(document.getElementById('repay-amount-input').value);
    const notes = document.getElementById('repay-notes-input').value;

    try {
        const res = await fetch('/loans/repay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ loan_id: loanId, amount, notes })
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to record repayment', 'error');
            return;
        }

        let msg = data.message;
        if (data.allocation) {
            const a = data.allocation;
            msg += ` | Allocated: Fees ZMW ${a.fees}, Penalty ZMW ${a.penalty}, Interest ZMW ${a.interest}, Principal ZMW ${a.principal}`;
        }
        showToast(msg);
        closeModal('repayment-modal');
        document.getElementById('repayment-form').reset();
        await loadDashboardData();
    } catch (err) {
        showToast('Error recording repayment', 'error');
    }
}

// Interactive Real-Time Calculators
function calcFertilizerSummary() {
    const compoundDBags = parseInt(document.getElementById('fert-compound-d-bags').value) || 0;
    const ureaBags = parseInt(document.getElementById('fert-urea-bags').value) || 0;
    const totalBags = compoundDBags + ureaBags;
    const ratioStr = document.getElementById('fert-ratio-input').value || '1:4';
    const ratioVal = parseInt(ratioStr.split(':')[1]) || 4;

    const expectedBags = totalBags * ratioVal;
    const downpayment = totalBags * 450;

    document.getElementById('fert-downpayment-input').value = downpayment;
    document.getElementById('fert-calc-summary').textContent = `Expected Maize: ${expectedBags} Bags | Downpayment: ZMW ${downpayment.toLocaleString()}`;
}

function updateFertilizerInputs() {
    const type = document.getElementById('fert-type-select').value;
    const compoundDGroup = document.getElementById('fert-compound-d-group');
    const compoundDInput = document.getElementById('fert-compound-d-bags');
    const ureaInput = document.getElementById('fert-urea-bags');
    
    if (type === 'Compound D') {
        compoundDGroup.style.display = 'none';
        compoundDInput.value = 0;
        ureaInput.value = 0;
        ureaInput.closest('.form-group').querySelector('label').textContent = 'Compound D Bags *';
        ureaInput.id = 'fert-main-bags';
    } else if (type === 'Urea') {
        compoundDGroup.style.display = 'none';
        compoundDInput.value = 0;
        ureaInput.value = 0;
        compoundDInput.closest('.form-group').querySelector('label').textContent = 'Urea Bags *';
        compoundDInput.id = 'fert-main-bags';
    } else {
        compoundDGroup.style.display = 'flex';
        compoundDInput.closest('.form-group').querySelector('label').textContent = 'Compound D Bags *';
        ureaInput.closest('.form-group').querySelector('label').textContent = 'Urea Bags *';
        compoundDInput.id = 'fert-compound-d-bags';
        ureaInput.id = 'fert-urea-bags';
    }
    
    calcFertilizerSummary();
}

function calcAssetSummary() {
    const val = parseFloat(document.getElementById('asset-value-input').value) || 0;
    const pct = parseFloat(document.getElementById('asset-downpayment-percent').value) || 0;
    const rate = parseFloat(document.getElementById('asset-interest-rate').value) || 0;

    const downpayment = val * pct / 100.0;
    const loanNet = val - downpayment;
    const totalRepayable = loanNet * (1 + rate / 100.0);

    document.getElementById('asset-calc-summary').textContent = 
        `Downpayment: ZMW ${downpayment.toLocaleString()} | Loan Net: ZMW ${loanNet.toLocaleString()} | Total Repayable: ZMW ${totalRepayable.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
}

function calcCashSummary() {
    const amt = parseFloat(document.getElementById('cash-amount-input').value) || 0;
    const rate = parseFloat(document.getElementById('cash-interest-input').value) || 0;

    const totalRepayable = amt * (1 + rate / 100.0);
    document.getElementById('cash-calc-summary').textContent = `ZMW ${totalRepayable.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
}

async function populateUnifiedLoanForm() {
    const farmerSelect = document.getElementById('unified-farmer-select');
    if (!farmerSelect) return;
    farmerSelect.innerHTML = '<option value="">Select Farmer</option>';
    (farmersData || []).forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = `${f.id} - ${f.name} (${f.shop})`;
        farmerSelect.appendChild(opt);
    });

    const productSelect = document.getElementById('unified-product-select');
    if (!productSelect) return;
    productSelect.innerHTML = '<option value="">Select Loan Product</option>';

    try {
        const res = await fetch('/loan_products', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (res.ok) {
            const data = await res.json();
            window.loanProducts = data.loan_products || [];
            (window.loanProducts || []).forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = `${p.name} (${p.type})`;
                opt.dataset.interest_type = p.interest_type || 'Flat Rate';
                opt.dataset.interest_rate = p.interest_rate || 0;
                opt.dataset.repayment_frequency = p.repayment_frequency || 'Monthly';
                opt.dataset.default_installments = p.default_installments || 6;
                opt.dataset.grace_period_days = p.grace_period_days || 0;
                opt.dataset.repayment_method = p.repayment_method || 'Cash only';
                opt.dataset.disbursement_method = p.disbursement_method || 'Cash at shop';
                opt.dataset.late_penalty_type = p.late_penalty_type || 'percentage';
                opt.dataset.late_penalty_value = p.late_penalty_value || 0;
                opt.dataset.default_handling = p.default_handling || '';
                opt.dataset.restructuring_allowed = p.restructuring_allowed ? 'true' : 'false';
                opt.dataset.approval_level = p.approval_level || 'Shop';
                productSelect.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('Error loading loan products:', err);
    }

    const shopDatalist = document.getElementById('unified-shop-list');
    if (shopDatalist) {
        shopDatalist.innerHTML = '';
        const shopList = [];
        for (const [prov, dists] of Object.entries(shopsData || {})) {
            for (const [dist, vills] of Object.entries(dists)) {
                for (const [vill, shopDict] of Object.entries(vills)) {
                    for (const shopName of Object.keys(shopDict)) {
                        const shopData = shopDict[shopName] || {};
                        shopList.push({name: shopName, id: shopData.shop_id || ''});
                    }
                }
            }
        }
        shopList.forEach(shop => {
            const opt = document.createElement('option');
            opt.value = `${shop.id} -- ${shop.name}`;
            shopDatalist.appendChild(opt);
        });
    }
}

function onUnifiedProductChange() {
    const select = document.getElementById('unified-product-select');
    if (!select || !select.value) return;
    const opt = select.selectedOptions[0];
    document.getElementById('unified-interest-rate').value = opt.dataset.interest_rate || 10;
    document.getElementById('unified-frequency').value = opt.dataset.repayment_frequency || 'Monthly';
    document.getElementById('unified-installments').value = opt.dataset.default_installments || 6;
    document.getElementById('unified-grace-period').value = opt.dataset.grace_period_days || 0;
    document.getElementById('unified-repayment-method').value = opt.dataset.repayment_method || 'Cash only';
    document.getElementById('unified-disbursement-method').value = opt.dataset.disbursement_method || 'Cash at shop';
    document.getElementById('unified-penalty-type').value = opt.dataset.late_penalty_type || 'percentage';
    document.getElementById('unified-penalty-value').value = opt.dataset.late_penalty_value || 0;
    document.getElementById('unified-default-handling').value = opt.dataset.default_handling || 'Mark defaulted after 3 missed installments';
    document.getElementById('unified-restructuring').value = opt.dataset.restructuring_allowed || 'false';
    document.getElementById('unified-approval-level').value = opt.dataset.approval_level || 'Shop';
    document.getElementById('unified-loan-tenure').value = opt.dataset.default_tenure || `${opt.dataset.default_installments || 6} ${opt.dataset.repayment_frequency || 'Months'}s`;
    calcUnifiedLoan();
}

function calcUnifiedLoan() {
    const amt = parseFloat(document.getElementById('unified-loan-amount').value) || 0;
    const rate = parseFloat(document.getElementById('unified-interest-rate').value) || 0;
    const installments = parseInt(document.getElementById('unified-installments').value) || 1;
    const frequency = document.getElementById('unified-frequency').value;
    const interestType = 'Flat Rate';

    let totalRepayable = amt;
    if (interestType === 'Flat Rate') {
        totalRepayable = amt * (1 + rate / 100.0);
    } else if (interestType === 'Reducing Balance') {
        const monthlyRate = rate / 100.0 / 12.0;
        if (monthlyRate > 0) {
            totalRepayable = amt * (monthlyRate * Math.pow(1 + monthlyRate, installments)) / (Math.pow(1 + monthlyRate, installments) - 1) * installments;
        }
    } else if (interestType === 'Service Fee') {
        totalRepayable = amt + rate;
    }

    totalRepayable = round(totalRepayable, 2);
    const installmentAmt = installments > 0 ? round(totalRepayable / installments, 2) : totalRepayable;

    const tenureText = `${installments} ${frequency}${installments > 1 ? 's' : ''}`;
    document.getElementById('unified-installment-amount').value = installmentAmt.toLocaleString(undefined, {minimumFractionDigits: 2});
    document.getElementById('unified-loan-tenure').value = tenureText;
    document.getElementById('unified-calc-summary').textContent = `Loan Tenure: ${tenureText} | Total Repayable: ZMW ${totalRepayable.toLocaleString(undefined, {minimumFractionDigits: 2})} | Installments: ${installments}`;
}

function round(value, decimals) {
    return Number(Math.round(value + 'e' + decimals) + 'e-' + decimals);
}

async function handleCreateUnifiedLoan(e) {
    e.preventDefault();
    const payload = {
        farmer_id: document.getElementById('unified-farmer-select').value,
        shop_id: document.getElementById('unified-shop-id-input').value.includes(' -- ') ? '' : document.getElementById('unified-shop-id-input').value,
        shop_name: document.getElementById('unified-shop-id-input').value.includes(' -- ') ? document.getElementById('unified-shop-id-input').value.split(' -- ').slice(1).join(' -- ') : document.getElementById('unified-shop-id-input').value,
        loan_product_id: document.getElementById('unified-product-select').value,
        loan_amount: parseFloat(document.getElementById('unified-loan-amount').value),
        interest_type: 'Flat Rate',
        interest_rate: parseFloat(document.getElementById('unified-interest-rate').value),
        repayment_frequency: document.getElementById('unified-frequency').value,
        total_installments: parseInt(document.getElementById('unified-installments').value),
        grace_period_days: parseInt(document.getElementById('unified-grace-period').value),
        repayment_method: document.getElementById('unified-repayment-method').value,
        disbursement_method: document.getElementById('unified-disbursement-method').value,
        late_penalty_type: document.getElementById('unified-penalty-type').value,
        late_penalty_value: parseFloat(document.getElementById('unified-penalty-value').value),
        default_handling: document.getElementById('unified-default-handling').value,
        restructuring_allowed: document.getElementById('unified-restructuring').value === 'true',
        approval_level: document.getElementById('unified-approval-level').value,
        loan_tenure: document.getElementById('unified-loan-tenure').value,
        purpose: document.getElementById('unified-purpose').value
    };

    try {
        const res = await fetch('/loans/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to create loan', 'error');
            return;
        }

        showToast(data.message);
        closeModal('issue-unified-modal');
        document.getElementById('issue-unified-form').reset();
        await loadDashboardData();
    } catch (err) {
        showToast('Error creating loan', 'error');
    }
}

function quickIssueForFarmer(name) {
    openModal('issue-loan-modal');
}

async function loadRepayments() {
    try {
        const res = await fetch('/api/repayments', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        const tbody = document.getElementById('repayment-table-body');
        if (!tbody) return;
        const repayments = data.repayments || [];
        if (repayments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 20px;">No repayments found.</td></tr>';
            return;
        }
        tbody.innerHTML = '';
        repayments.forEach(r => {
            const alloc = r.allocation || {};
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><code>${r.loan_id}-${r.date}</code></td>
                <td>${r.loan_id}</td>
                <td><strong>${r.borrower}</strong></td>
                <td>ZMW ${Number(r.amount).toLocaleString()}</td>
                <td>${r.notes || 'Cash'}</td>
                <td>${Object.keys(alloc).length > 0 ? JSON.stringify(alloc) : '-'}</td>
                <td>${r.date}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Error loading repayments:', err);
    }
}

async function loadProducts() {
    try {
        const res = await fetch('/api/products', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        const tbody = document.getElementById('products-table-body');
        if (!tbody) return;
        const products = data.products || [];
        if (products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 20px;">No products found.</td></tr>';
            return;
        }
        tbody.innerHTML = '';
        products.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><code>${p.id}</code></td>
                <td><strong>${p.name}</strong></td>
                <td><span class="badge badge-primary">${p.type}</span></td>
                <td>ZMW ${Number(p.min_amount).toLocaleString()}</td>
                <td>ZMW ${Number(p.max_amount).toLocaleString()}</td>
                <td>${p.interest_rate}%</td>
                <td>${p.interest_type}</td>
                <td>${p.repayment_frequency}</td>
                <td><span class="badge badge-active">Active</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Error loading products:', err);
    }
}

async function loadReporting() {
    try {
        const res = await fetch('/reports/portfolio', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        const kpiGrid = document.getElementById('reporting-kpi-grid');
        const tbody = document.getElementById('reporting-table-body');
        if (kpiGrid) {
            kpiGrid.innerHTML = `
                <div class="section-card glass" style="padding: 16px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: var(--emerald);">${data.total_loans || 0}</div>
                    <div style="color: var(--text-dim); margin-top: 4px;">Total Loans</div>
                </div>
                <div class="section-card glass" style="padding: 16px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: var(--emerald);">ZMW ${Number(data.total_principal || 0).toLocaleString()}</div>
                    <div style="color: var(--text-dim); margin-top: 4px;">Total Principal</div>
                </div>
                <div class="section-card glass" style="padding: 16px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: var(--amber);">ZMW ${Number(data.total_outstanding || 0).toLocaleString()}</div>
                    <div style="color: var(--text-dim); margin-top: 4px;">Outstanding Balance</div>
                </div>
                <div class="section-card glass" style="padding: 16px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: var(--rose);">${data.par30 || 0}</div>
                    <div style="color: var(--text-dim); margin-top: 4px;">PAR 30+ Days</div>
                </div>
            `;
        }
        if (tbody) {
            tbody.innerHTML = '';
            const metrics = [
                { metric: 'Total Loans', value: data.total_loans || 0, trend: '' },
                { metric: 'Total Principal Disbursed', value: 'ZMW ' + Number(data.total_principal || 0).toLocaleString(), trend: '' },
                { metric: 'Total Outstanding', value: 'ZMW ' + Number(data.total_outstanding || 0).toLocaleString(), trend: '' },
                { metric: 'PAR > 30 Days', value: data.par30 || 0, trend: '' },
                { metric: 'Overdue Loans', value: data.overdue_count || 0, trend: '' },
                { metric: 'Recovery Rate', value: (data.recovery_rate || 0) + '%', trend: '' }
            ];
            metrics.forEach(m => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td><strong>${m.metric}</strong></td><td>${m.value}</td><td>${m.trend}</td>`;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error('Error loading reporting:', err);
    }
}

// UI Modals & Tabs Switcher
function switchTab(tabId, elem) {
    document.querySelectorAll('.tab-view').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    elem.classList.add('active');

    const titleElem = document.getElementById('page-title');
    if (tabId === 'dashboard-home-tab') {
        titleElem.textContent = 'Dashboard';
        if (userMeta.role === 'HQ') renderHqDashboardStats();
    }
    else if (tabId === 'hq-shops-tab') titleElem.textContent = 'Shops Directory & Hierarchy Management';
    else if (tabId === 'hq-inventory-tab') {
        titleElem.textContent = 'Inventory Management';
        if (userMeta.role === 'HQ') {
            loadHqInventory();
            loadHqInventoryTransactions();
            loadHqInventoryAlerts();
        }
    }
    else if (tabId === 'farmers-tab') titleElem.textContent = 'Registered Farmers Directory';
    else if (tabId === 'fertilizer-tab') titleElem.textContent = 'Fertilizer Loans (Maize Repayment)';
    else if (tabId === 'asset-tab') titleElem.textContent = 'Asset Finance Loan Portfolio';
    else if (tabId === 'cash-tab') titleElem.textContent = 'Direct Working Capital Cash Loans';
    else if (tabId === 'applications-tab') {
        titleElem.textContent = 'Loan Applications';
        loadApplications();
    }
    else if (tabId === 'hq-disbursement-tab') {
        titleElem.textContent = 'Disbursement';
        loadDisbursements();
    }
    else if (tabId === 'hq-repayments-tab') {
        titleElem.textContent = 'Repayments & Reconciliation';
        loadRepayments();
    }
    else if (tabId === 'hq-products-tab') {
        titleElem.textContent = 'Products & Pricing';
        loadProducts();
    }
    else if (tabId === 'hq-reporting-tab') {
        titleElem.textContent = 'Reporting & Analytics';
        loadReporting();
    }
    else if (tabId === 'hq-admin-tab') {
        titleElem.textContent = 'Settings & Admin';
        loadSettingsPage();
    }
}

async function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
    if (modalId === 'add-shop-modal') {
        setupAddShopGeoDropdowns();
    }
    if (modalId === 'add-agent-modal') {
        const provSel = document.getElementById('new-agent-province-input');
        if (provSel) {
            provSel.onchange = function() {
                const distSel = document.getElementById('new-agent-district-input');
                distSel.innerHTML = '<option value="">Select District</option>';
                const districts = zambiaDistrictsByProvince[this.value] || [];
                districts.forEach(d => {
                    distSel.innerHTML += `<option value="${d}">${d}</option>`;
                });
            };
        }
    }
    if (modalId === 'add-hq-stock-modal') {
        populateHqStockItemSelect();
    }
    if (modalId === 'stock-management-modal') {
        await loadHqWarehouse();
        loadHqWarehouseItems();
        populateShopSearch();
    }
    if (modalId === 'issue-unified-modal') {
        populateUnifiedLoanForm();
    }
    if (modalId === 'adjust-inventory-modal') {
        openInventoryAdjustModal();
    }
}

function partialPayment() {
    const amountInput = document.getElementById('repay-amount-input');
    const currentBalance = parseFloat(document.getElementById('repay-meta-balance').textContent.replace(/[^0-9.]/g, ''));
    if (amountInput && currentBalance > 0) {
        amountInput.value = (currentBalance / 2).toFixed(2);
        showRepaymentPreview(document.getElementById('repay-loan-id').value, currentBalance / 2);
    }
}

async function reverseTransaction() {
    if (!confirm('Reverse the last repayment? This action cannot be undone.')) return;
    showToast('Transaction reversed', 'success');
    closeModal('repayment-modal');
    await loadDashboardData();
}

function printReceipt() {
    showToast('Printing receipt...', 'success');
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'n' || e.key === 'N') {
        if (document.querySelector('.modal.active') || document.getElementById('application-modal').classList.contains('active')) return;
        if (userMeta.role === 'HQ' || userMeta.role === 'District') {
            openApplicationModal();
        }
    }
});

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function openIssueModal(category) {
    if (userMeta.role !== 'Agent') {
        showToast('Only Agents can issue new loans', 'error');
        return;
    }
    if (category === 'fertilizer') {
        document.getElementById('fert-type-select').value = 'NPK + Urea Compound';
        document.getElementById('fert-compound-d-bags').value = 0;
        document.getElementById('fert-urea-bags').value = 0;
        document.getElementById('fert-ratio-input').value = '1:4';
        updateFertilizerInputs();
        openModal('issue-fert-modal');
    } else if (category === 'asset_finance') {
        calcAssetSummary();
        openModal('issue-asset-modal');
    } else if (category === 'cash') {
        calcCashSummary();
        openModal('issue-cash-modal');
    }
}

// Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'error') toast.style.borderColor = 'var(--rose)';

    const icon = type === 'error' ? 'fa-triangle-exclamation' : 'fa-circle-check';
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}



// Settings & Admin Page Functions
async function loadSettingsPage() {
    if (userMeta.role !== 'HQ') return;
    await Promise.all([loadUsers(), loadRoles(), loadHqSettings()]);
}

function loadRoles() {
    const tbody = document.getElementById('settings-roles-table-body');
    if (!tbody) return;
    const roles = [
        { name: 'HQ', approvalLimit: 'Unlimited', branchAccess: 'All Branches', hqAccess: 'Full' },
        { name: 'District', approvalLimit: '500,000', branchAccess: 'District Only', hqAccess: 'View Only' },
        { name: 'Village', approvalLimit: '50,000', branchAccess: 'Village Only', hqAccess: 'No Access' },
        { name: 'Agent', approvalLimit: '10,000', branchAccess: 'Assigned Shop', hqAccess: 'No Access' }
    ];
    tbody.innerHTML = roles.map(r => `
        <tr>
            <td><span class="badge badge-${r.name === 'HQ' ? 'primary' : r.name === 'District' ? 'amber' : r.name === 'Village' ? 'green' : 'dim'}">${r.name}</span></td>
            <td>${r.approvalLimit}</td>
            <td>${r.branchAccess}</td>
            <td>${r.hqAccess}</td>
            <td>${r.name !== 'HQ' ? '<button class="btn btn-sm btn-secondary" onclick="showToast(\'Role editing coming soon\', \'info\')"><i class="fa-solid fa-pen"></i></button>' : '<span style="color: var(--text-dim);">--</span>'}</td>
        </tr>
    `).join('');
}

async function loadUsers() {
    const tbody = document.getElementById('settings-users-table-body');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 20px;">Loading users...</td></tr>';

    try {
        const res = await fetch('/api/users', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 20px;">Failed to load users.</td></tr>';
            return;
        }
        const data = await res.json();
        const users = data.users || [];
        tbody.innerHTML = '';

        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 20px;">No users found.</td></tr>';
            return;
        }

        users.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${u.username}</strong></td>
                <td><span class="badge ${u.role === 'HQ' ? 'badge-active' : (u.role === 'Agent' ? 'badge-primary' : 'badge-warning')}">${u.role || 'N/A'}</span></td>
                <td>${u.district || '-'}</td>
                <td>${u.village || '-'}</td>
                <td>${u.shop || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-amber" onclick="setRole('${u.username}')"><i class="fa-solid fa-user-pen"></i> Set Role</button>
                    <button class="btn btn-sm btn-rose" onclick="deleteUser('${u.username}')" style="margin-top: 4px;"><i class="fa-solid fa-trash"></i> Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Error loading users:', err);
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 20px;">Error loading users.</td></tr>';
    }
}

async function createUser() {
    const username = prompt('Enter username:');
    if (!username) return;
    const password = prompt('Enter password:');
    if (!password) return;
    const role = document.getElementById('set-role-select')?.value || 'Agent';
    const district = prompt('Enter district (optional):') || '';
    const village = prompt('Enter village (optional):') || '';
    const shop = prompt('Enter shop (optional):') || '';

    try {
        const res = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ username, password, role, district, village, shop })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to create user', 'error');
            return;
        }
        showToast(data.message || 'User created successfully');
        loadUsers();
    } catch (err) {
        showToast('Error creating user', 'error');
    }
}

async function deleteUser(username) {
    if (!confirm(`Delete user "${username}"? This cannot be undone.`)) return;
    try {
        const res = await fetch(`/api/users/${encodeURIComponent(username)}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to delete user', 'error');
            return;
        }
        showToast(data.message || 'User deleted successfully');
        loadUsers();
    } catch (err) {
        showToast('Error deleting user', 'error');
    }
}

async function setRole(username) {
    const role = prompt(`Set role for ${username} (HQ, District, Village, Agent):`);
    if (!role) return;
    const district = prompt('Enter district (optional):') || '';
    const village = prompt('Enter village (optional):') || '';
    const shop = prompt('Enter shop (optional):') || '';

    try {
        const res = await fetch(`/api/users/${encodeURIComponent(username)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ role, district, village, shop })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to update role', 'error');
            return;
        }
        showToast(data.message || 'Role updated successfully');
        loadUsers();
    } catch (err) {
        showToast('Error updating role', 'error');
    }
}

async function toggleFeatureFlag(flag, enabled) {
    try {
        const res = await fetch('/api/feature-flags', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ [flag]: enabled })
        });

        if (res.ok) {
            showToast(`Feature flag "${flag}" updated`, 'success');
        } else {
            showToast('Failed to update feature flag', 'error');
        }
    } catch (err) {
        console.error('Error updating feature flag:', err);
        showToast('Error updating feature flag', 'error');
    }
}

function filterUsers() {
    const roleFilter = document.getElementById('user-role-filter')?.value || '';
    const rows = document.querySelectorAll('#settings-users-table-body tr');
    
    rows.forEach(row => {
        if (row.cells.length < 2) return;
        const roleCell = row.cells[1];
        const roleText = roleCell?.textContent?.trim() || '';
        
        if (!roleFilter || roleText.includes(roleFilter)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

async function handleAddProduct(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('prod-name').value.trim(),
        type: document.getElementById('prod-type').value,
        min_amount: parseFloat(document.getElementById('prod-min-amount').value),
        max_amount: parseFloat(document.getElementById('prod-max-amount').value),
        interest_rate: parseFloat(document.getElementById('prod-interest-rate').value),
        interest_type: document.getElementById('prod-interest-type').value === 'reducing' ? 'Reducing Balance' : 'Flat Rate',
        repayment_frequency: document.getElementById('prod-frequency').value,
        default_installments: parseInt(document.getElementById('prod-installments').value),
        grace_period_days: parseInt(document.getElementById('prod-grace-period').value) || 0,
        approval_level: document.getElementById('prod-approval-level').value,
        description: document.getElementById('prod-description').value.trim()
    };

    if (payload.min_amount > payload.max_amount) {
        showToast('Min amount cannot exceed max amount', 'error');
        return;
    }

    try {
        const res = await fetch('/api/products', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to create product', 'error');
            return;
        }
        showToast(data.message || 'Product created successfully');
        closeModal('add-product-modal');
        document.getElementById('add-product-form').reset();
        loadProducts();
    } catch (err) {
        showToast('Error creating product', 'error');
    }
}

async function handleNewDisbursement(e) {
    e.preventDefault();
    const loanId = document.getElementById('disb-loan-id').value.trim();
    const amount = parseFloat(document.getElementById('disb-amount').value);
    const method = document.getElementById('disb-method').value;
    const notes = document.getElementById('disb-notes').value.trim();

    if (!loanId || !amount || !method) {
        showToast('Loan ID, amount, and method are required', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/loans/${loanId}/disburse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ amount, method, notes })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Failed to disburse loan', 'error');
            return;
        }
        showToast(data.message || 'Loan disbursed successfully');
        closeModal('new-disbursement-modal');
        document.getElementById('new-disbursement-form').reset();
        loadDisbursements();
    } catch (err) {
        showToast('Error disbursing loan', 'error');
    }
}

async function loadDisbursements() {
    try {
        const res = await fetch('/api/disbursements', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        const tbody = document.getElementById('disbursement-table-body');
        if (!tbody) return;
        const disbursements = data.disbursements || [];
        if (disbursements.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 20px;">No disbursements found.</td></tr>';
            return;
        }
        tbody.innerHTML = '';
        disbursements.forEach(d => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><code>DISB-${d.loan_id}</code></td>
                <td>${d.loan_id}</td>
                <td><strong>${d.borrower}</strong></td>
                <td>ZMW ${Number(d.amount).toLocaleString()}</td>
                <td>${d.method}</td>
                <td>${d.date}</td>
                <td><span class="badge badge-active">${d.status}</span></td>
            `;
            tbody.appendChild(tr);
        });

        const datalist = document.getElementById('disb-loan-id-list');
        if (datalist) {
            datalist.innerHTML = '';
            disbursements.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.loan_id;
                opt.textContent = `${d.loan_id} - ${d.borrower}`;
                datalist.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('Error loading disbursements:', err);
    }
}

