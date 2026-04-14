# 角色分层与权限收敛改造说明（2026-04-12）

## 1. 目标

本次改造覆盖 Plants / Groups / Assignments 三个核心模块，目标如下：

- 同一路由下，管理员/教师/学生呈现差异化界面结构。
- 教师可查看全校数据，但仅可修改本人创建资源。
- 管理员新增系统级治理能力（迁移与批量修正）。
- 后端权限与前端按钮可见性保持一致，避免“前端可点、后端 403”。

## 2. 后端改造摘要

### 2.1 数据模型与迁移

- 新增字段：
  - `plant_profiles.created_by` (nullable)
  - `study_groups.created_by` (nullable)
- 迁移脚本：
  - `alembic/versions/0007_role_owner_ops.py`
- 历史数据策略：
  - 旧记录保持 `created_by = null`
  - 教师对该类记录只读
  - 管理员可修改

### 2.2 权限规则

- Plants：
  - 读：教师/管理员全校可见，学生按班级可见
  - 写：教师仅可修改/删除自己创建的植物（及其记录），管理员全权限
- Groups：
  - 读：教师/管理员全校可见，学生按班级可见
  - 写：教师仅可修改自己创建的小组及成员，管理员全权限
- Assignments：
  - 读：教师可查看全校任务、提交列表并可下载附件
  - 写：教师仅可发布/编辑/删除/批改本人任务，管理员全权限

### 2.3 新增管理员接口

- `POST /api/admin/plants/{plant_id}/migrate`
- `POST /api/admin/groups/{group_id}/migrate`
- `POST /api/admin/groups/{group_id}/members/batch-role`

## 3. 前端改造摘要

### 3.1 路由分发

三模块路由改为角色分发入口：

- `/assignments` -> `frontend/src/views/Assignments/index.vue`
- `/plants` -> `frontend/src/views/Plants/index.vue`
- `/groups` -> `frontend/src/views/Groups/index.vue`

### 3.2 角色壳组件

每个模块增加：

- `Admin*.vue`
- `Teacher*.vue`
- `Student*.vue`

说明：旧页面保留为共享业务页，通过角色壳组件装配，降低重构风险并保证功能连续性。

### 3.3 关键交互变化

- 教师端显示只读标识（非本人资源）。
- 非本人任务场景下隐藏批改/发布/删除按钮。
- 管理员端在 Plants/Groups 提供系统级操作弹窗。

## 4. API/类型层改造

- 扩展类型字段：
  - Assignment: `can_manage`, `can_grade`
  - PlantProfile: `created_by`, `can_manage`
  - Group: `created_by`, `can_manage`
- 新增前端 API 封装：
  - `migratePlant`
  - `migrateGroup`
  - `batchUpdateGroupMemberRoles`

## 5. 回归清单

### 5.1 后端

- 迁移执行：
  - `python -m alembic upgrade head`
- 语法检查：
  - `python -m compileall app main.py`

### 5.2 前端

- 构建检查：
  - `npm run build`（在 `frontend` 目录）

### 5.3 权限行为验证

- 教师 A 无法修改教师 B 创建的植物/小组。
- 教师 A 可查看教师 B 任务和提交，并可下载附件。
- 教师 A 无法发布/删除/批改教师 B 任务。
- `created_by = null` 的历史数据，教师只读，管理员可修改。
- 管理员三项系统操作可执行且结果即时可见。

## 6. 已知风险与建议

- 历史数据 `created_by = null` 会导致教师无法接管旧资源；如需接管，建议后续提供“管理员转派创建人”接口。
- 管理员跨班迁移小组时，成员班级一致性依赖业务规范；如需强校验，建议后续增加迁移前校验策略。
- 当前角色壳组件采用“共享页 + 分发器”模式，后续可逐步将共享页逻辑下沉到 composable 以进一步降低耦合。
