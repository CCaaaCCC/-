import os
import secrets

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.db.models import Class, Device, User


INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _generate_invite_code(db) -> str:
    while True:
        code = "".join(secrets.choice(INVITE_CODE_ALPHABET) for _ in range(8))
        exists = db.query(Class).filter(Class.invite_code == code).first()
        if not exists:
            return code

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
                hashed_pw = hash_password(password)
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

        if not db.query(Class).first():
            teacher_user = db.query(User).filter(User.role == "teacher").first()
            teacher_id = teacher_user.id if teacher_user else None

            classes = [
                Class(
                    class_name="三年级 1 班",
                    grade="三年级",
                    description="2024 级 1 班",
                    teacher_id=teacher_id,
                    invite_code=_generate_invite_code(db),
                ),
                Class(
                    class_name="三年级 2 班",
                    grade="三年级",
                    description="2024 级 2 班",
                    teacher_id=teacher_id,
                    invite_code=_generate_invite_code(db),
                ),
                Class(
                    class_name="四年级 1 班",
                    grade="四年级",
                    description="2023 级 1 班",
                    teacher_id=teacher_id,
                    invite_code=_generate_invite_code(db),
                ),
            ]
            for cls in classes:
                db.add(cls)
            db.commit()
            
    finally:
        db.close()
