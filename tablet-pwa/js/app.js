const App = {
    currentScreen: 'login',
    selectedNetwork: 'MTN',
    selectedType: 'withdraw',
    pin: '',
    currentTransaction: null,
    transactionTimeout: null,

    init() {
        this.bindEvents();
        this.checkAuth();
        this.setupWebSocketListeners();
    },

    bindEvents() {
        // Login screen
        document.querySelectorAll('#numpad button').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleNumpadInput(e.target.dataset.key, 'pin'));
        });

        document.getElementById('pin-input').addEventListener('input', (e) => {
            this.pin = e.target.value;
            this.updatePinDots();
            document.getElementById('login-btn').disabled = this.pin.length !== 4;
        });

        document.getElementById('login-btn').addEventListener('click', () => this.handleLogin());

        // Shift start
        document.querySelectorAll('#cash-numpad button').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleNumpadInput(e.target.dataset.key, 'cash'));
        });

        document.getElementById('open-shift-btn').addEventListener('click', () => this.openShift());
        document.getElementById('cancel-shift-btn').addEventListener('click', () => this.showScreen('login'));

        // Transaction screen
        document.querySelectorAll('#network-toggle .toggle-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectNetwork(e.target.dataset.network));
        });

        document.querySelectorAll('#type-toggle .toggle-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectType(e.target.dataset.type));
        });

        document.getElementById('amount').addEventListener('input', (e) => this.updateFeeDisplay());
        document.getElementById('process-btn').addEventListener('click', () => this.processTransaction());
        document.getElementById('close-shift-btn').addEventListener('click', () => this.showReconciliation());

        // Status overlay
        document.getElementById('status-close-btn').addEventListener('click', () => {
            this.hideStatusOverlay();
            this.showScreen('transaction');
        });

        // Reconciliation
        document.querySelectorAll('#reconcile-numpad button').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleNumpadInput(e.target.dataset.key, 'reconcile'));
        });

        document.getElementById('actual-cash').addEventListener('input', () => this.updateDiscrepancy());
        document.getElementById('confirm-close-btn').addEventListener('click', () => this.closeShift());
        document.getElementById('cancel-reconcile-btn').addEventListener('click', () => this.showScreen('transaction'));
        
        document.getElementById('print-receipt-btn').addEventListener('click', () => {
            window.print();
        });
    },

    checkAuth() {
        if (Auth.isAuthenticated() && Auth.isAdmin()) {
            this.showScreen('admin-dashboard');
            this.initAdminDashboard();
        } else if (Auth.isAuthenticated() && Auth.activeShift) {
            this.showTransactionScreen();
        } else if (Auth.isAuthenticated()) {
            this.showShiftStart();
        } else {
            this.showScreen('login');
        }
    },

    handleNumpadInput(key, field) {
        const input = document.getElementById(field === 'pin' ? 'pin-input' : field === 'cash' ? 'starting-cash' : 'actual-cash');
        if (!input) return;

        if (key === 'backspace') {
            input.value = input.value.slice(0, -1);
        } else if (key === 'clear') {
            input.value = '';
        } else if (key === '.') {
            if (!input.value.includes('.')) {
                input.value += '.';
            }
        } else {
            if (field === 'pin' && input.value.length < 4) {
                input.value += key;
            } else if (field !== 'pin') {
                input.value += key;
            }
        }

        if (field === 'pin') {
            this.pin = input.value;
            this.updatePinDots();
            document.getElementById('login-btn').disabled = this.pin.length !== 4;
        } else if (field === 'cash') {
            document.getElementById('open-shift-btn').disabled = !parseFloat(input.value) > 0;
        } else if (field === 'reconcile') {
            this.updateDiscrepancy();
        }
    },

    updatePinDots() {
        const dots = document.querySelectorAll('#pin-dots .dot');
        dots.forEach((dot, index) => {
            if (index < this.pin.length) {
                dot.classList.add('filled');
            } else {
                dot.classList.remove('filled');
            }
        });
    },

    async handleLogin() {
        const username = 'operator1';
        const pin = this.pin;
        const errorEl = document.getElementById('login-error');

        try {
            errorEl.textContent = 'Logging in...';
            await Auth.login(username, pin);
            errorEl.textContent = '';
            this.pin = '';
            document.getElementById('pin-input').value = '';
            this.updatePinDots();
            if (Auth.isAdmin()) {
                this.showAdminDashboard();
            } else {
                this.showShiftStart();
            }
        } catch (error) {
            errorEl.textContent = error.message;
            this.pin = '';
            document.getElementById('pin-input').value = '';
            this.updatePinDots();
        }
    },

    showShiftStart() {
        document.getElementById('operator-name').textContent = Auth.user?.username || 'Operator';
        document.getElementById('booth-name').textContent = Auth.booth?.name || 'Booth 1';
        document.getElementById('shift-date').textContent = new Date().toLocaleDateString();
        this.showScreen('shift-start');
    },

    async openShift() {
        const startingCash = parseFloat(document.getElementById('starting-cash').value);
        if (!startingCash || startingCash <= 0) {
            alert('Please enter a valid starting cash amount');
            return;
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/shifts/start?booth_id=${Auth.booth?.id || '1'}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...Auth.getAuthHeader(),
                },
                body: JSON.stringify({ starting_cash: startingCash }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start shift');
            }

            const shift = await response.json();
            Auth.activeShift = shift;
            localStorage.setItem('activeShift', JSON.stringify(shift));

            this.showTransactionScreen();
        } catch (error) {
            alert(error.message);
        }
    },

    showTransactionScreen() {
        document.getElementById('operator-display').textContent = Auth.user?.username || 'Operator';
        this.showScreen('transaction');
        this.connectWebSocket();
    },

    selectNetwork(network) {
        this.selectedNetwork = network;
        document.querySelectorAll('#network-toggle .toggle-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.network === network);
        });
        this.updateFeeDisplay();
    },

    selectType(type) {
        this.selectedType = type;
        document.querySelectorAll('#type-toggle .toggle-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.type === type);
        });
        this.updateFeeDisplay();
    },

    updateFeeDisplay() {
        let amount = parseFloat(document.getElementById('amount').value) || 0;
        if (this.selectedType === 'balance') amount = 0;
        const fee = Transactions.calculateFee(amount, this.selectedType);
        const total = this.selectedType === 'withdraw' ? amount + fee : amount;

        document.getElementById('fee-amount').textContent = Transactions.formatCurrency(fee);
        document.getElementById('total-amount').textContent = Transactions.formatCurrency(total);
        document.getElementById('process-btn').disabled = !this.validateTransactionForm();
    },

    validateTransactionForm() {
        const phone = document.getElementById('customer-phone').value.trim();
        const amount = parseFloat(document.getElementById('amount').value);
        if (this.selectedType === 'balance') return Transactions.validatePhoneNumber(phone);
        return Transactions.validatePhoneNumber(phone) && Transactions.validateAmount(amount);
    },

    async processTransaction() {
        const phone = document.getElementById('customer-phone').value.trim();
        let amount = parseFloat(document.getElementById('amount').value);
        if (this.selectedType === 'balance') {
            amount = 1.0; // Dummy amount for backend schema
        }

        if (!this.validateTransactionForm()) {
            alert('Please enter valid phone number and amount');
            return;
        }

        this.showStatusOverlay('processing', 'Sending Request', 'Connecting to server...');
        this.currentTransaction = { phone, amount, type: this.selectedType, network: this.selectedNetwork };

        try {
            const transaction = await Transactions.createTransaction({
                transaction_type: this.selectedType,
                customer_phone: phone,
                amount: amount,
                sim_card_id: null,
            });

            this.currentTransaction.id = transaction.id;
            this.updateStatusOverlay('pending', 'Waiting for Gateway', 'Position in queue...');
            this.startTransactionTimeout();

            wsManager.send({
                type: 'transaction_status',
                transaction_id: transaction.id,
                status: 'pending'
            });
        } catch (error) {
            this.hideStatusOverlay();
            alert(error.message);
        }
    },

    startTransactionTimeout() {
        if (this.transactionTimeout) {
            clearTimeout(this.transactionTimeout);
        }
        this.transactionTimeout = setTimeout(() => {
            if (this.currentTransaction) {
                this.showTransactionError('Transaction timeout. Please try again.');
            }
        }, CONFIG.TRANSACTION_TIMEOUT);
    },

    showStatusOverlay(status, title, message) {
        const overlay = document.getElementById('status-overlay');
        const icon = document.getElementById('status-icon');
        const titleEl = document.getElementById('status-title');
        const messageEl = document.getElementById('status-message');
        const detailsEl = document.getElementById('status-details');
        const queueInfo = document.getElementById('queue-info');
        const closeBtn = document.getElementById('status-close-btn');

        overlay.classList.remove('hidden');
        icon.className = 'status-icon ' + status;
        titleEl.textContent = title;
        messageEl.textContent = message;
        detailsEl.innerHTML = '';
        queueInfo.classList.add('hidden');
        closeBtn.classList.add('hidden');
    },

    updateStatusOverlay(status, title, message, detail = null) {
        const icon = document.getElementById('status-icon');
        const titleEl = document.getElementById('status-title');
        const messageEl = document.getElementById('status-message');
        const detailsEl = document.getElementById('status-details');

        icon.className = 'status-icon ' + status;
        titleEl.textContent = title;
        messageEl.textContent = message;

        if (detail) {
            detailsEl.textContent = detail;
        }
    },

    showTransactionSuccess(transaction) {
        const icon = document.getElementById('status-icon');
        const titleEl = document.getElementById('status-title');
        const messageEl = document.getElementById('status-message');
        const detailsEl = document.getElementById('status-details');
        const closeBtn = document.getElementById('status-close-btn');

        icon.className = 'status-icon success';
        titleEl.textContent = 'SUCCESS';
        messageEl.textContent = 'Transaction completed successfully';
        detailsEl.innerHTML = `
            <p><strong>Reference:</strong> ${transaction.mno_reference_code || 'N/A'}</p>
            <p><strong>Amount:</strong> ${Transactions.formatCurrency(transaction.amount)}</p>
            <p><strong>Fee:</strong> ${Transactions.formatCurrency(transaction.fee)}</p>
            <p><strong>Hand over ${Transactions.formatCurrency(transaction.amount)} to customer</strong></p>
        `;
        document.getElementById('print-receipt-btn').classList.remove('hidden');
        closeBtn.classList.remove('hidden');

        if (this.transactionTimeout) {
            clearTimeout(this.transactionTimeout);
        }
        this.currentTransaction = null;
    },

    showTransactionError(message) {
        const icon = document.getElementById('status-icon');
        const titleEl = document.getElementById('status-title');
        const messageEl = document.getElementById('status-message');
        const detailsEl = document.getElementById('status-details');
        const closeBtn = document.getElementById('status-close-btn');

        icon.className = 'status-icon error';
        titleEl.textContent = 'FAILED';
        messageEl.textContent = message;
        detailsEl.innerHTML = '<p>Do not give cash to customer. Transaction did not complete.</p>';
        document.getElementById('print-receipt-btn').classList.add('hidden');
        closeBtn.classList.remove('hidden');

        if (this.transactionTimeout) {
            clearTimeout(this.transactionTimeout);
        }
        this.currentTransaction = null;
    },

    hideStatusOverlay() {
        document.getElementById('status-overlay').classList.add('hidden');
    },

    showReconciliation() {
        this.loadShiftReport();
        this.showScreen('reconciliation');
    },

    async loadShiftReport() {
        if (!Auth.activeShift) return;

        try {
            const transactions = await Transactions.getShiftTransactions(Auth.activeShift.id);
            const cashIns = transactions
                .filter(t => t.transaction_type === 'cash_in' && t.status === 'success')
                .reduce((sum, t) => sum + parseFloat(t.amount), 0);
            const cashOuts = transactions
                .filter(t => t.transaction_type === 'cash_out' && t.status === 'success')
                .reduce((sum, t) => sum + parseFloat(t.amount), 0);

            const startingCash = parseFloat(Auth.activeShift.starting_cash) || 0;
            const expected = startingCash + cashIns - cashOuts;

            document.getElementById('report-starting').textContent = Transactions.formatCurrency(startingCash);
            document.getElementById('report-cashin').textContent = '+' + Transactions.formatCurrency(cashIns);
            document.getElementById('report-cashout').textContent = '-' + Transactions.formatCurrency(cashOuts);
            document.getElementById('report-expected').textContent = Transactions.formatCurrency(expected);

            this.expectedClosing = expected;
        } catch (error) {
            console.error('Failed to load shift report:', error);
        }
    },

    updateDiscrepancy() {
        const actualCash = parseFloat(document.getElementById('actual-cash').value) || 0;
        const discrepancyEl = document.getElementById('discrepancy-display');
        const discrepancyText = document.getElementById('discrepancy-text');

        if (actualCash > 0 && this.expectedClosing !== undefined) {
            const diff = actualCash - this.expectedClosing;
            discrepancyEl.classList.remove('hidden', 'balanced', 'shortage', 'overage');

            if (Math.abs(diff) < 0.01) {
                discrepancyEl.classList.add('balanced');
                discrepancyText.textContent = '✓ Balanced - No discrepancy';
            } else if (diff < 0) {
                discrepancyEl.classList.add('shortage');
                discrepancyText.textContent = `⚠ Shortage of ${Transactions.formatCurrency(Math.abs(diff))}`;
            } else {
                discrepancyEl.classList.add('overage');
                discrepancyText.textContent = `⚠ Overage of ${Transactions.formatCurrency(diff)}`;
            }
        } else {
            discrepancyEl.classList.add('hidden');
        }
    },

    async closeShift() {
        const actualCash = parseFloat(document.getElementById('actual-cash').value);
        if (!actualCash && actualCash !== 0) {
            alert('Please enter actual cash count');
            return;
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/shifts/${Auth.activeShift.id}/close`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...Auth.getAuthHeader(),
                },
                body: JSON.stringify({ actual_cash: actualCash }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to close shift');
            }

            Auth.activeShift = null;
            localStorage.removeItem('activeShift');
            this.hideStatusOverlay();
            this.showScreen('login');
        } catch (error) {
            alert(error.message);
        }
    },

    setupWebSocketListeners() {
        wsManager.on('connected', () => {
            console.log('WebSocket connected');
        });

        wsManager.on('transaction_update', (data) => {
            console.log('Transaction update:', data);
            this.handleTransactionUpdate(data);
        });

        wsManager.on('disconnected', () => {
            console.log('WebSocket disconnected');
        });

        wsManager.on('error', (error) => {
            console.error('WebSocket error:', error);
        });
    },

    connectWebSocket() {
        if (Auth.booth?.id) {
            wsManager.connect(Auth.booth.id);
        }
    },

    handleTransactionUpdate(data) {
        if (!this.currentTransaction || data.transaction_id !== this.currentTransaction.id) {
            return;
        }

        switch (data.status) {
            case 'pending':
                this.updateStatusOverlay('processing', 'Waiting for Gateway', 'Position in queue...');
                break;
            case 'processing':
                this.updateStatusOverlay('processing', 'Processing', 'Executing USSD...');
                break;
            case 'success':
                this.currentTransaction.status = 'success';
                this.showTransactionSuccess({
                    mno_reference_code: data.detail || 'TXN-' + Date.now(),
                    amount: this.currentTransaction.amount,
                    fee: Transactions.calculateFee(this.currentTransaction.amount, this.currentTransaction.type),
                });
                break;
            case 'failed':
                this.currentTransaction.status = 'failed';
                this.showTransactionError(data.detail || 'Transaction failed');
                break;
            case 'requires_manual_review':
                this.showTransactionError('Transaction requires manual review. Please contact admin.');
                break;
        }
    },

    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.add('hidden');
        });
        document.getElementById(`${screenId}-screen`).classList.remove('hidden');
        this.currentScreen = screenId;
    },

    showAdminDashboard() {
        this.showScreen('admin-dashboard');
        this.bindAdminEvents();
        this.loadAdminBooths();
    },

    bindAdminEvents() {
        if (this.adminEventsBound) return;
        
        document.getElementById('admin-logout-btn').addEventListener('click', () => {
            Auth.logout();
            this.showScreen('login');
        });

        document.querySelectorAll('.admin-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.admin-tabs .tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.admin-tab-content').forEach(c => c.classList.add('hidden'));
                
                e.target.classList.add('active');
                document.getElementById('tab-' + e.target.dataset.tab).classList.remove('hidden');

                if (e.target.dataset.tab === 'booths') this.loadAdminBooths();
                if (e.target.dataset.tab === 'operators') this.loadAdminOperators();
                if (e.target.dataset.tab === 'audit') this.loadAdminAudit();
            });
        });

        document.getElementById('refresh-booths-btn').addEventListener('click', () => this.loadAdminBooths());
        document.getElementById('refresh-operators-btn').addEventListener('click', () => this.loadAdminOperators());
        document.getElementById('refresh-audit-btn').addEventListener('click', () => this.loadAdminAudit());

        this.adminEventsBound = true;
    },

    async loadAdminBooths() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/booths`, {
                headers: Auth.getAuthHeader()
            });
            if (!response.ok) throw new Error('Failed to load booths');
            const booths = await response.json();
            
            const tbody = document.querySelector('#booths-table tbody');
            tbody.innerHTML = '';
            booths.forEach(booth => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${booth.name}</td>
                    <td>${booth.location || 'N/A'}</td>
                    <td><span class="status-badge ${booth.status || 'active'}">${(booth.status || 'ACTIVE').toUpperCase()}</span></td>
                    <td>
                        <button class="action-btn block-btn" data-id="${booth.id}">Block</button>
                        <button class="action-btn suspend-btn" data-id="${booth.id}">Suspend</button>
                        <button class="action-btn details-btn" data-id="${booth.id}">Details</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            
            // Add action listeners
            document.querySelectorAll('.block-btn').forEach(btn => btn.addEventListener('click', (e) => this.adminAction('booths', e.target.dataset.id, 'block')));
            document.querySelectorAll('.suspend-btn').forEach(btn => btn.addEventListener('click', (e) => this.adminAction('booths', e.target.dataset.id, 'suspend')));
        } catch (e) {
            console.error(e);
            document.querySelector('#booths-table tbody').innerHTML = '<tr><td colspan="4">Error loading booths</td></tr>';
        }
    },

    async loadAdminOperators() {
        const tbody = document.querySelector('#operators-table tbody');
        tbody.innerHTML = '<tr><td colspan="4">Operator API endpoint not fully implemented in demo, displaying mock data</td></tr>';
        // Mock data
        const mockOp = `<tr><td>operator1</td><td>operator</td><td><span class="status-badge active">ACTIVE</span></td><td>
            <button class="action-btn">Deactivate</button>
            <button class="action-btn">Reset Pwd</button>
        </td></tr>`;
        tbody.innerHTML += mockOp;
    },

    async loadAdminAudit() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/admin/audit-logs`, {
                headers: Auth.getAuthHeader()
            });
            if (!response.ok) throw new Error('Failed to load logs');
            const logs = await response.json();
            
            const tbody = document.querySelector('#audit-table tbody');
            tbody.innerHTML = '';
            logs.forEach(log => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                    <td>${log.admin_id}</td>
                    <td>${log.action_type}</td>
                    <td>${log.target_booth || '-'}</td>
                `;
                tbody.appendChild(tr);
            });
        } catch (e) {
            console.error(e);
            document.querySelector('#audit-table tbody').innerHTML = '<tr><td colspan="4">No logs or error loading</td></tr>';
        }
    },

    async adminAction(entity, id, action) {
        if (!confirm(`Are you sure you want to ${action} this ${entity}?`)) return;
        try {
            const res = await fetch(`${CONFIG.API_BASE_URL}/admin/${entity}/${id}/${action}`, {
                method: 'POST',
                headers: Auth.getAuthHeader()
            });
            if (res.ok) {
                alert(`Action ${action} successful`);
                if (entity === 'booths') this.loadAdminBooths();
            } else {
                alert('Action failed');
            }
        } catch (e) {
            console.error(e);
            alert('Error performing action');
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
