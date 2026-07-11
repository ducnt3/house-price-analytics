"""Generate the full synthetic data extension. Run from the repo root:

    python -m src.data_generation.generate

Outputs (all committed for reproducibility; identical on every run — seeded):
    data/synthetic/macro_monthly.csv      one row per month, 2006-01..2010-07
    data/synthetic/listings_synthetic.csv per-listing synthetic fields (with
                                          injected dirt), keyed to Ames by Id
    data/synthetic/ames_extended.csv      Kaggle train.csv joined with the
                                          synthetic fields — the single input
                                          for all downstream modules
"""

import pandas as pd

from src.config import DATA_RAW_DIR, DATA_SYNTHETIC_DIR, MONITORING_HOLDOUT_START
from src.data_generation.listing_synthesis import synthesize_listing_fields
from src.data_generation.macro_series import build_macro_series
from src.data_generation.quality_imperfections import inject_imperfections


def main() -> None:
    ames = pd.read_csv(DATA_RAW_DIR / "train.csv")

    macro = build_macro_series()
    listings = synthesize_listing_fields(ames, macro)
    listings = inject_imperfections(listings)

    extended = listings.merge(ames.drop(columns=["SalePrice"]), on="Id", how="left")

    DATA_SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    macro.to_csv(DATA_SYNTHETIC_DIR / "macro_monthly.csv", index=False)
    listings.to_csv(DATA_SYNTHETIC_DIR / "listings_synthetic.csv", index=False)
    extended.to_csv(DATA_SYNTHETIC_DIR / "ames_extended.csv", index=False)

    stream = extended["listing_date"] >= MONITORING_HOLDOUT_START
    print(f"listings: {len(extended)} ({len(extended) - len(ames)} injected duplicates)")
    print(f"training window: {(~stream).sum()} rows | monitoring stream: {stream.sum()} rows")
    print(f"months: {extended['listing_date'].min()} .. {extended['listing_date'].max()}")
    print(f"wrote 3 files to {DATA_SYNTHETIC_DIR}")


if __name__ == "__main__":
    main()
