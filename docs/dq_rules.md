# Data Quality Rules — Nusantara Retail

## 1. Overview

This document defines the Data Quality (DQ) rule catalogue used by the **Nusantara Retail — Data Quality & Business Monitoring Dashboard**.

The DQ framework exists to validate the quality of the transactional data before and during business reporting.

The framework evaluates five primary data quality dimensions:

```text
Completeness
Validity
Consistency
Uniqueness
Accuracy
```

The DQ monitoring flow is:

```text
Raw Data
    ↓
DQ Rule Engine
    ↓
Rule Evaluation
    ↓
PASS / WARNING / FAIL
    ↓
DQ Result Aggregation
    ↓
DQ Issue Detail
    ↓
DQ Score
    ↓
Data Health / Reliability Monitoring
```

The project implements exactly:

```text
15 DQ Rules
```

The dataset generator is the source of truth for the intentional DQ problems used to validate these rules.

For the underlying dataset structure and field definitions, see [Data Dictionary](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/data_dictionary.md).

For business requirements and KPI governance, see [Business Requirements](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/business_requirements.md).

For the technical processing architecture, see [System Architecture](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/architecture.md).

---

## 2. DQ Dimensions

The project uses five primary DQ dimensions.

| Dimension | Purpose |
|---|---|
| `Completeness` | Measures whether required data is present. |
| `Validity` | Measures whether values satisfy defined domain, range, or value rules. |
| `Consistency` | Measures whether related data and business calculations remain logically consistent. |
| `Uniqueness` | Measures whether identifiers expected to be unique are duplicated. |
| `Accuracy` | Measures whether business values behave correctly according to defined business logic. |

---

## 3. Rule Status

Each DQ rule produces a logical status:

```text
PASS
WARNING
FAIL
```

### PASS

The record satisfies the rule.

### WARNING

The record requires attention but is not necessarily considered invalid.

### FAIL

The record violates the rule.

The current 15 implemented project rules produce:

```text
PASS
FAIL
```

with:

```text
Warning Rule Checks = 0
```

`WARNING` remains part of the framework for future rule expansion and anomaly-oriented monitoring.

---

## 4. Severity Framework

The project defines four severity levels:

| Severity | Meaning |
|---|---|
| `Critical` | Potentially makes important business metrics unreliable. |
| `High` | Significant issue requiring attention. |
| `Medium` | Important issue that may affect part of the analysis. |
| `Low` | Minor issue that primarily affects consistency or usability. |

The current 15 implemented rules use:

```text
Critical
High
Medium
```

No implemented rule currently uses `Low`.

---

## 5. DQ Rule Catalogue

### 5.1 Completeness

Completeness measures whether required transaction attributes are present.

#### DQ-CN01 — Missing Customer ID

```text
Dimension    : Completeness
Severity     : High
Target Table : sales / fact_sales
Target Column: customer_id
Rule         : customer_id must not be NULL
```

A failure occurs when the transaction does not contain a customer identifier.

---

#### DQ-CN02 — Missing Product ID

```text
Dimension    : Completeness
Severity     : High
Target Table : sales / fact_sales
Target Column: product_id
Rule         : product_id must not be NULL
```

A failure occurs when the transaction does not contain a product identifier.

---

#### DQ-CN03 — Missing Transaction Date

```text
Dimension    : Completeness
Severity     : Critical
Target Table : sales / fact_sales
Target Column: transaction_date
Rule         : transaction_date must not be NULL
```

A failure occurs when the transaction does not contain a transaction date.

The rule is Critical because the transaction date is required for time-based reporting and period validation.

---

## 6. Validity Rules

Validity measures whether values satisfy defined domain or range requirements.

### DQ-VL01 — Invalid Quantity

```text
Dimension    : Validity
Severity     : High
Target Table : sales / fact_sales
Target Column: quantity
Rule         : quantity must be greater than 0
```

Expected condition:

```text
quantity > 0
```

---

### DQ-VL02 — Invalid Unit Price

```text
Dimension    : Validity
Severity     : High
Target Table : sales / fact_sales
Target Column: unit_price
Rule         : unit_price must be greater than or equal to 0
```

Expected condition:

```text
unit_price >= 0
```

---

### DQ-VL03 — Invalid Discount Percentage

```text
Dimension    : Validity
Severity     : Medium
Target Table : sales / fact_sales
Target Column: discount_pct
Rule         : discount_pct must be between 0 and 100
```

Expected condition:

```text
0 <= discount_pct <= 100
```

---

### DQ-VL04 — Invalid Payment Method

```text
Dimension    : Validity
Severity     : Medium
Target Table : sales / fact_sales
Target Column: payment_method
Rule         : payment_method must belong to the allowed values
```

Allowed values:

```text
Cash
Debit Card
Credit Card
E-Wallet
Bank Transfer
```

---

## 7. Consistency Rules

Consistency measures whether related data and business calculations remain logically aligned.

### DQ-CS01 — Orphan Customer ID

```text
Dimension    : Consistency
Severity     : High
Target Table : sales / fact_sales
Target Column: customer_id
Rule         : customer_id must exist in the customer master
```

Validation concept:

```text
sales.customer_id
        ↓
dim_customer.customer_id
```

A non-null customer identifier that does not exist in the customer master is considered a consistency failure.

---

### DQ-CS02 — Orphan Product ID

```text
Dimension    : Consistency
Severity     : High
Target Table : sales / fact_sales
Target Column: product_id
Rule         : product_id must exist in the product master
```

Validation concept:

```text
sales.product_id
        ↓
dim_product.product_id
```

A non-null product identifier that does not exist in the product master is considered a consistency failure.

---

### DQ-CS03 — Store–Region Consistency

```text
Dimension    : Consistency
Severity     : High
Target Table : sales / fact_sales + stores / dim_store
Target Column: store_id + region_id
Rule         : sales region must match the region assigned to the store
```

Validation concept:

```text
sales.store_id
      ↓
stores.store_id
      ↓
stores.region_id
      =
sales.region_id
```

The rule validates the relationship:

```text
sales.region_id
=
store.region_id
```

for the same `store_id`.

This rule is specifically a **Store–Region Consistency** rule.

It is not an orphan-store rule.

---

### DQ-CS04 — Incorrect Sales Amount

```text
Dimension    : Consistency
Severity     : Critical
Target Table : sales / fact_sales
Target Column: sales_amount
Rule         : sales_amount must match the expected transaction calculation
```

Expected transaction amount:

```text
quantity
× unit_price
× (1 - discount_pct / 100)
```

Rounding tolerance:

```text
ABS(actual - expected) <= 1
```

Therefore, a difference of no more than:

```text
Rp1
```

is accepted.

---

## 8. Uniqueness Rules

Uniqueness measures whether the transaction identifier expected to identify a business transaction remains unique.

### DQ-UN01 — Duplicate Transaction ID

```text
Dimension    : Uniqueness
Severity     : Critical
Target Table : sales / fact_sales
Target Column: transaction_id
Rule         : transaction_id should be unique
```

The project intentionally preserves duplicate transaction IDs as DQ evidence.

Final verified condition:

```text
100,000 physical sales rows
300 duplicate transaction IDs
600 physical rows participating in duplicate IDs
```

`transaction_id` is therefore not used as the physical warehouse primary key.

The warehouse uses a technical `sales_key` to preserve the duplicated business identifiers.

---

## 9. Accuracy Rules

Accuracy measures whether business values behave correctly according to defined business logic.

### DQ-AC01 — Completed Order with Non-positive Sales Amount

```text
Dimension    : Accuracy
Severity     : High
Target Table : sales / fact_sales
Target Column: order_status + sales_amount
Rule         : Completed orders must have sales_amount > 0
```

Expected condition:

```text
order_status = Completed
AND
sales_amount > 0
```

A completed transaction with a non-positive amount fails this rule.

---

### DQ-AC02 — Abnormal Sales Amount

```text
Dimension    : Accuracy
Severity     : Medium
Target Table : sales / fact_sales
Target Column: sales_amount
Rule         : sales_amount must not exceed 2× the expected amount
```

Expected transaction amount:

```text
quantity
× unit_price
× (1 - discount_pct / 100)
```

Failure condition:

```text
sales_amount
>
expected_amount × 2
```

This rule detects abnormal amounts rather than simply testing arithmetic equality.

---

### DQ-AC03 — Transaction Date Outside Business Period

```text
Dimension    : Accuracy
Severity     : Critical
Target Table : sales / fact_sales
Target Column: transaction_date
Rule         : transaction_date must fall within the 2025 business period
```

Valid business period:

```text
2025-01-01 → 2025-12-31
```

A transaction outside this period fails the rule.

This includes intentionally generated out-of-period dates such as dates in 2026.

---

## 10. Complete Rule Summary

| Rule ID | Rule Name | Dimension | Severity |
|---|---|---|---|
| `DQ-CN01` | Missing Customer ID | Completeness | High |
| `DQ-CN02` | Missing Product ID | Completeness | High |
| `DQ-CN03` | Missing Transaction Date | Completeness | Critical |
| `DQ-VL01` | Invalid Quantity | Validity | High |
| `DQ-VL02` | Invalid Unit Price | Validity | High |
| `DQ-VL03` | Invalid Discount Percentage | Validity | Medium |
| `DQ-VL04` | Invalid Payment Method | Validity | Medium |
| `DQ-CS01` | Orphan Customer ID | Consistency | High |
| `DQ-CS02` | Orphan Product ID | Consistency | High |
| `DQ-CS03` | Store–Region Consistency | Consistency | High |
| `DQ-CS04` | Incorrect Sales Amount | Consistency | Critical |
| `DQ-UN01` | Duplicate Transaction ID | Uniqueness | Critical |
| `DQ-AC01` | Completed Order with Non-positive Sales Amount | Accuracy | High |
| `DQ-AC02` | Abnormal Sales Amount | Accuracy | Medium |
| `DQ-AC03` | Transaction Date Outside Business Period | Accuracy | Critical |

Total:

```text
15 DQ Rules
```

---

## 11. Intentional DQ Injection Mapping

The Phase 2 dataset generator intentionally creates evidence for the DQ rules.

| Rule | Intended DQ Evidence |
|---|---:|
| `DQ-CN01` | 1,500 |
| `DQ-CN02` | 800 |
| `DQ-CN03` | 200 |
| `DQ-VL01` | 500 |
| `DQ-VL02` | 200 |
| `DQ-VL03` | 500 |
| `DQ-VL04` | 300 |
| `DQ-CS01` | 400 |
| `DQ-CS02` | 200 |
| `DQ-CS03` | 600 |
| `DQ-CS04` | 700 |
| `DQ-UN01` | 300 |
| `DQ-AC01` | 200 |
| `DQ-AC02` | 300 |
| `DQ-AC03` | 200 |

These values represent the intentional injection targets defined by the dataset generator.

Detected counts do not necessarily equal injection targets because natural secondary detections are allowed.

Verified examples:

```text
DQ-CS04
Primary injections = 700
Detected failures  = 2,200

DQ-AC02
Primary injections = 300
Detected failures  = 1,338
```

The additional detections are expected consequences of interactions between injected data-quality problems.

The dataset generator remains the source of truth for the exact generated defect population.

---

## 12. Rule Evaluation Principles

### 12.1 Primary Injection vs Natural Detection

The DQ Engine distinguishes between the concept of an injected defect and the result of evaluating the final dataset.

Therefore:

```text
Injected Defects
        ≠
Total Detected Rule Failures
```

One underlying data problem can cause more than one DQ rule to fail.

---

### 12.2 Rule Checks vs Business Records

A DQ result represents a rule evaluation.

Therefore:

```text
Rule Check
    ≠
Business Record
```

One physical record can be checked by multiple rules.

---

### 12.3 Business Transaction vs Physical Record

The project intentionally allows duplicated transaction identifiers.

Therefore:

```text
transaction_id
    ≠
physical row identity
```

For issue traceability, the DQ Engine uses:

```text
source_row_id
```

as the physical source-record identifier.

---

## 13. DQ Result Model

The DQ Engine produces two analytical outputs:

```text
data/quality/

├── dq_result.csv
└── dq_issue_detail.csv
```

### 13.1 `dq_result`

Grain:

```text
One row per:
rule_id + result_date
```

The result records aggregate rule evaluations including:

```text
result_id
rule_id
result_date
dimension
severity
total_records
pass_count
fail_count
warning_count
failure_rate
warning_rate
dq_score
```

---

### 13.2 `dq_issue_detail`

Grain:

```text
One row per:
Physical Source Record × DQ Issue
```

The issue record contains:

```text
issue_id
result_id
source_row_id
transaction_id
rule_id
issue_date
status
severity
issue_value
expected_value
issue_description
```

`source_row_id` provides physical-row traceability when `transaction_id` is duplicated.

---

## 14. Dimension-Level Metrics

The project can evaluate quality at the dimension level.

Conceptual metrics:

```text
Completeness Rate
Validity Rate
Consistency Rate
Uniqueness Rate
Accuracy Rate
```

For a given dimension:

```text
Dimension Quality Rate =
Passed Rule Checks
───────────────────
Total Rule Checks
```

The dimension-level metrics are used to understand where data-quality problems are concentrated.

---

## 15. Overall DQ Score

The project uses a custom severity-weighted Overall DQ Score.

Severity weights:

| Severity | Weight |
|---|---:|
| Critical | 1.50 |
| High | 1.25 |
| Medium | 1.00 |
| Low | 0.75 |

Formula:

```text
Overall DQ Score =
Σ(rule_score × severity_weight)
──────────────────────────────
Σ(severity_weight)
```

The metric is:

```text
Project-defined
```

and is not presented as a universal industry-standard DQ formula.

Verified full-period result:

```text
99.35%
```

---

## 16. DQ Health Status

The project-defined Data Health Status uses:

```text
>= 95% → Healthy
>= 90% → Needs Attention
>= 80% → At Risk
< 80%  → Critical
```

The verified full-period result is:

```text
Overall DQ Score = 99.35%
Data Health Status = Healthy
```

---

## 17. Supporting DQ Metrics

The DQ model supports monitoring through:

```text
Total Rule Checks
Passed Rule Checks
Failed Rule Checks
Warning Rule Checks
Failure Rate
Warning Rate
Rule DQ Score
Overall DQ Score
Critical Failed Rule Checks
Critical Failure Rate
```

Issue-level analysis can be segmented by:

```text
Rule
Dimension
Severity
Status
Issue Date
```

---

## 18. Data Reliability Connection

Data quality results are also used to measure the business exposure associated with DQ issues.

The analytical model distinguishes:

```text
Affected Transactions
```

from:

```text
Affected Records
```

because duplicated transaction IDs exist.

Definitions:

```text
Affected Transactions
=
Distinct transaction_id values with at least one DQ issue
```

```text
Affected Records
=
Distinct source_row_id values with at least one DQ issue
```

Business exposure can also be measured through:

```text
Affected Revenue
Affected Revenue Rate
```

Business-to-DQ linkage is implemented through the Power BI semantic model and DAX virtual relationships where required.

---

## 19. DQ → Business KPI Control

DQ monitoring is connected to business reporting through explicit quality dependencies.

### Revenue

Controlled by the validity and consistency of:

```text
customer references
product references
quantity
unit price
discount
sales amount
transaction status
```

### Orders

Controlled by:

```text
transaction_id
order_status
transaction_date
```

with distinct transaction identifiers used for completed-order counting.

### Product / Category Performance

Controlled by:

```text
product_id
product master availability
product/category relationships
transaction values
```

### Regional Performance

Controlled by:

```text
store_id
region_id
store-region consistency
customer references
```

### Customer Analysis

Controlled by:

```text
customer_id
customer master availability
customer segmentation attributes
```

The presence of a DQ issue does not automatically invalidate every business KPI.

DQ impact must therefore be interpreted according to the affected data and business metric.

---

## 20. Data Quality Monitoring Principles

The project follows these principles:

### Preserve Bad Data

Invalid and inconsistent source records are not silently removed simply to produce clean-looking reports.

### Make Defects Measurable

Every rule should produce an explicit, reproducible result.

### Preserve Traceability

Issue records should remain traceable to physical source records.

### Distinguish Detection from Injection

Injected defects represent the test population, while DQ results represent what the rules actually detect.

### Distinguish Quality from Business Impact

A DQ failure does not automatically mean that every business KPI is unusable.

### Keep Rule Definitions Explicit

Each rule has a clear:

```text
Rule ID
Dimension
Target
Validation Logic
Severity
Expected Outcome
```

---

## 21. Final Validation Results

The completed DQ Engine verified:

```text
15/15 DQ rules executed
100,000 physical records checked
```

Generated analytical outputs:

```text
dq_result rows       = 5,640
dq_issue_detail rows = 9,738
```

Verified full-period DQ score:

```text
99.35%
```

Verified duplicate condition:

```text
Duplicate transaction IDs = 300
Duplicate physical rows   = 600
```

Current rule evaluation result:

```text
PASS
FAIL
```

with:

```text
Warning Rule Checks = 0
```

---

## 22. DQ Rule Success Criteria

The DQ implementation is considered successful when:

```text
✓ All 15 defined rules execute successfully.
✓ Every primary DQ dimension has measurable results.
✓ Missing values can be identified.
✓ Invalid values can be identified.
✓ Orphan references can be identified.
✓ Store-region inconsistencies can be identified.
✓ Incorrect transaction calculations can be identified.
✓ Duplicate transaction IDs can be identified.
✓ Accuracy/business-logic violations can be identified.
✓ DQ scores can be calculated reproducibly.
✓ Rule results can be analyzed by dimension.
✓ Rule results can be analyzed by severity.
✓ Rule results can be analyzed by date.
✓ Individual issues can be traced to physical source records.
✓ DQ results can be connected to business reliability analysis.
```

---

## 23. Final DQ Framework

```text
                        DATA QUALITY
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    Completeness         Validity          Consistency
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
               Uniqueness          Accuracy
                    │                 │
                    └────────┬────────┘
                             ▼
                    Rule Evaluation
                             ↓
                      PASS / FAIL
                             ↓
                    DQ Result + Issues
                             ↓
                       DQ Score
                             ↓
                    Data Health Status
                             ↓
                    Data Reliability
                             ↓
                 Business Interpretation
```

The central principle is:

> **The DQ framework does not hide bad data. It detects, measures, traces, and communicates data-quality problems and their potential business impact.**