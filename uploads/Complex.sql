
-- Customers table
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100),
    email VARCHAR(100)
);

-- Orders table
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    total_amount DECIMAL(10, 2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Products table
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    price DECIMAL(10, 2)
);

-- Order Items table
CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Reviews table
CREATE TABLE reviews (
    review_id INT PRIMARY KEY,
    product_id INT,
    customer_id INT,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    review_date DATE,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);


-- Sample customers
INSERT INTO customers VALUES
(1, 'Alice Johnson', 'alice@example.com'),
(2, 'Bob Smith', 'bob@example.com'),
(3, 'Charlie Lee', 'charlie@example.com');

-- Sample products
INSERT INTO products VALUES
(101, 'Laptop', 1200.00),
(102, 'Smartphone', 800.00),
(103, 'Tablet', 300.00),
(104, 'Headphones', 150.00);

-- Sample orders
INSERT INTO orders VALUES
(1001, 1, '2024-01-15', 1950.00),
(1002, 2, '2024-02-20', 950.00),
(1003, 1, '2024-03-10', 150.00);

-- Sample order items
INSERT INTO order_items VALUES
(1, 1001, 101, 1),
(2, 1001, 104, 5),
(3, 1002, 102, 1),
(4, 1003, 104, 1);

-- Sample reviews
INSERT INTO reviews VALUES
(1, 101, 1, 5, 'Excellent laptop!', '2024-01-20'),
(2, 104, 1, 4, 'Great headphones.', '2024-01-22'),
(3, 104, 2, 4, 'Good quality.', '2024-02-21'),
(4, 104, 3, 3, 'Decent value.', '2024-03-05'),
(5, 102, 2, 5, 'Loving the phone.', '2024-02-25');

WITH customer_orders AS (
    SELECT
        c.customer_id,
        c.customer_name,
        COUNT(o.order_id) AS total_orders,
        SUM(o.total_amount) AS total_spent
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.customer_name
),
product_ratings AS (
    SELECT
        p.product_id,
        p.product_name,
        AVG(r.rating) AS average_rating,
        COUNT(r.review_id) AS review_count
    FROM products p
    LEFT JOIN reviews r ON p.product_id = r.product_id
    GROUP BY p.product_id, p.product_name
    HAVING COUNT(r.review_id) >= 3
)
SELECT
    co.customer_name,
    co.total_orders,
    co.total_spent,
    pr.product_name,
    pr.average_rating
FROM customer_orders co
JOIN orders o ON co.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN product_ratings pr ON p.product_id = pr.product_id
ORDER BY co.total_spent DESC, co.total_orders DESC;
