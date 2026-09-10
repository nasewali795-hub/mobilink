import uuid
import datetime
from flask import Blueprint, request, jsonify
from app.auth import token_required
from app.state import users, structure, app_settings
from app.utils import (
    round_to_2, generate_flat_schedule, generate_reducing_schedule,
    _adjust_rounding, allocate_repayment, find_loan_by_id, find_shop_by_name
)

loans_bp = Blueprint('loans', __name__)


@loans_bp.route('/fertilizer_loans/add', methods=['POST'])
@token_required(allowed_roles=["Agent", "Village", "District", "HQ"])
def add_fertilizer_loan():
    decoded = request.user
    agent_username = decoded["user"]
    shop_name = users[agent_username].get("shop")

    data = request.json or {}
    client_name = data.get("client_name")
    fertilizer_type = data.get("fertilizer_type", "NPK Compound")
    compound_d_bags = int(data.get("compound_d_bags", 0))
    urea_bags = int(data.get("urea_bags", 0))
    fertilizer_bags = int(data.get("fertilizer_bags", compound_d_bags + urea_bags))
    ratio = data.get("repayment_ratio", "1:4")

    try:
        ratio_value = int(ratio.split(":")[1])
    except Exception:
        ratio_value = 4
        ratio = "1:4"

    expected_maize_bags = fertilizer_bags * ratio_value
    downpayment = int(data.get("downpayment_cash", 450 * fertilizer_bags))

    for province in structure:
        for district in structure[province]:
            for village in structure[province][district]:
                if shop_name in structure[province][district][village]:
                    shop_data = structure[province][district][village][shop_name]
                    farmer = next((c for c in shop_data["clients"]["farmers"] if c["name"].lower() == client_name.lower()), None)
                    if not farmer:
                        return jsonify({"error": f"Client '{client_name}' must be registered in shop farmers database before adding a loan"}), 400

                    loan_record = {
                        "id": f"fl-{uuid.uuid4().hex[:6]}",
                        "name": client_name,
                        "loan_type": "fertilizer",
                        "fertilizer_type": fertilizer_type,
                        "compound_d_bags": compound_d_bags,
                        "urea_bags": urea_bags,
                        "fertilizer_bags": fertilizer_bags,
                        "downpayment_cash": downpayment,
                        "repayment_ratio": ratio,
                        "expected_maize_bags": expected_maize_bags,
                        "repayment_history": [],
                        "balance_remaining": expected_maize_bags,
                        "due_date": data.get("due_date", (datetime.date.today() + datetime.timedelta(days=180)).isoformat()),
                        "status": "active",
                        "added_by": agent_username,
                        "shop": shop_name,
                        "village": village,
                        "district": district,
                        "province": province
                    }

                    shop_data["clients"]["fertilizer_loans"].append(loan_record)

                    inventory = shop_data.get("inventory", [])
                    inv_item = next((i for i in inventory if i["item_name"].lower() == fertilizer_type.lower()), None)
                    if inv_item:
                        inv_item["quantity"] = max(0, inv_item.get("quantity", 0) - fertilizer_bags)

                    transactions = app_settings.setdefault("inventory", {}).setdefault("transactions", [])
                    transactions.append({
                        "id": f"tx-{uuid.uuid4().hex[:8]}",
                        "date": datetime.date.today().isoformat(),
                        "item_id": fertilizer_type.lower().replace(" ", "_"),
                        "item_name": fertilizer_type,
                        "type": "loan_issue",
                        "quantity": fertilizer_bags,
                        "unit": "bags",
                        "shop_id": shop_data.get("shop_id", ""),
                        "shop_name": shop_name,
                        "farmer_id": farmer.get("id", ""),
                        "farmer_name": client_name,
                        "loan_id": loan_record["id"],
                        "notes": f"Fertilizer loan issued to {client_name}",
                        "created_by": agent_username,
                        "created_by_role": request.user.get("role", "unknown")
                    })

                    return jsonify({"message": f"Fertilizer loan added for {client_name}", "loan": loan_record})

    return jsonify({"error": f"Shop '{shop_name}' not found in hierarchy"}), 404


@loans_bp.route('/asset_finance_loans/add', methods=['POST'])
@token_required(allowed_roles=["Agent", "Village", "District", "HQ"])
def add_asset_finance_loan():
    decoded = request.user
    agent_username = decoded["user"]
    shop_name = users[agent_username].get("shop")

    data = request.json or {}
    client_name = data.get("client_name")
    asset_type = data.get("asset_type")
    asset_value = float(data.get("asset_value", 0))

    if not client_name or not asset_type or asset_value <= 0:
        return jsonify({"error": "client_name, asset_type, and positive asset_value are required"}), 400

    downpayment_percent = float(data.get("downpayment_percent", 20))
    downpayment_cash = round(asset_value * downpayment_percent / 100.0, 2)
    loan_amount = round(asset_value - downpayment_cash, 2)
    interest_rate = float(data.get("interest_rate", 15))
    total_repayable = round(loan_amount * (1 + interest_rate / 100.0), 2)

    total_installments = int(data.get("total_installments", 12))
    installment_amount = round(total_repayable / total_installments, 2) if total_installments > 0 else total_repayable

    for province in structure:
        for district in structure[province]:
            for village in structure[province][district]:
                if shop_name in structure[province][district][village]:
                    shop_data = structure[province][district][village][shop_name]
                    farmer = next((c for c in shop_data["clients"]["farmers"] if c["name"].lower() == client_name.lower()), None)
                    if not farmer:
                        return jsonify({"error": f"Client '{client_name}' must be registered in shop farmers database before adding a loan"}), 400

                    loan_record = {
                        "id": f"af-{uuid.uuid4().hex[:6]}",
                        "name": client_name,
                        "loan_type": "asset_finance",
                        "asset_type": asset_type,
                        "asset_value": asset_value,
                        "downpayment_cash": downpayment_cash,
                        "loan_amount": loan_amount,
                        "interest_rate": interest_rate,
                        "total_repayable": total_repayable,
                        "installments": {
                            "frequency": data.get("frequency", "monthly"),
                            "total_installments": total_installments,
                            "installment_amount": installment_amount,
                            "repayment_history": []
                        },
                        "balance_remaining": total_repayable,
                        "due_date": data.get("due_date", (datetime.date.today() + datetime.timedelta(days=365)).isoformat()),
                        "status": "active",
                        "added_by": agent_username,
                        "shop": shop_name,
                        "village": village,
                        "district": district,
                        "province": province
                    }

                    shop_data["clients"]["asset_finance"].append(loan_record)

                    inventory = shop_data.get("inventory", [])
                    inv_item = next((i for i in inventory if i["item_name"].lower() == asset_type.lower()), None)
                    if inv_item:
                        inv_item["quantity"] = max(0, inv_item.get("quantity", 0) - 1)

                    transactions = app_settings.setdefault("inventory", {}).setdefault("transactions", [])
                    transactions.append({
                        "id": f"tx-{uuid.uuid4().hex[:8]}",
                        "date": datetime.date.today().isoformat(),
                        "item_id": asset_type.lower().replace(" ", "_"),
                        "item_name": asset_type,
                        "type": "loan_issue",
                        "quantity": 1,
                        "unit": "units",
                        "shop_id": shop_data.get("shop_id", ""),
                        "shop_name": shop_name,
                        "farmer_id": farmer.get("id", ""),
                        "farmer_name": client_name,
                        "loan_id": loan_record["id"],
                        "notes": f"Asset finance loan issued to {client_name}",
                        "created_by": agent_username,
                        "created_by_role": request.user.get("role", "unknown")
                    })

                    return jsonify({"message": f"Asset finance loan added for {client_name}", "loan": loan_record})

    return jsonify({"error": f"Shop '{shop_name}' not found in hierarchy"}), 404


@loans_bp.route('/cash_loans/add', methods=['POST'])
@token_required(allowed_roles=["HQ"])
def add_cash_loan():
    decoded = request.user
    agent_username = decoded["user"]
    agent_info = users.get(agent_username, {})
    shop_name = agent_info.get("shop")
    data = request.json or {}
    client_name = data.get("client_name")
    loan_amount = float(data.get("loan_amount", 0))

    if not client_name or loan_amount <= 0:
        return jsonify({"error": "client_name and positive loan_amount are required"}), 400

    if not shop_name:
        shop_name = data.get("shop")
    if not shop_name:
        return jsonify({"error": "Shop name is required for cash loan creation"}), 400

    interest_rate = float(data.get("interest_rate", 10))
    term_months = int(data.get("term_months", 6))
    total_repayable = round(loan_amount * (1 + interest_rate / 100.0), 2)

    target_shop, target_province, target_district, target_village = None, None, None, None

    for province in structure:
        for district in structure[province]:
            for village in structure[province][district]:
                if shop_name in structure[province][district][village]:
                    target_shop = structure[province][district][village][shop_name]
                    target_province, target_district, target_village = province, district, village
                    break

    if not target_shop:
        return jsonify({"error": f"Shop '{shop_name}' not found in hierarchy"}), 404

    farmer = next((c for c in target_shop["clients"]["farmers"] if c["name"].lower() == client_name.lower()), None)
    if not farmer:
        return jsonify({"error": f"Client '{client_name}' must be registered in shop farmers database before adding a loan"}), 400

    start_date = datetime.date.today().isoformat()
    schedule = []
    if term_months > 0:
        principal_per = round_to_2(loan_amount / term_months)
        interest_per = round_to_2((total_repayable - loan_amount) / term_months)
        current_date = datetime.date.fromisoformat(start_date)
        for i in range(1, term_months + 1):
            current_date = current_date + datetime.timedelta(days=30)
            schedule.append({
                "installment_no": i,
                "due_date": current_date.isoformat(),
                "due_principal": principal_per,
                "due_interest": interest_per,
                "due_fees": 0,
                "status": "due",
                "paid_at": None
            })
        schedule = _adjust_rounding(schedule, loan_amount, total_repayable - loan_amount, 0)

    loan_record = {
        "id": f"cl-{uuid.uuid4().hex[:6]}",
        "name": client_name,
        "loan_type": "cash",
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "total_repayable": total_repayable,
        "repayment_plan": {"term_months": term_months, "purpose": data.get("purpose", "General Agricultural Cash")},
        "schedule": schedule,
        "penalties": [],
        "repayment_history": [],
        "balance_remaining": total_repayable,
        "due_date": data.get("due_date", (datetime.date.today() + datetime.timedelta(days=180)).isoformat()),
        "status": "active",
        "added_by": agent_username,
        "shop": shop_name,
        "village": target_village,
        "district": target_district,
        "province": target_province
    }

    target_shop["clients"]["cash_loans"].append(loan_record)
    return jsonify({"message": f"Cash loan added for {client_name}", "loan": loan_record})


@loans_bp.route('/loans/create', methods=['POST'])
@token_required(allowed_roles=["Agent", "Village", "District", "HQ"])
def create_unified_loan():
    decoded = request.user
    agent_username = decoded["user"]
    agent_info = users.get(agent_username, {})
    data = request.json or {}

    shop_name = data.get("shop_name") or agent_info.get("shop")
    farmer_id = data.get("farmer_id")
    loan_product_id = data.get("loan_product_id")
    loan_amount = float(data.get("loan_amount", 0))

    if not shop_name:
        return jsonify({"error": "Shop name is required"}), 400
    if not farmer_id:
        return jsonify({"error": "farmer_id is required"}), 400
    if not loan_product_id:
        return jsonify({"error": "loan_product_id is required"}), 400
    if loan_amount <= 0:
        return jsonify({"error": "loan_amount must be positive"}), 400

    product = next((p for p in app_settings.get("loan_products", []) if p["id"] == loan_product_id), None)
    if not product:
        return jsonify({"error": f"Loan product '{loan_product_id}' not found"}), 404

    target_shop, target_province, target_district, target_village = None, None, None, None
    for province in structure:
        for district in structure[province]:
            for village in structure[province][district]:
                if shop_name in structure[province][district][village]:
                    target_shop = structure[province][district][village][shop_name]
                    target_province, target_district, target_village = province, district, village
                    break

    if not target_shop:
        return jsonify({"error": f"Shop '{shop_name}' not found in hierarchy"}), 404

    farmer = next((c for c in target_shop["clients"]["farmers"] if c.get("id") == farmer_id or c["name"].lower() == farmer_id.lower()), None)
    if not farmer:
        return jsonify({"error": f"Farmer '{farmer_id}' not found in shop '{shop_name}'"}), 404

    client_name = farmer["name"]
    interest_rate = float(data.get("interest_rate", product.get("interest_rate", 10)))
    interest_type = data.get("interest_type", product.get("interest_type", "Flat Rate"))
    total_installments = int(data.get("total_installments", product.get("default_installments", 6)))
    frequency = data.get("repayment_frequency", product.get("repayment_frequency", "Monthly"))
    total_repayable = round(loan_amount * (1 + interest_rate / 100.0), 2) if interest_type == "Flat Rate" else loan_amount
    installment_amount = round(total_repayable / total_installments, 2) if total_installments > 0 else total_repayable

    loan_type = product.get("type", "cash").lower()
    prefix_map = {"fertilizer": "fl", "asset_finance": "af", "cash": "cl"}
    prefix = prefix_map.get(loan_type, "gl")

    term_days = int(data.get("grace_period_days", 0))
    if frequency.lower() == "monthly":
        term_days = max(term_days, total_installments * 30)
    elif frequency.lower() == "weekly":
        term_days = max(term_days, total_installments * 7)
    else:
        term_days = max(term_days, 180)

    schedule = []
    if total_installments > 0:
        principal_per = round_to_2(loan_amount / total_installments)
        interest_per = round_to_2(total_repayable - loan_amount) / total_installments if total_repayable > loan_amount else 0
        interest_per = round_to_2(interest_per)
        current_date = datetime.date.today()
        for i in range(1, total_installments + 1):
            if frequency.lower() == "weekly":
                current_date = current_date + datetime.timedelta(days=7)
            elif frequency.lower() == "monthly":
                current_date = current_date + datetime.timedelta(days=30)
            else:
                current_date = current_date + datetime.timedelta(days=30)
            schedule.append({
                "installment_no": i,
                "due_date": current_date.isoformat(),
                "due_principal": principal_per,
                "due_interest": interest_per,
                "due_fees": 0,
                "status": "due",
                "paid_at": None
            })
        if total_repayable > loan_amount:
            schedule = _adjust_rounding(schedule, loan_amount, total_repayable - loan_amount, 0)

    loan_record = {
        "id": f"{prefix}-{uuid.uuid4().hex[:6]}",
        "name": client_name,
        "loan_type": loan_type,
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "interest_type": interest_type,
        "total_repayable": total_repayable,
        "loan_product_id": loan_product_id,
        "repayment_frequency": frequency,
        "total_installments": total_installments,
        "installment_amount": installment_amount,
        "grace_period_days": int(data.get("grace_period_days", 0)),
        "repayment_method": data.get("repayment_method", "Cash only"),
        "disbursement_method": data.get("disbursement_method", "Cash at shop"),
        "late_penalty_type": data.get("late_penalty_type", "percentage"),
        "late_penalty_value": float(data.get("late_penalty_value", 0)),
        "default_handling": data.get("default_handling", ""),
        "restructuring_allowed": data.get("restructuring_allowed", False),
        "approval_level": data.get("approval_level", "Shop"),
        "purpose": data.get("purpose", ""),
        "schedule": schedule,
        "repayment_history": [],
        "balance_remaining": total_repayable,
        "due_date": (datetime.date.today() + datetime.timedelta(days=term_days)).isoformat(),
        "status": "active",
        "added_by": agent_username,
        "shop": shop_name,
        "shop_name": shop_name,
        "village": target_village,
        "district": target_district,
        "province": target_province
    }

    category_map = {"fertilizer": "fertilizer_loans", "asset_finance": "asset_finance", "cash": "cash_loans"}
    category = category_map.get(loan_type, "cash_loans")
    target_shop["clients"][category].append(loan_record)

    return jsonify({"message": f"Loan created for {client_name}", "loan": loan_record})


@loans_bp.route('/loans/repay', methods=['POST'])
@token_required(allowed_roles=["Agent", "Village", "District", "HQ"])
def record_repayment():
    data = request.json or {}
    loan_id = data.get("loan_id")
    amount = float(data.get("amount", 0))
    notes = data.get("notes", "Repayment recorded")
    return record_repayment_with_id(loan_id, amount, notes, request.user.get("user"))


def record_repayment_with_id(loan_id, amount, notes="Repayment recorded", collected_by=None):
    if not loan_id or amount <= 0:
        return jsonify({"error": "loan_id and positive amount are required"}), 400

    target_loan, target_category, _ = find_loan_by_id(loan_id)

    if not target_loan:
        return jsonify({"error": f"Loan ID '{loan_id}' not found"}), 404

    current_balance = float(target_loan.get("balance_remaining", 0))
    if current_balance <= 0:
        return jsonify({"error": "Loan is already fully repaid"}), 400

    payment_entry = {
        "date": datetime.date.today().isoformat(),
        "amount": amount if target_category != "fertilizer_loans" else None,
        "bags": int(amount) if target_category == "fertilizer_loans" else None,
        "notes": notes,
        "recorded_by": collected_by
    }

    if target_category == "asset_finance":
        target_loan["installments"]["repayment_history"].append(payment_entry)
    else:
        target_loan["repayment_history"].append(payment_entry)

    if target_loan.get("schedule"):
        alloc_result = allocate_repayment(target_loan, amount)
        payment_entry["allocation"] = alloc_result.get("allocation", {})
        payment_entry["amount"] = amount
        return jsonify({
            "message": "Repayment successfully recorded",
            "loan_id": loan_id,
            "new_balance": target_loan["balance_remaining"],
            "status": target_loan["status"],
            "allocation": alloc_result.get("allocation", {})
        })
    else:
        new_balance = max(0.0, current_balance - amount)
        target_loan["balance_remaining"] = round(new_balance, 2)
        if target_loan["balance_remaining"] == 0:
            target_loan["status"] = "completed"
        return jsonify({
            "message": "Repayment successfully recorded",
            "loan_id": loan_id,
            "new_balance": target_loan["balance_remaining"],
            "status": target_loan["status"]
        })


@loans_bp.route('/api/loans/<loan_id>', methods=['GET'])
@token_required()
def api_get_loan(loan_id):
    target_loan, target_category, _ = find_loan_by_id(loan_id)
    if not target_loan:
        return jsonify({"error": f"Loan ID '{loan_id}' not found"}), 404
    return jsonify({"loan": target_loan, "schedules": target_loan.get("schedule", []), "repayments": []})


@loans_bp.route('/api/loans/<loan_id>/approve', methods=['POST'])
@token_required(allowed_roles=["HQ", "District"])
def approve_loan_api(loan_id):
    target_loan, _, _ = find_loan_by_id(loan_id)
    if not target_loan:
        return jsonify({"error": f"Loan ID '{loan_id}' not found"}), 404

    target_loan["status"] = "active"
    target_loan.setdefault("audit_trail", []).append({
        "action": "approved", "user": request.user.get("user"),
        "role": request.user.get("role"), "date": datetime.date.today().isoformat(),
        "notes": "Loan approved"
    })
    return jsonify({"loan_id": loan_id, "status": "active", "message": "Loan approved successfully"})


@loans_bp.route('/api/loans/<loan_id>/close', methods=['POST'])
@token_required()
def close_loan_api(loan_id):
    target_loan, _, _ = find_loan_by_id(loan_id)
    if not target_loan:
        return jsonify({"error": f"Loan ID '{loan_id}' not found"}), 404

    target_loan["status"] = "completed"
    target_loan.setdefault("audit_trail", []).append({
        "action": "closed", "user": request.user.get("user"),
        "role": request.user.get("role"), "date": datetime.date.today().isoformat(),
        "notes": "Loan closed"
    })
    return jsonify({"loan_id": loan_id, "status": "completed", "message": "Loan closed successfully"})


@loans_bp.route('/api/loans/<loan_id>/writeoff', methods=['POST'])
@token_required(allowed_roles=["HQ"])
def writeoff_loan_api(loan_id):
    target_loan, _, _ = find_loan_by_id(loan_id)
    if not target_loan:
        return jsonify({"error": f"Loan ID '{loan_id}' not found"}), 404

    target_loan["status"] = "written_off"
    target_loan.setdefault("audit_trail", []).append({
        "action": "written_off", "user": request.user.get("user"),
        "role": request.user.get("role"), "date": datetime.date.today().isoformat(),
        "notes": "Loan written off"
    })
    return jsonify({"loan_id": loan_id, "status": "written_off", "message": "Loan written off successfully"})


@loans_bp.route('/api/loans/<loan_id>/disburse', methods=['POST'])
@token_required(allowed_roles=["HQ", "District"])
def api_disburse_loan(loan_id):
    data = request.json or {}
    amount = float(data.get("amount", 0))
    method = data.get("method", "cash")

    if not amount or not method:
        return jsonify({"error": "amount and method are required"}), 400

    target_loan, _, _ = find_loan_by_id(loan_id)
    if not target_loan:
        return jsonify({"error": f"Loan ID '{loan_id}' not found"}), 404

    if target_loan.get("status") not in ["approved", "active"]:
        return jsonify({"error": "loan not in approved or active state"}), 409

    target_loan["status"] = "active"
    target_loan["disbursement_date"] = datetime.date.today().isoformat()
    target_loan["disbursement_method"] = method
    target_loan["disbursed_by"] = request.user.get("user")
    target_loan.setdefault("audit_trail", []).append({
        "action": "disbursed", "user": request.user.get("user"),
        "role": request.user.get("role"), "date": datetime.date.today().isoformat(),
        "notes": f"Disbursed ZMW {amount} via {method}"
    })

    return jsonify({"loan_id": loan_id, "status": "active", "message": "Loan disbursed successfully"})


@loans_bp.route('/api/loans/<loan_id>/schedule', methods=['GET'])
@token_required()
def api_get_loan_schedule(loan_id):
    return get_loan_schedule(loan_id)


@loans_bp.route('/api/loans/<loan_id>/restructure', methods=['POST'])
@token_required(allowed_roles=["HQ", "District"])
def api_restructure_loan(loan_id):
    return restructure_loan(loan_id)


@loans_bp.route('/api/loans/<loan_id>/repayments', methods=['POST'])
@token_required(allowed_roles=["Agent", "Village", "District", "HQ"])
def api_record_repayment(loan_id):
    data = request.json or {}
    amount = float(data.get("amount", 0))
    notes = data.get("notes", "Repayment recorded")
    return record_repayment_with_id(loan_id, amount, notes, request.user.get("user"))


@loans_bp.route('/loans/<loan_id>/schedule', methods=['GET'])
@token_required()
def get_loan_schedule(loan_id):
    target_loan, _, _ = find_loan_by_id(loan_id)
    if not target_loan:
        return jsonify({"error": f"Loan ID '{loan_id}' not found"}), 404

    return jsonify({
        "loan_id": loan_id,
        "loan_type": target_loan.get("loan_type"),
        "total_repayable": target_loan.get("total_repayable"),
        "balance_remaining": target_loan.get("balance_remaining"),
        "schedule": target_loan.get("schedule", [])
    })


@loans_bp.route('/loans/<loan_id>/restructure', methods=['POST'])
@token_required(allowed_roles=["HQ", "District"])
def restructure_loan(loan_id):
    data = request.json or {}
    new_term_days = data.get("new_term_days")
    new_installments = data.get("new_installments")
    requested_by = request.user.get("user")

    if not new_term_days or not new_installments:
        return jsonify({"error": "new_term_days and new_installments are required"}), 400

    target_loan, _, _ = find_loan_by_id(loan_id)
    if not target_loan:
        return jsonify({"error": f"Loan ID '{loan_id}' not found"}), 404

    if not target_loan.get("restructuring_allowed", False) and target_loan.get("loan_type") != "cash":
        return jsonify({"error": "Restructuring not allowed for this loan"}), 403

    schedule = target_loan.get("schedule", [])
    outstanding_principal = sum(r.get("due_principal", 0) for r in schedule) if schedule else target_loan.get("balance_remaining", 0)
    start_date = datetime.date.today().isoformat()
    interest_type = target_loan.get("interest_type", "Flat Rate")
    interest_rate = target_loan.get("interest_rate", 0)
    repayment_frequency = target_loan.get("repayment_frequency", "Monthly")

    if interest_type == "Flat Rate":
        new_schedule, new_total = generate_flat_schedule(outstanding_principal, interest_rate, new_term_days, new_installments, start_date, fees=0)
    else:
        new_schedule, new_total = generate_reducing_schedule(outstanding_principal, interest_rate, new_installments, start_date, repayment_frequency)

    target_loan["schedule"] = new_schedule
    target_loan["total_repayable"] = new_total
    target_loan["balance_remaining"] = new_total
    target_loan["status"] = "restructured"
    target_loan.setdefault("audit_trail", []).append({
        "action": "restructured", "user": requested_by,
        "role": request.user.get("role"), "date": datetime.date.today().isoformat(),
        "notes": f"Restructured to {new_installments} installments over {new_term_days} days"
    })

    return jsonify({
        "message": "Loan restructured successfully", "loan_id": loan_id,
        "new_total_repayable": new_total, "new_installments": new_installments,
        "status": "restructured"
    })


@loans_bp.route('/loan_products', methods=['GET'])
@token_required()
def get_loan_products():
    products = app_settings.get("loan_products", [])
    role = request.user.get("role")
    if role != "HQ":
        products = [p for p in products if p.get("approval_level") != "HQ"]
    return jsonify({"loan_products": products})


@loans_bp.route('/api/products', methods=['GET'])
@token_required()
def list_products():
    return jsonify({"products": app_settings.get('loan_products', [])})


@loans_bp.route('/api/products', methods=['POST'])
@token_required(allowed_roles=['HQ'])
def create_product():
    data = request.json or {}
    required_fields = ['name', 'type', 'min_amount', 'max_amount', 'interest_rate', 'interest_type', 'repayment_frequency']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    product_id = data.get('id', 'LP-' + uuid.uuid4().hex[:8].upper())
    product = {
        'id': product_id, 'name': data.get('name'), 'type': data.get('type'),
        'min_amount': float(data.get('min_amount', 0)), 'max_amount': float(data.get('max_amount', 0)),
        'interest_rate': float(data.get('interest_rate', 0)), 'interest_type': data.get('interest_type', 'Flat Rate'),
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


@loans_bp.route('/api/products/<product_id>', methods=['PUT'])
@token_required(allowed_roles=['HQ'])
def update_product(product_id):
    data = request.json or {}
    products = app_settings.get('loan_products', [])
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    product.update(data)
    return jsonify({'message': 'Product updated successfully', 'product': product})


@loans_bp.route('/api/products/<product_id>', methods=['DELETE'])
@token_required(allowed_roles=['HQ'])
def delete_product(product_id):
    products = app_settings.get('loan_products', [])
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    app_settings['loan_products'] = [p for p in products if p['id'] != product_id]
    return jsonify({'message': 'Product deleted successfully'})
