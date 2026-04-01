# 项目结构整理说明

## 目标

- 保持现有 API 行为与路径不变
- 降低 `main.py` 与其他模块的耦合
- 统一依赖注入与安全能力的复用入口

## 本次调整

### 1) 后端拆分

- 新增 `app/api/routes/auth.py`
  - `POST /token`
  - `POST /api/auth/logout`

- 新增 `app/api/routes/telemetry.py`
  - `POST /api/telemetry`
  - `GET /api/devices`
  - `POST /api/devices`
  - `POST /api/control/{device_id}`
  - `POST /api/demo/scenario/{device_id}`
  - `POST /api/ai/science-assistant`
  - `WS /ws/telemetry/{device_id}`
  - `POST /api/telemetry/export`
  - `GET /api/public/display`

- 新增 `app/api/routes/content.py`
  - `GET /api/content/categories`
  - `GET /api/content/categories/tree`
  - `POST /api/content/categories`
  - `PUT /api/content/categories/{category_id}`
  - `DELETE /api/content/categories/{category_id}`
  - `GET /api/content/contents`
  - `GET /api/content/contents/{content_id}`
  - `POST /api/content/contents`
  - `PUT /api/content/contents/{content_id}`
  - `DELETE /api/content/contents/{content_id}`
  - `POST /api/content/contents/{content_id}/publish`
  - `GET /api/content/my-learning`
  - `POST /api/content/contents/{content_id}/start`
  - `POST /api/content/contents/{content_id}/complete`
  - `PUT /api/content/contents/{content_id}/progress`
  - `GET /api/content/contents/{content_id}/comments`
  - `POST /api/content/contents/{content_id}/comments`
  - `PUT /api/content/comments/{comment_id}`
  - `GET /api/content/stats/overview`
  - `GET /api/content/stats/students`
  - `GET /api/content/stats/content/{content_id}`

- 新增 `app/api/routes/users.py`
  - `GET /api/users`
  - `POST /api/users`
  - `GET /api/users/{user_id}`
  - `PUT /api/users/{user_id}`
  - `DELETE /api/users/{user_id}`
  - `POST /api/users/{user_id}/reset-password`
  - `POST /api/users/{user_id}/toggle-active`
  - `GET /api/stats/users`
  - `POST /api/users/batch-create`
  - `POST /api/users/batch-delete`
  - `POST /api/users/batch-update-class`
  - `POST /api/users/batch-reset-password`
  - `POST /api/users/import`
  - `GET /api/users/export`
  - `GET /api/classes`
  - `POST /api/classes`
  - `PUT /api/classes/{class_id}`
  - `DELETE /api/classes/{class_id}`
  - `GET /api/classes/{class_id}/students`
  - `GET /api/classes/{class_id}/devices`
  - `POST /api/classes/{class_id}/devices/bind`
  - `DELETE /api/classes/{class_id}/devices/unbind/{bind_id}`
  - `GET /api/students/{student_id}/device`

- 新增 `app/api/routes/assignments.py`
  - `GET /api/assignments`
  - `GET /api/assignments/{assignment_id}`
  - `POST /api/assignments/{assignment_id}/publish`
  - `POST /api/assignments`
  - `PUT /api/assignments/{assignment_id}`
  - `DELETE /api/assignments/{assignment_id}`
  - `GET /api/assignments/{assignment_id}/submissions`
  - `GET /api/assignments/{assignment_id}/my-submission`
  - `POST /api/assignments/{assignment_id}/submit`
  - `POST /api/assignments/{assignment_id}/grade`

- 新增 `app/api/routes/logs.py`
  - `GET /api/logs/operations`
  - `POST /api/logs/operations/export`

- 新增 `app/core/security.py`
  - `pwd_context`
  - `oauth2_scheme`
  - `create_access_token`

- 新增 `app/api/dependencies.py`
  - `get_db`
  - `get_current_user`
  - `get_user_by_token`
  - `token_blacklist`

- 新增 `app/schemas/plants.py`
  - `GrowthRecordCreateRequest`

- 新增 `app/schemas/auth.py`
  - `Token`

- 新增 `app/schemas/telemetry.py`
  - `TelemetryData/TelemetryResponse`
  - `DeviceCreateRequest/DeviceResponse`
  - `ControlRequest`
  - `DemoScenarioRequest`
  - `AIScienceAskRequest/AIScienceAskResponse`
  - `ExportRequest`

- 新增 `app/schemas/content.py`
  - `ContentCategory*`
  - `TeachingContent*`
  - `StudentLearningRecord*`
  - `ContentComment*`
  - `LearningStats`
  - `StudentProgress`

- 新增 `app/schemas/users.py`
  - `User*`
  - `Class*`
  - `ClassDeviceBind*`
  - `UserStats`
  - `Batch*Request`

- 新增 `app/schemas/assignments.py`
  - `Assignment*`
  - `AssignmentSubmission*`
  - `AssignmentPublishRequest`

- 新增 `app/schemas/groups.py`
  - `StudyGroup*`
  - `GroupMember*`

- 新增 `app/schemas/profile.py`
  - `UserTodoStats`
  - `UserProfileResponse`

- 调整 `app/schemas/plants.py`
  - 补齐 `PlantProfile*`
  - 补齐 `GrowthRecordResponse`

- 新增 `app/services/telemetry_hub_service.py`
  - `TelemetryHub`

- 新增 `app/services/ai_science_service.py`
  - `build_rule_based_science_answer`
  - `ask_qwen_science_assistant`

### 2) 路由解耦

以下文件已不再依赖 `from main import ...`：

- `app/api/routes/profile.py`
- `app/api/routes/history.py`
- `app/api/routes/plants.py`
- `app/api/routes/groups.py`

统一改为从 `app/api/dependencies.py` 和 `app/schemas/*` 导入。

## 当前建议目录（后端）

```text
app/
  api/
    dependencies.py
    routes/
      auth.py
      content.py
      users.py
      assignments.py
      telemetry.py
      groups.py
      history.py
      plants.py
      profile.py
  core/
    config.py
    permission.py
    security.py
  db/
    base.py
    models.py
    session.py
  schemas/
    auth.py
    content.py
    users.py
    assignments.py
    plants.py
    telemetry.py
  services/
    ai_science_service.py
    groups_service.py
    history_service.py
    plants_service.py
    profile_service.py
    telemetry_hub_service.py
```

## 验证结果

- 静态错误检查通过
- 前端构建通过：`npm run build`
- 本地后端导入受环境依赖影响（缺少 `python-jose`）
- 现有接口路径未变（兼容现有前端调用）

## 后续可继续拆分（建议）

- 将 `main.py` 中剩余 Pydantic 模型继续分拆到 `app/schemas/`（按域划分）
- 将 `main.py` 中剩余业务路由继续下沉到 `app/api/routes/`
- 保留 `main.py` 仅作为应用装配入口（app factory / router include / middleware）
