"""Module 5 (part 2) — train the deployed quantile model. Run from repo root:

    python -m src.modeling.train_final

Trains LightGBM quantile models (p10/p50/p90) on the training window
(2006-2009) and calibrates the 80% interval with conformalized quantile
regression (CQR): a 20% calibration split, never seen in training, measures
how much the raw quantile band under/over-covers, and the band is widened by
exactly that amount. Result: a defensible statement — "80% of true prices fall
inside the stated range" — verified, not assumed.

Artifact: models/valuation_model.pkl (three boosters + conformal offset +
feature contract + training-median defaults for the UI).
"""

import json

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from src.config import MODELS_DIR, RANDOM_SEED
from src.features.build_model_table import (CATEGORICAL_FEATURES,
                                            NUMERIC_FEATURES, TARGET)
from src.modeling.model_inputs import (category_levels, encode_for_trees,
                                       load_model_table)

INTERVAL_COVERAGE = 0.80  # the "80% confidence range" shown in the UI

# Regularized for ~1.3k training rows (see models/model_comparison.json for
# the comparison run; larger default trees overfit this dataset)
_LGB_PARAMS = dict(n_estimators=1500, learning_rate=0.03, num_leaves=8,
                   min_child_samples=15, colsample_bytree=0.7, subsample=0.8,
                   subsample_freq=1, reg_lambda=1.0, random_state=RANDOM_SEED,
                   verbose=-1)


def train_quantile_models(X, y_log) -> dict:
    models = {}
    for name, alpha in {"p10": 0.10, "p50": 0.50, "p90": 0.90}.items():
        m = lgb.LGBMRegressor(objective="quantile", alpha=alpha, **_LGB_PARAMS)
        m.fit(X, y_log)
        models[name] = m
    return models


def conformal_offset(models, X_cal, y_log_cal) -> float:
    """CQR: score = how far outside the [p10, p90] band each calibration point
    falls; the (n+1)(1-a)/n empirical quantile of scores is the widening that
    guarantees the target coverage (Romano et al., 2019)."""
    lo = models["p10"].predict(X_cal)
    hi = models["p90"].predict(X_cal)
    scores = np.maximum(lo - y_log_cal, y_log_cal - hi)
    n = len(scores)
    level = min(1.0, np.ceil((n + 1) * INTERVAL_COVERAGE) / n)
    return float(np.quantile(scores, level))


def predict_interval(models, offset, X) -> pd.DataFrame:
    """Point + calibrated 80% interval on the dollar scale."""
    return pd.DataFrame({
        "low": np.expm1(models["p10"].predict(X) - offset),
        "point": np.expm1(models["p50"].predict(X)),
        "high": np.expm1(models["p90"].predict(X) + offset),
    })


def main() -> None:
    train, _ = load_model_table()
    levels = category_levels(train)

    fit_df, cal_df = train_test_split(train, test_size=0.20,
                                      random_state=RANDOM_SEED)
    X_fit, X_cal = (encode_for_trees(d, levels) for d in (fit_df, cal_df))
    y_fit_log = np.log1p(fit_df[TARGET]).to_numpy()
    y_cal, y_cal_log = cal_df[TARGET].to_numpy(), np.log1p(cal_df[TARGET]).to_numpy()

    models = train_quantile_models(X_fit, y_fit_log)
    offset = conformal_offset(models, X_cal, y_cal_log)

    # --- calibration evidence -------------------------------------------
    raw_lo = np.expm1(models["p10"].predict(X_cal))
    raw_hi = np.expm1(models["p90"].predict(X_cal))
    raw_cover = ((y_cal >= raw_lo) & (y_cal <= raw_hi)).mean()
    iv = predict_interval(models, offset, X_cal)
    cover = ((y_cal >= iv.low) & (y_cal <= iv.high)).mean()
    print(f"calibration set (n={len(cal_df)}): raw quantile coverage "
          f"{raw_cover:.1%} -> conformalized {cover:.1%} (target {INTERVAL_COVERAGE:.0%})")

    # interval width must grow for expensive homes (the UI's uncertainty story)
    width = iv.high - iv.low
    tercile = pd.qcut(iv.point, 3, labels=["typical", "mid", "high-value"])
    by_seg = pd.DataFrame({"width_usd": width, "width_pct": width / iv.point * 100,
                           "seg": tercile}).groupby("seg", observed=True).mean()
    print("\ninterval width by predicted-price tercile:")
    print(by_seg.round(0 if by_seg.width_usd.max() > 100 else 2).to_string())
    assert by_seg.width_usd.is_monotonic_increasing, \
        "intervals must widen for high-value homes"

    # point-model quality on calibration (baseline for monitoring)
    rmse = float(np.sqrt(mean_squared_error(y_cal, iv.point)))
    mae = float(mean_absolute_error(y_cal, iv.point))
    print(f"\np50 point model on calibration: RMSE ${rmse:,.0f}, MAE ${mae:,.0f}")

    # --- ship ------------------------------------------------------------
    defaults = {c: float(train[c].median()) for c in NUMERIC_FEATURES}
    defaults |= {c: train[c].mode()[0] for c in CATEGORICAL_FEATURES}
    artifact = {
        "models": models,
        "conformal_offset_log": offset,
        "interval_coverage": INTERVAL_COVERAGE,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "category_levels": levels,
        "input_defaults": defaults,
        "baseline": {"rmse": rmse, "mae": mae, "calibration_coverage": float(cover)},
        "trained_on": "2006-01..2009-12",
    }
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(artifact, MODELS_DIR / "valuation_model.pkl", compress=3)
    (MODELS_DIR / "training_summary.json").write_text(json.dumps({
        "calibration_coverage": float(cover), "raw_coverage": float(raw_cover),
        "conformal_offset_log": offset, "rmse": rmse, "mae": mae,
        "interval_width_by_segment": by_seg.round(1).to_dict()}, indent=2))
    size_mb = (MODELS_DIR / "valuation_model.pkl").stat().st_size / 1e6
    print(f"\nwrote models/valuation_model.pkl ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
