DROP TABLE IF EXISTS staging.sales CASCADE;
DROP TABLE IF EXISTS staging.stores CASCADE;
DROP TABLE IF EXISTS staging.customers CASCADE;
DROP TABLE IF EXISTS staging.products CASCADE;
DROP TABLE IF EXISTS staging.regions CASCADE;
DROP TABLE IF EXISTS staging.date CASCADE;

CREATE TABLE staging.regions AS
SELECT 
    TRIM(region_id) AS region_id,
    TRIM(region_name) AS region_name,
    TRIM(island) AS island
FROM raw.regions;

CREATE TABLE staging.stores AS
SELECT 
    TRIM(store_id) AS store_id,
    TRIM(store_name) AS store_name,
    TRIM(region_id) AS region_id,
    TRIM(city) AS city,
    TRIM(store_type) AS store_type,
    opening_date::DATE AS opening_date
FROM raw.stores;

CREATE TABLE staging.products AS
SELECT 
    TRIM(product_id) AS product_id,
    TRIM(product_name) AS product_name,
    TRIM(category) AS category,
    TRIM(subcategory) AS subcategory,
    TRIM(brand) AS brand,
    unit_cost::NUMERIC(10,2) AS unit_cost,
    list_price::NUMERIC(10,2) AS list_price
FROM raw.products;

CREATE TABLE staging.customers AS
SELECT 
    TRIM(customer_id) AS customer_id,
    TRIM(customer_name) AS customer_name,
    TRIM(gender) AS gender,
    TRIM(age_group) AS age_group,
    TRIM(city) AS city,
    TRIM(region_id) AS region_id,
    TRIM(customer_segment) AS customer_segment,
    registration_date::DATE AS registration_date
FROM raw.customers;

CREATE TABLE staging.date AS
SELECT 
    date::DATE AS date,
    year::INTEGER AS year,
    quarter::INTEGER AS quarter,
    month_number::INTEGER AS month_number,
    TRIM(month_name) AS month_name,
    week_number::INTEGER AS week_number,
    TRIM(day_name) AS day_name,
    is_weekend::BOOLEAN AS is_weekend
FROM raw.date;

CREATE TABLE staging.sales AS
SELECT 
    TRIM(transaction_id) AS transaction_id,
    NULLIF(TRIM(transaction_date), '')::DATE AS transaction_date,
    NULLIF(TRIM(customer_id), '') AS customer_id,
    NULLIF(TRIM(product_id), '') AS product_id,
    NULLIF(TRIM(store_id), '') AS store_id,
    NULLIF(TRIM(region_id), '') AS region_id,
    NULLIF(TRIM(quantity), '')::INTEGER AS quantity,
    NULLIF(TRIM(unit_price), '')::NUMERIC(12,2) AS unit_price,
    NULLIF(TRIM(discount_pct), '')::NUMERIC(5,2) AS discount_pct,
    NULLIF(TRIM(sales_amount), '')::NUMERIC(12,2) AS sales_amount,
    TRIM(payment_method) AS payment_method,
    TRIM(order_status) AS order_status
FROM raw.sales;
