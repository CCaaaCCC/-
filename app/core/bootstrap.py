import os

from app.core.config import settings
from app.core.security import pwd_context
from app.db.session import SessionLocal
from app.db.models import Class, ContentCategory, Device, User

def init_demo_data() -> None:
    """Initialize presentation/demo data silently if configured."""
    if not settings.seed_demo_data:
        return

    db = SessionLocal()
    try:
        admin_pw = os.getenv("DEMO_ADMIN_PASSWORD")
        teacher_pw = os.getenv("DEMO_TEACHER_PASSWORD")
        student_pw = os.getenv("DEMO_STUDENT_PASSWORD")

        if not (admin_pw and teacher_pw and student_pw):
            raise RuntimeError(
                "SEED_DEMO_DATA=true requires DEMO_ADMIN_PASSWORD, DEMO_TEACHER_PASSWORD, DEMO_STUDENT_PASSWORD"
            )

        users = [
            ("admin", admin_pw, "admin"),
            ("teacher", teacher_pw, "teacher"),
            ("student", student_pw, "student"),
        ]
        
        for username, password, role in users:
            if not db.query(User).filter(User.username == username).first():
                hashed_pw = pwd_context.hash(password)
                db.add(User(username=username, hashed_password=hashed_pw, role=role))
                
        if not db.query(Device).first():
            db.add(
                Device(
                    device_name="Default greenhouse",
                    status=1,
                    pump_state=0,
                    fan_state=0,
                    light_state=0,
                )
            )

        if not db.query(ContentCategory).first():
            categories = [
                ContentCategory(name="农作物习性", description="各种农作物的生长习性和环境需求", sort_order=1),
                ContentCategory(name="植物百科", description="植物分类和特征介绍", sort_order=2),
                ContentCategory(name="自然科学", description="自然科学基础知识", sort_order=3),
                ContentCategory(name="实验指导", description="实验步骤和操作指南", sort_order=4),
            ]
            for cat in categories:
                db.add(cat)
            db.commit()

            for cat in categories:
                db.refresh(cat)

            sub_categories = [
                ContentCategory(name="温度需求", parent_id=categories[0].id, description="不同作物的温度适应性", sort_order=1),
                ContentCategory(name="光照需求", parent_id=categories[0].id, description="光照对作物生长的影响", sort_order=2),
                ContentCategory(name="水分需求", parent_id=categories[0].id, description="作物灌溉和水分管理", sort_order=3),
                ContentCategory(name="土壤要求", parent_id=categories[0].id, description="土壤类型和肥料需求", sort_order=4),
            ]
            for sub_cat in sub_categories:
                db.add(sub_cat)
            db.commit()

        if not db.query(Class).first():
            teacher_user = db.query(User).filter(User.role == "teacher").first()
            teacher_id = teacher_user.id if teacher_user else None

            classes = [
                Class(class_name="三年级 1 班", grade="三年级", description="2024 级 1 班", teacher_id=teacher_id),
                Class(class_name="三年级 2 班", grade="三年级", description="2024 级 2 班", teacher_id=teacher_id),
                Class(class_name="四年级 1 班", grade="四年级", description="2023 级 1 班", teacher_id=teacher_id),
            ]
            for cls in classes:
                db.add(cls)
            db.commit()
            
    finally:
        db.close()
