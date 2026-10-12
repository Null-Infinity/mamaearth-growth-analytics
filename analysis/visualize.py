from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Find project folders
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "visualizations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load the source data
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")

# Remove duplicate submissions using the natural key
natural_key = [
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "discount_pct",
    "payment_method",
    "rating",
    "returned",
]
orders = orders.drop_duplicates(subset=natural_key, keep="first").copy()

# Standardise payment method labels
orders["payment_method"] = (
    orders["payment_method"].astype(str).str.strip().str.upper()
)

# Fill missing values consistently with the analysis
orders["discount_pct"] = orders["discount_pct"].fillna(0)
orders["rating"] = orders["rating"].fillna(orders["rating"].median())

# Merge product and customer details
data = orders.merge(products, on="product_id", how="left")
data = data.merge(
    customers[["customer_id", "city_tier"]],
    on="customer_id",
    how="left",
)

# Calculate order value
data["order_value"] = (
    data["quantity"]
    * data["price_inr"]
    * (1 - data["discount_pct"] / 100)
)

# --------------------------------------------------
# CHART 1: Return rate by payment method
# --------------------------------------------------
return_rates = (
    data.groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

plt.figure(figsize=(8, 5))
return_rates.plot(kind="bar")
plt.title("Return Rate by Payment Method")
plt.xlabel("Payment Method")
plt.ylabel("Return Rate (%)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "return_rate_by_payment_method.png", dpi=150)
plt.close()

# --------------------------------------------------
# CHART 2: Monthly revenue, with and without outliers
# --------------------------------------------------
data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")
data["month"] = data["order_date"].dt.to_period("M")

# Identify quantity outliers using the IQR rule
q1 = data["quantity"].quantile(0.25)
q3 = data["quantity"].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outlier_mask = (
    (data["quantity"] < lower_bound)
    | (data["quantity"] > upper_bound)
)

monthly_all = data.groupby("month")["order_value"].sum()
monthly_clean = (
    data.loc[~outlier_mask]
    .groupby("month")["order_value"]
    .sum()
)

plt.figure(figsize=(10, 5))
plt.plot(
    monthly_all.index.astype(str),
    monthly_all.values,
    marker="o",
    label="Including outliers",
)
plt.plot(
    monthly_clean.index.astype(str),
    monthly_clean.values,
    marker="o",
    label="Excluding quantity outliers",
)
plt.title("Monthly Revenue: Before and After Outlier Exclusion")
plt.xlabel("Month")
plt.ylabel("Revenue (INR)")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "monthly_revenue_comparison.png", dpi=150)
plt.close()

print("Visualisation script completed successfully.")
print(f"Chart 1: {OUTPUT_DIR / 'return_rate_by_payment_method.png'}")
print(f"Chart 2: {OUTPUT_DIR / 'monthly_revenue_comparison.png'}")