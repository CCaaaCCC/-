-- 此文件已废弃，数据库表由 SQLAlchemy 自动创建
-- 如果需要手动初始化，请使用 main.py 中的 startup_event
-- 以下是旧的 SQL，仅供参考

-- 创建数据库（如果不存在）
-- CREATE DATABASE IF NOT EXISTS smart_greenhouse DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE smart_greenhouse;

-- 用户表
-- CREATE TABLE IF NOT EXISTS `users` (
--     `id` INT AUTO_INCREMENT PRIMARY KEY,
--     `username` VARCHAR(50) NOT NULL UNIQUE,
--     `password_hash` VARCHAR(255) NOT NULL,
--     `role` ENUM('admin', 'teacher', 'student') NOT NULL DEFAULT 'student',
--     `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- ) ENGINE=InnoDB;

-- 设备表（注意：缺少 pump_state 等字段，与 main.py 不匹配）
-- CREATE TABLE IF NOT EXISTS `devices` (
--     `id` INT AUTO_INCREMENT PRIMARY KEY,
--     `device_name` VARCHAR(100) NOT NULL,
--     `status` TINYINT DEFAULT 1,
--     `last_seen` TIMESTAMP NULL DEFAULT NULL,
--     `pump_state` TINYINT DEFAULT 0,
--     `fan_state` TINYINT DEFAULT 0,
--     `light_state` TINYINT DEFAULT 0,
--     `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- ) ENGINE=InnoDB;

-- 传感器数据表
-- CREATE TABLE IF NOT EXISTS `sensor_readings` (
--     `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
--     `device_id` INT NOT NULL,
--     `temp` DECIMAL(5, 2),
--     `humidity` DECIMAL(5, 2),
--     `soil_moisture` DECIMAL(5, 2),
--     `light` DECIMAL(10, 2),
--     `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     CONSTRAINT `fk_device_readings` FOREIGN KEY (`device_id`) REFERENCES `devices`(`id`) ON DELETE CASCADE,
--     INDEX `idx_device_timestamp` (`device_id`, `timestamp`),
--     INDEX `idx_timestamp` (`timestamp`)
-- ) ENGINE=InnoDB;

-- 示例数据（密码哈希需正确生成）
-- INSERT INTO `users` (`username`, `password_hash`, `role`) VALUES
-- ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Le0fBp.3r5q3hK9K', 'admin'),
-- ('teacher', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Le0fBp.3r5q3hK9K', 'teacher'),
-- ('student', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Le0fBp.3r5q3hK9K', 'student');

-- INSERT INTO `devices` (`device_name`, `status`, `pump_state`, `fan_state`, `light_state`) VALUES
-- ('Default Greenhouse', 1, 0, 0, 0);
