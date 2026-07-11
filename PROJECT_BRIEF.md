# Business Analytics — Group Project Announcement

## House Price Prediction for a Real Estate Listing Platform
*An end-to-end analytics project: from raw data to a monitored, deployed model.*

| | |
|---|---|
| **Course** | Business Analytics |
| **Project type** | Group project (4–5 students per team) |
| **Domain** | Real Estate — Property Valuation |
| **Deployment target** | Cloud free tier (e.g. Render, Hugging Face Spaces, Streamlit Community Cloud) |
| **Coding requirement** | All code must be written by team members (no no-code / AutoML platforms) |

---

## 1. Project overview

Real estate listing platforms and buyers alike need a fast, defensible estimate of a property's fair market value — far ahead of a formal appraisal. An inaccurate estimate either scares away serious buyers with an inflated asking price or leaves money on the table for the seller. This project asks each team to act as the valuation-analytics function of a real estate platform and answer a concrete business question:

> **"Given a property's characteristics and location, what is its estimated market price, and how confident is that estimate?"**

Teams will build a regression model that predicts the sale price of a property from structural, locational, and condition-related features. The model will be engineered, deployed as a working application, and monitored after deployment — mirroring the full lifecycle of an analytics product in industry.

---

## 2. Data sources

Teams must combine the following two data sources:

- **Kaggle dataset (required base):** "House Prices — Advanced Regression Techniques" — kaggle.com/competitions/house-prices-advanced-regression-techniques. Provides structural attributes (area, number of rooms, age) and historical sale prices for homes in Ames, Iowa.
- **Synthetic data (required extension):** Each team must generate additional contextual data using Python (e.g. the Faker library plus custom business logic) — neighborhood amenity scores (distance to school/hospital/transit), renovation history, days-on-market, and macro indicators such as a local interest-rate or price-index trend over time.

This combination ensures the project is not a simple "download-and-train" exercise: teams must justify the realism of the contextual features they generate and document the simulation logic rigorously.

**Data Dictionary requirement:** Every synthetically generated field must be documented in a data dictionary specifying column name, data type, unit, valid range, and the generation logic or business assumption used.

---

## 3. Project structure (8 modules)

Organized into eight modules, suitable for an 8-week timeline (adjustable to the course schedule).

### Module 1 — Business Understanding & Data Generation
- Define the business problem and key KPIs (prediction error tolerance, business cost of over/under-valuation)
- Generate supplementary contextual property/neighborhood data in Python
- Produce a complete data dictionary

### Module 2 — Exploratory Data Analysis (EDA)
- Analyze distributions, outliers, and correlations between property attributes and sale price
- Compare price patterns across location, property type, and age
- Visualize relationships (e.g. price vs. area, price vs. distance to amenities) and check for multicollinearity

### Module 3 — Data Cleaning
- Handle missing values, duplicates, and inconsistent categorical labels (e.g. property type naming)
- Treat outliers (e.g. implausible area or price values, data-entry errors)
- Document all cleaning decisions with before/after comparisons

### Module 4 — Feature Engineering
- Construct derived features (price per square meter, property age, amenity-proximity score, renovation flag)
- Encode categorical variables, scale numerical features, and address skewness in price (e.g. log transform)
- Perform feature selection and check for multicollinearity (e.g. VIF)

### Module 5 — Model Development
- Train and compare regressors: Linear/Ridge/Lasso Regression, Random Forest, XGBoost / LightGBM
- Evaluate with regression metrics: RMSE, MAE, MAPE, and R²; validate with k-fold cross-validation
- Analyze residuals to check model assumptions and identify systematic under/over-prediction

### Module 6 — Model Deployment
- Package the model as an API (FastAPI or Flask) that returns a price estimate with a confidence range
- Build a demo interface (Streamlit) simulating a property-valuation tool for agents or buyers
- Deploy to a cloud free tier (Render, Hugging Face Spaces, or equivalent)

### Module 7 — Model Monitoring
- Track data drift by comparing incoming listing data distributions to training data
- Monitor rolling prediction error (RMSE/MAE) over time as new sales data arrives
- Build a simple monitoring dashboard (e.g. using the open-source Evidently library) and define retraining triggers

### Module 8 — Final Report & Presentation
- Translate findings into pricing-strategy recommendations and highlight key value drivers
- Discuss limitations and future improvements
- Present to the class with a live or recorded demo

---

## 4. Deliverables

| Deliverable | Format |
|---|---|
| Source code (notebooks/scripts) | GitHub repository |
| Data dictionary | Excel or Markdown file |
| Deployed API + valuation tool demo | Live link (Render / Hugging Face Spaces / Streamlit Cloud) |
| Monitoring dashboard or report | Notebook or Evidently report |
| Final report and slides | PDF and PPTX |

---

## 5. Suggested team roles (4–5 members)

| Role | Responsibilities |
|---|---|
| Data Engineer | Synthetic contextual data generation, data dictionary, data cleaning |
| Data Analyst | Exploratory data analysis and visualization of price drivers |
| ML Engineer — Modeling | Feature engineering and regression model development |
| ML Engineer — Evaluation | Cross-validation, residual analysis, and error-metric interpretation |
| MLOps Lead | Deployment and monitoring (may be combined with another role for 4-person teams) |

---

## 6. Evaluation focus

Grading emphasizes the rigor and clarity of each stage, rather than model accuracy alone:

- Quality and realism of synthetic contextual data, supported by a complete data dictionary
- Depth of EDA and clarity of insights communicated through visualization
- Soundness of cleaning and feature engineering decisions, with clear documentation
- Correct use of cross-validation and appropriate regression metrics (RMSE, MAE, MAPE, R²)
- A working, accessible deployment (live link required)
- A functioning monitoring component with defined drift/performance triggers
- Originality of code — all code must be authored by team members

---

## 7. Submission logistics

Instructors insert specific dates for each milestone:

1. Team formation and topic confirmation — [insert date]
2. Module 1–3 checkpoint (data + EDA + cleaning) — [insert date]
3. Module 4–5 checkpoint (features + models) — [insert date]
4. Module 6–7 checkpoint (deployment + monitoring) — [insert date]
5. Final submission and presentation — [insert date]

Questions about scope, data sources, or deployment options should be directed to the course instructor.
