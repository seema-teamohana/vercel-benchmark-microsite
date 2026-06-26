"""
Orchestrator — bridges user-facing queries to the engine and customer data.

Responsibilities:
1. Canonicalise user inputs to the model's feature schema.
2. Look up customer-specific data (band, TTF, recent hires).
3. Call the engine for the market prediction.
4. Assemble the response payload with calibration caveats.
"""
import json
import math
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import sys

# Make the taxonomy module (in the backend root) importable
sys.path.insert(0, str(Path(__file__).parent.parent))
from taxonomy import (
    MAPPING_RULES, FUNCTION_FOR_LEAF, map_role_for_row,
    normalise_level, bucket_level, derive_track,
    map_location, to_quarter_numeric, quarter_label, REFERENCE_DATE,
)
from app.engine import get_engine

import pandas as pd


def clean_nan(obj):
    """Recursively replace NaN (and other non-JSON-compliant floats) with None.

    JSON doesn't have a representation for NaN/Infinity, so we have to scrub
    these before returning from the API. Called once on the final response.
    """
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj


CUSTOMER_DATA_DIR = Path(__file__).parent.parent / "data"


# Customer ID aliases: maps the file-based customer ID (lowercase, matches the
# CSV filename) to the anonymised ID used in the training data and calibration
# table.
CUSTOMER_ID_ALIASES = {
    'docker': 'DOC',
    # add others as confirmed
}


# Pay-calibration threshold for Design B: if the customer's median pay for a
# (role, track) bucket differs by more than this fraction from the training
# median for the same bucket, we abstain on that role for this customer.
PAY_DEVIATION_THRESHOLD = 0.30

# Minimum number of customer hires needed to compute a meaningful per-bucket
# median. Fewer than this and we can't reliably calibrate, so we don't try.
MIN_CUSTOMER_ROWS_PER_BUCKET = 3


class Orchestrator:
    """Stateful orchestrator. Loads customer files once at startup."""

    def __init__(self):
        self.engine = get_engine()
        self.customer_data = self._load_customer_files()
        self.benchmark = pd.read_csv(
            Path(__file__).parent.parent / "artifacts" / "benchmark.csv"
        )
        self.benchmark['Actual start date'] = pd.to_datetime(self.benchmark['Actual start date'])
        self.calibration = self.engine.calibration

        # Design B: load the training-data pay profile (median pay per (role, track) bucket).
        # Used at query time to compare against the customer's own pay profile.
        with open(Path(__file__).parent.parent / "artifacts" / "training_pay_profile.json") as f:
            self.training_pay_profile = json.load(f)

        # Build a per-customer pay profile from each customer's data.
        # Same shape: dict of "canonical_role|level_track" -> {median_usd, n_rows}.
        self.customer_pay_profiles = self._build_customer_pay_profiles()

    # ------------------------------------------------------------------
    # Per-customer pay profile builder (Design B)
    # ------------------------------------------------------------------
    def _build_customer_pay_profiles(self) -> dict:
        """For each loaded customer, compute median pay per (canonical_role, level_track).

        This canonicalises the customer's hires (via the same taxonomy used by the
        model) and aggregates pay by bucket. Used to detect customers whose pay
        structure differs from training data.
        """
        profiles = {}
        for customer_id, df in self.customer_data.items():
            df = df.copy()

            # Map customer rows to canonical roles using the taxonomy
            # We need 'Job role' and 'Job title' columns; the customer CSV has
            # 'job_role' and 'job_title', so we map them
            df_for_mapping = df.rename(columns={
                'job_role': 'Job role',
                'job_title': 'Job title',
            })
            mapping_results = df_for_mapping.apply(map_role_for_row, axis=1, result_type='expand')
            mapping_results.columns = ['canonical_role', 'mapping_source']
            df['canonical_role'] = mapping_results['canonical_role']

            # Canonical level + track
            df['level_normalised'] = df['job_level'].apply(normalise_level) if 'job_level' in df.columns else None
            df['level_canonical'] = df['level_normalised'].apply(bucket_level) if 'level_normalised' in df.columns else 'Unknown'
            # derive_track expects 'canonical_role' and 'level_canonical' columns
            df['level_track'] = df.apply(derive_track, axis=1)

            # Drop rows we can't map
            df = df[
                (df['canonical_role'] != 'Other') &
                df['canonical_role'].notna() &
                df['actual_base'].notna()
            ].copy()

            # Aggregate
            profile = (
                df.groupby(['canonical_role', 'level_track'])['actual_base']
                  .agg(['median', 'count'])
                  .reset_index()
            )
            profile = profile[profile['count'] >= MIN_CUSTOMER_ROWS_PER_BUCKET]

            customer_profile = {
                f"{row['canonical_role']}|{row['level_track']}": {
                    'median_usd': float(row['median']),
                    'n_customer_rows': int(row['count']),
                }
                for _, row in profile.iterrows()
            }
            profiles[customer_id] = customer_profile

        return profiles

    # ------------------------------------------------------------------
    # Design B calibration check
    # ------------------------------------------------------------------
    def _calibration_check(self, customer_id: str, canonical_role: str,
                           level_track: str) -> dict:
        """Compare customer pay vs training pay for this (role, track) bucket.

        Returns dict:
          'status': 'calibrated' | 'uncalibrated' | 'no_data' | 'no_training_data'
          'deviation_pct': float or None
          'customer_median': float or None
          'training_median': float or None
          'message': human-readable explanation
        """
        bucket_key = f"{canonical_role}|{level_track}"

        training_bucket = self.training_pay_profile.get(bucket_key)
        if training_bucket is None:
            return {
                'status': 'no_training_data',
                'deviation_pct': None,
                'customer_median': None,
                'training_median': None,
                'message': f"No training data for {canonical_role} at {level_track} track.",
            }

        customer_profile = self.customer_pay_profiles.get(customer_id, {})
        customer_bucket = customer_profile.get(bucket_key)

        if customer_bucket is None:
            # Customer has no historical hires in this bucket — can't calibrate,
            # but this isn't a failure. We just don't have evidence either way.
            return {
                'status': 'no_data',
                'deviation_pct': None,
                'customer_median': None,
                'training_median': training_bucket['median_usd'],
                'message': f"No historical hires at this customer for {canonical_role} ({level_track}).",
            }

        # Compare medians
        deviation = (customer_bucket['median_usd'] - training_bucket['median_usd']) / training_bucket['median_usd']

        if abs(deviation) <= PAY_DEVIATION_THRESHOLD:
            return {
                'status': 'calibrated',
                'deviation_pct': float(deviation * 100),
                'customer_median': customer_bucket['median_usd'],
                'training_median': training_bucket['median_usd'],
                'message': f"Customer pay for this role is within {PAY_DEVIATION_THRESHOLD*100:.0f}% of training median; prediction is reliable.",
            }
        else:
            direction = "above" if deviation > 0 else "below"
            return {
                'status': 'uncalibrated',
                'deviation_pct': float(deviation * 100),
                'customer_median': customer_bucket['median_usd'],
                'training_median': training_bucket['median_usd'],
                'message': (
                    f"This customer's typical pay for {canonical_role} ({level_track}) is "
                    f"{abs(deviation)*100:.0f}% {direction} our training data's median. "
                    f"Predictions for this role at this customer are not reliable."
                ),
            }

    # ------------------------------------------------------------------
    # Customer file loading
    # ------------------------------------------------------------------
    def _load_customer_files(self) -> dict:
        """Find files like data/docker.csv, data/vercel.csv, etc. Return dict by customer id."""
        out = {}
        if not CUSTOMER_DATA_DIR.exists():
            return out
        for csv_path in CUSTOMER_DATA_DIR.glob("*.csv"):
            customer_id = csv_path.stem.lower()
            df = pd.read_csv(csv_path)
            df['actual_start_date'] = pd.to_datetime(df['actual_start_date'], errors='coerce')
            out[customer_id] = df
        return out

    def available_customers(self) -> list[str]:
        return sorted(self.customer_data.keys())

    # ------------------------------------------------------------------
    # Canonicalisation of user query
    # ------------------------------------------------------------------
    def _canonicalise(self, raw_role: str, raw_level: str, raw_location: str,
                      hire_date: datetime) -> dict:
        """Map user inputs to canonical model features."""
        # Role: canonicalise via the taxonomy. The user's "raw_role" might be
        # a canonical role they picked from a dropdown, OR the customer's
        # internal role string (e.g., "Software Engineer (IC)" for Docker).
        # Either way, map_role_for_row handles it correctly.
        canonical_role, _ = map_role_for_row({'Job role': raw_role, 'Job title': None})
        canonical_function = FUNCTION_FOR_LEAF.get(canonical_role, 'Unknown')

        # Level
        level_normalised = normalise_level(raw_level)
        level_canonical = bucket_level(level_normalised)

        # Location
        country, metro, is_remote = map_location(raw_location)

        # Derive track from role + level (same as training)
        level_track = derive_track({
            'level_canonical': level_canonical,
            'canonical_role': canonical_role,
        })

        # Hire quarter
        hire_quarter_numeric = to_quarter_numeric(hire_date)

        return {
            'canonical_role': canonical_role,
            'canonical_function': canonical_function,
            'level_canonical': level_canonical,
            'level_track': level_track,
            'country': country,
            'metro': metro,
            'is_remote': is_remote,
            'hire_quarter_numeric': hire_quarter_numeric,
        }

    # ------------------------------------------------------------------
    # TTF lookup (for default hire date)
    # ------------------------------------------------------------------
    def recommended_hire_date(self, customer_id: str, raw_role: str) -> dict:
        """Return {'hire_date': iso_string, 'ttf_days': int, 'source': str}.

        Hierarchical fallback for TTF source:
        1. Customer's own avg TTF for this role (≥5 historical rows).
        2. Customer's overall avg TTF.
        3. Global default (45 days).
        """
        today = datetime.now().date()
        if customer_id not in self.customer_data:
            return {
                'hire_date': (today + timedelta(days=45)).isoformat(),
                'ttf_days': 45,
                'source': 'global default',
            }

        df = self.customer_data[customer_id]
        # Filter to role
        role_match = df[df['job_role'].astype(str).str.lower() == raw_role.lower()]
        role_match = role_match[role_match['time_to_fill'].notna()]
        if len(role_match) >= 5:
            ttf = int(role_match['time_to_fill'].median())
            return {
                'hire_date': (today + timedelta(days=ttf)).isoformat(),
                'ttf_days': ttf,
                'source': f"customer-specific avg for {raw_role}",
            }

        # Customer-wide fallback
        overall = df[df['time_to_fill'].notna()]
        if len(overall) >= 5:
            ttf = int(overall['time_to_fill'].median())
            return {
                'hire_date': (today + timedelta(days=ttf)).isoformat(),
                'ttf_days': ttf,
                'source': f"customer-wide avg ({customer_id})",
            }

        return {
            'hire_date': (today + timedelta(days=45)).isoformat(),
            'ttf_days': 45,
            'source': 'global default',
        }

    # ------------------------------------------------------------------
    # Customer band lookup
    # ------------------------------------------------------------------
    def _customer_band(self, customer_id: str, raw_role: str, raw_level: str,
                       raw_location: str) -> Optional[dict]:
        """Look up the customer's approved band for this combination.

        Returns {'low', 'mid', 'high', 'currency', 'n_rows'} or None.
        """
        if customer_id not in self.customer_data:
            return None

        df = self.customer_data[customer_id]
        # Match on (job_role, job_level, location)
        m = df[
            (df['job_role'].astype(str).str.lower() == raw_role.lower()) &
            (df['job_level'].astype(str).str.lower() == raw_level.lower()) &
            (df['location'].astype(str).str.lower() == raw_location.lower()) &
            df['base_low'].notna() & df['base_high'].notna()
        ]
        if len(m) == 0:
            return None

        # Customers should have one consistent band per combination; if multiple, take the median
        # Guard against NaN in the median computation (can happen if all values are NaN)
        low = m['base_low'].median()
        high = m['base_high'].median()
        mid = m['base_mid'].median() if 'base_mid' in m.columns else None

        return {
            'low': float(low) if pd.notna(low) else None,
            'mid': float(mid) if (mid is not None and pd.notna(mid)) else None,
            'high': float(high) if pd.notna(high) else None,
            'currency': m['currency'].mode().iloc[0] if not m['currency'].mode().empty else 'USD',
            'n_rows': len(m),
        }

    # ------------------------------------------------------------------
    # Recent hires lookup
    # ------------------------------------------------------------------
    def _recent_hires(self, customer_id: str, raw_role: str, raw_level: str,
                      raw_location: str, limit: int = 10) -> list:
        """Recent filled hires matching the query."""
        if customer_id not in self.customer_data:
            return []

        df = self.customer_data[customer_id]
        m = df[
            (df['job_role'].astype(str).str.lower() == raw_role.lower()) &
            (df['job_level'].astype(str).str.lower() == raw_level.lower()) &
            (df['location'].astype(str).str.lower() == raw_location.lower()) &
            df['actual_base'].notna() &
            df['actual_start_date'].notna()
        ].sort_values('actual_start_date', ascending=False).head(limit)

        return [
            {
                'role': r['job_role'],
                'level': r['job_level'],
                'location': r['location'],
                'actual_base': float(r['actual_base']),
                'currency': r['currency'] if 'currency' in r and pd.notna(r['currency']) else 'USD',
                'start_date': r['actual_start_date'].date().isoformat() if pd.notna(r['actual_start_date']) else None,
                'time_to_fill': int(r['time_to_fill']) if pd.notna(r['time_to_fill']) else None,
            }
            for _, r in m.iterrows()
        ]

    # ------------------------------------------------------------------
    # Calibration caveat
    # ------------------------------------------------------------------
    def _calibration_note(self, customer_id: str) -> dict:
        """Return per-customer calibration caveat for the UI.

        Looks up the customer's anonymised training ID via CUSTOMER_ID_ALIASES,
        then fetches the per-customer test coverage from Section 14f.
        """
        # Translate the file-based customer ID to the anonymised training ID
        training_id = CUSTOMER_ID_ALIASES.get(customer_id.lower())

        if training_id is None:
            return {
                'confidence_tier': 'unknown',
                'coverage_pct': None,
                'note': "This customer is not yet linked to the model's calibration data; predictions should be treated as directional until calibration is established.",
            }

        per_cust = self.calibration['per_customer_test_coverage']
        coverage = per_cust.get(training_id)

        if coverage is None:
            return {
                'confidence_tier': 'unknown',
                'coverage_pct': None,
                'note': "This customer's calibration data is not available; predictions should be treated as directional.",
            }

        if coverage >= 0.50:
            tier = 'high'
            note = f"For this customer, the model is well-calibrated to historical hires (test coverage {coverage*100:.0f}%)."
        elif coverage >= 0.40:
            tier = 'medium'
            note = f"For this customer, the model is moderately calibrated (test coverage {coverage*100:.0f}%); treat ranges as guidance rather than authoritative."
        else:
            tier = 'low'
            note = f"For this customer, the model has lower coverage on historical hires (test coverage {coverage*100:.0f}%); predictions are directional only."

        return {
            'confidence_tier': tier,
            'coverage_pct': coverage,
            'note': note,
        }

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def predict(self, customer_id: str, raw_role: str, raw_level: str,
                raw_location: str, hire_date: datetime) -> dict:
        """Top-level entry point. Returns a structured response for the UI."""
        # 1. Canonicalise
        canonical = self._canonicalise(raw_role, raw_level, raw_location, hire_date)

        # 2. Design B calibration check — compare customer pay vs training pay
        #    for this (role, track) bucket. Abstain if uncalibrated.
        cal_check = self._calibration_check(
            customer_id=customer_id.lower(),
            canonical_role=canonical['canonical_role'],
            level_track=canonical['level_track'],
        )

        # 3. Engine prediction OR abstention from calibration check
        if cal_check['status'] == 'uncalibrated':
            # Abstain: customer's pay structure for this role differs from training
            engine_result = {
                'p25': None, 'p75': None,
                'support_n': 0, 'fallback_level': 'abstain',
                'confidence': 'low', 'abstain_reason': cal_check['message'],
            }
        else:
            pred = self.engine.predict(canonical)
            engine_result = {
                'p25': pred.p25, 'p75': pred.p75,
                'support_n': pred.support_n,
                'fallback_level': pred.fallback_level,
                'confidence': pred.confidence,
                'abstain_reason': pred.abstain_reason,
            }

        # 4. Customer band
        band = self._customer_band(customer_id, raw_role, raw_level, raw_location)

        # 5. Recent hires
        recent = self._recent_hires(customer_id, raw_role, raw_level, raw_location)

        # 6. Calibration caveat (about overall model trust for this customer)
        cal = self._calibration_note(customer_id)

        # 7. Comparison: band vs market
        comparison = None
        if band and engine_result['p25'] is not None:
            band_mid = (band['low'] + band['high']) / 2
            market_mid = (engine_result['p25'] + engine_result['p75']) / 2
            gap_pct = (band_mid - market_mid) / market_mid * 100
            if abs(gap_pct) < 3:
                signal = 'in_line'
            elif gap_pct > 0:
                signal = 'above_market'
            else:
                signal = 'below_market'
            comparison = {
                'band_vs_market_pct': float(gap_pct),
                'signal': signal,
            }

        # Build the response, then scrub NaN values for JSON compliance
        response = {
            'query': {
                'customer_id': customer_id,
                'raw_role': raw_role,
                'raw_level': raw_level,
                'raw_location': raw_location,
                'hire_date': hire_date.date().isoformat() if hasattr(hire_date, 'date') else str(hire_date),
                'hire_quarter': quarter_label(canonical['hire_quarter_numeric']),
                'canonical': canonical,
            },
            'market': {
                'p25': engine_result['p25'],
                'p75': engine_result['p75'],
                'currency': 'USD',
                'support_n': engine_result['support_n'],
                'fallback_level': engine_result['fallback_level'],
                'confidence': engine_result['confidence'],
                'abstain_reason': engine_result['abstain_reason'],
            },
            'pay_calibration': {
                'status': cal_check['status'],
                'deviation_pct': cal_check['deviation_pct'],
                'customer_median': cal_check['customer_median'],
                'training_median': cal_check['training_median'],
                'message': cal_check['message'],
            },
            'company_band': band,
            'comparison': comparison,
            'recent_hires': recent,
            'calibration': cal,
        }
        return clean_nan(response)


# Singleton
_orch: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _orch
    if _orch is None:
        _orch = Orchestrator()
    return _orch
