SECRET_KEY = 'supersecretkey_microfin_2026_secure_key_32_bytes!'
JWT_EXPIRY_HOURS = 4

APP_SETTINGS = {
    "system": {
        "system_name": "AgriFin Microfinance Portal",
        "version": "1.0.0",
        "jwt_expiry_hours": 4,
        "default_theme": "dark",
        "shops_per_page": 16,
        "inventory_per_page": 10
    },
    "loan_rules": {
        "fertilizer_downpayment_per_bag": 450,
        "default_repayment_ratio": "1:4",
        "fertilizer_term_days": 180,
        "default_fertilizer_type": "NPK + Urea Compound",
        "asset_downpayment_percent": 20,
        "asset_interest_rate": 15,
        "asset_installments": 12,
        "asset_installment_frequency": "monthly",
        "asset_term_days": 365,
        "cash_interest_rate": 10,
        "cash_term_months": 6,
        "default_cash_purpose": "General Agricultural Cash",
        "cash_term_days": 180
    },
    "limits": {
        "default_shop_max_loan_limit": 10000,
        "min_cash_loan_amount": 50,
        "min_asset_value": 100,
        "low_stock_threshold": 10,
        "fert_low_stock_threshold": 500,
        "asset_low_stock_threshold": 2,
        "cash_reserve_low_threshold": 50000,
        "expiry_warning_days": 90
    },
    "features": {
        "mobile_money": True,
        "sms_notifications": False,
        "accounting_sync": True
    },
    "templates": {
        "repayment_reminder": "Dear {{farmer_name}}, your loan repayment of ZMW {{amount}} is due on {{due_date}}. Please visit your nearest shop to make payment.",
        "disbursement_notice": "Dear {{farmer_name}}, your loan of ZMW {{amount}} has been disbursed. Please collect from {{shop_name}}.",
        "overdue_alert": "Dear {{farmer_name}}, your loan payment is overdue by {{days_overdue}} days. Please settle immediately to avoid penalties."
    },
    "inventory": {
        "next_item_id": 1,
        "items": {},
        "transactions": [],
        "master_catalog": [
            {"name": "Compound D", "category": "fertilizer", "unit": "bags", "cost_price": 450, "loan_value": 450, "selling_price": 500, "supplier": "Zamagro Ltd", "low_stock_threshold": 500},
            {"name": "Urea", "category": "fertilizer", "unit": "bags", "cost_price": 420, "loan_value": 420, "selling_price": 460, "supplier": "Zamagro Ltd", "low_stock_threshold": 500},
            {"name": "NPK + Urea Compound", "category": "fertilizer", "unit": "bags", "cost_price": 480, "loan_value": 480, "selling_price": 530, "supplier": "Zamagro Ltd", "low_stock_threshold": 500},
            {"name": "Basal Top Dressing", "category": "fertilizer", "unit": "bags", "cost_price": 390, "loan_value": 390, "selling_price": 430, "supplier": "Nutrient Africa", "low_stock_threshold": 500},
            {"name": "Lime", "category": "fertilizer", "unit": "bags", "cost_price": 150, "loan_value": 150, "selling_price": 180, "supplier": "LimeCo", "low_stock_threshold": 300},
            {"name": "Sulphate of Ammonia", "category": "fertilizer", "unit": "bags", "cost_price": 410, "loan_value": 410, "selling_price": 450, "supplier": "Zamagro Ltd", "low_stock_threshold": 500},
            {"name": "Maize Seed (Hybrid)", "category": "seed", "unit": "kg", "cost_price": 25, "loan_value": 25, "selling_price": 30, "supplier": "SeedCo", "low_stock_threshold": 50},
            {"name": "Soybean Seed", "category": "seed", "unit": "kg", "cost_price": 28, "loan_value": 28, "selling_price": 35, "supplier": "SeedCo", "low_stock_threshold": 50},
            {"name": "Cypermethrin", "category": "pesticide", "unit": "liters", "cost_price": 120, "loan_value": 120, "selling_price": 150, "supplier": "CropCare", "low_stock_threshold": 20},
            {"name": "Mancozeb", "category": "pesticide", "unit": "kg", "cost_price": 95, "loan_value": 95, "selling_price": 120, "supplier": "CropCare", "low_stock_threshold": 20}
        ]
    },
    "loan_products": [
        {
            "id": "LP-CASH-STD",
            "name": "Cash Loan - Standard",
            "type": "cash",
            "interest_type": "Flat Rate",
            "interest_rate": 10,
            "repayment_frequency": "Monthly",
            "default_installments": 6,
            "default_tenure": "6 Months",
            "grace_period_days": 0,
            "repayment_method": "Cash only",
            "late_penalty_type": "percentage",
            "late_penalty_value": 2,
            "default_handling": "Mark defaulted after 3 missed installments",
            "restructuring_allowed": True,
            "approval_level": "Shop",
            "disbursement_method": "Cash at shop",
            "alerts_enabled": True,
            "audit_trail_enabled": True
        },
        {
            "id": "LP-CASH-AGRIC",
            "name": "Cash Loan - Agricultural Input",
            "type": "cash",
            "interest_type": "Flat Rate",
            "interest_rate": 12,
            "repayment_frequency": "Seasonal",
            "default_installments": 2,
            "default_tenure": "2 Seasons",
            "grace_period_days": 30,
            "repayment_method": "Mixed",
            "late_penalty_type": "percentage",
            "late_penalty_value": 3,
            "default_handling": "Mark defaulted after 2 missed installments",
            "restructuring_allowed": True,
            "approval_level": "HQ",
            "disbursement_method": "Mobile money",
            "alerts_enabled": True,
            "audit_trail_enabled": True
        },
        {
            "id": "LP-FERT-STD",
            "name": "Fertilizer Loan - Standard",
            "type": "fertilizer",
            "interest_type": "Service Fee",
            "interest_rate": 0,
            "repayment_frequency": "Seasonal",
            "default_installments": 1,
            "default_tenure": "1 Season",
            "grace_period_days": 0,
            "repayment_method": "Commodity only",
            "late_penalty_type": "fixed",
            "late_penalty_value": 50,
            "default_handling": "Mark defaulted after 1 missed installment",
            "restructuring_allowed": False,
            "approval_level": "Shop",
            "disbursement_method": "Inputs at shop",
            "alerts_enabled": True,
            "audit_trail_enabled": True
        },
        {
            "id": "LP-ASSET-STD",
            "name": "Asset Finance - Standard",
            "type": "equipment",
            "interest_type": "Reducing Balance",
            "interest_rate": 15,
            "repayment_frequency": "Monthly",
            "default_installments": 12,
            "default_tenure": "12 Months",
            "grace_period_days": 0,
            "repayment_method": "Cash only",
            "late_penalty_type": "percentage",
            "late_penalty_value": 2.5,
            "default_handling": "Mark defaulted after 3 missed installments",
            "restructuring_allowed": True,
            "approval_level": "HQ",
            "disbursement_method": "Asset delivery",
            "alerts_enabled": True,
            "audit_trail_enabled": True
        }
    ]
}

HQ_WAREHOUSE = {
    "fertilizers": [
        {"item_name": "Compound D", "quantity": 5000, "unit": "bags", "batch_no": "CD-2026-001", "expiry_date": "2027-06-30"},
        {"item_name": "Urea", "quantity": 3500, "unit": "bags", "batch_no": "UR-2026-001", "expiry_date": "2027-06-30"},
        {"item_name": "Green Sulf", "quantity": 800, "unit": "bags", "batch_no": "GS-2026-001", "expiry_date": "2027-03-31"},
        {"item_name": "NPK + Urea Compound", "quantity": 2000, "unit": "bags", "batch_no": "NPK-2026-001", "expiry_date": "2027-06-30"},
        {"item_name": "Basal Top Dressing", "quantity": 1200, "unit": "bags", "batch_no": "BTD-2026-001", "expiry_date": "2027-04-30"},
        {"item_name": "Lime", "quantity": 3000, "unit": "bags", "batch_no": "LM-2026-001", "expiry_date": "2028-01-31"},
        {"item_name": "Sulphate of Ammonia", "quantity": 1500, "unit": "bags", "batch_no": "SA-2026-001", "expiry_date": "2027-05-31"}
    ],
    "seeds": [
        {"item_name": "Maize Seed (Hybrid)", "quantity": 500, "unit": "kg", "batch_no": "MS-2026-001", "expiry_date": "2027-03-31"},
        {"item_name": "Soybean Seed", "quantity": 300, "unit": "kg", "batch_no": "SB-2026-001", "expiry_date": "2027-03-31"}
    ],
    "pesticides": [
        {"item_name": "Cypermethrin", "quantity": 200, "unit": "liters", "batch_no": "CY-2026-001", "expiry_date": "2027-12-31"},
        {"item_name": "Mancozeb", "quantity": 150, "unit": "kg", "batch_no": "MN-2026-001", "expiry_date": "2027-08-31"}
    ],
    "assets": [
        {"item_name": "Tractor", "quantity": 5, "unit": "units", "purchase_cost": 250000, "financing_terms": "12 months", "status": "available"},
        {"item_name": "Plough", "quantity": 8, "unit": "units", "purchase_cost": 15000, "financing_terms": "6 months", "status": "available"},
        {"item_name": "Irrigation Pump", "quantity": 12, "unit": "units", "purchase_cost": 8500, "financing_terms": "6 months", "status": "available"},
        {"item_name": "Motorized Maize Sheller", "quantity": 6, "unit": "units", "purchase_cost": 12000, "financing_terms": "6 months", "status": "available"},
        {"item_name": "Solar Water Pump Kit", "quantity": 10, "unit": "kits", "purchase_cost": 8500, "financing_terms": "12 months", "status": "available"}
    ],
    "cash_pool": {
        "total_cash": 500000,
        "allocated_to_shops": 125000,
        "reserved": 375000,
        "available_for_disbursement": 0
    },
    "distribution_history": [
        {"date": "2026-01-05", "shop": "ShopA", "province": "Eastern Province", "district": "DistrictA", "village": "VillageX", "item": "Compound D", "quantity": 500, "unit": "bags", "type": "fertilizer"},
        {"date": "2026-02-12", "shop": "ShopB", "province": "Eastern Province", "district": "DistrictA", "village": "VillageY", "item": "Urea", "quantity": 200, "unit": "bags", "type": "fertilizer"},
        {"date": "2026-03-18", "shop": "ShopC", "province": "Central Province", "district": "Kabwe", "village": "Village-1", "item": "Maize Seed (Hybrid)", "quantity": 50, "unit": "kg", "type": "seed"}
    ]
}
