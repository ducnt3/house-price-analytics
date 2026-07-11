# Data Dictionary — Synthetic Fields

Every synthetically generated field, per the course requirement: column name,
data type, unit, valid range, and the generation logic / business assumption.
The base Kaggle (Ames) fields are documented by Kaggle's own
`data/raw/data_description.txt` and are not duplicated here.

**Reproducibility:** all generation is seeded (`RANDOM_SEED = 42`,
`src/config.py`). `python -m src.data_generation.generate` reproduces the
identical files byte-for-byte (verified).

**Time axis:** listings are anchored to the *real* Ames sale dates
(`YrSold`/`MoSold`, Jan 2006 – Jul 2010, 55 months). All 2010 listings
(Jan–Jul, 175 rows) are the **monitoring holdout stream** — never used in
training, replayed month-by-month in Module 7.

## Files

| File | Grain | Contents |
|---|---|---|
| `data/synthetic/macro_monthly.csv` | 1 row / month | Synthetic macro series |
| `data/synthetic/listings_synthetic.csv` | 1 row / listing | Synthetic fields only, keyed to Ames by `Id` |
| `data/synthetic/ames_extended.csv` | 1 row / listing | Kaggle columns + synthetic fields — input for all downstream modules |

## Listing-level fields

| Column | Type | Unit | Valid range | Generation logic / business assumption |
|---|---|---|---|---|
| `listing_id` | str | — | `L-` + 6 digits | Platform listing key. Injected duplicates use prefix `L-9`. |
| `listing_date` | date | — | 2006-01-01 … 2010-07-27 | Real Ames sale month (`YrSold`/`MoSold`) + random day 1–27. Uses the dataset's own dates so no row is internally inconsistent. |
| `dist_school_km` | float | km | 0.1 – ~6 | Neighborhood base distance + per-home lognormal scatter (σ=0.18). **Assumption:** pricier neighborhoods sit closer to schools (families pay for access) — base distance rises as neighborhood median price falls (0.4→3.5 km) plus noise. Realized corr with price ≈ −0.60. |
| `dist_hospital_km` | float | km | 0.5 – ~14 | Same mechanism as schools, range 1.0→8.0 km. |
| `dist_transit_km` | float | km | 0.1 – ~4 | Neighborhood base drawn **independently of price** (bus lines follow arterial roads, not wealth) from U(0.2, 2.5) km + scatter. Realized corr with price ≈ 0.1. |
| `renovated` | str | — | Yes / No | `Yes` iff Kaggle `YearRemodAdd` > `YearBuilt` — consistent with the real remodel column by construction. |
| `renovation_cost_usd` | float | USD | ~$15k – $400k; NaN if not renovated | Living area × ($12 + $3.2 × OverallQual)/sqft × lognormal(σ=0.30), rounded to $100. **Assumption:** remodel cost scales with size and finish quality (~$15–44/sqft). |
| `days_on_market` | int | days | 3 – ~250 | 35 days × (price ÷ neighborhood median)^1.8 × market-coldness^6 × lognormal(σ=0.35). **Assumptions:** overpriced homes sit longer; everything sits longer when the market index is below trend (2008–09). Realized median: 32.5 (2006) → 38 (2008) → 32 (2010). |
| `local_interest_rate_pct` | float | % p.a. | 4.7 – 6.7 | Monthly macro series joined by listing month (see below). |
| `market_price_index` | float | index, Jan 2006 = 100 | ~94 – 106 | Monthly macro series joined by listing month (see below). |
| `sale_price` | int | USD | ~$34k – $770k | **Modeling target.** Kaggle `SalePrice` × (index ÷ mean index) × lognormal(σ=0.02) negotiation noise, rounded to $100. Re-expresses each price under the synthetic market trend so the target genuinely drifts over time. |
| `sale_price_kaggle` | int | USD | 34,900 – 755,000 | Original Kaggle `SalePrice`, preserved unmodified for transparency and auditability. |

## Macro series (`macro_monthly.csv`)

| Column | Type | Unit | Valid range | Generation logic / business assumption |
|---|---|---|---|---|
| `month` | str | YYYY-MM | 2006-01 … 2010-07 | Calendar month. |
| `local_interest_rate_pct` | float | % p.a. | 4.7 – 6.7 | Piecewise-linear through anchors shaped like US 30-yr mortgage rates through the financial crisis (6.25% → peak 6.65% mid-2007 → 4.75% by 2010) + N(0, 0.04) monthly noise. |
| `market_price_index` | float | index | ~94 – 106 | Boom–crisis–rebound shape: +5.5% to mid-2007, −10% peak-to-trough through 2009, **+9.5% rebound during 2010** (sharp post-crisis recoveries of this size occurred in real US metros; sized to be detectable within the 7-month stream). The rebound occurs only inside the monitoring stream, so a model trained on 2006–09 under-predicts 2010 — a designed, explainable performance-drift signal for Module 7. + N(0, 0.35) noise. |

## Injected data-quality problems

Deliberate, seeded, injected **only into synthetic fields** and **only before
2010** (the monitoring stream stays clean so drift is never confused with
dirt). Module 3 must detect and fix each with before/after evidence.
Definitions: `src/data_generation/quality_imperfections.py`.

| # | Field | Problem | Rate / count (realized) |
|---|---|---|---|
| 1 | `dist_school_km` | Missing (blank at listing entry) | 2% (26 rows) |
| 2 | `renovated` | Inconsistent free-text labels: Y, yes, YES, N, no, NO | 4% (51 rows) |
| 3 | `days_on_market` | Legacy sentinel `999` = "unknown" | 0.4% (5 rows) |
| 4 | `dist_transit_km` | Entered in meters instead of km (values > 100) | 0.3% (4 rows) |
| 5 | whole row | Same home re-posted days later under a new `listing_id` (`L-9…`) | 12 rows |
