"""Single source of truth for paths, seeds, and project-wide constants.

Every script and notebook imports from here so that changing a path or the
random seed happens in exactly one place — a reproducibility requirement of
the course brief.
"""

from pathlib import Path

# Repo root = two levels up from this file (src/config.py -> src -> root)
ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_SYNTHETIC_DIR = ROOT_DIR / "data" / "synthetic"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "models"
MONITORING_REPORTS_DIR = ROOT_DIR / "monitoring" / "reports"

# One seed used everywhere (numpy, Faker, LightGBM, train/test splits)
RANDOM_SEED = 42

# Currency shown in the demo UI. The model is trained on Ames, Iowa prices,
# so USD is the faithful unit (team decision, see DECISIONS.md).
CURRENCY = "USD"

# Time axis: anchored to the REAL sale dates in the Ames data (YrSold/MoSold,
# Jan 2006 - Jul 2010). Synthetic macro series (interest rate, price index)
# are overlaid on this axis. All 2010 sales (Jan-Jul, ~175 homes) are held out
# as the "incoming data stream" that the monitoring module replays — the model
# never sees them during training.
TIME_AXIS_START = "2006-01"
TIME_AXIS_END = "2010-07"
MONITORING_HOLDOUT_START = "2010-01-01"
