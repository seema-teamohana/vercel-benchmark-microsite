"""
FastAPI HTTP layer.

Endpoints:
- GET  /healthz       - basic health check
- GET  /customers     - list of customers (for the "view as" dropdown)
- GET  /reference     - canonical roles, levels, countries, metros for UI
- POST /predict       - the main endpoint
"""
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.orchestrator import get_orchestrator

app = FastAPI(title="TeamOhana Salary Benchmark", version="0.1.0")

# CORS — allow the Vercel-hosted frontend to call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    customer_id: str = Field(..., description="Lowercase customer id, e.g. 'docker'")
    role: str = Field(..., description="The customer's raw role string")
    level: str = Field(..., description="The customer's raw level code")
    location: str = Field(..., description="The customer's raw location string")
    hire_date: str = Field(..., description="YYYY-MM-DD")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/customers")
def customers():
    orch = get_orchestrator()
    return {"customers": orch.available_customers()}


@app.get("/reference")
def reference():
    orch = get_orchestrator()
    return orch.engine.reference


@app.get("/recommend-date")
def recommend_date(customer_id: str, role: str):
    orch = get_orchestrator()
    return orch.recommended_hire_date(customer_id, role)


@app.post("/predict")
def predict(req: PredictRequest):
    orch = get_orchestrator()
    try:
        hire_date = datetime.strptime(req.hire_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, detail="hire_date must be YYYY-MM-DD")

    result = orch.predict(
        customer_id=req.customer_id,
        raw_role=req.role,
        raw_level=req.level,
        raw_location=req.location,
        hire_date=hire_date,
    )
    return result


# For listing available roles/levels/locations within a specific customer's file
@app.get("/customer/{customer_id}/options")
def customer_options(customer_id: str):
    """Return the role/level/location strings present in this customer's data.
    The frontend uses these to populate dropdowns specific to the customer
    (so a Docker user picks from Docker's actual role strings)."""
    orch = get_orchestrator()
    if customer_id not in orch.customer_data:
        raise HTTPException(404, detail=f"Unknown customer: {customer_id}")
    df = orch.customer_data[customer_id]
    return {
        "roles": sorted(df['job_role'].dropna().unique().tolist()),
        "levels": sorted(df['job_level'].dropna().unique().tolist()),
        "locations": sorted(df['location'].dropna().unique().tolist()),
    }
