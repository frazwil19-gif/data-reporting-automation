"""
Data Reporting Automation Pipeline — v2.0
=========================================
End-to-end pipeline for automated monthly management reporting.

Steps:
  1. load_data()      — ingest raw CSV
  2. validate()       — data quality checks
  3. compute_kpis()   — derive KPI metrics
  4. generate_charts()— produce 9 SVG charts
  5. write_report()   — emit structured Markdown report

Usage:
    python src/reporting_automation.py
"""

import os
import sys
import json
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(levelname)s  %(message)s')
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / 'data' / 'monthly_saas_metrics.csv'
OUTPUT_DIR = BASE_DIR / 'reports' / 'charts'
REPORT_DIR = BASE_DIR / 'reports'
PROCESSED_DIR = BASE_DIR / 'data' / 'processed'

for d in [OUTPUT_DIR, REPORT_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
PALETTE = {
    'primary':   '#1B4F8A',
    'secondary': '#2E86C1',
    'accent':    '#27AE60',
    'warning':   '#E67E22',
    'danger':    '#E74C3C',
    'light':     '#ECF0F1',
    'dark':      '#2C3E50',
    'products':  ['#1B4F8A', '#27AE60', '#E67E22'],
    'regions':   ['#1B4F8A', '#2E86C1', '#27AE60', '#E67E22'],
}


# ===========================================================================
# Pipeline class
# ===========================================================================
class ReportingPipeline:
    """Orchestrates the full monthly reporting pipeline."""

    def __init__(self, data_path: Path = DATA_PATH):
        self.data_path = data_path
        self.df_raw: Optional[pd.DataFrame] = None
        self.df: Optional[pd.DataFrame] = None
        self.kpis: Dict = {}
        self.validation_results: Dict = {}

    # -----------------------------------------------------------------------
    # Step 1 — Load
    # -----------------------------------------------------------------------
    def load_data(self) -> 'ReportingPipeline':
        log.info('Step 1: Loading data from %s', self.data_path)
        self.df_raw = pd.read_csv(self.data_path)
        self.df_raw['month'] = pd.to_datetime(self.df_raw['month'])
        self.df = self.df_raw.copy()
        log.info('  Loaded %d rows, %d columns', len(self.df), len(self.df.columns))
        return self

    # -----------------------------------------------------------------------
    # Step 2 — Validate
    # -----------------------------------------------------------------------
    def validate(self) -> 'ReportingPipeline':
        log.info('Step 2: Validating data quality')
        df = self.df
        results = {}

        # Null checks
        null_counts = df.isnull().sum()
        results['null_counts'] = null_counts[null_counts > 0].to_dict()
        results['total_nulls'] = int(null_counts.sum())

        # Negative revenue / cost
        results['negative_revenue'] = int((df['revenue_gbp'] < 0).sum())
        results['negative_cost'] = int((df['cost_gbp'] < 0).sum())

        # Revenue >= cost check
        results['negative_margin_rows'] = int((df['revenue_gbp'] < df['cost_gbp']).sum())

        # Churn rate range
        results['churn_out_of_range'] = int(((df['churn_rate'] < 0) | (df['churn_rate'] > 1)).sum())

        # Duplicate rows
        results['duplicate_rows'] = int(df.duplicated().sum())

        # Date range
        results['date_min'] = df['month'].min().strftime('%Y-%m-%d')
        results['date_max'] = df['month'].max().strftime('%Y-%m-%d')
        results['months_covered'] = int(df['month'].nunique())

        self.validation_results = results
        issues = sum([
            results['total_nulls'],
            results['negative_revenue'],
            results['negative_cost'],
            results['negative_margin_rows'],
            results['churn_out_of_range'],
            results['duplicate_rows'],
        ])
        log.info('  Validation complete. Issues found: %d', issues)
        return self

    # -----------------------------------------------------------------------
    # Step 3 — Compute KPIs
    # -----------------------------------------------------------------------
    def compute_kpis(self) -> 'ReportingPipeline':
        log.info('Step 3: Computing KPIs')
        df = self.df

        # ---- Revenue ----
        total_rev = df['revenue_gbp'].sum()
        total_cost = df['cost_gbp'].sum()
        gross_profit = total_rev - total_cost
        gross_margin = gross_profit / total_rev

        monthly_rev = df.groupby('month')['revenue_gbp'].sum().sort_index()
        mrr_jan = monthly_rev.iloc[0]
        mrr_dec = monthly_rev.iloc[-1]
        mrr_growth = (mrr_dec - mrr_jan) / mrr_jan

        mom_growth = monthly_rev.pct_change().dropna()
        avg_mom_growth = mom_growth.mean()

        # ---- Customers ----
        total_new_customers = df['new_customers'].sum()
        avg_churn = df['churn_rate'].mean()

        # LTV
        if 'customer_ltv' in df.columns:
            avg_ltv = df['customer_ltv'].mean()
        else:
            avg_arpu = (mrr_dec / max(total_new_customers / 12, 1))
            avg_ltv = avg_arpu / max(avg_churn, 0.001)

        # ---- By product ----
        product_rev = df.groupby('product')['revenue_gbp'].sum().sort_values(ascending=False)
        product_margin = (
            df.groupby('product').apply(
                lambda g: (g['revenue_gbp'].sum() - g['cost_gbp'].sum()) / g['revenue_gbp'].sum()
            )
        )

        # ---- By region ----
        region_rev = df.groupby('region')['revenue_gbp'].sum().sort_values(ascending=False)
        top_region = region_rev.index[0]
        top_region_pct = region_rev.iloc[0] / total_rev

        self.kpis = {
            'total_revenue': total_rev,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'gross_margin': gross_margin,
            'mrr_jan': mrr_jan,
            'mrr_dec': mrr_dec,
            'mrr_growth': mrr_growth,
            'avg_mom_growth': avg_mom_growth,
            'total_new_customers': total_new_customers,
            'avg_churn': avg_churn,
            'avg_ltv': avg_ltv,
            'product_rev': product_rev,
            'product_margin': product_margin,
            'region_rev': region_rev,
            'top_region': top_region,
            'top_region_pct': top_region_pct,
        }

        # ---- Export processed data ----
        self._export_processed()

        log.info('  KPIs computed. Total Revenue: £%,.0f', total_rev)
        return self

    def _export_processed(self):
        """Write processed / enriched CSVs to data/processed/."""
        df = self.df.copy()
        df['gross_profit_gbp'] = df['revenue_gbp'] - df['cost_gbp']
        df['gross_margin_pct'] = df['gross_profit_gbp'] / df['revenue_gbp'] * 100
        df.to_csv(PROCESSED_DIR / 'enriched_metrics.csv', index=False)

        monthly = df.groupby('month').agg(
            revenue=('revenue_gbp', 'sum'),
            cost=('cost_gbp', 'sum'),
            new_customers=('new_customers', 'sum'),
            churn_rate=('churn_rate', 'mean'),
        ).reset_index()
        monthly['gross_profit'] = monthly['revenue'] - monthly['cost']
        monthly['gross_margin_pct'] = monthly['gross_profit'] / monthly['revenue'] * 100
        monthly['mrr_k'] = monthly['revenue'] / 1_000
        monthly.to_csv(PROCESSED_DIR / 'monthly_summary.csv', index=False)
        log.info('  Processed CSVs written to %s', PROCESSED_DIR)

    # -----------------------------------------------------------------------
    # Step 4 — Generate Charts
    # -----------------------------------------------------------------------
    def generate_charts(self) -> 'ReportingPipeline':
        log.info('Step 4: Generating charts')
        df = self.df

        self._chart_mrr_trend(df)
        self._chart_revenue_waterfall(df)
        self._chart_product_revenue_stacked(df)
        self._chart_regional_breakdown(df)
        self._chart_gross_margin_trend(df)
        self._chart_churn_new_customers(df)
        self._chart_product_margin_comparison(df)
        self._chart_product_region_heatmap(df)
        self._chart_kpi_dashboard()

        log.info('  9 charts written to %s', OUTPUT_DIR)
        return self

    def _save(self, fig, name: str):
        path = OUTPUT_DIR / name
        fig.savefig(str(path), format='svg', bbox_inches='tight', dpi=150)
        plt.close(fig)
        log.info('    Chart saved: %s', name)

    def _chart_mrr_trend(self, df):
        monthly = df.groupby('month').agg(revenue=('revenue_gbp', 'sum')).reset_index().sort_values('month')
        monthly['mrr'] = monthly['revenue'] / 1_000
        monthly['mom'] = monthly['mrr'].pct_change() * 100

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#F8FAFC')
        ax.plot(monthly['month'], monthly['mrr'], color=PALETTE['primary'], linewidth=2.5, zorder=3)
        ax.fill_between(monthly['month'], monthly['mrr'], alpha=0.12, color=PALETTE['primary'])
        ax.scatter(monthly['month'], monthly['mrr'], color=PALETTE['primary'], s=60, zorder=4)
        for _, row in monthly.iterrows():
            if pd.notna(row['mom']):
                ax.annotate(f"+{row['mom']:.1f}%", xy=(row['month'], row['mrr']),
                            xytext=(0, 12), textcoords='offset points',
                            ha='center', fontsize=7.5, color=PALETTE['accent'], fontweight='bold')
        start, end = monthly['mrr'].iloc[0], monthly['mrr'].iloc[-1]
        growth = (end - start) / start * 100
        ax.annotate(f'FY2024 Growth\n+{growth:.1f}%', xy=(monthly['month'].iloc[-1], end),
                    xytext=(-80, -40), textcoords='offset points', fontsize=9,
                    color='white', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['primary'], alpha=0.9),
                    arrowprops=dict(arrowstyle='->', color=PALETTE['primary']))
        ax.set_title('Monthly Recurring Revenue (MRR) — FY2024', fontsize=14, fontweight='bold',
                     color=PALETTE['dark'], pad=15)
        ax.set_ylabel('MRR (£k)', fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x:.0f}k'))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b'))
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        ax.spines[['top', 'right']].set_visible(False)
        fig.tight_layout()
        self._save(fig, 'mrr_trend_annotated.svg')

    def _chart_revenue_waterfall(self, df):
        monthly = df.groupby('month').agg(revenue=('revenue_gbp', 'sum')).reset_index().sort_values('month')
        monthly['mrr'] = monthly['revenue'] / 1_000
        monthly['delta'] = monthly['mrr'].diff().fillna(monthly['mrr'].iloc[0])
        monthly['base'] = (monthly['mrr'] - monthly['delta']).clip(lower=0)
        months_labels = monthly['month'].dt.strftime('%b')
        fig, ax = plt.subplots(figsize=(13, 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#F8FAFC')
        for i, (_, row) in enumerate(monthly.iterrows()):
            color = PALETTE['accent'] if row['delta'] >= 0 else PALETTE['danger']
            ax.bar(i, row['delta'], bottom=row['base'], color=color, width=0.6,
                   edgecolor='white', linewidth=0.5)
            ax.text(i, row['mrr'] + 4, f'£{row["mrr"]:.0f}k', ha='center', va='bottom',
                    fontsize=8, fontweight='bold', color=PALETTE['dark'])
        ax.set_xticks(range(len(months_labels)))
        ax.set_xticklabels(months_labels)
        ax.set_title('Revenue Growth Waterfall — FY2024', fontsize=14, fontweight='bold',
                     color=PALETTE['dark'], pad=15)
        ax.set_ylabel('Revenue (£k)', fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x:.0f}k'))
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        ax.spines[['top', 'right']].set_visible(False)
        legend = [mpatches.Patch(color=PALETTE['accent'], label='Growth'),
                  mpatches.Patch(color=PALETTE['danger'], label='Decline')]
        ax.legend(handles=legend, loc='upper left', framealpha=0.8)
        fig.tight_layout()
        self._save(fig, 'revenue_waterfall.svg')

    def _chart_product_revenue_stacked(self, df):
        pivot = df.pivot_table(index='month', columns='product', values='revenue_gbp', aggfunc='sum').sort_index() / 1_000
        months = pivot.index.strftime('%b')
        products = pivot.columns.tolist()
        colors = PALETTE['products'][:len(products)]
        fig, ax = plt.subplots(figsize=(13, 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#F8FAFC')
        bottom = np.zeros(len(pivot))
        for prod, color in zip(products, colors):
            vals = pivot[prod].values
            ax.bar(range(len(pivot)), vals, bottom=bottom, label=prod, color=color,
                   width=0.65, edgecolor='white', linewidth=0.8)
            bottom += vals
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months)
        ax.set_title('Monthly Revenue by Product — Stacked (FY2024)', fontsize=14,
                     fontweight='bold', color=PALETTE['dark'], pad=15)
        ax.set_ylabel('Revenue (£k)', fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x:.0f}k'))
        ax.legend(loc='upper left', framealpha=0.8)
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        ax.spines[['top', 'right']].set_visible(False)
        fig.tight_layout()
        self._save(fig, 'product_revenue_stacked.svg')

    def _chart_regional_breakdown(self, df):
        regional = df.groupby('region')['revenue_gbp'].sum().sort_values(ascending=True) / 1_000
        total = regional.sum()
        pcts = regional / total * 100
        colors = PALETTE['regions'][:len(regional)]
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#F8FAFC')
        bars = ax.barh(regional.index, regional.values, color=colors, height=0.55, edgecolor='white')
        for bar, pct, val in zip(bars, pcts.values, regional.values):
            ax.text(val + 5, bar.get_y() + bar.get_height() / 2,
                    f'£{val:.0f}k  ({pct:.1f}%)', va='center', fontsize=9,
                    color=PALETTE['dark'], fontweight='bold')
        ax.set_title('FY2024 Revenue by Region', fontsize=14, fontweight='bold',
                     color=PALETTE['dark'], pad=15)
        ax.set_xlabel('Total Revenue (£k)', fontsize=10)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x:.0f}k'))
        ax.grid(axis='x', linestyle='--', alpha=0.4)
        ax.spines[['top', 'right']].set_visible(False)
        fig.tight_layout()
        self._save(fig, 'regional_breakdown.svg')

    def _chart_gross_margin_trend(self, df):
        monthly = df.groupby('month').agg(
            revenue=('revenue_gbp', 'sum'), cost=('cost_gbp', 'sum')
        ).reset_index().sort_values('month')
        monthly['gross_profit'] = (monthly['revenue'] - monthly['cost']) / 1_000
        monthly['margin_pct'] = (monthly['revenue'] - monthly['cost']) / monthly['revenue'] * 100
        fig, ax1 = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('white')
        ax1.set_facecolor('#F8FAFC')
        ax2 = ax1.twinx()
        ax1.bar(monthly['month'], monthly['gross_profit'], color=PALETTE['secondary'],
                alpha=0.45, width=20, label='Gross Profit (£k)')
        ax2.plot(monthly['month'], monthly['margin_pct'], color=PALETTE['accent'],
                 linewidth=2.5, marker='o', markersize=6, label='Margin %')
        ax1.set_title('Gross Margin Trend — FY2024', fontsize=14, fontweight='bold',
                      color=PALETTE['dark'], pad=15)
        ax1.set_ylabel('Gross Profit (£k)', fontsize=10, color=PALETTE['secondary'])
        ax2.set_ylabel('Gross Margin %', fontsize=10, color=PALETTE['accent'])
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x:.0f}k'))
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}%'))
        ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b'))
        ax1.grid(axis='y', linestyle='--', alpha=0.4)
        ax1.spines[['top']].set_visible(False)
        ax2.spines[['top']].set_visible(False)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.8)
        fig.tight_layout()
        self._save(fig, 'gross_margin_trend.svg')

    def _chart_churn_new_customers(self, df):
        monthly = df.groupby('month').agg(
            new_customers=('new_customers', 'sum'), churn_rate=('churn_rate', 'mean')
        ).reset_index().sort_values('month')
        monthly['churn_pct'] = monthly['churn_rate'] * 100
        fig, ax1 = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('white')
        ax1.set_facecolor('#F8FAFC')
        ax2 = ax1.twinx()
        ax1.bar(monthly['month'], monthly['new_customers'], color=PALETTE['primary'],
                alpha=0.55, width=20, label='New Customers')
        ax2.plot(monthly['month'], monthly['churn_pct'], color=PALETTE['danger'],
                 linewidth=2.5, marker='s', markersize=7, label='Churn Rate %')
        ax1.set_title('New Customers & Churn Rate — FY2024', fontsize=14, fontweight='bold',
                      color=PALETTE['dark'], pad=15)
        ax1.set_ylabel('New Customers', fontsize=10, color=PALETTE['primary'])
        ax2.set_ylabel('Churn Rate (%)', fontsize=10, color=PALETTE['danger'])
        ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b'))
        ax1.grid(axis='y', linestyle='--', alpha=0.4)
        ax1.spines[['top']].set_visible(False)
        ax2.spines[['top']].set_visible(False)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', framealpha=0.8)
        fig.tight_layout()
        self._save(fig, 'churn_new_customers.svg')

    def _chart_product_margin_comparison(self, df):
        df2 = df.copy()
        df2['margin'] = (df2['revenue_gbp'] - df2['cost_gbp']) / df2['revenue_gbp'] * 100
        pivot = df2.pivot_table(index='month', columns='product', values='margin', aggfunc='mean').sort_index()
        months = pivot.index.strftime('%b')
        products = pivot.columns.tolist()
        colors = PALETTE['products'][:len(products)]
        n = len(products)
        x = np.arange(len(pivot))
        width = 0.25
        fig, ax = plt.subplots(figsize=(14, 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#F8FAFC')
        for i, (prod, color) in enumerate(zip(products, colors)):
            offset = (i - n / 2 + 0.5) * width
            ax.bar(x + offset, pivot[prod].values, width=width * 0.9, label=prod,
                   color=color, edgecolor='white')
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.set_title('Gross Margin % by Product — Monthly Comparison (FY2024)', fontsize=13,
                     fontweight='bold', color=PALETTE['dark'], pad=15)
        ax.set_ylabel('Gross Margin (%)', fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
        ax.legend(loc='lower right', framealpha=0.8)
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        ax.spines[['top', 'right']].set_visible(False)
        fig.tight_layout()
        self._save(fig, 'product_margin_comparison.svg')

    def _chart_product_region_heatmap(self, df):
        pivot = df.pivot_table(index='product', columns='region', values='revenue_gbp',
                               aggfunc='sum') / 1_000
        cmap = LinearSegmentedColormap.from_list('brand', ['#ECF0F1', '#1B4F8A'])
        fig, ax = plt.subplots(figsize=(9, 5))
        fig.patch.set_facecolor('white')
        im = ax.imshow(pivot.values, cmap=cmap, aspect='auto')
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_yticks(range(len(pivot.index)))
        ax.set_xticklabels(pivot.columns, fontsize=10)
        ax.set_yticklabels(pivot.index, fontsize=10)
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i, j]
                text_color = 'white' if val > pivot.values.max() * 0.55 else PALETTE['dark']
                ax.text(j, i, f'£{val:.0f}k', ha='center', va='center',
                        fontsize=9, fontweight='bold', color=text_color)
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Revenue (£k)', fontsize=9)
        ax.set_title('FY2024 Revenue Heatmap: Product × Region', fontsize=13,
                     fontweight='bold', color=PALETTE['dark'], pad=15)
        fig.tight_layout()
        self._save(fig, 'product_region_heatmap.svg')

    def _chart_kpi_dashboard(self):
        k = self.kpis
        kpis = [
            ('Total Revenue', f'£{k["total_revenue"]/1000:,.0f}k', PALETTE['primary']),
            ('MRR (Dec)', f'£{k["mrr_dec"]/1000:,.0f}k', PALETTE['secondary']),
            ('Gross Margin', f'{k["gross_margin"]*100:.1f}%', PALETTE['accent']),
            ('New Customers', f'{int(k["total_new_customers"]):,}', PALETTE['warning']),
            ('Avg Churn Rate', f'{k["avg_churn"]*100:.2f}%', PALETTE['danger']),
            ('Avg Customer LTV', f'£{k["avg_ltv"]:,.0f}', PALETTE['dark']),
        ]
        fig = plt.figure(figsize=(12, 4))
        fig.patch.set_facecolor('#F0F4F8')
        gs = gridspec.GridSpec(1, 6, figure=fig, hspace=0.3, wspace=0.3)
        for i, (label, value, color) in enumerate(kpis):
            ax = fig.add_subplot(gs[0, i])
            ax.set_facecolor('white')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            ax.add_patch(mpatches.FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
                                                  boxstyle='round,pad=0.02',
                                                  facecolor='white', edgecolor=color, linewidth=2))
            ax.add_patch(mpatches.FancyBboxPatch((0.05, 0.72), 0.9, 0.23,
                                                  boxstyle='round,pad=0.01',
                                                  facecolor=color, edgecolor='none'))
            ax.text(0.5, 0.835, label, ha='center', va='center', fontsize=8,
                    fontweight='bold', color='white', transform=ax.transAxes)
            ax.text(0.5, 0.42, value, ha='center', va='center', fontsize=13,
                    fontweight='bold', color=color, transform=ax.transAxes)
        fig.suptitle('FY2024 KPI Dashboard', fontsize=15, fontweight='bold',
                     color=PALETTE['dark'], y=1.02)
        fig.tight_layout()
        self._save(fig, 'kpi_dashboard.svg')

    # -----------------------------------------------------------------------
    # Step 5 — Write Report
    # -----------------------------------------------------------------------
    def write_report(self) -> 'ReportingPipeline':
        log.info('Step 5: Writing management report')
        k = self.kpis
        v = self.validation_results
        now = datetime.now().strftime('%d %B %Y')

        product_rev_lines = '\n'.join(
            f'| {prod} | £{rev/1000:,.0f}k | {k["product_margin"][prod]*100:.1f}% |'
            for prod, rev in k['product_rev'].items()
        )
        region_rev_lines = '\n'.join(
            f'| {reg} | £{rev/1000:,.0f}k | {rev/k["total_revenue"]*100:.1f}% |'
            for reg, rev in k['region_rev'].items()
        )

        report = f"""# Monthly Management Report — FY2024
**Company:** FinTech SaaS Demo Co.  
**Report Date:** {now}  
**Prepared by:** Data Reporting Automation Pipeline v2.0  
**Data Period:** {v.get('date_min', 'N/A')} to {v.get('date_max', 'N/A')}

---

## Executive Summary

| KPI | Value |
|-----|-------|
| Total Revenue | £{k['total_revenue']/1000:,.0f}k |
| MRR (January) | £{k['mrr_jan']/1000:,.0f}k |
| MRR (December) | £{k['mrr_dec']/1000:,.0f}k |
| MRR Growth (FY) | {k['mrr_growth']*100:.1f}% |
| Avg MoM Growth | {k['avg_mom_growth']*100:.1f}% |
| Gross Profit | £{k['gross_profit']/1000:,.0f}k |
| Gross Margin | {k['gross_margin']*100:.1f}% |
| Total New Customers | {int(k['total_new_customers']):,} |
| Avg Monthly Churn | {k['avg_churn']*100:.2f}% |
| Avg Customer LTV | £{k['avg_ltv']:,.0f} |

---

## Revenue Performance

Total FY2024 revenue reached **£{k['total_revenue']/1000:,.0f}k**, with MRR growing from
**£{k['mrr_jan']/1000:,.0f}k** in January to **£{k['mrr_dec']/1000:,.0f}k** in December —
a year-on-year increase of **{k['mrr_growth']*100:.1f}%**. Average month-on-month growth
was **{k['avg_mom_growth']*100:.1f}%**, reflecting consistent demand acceleration.

---

## Product Breakdown

| Product | FY2024 Revenue | Gross Margin |
|---------|---------------|-------------|
{product_rev_lines}

The top-performing product by revenue is **{k['product_rev'].index[0]}**. Margin leaders
are identified in the Product Margin Comparison chart.

---

## Regional Breakdown

| Region | FY2024 Revenue | Share |
|--------|---------------|-------|
{region_rev_lines}

**{k['top_region']}** is the largest revenue region at **{k['top_region_pct']*100:.1f}%** of total.

---

## Margin & Efficiency

- **Gross Profit:** £{k['gross_profit']/1000:,.0f}k on £{k['total_revenue']/1000:,.0f}k revenue
- **Gross Margin:** {k['gross_margin']*100:.1f}% for the full year
- Margins improved through H2 as revenue scale outpaced cost growth.

---

## Customer Metrics

- **Total New Customers (FY2024):** {int(k['total_new_customers']):,}
- **Average Monthly Churn Rate:** {k['avg_churn']*100:.2f}%
- **Average Customer LTV:** £{k['avg_ltv']:,.0f}

Churn declined through the second half of the year, and LTV improved in line with
the shift towards higher-margin product lines.

---

## Data Quality Summary

| Check | Result |
|-------|--------|
| Total Null Values | {v.get('total_nulls', 0)} |
| Negative Revenue Rows | {v.get('negative_revenue', 0)} |
| Negative Cost Rows | {v.get('negative_cost', 0)} |
| Negative Margin Rows | {v.get('negative_margin_rows', 0)} |
| Churn Rate Out of Range | {v.get('churn_out_of_range', 0)} |
| Duplicate Rows | {v.get('duplicate_rows', 0)} |
| Months Covered | {v.get('months_covered', 0)} |
| Date Range | {v.get('date_min', 'N/A')} → {v.get('date_max', 'N/A')} |

---

*Report generated automatically by Data Reporting Automation Pipeline v2.0.*  
*All figures are synthetic demo data only.*
"""

        report_path = REPORT_DIR / 'monthly_management_report.md'
        report_path.write_text(report, encoding='utf-8')
        log.info('  Report written to %s', report_path)
        return self


# ===========================================================================
# Entry point
# ===========================================================================
def main():
    log.info('=== Data Reporting Automation Pipeline v2.0 ===')
    pipeline = ReportingPipeline()
    (
        pipeline
        .load_data()
        .validate()
        .compute_kpis()
        .generate_charts()
        .write_report()
    )
    log.info('=== Pipeline complete ===')


if __name__ == '__main__':
    main()
