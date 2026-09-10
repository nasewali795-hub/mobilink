import uuid
import datetime
from flask import Blueprint, request, jsonify
from app.auth import token_required
from app.state import users, structure, hq_warehouse, app_settings

hq_bp = Blueprint('hq', __name__)


@hq_bp.route('/hq/settings', methods=['GET'])
@token_required(allowed_roles=["HQ"])
def hq_get_settings():
    return jsonify(app_settings)


@hq_bp.route('/hq/settings', methods=['POST'])
@token_required(allowed_roles=["HQ"])
def hq_update_settings():
    data = request.json or {}
    for section in ["system", "loan_rules", "limits", "loan_products", "features", "templates"]:
        if section in data and isinstance(data[section], dict):
            if section not in app_settings:
                app_settings[section] = {}
            for key, value in data[section].items():
                app_settings[section][key] = value
    return jsonify({"message": "HQ settings updated successfully", "settings": app_settings})


@hq_bp.route('/hq/agents', methods=['POST'])
@token_required(allowed_roles=["HQ"])
def hq_create_agent():
    data = request.json or {}
    username = data.get("username")
    name = data.get("name")
    password = data.get("password")
    province = data.get("province", "")
    district = data.get("district", "")
    village = data.get("village", "")

    if not username or not name or not password:
        return jsonify({"error": "username, name and password are required"}), 400

    if username in users:
        return jsonify({"error": f"Agent username '{username}' already exists"}), 400

    users[username] = {
        "password": password, "role": "Agent", "name": name,
        "province": province, "district": district, "village": village, "shop": None
    }

    return jsonify({"message": f"Agent '{username}' created successfully", "agent": {"username": username, "name": name, "role": "Agent"}})


@hq_bp.route('/hq/warehouse', methods=['GET'])
@token_required(allowed_roles=["HQ"])
def get_hq_warehouse():
    return jsonify({
        "fertilizers": hq_warehouse.get("fertilizers", []),
        "seeds": hq_warehouse.get("seeds", []),
        "pesticides": hq_warehouse.get("pesticides", []),
        "assets": hq_warehouse.get("assets", []),
        "cash_pool": hq_warehouse.get("cash_pool", {}),
        "distribution_history": hq_warehouse.get("distribution_history", [])
    })


@hq_bp.route('/hq/warehouse/stock', methods=['POST'])
@token_required(allowed_roles=["HQ"])
def add_hq_warehouse_stock():
    data = request.json or {}
    category = data.get("category", "fertilizers")
    item_name = data.get("item_name")
    quantity = int(data.get("quantity", 0))
    unit = data.get("unit", "bags")
    batch_no = data.get("batch_no", "")
    expiry_date = data.get("expiry_date", "")
    purchase_cost = data.get("purchase_cost")
    financing_terms = data.get("financing_terms", "")
    asset_status = data.get("status", "available")

    if not item_name or quantity <= 0:
        return jsonify({"error": "item_name and positive quantity are required"}), 400

    if category not in hq_warehouse:
        hq_warehouse[category] = []

    new_item = {"item_name": item_name, "quantity": quantity, "unit": unit}

    if category in ["fertilizers", "seeds", "pesticides"]:
        new_item["batch_no"] = batch_no
        new_item["expiry_date"] = expiry_date
    elif category == "assets":
        new_item["purchase_cost"] = purchase_cost
        new_item["financing_terms"] = financing_terms
        new_item["status"] = asset_status

    existing_item = next((item for item in hq_warehouse[category] if item["item_name"].lower() == item_name.lower()), None)
    if existing_item:
        existing_item["quantity"] += quantity
        response_item = existing_item
    else:
        hq_warehouse[category].append(new_item)
        response_item = new_item

    inv_section = app_settings.setdefault("inventory", {})
    inv_items = inv_section.setdefault("items", {})
    item_key = item_name.lower().replace(" ", "_")
    if item_key not in inv_items:
        catalog = inv_section.setdefault("master_catalog", [])
        catalog_item = next((c for c in catalog if c["name"].lower() == item_name.lower()), None)
        inv_items[item_key] = {
            "name": item_name, "category": category.rstrip("s"), "unit": unit,
            "hq_stock": 0, "allocated_to_shops": 0, "available_stock": 0,
            "cost_price": (catalog_item or {}).get("cost_price", 0),
            "loan_value": (catalog_item or {}).get("loan_value", 0),
            "selling_price": (catalog_item or {}).get("selling_price", 0),
            "supplier": (catalog_item or {}).get("supplier", ""),
            "low_stock_threshold": (catalog_item or {}).get("low_stock_threshold", 100)
        }
    inv_item = inv_items[item_key]
    inv_item["hq_stock"] = inv_item.get("hq_stock", 0) + quantity
    inv_item["available_stock"] = inv_item.get("available_stock", 0) + quantity

    transactions = inv_section.setdefault("transactions", [])
    transactions.append({
        "id": f"tx-{uuid.uuid4().hex[:8]}", "date": datetime.date.today().isoformat(),
        "item_id": item_key, "item_name": item_name, "type": "purchase",
        "quantity": quantity, "unit": unit, "notes": "Added via warehouse stock",
        "created_by": request.user.get("user", "system"),
        "created_by_role": request.user.get("role", "unknown"),
        "hq_stock_after": inv_item.get("hq_stock", 0),
        "available_stock_after": inv_item.get("available_stock", 0),
        "allocated_to_shops_after": inv_item.get("allocated_to_shops", 0)
    })
    inv_section["items"] = inv_items

    return jsonify({"message": f"Added {quantity} {unit} of '{item_name}' to HQ warehouse ({category})", "item": response_item})


@hq_bp.route('/hq/warehouse/allocate', methods=['POST'])
@token_required(allowed_roles=["HQ"])
def allocate_hq_warehouse_stock():
    data = request.json or {}
    shop_name = data.get("shop")
    shop_id = data.get("shop_id")
    item_name = data.get("item_name")
    quantity = int(data.get("quantity", 0))
    unit = data.get("unit", "bags")
    category = data.get("category", "fertilizers")

    if not shop_name or not item_name or quantity <= 0:
        return jsonify({"error": "shop, item_name, and positive quantity are required"}), 400

    target_shop = None
    target_province = target_district = target_village = resolved_shop_name = shop_name

    if shop_id:
        for prov_name in structure:
            for dist_name in structure[prov_name]:
                for vill_name in structure[prov_name][dist_name]:
                    for s_name, s_data in structure[prov_name][dist_name][vill_name].items():
                        if s_data.get("shop_id") == shop_id:
                            target_shop = s_data
                            target_province, target_district, target_village, resolved_shop_name = prov_name, dist_name, vill_name, s_name
                            break
                    if target_shop: break
                if target_shop: break
            if target_shop: break
    else:
        for prov_name in structure:
            for dist_name in structure[prov_name]:
                for vill_name in structure[prov_name][dist_name]:
                    if shop_name in structure[prov_name][dist_name][vill_name]:
                        target_shop = structure[prov_name][dist_name][vill_name][shop_name]
                        target_province, target_district, target_village = prov_name, dist_name, vill_name
                        break

    if not target_shop:
        return jsonify({"error": f"Shop '{shop_name or shop_id}' not found"}), 404

    warehouse_items = hq_warehouse.get(category, [])
    warehouse_item = next((item for item in warehouse_items if item["item_name"].lower() == item_name.lower()), None)

    if not warehouse_item:
        return jsonify({"error": f"Item '{item_name}' not found in HQ warehouse ({category})"}), 404

    if warehouse_item["quantity"] < quantity:
        return jsonify({"error": f"Insufficient stock. Available: {warehouse_item['quantity']} {warehouse_item['unit']}, Requested: {quantity} {unit}", "available": warehouse_item["quantity"]}), 400

    warehouse_item["quantity"] -= quantity

    shop_inventory = target_shop.get("inventory", [])
    existing_item = next((item for item in shop_inventory if item["item_name"].lower() == item_name.lower()), None)
    if existing_item:
        existing_item["quantity"] += quantity
    else:
        shop_inventory.append({"item_name": item_name, "quantity": quantity, "unit": unit})
    target_shop["inventory"] = shop_inventory

    distribution_record = {
        "date": datetime.date.today().isoformat(), "shop": resolved_shop_name,
        "shop_id": shop_id or (target_shop.get("shop_id") if target_shop else ""),
        "province": target_province, "district": target_district, "village": target_village,
        "item": item_name, "quantity": quantity, "unit": unit, "type": category.rstrip('s')
    }
    hq_warehouse["distribution_history"].insert(0, distribution_record)

    return jsonify({"message": f"Allocated {quantity} {unit} of '{item_name}' from HQ warehouse to {resolved_shop_name}", "remaining_hq_stock": warehouse_item["quantity"], "distribution": distribution_record})


@hq_bp.route('/hq/warehouse/distribution', methods=['GET'])
@token_required(allowed_roles=["HQ"])
def get_distribution_history():
    return jsonify({"distribution_history": hq_warehouse.get("distribution_history", [])})


@hq_bp.route('/hq/warehouse/cash', methods=['POST'])
@token_required(allowed_roles=["HQ"])
def update_cash_pool():
    data = request.json or {}
    total_cash = float(data.get("total_cash", 0))
    allocated_to_shops = float(data.get("allocated_to_shops", 0))
    reserved = float(data.get("reserved", 0))
    available_for_disbursement = float(data.get("available_for_disbursement", total_cash - allocated_to_shops - reserved))

    hq_warehouse["cash_pool"] = {
        "total_cash": total_cash, "currency": "ZMW",
        "allocated_to_shops": allocated_to_shops, "reserved": reserved,
        "available_for_disbursement": available_for_disbursement
    }

    return jsonify({"message": "Cash pool updated successfully", "cash_pool": hq_warehouse["cash_pool"]})
