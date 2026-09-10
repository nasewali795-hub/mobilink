import math
import datetime


def round_to_2(x):
    return round(float(x) + 1e-9, 2)


def generate_flat_schedule(principal, interest_rate_pct, term_days, installments, start_date, fees=0):
    total_interest = round_to_2(principal * (interest_rate_pct / 100.0) * (term_days / 365.0))
    total_payable = round_to_2(principal + total_interest + (fees or 0))
    installment_amount = round_to_2(total_payable / installments)
    principal_per_installment = round_to_2(principal / installments)
    interest_per_installment = round_to_2(total_interest / installments)
    fees_per_installment = round_to_2((fees or 0) / installments)
    interval_days = max(1, math.floor(term_days / installments))
    schedule = []
    current_date = datetime.date.fromisoformat(start_date)
    for i in range(1, installments + 1):
        current_date = current_date + datetime.timedelta(days=interval_days)
        schedule.append({
            "installment_no": i,
            "due_date": current_date.isoformat(),
            "due_principal": principal_per_installment,
            "due_interest": interest_per_installment,
            "due_fees": fees_per_installment,
            "status": "due",
            "paid_at": None
        })
    schedule = _adjust_rounding(schedule, principal, total_interest, fees or 0)
    total_recalc = round_to_2(
        sum(s["due_principal"] for s in schedule) +
        sum(s["due_interest"] for s in schedule) +
        sum(s["due_fees"] for s in schedule)
    )
    return schedule, total_recalc


def generate_reducing_schedule(principal, interest_rate_pct, installments, start_date, frequency="monthly"):
    periods_per_year = 52 if frequency == "Weekly" else 12
    r = (interest_rate_pct / 100.0) / periods_per_year
    n = installments
    if r > 0 and n > 0:
        emi = round_to_2(principal * (r * ((1 + r) ** n)) / (((1 + r) ** n) - 1))
    else:
        emi = round_to_2(principal / n) if n > 0 else round_to_2(principal)
    schedule = []
    outstanding = principal
    current_date = datetime.date.fromisoformat(start_date)
    interval = 7 if frequency == "Weekly" else 30
    for i in range(1, n + 1):
        interest = round_to_2(outstanding * r)
        principal_component = round_to_2(emi - interest)
        if i == n:
            principal_component = round_to_2(outstanding)
        outstanding = round_to_2(outstanding - principal_component)
        current_date = current_date + datetime.timedelta(days=interval)
        schedule.append({
            "installment_no": i,
            "due_date": current_date.isoformat(),
            "due_principal": principal_component,
            "due_interest": interest,
            "due_fees": 0,
            "status": "due",
            "paid_at": None
        })
    return schedule, emi * n


def _adjust_rounding(schedule, principal, total_interest, total_fees):
    sum_principal = sum(s["due_principal"] for s in schedule)
    sum_interest = sum(s["due_interest"] for s in schedule)
    sum_fees = sum(s["due_fees"] for s in schedule)
    principal_diff = round_to_2(principal - sum_principal)
    interest_diff = round_to_2(total_interest - sum_interest)
    fees_diff = round_to_2(total_fees - sum_fees)
    if principal_diff != 0:
        schedule[-1]["due_principal"] = round_to_2(schedule[-1]["due_principal"] + principal_diff)
    if interest_diff != 0:
        schedule[-1]["due_interest"] = round_to_2(schedule[-1]["due_interest"] + interest_diff)
    if fees_diff != 0:
        schedule[-1]["due_fees"] = round_to_2(schedule[-1]["due_fees"] + fees_diff)
    return schedule


def allocate_repayment(loan, amount):
    schedule = loan.get("schedule", [])
    penalties = loan.get("penalties", [])
    remaining = round_to_2(amount)
    allocated = {"fees": 0, "penalty": 0, "interest": 0, "principal": 0}

    due_rows = [r for r in schedule if r.get("status") == "due"]
    for row in due_rows:
        if remaining <= 0:
            break
        if row.get("due_fees", 0) > 0:
            take = min(remaining, row["due_fees"])
            row["due_fees"] = round_to_2(row["due_fees"] - take)
            allocated["fees"] = round_to_2(allocated["fees"] + take)
            remaining = round_to_2(remaining - take)
            if row["due_principal"] == 0 and row["due_interest"] == 0 and row["due_fees"] == 0:
                row["status"] = "paid"

    for p in penalties:
        if remaining <= 0:
            break
        if not p.get("paid"):
            take = min(remaining, p.get("amount", 0))
            p["amount"] = round_to_2(p["amount"] - take)
            allocated["penalty"] = round_to_2(allocated["penalty"] + take)
            remaining = round_to_2(remaining - take)
            if p["amount"] == 0:
                p["paid"] = True

    for row in due_rows:
        if remaining <= 0:
            break
        if row.get("due_interest", 0) > 0:
            take = min(remaining, row["due_interest"])
            row["due_interest"] = round_to_2(row["due_interest"] - take)
            allocated["interest"] = round_to_2(allocated["interest"] + take)
            remaining = round_to_2(remaining - take)
            if row["due_principal"] == 0 and row["due_interest"] == 0 and row["due_fees"] == 0:
                row["status"] = "paid"

    for row in due_rows:
        if remaining <= 0:
            break
        if row.get("due_principal", 0) > 0:
            take = min(remaining, row["due_principal"])
            row["due_principal"] = round_to_2(row["due_principal"] - take)
            allocated["principal"] = round_to_2(allocated["principal"] + take)
            remaining = round_to_2(remaining - take)
            if row["due_principal"] == 0 and row["due_interest"] == 0 and row["due_fees"] == 0:
                row["status"] = "paid"

    if remaining > 0:
        allocated["principal"] = round_to_2(allocated["principal"] + remaining)
        remaining = 0

    outstanding_principal = sum(r.get("due_principal", 0) for r in schedule)
    loan["balance_remaining"] = round_to_2(outstanding_principal)
    if loan.get("balance_remaining", 0) == 0:
        loan["status"] = "completed"
    return {"allocation": allocated, "remaining": remaining}


def find_loan_by_id(loan_id):
    from app.state import structure
    for province in structure:
        for district in structure[province]:
            for village in structure[province][district]:
                for shop, shop_data in structure[province][district][village].items():
                    clients = shop_data.get("clients", {})
                    for cat in ["fertilizer_loans", "asset_finance", "cash_loans"]:
                        for loan in clients.get(cat, []):
                            if loan.get("id") == loan_id:
                                return loan, cat, shop_data
    return None, None, None


def find_shop_by_name(shop_name):
    from app.state import structure
    for province in structure:
        for district in structure[province]:
            for village in structure[province][district]:
                if shop_name in structure[province][district][village]:
                    return structure[province][district][village][shop_name], province, district, village
    return None, None, None, None


def find_shop_by_id(shop_id):
    from app.state import structure
    for province in structure:
        for district in structure[province]:
            for village in structure[province][district]:
                for s_name, s_data in structure[province][district][village].items():
                    if s_data.get("shop_id") == shop_id:
                        return s_data, s_name, province, district, village
    return None, None, None, None, None
