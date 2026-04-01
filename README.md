# 智慧大棚教具系统 - 项目上下文文档

## 📋 项目概述

**智慧大棚 IoT 系统**是一款面向中小学生科学课设计的物联网教学设备。系统采用完整的全栈架构，实现环境监测、远程控制、权限管理、数据可视化、教学内容和用户管理功能。

### 核心特性

#### 物联网监控功能
- **三级权限系统 (RBAC)**：学生（只读）、教师（监控 + 控制）、管理员（全权限）
- **实时数据更新**：5 秒刷新周期
- **远程控制**：水泵、风扇、植物灯开关控制
- **数据导出**：支持 CSV/Excel 格式导出传感器历史记录（最多 31 天）
- **数据可视化**：ECharts 动态图表展示温湿度、土壤湿度、光照变化

#### 教学管理功能
- **教学内容管理**：支持文章、视频、图片等多种格式，分类树形结构
- **学生学习记录**：跟踪学习进度、时长、完成状态
- **评论互动系统**：所有登录用户可评论、回复、点赞
- **站内消息提醒**：评论被回复/被点赞时自动提醒（未读角标 + 消息列表）
- **学习统计**：教师可查看班级学习进度和完成率

#### 个人中心增强（已完成）⭐
- **头像上传**：支持 jpg/jpeg/png/webp 格式，大小不超过 2MB
- **名称修改**：用户可在个人中心修改展示名称（2-20 字）
- **跨页面展示**：头像与名称在评论区、个人中心统一展示

#### 实验报告系统（已完成）⭐
- **实验任务管理**：教师可布置实验任务，设置截止时间
- **在线提交报告**：学生可在线提交实验报告，记录观察数据
- **批改评分**：教师可在线批改报告，给出分数和评语
- **实验数据关联**：自动关联传感器历史数据

#### 植物生长档案（已完成）⭐
- **植物档案管理**：为每株植物建立独立档案
- **生长记录跟踪**：记录植物各阶段生长数据（高度、叶片数、花朵数等）
- **生长阶段标记**：种子→发芽→幼苗→开花→结果→收获
- **时间轴展示**：以时间轴形式展示植物生长历程

#### 数据大屏展示（已完成）⭐
- **全屏展示模式**：支持 F11 全屏，适合公开课展示
- **实时数据展示**：温度、湿度、土壤湿度、光照强度
- **设备状态监控**：水泵、风扇、植物灯状态
- **生长记录时间轴**：最近植物生长记录
- **无需登录**：公开访问模式

#### STEAM 教育深度集成（已完成）⭐
- **AI 科学助手**：接入 Qwen 大模型，支持上下文感知、设备状态诊断和解答科学问题，集成知识库兜底。
- **无 Key 稳定兜底**：当 `QWEN_API_KEY` 未配置或外部接口异常时，自动切换为 rule-based 科学解释，保证课堂演示不中断。
- **设备微孪生 (Digital Twin)**：基于 CSS/Vue 动画实现的温室设备实时状态呈现（风扇转动、水波纹等）。
- **实时数据流**：借助 WebSocket 实现毫秒级数据推送，低延迟同步呈现设备信息。
- **师生双视角闭环**：前端原生支持多角色渲染。学生享有游戏化学习体验；老师拥有专属分析大屏 (`TeachingAnalytics.vue`) 了解学生作业提交率与设备健康度。
- **答辩演示场景模式**：一键下发极端环境场景指令（如“干旱预警”、“极端高温”），应对比赛现场实机演示大屏效果。

#### 小组合作学习（已完成）⭐
- **小组管理**：创建学习小组，分配设备和植物
- **角色分配**：组长、记录员、操作员、汇报员
- **成员管理**：添加/移除小组成员

## ✅ 2026-03-31 闭环优化与验证结果

本轮已完成“用户端功能闭环测试 + 高优问题实装修复 + 自动化回归验证”。

- 闭环实测：教师布置任务 -> 学生提交 -> 教师批改 -> 学生查看状态，全链路通过。
- 自动化探测：`scripts/ux_api_probe.py` 执行结果 `24/24` 通过。
- 证据文件：`docs/ux_api_probe_results_2026-03-31.json`。
- 详细报告：`docs/UX_CLOSED_LOOP_TEST_REPORT_2026-03-31.md`。

本轮关键落地点：

- 修复初始化阻断问题：`init_db.py` 可正常执行，默认账号改为“环境变量优先 + 随机强口令兜底”。
- 修复管理员重置脚本：`reset_admin_password.py` 与当前安全组件一致。
- 强化实验提交流程权限：仅学生可提交报告（普通提交与文件提交均受限）。
- 大屏改为真实历史数据：新增公开历史接口并支持按设备展示。
- 前端体验收敛：登录/越权引导、错误提示可行动化、日期本地化、防连点与静默失败提示。

#### 用户与班级管理
- **批量操作**：批量删除、批量修改班级、批量重置密码
- **班级管理**：创建班级、分配班主任、学生归属班级
- **操作日志**：记录所有用户管理操作

## 🏗️ 技术架构

```
┌─────────────┐     HTTP      ┌─────────────┐     HTTP      ┌─────────────┐
│   ESP32     │ ────────────> │  FastAPI    │ ────────────> │   MySQL     │
│  (硬件端)   │   JSON 数据    │  (后端)     │   SQLAlchemy  │  (数据库)   │
└─────────────┘               └─────────────┘               └─────────────┘
                                   ▲  ▲
                 HTTP/REST, WebSocket │
                                   ▼  ▼
                            ┌─────────────┐
                            │  Vue 3 + TS │
                            │  (前端)     │
                            └─────────────┘
```

### 技术栈详情

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端** | Python, FastAPI (WebSockets), SQLAlchemy, PyJWT, Passlib, Qwen HTTP | Python 3.10+ |
| **前端** | Vue 3, TypeScript, Vite, Element Plus, ECharts, Lucide Icons | Node.js 18+ |
| **部署/CI** | Docker, Docker Compose, GitHub Actions | - |
| **数据库** | MySQL | 8.0+ |
| **硬件** | ESP32, ArduinoJson | - |
| **数据处理** | Pandas, OpenPyXL | Pandas 2.0+ |
| **数据库迁移** | Alembic | - |

## 🧩 模块化拆分（2026-03-26）

为降低 `main.py` 耦合并提升可维护性，本次已完成首轮后端模块化拆分：

- 抽离认证与安全组件到 `app/core/security.py`
- 抽离 FastAPI 共享依赖到 `app/api/dependencies.py`
- 抽离认证路由到 `app/api/routes/auth.py`（`/token`、`/api/auth/logout`）
- 抽离设备与遥测路由到 `app/api/routes/telemetry.py`（设备、上报、控制、WebSocket、导出与公开大屏）
- 抽离植物记录请求模型到 `app/schemas/plants.py`
- 抽离认证响应模型到 `app/schemas/auth.py`
- 抽离设备与遥测模型到 `app/schemas/telemetry.py`
- 抽离实时连接管理到 `app/services/telemetry_hub_service.py`
- 抽离 AI 科学助手逻辑到 `app/services/ai_science_service.py`
- 将 `app/api/routes/*` 从 `from main import ...` 改为依赖 `app` 内部模块，去除反向耦合

说明：当前 `main.py` 仍保留既有 API 路由定义与路径，不影响前端和外部调用。

## 📁 目录结构（关键目录）

```
d:\4C\
├── main.py                    # FastAPI 入口（保留既有 API 路由）
├── requirements.txt           # Python 依赖
├── alembic.ini               # Alembic 数据库迁移配置
├── alembic/                  # 数据库迁移脚本目录
├── init_db.sql               # 数据库初始化脚本（已废弃，使用 SQLAlchemy 自动创建）
├── simulate_esp32.py         # ESP32 模拟器（无硬件时使用）
├── esp32_telemetry.ino       # ESP32 真实硬件代码（Arduino C++）
│
├── clear_contents.py         # 清空教学内容脚本
├── init_sample_contents.py   # 初始化示例教学内容脚本
├── migrate_users.py          # 用户数据迁移脚本
├── reset_admin_password.py   # 重置管理员密码脚本
│
├── app/                      # 后端模块化目录
│   ├── __init__.py
│   ├── api/
│   │   ├── dependencies.py   # 通用依赖（get_db/get_current_user/token blacklist）
│   │   └── routes/           # 已拆分路由
│   │       ├── auth.py       # 认证路由
│   │       └── telemetry.py  # 设备/遥测路由
│   ├── core/
│   │   └── config.py        # 配置管理（数据库、JWT、CORS）
│   │   └── security.py       # 安全组件（token 创建、密码哈希、oauth2）
│   └── db/
│       ├── base.py          # SQLAlchemy Base 类
│       ├── models.py        # 所有数据库模型定义（14 个模型）
│       └── session.py       # 数据库会话管理
│   ├── schemas/
│   │   └── auth.py           # 认证模型
│   │   └── plants.py         # 植物记录相关请求模型
│   │   └── telemetry.py      # 设备与遥测相关模型
│   └── services/
│       ├── ai_science_service.py     # AI 科学助手逻辑
│       └── telemetry_hub_service.py  # WebSocket 连接管理
│
└── frontend/                 # Vue 3 前端项目
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    └── src\
        ├── main.ts           # 入口文件
        ├── App.vue
        ├── env.d.ts          # TypeScript 环境声明
        ├── api\
        │   ├── index.ts      # API 封装（含 JWT 拦截器、所有 API 调用）
        │   ├── teaching.ts   # 教学内容 API 导出
        │   └── users.ts      # 用户管理 API 导出
        ├── router\
        │   └── index.ts      # 路由配置（含权限守卫）
        ├── components\
        │   ├── Dashboard.vue # 主仪表盘（含导出对话框、设备选择）
        │   └── TelemetryChart.vue  # ECharts 图表组件
        └── views\
            ├── Login.vue     # 登录页面
            ├── Dashboard.vue # 主仪表盘（已在 components 中）
            ├── DashboardDisplay.vue # 数据大屏展示（公开）
            ├── TeachingContents.vue  # 教学内容浏览页面
            ├── UserManagement.vue    # 用户管理页面（仅管理员）
            ├── Assignments.vue       # 实验报告系统
            └── Plants.vue            # 植物生长档案
```

## 🚀 运行命令

### 环境准备
```bash
# Python 虚拟环境激活（Windows）
.venv\Scripts\activate

# 前端依赖安装（首次运行）
cd frontend && npm install
```

### 启动服务

#### 首次运行（初始化数据库）
```bash
# 1. 初始化数据库（创建默认账号）
cd d:\4C
.venv\Scripts\python.exe init_db.py
```

#### 版本升级（已有数据库）
```bash
# 执行数据库迁移（新增头像、评论互动、站内通知相关表/字段）
cd d:\4C
.venv\Scripts\python.exe -m alembic upgrade head
```

#### 正常启动
```bash
# 1. 启动后端（端口 8000）
cd d:\4C
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000

# 2. 启动前端（端口 5173，新终端）
cd d:\4C\frontend
npm run dev

# 3. 模拟 ESP32 数据（可选，新终端）
cd d:\4C
.venv\Scripts\python.exe simulate_esp32.py
```

### 访问地址
- **前端界面**: http://localhost:5173
- **数据大屏**: http://localhost:5173/display（无需登录）
- **API 文档**: http://localhost:8000/docs
- **数据库**: `smart_greenhouse` (MySQL)

### 默认账号

`init_db.py` 已改为“环境变量优先 + 随机强密码兜底”，不再固定弱口令。

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | `admin` | `DEFAULT_ADMIN_PASSWORD` 或随机生成 | 全权限 |
| 教师 | `teacher` | `DEFAULT_TEACHER_PASSWORD`（默认继承管理员） | 查看 + 控制 + 教学内容管理 |
| 学生 | `student` | `DEFAULT_STUDENT_PASSWORD`（默认继承管理员） | 仅查看 |

说明：
- 若未设置上述环境变量，脚本会为默认账号生成随机强密码并打印到控制台。
- 联调测试可使用 `scripts/set_test_passwords.py` 统一设置测试口令。

## 🔌 核心 API 接口

### 认证
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| POST | `/token` | 公开 | 登录获取 JWT Token |

### 个人中心与站内通知
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/profile/me` | 认证 | 获取个人中心信息（含头像/待办） |
| PATCH | `/api/profile/me` | 认证 | 更新个人展示名称 |
| POST | `/api/profile/avatar` | 认证 | 上传头像图片（jpg/jpeg/png/webp，<=2MB） |
| GET | `/api/notifications` | 认证 | 获取站内通知列表（分页） |
| GET | `/api/notifications/unread-count` | 认证 | 获取未读通知数 |
| POST | `/api/notifications/{id}/read` | 认证 | 标记单条通知已读 |
| POST | `/api/notifications/read-all` | 认证 | 标记全部通知已读 |

### 设备与传感器
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/telemetry` | 公开 | ESP32 上报传感器数据 |
| GET | `/api/devices` | 认证 | 获取设备列表 |
| POST | `/api/devices` | 管理员 | 创建设备 |
| GET | `/api/history/{device_id}` | 认证 | 获取历史数据（最近 20 条） |
| POST | `/api/control/{device_id}` | 教师/管理员 | 远程控制设备 |
| POST | `/api/telemetry/export` | 认证 | 导出传感器数据（CSV/Excel，最多 31 天） |

### 公开数据大屏
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/public/display` | 公开 | 获取大屏展示数据（支持 `device_id` 参数） |
| GET | `/api/public/history/{device_id}` | 公开 | 获取大屏趋势历史数据（`limit` 最大 200） |

### 教学内容管理
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/content/categories` | 认证 | 获取分类列表 |
| GET | `/api/content/categories/tree` | 认证 | 获取分类树形结构 |
| POST | `/api/content/categories` | 教师/管理员 | 创建分类 |
| PUT | `/api/content/categories/{id}` | 教师/管理员 | 更新分类 |
| DELETE | `/api/content/categories/{id}` | 管理员 | 删除分类 |
| GET | `/api/content/contents` | 认证 | 获取内容列表（支持筛选、搜索） |
| GET | `/api/content/contents/{id}` | 认证 | 获取内容详情 |
| POST | `/api/content/contents` | 教师/管理员 | 创建内容 |
| PUT | `/api/content/contents/{id}` | 教师/管理员 | 更新内容 |
| DELETE | `/api/content/contents/{id}` | 教师/管理员 | 删除内容 |
| POST | `/api/content/contents/{id}/publish` | 教师/管理员 | 发布/取消发布内容 |
| GET | `/api/content/my-learning` | 认证 | 获取我的学习记录 |
| POST | `/api/content/contents/{id}/start` | 认证 | 开始学习 |
| POST | `/api/content/contents/{id}/complete` | 认证 | 完成学习 |
| PUT | `/api/content/contents/{id}/progress` | 认证 | 更新学习进度 |
| GET | `/api/content/contents/{id}/comments` | 认证 | 获取评论列表 |
| POST | `/api/content/contents/{id}/comments` | 认证 | 添加评论（支持 `parent_id` 作为回复） |
| POST | `/api/content/comments/{id}/reply` | 认证 | 回复指定评论 |
| POST | `/api/content/comments/{id}/like` | 认证 | 点赞/取消点赞评论（切换） |
| PUT | `/api/content/comments/{id}` | 教师/管理员 | 回复评论 |
| GET | `/api/content/stats/overview` | 教师/管理员 | 获取学习统计概览 |
| GET | `/api/content/stats/students` | 教师/管理员 | 获取所有学生学习进度 |
| GET | `/api/content/stats/content/{id}` | 教师/管理员 | 获取特定内容学习统计 |

### 用户管理（管理员）
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/users` | 管理员 | 获取用户列表（支持搜索、筛选） |
| GET | `/api/users/{id}` | 管理员 | 获取用户详情 |
| POST | `/api/users` | 管理员 | 创建用户 |
| PUT | `/api/users/{id}` | 管理员 | 更新用户 |
| DELETE | `/api/users/{id}` | 管理员 | 删除用户 |
| POST | `/api/users/{id}/reset-password` | 管理员 | 重置密码 |
| POST | `/api/users/{id}/toggle-active` | 管理员 | 启用/禁用账号 |
| POST | `/api/users/batch-create` | 管理员 | 批量创建用户 |
| POST | `/api/users/import` | 管理员 | Excel 导入用户 |
| GET | `/api/users/export` | 管理员 | 导出用户列表（CSV） |
| POST | `/api/users/batch-delete` | 管理员 | 批量删除用户 |
| POST | `/api/users/batch-update-class` | 管理员 | 批量修改班级 |
| POST | `/api/users/batch-reset-password` | 管理员 | 批量重置密码 |
| GET | `/api/stats/users` | 管理员 | 获取用户统计 |

### 班级管理
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/classes` | 认证 | 获取班级列表 |
| POST | `/api/classes` | 管理员 | 创建班级 |
| PUT | `/api/classes/{id}` | 管理员 | 更新班级 |
| DELETE | `/api/classes/{id}` | 管理员 | 删除班级 |
| GET | `/api/classes/{id}/students` | 认证 | 获取班级学生列表 |
| GET | `/api/classes/{id}/devices` | 认证 | 获取班级绑定设备 |
| POST | `/api/classes/{id}/devices/bind` | 管理员 | 绑定班级与设备 |
| DELETE | `/api/classes/{id}/devices/unbind/{bind_id}` | 管理员 | 解绑班级与设备 |
| GET | `/api/students/{student_id}/device` | 认证 | 获取学生所属班级设备 |

### 实验报告系统 ⭐
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/assignments` | 认证 | 获取实验任务列表 |
| GET | `/api/assignments/{id}` | 认证 | 获取任务详情 |
| POST | `/api/assignments` | 教师/管理员 | 创建实验任务 |
| PUT | `/api/assignments/{id}` | 教师/管理员 | 更新实验任务 |
| DELETE | `/api/assignments/{id}` | 教师/管理员 | 删除实验任务 |
| GET | `/api/assignments/{id}/submissions` | 认证 | 获取提交列表 |
| GET | `/api/assignments/{id}/my-submission` | 认证 | 获取我的提交 |
| POST | `/api/assignments/{id}/submit` | 学生 | 提交实验报告 |
| POST | `/api/assignments/{id}/submit-with-file` | 学生 | 上传文件并提交实验报告 |
| POST | `/api/assignments/{id}/grade` | 教师/管理员 | 批改报告 |

### 植物生长档案 ⭐
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/plants` | 认证 | 获取植物档案列表 |
| GET | `/api/plants/{id}` | 认证 | 获取植物详情 |
| POST | `/api/plants` | 教师/管理员 | 创建植物档案 |
| PUT | `/api/plants/{id}` | 教师/管理员 | 更新植物档案 |
| DELETE | `/api/plants/{id}` | 教师/管理员 | 删除植物档案 |
| GET | `/api/plants/{id}/records` | 认证 | 获取生长记录列表 |
| POST | `/api/plants/{id}/records` | 认证 | 添加生长记录 |
| DELETE | `/api/plants/records/{id}` | 教师/管理员 | 删除生长记录 |

### 小组合作学习 ⭐
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/groups` | 认证 | 获取小组列表 |
| POST | `/api/groups` | 教师/管理员 | 创建小组 |
| GET | `/api/groups/{id}` | 认证 | 获取小组详情 |
| POST | `/api/groups/{id}/members` | 教师/管理员 | 添加小组成员 |
| DELETE | `/api/groups/members/{id}` | 教师/管理员 | 移除小组成员 |

### 操作日志 ⭐
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/logs/operations` | 管理员 | 获取操作日志列表（分页） |
| POST | `/api/logs/operations/export` | 管理员 | 导出操作日志（Excel） |

## 📊 数据库模型

### 核心模型

| 模型 | 表名 | 字段 |
|------|------|------|
| `User` | `users` | id, username, hashed_password, role, email, real_name, avatar_url, student_id, teacher_id, class_id, is_active, created_by, created_at, updated_at |
| `Device` | `devices` | id, device_name, status, last_seen, pump_state, fan_state, light_state, created_at |
| `SensorReading` | `sensor_readings` | id, device_id, temp, humidity, soil_moisture, light, timestamp |

### 教学内容管理模型

| 模型 | 表名 | 字段 |
|------|------|------|
| `ContentCategory` | `content_categories` | id, name, parent_id, description, sort_order, created_at |
| `TeachingContent` | `teaching_contents` | id, title, category_id, content_type, content, video_url, file_path, cover_image, author_id, view_count, is_published, published_at, created_at, updated_at |
| `StudentLearningRecord` | `student_learning_records` | id, student_id, content_id, status, progress_percent, time_spent_seconds, last_accessed, completed_at |
| `ContentComment` | `content_comments` | id, content_id, student_id, parent_id, comment, like_count, teacher_reply, reply_at, created_at |
| `ContentCommentLike` | `content_comment_likes` | id, comment_id, user_id, created_at |
| `UserNotification` | `user_notifications` | id, user_id, actor_id, notification_type, title, content, content_id, comment_id, is_read, created_at |

### 用户管理模型

| 模型 | 表名 | 字段 |
|------|------|------|
| `Class` | `classes` | id, class_name, grade, teacher_id, description, is_active, created_at |
| `ClassDeviceBind` | `class_device_binds` | id, class_id, device_id, created_at |
| `UserOperationLog` | `user_operation_logs` | id, operator_id, operation_type, target_user_id, details, created_at |

### 实验报告系统模型 ⭐

| 模型 | 表名 | 字段 |
|------|------|------|
| `Assignment` | `assignments` | id, title, description, device_id, class_id, teacher_id, start_date, due_date, requirement, template, is_published, created_at |
| `AssignmentSubmission` | `assignment_submissions` | id, assignment_id, student_id, status, experiment_date, observations, conclusion, temp_records, humidity_records, soil_moisture_records, light_records, photos, score, teacher_comment, created_at, updated_at |

### 植物生长档案模型 ⭐

| 模型 | 表名 | 字段 |
|------|------|------|
| `PlantProfile` | `plant_profiles` | id, plant_name, species, class_id, group_id, device_id, plant_date, cover_image, status, expected_harvest_date, description, created_at |
| `GrowthRecord` | `growth_records` | id, plant_id, record_date, stage, height_cm, leaf_count, flower_count, fruit_count, description, photos, recorded_by, created_at |

### 小组合作学习模型 ⭐

| 模型 | 表名 | 字段 |
|------|------|------|
| `StudyGroup` | `study_groups` | id, group_name, class_id, device_id, description, created_at |
| `GroupMember` | `group_members` | id, group_id, student_id, role, joined_at |

## 🔐 权限说明

### 角色权限矩阵

| 角色 | 监控仪表盘 | 远程控制 | 教学内容管理 | 用户管理 | 实验报告 | 植物档案 |
|------|-----------|---------|-------------|---------|---------|---------|
| 学生 | ✅ 只读 | ❌ | ❌ | ❌ | 查看、提交 | 查看、添加记录（小组成员） |
| 教师 | ✅ | ✅ | ✅（自己创建的内容） | ❌ | 创建、批改 | 创建、编辑、删除 |
| 管理员 | ✅ | ✅ | ✅（所有内容） | ✅ | 全权限 | 全权限 |

### 密码强度规则

| 角色 | 要求 |
|------|------|
| 学生 | 至少 6 位 |
| 教师/管理员 | 至少 8 位，包含大小写字母和数字 |

### 用户名规则
- 只能包含字母、数字、下划线
- 长度 3-20 位
- 正则：`^[a-zA-Z0-9_]{3,20}$`

### 站内提醒范围（当前版本）
- 已支持：评论被点赞、评论被回复的站内提醒。
- 暂未启用：邮件通知、短信通知（后续版本扩展）。

## 📝 开发注意事项

### 后端开发
- 数据库连接字符串通过 `DATABASE_URL` 环境变量配置，默认：`mysql+pymysql://greenhouse_user:change_this_password_in_production@localhost:3306/smart_greenhouse`
- JWT 密钥通过 `SECRET_KEY` 环境变量配置（**生产环境必须修改**）
- 新增 API 需添加 `Depends(get_current_user)` 进行认证
- 权限控制使用 `Depends(get_teacher_user)` 或 `Depends(get_admin_user)`
- 使用 Alembic 进行数据库迁移管理

### 前端开发
- API 基础地址：`http://localhost:8000/api`
- Token 存储在 `localStorage`，通过 Axios 拦截器自动注入
- 401 错误自动跳转登录页
- 导出功能使用 `exportTelemetry()` 函数（`src/api/index.ts`）
- 路由权限守卫在 `src/router/index.ts` 中配置
- Markdown 渲染使用 `markdown-it` 库

### 数据导出限制
- 最大日期范围：31 天
- 支持格式：CSV、Excel (XLSX)
- 文件名自动 URL 编码（支持中文）

### JWT 配置
- 算法：HS256
- 有效期：30 分钟
- Token 存储：localStorage

### 数据刷新频率
- 仪表盘：5 秒
- 数据大屏：5 秒

## 🛠️ 常见问题

### 测试账号无法登录
- 执行 `scripts/set_test_passwords.py` 统一测试口令后重试。
- 若是首次部署，优先检查 `init_db.py` 输出的初始化密码。

### 后端启动失败
- 检查 MySQL 服务是否运行
- 验证数据库连接字符串（用户名/密码/端口）
- 确认依赖已安装：`pip install -r requirements.txt`
- 确保 `SECRET_KEY` 环境变量已设置

### 前端构建错误
- 清除缓存：`rm -rf node_modules/.vite` 然后重新 `npm run dev`
- 检查 Node.js 版本（建议 18+）

### 导出功能无数据
- 确保 ESP32 模拟器正在运行并发送数据
- 检查日期范围选择正确

### 控制设备失败
- 确认用户角色为 teacher 或 admin
- 检查设备 ID 是否存在

### 密码强度不足
- 学生密码必须至少 6 位
- 教师/管理员密码必须至少 8 位，包含大小写字母和数字

## 📚 扩展方向

### 已完成功能
1. ✅ 数据导出（CSV/Excel）
2. ✅ 教学内容管理（分类、内容、发布）
3. ✅ 学生学习记录跟踪
4. ✅ 评论/问答系统
5. ✅ 用户管理（CRUD、批量导入、导出、批量操作）
6. ✅ 班级管理
7. ✅ 实验报告系统（任务布置、在线提交、批改评分）⭐
8. ✅ 植物生长档案（档案管理、生长记录跟踪）⭐
9. ✅ 数据大屏展示模式（全屏展示、实时监控）⭐
10. ✅ 小组合作学习（小组管理、成员分配）⭐
11. ✅ 操作日志查看（管理员专用）⭐
12. ✅ 班级与设备绑定功能 ⭐
13. ✅ 分页查询（用户列表、内容列表）⭐
14. ✅ 移动端适配优化（响应式布局）⭐
15. ✅ 个人中心头像与名称编辑（含头像上传）⭐
16. ✅ 评论回复/点赞与站内通知提醒 ⭐

### 待实现功能
1. ⏳ 移动端进一步优化（PWA 支持）
2. ⏳ 数据对比分析工具
3. ⏳ 课堂互动功能（投票、抢答）
4. ⏳ 学生实验数据自动采集

## 🧪 测试脚本

```bash
# 统一默认测试账号密码（admin/teacher/student）
.venv\Scripts\python.exe scripts\set_test_passwords.py

# 运行多角色 API 闭环探测
.venv\Scripts\python.exe scripts\ux_api_probe.py
```

脚本输出会写入 `docs/ux_api_probe_results_2026-03-31.json`，可作为回归与验收证据。

### 性能优化建议
1. 添加数据库索引（部分查询字段）
2. 实现分页查询（用户列表、内容列表）
3. 添加缓存层（Redis）

## 🔐 安全配置

### 生产环境必须修改
1. `SECRET_KEY` - 生成随机密钥（推荐使用 `openssl rand -hex 32`）
2. `DATABASE_URL` - 使用专用数据库用户，限制权限
3. 启用 HTTPS（使用 Nginx 反向代理或 Let's Encrypt）
4. 配置 CORS 白名单（修改 `app/core/config.py` 中的 `cors_origins`）
5. 修改默认账号密码

### 推荐的安全加固
```bash
# 生成随机密钥
openssl rand -hex 32

# 创建专用数据库用户
CREATE USER 'greenhouse'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON smart_greenhouse.* TO 'greenhouse'@'localhost';
```

## 📊 项目统计

| 指标 | 数量 |
|------|------|
| 后端核心文件 | 5 个（main.py + app/模块化目录） |
| 前端页面组件 | 9 个视图组件 |
| 数据库表 | 17 个 |
| API 端点 | 约 90 个 |
| 后端代码行数 | ~3200 行 (main.py) |
| 前端主要依赖 | 8 个 |

## 📦 依赖列表

### 后端依赖 (requirements.txt)
```
fastapi
uvicorn
sqlalchemy
pymysql
pydantic
python-jose[cryptography]
passlib[bcrypt]
python-multipart
cryptography
pandas>=2.0.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
alembic
```

### 前端依赖 (package.json)
```json
{
  "dependencies": {
    "@types/markdown-it": "^14.1.2",
    "axios": "^1.6.0",
    "echarts": "^5.5.0",
    "element-plus": "^2.6.0",
    "lucide-vue-next": "^0.350.0",
    "markdown-it": "^14.1.1",
    "vue": "^3.4.0",
    "vue-router": "^5.0.3"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.2.0",
    "vite": "^5.1.0",
    "vue-tsc": "^1.8.0"
  }
}
```

---

**最后更新**: 2026-04-01  
**项目状态**: 个人中心与评论互动增强已完成（站内提醒已上线，邮件/短信待后续）  
**文档版本**: 3.5

## 🎯 第三阶段修复完成总结

### 修复的问题
1. **实验报告布置功能** ✅
   - 修复 `create_assignment` API 返回格式问题
   - 现在正确返回包含 `teacher_name`, `class_name`, `device_name` 的完整响应

2. **植物档案创建功能** ✅
   - 修复 `create_plant` 和 `update_plant` API 返回格式问题
   - 现在正确返回包含 `class_name`, `device_name`, `group_name`, `growth_record_count` 的完整响应

3. **教学内容发布和删除功能** ✅
   - 发布功能正常工作
   - 删除功能正常工作（教师只能删除自己的内容）

4. **用户管理模块** ✅
   - 添加分页支持
   - 前端适配分页响应格式 `{items: [...], total: ..., page: ..., page_size: ...}`
   - 添加分页组件

### API 修复清单
| API | 修复内容 |
|-----|---------|
| `POST /api/assignments` | 返回完整响应对象（含关联数据） |
| `PUT /api/assignments/{id}` | 返回完整响应对象 |
| `POST /api/plants` | 返回完整响应对象（含关联数据和记录数） |
| `PUT /api/plants/{id}` | 返回完整响应对象 |
| `GET /api/users` | 添加分页支持 |
| `GET /api/content/contents` | 添加分页支持 |
| `GET /api/logs/operations` | 添加分页支持 |

### 前端修复清单
| 页面 | 修复内容 |
|------|---------|
| UserManagement.vue | 适配分页 API，添加分页组件 |
| Assignments.vue | 无需修改（API 已修复） |
| Plants.vue | 无需修改（API 已修复） |
| TeachingContents.vue | 无需修改（API 正常） |

### 访问地址
- **前端界面**: http://localhost:5173
- **实验报告**: http://localhost:5173/assignments
- **植物档案**: http://localhost:5173/plants
- **小组管理**: http://localhost:5173/groups
- **操作日志**: http://localhost:5173/logs（管理员）
- **数据大屏**: http://localhost:5173/display (无需登录)
- **API 文档**: http://localhost:8000/docs

## 2026-03-26 模块增强说明

本次版本在"实验报告"、"植物档案"、"个人中心"三个模块完成以下增强：

### 1. 实验报告模块增强

- 教师/管理员可以对自己布置的任务执行"取消发布"与"重新发布"。
- 学生仅能查看自己所在班级且已发布的实验任务。
- 学生筛选状态（未提交/已提交/已批改）由后端按本人提交记录计算，避免前后端口径不一致。
- 教师查看提交列表时，默认仅能查看自己布置任务的提交（管理员可查看全部）。

### 2. 植物档案模块增强

- 新增植物封面图上传能力（支持 jpg/jpeg/png/webp/gif）。
- 上传后返回静态访问路径，封面可在卡片与详情页展示。
- 学生仅能查看与记录本班级植物档案，不可跨班访问。

### 3. 个人中心模块新增

- 新增"个人中心"页面，支持查看：
   - 基础信息（账号、角色、邮箱、所属班级）
   - 待办统计（待完成任务、逾期任务、待批改、班级植物数）
   - 即将到期任务列表
- 对应后端接口：\GET /api/profile/me\

### 4. 额外修复

- 教学内容发布/取消发布接口增加权限收敛：教师仅可操作自己创建的内容。
- 统一加强了实验报告与植物档案详情接口的班级隔离校验，避免绕过列表直接越权访问。

### 5. 路由与入口

- 仪表盘、实验报告、植物档案页面均新增"个人中心"入口。
- 新增前端路由：\/profile\。
