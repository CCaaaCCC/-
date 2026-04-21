import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    Enum,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


# --- 数据库模型定义 ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(20), index=True)  # 'student', 'teacher', 'admin'

    email = Column(String(100), unique=True, nullable=True, index=True)
    real_name = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    student_id = Column(String(20), unique=True, nullable=True, index=True)
    teacher_id = Column(String(20), unique=True, nullable=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        # 复合索引：按班级和角色查询
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )

    ai_conversations = relationship("AIConversation", back_populates="user", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_name = Column(String(100), nullable=False)
    status = Column(SmallInteger, default=1)
    last_seen = Column(DateTime, nullable=True)
    pump_state = Column(SmallInteger, default=0)
    fan_state = Column(SmallInteger, default=0)
    fan_speed = Column(SmallInteger, default=100)
    light_state = Column(SmallInteger, default=0)
    light_brightness = Column(SmallInteger, default=100)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    temp = Column(DECIMAL(5, 2))
    humidity = Column(DECIMAL(5, 2))
    soil_moisture = Column(DECIMAL(5, 2))
    light = Column(DECIMAL(10, 2))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    device = relationship("Device")

    __table_args__ = (
        # 复合索引：按设备和时间查询历史数据
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )


# --- 教学内容管理模型 ---
class TeachingContent(Base):
    """教学内容表"""

    __tablename__ = "teaching_contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    tags = Column(String(500), nullable=True, index=True)
    content_type = Column(String(20), default="article")  # article, video, image, document, pdf
    content = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)
    file_path = Column(String(500), nullable=True)
    cover_image = Column(String(500), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    view_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=False, index=True)
    published_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    author = relationship("User")
    learning_records = relationship("StudentLearningRecord", back_populates="content")
    comments = relationship("ContentComment", back_populates="content")

    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )


class StudentLearningRecord(Base):
    """学生学习记录表"""

    __tablename__ = "student_learning_records"
    __table_args__ = (
        # 复合唯一索引：一个学生对同一内容只有一条记录
        UniqueConstraint('student_id', 'content_id', name='uix_student_content'),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("teaching_contents.id"), nullable=False, index=True)
    status = Column(String(20), default="not_started", index=True)  # not_started, in_progress, completed
    progress_percent = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)

    student = relationship("User")
    content = relationship("TeachingContent", back_populates="learning_records")

class ContentComment(Base):
    """内容评论/问答表"""

    __tablename__ = "content_comments"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("teaching_contents.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("content_comments.id"), nullable=True, index=True)
    comment = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    teacher_reply = Column(Text, nullable=True)
    reply_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    content = relationship("TeachingContent", back_populates="comments")
    student = relationship("User")
    parent = relationship("ContentComment", remote_side=[id], backref="replies")


class ContentCommentLike(Base):
    """评论点赞表"""

    __tablename__ = "content_comment_likes"
    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', name='uix_comment_like_user'),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("content_comments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    comment = relationship("ContentComment")
    user = relationship("User")


class UserNotification(Base):
    """站内通知表"""

    __tablename__ = "user_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    content_id = Column(Integer, ForeignKey("teaching_contents.id"), nullable=True, index=True)
    comment_id = Column(Integer, ForeignKey("content_comments.id"), nullable=True, index=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])
    teaching_content = relationship("TeachingContent")
    comment = relationship("ContentComment")


class Class(Base):
    """班级表"""

    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(100), nullable=False, index=True)
    grade = Column(String(20), nullable=True)
    invite_code = Column(String(32), nullable=False, unique=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 班级与设备关联
    devices = relationship("ClassDeviceBind", back_populates="parent_class")

    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )


class ClassDeviceBind(Base):
    """班级与设备绑定表"""

    __tablename__ = "class_device_binds"
    __table_args__ = (
        # 唯一约束：同一班级不能绑定同一设备多次
        UniqueConstraint('class_id', 'device_id', name='uix_class_device'),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    parent_class = relationship("Class", back_populates="devices")
    device = relationship("Device")

class UserOperationLog(Base):
    """用户操作日志表"""

    __tablename__ = "user_operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    operation_type = Column(String(20), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    operator = relationship("User", foreign_keys=[operator_id])
    target_user = relationship("User", foreign_keys=[target_user_id])


class MarketProduct(Base):
    """线下交易商品信息表"""

    __tablename__ = "market_products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=True)
    location = Column(String(255), nullable=False)
    contact_info = Column(String(255), nullable=False)
    image_url = Column(String(500), nullable=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), default="on_sale", index=True)  # on_sale, sold, off_shelf
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    seller = relationship("User")

    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )


# ==================== 实验报告系统模型 ====================
class Assignment(Base):
    """实验任务表"""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), index=True)
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    requirement = Column(Text)
    template = Column(Text)
    is_published = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    device = relationship("Device")


class AssignmentSubmission(Base):
    """实验报告提交表"""

    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), index=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(String(20), default="submitted", index=True)  # submitted, graded
    experiment_date = Column(Date, nullable=True, index=True)

    observations = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)

    temp_records = Column(Text, nullable=True)
    humidity_records = Column(Text, nullable=True)
    soil_moisture_records = Column(Text, nullable=True)
    light_records = Column(Text, nullable=True)
    photos = Column(Text, nullable=True)

    score = Column(Float, nullable=True, index=True)
    teacher_comment = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True, index=True)
    graded_at = Column(DateTime, nullable=True, index=True)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    report_file_name = Column(String(255), nullable=True)
    report_file_path = Column(String(500), nullable=True)
    report_file_size = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    assignment = relationship("Assignment")
    student = relationship("User", foreign_keys=[student_id])
    grader = relationship("User", foreign_keys=[graded_by])

    __table_args__ = (
        # 复合索引：快速查询学生的提交
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )


# ==================== 植物生长档案模型 ====================
class PlantProfile(Base):
    """植物档案表"""

    __tablename__ = "plant_profiles"

    id = Column(Integer, primary_key=True, index=True)
    plant_name = Column(String(100), nullable=False)
    species = Column(String(100), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("study_groups.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    plant_date = Column(Date, nullable=True)
    cover_image = Column(String(500), nullable=True)
    status = Column(String(20), default="growing")  # growing, harvested, dead
    expected_harvest_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    growth_records = relationship("GrowthRecord", back_populates="plant")


class GrowthRecord(Base):
    """生长记录表"""

    __tablename__ = "growth_records"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plant_profiles.id"), index=True)
    record_date = Column(Date, default=datetime.date.today)
    stage = Column(String(20), default="seed")  # seed, sprout, seedling, flowering, fruiting, harvest
    height_cm = Column(Float, nullable=True)
    leaf_count = Column(Integer, nullable=True)
    flower_count = Column(Integer, nullable=True)
    fruit_count = Column(Integer, nullable=True)
    description = Column(Text)
    photos = Column(Text)
    recorded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    plant = relationship("PlantProfile", back_populates="growth_records")
    recorder = relationship("User")


# ==================== 小组合作学习模型 ====================
class StudyGroup(Base):
    """学习小组表"""

    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(100), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"))
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    clas = relationship("Class")
    device = relationship("Device")
    members = relationship("GroupMember", back_populates="group")


class GroupMember(Base):
    """小组成员表"""

    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20))  # leader, recorder, operator, reporter
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    group = relationship("StudyGroup", back_populates="members")
    student = relationship("User")


class AIConversation(Base):
    """AI 助手会话表（用户私有）"""

    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(120), nullable=False, default="新对话")
    is_pinned = Column(Boolean, nullable=False, default=False, index=True)
    pinned_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, index=True)
    last_message_at = Column(DateTime, nullable=True, index=True)

    user = relationship("User", back_populates="ai_conversations")
    messages = relationship(
        "AIConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIConversationMessage.created_at",
    )

    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )


class AIConversationMessage(Base):
    """AI 助手会话消息表"""

    __tablename__ = "ai_conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, index=True)  # user, assistant
    content = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    source = Column(String(64), nullable=True)
    model = Column(String(80), nullable=True)
    citations_json = Column(Text, nullable=True)
    web_search_notice = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="done")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    conversation = relationship("AIConversation", back_populates="messages")

    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

