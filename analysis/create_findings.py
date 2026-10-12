import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
NARRATOR_DIR = PROJECT_ROOT / "narrator"

OUTPUT_DIR.mkdir(exist_ok=True)
NARRATOR_DIR.mkdir(exist_ok=True)

# Load original source files without modifying them.
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")

raw_order_count = len(orders)

# Remove duplicate submissions using the natural key.
duplicate_key = [
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "discount_pct",
    "payment_method",
    "rating",
    "returned",
]

cleaned = orders.drop_duplicates(
    subset=duplicate_key,
    keep="first"
).copy()

duplicates_removed = raw_order_count - len(cleaned)

# Standardize payment methods and fill missing values.
cleaned["payment_method"] = (
    cleaned["payment_method"]
    .astype("string")
    .str.strip()
    .str.upper()
)

cleaned["discount_pct"] = cleaned["discount_pct"].fillna(0)
cleaned["rating"] = cleaned["rating"].fillna(
    cleaned["rating"].median()
)

# Merge product prices and calculate order value.
cleaned = cleaned.merge(
    products[["product_id", "price_inr"]],
    on="product_id",
    how="left",
    validate="many_to_one"
)

cleaned["order_value_inr"] = (
    cleaned["quantity"]
    * cleaned["price_inr"]
    * (1 - cleaned["discount_pct"] / 100)
)

# Calculate return rates by payment method.
payment_returns = (
    cleaned.groupby("payment_method")
    .agg(
        total_orders=("order_id", "count"),
        returned_orders=("returned", "sum"),
    )
    .reset_index()
)

payment_returns["return_rate_pct"] = (
    100 * payment_returns["returned_orders"]
    / payment_returns["total_orders"]
).round(2)

# Identify quantity outliers using the IQR rule.
q1 = cleaned["quantity"].quantile(0.25)
q3 = cleaned["quantity"].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

cleaned["is_quantity_outlier"] = (
    (cleaned["quantity"] < lower_bound)
    | (cleaned["quantity"] > upper_bound)
)

# Calculate monthly revenue with and without flagged outliers.
cleaned["order_date"] = pd.to_datetime(cleaned["order_date"])
cleaned["month"] = cleaned["order_date"].dt.to_period("M").astype(str)

monthly = (
    cleaned.groupby("month")
    .apply(
        lambda group: pd.Series({
            "revenue_including_outliers_inr":
                group["order_value_inr"].sum(),
            "revenue_excluding_outliers_inr":
                group.loc[
                    ~group["is_quantity_outlier"],
                    "order_value_inr"
                ].sum(),
        }),
        include_groups=False,
    )
    .reset_index()
)

monthly = monthly.round(2)
monthly.to_csv(
    OUTPUT_DIR / "monthly_revenue_comparison.csv",
    index=False
)

# Save the cleaned orders for reproducibility.
cleaned.to_csv(OUTPUT_DIR / "cleaned_orders.csv", index=False)

peak_including = monthly.loc[
    monthly["revenue_including_outliers_inr"].idxmax()
]
peak_excluding = monthly.loc[
    monthly["revenue_excluding_outliers_inr"].idxmax()
]

findings = {
    "project": "Mamaearth Growth Analytics",
    "data_note": (
        "This project uses a synthetic educational dataset. "
        "These are not official Mamaearth business figures."
    ),
    "raw_order_count": int(raw_order_count),
    "cleaned_order_count": int(len(cleaned)),
    "duplicate_submissions_removed": int(duplicates_removed),
    "cleaned_revenue_inr": round(float(cleaned["order_value_inr"].sum()), 2),
    "quantity_outlier_count": int(cleaned["is_quantity_outlier"].sum()),
    "payment_method_return_rates": payment_returns.to_dict(orient="records"),
    "monthly_revenue": monthly.to_dict(orient="records"),
    "peak_month_including_outliers": {
        "month": str(peak_including["month"]),
        "revenue_inr": float(peak_including["revenue_including_outliers_inr"]),
    },
    "peak_month_excluding_outliers": {
        "month": str(peak_excluding["month"]),
        "revenue_inr": float(peak_excluding["revenue_excluding_outliers_inr"]),
    },
}

findings_path = NARRATOR_DIR / "findings.json"
with open(findings_path, "w", encoding="utf-8") as file:
    json.dump(findings, file, indent=2, default=str)

print(f"Raw orders: {raw_order_count}")
print(f"Cleaned orders: {len(cleaned)}")
print(f"Duplicate submissions removed: {duplicates_removed}")
print(f"Findings saved to: {findings_path}")
print("findings.json created successfully.")