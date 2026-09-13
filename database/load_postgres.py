import os
import time
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()
DB_URI = os.getenv("DB_URI")

def run_sql_file(conn, filepath):
    print(f"Executing {filepath}...")
    with open(filepath, 'r') as f:
        sql_script = f.read()
    with conn.cursor() as cur:
        cur.execute(sql_script)
    conn.commit()

def load_csv(conn, table_name, csv_path):
    print(f"Loading {csv_path} into {table_name}...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        with conn.cursor() as cur:
            cur.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER", f)
    conn.commit()

def run_validation(conn):
    print("\n============================================================")
    print("PHASE 4 FINAL AUDIT - DATABASE VALIDATION")
    print("============================================================")
    
    with conn.cursor() as cur:
        # Check counts
        cur.execute("SELECT count(*) FROM raw.sales")
        raw_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM warehouse.fact_sales")
        fact_count = cur.fetchone()[0]
        print(f"raw.sales count:            {raw_count}")
        print(f"warehouse.fact_sales count: {fact_count}")
        assert raw_count == 100000, "raw.sales must have 100,000 rows"
        assert fact_count == 100000, "fact_sales must have 100,000 rows"
        
        # Check intentional duplicates
        cur.execute("SELECT count(*) FROM (SELECT transaction_id FROM warehouse.fact_sales GROUP BY transaction_id HAVING count(*) > 1) AS sub")
        dup_count = cur.fetchone()[0]
        print(f"Duplicate transaction IDs:  {dup_count}")
        assert dup_count > 0, "DQ-UN01 failed: duplicates missing"
        
        # Quality Schema Validations
        cur.execute("SELECT count(*) FROM quality.dim_dq_rule")
        rules_count = cur.fetchone()[0]
        assert rules_count == 15, "Expected 15 rules in dim_dq_rule"
        print("quality.dim_dq_rule count:  15 (Verified)")
        
        # Result ID Uniqueness
        cur.execute("SELECT count(*), count(DISTINCT result_id) FROM quality.dq_result")
        tot_res, unq_res = cur.fetchone()
        assert tot_res == unq_res, "result_id is not unique in dq_result"
        print(f"dq_result rows unique ID:   {tot_res} (Verified)")
        
        # FK constraints are already enforced via DDL, but we can verify status
        cur.execute("SELECT count(*) FROM quality.dq_issue_detail WHERE status NOT IN ('FAIL', 'WARNING')")
        invalid_status = cur.fetchone()[0]
        assert invalid_status == 0, "Found issues with status other than FAIL/WARNING"
        print("dq_issue_detail statuses:   All FAIL/WARNING (Verified)")
        
        # Duplicate distinction check
        # source_row_id belongs to quality.dq_issue_detail,
        # not warehouse.fact_sales.
        cur.execute("""
            SELECT
                COUNT(DISTINCT source_row_id),
                COUNT(DISTINCT transaction_id)
            FROM quality.dq_issue_detail
            WHERE rule_id = 'DQ-UN01'
        """)
        dup_source_rows, dup_transaction_ids = cur.fetchone()

        assert dup_transaction_ids == dup_count, (
            "DQ-UN01 transaction IDs in issue detail do not match warehouse duplicates"
        )

        assert dup_source_rows == dup_count * 2, (
            "DQ-UN01 should preserve both physical rows for each duplicate transaction ID"
        )

        print(
            f"Distinguishable duplicates: {dup_source_rows} unique source_row_ids "
            f"across {dup_transaction_ids} duplicate transaction IDs (Verified)"
        )

        # Ensure every DQ issue has a traceable physical source row
        cur.execute("""
            SELECT COUNT(*)
            FROM quality.dq_issue_detail
            WHERE source_row_id IS NULL
        """)
        null_source_rows = cur.fetchone()[0]

        assert null_source_rows == 0, (
            "Some DQ issue records are missing source_row_id"
        )

        print("DQ issue source_row_id:     All populated (Verified)")

    print("============================================================")
    print("Database validation PASSED. All intentional DQ issues preserved.")
    print("============================================================\n")

def main():
    # Wait for DB to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(DB_URI)
            print("Connected to PostgreSQL successfully.")
            break
        except psycopg2.OperationalError:
            print(f"Waiting for database to start... ({i+1}/{max_retries})")
            time.sleep(2)
    else:
        print("Failed to connect to PostgreSQL.")
        return

    try:
        run_sql_file(conn, "database/1_schemas.sql")
        run_sql_file(conn, "database/2_raw_tables.sql")
        
        # Load Raw
        load_csv(conn, "raw.regions", "data/raw/regions.csv")
        load_csv(conn, "raw.stores", "data/raw/stores.csv")
        load_csv(conn, "raw.products", "data/raw/products.csv")
        load_csv(conn, "raw.customers", "data/raw/customers.csv")
        load_csv(conn, "raw.date", "data/raw/date.csv")
        load_csv(conn, "raw.sales", "data/raw/sales.csv")
        
        # Transform & Staging -> Warehouse
        run_sql_file(conn, "database/3_staging_tables.sql")
        run_sql_file(conn, "database/4_warehouse_tables.sql")
        
        # Quality Schema & Load
        run_sql_file(conn, "database/5_quality_tables.sql")
        load_csv(conn, "quality.dq_result", "data/quality/dq_result.csv")
        load_csv(conn, "quality.dq_issue_detail", "data/quality/dq_issue_detail.csv")
        
        run_validation(conn)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
