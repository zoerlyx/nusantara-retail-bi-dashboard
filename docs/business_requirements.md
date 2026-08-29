# Business Requirements — Nusantara Retail

## 1. Document Overview

This document defines the business requirements for the **Nusantara Retail — Data Quality & Business Monitoring Dashboard**.

The project is designed as an end-to-end Business Intelligence solution that addresses two connected business needs:

```text
1. How is the business performing?
2. How reliable is the data used to measure that performance?
```

The solution therefore combines:

```text
Business Performance
        +
Data Quality
        +
Data Reliability
```

into a single analytical solution.

Technical architecture, data structures, and detailed DQ implementation are documented separately in:

- [System Architecture](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/business_requirements.md).
- [Data Dictionary](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/data_dictionary.md)
- [Data Quality Rules](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/dq_rules.md)

---

## 2. Business Scenario

### Company

```text
Nusantara Retail
```

### Industry

```text
Retail
```

### Business Model

```text
Omnichannel Retail
```

Nusantara Retail operates multiple stores across several regions in Indonesia and generates transaction-level sales data across customer, product, store, and regional operations.

Management relies on transaction data to monitor business performance and make decisions.

However, the organization does not yet have a systematic mechanism for monitoring whether the underlying data is:

```text
Complete
Valid
Consistent
Unique
Accurate
```

Poor data quality can reduce the reliability of business KPIs even when the dashboard and calculations are technically correct.

---

## 3. Business Problem

The primary business problem is:

> Management uses transaction data to make decisions, but the quality of the underlying data is not systematically monitored.

The dataset may contain problems such as:

```text
Missing values
Invalid values
Duplicate transaction IDs
Orphan references
Inconsistent store-region relationships
Incorrect transaction calculations
Abnormal transaction amounts
Out-of-period dates
```

Without explicit monitoring, these problems may:

- reduce confidence in business reports;
- distort KPI interpretation;
- make root-cause investigation difficult;
- hide the operational impact of poor data quality.

Therefore, the BI solution must measure both:

```text
Business Performance
```

and:

```text
Data Reliability
```

---

## 4. Business Objective

The core objective is:

> **Monitor business performance while measuring the reliability of the underlying transactional data.**

The solution must enable management and BI/data teams to:

1. Monitor core business KPIs.
2. Monitor data quality health.
3. Identify the most problematic DQ dimensions and rules.
4. Investigate individual problematic records.
5. Understand the business activity exposed to DQ issues.

---

## 5. Stakeholder Definition

### 5.1 Management / Executive

#### Primary Needs

```text
Business performance
Overall data health
Data reliability
Regional and category performance
Business impact of DQ problems
```

#### Main Questions

```text
How is the business performing?
Can management trust the current reporting data?
Where are the major risks?
```

---

### 5.2 BI / Data Team

#### Primary Needs

```text
DQ monitoring
Rule performance
Failure analysis
Severity analysis
Issue investigation
Record-level traceability
```

#### Main Questions

```text
Which rules are failing?
Which dimensions are weakest?
Which records are affected?
What should be investigated or fixed?
```

---

### 5.3 Business Analyst

#### Primary Needs

```text
Regional analysis
Product analysis
Category analysis
Customer segmentation
Payment behavior
Trend analysis
```

#### Main Questions

```text
What is driving business performance?
Which regions/products/categories contribute most?
How does customer behavior differ across segments?
```

---

## 6. Business Questions

### 6.1 Business Performance Questions

#### BQ01 — Revenue Trend

> How much revenue is generated and how does revenue change over time?

Required analysis:

```text
Revenue
Revenue Trend
Revenue Growth
```

---

#### BQ02 — Regional Contribution

> Which regions and stores contribute the most revenue?

Required analysis:

```text
Revenue by Region
Revenue by Store
Regional Hierarchy
```

---

#### BQ03 — Product and Category Performance

> Which products and categories perform best and worst?

Required analysis:

```text
Revenue by Category
Revenue by Product
Top Products
```

---

#### BQ04 — Orders and Customers

> How do the number of orders and customers change over time?

Required metrics:

```text
Orders
Customers
Order Growth
```

---

#### BQ05 — Average Order Value

> How does Average Order Value change?

Required metric:

```text
AOV
```

Formula:

```text
AOV = Revenue / Orders
```

---

#### BQ06 — Period Comparison

> How does business performance change between available time periods?

The project uses a 2025-only dataset. Therefore, valid comparisons are based on available monthly/date context rather than unsupported historical years.

The project does not invent 2024 or other unavailable periods.

---

## 7. Data Quality Questions

### DQ01 — Overall Data Health

> How healthy is the dataset overall?

Required metric:

```text
Overall DQ Score
```

---

### DQ02 — Weakest Quality Dimension

> Which data quality dimension has the most failures?

Required dimensions:

```text
Completeness
Validity
Consistency
Uniqueness
Accuracy
```

Detailed rule definitions are maintained in [Data Quality Rules](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/dq_rules.md).

---

### DQ03 — Problematic DQ Rules

> Which validation rules generate the most failures?

Required analysis:

```text
Failed Rule Checks by Rule
Top Failed Rules
```

---

### DQ04 — Issue Types

> Are there missing, invalid, duplicate, or inconsistent records?

Required analysis:

```text
DQ Dimension
Severity
Status
Issue Detail
```

---

### DQ05 — Data Quality Trend

> How does data quality change over time?

Required analysis:

```text
DQ Score Trend
Failure Rate Trend
Issue Trend
```

The DQ monitoring process therefore produces daily quality results for time-based analysis.

---

### DQ06 — Business Records Affected

> How many business transactions and physical records are affected by DQ problems?

Required measures:

```text
Affected Transactions
Affected Records
Affected Revenue
Affected Revenue Rate
```

---

## 8. Business KPI Framework

The project intentionally limits business KPIs to a small set of clearly defined metrics.

### 8.1 Revenue

#### Definition

> Total `sales_amount` for Completed orders.

#### Conceptual Formula

```text
Revenue =
SUM(sales_amount)
where order_status = Completed
```

---

### 8.2 Orders

#### Definition

> Number of distinct Completed transaction IDs.

```text
Orders =
DISTINCTCOUNT(transaction_id)
where order_status = Completed
```

The use of `DISTINCTCOUNT` is intentional because the dataset contains duplicate transaction IDs for DQ testing.

---

### 8.3 Customers

#### Definition

> Number of distinct customers associated with Completed transactions.

```text
Customers =
DISTINCTCOUNT(customer_id)
where order_status = Completed
```

---

### 8.4 AOV

#### Definition

> Average revenue generated per completed transaction.

```text
AOV =
Revenue / Orders
```

---

### 8.5 Revenue Growth

#### Definition

> Change in revenue across the available reporting period.

The dashboard uses available 2025 time context rather than fabricating unavailable historical data.

---

### 8.6 Order Growth

#### Definition

> Change in completed orders across the available reporting period.

---

## 9. Data Quality KPI Framework

### 9.1 Total Rule Checks

#### Definition

> Total number of rule evaluations performed.

```text
Total Rule Checks =
SUM(dq_result.total_records)
```

**Important:**

```text
Rule Checks ≠ Business Records
```

A single business record can be evaluated against multiple DQ rules.

---

### 9.2 Passed Rule Checks

#### Definition

> Number of rule evaluations that passed.

```text
Passed Rule Checks =
SUM(dq_result.pass_count)
```

---

### 9.3 Failed Rule Checks

#### Definition

> Number of rule evaluations that failed.

```text
Failed Rule Checks =
SUM(dq_result.fail_count)
```

---

### 9.4 Warning Rule Checks

#### Definition

> Number of rule evaluations classified as WARNING.

Current project result:

```text
Warning Rule Checks = 0
```

The current implemented rules produce PASS/FAIL outcomes.

---

### 9.5 Failure Rate

```text
Failure Rate =
Failed Rule Checks
──────────────────
Total Rule Checks
```

---

### 9.6 Warning Rate

```text
Warning Rate =
Warning Rule Checks
────────────────────
Total Rule Checks
```

---

### 9.7 Rule DQ Score

```text
Rule DQ Score =
Passed Rule Checks
──────────────────
Total Rule Checks
```

---

### 9.8 Overall DQ Score

The project uses a custom severity-weighted score.

Severity weights:

```text
Critical = 1.50
High     = 1.25
Medium   = 1.00
Low      = 0.75
```

Formula:

```text
Overall DQ Score =
Σ(rule_score × severity_weight)
──────────────────────────────
Σ(severity_weight)
```

Verified final value:

```text
99.35%
```

This score is a **custom project metric**, not a universal industry standard.

---

## 10. Data Quality Dimensions

The project uses exactly five primary data quality dimensions:

```text
Completeness
Validity
Consistency
Uniqueness
Accuracy
```

### 10.1 Completeness

Measures whether required data is present.

Examples include:

```text
Missing Customer ID
Missing Product ID
Missing Transaction Date
```

---

### 10.2 Validity

Measures whether values satisfy defined value or range rules.

Examples include:

```text
Invalid Quantity
Invalid Unit Price
Invalid Discount
Invalid Payment Method
```

---

### 10.3 Consistency

Measures whether data is logically consistent across records and reference relationships.

Examples include:

```text
Orphan Customer
Orphan Product
Store-Region Mismatch
Incorrect Sales Amount
```

---

### 10.4 Uniqueness

Measures whether identifiers expected to be unique are duplicated.

Example:

```text
Duplicate Transaction ID
```

---

### 10.5 Accuracy

Measures whether business values behave correctly according to business logic.

Examples include:

```text
Completed Order with Non-positive Amount
Abnormal Sales Amount
Out-of-period Transaction Date
```

Detailed DQ rule logic, severity, thresholds, and validation behavior are documented in [Data Quality Rules](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/dq_rules.md).

---

## 11. Severity Framework

The project defines four severity levels.

| Severity | Meaning |
|---|---|
| `Critical` | Potentially makes important business metrics unreliable |
| `High` | Significant issue requiring attention |
| `Medium` | Important issue that does not necessarily affect the whole report |
| `Low` | Minor issue |

The final implemented rule set uses:

```text
Critical
High
Medium
```

The framework also supports:

```text
Low
```

although no implemented rule currently uses it.

---

## 12. DQ Status Framework

Three statuses are supported:

```text
PASS
WARNING
FAIL
```

### PASS

Data satisfies the validation rule.

### WARNING

Data remains usable but requires attention.

### FAIL

Data violates the rule.

Current project behavior:

```text
PASS
FAIL
```

with:

```text
Warning Rule Checks = 0
```

---

## 13. KPI Governance

All KPI definitions are centralized in the BI semantic layer.

The project follows:

```text
Business Requirement
        ↓
KPI Definition
        ↓
DAX Measure
        ↓
Dashboard Visual
```

Visuals should not independently calculate KPI values.

This prevents the same KPI from producing different values across dashboard pages.

Detailed data model and DAX implementation are documented separately in the technical documentation.

---

## 14. KPI → Decision Mapping

| KPI / Metric | Business Question | Decision Use |
|---|---|---|
| Revenue | How much business is generated? | Monitor business performance |
| Orders | How many completed transactions occur? | Monitor transaction activity |
| Customers | How many customers transact? | Monitor customer activity |
| AOV | How much revenue per order? | Evaluate basket value |
| Revenue Growth | Is revenue changing? | Detect performance trend |
| Order Growth | Are completed orders changing? | Detect transaction trend |
| Overall DQ Score | Is data healthy? | Assess reporting reliability |
| Failure Rate | How many rule checks fail? | Identify quality degradation |
| Critical Failed Rule Checks | How severe are the failures? | Prioritize critical investigation |
| Affected Transactions | How many transactions have issues? | Estimate operational exposure |
| Affected Records | How many physical rows are affected? | Estimate data remediation scope |
| Affected Revenue | How much reported revenue is associated with affected transactions? | Estimate business exposure |
| Data Reliability | Can the current data be considered reliable? | Support reporting confidence |

---

## 15. Dashboard Requirements

The solution contains four pages.

### 15.1 Executive Overview

#### Audience

```text
Management / Executive
```

#### Primary Question

> How is the business performing and how reliable is the data?

#### Required Information

```text
Revenue
Orders
Customers
AOV
Overall DQ Score
Data Health Status
Data Reliability
Affected Transactions
Affected Records
Affected Revenue
Affected Revenue Rate
Revenue Trend
Revenue by Region
Revenue by Category
```

---

### 15.2 Data Health

#### Audience

```text
Management + BI/Data Team
```

#### Primary Question

> How healthy is the underlying data?

#### Required Information

```text
Overall DQ Score
Data Health Status
Data Reliability
Passed Rule Checks
Failed Rule Checks
Warning Rule Checks
Failure Rate
Critical Failed Rule Checks
DQ Score Trend
Failed Rules by Dimension
Failed Rules by Severity
Top Failed Rules
```

---

### 15.3 Data Quality Details

#### Audience

```text
BI / Data Analyst
```

#### Primary Question

> What DQ problems exist and which records are affected?

#### Required Capabilities

```text
Dimension filtering
Severity filtering
Rule filtering
Status filtering
Rule Performance Matrix
Issue Detail Table
Drill-through
```

#### Issue-Level Information

```text
Transaction ID
Issue Date
Rule
Dimension
Severity
Status
Issue Value
Expected Value
Issue Description
```

---

### 15.4 Business Analysis

#### Audience

```text
Business Analyst / Management
```

#### Primary Question

> What is driving business performance?

#### Required Information

```text
Revenue
Revenue Growth
Orders
AOV
Revenue by Date
Revenue by Region
Revenue by Category
Revenue by Product
Revenue by Payment Method
Customers + Revenue by Customer Segment
```

---

## 16. Business Success Criteria

The project is considered successful when the following requirements are met.

### 16.1 Business Reporting

```text
✓ Business KPIs can be calculated consistently.
✓ Revenue can be analyzed over time.
✓ Regional and product performance can be compared.
✓ Customer and order activity can be analyzed.
✓ AOV can be monitored.
```

---

### 16.2 Data Quality Monitoring

```text
✓ All 15 DQ rules execute successfully.
✓ DQ issues are measurable.
✓ DQ issues can be analyzed by dimension.
✓ DQ issues can be analyzed by severity.
✓ DQ trends can be monitored over time.
✓ Individual issues can be traced to source records.
```

---

### 16.3 Data Reliability

```text
✓ Overall DQ Score is available.
✓ Data Health Status is available.
✓ Data Reliability is available.
✓ Affected Transactions are measurable.
✓ Affected Records are measurable.
✓ Affected Revenue is measurable.
```

---

### 16.4 Technical Architecture

The business requirements depend on a technical implementation that ensures:

```text
✓ Raw data is preserved.
✓ Staging standardizes data representation.
✓ Warehouse supports analytical reporting.
✓ DQ results are stored separately.
✓ Power BI uses a star-schema semantic model.
✓ DAX provides centralized KPI logic.
```

Technical implementation details are maintained in [System Architecture](https://github.com/zoerlyx/nusantara-retail-bi-dashboard/blob/main/docs/architecture.md).

---

## 17. Final Business Requirements Summary

```text
COMPANY
Nusantara Retail

DOMAIN
Retail / Omnichannel Retail

ROLE
BI Developer

CORE OBJECTIVE
Monitor business performance while measuring
the reliability of the underlying data.

BUSINESS KPI
6

DATA QUALITY KPI
6+

DQ DIMENSIONS
5

DQ RULES
15

SEVERITY LEVELS
4

STATUS
PASS / WARNING / FAIL

TRANSACTION DATA
100,000 physical records

BUSINESS PERIOD
January–December 2025

CUSTOMERS
15,000

PRODUCTS
500

STORES
30

REGIONS
8

DATABASE
PostgreSQL

DATA ARCHITECTURE
Raw → Staging → Warehouse → Quality

BI TOOL
Power BI

DAX
Business + Data Quality + Reliability

DASHBOARD PAGES
4
```

---

## 18. Final Business Principle

The project is built around one central principle:

> **Business performance should be analyzed together with the reliability of the data used to measure it.**

Therefore, the final solution does not stop at:

```text
Revenue = X
```

It also asks:

```text
How healthy is the data?
How many records are affected?
Which rules are failing?
How severe are the issues?
How much business activity is associated with affected transactions?
```

This creates a BI solution that connects:

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

The objective is not merely to report business numbers, but to provide decision-makers with sufficient context to understand how trustworthy those numbers are.