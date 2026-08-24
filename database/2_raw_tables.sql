DROP TABLE IF EXISTS raw.sales CASCADE;
DROP TABLE IF EXISTS raw.stores CASCADE;
DROP TABLE IF EXISTS raw.customers CASCADE;
DROP TABLE IF EXISTS raw.products CASCADE;
DROP TABLE IF EXISTS raw.regions CASCADE;
DROP TABLE IF EXISTS raw.date CASCADE;

CREATE TABLE raw.regions (
    region_id TEXT,
    region_name TEXT,
    island TEXT
);

CREATE TABLE raw.stores (
    store_id TEXT,
    store_name TEXT,
    region_id TEXT,
    city TEXT,
    store_type TEXT,
    opening_date TEXT
);

CREATE TABLE raw.products (
    product_id TEXT,
    product_name TEXT,
    category TEXT,
    subcategory TEXT,
    brand TEXT,
    unit_cost TEXT,
    list_price TEXT
);

CREATE TABLE raw.customers (
    customer_id TEXT,
    customer_name TEXT,
    gender TEXT,
    age_group TEXT,
    city TEXT,
    region_id TEXT,
    customer_segment TEXT,
    registration_date TEXT
);

CREATE TABLE raw.date (
    date TEXT,
    year TEXT,
    quarter TEXT,
    month_number TEXT,
    month_name TEXT,
    week_number TEXT,
    day_name TEXT,
    is_weekend TEXT
);

CREATE TABLE raw.sales (
    transaction_id TEXT,
    transaction_date TEXT,
    customer_id TEXT,
    product_id TEXT,
    store_id TEXT,
    region_id TEXT,
    quantity TEXT,
    unit_price TEXT,
    discount_pct TEXT,
    sales_amount TEXT,
    payment_method TEXT,
    order_status TEXT
);
