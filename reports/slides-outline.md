# Slides Outline — 12 slides, ~15 minutes + live demo

Narrative arc: problem → trustworthy data → insight → honest model →
working product → self-monitoring → recommendations. One presenter hand-off
per project role. Figures referenced from `reports/figures/`.

| # | Slide | Content | Visual | Presenter |
|---|---|---|---|---|
| 1 | Title | Project, team, live-demo QR code to the Streamlit app | QR + screenshot | Đức |
| 2 | The business problem | Mispricing costs both sides; agents need estimate + trust level *before* an appraisal. KPI: ≤10% typical error, ≤5% portfolio bias | one-line stat | Đức |
| 3 | Data strategy | Kaggle Ames base + 12 documented synthetic fields; real 2006–10 time axis anchored to actual sale dates; crisis-era macro overlay | 02_market_over_time.png | Việt |
| 4 | Why the synthetic data is credible | Data dictionary; assumptions (schools priced, transit not); injected dirt is seeded + documented + test-enforced | DATA_DICTIONARY excerpt | Việt |
| 5 | What drives price | Quality 0.79, area 0.71, school distance −0.60; neighborhood = 3.5× lever | 03_top_price_drivers.png + 05 | Minh Huyền |
| 6 | Market over time | Boom → −10% crisis → 2010 rebound; "a price model ages" — sets up monitoring | 02 (reprise, annotated) | Minh Huyền |
| 7 | Cleaning with evidence | Before/after table (12 dupes, 51 labels, unit errors, outliers); log-transform decision | cleaning console table | Việt |
| 8 | Model comparison | CV table; Ridge wins points, we ship quantile LightGBM for calibrated ranges — trade-off stated openly | comparison table | Huyền Trang |
| 9 | Honest uncertainty | Raw band covered 59% while claiming 80% → conformal calibration → 80.5% verified; width $35k typical vs $78k high-value | 08_residual_analysis.png + width table | Cường |
| 10 | **Live demo** | Value a typical home (tight range) then a mansion (wide range + "consider appraisal") ; mention API /docs | live app | Đức |
| 11 | The model watches itself | 4 pre-defined triggers; replay of 2010: retrain signal fires March; bias −7.9% by July | 09_monitoring_timeline.png | Cường |
| 12 | Recommendations & limits | Price on quality+location; show ranges; retrain quarterly. Limits: synthetic context, 2010 price level, cheap-segment bias | 3 bullets | Đức |

## Demo runbook (risk control)

1. T−10 min: open the live app once (wakes the free-tier container).
2. Backup: `streamlit run app/streamlit_app.py` on the presenter laptop —
   same model artifact, identical behavior, zero internet dependency.
3. Demo inputs prepared: NAmes / 1,500 sq ft / quality 5 (tight range) vs
   NridgHt / 3,200 sq ft / quality 9 / kitchen Ex (wide range).

## Q&A preparation — likely panel questions

Answers live in DECISIONS.md: why USD (D8) · why the time axis is real
(D11) · why the rebound is +9.5% (D12) · why ship LightGBM over Ridge (D14)
· why intervals are conformal (D5) · why days-on-market is excluded (D15) ·
what happened with Hugging Face (D3).

## Production notes

- PPTX: build from this outline (one row = one slide);
  `pandoc reports/final-report.md -o report.pdf` for the PDF (or print the
  Markdown preview to PDF).
