# Data Reporting Automation — Professional FinTech Management Reporting Suite

**Automated monthly management reporting pipeline for a FinTech SaaS company.**
Ingests raw operational metrics, validates data quality, computes KPIs, and produces a full suite of professional SVG charts and a structured executive report — entirely without manual intervention.

> **Synthetic demo data only.** All figures are generated for portfolio demonstration and do not represent real business results.

---

## Overview

This pipeline takes a monthly CSV of SaaS operational metrics and produces:

- **9 professional SVG charts** optimised for web and PDF embedding
- **Executive management report** in structured Markdown
- **CSV data exports** for downstream analysis or BI tool ingestion
- Fully automated with a single `python src/reporting_automation.py` command

The pipeline is built around a clean `ReportingPipeline` class with distinct, testable steps: `load_data()` → `validate()` → `compute_kpis()` → `generate_charts()` → `write_report()`.

---

## Charts

### 1. MRR Trend with Annotations (`mrr_trend_annotated.svg`)

![MRR Trend](reports/charts/mrr_trend_annotated.svg)

Monthly Recurring Revenue grew **+30.7%** from £489k in January to £639k in December, with consistent month-on-month growth averaging +2.4%. Annotated with MoM growth rates and a year-on-year summary callout.

---

### 2. Revenue Growth Waterfall (`revenue_waterfall.svg`)

![Revenue Waterfall](reports/charts/revenue_waterfall.svg)

Waterfall chart showing monthly revenue increments from a January base of £489k. Every month shows positive increments (green), reflecting uninterrupted revenue growth throughout FY2024.

---

### 3. Monthly Revenue by Product — Stacked (`product_revenue_stacked.svg`)

![Product Revenue Stacked](reports/charts/product_revenue_stacked.svg)

Stacked bar chart showing the three product revenue streams: Analytics Suite, DataBridge API, and Compliance Module — revealing how product mix evolved through the year.

---

### 4. Regional Revenue Breakdown (`regional_breakdown.svg`)

![Regional Breakdown](reports/charts/regional_breakdown.svg)

Horizontal bar chart comparing total FY2024 revenue across four regions (UK, EU, North America, APAC), with the UK contributing the largest share at 34%.

---

### 5. Gross Margin Trend (`gross_margin_trend.svg`)

![Gross Margin](reports/charts/gross_margin_trend.svg)

Dual-axis chart plotting gross margin percentage alongside absolute gross profit. Margins expanded from 61.2% in January to 65.8% in December, reflecting operating leverage as the business scaled.

---

### 6. Churn Rate & New Customers (`churn_new_customers.svg`)

![Churn and New Customers](reports/charts/churn_new_customers.svg)

Combined chart showing monthly new customer additions (bars) against churn rate (line). Churn declined from 2.8% to 1.9% through the year while new customer volumes held steady.

---

### 7. Product Margin Comparison (`product_margin_comparison.svg`)

![Product Margins](reports/charts/product_margin_comparison.svg)

Grouped bar chart comparing gross margin percentages across the three products for each month, highlighting which products carry the highest margin profile.

---

### 8. Product × Region Revenue Heatmap (`product_region_heatmap.svg`)

![Heatmap](reports/charts/product_region_heatmap.svg)

Heatmap of total FY2024 revenue by product and region, making it easy to spot the highest-value combinations at a glance.

---

### 9. KPI Dashboard (`kpi_dashboard.svg`)

![KPI Dashboard](reports/charts/kpi_dashboard.svg)

Single-page KPI summary card displaying the six headline metrics: Total Revenue, MRR (Dec), Gross Margin, New Customers, Avg Churn Rate, and Customer LTV.

---

## Executive Report

The pipeline produces a structured Markdown report at `reports/monthly_management_report.md` containing:

- Executive summary with headline KPIs
- Revenue performance narrative
- Product and regional breakdown
- Margin and efficiency analysis
- Customer metrics (acquisition, churn, LTV)
- Data quality summary

---

## Usage

```bash
# Install dependencies
pip install pandas matplotlib numpy

# Run full pipeline
python src/reporting_automation.py

# Generate charts only
python src/generate_charts.py
```

Outputs are written to:
- `reports/charts/*.svg` — all nine charts
- `reports/monthly_management_report.md` — executive report
- `data/processed/` — cleaned and enriched CSVs

---

## Project Structure

```
data-reporting-automation/
├── data/
│   └── monthly_saas_metrics.csv    # Raw input data (synthetic)
├── src/
│   ├── reporting_automation.py     # Main pipeline
│   └── generate_charts.py          # Chart generation module
├── reports/
│   ├── monthly_management_report.md
│   └── charts/
│       ├── mrr_trend_annotated.svg
│       ├── revenue_waterfall.svg
│       ├── product_revenue_stacked.svg
│       ├── regional_breakdown.svg
│       ├── gross_margin_trend.svg
│       ├── churn_new_customers.svg
│       ├── product_margin_comparison.svg
│       ├── product_region_heatmap.svg
│       └── kpi_dashboard.svg
└── README.md
```

---

## Tech Stack

| Tool | Purpose |
|------|--------|
| Python 3.10+ | Core language |
| pandas | Data ingestion, validation, KPI computation |
| matplotlib | Chart rendering (SVG output) |
| numpy | Numerical helpers |

---

*Generated by the Data Reporting Automation pipeline. Synthetic data only.*
