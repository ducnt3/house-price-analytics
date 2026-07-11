"""Per-neighborhood amenity-distance profiles.

Business assumption (documented in DATA_DICTIONARY.md): in a small city like
Ames, amenity access is a NEIGHBORHOOD property, not a per-house lottery.
Pricier neighborhoods tend to sit closer to schools and hospitals (families
pay for access), while transit access is unrelated to price (bus lines follow
arterial roads, not wealth). Each neighborhood therefore gets one fixed base
distance per amenity; individual homes vary around that base.

Implementation: neighborhoods are ranked by their median Kaggle sale price;
school/hospital base distances increase as the price rank falls, plus seeded
noise so the relationship is a tendency, not a rule. Transit distance is drawn
independently of price rank.
"""

import numpy as np
import pandas as pd

from src.config import RANDOM_SEED

# Base-distance ranges (km) across the price ranking, best -> worst neighborhood
_SCHOOL_KM_RANGE = (0.4, 3.5)
_HOSPITAL_KM_RANGE = (1.0, 8.0)
_TRANSIT_KM_RANGE = (0.2, 2.5)  # independent of price


def build_neighborhood_profiles(ames: pd.DataFrame) -> pd.DataFrame:
    """Return one row per neighborhood with base amenity distances in km."""
    rng = np.random.default_rng(RANDOM_SEED + 1)

    median_price = ames.groupby("Neighborhood")["SalePrice"].median()
    # rank 0.0 = most expensive neighborhood, 1.0 = least expensive
    rank = median_price.rank(ascending=False, pct=True) - 1 / len(median_price)

    def _priced_distance(lo: float, hi: float) -> pd.Series:
        base = lo + rank * (hi - lo)               # price-linked component
        noise = rng.normal(0, (hi - lo) * 0.12, len(rank))  # tendency, not rule
        return (base + noise).clip(lower=lo * 0.5)

    profiles = pd.DataFrame({
        "Neighborhood": rank.index,
        "base_dist_school_km": _priced_distance(*_SCHOOL_KM_RANGE),
        "base_dist_hospital_km": _priced_distance(*_HOSPITAL_KM_RANGE),
        "base_dist_transit_km": rng.uniform(*_TRANSIT_KM_RANGE, len(rank)),
    })
    return profiles.reset_index(drop=True)
