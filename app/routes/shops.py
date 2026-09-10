import datetime
import uuid
import jwt
from flask import Blueprint, request, jsonify, render_template
from app.auth import token_required, filter_hierarchy_for_user, get_user_profile
from app.config import SECRET_KEY
from app.state import users, structure, ensure_shop_data

shops_bp = Blueprint('shops', __name__)


@shops_bp.route('/')
def home():
    return render_template('index.html')


@shops_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if username in users and users[username]["password"] == password:
        user_profile = get_user_profile(username)
        token = jwt.encode({
            "user": username,
            "role": user_profile["role"],
            "district": user_profile.get("district"),
            "village": user_profile.get("village"),
            "shop": user_profile.get("shop"),
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=4)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({"token": token, "user": user_profile})
    return jsonify({"error": "Invalid username or password"}), 401


@shops_bp.route('/me', methods=['GET'])
@token_required()
def me():
    username = request.user.get("user")
    profile = get_user_profile(username)
    return jsonify({"user": profile})


@shops_bp.route('/shops', methods=['GET'])
@token_required()
def get_shops():
    user_tree = filter_hierarchy_for_user(request.user)
    shops_grouped = {}
    shops_flat = []

    for prov_name, prov_val in user_tree.items():
        if prov_name not in shops_grouped:
            shops_grouped[prov_name] = {}
        for dist_name, dist_val in prov_val.items():
            if dist_name not in shops_grouped[prov_name]:
                shops_grouped[prov_name][dist_name] = {}
            for vill_name, vill_val in dist_val.items():
                if vill_name not in shops_grouped[prov_name][dist_name]:
                    shops_grouped[prov_name][dist_name][vill_name] = []
                for shop_name, shop_data in vill_val.items():
                    farmers = shop_data.get("clients", {}).get("farmers", [])
                    fl_count = len(shop_data.get("clients", {}).get("fertilizer_loans", []))
                    af_count = len(shop_data.get("clients", {}).get("asset_finance", []))
                    cl_count = len(shop_data.get("clients", {}).get("cash_loans", []))

                    shop_item = {
                        "shop_id": shop_data.get("shop_id", ""),
                        "shop": shop_name,
                        "province": prov_name,
                        "district": dist_name,
                        "village": vill_name,
                        "agent": shop_data.get("agent", "Unassigned"),
                        "status": shop_data.get("status", "active"),
                        "max_loan_limit": shop_data.get("max_loan_limit", 10000),
                        "created_at": shop_data.get("created_at", "N/A"),
                        "farmer_count": len(farmers),
                        "total_loans_count": fl_count + af_count + cl_count,
                        "inventory": shop_data.get("inventory", [])
                    }

                    shops_grouped[prov_name][dist_name][vill_name].append(shop_item)
                    shops_flat.append(shop_item)

    return jsonify({"grouped": shops_grouped, "shops": shops_flat})


@shops_bp.route('/shops/add', methods=['POST'])
@token_required(allowed_roles=["HQ", "District"])
def add_shop():
    data = request.json or {}
    province = data.get("province")
    district = data.get("district")
    village = data.get("village")
    shop_name = data.get("shop")
    agent_username = data.get("agent", "Unassigned")
    max_loan_limit = float(data.get("max_loan_limit", 10000))

    if not province or not district or not village or not shop_name:
        return jsonify({"error": "province, district, village, and shop name are required"}), 400

    if province in structure and district in structure[province] and village in structure[province][district]:
        if shop_name in structure[province][district][village]:
            return jsonify({"error": f"Shop '{shop_name}' already exists in {village}, {district}"}), 400

    shop_data = ensure_shop_data(province, district, village, shop_name, agent_name=agent_username, max_limit=max_loan_limit)

    if agent_username in users:
        users[agent_username]["province"] = province
        users[agent_username]["district"] = district
        users[agent_username]["village"] = village
        users[agent_username]["shop"] = shop_name

    return jsonify({
        "message": f"Shop '{shop_name}' created successfully in {village}, {district}",
        "shop": {
            "shop_id": shop_data.get("shop_id", ""),
            "shop": shop_name, "province": province, "district": district,
            "village": village, "agent": agent_username, "status": "active",
            "max_loan_limit": max_loan_limit
        }
    })


@shops_bp.route('/shops/detail/<shop_name>', methods=['GET'])
@token_required()
def get_shop_detail(shop_name):
    for prov_name in structure:
        for dist_name in structure[prov_name]:
            for vill_name in structure[prov_name][dist_name]:
                if shop_name in structure[prov_name][dist_name][vill_name]:
                    shop_data = structure[prov_name][dist_name][vill_name][shop_name]
                    return jsonify({
                        "shop_id": shop_data.get("shop_id", ""),
                        "shop": shop_name, "province": prov_name, "district": dist_name,
                        "village": vill_name, "agent": shop_data.get("agent"),
                        "status": shop_data.get("status", "active"),
                        "max_loan_limit": shop_data.get("max_loan_limit", 10000),
                        "created_at": shop_data.get("created_at", "N/A"),
                        "inventory": shop_data.get("inventory", []),
                        "clients": shop_data.get("clients", {})
                    })
    return jsonify({"error": f"Shop '{shop_name}' not found"}), 404


@shops_bp.route('/shops/settings', methods=['POST'])
@token_required(allowed_roles=["HQ", "District"])
def update_shop_settings():
    data = request.json or {}
    shop_name = data.get("shop")
    status = data.get("status")
    agent = data.get("agent")
    max_loan_limit = data.get("max_loan_limit")

    if not shop_name:
        return jsonify({"error": "shop name is required"}), 400

    target_shop = None
    for prov_name in structure:
        for dist_name in structure[prov_name]:
            for vill_name in structure[prov_name][dist_name]:
                if shop_name in structure[prov_name][dist_name][vill_name]:
                    target_shop = structure[prov_name][dist_name][vill_name][shop_name]
                    break

    if not target_shop:
        return jsonify({"error": f"Shop '{shop_name}' not found"}), 404

    if status:
        target_shop["status"] = status
    if agent:
        target_shop["agent"] = agent
    if max_loan_limit is not None:
        target_shop["max_loan_limit"] = float(max_loan_limit)

    return jsonify({"message": f"Settings for '{shop_name}' updated successfully", "shop_data": target_shop})


@shops_bp.route('/shops/allocate_inventory', methods=['POST'])
@token_required(allowed_roles=["HQ", "District"])
def allocate_inventory():
    data = request.json or {}
    shop_name = data.get("shop")
    shop_id = data.get("shop_id")
    item_name = data.get("item_name")
    quantity = int(data.get("quantity", 0))
    unit = data.get("unit", "units")

    if not shop_name or not item_name or quantity <= 0:
        return jsonify({"error": "shop, item_name, and positive quantity are required"}), 400

    target_shop = None
    resolved_shop_name = shop_name

    if shop_id:
        for prov_name in structure:
            for dist_name in structure[prov_name]:
                for vill_name in structure[prov_name][dist_name]:
                    for s_name, s_data in structure[prov_name][dist_name][vill_name].items():
                        if s_data.get("shop_id") == shop_id:
                            target_shop = s_data
                            resolved_shop_name = s_name
                            break
                    if target_shop:
                        break
                if target_shop:
                    break
            if target_shop:
                break
    else:
        for prov_name in structure:
            for dist_name in structure[prov_name]:
                for vill_name in structure[prov_name][dist_name]:
                    if shop_name in structure[prov_name][dist_name][vill_name]:
                        target_shop = structure[prov_name][dist_name][vill_name][shop_name]
                        break

    if not target_shop:
        return jsonify({"error": f"Shop '{shop_name or shop_id}' not found"}), 404

    inventory = target_shop.get("inventory", [])
    existing_item = next((item for item in inventory if item["item_name"].lower() == item_name.lower()), None)

    if existing_item:
        existing_item["quantity"] += quantity
    else:
        inventory.append({"item_name": item_name, "quantity": quantity, "unit": unit})
        target_shop["inventory"] = inventory

    return jsonify({
        "message": f"Allocated {quantity} {unit} of '{item_name}' to {resolved_shop_name}",
        "inventory": target_shop["inventory"]
    })
