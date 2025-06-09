
-- ✅ Valid UPDATE query
UPDATE users SET is_active = 1 WHERE id = 1;

-- ❌ UPDATE without WHERE clause (could update all rows)
UPDATE users SET is_active = 0;

-- ❌ Updating a non-existent column
UPDATE users SET activation_status = 1 WHERE id = 2;

-- ❌ Wrong table name
UPDATE user SET is_active = 1 WHERE id = 3;

-- ❌ Syntax error: missing SET keyword
UPDATE users is_active = 1 WHERE id = 4;

-- ❌ Type mismatch (assuming age is INT)
UPDATE users SET age = 'twenty' WHERE id = 5;

-- ✅ Conditional update with multiple fields
UPDATE users SET name = 'Bob', age = 30 WHERE id = 6;

-- ❌ Invalid WHERE clause syntax
UPDATE users SET is_active = 1 WHERE;

-- ❌ Invalid value (assuming gender is ENUM('male','female'))
UPDATE users SET gender = 'robot' WHERE id = 7;

-- ✅ Update based on subquery (valid, but complex)
UPDATE users SET is_active = 1 WHERE id IN (SELECT user_id FROM logins WHERE last_login > '2024-01-01');
