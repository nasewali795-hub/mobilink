import uuid
import datetime
from flask import Blueprint, request, jsonify
from app.auth import token_required, filter_hierarchy_for_user
from app.state import users, structure, ensure_shop_data
from app.utils import find_shop_by_name

clients_bp = Blueprint('clients', __name__)


@clients_bp.route('/add_client', methods=['POST'])
@token_required(allowed_roles=["Agent", "Village", "District", "HQ"])
def add_client():
    decoded = request.user
    agent_username = decoded["user"]
    agent_info = users.get(agent_username, {})

    data = request.json or {}
    province = data.get("province", agent_info.get("province", "Eastern Province"))
    district = data.get("district", agent_info.get("district", "DistrictA"))
    village = data.get("village", agent_info.get("village", "VillageX"))
    shop = data.get("shop", agent_info.get("shop", "ShopA"))
    client_name = data.get("client_name")

    if not client_name:
        return jsonify({"error": "client_name is required"}), 400

    shop_data = ensure_shop_data(province, district, village, shop, agent_username)

    existing = next((c for c in shop_data["clients"]["farmers"] if c["name"].lower() == client_name.lower()), None)
    if existing:
        return jsonify({"message": f"Client '{client_name}' already exists in {shop}", "client": existing}), 200

    client_record = {
        "id": f"c-{uuid.uuid4().hex[:6]}",
        "name": client_name,
        "phone": data.get("phone", "N/A"),
        "nrc": data.get("nrc", "N/A"),
        "shop": shop,
        "village": village,
        "district": district,
        "province": province,
        "registered_at": datetime.date.today().isoformat()
    }

    shop_data["clients"]["farmers"].append(client_record)
    return jsonify({"message": f"Client {client_name} added to {shop} farmers database", "client": client_record})


@clients_bp.route('/clients', methods=['GET'])
@token_required()
def get_clients():
    user_tree = filter_hierarchy_for_user(request.user)
    farmers_list = []
    loans_list = []

    for prov_name, prov_val in user_tree.items():
        for dist_name, dist_val in prov_val.items():
            for vill_name, vill_val in dist_val.items():
                for shop_name, shop_val in vill_val.items():
                    clients = shop_val.get("clients", {})
                    for farmer in clients.get("farmers", []):
                        farmers_list.append(farmer)
                    for cat in ["fertilizer_loans", "asset_finance", "cash_loans"]:
                        for loan in clients.get(cat, []):
                            loans_list.append(loan)

    return jsonify({"farmers": farmers_list, "loans": loans_list})


@clients_bp.route('/hierarchy', methods=['GET'])
@token_required()
def get_hierarchy():
    user_tree = filter_hierarchy_for_user(request.user)
    return jsonify({"hierarchy": user_tree})
