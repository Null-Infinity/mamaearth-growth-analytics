-- Mamaearth Growth Analytics Project
PRAGMA foreign_keys = ON;

-- Clear tables in foreign-key-safe order.
DELETE FROM orders;
DELETE FROM products;
DELETE FROM customers;

-- Import the original CSV files.
.mode csv
.import --skip 1 data/customers.csv customers
.import --skip 1 data/products.csv products
.import --skip 1 data/orders.csv orders

-- Verify the imported row counts.
.mode column
.headers on

SELECT 'customers' AS table_name, COUNT(*) AS row_count
FROM customers;

SELECT 'products' AS table_name, COUNT(*) AS row_count
FROM products;

SELECT 'orders' AS table_name, COUNT(*) AS row_count
FROM orders;