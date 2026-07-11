"""Prediction API (Module 6 deliverable). Run from the repo root:

    uvicorn app.api.main:app --reload

POST /predict returns a price estimate with a calibrated 80% confidence
range. Uses the same ValuationService as the Streamlit tool, so both
deliverables always agree. Interactive docs at /docs (OpenAPI).

Any omitted field falls back to the training-median "typical home" default —
the response echoes which defaults were applied so callers know.
"""

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.modeling.valuation_service import ValuationService

app = FastAPI(
    title="House Price Valuation API",
    description="Estimates fair market value (USD, 2010 Ames market level) "
                "with a conformally calibrated 80% confidence range.",
    version="1.0.0",
)
service = ValuationService()


class PropertyFeatures(BaseModel):
    """All fields optional — omitted ones use training-median defaults."""
    Neighborhood: str | None = Field(None, examples=["NAmes"])
    GrLivArea: float | None = Field(None, ge=200, le=8000,
                                    description="Above-ground living area, sq ft")
    TotalBsmtSF: float | None = Field(None, ge=0, le=4000)
    OverallQual: int | None = Field(None, ge=1, le=10)
    OverallCond: int | None = Field(None, ge=1, le=10)
    property_age: float | None = Field(None, ge=0, le=150, description="Years")
    years_since_remodel: float | None = Field(None, ge=0, le=150)
    total_baths: float | None = Field(None, ge=0, le=8)
    GarageCars: float | None = Field(None, ge=0, le=5)
    Fireplaces: float | None = Field(None, ge=0, le=4)
    LotArea: float | None = Field(None, ge=500, le=250000, description="Sq ft")
    dist_school_km: float | None = Field(None, ge=0, le=30)
    dist_hospital_km: float | None = Field(None, ge=0, le=50)
    dist_transit_km: float | None = Field(None, ge=0, le=30)
    renovation_cost_usd: float | None = Field(None, ge=0, le=1_000_000)
    KitchenQual: str | None = Field(None, examples=["TA"])
    ExterQual: str | None = None
    BldgType: str | None = None
    HouseStyle: str | None = None
    CentralAir: str | None = Field(None, pattern="^[YN]$")


class ValuationResponse(BaseModel):
    estimate_usd: float
    range_low_usd: float
    range_high_usd: float
    coverage: float = Field(description="Calibrated interval coverage (0.8 = 80%)")
    relative_width_pct: float
    defaults_applied: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_trained_on": service.artifact["trained_on"]}


@app.post("/predict", response_model=ValuationResponse)
def predict(features: PropertyFeatures) -> ValuationResponse:
    provided = features.model_dump(exclude_none=True)
    # reject unknown category values with a helpful message
    for col, cats in service.category_levels.items():
        if col in provided and str(provided[col]) not in cats:
            raise HTTPException(422, f"unknown {col} '{provided[col]}'; "
                                     f"valid values: {cats}")
    result = service.predict(provided)
    omitted = [k for k in service.input_defaults if k not in provided]
    return ValuationResponse(**result, defaults_applied=omitted)
