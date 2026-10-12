PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    city TEXT,
    city_tier INTEGER,
    signup_date TEXT,
    acquisition_source TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price_inr REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    discount_pct REAL,
    payment_method TEXT NOT NULL,
    rating REAL,
    returned INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);