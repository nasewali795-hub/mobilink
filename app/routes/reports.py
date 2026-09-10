import datetime
from flask import Blueprint, request, jsonify
from app.auth import token_required, filter_hierarchy_for_user
from app.utils import round_to_2

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports/portfolio', methods=['GET'])
@token_required(allowed_roles=["HQ", "District"])
def portfolio_report():
    user_tree = filter_hierarchy_for_user(request.user)
    summary = {
        "total_loans": 0, "total_principal": 0.0, "total_outstanding": 0.0,
        "by_status": {}, "by_type": {}, "par30": 0, "overdue_count": 0
    }

    today = datetime.date.today()

    for prov_name, prov_val in user_tree.items():
        for dist_name, dist_val in prov_val.items():
            for vill_name, vill_val in dist_val.items():
                for shop_name, shop_val in vill_val.items():
                    clients = shop_val.get("clients", {})
                    for cat in ["cash_loans", "fertilizer_loans", "asset_finance"]:
                        for loan in clients.get(cat, []):
                            summary["total_loans"] += 1
                            summary["total_principal"] = round_to_2(summary["total_principal"] + loan.get("loan_amount", 0))
                            summary["total_outstanding"] = round_to_2(summary["total_outstanding"] + loan.get("balance_remaining", 0))

                            status = loan.get("status", "unknown")
                            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

                            ltype = loan.get("loan_type", cat)
                            summary["by_type"][ltype] = summary["by_type"].get(ltype, 0) + 1

                            schedule = loan.get("schedule", [])
                            for row in schedule:
                                if row.get("status") == "due" and row.get("due_date"):
                                    due = datetime.date.fromisoformat(row["due_date"])
                                    if due < today - datetime.timedelta(days=30):
                                        summary["par30"] += 1
                                        break
                            for row in schedule:
                                if row.get("status") == "due" and row.get("due_date"):
                                    due = datetime.date.fromisoformat(row["due_date"])
                                    if due < today:
                                        loan["status"] = "overdue"
                                        summary["overdue_count"] += 1
                                        break

    return jsonify(summary)


@reports_bp.route('/dashboard/summary', methods=['GET'])
@token_required()
def dashboard_summary():
    user_tree = filter_hierarchy_for_user(request.user)

    total_farmers = 0
    total_fertilizer_loans = 0
    total_expected_maize = 0
    remaining_maize = 0
    total_asset_loans = 0
    total_asset_value = 0.0
    asset_balance_remaining = 0.0
    total_cash_loans = 0
    total_cash_repayable = 0.0
    cash_balance_remaining = 0.0

    for prov_name, prov_val in user_tree.items():
        for dist_name, dist_val in prov_val.items():
            for vill_name, vill_val in dist_val.items():
                for shop_name, shop_val in vill_val.items():
                    clients = shop_val.get("clients", {})
                    total_farmers += len(clients.get("farmers", []))

                    for floan in clients.get("fertilizer_loans", []):
                        total_fertilizer_loans += 1
                        total_expected_maize += floan.get("expected_maize_bags", 0)
                        remaining_maize += floan.get("balance_remaining", 0)

                    for aloan in clients.get("asset_finance", []):
                        total_asset_loans += 1
                        total_asset_value += aloan.get("asset_value", 0)
                        asset_balance_remaining += aloan.get("balance_remaining", 0)

                    for cloan in clients.get("cash_loans", []):
                        total_cash_loans += 1
                        total_cash_repayable += cloan.get("total_repayable", 0)
                        cash_balance_remaining += cloan.get("balance_remaining", 0)

    return jsonify({
        "role": request.user.get("role"),
        "user": request.user.get("user"),
        "summary": {
            "total_farmers": total_farmers,
            "fertilizer": {
                "count": total_fertilizer_loans,
                "expected_maize_bags": total_expected_maize,
                "remaining_maize_bags": remaining_maize,
                "collected_maize_bags": total_expected_maize - remaining_maize
            },
            "asset_finance": {
                "count": total_asset_loans,
                "total_asset_value": round(total_asset_value, 2),
                "balance_remaining": round(asset_balance_remaining, 2)
            },
            "cash_loans": {
                "count": total_cash_loans,
                "total_repayable": round(total_cash_repayable, 2),
                "balance_remaining": round(cash_balance_remaining, 2)
            }
        }
    })
