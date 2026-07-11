"""Build the presentation on the official HUST 2022 (red, 4:3) template.

Reuses the template's designed cover and closing slides, fills content slides
through the branded layouts, and embeds the LaTeX formulas rendered by
build_formulas.py. Run from repo root:

    python reports/build/build_slides.py

Output: reports/hust-house-price-slides.pptx
"""

import copy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent.parent
BRAND = ROOT / "reports" / "branding"
FIG = ROOT / "reports" / "figures"
FORM = BRAND / "formulas"

HUST_RED = RGBColor(0xC0, 0x00, 0x00)
INK = RGBColor(0x3A, 0x3A, 0x3A)

TITLE = "House Price Prediction for a Real Estate Listing Platform"
SUBTITLE = ("From raw data to a monitored, deployed valuation tool\n"
            "IT5315E Business Analytics — Group Project")
TEAM = ("Đỗ Hoàng Việt · Nguyễn Minh Huyền · Nguyễn Thị Huyền Trang · "
        "Bùi Tá Cường · Nguyễn Tiến Đức")


# --------------------------------------------------------------------------
# low-level helpers
# --------------------------------------------------------------------------
def delete_slide(prs, slide):
    xml_slides = prs.slides._sldIdLst
    for sld in list(xml_slides):
        if prs.part.related_part(sld.rId) == slide.part:
            prs.part.drop_rel(sld.rId)  # else the part is written twice
            xml_slides.remove(sld)


def move_slide_to_end(prs, index):
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    xml_slides.remove(slides[index])
    xml_slides.append(slides[index])


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


def add_picture_fit(slide, path, left, top, max_w, max_h):
    """Insert a picture scaled to fit inside a box, centered horizontally."""
    from PIL import Image
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
                    run.font.color.rgb = (RGBColor(0xFF, 0xFF, 0xFF)
                                          if i == 0 else INK)
    return table


def content_slide(prs, title):
    """Branded content slide: red title bar + one content area (layout 3)."""
    slide = prs.slides.add_slide(prs.slide_layouts[3])
    set_title(slide, title)
    return slide


def two_content_slide(prs, title):
    """Branded content slide with two side-by-side areas (layout 4)."""
    slide = prs.slides.add_slide(prs.slide_layouts[4])
    set_title(slide, title)
    return slide


def body_frame(slide, ph_idx):
    return slide.placeholders[ph_idx].text_frame


# --------------------------------------------------------------------------
# deck definition
# --------------------------------------------------------------------------
def add_text(slide, left, top, width, height, lines, align=PP_ALIGN.LEFT):
    """Text box from (text, size, bold, color) tuples, one per paragraph."""
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


def build():
    prs = Presentation(BRAND / "hust-template-4x3.pptx")

    # the cover/closing artwork lives in the layouts, so sample slides can go
    for slide in list(prs.slides):
        delete_slide(prs, slide)

    # ---- 1. cover (layout 2 carries the white title-page design) ----------
    cover = prs.slides.add_slide(prs.slide_layouts[2])
    add_text(cover, Inches(0.55), Inches(1.55), Inches(6.4), Inches(2.0), [
        (TITLE, 29, True, HUST_RED)])
    add_text(cover, Inches(0.55), Inches(3.7), Inches(6.2), Inches(2.4), [
        (SUBTITLE.split("\n")[0], 15, True, INK),
        (SUBTITLE.split("\n")[1], 13, False, INK),
        ("", 8, False, INK),
        (TEAM, 12, False, INK)])

    # ---- 2. business problem ----------------------------------------------
    s = content_slide(prs, "The business problem")
    bullets(body_frame(s, 13), [
        (0, "Mispricing hurts both sides: inflated asks scare buyers away; "
            "underpricing leaves the seller's money on the table.", False),
        (0, "Agents need a defensible estimate long before a formal appraisal "
            "— and need to know how much to trust it.", False),
        (0, "Business question: given a property's characteristics and "
            "location, what is its market price — and how confident is that "
            "estimate?", True),
        (0, "Error tolerance: ~10% typical error is within negotiation "
            "margin; systematic bias beyond ~5% must trigger retraining.", False),
        (0, "Deliverable: a working valuation tool that returns an estimate "
            "with a calibrated confidence range.", False),
    ])

    # ---- 3. data strategy ---------------------------------------------------
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

    # ---- 4. synthetic credibility ------------------------------------------
    s = content_slide(prs, "Why the synthetic data can be trusted")
    bullets(body_frame(s, 13), [
        (0, "Behavioral assumptions, generated conditionally:", True),
        (1, "Pricier neighborhoods sit closer to schools (realized r = "
            "−0.60); transit access deliberately unpriced (r ≈ 0.1).", False),
        (1, "Renovation costs consistent with the real remodel-year column; "
            "days-on-market lengthens in the 2008–09 cold market.", False),
        (0, "Prices re-expressed under the synthetic market index "
            "(original Kaggle price preserved for audit):", True),
        (0, "Five seeded data-quality problems injected only pre-2010 — "
            "cleaning has real, verifiable work.", False),
        (0, "Every documented claim is enforced by automated tests; "
            "generation reproduces byte-for-byte.", False),
    ], size=15)
    add_picture_fit(s, FORM / "price_index.png",
                    Inches(1.2), Inches(5.35), Inches(7.6), Inches(1.15))

    # ---- 5. what drives price ----------------------------------------------
    s = two_content_slide(prs, "What drives price (EDA)")
    add_picture_fit(s, FIG / "03_top_price_drivers.png",
                    Inches(0.3), Inches(1.6), Inches(4.9), Inches(4.4))
    bullets(body_frame(s, 2), [
        (0, "Quality (r = 0.79) and living area (0.71) dominate.", False),
        (0, "Neighborhood is a 3.5× price lever — from $90k (MeadowV) to "
            "$313k (NridgHt) medians.", False),
        (0, "School proximity is priced in; bus access is not — an "
            "actionable platform insight.", False),
        (0, "Market moved: +5% boom, −10% crisis, 2010 rebound. "
            "A price model ages.", True),
        (0, "Price is right-skewed (1.93 → 0.12 after log), so models "
            "predict:", False),
    ], size=14)
    add_picture_fit(s, FORM / "target.png",
                    Inches(5.35), Inches(5.85), Inches(4.2), Inches(0.75))

    # ---- 6. cleaning ---------------------------------------------------------
    s = content_slide(prs, "Cleaning with before / after evidence")
    add_table(s, [
        ["Problem (diagnosed cause)", "Before", "After"],
        ["Duplicate listings (re-posted homes) — keep earliest", "12", "0"],
        ["Free-text renovation labels (Y/yes/NO/…)", "51", "0"],
        ["Days-on-market sentinel 999 → quarter-median impute", "5", "0"],
        ["Transit distance entered in metres → ÷1000", "4", "0"],
        ["Missing school distance → neighborhood median", "26", "0"],
        ['Kaggle "no such feature" NAs → explicit category', "7,480", "0"],
        ["Partial-sale outliers (Ids 524, 1299) → dropped", "2 rows", "—"],
    ], Inches(0.7), Inches(1.6), Inches(8.6), col_widths=[6, 1.2, 1.2], size=13)
    box = s.shapes.add_textbox(Inches(0.7), Inches(5.9), Inches(8.6), Inches(0.9))
    bullets(box.text_frame, [
        (0, "1,472 listings in → 1,458 out. Every fix targets a diagnosed "
            "cause; the pipeline prints this table on every run.", False),
    ], size=13)

    # ---- 7. features & multicollinearity ------------------------------------
    s = content_slide(prs, "Feature engineering & multicollinearity")
    bullets(body_frame(s, 13), [
        (0, "Derived: property age, years since remodel, total baths, "
            "renovation flag, amenity score.", False),
        (0, "Leakage discipline — only what an agent knows at valuation "
            "time:", True),
        (1, "Excluded: days-on-market (an outcome), market price index "
            "(published with a lag).", False),
        (1, "Included: interest rate (public at listing time).", False),
        (0, "One variable per concept (garage cars not garage area, r=0.88); "
            "verified with variance inflation factors:", False),
    ], size=15)
    add_picture_fit(s, FORM / "vif.png",
                    Inches(2.9), Inches(4.55), Inches(2.6), Inches(1.0))
    box = s.shapes.add_textbox(Inches(1.2), Inches(5.7), Inches(7.2), Inches(0.6))
    bullets(box.text_frame, [(0, "Max VIF = 3.9 across 16 numeric features "
                                 "(threshold 10) — stable linear baselines.", True)],
            size=14)

    # ---- 8. model comparison -------------------------------------------------
    s = content_slide(prs, "Model comparison — 5-fold cross-validation")
    add_table(s, [
        ["Model", "RMSE", "MAE", "MAPE", "R²"],
        ["Linear Regression", "$23,409", "$15,806", "9.11%", "0.914"],
        ["Ridge (best point model)", "$23,195", "$15,573", "8.99%", "0.916"],
        ["Lasso", "$23,324", "$15,670", "9.04%", "0.915"],
        ["Random Forest", "$29,509", "$18,469", "10.43%", "0.863"],
        ["LightGBM (deployed, quantile)", "$27,441", "$17,334", "9.78%", "0.882"],
    ], Inches(0.8), Inches(1.55), Inches(8.4), col_widths=[3.2, 1.2, 1.2, 1, 1], size=13)
    add_picture_fit(s, FORM / "metrics.png",
                    Inches(1.0), Inches(4.35), Inches(8.0), Inches(1.5))
    box = s.shapes.add_textbox(Inches(0.8), Inches(6.0), Inches(8.4), Inches(0.9))
    bullets(box.text_frame, [
        (0, "Ridge wins points — log-price is near-linear in the drivers. We "
            "deploy quantile LightGBM anyway: the business asks for a "
            "calibrated range, and one coherent model beats stitching two "
            "families. Trade-off reported openly.", False)], size=13)

    # ---- 9. honest uncertainty ------------------------------------------------
    s = content_slide(prs, "Honest uncertainty: quantile + conformal calibration")
    bullets(body_frame(s, 13), [
        (0, "Three LightGBM models trained on the pinball loss:", False),
    ], size=15)
    add_picture_fit(s, FORM / "pinball.png",
                    Inches(1.0), Inches(2.0), Inches(8.0), Inches(0.85))
    box = s.shapes.add_textbox(Inches(0.6), Inches(2.95), Inches(8.9), Inches(0.6))
    bullets(box.text_frame, [
        (0, "The raw p10–p90 band claimed 80% but covered only 59% of "
            "held-out prices. Conformalized quantile regression fixes it:", True),
    ], size=15)
    add_picture_fit(s, FORM / "cqr.png",
                    Inches(0.9), Inches(3.6), Inches(8.2), Inches(1.5))
    box = s.shapes.add_textbox(Inches(0.6), Inches(5.3), Inches(8.9), Inches(1.3))
    bullets(box.text_frame, [
        (0, "Verified coverage after calibration: 80.5% (target 80%).", True),
        (0, "Width behaves honestly: ≈$35k for a typical home, ≈$78k for "
            "high-value homes — the UI says when to escalate to an appraisal.",
         False),
    ], size=14)

    # ---- 10. live demo ---------------------------------------------------------
    s = content_slide(prs, "Live demo — the valuation tool")
    bullets(body_frame(s, 13), [
        (0, "https://house-price-analytics-tjpb7ntxsd6kzbapp7bymmv."
            "streamlit.app", True),
        (0, "Scenario A — typical home: NAmes, 1,500 sq ft, quality 5 "
            "→ tight range (±13%).", False),
        (0, "Scenario B — high-value home: NridgHt, 3,200 sq ft, quality 9 "
            "→ wide range + “consider an appraisal”.", False),
        (0, "Same model behind a REST API: POST /predict "
            "(FastAPI, OpenAPI docs).", False),
        (0, "Risk control: link warmed before the talk; identical local "
            "fallback ready (streamlit run app/streamlit_app.py).", False),
    ])

    # ---- 11. monitoring ---------------------------------------------------------
    s = two_content_slide(prs, "Monitoring: the model watches itself age")
    bullets(body_frame(s, 1), [
        (0, "2010 stream replayed month-by-month (rolling 3-month window) "
            "with Evidently.", False),
        (0, "Four triggers, defined before looking:", True),
        (1, "T1 input drift: >30% features drift", False),
        (1, "T2 error: RMSE >1.25× baseline", False),
        (1, "T3 bias: |mean error| >5% of median", False),
        (1, "T4 coverage: 80% range covers <65%", False),
        (0, "Verdict: retrain from Mar 2010. Bias reaches −7.9% as the "
            "rebound outruns the training window.", True),
        (0, "Input drift says things changed; error/bias monitors prove it "
            "matters.", False),
    ], size=14)
    add_picture_fit(s, FIG / "09_monitoring_timeline.png",
                    Inches(5.15), Inches(1.5), Inches(4.55), Inches(5.5))

    # ---- 12. recommendations ----------------------------------------------------
    s = two_content_slide(prs, "Recommendations & limitations")
    bullets(body_frame(s, 1), [
        (0, "For the platform:", True),
        (1, "Price on quality + location first; school proximity is the "
            "amenity that is actually priced.", False),
        (1, "Always show the range — it converts a black box into a "
            "negotiation aid.", False),
        (1, "Treat the model as perishable: it drifted beyond tolerance "
            "within ~3 months; budget quarterly retraining.", False),
    ], size=15)
    bullets(body_frame(s, 2), [
        (0, "Limitations:", True),
        (1, "Contextual layer is synthetic — documented and test-enforced, "
            "but real amenity data would shift coefficients.", False),
        (1, "Prices at 2010 Ames level; new markets need local data.", False),
        (1, "Cheapest decile over-predicted; segment model is future work.",
         False),
        (1, "Retraining recommended by triggers, not yet automated.", False),
    ], size=15)

    # ---- 13. closing (layout 12 carries the HUST-sidebar design) ---------------
    closing = prs.slides.add_slide(prs.slide_layouts[12])
    add_text(closing, Inches(4.0), Inches(2.9), Inches(5.6), Inches(1.2), [
        ("THANK YOU !", 44, True, HUST_RED)], align=PP_ALIGN.CENTER)
    add_text(closing, Inches(4.0), Inches(4.2), Inches(5.6), Inches(1.0), [
        ("Live tool: house-price-analytics-tjpb7ntxsd6kzbapp7bymmv"
         ".streamlit.app", 12, False, INK),
        ("Code: github.com/ducnt3/house-price-analytics", 12, False, INK)],
        align=PP_ALIGN.CENTER)

    out = ROOT / "reports" / "hust-house-price-slides.pptx"
    prs.save(out)
    print(f"wrote {out} ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")


if __name__ == "__main__":
    build()
