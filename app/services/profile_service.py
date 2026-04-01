import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.permission import get_allowed_class_ids, get_allowed_group_ids
from app.db.models import (
    Assignment,
    AssignmentSubmission,
    Class,
    PlantProfile,
    User,
    StudyGroup,
)


def _class_name_map(db: Session, class_ids: List[int]) -> Dict[int, str]:
    if not class_ids:
        return {}
    rows = db.query(Class.id, Class.class_name).filter(Class.id.in_(class_ids)).all()
    return {cid: cname for cid, cname in rows}


def get_my_profile(db: Session, current_user: User) -> Dict[str, Any]:
    """
    Build the same shape as `UserProfileResponse`, but returned as a plain dict
    so it can be reused by both main.py and APIRouter modules.
    """
    now = datetime.datetime.utcnow()

    allowed_class_ids = get_allowed_class_ids(db, current_user)
    allowed_group_ids: List[int] = []
    if allowed_class_ids is not None:
        allowed_group_ids = get_allowed_group_ids(db, current_user) or []

    # `class_name` shown on the profile card
    class_name: Optional[str] = None
    if current_user.role == "student" and current_user.class_id:
        cls = db.query(Class).filter(Class.id == current_user.class_id).first()
        class_name = cls.class_name if cls else None
    elif current_user.role == "teacher":
        teacher_classes = (
            db.query(Class).filter(Class.teacher_id == current_user.id).order_by(Class.created_at.desc()).all()
        )
        if teacher_classes:
            names = [c.class_name for c in teacher_classes[:3]]
            class_name = ", ".join(names) + ("..." if len(teacher_classes) > 3 else "")

    pending_assignments = 0
    overdue_assignments = 0
    assignments_to_grade = 0
    plants_in_class = 0
    upcoming_assignments: List[Dict[str, Any]] = []

    # ---------------- Student ----------------
    if current_user.role == "student":
        if not current_user.class_id:
            # no class => no todo / plant scope
            return {
                "id": current_user.id,
                "username": current_user.username,
                "role": current_user.role,
                "real_name": current_user.real_name,
                "avatar_url": current_user.avatar_url,
                "email": current_user.email,
                "class_id": current_user.class_id,
                "class_name": class_name,
                "todos": {
                    "pending_assignments": 0,
                    "overdue_assignments": 0,
                    "assignments_to_grade": 0,
                    "plants_in_class": 0,
                },
                "upcoming_assignments": [],
            }

        available_assignments = db.query(Assignment).filter(
            Assignment.class_id == current_user.class_id,
            Assignment.is_published == True,
        ).all()
        assignment_ids = [a.id for a in available_assignments]

        my_submissions = (
            db.query(AssignmentSubmission)
            .filter(
                AssignmentSubmission.student_id == current_user.id,
                AssignmentSubmission.assignment_id.in_(assignment_ids) if assignment_ids else False,
            )
            .all()
            if assignment_ids
            else []
        )

        submitted_ids = {s.assignment_id for s in my_submissions}
        pending = [a for a in available_assignments if a.id not in submitted_ids]

        pending_assignments = len(pending)
        overdue_assignments = len([a for a in pending if a.due_date and a.due_date < now])

        assignments_to_grade = len([s for s in my_submissions if getattr(s, "status", None) == "graded"])

        # align with permission scope: class_id + group_id plants
        condition = PlantProfile.class_id.in_([current_user.class_id]) if current_user.class_id else None
        if allowed_class_ids is None:
            # shouldn't happen for student
            plants_in_class = db.query(PlantProfile).count()
        else:
            if current_user.class_id:
                condition = PlantProfile.class_id == current_user.class_id
            if allowed_group_ids:
                condition = (PlantProfile.class_id == current_user.class_id) | (PlantProfile.group_id.in_(allowed_group_ids))
            else:
                condition = PlantProfile.class_id == current_user.class_id
            plants_in_class = db.query(PlantProfile).filter(condition).count()

        upcoming = sorted([a for a in pending if a.due_date], key=lambda x: x.due_date)[:5]

        class_ids_for_upcoming = {a.class_id for a in pending if a.class_id}
        class_map = _class_name_map(db, list(class_ids_for_upcoming))

        for item in upcoming:
            upcoming_assignments.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "device_id": item.device_id,
                    "class_id": item.class_id,
                    "teacher_id": item.teacher_id,
                    "start_date": item.start_date,
                    "due_date": item.due_date,
                    "requirement": item.requirement,
                    "template": item.template,
                    "is_published": item.is_published,
                    "created_at": item.created_at,
                    "submission_count": 0,
                    "class_name": class_map.get(item.class_id),
                }
            )

    # ---------------- Teacher ----------------
    elif current_user.role == "teacher":
        # class-scoped assignments + plant stats
        my_assignments_query = db.query(Assignment).filter(Assignment.teacher_id == current_user.id)
        if allowed_class_ids:
            my_assignments_query = my_assignments_query.filter(Assignment.class_id.in_(allowed_class_ids))
        my_assignments = my_assignments_query.all()
        my_assignment_ids = [a.id for a in my_assignments]

        pending_assignments = len([a for a in my_assignments if not a.is_published])
        assignments_to_grade = (
            db.query(AssignmentSubmission)
            .filter(
                AssignmentSubmission.assignment_id.in_(my_assignment_ids) if my_assignment_ids else False,
                AssignmentSubmission.status == "submitted",
            )
            .count()
            if my_assignment_ids
            else 0
        )

        if allowed_class_ids:
            plants_condition = PlantProfile.class_id.in_(allowed_class_ids)
            if allowed_group_ids:
                plants_condition = plants_condition | PlantProfile.group_id.in_(allowed_group_ids)
            plants_in_class = db.query(PlantProfile).filter(plants_condition).count()
        else:
            plants_in_class = 0

        upcoming_items = sorted(
            [a for a in my_assignments if a.due_date and a.due_date >= now], key=lambda x: x.due_date
        )[:5]

        class_ids_for_upcoming = {a.class_id for a in my_assignments if a.class_id}
        class_map = _class_name_map(db, list(class_ids_for_upcoming))

        for item in upcoming_items:
            upcoming_assignments.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "device_id": item.device_id,
                    "class_id": item.class_id,
                    "teacher_id": item.teacher_id,
                    "start_date": item.start_date,
                    "due_date": item.due_date,
                    "requirement": item.requirement,
                    "template": item.template,
                    "is_published": item.is_published,
                    "created_at": item.created_at,
                    "submission_count": 0,
                    "class_name": class_map.get(item.class_id),
                }
            )

    # ---------------- Admin (and other roles) ----------------
    else:
        pending_assignments = db.query(Assignment).filter(Assignment.is_published == False).count()
        assignments_to_grade = db.query(AssignmentSubmission).filter(AssignmentSubmission.status == "submitted").count()
        plants_in_class = db.query(PlantProfile).count()
        overdue_assignments = 0

        upcoming_items = (
            db.query(Assignment).filter(Assignment.due_date != None).order_by(Assignment.due_date.asc()).limit(5).all()
        )
        class_ids_for_upcoming = {a.class_id for a in upcoming_items if a.class_id}
        class_map = _class_name_map(db, list(class_ids_for_upcoming))
        for item in upcoming_items:
            upcoming_assignments.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "device_id": item.device_id,
                    "class_id": item.class_id,
                    "teacher_id": item.teacher_id,
                    "start_date": item.start_date,
                    "due_date": item.due_date,
                    "requirement": item.requirement,
                    "template": item.template,
                    "is_published": item.is_published,
                    "created_at": item.created_at,
                    "submission_count": 0,
                    "class_name": class_map.get(item.class_id),
                }
            )

    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "real_name": current_user.real_name,
        "avatar_url": current_user.avatar_url,
        "email": current_user.email,
        "class_id": current_user.class_id,
        "class_name": class_name,
        "todos": {
            "pending_assignments": pending_assignments,
            "overdue_assignments": overdue_assignments,
            "assignments_to_grade": assignments_to_grade,
            "plants_in_class": plants_in_class,
        },
        "upcoming_assignments": upcoming_assignments,
    }

