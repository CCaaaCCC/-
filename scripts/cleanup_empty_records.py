import re

from sqlalchemy import func

from app.db.models import AIConversation, AIConversationMessage, Assignment, AssignmentSubmission
from app.db.session import SessionLocal


def cleanup_placeholder_conversations(session) -> int:
    deleted = 0

    user_ids = [row[0] for row in session.query(AIConversation.user_id).distinct().all() if row[0] is not None]
    for user_id in user_ids:
        conversations = (
            session.query(AIConversation)
            .filter(AIConversation.user_id == user_id)
            .order_by(AIConversation.updated_at.desc(), AIConversation.id.desc())
            .all()
        )

        placeholders = []
        for conv in conversations:
            message_count = (
                session.query(func.count(AIConversationMessage.id))
                .filter(AIConversationMessage.conversation_id == conv.id)
                .scalar()
                or 0
            )
            title = (conv.title or "").strip()
            if message_count == 0 and (title == "" or title == "新对话"):
                placeholders.append(conv)

        # Keep at most one placeholder conversation per user.
        for conv in placeholders[1:]:
            session.delete(conv)
            deleted += 1

    return deleted


def cleanup_probe_assignments(session) -> int:
    deleted = 0
    probe_pattern = re.compile(r"^UX闭环测试任务-\d+$")

    assignments = session.query(Assignment).all()
    for assignment in assignments:
        title = (assignment.title or "").strip()
        description = (assignment.description or "").strip()
        requirement = (assignment.requirement or "").strip()

        submission_count = (
            session.query(func.count(AssignmentSubmission.id))
            .filter(AssignmentSubmission.assignment_id == assignment.id)
            .scalar()
            or 0
        )

        is_empty_assignment = not title and not description and not requirement
        is_probe_assignment = (
            bool(probe_pattern.match(title))
            and "自动探测脚本创建" in description
            and submission_count == 0
        )

        if is_empty_assignment or is_probe_assignment:
            session.delete(assignment)
            deleted += 1

    return deleted


def main() -> int:
    session = SessionLocal()
    try:
        deleted_conversations = cleanup_placeholder_conversations(session)
        deleted_assignments = cleanup_probe_assignments(session)
        session.commit()

        print(
            f"cleanup completed: deleted_conversations={deleted_conversations}, "
            f"deleted_assignments={deleted_assignments}"
        )
        return 0
    except Exception as exc:
        session.rollback()
        print(f"cleanup failed: {exc}")
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
