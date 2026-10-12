import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "mamaearth.db"
REPORTS_PATH = PROJECT_ROOT / "sql" / "reports.sql"

sql_text = REPORTS_PATH.read_text(encoding="utf-8")
connection = sqlite3.connect(DB_PATH)

try:
    connection.execute("PRAGMA foreign_keys = ON")

    statements = [
        statement.strip()
        for statement in sql_text.split(";")
        if statement.strip()
    ]

    for statement in statements:
        # Skip adding the loyalty column if it already exists.
        if statement.upper().startswith("ALTER TABLE CUSTOMERS"):
            columns = [
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(customers)"
                ).fetchall()
            ]

            if "loyalty_tier" in columns:
                print("\nLoyalty column already exists; skipping ALTER TABLE.")
                continue

        cursor = connection.execute(statement)

        if cursor.description:
            print("\n" + "=" * 70)
            print(statement.splitlines()[0])
            print("=" * 70)

            print(" | ".join(item[0] for item in cursor.description))

            for row in cursor.fetchall():
                print(" | ".join(str(value) for value in row))

    connection.commit()
    print("\nAll SQL reports executed successfully.")

except Exception as error:
    connection.rollback()
    print("SQL ERROR:", error)
    raise

finally:
    connection.close()