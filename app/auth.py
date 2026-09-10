import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from app.config import SECRET_KEY
from app.state import users, structure


def verify_token(token):
    if not token:
        return None
    if token.startswith("Bearer "):
        token = token[7:]
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except Exception:
        return None


def token_required(allowed_roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            decoded = verify_token(auth_header)
            if not decoded:
                return jsonify({"error": "Unauthorized or invalid token"}), 401
            user_role = decoded.get("role")
            if allowed_roles and user_role not in allowed_roles:
                return jsonify({"error": f"Forbidden - user with role '{user_role}' cannot access this endpoint"}), 403
            request.user = decoded
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_user_profile(username):
    user_info = users.get(username, {}).copy()
    user_info["username"] = username
    user_info.pop("password", None)
    return user_info


def filter_hierarchy_for_user(user_decoded):
    role = user_decoded.get("role")
    username = user_decoded.get("user")
    user_meta = users.get(username, {})

    if role == "HQ":
        return structure

    filtered = {}
    if role == "District":
        user_district = user_meta.get("district")
        for prov_name, prov_val in structure.items():
            dist_match = {}
            for dist_name, dist_val in prov_val.items():
                if dist_name == user_district:
                    dist_match[dist_name] = dist_val
            if dist_match:
                filtered[prov_name] = dist_match
        return filtered

    if role == "Village":
        user_district = user_meta.get("district")
        user_village = user_meta.get("village")
        for prov_name, prov_val in structure.items():
            dist_match = {}
            for dist_name, dist_val in prov_val.items():
                if dist_name == user_district:
                    vill_match = {}
                    for vill_name, vill_val in dist_val.items():
                        if vill_name == user_village:
                            vill_match[vill_name] = vill_val
                    if vill_match:
                        dist_match[dist_name] = vill_match
            if dist_match:
                filtered[prov_name] = dist_match
        return filtered

    if role == "Agent":
        user_shop = user_meta.get("shop")
        for prov_name, prov_val in structure.items():
            dist_match = {}
            for dist_name, dist_val in prov_val.items():
                vill_match = {}
                for vill_name, vill_val in dist_val.items():
                    shop_match = {}
                    for shop_name, shop_val in vill_val.items():
                        if shop_name == user_shop:
                            shop_match[shop_name] = shop_val
                    if shop_match:
                        vill_match[vill_name] = shop_match
                if vill_match:
                    dist_match[dist_name] = vill_match
            if dist_match:
                filtered[prov_name] = dist_match
        return filtered

    return {}
