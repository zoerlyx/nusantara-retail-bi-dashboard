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

os.makedirs(OUTPUT_DIR, exist_ok=True)

SEVERITY_WEIGHTS = {
    "Critical": 1.50,
    "High": 1.25,
    "Medium": 1.00,
    "Low": 0.75
}

RULES_CONFIG = {
    "DQ-CN01": {"dim": "Completeness", "sev": "High",     "desc": "Customer ID does not exist in customer master."},
    "DQ-CN02": {"dim": "Completeness", "sev": "High",     "desc": "Product ID is missing."},
    "DQ-CN03": {"dim": "Completeness", "sev": "Critical", "desc": "Transaction Date is missing."},
    "DQ-VL01": {"dim": "Validity",     "sev": "High",     "desc": "Quantity must be greater than zero."},
    "DQ-VL02": {"dim": "Validity",     "sev": "High",     "desc": "Unit price must be greater than or equal to zero."},
    "DQ-VL03": {"dim": "Validity",     "sev": "Medium",   "desc": "Discount must be between 0 and 100."},
    "DQ-VL04": {"dim": "Validity",     "sev": "Medium",   "desc": "Payment method is not recognized."},
    "DQ-CS01": {"dim": "Consistency",  "sev": "High",     "desc": "Customer ID does not exist in customer master."},
    "DQ-CS02": {"dim": "Consistency",  "sev": "High",     "desc": "Product ID does not exist in product master."},
    "DQ-CS03": {"dim": "Consistency",  "sev": "High",     "desc": "Store region does not match the region recorded in the transaction."},
    "DQ-CS04": {"dim": "Consistency",  "sev": "Critical", "desc": "Sales amount differs from expected transaction amount by more than Rp1."},
    "DQ-UN01": {"dim": "Uniqueness",   "sev": "Critical", "desc": "Duplicate transaction ID found."},
    "DQ-AC01": {"dim": "Accuracy",     "sev": "High",     "desc": "Completed orders must have sales amount > 0."},
    "DQ-AC02": {"dim": "Accuracy",     "sev": "Medium",   "desc": "Sales amount is more than 2x the expected amount."},
    "DQ-AC03": {"dim": "Accuracy",     "sev": "Critical", "desc": "Transaction date is outside the 2025 business period."}
}

PAYMENT_METHODS = ["Cash", "Debit Card", "Credit Card", "E-Wallet", "Bank Transfer"]
N_SALES = 100_000

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
    
    sales['source_row_id'] = sales.index
    sales['safe_transaction_date'] = sales['transaction_date'].fillna('UNKNOWN_DATE')
    
    valid_customers = set(customers['customer_id'].dropna())
    valid_products = set(products['product_id'].dropna())
    store_region_map = dict(zip(stores['store_id'], stores['region_id']))
    
    sales['quantity_num'] = pd.to_numeric(sales['quantity'], errors='coerce')
    sales['unit_price_num'] = pd.to_numeric(sales['unit_price'], errors='coerce')
    sales['discount_pct_num'] = pd.to_numeric(sales['discount_pct'], errors='coerce')
    sales['sales_amount_num'] = pd.to_numeric(sales['sales_amount'], errors='coerce')
    
    return sales, valid_customers, valid_products, store_region_map

# ====================================================================
# DQ RULE EVALUATION
# ====================================================================
def evaluate_rules(sales, valid_customers, valid_products, store_region_map):
    print("[2/3] Evaluating Rules...")
    fails = {}
    
    # --- COMPLETENESS ---
    fails["DQ-CN01"] = sales['customer_id'].isna()
    fails["DQ-CN02"] = sales['product_id'].isna()
    fails["DQ-CN03"] = sales['transaction_date'].isna()
    
    # --- VALIDITY ---
    fails["DQ-VL01"] = (sales['quantity_num'] <= 0) | sales['quantity_num'].isna()
    fails["DQ-VL02"] = (sales['unit_price_num'] < 0) | sales['unit_price_num'].isna()
    fails["DQ-VL03"] = (sales['discount_pct_num'] < 0) | (sales['discount_pct_num'] > 100) | sales['discount_pct_num'].isna()
    fails["DQ-VL04"] = ~sales['payment_method'].isin(PAYMENT_METHODS) & sales['payment_method'].notna()
    
    # --- CONSISTENCY ---
    fails["DQ-CS01"] = sales['customer_id'].notna() & ~sales['customer_id'].isin(valid_customers)
    fails["DQ-CS02"] = sales['product_id'].notna() & ~sales['product_id'].isin(valid_products)
    
    mapped_region = sales['store_id'].map(store_region_map)
    fails["DQ-CS03"] = sales['store_id'].notna() & sales['region_id'].notna() & (sales['region_id'] != mapped_region)
    
    expected_amt = (
        sales['quantity_num'] * 
        sales['unit_price_num'] * 
        (1 - sales['discount_pct_num'] / 100)
    ).round(2)
    sales['expected_amount_num'] = expected_amt
    fails["DQ-CS04"] = (sales['sales_amount_num'] - expected_amt).abs() > 1.0
    
    # --- UNIQUENESS ---
    # DQ-UN01 is evaluated over entire dataset
    fails["DQ-UN01"] = sales.duplicated(subset=['transaction_id'], keep=False) & sales['transaction_id'].notna()
    
    # --- ACCURACY ---
    fails["DQ-AC01"] = (sales['order_status'] == 'Completed') & (sales['sales_amount_num'] <= 0)
    fails["DQ-AC02"] = sales['sales_amount_num'] > (expected_amt * 2)
    
    def is_out_of_period(d):
        try:
            if pd.isna(d): return False 
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
    
    dq_results = []
    dq_issues = []
    
    # Track full-period pass counts for overall score
    full_period_stats = {}

    # Map for CS03 expected values
    store_region_map = dict(zip(pd.read_csv(f"{DATA_DIR}/stores.csv")['store_id'], pd.read_csv(f"{DATA_DIR}/stores.csv")['region_id']))

    for rule_id, fail_mask in fails.items():
        conf = RULES_CONFIG[rule_id]
        
        # Calculate full-period stats
        total_full = len(sales)
        fail_full = fail_mask.sum()
        pass_full = total_full - fail_full
        full_period_stats[rule_id] = {
            "pass": pass_full,
            "fail": fail_full,
            "total": total_full,
            "score": (pass_full / total_full) * 100,
            "severity": conf["sev"]
        }
        
        # Aggregate by safe_transaction_date (i.e. daily grain, with 'UNKNOWN_DATE' for nulls)
        sales_with_fail = sales.copy()
        sales_with_fail['is_fail'] = fail_mask
        
        # Group by the date column
        grouped = sales_with_fail.groupby('safe_transaction_date')
        
        for dt_val, group in grouped:
            # Reconvert UNKNOWN_DATE to proper empty string/null representation in result_date
            res_date = dt_val if dt_val != 'UNKNOWN_DATE' else None
            
            result_id = str(uuid.uuid4())
            total_records = len(group)
            fail_count = group['is_fail'].sum()
            pass_count = total_records - fail_count
            warning_count = 0
            
            failure_rate = fail_count / total_records if total_records > 0 else 0.0
            warning_rate = 0.0
            dq_score = (pass_count / total_records) * 100 if total_records > 0 else 0.0
            
            dq_results.append({
                "result_id": result_id,
                "rule_id": rule_id,
                "result_date": res_date,
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
            
            failed_records = group[group['is_fail']]
            for _, row in failed_records.iterrows():
                issue_val = None
                expected_val = None
                
                # Context-specific issue extraction
                if rule_id == "DQ-CN01": 
                    issue_val = None
                    expected_val = "NOT NULL"
                elif rule_id == "DQ-CN02": 
                    issue_val = None
                    expected_val = "NOT NULL"
                elif rule_id == "DQ-CN03": 
                    issue_val = None
                    expected_val = "valid 2025 transaction date"
                elif rule_id == "DQ-VL01": 
                    issue_val = row["quantity"]
                    expected_val = "> 0"
                elif rule_id == "DQ-VL02": 
                    issue_val = row["unit_price"]
                    expected_val = ">= 0"
                elif rule_id == "DQ-VL03": 
                    issue_val = row["discount_pct"]
                    expected_val = "0-100"
                elif rule_id == "DQ-VL04": 
                    issue_val = row["payment_method"]
                    expected_val = "valid PAYMENT_METHODS values"
                elif rule_id == "DQ-CS01": 
                    issue_val = row["customer_id"]
                    expected_val = "existing customer_id in dim_customer"
                elif rule_id == "DQ-CS02": 
                    issue_val = row["product_id"]
                    expected_val = "existing product_id in dim_product"
                elif rule_id == "DQ-CS03": 
                    issue_val = row["region_id"]
                    expected_val = store_region_map.get(row["store_id"], "Unknown Store Region")
                elif rule_id == "DQ-CS04": 
                    issue_val = row["sales_amount"]
                    expected_val = row["expected_amount_num"]
                elif rule_id == "DQ-UN01": 
                    issue_val = row["transaction_id"]
                    expected_val = "unique transaction_id"
                elif rule_id == "DQ-AC01": 
                    issue_val = row["sales_amount"]
                    expected_val = "> 0 for Completed order"
                elif rule_id == "DQ-AC02": 
                    issue_val = row["sales_amount"]
                    expected_val = f"<= {row['expected_amount_num'] * 2 if pd.notna(row['expected_amount_num']) else 'N/A'}"
                elif rule_id == "DQ-AC03": 
                    issue_val = row["transaction_date"]
                    expected_val = "2025-01-01 to 2025-12-31"
                
                # Issue Date should map to underlying transaction_date
                iss_date = row["transaction_date"] if pd.notna(row["transaction_date"]) else None
                
                dq_issues.append({
                    "issue_id": str(uuid.uuid4()),
                    "result_id": result_id,
                    "source_row_id": row["source_row_id"],
                    "transaction_id": row["transaction_id"],
                    "rule_id": rule_id,
                    "issue_date": iss_date,
                    "status": "FAIL",
                    "severity": conf["sev"],
                    "issue_value": str(issue_val) if issue_val is not None else "",
                    "expected_value": str(expected_val) if expected_val is not None else "",
                    "issue_description": conf["desc"]
                })
            
    # Calculate Overall Score across FULL 100,000 records
    total_weight = 0
    weighted_score_sum = 0
    for rule_id, stats in full_period_stats.items():
        w = SEVERITY_WEIGHTS[stats["severity"]]
        total_weight += w
        weighted_score_sum += (stats["score"] * w)
        
    overall_score = weighted_score_sum / total_weight if total_weight > 0 else 0
    
    # Save CSVs
    df_results = pd.DataFrame(dq_results)
    df_issues = pd.DataFrame(dq_issues)
    
    df_results.to_csv(f"{OUTPUT_DIR}/dq_result.csv", index=False)
    df_issues.to_csv(f"{OUTPUT_DIR}/dq_issue_detail.csv", index=False)
    
    # Audit Console Output
    print("\n============================================================")
    print("PHASE 3 FINAL AUDIT")
    print("============================================================")
    print(f"Total Rules Executed : 15/15")
    print(f"Total Records Checked: {N_SALES}")
    print(f"CUSTOM PROJECT METRIC Overall DQ Score (Full Period): {overall_score:.2f}%\n")
    print(f"dq_result rows generated      : {len(df_results)}")
    print(f"dq_issue_detail rows generated: {len(df_issues)}\n")
    
    print(f"{'Rule':<10} {'Primary Target':<18} {'Total Detected':<15} {'Secondary Diff'}")
    print("-" * 65)
    
    for rule_id in RULES_CONFIG.keys():
        target = PHASE2_TARGETS[rule_id]
        detected = full_period_stats[rule_id]["fail"]
        
        if rule_id == "DQ-UN01":
            detected = int(detected / 2)

        diff = detected - target
        
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print(f"{rule_id:<10} {target:<18} {detected:<15} {diff_str}")
        
    print("\n--- SECONDARY DETECTION BREAKDOWN ---")
    print("DQ-CS04")
    cs04_det = full_period_stats["DQ-CS04"]["fail"]
    cs04_tgt = PHASE2_TARGETS["DQ-CS04"]
    print(f"  Primary: {cs04_tgt}")
    print(f"  Secondary: {cs04_det - cs04_tgt}")
    print(f"  Total detected: {cs04_det}")
    
    print("\nDQ-AC02")
    ac02_det = full_period_stats["DQ-AC02"]["fail"]
    ac02_tgt = PHASE2_TARGETS["DQ-AC02"]
    print(f"  Primary: {ac02_tgt}")
    print(f"  Secondary: {ac02_det - ac02_tgt}")
    print(f"  Total detected: {ac02_det}")

    print("============================================================")
    print("DQ engine complete. Outputs written to data/quality/")

if __name__ == "__main__":
    sales, valid_customers, valid_products, store_region_map = load_data()
    fails = evaluate_rules(sales, valid_customers, valid_products, store_region_map)
    generate_outputs(sales, fails)
