DROP TABLE IF EXISTS quality.dq_issue_detail CASCADE;
DROP TABLE IF EXISTS quality.dq_result CASCADE;
DROP TABLE IF EXISTS quality.dim_dq_rule CASCADE;

CREATE TABLE quality.dim_dq_rule (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT,
    dimension TEXT,
    severity TEXT,
    description TEXT,
    target_table TEXT,
    target_column TEXT
);

INSERT INTO quality.dim_dq_rule (rule_id, rule_name, dimension, severity, description, target_table, target_column) VALUES
('DQ-CN01', 'Missing Customer ID', 'Completeness', 'High', 'Customer ID is null', 'fact_sales', 'customer_id'),
('DQ-CN02', 'Missing Product ID', 'Completeness', 'High', 'Product ID is null', 'fact_sales', 'product_id'),
('DQ-CN03', 'Missing Transaction Date', 'Completeness', 'Critical', 'Transaction Date is null', 'fact_sales', 'transaction_date'),
('DQ-VL01', 'Invalid Quantity', 'Validity', 'High', 'Quantity <= 0', 'fact_sales', 'quantity'),
('DQ-VL02', 'Invalid Unit Price', 'Validity', 'High', 'Unit price < 0', 'fact_sales', 'unit_price'),
('DQ-VL03', 'Invalid Discount', 'Validity', 'Medium', 'Discount outside 0-100', 'fact_sales', 'discount_pct'),
('DQ-VL04', 'Invalid Payment Method', 'Validity', 'Medium', 'Unrecognized payment method', 'fact_sales', 'payment_method'),
('DQ-CS01', 'Orphan Customer', 'Consistency', 'High', 'Customer ID not in dim_customer', 'fact_sales', 'customer_id'),
('DQ-CS02', 'Orphan Product', 'Consistency', 'High', 'Product ID not in dim_product', 'fact_sales', 'product_id'),
('DQ-CS03', 'Store-Region Mismatch', 'Consistency', 'High', 'Region ID does not match store master', 'fact_sales', 'region_id'),
('DQ-CS04', 'Incorrect Sales Amount', 'Consistency', 'Critical', 'Sales amount fails math logic', 'fact_sales', 'sales_amount'),
('DQ-UN01', 'Duplicate Transaction ID', 'Uniqueness', 'Critical', 'Duplicate transaction ID', 'fact_sales', 'transaction_id'),
('DQ-AC01', 'Completed + Non-positive Amt', 'Accuracy', 'High', 'Order completed but amt <= 0', 'fact_sales', 'sales_amount'),
('DQ-AC02', 'Abnormal Sales Amount', 'Accuracy', 'Medium', 'Sales amount > 2x expected', 'fact_sales', 'sales_amount'),
('DQ-AC03', 'Out-of-period Date', 'Accuracy', 'Critical', 'Transaction date outside 2025', 'fact_sales', 'transaction_date');

CREATE TABLE quality.dq_result (
    result_id TEXT PRIMARY KEY,
    rule_id TEXT REFERENCES quality.dim_dq_rule(rule_id),
    result_date TIMESTAMP,
    dimension TEXT,
    severity TEXT,
    total_records INTEGER,
    pass_count INTEGER,
    fail_count INTEGER,
    warning_count INTEGER,
    failure_rate NUMERIC,
    warning_rate NUMERIC,
    dq_score NUMERIC
);

CREATE TABLE quality.dq_issue_detail (
    issue_id TEXT PRIMARY KEY,
    result_id TEXT REFERENCES quality.dq_result(result_id),
    source_row_id INTEGER,
    transaction_id TEXT,
    rule_id TEXT REFERENCES quality.dim_dq_rule(rule_id),
    issue_date TIMESTAMP,
    status TEXT,
    severity TEXT,
    issue_value TEXT,
    expected_value TEXT,
    issue_description TEXT
);

-- Analytical indexes for quality tables
CREATE INDEX idx_dq_result_date ON quality.dq_result(result_date);
CREATE INDEX idx_dq_result_rule ON quality.dq_result(rule_id);
CREATE INDEX idx_dq_issue_txn ON quality.dq_issue_detail(transaction_id);
CREATE INDEX idx_dq_issue_rule ON quality.dq_issue_detail(rule_id);
CREATE INDEX idx_dq_issue_date ON quality.dq_issue_detail(issue_date);
