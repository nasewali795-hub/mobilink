import re
with open("app.py", "r") as f:
    py = f.read()

new_endpoints = """
# --- Settings & Admin Endpoints ---

@app.route('/api/settings', methods=['GET'])
@token_required(allowed_roles=['HQ'])
def get_settings():
    settings = app_settings.get('settings', {
        'system': {
            'organization_name': 'AgriFin Microfinance',
            'currency': 'ZMW',
            'date_format': 'YYYY-MM-DD',
            'jwt_expiry_hours': 4,
            'default_theme': 'dark'
        },
        'loan_rules': {
            'fertilizer_downpayment_per_bag': 450,
            'default_repayment_ratio': '1:4',
            'fertilizer_term_days': 180,
            'default_fertilizer_type': 'NPK + Urea Compound',
            'asset_downpayment_percent': 20,
            'asset_interest_rate': 15,
            'asset_installments': 12,
            'asset_installment_frequency': 'monthly',
            'asset_term_days': 365,
            'cash_interest_rate': 10,
            'cash_term_months': 6,
            'cash_term_days': 180,
            'default_cash_purpose': 'General Agricultural Cash',
            'shop_max_loan_limit': 10000,
            'min_cash_loan_amount': 50
        },
        'features': {
            'mobile_money': True,
            'sms_notifications': False,
            'accounting_sync': True
        },
        'templates': {
            'repayment_reminder': 'Dear {{borrower_name}}, your loan repayment of {{amount}} is due on {{due_date}}. Please visit your nearest shop to make payment.',
            'disbursement_notice': 'Dear {{borrower_name}}, your loan of {{amount}} has been disbursed. Please collect from {{shop_name}}.',
            'overdue_alert': 'Dear {{borrower_name}}, your loan payment is overdue by {{days_overdue}} days. Please settle immediately to avoid penalties.'
        }
    })
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
@token_required(allowed_roles=['HQ'])
def save_settings():
    data = request.json or {}
    app_settings['settings'] = data
    app_settings.setdefault('audit_trail', []).append({
        'action': 'settings_updated',
        'user': request.user.get('user'),
        'role': request.user.get('role'),
        'date': datetime.date.today().isoformat(),
        'notes': 'System settings updated'
    })
    return jsonify({'message': 'Settings saved successfully', 'settings': data})

@app.route('/api/feature-flags', methods=['GET'])
@token_required(allowed_roles=['HQ'])
def get_feature_flags():
    flags = app_settings.get('settings', {}).get('features', {
        'mobile_money': True,
        'sms_notifications': False,
        'accounting_sync': True
    })
    return jsonify(flags)

@app.route('/api/feature-flags', methods=['POST'])
@token_required(allowed_roles=['HQ'])
def update_feature_flags():
    data = request.json or {}
    if 'settings' not in app_settings:
        app_settings['settings'] = {}
    if 'features' not in app_settings['settings']:
        app_settings['settings']['features'] = {}
    app_settings['settings']['features'].update(data)
    return jsonify({'message': 'Feature flags updated', 'features': app_settings['settings']['features']})

@app.route('/api/users', methods=['GET'])
@token_required(allowed_roles=['HQ'])
def list_users():
    user_list = []
    for username, info in users.items():
        user_list.append({
            'username': username,
            'role': info.get('role', 'Agent'),
            'district': info.get('district'),
            'village': info.get('village'),
            'shop': info.get('shop')
        })
    return jsonify({'users': user_list})

@app.route('/api/users', methods=['POST'])
@token_required(allowed_roles=['HQ'])
def create_user():
    data = request.json or {}
    username = data.get('username')
    role = data.get('role', 'Agent')
    district = data.get('district')
    village = data.get('village')
    shop = data.get('shop')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    if username in users:
        return jsonify({'error': 'User already exists'}), 409
    
    users[username] = {
        'role': role,
        'district': district,
        'village': village,
        'shop': shop,
        'created_at': datetime.date.today().isoformat()
    }
    
    return jsonify({'message': 'User created successfully', 'user': users[username]})

@app.route('/api/users/<username>', methods=['PUT'])
@token_required(allowed_roles=['HQ'])
def update_user(username):
    data = request.json or {}
    if username not in users:
        return jsonify({'error': 'User not found'}), 404
    
    users[username].update({
        'role': data.get('role', users[username].get('role')),
        'district': data.get('district', users[username].get('district')),
        'village': data.get('village', users[username].get('village')),
        'shop': data.get('shop', users[username].get('shop'))
    })
    
    return jsonify({'message': 'User updated successfully', 'user': users[username]})

@app.route('/api/users/<username>', methods=['DELETE'])
@token_required(allowed_roles=['HQ'])
def delete_user(username):
    if username not in users:
        return jsonify({'error': 'User not found'}), 404
    
    del users[username]
    return jsonify({'message': 'User deleted successfully'})

@app.route('/api/products', methods=['GET'])
@token_required()
def list_products():
    products = app_settings.get('loan_products', [])
    return jsonify({'products': products})

@app.route('/api/products', methods=['POST'])
@token_required(allowed_roles=['HQ'])
def create_product():
    data = request.json or {}
    required_fields = ['name', 'type', 'min_amount', 'max_amount', 'interest_rate', 'interest_type', 'repayment_frequency']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    product_id = data.get('id', 'LP-' + uuid.uuid4().hex[:8].upper())
    product = {
        'id': product_id,
        'name': data.get('name'),
        'type': data.get('type'),
        'min_amount': float(data.get('min_amount', 0)),
        'max_amount': float(data.get('max_amount', 0)),
        'interest_rate': float(data.get('interest_rate', 0)),
        'interest_type': data.get('interest_type', 'Flat Rate'),
        'repayment_frequency': data.get('repayment_frequency', 'Monthly'),
        'grace_period_days': int(data.get('grace_period_days', 0)),
        'default_installments': int(data.get('default_installments', 6)),
        'default_tenure': data.get('default_tenure', '6 Months'),
        'disbursement_method': data.get('disbursement_method', 'Cash at shop'),
        'repayment_method': data.get('repayment_method', 'Cash only'),
        'late_penalty_type': data.get('late_penalty_type', 'percentage'),
        'late_penalty_value': float(data.get('late_penalty_value', 0)),
        'default_handling': data.get('default_handling', ''),
        'restructuring_allowed': data.get('restructuring_allowed', True),
        'approval_level': data.get('approval_level', 'Shop'),
        'alerts_enabled': data.get('alerts_enabled', True),
        'audit_trail_enabled': data.get('audit_trail_enabled', True)
    }
    
    app_settings.setdefault('loan_products', []).append(product)
    return jsonify({'message': 'Product created successfully', 'product': product}), 201

@app.route('/api/products/<product_id>', methods=['PUT'])
@token_required(allowed_roles=['HQ'])
def update_product(product_id):
    data = request.json or {}
    products = app_settings.get('loan_products', [])
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    product.update(data)
    return jsonify({'message': 'Product updated successfully', 'product': product})

@app.route('/api/products/<product_id>', methods=['DELETE'])
@token_required(allowed_roles=['HQ'])
def delete_product(product_id):
    products = app_settings.get('loan_products', [])
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    app_settings['loan_products'] = [p for p in products if p['id'] != product_id]
    return jsonify({'message': 'Product deleted successfully'})

@app.route('/api/audit/export', methods=['GET'])
@token_required(allowed_roles=['HQ'])
def export_audit_log():
    audit_log = app_settings.get('audit_trail', [])
    format = request.args.get('format', 'json')
    
    if format == 'csv':
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['action', 'user', 'role', 'date', 'notes'])
        writer.writeheader()
        for entry in audit_log:
            writer.writerow({
                'action': entry.get('action', ''),
                'user': entry.get('user', ''),
                'role': entry.get('role', ''),
                'date': entry.get('date', ''),
                'notes': entry.get('notes', '')
            })
        return output.getvalue(), 200, {'Content-Type': 'text/csv'}
    else:
        return jsonify({'audit_log': audit_log})

"""

marker = "@app.route('/loan_products', methods=['GET'])"
if marker in py:
    py = py.replace(marker, new_endpoints + "\n" + marker)
    print('Added settings and admin endpoints')
else:
    print('Could not find marker')

with open('app.py', 'w') as f:
    f.write(py)
print('Saved app.py')
