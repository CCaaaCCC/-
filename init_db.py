#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化数据库脚本
创建默认管理员、教师、学生账号
"""

import os
import secrets
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, engine
from app.db.models import User, Class, Device
from app.db.base import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def init_db():
    """初始化数据库"""
    print("🔄 正在初始化数据库...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")
    
    db = SessionLocal()
    
    try:
        # 检查是否已有管理员
        admin_exists = db.query(User).filter(User.role == 'admin').first()
        if admin_exists:
            print("⚠️  数据库中已存在管理员账号，跳过初始化")
            return
        
        # 创建默认管理员（密码可通过环境变量传入，未设置时生成强随机密码）
        default_admin_pw = os.getenv("DEFAULT_ADMIN_PASSWORD")
        if not default_admin_pw:
            default_admin_pw = secrets.token_urlsafe(12)

        admin = User(
            username="admin",
            hashed_password=hash_password(default_admin_pw),
            role="admin",
            email="admin@school.com",
            real_name="系统管理员",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("✅ 管理员账号创建成功：admin")
        print(f"   admin password: {default_admin_pw}")

        # 教师与学生默认密码可继承管理员密码或分别设置
        default_teacher_pw = os.getenv("DEFAULT_TEACHER_PASSWORD", default_admin_pw)

        # 创建默认教师
        teacher = User(
            username="teacher",
            hashed_password=hash_password(default_teacher_pw),
            role="teacher",
            email="teacher@school.com",
            real_name="张老师",
            teacher_id="T001",
            is_active=True
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        print("✅ 教师账号创建成功：teacher")
        print(f"   teacher password: {default_teacher_pw}")
        
        # 创建默认班级
        class1 = Class(
            class_name="三年级 1 班",
            grade="三年级",
            teacher_id=teacher.id,
            description="第一个班级",
            is_active=True
        )
        db.add(class1)
        db.commit()
        db.refresh(class1)
        print(f"✅ 班级创建成功：{class1.class_name}")
        
        # 创建默认学生
        students = [
            {"username": "student", "real_name": "李明", "student_id": "S001"},
            {"username": "student2", "real_name": "王芳", "student_id": "S002"},
            {"username": "student3", "real_name": "张伟", "student_id": "S003"},
        ]
        
        default_student_pw = os.getenv("DEFAULT_STUDENT_PASSWORD", default_admin_pw)
        for stu in students:
            student = User(
                username=stu["username"],
                hashed_password=hash_password(default_student_pw),
                role="student",
                real_name=stu["real_name"],
                student_id=stu["student_id"],
                class_id=class1.id,
                is_active=True
            )
            db.add(student)

        db.commit()
        print("✅ 学生账号创建成功：student / student2 / student3")
        print(f"   student password: {default_student_pw}")
        
        # 创建默认设备
        device = Device(
            device_name="大棚 1 号设备",
            status=1,
            pump_state=0,
            fan_state=0,
            light_state=0
        )
        db.add(device)
        db.commit()
        print(f"✅ 设备创建成功：{device.device_name}")
        
        # 绑定班级与设备
        from app.db.models import ClassDeviceBind
        bind = ClassDeviceBind(
            class_id=class1.id,
            device_id=device.id
        )
        db.add(bind)
        db.commit()
        print(f"✅ 班级与设备绑定成功")
        
        print("\n" + "=" * 50)
        print("🎉 数据库初始化完成！")
        print("=" * 50)
        print("\n默认账号：")
        print("  管理员：admin （密码见上方或设置环境变量 DEFAULT_ADMIN_PASSWORD）")
        print("  教师：teacher （密码见上方或设置环境变量 DEFAULT_TEACHER_PASSWORD）")
        print("  学生：student / student2 / student3 （密码见上方或设置环境变量 DEFAULT_STUDENT_PASSWORD）")
        print("=" * 50)
        
    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
