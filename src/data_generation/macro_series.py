"""Synthetic monthly macro series for the Ames market, Jan 2006 - Jul 2010.

Business assumptions (documented in DATA_DICTIONARY.md):
- local_interest_rate_pct follows the broad shape of US 30-year mortgage rates
  through the financial crisis: ~6.3% in 2006, peaking ~6.6% in mid-2007, then
  cut sharply to ~4.8% by 2010, with small month-to-month noise.
- market_price_index (base 100 = Jan 2006) rises ~4%/yr pre-crisis, falls ~10%
  peak-to-trough through 2008-2009, then REBOUNDS ~9.5% during 2010 (sharp
  post-crisis recoveries of this size occurred in several US metros).
  The 2010 rebound is deliberate: it happens only in the monitoring holdout
  period, so a model trained on 2006-2009 systematically under-predicts 2010
  prices — a real, explainable performance-drift signal for Module 7. Its
  size is chosen so the drift is detectable within the short 7-month stream.
"""

import numpy as np
import pandas as pd

from src.config import RANDOM_SEED, TIME_AXIS_END, TIME_AXIS_START

# (month, anchor rate %) — interpolated linearly between anchors
_RATE_ANCHORS = [
    ("2006-01", 6.25), ("2007-06", 6.65), ("2008-06", 6.05),
    ("2009-03", 5.05), ("2009-12", 4.95), ("2010-07", 4.75),
]

# (month, anchor index level, base 100 = Jan 2006)
_INDEX_ANCHORS = [
    ("2006-01", 100.0), ("2007-06", 105.5), ("2008-06", 101.5),
    ("2009-06", 95.5), ("2009-12", 95.0), ("2010-07", 104.0),
]


def _interpolate_anchors(months: pd.PeriodIndex, anchors) -> np.ndarray:
    """Piecewise-linear interpolation of (month, value) anchors over the axis."""
    anchor_pos = [months.get_loc(pd.Period(m, freq="M")) for m, _ in anchors]
    anchor_val = [v for _, v in anchors]
    return np.interp(np.arange(len(months)), anchor_pos, anchor_val)


def build_macro_series() -> pd.DataFrame:
    """Return one row per month: interest rate and price index, with seeded noise."""
    rng = np.random.default_rng(RANDOM_SEED)
    months = pd.period_range(TIME_AXIS_START, TIME_AXIS_END, freq="M")

    rate = _interpolate_anchors(months, _RATE_ANCHORS)
    rate += rng.normal(0, 0.04, len(months))  # small monthly wobble

    index = _interpolate_anchors(months, _INDEX_ANCHORS)
    index += rng.normal(0, 0.35, len(months))

    return pd.DataFrame({
        "month": months.astype(str),
        "local_interest_rate_pct": rate.round(2),
        "market_price_index": index.round(2),
    })
