# Nusantara Retail — Data Quality & Business Monitoring Dashboard

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)
![Faker](https://img.shields.io/badge/Faker-Data%20Generation-6C5CE7?style=flat-square)

> An end-to-end Business Intelligence solution that monitors retail business performance while measuring the reliability of the data used to report it.

## 1. Project Overview

**Nusantara Retail** is a fictional omnichannel retail company operating across multiple regions in Indonesia.

This project addresses two connected questions:

```text
1. How is the business performing?
2. How reliable is the data behind that performance?
```

The solution combines:

```text
Business Performance
        +
Data Quality
        +
Data Reliability
```

into a single BI workflow.

**Role:** BI Developer

**Domain:** Retail / Omnichannel Retail

**Business Period:** January–December 2025

---

## 2. Key Capabilities

### Business Performance

- Revenue and revenue trend monitoring
- Order and customer analysis
- Average Order Value (AOV)
- Regional and store performance
- Product and category performance
- Customer segment analysis
- Payment method analysis

### Data Quality

- Missing-value detection
- Value and range validation
- Referential and relationship consistency checks
- Duplicate transaction detection
- Transaction calculation validation
- Business-logic validation
- Record-level issue traceability

### Data Reliability

- Overall DQ Score
- Data Health Status
- Data Reliability
- Affected Transactions
- Affected Records
- Affected Revenue
- Business exposure to data-quality issues

---

## 3. Solution Architecture

```text
┌──────────────────────────┐
│ Python Dataset Generator │
│    generate_dataset.py   │
│       SEED = 2025        │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│      Raw CSV Dataset     │
│  100K transaction rows   │
│      + master data       │
└────────────┬─────────────┘
             │
             ├─────────────────────┐
             │                     │
             ▼                     ▼
┌─────────────────────┐   ┌────────────────────────┐
│   Data Quality      │   │      PostgreSQL        │
│      Engine         │   │                        │
│     15 DQ Rules     │   │ raw → staging          │
│   PASS / FAIL       │   │     → warehouse        │
│   source_row_id     │   │     → quality          │
└──────────┬──────────┘   └───────────┬────────────┘
           │                          │
           ▼                          │
┌─────────────────────┐               │
│   DQ Output Files   │───────────────┘
│                     │
│ dq_result.csv       │
│ dq_issue_detail.csv │
└─────────────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │   Power BI Semantic    │
                         │         Model          │
                         │                        │
                         │ Business Model         │
                         │ Data Quality Model     │
                         │ Conformed Date         │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │       DAX / KPI        │
                         │ Business + DQ +        │
                         │ Reliability Measures   │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │      Power BI Report   │
                         │                        │
                         │ 01 Executive Overview  │
                         │ 02 Data Health         │
                         │ 03 DQ Details          │
                         │ 04 Business Analysis   │
                         └────────────────────────┘
```

For the full technical architecture, see `docs/architecture.md`.

---

## 4. Dataset

The dataset is deterministic and generated with:

```text
SEED = 2025
```

### Business Data

| Dataset | Rows | Purpose |
|---|---:|---|
| `sales.csv` | 100,000 | Transaction-level sales |
| `customers.csv` | 15,000 | Customer master |
| `products.csv` | 500 | Product master |
| `stores.csv` | 30 | Store master |
| `regions.csv` | 8 | Regional master |
| `date.csv` | 365 | Official 2025 date dimension |

### Data Quality Outputs

| Dataset | Rows | Purpose |
|---|---:|---|
| `dq_result.csv` | 5,640 | Daily aggregated DQ results |
| `dq_issue_detail.csv` | 9,738 | Record-level DQ issues |

The six generated Phase 2 CSV files are the source dataset for subsequent processing stages.

For dataset structure and field definitions, see `docs/data_dictionary.md`.

---

## 5. Data Quality Framework

The project implements **15 DQ rules** across five primary dimensions:

```text
Completeness
Validity
Consistency
Uniqueness
Accuracy
```

---

## 6. Key Data Quality Characteristics

The project intentionally preserves defective data instead of silently removing it.

For example:

```text
100,000 physical sales rows
300 duplicate transaction IDs
600 physical rows participating in duplicate IDs
```

Because `transaction_id` is intentionally non-unique, physical record traceability is maintained through:

```text
source_row_id
```

The DQ Engine also allows natural secondary detections.

Verified examples:

```text
DQ-CS04
Primary injections = 700
Detected failures = 2,200

DQ-AC02
Primary injections = 300
Detected failures = 1,338
```

These additional detections are expected consequences of interactions between data-quality problems.

---

## 7. PostgreSQL Data Architecture

PostgreSQL uses four schemas:

```text
raw
staging
warehouse
quality
```

```text
raw
↓
Preserve source data

staging
↓
Standardize representation

warehouse
↓
Analytical business model

quality
↓
Analytical DQ model
```

Power BI consumes only:

```text
warehouse
quality
```

The analytical warehouse uses a star schema centered on:

```text
warehouse.fact_sales
```

with:

```text
dim_date
dim_customer
dim_product
dim_store
dim_region
```

The quality model contains:

```text
dim_dq_rule
dq_result
dq_issue_detail
```

For the detailed data model and technical architecture, see `docs/data_dictionary.md` and `docs/architecture.md`.

---

## 8. Power BI Dashboard

The final Power BI report contains four pages:

### 01 — Executive Overview

Combines:

```text
Business Performance
+
Data Health
+
Data Reliability
```

### 02 — Data Health

Focuses on:

```text
Overall DQ Score
Failure Rate
Critical Failures
DQ Trends
Failed Rules
Dimensions
Severity
```

### 03 — Data Quality Details

Provides record-level investigation through:

```text
Dimension
Severity
Rule
Status
Issue Detail
Drill-through
```

### 04 — Business Analysis

Explores:

```text
Revenue
Revenue Growth
Orders
AOV
Region
Store
Category
Product
Payment Method
Customer Segment
```

---

## 9. Verified Results

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

Overall DQ Score           = 99.35%
```

Under the project-defined thresholds:

```text
Data Health Status = Healthy
Data Reliability   = High
```

The DQ Score is a **project-defined metric**, not a universal industry standard.

---

## 10. Repository Structure

```text
nusantara-retail-bi-dashboard/

├── data/
│   ├── raw/
│   └── quality/
│
├── database/
│   ├── 1_schemas.sql
│   ├── 2_raw_tables.sql
│   ├── 3_staging_tables.sql
│   ├── 4_warehouse_tables.sql
│   ├── 5_quality_tables.sql
│   └── load_postgres.py
│
├── powerbi/
│   ├── dashboard.pbix
│   └── screenshots/
│
├── docs/
│   ├── architecture.md
│   ├── business_requirements.md
│   ├── data_dictionary.md
│   └── dq_rules.md
│
├── generate_dataset.py
├── dq_engine.py
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .gitignore
```

Generated datasets can be reproduced from `generate_dataset.py`, so large generated CSV files do not need to be committed when repository policy excludes them.

---

## 11. Documentation

Detailed documentation is separated by responsibility:

| Document | Purpose |
|---|---|
| `business_requirements.md` | Business context, objectives, questions, KPIs, dashboard requirements, and success criteria |
| `architecture.md` | Technical architecture, data flow, processing layers, semantic model, and implementation structure |
| `data_dictionary.md` | Dataset, table, column, grain, key, and data-model definitions |
| `dq_rules.md` | DQ rule catalogue, validation logic, severity, scoring, and DQ evaluation principles |

---

## 12. How to Run

### 1. Generate the Dataset

```bash
python generate_dataset.py
```

This recreates the deterministic Phase 2 dataset.

### 2. Run the Data Quality Engine

```bash
python dq_engine.py
```

Outputs:

```text
data/quality/dq_result.csv
data/quality/dq_issue_detail.csv
```

### 3. Start PostgreSQL

```bash
docker compose up -d
```

PostgreSQL is exposed locally through:

```text
localhost:15432
```

### 4. Load PostgreSQL

```bash
python database/load_postgres.py
```

The loader creates the PostgreSQL schemas and loads the source and analytical data layers.

### 5. Connect Power BI

Use:

```text
Server:   localhost:15432
Database: (nama_database)
```

Load the analytical tables from:

```text
warehouse
quality
```

---

## 13. Technology Stack

### Data

```text
Python
Pandas
NumPy
Faker
```

### Database

```text
PostgreSQL
SQL
Docker
psycopg2
```

### Business Intelligence

```text
Power BI
Power Query
DAX
```

### Version Control

```text
Git
GitHub
```

---

## 14. Limitations

This is a synthetic portfolio project.

Therefore:

- The dataset is not sourced from a production operational system.
- Data-quality problems are intentionally injected for monitoring and validation.
- DQ thresholds and severity weights are project-defined.
- Business findings are limited to the synthetic 2025 dataset.
- The project demonstrates the BI and monitoring workflow rather than production-scale orchestration.

---

## 15. Future Improvements

Potential production-oriented extensions include:

```text
Automated scheduled DQ runs
Critical DQ alerts
Incremental loading
Automated Power BI refresh
Integration with production data sources
Production-grade orchestration
```

These are future extensions and are not represented as current project capabilities.

---

## 17. Core Principle

The project is built around one principle:

> **Business performance should be analyzed together with the reliability of the data used to measure it.**

The final solution therefore connects:

```text
Data
 ↓
Quality
 ↓
Business Performance
 ↓
Reliability
 ↓
Decision
```

The goal is not only to produce business numbers, but to provide the context required to understand how trustworthy those numbers are.

## 18. Author

**Fardho Z.**  
Data Analyst | BI Engineer

---

<p align="center">
  © 2026 Fardho Z.
</p>
