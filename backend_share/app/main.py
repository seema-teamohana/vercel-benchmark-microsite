"""
FastAPI app for the public salary benchmark microsite.

Three endpoints:
  GET  /healthz       — health check (no rate limit)
  GET  /reference     — dropdown options (rate limited)
  POST /predict       — query → 4 quantiles + offer distribution (rate limited)

Rate limit: 10 requests/minute per IP. Applies to /reference and /predict.
The frontend calls /reference once per page load and /predict once per query,
so 10/min easily covers normal usage and blocks abuse.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.orchestrator import get_orchestrator

# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------
app = FastAPI(title="TeamOhana Salary Benchmark", version="2.0")

# Rate limiter — 10 requests/minute per IP for protected endpoints
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------
class PredictRequest(BaseModel):
    role: str
    level: str
    location: str
    hire_date: str  # YYYY-MM-DD


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    """Health check. Render uses this to know the service is up."""
    return {"ok": True}


@app.get("/reference")
@limiter.limit("10/minute")
def reference(request: Request):
    """Dropdown options for the public microsite.

    Returns:
      - roles: public canonical roles only
      - countries: countries with any supported data
      - available_combinations: nested {role -> country -> {level: n_rows}}
        for cascading dropdowns. Only includes combinations with >= 5 rows
        of training data at the (role, country, standard_level) grain.
      - metros_by_country: optional metro dropdown per country
    """
    import json as _json
    from pathlib import Path as _Path
    orch = get_orchestrator()
    ref = orch.engine.reference

    # Load available_combinations artifact
    artifacts_dir = _Path(__file__).parent.parent / "artifacts"
    with open(artifacts_dir / "available_combinations.json") as f:
        available_combinations = _json.load(f)

    # Derive roles + countries from the combinations for convenience
    roles = sorted(available_combinations.keys())
    countries_set = set()
    for role_dict in available_combinations.values():
        countries_set.update(role_dict.keys())

    return {
        "roles": roles,
        "countries": sorted(countries_set),
        "available_combinations": available_combinations,
        "metros_by_country": ref.get("metros_by_country", {}),
    }


@app.post("/predict")
@limiter.limit("10/minute")
def predict(request: Request, body: PredictRequest):
    """Predict 4 quantiles + offer distribution for a query."""
    # Parse hire date
    try:
        hire_date = datetime.strptime(body.hire_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hire_date format: {body.hire_date}. Expected YYYY-MM-DD."
        )

    orch = get_orchestrator()
    result = orch.predict(
        raw_role=body.role,
        raw_level=body.level,
        raw_location=body.location,
        hire_date=hire_date,
    )
    return result
