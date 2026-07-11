"""Build the presentation on the official HUST 2022 (red, 4:3) template.

Deletes the template's sample slides (the cover/closing artwork lives in the
layouts), then fills ~21 content slides through the branded layouts, embedding
the LaTeX formulas rendered by build_formulas.py and every analysis figure.
Run from repo root:

    python reports/build/build_slides.py

Output: reports/hust-house-price-slides.pptx
"""

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent.parent
BRAND = ROOT / "reports" / "branding"
FIG = ROOT / "reports" / "figures"
FORM = BRAND / "formulas"

HUST_RED = RGBColor(0xC0, 0x00, 0x00)
INK = RGBColor(0x2B, 0x2B, 0x2B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

TITLE = "House Price Prediction for a Real Estate Listing Platform"
SUBTITLE = "From raw data to a monitored, deployed valuation tool"
COURSE = "IT5315E Business Analytics — Group Project"
TEAM = [
    ("Đỗ Hoàng Việt", "20252744M"),
    ("Nguyễn Minh Huyền", "20252007M"),
    ("Nguyễn Thị Huyền Trang", "20251322M"),
    ("Bùi Tá Cường", "20242430M"),
    ("Nguyễn Tiến Đức", "20252076M"),
]
APP_URL = "house-price-analytics-tjpb7ntxsd6kzbapp7bymmv.streamlit.app"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def delete_slide(prs, slide):
    xml_slides = prs.slides._sldIdLst
    for sld in list(xml_slides):
        if prs.part.related_part(sld.rId) == slide.part:
            prs.part.drop_rel(sld.rId)  # else the part is written twice
            xml_slides.remove(sld)


def set_title(slide, text, size=26):
    ph = slide.placeholders[0]
    ph.text = text
    for run in ph.text_frame.paragraphs[0].runs:
        run.font.size = Pt(size)
        run.font.bold = True


def bullets(tf, items, size=16, space_after=8):
    """Fill a text frame with (level, text, bold) bullet tuples."""
    tf.word_wrap = True
    for i, (level, text, bold) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.level = level
        p.space_after = Pt(space_after)
        for run in p.runs:
            run.font.size = Pt(size - 2 * level)
            run.font.bold = bold
            run.font.color.rgb = INK


def add_text(slide, left, top, width, height, lines, align=PP_ALIGN.LEFT):
    """Plain text box from (text, size, bold, color) tuples."""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, (text, size, bold, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.alignment = align
        for run in p.runs:
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = color
    return box


def add_picture_fit(slide, path, left, top, max_w, max_h):
    """Insert a picture scaled to fit inside a box, centered in it."""
    w, h = Image.open(path).size
    scale = min(max_w / w, max_h / h)
    pw, ph = int(w * scale), int(h * scale)
    slide.shapes.add_picture(str(path), left + (max_w - pw) // 2,
                             top + (max_h - ph) // 2, pw, ph)


def add_table(slide, rows, left, top, width, col_widths=None, size=13):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), left, top,
                                   width, Emu(1))
    table = shape.table
    if col_widths:
        total = sum(col_widths)
        for j, cw in enumerate(col_widths):
            table.columns[j].width = int(width * cw / total)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            if i == 0:  # header row in HUST red, not the Office default blue
                cell.fill.solid()
                cell.fill.fore_color.rgb = HUST_RED
            cell.text = str(val)
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER if j and i else PP_ALIGN.LEFT
                for run in p.runs:
                    run.font.size = Pt(size)
                    run.font.bold = i == 0
                    run.font.color.rgb = WHITE if i == 0 else INK
    return table


def content_slide(prs, title):
    """Branded slide: red title bar + one content placeholder (layout 3)."""
    slide = prs.slides.add_slide(prs.slide_layouts[3])
    set_title(slide, title)
    return slide


def two_content_slide(prs, title):
    """Branded slide with two side-by-side placeholders (layout 4)."""
    slide = prs.slides.add_slide(prs.slide_layouts[4])
    set_title(slide, title)
    return slide


def body_frame(slide, ph_idx):
    return slide.placeholders[ph_idx].text_frame


def figure_slide(prs, title, fig_path, notes, fig_box=None, note_size=14):
    """Full-width figure with takeaway bullets underneath (or beside)."""
    s = content_slide(prs, title)
    left, top, w, h = fig_box or (Inches(0.9), Inches(1.45), Inches(8.2), Inches(4.1))
    add_picture_fit(s, fig_path, left, top, w, h)
    box = s.shapes.add_textbox(Inches(0.7), top + h + Inches(0.15),
                               Inches(8.6), Inches(1.3))
    bullets(box.text_frame, notes, size=note_size, space_after=4)
    return s


# --------------------------------------------------------------------------
# deck
# --------------------------------------------------------------------------
def build():
    prs = Presentation(BRAND / "hust-template-4x3.pptx")
    for slide in list(prs.slides):
        delete_slide(prs, slide)

    # ---- 1. cover (layout 2 = white title-page artwork) --------------------
    cover = prs.slides.add_slide(prs.slide_layouts[2])
    add_text(cover, Inches(0.55), Inches(1.25), Inches(6.4), Inches(1.9), [
        (TITLE, 28, True, HUST_RED)])
    add_text(cover, Inches(0.55), Inches(3.15), Inches(6.2), Inches(0.8), [
        (SUBTITLE, 15, True, INK),
        (COURSE, 13, False, INK)])
    team_lines = [(f"{name}  —  {sid}", 12, False, INK) for name, sid in TEAM]
    add_text(cover, Inches(0.55), Inches(4.15), Inches(6.0), Inches(2.2),
             team_lines)

    # ---- 2. agenda ----------------------------------------------------------
    s = two_content_slide(prs, "Agenda")
    bullets(body_frame(s, 1), [
        (0, "1. The business problem", False),
        (0, "2. Data: real base + synthetic context", False),
        (0, "3. Exploratory analysis — what drives price", False),
        (0, "4. Data cleaning with evidence", False),
        (0, "5. Features & multicollinearity", False),
    ], size=16)
    bullets(body_frame(s, 2), [
        (0, "6. Model comparison (5-fold CV)", False),
        (0, "7. Calibrated confidence intervals", False),
        (0, "8. Live demo — the valuation tool", False),
        (0, "9. Monitoring & retraining triggers", False),
        (0, "10. Recommendations & limitations", False),
    ], size=16)

    # ---- 3. business problem ------------------------------------------------
    s = content_slide(prs, "The business problem")
    bullets(body_frame(s, 13), [
        (0, "Mispricing hurts both sides: inflated asks scare buyers away; "
            "underpricing leaves the seller's money on the table.", False),
        (0, "Agents need a defensible estimate long before a formal appraisal "
            "— and need to know how much to trust it.", False),
        (0, "Business question: given a property's characteristics and "
            "location, what is its market price — and how confident is that "
            "estimate?", True),
        (0, "$180k ± $18k → list with confidence.  $180k ± $70k → order an "
            "appraisal first. The range changes the decision.", False),
        (0, "KPIs: typical error ≤ ~10% (negotiation margin); calibrated "
            "uncertainty; systematic bias ≤ 5%; a working deployment with "
            "monitoring.", False),
    ], size=15)

    # ---- 4. data strategy ----------------------------------------------------
    s = two_content_slide(prs, "Data: real base + documented synthetic context")
    bullets(body_frame(s, 1), [
        (0, "Base: Kaggle Ames — 1,460 sales, 80 attributes.", False),
        (0, "Extension: 12 synthetic contextual fields, each documented "
            "(type, unit, range, assumption).", False),
        (0, "Time axis anchored to the data's real sale dates: "
            "Jan 2006 – Jul 2010.", True),
        (0, "Macro overlay: interest-rate series; price index with boom, "
            "−10% crisis, +9.5% rebound in 2010.", False),
        (0, "All 175 sales of 2010 held out as the incoming stream for "
            "monitoring.", False),
    ], size=15)
    add_picture_fit(s, FIG / "02_market_over_time.png",
                    Inches(5.1), Inches(1.5), Inches(4.6), Inches(5.4))

    # ---- 5. synthetic credibility ---------------------------------------------
    s = content_slide(prs, "Why the synthetic data can be trusted")
    bullets(body_frame(s, 13), [
        (0, "Behavioral assumptions, generated conditionally:", True),
        (1, "Pricier neighborhoods sit closer to schools (realized r = "
            "−0.60); transit access deliberately unpriced (r ≈ 0.1).", False),
        (1, "Renovation costs consistent with the real remodel-year column; "
            "days-on-market lengthens in the 2008–09 cold market.", False),
        (0, "Prices re-expressed under the synthetic market index "
            "(original Kaggle price preserved for audit):", True),
    ], size=15)
    add_picture_fit(s, FORM / "price_index.png",
                    Inches(0.9), Inches(3.85), Inches(8.2), Inches(0.85))
    box = s.shapes.add_textbox(Inches(0.65), Inches(4.9), Inches(8.7), Inches(1.7))
    bullets(box.text_frame, [
        (0, "Every documented claim is enforced by automated tests; "
            "generation reproduces byte-for-byte from a fixed seed.", False),
        (0, "The +9.5% rebound lives only inside the monitoring stream — the "
            "designed, explainable drift signal.", True),
    ], size=15, space_after=4)

    # ---- 6. injected imperfections ---------------------------------------------
    s = content_slide(prs, "Designed imperfections — so cleaning is real work")
    add_table(s, [
        ["Field", "Injected problem", "Rate"],
        ["dist_school_km", "Missing — blank at listing entry", "2% (26 rows)"],
        ["renovated", "Free-text labels: Y / yes / YES / N / no / NO", "4% (51)"],
        ["days_on_market", 'Legacy sentinel 999 = "unknown"', "0.4% (5)"],
        ["dist_transit_km", "Entered in metres instead of km", "0.3% (4)"],
        ["whole row", "Home re-posted under a new listing id", "12 rows"],
    ], Inches(0.7), Inches(1.6), Inches(8.6), col_widths=[2.2, 5.2, 1.6], size=13)
    box = s.shapes.add_textbox(Inches(0.7), Inches(4.6), Inches(8.6), Inches(1.7))
    bullets(box.text_frame, [
        (0, "Injected only into synthetic fields, only before 2010 — the "
            "monitoring stream stays clean, so drift is never confused with "
            "dirt.", False),
        (0, "Ground truth is known → cleaning quality can be proven, not "
            "assumed.", True),
    ], size=14, space_after=4)

    # ---- 7. EDA: target -----------------------------------------------------------
    s = figure_slide(prs, "EDA 1/4 — the target is right-skewed",
                     FIG / "01_target_distribution.png", [
        (0, "Median $162.9k vs mean $181.4k, tail to $779k; skew 1.93 → 0.12 "
            "after log. All models predict:", False)],
        fig_box=(Inches(1.0), Inches(1.5), Inches(8.0), Inches(3.3)))
    add_picture_fit(s, FORM / "target.png",
                    Inches(2.9), Inches(5.75), Inches(4.2), Inches(0.8))

    # ---- 8. EDA: drivers ------------------------------------------------------------
    s = two_content_slide(prs, "EDA 2/4 — what drives price")
    add_picture_fit(s, FIG / "03_top_price_drivers.png",
                    Inches(0.3), Inches(1.6), Inches(4.9), Inches(4.4))
    bullets(body_frame(s, 2), [
        (0, "Quality (r = 0.79) and living area (0.71) dominate — median "
            "price quadruples from quality 3 ($85k) to 9 ($346k).", False),
        (0, "Synthetic amenities behave as designed: school −0.60, hospital "
            "−0.58, transit ≈ +0.1.", False),
        (0, "renovation_cost (0.69) is partly derivative — generated from "
            "area × quality; flagged for the VIF check.", False),
    ], size=14)

    # ---- 9. EDA: outliers -----------------------------------------------------------
    figure_slide(prs, "EDA 3/4 — quality, size, and two notorious outliers",
                 FIG / "04_quality_area_outliers.png", [
        (0, "Two homes > 4,000 sq ft sold far below trend (Ids 524, 1299) — "
            "known Ames partial sales, dropped in cleaning with "
            "justification.", False)])

    # ---- 10. EDA: location ------------------------------------------------------------
    s = content_slide(prs, "EDA 4/4 — location is a 3.5× price lever")
    add_picture_fit(s, FIG / "05_neighborhood_prices.png",
                    Inches(0.5), Inches(1.45), Inches(9.0), Inches(2.5))
    add_picture_fit(s, FIG / "06_amenity_distances.png",
                    Inches(0.5), Inches(4.05), Inches(9.0), Inches(2.1))
    box = s.shapes.add_textbox(Inches(0.7), Inches(6.25), Inches(8.6), Inches(0.7))
    bullets(box.text_frame, [
        (0, "Medians $90k (MeadowV) → $313k (NridgHt). School proximity is "
            "priced in; bus access is not — an actionable platform insight.",
         True)], size=13)

    # ---- 11. multicollinearity ----------------------------------------------------------
    s = two_content_slide(prs, "Redundant variables — mapped, then pruned")
    add_picture_fit(s, FIG / "07_correlation_heatmap.png",
                    Inches(0.25), Inches(1.5), Inches(5.2), Inches(5.2))
    bullets(body_frame(s, 2), [
        (0, "Four pairs above |r| = 0.8: garage cars/area (0.88), rooms/area "
            "(0.83), 1st-floor/basement (0.82), build/garage year (0.83).",
         False),
        (0, "Kept one variable per concept; verified with variance "
            "inflation:", False),
    ], size=14)
    add_picture_fit(s, FORM / "vif.png",
                    Inches(6.1), Inches(3.7), Inches(2.6), Inches(1.0))
    box = s.shapes.add_textbox(Inches(5.5), Inches(4.9), Inches(4.1), Inches(1.4))
    bullets(box.text_frame, [
        (0, "Max VIF = 3.9 across 16 numeric features (threshold 10) — "
            "stable, interpretable linear baselines.", True)], size=14)

    # ---- 12. cleaning ---------------------------------------------------------------------
    s = content_slide(prs, "Cleaning with before / after evidence")
    add_table(s, [
        ["Problem (diagnosed cause)", "Before", "After"],
        ["Duplicate listings (re-posted homes) — keep earliest", "12", "0"],
        ["Free-text renovation labels (Y/yes/NO/…)", "51", "0"],
        ["Days-on-market sentinel 999 → quarter-median impute", "5", "0"],
        ["Transit distance entered in metres → ÷1000", "4", "0"],
        ["Missing school distance → neighborhood median", "26", "0"],
        ['Kaggle "no such feature" NAs → explicit category', "7,480", "0"],
        ["LotFrontage → neighborhood median", "259", "0"],
        ["Partial-sale outliers (Ids 524, 1299) → dropped", "2 rows", "—"],
    ], Inches(0.7), Inches(1.55), Inches(8.6), col_widths=[6, 1.2, 1.2], size=12)
    box = s.shapes.add_textbox(Inches(0.7), Inches(5.95), Inches(8.6), Inches(0.9))
    bullets(box.text_frame, [
        (0, "1,472 listings in → 1,458 out. Every fix targets a diagnosed "
            "cause; the pipeline prints this table on every run.", False),
    ], size=13)

    # ---- 13. features & leakage -----------------------------------------------------------
    s = content_slide(prs, "Feature engineering & leakage discipline")
    bullets(body_frame(s, 13), [
        (0, "Derived: property age, years since remodel, total baths, "
            "renovation flag & cost, amenity score, listing month.", False),
        (0, "Only what an agent knows at valuation time:", True),
        (1, "Excluded: days-on-market — an outcome of the listing, unknown "
            "on pricing day.", False),
        (1, "Excluded: market price index — published with a lag; feeding "
            "the current value would be look-ahead leakage (and would let "
            "the model “see” the 2010 rebound).", False),
        (1, "Included: interest rate — public on listing day.", False),
        (0, "Final feature contract: 16 numeric + 6 categorical variables.",
         True),
    ], size=15)

    # ---- 14. model comparison ----------------------------------------------------------------
    s = content_slide(prs, "Model comparison — 5-fold cross-validation")
    add_table(s, [
        ["Model", "RMSE", "MAE", "MAPE", "R²"],
        ["Linear Regression", "$23,409", "$15,806", "9.11%", "0.914"],
        ["Ridge (best point model)", "$23,195", "$15,573", "8.99%", "0.916"],
        ["Lasso", "$23,324", "$15,670", "9.04%", "0.915"],
        ["Random Forest", "$29,509", "$18,469", "10.43%", "0.863"],
        ["LightGBM (deployed, quantile)", "$27,441", "$17,334", "9.78%", "0.882"],
    ], Inches(0.8), Inches(1.5), Inches(8.4), col_widths=[3.2, 1.2, 1.2, 1, 1], size=13)
    add_picture_fit(s, FORM / "metrics_errors.png",
                    Inches(1.3), Inches(4.25), Inches(7.4), Inches(0.95))
    add_picture_fit(s, FORM / "metrics_relative.png",
                    Inches(1.3), Inches(5.25), Inches(7.4), Inches(0.95))
    box = s.shapes.add_textbox(Inches(0.7), Inches(6.35), Inches(8.6), Inches(0.7))
    bullets(box.text_frame, [
        (0, "Log-price is near-linear in the drivers and n ≈ 1,300 favors "
            "low-variance models — Ridge wins the point contest.", False)],
        size=12)

    # ---- 15. residuals --------------------------------------------------------------------------
    figure_slide(prs, "Residual analysis — where the model is honest, and not",
                 FIG / "08_residual_analysis.png", [
        (0, "No trend vs fitted values; deciles 2–9 unbiased.", False),
        (0, "Cheapest decile over-predicted (+13%), priciest slightly under "
            "(−4.7%) — classic shrinkage; flagged as a limitation and "
            "covered by wider intervals exactly there.", False)],
        fig_box=(Inches(0.7), Inches(1.5), Inches(8.6), Inches(3.6)),
        note_size=13)

    # ---- 16. why quantile model ships ------------------------------------------------------------
    s = content_slide(prs, "Model choice: accuracy is not the deliverable")
    bullets(body_frame(s, 13), [
        (0, "The business asks for a per-home confidence range, not just a "
            "number.", True),
        (0, "Deployed: three LightGBM models (p10 / p50 / p90) trained on "
            "the pinball loss — feature-dependent intervals natively:", False),
    ], size=15)
    add_picture_fit(s, FORM / "pinball.png",
                    Inches(0.8), Inches(3.0), Inches(8.4), Inches(0.85))
    box = s.shapes.add_textbox(Inches(0.65), Inches(4.1), Inches(8.7), Inches(2.3))
    bullets(box.text_frame, [
        (0, "One coherent model family — no stitching a Ridge point onto "
            "someone else's interval (mismatched band, two failure modes).",
         False),
        (0, "Cost: 9.78% vs 8.99% MAPE — immaterial against the negotiation-"
            "margin KPI; the comparison is reported, not hidden.", False),
    ], size=15, space_after=6)

    # ---- 17. conformal calibration ------------------------------------------------------------------
    s = content_slide(prs, "The naive band lies — conformal calibration fixes it")
    box = s.shapes.add_textbox(Inches(0.65), Inches(1.45), Inches(8.7), Inches(0.8))
    bullets(box.text_frame, [
        (0, "On 257 held-out sales, the raw p10–p90 band claimed 80% but "
            "covered only 59.1%. CQR measures the shortfall…", True)], size=15)
    add_picture_fit(s, FORM / "cqr_score.png",
                    Inches(1.3), Inches(2.45), Inches(7.4), Inches(0.8))
    box = s.shapes.add_textbox(Inches(0.65), Inches(3.45), Inches(8.7), Inches(0.55))
    bullets(box.text_frame, [
        (0, "…and widens the band by the empirical quantile of the scores:",
         False)], size=15)
    add_picture_fit(s, FORM / "cqr_interval.png",
                    Inches(0.9), Inches(4.05), Inches(8.2), Inches(0.85))
    box = s.shapes.add_textbox(Inches(0.65), Inches(5.1), Inches(8.7), Inches(1.6))
    bullets(box.text_frame, [
        (0, "Verified coverage after calibration: 80.5% (target 80%).", True),
        (0, "Width scales honestly: ≈$35k typical · ≈$41k mid · ≈$78k "
            "high-value tercile — wide range ⇒ “consider an appraisal”.",
         False),
    ], size=15, space_after=6)

    # ---- 18. live demo ----------------------------------------------------------------------------------
    s = two_content_slide(prs, "Live demo — the valuation tool")
    bullets(body_frame(s, 1), [
        (0, APP_URL, True),
        (0, "Scenario A — typical: NAmes, 1,500 sq ft, quality 5 → tight "
            "range (±13%).", False),
        (0, "Scenario B — high-value: NridgHt, 3,200 sq ft, quality 9 → "
            "wide range + appraisal advice.", False),
        (0, "Same model behind a REST API: POST /predict (FastAPI, OpenAPI "
            "docs).", False),
        (0, "Risk control: link warmed before the talk; identical local "
            "fallback ready.", False),
    ], size=14)
    add_picture_fit(s, BRAND / "app_screenshot.png",
                    Inches(4.9), Inches(1.6), Inches(4.85), Inches(5.2))

    # ---- 19. monitoring design ----------------------------------------------------------------------------
    s = content_slide(prs, "Monitoring design — four triggers, fixed in advance")
    add_table(s, [
        ["Trigger", "Definition", "Why it matters"],
        ["T1  Data drift", "> 30% of features drift (Evidently, ≥40-row window)",
         "The world changed"],
        ["T2  Performance", "Rolling RMSE > 1.25 × baseline ($24.4k)",
         "Errors grew materially"],
        ["T3  Systematic bias", "|mean error| > 5% of median price",
         "One-directional mispricing distorts the platform"],
        ["T4  Interval health", "80% range covers < 65%",
         "The confidence promise is breaking"],
    ], Inches(0.55), Inches(1.6), Inches(8.9), col_widths=[1.9, 3.6, 3.0], size=12)
    box = s.shapes.add_textbox(Inches(0.7), Inches(4.75), Inches(8.6), Inches(1.6))
    bullets(box.text_frame, [
        (0, "Thresholds committed before replaying the stream — no tuning "
            "alerts until they fire.", True),
        (0, "Rolling 3-month windows: single months (6–48 sales) are too "
            "small — a 10-row window flags every feature as drifted "
            "(verified noise).", False),
    ], size=14, space_after=6)

    # ---- 20. monitoring results ------------------------------------------------------------------------------
    s = two_content_slide(prs, "2010 replay: the model ages — and says so")
    bullets(body_frame(s, 1), [
        (0, "Jan–Feb: healthy (errors below baseline, coverage on target).",
         False),
        (0, "March: RMSE spike + drift over threshold → first retrain "
            "signal.", True),
        (0, "Apr–Jul: bias marches −0.4% → −7.9% as the rebound outruns the "
            "training window; coverage sags to ~73%.", False),
        (0, "Verdict: retrain from March 2010.", True),
        (0, "Lesson: input drift says things changed; error & bias monitors "
            "prove it matters.", False),
    ], size=14)
    add_picture_fit(s, FIG / "09_monitoring_timeline.png",
                    Inches(5.15), Inches(1.5), Inches(4.55), Inches(5.5))

    # ---- 21. recommendations -------------------------------------------------------------------------------------
    s = two_content_slide(prs, "Recommendations & limitations")
    bullets(body_frame(s, 1), [
        (0, "For the platform:", True),
        (1, "Price on quality + location first; school proximity is the "
            "amenity actually priced.", False),
        (1, "Always show the range — it turns a black box into a "
            "negotiation aid.", False),
        (1, "Treat the model as perishable: drifted beyond tolerance in ~3 "
            "months; budget quarterly retraining.", False),
        (1, "Route wide-interval homes to appraisal as a premium service.",
         False),
    ], size=14)
    bullets(body_frame(s, 2), [
        (0, "Limitations:", True),
        (1, "Contextual layer is synthetic — documented and test-enforced, "
            "but real data would shift coefficients.", False),
        (1, "Prices at the 2010 Ames level; new markets need local data.",
         False),
        (1, "Cheapest decile over-predicted; segment model is future work.",
         False),
        (1, "Retraining recommended by triggers, not yet automated.", False),
    ], size=14)

    # ---- 22. closing -----------------------------------------------------------------------------------------------
    closing = prs.slides.add_slide(prs.slide_layouts[12])
    add_text(closing, Inches(4.0), Inches(2.9), Inches(5.6), Inches(1.2), [
        ("THANK YOU !", 44, True, HUST_RED)], align=PP_ALIGN.CENTER)
    add_text(closing, Inches(4.0), Inches(4.2), Inches(5.6), Inches(1.0), [
        (f"Live tool: {APP_URL}", 12, False, INK),
        ("Code: github.com/ducnt3/house-price-analytics", 12, False, INK)],
        align=PP_ALIGN.CENTER)

    out = ROOT / "reports" / "hust-house-price-slides.pptx"
    prs.save(out)
    print(f"wrote {out} ({len(prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    build()
