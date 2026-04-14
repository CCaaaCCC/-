# 项目结构与设计说明

## 目标

- 保持现有 API 行为与路径不变
- 提升前端可用性与跨环境访问稳定性
- 统一视觉规范，降低样式维护成本

## 本轮关键调整（2026-04-12）

### 1) 前端访问稳定性修复

- 修改 `frontend/vite.config.ts`
  - `server.host = '0.0.0.0'`
  - `server.port = 5173`
  - `server.strictPort = true`

效果：开发环境下可同时通过 `localhost:5173` 与 `127.0.0.1:5173` 访问，避免“浏览器打不开页面”问题。

### 2) AI 助手样式维护优化

- 清理 `frontend/src/components/FloatingAIAssistant.vue` 中重复的 `style scoped` 块
- 合并“思考过程”面板样式，统一维护单一来源

效果：减少样式覆盖冲突风险，后续迭代更稳定。

### 3) 主题变量补齐

- 在 `frontend/src/styles/theme.css` 增加布局变量：
  - `--layout-max-width`
  - `--layout-wide-max-width`
  - `--layout-gutter`

效果：与页面组件中的布局变量使用保持一致，避免样式回退与布局异常。

### 4) AI 助手会话化改造

- 后端新增会话持久化模型：
  - `app/db/models.py`
  - `AIConversation`
  - `AIConversationMessage`
- 后端新增会话化接口：
  - `GET /api/ai/conversations`
  - `POST /api/ai/conversations`
  - `GET /api/ai/conversations/{conversation_id}`
  - `PATCH /api/ai/conversations/{conversation_id}/title`
  - `DELETE /api/ai/conversations/{conversation_id}`
  - `POST /api/ai/conversations/{conversation_id}/science-assistant`
  - `POST /api/ai/conversations/{conversation_id}/science-assistant/stream`
- 后端迁移脚本：
  - `alembic/versions/0004_ai_conversation_history.py`
- 前端会话化 UI：
  - `frontend/src/components/FloatingAIAssistant.vue`
  - 支持新建、切换、重命名、删除会话
  - 流式生成期间禁止会话切换
- 前端 API 封装：
  - `frontend/src/api/index.ts`
  - 新增会话 CRUD 与会话内问答/流式接口封装

效果：AI 助手从“单次问答”升级为“用户私有的可持续对话”，并保留旧接口兼容现有调用。

### 5) 三模块角色分层改造（A->D）

- 后端权限与数据层：
  - 新增所有权字段：
    - `plant_profiles.created_by`
    - `study_groups.created_by`
  - 教师在 Plants / Groups / Assignments 中具备“全校可读”能力。
  - 教师写操作收敛为“仅本人创建资源可写”；`created_by` 为空的历史数据仅管理员可写。
  - 管理员新增系统级接口：
    - `POST /api/admin/plants/{plant_id}/migrate`
    - `POST /api/admin/groups/{group_id}/migrate`
    - `POST /api/admin/groups/{group_id}/members/batch-role`

- 前端路由与页面结构：
  - 三个核心模块由“单页面”升级为“角色分发入口 + 角色壳组件”：
    - `frontend/src/views/Assignments/index.vue`
    - `frontend/src/views/Plants/index.vue`
    - `frontend/src/views/Groups/index.vue`
  - 每个模块均拆出：
    - `Admin*.vue`
    - `Teacher*.vue`
    - `Student*.vue`
  - 旧页面保留为共享业务页，由角色壳组件装配，减少重写风险。

- 前端行为变化：
  - 教师查看非本人资源时明确显示“只读”状态。
  - 管理员在 Plants/Groups 页面可直接执行迁移与批量修正。

效果：实现“同一路由下按角色差异化界面与权限行为”，同时保证后端权限与前端交互一致。

## 视觉与交互规范（Scheme A）

- 毛玻璃布局：左侧固定导航 + 主内容沉浸式背景
- 统一圆角与阴影层级：减少组件风格碎片化
- AI 面板：支持“深度思考”折叠展示，强调可解释性

## 文档索引

- 总览与运行：`README.md`
- 维护手册：`docs/MAINTENANCE_GUIDE.md`
- 部署与演示：`DEPLOY_AND_DEMO.md`
- 角色分层改造专项：`docs/ROLE_UI_REFACTOR_PLAN.md`
