import os
import sys

from passlib.context import CryptContext


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.session import SessionLocal
from app.db.models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main() -> None:
    # Unified test password for all default demo users to support repeatable E2E probes.
    test_password = "Test1234A"
    usernames = ["admin", "teacher", "student", "student2", "student3"]

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.username.in_(usernames)).all()
        found = {u.username for u in users}
        missing = [u for u in usernames if u not in found]

        for user in users:
            user.hashed_password = pwd_context.hash(test_password)

        db.commit()
        print(f"updated={len(users)} password={test_password}")
        if missing:
            print("missing=" + ",".join(missing))
    finally:
        db.close()


if __name__ == "__main__":
    main()
