"""
Train the salary prediction model and save artifacts for the backend.

Run this once after the notebook to produce model files. The backend loads
these artifacts at startup. Re-run when training data changes.

Outputs (to artifacts/):
  - lgb_p25.joblib, lgb_p75.joblib  - the two quantile regressors
  - canonical_categories.json        - the categorical feature dtypes used at training
  - reference.json                   - lists of canonical roles, levels, etc. for UI
  - calibration_metadata.json        - thresholds and per-customer caveats
  - taxonomy_mappings.py             - role/level/location mapping functions

The data file used is the same Master sheet + customer-ID file.
"""
import json
import re
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
DATA_PATH = "/mnt/user-data/uploads/Master_sheet_-_Sheet_with_customer_ID.csv"

# ============================================================
# STEP 1: Load + clean (mirror of notebook sections 1-10)
# ============================================================

print("Loading data...")
df = pd.read_csv(DATA_PATH)
df['Actual start date'] = pd.to_datetime(df['Actual start date'], format='%m-%d-%Y', errors='coerce')
for c in ['Actual salary', 'Actual variable', 'Actual bonus amount', 'Actual equity']:
    df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce')
print(f"  Loaded {len(df):,} rows")

# Filter interns/contractors
mask = df['Employee type'].isin(['Intern', 'Contractor'])
df = df[~mask].reset_index(drop=True)
print(f"  After intern/contractor filter: {len(df):,}")

# Annualise pay
ANNUAL_MULTIPLIER = {'YEAR': 1, 'HOUR': 2080, 'WEEK': 52, 'MONTH': 12}
df['Actual salary annual'] = df['Actual salary'] * df['Actual pay rate'].map(ANNUAL_MULTIPLIER)

# FX to USD
FX_USD_PER_UNIT = {
    'USD': 1.0, 'GBP': 1.27, 'EUR': 1.08, 'AUD': 0.65, 'CAD': 0.74,
    'MXN': 0.056, 'JPY': 0.0067, 'INR': 0.012, 'ILS': 0.27, 'QAR': 0.275,
    'CHF': 1.13, 'SGD': 0.74, 'AED': 0.272, 'SAR': 0.267, 'NZD': 0.61,
    'HUF': 0.0028, 'BGN': 0.55, 'ISK': 0.0073, 'RON': 0.22, 'PLN': 0.25,
    'SEK': 0.095, 'NOK': 0.094,
}
df['Actual salary annual_usd'] = df['Actual salary annual'] * df['Actual pay currency'].map(FX_USD_PER_UNIT)

# Date filter
df = df[df['Actual start date'] >= pd.Timestamp('2018-01-01')].reset_index(drop=True)

# Low pay filter
df = df[~(df['Actual salary annual_usd'].notna() & (df['Actual salary annual_usd'] < 15_000))].reset_index(drop=True)

# Dedup
df = df.drop_duplicates().reset_index(drop=True)
print(f"  After cleanup: {len(df):,}")


# ============================================================
# STEP 2: Taxonomy mappings (roles, levels, locations)
# These need to be importable by the backend, so we copy the
# logic into a standalone module. For now: inline the mapping functions.
# ============================================================

# I'll write the taxonomy module as a separate file so the backend can import it.

print("Applying canonical taxonomy mappings...")
# Import the mapping logic from the notebook builder script
import sys
sys.path.insert(0, '/home/claude')

# Re-run the mapping logic. We'll save the mapping rules as Python so the
# backend can apply them at query time (the user gives raw role strings,
# the backend canonicalises before querying the model).
from taxonomy import (
    TAXONOMY, MAPPING_RULES, FUNCTION_FOR_LEAF,
    map_role_for_row, normalise_level, bucket_level,
    derive_track, MANAGER_ROLES, SUPPORT_ROLES, MANUFACTURING_ROLES,
    COMPILED_LOCATION_RULES, is_remote_string, map_location, to_quarter_numeric,
    quarter_label, REFERENCE_DATE,
)

# Apply role mapping
mapping_results = df.apply(map_role_for_row, axis=1, result_type='expand')
mapping_results.columns = ['canonical_role', 'mapping_source']
df['canonical_role'] = mapping_results['canonical_role']
df['canonical_function'] = df['canonical_role'].map(FUNCTION_FOR_LEAF)

# Apply level mapping
df['level_normalised'] = df['Job level'].apply(normalise_level)
df['level_canonical'] = df['level_normalised'].apply(bucket_level)
# Auto-rare reroute
cc = df['level_canonical'].value_counts()
auto_rare = cc[cc < 20].index.tolist()
df['level_canonical'] = df['level_canonical'].apply(lambda x: 'Unknown' if x in auto_rare else x)
df['level_track'] = df.apply(derive_track, axis=1)

# Apply location mapping
loc_results = df['Location'].apply(map_location)
df['country'] = loc_results.apply(lambda t: t[0])
df['metro'] = loc_results.apply(lambda t: t[1])
df['is_remote'] = loc_results.apply(lambda t: t[2])

# Quarter
df['hire_quarter_numeric'] = df['Actual start date'].apply(to_quarter_numeric)

print(f"  Mapping done. Canonical role distribution: {df['canonical_role'].nunique()} distinct")


# ============================================================
# STEP 3: Train the LightGBM quantile model
# ============================================================

print("Training LightGBM model (with Section 13h hyperparameters)...")

modellable = df[
    (df['canonical_role'] != 'Other') &
    (df['country'] != 'Other / Unknown') &
    (df['Actual salary annual_usd'].notna()) &
    (df['Actual start date'].notna()) &
    (df['canonical_role'].notna()) &
    (df['level_canonical'].notna()) &
    (df['country'].notna()) &
    (df['hire_quarter_numeric'].notna())
].copy()
modellable['metro'] = modellable['metro'].fillna('(no metro)')
modellable['log_salary'] = np.log(modellable['Actual salary annual_usd'])
print(f"  Modellable rows: {len(modellable):,}")

FEATURE_COLS = [
    'canonical_role', 'canonical_function', 'level_canonical', 'level_track',
    'country', 'metro', 'is_remote', 'hire_quarter_numeric',
]
CAT_COLS = ['canonical_role', 'canonical_function', 'level_canonical', 'level_track',
            'country', 'metro']

import lightgbm as lgb

# Use ALL modellable data for the production model (no val split — we already validated
# in the notebook on the held-out 2026 test set. For production we use everything.)
train = modellable[FEATURE_COLS].copy()
for col in CAT_COLS:
    train[col] = train[col].astype('category')

y = modellable['log_salary']

# Winning hyperparameters from Section 13h
HP = dict(
    objective='quantile',
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=15,
    min_child_samples=10,
    max_depth=-1,
    verbosity=-1,
    random_state=42,
)

print("  Fitting q=0.20...")
m_lo = lgb.LGBMRegressor(alpha=0.20, **HP)
m_lo.fit(train, y, categorical_feature=CAT_COLS)

print("  Fitting q=0.80...")
m_hi = lgb.LGBMRegressor(alpha=0.80, **HP)
m_hi.fit(train, y, categorical_feature=CAT_COLS)

# Save the categorical schemas — backend needs these to encode queries the same way
categorical_schemas = {col: list(train[col].cat.categories) for col in CAT_COLS}

# ============================================================
# STEP 4: Save artifacts
# ============================================================

print("Saving artifacts...")

joblib.dump(m_lo, ARTIFACTS_DIR / "lgb_p25.joblib")
joblib.dump(m_hi, ARTIFACTS_DIR / "lgb_p75.joblib")

with open(ARTIFACTS_DIR / "categorical_schemas.json", "w") as f:
    json.dump(categorical_schemas, f, indent=2)

# Reference data for UI dropdowns
all_roles_with_counts = df['canonical_role'].value_counts().drop('Other', errors='ignore').to_dict()
reference = {
    'canonical_roles': sorted(all_roles_with_counts.keys()),
    'role_to_function': FUNCTION_FOR_LEAF,
    'level_canonicals': sorted([x for x in df['level_canonical'].unique() if x != 'Unknown']) + ['Unknown'],
    'countries': sorted([x for x in df['country'].unique() if x != 'Other / Unknown']),
    'metros_by_country': df.groupby('country')['metro'].apply(
        lambda s: sorted([m for m in s.dropna().unique()])
    ).to_dict(),
    'reference_date': REFERENCE_DATE.strftime('%Y-%m-%d'),
}
with open(ARTIFACTS_DIR / "reference.json", "w") as f:
    json.dump(reference, f, indent=2, default=str)

# Build the support index — for the abstention wrapper
support_levels = [
    ('role+level+country+metro', ['canonical_role', 'level_canonical', 'country', 'metro']),
    ('role+level+country',       ['canonical_role', 'level_canonical', 'country']),
    ('role+level',               ['canonical_role', 'level_canonical']),
    ('role+country',             ['canonical_role', 'country']),
    ('role',                     ['canonical_role']),
]
support_index = {}
for level_name, cols in support_levels:
    counts = modellable.groupby(cols).size()
    support_index[level_name] = {
        '_keys': cols,
        '_counts': {'|'.join(str(k) for k in idx) if isinstance(idx, tuple) else str(idx): int(c)
                    for idx, c in counts.items()},
    }
with open(ARTIFACTS_DIR / "support_index.json", "w") as f:
    json.dump(support_index, f, indent=2)

# Per-customer calibration profile metadata
calibration = {
    'dominant_customers': ['SCAL', 'VANT', 'CRUS'],
    'note': (
        "Predictions are best-calibrated for customers whose hire mix resembles the "
        "highest-volume training contributors. Per-customer test-set coverage from "
        "Section 14f: SCAL 53.8%, VANT 56.0%, CRUS 55.8%, DOC 37.8%, IONQ 44.8%, "
        "LUCI 43.1%, STGK 34.0%, ABRI 62.9%, DECA 43.8%. Lower-coverage customers "
        "should treat predicted ranges as directional rather than authoritative."
    ),
    'per_customer_test_coverage': {
        'SCAL': 0.538, 'VANT': 0.560, 'CRUS': 0.558, 'DOC': 0.378,
        'IONQ': 0.448, 'LUCI': 0.431, 'STGK': 0.340, 'ABRI': 0.629,
        'DECA': 0.438, 'GH': 0.500,
    },
}
with open(ARTIFACTS_DIR / "calibration.json", "w") as f:
    json.dump(calibration, f, indent=2)

# Training pay profile — median pay per (canonical_role, level_track).
# Used by the orchestrator at query time to compare against customer pay profile
# and abstain when the customer's pay structure diverges from training (Design B).
print("Building training pay profile...")
pay_profile = (
    modellable
    .groupby(['canonical_role', 'level_track'])['Actual salary annual_usd']
    .agg(['median', 'count'])
    .reset_index()
)
# Only keep buckets with at least 5 rows
pay_profile = pay_profile[pay_profile['count'] >= 5]
pay_profile_dict = {
    f"{row['canonical_role']}|{row['level_track']}": {
        'median_usd': float(row['median']),
        'n_training_rows': int(row['count']),
    }
    for _, row in pay_profile.iterrows()
}
with open(ARTIFACTS_DIR / "training_pay_profile.json", "w") as f:
    json.dump(pay_profile_dict, f, indent=2)
print(f"  Training pay profile: {len(pay_profile_dict)} (role, track) buckets")

# Save the canonical benchmark data — the backend uses this to look up
# "matching historical hires" alongside predictions
benchmark_cols = [
    'CUSTOMER ID', 'canonical_role', 'canonical_function', 'level_canonical',
    'level_track', 'country', 'metro', 'is_remote', 'hire_quarter_numeric',
    'Actual salary annual_usd', 'Actual start date',
]
modellable[benchmark_cols].to_csv(ARTIFACTS_DIR / "benchmark.csv", index=False)

print(f"\nArtifacts saved to {ARTIFACTS_DIR}/:")
for f in sorted(ARTIFACTS_DIR.iterdir()):
    print(f"  {f.name:35s}  {f.stat().st_size:,} bytes")
