"""
Chart generation script — FinTech SaaS Demo Reporting Suite
===========================================================
Produces 9 publication-quality SVG charts from the processed SaaS metrics.
Can be run standalone or called from reporting_automation.py.

Outputs written to: reports/charts/
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'monthly_saas_metrics.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'reports', 'charts')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
PALETTE = {
    'primary':    '#1B4F8A',
    'secondary':  '#2E86C1',
    'accent':     '#27AE60',
    'warning':    '#E67E22',
    'danger':     '#E74C3C',
    'light':      '#ECF0F1',
    'mid':        '#BDC3C7',
    'dark':       '#2C3E50',
    'products':   ['#1B4F8A', '#27AE60', '#E67E22'],
    'regions':    ['#1B4F8A', '#2E86C1', '#27AE60', '#E67E22'],
}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df['month'] = pd.to_datetime(df['month'])
    return df


def _save(fig, name: str):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, format='svg', bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f'  Saved: {path}')


# ---------------------------------------------------------------------------
# 1. MRR Trend with Annotations
# ---------------------------------------------------------------------------
def chart_mrr_trend(df: pd.DataFrame):
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
                        ha='center', fontsize=7.5, color=PALETTE['accent'],
                        fontweight='bold')

    start, end = monthly['mrr'].iloc[0], monthly['mrr'].iloc[-1]
    growth = (end - start) / start * 100
    ax.annotate(f'FY2024 Growth\n+{growth:.1f}%',
                xy=(monthly['month'].iloc[-1], end),
                xytext=(-80, -40), textcoords='offset points',
                fontsize=9, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=PALETTE['primary'], alpha=0.9),
                arrowprops=dict(arrowstyle='->', color=PALETTE['primary']))

    ax.set_title('Monthly Recurring Revenue (MRR) — FY2024', fontsize=14, fontweight='bold',
                 color=PALETTE['dark'], pad=15)
    ax.set_ylabel('MRR (£k)', fontsize=10, color=PALETTE['dark'])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'£{x:.0f}k'))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b'))
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    _save(fig, 'mrr_trend_annotated.svg')


# ---------------------------------------------------------------------------
# 2. Revenue Waterfall
# ---------------------------------------------------------------------------
def chart_revenue_waterfall(df: pd.DataFrame):
    monthly = df.groupby('month').agg(revenue=('revenue_gbp', 'sum')).reset_index().sort_values('month')
    monthly['mrr'] = monthly['revenue'] / 1_000
    monthly['delta'] = monthly['mrr'].diff().fillna(monthly['mrr'].iloc[0])
    monthly['base'] = monthly['mrr'] - monthly['delta']
    monthly['base'] = monthly['base'].clip(lower=0)
    months = monthly['month'].dt.strftime('%b')

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#F8FAFC')

    for i, (_, row) in enumerate(monthly.iterrows()):
        color = PALETTE['accent'] if row['delta'] >= 0 else PALETTE['danger']
        ax.bar(i, row['delta'], bottom=row['base'], color=color, width=0.6, zorder=3,
               edgecolor='white', linewidth=0.5)
        ax.text(i, row['mrr'] + 4, f'£{row["mrr"]:.0f}k', ha='center', va='bottom',
                fontsize=8, fontweight='bold', color=PALETTE['dark'])

    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months)
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
    _save(fig, 'revenue_waterfall.svg')


# ---------------------------------------------------------------------------
# 3. Product Revenue Stacked
# ---------------------------------------------------------------------------
def chart_product_revenue_stacked(df: pd.DataFrame):
    pivot = df.pivot_table(index='month', columns='product', values='revenue_gbp', aggfunc='sum')
    pivot = pivot.sort_index()
    pivot = pivot / 1_000
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
    _save(fig, 'product_revenue_stacked.svg')


# ---------------------------------------------------------------------------
# 4. Regional Revenue Breakdown
# ---------------------------------------------------------------------------
def chart_regional_breakdown(df: pd.DataFrame):
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
    _save(fig, 'regional_breakdown.svg')


# ---------------------------------------------------------------------------
# 5. Gross Margin Trend
# ---------------------------------------------------------------------------
def chart_gross_margin_trend(df: pd.DataFrame):
    monthly = df.groupby('month').agg(
        revenue=('revenue_gbp', 'sum'),
        cost=('cost_gbp', 'sum')
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
    _save(fig, 'gross_margin_trend.svg')


# ---------------------------------------------------------------------------
# 6. Churn Rate & New Customers
# ---------------------------------------------------------------------------
def chart_churn_new_customers(df: pd.DataFrame):
    monthly = df.groupby('month').agg(
        new_customers=('new_customers', 'sum'),
        churn_rate=('churn_rate', 'mean')
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
    _save(fig, 'churn_new_customers.svg')


# ---------------------------------------------------------------------------
# 7. Product Margin Comparison
# ---------------------------------------------------------------------------
def chart_product_margin_comparison(df: pd.DataFrame):
    df2 = df.copy()
    df2['margin'] = (df2['revenue_gbp'] - df2['cost_gbp']) / df2['revenue_gbp'] * 100
    pivot = df2.pivot_table(index='month', columns='product', values='margin', aggfunc='mean')
    pivot = pivot.sort_index()
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
    _save(fig, 'product_margin_comparison.svg')


# ---------------------------------------------------------------------------
# 8. Product × Region Heatmap
# ---------------------------------------------------------------------------
def chart_product_region_heatmap(df: pd.DataFrame):
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
    _save(fig, 'product_region_heatmap.svg')


# ---------------------------------------------------------------------------
# 9. KPI Dashboard
# ---------------------------------------------------------------------------
def chart_kpi_dashboard(df: pd.DataFrame):
    total_rev = df['revenue_gbp'].sum() / 1_000
    dec = df[df['month'] == df['month'].max()]
    mrr_dec = dec['revenue_gbp'].sum() / 1_000
    gross_margin = (df['revenue_gbp'].sum() - df['cost_gbp'].sum()) / df['revenue_gbp'].sum() * 100
    new_cust = df['new_customers'].sum()
    avg_churn = df['churn_rate'].mean() * 100
    ltv = df['customer_ltv'].mean() if 'customer_ltv' in df.columns else (mrr_dec / (avg_churn / 100)) if avg_churn > 0 else 0

    kpis = [
        ('Total Revenue', f'£{total_rev:,.0f}k', PALETTE['primary']),
        ('MRR (Dec)', f'£{mrr_dec:,.0f}k', PALETTE['secondary']),
        ('Gross Margin', f'{gross_margin:.1f}%', PALETTE['accent']),
        ('New Customers', f'{int(new_cust):,}', PALETTE['warning']),
        ('Avg Churn Rate', f'{avg_churn:.2f}%', PALETTE['danger']),
        ('Avg Customer LTV', f'£{ltv:,.0f}', PALETTE['dark']),
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
                                              facecolor='white',
                                              edgecolor=color, linewidth=2))
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
    _save(fig, 'kpi_dashboard.svg')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print('Loading data...')
    df = load_data()
    print(f'  {len(df)} rows loaded.')
    print('Generating charts...')
    chart_mrr_trend(df)
    chart_revenue_waterfall(df)
    chart_product_revenue_stacked(df)
    chart_regional_breakdown(df)
    chart_gross_margin_trend(df)
    chart_churn_new_customers(df)
    chart_product_margin_comparison(df)
    chart_product_region_heatmap(df)
    chart_kpi_dashboard(df)
    print('All 9 charts generated.')


if __name__ == '__main__':
    main()
