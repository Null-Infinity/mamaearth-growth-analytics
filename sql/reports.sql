-- Mamaearth Growth Analytics Project
-- Run these queries against mamaearth.db.

PRAGMA foreign_keys = ON;

-- =========================================================
-- REPORT A: Order totals, revenue, and average order value
-- NULL discounts are treated as 0%.
-- =========================================================
SELECT
    COUNT(*) AS total_orders,
    ROUND(SUM(
        quantity * price_inr *
        (1 - COALESCE(discount_pct, 0) / 100.0)
    ), 2) AS total_revenue_inr,
    ROUND(AVG(
        quantity * price_inr *
        (1 - COALESCE(discount_pct, 0) / 100.0)
    ), 2) AS average_order_value_inr
FROM orders
JOIN products USING (product_id);


-- =========================================================
-- REPORT B: Ratings available and missing
-- =========================================================
SELECT
    COUNT(*) AS total_orders,
    COUNT(rating) AS orders_with_rating,
    COUNT(*) - COUNT(rating) AS orders_without_rating
FROM orders;


-- =========================================================
-- REPORT C1: Customers who placed zero orders using LEFT JOIN
-- =========================================================
SELECT c.customer_id, c.customer_name
FROM customers AS c
LEFT JOIN orders AS o
    ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL
ORDER BY c.customer_id;


-- =========================================================
-- REPORT C2: Customers who placed zero orders using NOT IN
-- =========================================================
SELECT customer_id, customer_name
FROM customers
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM orders
)
ORDER BY customer_id;


-- =========================================================
-- REPORT D: Return rate by city
-- Only cities with more than 20 orders are included.
-- =========================================================
SELECT
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(100.0 * SUM(o.returned) / COUNT(o.order_id), 2)
        AS return_rate_pct
FROM orders AS o
JOIN customers AS c
    ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING COUNT(o.order_id) > 20
ORDER BY return_rate_pct DESC;


-- =========================================================
-- REPORT E: Top five customers by spend
-- Ranks 3 through 5 are shown using LIMIT and OFFSET.
-- =========================================================
SELECT
    c.customer_id,
    c.customer_name,
    ROUND(SUM(
        o.quantity * p.price_inr *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS total_spend_inr
FROM customers AS c
JOIN orders AS o
    ON c.customer_id = o.customer_id
JOIN products AS p
    ON o.product_id = p.product_id
GROUP BY c.customer_id, c.customer_name
ORDER BY total_spend_inr DESC, c.customer_id
LIMIT 5;


-- Ranks 3, 4, and 5
SELECT
    c.customer_id,
    c.customer_name,
    ROUND(SUM(
        o.quantity * p.price_inr *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS total_spend_inr
FROM customers AS c
JOIN orders AS o
    ON c.customer_id = o.customer_id
JOIN products AS p
    ON o.product_id = p.product_id
GROUP BY c.customer_id, c.customer_name
ORDER BY total_spend_inr DESC, c.customer_id
LIMIT 3 OFFSET 2;


-- =========================================================
-- REPORT F: Order count and revenue by product category
-- =========================================================
SELECT
    p.category,
    COUNT(o.order_id) AS order_count,
    ROUND(SUM(
        o.quantity * p.price_inr *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS revenue_inr
FROM orders AS o
JOIN products AS p
    ON o.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue_inr DESC;


-- =========================================================
-- REPORT G: Customer names starting with A
-- =========================================================
SELECT customer_id, customer_name
FROM customers
WHERE customer_name LIKE 'A%'
ORDER BY customer_name;


-- =========================================================
-- REPORT H: Distinct customer acquisition sources
-- =========================================================
SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;


-- =========================================================
-- REPORT I: Add and update loyalty tiers
-- Tier 1 city = Gold, all other tiers = Silver.
-- =========================================================
ALTER TABLE customers
ADD COLUMN loyalty_tier TEXT;

UPDATE customers
SET loyalty_tier = CASE
    WHEN city_tier = 1 THEN 'Gold'
    ELSE 'Silver'
END;

SELECT
    customer_id,
    customer_name,
    city_tier,
    loyalty_tier
FROM customers
ORDER BY customer_id;
SELECT COUNT(*) AS customers_with_no_orders
FROM customers c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.customer_id = c.customer_id
);