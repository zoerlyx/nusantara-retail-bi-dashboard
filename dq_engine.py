import os
import uuid
import pandas as pd
import numpy as np
from datetime import datetime, date

# ====================================================================
# CONFIGURATION & CONSTANTS
# ====================================================================
DATA_DIR = "data/raw"
OUTPUT_DIR = "data/quality"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEVERITY_WEIGHTS = {
    "Critical": 1.50,
    "High": 1.25,
    "Medium": 1.00,
    "Low": 0.75
}

RULES_CONFIG = {
    "DQ-CN01": {"dim": "Completeness", "sev": "High",     "desc": "Missing Customer ID"},
    "DQ-CN02": {"dim": "Completeness", "sev": "High",     "desc": "Missing Product ID"},
    "DQ-CN03": {"dim": "Completeness", "sev": "Critical", "desc": "Missing Transaction Date"},
    "DQ-VL01": {"dim": "Validity",     "sev": "High",     "desc": "Invalid Quantity"},
    "DQ-VL02": {"dim": "Validity",     "sev": "High",     "desc": "Invalid Unit Price"},
    "DQ-VL03": {"dim": "Validity",     "sev": "Medium",   "desc": "Invalid Discount"},
    "DQ-VL04": {"dim": "Validity",     "sev": "Medium",   "desc": "Invalid Payment Method"},
    "DQ-CS01": {"dim": "Consistency",  "sev": "High",     "desc": "Orphan Customer"},
    "DQ-CS02": {"dim": "Consistency",  "sev": "High",     "desc": "Orphan Product"},
    "DQ-CS03": {"dim": "Consistency",  "sev": "High",     "desc": "Store-Region Mismatch"},
    "DQ-CS04": {"dim": "Consistency",  "sev": "Critical", "desc": "Incorrect Sales Amount"},
    "DQ-UN01": {"dim": "Uniqueness",   "sev": "Critical", "desc": "Duplicate Transaction ID"},
    "DQ-AC01": {"dim": "Accuracy",     "sev": "High",     "desc": "Completed + Non-positive Amt"},
    "DQ-AC02": {"dim": "Accuracy",     "sev": "Medium",   "desc": "Abnormal Sales Amount"},
    "DQ-AC03": {"dim": "Accuracy",     "sev": "Critical", "desc": "Out-of-period Date"}
}

# Values imported from generate_dataset.py for validation
PAYMENT_METHODS = ["Cash", "Debit Card", "Credit Card", "E-Wallet", "Bank Transfer"]
N_SALES = 100_000

# Targets from Phase 2 to compare in the audit
PHASE2_TARGETS = {
    "DQ-CN01": int(N_SALES * 0.015),
    "DQ-CN02": int(N_SALES * 0.008),
    "DQ-CN03": int(N_SALES * 0.002),
    "DQ-VL01": int(N_SALES * 0.005),
    "DQ-VL02": int(N_SALES * 0.002),
    "DQ-VL03": int(N_SALES * 0.005),
    "DQ-VL04": int(N_SALES * 0.003),
    "DQ-CS01": int(N_SALES * 0.004),
    "DQ-CS02": int(N_SALES * 0.002),
    "DQ-CS03": int(N_SALES * 0.006),
    "DQ-CS04": int(N_SALES * 0.007),
    "DQ-UN01": int(N_SALES * 0.003),
    "DQ-AC01": int(N_SALES * 0.002),
    "DQ-AC02": int(N_SALES * 0.003),
    "DQ-AC03": int(N_SALES * 0.002),
}

# ====================================================================
# DATA LOADING
# ====================================================================
def load_data():
    print("[1/3] Loading Data...")
    sales = pd.read_csv(f"{DATA_DIR}/sales.csv")
    customers = pd.read_csv(f"{DATA_DIR}/customers.csv")
    products = pd.read_csv(f"{DATA_DIR}/products.csv")
    stores = pd.read_csv(f"{DATA_DIR}/stores.csv")
    
    # Create internal source_row_id for physical uniqueness (0-indexed matching Dataframe index)
    sales['source_row_id'] = sales.index
    
    # Pre-process for references
    valid_customers = set(customers['customer_id'].dropna())
    valid_products = set(products['product_id'].dropna())
    store_region_map = dict(zip(stores['store_id'], stores['region_id']))
    
    # Ensure types for numeric columns to handle NaN gracefully
    sales['quantity'] = pd.to_numeric(sales['quantity'], errors='coerce')
    sales['unit_price'] = pd.to_numeric(sales['unit_price'], errors='coerce')
    sales['discount_pct'] = pd.to_numeric(sales['discount_pct'], errors='coerce')
    sales['sales_amount'] = pd.to_numeric(sales['sales_amount'], errors='coerce')
    
    return sales, valid_customers, valid_products, store_region_map

# ====================================================================
# DQ RULE EVALUATION
# ====================================================================
def evaluate_rules(sales, valid_customers, valid_products, store_region_map):
    print("[2/3] Evaluating Rules...")
    
    # We will build boolean masks for FAILING conditions
    # If mask is True, it FAILS the rule. Otherwise it PASSES.
    fails = {}
    
    # --- COMPLETENESS ---
    fails["DQ-CN01"] = sales['customer_id'].isna()
    fails["DQ-CN02"] = sales['product_id'].isna()
    fails["DQ-CN03"] = sales['transaction_date'].isna()
    
    # --- VALIDITY ---
    fails["DQ-VL01"] = (sales['quantity'] <= 0) | sales['quantity'].isna()
    fails["DQ-VL02"] = (sales['unit_price'] < 0) | sales['unit_price'].isna()
    fails["DQ-VL03"] = (sales['discount_pct'] < 0) | (sales['discount_pct'] > 100) | sales['discount_pct'].isna()
    fails["DQ-VL04"] = ~sales['payment_method'].isin(PAYMENT_METHODS) & sales['payment_method'].notna()
    # Note: If it's NaN, should it fail VL04? Usually VL rules fail if present and invalid, but since we don't have a CN for payment method, we fail it if not in list. We check if not in list.
    
    # --- CONSISTENCY ---
    # DQ-CS01: Not null, but not in valid customers
    fails["DQ-CS01"] = sales['customer_id'].notna() & ~sales['customer_id'].isin(valid_customers)
    
    # DQ-CS02: Not null, but not in valid products
    fails["DQ-CS02"] = sales['product_id'].notna() & ~sales['product_id'].isin(valid_products)
    
    # DQ-CS03: Store-region mismatch. Store exists, but region doesn't match dim_store
    mapped_region = sales['store_id'].map(store_region_map)
    fails["DQ-CS03"] = sales['store_id'].notna() & sales['region_id'].notna() & (sales['region_id'] != mapped_region)
    
    # DQ-CS04: Incorrect sales amount formula
    expected_amt = (
        sales['quantity'] * 
        sales['unit_price'] * 
        (1 - sales['discount_pct'] / 100)
    ).round(2)
    # Using Rp1 tolerance as per Phase 3 contract
    fails["DQ-CS04"] = (sales['sales_amount'] - expected_amt).abs() > 1.0
    
    # --- UNIQUENESS ---
    # DQ-UN01: Duplicate transaction ID. All duplicates are flagged (keep=False)
    fails["DQ-UN01"] = sales.duplicated(subset=['transaction_id'], keep=False) & sales['transaction_id'].notna()
    
    # --- ACCURACY ---
    # DQ-AC01: Completed + Non-positive Amount
    fails["DQ-AC01"] = (sales['order_status'] == 'Completed') & (sales['sales_amount'] <= 0)
    
    # DQ-AC02: Abnormal Sales Amount (> 2x expected)
    fails["DQ-AC02"] = sales['sales_amount'] > (expected_amt * 2)
    
    # DQ-AC03: Out-of-period Date
    # Safe convert to dates for comparison
    def is_out_of_period(d):
        try:
            if pd.isna(d): return False # Let CN03 handle NA
            parsed = pd.to_datetime(d).date()
            return parsed < date(2025, 1, 1) or parsed > date(2025, 12, 31)
        except:
            return True
            
    fails["DQ-AC03"] = sales['transaction_date'].apply(is_out_of_period)

    return fails

# ====================================================================
# AGGREGATION & REPORTING
# ====================================================================
def generate_outputs(sales, fails):
    print("[3/3] Generating Outputs...")
    
    result_id = str(uuid.uuid4())
    result_date = datetime.now().isoformat()
    total_records = len(sales)
    
    dq_results = []
    dq_issues = []
    
    for rule_id, fail_mask in fails.items():
        conf = RULES_CONFIG[rule_id]
        
        fail_count = fail_mask.sum()
        pass_count = total_records - fail_count
        warning_count = 0  # No warning thresholds defined for these rules
        
        failure_rate = fail_count / total_records
        warning_rate = 0.0
        dq_score = (pass_count / total_records) * 100
        
        # Aggregate Record
        dq_results.append({
            "result_id": result_id,
            "rule_id": rule_id,
            "result_date": result_date,
            "dimension": conf["dim"],
            "severity": conf["sev"],
            "total_records": total_records,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "warning_count": warning_count,
            "failure_rate": failure_rate,
            "warning_rate": warning_rate,
            "dq_score": dq_score
        })
        
        # Detail Records (only for fails)
        failed_records = sales[fail_mask]
        for _, row in failed_records.iterrows():
            issue_val = None
            expected_val = None
            
            # Context-specific issue extraction
            if rule_id == "DQ-CN01": issue_val = row["customer_id"]
            elif rule_id == "DQ-CN02": issue_val = row["product_id"]
            elif rule_id == "DQ-CN03": issue_val = row["transaction_date"]
            elif rule_id == "DQ-VL01": issue_val = row["quantity"]
            elif rule_id == "DQ-VL02": issue_val = row["unit_price"]
            elif rule_id == "DQ-VL03": issue_val = row["discount_pct"]
            elif rule_id == "DQ-VL04": issue_val = row["payment_method"]
            elif rule_id == "DQ-CS01": issue_val = row["customer_id"]
            elif rule_id == "DQ-CS02": issue_val = row["product_id"]
            elif rule_id == "DQ-CS03": issue_val = str(row["region_id"])
            elif rule_id == "DQ-CS04": issue_val = row["sales_amount"]
            elif rule_id == "DQ-UN01": issue_val = row["transaction_id"]
            elif rule_id == "DQ-AC01": issue_val = row["sales_amount"]
            elif rule_id == "DQ-AC02": issue_val = row["sales_amount"]
            elif rule_id == "DQ-AC03": issue_val = row["transaction_date"]
            
            dq_issues.append({
                "issue_id": str(uuid.uuid4()),
                "result_id": result_id,
                "source_row_id": row["source_row_id"],
                "transaction_id": row["transaction_id"],
                "rule_id": rule_id,
                "issue_date": result_date,
                "status": "FAIL",
                "severity": conf["sev"],
                "issue_value": issue_val,
                "expected_value": expected_val,
                "issue_description": conf["desc"]
            })
            
    # Calculate Overall Score
    total_weight = 0
    weighted_score_sum = 0
    for r in dq_results:
        w = SEVERITY_WEIGHTS[r["severity"]]
        total_weight += w
        weighted_score_sum += (r["dq_score"] * w)
        
    overall_score = weighted_score_sum / total_weight if total_weight > 0 else 0
    
    # Save CSVs
    df_results = pd.DataFrame(dq_results)
    df_issues = pd.DataFrame(dq_issues)
    
    df_results.to_csv(f"{OUTPUT_DIR}/dq_result.csv", index=False)
    df_issues.to_csv(f"{OUTPUT_DIR}/dq_issue_detail.csv", index=False)
    
    # Audit Console Output
    print("\n============================================================")
    print("PHASE 3: DATA QUALITY ENGINE AUDIT")
    print("============================================================")
    print(f"Total Rules Executed : {len(dq_results)}/15")
    print(f"Total Records Checked: {total_records}")
    print(f"CUSTOM PROJECT METRIC Overall DQ Score: {overall_score:.2f}%\n")
    
    print(f"{'Rule':<10} {'Target(Primary)':<18} {'Detected':<10} {'Natural Secondary(Diff)'}")
    print("-" * 65)
    
    for r in dq_results:
        rid = r["rule_id"]
        target = PHASE2_TARGETS[rid]
        detected = r["fail_count"]
        # In DQ-UN01, the target was 300 duplicates, but each duplicate means TWO records share the same ID.
        # So "duplicated(keep=False)" detects 600 records. We divide by 2 just for the audit display mapping to 'target events' vs 'rows'.
        if rid == "DQ-UN01":
            detected = int(detected / 2) # Since a duplicate pair flags 2 rows

        diff = detected - target
        print(f"{rid:<10} {target:<18} {detected:<10} +{diff}")
        
    print("============================================================")
    print("DQ engine complete. Outputs written to data/quality/")

if __name__ == "__main__":
    sales, valid_customers, valid_products, store_region_map = load_data()
    fails = evaluate_rules(sales, valid_customers, valid_products, store_region_map)
    generate_outputs(sales, fails)
