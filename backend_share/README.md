# TeamOhana Salary Benchmark Backend

FastAPI service that serves salary predictions and customer benchmarks.

## Project structure

```
backend/
├── app/
│   ├── main.py           - FastAPI HTTP layer
│   ├── orchestrator.py   - Query routing + canonicalisation + customer data lookup
│   ├── engine.py         - Pure prediction engine (loads model + predicts)
├── taxonomy.py           - Canonical taxonomy mappings (shared by training + serving)
├── artifacts/            - Trained model + reference data (produced by train_and_save.py)
│   ├── lgb_p25.joblib
│   ├── lgb_p75.joblib
│   ├── categorical_schemas.json
│   ├── support_index.json
│   ├── reference.json
│   ├── calibration.json
│   └── benchmark.csv
├── data/                 - Per-customer files (one CSV per customer)
│   └── docker.csv
├── train_and_save.py     - One-off script: train model and save artifacts
├── requirements.txt
└── render.yaml           - Render deployment config
```

## Local setup

```bash
pip install -r requirements.txt

# Train and save artifacts (only needed once, or when training data changes)
python train_and_save.py

# Run the API server
uvicorn app.main:app --reload
```

The API is then available at http://localhost:8000 with interactive docs at /docs.

## Endpoints

- `GET /healthz` - health check
- `GET /customers` - list of available customer IDs
- `GET /reference` - canonical roles/levels/countries for UI dropdowns
- `GET /recommend-date?customer_id=X&role=Y` - recommended hire date based on TTF
- `GET /customer/{id}/options` - role/level/location strings for that customer
- `POST /predict` - the main prediction endpoint

## Deployment

Push to a GitHub repo, then on Render: New > Web Service > pick the repo. The `render.yaml` config will be used automatically.
