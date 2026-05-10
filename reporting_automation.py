import pandas as pd

# Load sample data

df = pd.read_csv("sample_reporting_data.csv")

# Calculate profit

df["profit"] = df["revenue"] - df["cost"]

# KPI summary

summary = pd.DataFrame({
    "Metric": [
        "Total Revenue",
        "Total Cost",
        "Total Profit",
        "Average Revenue",
        "Average Profit"
    ],
    "Value": [
        df["revenue"].sum(),
        df["cost"].sum(),
        df["profit"].sum(),
        round(df["revenue"].mean(), 2),
        round(df["profit"].mean(), 2)
    ]
})

summary.to_csv("outputs/kpi_summary.csv", index=False)

# Regional summary

regional_summary = df.groupby("region")[["revenue", "profit"]].sum().reset_index()
regional_summary.to_csv("outputs/regional_summary.csv", index=False)

# Product summary

product_summary = df.groupby("product")[["revenue", "profit"]].sum().reset_index()
product_summary.to_csv("outputs/product_summary.csv", index=False)

print("Reporting outputs generated successfully.")
