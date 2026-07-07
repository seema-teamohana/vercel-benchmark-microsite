"""
Salary prediction engine for the public microsite.

Loads 4 LightGBM quantile models at startup (p25, p50, p75, p90).
Exposes a single predict() function that takes a canonicalised query and
returns all four predictions, plus support metadata.

Quantile-monotonicity guard: independently-trained quantile models can
occasionally produce crossed predictions (e.g. p25 > p50). We sort the
4 outputs at query time to ensure p25 <= p50 <= p75 <= p90 always.

Standard-level aggregation: the public UI shows only standard levels
(IC1-IC7, M1-M8, Director, Executive). Behind the scenes, the training data
uses many company-specific codes (P3, L4, SEIC5, EL5, G6, ...). The engine
maps the user's standard-level input to the most-common raw code for that
(role, country) combo, and aggregates support counts across all mapped codes.
"""
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional, NamedTuple

ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts"


class Prediction(NamedTuple):
    p25: Optional[float]
    p50: Optional[float]
    p75: Optional[float]
    p90: Optional[float]
    support_n: int
    fallback_level: str
    confidence: str
    abstain_reason: Optional[str]
    raw_level_used: Optional[str]  # which raw code we mapped the standard level to


WRAPPER_LEVELS = [
    ('role+level+country+metro', ['canonical_role', 'level_canonical', 'country', 'metro']),
    ('role+level+country',       ['canonical_role', 'level_canonical', 'country']),
    ('role+level',               ['canonical_role', 'level_canonical']),
    ('role+country',             ['canonical_role', 'country']),
    ('role',                     ['canonical_role']),
]

MIN_CELL_SIZE = 5
HIGH_CONF_MIN = 20


class Engine:
    def __init__(self, artifacts_dir: Path = ARTIFACTS_DIR):
        self.m_p25 = joblib.load(artifacts_dir / "lgb_p25.joblib")
        self.m_p50 = joblib.load(artifacts_dir / "lgb_p50.joblib")
        self.m_p75 = joblib.load(artifacts_dir / "lgb_p75.joblib")
        self.m_p90 = joblib.load(artifacts_dir / "lgb_p90.joblib")
        with open(artifacts_dir / "categorical_schemas.json") as f:
            self.categorical_schemas = json.load(f)
        with open(artifacts_dir / "support_index.json") as f:
            self.support_index = json.load(f)
        with open(artifacts_dir / "reference.json") as f:
            self.reference = json.load(f)
        # Standard-level mapping: raw code -> standard bucket (IC1-IC7, M1-M8, etc.)
        with open(artifacts_dir / "level_standardization.json") as f:
            self.level_std_map = json.load(f)
        # (role|country|standard_level) -> {raw_level, n}
        # Used to resolve a user's standard-level choice into a specific raw code
        # for the model.
        with open(artifacts_dir / "standard_level_to_raw.json") as f:
            self.std_to_raw = json.load(f)
        # Precompute reverse mapping: standard_level -> [list of raw codes]
        self.std_to_raw_list = {}
        for raw, std in self.level_std_map.items():
            self.std_to_raw_list.setdefault(std, []).append(raw)
        # Precompute metro distribution per (role, country) from the training data
        # (via benchmark.csv). Used to average predictions across metros when
        # the user hasn't specified one, so the country-level range reflects the
        # actual spread of metros rather than collapsing to a single niche bucket.
        self._metros_by_role_country = self._build_metro_distribution(artifacts_dir)

    def _build_metro_distribution(self, artifacts_dir: Path) -> dict:
        """Build {(role, country): [(metro, is_remote, count), ...]} lookup.

        Used at prediction time to compute a metro-weighted country prediction.
        """
        bench = pd.read_csv(artifacts_dir / "benchmark.csv")
        grouped = bench.groupby(
            ['canonical_role', 'country', 'metro', 'is_remote']
        ).size().reset_index(name='n')
        result = {}
        for _, row in grouped.iterrows():
            key = (row['canonical_role'], row['country'])
            metro = row['metro']
            # Guard against NaN metro
            if pd.isna(metro):
                metro = '(no metro)'
            result.setdefault(key, []).append(
                (metro, bool(row['is_remote']), int(row['n']))
            )
        return result

    def _support_count(self, level_name: str, key_values: list) -> int:
        level_info = self.support_index.get(level_name, {})
        counts = level_info.get('_counts', {})
        key_str = '|'.join(str(v) for v in key_values)
        return counts.get(key_str, 0)

    def _support_count_aggregated(self, role: str, country: str,
                                   standard_level: str, metro=None) -> int:
        """Sum support across all raw levels that map to the given standard level.

        E.g. for (SWE, US, IC4), sum counts for L4, IC4, P4, SEIC4, G4, EL3, DEIC4.
        This gives a true count of comparable hires the user can see.
        """
        raw_codes = self.std_to_raw_list.get(standard_level, [])
        total = 0
        for raw in raw_codes:
            if metro:
                total += self._support_count(
                    'role+level+country+metro', [role, raw, country, metro]
                )
            else:
                total += self._support_count(
                    'role+level+country', [role, raw, country]
                )
        return total

    def _resolve_raw_level(self, role: str, country: str,
                            standard_level: str) -> Optional[str]:
        """For a user's standard-level choice, find the raw code with best support
        in this specific (role, country) context. Falls back to any code if
        role+country lookup fails.
        """
        # Try exact role+country match first
        key = f"{role}|{country}|{standard_level}"
        entry = self.std_to_raw.get(key)
        if entry:
            return entry['raw_level']
        # Fallback: try any country for the same role
        for other_key, other_entry in self.std_to_raw.items():
            parts = other_key.split('|')
            if parts[0] == role and parts[2] == standard_level:
                return other_entry['raw_level']
        # Last resort: use the standard level itself as-is (works for IC/M levels
        # since IC4, M3, etc. are also valid raw codes)
        return standard_level

    def _find_supported_cell(self, query: dict) -> tuple:
        for level_name, cols in WRAPPER_LEVELS:
            key_values = []
            skip = False
            for col in cols:
                v = query.get(col)
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    skip = True
                    break
                key_values.append(v)
            if skip:
                continue
            n = self._support_count(level_name, key_values)
            if n >= MIN_CELL_SIZE:
                return (n, level_name)
        return (0, 'abstain')

    def _encode(self, query: dict) -> pd.DataFrame:
        feature_cols = [
            'canonical_role', 'canonical_function', 'level_canonical', 'level_track',
            'country', 'metro', 'is_remote', 'hire_quarter_numeric',
        ]
        cat_cols = ['canonical_role', 'canonical_function', 'level_canonical', 'level_track',
                    'country', 'metro']
        row = {col: query.get(col) for col in feature_cols}
        df = pd.DataFrame([row])
        for col in cat_cols:
            cats = self.categorical_schemas.get(col, [])
            df[col] = pd.Categorical(df[col], categories=cats)
        return df

    def predict(self, query: dict) -> Prediction:
        if not query.get('canonical_role'):
            return Prediction(None, None, None, None, 0, 'abstain', 'low',
                              'No canonical role specified', None)
        if query.get('canonical_role') == 'Other':
            return Prediction(None, None, None, None, 0, 'abstain', 'low',
                              "The 'Other' role bucket is too heterogeneous to predict", None)
        if not query.get('country') or query.get('country') == 'Other / Unknown':
            return Prediction(None, None, None, None, 0, 'abstain', 'low',
                              'No country specified', None)

        # The query comes in with a *standard* level (IC1-IC7, M1-M8, Director,
        # Executive) — resolve to the raw code the model was trained on.
        standard_level = query.get('level_canonical')
        role = query.get('canonical_role')
        country = query.get('country')
        raw_level = self._resolve_raw_level(role, country, standard_level)

        # Use aggregated support (across all raw codes mapping to this standard level)
        aggregated_support = self._support_count_aggregated(
            role, country, standard_level
        )

        # Now build the query with the raw level for the model
        query_for_model = {**query, 'level_canonical': raw_level}

        # If aggregated support is below threshold, abstain immediately.
        # The frontend restricts dropdowns to available_combinations, so this
        # only fires when the API is called directly with an unsupported combo.
        if aggregated_support < MIN_CELL_SIZE:
            return Prediction(
                None, None, None, None,
                aggregated_support,
                'abstain',
                'low',
                f'Not enough comparable data for {role} at {standard_level} in {country} '
                f'(only {aggregated_support} rows; need >= {MIN_CELL_SIZE}).',
                raw_level,
            )

        support_n = aggregated_support
        level_name = 'role+level+country'
        confidence = 'high' if support_n >= HIGH_CONF_MIN else 'medium'

        # Hybrid prediction approach:
        # 1. Use EMPIRICAL quantiles from training data for this role+country+standard_level.
        #    These properly represent the actual dispersion across metros / remote /
        #    hire quarters within the cell.
        # 2. Adjust for temporal drift via the model: compute the model's p50 for
        #    the requested hire date vs the training-median hire date, and scale
        #    the empirical quantiles by that ratio.
        #
        # This gives a properly-wide range that reflects real salary variance,
        # while still respecting temporal salary drift the model has learned.
        p25_pred, p50_pred, p75_pred, p90_pred = self._predict_hybrid(
            role, country, standard_level, query
        )

        # Sort guard: ensure p25 <= p50 <= p75 <= p90
        quantiles_sorted = sorted([p25_pred, p50_pred, p75_pred, p90_pred])
        p25_usd, p50_usd, p75_usd, p90_usd = quantiles_sorted

        return Prediction(
            p25=p25_usd, p50=p50_usd, p75=p75_usd, p90=p90_usd,
            support_n=support_n,
            fallback_level=level_name,
            confidence=confidence,
            abstain_reason=None,
            raw_level_used=raw_level,
        )

    def _predict_hybrid(self, role: str, country: str, standard_level: str,
                         query: dict) -> tuple:
        """Empirical quantiles adjusted by model's temporal-drift signal.

        Returns (p25, p50, p75, p90) in USD.
        """
        # Get empirical quantiles from training data for this cell
        raw_levels = self.std_to_raw_list.get(standard_level, [standard_level])
        cell_rows = self._benchmark_lookup(role, country, raw_levels)

        if len(cell_rows) < MIN_CELL_SIZE:
            # Insufficient data — shouldn't happen since we already gated on
            # aggregated_support, but fall back to model prediction.
            X = self._encode(query)
            return (
                float(np.exp(self.m_p25.predict(X)[0])),
                float(np.exp(self.m_p50.predict(X)[0])),
                float(np.exp(self.m_p75.predict(X)[0])),
                float(np.exp(self.m_p90.predict(X)[0])),
            )

        emp_p25 = float(cell_rows['Actual salary annual_usd'].quantile(0.25))
        emp_p50 = float(cell_rows['Actual salary annual_usd'].quantile(0.50))
        emp_p75 = float(cell_rows['Actual salary annual_usd'].quantile(0.75))
        emp_p90 = float(cell_rows['Actual salary annual_usd'].quantile(0.90))

        # Temporal drift adjustment via the model.
        # Compare model p50 for the requested hire quarter vs the median hire
        # quarter in the training data. If salaries have gone up 4% between then
        # and the requested date, scale empirical quantiles by 1.04.
        training_median_quarter = float(cell_rows['hire_quarter_numeric'].median())
        requested_quarter = query.get('hire_quarter_numeric')
        if requested_quarter is None or pd.isna(requested_quarter):
            drift_ratio = 1.0
        else:
            drift_ratio = self._compute_drift_ratio(
                role, country, standard_level, query,
                training_median_quarter, float(requested_quarter),
            )

        return (
            emp_p25 * drift_ratio,
            emp_p50 * drift_ratio,
            emp_p75 * drift_ratio,
            emp_p90 * drift_ratio,
        )

    def _compute_drift_ratio(self, role: str, country: str, standard_level: str,
                             query: dict,
                             training_median_quarter: float,
                             requested_quarter: float) -> float:
        """Ratio between model's p50 at requested hire quarter vs training median.

        Uses the most-common metro for this cell (to make the drift signal stable)
        and the dominant raw level code.
        """
        raw_level = self._resolve_raw_level(role, country, standard_level)
        # Pick a representative metro (most common) for stable drift estimation
        metros_and_weights = self._metros_by_role_country.get((role, country), [])
        if metros_and_weights:
            # Sort by count desc, pick the top
            metros_and_weights_sorted = sorted(
                metros_and_weights, key=lambda t: -t[2]
            )
            rep_metro, rep_remote, _ = metros_and_weights_sorted[0]
        else:
            rep_metro = query.get('metro') or '(no metro)'
            rep_remote = bool(query.get('is_remote', False))

        base_query = {
            'canonical_role': role,
            'canonical_function': query.get('canonical_function'),
            'level_canonical': raw_level,
            'level_track': query.get('level_track'),
            'country': country,
            'metro': rep_metro,
            'is_remote': rep_remote,
        }

        # Predict at training median
        q_train = {**base_query, 'hire_quarter_numeric': training_median_quarter}
        X_train = self._encode(q_train)
        p50_train = float(np.exp(self.m_p50.predict(X_train)[0]))

        # Predict at requested date
        q_req = {**base_query, 'hire_quarter_numeric': requested_quarter}
        X_req = self._encode(q_req)
        p50_req = float(np.exp(self.m_p50.predict(X_req)[0]))

        if p50_train <= 0:
            return 1.0
        return p50_req / p50_train

    def _benchmark_lookup(self, role: str, country: str, raw_levels: list):
        """Return rows in benchmark.csv matching (role, country, any of raw_levels)."""
        # We use the benchmark stored on the orchestrator side. But engine also
        # needs it — lazy-load from disk on first use.
        if not hasattr(self, '_benchmark_df'):
            self._benchmark_df = pd.read_csv(ARTIFACTS_DIR / 'benchmark.csv')
        df = self._benchmark_df
        return df[
            (df['canonical_role'] == role) &
            (df['country'] == country) &
            (df['level_canonical'].isin(raw_levels))
        ]


_engine: Optional[Engine] = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine
