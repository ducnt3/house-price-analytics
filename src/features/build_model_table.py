"""Module 4 (features) — build the modeling table. Run from the repo root:

    python -m src.features.build_model_table

Reads data/processed/listings_clean.csv, engineers derived features, selects
the model feature set, runs a VIF multicollinearity check, and writes
data/processed/model_table.csv (features + target + time split flag).

Feature-selection principles (defended in DECISIONS.md):
- Only information available AT VALUATION TIME enters the model. Excluded:
  days_on_market (an outcome of the listing, unknown when the home is priced)
  and market_price_index (a citywide index is published with a lag — using the
  current month's value would be look-ahead leakage).
- One variable per concept: GarageCars not GarageArea (r=0.88), GrLivArea +
  TotalBsmtSF not TotRmsAbvGrd (r=0.83), bath counts combined into one.
"""

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED_DIR, MONITORING_HOLDOUT_START

# The model's contract: exactly these columns, in this role.
NUMERIC_FEATURES = [
    "OverallQual", "OverallCond", "GrLivArea", "TotalBsmtSF", "LotArea",
    "property_age", "years_since_remodel", "total_baths", "GarageCars",
    "Fireplaces", "dist_school_km", "dist_hospital_km", "dist_transit_km",
    "renovation_cost_usd", "local_interest_rate_pct", "listing_month",
]
CATEGORICAL_FEATURES = [
    "Neighborhood", "BldgType", "HouseStyle", "ExterQual", "KitchenQual",
    "CentralAir",
]
TARGET = "sale_price"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns (brief M4: age, renovation flag, amenity score)."""
    out = df.copy()
    out["property_age"] = (out["YrSold"] - out["YearBuilt"]).clip(lower=0)
    out["years_since_remodel"] = (out["YrSold"] - out["YearRemodAdd"]).clip(lower=0)
    out["total_baths"] = (out["FullBath"] + 0.5 * out["HalfBath"]
                          + out["BsmtFullBath"] + 0.5 * out["BsmtHalfBath"])
    out["is_renovated"] = (out["renovated"] == "Yes").astype(int)
    out["renovation_cost_usd"] = out["renovation_cost_usd"].fillna(0)
    out["listing_month"] = out["listing_date"].dt.month
    # amenity-proximity score: closer = higher; kept for EDA/report, NOT a
    # model feature (it is a function of the three distances already included)
    out["amenity_score"] = (1 / (1 + out["dist_school_km"])
                            + 0.5 / (1 + out["dist_hospital_km"])
                            + 0.3 / (1 + out["dist_transit_km"]))
    return out


def vif_table(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """Variance inflation factors: VIF_i = 1 / (1 - R²) of feature i regressed
    on all others. > 10 signals problematic multicollinearity."""
    X = df[cols].to_numpy(dtype=float)
    X = (X - X.mean(0)) / X.std(0)
    vifs = {}
    for i, col in enumerate(cols):
        y, others = X[:, i], np.delete(X, i, axis=1)
        beta, *_ = np.linalg.lstsq(others, y, rcond=None)
        r2 = 1 - ((y - others @ beta) ** 2).sum() / (y ** 2).sum()
        vifs[col] = 1 / max(1 - r2, 1e-9)
    return pd.Series(vifs).sort_values(ascending=False)


def main() -> None:
    df = pd.read_csv(DATA_PROCESSED_DIR / "listings_clean.csv",
                     parse_dates=["listing_date"])
    df = engineer_features(df)

    vifs = vif_table(df, NUMERIC_FEATURES)
    print("VIF (numeric model features):")
    print(vifs.round(2).to_string())
    worst = vifs.iloc[0]
    assert worst < 10, f"multicollinearity regression: max VIF {worst:.1f}"
    print(f"max VIF = {worst:.2f} < 10 — feature set is acceptable for linear models\n")

    keep = (["Id", "listing_id", "listing_date", "is_renovated", "amenity_score"]
            + NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET])
    table = df[keep].copy()
    table["is_monitoring_stream"] = (
        table["listing_date"] >= MONITORING_HOLDOUT_START).astype(int)

    table.to_csv(DATA_PROCESSED_DIR / "model_table.csv", index=False)
    n_stream = table["is_monitoring_stream"].sum()
    print(f"model_table.csv: {len(table)} rows "
          f"({len(table) - n_stream} training window, {n_stream} monitoring stream), "
          f"{len(NUMERIC_FEATURES)} numeric + {len(CATEGORICAL_FEATURES)} categorical features")


if __name__ == "__main__":
    main()
