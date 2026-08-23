"""
generate_dataset.py
====================
Nusantara Retail - Phase 2: Synthetic Dataset Generator

Generates deterministic synthetic retail data with intentional,
auditable Data Quality issues covering all 15 DQ rules defined in
the Phase 2 contract.

Pipeline:
    GENERATE → VALIDATE → AUDIT DQ INJECTION COVERAGE
             → AUDIT DQ RULE COMPATIBILITY → READY FOR PHASE 3

Output:
    data/raw/regions.csv
    data/raw/stores.csv
    data/raw/products.csv
    data/raw/customers.csv
    data/raw/date.csv
    data/raw/sales.csv   ← exactly 100,000 physical rows

Author : Nusantara Retail BI Team
Encoding: UTF-8 (stdout forced at runtime for Windows compatibility)
Phase  : 2 — Dataset Design & Generation
Seed   : 2025 (deterministic — same seed → same output)
"""

import os
import sys
import math
import random
from datetime import date, timedelta

# Force UTF-8 stdout so Unicode characters render on Windows terminals.
# Falls back silently if reconfiguration is unavailable (Python < 3.7).
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd
from faker import Faker

# ============================================================
# 1. CONFIGURATION & CONSTANTS
# ============================================================

SEED = 2025

# Dataset volume targets
N_REGIONS   = 8
N_STORES    = 30
N_PRODUCTS  = 500
N_CUSTOMERS = 15_000
N_SALES     = 100_000
YEAR        = 2025

# Business period
BIZ_START = date(2025, 1, 1)
BIZ_END   = date(2025, 12, 31)

# Allowed enum values
PAYMENT_METHODS = ["Cash", "Debit Card", "Credit Card", "E-Wallet", "Bank Transfer"]
ORDER_STATUSES  = ["Completed", "Cancelled", "Pending", "Processing"]
STORE_TYPES     = ["Flagship", "Standard", "Outlet"]
CUSTOMER_SEGS   = ["New", "Regular", "Loyal"]
GENDERS         = ["Male", "Female"]
AGE_GROUPS      = ["18-24", "25-34", "35-44", "45-54", "55+"]

# DQ injection targets (counts, derived from rates)
# Rates are targets; ±10% relative tolerance is accepted.
DQ_INJECTION_TARGETS = {
    "DQ-CN01": int(N_SALES * 0.015),   # 1.5% → 1500
    "DQ-CN02": int(N_SALES * 0.008),   # 0.8% →  800
    "DQ-CN03": int(N_SALES * 0.002),   # 0.2% →  200
    "DQ-VL01": int(N_SALES * 0.005),   # 0.5% →  500
    "DQ-VL02": int(N_SALES * 0.002),   # 0.2% →  200
    "DQ-VL03": int(N_SALES * 0.005),   # 0.5% →  500
    "DQ-VL04": int(N_SALES * 0.003),   # 0.3% →  300
    "DQ-CS01": int(N_SALES * 0.004),   # 0.4% →  400
    "DQ-CS02": int(N_SALES * 0.002),   # 0.2% →  200
    "DQ-CS03": int(N_SALES * 0.006),   # 0.6% →  600
    "DQ-CS04": int(N_SALES * 0.007),   # 0.7% →  700
    "DQ-UN01": int(N_SALES * 0.003),   # 0.3% →  300
    "DQ-AC01": int(N_SALES * 0.002),   # 0.2% →  200
    "DQ-AC02": int(N_SALES * 0.003),   # 0.3% →  300
    "DQ-AC03": int(N_SALES * 0.002),   # 0.2% →  200
}

# ±10% relative tolerance for injection rate acceptance
TOLERANCE = 0.10

# Output directory
OUTPUT_DIR = os.path.join("data", "raw")

# ============================================================
# 2. RNG INITIALISATION
# ============================================================

rng    = np.random.default_rng(SEED)
py_rng = random.Random(SEED)
fake   = Faker("id_ID")
Faker.seed(SEED)

# ============================================================
# 3. INJECTION INDEX ALLOCATOR
# ============================================================
# Each DQ rule gets a dedicated, non-overlapping set of row indices.
# A row injected for DQ-CN01 is NOT re-used for DQ-VL01, etc.
# Natural multi-rule detection overlaps (side effects) are allowed.

_used_indices: set = set()

def allocate_indices(n: int) -> np.ndarray:
    """
    Allocate n unique row indices not yet claimed by any prior injection.
    Indices are drawn without replacement from the remaining pool.
    """
    global _used_indices
    available = np.array(sorted(set(range(N_SALES)) - _used_indices))
    chosen    = rng.choice(available, size=n, replace=False)
    _used_indices.update(chosen.tolist())
    return chosen


def reset_allocator():
    """Reset the global used-index set (for testing only)."""
    global _used_indices
    _used_indices = set()


# ============================================================
# 4. MASTER DATA GENERATION
# ============================================================

def generate_regions() -> pd.DataFrame:
    """
    Generate 8 Indonesian regions (REG001–REG008).
    All master region records are structurally clean.
    """
    data = [
        ("REG001", "Sumatera Utara",    "Sumatera"),
        ("REG002", "DKI Jakarta",        "Jawa"),
        ("REG003", "Jawa Barat",         "Jawa"),
        ("REG004", "Jawa Tengah",        "Jawa"),
        ("REG005", "Jawa Timur",         "Jawa"),
        ("REG006", "Kalimantan Timur",   "Kalimantan"),
        ("REG007", "Sulawesi Selatan",   "Sulawesi"),
        ("REG008", "Bali",               "Bali & Nusa Tenggara"),
    ]
    df = pd.DataFrame(data, columns=["region_id", "region_name", "island"])
    assert len(df) == N_REGIONS, f"Expected {N_REGIONS} regions, got {len(df)}"
    return df


# Mapping: region_id → representative cities
REGION_CITIES = {
    "REG001": ["Medan", "Pematangsiantar", "Binjai", "Tebing Tinggi"],
    "REG002": ["Jakarta Pusat", "Jakarta Selatan", "Jakarta Utara", "Jakarta Timur", "Jakarta Barat"],
    "REG003": ["Bandung", "Bekasi", "Depok", "Bogor", "Cimahi"],
    "REG004": ["Semarang", "Solo", "Yogyakarta", "Magelang", "Salatiga"],
    "REG005": ["Surabaya", "Malang", "Kediri", "Blitar", "Pasuruan"],
    "REG006": ["Balikpapan", "Samarinda", "Bontang", "Kutai Kartanegara"],
    "REG007": ["Makassar", "Parepare", "Palopo", "Gowa"],
    "REG008": ["Denpasar", "Badung", "Gianyar", "Tabanan"],
}

# Assign regions and cities to stores deterministically
STORE_REGION_ASSIGNMENTS = []
for i in range(N_STORES):
    region = f"REG{((i % N_REGIONS) + 1):03d}"
    STORE_REGION_ASSIGNMENTS.append(region)


def generate_stores(regions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate 30 clean store master records (STR001–STR030).
    region_id and city are consistent. No corruption injected here.
    """
    rows = []
    store_rng = np.random.default_rng(SEED + 10)

    for i in range(N_STORES):
        store_id   = f"STR{(i+1):03d}"
        region_id  = STORE_REGION_ASSIGNMENTS[i]
        city_opts  = REGION_CITIES[region_id]
        city       = city_opts[store_rng.integers(0, len(city_opts))]
        store_type = STORE_TYPES[store_rng.integers(0, len(STORE_TYPES))]
        store_name = f"Nusantara {store_type} {city}"
        # Opening date: 2018-01-01 through 2024-12-31
        open_offset   = int(store_rng.integers(0, (date(2024, 12, 31) - date(2018, 1, 1)).days))
        opening_date  = date(2018, 1, 1) + timedelta(days=open_offset)
        rows.append({
            "store_id":     store_id,
            "store_name":   store_name,
            "region_id":    region_id,
            "city":         city,
            "store_type":   store_type,
            "opening_date": opening_date.isoformat(),
        })

    df = pd.DataFrame(rows)
    assert len(df) == N_STORES
    return df


def generate_products() -> pd.DataFrame:
    """
    Generate exactly 500 products across 6 categories.
    Uses remainder-distribution to guarantee total == 500.

    Category allocation:
        6 categories, 500 total
        base = 500 // 6 = 83
        remainder = 500 % 6 = 2
        → first 2 categories get 84, rest get 83 → 84+84+83+83+83+83 = 500
    """
    categories = {
        "Electronics":  {"subs": ["Smartphones", "Laptops", "Accessories", "Audio"], "brands": ["Samsung", "Apple", "Xiaomi", "ASUS", "Lenovo"]},
        "Fashion":       {"subs": ["Men's Wear", "Women's Wear", "Kids Wear", "Footwear"], "brands": ["Zara", "H&M", "Uniqlo", "Nike", "Adidas"]},
        "Food & Beverage":{"subs": ["Snacks", "Beverages", "Dairy", "Instant Food"], "brands": ["Indofood", "Wings", "Mayora", "Garuda", "ABC"]},
        "Home & Living":  {"subs": ["Furniture", "Kitchenware", "Decor", "Bedding"], "brands": ["IKEA", "ACE", "Olympic", "Courts", "Index"]},
        "Sports":         {"subs": ["Gym Equipment", "Outdoor", "Team Sports", "Swimming"], "brands": ["Nike", "Adidas", "Speedo", "Decathlon", "Reebok"]},
        "Beauty":         {"subs": ["Skincare", "Makeup", "Haircare", "Fragrance"], "brands": ["L'Oreal", "Wardah", "Emina", "Pond's", "Nivea"]},
    }
    cat_names  = list(categories.keys())
    n_cats     = len(cat_names)          # 6
    base       = N_PRODUCTS // n_cats    # 83
    remainder  = N_PRODUCTS % n_cats     # 2
    counts     = [base + (1 if i < remainder else 0) for i in range(n_cats)]
    assert sum(counts) == N_PRODUCTS, f"Product count mismatch: {sum(counts)} != {N_PRODUCTS}"

    prod_rng = np.random.default_rng(SEED + 20)
    rows = []
    product_num = 1

    for cat_idx, cat_name in enumerate(cat_names):
        cat_info = categories[cat_name]
        for _ in range(counts[cat_idx]):
            product_id   = f"PRD{product_num:05d}"
            sub          = cat_info["subs"][prod_rng.integers(0, len(cat_info["subs"]))]
            brand        = cat_info["brands"][prod_rng.integers(0, len(cat_info["brands"]))]
            product_name = f"{brand} {sub} {product_num:04d}"
            # Cost and price bands by category
            if cat_name == "Electronics":
                unit_cost  = round(float(prod_rng.uniform(200_000, 8_000_000)), 2)
            elif cat_name == "Fashion":
                unit_cost  = round(float(prod_rng.uniform(50_000, 1_500_000)), 2)
            elif cat_name == "Food & Beverage":
                unit_cost  = round(float(prod_rng.uniform(5_000, 200_000)), 2)
            elif cat_name == "Home & Living":
                unit_cost  = round(float(prod_rng.uniform(30_000, 3_000_000)), 2)
            elif cat_name == "Sports":
                unit_cost  = round(float(prod_rng.uniform(50_000, 2_000_000)), 2)
            else:  # Beauty
                unit_cost  = round(float(prod_rng.uniform(20_000, 500_000)), 2)
            margin     = round(float(prod_rng.uniform(0.15, 0.60)), 4)
            list_price = round(unit_cost * (1 + margin), 2)
            rows.append({
                "product_id":   product_id,
                "product_name": product_name,
                "category":     cat_name,
                "subcategory":  sub,
                "brand":        brand,
                "unit_cost":    unit_cost,
                "list_price":   list_price,
            })
            product_num += 1

    df = pd.DataFrame(rows)
    assert len(df) == N_PRODUCTS, f"Product count: {len(df)}"
    return df


def generate_customers(regions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate 15,000 customer master records (CUS00001–CUS15000).
    All references to region_id are valid. No corruption here.
    """
    cust_rng   = np.random.default_rng(SEED + 30)
    region_ids = regions_df["region_id"].tolist()
    rows       = []

    for i in range(N_CUSTOMERS):
        customer_id  = f"CUS{(i+1):05d}"
        gender       = GENDERS[cust_rng.integers(0, len(GENDERS))]
        age_group    = AGE_GROUPS[cust_rng.integers(0, len(AGE_GROUPS))]
        region_id    = region_ids[cust_rng.integers(0, len(region_ids))]
        city_opts    = REGION_CITIES[region_id]
        city         = city_opts[cust_rng.integers(0, len(city_opts))]
        segment      = CUSTOMER_SEGS[cust_rng.integers(0, len(CUSTOMER_SEGS))]
        # Registration: 2020-01-01 through 2024-12-31
        reg_offset   = int(cust_rng.integers(0, (date(2024, 12, 31) - date(2020, 1, 1)).days + 1))
        reg_date     = date(2020, 1, 1) + timedelta(days=reg_offset)
        # Simple Indonesian-style name
        first_names  = ["Budi", "Siti", "Ahmad", "Dewi", "Eko", "Fitri", "Gunawan",
                         "Hana", "Iman", "Joko", "Kartini", "Lestari", "Made", "Nadia",
                         "Omar", "Putri", "Rizky", "Sari", "Tono", "Udin", "Vina",
                         "Wahyu", "Xenia", "Yuni", "Zahra"]
        last_names   = ["Santoso", "Wijaya", "Kusuma", "Hartono", "Suharto", "Wibowo",
                         "Susanto", "Prasetyo", "Nugroho", "Handoko", "Setiawan",
                         "Rahayu", "Purnama", "Utama", "Hidayat", "Saputra"]
        fn = first_names[cust_rng.integers(0, len(first_names))]
        ln = last_names[cust_rng.integers(0, len(last_names))]
        rows.append({
            "customer_id":       customer_id,
            "customer_name":     f"{fn} {ln}",
            "gender":            gender,
            "age_group":         age_group,
            "city":              city,
            "region_id":         region_id,
            "customer_segment":  segment,
            "registration_date": reg_date.isoformat(),
        })

    df = pd.DataFrame(rows)
    assert len(df) == N_CUSTOMERS
    return df


def generate_date_dim() -> pd.DataFrame:
    """
    Generate 365 date-dimension records for 2025-01-01 → 2025-12-31.
    """
    month_names = {
        1: "January", 2: "February", 3: "March",    4: "April",
        5: "May",     6: "June",     7: "July",      8: "August",
        9: "September",10:"October", 11:"November",  12:"December",
    }
    rows = []
    current = BIZ_START
    while current <= BIZ_END:
        rows.append({
            "date":         current.isoformat(),
            "year":         current.year,
            "quarter":      math.ceil(current.month / 3),
            "month_number": current.month,
            "month_name":   month_names[current.month],
            "week_number":  current.isocalendar()[1],
            "day_name":     current.strftime("%A"),
            "is_weekend":   1 if current.weekday() >= 5 else 0,
        })
        current += timedelta(days=1)

    df = pd.DataFrame(rows)
    assert len(df) == 365, f"Date dim: {len(df)}"
    return df


# ============================================================
# 5. TRANSACTION GENERATION (CLEAN BASE)
# ============================================================

def generate_sales_clean(
    customers_df: pd.DataFrame,
    products_df:  pd.DataFrame,
    stores_df:    pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate 100,000 clean base transaction records.

    Clean record invariants:
        - transaction_id: TRX000001–TRX100000 (unique)
        - transaction_date ∈ [2025-01-01, 2025-12-31]
        - customer_id ∈ customers master
        - product_id  ∈ products master
        - store_id    ∈ stores master
        - region_id   = stores.region_id for that store_id
        - quantity    ∈ [1, 20]
        - unit_price  = product list_price
        - discount_pct ∈ [0, 30]
        - sales_amount = qty × unit_price × (1 - discount/100), rounded 2dp
        - payment_method ∈ allowed values
        - order_status   ∈ allowed values
    """
    sale_rng = np.random.default_rng(SEED + 50)

    customer_ids = customers_df["customer_id"].values
    product_ids  = products_df["product_id"].values
    list_prices  = products_df["list_price"].values
    store_ids    = stores_df["store_id"].values
    # Build store → region_id lookup
    store_region = dict(zip(stores_df["store_id"], stores_df["region_id"]))

    # Random date offsets within 2025 (0–364)
    total_days   = (BIZ_END - BIZ_START).days  # 364
    date_offsets = sale_rng.integers(0, total_days + 1, size=N_SALES)

    # Draw indices into master arrays
    cust_idx  = sale_rng.integers(0, len(customer_ids), size=N_SALES)
    prod_idx  = sale_rng.integers(0, len(product_ids),  size=N_SALES)
    store_idx = sale_rng.integers(0, len(store_ids),    size=N_SALES)

    quantities    = sale_rng.integers(1, 21, size=N_SALES).astype(int)
    discount_pcts = np.round(sale_rng.uniform(0, 30, size=N_SALES), 2)

    pay_idx    = sale_rng.integers(0, len(PAYMENT_METHODS), size=N_SALES)
    status_idx = sale_rng.integers(0, len(ORDER_STATUSES),  size=N_SALES)

    rows = []
    for i in range(N_SALES):
        sid        = store_ids[store_idx[i]]
        pid_str    = product_ids[prod_idx[i]]
        cid_str    = customer_ids[cust_idx[i]]
        unit_price = float(list_prices[prod_idx[i]])
        qty        = int(quantities[i])
        disc       = float(discount_pcts[i])
        amount     = round(qty * unit_price * (1 - disc / 100), 2)
        txn_date   = (BIZ_START + timedelta(days=int(date_offsets[i]))).isoformat()

        rows.append({
            "transaction_id":   f"TRX{(i+1):06d}",
            "transaction_date": txn_date,
            "customer_id":      cid_str,
            "product_id":       pid_str,
            "store_id":         sid,
            "region_id":        store_region[sid],
            "quantity":         qty,
            "unit_price":       unit_price,
            "discount_pct":     disc,
            "sales_amount":     amount,
            "payment_method":   PAYMENT_METHODS[int(pay_idx[i])],
            "order_status":     ORDER_STATUSES[int(status_idx[i])],
        })

    return pd.DataFrame(rows)


# ============================================================
# 6. DQ INJECTION
# ============================================================
# Each inject_* function:
#   1. Claims exclusive row indices from the central allocator.
#   2. Mutates those rows in the DataFrame in-place.
#   3. Returns (rule_id, injected_indices) for audit.
#
# CC-3: Injection indices are non-overlapping by construction.
#        Natural secondary detection overlaps are NOT suppressed.

def inject_cn01(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-CN01 — Missing customer_id (NULL)
    Target: ~1.5% ≈ 1,500 records
    """
    idx = allocate_indices(DQ_INJECTION_TARGETS["DQ-CN01"])
    df.loc[idx, "customer_id"] = np.nan
    return idx


def inject_cn02(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-CN02 — Missing product_id (NULL)
    Target: ~0.8% ≈ 800 records
    """
    idx = allocate_indices(DQ_INJECTION_TARGETS["DQ-CN02"])
    df.loc[idx, "product_id"] = np.nan
    return idx


def inject_cn03(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-CN03 — Missing transaction_date (NULL)
    Target: ~0.2% ≈ 200 records
    """
    idx = allocate_indices(DQ_INJECTION_TARGETS["DQ-CN03"])
    df.loc[idx, "transaction_date"] = np.nan
    return idx


def inject_vl01(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-VL01 — Invalid quantity (quantity <= 0)
    Inject values: 0, -1, -5, -10
    Target: ~0.5% ≈ 500 records
    """
    idx      = allocate_indices(DQ_INJECTION_TARGETS["DQ-VL01"])
    inj_rng  = np.random.default_rng(SEED + 101)
    bad_vals = [0, -1, -5, -10]
    for i in idx:
        df.at[i, "quantity"] = bad_vals[inj_rng.integers(0, len(bad_vals))]
    return idx


def inject_vl02(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-VL02 — Invalid unit_price (unit_price < 0)
    Inject random negative prices.
    Target: ~0.2% ≈ 200 records
    """
    idx     = allocate_indices(DQ_INJECTION_TARGETS["DQ-VL02"])
    inj_rng = np.random.default_rng(SEED + 102)
    for i in idx:
        df.at[i, "unit_price"] = round(float(-inj_rng.uniform(1_000, 500_000)), 2)
    return idx


def inject_vl03(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-VL03 — Invalid discount_pct (outside [0, 100])
    Inject values: -10, 110, 150
    Target: ~0.5% ≈ 500 records
    """
    idx      = allocate_indices(DQ_INJECTION_TARGETS["DQ-VL03"])
    inj_rng  = np.random.default_rng(SEED + 103)
    bad_vals = [-10.0, 110.0, 150.0]
    for i in idx:
        df.at[i, "discount_pct"] = bad_vals[inj_rng.integers(0, len(bad_vals))]
    return idx


def inject_vl04(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-VL04 — Invalid payment_method (not in allowed set)
    Inject values: "Unknown", "Crypto", "Invalid"
    Target: ~0.3% ≈ 300 records
    """
    idx      = allocate_indices(DQ_INJECTION_TARGETS["DQ-VL04"])
    inj_rng  = np.random.default_rng(SEED + 104)
    bad_vals = ["Unknown", "Crypto", "Invalid"]
    for i in idx:
        df.at[i, "payment_method"] = bad_vals[inj_rng.integers(0, len(bad_vals))]
    return idx


def inject_cs01(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-CS01 — Orphan customer_id (not in customers master)
    Replace customer_id with IDs that do not exist in master.
    Target: ~0.4% ≈ 400 records
    """
    idx     = allocate_indices(DQ_INJECTION_TARGETS["DQ-CS01"])
    inj_rng = np.random.default_rng(SEED + 201)
    orphan_pool = [f"CUS{90000 + i:05d}XXX" for i in range(50)]  # guaranteed non-existent
    for i in idx:
        df.at[i, "customer_id"] = orphan_pool[inj_rng.integers(0, len(orphan_pool))]
    return idx


def inject_cs02(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-CS02 — Orphan product_id (not in products master)
    Replace product_id with IDs that do not exist in master.
    Target: ~0.2% ≈ 200 records
    """
    idx     = allocate_indices(DQ_INJECTION_TARGETS["DQ-CS02"])
    inj_rng = np.random.default_rng(SEED + 202)
    orphan_pool = [f"PRD{90000 + i:05d}XXX" for i in range(50)]  # guaranteed non-existent
    for i in idx:
        df.at[i, "product_id"] = orphan_pool[inj_rng.integers(0, len(orphan_pool))]
    return idx


def inject_cs03(df: pd.DataFrame, stores_df: pd.DataFrame) -> np.ndarray:
    """
    DQ-CS03 — Store-Region mismatch (transaction region_id != store's master region_id)

    Strategy:
        For each target row, the store_id remains valid.
        The transaction's region_id is replaced with a DIFFERENT region
        than what the master stores table says for that store.

        stores.csv remains CLEAN — only sales.region_id is corrupted.

    This makes the rule genuinely testable:
        sales.region_id != stores.region_id  for the same store_id

    Target: ~0.6% ≈ 600 records
    """
    idx          = allocate_indices(DQ_INJECTION_TARGETS["DQ-CS03"])
    inj_rng      = np.random.default_rng(SEED + 203)
    store_region = dict(zip(stores_df["store_id"], stores_df["region_id"]))
    all_regions  = list(store_region.values())
    region_ids   = [f"REG{i:03d}" for i in range(1, N_REGIONS + 1)]

    for i in idx:
        correct_region = store_region[df.at[i, "store_id"]]
        # Pick any region that is different from the correct one
        wrong_options = [r for r in region_ids if r != correct_region]
        df.at[i, "region_id"] = wrong_options[inj_rng.integers(0, len(wrong_options))]
    return idx


def inject_cs04(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-CS04 — Incorrect sales_amount (does not equal qty × unit_price × (1 - disc/100))

    Inject manipulated sales_amount by multiplying expected by a bad factor:
        0.50 × expected
        0.75 × expected
        1.10 × expected
        1.25 × expected
        1.50 × expected

    Target: ~0.7% ≈ 700 records
    """
    idx         = allocate_indices(DQ_INJECTION_TARGETS["DQ-CS04"])
    inj_rng     = np.random.default_rng(SEED + 204)
    bad_factors = [0.50, 0.75, 1.10, 1.25, 1.50]
    for i in idx:
        qty    = df.at[i, "quantity"]
        price  = df.at[i, "unit_price"]
        disc   = df.at[i, "discount_pct"]
        try:
            expected = qty * price * (1 - disc / 100)
        except Exception:
            expected = 0.0
        factor = bad_factors[inj_rng.integers(0, len(bad_factors))]
        df.at[i, "sales_amount"] = round(float(expected * factor), 2)
    return idx


def inject_un01(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-UN01 — Duplicate transaction_id

    CONTRACT CORRECTION 1:
        Physical row count MUST remain exactly 100,000.
        Duplicates are created by COPYING an existing transaction_id
        into a target row (not by appending rows).

    Strategy:
        1. Allocate ~300 "receiver" rows (from non-overlapping pool).
        2. Separately sample ~300 "donor" rows from the unused pool.
        3. Copy donor's transaction_id into receiver's transaction_id.

    Result:
        - Physical rows:      100,000  (unchanged)
        - Unique TXN IDs:    ~99,700
        - Duplicate TXN IDs: ~300

    Target: ~0.3% ≈ 300 records
    """
    n_dup   = DQ_INJECTION_TARGETS["DQ-UN01"]
    idx     = allocate_indices(n_dup)   # receiver rows
    inj_rng = np.random.default_rng(SEED + 301)

    # Sample donor rows from the still-unused pool
    available_donors = np.array(sorted(set(range(N_SALES)) - _used_indices))
    donor_idx        = inj_rng.choice(available_donors, size=n_dup, replace=False)

    for receiver, donor in zip(idx, donor_idx):
        df.at[receiver, "transaction_id"] = df.at[donor, "transaction_id"]
    return idx


def inject_ac01(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-AC01 — Completed order with sales_amount <= 0

    CONTRACT CORRECTION 2:
        Must NOT trigger DQ-CS04 as a side effect.

    Strategy (unit_price = 0 isolation):
        order_status  = "Completed"
        unit_price    = 0.00
        quantity      > 0  (kept valid)
        discount_pct  ∈ [0, 30]  (kept valid)
        sales_amount  = 0.00

        Expected = qty × 0.00 × (1 - disc/100) = 0.00
        Actual   = 0.00
        → DQ-CS04 formula: 0.00 == 0.00  → PASS (no CS04 violation)
        → DQ-AC01: Completed + 0.00 amount → FAIL (AC01 fires)

    Target: ~0.2% ≈ 200 records
    """
    idx     = allocate_indices(DQ_INJECTION_TARGETS["DQ-AC01"])
    for i in idx:
        df.at[i, "order_status"]  = "Completed"
        df.at[i, "unit_price"]    = 0.00
        df.at[i, "sales_amount"]  = 0.00
        # quantity and discount_pct remain as originally generated (valid)
    return idx


def inject_ac02(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-AC02 — Abnormal sales_amount (> 2× expected)

    Threshold (documented, deterministic):
        sales_amount > qty × unit_price × (1 - discount_pct/100) × 2.0

    Strategy:
        Set sales_amount = expected × 3.0  (well above the 2× threshold)
        Rows are drawn from clean (non-injected) pool to ensure
        the formula baseline is valid.

    Target: ~0.3% ≈ 300 records
    """
    idx = allocate_indices(DQ_INJECTION_TARGETS["DQ-AC02"])
    for i in idx:
        qty    = df.at[i, "quantity"]
        price  = df.at[i, "unit_price"]
        disc   = df.at[i, "discount_pct"]
        try:
            expected = qty * price * (1 - disc / 100)
        except Exception:
            expected = 1.0
        df.at[i, "sales_amount"] = round(float(expected * 3.0), 2)
    return idx


def inject_ac03(df: pd.DataFrame) -> np.ndarray:
    """
    DQ-AC03 — Transaction date outside business period [2025-01-01, 2025-12-31]

    Inject dates in 2026 (e.g., 2026-01-01 through 2026-06-30).
    Target: ~0.2% ≈ 200 records
    """
    idx     = allocate_indices(DQ_INJECTION_TARGETS["DQ-AC03"])
    inj_rng = np.random.default_rng(SEED + 401)
    out_of_period = [
        "2026-01-01", "2026-01-15", "2026-02-01", "2026-02-15",
        "2026-03-01", "2026-03-20", "2026-04-10", "2026-05-05",
        "2026-06-01", "2026-06-30",
    ]
    for i in idx:
        df.at[i, "transaction_date"] = out_of_period[inj_rng.integers(0, len(out_of_period))]
    return idx


def run_all_injections(
    df:          pd.DataFrame,
    stores_df:   pd.DataFrame,
) -> dict:
    """
    Run all 15 DQ injections in rule-ID order.
    Each rule claims exclusive index slots via the central allocator.

    Returns a dict mapping rule_id → injected index array.
    """
    reset_allocator()   # Ensure fresh state (important for determinism)
    # Re-seed the allocator-facing RNG so that index selection is deterministic
    global rng
    rng = np.random.default_rng(SEED)

    injection_map = {}
    injection_map["DQ-CN01"] = inject_cn01(df)
    injection_map["DQ-CN02"] = inject_cn02(df)
    injection_map["DQ-CN03"] = inject_cn03(df)
    injection_map["DQ-VL01"] = inject_vl01(df)
    injection_map["DQ-VL02"] = inject_vl02(df)
    injection_map["DQ-VL03"] = inject_vl03(df)
    injection_map["DQ-VL04"] = inject_vl04(df)
    injection_map["DQ-CS01"] = inject_cs01(df)
    injection_map["DQ-CS02"] = inject_cs02(df)
    injection_map["DQ-CS03"] = inject_cs03(df, stores_df)
    injection_map["DQ-CS04"] = inject_cs04(df)
    injection_map["DQ-UN01"] = inject_un01(df)
    injection_map["DQ-AC01"] = inject_ac01(df)
    injection_map["DQ-AC02"] = inject_ac02(df)
    injection_map["DQ-AC03"] = inject_ac03(df)
    return injection_map


# ============================================================
# 7. VALIDATION
# ============================================================

class ValidationResult:
    def __init__(self):
        self.structural_pass   = True
        self.referential_pass  = True
        self.business_pass     = True
        self.messages          = []

    def fail(self, section: str, msg: str):
        self.messages.append(f"[{section}] FAIL: {msg}")
        if section == "STRUCTURAL":
            self.structural_pass = False
        elif section == "REFERENTIAL":
            self.referential_pass = False
        elif section == "BUSINESS":
            self.business_pass = False

    def warn(self, section: str, msg: str):
        self.messages.append(f"[{section}] EXPECTED: {msg}")


def validate_structural(
    regions_df:   pd.DataFrame,
    stores_df:    pd.DataFrame,
    products_df:  pd.DataFrame,
    customers_df: pd.DataFrame,
    date_df:      pd.DataFrame,
    sales_df:     pd.DataFrame,
    result:       ValidationResult,
):
    """Validate row counts, column presence, PK uniqueness, and date coverage."""

    # Row counts
    checks = [
        ("Regions",   regions_df,   N_REGIONS),
        ("Stores",    stores_df,    N_STORES),
        ("Products",  products_df,  N_PRODUCTS),
        ("Customers", customers_df, N_CUSTOMERS),
        ("Dates",     date_df,      365),
        ("Sales",     sales_df,     N_SALES),
    ]
    for name, df, expected in checks:
        if len(df) != expected:
            result.fail("STRUCTURAL", f"{name}: expected {expected}, got {len(df)}")

    # Physical sales rows (CC-1 contract)
    phys_rows  = len(sales_df)
    unique_ids = sales_df["transaction_id"].nunique()
    dup_ids    = phys_rows - unique_ids

    # Required columns
    col_requirements = {
        "regions":   ["region_id", "region_name", "island"],
        "stores":    ["store_id", "store_name", "region_id", "city", "store_type", "opening_date"],
        "products":  ["product_id", "product_name", "category", "subcategory", "brand", "unit_cost", "list_price"],
        "customers": ["customer_id", "customer_name", "gender", "age_group", "city", "region_id",
                      "customer_segment", "registration_date"],
        "date":      ["date", "year", "quarter", "month_number", "month_name", "week_number",
                      "day_name", "is_weekend"],
        "sales":     ["transaction_id", "transaction_date", "customer_id", "product_id", "store_id",
                      "region_id", "quantity", "unit_price", "discount_pct", "sales_amount",
                      "payment_method", "order_status"],
    }
    dfs = {"regions": regions_df, "stores": stores_df, "products": products_df,
           "customers": customers_df, "date": date_df, "sales": sales_df}
    for tbl, cols in col_requirements.items():
        missing = [c for c in cols if c not in dfs[tbl].columns]
        if missing:
            result.fail("STRUCTURAL", f"{tbl} missing columns: {missing}")

    # PK uniqueness on master tables
    for name, df, pk_col in [
        ("regions",   regions_df,   "region_id"),
        ("stores",    stores_df,    "store_id"),
        ("products",  products_df,  "product_id"),
        ("customers", customers_df, "customer_id"),
        ("date",      date_df,      "date"),
    ]:
        if df[pk_col].duplicated().any():
            result.fail("STRUCTURAL", f"{name}.{pk_col} has duplicate values")

    # Date dimension spans exactly 2025
    if date_df is not None and len(date_df) > 0:
        min_d = date_df["date"].min()
        max_d = date_df["date"].max()
        if min_d != "2025-01-01":
            result.fail("STRUCTURAL", f"Date dim starts at {min_d}, expected 2025-01-01")
        if max_d != "2025-12-31":
            result.fail("STRUCTURAL", f"Date dim ends at {max_d}, expected 2025-12-31")

    return phys_rows, unique_ids, dup_ids


def validate_referential(
    sales_df:     pd.DataFrame,
    customers_df: pd.DataFrame,
    products_df:  pd.DataFrame,
    stores_df:    pd.DataFrame,
    injection_map: dict,
    result:       ValidationResult,
):
    """
    FK validation with EXPECTED-violation classification.
    Rows intentionally injected as orphans or NULL are excluded from FAIL.
    """
    cn01_idx = set(injection_map["DQ-CN01"].tolist())
    cn02_idx = set(injection_map["DQ-CN02"].tolist())
    cs01_idx = set(injection_map["DQ-CS01"].tolist())
    cs02_idx = set(injection_map["DQ-CS02"].tolist())

    valid_customers = set(customers_df["customer_id"])
    valid_products  = set(products_df["product_id"])
    valid_stores    = set(stores_df["store_id"])

    # customer_id FK
    cust_violations = 0
    for i, row in sales_df.iterrows():
        if i in cn01_idx or i in cs01_idx:
            continue  # Expected NULL or orphan
        cid = row["customer_id"]
        if pd.isna(cid):
            result.warn("REFERENTIAL", f"Unexpected NULL customer_id at row {i}")
        elif cid not in valid_customers:
            cust_violations += 1
    if cust_violations > 0:
        result.fail("REFERENTIAL", f"{cust_violations} unexpected orphan customer_ids")

    # product_id FK
    prod_violations = 0
    for i, row in sales_df.iterrows():
        if i in cn02_idx or i in cs02_idx:
            continue
        pid = row["product_id"]
        if pd.isna(pid):
            result.warn("REFERENTIAL", f"Unexpected NULL product_id at row {i}")
        elif pid not in valid_products:
            prod_violations += 1
    if prod_violations > 0:
        result.fail("REFERENTIAL", f"{prod_violations} unexpected orphan product_ids")

    # store_id FK (no store orphan injection — must be 100% valid)
    bad_stores = sales_df[~sales_df["store_id"].isin(valid_stores)]
    if len(bad_stores) > 0:
        result.fail("REFERENTIAL", f"{len(bad_stores)} invalid store_id references")

    # Classify expected violations
    result.warn("REFERENTIAL",
        f"DQ-CN01: {len(cn01_idx)} NULL customer_ids (expected)")
    result.warn("REFERENTIAL",
        f"DQ-CN02: {len(cn02_idx)} NULL product_ids (expected)")
    result.warn("REFERENTIAL",
        f"DQ-CS01: {len(cs01_idx)} orphan customer_ids (expected)")
    result.warn("REFERENTIAL",
        f"DQ-CS02: {len(cs02_idx)} orphan product_ids (expected)")


def validate_business_logic(
    sales_df:      pd.DataFrame,
    injection_map: dict,
    result:        ValidationResult,
):
    """
    Validate clean records against business rules.
    Rows in any injection index set are excluded from clean-data checks.
    """
    # Build combined injected index set
    all_injected = set()
    for indices in injection_map.values():
        all_injected.update(indices.tolist())

    clean_df = sales_df[~sales_df.index.isin(all_injected)].copy()

    # Formula check: sales_amount = qty × unit_price × (1 - disc/100)
    clean_df["expected_amount"] = (
        clean_df["quantity"].astype(float)
        * clean_df["unit_price"].astype(float)
        * (1 - clean_df["discount_pct"].astype(float) / 100)
    ).round(2)
    # Tolerance of 0.05 (5 IDR) accounts for Python round() vs pandas .round()
    # floating-point precision differences on edge-case values.
    # Any real CS04 formula violation differs by at least 25% of transaction
    # value (minimum factor 0.75x), which is thousands of IDR — far above 0.05.
    formula_violations = ((clean_df["sales_amount"] - clean_df["expected_amount"]).abs() > 0.05).sum()
    if formula_violations > 0:
        result.fail("BUSINESS", f"{formula_violations} clean records have incorrect sales_amount (>0.05 IDR diff)")

    # quantity > 0
    bad_qty = (clean_df["quantity"].astype(float) <= 0).sum()
    if bad_qty > 0:
        result.fail("BUSINESS", f"{bad_qty} clean records have quantity <= 0")

    # discount_pct ∈ [0, 100]
    bad_disc = ((clean_df["discount_pct"].astype(float) < 0) | (clean_df["discount_pct"].astype(float) > 100)).sum()
    if bad_disc > 0:
        result.fail("BUSINESS", f"{bad_disc} clean records have invalid discount_pct")

    # unit_price >= 0
    bad_price = (clean_df["unit_price"].astype(float) < 0).sum()
    if bad_price > 0:
        result.fail("BUSINESS", f"{bad_price} clean records have negative unit_price")

    # payment_method ∈ allowed
    bad_pay = (~clean_df["payment_method"].isin(PAYMENT_METHODS)).sum()
    if bad_pay > 0:
        result.fail("BUSINESS", f"{bad_pay} clean records have invalid payment_method")

    # transaction_date ∈ [2025-01-01, 2025-12-31]
    non_null_dates = clean_df["transaction_date"].dropna()
    bad_dates = ((non_null_dates < "2025-01-01") | (non_null_dates > "2025-12-31")).sum()
    if bad_dates > 0:
        result.fail("BUSINESS", f"{bad_dates} clean records have out-of-period transaction_date")


# ============================================================
# 8. DQ COMPATIBILITY AUDIT
# ============================================================

def audit_dq_compatibility(
    sales_df:      pd.DataFrame,
    stores_df:     pd.DataFrame,
    customers_df:  pd.DataFrame,
    products_df:   pd.DataFrame,
    injection_map: dict,
) -> dict:
    """
    For each of 15 DQ rules, count detectable violations in the raw dataset.
    Returns dict: rule_id → detected_count

    Tolerance: ±10% relative of target count is acceptable.
    """
    results = {}

    # --- DQ-CN01: NULL customer_id ---
    results["DQ-CN01"] = int(sales_df["customer_id"].isna().sum())

    # --- DQ-CN02: NULL product_id ---
    results["DQ-CN02"] = int(sales_df["product_id"].isna().sum())

    # --- DQ-CN03: NULL transaction_date ---
    results["DQ-CN03"] = int(sales_df["transaction_date"].isna().sum())

    # --- DQ-VL01: quantity <= 0 ---
    results["DQ-VL01"] = int((pd.to_numeric(sales_df["quantity"], errors="coerce") <= 0).sum())

    # --- DQ-VL02: unit_price < 0 ---
    results["DQ-VL02"] = int((pd.to_numeric(sales_df["unit_price"], errors="coerce") < 0).sum())

    # --- DQ-VL03: discount_pct outside [0, 100] ---
    disc = pd.to_numeric(sales_df["discount_pct"], errors="coerce")
    results["DQ-VL03"] = int(((disc < 0) | (disc > 100)).sum())

    # --- DQ-VL04: invalid payment_method ---
    results["DQ-VL04"] = int((~sales_df["payment_method"].isin(PAYMENT_METHODS)).sum())

    # --- DQ-CS01: orphan customer_id ---
    valid_custs = set(customers_df["customer_id"])
    non_null_cids = sales_df["customer_id"].dropna()
    results["DQ-CS01"] = int((~non_null_cids.isin(valid_custs)).sum())

    # --- DQ-CS02: orphan product_id ---
    valid_prods = set(products_df["product_id"])
    non_null_pids = sales_df["product_id"].dropna()
    results["DQ-CS02"] = int((~non_null_pids.isin(valid_prods)).sum())

    # --- DQ-CS03: store-region mismatch ---
    # Join sales → stores on store_id, compare sales.region_id vs stores.region_id
    store_map    = stores_df.set_index("store_id")["region_id"].to_dict()
    # Only consider rows with valid store_id
    mask_valid   = sales_df["store_id"].isin(store_map)
    temp         = sales_df[mask_valid].copy()
    temp["store_region"] = temp["store_id"].map(store_map)
    results["DQ-CS03"] = int((temp["region_id"] != temp["store_region"]).sum())

    # --- DQ-CS04: sales_amount != qty × unit_price × (1 - disc/100) ---
    qty    = pd.to_numeric(sales_df["quantity"],    errors="coerce")
    price  = pd.to_numeric(sales_df["unit_price"],  errors="coerce")
    disc   = pd.to_numeric(sales_df["discount_pct"],errors="coerce")
    amt    = pd.to_numeric(sales_df["sales_amount"],errors="coerce")
    expected = (qty * price * (1 - disc / 100)).round(2)
    results["DQ-CS04"] = int(((amt - expected).abs() > 0.01).sum())

    # --- DQ-UN01: duplicate transaction_id ---
    phys_rows  = len(sales_df)
    unique_ids = sales_df["transaction_id"].nunique()
    results["DQ-UN01"] = phys_rows - unique_ids  # number of duplicate entries

    # --- DQ-AC01: Completed order with sales_amount <= 0 ---
    mask_completed = sales_df["order_status"] == "Completed"
    mask_nonpos    = pd.to_numeric(sales_df["sales_amount"], errors="coerce") <= 0
    results["DQ-AC01"] = int((mask_completed & mask_nonpos).sum())

    # --- DQ-AC02: sales_amount > 2× expected (abnormal) ---
    # Threshold: sales_amount > qty × unit_price × (1 - disc/100) × 2.0
    threshold = (qty * price * (1 - disc / 100) * 2.0).round(2)
    results["DQ-AC02"] = int((amt > threshold).sum())

    # --- DQ-AC03: transaction_date outside 2025 ---
    dates = sales_df["transaction_date"].dropna()
    results["DQ-AC03"] = int(((dates < "2025-01-01") | (dates > "2025-12-31")).sum())

    return results


# ============================================================
# 9. SAVING
# ============================================================

def save_datasets(
    regions_df:   pd.DataFrame,
    stores_df:    pd.DataFrame,
    products_df:  pd.DataFrame,
    customers_df: pd.DataFrame,
    date_df:      pd.DataFrame,
    sales_df:     pd.DataFrame,
):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    regions_df.to_csv(  os.path.join(OUTPUT_DIR, "regions.csv"),   index=False)
    stores_df.to_csv(   os.path.join(OUTPUT_DIR, "stores.csv"),    index=False)
    products_df.to_csv( os.path.join(OUTPUT_DIR, "products.csv"),  index=False)
    customers_df.to_csv(os.path.join(OUTPUT_DIR, "customers.csv"), index=False)
    date_df.to_csv(     os.path.join(OUTPUT_DIR, "date.csv"),      index=False)
    sales_df.to_csv(    os.path.join(OUTPUT_DIR, "sales.csv"),     index=False)
    print(f"\nDatasets saved to: {os.path.abspath(OUTPUT_DIR)}")


# ============================================================
# 10. CONSOLE REPORT
# ============================================================

def print_report(
    regions_df:    pd.DataFrame,
    stores_df:     pd.DataFrame,
    products_df:   pd.DataFrame,
    customers_df:  pd.DataFrame,
    date_df:       pd.DataFrame,
    sales_df:      pd.DataFrame,
    phys_rows:     int,
    unique_ids:    int,
    dup_ids:       int,
    dq_counts:     dict,
    val_result:    ValidationResult,
    injection_map: dict,
):
    def check(condition): return "[OK]" if condition else "[!!]"
    def pad(label, width=35): return label.ljust(width)

    # DQ rule compatibility (PASS = detected count > 0)
    rule_pass = {rule: dq_counts[rule] > 0 for rule in dq_counts}

    # Injection coverage: compare injected row count vs target (±10% relative).
    # Uses actual INJECTED counts (from injection_map), NOT detected counts.
    # Detected counts (from dq_counts) include secondary natural violations
    # from other injections (CC-3 detection overlap), so they are NOT used here.
    def injected_count(rule_id):
        return len(injection_map[rule_id])

    def in_tolerance(rule_id):
        target  = DQ_INJECTION_TARGETS[rule_id]
        actual  = injected_count(rule_id)
        lo      = target * (1 - TOLERANCE)
        hi      = target * (1 + TOLERANCE)
        return lo <= actual <= hi

    print()
    print("=" * 60)
    print("NUSANTARA RETAIL")
    print("DATASET GENERATION & DQ COMPATIBILITY AUDIT")
    print("=" * 60)

    print("\nSTRUCTURAL VALIDATION")
    print("-" * 60)
    print(f"{pad('Regions')} : {len(regions_df):<10} {check(len(regions_df) == N_REGIONS)}")
    print(f"{pad('Products')} : {len(products_df):<10} {check(len(products_df) == N_PRODUCTS)}")
    print(f"{pad('Stores')} : {len(stores_df):<10} {check(len(stores_df) == N_STORES)}")
    print(f"{pad('Customers')} : {len(customers_df):<10} {check(len(customers_df) == N_CUSTOMERS)}")
    print(f"{pad('Date dimension')} : {len(date_df):<10} {check(len(date_df) == 365)}")
    print(f"{pad('Sales transactions (physical)')} : {phys_rows:<10} {check(phys_rows == N_SALES)}")
    print(f"{pad('  Unique transaction IDs')} : {unique_ids:<10}")
    print(f"{pad('  Duplicate transaction IDs')} : {dup_ids:<10} {check(dup_ids > 0)}")

    print("\nDQ INJECTION COVERAGE")
    print("-" * 60)
    print(f"  Note: 'Actual' = primary injected rows. Detected violations")
    print(f"  may be higher due to natural secondary detection overlap (CC-3).")
    print("-" * 60)
    print(f"{'Rule':<10} {'Issue':<35} {'Target':>7} {'Actual':>7} {'Tol':>6} {'OK?':>4}")
    print("-" * 60)
    rule_labels = {
        "DQ-CN01": "Missing Customer ID",
        "DQ-CN02": "Missing Product ID",
        "DQ-CN03": "Missing Transaction Date",
        "DQ-VL01": "Invalid Quantity",
        "DQ-VL02": "Invalid Unit Price",
        "DQ-VL03": "Invalid Discount",
        "DQ-VL04": "Invalid Payment Method",
        "DQ-CS01": "Orphan Customer",
        "DQ-CS02": "Orphan Product",
        "DQ-CS03": "Store-Region Mismatch",
        "DQ-CS04": "Incorrect Sales Amount",
        "DQ-UN01": "Duplicate Transaction ID",
        "DQ-AC01": "Completed + Non-positive Amt",
        "DQ-AC02": "Abnormal Sales Amount",
        "DQ-AC03": "Out-of-period Date",
    }
    for rule_id, label in rule_labels.items():
        target   = DQ_INJECTION_TARGETS[rule_id]
        injected = injected_count(rule_id)
        detected = dq_counts[rule_id]
        ok       = check(in_tolerance(rule_id))
        print(f"{rule_id:<10} {label:<35} {target:>7} {injected:>7}  +/-10% {ok}  (detected: {detected})")

    print("\nDQ RULE COMPATIBILITY")
    print("-" * 60)
    for rule_id, label in rule_labels.items():
        status = check(rule_pass[rule_id])
        print(f"{rule_id:<10}  {label:<35} {status}")

    all_pass = all(rule_pass.values())
    testable_count = sum(rule_pass.values())
    print("-" * 60)
    print(f"{testable_count}/15 DQ RULES TESTABLE".ljust(50) + f" {check(all_pass)}")
    print("-" * 60)

    print("\nDATASET VALIDATION")
    print("-" * 60)
    print(f"{'Structural validation':<40} {'PASS' if val_result.structural_pass  else 'FAIL'}")
    print(f"{'Referential validation':<40} {'PASS*' if val_result.referential_pass else 'FAIL'}")
    print(f"{'Business rule validation':<40} {'PASS*' if val_result.business_pass   else 'FAIL'}")
    inj_coverage_pass = all(in_tolerance(r) for r in DQ_INJECTION_TARGETS)
    print(f"{'DQ injection coverage':<40} {'PASS' if inj_coverage_pass else 'FAIL'}")
    print(f"{'DQ rule compatibility':<40} {'PASS' if all_pass else 'FAIL'}")
    print()
    print("* Expected intentional violations are excluded")
    print("  from clean-data validation failures.")

    if val_result.messages:
        print("\nVALIDATION DETAIL")
        print("-" * 60)
        for msg in val_result.messages:
            print(f"  {msg}")

    overall_pass = (
        val_result.structural_pass
        and val_result.referential_pass
        and val_result.business_pass
        and inj_coverage_pass
        and all_pass
    )
    print()
    print("=" * 60)
    if overall_pass:
        print("DATASET STATUS: READY FOR PHASE 3")
    else:
        print("DATASET STATUS: NOT READY -- review failures above")
    print("=" * 60)
    print()
    return overall_pass


# ============================================================
# 11. MAIN
# ============================================================

def main():
    print("=" * 60)
    print("NUSANTARA RETAIL - Phase 2 Dataset Generator")
    print(f"Seed: {SEED}  |  Target rows: {N_SALES:,}")
    print("=" * 60)

    # ── Master Data ──────────────────────────────────────────
    print("\n[1/5] Generating master data...")
    regions_df   = generate_regions()
    stores_df    = generate_stores(regions_df)
    products_df  = generate_products()
    customers_df = generate_customers(regions_df)
    date_df      = generate_date_dim()
    print(f"      Regions:   {len(regions_df)}")
    print(f"      Stores:    {len(stores_df)}")
    print(f"      Products:  {len(products_df)}")
    print(f"      Customers: {len(customers_df)}")
    print(f"      Dates:     {len(date_df)}")

    # ── Transactions ─────────────────────────────────────────
    print("\n[2/5] Generating clean transactions...")
    sales_df = generate_sales_clean(customers_df, products_df, stores_df)
    print(f"      Sales (clean base): {len(sales_df):,}")

    # ── DQ Injection ─────────────────────────────────────────
    print("\n[3/5] Injecting DQ issues...")
    injection_map = run_all_injections(sales_df, stores_df)
    for rule_id, idx in injection_map.items():
        print(f"      {rule_id}: {len(idx)} records injected")

    # Verify physical row count after injection (CC-1 contract)
    assert len(sales_df) == N_SALES, \
        f"Physical row count changed! Expected {N_SALES}, got {len(sales_df)}"

    # ── Saving ───────────────────────────────────────────────
    print("\n[4/5] Saving datasets...")
    save_datasets(regions_df, stores_df, products_df, customers_df, date_df, sales_df)

    # ── Validation & Audit ───────────────────────────────────
    print("\n[5/5] Running validation & DQ compatibility audit...")
    val_result = ValidationResult()

    phys_rows, unique_ids, dup_ids = validate_structural(
        regions_df, stores_df, products_df, customers_df, date_df, sales_df, val_result
    )
    validate_referential(
        sales_df, customers_df, products_df, stores_df, injection_map, val_result
    )
    validate_business_logic(sales_df, injection_map, val_result)
    dq_counts = audit_dq_compatibility(
        sales_df, stores_df, customers_df, products_df, injection_map
    )

    # ── Console Report ───────────────────────────────────────
    overall_pass = print_report(
        regions_df, stores_df, products_df, customers_df, date_df, sales_df,
        phys_rows, unique_ids, dup_ids,
        dq_counts, val_result, injection_map,
    )

    return 0 if overall_pass else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
