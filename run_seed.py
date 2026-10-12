import sqlite3
import pandas as pd
from pathlib import Path

# Locate the project folders
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
SQL_DIR = PROJECT_ROOT / "sql"

DB_PATH = PROJECT_ROOT / "mamaearth.db"

# Create or open the SQLite database
connection = sqlite3.connect(DB_PATH)

try:
    connection.execute("PRAGMA foreign_keys = ON")

    # Rebuild the database tables using schema.sql
    schema_path = SQL_DIR / "schema.sql"
    schema = schema_path.read_text(encoding="utf-8")

    connection.executescript("""
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
    """)

    connection.executescript(schema)

    # Import the original CSV files without cleaning their data
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    orders = pd.read_csv(DATA_DIR / "orders.csv")

    customers.to_sql("customers", connection, if_exists="append", index=False)
    products.to_sql("products", connection, if_exists="append", index=False)
    orders.to_sql("orders", connection, if_exists="append", index=False)

    # Confirm imported row counts
    print("Database created:", DB_PATH.name)

    for table in ("customers", "products", "orders"):
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        print(f"{table}: {count} rows")

    print("\nSeed data loaded successfully.")

except Exception as error:
    print("ERROR:", error)
    raise

finally:
    connection.close()