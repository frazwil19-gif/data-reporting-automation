"""
Data Reporting Automation Pipeline
====================================
Automated monthly management reporting for a FinTech SaaS company.

Ingests raw monthly metrics, runs validation checks, computes KPIs,
generates professional charts and writes a structured management report.

Dataset: synthetic demo data — not real business results.
Usage:   python src/reporting_automation.py
Outputs: reports/*.csv  |  reports/charts/*.png  |  reports/monthly_management_report.md
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
REPORTS  = ROOT / "reports"
CHARTS   = REPORTS / "charts"

for _dir in (CHARTS,):
    _dir.mkdir(parents=True, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

PRODUCT_COLORS = {
    "Analytics Platform": "#1f77b4",
    "Risk Engine":        "#ff7f0e",
    "Data API":           "#2ca02c",
}
REGION_COLORS = {"UK": "#1f77b4", "EU": "#ff7f0e", "US": "#2ca02c"}

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "#f9f9f9",
    "axes.grid":        True,
    "grid.alpha":       0.35,
    "font.family":      "DejaVu Sans",
})


# ── Data loading ──────────────────────────────────────────────────────────────

class DataLoader:
    REQUIRED_COLUMNS = {
        "month", "region", "product",
        "revenue_gbp", "cost_gbp",
        "new_customers", "churned_customers", "active_customers",
    }

    def load(self, path: Path) -> pd.DataFrame:
        """Load CSV and validate schema."""
        if not path.exists():
            log.error(f"Data file not found: {path}")
            sys.exit(1)
        df = pd.read_csv(path)
        df["month"] = pd.to_datetime(df["month"])
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            log.error(f"Missing required columns: {missing}")
            sys.exit(1)
        log.info(
            f"Loaded {len(df)} rows | "
            f"{df['month'].dt.to_period('M').nunique()} months | "
            f"{df['product'].nunique()} products | "
            f"{df['region'].nunique()} regions"
        )
        return df


# ── Validation ───────────────────────────────────────────────────────────────

class DataValidator:
    """Run data quality checks and log pass/fail results."""

    def validate(self, df: pd.DataFrame) -> bool:
        checks = [
            ("No null values",       df.isnull().sum().sum() == 0),
            ("Revenue > 0",          (df["revenue_gbp"] > 0).all()),
            ("Cost > 0",             (df["cost_gbp"] > 0).all()),
            ("Cost < Revenue",       (df["cost_gbp"] < df["revenue_gbp"]).all()),
            ("Active customers > 0", (df["active_customers"] > 0).all()),
            ("Churn <= active",      (df["churned_customers"] <= df["active_customers"]).all()),
        ]
        log.info("Running data validation checks:")
        all_passed = True
        for name, result in checks:
            status = "PASS" if result else "FAIL"
            if not result:
                all_passed = False
            log.info(f"  [{status}]  {name}")
        if all_passed:
            log.info("All validation checks passed.")
        else:
            log.warning("One or more checks failed — review data quality before proceeding.")
        return all_passed


# ── KPI calculation ───────────────────────────────────────────────────────────

class KPICalculator:
    """Compute portfolio, product and regional KPIs."""

    def monthly_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        grp = (
            df.groupby("month")
            .agg(
                revenue_gbp       =("revenue_gbp",       "sum"),
                cost_gbp          =("cost_gbp",          "sum"),
                new_customers     =("new_customers",     "sum"),
                churned_customers =("churned_customers", "sum"),
                active_customers  =("active_customers",  "sum"),
            )
            .reset_index()
        )
        grp["gross_profit_gbp"] = grp["revenue_gbp"] - grp["cost_gbp"]
        grp["gross_margin_pct"] = grp["gross_profit_gbp"] / grp["revenue_gbp"]
        grp["mom_growth"]       = grp["revenue_gbp"].pct_change()
        grp["churn_rate"]       = grp["churned_customers"] / grp["active_customers"]
        return grp

    def product_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("product")
            .agg(revenue_gbp=("revenue_gbp", "sum"), cost_gbp=("cost_gbp", "sum"))
            .assign(
                gross_profit_gbp=lambda d: d["revenue_gbp"] - d["cost_gbp"],
                gross_margin_pct=lambda d: (d["revenue_gbp"] - d["cost_gbp"]) / d["revenue_gbp"],
            )
            .reset_index()
        )

    def region_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("region")
            .agg(revenue_gbp=("revenue_gbp", "sum"), cost_gbp=("cost_gbp", "sum"))
            .assign(
                gross_profit_gbp=lambda d: d["revenue_gbp"] - d["cost_gbp"],
                gross_margin_pct=lambda d: (d["revenue_gbp"] - d["cost_gbp"]) / d["revenue_gbp"],
            )
            .reset_index()
        )

    def annual_kpis(self, df: pd.DataFrame, monthly: pd.DataFrame) -> dict:
        total_rev    = df["revenue_gbp"].sum()
        total_cost   = df["cost_gbp"].sum()
        total_profit = total_rev - total_cost
        mrr_growth   = (
            (monthly["revenue_gbp"].iloc[-1] - monthly["revenue_gbp"].iloc[0])
            / monthly["revenue_gbp"].iloc[0]
        )
        return {
            "Period":               f"{df['month'].min().strftime('%b %Y')} – {df['month'].max().strftime('%b %Y')}",
            "Total Revenue":        f"£{total_rev:,.0f}",
            "Total Gross Profit":   f"£{total_profit:,.0f}",
            "Average Gross Margin": f"{total_profit / total_rev:.1%}",
            "Starting MRR":         f"£{monthly['revenue_gbp'].iloc[0]:,.0f}",
            "Ending MRR":           f"£{monthly['revenue_gbp'].iloc[-1]:,.0f}",
            "MRR Growth (period)":  f"{mrr_growth:.1%}",
            "Peak MRR Month":       monthly.loc[monthly['revenue_gbp'].idxmax(), 'month'].strftime('%b %Y'),
            "Avg Monthly Churn":    f"{monthly['churn_rate'].mean():.2%}",
            "Products Tracked":     str(df["product"].nunique()),
            "Regions Tracked":      str(df["region"].nunique()),
        }


# ── Charts ────────────────────────────────────────────────────────────────────

class ChartGenerator:

    def revenue_trend(self, df: pd.DataFrame):
        """Stacked monthly revenue by product."""
        pivot = df.pivot_table(
            index="month", columns="product", values="revenue_gbp", aggfunc="sum"
        ).fillna(0)
        labels = [d.strftime("%b %Y") for d in pivot.index]
        fig, ax = plt.subplots(figsize=(13, 5))
        bottom = np.zeros(len(pivot))
        for product in pivot.columns:
            color = PRODUCT_COLORS.get(product, "#aec7e8")
            ax.bar(labels, pivot[product].values, bottom=bottom,
                   label=product, color=color, width=0.65, edgecolor="white")
            bottom += pivot[product].values
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v/1000:.0f}k"))
        ax.set_title("Monthly Revenue by Product — FY2024 (Synthetic Demo)",
                     fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Month", labelpad=8)
        ax.set_ylabel("Revenue (£)", labelpad=8)
        ax.legend(loc="upper left", framealpha=0.85)
        plt.xticks(rotation=45, ha="right")
        fig.tight_layout()
        fig.savefig(CHARTS / "revenue_trend.png", dpi=150)
        plt.close()
        log.info("Saved revenue_trend.png")

    def revenue_vs_profit(self, monthly: pd.DataFrame):
        """Revenue vs gross profit trend lines."""
        x      = list(range(len(monthly)))
        labels = [d.strftime("%b %Y") for d in monthly["month"]]
        fig, ax = plt.subplots(figsize=(13, 5))
        ax.plot(x, monthly["revenue_gbp"], color="#1f77b4", linewidth=2.2,
                marker="o", markersize=5, label="Revenue")
        ax.plot(x, monthly["gross_profit_gbp"], color="#2ca02c", linewidth=2.2,
                marker="s", markersize=5, label="Gross Profit")
        ax.fill_between(x, monthly["gross_profit_gbp"], alpha=0.08, color="#2ca02c")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v/1000:.0f}k"))
        ax.set_title("Monthly Revenue vs Gross Profit — FY2024 (Synthetic Demo)",
                     fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Month", labelpad=8)
        ax.set_ylabel("(£)", labelpad=8)
        ax.legend(framealpha=0.85)
        fig.tight_layout()
        fig.savefig(CHARTS / "revenue_vs_profit.png", dpi=150)
        plt.close()
        log.info("Saved revenue_vs_profit.png")

    def product_bar(self, product_summary: pd.DataFrame):
        """Annual revenue by product."""
        colors = [PRODUCT_COLORS.get(p, "#aec7e8") for p in product_summary["product"]]
        fig, ax = plt.subplots(figsize=(9, 5))
        bars = ax.bar(product_summary["product"], product_summary["revenue_gbp"],
                      color=colors, width=0.5, edgecolor="white")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v/1_000_000:.2f}M"))
        ax.set_title("Annual Revenue by Product — FY2024 (Synthetic Demo)",
                     fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel("Revenue (£)", labelpad=8)
        for bar, val in zip(bars, product_summary["revenue_gbp"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 12000,
                    f"£{val/1_000_000:.2f}M", ha="center", fontsize=10)
        fig.tight_layout()
        fig.savefig(CHARTS / "product_revenue.png", dpi=150)
        plt.close()
        log.info("Saved product_revenue.png")

    def region_bar(self, region_summary: pd.DataFrame):
        """Annual revenue by region."""
        colors = [REGION_COLORS.get(r, "#aec7e8") for r in region_summary["region"]]
        fig, ax = plt.subplots(figsize=(9, 5))
        bars = ax.bar(region_summary["region"], region_summary["revenue_gbp"],
                      color=colors, width=0.4, edgecolor="white")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v/1_000_000:.2f}M"))
        ax.set_title("Annual Revenue by Region — FY2024 (Synthetic Demo)",
                     fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel("Revenue (£)", labelpad=8)
        for bar, val in zip(bars, region_summary["revenue_gbp"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 12000,
                    f"£{val/1_000_000:.2f}M", ha="center", fontsize=10)
        fig.tight_layout()
        fig.savefig(CHARTS / "region_revenue.png", dpi=150)
        plt.close()
        log.info("Saved region_revenue.png")


# ── Report generator ──────────────────────────────────────────────────────────

class ReportGenerator:
    """Write a structured management report to a markdown file."""

    def write(self, kpis: dict, product_df: pd.DataFrame,
              region_df: pd.DataFrame, monthly: pd.DataFrame):
        now   = datetime.now().strftime("%d %B %Y, %H:%M")
        lines = [
            "# Management Report — FY2024\n",
            f"*Auto-generated: {now} | Synthetic demo data*\n\n---\n\n",
            "## Executive Summary\n\n",
        ]
        for metric, value in kpis.items():
            lines.append(f"- **{metric}:** {value}\n")

        lines += ["\n---\n\n## Revenue by Product\n\n",
                  "| Product | Revenue | Cost | Gross Profit | Margin |\n",
                  "|---|---|---|---|---|\n"]
        for _, row in product_df.iterrows():
            lines.append(
                f"| {row['product']} | £{row['revenue_gbp']:,.0f} | £{row['cost_gbp']:,.0f} "
                f"| £{row['gross_profit_gbp']:,.0f} | {row['gross_margin_pct']:.1%} |\n"
            )

        lines += ["\n---\n\n## Revenue by Region\n\n",
                  "| Region | Revenue | Gross Profit | Margin |\n",
                  "|---|---|---|---|\n"]
        for _, row in region_df.iterrows():
            lines.append(
                f"| {row['region']} | £{row['revenue_gbp']:,.0f} "
                f"| £{row['gross_profit_gbp']:,.0f} | {row['gross_margin_pct']:.1%} |\n"
            )

        lines += ["\n---\n\n## Monthly Performance\n\n",
                  "| Month | Revenue | Gross Profit | Margin | MoM Growth | Churn |\n",
                  "|---|---|---|---|---|---|\n"]
        for _, row in monthly.iterrows():
            mom = f"{row['mom_growth']:.1%}" if pd.notna(row["mom_growth"]) else "—"
            lines.append(
                f"| {row['month'].strftime('%b %Y')} | £{row['revenue_gbp']:,.0f} "
                f"| £{row['gross_profit_gbp']:,.0f} | {row['gross_margin_pct']:.1%} "
                f"| {mom} | {row['churn_rate']:.2%} |\n"
            )

        lines += ["\n---\n\n",
                  "*This report was generated automatically by the reporting automation pipeline.*\n",
                  "*Synthetic demo data only. Not financial advice.*\n"]

        out = REPORTS / "monthly_management_report.md"
        out.write_text("".join(lines), encoding="utf-8")
        log.info(f"Saved {out.name}")


# ── CSV exports ─────────────────────────────────────────────────────────────────

def export_csvs(monthly, product_df, region_df, kpis):
    monthly.assign(
        month=lambda d: d["month"].dt.strftime("%Y-%m"),
        gross_margin_pct=lambda d: d["gross_margin_pct"].map("{:.1%}".format),
        mom_growth=lambda d: d["mom_growth"].map(
            lambda v: f"{v:.1%}" if pd.notna(v) else "—"
        ),
        churn_rate=lambda d: d["churn_rate"].map("{:.2%}".format),
    ).to_csv(REPORTS / "monthly_summary.csv", index=False)

    product_df.assign(
        gross_margin_pct=lambda d: d["gross_margin_pct"].map("{:.1%}".format)
    ).to_csv(REPORTS / "product_summary.csv", index=False)

    region_df.assign(
        gross_margin_pct=lambda d: d["gross_margin_pct"].map("{:.1%}".format)
    ).to_csv(REPORTS / "region_summary.csv", index=False)

    pd.DataFrame(list(kpis.items()), columns=["Metric", "Value"]).to_csv(
        REPORTS / "annual_kpis.csv", index=False
    )
    log.info("Saved monthly_summary.csv, product_summary.csv, region_summary.csv, annual_kpis.csv")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("── Data Reporting Automation Pipeline ─────────────")

    loader    = DataLoader()
    validator = DataValidator()
    calc      = KPICalculator()
    charts    = ChartGenerator()
    reporter  = ReportGenerator()

    df = loader.load(DATA_RAW / "monthly_saas_metrics.csv")
    validator.validate(df)

    monthly     = calc.monthly_totals(df)
    product_df  = calc.product_summary(df)
    region_df   = calc.region_summary(df)
    kpis        = calc.annual_kpis(df, monthly)

    print("\n" + "=" * 56)
    print("  ANNUAL KPI SUMMARY — FY2024")
    print("  (Synthetic demo data — not real business results)")
    print("=" * 56)
    for metric, value in kpis.items():
        print(f"  {metric:<28} {value}")
    print("=" * 56 + "\n")

    log.info("Generating charts…")
    charts.revenue_trend(df)
    charts.revenue_vs_profit(monthly)
    charts.product_bar(product_df)
    charts.region_bar(region_df)

    log.info("Exporting CSV reports…")
    export_csvs(monthly, product_df, region_df, kpis)
    reporter.write(kpis, product_df, region_df, monthly)

    log.info("Done. All outputs saved to reports/")


if __name__ == "__main__":
    main()
