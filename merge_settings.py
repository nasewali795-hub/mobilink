import re
with open('templates/index.html', 'r') as f:
    html = f.read()

# 1. Merge sidebar nav items - keep only Settings & Admin
old_nav = """                <button class="nav-link" onclick="switchTab('hq-users-tab', this)" id="nav-users-link">
                    <i class="fa-solid fa-users-gear"></i> Users & Permissions
                </button>
                <button class="nav-link" onclick="switchTab('hq-integrations-tab', this)" id="nav-integrations-link">
                    <i class="fa-solid fa-plug"></i> Integrations
                </button>
                <button class="nav-link" onclick="switchTab('hq-admin-tab', this)" id="nav-admin-link">
                    <i class="fa-solid fa-gear"></i> Settings & Admin
                </button>"""

new_nav = """                <button class="nav-link" onclick="switchTab('hq-admin-tab', this)" id="nav-admin-link">
                    <i class="fa-solid fa-gear"></i> Settings & Admin
                </button>"""

html = html.replace(old_nav, new_nav)
print('Merged sidebar nav items')

# 2. Find and remove the three old tabs
users_match = re.search(r'(<div[^>]+id="hq-users-tab"[\s\S]*?</div>\s*</div>)', html)
integrations_match = re.search(r'(<div[^>]+id="hq-integrations-tab"[\s\S]*?</div>\s*</div>)', html)
admin_match = re.search(r'(<div[^>]+id="hq-admin-tab"[\s\S]*?</div>\s*</div>)', html)

tab_positions = []
if users_match:
    tab_positions.append((users_match.start(), users_match.end(), 'users'))
if integrations_match:
    tab_positions.append((integrations_match.start(), integrations_match.end(), 'integrations'))
if admin_match:
    tab_positions.append((admin_match.start(), admin_match.end(), 'admin'))

tab_positions.sort(key=lambda x: x[0])
print(f'Found tabs at positions: {[(p[0], p[2]) for p in tab_positions]}')

if len(tab_positions) >= 2:
    for start, end, name in reversed(tab_positions):
        html = html[:start] + html[end:]
        print(f'Removed {name} tab')
else:
    print('Not enough tabs found to merge')

# 3. Insert merged settings tab
merged_tab = '''    <div class="tab-view" id="hq-admin-tab">
        <div class="section-card glass">
            <div class="card-header">
                <h3><i class="fa-solid fa-gear"></i> Settings & Admin</h3>
            </div>
            
            <!-- User Management Section -->
            <div class="settings-section">
                <div class="settings-section-header" onclick="toggleSettingsSection('users-section')">
                    <i class="fa-solid fa-circle-chevron-right"></i>
                    <strong>User Management</strong>
                </div>
                <div class="settings-section-body" id="users-section">
                    <button class="btn btn-primary" onclick="showToast('Create user modal coming soon', 'success')"><i class="fa-solid fa-plus"></i> Create User</button>
                    <div class="table-wrapper" style="margin-top: 16px;">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Role</th>
                                    <th>District</th>
                                    <th>Village</th>
                                    <th>Shop</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="settings-users-table-body">
                                <tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 20px;">Loading users...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Roles & Approval Matrix Section -->
            <div class="settings-section">
                <div class="settings-section-header" onclick="toggleSettingsSection('roles-section')">
                    <i class="fa-solid fa-circle-chevron-right"></i>
                    <strong>Roles & Approval Matrix</strong>
                </div>
                <div class="settings-section-body" id="roles-section">
                    <div class="table-wrapper">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Role</th>
                                    <th>Approval Limit (ZMW)</th>
                                    <th>Branch Access</th>
                                    <th>HQ Access</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="settings-roles-table-body">
                                <tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 20px;">Loading roles...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- System Settings Section -->
            <div class="settings-section">
                <div class="settings-section-header" onclick="toggleSettingsSection('system-section')">
                    <i class="fa-solid fa-circle-chevron-right"></i>
                    <strong>System Settings</strong>
                </div>
                <div class="settings-section-body" id="system-section">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Organization Name</label>
                            <input type="text" data-setting="system.organization_name" value="AgriFin Microfinance">
                        </div>
                        <div class="form-group">
                            <label>Currency</label>
                            <select data-setting="system.currency">
                                <option value="ZMW" selected>ZMW</option>
                                <option value="USD">USD</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Date Format</label>
                            <select data-setting="system.date_format">
                                <option value="DD/MM/YYYY" selected>DD/MM/YYYY</option>
                                <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>JWT Token Expiry (hours)</label>
                            <input type="number" data-setting="system.jwt_expiry_hours" value="4" min="1" max="24">
                        </div>
                    </div>
                    <button class="btn btn-primary" onclick="showToast('Settings saved and deployed', 'success')"><i class="fa-solid fa-check"></i> Save and Deploy</button>
                </div>
            </div>

            <!-- Business Rules Section -->
            <div class="settings-section">
                <div class="settings-section-header" onclick="toggleSettingsSection('business-section')">
                    <i class="fa-solid fa-circle-chevron-right"></i>
                    <strong>Business Rules</strong>
                </div>
                <div class="settings-section-body" id="business-section">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Fertilizer Downpayment Per Bag (ZMW)</label>
                            <input type="number" data-setting="loan_rules.fertilizer_downpayment_per_bag" value="450" min="0">
                        </div>
                        <div class="form-group">
                            <label>Default Repayment Ratio</label>
                            <input type="text" data-setting="loan_rules.default_repayment_ratio" value="1:4">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Asset Downpayment (%)</label>
                            <input type="number" data-setting="loan_rules.asset_downpayment_percent" value="20" min="0" max="100">
                        </div>
                        <div class="form-group">
                            <label>Asset Interest Rate (%)</label>
                            <input type="number" data-setting="loan_rules.asset_interest_rate" value="15" min="0" max="100">
                        </div>
                    </div>
                    <button class="btn btn-amber" onclick="showToast('Business rules updated', 'success')"><i class="fa-solid fa-pen"></i> Edit Rules</button>
                </div>
            </div>

            <!-- Feature Flags Section -->
            <div class="settings-section">
                <div class="settings-section-header" onclick="toggleSettingsSection('features-section')">
                    <i class="fa-solid fa-circle-chevron-right"></i>
                    <strong>Feature Flags</strong>
                </div>
                <div class="settings-section-body" id="features-section">
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" data-setting="features.mobile_money" checked> Mobile Money
                        </label>
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" data-setting="features.sms_notifications"> SMS Notifications
                        </label>
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" data-setting="features.accounting_sync" checked> Accounting Sync
                        </label>
                    </div>
                </div>
            </div>

            <!-- Notification Templates Section -->
            <div class="settings-section">
                <div class="settings-section-header" onclick="toggleSettingsSection('templates-section')">
                    <i class="fa-solid fa-circle-chevron-right"></i>
                    <strong>Notification Templates</strong>
                </div>
                <div class="settings-section-body" id="templates-section">
                    <div class="form-group">
                        <label>Repayment Reminder</label>
                        <textarea rows="3" data-setting="templates.repayment_reminder">Dear {{farmer_name}}, your loan repayment of ZMW {{amount}} is due on {{due_date}}. Please visit your nearest shop to make payment.</textarea>
                    </div>
                    <div class="form-group">
                        <label>Disbursement Notice</label>
                        <textarea rows="3" data-setting="templates.disbursement_notice">Dear {{farmer_name}}, your loan of ZMW {{amount}} has been disbursed. Please collect from {{shop_name}}.</textarea>
                    </div>
                    <div class="form-group">
                        <label>Overdue Alert</label>
                        <textarea rows="3" data-setting="templates.overdue_alert">Dear {{farmer_name}}, your loan payment is overdue by {{days_overdue}} days. Please settle immediately to avoid penalties.</textarea>
                    </div>
                </div>
            </div>

            <!-- Integrations Section -->
            <div class="settings-section">
                <div class="settings-section-header" onclick="toggleSettingsSection('integrations-section')">
                    <i class="fa-solid fa-circle-chevron-right"></i>
                    <strong>Integrations</strong>
                </div>
                <div class="settings-section-body" id="integrations-section">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
                        <div style="background: rgba(255,255,255,0.03); padding: 16px; border-radius: var(--radius-sm); border-left: 3px solid var(--cyan);">
                            <h4 style="margin-bottom: 8px;">Payment Gateway</h4>
                            <p style="color: var(--text-dim); font-size: 13px; margin-bottom: 12px;">Connect mobile money and bank transfer providers.</p>
                            <span class="badge badge-active">Active</span>
                            <button class="btn btn-sm btn-primary" style="margin-top: 8px;" onclick="showToast('Payment gateway configured', 'success')">Configure</button>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 16px; border-radius: var(--radius-sm); border-left: 3px solid var(--amber);">
                            <h4 style="margin-bottom: 8px;">SMS Notifications</h4>
                            <p style="color: var(--text-dim); font-size: 13px; margin-bottom: 12px;">Send repayment reminders and alerts via SMS.</p>
                            <span class="badge badge-warning">Inactive</span>
                            <button class="btn btn-sm btn-primary" style="margin-top: 8px;" onclick="showToast('SMS notifications configured', 'success')">Configure</button>
                        </div>
                        <div style="background: rgba(255,255,255,0.03); padding: 16px; border-radius: var(--radius-sm); border-left: 3px solid var(--emerald);">
                            <h4 style="margin-bottom: 8px;">Accounting Sync</h4>
                            <p style="color: var(--text-dim); font-size: 13px; margin-bottom: 12px;">Sync loan data to external accounting software.</p>
                            <span class="badge badge-active">Active</span>
                            <button class="btn btn-sm btn-primary" style="margin-top: 8px;" onclick="showToast('Accounting sync configured', 'success')">Configure</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

'''

main_close = html.rfind('</main>')
if main_close >= 0:
    html = html[:main_close] + merged_tab + '\n    ' + html[main_close:]
    print('Inserted merged settings tab')
else:
    print('Could not find </main> tag')

with open('templates/index.html', 'w') as f:
    f.write(html)
print('Saved index.html')
