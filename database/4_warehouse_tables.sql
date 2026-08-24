DROP TABLE IF EXISTS warehouse.fact_sales CASCADE;
DROP TABLE IF EXISTS warehouse.dim_store CASCADE;
DROP TABLE IF EXISTS warehouse.dim_customer CASCADE;
DROP TABLE IF EXISTS warehouse.dim_product CASCADE;
DROP TABLE IF EXISTS warehouse.dim_region CASCADE;
DROP TABLE IF EXISTS warehouse.dim_date CASCADE;

CREATE TABLE warehouse.dim_region (
    region_id TEXT PRIMARY KEY,
    region_name TEXT,
    island TEXT
);

CREATE TABLE warehouse.dim_store (
    store_id TEXT PRIMARY KEY,
    store_name TEXT,
    region_id TEXT REFERENCES warehouse.dim_region(region_id),
    city TEXT,
    store_type TEXT,
    opening_date DATE
);

CREATE TABLE warehouse.dim_product (
    product_id TEXT PRIMARY KEY,
    product_name TEXT,
    category TEXT,
    subcategory TEXT,
    brand TEXT,
    unit_cost NUMERIC(10,2),
    list_price NUMERIC(10,2)
);

CREATE TABLE warehouse.dim_customer (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT,
    gender TEXT,
    age_group TEXT,
    city TEXT,
    region_id TEXT REFERENCES warehouse.dim_region(region_id),
    customer_segment TEXT,
    registration_date DATE
);

CREATE TABLE warehouse.dim_date (
    date DATE PRIMARY KEY,
    year INTEGER,
    quarter INTEGER,
    month_number INTEGER,
    month_name TEXT,
    week_number INTEGER,
    day_name TEXT,
    is_weekend BOOLEAN
);

CREATE TABLE warehouse.fact_sales (
    sales_key BIGSERIAL PRIMARY KEY,
    transaction_id TEXT,
    transaction_date DATE,
    customer_id TEXT,
    product_id TEXT,
    store_id TEXT,
    region_id TEXT,
    quantity INTEGER,
    unit_price NUMERIC(12,2),
    discount_pct NUMERIC(5,2),
    sales_amount NUMERIC(12,2),
    payment_method TEXT,
    order_status TEXT
);

-- Load data from staging to warehouse
INSERT INTO warehouse.dim_region SELECT * FROM staging.regions;
INSERT INTO warehouse.dim_store SELECT * FROM staging.stores;
INSERT INTO warehouse.dim_product SELECT * FROM staging.products;
INSERT INTO warehouse.dim_customer SELECT * FROM staging.customers;
INSERT INTO warehouse.dim_date SELECT * FROM staging.date;
INSERT INTO warehouse.fact_sales (
    transaction_id, transaction_date, customer_id, product_id, 
    store_id, region_id, quantity, unit_price, discount_pct, 
    sales_amount, payment_method, order_status
)
SELECT 
    transaction_id, transaction_date, customer_id, product_id, 
    store_id, region_id, quantity, unit_price, discount_pct, 
    sales_amount, payment_method, order_status
FROM staging.sales;

-- Create required analytical indexes
CREATE INDEX idx_fact_sales_date ON warehouse.fact_sales(transaction_date);
CREATE INDEX idx_fact_sales_cust ON warehouse.fact_sales(customer_id);
CREATE INDEX idx_fact_sales_prod ON warehouse.fact_sales(product_id);
CREATE INDEX idx_fact_sales_store ON warehouse.fact_sales(store_id);
CREATE INDEX idx_fact_sales_region ON warehouse.fact_sales(region_id);
