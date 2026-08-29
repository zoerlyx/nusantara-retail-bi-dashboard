# Data Dictionary — Nusantara Retail

## 1. Overview

This document defines the structure, meaning, and purpose of the data used by the **Nusantara Retail — Data Quality & Business Monitoring Dashboard**.

The project uses four PostgreSQL schemas:

```text
raw
staging
warehouse
quality
```

Power BI consumes only the analytical schemas:

```text
warehouse
quality
```

The `raw` and `staging` schemas support data loading, standardization, and data-quality processing.

For system architecture, see [System Architecture](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/architecture.md).

For business requirements and KPI definitions, see [Business Requirements](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/business_requirements.md).

For detailed DQ rules, see [Data Quality Rules](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/dq_rules.md).

---

## 2. Dataset Overview

| Dataset | Rows | Purpose |
|---|---:|---|
| `sales.csv` | 100,000 | Transaction-level sales data |
| `customers.csv` | 15,000 | Customer master data |
| `products.csv` | 500 | Product master data |
| `stores.csv` | 30 | Store master data |
| `regions.csv` | 8 | Regional master data |
| `date.csv` | 365 | Official date dimension source |
| `dq_result.csv` | 5,640 | Daily aggregated DQ results |
| `dq_issue_detail.csv` | 9,738 | Record-level DQ issues |

Business period:

```text
2025-01-01 → 2025-12-31
```

Dataset generator:

```text
generate_dataset.py
```

Deterministic seed:

```text
SEED = 2025
```

The six Phase 2 CSV files are the source dataset for subsequent processing stages.

---

## 3. Raw Layer

The `raw` schema contains the generated CSV data loaded into PostgreSQL.

The raw layer intentionally does not enforce strict business constraints that would reject invalid or inconsistent records before they can be evaluated by the Data Quality Engine.

### 3.1 `raw.sales`

**Purpose:** Raw transaction-level sales data.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `transaction_id` | TEXT | Business ID | Transaction identifier. May contain duplicate values for DQ testing. |
| `transaction_date` | TEXT | Date reference | Transaction date. |
| `customer_id` | TEXT | Customer reference | Customer identifier. May be NULL or orphaned because of DQ injections. |
| `product_id` | TEXT | Product reference | Product identifier. May be NULL or orphaned because of DQ injections. |
| `store_id` | TEXT | Store reference | Store identifier. |
| `region_id` | TEXT | Business attribute | Region recorded on the transaction. |
| `quantity` | TEXT | Measure | Number of products purchased. |
| `unit_price` | TEXT | Measure | Selling price per unit. |
| `discount_pct` | TEXT | Measure | Discount percentage represented from 0 to 100. |
| `sales_amount` | TEXT | Measure | Recorded transaction amount. |
| `payment_method` | TEXT | Attribute | Payment method. |
| `order_status` | TEXT | Attribute | Transaction order status. |

#### Sales Amount Business Calculation

Expected transaction amount:

```text
quantity
× unit_price
× (1 - discount_pct / 100)
```

DQ-CS04 uses a maximum difference of:

```text
Rp1
```

as rounding tolerance.

The complete DQ rule definition is maintained in [Data Quality Rules](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/dq_rules.md).

### 3.2 `raw.customers`

**Purpose:** Raw customer master data.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `customer_id` | TEXT | Primary identifier | Unique customer identifier. |
| `customer_name` | TEXT | Attribute | Customer name. |
| `gender` | TEXT | Attribute | Gender category. |
| `age_group` | TEXT | Attribute | Customer age group. |
| `city` | TEXT | Attribute | Customer city. |
| `region_id` | TEXT | Region reference | Customer region identifier. |
| `customer_segment` | TEXT | Attribute | Customer segment: New, Regular, or Loyal. |
| `registration_date` | TEXT | Attribute | Customer registration date. |

### 3.3 `raw.products`

**Purpose:** Raw product master data.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `product_id` | TEXT | Primary identifier | Unique product identifier. |
| `product_name` | TEXT | Attribute | Product name. |
| `category` | TEXT | Attribute | Product category. |
| `subcategory` | TEXT | Attribute | Product subcategory. |
| `brand` | TEXT | Attribute | Product brand. |
| `unit_cost` | TEXT | Measure | Product unit cost. |
| `list_price` | TEXT | Measure | Product list price. |

### 3.4 `raw.stores`

**Purpose:** Raw store master data.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `store_id` | TEXT | Primary identifier | Unique store identifier. |
| `store_name` | TEXT | Attribute | Store name. |
| `region_id` | TEXT | Region reference | Region assigned to the store. |
| `city` | TEXT | Attribute | Store city. |
| `store_type` | TEXT | Attribute | Flagship, Standard, or Outlet. |
| `opening_date` | TEXT | Attribute | Store opening date. |

### 3.5 `raw.regions`

**Purpose:** Raw regional master data.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `region_id` | TEXT | Primary identifier | Unique region identifier. |
| `region_name` | TEXT | Attribute | Business region name. |
| `island` | TEXT | Attribute | Island group. |

### 3.6 `raw.date`

**Purpose:** Source data for the official date dimension.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `date` | TEXT | Primary identifier | Calendar date. |
| `year` | TEXT | Attribute | Calendar year. |
| `quarter` | TEXT | Attribute | Calendar quarter. |
| `month_number` | TEXT | Attribute | Numeric month number. |
| `month_name` | TEXT | Attribute | Month name. |
| `week_number` | TEXT | Attribute | Calendar week number. |
| `day_name` | TEXT | Attribute | Day name. |
| `is_weekend` | TEXT | Attribute | Weekend indicator. |

---

## 4. Staging Layer

The `staging` schema contains standardized versions of the raw tables before they are loaded into the analytical model.

Typical representation-level transformations include:

```text
TRIM whitespace
NULL normalization
DATE casting
INTEGER casting
NUMERIC casting
BOOLEAN casting
Text normalization
```

The staging layer does **not silently repair business-quality issues**.

For example:

```text
Raw:
quantity = -5

Staging:
quantity = -5
```

The invalid business value remains available for DQ validation.

The staging layer is therefore responsible for representation standardization, not business-quality correction.

---

## 5. Warehouse Layer

The `warehouse` schema contains the analytical star schema used by Power BI.

```text
warehouse
│
├── fact_sales
├── dim_date
├── dim_customer
├── dim_product
├── dim_store
└── dim_region
```

---

## 6. `warehouse.fact_sales`

**Purpose:** Central transaction fact table.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `sales_key` | BIGSERIAL | Primary Key | Technical warehouse row identifier. |
| `transaction_id` | TEXT | Business ID | Business transaction identifier. Intentionally not unique. |
| `transaction_date` | DATE | Date reference | Transaction date. |
| `customer_id` | TEXT | Customer reference | Customer identifier. May be NULL or orphaned. |
| `product_id` | TEXT | Product reference | Product identifier. May be NULL or orphaned. |
| `store_id` | TEXT | Store reference | Store identifier. |
| `region_id` | TEXT | Business attribute | Region stored on the transaction. |
| `quantity` | INTEGER | Measure | Quantity purchased. |
| `unit_price` | NUMERIC(12,2) | Measure | Unit transaction price. |
| `discount_pct` | NUMERIC(5,2) | Measure | Discount percentage. |
| `sales_amount` | NUMERIC(12,2) | Measure | Recorded transaction amount. |
| `payment_method` | TEXT | Attribute | Payment method. |
| `order_status` | TEXT | Attribute | Order status. |

### Key Design

`transaction_id` is intentionally not the primary key.

```text
sales_key
    ↓
Technical / physical warehouse row identity

transaction_id
    ↓
Business transaction identifier
```

This allows the warehouse to preserve duplicate transaction IDs for DQ monitoring.

---

## 7. `warehouse.dim_customer`

**Purpose:** Customer dimension for customer analysis and segmentation.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `customer_id` | TEXT | Primary Key | Unique customer identifier. |
| `customer_name` | TEXT | Attribute | Customer name. |
| `gender` | TEXT | Attribute | Gender category. |
| `age_group` | TEXT | Attribute | Age group. |
| `city` | TEXT | Attribute | Customer city. |
| `region_id` | TEXT | Foreign Key | Customer region. |
| `customer_segment` | TEXT | Attribute | New, Regular, or Loyal. |
| `registration_date` | DATE | Attribute | Customer registration date. |

---

## 8. `warehouse.dim_product`

**Purpose:** Product dimension for category, product, and revenue analysis.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `product_id` | TEXT | Primary Key | Unique product identifier. |
| `product_name` | TEXT | Attribute | Product name. |
| `category` | TEXT | Attribute | Product category. |
| `subcategory` | TEXT | Attribute | Product subcategory. |
| `brand` | TEXT | Attribute | Product brand. |
| `unit_cost` | NUMERIC(10,2) | Measure | Product unit cost. |
| `list_price` | NUMERIC(10,2) | Measure | Product list price. |

---

## 9. `warehouse.dim_store`

**Purpose:** Store dimension for store and regional analysis.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `store_id` | TEXT | Primary Key | Unique store identifier. |
| `store_name` | TEXT | Attribute | Store name. |
| `region_id` | TEXT | Foreign Key | Region assigned to the store. |
| `city` | TEXT | Attribute | Store city. |
| `store_type` | TEXT | Attribute | Flagship, Standard, or Outlet. |
| `opening_date` | DATE | Attribute | Store opening date. |

Relationship:

```text
dim_region
    1
    ↓
dim_store
    *
```

---

## 10. `warehouse.dim_region`

**Purpose:** Geographic dimension for regional analysis.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `region_id` | TEXT | Primary Key | Unique region identifier. |
| `region_name` | TEXT | Attribute | Region name. |
| `island` | TEXT | Attribute | Island group. |

Hierarchy:

```text
Island Group
    ↓
Region
    ↓
Store
```

---

## 11. `warehouse.dim_date`

**Purpose:** Official date dimension used for time-based analysis.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `date` | DATE | Primary Key | Calendar date. |
| `year` | INTEGER | Attribute | Calendar year. |
| `quarter` | INTEGER | Attribute | Calendar quarter. |
| `month_number` | INTEGER | Attribute | Numeric month number. |
| `month_name` | TEXT | Attribute | Month name. |
| `week_number` | INTEGER | Attribute | Calendar week number. |
| `day_name` | TEXT | Attribute | Day name. |
| `is_weekend` | BOOLEAN | Attribute | Weekend indicator. |

`dim_date` is the conformed date dimension for:

```text
fact_sales
dq_result
dq_issue_detail
```

In Power BI, `dim_date[date]` is used as the official Date Table.

---

## 12. Quality Layer

The `quality` schema contains the analytical Data Quality model.

```text
quality
│
├── dim_dq_rule
├── dq_result
└── dq_issue_detail
```

Detailed rule logic, dimensions, severity, thresholds, and validation behavior are documented in [Data Quality Rules](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/dq_rules.md).

---

## 13. `quality.dim_dq_rule`

**Purpose:** Definition and metadata for the 15 implemented DQ rules.

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `rule_id` | TEXT | Primary Key | Unique DQ rule identifier. |
| `rule_name` | TEXT | Attribute | Human-readable rule name. |
| `dimension` | TEXT | Attribute | DQ dimension. |
| `severity` | TEXT | Attribute | Critical, High, Medium, or Low. |
| `description` | TEXT | Attribute | Rule description. |
| `target_table` | TEXT | Metadata | Target table evaluated by the rule. |
| `target_column` | TEXT | Metadata | Target column evaluated by the rule. |

Final implemented rule count:

```text
15
```

---

## 14. `quality.dq_result`

**Purpose:** Aggregated Data Quality validation results.

### Grain

```text
One row per:
rule_id + result_date
```

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `result_id` | TEXT | Primary Key | Unique identifier for one rule/date result. |
| `rule_id` | TEXT | Foreign Key | DQ rule being evaluated. |
| `result_date` | TIMESTAMP | Date | Business validation date. |
| `dimension` | TEXT | Attribute | DQ dimension. |
| `severity` | TEXT | Attribute | Rule severity. |
| `total_records` | INTEGER | Measure | Number of records/rule checks evaluated for that date. |
| `pass_count` | INTEGER | Measure | Number of PASS results. |
| `fail_count` | INTEGER | Measure | Number of FAIL results. |
| `warning_count` | INTEGER | Measure | Number of WARNING results. |
| `failure_rate` | NUMERIC | Measure | Failed rule checks / total rule checks. |
| `warning_rate` | NUMERIC | Measure | Warning rule checks / total rule checks. |
| `dq_score` | NUMERIC | Measure | PASS count / total records. |

### Important Terminology

```text
dq_result.total_records
```

represents rule checks, not unique business records.

Therefore:

```text
Rule Checks
≠
Business Transactions
```

---

## 15. `quality.dq_issue_detail`

**Purpose:** Record-level Data Quality issue investigation and traceability.

### Grain

```text
One row per:
Physical Source Record × DQ Issue
```

| Column | Data Type | Key / Role | Description |
|---|---|---|---|
| `issue_id` | TEXT | Primary Key | Unique issue identifier. |
| `result_id` | TEXT | Foreign Key | Associated DQ result row. |
| `source_row_id` | INTEGER | Traceability ID | Physical source row identifier generated by the DQ Engine. |
| `transaction_id` | TEXT | Business ID | Business transaction identifier. |
| `rule_id` | TEXT | Foreign Key | DQ rule that detected the issue. |
| `issue_date` | TIMESTAMP | Date | Original business transaction date. |
| `status` | TEXT | Attribute | FAIL or WARNING for issue records. |
| `severity` | TEXT | Attribute | Rule severity. |
| `issue_value` | TEXT | Attribute | Actual problematic value. |
| `expected_value` | TEXT | Attribute | Expected value or expected condition. |
| `issue_description` | TEXT | Attribute | Actionable description of the issue. |

### Traceability

`source_row_id` is required because:

```text
transaction_id
```

is intentionally not unique.

The final audited duplicate condition is:

```text
300 duplicate transaction IDs
600 participating physical records
```

---

## 16. Data Relationships

The analytical data model uses the following logical relationships.

### 16.1 Business Relationships

```text
dim_date
    1
    ↓
fact_sales
    *

dim_customer
    1
    ↓
fact_sales
    *

dim_product
    1
    ↓
fact_sales
    *

dim_store
    1
    ↓
fact_sales
    *

dim_region
    1
    ↓
dim_store
    *
```

### 16.2 Data Quality Relationships

```text
dim_date
    1
    ↓
dq_result
    *

dim_date
    1
    ↓
dq_issue_detail
    *

dim_dq_rule
    1
    ↓
dq_result
    *

dim_dq_rule
    1
    ↓
dq_issue_detail
    *
```

These describe the analytical model. The Power BI relationship configuration is documented in [System Architecture](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/architecture.md).

---

## 17. Data Interpretation Principles

The project intentionally distinguishes several concepts.

### 17.1 Business Transaction vs Physical Record

```text
Business Transaction
        ≠
Physical Record
```

because duplicate `transaction_id` values exist.

`transaction_id` represents the business identifier, while `source_row_id` provides physical source-record traceability for DQ issues.

---

### 17.2 Rule Check vs Business Record

```text
Rule Check
        ≠
Business Record
```

A single business record can be evaluated against multiple DQ rules.

Therefore, aggregated DQ counts must not automatically be interpreted as counts of unique business records.

---

### 17.3 DQ Issue vs Business Metric

```text
DQ Issue
        ≠
Invalid Business Metric
```

Not every data quality issue automatically makes every business KPI unusable.

The analytical solution therefore separates:

```text
Business Performance
Data Quality
Data Reliability
```

while allowing their controlled relationship in the BI semantic model.

---

## 18. Final Verified Data Facts

The completed implementation verified:

```text
Sales rows                 = 100,000
Customers                  = 15,000
Products                   = 500
Stores                     = 30
Regions                    = 8
Date records               = 365

DQ Rules                   = 15
DQ Result Rows             = 5,640
DQ Issue Detail Rows       = 9,738

Duplicate Transaction IDs  = 300
Duplicate Physical Rows    = 600
```

The final PostgreSQL validation also confirmed:

```text
raw.sales                  = 100,000
warehouse.fact_sales       = 100,000
quality.dim_dq_rule        = 15
dq_result IDs              = unique
DQ source_row_id           = populated
```

The Overall DQ Score and other business/quality KPIs are defined and governed separately in [Business Requirements](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/business_requirements.md).

---

## 19. Data Model Summary

The project supports the following analytical structure:

```text
                        dim_date
                           │
                           ▼
dim_customer ──────── fact_sales ──────── dim_product
                           ▲
                           │
                       dim_store
                           ▲
                           │
                       dim_region


                        dim_date
                       /       \
                      ▼         ▼
                 dq_result   dq_issue_detail
                      ▲         ▲
                      │         │
                 dim_dq_rule ───┘
```

The model separates business transactions from DQ monitoring while maintaining shared dimensions and traceability where appropriate.

---

## 20. Summary

The data model provides a consistent representation from generated source data through analytical warehouse and quality layers:

```text
Raw Data
   ↓
Staging Data
   ↓
Business Warehouse
   +
Quality Model
   ↓
Power BI Analytical Model
```

The key principle is:

> **The data model preserves the distinction between business data, physical source records, rule evaluations, and Data Quality issues so that analytical results remain traceable and interpretable.**