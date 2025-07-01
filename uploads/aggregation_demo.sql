
-- Drop and recreate the necessary tables
DROP TABLE IF EXISTS Sales;
DROP TABLE IF EXISTS Products;

-- Products table
CREATE TABLE Products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10, 2)
);

-- Sales table
CREATE TABLE Sales (
    sale_id INT PRIMARY KEY,
    product_id INT,
    quantity INT,
    sale_date DATE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

-- Sample data for Products
INSERT INTO Products VALUES
(1, 'Laptop', 'Electronics', 1200.00),
(2, 'Mouse', 'Electronics', 25.00),
(3, 'Desk', 'Furniture', 300.00),
(4, 'Chair', 'Furniture', 150.00);

-- Sample data for Sales
INSERT INTO Sales VALUES
(101, 1, 2, '2024-01-15'),
(102, 2, 5, '2024-01-16'),
(103, 3, 1, '2024-01-17'),
(104, 4, 3, '2024-01-18'),
(105, 2, 4, '2024-02-01'),
(106, 1, 1, '2024-02-10'),
(107, 3, 2, '2024-02-15');

-- Aggregation Functions

-- COUNT: Number of sales per product
SELECT p.product_name, COUNT(s.sale_id) AS total_sales
FROM Products p
LEFT JOIN Sales s ON p.product_id = s.product_id
GROUP BY p.product_name;

-- SUM: Total quantity sold per category
SELECT p.category, SUM(s.quantity) AS total_quantity
FROM Products p
JOIN Sales s ON p.product_id = s.product_id
GROUP BY p.category;

-- AVG: Average quantity per sale
SELECT p.product_name, AVG(s.quantity) AS avg_quantity
FROM Products p
JOIN Sales s ON p.product_id = s.product_id
GROUP BY p.product_name;

-- MIN and MAX: Min and Max quantity sold per product
SELECT p.product_name, MIN(s.quantity) AS min_qty, MAX(s.quantity) AS max_qty
FROM Products p
JOIN Sales s ON p.product_id = s.product_id
GROUP BY p.product_name;

-- Aggregate with HAVING: Products with total quantity > 5
SELECT p.product_name, SUM(s.quantity) AS total_qty
FROM Products p
JOIN Sales s ON p.product_id = s.product_id
GROUP BY p.product_name
HAVING SUM(s.quantity) > 5;


