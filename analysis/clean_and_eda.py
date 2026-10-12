
from pathlib import Path
import pandas as pd

# Find the project folder automatically
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

# Load the three original CSV files
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")

# Inspect the data without changing the original files
print("=== CUSTOMERS ===")
print("Shape:", customers.shape)
print(customers.head())
print()

print("=== PRODUCTS ===")
print("Shape:", products.shape)
print(products.head())
print()

print("=== ORDERS ===")
print("Shape:", orders.shape)
print(orders.head())
print()

print("=== MISSING VALUES IN ORDERS ===")
print(orders.isna().sum())

print("\nData inspection completed.")

print("\n=== ORDER COLUMN NAMES ===")
print(orders.columns.tolist())

print("\n=== RAW PAYMENT METHODS ===")
print(orders["payment_method"].value_counts(dropna=False))


print("\n=== DUPLICATE SUBMISSION CHECK ===")

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

duplicate_mask = orders.duplicated(
    subset=natural_key,
    keep="first"
)

print("Duplicate submissions found:", duplicate_mask.sum())
print("\nDuplicate order IDs:")
print(orders.loc[duplicate_mask, "order_id"].tolist())


print("\n=== CLEANING ORDERS FOR ANALYSIS ===")

# Keep the original orders DataFrame unchanged
clean_orders = orders.copy()

# Remove duplicate submissions using the natural key
duplicate_mask = clean_orders.duplicated(
    subset=natural_key,
    keep="first"
)
dropped_ids = clean_orders.loc[duplicate_mask, "order_id"].tolist()
clean_orders = clean_orders.loc[~duplicate_mask].copy()

print("Dropped duplicate order IDs:", dropped_ids)
print("Orders remaining:", len(clean_orders))

# Standardize payment method capitalization
clean_orders["payment_method"] = (
    clean_orders["payment_method"].str.strip().str.upper()
)

print("\nPayment methods after standardization:")
print(clean_orders["payment_method"].value_counts())

# Fill missing discounts with 0%
clean_orders["discount_pct"] = clean_orders["discount_pct"].fillna(0)

# Fill missing ratings with the median of the remaining ratings
rating_median = clean_orders["rating"].median()
clean_orders["rating"] = clean_orders["rating"].fillna(rating_median)

print("\nMedian rating used:", rating_median)
print("Missing discounts remaining:", clean_orders["discount_pct"].isna().sum())
print("Missing ratings remaining:", clean_orders["rating"].isna().sum())



print("\n=== CLEANED DATA SUMMARY ===")
print("Orders:", len(clean_orders))
print("Payment methods:")
print(clean_orders["payment_method"].value_counts())

print("\n=== PRODUCT COLUMN NAMES ===")
print(products.columns.tolist())

# Merge orders with product details
analysis_data = clean_orders.merge(
    products,
    on="product_id",
    how="left",
    suffixes=("_order", "_product")
)

print("\n=== MERGED COLUMN NAMES ===")
print(analysis_data.columns.tolist())

print("\nProduct merge completed.")
print("Rows after merge:", len(analysis_data))
print("Missing product matches:", analysis_data["product_id"].isna().sum())


# Calculate order value after discount
analysis_data["order_value"] = (
    analysis_data["quantity"]
    * analysis_data["price_inr"]
    * (1 - analysis_data["discount_pct"] / 100)
)

print("\n=== ORDER VALUE CHECK ===")
print("Total revenue (INR):", round(analysis_data["order_value"].sum(), 2))
print("Average order value (INR):", round(analysis_data["order_value"].mean(), 2))
print("Missing order values:", analysis_data["order_value"].isna().sum())


print("\n=== QUANTITY OUTLIER ANALYSIS ===")

Q1 = analysis_data["quantity"].quantile(0.25)
Q3 = analysis_data["quantity"].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outlier_mask = (
    (analysis_data["quantity"] < lower_bound)
    | (analysis_data["quantity"] > upper_bound)
)

analysis_data["quantity_outlier"] = outlier_mask

print("Q1:", Q1)
print("Q3:", Q3)
print("IQR:", IQR)
print("Lower bound:", lower_bound)
print("Upper bound:", upper_bound)
print("Outlier rows:", outlier_mask.sum())

print("\nFlagged orders:")
print(
    analysis_data.loc[
        outlier_mask,
        ["order_id", "quantity", "order_value"]
    ].to_string(index=False)
)


print("\n=== RETURN RATE BY PAYMENT METHOD ===")

return_by_payment = (
    analysis_data.groupby("payment_method")
    .agg(
        total_orders=("order_id", "count"),
        returned_orders=("returned", "sum")
    )
    .reset_index()
)

return_by_payment["return_rate_pct"] = (
    return_by_payment["returned_orders"]
    / return_by_payment["total_orders"]
    * 100
)

print(return_by_payment.round(2).to_string(index=False))

cod_rate = return_by_payment.loc[
    return_by_payment["payment_method"] == "COD",
    "return_rate_pct"
].iloc[0]

other_rate = return_by_payment.loc[
    return_by_payment["payment_method"] != "COD",
    "return_rate_pct"
].mean()

print("\nCOD return rate (%):", round(cod_rate, 2))
print("Average return rate of other methods (%):", round(other_rate, 2))

if cod_rate > other_rate:
    print("Initial finding: COD has a higher return rate in this dataset.")
elif cod_rate < other_rate:
    print("Initial finding: COD has a lower return rate in this dataset.")
else:
    print("Initial finding: COD and other methods have equal return rates.")

    
print("\n=== RETURN RATE BY PAYMENT METHOD AND CITY TIER ===")

# Add city tier to the order-level data
analysis_data = analysis_data.merge(
    customers[["customer_id", "city_tier"]],
    on="customer_id",
    how="left"
)

return_by_segment = (
    analysis_data.groupby(
        ["payment_method", "city_tier"],
        dropna=False
    )
    .agg(
        total_orders=("order_id", "count"),
        returned_orders=("returned", "sum")
    )
    .reset_index()
)

return_by_segment["return_rate_pct"] = (
    return_by_segment["returned_orders"]
    / return_by_segment["total_orders"]
    * 100
)

return_by_segment = return_by_segment.sort_values(
    "return_rate_pct",
    ascending=False
)

print(return_by_segment.round(2).to_string(index=False))

print("\nHighest-return-rate segment:")
print(return_by_segment.head(1).round(2).to_string(index=False))

print(
    "\nOrders without a matched city tier:",
    analysis_data["city_tier"].isna().sum()
)
# STEP 18: Monthly revenue comparison with and without quantity outliers

print("\n" + "=" * 60)
print("STEP 18: MONTHLY REVENUE COMPARISON")
print("=" * 60)

# Ensure order dates are in the correct format
analysis_data["order_date"] = pd.to_datetime(
    analysis_data["order_date"], errors="coerce"
)

# Create a month column
analysis_data["month"] = (
    analysis_data["order_date"].dt.to_period("M").astype(str)
)

# Recalculate the quantity outlier flag using the IQR method
q1 = analysis_data["quantity"].quantile(0.25)
q3 = analysis_data["quantity"].quantile(0.75)
iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

analysis_data["is_quantity_outlier"] = (
    (analysis_data["quantity"] < lower_bound)
    | (analysis_data["quantity"] > upper_bound)
)

# Calculate monthly revenue including all orders
monthly_revenue_all = (
    analysis_data.dropna(subset=["month"])
    .groupby("month")["order_value"]
    .sum()
    .sort_index()
)

# Calculate monthly revenue excluding quantity outliers
monthly_revenue_without_outliers = (
    analysis_data.loc[
        ~analysis_data["is_quantity_outlier"]
    ]
    .dropna(subset=["month"])
    .groupby("month")["order_value"]
    .sum()
    .sort_index()
)

# Display monthly revenue including outliers
print("\nMonthly revenue INCLUDING outliers (INR):")
print(monthly_revenue_all.round(2).to_string())

# Display monthly revenue excluding outliers
print("\nMonthly revenue EXCLUDING quantity outliers (INR):")
print(monthly_revenue_without_outliers.round(2).to_string())

# Identify peak revenue months
if not monthly_revenue_all.empty:
    peak_month_all = monthly_revenue_all.idxmax()
    peak_revenue_all = monthly_revenue_all.max()

    print("\nPeak month INCLUDING outliers:")
    print(f"Month: {peak_month_all}")
    print(f"Revenue: INR {peak_revenue_all:,.2f}")

if not monthly_revenue_without_outliers.empty:
    peak_month_clean = monthly_revenue_without_outliers.idxmax()
    peak_revenue_clean = monthly_revenue_without_outliers.max()

    print("\nPeak month EXCLUDING quantity outliers:")
    print(f"Month: {peak_month_clean}")
    print(f"Revenue: INR {peak_revenue_clean:,.2f}")

# Compare the peak months
if (
    not monthly_revenue_all.empty
    and not monthly_revenue_without_outliers.empty
):
    print("\nPeak month comparison:")

    if peak_month_all == peak_month_clean:
        print("The peak revenue month remains the same.")
    else:
        print(
            "The peak revenue month changes after excluding "
            "quantity outliers."
        )

# Save the comparison for later use
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
outputs_folder = project_root / "outputs"
outputs_folder.mkdir(parents=True, exist_ok=True)

monthly_comparison = pd.concat(
    [
        monthly_revenue_all.rename("revenue_including_outliers"),
        monthly_revenue_without_outliers.rename(
            "revenue_excluding_outliers"
        ),
    ],
    axis=1,
).fillna(0)

monthly_comparison.to_csv(
    outputs_folder / "monthly_revenue_comparison.csv"
)

print("\nMonthly comparison saved successfully.")
print("File: outputs/monthly_revenue_comparison.csv")
print("\nPython analysis section completed.")