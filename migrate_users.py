"""
数据库迁移脚本 - 添加用户管理相关字段

使用方法：
    .venv\Scripts\python.exe migrate_users.py
"""

import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '222710',
    'database': 'smart_greenhouse'
}

def migrate():
    """执行数据库迁移"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("🔧 开始数据库迁移...")
    
    try:
        # 检查并添加 users 表字段
        print("\n📋 检查 users 表字段...")
        
        columns_to_add = [
            ("email", "VARCHAR(100) UNIQUE"),
            ("real_name", "VARCHAR(50)"),
            ("student_id", "VARCHAR(20) UNIQUE"),
            ("teacher_id", "VARCHAR(20) UNIQUE"),
            ("class_id", "INT"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("created_by", "INT"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        ]
        
        # 获取现有列
        cursor.execute("SHOW COLUMNS FROM users")
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                print(f"  ✓ 添加字段：{col_name}")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            else:
                print(f"  - 字段已存在：{col_name}")
        
        # 创建 classes 表
        print("\n📋 检查 classes 表...")
        cursor.execute("SHOW TABLES LIKE 'classes'")
        if not cursor.fetchone():
            print("  ✓ 创建 classes 表")
            cursor.execute("""
                CREATE TABLE classes (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    class_name VARCHAR(100) NOT NULL,
                    grade VARCHAR(20),
                    teacher_id INT,
                    description VARCHAR(500),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (teacher_id) REFERENCES users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            print("  - classes 表已存在")
        
        # 创建 user_operation_logs 表
        print("\n📋 检查 user_operation_logs 表...")
        cursor.execute("SHOW TABLES LIKE 'user_operation_logs'")
        if not cursor.fetchone():
            print("  ✓ 创建 user_operation_logs 表")
            cursor.execute("""
                CREATE TABLE user_operation_logs (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    operator_id INT NOT NULL,
                    operation_type VARCHAR(20) NOT NULL,
                    target_user_id INT,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (operator_id) REFERENCES users(id),
                    INDEX idx_operator (operator_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        else:
            print("  - user_operation_logs 表已存在")
        
        # 添加外键约束
        print("\n📋 添加外键约束...")
        try:
            cursor.execute("ALTER TABLE users ADD CONSTRAINT fk_users_class FOREIGN KEY (class_id) REFERENCES classes(id)")
            print("  ✓ 添加 users.class_id 外键")
        except Exception as e:
            if "Duplicate key" not in str(e):
                print(f"  - 外键已存在或无法添加：fk_users_class")
        
        conn.commit()
        print("\n✅ 数据库迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败：{e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 用户管理数据库迁移工具")
    print("=" * 50)
    migrate()
