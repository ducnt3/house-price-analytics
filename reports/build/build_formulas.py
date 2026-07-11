"""Render the project's LaTeX formulas to transparent PNGs for the slides.

The report renders the same LaTeX via KaTeX; PowerPoint has no native LaTeX,
so slides embed these images. Run: python reports/build/build_formulas.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Computer Modern — the classic LaTeX typeface — instead of the DejaVu default,
# so slide formulas look properly typeset
matplotlib.rcParams["mathtext.fontset"] = "cm"

OUT = Path(__file__).resolve().parent.parent / "branding" / "formulas"
INK = "#2b2b2b"

FORMULAS = {
    # modeling target
    "target": r"$y \;=\; \log\left(1 + \mathrm{SalePrice}\right)$",
    # evaluation metrics (one line per image so nothing collides)
    "metrics_errors": (
        r"$\mathrm{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n}\left(y_i - \hat{y}_i\right)^2}"
        r"\qquad \mathrm{MAE} = \frac{1}{n}\sum_{i=1}^{n}\left|y_i - \hat{y}_i\right|$"
    ),
    "metrics_relative": (
        r"$\mathrm{MAPE} = \frac{100\%}{n}\sum_{i=1}^{n}\left|\frac{y_i - \hat{y}_i}{y_i}\right|"
        r"\qquad R^2 = 1 - \frac{\sum_i (y_i-\hat{y}_i)^2}{\sum_i (y_i-\bar{y})^2}$"
    ),
    # quantile (pinball) loss used by the LightGBM quantile objective
    "pinball": (
        r"$\mathcal{L}_{\alpha}(y,\hat{y}) \;=\;"
        r"\mathrm{max}\left(\alpha\,(y-\hat{y}),\;(\alpha-1)\,(y-\hat{y})\right),"
        r"\quad \alpha \in \{0.10,\,0.50,\,0.90\}$"
    ),
    # conformalized quantile regression (Romano et al., 2019)
    "cqr_score": (
        r"$E_i \;=\; \mathrm{max}\left(\hat{q}_{0.10}(x_i) - y_i,\;"
        r" y_i - \hat{q}_{0.90}(x_i)\right)$"
    ),
    "cqr_interval": (
        r"$\hat{C}(x) \;=\; \left[\hat{q}_{0.10}(x) - Q_{1-\alpha}(E),\;"
        r" \hat{q}_{0.90}(x) + Q_{1-\alpha}(E)\right],\quad 1-\alpha = 0.80$"
    ),
    # variance inflation factor
    "vif": r"$\mathrm{VIF}_j \;=\; \frac{1}{1 - R_j^{\,2}}$",
    # price re-expression under the synthetic market index
    "price_index": (
        r"$\mathrm{sale\_price}_i \;=\; \mathrm{SalePrice}_i \times"
        r" \frac{I(m_i)}{\bar{I}} \times \varepsilon_i,"
        r"\quad \varepsilon_i \sim \mathrm{LogNormal}(0,\,0.02)$"
    ),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, tex in FORMULAS.items():
        lines = tex.split("\n")
        fig = plt.figure(figsize=(10, 0.9 * len(lines)))
        for k, line in enumerate(lines):
            fig.text(0.5, 1 - (k + 0.5) / len(lines), line, ha="center",
                     va="center", fontsize=21, color=INK)
        fig.savefig(OUT / f"{name}.png", dpi=300, transparent=True,
                    bbox_inches="tight", pad_inches=0.05)
        plt.close(fig)
        print(f"rendered {name}.png")


if __name__ == "__main__":
    main()
