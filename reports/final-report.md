# How Much Is This House Worth — and How Sure Are We?

**House Price Prediction for a Real Estate Listing Platform**
Business Analytics (IT5315E) · Group project · Final report

| Member | Student ID | Role |
|---|---|---|
| Đỗ Hoàng Việt | 20252744M | Data Engineer — synthetic data, data dictionary, cleaning |
| Nguyễn Minh Huyền | 20252007M | Data Analyst — EDA, visualization of price drivers |
| Nguyễn Thị Huyền Trang | 20251322M | ML Engineer (Modeling) — features, regression models |
| Bùi Tá Cường | 20242430M | ML Engineer (Evaluation) — CV, residuals, interval calibration |
| Nguyễn Tiến Đức | 20252076M | MLOps Lead — deployment, API, monitoring |

**Live valuation tool:** https://house-price-analytics-tjpb7ntxsd6kzbapp7bymmv.streamlit.app/
**Source code:** https://github.com/ducnt3/house-price-analytics

---

## 1. The business problem

A listing platform loses both ways when prices are wrong: an inflated asking
price scares serious buyers away; an underpriced home leaves the seller's
money on the table. Agents need a *defensible* estimate long before a formal
appraisal — and, just as importantly, they need to know **how much to trust
it**. A $180k ± $18k estimate supports a confident listing; $180k ± $70k says
"get an appraisal first." Our deliverable is therefore not a number but a
number **with a calibrated confidence range**, deployed as a working tool.

Error tolerance: mispricing by ~10% is roughly the margin agents negotiate
within; a systematic bias beyond ~5% at portfolio level distorts the
platform's market statistics and must trigger model retraining.

## 2. The data — and why it can be trusted

**Base:** the Kaggle Ames, Iowa dataset — 1,460 home sales with 80 structural
attributes (area, quality, age, garage, …). **Extension (required synthetic
component):** 12 contextual fields we generated in Python, each documented in
`DATA_DICTIONARY.md` with its unit, valid range, and the business assumption
behind it.

Three design choices make the synthetic layer trustworthy rather than
decorative:

1. **Real time axis.** Rather than inventing listing dates, we anchored them
   to the sale dates already inside the Ames data (Jan 2006 – Jul 2010). No
   row contradicts itself, and the window spans a true market story — the
   financial crisis. A synthetic macro layer (interest-rate series, market
   price index with boom → −10% crisis → +9.5% rebound in 2010) re-expresses
   each sale price under that trend; the original Kaggle price is preserved
   in a separate column for auditability.
2. **Behavioral realism, generated conditionally.** Amenity distances are a
   neighborhood property (pricier neighborhoods sit closer to schools:
   realized correlation −0.60 with price; transit access deliberately
   uncorrelated). Renovation costs are consistent with the dataset's real
   remodel-year column. Days-on-market lengthens when the market index falls
   — as it did in 2008–09.
3. **Documented imperfections.** Real listing pipelines produce dirty data, so
   we injected five seeded, documented problems (missing values, free-text
   label variants, sentinel 999s, metre/km unit errors, duplicate listings) —
   only into synthetic fields, and only before 2010, so the monitoring stream
   is never confused with dirt. Every claim above is enforced by automated
   tests; the whole generation is seeded and reproduces byte-for-byte.

## 3. What drives price (EDA)

*(Figures 1–7 in `reports/figures/`.)*

- **Quality and size dominate.** Overall quality correlates 0.79 with price
  (median $85k at quality 3 → $346k at quality 9); living area 0.71.
- **Location is a 3.5× lever.** Neighborhood medians span $90k (MeadowV) to
  $313k (NridgHt) — and our amenity fields explain much of the premium:
  price falls steadily with school distance, while transit distance is flat.
  Actionable for the platform: school proximity is priced in; bus access isn't.
- **The market moved.** Prices rose ~5% to mid-2007, fell ~10% through 2009,
  and rebounded sharply in 2010. A price model in this market **ages** — which
  is why monitoring (§6) is a first-class deliverable, not an afterthought.
- **Redundancy mapped.** Garage cars/area correlate 0.88, rooms/living area
  0.83, etc. We kept one variable per concept; the final feature set has a
  maximum variance-inflation factor of 3.9 (well under the standard threshold
  of 10), so linear baselines are stable.
- Sale price is right-skewed (skew 1.93 → 0.12 after log transform), so all
  models predict log price.

## 4. Cleaning, with before/after evidence

Every fix targets a diagnosed cause (script prints the evidence table):
12 duplicate listings removed (same home re-posted; kept the earliest);
51 free-text renovation labels normalized; 5 days-on-market "999" sentinels
imputed with the listing quarter's median; 4 transit distances entered in
metres converted; 26 missing school distances filled with the neighborhood
median (amenity access is a neighborhood property); 7,480 Kaggle "no such
feature" NAs converted to an explicit category; LotFrontage imputed by
neighborhood; and the two canonical Ames partial-sale outliers (Ids 524,
1299) dropped as non-market transactions. 1,472 rows in → 1,458 out.

## 5. The model — and its honesty about uncertainty

**Leakage discipline.** Only information available at valuation time enters
the model. We excluded days-on-market (an outcome of the listing, not an
input) and the market price index (published with a lag; using the current
month's value would be look-ahead leakage). The interest rate stays — it is
publicly known when a home is listed.

**Comparison (5-fold cross-validation, 1,283 training sales, 2006–09):**

| Model | RMSE | MAE | MAPE | R² |
|---|---|---|---|---|
| Linear Regression | $23,409 | $15,806 | 9.11% | 0.914 |
| **Ridge** | **$23,195** | **$15,573** | **8.99%** | **0.916** |
| Lasso | $23,324 | $15,670 | 9.04% | 0.915 |
| Random Forest | $29,509 | $18,469 | 10.43% | 0.863 |
| LightGBM | $27,441 | $17,334 | 9.78% | 0.882 |

Ridge wins on point accuracy — log price is close to linear in the drivers,
and 1,283 rows favor low-variance models. **We nevertheless deploy the
quantile LightGBM** (its median forecast as the point estimate): the business
question demands a per-home confidence range, quantile regression provides
feature-dependent intervals natively, and one coherent model beats stitching
two model families together. The cost — 9.8% vs 9.0% MAPE — is immaterial to
the tool's purpose; the comparison is reported, not hidden.

**The confidence range is verified, not assumed.** The raw p10–p90 quantile
band claimed 80% coverage but actually contained only **59%** of held-out
prices — naive intervals lie. Conformalized quantile regression (a 20%
calibration split measures the shortfall and widens the band accordingly)
restores measured coverage to **80.5%**. Interval width behaves as a buyer
would expect: ~$35k for a typical home, ~$78k for high-value homes. Residual
analysis shows no systematic bias across price segments except the cheapest
decile (over-predicted — the model is cautious about very cheap homes; noted
as a limitation).

## 6. The working product

- **Valuation tool (live link above):** a Streamlit app where an agent enters
  a property's characteristics and receives the estimate, the calibrated 80%
  range, and a plain-language confidence note (tight range = common home
  profile; wide range = unusual/high-value, consider an appraisal). The model
  runs in-process — the demo cannot be taken down by a second service failing.
- **Prediction API:** a FastAPI service (`uvicorn app.api.main:app`) exposing
  `POST /predict` with OpenAPI docs; any omitted field falls back to
  training-median defaults and the response says which. Both surfaces share
  one serving layer, so they can never disagree.
- Deployment survived a real-world shock: our first target (Hugging Face
  Spaces) paywalled compute mid-project; because the pipeline was proven in
  week one with a placeholder model, switching to Streamlit Community Cloud
  cost hours, not weeks.

## 7. Monitoring: the model watches itself age

The 175 sales of 2010 were held out as the "incoming stream" and replayed
month by month through Evidently, evaluating a rolling 3-month window against
the training baseline. Four retraining triggers were defined **before**
looking at the stream:

| Trigger | Definition | 2010 outcome |
|---|---|---|
| T1 Data drift | >30% of features drift (Evidently; min. 40-row window) | Fires Mar–Jul: interest-rate regime + post-crisis sales-mix shift |
| T2 Performance | Rolling RMSE > 1.25× baseline | Fires March (RMSE $32.0k vs $24.4k baseline) |
| T3 Systematic bias | \|mean error\| > 5% of median price | Fires Apr–Jul: bias −0.4% → **−7.9%** as the rebound accelerates |
| T4 Interval health | 80%-range coverage < 65% | Never fires, but coverage degrades 80% → ~73% — early warning visible |

The verdict a real platform would act on: **retrain from March 2010** — the
market recovered faster than the model's training window, and the model
systematically prices below the market. Notably, drift detection alone (T1)
flags *that* inputs changed, but only the error/bias monitors (T2/T3) show
*it matters* — the case for monitoring predictions, not just inputs.

## 8. Pricing-strategy recommendations

1. **Price on quality and location first** — quality, area, and neighborhood
   (largely via school proximity) carry most of the signal; renovation
   history refines it.
2. **Show the range, not just the number.** A calibrated range converts the
   tool from a black box into a negotiation aid, and tells agents when to
   escalate to an appraisal (wide range = unusual home).
3. **Treat the model as perishable.** In a moving market our model drifted
   beyond tolerance within ~3 months; the platform should budget for
   quarterly retraining, gated by the four triggers above.

## 9. Limitations and future work

- The contextual layer is synthetic; assumptions are documented and tested,
  but real amenity/transaction data would change coefficients.
- Prices are expressed at the 2010 Ames market level; deployment to another
  market requires local data and recalibration.
- The cheapest price decile is over-predicted — a segment-specific model or
  monotonicity constraints could help.
- Retraining is recommended by triggers but not yet automated; the natural
  next step is a scheduled retrain-evaluate-promote loop.
- Monthly stream samples are small (6–48 sales); confidence in monthly drift
  verdicts is limited by design — hence rolling windows and minimum-sample
  gates.
