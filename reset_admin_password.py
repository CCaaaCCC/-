"""
重置 admin 用户密码脚本

使用方法：
    .venv\Scripts\python.exe reset_admin_password.py 新密码
"""

import sys
from main import SessionLocal, User, pwd_context

def reset_admin_password(new_password: str):
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("❌ admin 用户不存在")
            return
        
        admin.hashed_password = pwd_context.hash(new_password)
        db.commit()
        print(f"✅ admin 密码已重置为：{new_password}")
        print("请使用新密码登录")
    except Exception as e:
        db.rollback()
        print(f"❌ 重置失败：{e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("📝 使用方法：.venv\\Scripts\\python.exe reset_admin_password.py 新密码")
        print("示例：.venv\\Scripts\\python.exe reset_admin_password.py admin123")
        sys.exit(1)
    
    new_password = sys.argv[1]
    if len(new_password) < 6:
        print("❌ 密码长度至少 6 位")
        sys.exit(1)
    
    reset_admin_password(new_password)
