import datetime
import copy
from app.config import APP_SETTINGS, HQ_WAREHOUSE

users = {
    "hq_admin": {"password": "hq123", "role": "HQ", "name": "Headquarters Admin"},
    "agent1": {"password": "pass123", "role": "Agent", "shop": "ShopA", "name": "Agent Joseph (Shop A)"},
    "agent2": {"password": "pass456", "role": "Agent", "shop": "ShopB", "name": "Agent Mary (Shop B)"},
    "agent3": {"password": "pass789", "role": "Agent", "shop": "ShopC", "name": "Agent Peter (Shop C)"}
}

structure = {}
next_shop_id = 1
hq_warehouse = copy.deepcopy(HQ_WAREHOUSE)
app_settings = copy.deepcopy(APP_SETTINGS)


def assign_missing_shop_ids():
    global next_shop_id
    for prov_name in structure:
        for dist_name in structure[prov_name]:
            for vill_name in structure[prov_name][dist_name]:
                for shop_name, shop_data in structure[prov_name][dist_name][vill_name].items():
                    if not shop_data.get("shop_id"):
                        shop_data["shop_id"] = f"SHOP-{next_shop_id:04d}"
                        next_shop_id += 1


def seed_sample_data():
    structure.clear()
    structure["Eastern Province"] = {
        "DistrictA": {
            "VillageX": {
                "ShopA": {
                    "agent": "agent1", "status": "active", "max_loan_limit": 15000,
                    "created_at": "2026-01-01",
                    "inventory": [
                        {"item_name": "NPK + Urea Compound (Bags)", "quantity": 100, "unit": "bags"},
                        {"item_name": "Solar Water Pump Kit", "quantity": 15, "unit": "kits"},
                        {"item_name": "Motorized Maize Sheller", "quantity": 5, "unit": "units"}
                    ],
                    "clients": {
                        "farmers": [
                            {"id": "c-101", "name": "Chileshe Banda", "phone": "+260971112233", "nrc": "112233/44/1", "shop": "ShopA", "village": "VillageX", "district": "DistrictA", "province": "Eastern Province", "registered_at": "2026-01-15"}
                        ],
                        "fertilizer_loans": [], "asset_finance": [], "cash_loans": []
                    }
                }
            },
            "VillageY": {
                "ShopB": {
                    "agent": "agent2", "status": "active", "max_loan_limit": 10000,
                    "created_at": "2026-01-10",
                    "inventory": [
                        {"item_name": "Urea Starter Pack (Bags)", "quantity": 40, "unit": "bags"},
                        {"item_name": "Treadle Water Pump", "quantity": 10, "unit": "kits"}
                    ],
                    "clients": {
                        "farmers": [
                            {"id": "c-103", "name": "Mwamba Tembo", "phone": "+260973334455", "nrc": "334455/66/1", "shop": "ShopB", "village": "VillageY", "district": "DistrictA", "province": "Eastern Province", "registered_at": "2026-02-10"}
                        ],
                        "fertilizer_loans": [], "asset_finance": [], "cash_loans": []
                    }
                }
            }
        }
    }
    structure["Central Province"] = {
        "Kabwe": {
            "Village-1": {
                "ShopC": {
                    "agent": "agent3", "status": "active", "max_loan_limit": 10000,
                    "created_at": "2026-02-01",
                    "inventory": [
                        {"item_name": "Compound D", "quantity": 60, "unit": "bags"},
                        {"item_name": "Basal Top Dressing", "quantity": 30, "unit": "bags"}
                    ],
                    "clients": {
                        "farmers": [
                            {"id": "c-201", "name": "Kasonke Mulenga", "phone": "+260974445566", "nrc": "445566/77/1", "shop": "ShopC", "village": "Village-1", "district": "Kabwe", "province": "Central Province", "registered_at": "2026-03-05"}
                        ],
                        "fertilizer_loans": [], "asset_finance": [], "cash_loans": []
                    }
                }
            }
        }
    }


def ensure_shop_data(province, district, village, shop, agent_name="", status="active", max_limit=10000):
    global next_shop_id
    if province not in structure:
        structure[province] = {}
    if district not in structure[province]:
        structure[province][district] = {}
    if village not in structure[province][district]:
        structure[province][district][village] = {}
    if shop not in structure[province][district][village]:
        structure[province][district][village][shop] = {
            "shop_id": f"SHOP-{next_shop_id:04d}",
            "agent": agent_name,
            "status": status,
            "max_loan_limit": max_limit,
            "created_at": datetime.date.today().isoformat(),
            "inventory": [],
            "clients": {
                "farmers": [],
                "fertilizer_loans": [],
                "asset_finance": [],
                "cash_loans": []
            }
        }
        next_shop_id += 1
    return structure[province][district][village][shop]


seed_sample_data()
assign_missing_shop_ids()
