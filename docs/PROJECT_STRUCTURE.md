# 项目结构与设计说明

## 设计目标

- 保持 API 行为与路径不变
- 后端模块化拆分，降低 `main.py` 耦合
- 前端角色分发架构，统一权限与交互
- 提升可维护性、可测试性与跨环境访问稳定性

---

## 整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│                         前端 (Vue 3 + TS)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  Views    │  │Components│  │Composables│  │   API Layer    │  │
│  │ (角色化)  │  │ (公共)   │  │ (复用逻辑)│  │ (Axios+类型)   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│        │              │             │               │            │
│        └──────────────┴─────────────┴───────────────┘            │
│                              │                                    │
│                     Router + Auth Guard                           │
└──────────────────────────────┬───────────────────────────────────┘
                               │ HTTP/REST + WebSocket/SSE
┌──────────────────────────────┴───────────────────────────────────┐
│                      后端 (FastAPI)                               │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    Routes (11 模块)                       │    │
│  │  auth │ telemetry │ content │ users │ assignments │ ...  │    │
│  └──────────────────────┬───────────────────────────────────┘    │
│                         │ Depends                                │
│  ┌──────────────────────┴───────────────────────────────────┐    │
│  │              Dependencies (认证/权限/DB会话)              │    │
│  └──────────────────────┬───────────────────────────────────┘    │
│                         │                                        │
│  ┌──────────────────────┴───────────────────────────────────┐    │
│  │                Services (10 业务模块)                     │    │
│  │  ai_science │ langchain │ rag │ plants │ groups │ ...    │    │
│  └──────────────────────┬───────────────────────────────────┘    │
│                         │                                        │
│  ┌──────────────────────┴───────────────────────────────────┐    │
│  │            Core (config/security/permission/validators)   │    │
│  └──────────────────────┬───────────────────────────────────┘    │
│                         │                                        │
│  ┌──────────────────────┴───────────────────────────────────┐    │
│  │              DB Layer (models/session/base)               │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                               │
                        ┌──────┴──────┐
                        │   MySQL 8   │
                        └─────────────┘
```

---

## 后端模块详解

### 入口层 — `main.py`

纯装配入口，不包含业务逻辑：

- 创建 FastAPI 实例
- 配置 CORS 中间件
- 挂载静态文件 (`/uploads`)
- 注册启动事件 (`init_demo_data`)
- `include_router` 装配全部路由模块

### 路由层 — `app/api/routes/`

每个路由模块对应一个业务域，职责为：参数校验、权限检查、调用 Service、构造响应。

| 模块 | 文件 | 核心端点 | 说明 |
|------|------|----------|------|
| 认证 | `auth.py` | `/token`, `/api/auth/*` | 登录频控、JWT 签发、注销拉黑、邀请码注册 |
| 遥测 | `telemetry.py` | `/api/telemetry`, `/api/devices`, `/api/ai/*` | 设备 CRUD、传感器上报、远程控制、WebSocket 推送、AI 会话管理、数据导出、公开大屏 |
| 教学内容 | `content.py` | `/api/content/*` | 内容 CRUD、发布管理、学习记录、评论互动、AI 润色、RAG 索引触发 |
| 用户管理 | `users.py` | `/api/users/*`, `/api/classes/*` | 用户 CRUD、批量操作、班级管理、设备绑定 |
| 实验报告 | `assignments.py` | `/api/assignments/*` | 任务 CRUD、提交/批改、文件上传下载、AI 点评 |
| 植物档案 | `plants.py` | `/api/plants/*` | 档案 CRUD、生长记录、图片上传、跨班迁移 |
| 小组合作 | `groups.py` | `/api/groups/*` | 小组 CRUD、成员管理、跨班迁移、批量角色修正 |
| 线下商城 | `market.py` | `/api/market/*` | 商品 CRUD、图片上传、分页搜索 |
| 个人中心 | `profile.py` | `/api/profile/*`, `/api/notifications/*` | 个人信息、头像上传、站内通知 |
| 历史数据 | `history.py` | `/api/history/*` | 传感器历史查询 |
| 操作日志 | `logs.py` | `/api/logs/*` | 日志查询与导出 |

### 依赖层 — `app/api/dependencies.py`

提供 FastAPI 依赖注入函数：

| 函数 | 说明 |
|------|------|
| `get_db()` | 数据库会话生命周期管理 |
| `get_current_user()` | JWT 解码 + 用户查询 + 黑名单检查 |
| `get_teacher_user()` | 教师/管理员权限守卫 |
| `get_admin_user()` | 管理员权限守卫 |
| `get_content_editor()` | 内容编辑权限守卫 |
| `get_user_by_token()` | WebSocket 场景下的 Token 解析 |

`token_blacklist` 全局集合用于注销时的 Token 失效。

### 核心层 — `app/core/`

| 文件 | 职责 |
|------|------|
| `config.py` | 环境变量加载，`Settings` dataclass，CORS 解析 |
| `security.py` | 密码哈希（passlib + bcrypt 兜底）、JWT 创建、OAuth2 Scheme |
| `permission.py` | 权限判定：班级/设备/小组/植物的可见范围与操作权限 |
| `validators.py` | 输入校验：密码强度、用户名格式、邮箱格式 |
| `bootstrap.py` | 启动种子数据：演示账号、默认设备、示例班级 |

#### 权限判定核心逻辑 (`permission.py`)

```
get_allowed_class_ids()   → 管理员: None(全部), 教师: 所带班级, 学生: 所属班级
get_allowed_device_ids()  → 基于班级-设备绑定推导可见设备
get_allowed_group_ids()   → 基于班级推导可见小组
can_manage_owned_resource() → 管理员: 全部, 教师: 仅 created_by=自己
```

### 数据层 — `app/db/`

| 文件 | 职责 |
|------|------|
| `base.py` | SQLAlchemy Declarative Base |
| `models.py` | 全部 20 个 ORM 模型定义 |
| `session.py` | `SessionLocal` 工厂 |

#### 模型关系图（核心）

```
User ──┬── Class (teacher_id)
       ├── ClassDeviceBind (class_id ↔ device_id)
       ├── TeachingContent (author_id)
       ├── StudentLearningRecord (student_id)
       ├── ContentComment (student_id)
       ├── UserNotification (user_id, actor_id)
       ├── UserOperationLog (operator_id)
       ├── MarketProduct (seller_id)
       ├── Assignment (teacher_id)
       ├── AssignmentSubmission (student_id, graded_by)
       ├── PlantProfile (created_by)
       ├── GrowthRecord (recorded_by)
       ├── StudyGroup (created_by)
       ├── GroupMember (student_id)
       ├── AIConversation (user_id)
       └── AIConversationMessage (conversation_id)

Device ──┬── SensorReading (device_id)
         ├── ClassDeviceBind
         ├── Assignment (device_id)
         ├── PlantProfile (device_id)
         └── StudyGroup (device_id)

Class ──┬── User (class_id)
        ├── ClassDeviceBind
        ├── Assignment (class_id)
        ├── PlantProfile (class_id)
        └── StudyGroup (class_id)

TeachingContent ──┬── StudentLearningRecord
                  ├── ContentComment
                  └── UserNotification
```

### Schema 层 — `app/schemas/`

Pydantic v1 模型，负责请求体验证与响应体序列化：

| 文件 | 覆盖域 |
|------|--------|
| `auth.py` | 登录响应、注册请求/响应 |
| `telemetry.py` | 设备/遥测/AI 会话/控制/导出请求与响应 |
| `content.py` | 教学内容 CRUD、学习记录、评论 |
| `users.py` | 用户/班级/批量操作 |
| `assignments.py` | 实验任务与提交（含分页响应） |
| `plants.py` | 植物档案与生长记录 |
| `groups.py` | 小组与成员 |
| `market.py` | 商城商品（`extra=forbid`） |
| `profile.py` | 个人中心 |

### 服务层 — `app/services/`

业务逻辑核心，被路由层调用：

| 服务 | 文件 | 职责 |
|------|------|------|
| AI 科学问答 | `ai_science_service.py` | 问答编排、联网检索、天气查询、来源引用对齐、流式输出 |
| LangChain 编排 | `langchain_service.py` | 模型调用、提示词构建、大棚意图识别、标题生成 |
| RAG 检索 | `rag_service.py` | 教学内容向量化、增量索引同步、语义检索 |
| AI 审计 | `ai_audit_service.py` | 调用日志记录、Token 估算、回退原因推断 |
| WebSocket 管理 | `telemetry_hub_service.py` | 连接池管理、广播、断线清理 |
| 植物档案 | `plants_service.py` | 档案查询、生长记录 CRUD、权限检查 |
| 小组合作 | `groups_service.py` | 小组 CRUD、成员管理、权限检查 |
| 历史数据 | `history_service.py` | 传感器历史查询 |
| 个人中心 | `profile_service.py` | 个人信息聚合、待办统计 |
| 通知 | `notification_service.py` | 站内通知创建 |

#### AI 问答链路

```
用户提问
    │
    ▼
ai_science_service.ask_science_assistant()
    │
    ├── has_greenhouse_intent() ─── 判断是否大棚相关问题
    │
    ├── RAG 检索 (rag_service)
    │   └── search_teaching_content_context() ─── 本地 Chroma 向量检索
    │
    ├── 联网检索 (enable_web_search)
    │   ├── 天气意图 → Open-Meteo API
    │   └── 通用搜索 → Bing API + 页面抓取 + 相关性评分
    │
    ├── LangChain 编排 (langchain_service)
    │   ├── ask_science_with_langchain() ─── 标准问答
    │   └── stream_science_with_langchain() ─── 流式问答
    │
    ├── 引用对齐 (align_citations_with_answer)
    │   └── 正文 [n] 编号与来源链接一一映射
    │
    └── AI 审计 (ai_audit_service)
        └── record_ai_audit() ─── 记录来源/耗时/Token/回退原因
```

---

## 前端模块详解

### 路由与权限 — `router/index.ts`

- 路由懒加载（动态 import）
- `beforeEach` 守卫：Token 检查 → 角色权限 → 越权引导
- 大屏页面 (`/display`) 免认证
- 首页 `/` 按角色重定向到对应 Home
- Chunk 加载失败自动刷新（一次性重试）

### 角色分发架构

三个核心模块采用"角色分发入口 + 角色壳组件"模式：

```
/views/Assignments/
├── index.vue              # 角色分发入口（根据 role 动态加载）
├── AdminAssignments.vue   # 管理员视图
├── TeacherAssignments.vue # 教师视图（全校可见/仅本人可写）
└── StudentAssignments.vue # 学生视图（提交报告）

/views/Plants/  (同构)
/views/Groups/  (同构)
```

### API 层 — `api/`

| 文件 | 职责 |
|------|------|
| `index.ts` | Axios 实例创建、请求/响应拦截器、API 基址自动推导与回退、认证 API |
| `assignments.ts` | 实验报告 API |
| `classes.ts` | 班级 API |
| `devices.ts` | 设备 API |
| `groups.ts` | 小组 API |
| `market.ts` | 商城 API |
| `plants.ts` | 植物 API |
| `profile.ts` | 个人中心 API |
| `teaching.ts` | 教学内容 API |
| `users.ts` | 用户管理 API |

#### API 基址推导策略

1. 优先读取 `VITE_API_BASE_URL`
2. 开发模式（5173/4173/3000 端口）：推导为 `hostname:8000/api`
3. 生产模式：推导为 `origin/api`
4. 网络失败时自动在候选地址间回退重试

### 组合式函数 — `composables/`

| 函数 | 职责 |
|------|------|
| `useCurrentUser` | 当前用户状态管理，失败短冷却防抖 |
| `usePagination` | 分页逻辑，页码钳制防幽灵空页 |
| `useTheme` | 四模式主题管理（light/dark/modern/system），localStorage 持久化 |
| `useFileValidation` | 文件类型与大小校验 |

### 工具函数 — `utils/`

| 文件 | 职责 |
|------|------|
| `authSession.ts` | Token 存取、用户角色缓存、认证状态清理 |
| `error.ts` | 统一错误解析（FastAPI validation error / HTTP error / network error） |
| `aiMarkdown.ts` | AI 回答 Markdown 解析配置 |
| `runtimeGuards.ts` | 运行时安全检查 |

### 主题系统 — `styles/theme.css` + `composables/useTheme.ts`

- CSS 变量驱动，支持 light / dark / modern / system 四模式
- `system` 模式跟随 `prefers-color-scheme` 媒体查询
- 主题偏好持久化到 `localStorage`（键名 `ui.theme.mode`）
- 图表配色通过 CSS 变量联动，切换主题即时刷新
- 全局路由过渡动画，`prefers-reduced-motion` 无障碍兼容

### 关键组件

| 组件 | 职责 |
|------|------|
| `Dashboard.vue` | 监控仪表盘（设备选择、实时数据、远程控制、导出对话框） |
| `TelemetryChart.vue` | ECharts 图表（温湿度/土壤/光照趋势） |
| `FloatingAIAssistant.vue` | AI 助手浮窗（会话管理、流式输出、Markdown 渲染、深度思考/智能搜索切换） |
| `AppLayout.vue` | 全局布局框架 |
| `AppTopBar.vue` | 顶部导航（含主题切换器） |
| `NotificationBell.vue` | 通知铃铛（未读角标） |
| `DashboardDisplay.vue` | 数据大屏（全屏展示，防重入刷新） |
| `AIMarkdownContent.vue` | AI Markdown 富文本渲染（代码高亮/KaTeX/Mermaid 按需加载） |
| `MarketProductCard.vue` | 商城商品卡片 |

---

## 数据库迁移 — Alembic

迁移脚本位于 `alembic/versions/`：

| 版本 | 说明 |
|------|------|
| 0001 | 初始 Schema |
| 0002 | 实验报告文件字段 |
| 0003 | 个人中心评论通知 |
| 0004 | AI 会话历史 |
| 0005 | AI 会话置顶 |
| 0006 | 置顶字段 server default |
| 0007 | 角色 owner 权限（created_by 字段） |
| 0008 | 商城标签 |
| 0009 | 设备执行器级别（风扇速度/灯光亮度） |

---

## ESP32 硬件端

| 文件 | 说明 |
|------|------|
| `esp32_telemetry.ino` | 温湿度/土壤/光照传感器数据采集与 HTTP 上报 |
| `esp32_plant_monitor_uart.ino` | 植物监测 UART 通信版本 |
| `simulate_esp32.py` | 无硬件时的 Python 模拟器 |

上报协议：POST `/api/telemetry`，Header `X-Device-Token` 鉴权，JSON body 含 `device_id` + 传感器读数。

---

## 视觉与交互规范

- 毛玻璃布局：左侧固定导航 + 主内容沉浸式背景
- 统一圆角与阴影层级
- AI 面板：深度思考折叠展示，强调可解释性
- 主题变量覆盖图表、卡片、焦点态和动效参数
- Vite 分包策略：`vue/http/chart/ep/icons` 稳定 vendor 分层
- 浮窗 AI 组件异步加载，降低首屏主包压力

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目总览、快速上手、接口参考 |
| [MAINTENANCE_GUIDE.md](MAINTENANCE_GUIDE.md) | 维护操作标准、排障手册 |
| [DEPLOY_AND_DEMO.md](../DEPLOY_AND_DEMO.md) | 部署流程、演示指南 |
| [CHANGES.md](../CHANGES.md) | 版本变更记录 |

---

**最后更新**: 2026-04-21
