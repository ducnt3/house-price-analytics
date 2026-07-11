"""Synthesize per-listing contextual fields on top of the Ames base data.

Every generation rule encodes a documented business assumption — see
DATA_DICTIONARY.md for the field-by-field summary and valid ranges.
"""

import numpy as np
import pandas as pd

from src.config import RANDOM_SEED
from src.data_generation.neighborhood_profiles import build_neighborhood_profiles


def _listing_dates(ames: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    """Anchor listing_date to the REAL Ames sale month (YrSold/MoSold).

    A random day-of-month is added purely for realism; the analytical unit is
    the month. Using the dataset's own dates keeps every row internally
    consistent (no home 'listed' years after it actually sold).
    """
    day = rng.integers(1, 28, len(ames))  # 1-27 avoids month-length edge cases
    return pd.to_datetime(dict(year=ames["YrSold"], month=ames["MoSold"], day=day))


def _amenity_distances(ames: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Home-level distances = neighborhood base + per-home variation."""
    profiles = build_neighborhood_profiles(ames)
    merged = ames[["Neighborhood"]].merge(profiles, on="Neighborhood", how="left")
    out = pd.DataFrame(index=ames.index)
    for amenity in ("school", "hospital", "transit"):
        base = merged[f"base_dist_{amenity}_km"].to_numpy()
        # homes scatter around the neighborhood base; floor at 100 m
        out[f"dist_{amenity}_km"] = np.maximum(
            0.1, base * rng.lognormal(0, 0.18, len(ames))
        ).round(2)
    return out


def _renovation_fields(ames: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Renovation flag + cost, consistent with the real YearRemodAdd column.

    Assumption: a remodel's cost scales with home size and finish quality —
    roughly $15 to $44 per sq ft of living area depending on quality, with
    lognormal spread. Homes never remodeled (YearRemodAdd == YearBuilt)
    get renovated='No' and no cost.
    """
    renovated = ames["YearRemodAdd"] > ames["YearBuilt"]
    cost_per_sqft = 12 + 3.2 * ames["OverallQual"]  # quality drives spec level
    cost = ames["GrLivArea"] * cost_per_sqft * rng.lognormal(0, 0.30, len(ames))
    return pd.DataFrame({
        "renovated": np.where(renovated, "Yes", "No"),
        "renovation_cost_usd": np.where(renovated, cost.round(-2), np.nan),
    }, index=ames.index)


def _days_on_market(ames: pd.DataFrame, listing_month: pd.Series,
                    macro: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    """DOM driven by (a) how the home is priced vs its neighborhood and
    (b) market conditions over time.

    Assumptions: a home priced well above its neighborhood's typical level
    sits longer; when the market index is falling (2008-2009 crisis), all
    homes sit substantially longer. Base: median ~35 days in a normal market.
    """
    nbhd_median = ames.groupby("Neighborhood")["SalePrice"].transform("median")
    overprice_ratio = (ames["SalePrice"] / nbhd_median).clip(0.5, 2.5)

    # market heat per month: index below its 6-month trend => cold market
    idx = macro.set_index("month")["market_price_index"]
    trend = idx.rolling(6, min_periods=1).mean()
    cold = (trend / idx).reindex(listing_month).to_numpy()  # >1 when falling

    dom = 35 * overprice_ratio.to_numpy() ** 1.8 * cold ** 6
    dom *= rng.lognormal(0, 0.35, len(ames))
    return pd.Series(np.maximum(3, dom).round().astype(int), index=ames.index)


def _sale_price_with_market_trend(ames: pd.DataFrame, listing_month: pd.Series,
                                  macro: pd.DataFrame,
                                  rng: np.random.Generator) -> pd.Series:
    """Re-express the Kaggle price under the synthetic market index.

    The original Kaggle SalePrice is treated as the home's value at the
    dataset's average market level; multiplying by (index / index_mean) makes
    prices carry the boom-crisis-rebound trend. Original values are preserved
    in sale_price_kaggle for full transparency.
    """
    idx = macro.set_index("month")["market_price_index"]
    factor = (idx / idx.mean()).reindex(listing_month).to_numpy()
    noise = rng.lognormal(0, 0.02, len(ames))  # ±2% idiosyncratic negotiation
    return pd.Series((ames["SalePrice"] * factor * noise).round(-2).astype(int),
                     index=ames.index)


def synthesize_listing_fields(ames: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    """Return the full synthetic extension, one row per Ames home (keyed by Id)."""
    rng = np.random.default_rng(RANDOM_SEED + 2)

    out = pd.DataFrame({"Id": ames["Id"]})
    out["listing_id"] = "L-" + ames["Id"].astype(str).str.zfill(6)
    out["listing_date"] = _listing_dates(ames, rng)
    listing_month = out["listing_date"].dt.to_period("M").astype(str)

    out = pd.concat([out, _amenity_distances(ames, rng),
                     _renovation_fields(ames, rng)], axis=1)
    out["days_on_market"] = _days_on_market(ames, listing_month, macro, rng)

    # monthly macro joined onto each listing
    macro_by_month = macro.set_index("month")
    out["local_interest_rate_pct"] = (
        macro_by_month["local_interest_rate_pct"].reindex(listing_month).to_numpy()
    )
    out["market_price_index"] = (
        macro_by_month["market_price_index"].reindex(listing_month).to_numpy()
    )
    out["sale_price"] = _sale_price_with_market_trend(ames, listing_month, macro, rng)
    out["sale_price_kaggle"] = ames["SalePrice"]
    return out
