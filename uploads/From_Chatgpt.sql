-- ECOMMERCE AND LOGISTICS SYSTEM SCHEMA

-- Drop existing tables to prevent conflicts
DROP SCHEMA IF EXISTS ecommerce CASCADE;
CREATE SCHEMA ecommerce;
SET search_path TO ecommerce;

-- USERS TABLE
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (char_length(password_hash) > 20)
);

-- ADDRESSES
CREATE TABLE addresses (
    address_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    street VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    zip_code VARCHAR(20),
    is_primary BOOLEAN DEFAULT FALSE
);

-- PRODUCTS
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL CHECK (price > 0),
    weight_grams INT CHECK (weight_grams > 0),
    stock_quantity INT DEFAULT 0 CHECK (stock_quantity >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CATEGORIES
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- PRODUCT-CATEGORY (Many-to-Many)
CREATE TABLE product_categories (
    product_id INT REFERENCES products(product_id) ON DELETE CASCADE,
    category_id INT REFERENCES categories(category_id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, category_id)
);

-- ORDERS
CREATE TABLE orders (
    order_id BIGSERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) CHECK (status IN ('PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED')),
    total_amount NUMERIC(12,2) CHECK (total_amount >= 0)
) PARTITION BY RANGE (order_date);

-- Example Partitioning (by year)
CREATE TABLE orders_2024 PARTITION OF orders
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE orders_2025 PARTITION OF orders
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- ORDER ITEMS
CREATE TABLE order_items (
    order_id BIGINT REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    price_at_purchase NUMERIC(10,2),
    PRIMARY KEY (order_id, product_id)
);

-- SHIPMENTS
CREATE TABLE shipments (
    shipment_id SERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES orders(order_id),
    shipped_date TIMESTAMP,
    delivery_date TIMESTAMP,
    tracking_number VARCHAR(100) UNIQUE,
    carrier VARCHAR(50)
);

-- INVENTORY TRIGGER
CREATE FUNCTION reduce_inventory() RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET stock_quantity = stock_quantity - NEW.quantity
    WHERE product_id = NEW.product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reduce_inventory
AFTER INSERT ON order_items
FOR EACH ROW
EXECUTE FUNCTION reduce_inventory();

-- VIEWS
CREATE VIEW v_user_order_summary AS
SELECT
    u.user_id,
    u.username,
    COUNT(o.order_id) AS total_orders,
    SUM(o.total_amount) AS lifetime_value
FROM users u
JOIN orders o ON o.user_id = u.user_id
GROUP BY u.user_id, u.username;

-- STORED PROCEDURE TO CANCEL ORDER
CREATE OR REPLACE FUNCTION cancel_order(order_to_cancel BIGINT) RETURNS VOID AS $$
BEGIN
    UPDATE orders SET status = 'CANCELLED' WHERE order_id = order_to_cancel;
    DELETE FROM order_items WHERE order_id = order_to_cancel;
    DELETE FROM shipments WHERE order_id = order_to_cancel;
END;
$$ LANGUAGE plpgsql;

-- INDEXES
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- AUDIT TABLE
CREATE TABLE order_audit (
    audit_id SERIAL PRIMARY KEY,
    order_id BIGINT,
    action VARCHAR(50),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AUDIT TRIGGER
CREATE FUNCTION log_order_change() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO order_audit (order_id, action)
    VALUES (NEW.order_id, TG_OP);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_order_audit
AFTER UPDATE OR DELETE ON orders
FOR EACH ROW
EXECUTE FUNCTION log_order_change();
