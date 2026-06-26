"""
The salary prediction engine.

Pure prediction logic. Loads artifacts at startup, exposes a single predict()
function. No I/O concerns, no UI concerns. Imported by the orchestrator.
"""
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional, NamedTuple

ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts"


class Prediction(NamedTuple):
    p25: Optional[float]            # USD, or None if abstaining
    p75: Optional[float]            # USD, or None if abstaining
    support_n: int                  # number of training rows in the matched cell
    fallback_level: str             # one of WRAPPER_LEVELS or 'abstain'
    confidence: str                 # 'high' (>=20), 'medium' (5-19), 'low' (none)
    abstain_reason: Optional[str]   # filled if predicting refused; None otherwise


# Cell key fallback chain (same as Section 13d / 13h of the notebook)
WRAPPER_LEVELS = [
    ('role+level+country+metro', ['canonical_role', 'level_canonical', 'country', 'metro']),
    ('role+level+country',       ['canonical_role', 'level_canonical', 'country']),
    ('role+level',               ['canonical_role', 'level_canonical']),
    ('role+country',             ['canonical_role', 'country']),
    ('role',                     ['canonical_role']),
]

MIN_CELL_SIZE = 5            # abstain below this
HIGH_CONF_MIN = 20           # need at least this many for "high" confidence


class Engine:
    """Holds the loaded artifacts and exposes prediction methods.

    Instantiated once at backend startup; reused across all requests.
    """

    def __init__(self, artifacts_dir: Path = ARTIFACTS_DIR):
        # Load models
        self.m_lo = joblib.load(artifacts_dir / "lgb_p25.joblib")
        self.m_hi = joblib.load(artifacts_dir / "lgb_p75.joblib")

        # Load categorical schemas — needed to encode queries identically to training
        with open(artifacts_dir / "categorical_schemas.json") as f:
            self.categorical_schemas = json.load(f)

        # Load support index
        with open(artifacts_dir / "support_index.json") as f:
            self.support_index = json.load(f)

        # Reference data (for UI dropdowns and validation)
        with open(artifacts_dir / "reference.json") as f:
            self.reference = json.load(f)

        # Calibration metadata
        with open(artifacts_dir / "calibration.json") as f:
            self.calibration = json.load(f)

    # ------------------------------------------------------------------
    # Support lookup (drives abstention)
    # ------------------------------------------------------------------
    def _support_count(self, level_name: str, key_values: list) -> int:
        """Look up cell support count for a given fallback level."""
        level_info = self.support_index.get(level_name, {})
        counts = level_info.get('_counts', {})
        key_str = '|'.join(str(v) for v in key_values)
        return counts.get(key_str, 0)

    def _find_supported_cell(self, query: dict) -> tuple:
        """Walk the fallback chain. Return (support_n, level_name).
        If no level has >=MIN_CELL_SIZE rows, returns (0, 'abstain')."""
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

    # ------------------------------------------------------------------
    # Feature encoding for the model
    # ------------------------------------------------------------------
    def _encode(self, query: dict) -> pd.DataFrame:
        """Build a single-row DataFrame matching the training feature schema."""
        # Required features in the same order as training
        feature_cols = [
            'canonical_role', 'canonical_function', 'level_canonical', 'level_track',
            'country', 'metro', 'is_remote', 'hire_quarter_numeric',
        ]
        cat_cols = ['canonical_role', 'canonical_function', 'level_canonical', 'level_track',
                    'country', 'metro']

        row = {col: query.get(col) for col in feature_cols}
        df = pd.DataFrame([row])
        # Apply the exact category schema used at training time
        for col in cat_cols:
            cats = self.categorical_schemas.get(col, [])
            df[col] = pd.Categorical(df[col], categories=cats)
        return df

    # ------------------------------------------------------------------
    # Public predict
    # ------------------------------------------------------------------
    def predict(self, query: dict) -> Prediction:
        """Predict p25/p75 for a canonicalised query.

        Query must have these keys (use canonical names, not raw user input —
        the orchestrator handles canonicalisation):
          canonical_role, canonical_function, level_canonical, level_track,
          country, metro (or None), is_remote (bool), hire_quarter_numeric (int)

        Returns a Prediction. If the cell is too sparse for any fallback level,
        p25/p75 are None and abstain_reason is filled.
        """
        # Validate required inputs
        if not query.get('canonical_role'):
            return Prediction(None, None, 0, 'abstain', 'low',
                              'No canonical role specified')

        if query.get('canonical_role') == 'Other':
            return Prediction(None, None, 0, 'abstain', 'low',
                              "The 'Other' role bucket is too heterogeneous to predict")

        if not query.get('country') or query.get('country') == 'Other / Unknown':
            return Prediction(None, None, 0, 'abstain', 'low',
                              'No country specified')

        # Check support
        support_n, level_name = self._find_supported_cell(query)
        if level_name == 'abstain':
            return Prediction(None, None, support_n, 'abstain', 'low',
                              'Not enough comparable historical data')

        confidence = 'high' if support_n >= HIGH_CONF_MIN else 'medium'

        # Encode and predict
        X = self._encode(query)
        log_p25 = float(self.m_lo.predict(X)[0])
        log_p75 = float(self.m_hi.predict(X)[0])
        p25_usd = float(np.exp(log_p25))
        p75_usd = float(np.exp(log_p75))

        return Prediction(
            p25=p25_usd,
            p75=p75_usd,
            support_n=support_n,
            fallback_level=level_name,
            confidence=confidence,
            abstain_reason=None,
        )


# Singleton — loaded once when this module imports
_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """Lazy singleton. Backend startup calls this once."""
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine
