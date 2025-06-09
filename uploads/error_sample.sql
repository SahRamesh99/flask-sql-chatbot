
-- Missing semicolon and typo in SELECT
SELEC * FROM users

-- Reference to a non-existing table
SELECT * FROM non_existing_table;

-- Incorrect data type for column (assuming `age` is INT)
INSERT INTO users (id, name, age) VALUES (1, 'Alice', 'twenty-five');

-- Syntax error: missing closing parenthesis
INSERT INTO products (id, name, price VALUES (101, 'Laptop', 999.99);

-- Duplicate column name
SELECT id, name, id FROM users;

-- Invalid SQL function
SELECT MADEUP_FUNCTION(name) FROM users;

-- Using reserved word as column name without escaping
SELECT select FROM orders;

-- Foreign key violation (assuming product_id 999 doesn't exist)
INSERT INTO order_items (order_id, product_id, quantity) VALUES (1, 999, 2);

-- Update without WHERE clause (could cause unintended full update)
UPDATE users SET is_active = 0;

-- Drop table without IF EXISTS
DROP TABLE archived_users;
