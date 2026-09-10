import uuid
import datetime
from flask import Blueprint, request, jsonify
from app.auth import token_required
from app.state import structure, app_settings
from app.utils import find_shop_by_id

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory/catalog', methods=['GET'])
@token_required()
def get_inventory_catalog():
    catalog = app_settings.get("inventory", {}).get("master_catalog", [])
    return jsonify({"catalog": catalog})


@inventory_bp.route('/inventory/items', methods=['GET'])
@token_required()
def get_inventory_items():
    items = app_settings.get("inventory", {}).get("items", {})
    items_list = []
    for item_id, item in items.items():
        items_list.append({
            "item_id": item_id, "name": item.get("name"), "category": item.get("category"),
            "unit": item.get("unit"), "hq_stock": item.get("hq_stock", 0),
            "allocated_to_shops": item.get("allocated_to_shops", 0),
            "available_stock": item.get("available_stock", item.get("hq_stock", 0) - item.get("allocated_to_shops", 0)),
            "cost_price": item.get("cost_price"), "loan_value": item.get("loan_value"),
            "selling_price": item.get("selling_price"), "supplier": item.get("supplier"),
            "expiry_date": item.get("expiry_date"), "batch_number": item.get("batch_number"),
            "low_stock_threshold": item.get("low_stock_threshold", 100)
        })
    return jsonify({"items": items_list})


@inventory_bp.route('/inventory/transactions', methods=['GET'])
@token_required()
def get_inventory_transactions():
    transactions = app_settings.get("inventory", {}).get("transactions", [])
    item_id = request.args.get("item_id")
    tx_type = request.args.get("type")
    shop_id = request.args.get("shop_id")

    filtered = transactions
    if item_id:
        filtered = [t for t in filtered if t.get("item_id") == item_id]
    if tx_type:
        filtered = [t for t in filtered if t.get("type") == tx_type]
    if shop_id:
        filtered = [t for t in filtered if t.get("shop_id") == shop_id]

    filtered = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)
    return jsonify({"transactions": filtered})


@inventory_bp.route('/inventory/shop/<shop_id>', methods=['GET'])
@token_required()
def get_shop_inventory(shop_id):
    target_shop, _, _, _, _ = find_shop_by_id(shop_id)

    if not target_shop:
        return jsonify({"error": f"Shop '{shop_id}' not found"}), 404

    inventory = target_shop.get("inventory", [])
    loan_inventory = []
    for cat in ["fertilizer_loans", "asset_finance", "cash_loans"]:
        for loan in target_shop.get("clients", {}).get(cat, []):
            if loan.get("status") in ["active", "pending_approval"]:
                loan_inventory.append({
                    "loan_id": loan.get("id"),
                    "farmer_name": loan.get("farmer_name") or loan.get("name"),
                    "loan_type": loan.get("loan_type"),
                    "item": loan.get("fertilizer_type") or loan.get("asset_type"),
                    "quantity": loan.get("fertilizer_bags") or loan.get("quantity", 1),
                    "unit": "bags" if loan.get("loan_type") == "fertilizer" else "units",
                    "status": loan.get("status")
                })

    return jsonify({
        "shop_id": shop_id,
        "shop_name": target_shop.get("agent", "Unknown"),
        "inventory": inventory,
        "loan_linked_inventory": loan_inventory,
        "total_physical_stock": sum(i.get("quantity", 0) for i in inventory),
        "total_loaned_out": sum(i.get("quantity", 0) for i in loan_inventory)
    })


@inventory_bp.route('/inventory/transfer', methods=['POST'])
@token_required(allowed_roles=["HQ", "District"])
def transfer_inventory():
    data = request.json or {}
    shop_id = data.get("shop_id")
    shop_name = data.get("shop_name")
    item_id = data.get("item_id")
    item_name = data.get("item_name")
    quantity = int(data.get("quantity", 0))
    transaction_type = data.get("type", "transfer_out")
    notes = data.get("notes", "")

    if not item_name or quantity <= 0:
        return jsonify({"error": "item_name and positive quantity are required"}), 400

    catalog = app_settings.get("inventory", {}).get("master_catalog", [])
    catalog_item = next((c for c in catalog if c["name"].lower() == item_name.lower()), None)
    if not catalog_item:
        return jsonify({"error": f"Item '{item_name}' not found in catalog"}), 404

    inv_items = app_settings.setdefault("inventory", {}).setdefault("items", {})
    item_key = item_id or item_name.lower().replace(" ", "_")
    if item_key not in inv_items:
        inv_items[item_key] = {
            "name": item_name, "category": catalog_item.get("category", "general"),
            "unit": catalog_item.get("unit", "units"),
            "hq_stock": 0, "allocated_to_shops": 0, "available_stock": 0,
            "cost_price": catalog_item.get("cost_price", 0),
            "loan_value": catalog_item.get("loan_value", 0),
            "selling_price": catalog_item.get("selling_price", 0),
            "supplier": catalog_item.get("supplier", ""),
            "low_stock_threshold": catalog_item.get("low_stock_threshold", 100)
        }

    inv_item = inv_items[item_key]

    if transaction_type == "purchase":
        inv_item["hq_stock"] = inv_item.get("hq_stock", 0) + quantity
        inv_item["available_stock"] = inv_item.get("available_stock", 0) + quantity
    elif transaction_type == "transfer_out":
        available = inv_item.get("available_stock", 0)
        if available < quantity:
            return jsonify({"error": f"Insufficient available stock. Available: {available}, Requested: {quantity}"}), 400
        inv_item["available_stock"] -= quantity
        inv_item["allocated_to_shops"] = inv_item.get("allocated_to_shops", 0) + quantity
    elif transaction_type == "return":
        inv_item["hq_stock"] = inv_item.get("hq_stock", 0) + quantity
        inv_item["available_stock"] = inv_item.get("available_stock", 0) + quantity
        inv_item["allocated_to_shops"] = max(0, inv_item.get("allocated_to_shops", 0) - quantity)
    elif transaction_type in ["damaged", "expired", "adjustment"]:
        hq_stock = inv_item.get("hq_stock", 0)
        if hq_stock < quantity:
            return jsonify({"error": f"Insufficient HQ stock for adjustment. Available: {hq_stock}, Requested: {quantity}"}), 400
        inv_item["hq_stock"] -= quantity
        inv_item["available_stock"] = max(0, inv_item.get("available_stock", 0) - quantity)
    else:
        return jsonify({"error": f"Unknown transaction type: {transaction_type}"}), 400

    target_shop = None
    if shop_id or shop_name:
        for prov_name in structure:
            for dist_name in structure[prov_name]:
                for vill_name in structure[prov_name][dist_name]:
                    for s_name, s_data in structure[prov_name][dist_name][vill_name].items():
                        if (shop_id and s_data.get("shop_id") == shop_id) or (shop_name and s_name == shop_name):
                            target_shop = s_data
                            break
                    if target_shop: break
                if target_shop: break
            if target_shop: break

    if target_shop and transaction_type == "transfer_out":
        shop_inventory = target_shop.get("inventory", [])
        existing = next((i for i in shop_inventory if i["item_name"].lower() == item_name.lower()), None)
        if existing:
            existing["quantity"] += quantity
        else:
            shop_inventory.append({"item_name": item_name, "quantity": quantity, "unit": inv_item.get("unit", "units")})
        target_shop["inventory"] = shop_inventory

    tx = {
        "id": f"tx-{uuid.uuid4().hex[:8]}", "date": datetime.date.today().isoformat(),
        "item_id": item_key, "item_name": item_name, "type": transaction_type,
        "quantity": quantity, "unit": inv_item.get("unit", "units"),
        "shop_id": shop_id, "shop_name": shop_name, "notes": notes,
        "created_by": request.user.get("user", "system"),
        "created_by_role": request.user.get("role", "unknown"),
        "hq_stock_after": inv_item.get("hq_stock", 0),
        "available_stock_after": inv_item.get("available_stock", 0),
        "allocated_to_shops_after": inv_item.get("allocated_to_shops", 0)
    }

    transactions = app_settings.setdefault("inventory", {}).setdefault("transactions", [])
    transactions.append(tx)
    app_settings["inventory"]["items"] = inv_items

    return jsonify({
        "message": f"Transaction '{transaction_type}' recorded for {quantity} {inv_item.get('unit', 'units')} of '{item_name}'",
        "transaction": tx,
        "current_stock": {
            "hq_stock": inv_item.get("hq_stock", 0),
            "allocated_to_shops": inv_item.get("allocated_to_shops", 0),
            "available_stock": inv_item.get("available_stock", 0)
        }
    })


@inventory_bp.route('/inventory/adjust', methods=['POST'])
@token_required(allowed_roles=["HQ", "District"])
def adjust_inventory():
    data = request.json or {}
    item_id = data.get("item_id")
    item_name = data.get("item_name")
    quantity_change = int(data.get("quantity_change", 0))
    reason = data.get("reason", "Manual adjustment")

    if not item_name or quantity_change == 0:
        return jsonify({"error": "item_name and non-zero quantity_change are required"}), 400

    inv_items = app_settings.get("inventory", {}).get("items", {})
    item_key = item_id or item_name.lower().replace(" ", "_")

    if item_key not in inv_items:
        return jsonify({"error": f"Item '{item_name}' not found"}), 404

    inv_item = inv_items[item_key]
    old_hq = inv_item.get("hq_stock", 0)
    old_avail = inv_item.get("available_stock", 0)

    inv_item["hq_stock"] = max(0, old_hq + quantity_change)
    inv_item["available_stock"] = max(0, old_avail + quantity_change)

    tx = {
        "id": f"tx-{uuid.uuid4().hex[:8]}", "date": datetime.date.today().isoformat(),
        "item_id": item_key, "item_name": item_name, "type": "adjustment",
        "quantity": abs(quantity_change), "quantity_change": quantity_change,
        "unit": inv_item.get("unit", "units"), "reason": reason,
        "created_by": request.user.get("user", "system"),
        "created_by_role": request.user.get("role", "unknown"),
        "hq_stock_after": inv_item.get("hq_stock", 0),
        "available_stock_after": inv_item.get("available_stock", 0),
        "allocated_to_shops_after": inv_item.get("allocated_to_shops", 0)
    }

    transactions = app_settings.setdefault("inventory", {}).setdefault("transactions", [])
    transactions.append(tx)
    app_settings["inventory"]["items"] = inv_items

    return jsonify({
        "message": f"Adjusted '{item_name}' by {quantity_change:+d}",
        "transaction": tx,
        "current_stock": {
            "hq_stock": inv_item.get("hq_stock", 0),
            "available_stock": inv_item.get("available_stock", 0),
            "allocated_to_shops": inv_item.get("allocated_to_shops", 0)
        }
    })


@inventory_bp.route('/inventory/alerts', methods=['GET'])
@token_required()
def get_inventory_alerts():
    items = app_settings.get("inventory", {}).get("items", {})
    alerts = []
    expiry_days = app_settings.get("limits", {}).get("expiry_warning_days", 90)
    today = datetime.date.today()

    for item_id, item in items.items():
        available = item.get("available_stock", 0)
        threshold = item.get("low_stock_threshold", 100)

        if available <= threshold:
            alerts.append({
                "type": "low_stock", "item_id": item_id, "item_name": item.get("name"),
                "message": f"Low stock: {available} {item.get('unit', 'units')} remaining (threshold: {threshold})",
                "severity": "high" if available == 0 else "medium",
                "current_value": available, "threshold": threshold
            })

    return jsonify({"alerts": alerts})
