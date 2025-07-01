
-- Drop table if it exists
DROP TABLE IF EXISTS customers;

-- Create customers table
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    address TEXT
);

-- Insert sample customers
INSERT INTO customers (customer_id, name, email, phone, address) VALUES
(1, 'Alice Smith', 'alice@example.com', '123-456-7890', '123 Maple Street, Springfield'),
(2, 'Bob Johnson', 'bob@example.com', '234-567-8901', '456 Oak Avenue, Metropolis'),
(3, 'Charlie Lee', 'charlie@example.com', '345-678-9012', '789 Pine Road, Gotham');
