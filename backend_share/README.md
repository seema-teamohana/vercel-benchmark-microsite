# TeamOhana Public Salary Benchmark Backend

FastAPI service powering the public salary benchmark microsite. No authentication, rate-limited to 10 requests/minute per IP.

## Project structure

```
backend/
├── app/
│   ├── main.py           — FastAPI HTTP layer (3 endpoints)
│   ├── orchestrator.py   — Canonicalisation + offer distribution
│   └── engine.py         — Quantile prediction + standard-level aggregation
├── taxonomy.py           — Canonical taxonomy mappings (role/level/location normalization)
├── artifacts/            — Trained model + reference data
│   ├── lgb_p25.joblib          — Quantile regression models (LightGBM)
│   ├── lgb_p50.joblib
│   ├── lgb_p75.joblib
│   ├── lgb_p90.joblib
│   ├── categorical_schemas.json — Model feature schema
│   ├── support_index.json       — Row counts per (role, level, country[, metro]) cell
│   ├── reference.json           — All roles/levels/countries in training
│   ├── available_combinations.json — What the UI should show (>= 5 rows per cell)
│   ├── level_standardization.json  — Raw level code → standard level (IC1-IC7, M1-M8, etc.)
│   ├── standard_level_to_raw.json  — Reverse lookup for prediction
│   └── benchmark.csv            — Training data (used for offer distribution counts)
├── requirements.txt
└── render.yaml           — Render deployment config
```

## Endpoints

- `GET /healthz` — health check, no rate limit
- `GET /reference` — dropdown options for the public microsite, with cascading filter data
- `POST /predict` — main prediction endpoint

### Reference response shape

```json
{
  "roles": ["Software Engineering", "Product Management", ...],
  "countries": ["US", "UK", "Canada", ...],
  "available_combinations": {
    "Software Engineering": {
      "US": {"IC1": 71, "IC2": 201, "IC3": 312, "IC4": 515, "IC5": 297, ...},
      "UK": {"IC3": 21, "IC4": 48, ...}
    },
    ...
  }
}
```

The frontend uses `available_combinations` to filter dropdowns: once a user picks a role, only countries present under that role appear. Once they pick a country, only levels available for that role+country appear.

### Predict request shape

```json
POST /predict
{
  "role": "Software Engineering",
  "level": "IC4",
  "location": "US",
  "hire_date": "2026-08-30"
}
```

### Predict response shape

```json
{
  "query": {...},
  "market": {
    "p25": 217291,
    "p50": 220298,
    "p75": 225578,
    "p90": 228543,
    "currency": "USD",
    "support_n": 515,
    "confidence": "high",
    "raw_level_used": "L4",
    "abstain_reason": null
  },
  "offer_distribution": {
    "n_total": 515,
    "match_level": "role+level+country",
    "time_window_years": 3,
    "ranges": [
      {"label": "Below p25", "n": 129, "pct": 25.0},
      {"label": "p25 – p50", "n": 128, "pct": 24.8},
      {"label": "p50 – p75", "n": 129, "pct": 25.0},
      {"label": "p75 – p90", "n": 76, "pct": 14.8},
      {"label": "Above p90", "n": 53, "pct": 10.3}
    ]
  }
}
```

Confidence levels:
- `high` — >= 20 comparable rows in training
- `medium` — 5–19 rows
- `low` — abstained (< 5 rows); p25-p90 will be null

## Local setup

```bash
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload --port 8000
```

Interactive docs at http://localhost:8000/docs

## Deployment

Push to a GitHub repo, then on Render: New > Web Service > pick the repo. The `render.yaml` config will be used automatically.

Rate limit is set via slowapi at 10 requests/minute per IP. For higher traffic, upgrade Render plan and raise the limit in `main.py`.
