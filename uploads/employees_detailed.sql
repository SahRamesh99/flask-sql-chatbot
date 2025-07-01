
-- Drop tables if they exist
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

-- Create departments table
CREATE TABLE departments (
    department_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Create employees table
CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    position VARCHAR(50),
    hire_date DATE,
    salary DECIMAL(10,2),
    department_id INT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- Insert sample departments
INSERT INTO departments (department_id, name) VALUES
(1, 'Management'),
(2, 'Sales'),
(3, 'Support'),
(4, 'Engineering');

-- Insert sample employees
INSERT INTO employees (employee_id, name, email, phone, position, hire_date, salary, department_id) VALUES
(1, 'David Miller', 'david.miller@example.com', '456-789-0123', 'Manager', '2020-01-15', 85000.00, 1),
(2, 'Emma Davis', 'emma.davis@example.com', '567-890-1234', 'Sales Associate', '2021-06-23', 55000.00, 2),
(3, 'Frank Wilson', 'frank.wilson@example.com', '678-901-2345', 'Support Specialist', '2022-03-30', 48000.00, 3),
(4, 'Grace Lee', 'grace.lee@example.com', '789-012-3456', 'Software Engineer', '2023-09-01', 92000.00, 4),
(5, 'Henry Adams', 'henry.adams@example.com', '890-123-4567', 'DevOps Engineer', '2021-11-15', 88000.00, 4);
