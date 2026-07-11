"""Serving layer: one prediction path shared by the Streamlit app and the
FastAPI service, so the two deliverables can never disagree.

Callers pass any subset of model features; unspecified fields fall back to
the training-median defaults stored inside the artifact (a sensible "typical
home" prior for fields a user doesn't know).
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

DEFAULT_ARTIFACT = Path(__file__).resolve().parent.parent.parent / "models" / "valuation_model.pkl"


class ValuationService:
    def __init__(self, artifact_path: Path = DEFAULT_ARTIFACT):
        self.artifact = joblib.load(artifact_path)

    @property
    def input_defaults(self) -> dict:
        return dict(self.artifact["input_defaults"])

    @property
    def category_levels(self) -> dict:
        return dict(self.artifact["category_levels"])

    def _encode(self, inputs: dict) -> pd.DataFrame:
        a = self.artifact
        row = a["input_defaults"] | {k: v for k, v in inputs.items() if v is not None}
        X = pd.DataFrame([row])
        for col in a["numeric_features"]:
            X[col] = pd.to_numeric(X[col])
        for col, cats in a["category_levels"].items():
            X[col] = pd.Categorical(X[col].astype(str), categories=cats)
        return X[a["numeric_features"] + a["categorical_features"]]

    def predict(self, inputs: dict) -> dict:
        """Return point estimate + calibrated interval (USD) for one home."""
        a = self.artifact
        X = self._encode(inputs)
        offset = a["conformal_offset_log"]
        low = float(np.expm1(a["models"]["p10"].predict(X)[0] - offset))
        point = float(np.expm1(a["models"]["p50"].predict(X)[0]))
        high = float(np.expm1(a["models"]["p90"].predict(X)[0] + offset))
        # quantile models are trained independently; enforce ordering at the edge
        low, high = min(low, point), max(high, point)
        return {
            "estimate_usd": round(point, -2),
            "range_low_usd": round(low, -2),
            "range_high_usd": round(high, -2),
            "coverage": a["interval_coverage"],
            "relative_width_pct": round((high - low) / point * 100, 1),
        }
