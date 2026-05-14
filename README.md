# Data Reporting Automation Pipeline

**Automated monthly management reporting for a FinTech SaaS business | Python · pandas · matplotlib**

> **Dataset:** All data is entirely synthetic and used for portfolio demonstration purposes only. It does not represent real business results or financial advice.

---

## Overview

This project automates the end-to-end monthly reporting workflow for a simulated FinTech B2B SaaS company with three products and three regional markets. It ingests raw monthly metrics, runs data validation checks, computes KPIs, generates professional charts and writes a formatted management report — all from a single script.

Demonstrates practical skills in:
- Automated data ingestion with schema validation
- KPI calculation: MRR, gross margin, churn rate, MoM revenue growth
- Object-oriented Python pipeline design
- Professional chart generation
- Automated markdown report writing
- Logging and error handling

---

## Business Context

A data analyst at a FinTech SaaS company is responsible for producing a monthly management pack covering revenue, margins, customer growth, and regional/product breakdown. This pipeline replaces a manual spreadsheet process with an automated, repeatable Python workflow.

**Before automation:** analyst spends ~4 hours manually pulling data, formatting tables and copying charts into a report template.

**After automation:** `python src/reporting_automation.py` produces the full report pack in seconds.

---

## Target Use Case

| Role | Relevance |
|---|---|
| Data Analyst | Pipeline design, KPI automation, pandas, data validation |
| Financial Analyst | MRR reporting, margin analysis, management pack production |
| Reporting Analyst | Automated report generation, structured outputs |
| FinTech Roles | SaaS metrics (MRR, churn, NRR concepts), B2B revenue analysis |

---

## Dataset

**File:** `data/raw/monthly_saas_metrics.csv`
**Rows:** 108 (12 months × 3 products × 3 regions)

| Field | Description |
|---|---|
| `month` | Reporting month (YYYY-MM) |
| `region` | UK, EU, or US |
| `product` | Analytics Platform, Risk Engine, or Data API |
| `revenue_gbp` | Monthly recurring revenue (£) |
| `cost_gbp` | Direct costs (£) |
| `new_customers` | New customers added in month |
| `churned_customers` | Customers lost in month |
| `active_customers` | End-of-month active customer count |

---

## Key Findings (FY2024 — Synthetic Demo)

| Metric | Value |
|---|---|
| **Total FY2024 Revenue** | **£6,728,100** |
| Total Gross Profit | £4,036,800 |
| Average Gross Margin | 60.0% |
| January MRR | £489,000 |
| December MRR | £639,300 |
| **MRR Growth (FY2024)** | **+30.7%** |
| Average Monthly Churn | ~1.8% |

**Revenue by Product:**

| Product | Annual Revenue | Share |
|---|---|---|
| Analytics Platform | £3,063,000 | 45.5% |
| Risk Engine | £2,307,900 | 34.3% |
| Data API | £1,357,200 | 20.2% |

**Revenue by Region:**

| Region | Annual Revenue | Share |
|---|---|---|
| UK | £2,667,700 | 39.6% |
| US | £2,187,600 | 32.5% |
| EU | £1,872,800 | 27.8% |

---

## Validation Checks

The pipeline runs six automated data quality checks before processing:

| Check | Description |
|---|---|
| No null values | All required fields populated |
| Revenue > 0 | No zero or negative revenue rows |
| Cost > 0 | No zero or negative cost rows |
| Cost < Revenue | Gross margin is positive for all rows |
| Active customers > 0 | No zero-customer rows |
| Churn ≤ active | Churn count cannot exceed active customers |

---

## Outputs

| Output | Description |
|---|---|
| `reports/charts/revenue_trend.png` | Monthly revenue stacked by product |
| `reports/charts/revenue_vs_profit.png` | Revenue vs gross profit trend |
| `reports/charts/product_revenue.png` | Annual revenue by product |
| `reports/charts/region_revenue.png` | Annual revenue by region |
| `reports/monthly_summary.csv` | Portfolio-level monthly KPIs |
| `reports/product_summary.csv` | Annual product performance |
| `reports/region_summary.csv` | Annual regional performance |
| `reports/annual_kpis.csv` | Top-level annual KPI table |
| `reports/monthly_management_report.md` | Formatted management report (auto-generated) |

See `reports/example_report.md` for a sample of the generated report.

---

## Folder Structure

```text
data-reporting-automation/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/
│   │   └── monthly_saas_metrics.csv
│   └── processed/
├── src/
│   └── reporting_automation.py
└── reports/
    ├── charts/           ← generated
    ├── monthly_summary.csv   ← generated
    ├── product_summary.csv   ← generated
    ├── region_summary.csv    ← generated
    ├── annual_kpis.csv       ← generated
    ├── monthly_management_report.md  ← generated
    └── example_report.md
```

---

## How to Run

```bash
git clone https://github.com/frazwil19-gif/data-reporting-automation.git
cd data-reporting-automation
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/reporting_automation.py
```

---

## Limitations

- Data is **entirely synthetic** — not real business results
- Gross margin is consistent across products; real SaaS businesses show product-level margin differences
- No ARR, NRR, LTV/CAC or cohort analysis — these are noted as next improvements
- No database connection — pipeline reads from flat CSV; production systems would query a data warehouse

---

## Next Improvements

- [ ] Add ARR and NRR (Net Revenue Retention) calculations
- [ ] Add LTV/CAC ratio analysis
- [ ] Implement cohort-level churn analysis
- [ ] Connect to a SQL database or data warehouse source
- [ ] Add PDF report generation
- [ ] Implement email delivery of the report
- [ ] Add YoY comparison once multi-year data is available

---

## Disclaimer

This project is for portfolio and educational purposes only. It does not constitute financial advice or represent real business performance.
