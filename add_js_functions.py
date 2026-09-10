import re

with open("static/js/app.js", "r") as f:
    js = f.read()

# Add missing JS functions before the last function or at the end
new_functions = """

async function saveSettings() {
    try {
        const settings = {
            system: {
                organization_name: document.getElementById('setting-org-name')?.value || 'AgriFin Microfinance',
                currency: document.getElementById('setting-currency')?.value || 'ZMW',
                date_format: document.getElementById('setting-date-format')?.value || 'YYYY-MM-DD',
                jwt_expiry_hours: parseInt(document.getElementById('setting-jwt-expiry')?.value || '4'),
                default_theme: document.getElementById('setting-default-theme')?.value || 'dark'
            },
            loan_rules: {
                fertilizer_downpayment_per_bag: parseFloat(document.getElementById('rule-fert-downpayment')?.value || '450'),
                default_repayment_ratio: document.getElementById('rule-repayment-ratio')?.value || '1:4',
                fertilizer_term_days: parseInt(document.getElementById('rule-fert-term')?.value || '180'),
                default_fertilizer_type: document.getElementById('rule-fert-type')?.value || 'NPK + Urea Compound',
                asset_downpayment_percent: parseFloat(document.getElementById('rule-asset-downpayment')?.value || '20'),
                asset_interest_rate: parseFloat(document.getElementById('rule-asset-interest')?.value || '15'),
                asset_installments: parseInt(document.getElementById('rule-asset-installments')?.value || '12'),
                asset_installment_frequency: document.getElementById('rule-asset-frequency')?.value || 'monthly',
                asset_term_days: parseInt(document.getElementById('rule-asset-term')?.value || '365'),
                cash_interest_rate: parseFloat(document.getElementById('rule-cash-interest')?.value || '10'),
                cash_term_months: parseInt(document.getElementById('rule-cash-term-months')?.value || '6'),
                cash_term_days: parseInt(document.getElementById('rule-cash-term-days')?.value || '180'),
                default_cash_purpose: document.getElementById('rule-cash-purpose')?.value || 'General Agricultural Cash',
                shop_max_loan_limit: parseFloat(document.getElementById('rule-shop-max-loan')?.value || '10000'),
                min_cash_loan_amount: parseFloat(document.getElementById('rule-min-cash')?.value || '50')
            },
            features: {
                mobile_money: document.getElementById('flag-mobile-money')?.checked || true,
                sms_notifications: document.getElementById('flag-sms')?.checked || false,
                accounting_sync: document.getElementById('flag-accounting')?.checked || true
            },
            templates: {
                repayment_reminder: document.getElementById('template-repayment')?.value || '',
                disbursement_notice: document.getElementById('template-disbursement')?.value || '',
                overdue_alert: document.getElementById('template-overdue')?.value || ''
            }
        };

        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(settings)
        });

        if (res.ok) {
            showToast('Settings saved and deployed successfully', 'success');
        } else {
            showToast('Failed to save settings', 'error');
        }
    } catch (err) {
        console.error('Error saving settings:', err);
        showToast('Error saving settings', 'error');
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
    const rows = document.querySelectorAll('#users-table-body tr');
    
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

async function setRole(username) {
    const newRole = prompt(`Enter new role for ${username}:\\nOptions: HQ, District, Village, Agent`);
    if (!newRole) return;
    
    try {
        const res = await fetch(`/api/users/${encodeURIComponent(username)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ role: newRole })
        });

        const data = await res.json();
        if (res.ok) {
            showToast(`Role updated for ${username}`, 'success');
            loadUsers();
        } else {
            showToast(data.error || 'Failed to update role', 'error');
        }
    } catch (err) {
        console.error('Error updating role:', err);
        showToast('Error updating role', 'error');
    }
}

async function deleteUser(username) {
    if (!confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) return;
    
    try {
        const res = await fetch(`/api/users/${encodeURIComponent(username)}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        const data = await res.json();
        if (res.ok) {
            showToast(`User ${username} deleted`, 'success');
            loadUsers();
        } else {
            showToast(data.error || 'Failed to delete user', 'error');
        }
    } catch (err) {
        console.error('Error deleting user:', err);
        showToast('Error deleting user', 'error');
    }
}

function exportPortfolioCSV() {
    const loans = window.allCashLoans || [];
    if (loans.length === 0) {
        showToast('No loans to export', 'error');
        return;
    }
    const headers = ['Loan ID', 'Borrower', 'Shop', 'Amount', 'Total Repayable', 'Balance', 'Status'];
    const rows = loans.map(l => [l.id, l.name, l.shop, l.loan_amount, l.total_repayable, l.balance_remaining, l.status]);
    let csv = headers.join(',') + '\\n';
    rows.forEach(r => csv += r.join(',') + '\\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'portfolio_export.csv';
    a.click();
    URL.revokeObjectURL(url);
    showToast('CSV exported', 'success');
}

"""

# Find a good place to insert - at the end of the file or before the last function
insert_pos = js.rfind('}')
if insert_pos >= 0:
    js = js[:insert_pos] + new_functions + js[insert_pos:]
    print('Added missing JS functions')
else:
    print('Could not find insertion point')

with open("static/js/app.js", "w") as f:
    f.write(js)
print('Saved app.js')
