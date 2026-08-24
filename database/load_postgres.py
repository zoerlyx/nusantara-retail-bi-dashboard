import os
import time
import psycopg2
from psycopg2 import sql

DB_URI = "postgresql://admin:password@localhost:15432/nusantara_retail"

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
    print("PHASE 4: DATABASE VALIDATION AUDIT")
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
        
        # Check CS04 logic preservation
        cur.execute("SELECT count(*) FROM quality.dq_issue_detail WHERE rule_id = 'DQ-CS04'")
        cs04_count = cur.fetchone()[0]
        print(f"DQ-CS04 issues detected:    {cs04_count}")
        assert cs04_count > 0, "DQ-CS04 failed: incorrect math missing"
        
        # AC01 cases exist
        cur.execute("SELECT count(*) FROM quality.dq_issue_detail WHERE rule_id = 'DQ-AC01'")
        ac01_count = cur.fetchone()[0]
        print(f"DQ-AC01 issues detected:    {ac01_count}")
        assert ac01_count > 0, "DQ-AC01 failed: missing"
        
        # CN01 missing customers
        cur.execute("SELECT count(*) FROM warehouse.fact_sales WHERE customer_id IS NULL")
        missing_customers = cur.fetchone()[0]
        print(f"NULL customer IDs:          {missing_customers}")
        assert missing_customers > 0, "DQ-CN01 failed"
        
        # CS01 orphan customers
        cur.execute("SELECT count(*) FROM warehouse.fact_sales fs LEFT JOIN warehouse.dim_customer dc ON fs.customer_id = dc.customer_id WHERE fs.customer_id IS NOT NULL AND dc.customer_id IS NULL")
        orphan_customers = cur.fetchone()[0]
        print(f"Orphan customers:           {orphan_customers}")
        assert orphan_customers > 0, "DQ-CS01 failed"
        
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
