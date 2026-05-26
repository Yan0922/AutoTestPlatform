-- 初始化算法测试平台数据库
-- 用法: mysql -u root -p < init_mysql.sql

CREATE DATABASE IF NOT EXISTS algotest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'test'@'localhost' IDENTIFIED BY 'test123';
CREATE USER IF NOT EXISTS 'test'@'%' IDENTIFIED BY 'test123';

GRANT ALL PRIVILEGES ON algotest.* TO 'test'@'localhost';
GRANT ALL PRIVILEGES ON algotest.* TO 'test'@'%';

FLUSH PRIVILEGES;

SHOW DATABASES LIKE 'algotest';
SELECT User, Host FROM mysql.user WHERE User = 'test';
