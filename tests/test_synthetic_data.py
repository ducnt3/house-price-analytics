"""Invariant tests for the generated synthetic data.

These encode the claims made in DATA_DICTIONARY.md — if a change to the
generator breaks a documented property (correlation direction, dirt placement,
clean monitoring stream), a test fails rather than the claim silently rotting.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_SYNTHETIC_DIR, MONITORING_HOLDOUT_START


def _load() -> pd.DataFrame:
    return pd.read_csv(
        DATA_SYNTHETIC_DIR / "ames_extended.csv", parse_dates=["listing_date"]
    )


def test_time_axis_matches_real_ames_sale_dates():
    df = _load()
    assert (df["listing_date"].dt.year == df["YrSold"]).all()
    assert (df["listing_date"].dt.month == df["MoSold"]).all()


def test_monitoring_stream_exists_and_is_clean():
    df = _load()
    stream = df[df["listing_date"] >= MONITORING_HOLDOUT_START]
    assert len(stream) >= 150  # enough rows for monthly rolling metrics
    # no injected dirt in the stream: drift must not be confused with dirt
    assert stream["dist_school_km"].notna().all()
    assert stream["renovated"].isin(["Yes", "No"]).all()
    assert (stream["days_on_market"] != 999).all()
    assert (stream["dist_transit_km"] < 100).all()
    assert not stream["Id"].duplicated().any()


def test_documented_dirt_is_present_in_training_window():
    df = _load()
    train = df[df["listing_date"] < MONITORING_HOLDOUT_START]
    assert train["dist_school_km"].isna().sum() > 0
    assert not train["renovated"].isin(["Yes", "No"]).all()  # messy labels exist
    assert (train["days_on_market"] == 999).sum() > 0
    assert (train["dist_transit_km"] > 100).sum() > 0  # meter-unit errors
    assert train["Id"].duplicated().sum() > 0  # duplicate listings


def test_amenity_price_relationships_as_documented():
    df = _load()
    ok = df["dist_transit_km"] < 100  # exclude meter-unit errors
    assert df["dist_school_km"].corr(df["sale_price"]) < -0.4
    assert abs(df.loc[ok, "dist_transit_km"].corr(df.loc[ok, "sale_price"])) < 0.25


def test_target_carries_market_trend():
    df = _load()
    factor = df["sale_price"] / df["sale_price_kaggle"]
    by_year = factor.groupby(df["listing_date"].dt.year).mean()
    assert by_year[2007] > by_year[2009]  # boom then crisis
    assert by_year[2010] > by_year[2009]  # rebound inside the monitoring stream


def test_renovation_consistent_with_kaggle_remodel_column():
    df = _load()
    clean = df[df["renovated"].isin(["Yes", "No"])]
    remodeled = clean["YearRemodAdd"] > clean["YearBuilt"]
    assert ((clean["renovated"] == "Yes") == remodeled).all()
    # cost present iff renovated
    assert clean.loc[clean["renovated"] == "Yes", "renovation_cost_usd"].notna().all()
    assert clean.loc[clean["renovated"] == "No", "renovation_cost_usd"].isna().all()
