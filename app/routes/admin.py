import uuid
import datetime
import csv
import io
from flask import Blueprint, request, jsonify
from app.auth import token_required
from app.state import users, structure, app_settings

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/users', methods=['GET'])
@token_required(allowed_roles=["HQ"])
def list_users():
    user_list = []
    for username, info in users.items():
        user_list.append({
            "username": username,
            "role": info.get("role", "Agent"),
            "district": info.get("district"),
            "village": info.get("village"),
            "shop": info.get("shop")
        })
    return jsonify({"users": user_list})


@admin_bp.route('/api/users', methods=['POST'])
@token_required(allowed_roles=["HQ"])
def create_user():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "Agent")
    district = data.get("district", "")
    village = data.get("village", "")
    shop = data.get("shop", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    if username in users:
        return jsonify({"error": f"User '{username}' already exists"}), 400

    users[username] = {
        "password": password, "role": role, "name": data.get("name", username),
        "district": district, "village": village, "shop": shop
    }

    return jsonify({"message": f"User '{username}' created successfully", "user": {
        "username": username, "role": role, "district": district, "village": village, "shop": shop
    }}), 201


@admin_bp.route('/api/users/<username>', methods=['PUT'])
@token_required(allowed_roles=["HQ"])
def update_user(username):
    if username not in users:
        return jsonify({"error": f"User '{username}' not found"}), 404

    data = request.json or {}
    if "role" in data:
        users[username]["role"] = data["role"]
    if "district" in data:
        users[username]["district"] = data["district"]
    if "village" in data:
        users[username]["village"] = data["village"]
    if "shop" in data:
        users[username]["shop"] = data["shop"]
    if "password" in data and data["password"]:
        users[username]["password"] = data["password"]
    if "name" in data:
        users[username]["name"] = data["name"]

    return jsonify({"message": f"User '{username}' updated successfully", "user": {
        "username": username,
        "role": users[username].get("role"),
        "district": users[username].get("district"),
        "village": users[username].get("village"),
        "shop": users[username].get("shop")
    }})


@admin_bp.route('/api/users/<username>', methods=['DELETE'])
@token_required(allowed_roles=["HQ"])
def delete_user(username):
    if username not in users:
        return jsonify({"error": f"User '{username}' not found"}), 404

    if users[username].get("role") == "HQ":
        hq_user_count = sum(1 for u in users.values() if u.get("role") == "HQ")
        if hq_user_count <= 1:
            return jsonify({"error": "Cannot delete the last HQ user"}), 400

    del users[username]
    return jsonify({"message": f"User '{username}' deleted successfully"})


@admin_bp.route('/api/feature-flags', methods=['GET'])
@token_required(allowed_roles=["HQ"])
def get_feature_flags():
    return jsonify(app_settings.get("features", {}))


@admin_bp.route('/api/feature-flags', methods=['POST'])
@token_required(allowed_roles=["HQ"])
def update_feature_flags():
    data = request.json or {}
    if "features" not in app_settings:
        app_settings["features"] = {}
    app_settings["features"].update(data)
    return jsonify({"message": "Feature flags updated", "features": app_settings["features"]})


@admin_bp.route('/api/settings', methods=['GET'])
@token_required(allowed_roles=['HQ'])
def get_settings():
    return jsonify(app_settings)


@admin_bp.route('/api/settings', methods=['POST'])
@token_required(allowed_roles=['HQ'])
def save_settings():
    data = request.json or {}
    for section in ["system", "loan_rules", "limits", "features", "templates"]:
        if section in data and isinstance(data[section], dict):
            if section not in app_settings:
                app_settings[section] = {}
            app_settings[section].update(data[section])

    app_settings.setdefault('audit_trail', []).append({
        'action': 'settings_updated',
        'user': request.user.get('user'),
        'role': request.user.get('role'),
        'date': datetime.date.today().isoformat(),
        'notes': 'System settings updated'
    })
    return jsonify({'message': 'Settings saved successfully', 'settings': app_settings})


@admin_bp.route('/api/audit/export', methods=['GET'])
@token_required(allowed_roles=['HQ'])
def export_audit_log():
    audit_log = app_settings.get('audit_trail', [])
    fmt = request.args.get('format', 'json')

    if fmt == 'csv':
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


@admin_bp.route('/api/disbursements', methods=['GET'])
@token_required(allowed_roles=["HQ", "District"])
def list_disbursements():
    results = []
    for province in structure:
        for district in structure[province]:
            for village in structure[province][district]:
                for shop, shop_data in structure[province][district][village].items():
                    for cat in ["fertilizer_loans", "asset_finance", "cash_loans"]:
                        for loan in shop_data.get("clients", {}).get(cat, []):
                            if loan.get("disbursement_date"):
                                results.append({
                                    "loan_id": loan.get("id"),
                                    "borrower": loan.get("name"),
                                    "shop": loan.get("shop_name"),
                                    "amount": loan.get("loan_amount"),
                                    "method": loan.get("disbursement_method", "cash"),
                                    "date": loan.get("disbursement_date"),
                                    "status": loan.get("status", "active")
                                })
    return jsonify({"disbursements": results})


@admin_bp.route('/api/repayments', methods=['GET'])
@token_required(allowed_roles=["HQ", "District"])
def list_repayments():
    results = []
    for province in structure:
        for district in structure[province]:
            for village in structure[province][district]:
                for shop, shop_data in structure[province][district][village].items():
                    for cat in ["fertilizer_loans", "asset_finance", "cash_loans"]:
                        for loan in shop_data.get("clients", {}).get(cat, []):
                            for payment in loan.get("repayment_history", []):
                                results.append({
                                    "loan_id": loan.get("id"),
                                    "borrower": loan.get("name"),
                                    "shop": loan.get("shop_name"),
                                    "amount": payment.get("amount"),
                                    "date": payment.get("date"),
                                    "notes": payment.get("notes", ""),
                                    "allocation": payment.get("allocation", {})
                                })
    return jsonify({"repayments": results})


@admin_bp.route('/api/applications', methods=['GET'])
@token_required()
def list_applications():
    applications = app_settings.get("applications", [])
    return jsonify({"applications": applications})


@admin_bp.route('/api/applications', methods=['POST'])
@token_required(allowed_roles=["Agent", "Village", "District", "HQ"])
def create_application():
    decoded = request.user
    agent_username = decoded["user"]
    data = request.json or {}
    borrower_name = data.get("borrower_name")
    product_id = data.get("product_id")
    requested_amount = float(data.get("requested_amount", 0))
    requested_term_days = int(data.get("requested_term_days", 30))
    repayment_frequency = data.get("repayment_frequency", "Monthly")
    collateral = data.get("collateral", "")
    attachments = data.get("attachments", [])

    if not borrower_name or not product_id or requested_amount <= 0:
        return jsonify({"error": "borrower_name, product_id, and positive requested_amount are required"}), 400

    products = app_settings.get("loan_products", [])
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return jsonify({"error": f"Product '{product_id}' not found"}), 404

    application_id = f"app-{uuid.uuid4().hex[:6]}"
    application = {
        "application_id": application_id,
        "borrower_name": borrower_name,
        "product_id": product_id,
        "product_name": product.get("name", product_id),
        "requested_amount": requested_amount,
        "requested_term_days": requested_term_days,
        "repayment_frequency": repayment_frequency,
        "collateral": collateral,
        "attachments": attachments,
        "status": "submitted",
        "submitted_by": agent_username,
        "submitted_at": datetime.date.today().isoformat(),
        "audit_trail": [{
            "action": "application_created",
            "user": agent_username,
            "role": decoded.get("role"),
            "date": datetime.date.today().isoformat(),
            "notes": f"Application for {borrower_name} - {product.get('name', product_id)}"
        }]
    }
    app_settings.setdefault("applications", []).append(application)
    return jsonify({"message": "Application submitted", "application": application}), 201


@admin_bp.route('/api/applications/<application_id>', methods=['GET'])
@token_required()
def get_application(application_id):
    applications = app_settings.get("applications", [])
    application = next((a for a in applications if a["application_id"] == application_id), None)
    if not application:
        return jsonify({"error": "Application not found"}), 404
    return jsonify(application)
