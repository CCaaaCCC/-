import datetime
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, get_teacher_user
from app.core.permission import get_allowed_class_ids
from app.db.models import Assignment, AssignmentSubmission, Class, Device, User
from app.schemas.assignments import (
    AssignmentCreate,
    AssignmentPublishRequest,
    AssignmentResponse,
    AssignmentSubmissionGrade,
    AssignmentSubmissionResponse,
    AssignmentSubmissionSubmit,
    AssignmentUpdate,
)


router = APIRouter(tags=["assignments"])

UPLOAD_ROOT = "uploads"
REPORT_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "assignment_reports")


def _build_submission_response(submission: AssignmentSubmission, student_name: str | None = None) -> AssignmentSubmissionResponse:
    return AssignmentSubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        student_name=student_name,
        status=submission.status,
        experiment_date=submission.experiment_date,
        observations=submission.observations,
        conclusion=submission.conclusion,
        temp_records=submission.temp_records,
        humidity_records=submission.humidity_records,
        soil_moisture_records=submission.soil_moisture_records,
        light_records=submission.light_records,
        photos=submission.photos,
        score=submission.score,
        teacher_comment=submission.teacher_comment,
        report_file_name=submission.report_file_name,
        report_file_path=submission.report_file_path,
        report_file_size=submission.report_file_size,
        graded_at=submission.graded_at,
        submitted_at=submission.submitted_at,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )


@router.get("/api/assignments", response_model=list[AssignmentResponse])
async def get_assignments(
    class_id: int | None = None,
    teacher_id: int | None = None,
    is_published: bool | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Assignment)

    if current_user.role == "student":
        if not current_user.class_id:
            return []
        query = query.filter(Assignment.class_id == current_user.class_id)
    elif current_user.role == "teacher":
        query = query.filter(Assignment.teacher_id == current_user.id)

        allowed_class_ids = get_allowed_class_ids(db, current_user)
        if not allowed_class_ids:
            return []

        if class_id is not None:
            if class_id not in allowed_class_ids:
                raise HTTPException(status_code=403, detail="无权访问该班级的实验任务")
            query = query.filter(Assignment.class_id == class_id)
        else:
            query = query.filter(Assignment.class_id.in_(allowed_class_ids))

    if class_id is not None and current_user.role != "teacher":
        query = query.filter(Assignment.class_id == class_id)
    if teacher_id:
        query = query.filter(Assignment.teacher_id == teacher_id)
    if is_published is not None:
        query = query.filter(Assignment.is_published == is_published)
    elif current_user.role == "student":
        query = query.filter(Assignment.is_published == True)

    assignments = query.order_by(desc(Assignment.created_at)).all()

    if not assignments:
        return []

    if current_user.role == "student" and status and status != "all":
        assignment_ids_for_status = [a.id for a in assignments]
        my_submissions = (
            db.query(AssignmentSubmission)
            .filter(
                AssignmentSubmission.assignment_id.in_(assignment_ids_for_status),
                AssignmentSubmission.student_id == current_user.id,
            )
            .all()
        )
        submission_map = {s.assignment_id: s.status for s in my_submissions}

        filtered = []
        for item in assignments:
            sub_status = submission_map.get(item.id)
            if status == "pending" and not sub_status:
                filtered.append(item)
            elif status == "submitted" and sub_status == "submitted":
                filtered.append(item)
            elif status == "graded" and sub_status == "graded":
                filtered.append(item)
        assignments = filtered

    if not assignments:
        return []

    assignment_ids = [a.id for a in assignments]
    teacher_ids = {a.teacher_id for a in assignments if a.teacher_id is not None}
    device_ids = {a.device_id for a in assignments if a.device_id is not None}
    class_ids = {a.class_id for a in assignments if a.class_id is not None}

    teacher_map = {}
    device_map = {}
    class_map = {}

    if teacher_ids:
        teachers = db.query(User).filter(User.id.in_(teacher_ids)).all()
        teacher_map = {t.id: t for t in teachers}
    if device_ids:
        devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
        device_map = {d.id: d.device_name for d in devices}
    if class_ids:
        classes = db.query(Class).filter(Class.id.in_(class_ids)).all()
        class_map = {c.id: c.class_name for c in classes}

    submission_counts = (
        db.query(AssignmentSubmission.assignment_id, func.count(AssignmentSubmission.id).label("count"))
        .filter(AssignmentSubmission.assignment_id.in_(assignment_ids))
        .group_by(AssignmentSubmission.assignment_id)
        .all()
    )
    count_map = {sc.assignment_id: sc.count for sc in submission_counts}

    result = []
    for assignment in assignments:
        teacher = teacher_map.get(assignment.teacher_id)
        result.append(
            AssignmentResponse(
                id=assignment.id,
                title=assignment.title,
                description=assignment.description,
                device_id=assignment.device_id,
                class_id=assignment.class_id,
                teacher_id=assignment.teacher_id,
                teacher_name=(teacher.real_name or teacher.username) if teacher else None,
                device_name=device_map.get(assignment.device_id),
                class_name=class_map.get(assignment.class_id),
                start_date=assignment.start_date,
                due_date=assignment.due_date,
                requirement=assignment.requirement,
                template=assignment.template,
                is_published=assignment.is_published,
                created_at=assignment.created_at,
                submission_count=count_map.get(assignment.id, 0),
            )
        )

    return result


@router.get("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="任务不存在")

    if current_user.role == "student":
        if assignment.class_id != current_user.class_id or not assignment.is_published:
            raise HTTPException(status_code=403, detail="无权查看非本班任务")

    return assignment


@router.post("/api/assignments/{assignment_id}/publish", response_model=AssignmentResponse)
async def set_assignment_publish_status(
    assignment_id: int,
    publish_data: AssignmentPublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="任务不存在")

    if current_user.role != "admin" and assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能操作自己布置的任务")

    assignment.is_published = publish_data.is_published
    db.commit()
    db.refresh(assignment)

    teacher = db.query(User).filter(User.id == assignment.teacher_id).first() if assignment.teacher_id else None
    device = db.query(Device).filter(Device.id == assignment.device_id).first() if assignment.device_id else None
    clas = db.query(Class).filter(Class.id == assignment.class_id).first() if assignment.class_id else None
    submission_count = db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment.id).count()

    return AssignmentResponse(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        device_id=assignment.device_id,
        class_id=assignment.class_id,
        teacher_id=assignment.teacher_id,
        teacher_name=(teacher.real_name or teacher.username) if teacher else None,
        device_name=device.device_name if device else None,
        class_name=clas.class_name if clas else None,
        start_date=assignment.start_date,
        due_date=assignment.due_date,
        requirement=assignment.requirement,
        template=assignment.template,
        is_published=assignment.is_published,
        created_at=assignment.created_at,
        submission_count=submission_count,
    )


@router.post("/api/assignments", response_model=AssignmentResponse)
async def create_assignment(
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_assignment = Assignment(**assignment.model_dump(), teacher_id=current_user.id)
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)

    teacher_name = current_user.real_name or current_user.username
    device_name = None
    class_name = None

    if db_assignment.device_id:
        device = db.query(Device).filter(Device.id == db_assignment.device_id).first()
        if device:
            device_name = device.device_name

    if db_assignment.class_id:
        cls = db.query(Class).filter(Class.id == db_assignment.class_id).first()
        if cls:
            class_name = cls.class_name

    return AssignmentResponse(
        id=db_assignment.id,
        title=db_assignment.title,
        description=db_assignment.description,
        device_id=db_assignment.device_id,
        class_id=db_assignment.class_id,
        teacher_id=db_assignment.teacher_id,
        teacher_name=teacher_name,
        device_name=device_name,
        class_name=class_name,
        start_date=db_assignment.start_date,
        due_date=db_assignment.due_date,
        requirement=db_assignment.requirement,
        template=db_assignment.template,
        is_published=db_assignment.is_published,
        created_at=db_assignment.created_at,
        submission_count=0,
    )


@router.put("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    assignment_update: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="任务不存在")

    if current_user.role != "admin" and db_assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能编辑自己创建的任务")

    update_data = assignment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_assignment, key, value)

    db.commit()
    db.refresh(db_assignment)
    return db_assignment


@router.delete("/api/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    db_assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="任务不存在")

    if current_user.role != "admin" and db_assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己创建的任务")

    submissions = db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id).all()
    deleted_files = 0
    for sub in submissions:
        if sub.report_file_path and os.path.exists(sub.report_file_path):
            try:
                os.remove(sub.report_file_path)
                deleted_files += 1
            except OSError:
                pass

    db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id).delete(synchronize_session=False)
    db.delete(db_assignment)
    db.commit()
    return {
        "message": "任务已彻底删除",
        "deleted_submissions": len(submissions),
        "deleted_files": deleted_files,
    }


@router.get("/api/assignments/{assignment_id}/submissions", response_model=list[AssignmentSubmissionResponse])
async def get_submissions(
    assignment_id: int,
    student_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="任务不存在")

    if current_user.role == "student":
        student_id = current_user.id
    elif current_user.role != "admin" and assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能查看自己布置任务的提交")

    query = db.query(AssignmentSubmission).filter(AssignmentSubmission.assignment_id == assignment_id)

    if student_id:
        query = query.filter(AssignmentSubmission.student_id == student_id)
    if status:
        query = query.filter(AssignmentSubmission.status == status)

    submissions = query.order_by(desc(AssignmentSubmission.created_at)).all()

    student_ids = {sub.student_id for sub in submissions}
    student_map: dict[int, str] = {}
    if student_ids:
        students = db.query(User).filter(User.id.in_(student_ids)).all()
        student_map = {stu.id: stu.username for stu in students}

    result = []
    for sub in submissions:
        result.append(_build_submission_response(sub, student_map.get(sub.student_id)))

    return result


@router.get("/api/assignments/{assignment_id}/my-submission", response_model=AssignmentSubmissionResponse)
async def get_my_submission(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.assignment_id == assignment_id, AssignmentSubmission.student_id == current_user.id)
        .first()
    )

    if not submission:
        raise HTTPException(status_code=404, detail="未找到提交记录")

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if assignment and current_user.role == "student" and assignment.class_id and assignment.class_id != current_user.class_id:
        raise HTTPException(status_code=403, detail="无权查看非本班任务")

    return _build_submission_response(submission, current_user.username)


@router.post("/api/assignments/{assignment_id}/submit", response_model=AssignmentSubmissionResponse)
async def submit_assignment(
    assignment_id: int,
    submission: AssignmentSubmissionSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="仅学生可提交实验报告")

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="任务不存在")

    if assignment.due_date and datetime.datetime.utcnow() > assignment.due_date:
        raise HTTPException(
            status_code=400,
            detail=f"已超过提交截止时间 ({assignment.due_date.strftime('%Y-%m-%d %H:%M')})",
        )

    if assignment.class_id:
        student = db.query(User).filter(User.id == current_user.id).first()
        if student and student.class_id != assignment.class_id:
            raise HTTPException(status_code=403, detail="您不属于该任务布置的班级")

    existing = (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.assignment_id == assignment_id, AssignmentSubmission.student_id == current_user.id)
        .first()
    )

    if existing:
        existing.observations = submission.observations
        existing.conclusion = submission.conclusion
        existing.temp_records = submission.temp_records
        existing.humidity_records = submission.humidity_records
        existing.soil_moisture_records = submission.soil_moisture_records
        existing.light_records = submission.light_records
        existing.photos = submission.photos
        existing.experiment_date = submission.experiment_date
        existing.status = "submitted"
        existing.submitted_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing)
        result = existing
    else:
        new_submission = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=current_user.id,
            experiment_date=submission.experiment_date,
            observations=submission.observations,
            conclusion=submission.conclusion,
            temp_records=submission.temp_records,
            humidity_records=submission.humidity_records,
            soil_moisture_records=submission.soil_moisture_records,
            light_records=submission.light_records,
            photos=submission.photos,
            status="submitted",
            submitted_at=datetime.datetime.utcnow(),
        )
        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)
        result = new_submission

    return result


@router.post("/api/assignments/{assignment_id}/submit-with-file", response_model=AssignmentSubmissionResponse)
async def submit_assignment_with_file(
    assignment_id: int,
    experiment_date: str | None = Form(default=None),
    observations: str | None = Form(default=None),
    conclusion: str | None = Form(default=None),
    temp_records: str | None = Form(default=None),
    humidity_records: str | None = Form(default=None),
    soil_moisture_records: str | None = Form(default=None),
    light_records: str | None = Form(default=None),
    photos: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="仅学生可提交实验报告")

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="任务不存在")

    if assignment.due_date and datetime.datetime.utcnow() > assignment.due_date:
        raise HTTPException(
            status_code=400,
            detail=f"已超过提交截止时间 ({assignment.due_date.strftime('%Y-%m-%d %H:%M')})",
        )

    if assignment.class_id and current_user.class_id != assignment.class_id:
        raise HTTPException(status_code=403, detail="您不属于该任务布置的班级")

    ext = os.path.splitext(file.filename or "")[1].lower()
    allowed = {".pdf", ".doc", ".docx", ".txt", ".md"}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="仅支持 pdf/doc/docx/txt/md 文档")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件为空，无法提交")
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件过大，限制为 20MB")

    os.makedirs(REPORT_UPLOAD_DIR, exist_ok=True)
    stored_name = f"{assignment_id}_{current_user.id}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(REPORT_UPLOAD_DIR, stored_name)
    with open(save_path, "wb") as f:
        f.write(content)

    parsed_experiment_date = None
    if experiment_date:
        try:
            parsed_experiment_date = datetime.datetime.strptime(experiment_date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="实验日期格式应为 YYYY-MM-DD") from exc

    existing = (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.assignment_id == assignment_id, AssignmentSubmission.student_id == current_user.id)
        .first()
    )

    if existing:
        if existing.report_file_path and os.path.exists(existing.report_file_path):
            try:
                os.remove(existing.report_file_path)
            except OSError:
                pass

        existing.experiment_date = parsed_experiment_date
        existing.observations = observations
        existing.conclusion = conclusion
        existing.temp_records = temp_records
        existing.humidity_records = humidity_records
        existing.soil_moisture_records = soil_moisture_records
        existing.light_records = light_records
        existing.photos = photos
        existing.report_file_name = file.filename
        existing.report_file_path = save_path
        existing.report_file_size = len(content)
        existing.status = "submitted"
        existing.submitted_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return _build_submission_response(existing, current_user.username)

    new_submission = AssignmentSubmission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        experiment_date=parsed_experiment_date,
        observations=observations,
        conclusion=conclusion,
        temp_records=temp_records,
        humidity_records=humidity_records,
        soil_moisture_records=soil_moisture_records,
        light_records=light_records,
        photos=photos,
        report_file_name=file.filename,
        report_file_path=save_path,
        report_file_size=len(content),
        status="submitted",
        submitted_at=datetime.datetime.utcnow(),
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)
    return _build_submission_response(new_submission, current_user.username)


@router.get("/api/assignments/submissions/{submission_id}/file")
async def download_submission_file(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="任务不存在")

    if current_user.role == "student":
        if submission.student_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权下载他人提交的报告")
    elif current_user.role == "teacher":
        if assignment.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权下载非本人任务的报告")

    if not submission.report_file_path or not os.path.exists(submission.report_file_path):
        raise HTTPException(status_code=404, detail="未找到报告文件")

    filename = submission.report_file_name or os.path.basename(submission.report_file_path)
    return FileResponse(
        path=submission.report_file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/api/assignments/{assignment_id}/grade")
async def grade_assignment(
    assignment_id: int,
    submission_id: int,
    grade: AssignmentSubmissionGrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_teacher_user),
):
    submission = (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.id == submission_id, AssignmentSubmission.assignment_id == assignment_id)
        .first()
    )
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="任务不存在")

    if current_user.role != "admin" and assignment.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能批改自己布置的任务")

    submission.score = grade.score
    submission.teacher_comment = grade.teacher_comment
    submission.graded_at = datetime.datetime.utcnow()
    submission.graded_by = current_user.id
    submission.status = "graded"

    db.commit()
    return {"message": "批改完成"}
