"""
Lightweight orchestrator for the public microsite.

Responsibilities:
  1. Canonicalise raw user input (role, level, location) into the model's
     internal feature space.
  2. Call the engine to get quantile predictions.
  3. Compute the offer-count distribution from the training data — for the
     queried role/level/country, how many historical hires fall in each
     predicted range (below p25, p25-p50, p50-p75, p75-p90, above p90).
  4. Return a JSON-clean response.

No customer-specific logic. No Design B. No band comparison. No recent hires.
Standard-level aggregation: user input uses standard levels (IC1-IC7, M1-M8,
Director, Executive). Behind the scenes the training data has many raw codes
(P3, L4, SEIC5, ...). The offer distribution aggregates across all raw codes
that map to the same standard bucket.
"""
import json
import math
from pathlib import Path
from datetime import datetime
import sys

# Make the taxonomy module (in the backend root) importable
sys.path.insert(0, str(Path(__file__).parent.parent))
from taxonomy import (
    map_role_for_row, normalise_level, bucket_level, derive_track,
    map_location, to_quarter_numeric, quarter_label, REFERENCE_DATE,
    FUNCTION_FOR_LEAF,
)
from app.engine import get_engine

import pandas as pd


# Time window for the offer-count distribution. Last 3 years from REFERENCE_DATE.
OFFER_DIST_YEARS_BACK = 3


def clean_nan(obj):
    """Recursively replace NaN/Inf floats with None for JSON compliance."""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj


class Orchestrator:
    def __init__(self):
        self.engine = get_engine()
        # Load benchmark CSV — the training data, used for offer-count distribution
        self.benchmark = pd.read_csv(
            Path(__file__).parent.parent / "artifacts" / "benchmark.csv"
        )
        self.benchmark['Actual start date'] = pd.to_datetime(
            self.benchmark['Actual start date'], errors='coerce'
        )
        # Load the standard-level mapping (raw -> standard)
        with open(Path(__file__).parent.parent / "artifacts" / "level_standardization.json") as f:
            self.level_std_map = json.load(f)
        # Precompute reverse mapping: standard -> [raw levels]
        self.std_to_raw_list = {}
        for raw, std in self.level_std_map.items():
            self.std_to_raw_list.setdefault(std, []).append(raw)

    # ------------------------------------------------------------------
    # Canonicalisation — map raw user input to model feature space
    # ------------------------------------------------------------------
    def _canonicalise(self, raw_role: str, raw_level: str,
                      raw_location: str, hire_date) -> dict:
        """Convert user input into the model's feature schema.

        Note: level here is expected to already be a *standard* level
        (IC1-IC7, M1-M8, Director, Executive) — the frontend restricts the
        dropdown to those. If a raw code sneaks through, it's passed through
        to the model as-is.
        """
        canonical_role = raw_role
        canonical_function = FUNCTION_FOR_LEAF.get(canonical_role, 'Other')

        # For a standard level, pass it directly; the engine will handle
        # resolving to a specific raw code for the model at prediction time.
        # If it's actually a raw code, we still normalise+bucket for legacy safety.
        if raw_level in {'IC1', 'IC2', 'IC3', 'IC4', 'IC5', 'IC6', 'IC7',
                         'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8',
                         'Director', 'Executive'}:
            level_canonical = raw_level
        else:
            level_normalised = normalise_level(raw_level)
            level_canonical = bucket_level(level_normalised)

        level_track = derive_track({
            'canonical_role': canonical_role,
            'level_canonical': level_canonical,
        })

        # Location
        country, metro, is_remote = map_location(raw_location)

        # Hire quarter
        hire_quarter_numeric = to_quarter_numeric(hire_date)

        return {
            'canonical_role': canonical_role,
            'canonical_function': canonical_function,
            'level_canonical': level_canonical,
            'level_track': level_track,
            'country': country,
            'metro': metro,
            'is_remote': bool(is_remote),
            'hire_quarter_numeric': hire_quarter_numeric,
        }

    # ------------------------------------------------------------------
    # Offer count distribution — how do historical hires distribute
    # across the predicted ranges?
    # ------------------------------------------------------------------
    def _offer_distribution(self, canonical: dict, p25: float, p50: float,
                            p75: float, p90: float) -> dict:
        """Filter benchmark to cell + count by predicted range.

        Aggregates across all raw level codes that map to the same standard level.
        E.g. if user picks IC4, includes rows labeled IC4, P4, L4, SEIC4, G4,
        EL3, DEIC4 (all of which standardize to IC4).

        Restricts to the last 3 years of data. Uses exact-match role+country
        (no fallback chain) — the user sees a count of comparable hires that
        genuinely match their query.
        """
        df = self.benchmark
        # Restrict to last 3 years of data
        cutoff = REFERENCE_DATE - pd.DateOffset(years=OFFER_DIST_YEARS_BACK)
        df = df[df['Actual start date'] >= cutoff]

        # Filter to role + country
        df = df[
            (df['canonical_role'] == canonical['canonical_role']) &
            (df['country'] == canonical['country'])
        ]

        # Aggregate across all raw levels that map to the user's standard level
        std_level = canonical['level_canonical']
        raw_levels = self.std_to_raw_list.get(std_level, [std_level])
        df_with_level = df[df['level_canonical'].isin(raw_levels)]

        # Softer fallback: if aggregation still misses, fall back to role+country
        if len(df_with_level) >= 5:
            df = df_with_level
            match_level = 'role+level+country'
        else:
            match_level = 'role+country'

        actuals = df['Actual salary annual_usd'].dropna()
        n_total = len(actuals)

        if n_total == 0:
            return {
                'n_total': 0,
                'match_level': 'no_match',
                'time_window_years': OFFER_DIST_YEARS_BACK,
                'ranges': [],
            }

        # Count in each range
        ranges = [
            ('Below p25',  actuals < p25),
            ('p25 – p50',  (actuals >= p25) & (actuals < p50)),
            ('p50 – p75',  (actuals >= p50) & (actuals < p75)),
            ('p75 – p90',  (actuals >= p75) & (actuals < p90)),
            ('Above p90',  actuals >= p90),
        ]
        range_dicts = [
            {
                'label': label,
                'n': int(mask.sum()),
                'pct': float(mask.sum() / n_total * 100),
            }
            for label, mask in ranges
        ]

        return {
            'n_total': int(n_total),
            'match_level': match_level,
            'time_window_years': OFFER_DIST_YEARS_BACK,
            'ranges': range_dicts,
        }

    # ------------------------------------------------------------------
    # Top-level predict
    # ------------------------------------------------------------------
    def predict(self, raw_role: str, raw_level: str, raw_location: str,
                hire_date: datetime) -> dict:
        """Top-level entry point. Returns a JSON-clean structured response."""
        canonical = self._canonicalise(raw_role, raw_level, raw_location, hire_date)
        pred = self.engine.predict(canonical)

        # Build the offer distribution only if we got a prediction
        if pred.p25 is not None:
            offer_dist = self._offer_distribution(
                canonical, pred.p25, pred.p50, pred.p75, pred.p90
            )
        else:
            offer_dist = {
                'n_total': 0,
                'match_level': 'no_match',
                'time_window_years': OFFER_DIST_YEARS_BACK,
                'ranges': [],
            }

        response = {
            'query': {
                'raw_role': raw_role,
                'raw_level': raw_level,
                'raw_location': raw_location,
                'hire_date': hire_date.date().isoformat() if hasattr(hire_date, 'date') else str(hire_date),
                'hire_quarter': quarter_label(canonical['hire_quarter_numeric']),
                'canonical': canonical,
            },
            'market': {
                'p25': pred.p25,
                'p50': pred.p50,
                'p75': pred.p75,
                'p90': pred.p90,
                'currency': 'USD',
                'support_n': pred.support_n,
                'fallback_level': pred.fallback_level,
                'confidence': pred.confidence,
                'abstain_reason': pred.abstain_reason,
                'raw_level_used': pred.raw_level_used,
            },
            'offer_distribution': offer_dist,
        }
        return clean_nan(response)


# Singleton
_orch = None


def get_orchestrator() -> Orchestrator:
    global _orch
    if _orch is None:
        _orch = Orchestrator()
    return _orch
