# 智慧大棚 IoT 教学系统

面向中小学科学课的物联网教学平台，集成环境监测、远程控制、教学内容管理、AI 科学助手、实验报告与植物档案等全栈能力。

## 文档导航

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目总览、快速上手、接口参考 |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | 模块架构、代码结构、设计说明 |
| [docs/MAINTENANCE_GUIDE.md](docs/MAINTENANCE_GUIDE.md) | 维护操作标准、排障手册 |
| [DEPLOY_AND_DEMO.md](DEPLOY_AND_DEMO.md) | 部署流程、演示指南 |
| [CHANGES.md](CHANGES.md) | 版本变更记录 |

---

## 核心特性

### 物联网监控

- **三级权限 (RBAC)**：学生（只读）、教师（监控+控制）、管理员（全权限）
- **实时数据**：5 秒刷新，WebSocket 毫秒级推送
- **远程控制**：水泵、风扇、植物灯开关与强度调节
- **数据导出**：CSV / Excel，最多 31 天
- **可视化**：ECharts 动态图表（温湿度、土壤、光照）
- **设备微孪生**：CSS/Vue 动画呈现温室设备实时状态

### 教学管理

- **教学内容**：文章/视频/图片/文档，多标签组织，附件上传
- **学习记录**：进度跟踪、时长统计、完成状态
- **评论互动**：回复、点赞、站内消息提醒
- **学习统计**：班级进度与完成率分析

### 实验报告

- 教师布置任务（含截止时间），学生在线提交报告
- 教师批改评分，AI 辅助点评建议
- 报告文件上传下载，自动关联传感器数据

### 植物生长档案

- 独立植物档案，生长阶段标记（种子→发芽→幼苗→开花→结果→收获）
- 时间轴展示，高度/叶片/花朵等量化记录

### 小组合作

- 创建学习小组，分配设备与植物
- 角色分配：组长、记录员、操作员、汇报员

### AI 科学助手

- **DeepSeek + LangChain**：上下文感知科学问答
- **RAG 检索增强**：本地 Chroma 向量索引检索教学内容
- **多会话管理**：新建/切换/重命名/删除/置顶
- **深度思考**：可切换 deepseek-reasoner 模型
- **智能联网**：实时天气检索、来源引用对齐
- **Markdown 富文本**：代码高亮、表格、KaTeX 公式、Mermaid 图
- **AI 审计**：统一记录来源、耗时、Token 用量与回退原因

### 其他

- **邀请码注册**：学生/教师自助注册并自动绑定班级
- **线下商城**：农作物/花卉信息展示，线下联系
- **数据大屏**：全屏展示模式，无需登录，适合公开课
- **主题系统**：light / dark / modern / system 四模式
- **操作日志**：管理员查看与导出

---

## 技术架构

```
┌─────────────┐     HTTP/JSON  ┌──────────────────┐    SQLAlchemy    ┌─────────┐
│   ESP32     │ ─────────────> │   FastAPI 后端    │ ───────────────> │  MySQL  │
│  (硬件端)   │                │  + WebSocket/SSE  │                  │  8.0+   │
└─────────────┘                │  + LangChain/RAG  │                  └─────────┘
                               └──────────────────┘
                                      ▲  ▲
                        HTTP/REST     │  │     WebSocket/SSE
                                      ▼  ▼
                               ┌──────────────────┐
                               │   Vue 3 + TS     │
                               │   Element Plus   │
                               │   ECharts        │
                               └──────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI + Uvicorn | 异步 Web 框架，支持 WebSocket/SSE |
| **ORM** | SQLAlchemy + Alembic | 数据库操作与迁移管理 |
| **认证** | python-jose + passlib | JWT Token + bcrypt 密码哈希 |
| **AI** | LangChain + DeepSeek + Chroma | 问答编排、向量检索、流式输出 |
| **数据处理** | Pandas + OpenPyXL | 数据导出 |
| **前端框架** | Vue 3 + TypeScript + Vite | SPA 应用 |
| **UI 组件** | Element Plus + Lucide Icons | 组件库与图标 |
| **可视化** | ECharts | 传感器数据图表 |
| **Markdown** | markdown-it + highlight.js + KaTeX + Mermaid | AI 回答富文本渲染 |
| **HTTP 客户端** | Axios | API 请求与拦截器 |
| **部署** | Docker + Docker Compose + Nginx | 容器化部署 |
| **CI** | GitHub Actions | 自动语法检查与构建 |
| **数据库** | MySQL 8.0+ | InnoDB, utf8mb4 |
| **硬件** | ESP32 + ArduinoJson | 传感器数据采集与上报 |

---

## 快速上手

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 环境变量

复制 `.env.example` 为 `.env` 并修改关键配置：

```bash
# 必须修改
DATABASE_URL=mysql+pymysql://greenhouse_user:your_password@localhost:3306/smart_greenhouse
SECRET_KEY=<openssl rand -hex 32 生成>

# 可选 - AI 助手
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 可选 - 演示数据
SEED_DEMO_DATA=true
DEMO_ADMIN_PASSWORD=admin123
DEMO_TEACHER_PASSWORD=teacher123
DEMO_STUDENT_PASSWORD=student123
```

### 首次部署

```bash
# 1. 初始化数据库
python init_db.py

# 2. 执行迁移（版本升级时）
python -m alembic upgrade head
```

### 启动服务

```bash
# 后端（端口 8000）
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 前端（端口 5173，新终端）
cd frontend
npm install
npm run dev

# 模拟 ESP32 数据（可选，新终端）
python simulate_esp32.py
```

### 访问地址

| 入口 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173 |
| 数据大屏 | http://localhost:5173/display（无需登录） |
| API 文档 | http://localhost:8000/docs |
| 用户注册 | http://localhost:5173/register |

### Docker 一键部署

```bash
docker-compose up -d --build
```

默认前端访问 http://localhost:80，后端 API http://localhost:8000/docs。

### 默认账号

`init_db.py` 采用"环境变量优先 + 随机强密码兜底"策略。若设置了 `SEED_DEMO_DATA=true` 及 `DEMO_*_PASSWORD`，则使用指定密码；否则生成随机密码并打印到控制台。

联调测试可执行：`python scripts/set_test_passwords.py`

---

## 目录结构

```
d:\4C\
├── main.py                          # FastAPI 入口（路由装配）
├── requirements.txt                 # Python 依赖
├── Dockerfile                       # 后端容器构建
├── docker-compose.yml               # 编排配置
├── alembic.ini                      # 数据库迁移配置
├── .env.example                     # 环境变量模板
│
├── app/                             # 后端模块化目录
│   ├── api/
│   │   ├── dependencies.py          # 通用依赖（DB 会话、认证、权限）
│   │   └── routes/                  # 路由模块
│   │       ├── auth.py              # 认证（登录/注销/注册）
│   │       ├── telemetry.py         # 设备/遥测/AI 会话/WebSocket
│   │       ├── content.py           # 教学内容与学习记录
│   │       ├── users.py             # 用户与班级管理
│   │       ├── assignments.py       # 实验报告
│   │       ├── plants.py            # 植物档案
│   │       ├── groups.py            # 小组合作
│   │       ├── market.py            # 线下商城
│   │       ├── profile.py           # 个人中心
│   │       ├── history.py           # 历史数据
│   │       └── logs.py              # 操作日志
│   ├── core/
│   │   ├── config.py                # 配置管理（环境变量加载）
│   │   ├── security.py              # 安全组件（JWT/bcrypt/OAuth2）
│   │   ├── permission.py            # 权限判定（班级/设备/小组/植物）
│   │   ├── validators.py            # 输入校验（密码/用户名/邮箱）
│   │   └── bootstrap.py             # 启动种子数据
│   ├── db/
│   │   ├── base.py                  # SQLAlchemy Base
│   │   ├── models.py                # 全部数据库模型
│   │   └── session.py               # 数据库会话工厂
│   ├── schemas/                     # Pydantic 请求/响应模型
│   │   ├── auth.py, content.py, market.py
│   │   ├── plants.py, users.py, telemetry.py
│   │   ├── assignments.py, groups.py, profile.py
│   └── services/                    # 业务逻辑层
│       ├── ai_science_service.py    # AI 问答编排与联网检索
│       ├── langchain_service.py     # LangChain 模型调用与提示词
│       ├── rag_service.py           # 教学内容向量索引与检索
│       ├── ai_audit_service.py      # AI 调用审计记录
│       ├── telemetry_hub_service.py # WebSocket 连接管理
│       ├── plants_service.py        # 植物档案业务逻辑
│       ├── groups_service.py        # 小组业务逻辑
│       ├── history_service.py       # 历史数据查询
│       ├── profile_service.py       # 个人中心业务逻辑
│       └── notification_service.py  # 站内通知
│
├── alembic/versions/                # 数据库迁移脚本
├── scripts/                         # 工具脚本
│   ├── set_test_passwords.py        # 设置测试密码
│   ├── simulate_esp32.py            # ESP32 模拟器
│   ├── ux_api_probe.py              # API 闭环探测
│   ├── ai_regression_probe.py       # AI 回归探测
│   └── stability_regression_probe.py # 稳定性探测
├── docs/                            # 项目文档
├── uploads/                         # 上传文件目录
│   ├── plants/ avatars/ content/ market/
│   └── assignment_reports/
│
├── frontend/                        # Vue 3 前端
│   ├── src/
│   │   ├── main.ts                  # 入口
│   │   ├── App.vue                  # 根组件
│   │   ├── api/                     # API 封装与类型
│   │   │   ├── index.ts             # Axios 实例、拦截器、基础 API
│   │   │   ├── assignments.ts, classes.ts, devices.ts
│   │   │   ├── groups.ts, market.ts, plants.ts
│   │   │   ├── profile.ts, teaching.ts, users.ts
│   │   ├── components/              # 公共组件
│   │   │   ├── Dashboard.vue        # 监控仪表盘
│   │   │   ├── TelemetryChart.vue   # ECharts 图表
│   │   │   ├── FloatingAIAssistant.vue # AI 助手浮窗
│   │   │   ├── AppLayout.vue        # 布局框架
│   │   │   ├── AppTopBar.vue        # 顶部导航
│   │   │   ├── NotificationBell.vue # 通知铃铛
│   │   │   ├── StatusPanel.vue      # 状态面板
│   │   │   ├── MarketProductCard.vue # 商城卡片
│   │   │   └── AIMarkdownContent.vue # AI Markdown 渲染
│   │   ├── composables/             # 组合式函数
│   │   │   ├── useCurrentUser.ts    # 当前用户状态
│   │   │   ├── usePagination.ts     # 分页逻辑
│   │   │   ├── useTheme.ts          # 主题管理
│   │   │   └── useFileValidation.ts # 文件校验
│   │   ├── directives/              # 自定义指令
│   │   │   └── lazy.ts              # 懒加载
│   │   ├── router/index.ts          # 路由与权限守卫
│   │   ├── styles/theme.css         # 主题变量
│   │   ├── utils/                   # 工具函数
│   │   │   ├── authSession.ts       # 认证会话管理
│   │   │   ├── error.ts             # 统一错误处理
│   │   │   ├── aiMarkdown.ts        # AI Markdown 解析
│   │   │   └── runtimeGuards.ts     # 运行时守卫
│   │   └── views/                   # 页面视图
│   │       ├── Login.vue, Register.vue
│   │       ├── StudentHome.vue, TeacherHome.vue, AdminHome.vue
│   │       ├── TeachingContents.vue, Market.vue
│   │       ├── UserManagement.vue, OperationLogs.vue
│   │       ├── TeachingAnalytics.vue, Profile.vue
│   │       ├── DashboardDisplay.vue  # 数据大屏
│   │       ├── Assignments/          # 角色分发入口
│   │       ├── Plants/
│   │       └── Groups/
│   ├── Dockerfile                   # 前端容器构建
│   ├── nginx.conf                   # Nginx 配置
│   ├── vite.config.ts               # Vite 构建配置
│   └── package.json
│
├── esp32_telemetry.ino              # ESP32 遥测代码
├── esp32_plant_monitor_uart.ino     # ESP32 植物监测代码
└── init_db.py, reset_admin_password.py, clear_contents.py  # 工具脚本
```

---

## API 接口参考

### 认证

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| POST | `/token` | 公开 | 登录获取 JWT（含登录频控） |
| POST | `/api/auth/logout` | 认证 | 注销（Token 拉黑） |
| POST | `/api/auth/register` | 公开 | 邀请码注册 |

### 个人中心与通知

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/profile/me` | 认证 | 个人信息（含待办统计） |
| PATCH | `/api/profile/me` | 认证 | 修改展示名称 |
| POST | `/api/profile/avatar` | 认证 | 上传头像（jpg/png/webp, ≤2MB） |
| GET | `/api/notifications` | 认证 | 通知列表（分页） |
| GET | `/api/notifications/unread-count` | 认证 | 未读数 |
| POST | `/api/notifications/{id}/read` | 认证 | 标记已读 |
| POST | `/api/notifications/read-all` | 认证 | 全部已读 |

### 设备与传感器

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/telemetry` | Device Token | ESP32 上报数据 |
| GET | `/api/devices` | 认证 | 设备列表 |
| POST | `/api/devices` | 管理员 | 创建设备 |
| GET | `/api/history/{device_id}` | 认证 | 历史数据（最近 20 条） |
| POST | `/api/control/{device_id}` | 教师/管理员 | 远程控制 |
| POST | `/api/telemetry/export` | 认证 | 导出 CSV/Excel（≤31 天） |
| WS | `/ws/telemetry/{device_id}` | 认证 | 实时数据推送 |

### AI 科学助手

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/ai/science-assistant` | 认证 | 科学问答 |
| POST | `/api/ai/science-assistant/stream` | 认证 | 流式问答（SSE） |
| GET | `/api/ai/conversations` | 认证 | 会话列表 |
| POST | `/api/ai/conversations` | 认证 | 创建会话 |
| GET | `/api/ai/conversations/{id}` | 认证 | 会话详情 |
| PATCH | `/api/ai/conversations/{id}/title` | 认证 | 重命名 |
| DELETE | `/api/ai/conversations/{id}` | 认证 | 删除会话 |
| POST | `/api/ai/conversations/{id}/science-assistant` | 认证 | 会话内问答 |
| POST | `/api/ai/conversations/{id}/science-assistant/stream` | 认证 | 会话内流式问答 |
| POST | `/api/assignments/{id}/ai-feedback` | 教师/管理员 | AI 点评建议 |
| POST | `/api/content/ai/polish` | 教师/管理员 | AI 内容润色 |
| POST | `/api/content/ai/reindex` | 管理员 | 重建 RAG 索引 |

AI 问答请求体支持：`enable_deep_thinking`（切换 reasoner 模型）、`enable_web_search`（联网检索+来源引用）。

### 公开大屏

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/public/display` | 公开 | 大屏实时数据 |
| GET | `/api/public/history/{device_id}` | 公开 | 大屏趋势历史 |

### 教学内容

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/content/contents` | 认证 | 内容列表（标签/搜索/分页） |
| GET | `/api/content/contents/{id}` | 认证 | 内容详情 |
| POST | `/api/content/contents` | 教师/管理员 | 创建内容 |
| PUT | `/api/content/contents/{id}` | 教师/管理员 | 更新内容 |
| DELETE | `/api/content/contents/{id}` | 教师/管理员 | 删除内容 |
| POST | `/api/content/upload` | 教师/管理员 | 上传附件 |
| POST | `/api/content/contents/{id}/publish` | 教师/管理员 | 发布/取消发布 |
| GET | `/api/content/my-learning` | 认证 | 学习记录 |
| POST | `/api/content/contents/{id}/start` | 认证 | 开始学习 |
| POST | `/api/content/contents/{id}/complete` | 认证 | 完成学习 |
| PUT | `/api/content/contents/{id}/progress` | 认证 | 更新进度 |
| GET | `/api/content/contents/{id}/comments` | 认证 | 评论列表 |
| POST | `/api/content/contents/{id}/comments` | 认证 | 添加评论 |
| POST | `/api/content/comments/{id}/like` | 认证 | 点赞/取消 |
| GET | `/api/content/stats/overview` | 教师/管理员 | 学习统计概览 |

### 用户与班级管理

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/users` | 管理员 | 用户列表（搜索/分页） |
| POST | `/api/users` | 管理员 | 创建用户 |
| PUT | `/api/users/{id}` | 管理员 | 更新用户 |
| DELETE | `/api/users/{id}` | 管理员 | 删除用户 |
| POST | `/api/users/{id}/reset-password` | 管理员 | 重置密码 |
| POST | `/api/users/{id}/toggle-active` | 管理员 | 启用/禁用 |
| POST | `/api/users/batch-create` | 管理员 | 批量创建 |
| POST | `/api/users/import` | 管理员 | Excel 导入 |
| GET | `/api/users/export` | 管理员 | 导出 CSV |
| POST | `/api/users/batch-delete` | 管理员 | 批量删除 |
| POST | `/api/users/batch-update-class` | 管理员 | 批量改班 |
| POST | `/api/users/batch-reset-password` | 管理员 | 批量重置密码 |
| GET | `/api/classes` | 认证 | 班级列表 |
| POST | `/api/classes` | 管理员 | 创建班级 |
| POST | `/api/classes/{id}/refresh-invite-code` | 管理员 | 刷新邀请码 |
| GET | `/api/classes/{id}/students` | 认证 | 班级学生 |
| POST | `/api/classes/{id}/devices/bind` | 管理员 | 绑定设备 |

### 实验报告

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/assignments` | 认证 | 任务列表（支持分页） |
| POST | `/api/assignments` | 教师/管理员 | 创建任务 |
| PUT | `/api/assignments/{id}` | 教师/管理员 | 更新任务（仅本人） |
| DELETE | `/api/assignments/{id}` | 教师/管理员 | 删除任务（仅本人） |
| GET | `/api/assignments/{id}/submissions` | 认证 | 提交列表 |
| POST | `/api/assignments/{id}/submit` | 学生 | 提交报告 |
| POST | `/api/assignments/{id}/submit-with-file` | 学生 | 上传文件并提交 |
| GET | `/api/assignments/submissions/{id}/file` | 认证 | 下载附件 |
| POST | `/api/assignments/{id}/grade` | 教师/管理员 | 批改（仅本人任务） |

### 植物档案

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/plants` | 认证 | 植物列表 |
| POST | `/api/plants` | 教师/管理员 | 创建档案 |
| PUT | `/api/plants/{id}` | 教师/管理员 | 更新（仅本人创建） |
| DELETE | `/api/plants/{id}` | 教师/管理员 | 删除（仅本人创建） |
| GET | `/api/plants/{id}/records` | 认证 | 生长记录 |
| POST | `/api/plants/{id}/records` | 认证 | 添加记录 |
| POST | `/api/admin/plants/{id}/migrate` | 管理员 | 跨班迁移 |

### 小组合作

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/groups` | 认证 | 小组列表 |
| POST | `/api/groups` | 教师/管理员 | 创建小组 |
| PUT | `/api/groups/{id}` | 教师/管理员 | 更新（仅本人创建） |
| DELETE | `/api/groups/{id}` | 教师/管理员 | 删除（仅本人创建） |
| POST | `/api/groups/{id}/members` | 教师/管理员 | 添加成员 |
| POST | `/api/admin/groups/{id}/migrate` | 管理员 | 跨班迁移 |
| POST | `/api/admin/groups/{id}/members/batch-role` | 管理员 | 批量修正角色 |

### 线下商城

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/market/products` | 认证 | 商品列表（搜索/分页） |
| POST | `/api/market/products` | 认证 | 发布商品 |
| PUT | `/api/market/products/{id}` | 认证 | 更新（发布者/管理员） |
| DELETE | `/api/market/products/{id}` | 认证 | 删除（发布者/管理员） |
| POST | `/api/market/upload-image` | 认证 | 上传商品图片 |

### 操作日志

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/logs/operations` | 管理员 | 日志列表（分页） |
| POST | `/api/logs/operations/export` | 管理员 | 导出 Excel |

---

## 权限体系

### 角色权限矩阵

| 功能 | 学生 | 教师 | 管理员 |
|------|------|------|--------|
| 监控仪表盘 | 只读 | 读写 | 读写 |
| 远程控制 | - | ✅ | ✅ |
| 教学内容 | 学习/评论 | 创建/管理本人 | 全部 |
| 用户管理 | - | - | ✅ |
| 实验报告 | 提交 | 全校可见/仅本人可写 | 全部 |
| 植物档案 | 查看/小组成员添加记录 | 全校可见/仅本人可写 | 全部+跨班迁移 |
| 小组 | 查看 | 全校可见/仅本人可写 | 全部+跨班迁移 |
| AI 助手 | ✅ | ✅ | ✅ |
| 线下商城 | 查看/发布 | 查看/发布 | 全部 |
| 操作日志 | - | - | ✅ |

### 密码策略

| 角色 | 要求 |
|------|------|
| 学生 | 至少 6 位 |
| 教师/管理员 | 至少 8 位，含大小写字母和数字 |

### 认证机制

- JWT (HS256)，有效期通过 `ACCESS_TOKEN_EXPIRE_MINUTES` 配置（默认 30 分钟）
- Token 存储于 localStorage，Axios 拦截器自动注入
- 登录频控：IP+用户名窗口内最多 8 次失败
- 注销时 Token 加入黑名单

---

## 数据库模型概览

| 模型 | 表名 | 说明 |
|------|------|------|
| User | users | 用户（含角色/班级/头像） |
| Device | devices | IoT 设备 |
| SensorReading | sensor_readings | 传感器读数 |
| Class | classes | 班级（含邀请码） |
| ClassDeviceBind | class_device_binds | 班级-设备绑定 |
| TeachingContent | teaching_contents | 教学内容 |
| StudentLearningRecord | student_learning_records | 学习记录 |
| ContentComment | content_comments | 评论/回复 |
| ContentCommentLike | content_comment_likes | 评论点赞 |
| UserNotification | user_notifications | 站内通知 |
| UserOperationLog | user_operation_logs | 操作日志（含 AI 审计） |
| MarketProduct | market_products | 线下商城商品 |
| Assignment | assignments | 实验任务 |
| AssignmentSubmission | assignment_submissions | 实验报告提交 |
| PlantProfile | plant_profiles | 植物档案 |
| GrowthRecord | growth_records | 生长记录 |
| StudyGroup | study_groups | 学习小组 |
| GroupMember | group_members | 小组成员 |
| AIConversation | ai_conversations | AI 会话 |
| AIConversationMessage | ai_conversation_messages | AI 会话消息 |

---

## 环境变量参考

### 必需

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | MySQL 连接字符串 |
| `SECRET_KEY` | JWT 签名密钥（生产环境必须修改） |

### 认证与安全

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `JWT_ALGORITHM` | HS256 | JWT 算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Token 有效期 |
| `DEVICE_TOKEN` | default_secret_device_token | ESP32 上报鉴权 |
| `CORS_ORIGINS` | localhost:5173 等 | CORS 白名单 |
| `CORS_ORIGIN_REGEX` | 局域网自动放行 | CORS 正则 |

### AI 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_KEY` | - | DeepSeek API Key |
| `DEEPSEEK_MODEL` | deepseek-chat | 基础模型 |
| `DEEPSEEK_BASE_URL` | https://api.deepseek.com/v1 | API 地址 |
| `AI_CHAT_MODEL` | deepseek-chat | 普通问答模型 |
| `AI_REASONER_MODEL` | deepseek-reasoner | 深度思考模型 |
| `AI_LANGCHAIN_ENABLED` | true | 启用 LangChain |
| `AI_STREAM_ENABLED` | true | 启用流式输出 |
| `AI_TEMPERATURE` | 0.4 | 模型温度 |
| `AI_MAX_TOKENS` | 600 | Token 上限 |
| `AI_TIMEOUT_SECONDS` | 20 | 调用超时 |
| `AI_STREAM_TIMEOUT_SECONDS` | 45 | 流式超时 |
| `AI_RETRY_COUNT` | 1 | 重试次数 |
| `AI_RETRY_BACKOFF_MS` | 300 | 重试退避 |
| `RAG_ENABLED` | true | 启用 RAG |
| `RAG_INDEX_DIR` | data/chroma | 索引目录 |
| `RAG_TOP_K` | 4 | 检索片段数 |

### 演示数据

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SEED_DEMO_DATA` | false | 启用演示数据 |
| `DEMO_ADMIN_PASSWORD` | - | 管理员密码 |
| `DEMO_TEACHER_PASSWORD` | - | 教师密码 |
| `DEMO_STUDENT_PASSWORD` | - | 学生密码 |

---

## 安全配置

### 生产环境必须修改

1. `SECRET_KEY` — 使用 `openssl rand -hex 32` 生成
2. `DATABASE_URL` — 使用专用数据库用户，强密码
3. `DEVICE_TOKEN` — 更换为安全随机值
4. `CORS_ORIGINS` — 限制为实际域名
5. 启用 HTTPS（Nginx 反向代理 + Let's Encrypt）
6. 修改默认账号密码

### 推荐加固

```sql
CREATE USER 'greenhouse'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON smart_greenhouse.* TO 'greenhouse'@'localhost';
```

---

## 常见问题

**测试账号无法登录** — 执行 `python scripts/set_test_passwords.py`

**后端启动失败** — 检查 MySQL 服务、`DATABASE_URL`、`SECRET_KEY`、`pip install -r requirements.txt`

**前端构建错误** — 清除缓存 `rm -rf node_modules/.vite`，确认 Node.js 18+

**AI 助手 Network Error** — 确认后端 8000 端口可达，前端使用 localhost:5173 访问

**AI 会话 404/503** — 执行 `python -m alembic upgrade head` 确保会话表存在

**AI 天气无实时结果** — 确认提问含城市名、开启智能搜索、检查外网访问

**CORS 错误** — 配置 `CORS_ORIGINS` 或 `CORS_ORIGIN_REGEX` 放行前端来源

---

## 项目统计

| 指标 | 数量 |
|------|------|
| 数据库表 | 20 |
| API 端点 | 100+ |
| 前端视图 | 20+ |
| 数据库迁移 | 9 版本（head: 0009） |
| 后端路由模块 | 11 |
| 后端服务模块 | 10 |

---

**最后更新**: 2026-04-21
**文档版本**: 4.0
