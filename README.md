# 智慧大棚教具系统 - 项目上下文文档

## 📋 项目概述

**智慧大棚 IoT 系统**是一款面向中小学生科学课设计的物联网教学设备。系统采用完整的全栈架构，实现环境监测、远程控制、权限管理、数据可视化、教学内容和用户管理功能。

## 📚 文档导航（维护入口）

- 项目总览与接口：`README.md`
- 维护操作标准：`docs/MAINTENANCE_GUIDE.md`
- 模块结构说明：`docs/PROJECT_STRUCTURE.md`
- 部署与演示流程：`DEPLOY_AND_DEMO.md`
- 产品打磨记录：`docs/PRODUCT_POLISH_REPORT_2026-04-02.md`

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
- **AI 科学助手**：接入 DeepSeek/Qwen 兼容链路，支持上下文感知、设备状态诊断、角色化科学问答与知识库兜底，并在浮窗中支持 Markdown 富文本渲染（代码高亮、表格、任务列表、KaTeX 公式、Mermaid 图）。
- **AI 多会话管理**：支持“开启新对话”、历史会话切换、重命名与删除；当前会话标题支持单击原地重命名，历史会话标题支持双击原地重命名。会话按用户隔离，流式生成期间前端锁定会话切换以避免上下文错乱。
- **深度思考与智能搜索**：前端支持“深度思考/标准对话”切换；开启智能搜索后会按“相关性 + 来源可信度”筛选候选来源，并仅展示在回答正文中以 `[n]` 编号被引用的链接。
- **天气实时检索优化**：天气类提问（如“某城市现在天气如何”）优先走实时天气检索链路，默认返回带来源编号的实时结果；若暂未获取到实时来源，会自动给出温和兜底回答，不再出现“无法联网”式硬提示。
- **LangChain 编排接入**：问答链路升级为 LangChain 优先，保留原有 Qwen 直连与规则回退，兼顾可演进性与课堂稳定性。
- **RAG 轻量检索**：基于本地 Chroma 向量索引检索已发布教学内容，按问题注入相关知识片段后再生成答案。
- **AI 调用审计**：AI 问答/流式问答/作业点评/内容润色统一写入操作日志，记录来源、耗时、token 用量与回退原因。
- **无 Key 稳定兜底**：当 `QWEN_API_KEY` 未配置或外部接口异常时，自动切换为 rule-based 科学解释，保证课堂演示不中断。
- **设备微孪生 (Digital Twin)**：基于 CSS/Vue 动画实现的温室设备实时状态呈现（风扇转动、水波纹等）。
- **实时数据流**：借助 WebSocket 实现毫秒级数据推送，低延迟同步呈现设备信息。
- **师生双视角闭环**：前端原生支持多角色渲染。学生享有游戏化学习体验；老师拥有专属分析大屏 (`TeachingAnalytics.vue`) 了解学生作业提交率与设备健康度。
- **答辩演示场景模式**：一键下发极端环境场景指令（如“干旱预警”、“极端高温”），应对比赛现场实机演示大屏效果。

## ✅ 2026-04-02 LangChain 融合进展

本轮已完成首批 AI 架构落地（P1 的 1、2 项）：

- 已上线 RAG 索引流程：教学内容创建/更新/发布/删除会触发增量索引同步。
- 已接入问答检索增强：`/api/ai/science-assistant` 与流式接口会自动注入检索上下文。
- 已上线 AI 审计日志：统一记录 source、latency、token（估算）、fallback reason。
- 已开放新增接口：
   - `POST /api/ai/science-assistant/stream`（SSE 流式问答）
   - `POST /api/assignments/{id}/ai-feedback`（作业点评建议）
   - `POST /api/content/ai/polish`（教学内容组织语言）
   - `POST /api/content/ai/reindex`（重建教学内容索引，管理员）

## ✅ 2026-04-02 产品打磨（代码质量 + UX）

本轮围绕“可维护性重构 + 用户体验打磨 + 回归验证”完成如下工作：

- 可维护性优化：
   - 新增前端统一错误处理工具 `frontend/src/utils/error.ts`，将高频 `error.response?.data?.detail` 分支收敛为统一解析。
   - 后端 `app/services/ai_science_service.py` 提炼 AI 问答上下文构建与来源判定逻辑，减少重复代码并统一 source 常量。
   - Qwen 直连调用改为复用配置项 `AI_TEMPERATURE` / `AI_MAX_TOKENS`，降低硬编码参数漂移风险。

- UX 优化：
   - 监控页 AI 面板新增“快捷提问、停止生成、流式光标反馈、来源标签展示”。
   - 教学内容编辑新增“AI 语气偏好”输入与操作提示，并修复“新建内容沿用旧表单”问题。
   - 作业批改页新增 AI 建议来源展示，提升教师判读可解释性。

- 质量验证：
   - 前端：`npx vite build` 通过。
   - 后端：`python -m compileall app main.py` 通过。
   - 静态错误检查：`get_errors` 全量 0 错误。

- 详细记录：`docs/PRODUCT_POLISH_REPORT_2026-04-02.md`

## ✅ 2026-04-13 AI 助手渲染与联网质量优化

本轮围绕“AI 助手可读性 + 联网链接相关性 + 稳定性与性能”完成如下改进：

- AI 助手渲染体验升级：
   - 浮窗消息从纯文本显示升级为 Markdown 富文本显示。
   - 支持代码高亮、表格、任务列表、KaTeX 数学公式、Mermaid 流程图。
   - 保持流式输出稳定：流式阶段以纯文本实时显示，完成后自动渲染富文本。

- 智能联网质量提升：
   - 后端搜索评分由单一相关度升级为“相关性 + 来源可信度”综合排序。
   - 增加权威域名偏好与低质量站点惩罚，收紧低相关结果阈值。
   - 增加“正文引用对齐”机制：仅保留回答中标注 `[n]` 的来源链接。
   - 增加“引用编号归一化”机制：当回答使用非连续编号（如 `[3] [5]`）时，会自动重排为连续编号并与返回链接一一对应，确保会话重载后来源展示一致。
   - 前端来源面板仅展示被正文实际引用的链接，避免链接与答案脱节。

- 稳定性与性能补强：
   - 作业附件上传改为分块写入，避免一次性读取大文件带来的内存峰值风险（仍限制 20MB）。
   - 公开大屏接口修复 0 值传感器数据误判，避免合法零值被错误显示为 `null`。
   - Mermaid/KaTeX 渲染改为按需动态加载，显著降低 AI 浮窗主包体积，改善首屏性能。

- 质量验证：
   - 前端：`npm run build -- --outDir .verify-dist` 通过。
   - 后端：`d:/4C/.venv/Scripts/python.exe -m compileall app main.py` 通过。
   - 静态检查：`get_errors` 全量 0 错误。
   - 新增 AI 回归脚本：`scripts/ai_regression_probe.py`（覆盖 Markdown 输出契约、`[n]` 引用对齐、会话流式回读一致性）。

## ✅ 2026-04-12 角色分层与权限收敛改造（A→D 全量完成）

本轮已完成“后端权限收敛 + 前端角色分发 + 文档落地 + 回归验证”：

- 后端权限与数据基础：
   - 新增所有权字段：`plant_profiles.created_by`、`study_groups.created_by`。
   - 历史数据保持 `created_by = null`，该类数据仅管理员可修改，教师只读。
   - 教师可查看全校 Plants / Groups / Assignments；仅可修改本人创建的数据。
   - 教师可查看全校任务提交与下载报告，但仅可发布/删除/批改本人任务。

- 管理员系统级能力（已落地）：
   - 植物跨班迁移：`POST /api/admin/plants/{plant_id}/migrate`
   - 小组跨班迁移：`POST /api/admin/groups/{group_id}/migrate`
   - 小组成员角色批量修正：`POST /api/admin/groups/{group_id}/members/batch-role`

- 前端角色化页面改造：
   - 路由改为角色分发入口：`Assignments / Plants / Groups` 均由 `index.vue` 负责角色分发。
   - 新增 `Admin / Teacher / Student` 角色壳组件，教师端只读场景在界面明确标识。

- 验证结果：
   - 后端语法检查通过：`python -m compileall app main.py`
   - 前端构建通过：`npm run build`
   - 全量静态错误检查通过：`get_errors` 0 错误

## ✅ 2026-04-12 浮窗 AI 三点菜单层级修复

本轮修复了浮窗 AI 助手历史会话区“三点菜单弹出后被其他记录遮挡”的交互问题：

- 问题现象：点击会话右侧三点按钮后，弹出的操作项会被下方历史记录覆盖，导致“重命名/置顶/删除”点击体验不稳定。
- 修复方案：在 `frontend/src/components/FloatingAIAssistant.vue` 中为“菜单打开态”会话项增加独立层级标记（`is-menu-open`），并提升菜单容器与弹层的层级，确保弹出菜单始终位于历史列表最上层。
- 验证结果：前端构建 `npm run build` 通过，组件静态错误检查为 0。

## ✅ 2026-04-13 前端主题系统二轮打磨（Theme + UX）

本轮完成主题能力与交互细节二次收敛，新增内容如下：

- 主题能力增强：
   - 新增 `system`（跟随系统）模式，与 `prefers-color-scheme` 自动同步。
   - 保留 `light / dark / modern` 三主题，统一由 `frontend/src/composables/useTheme.ts` 管理。
   - 主题偏好持久化到 `localStorage`（键名 `ui.theme.mode`）。

- 视觉与交互增强：
   - 顶部主题切换器支持显示“系统解析后主题状态”。
   - 新增全局路由过渡动画，并对 `prefers-reduced-motion` 做无障碍兼容。
   - 全局样式 token 扩展到图表、卡片、焦点态和动效参数。

- 图表联动增强：
   - 监控页与大屏图表改为 CSS 变量驱动，切换主题后即时刷新配色。
   - 优化大屏主题切换逻辑：改为复用已缓存历史数据重绘图表，避免主题切换触发额外历史接口请求。

- 回归验证：
   - 关键前端文件静态检查通过（`get_errors` 无报错）。
   - 前端构建通过：`npx vite build --outDir .verify-dist`。
   - 构建警告仅剩既有 chunk 体积提示，不影响功能正确性。

## ✅ 2026-04-13 前端第三轮收敛（性能 + 稳定性）

本轮聚焦发布稳定性与运行一致性：

- 构建链路：
   - 优化 Vite 分包策略，保留稳定 vendor 分层（`vue/http/chart/ep/icons`）。
   - 将浮窗 AI 组件改为异步加载，降低首屏主包压力。

- 大屏稳定性：
   - 新增刷新防重入与排队机制，避免定时器导致并发请求叠加。
   - 实时数据与历史趋势改为并行拉取，减少单轮刷新耗时。
   - 补齐图表 resize 与全屏状态同步，提升展示场景一致性。

- 验证结果：
   - 前端构建通过（无循环 chunk 警告）。
   - 相关文件静态检查通过。

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
| **后端** | Python, FastAPI (WebSockets/SSE), SQLAlchemy, PyJWT, Passlib, LangChain, Qwen HTTP, Chroma | Python 3.10+ |
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
│       ├── langchain_service.py      # LangChain 模型编排
│       ├── rag_service.py            # 教学内容向量索引与检索
│       ├── ai_audit_service.py       # AI 调用审计记录
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
         ├── Assignments.vue       # 实验报告共享页（由角色分发器装配）
         ├── Plants.vue            # 植物档案共享页（由角色分发器装配）
         ├── Groups.vue            # 小组共享页（由角色分发器装配）
         ├── Assignments\
         │   ├── index.vue         # 角色分发入口
         │   ├── AdminAssignments.vue
         │   ├── TeacherAssignments.vue
         │   └── StudentAssignments.vue
         ├── Plants\
         │   ├── index.vue         # 角色分发入口
         │   ├── AdminPlants.vue
         │   ├── TeacherPlants.vue
         │   └── StudentPlants.vue
         └── Groups\
            ├── index.vue         # 角色分发入口
            ├── AdminGroups.vue
            ├── TeacherGroups.vue
            └── StudentGroups.vue
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
# 默认监听 0.0.0.0，可通过 localhost / 127.0.0.1 访问

# 3. 模拟 ESP32 数据（可选，新终端）
cd d:\4C
.venv\Scripts\python.exe simulate_esp32.py
```

### 访问地址
- **前端界面**: http://localhost:5173 或 http://127.0.0.1:5173
- **数据大屏**: http://localhost:5173/display 或 http://127.0.0.1:5173/display（无需登录）
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

AI 助手最小回归探测（可选）：
```bash
cd d:\4C
.venv\Scripts\python.exe scripts/ai_regression_probe.py

# 严格模式：要求 Markdown 与 [n] 引用链路都满足
.venv\Scripts\python.exe scripts/ai_regression_probe.py --strict-markdown --strict-citations
```

输出说明：
- 默认输出 `docs/ai_regression_probe_results_latest.json`
- 若环境触发模型兜底（如无外部模型或联网不可用），部分检查会标记为 `warn`

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
| POST | `/api/ai/science-assistant` | 认证 | AI 科学问答（支持 `enable_deep_thinking` / `enable_web_search`，返回模型名与来源链接） |
| POST | `/api/ai/science-assistant/stream` | 认证 | AI 科学流式问答（SSE，`meta` 事件含模型、联网状态与来源链接） |
| GET | `/api/ai/conversations` | 认证 | 获取当前用户会话列表（含预览、消息数） |
| POST | `/api/ai/conversations` | 认证 | 创建新会话（可选标题） |
| GET | `/api/ai/conversations/{conversation_id}` | 认证 | 获取会话详情（含消息列表） |
| PATCH | `/api/ai/conversations/{conversation_id}/title` | 认证 | 重命名会话 |
| DELETE | `/api/ai/conversations/{conversation_id}` | 认证 | 永久删除会话 |
| POST | `/api/ai/conversations/{conversation_id}/science-assistant` | 认证 | 在指定会话中提问（非流式） |
| POST | `/api/ai/conversations/{conversation_id}/science-assistant/stream` | 认证 | 在指定会话中流式提问（SSE） |

AI 问答接口补充说明：
- 请求体新增布尔字段：`enable_deep_thinking`、`enable_web_search`（默认均为 `false`）。
- `enable_deep_thinking=true` 时优先使用 `AI_REASONER_MODEL`（默认 `deepseek-reasoner`）；否则使用 `AI_CHAT_MODEL`（默认 `deepseek-chat`）。
- `enable_web_search=true` 时会尝试联网检索并在响应中返回 `citations`（最多 5 条）；若暂未获取到实时来源，`web_search_notice` 会提示已自动提供通用回答。
- 兼容性说明：原 `/api/ai/science-assistant` 与 `/api/ai/science-assistant/stream` 保持可用；新增 `/api/ai/conversations/*` 用于持久化多会话能力。
- 会话权限说明：仅会话创建者可读取、重命名、删除和继续提问。
- 删除行为说明：会话删除为永久删除，同时清理该会话下全部消息。

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
| POST | `/api/content/ai/polish` | 教师/管理员 | AI 组织教学要点为可发布文本（支持 `target_length` 指定目标篇幅） |
| POST | `/api/content/ai/reindex` | 管理员 | 重建已发布教学内容的向量索引 |
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
| PUT | `/api/assignments/{id}` | 教师/管理员 | 更新实验任务（教师仅可修改本人任务） |
| DELETE | `/api/assignments/{id}` | 教师/管理员 | 删除实验任务（教师仅可删除本人任务） |
| GET | `/api/assignments/{id}/submissions` | 认证 | 获取提交列表 |
| GET | `/api/assignments/{id}/my-submission` | 认证 | 获取我的提交 |
| GET | `/api/assignments/submissions/{submission_id}/file` | 认证 | 下载提交附件（教师可全校只读下载） |
| POST | `/api/assignments/{id}/submit` | 学生 | 提交实验报告 |
| POST | `/api/assignments/{id}/submit-with-file` | 学生 | 上传文件并提交实验报告 |
| POST | `/api/assignments/{id}/grade` | 教师/管理员 | 批改报告（教师仅可批改本人任务） |
| POST | `/api/assignments/{id}/ai-feedback` | 教师/管理员 | 生成 AI 点评建议（教师仅可用于本人任务） |

说明（2026-04-12）：
- 教师读取范围已放开为“全校可见（任务/提交/附件下载）”，写入能力仍保持“仅本人任务可写”。

### 植物生长档案 ⭐
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/plants` | 认证 | 获取植物档案列表 |
| GET | `/api/plants/{id}` | 认证 | 获取植物详情 |
| POST | `/api/plants` | 教师/管理员 | 创建植物档案 |
| PUT | `/api/plants/{id}` | 教师/管理员 | 更新植物档案（教师仅可修改本人创建） |
| DELETE | `/api/plants/{id}` | 教师/管理员 | 删除植物档案（教师仅可删除本人创建） |
| GET | `/api/plants/{id}/records` | 认证 | 获取生长记录列表 |
| POST | `/api/plants/{id}/records` | 认证 | 添加生长记录 |
| DELETE | `/api/plants/records/{id}` | 教师/管理员 | 删除生长记录（教师仅可删除本人创建植物下的记录） |
| POST | `/api/admin/plants/{plant_id}/migrate` | 管理员 | 跨班迁移植物档案 |

### 小组合作学习 ⭐
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/groups` | 认证 | 获取小组列表 |
| POST | `/api/groups` | 教师/管理员 | 创建小组 |
| GET | `/api/groups/{id}` | 认证 | 获取小组详情 |
| PUT | `/api/groups/{id}` | 教师/管理员 | 更新小组（教师仅可修改本人创建） |
| DELETE | `/api/groups/{id}` | 教师/管理员 | 删除小组（教师仅可删除本人创建） |
| POST | `/api/groups/{id}/members` | 教师/管理员 | 添加小组成员（教师仅可管理本人创建小组） |
| PUT | `/api/groups/members/{id}` | 教师/管理员 | 修改成员角色（教师仅可管理本人创建小组） |
| DELETE | `/api/groups/members/{id}` | 教师/管理员 | 移除小组成员（教师仅可管理本人创建小组） |
| POST | `/api/admin/groups/{group_id}/migrate` | 管理员 | 跨班迁移小组 |
| POST | `/api/admin/groups/{group_id}/members/batch-role` | 管理员 | 批量修正成员角色 |

### 操作日志 ⭐
| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/logs/operations` | 管理员 | 获取操作日志列表（分页，含 AI 调用审计） |
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

### AI 会话模型 ⭐

| 模型 | 表名 | 字段 |
|------|------|------|
| `AIConversation` | `ai_conversations` | id, user_id, title, created_at, updated_at, last_message_at |
| `AIConversationMessage` | `ai_conversation_messages` | id, conversation_id, role, content, reasoning, source, model, citations_json, web_search_notice, status, created_at |

### 实验报告系统模型 ⭐

| 模型 | 表名 | 字段 |
|------|------|------|
| `Assignment` | `assignments` | id, title, description, device_id, class_id, teacher_id, start_date, due_date, requirement, template, is_published, created_at |
| `AssignmentSubmission` | `assignment_submissions` | id, assignment_id, student_id, status, experiment_date, observations, conclusion, temp_records, humidity_records, soil_moisture_records, light_records, photos, score, teacher_comment, created_at, updated_at |

### 植物生长档案模型 ⭐

| 模型 | 表名 | 字段 |
|------|------|------|
| `PlantProfile` | `plant_profiles` | id, plant_name, species, class_id, group_id, device_id, plant_date, cover_image, status, expected_harvest_date, description, created_by, created_at |
| `GrowthRecord` | `growth_records` | id, plant_id, record_date, stage, height_cm, leaf_count, flower_count, fruit_count, description, photos, recorded_by, created_at |

### 小组合作学习模型 ⭐

| 模型 | 表名 | 字段 |
|------|------|------|
| `StudyGroup` | `study_groups` | id, group_name, class_id, device_id, description, created_by, created_at |
| `GroupMember` | `group_members` | id, group_id, student_id, role, joined_at |

## 🔐 权限说明

### 角色权限矩阵

| 角色 | 监控仪表盘 | 远程控制 | 教学内容管理 | 用户管理 | 实验报告 | 植物档案 |
|------|-----------|---------|-------------|---------|---------|---------|
| 学生 | ✅ 只读 | ❌ | ❌ | ❌ | 查看、提交 | 查看、添加记录（小组成员） |
| 教师 | ✅ | ✅ | ✅（自己创建的内容） | ❌ | 全校可见、仅本人任务可写 | 全校可见、仅本人创建可写 |
| 管理员 | ✅ | ✅ | ✅（所有内容） | ✅ | 全权限 | 全权限 |

补充说明（2026-04-12）：
- 小组模块与植物模块均引入创建人所有权规则（`created_by`）。
- 教师读取范围为全校可见，写入范围按“本人创建”收敛。
- 管理员具备跨班迁移与批量角色修正能力。

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
- AI 相关环境变量（新增）：
   - `QWEN_API_KEY`：通义 API Key（仅通过环境变量配置，不写入代码）
   - `QWEN_MODEL`：兼容模型名（默认 `deepseek-chat`，可被 DeepSeek 配置覆盖）
   - `QWEN_BASE_URL`：通义 OpenAI 兼容接口地址
   - `AI_CHAT_MODEL`：普通问答模型（默认 `deepseek-chat`）
   - `AI_REASONER_MODEL`：深度思考模型（默认 `deepseek-reasoner`）
   - `AI_LANGCHAIN_ENABLED`：是否启用 LangChain 编排
   - `AI_STREAM_ENABLED`：是否启用流式问答
   - `AI_TIMEOUT_SECONDS`：模型调用超时秒数
   - `AI_STREAM_TIMEOUT_SECONDS`：流式问答超时秒数
   - `AI_RETRY_COUNT`：模型调用重试次数（仅网络/限流等可重试错误）
   - `AI_RETRY_BACKOFF_MS`：重试退避毫秒数
   - `AI_TEMPERATURE`：模型温度
   - `AI_MAX_TOKENS`：生成 token 上限
   - `RAG_ENABLED`：是否启用教学内容检索增强
   - `RAG_INDEX_DIR`：本地向量索引目录
   - `RAG_TOP_K`：检索片段数量

### 前端开发
- API 基础地址：优先读取 `VITE_API_BASE_URL`，未配置时自动按当前域名推导
- 网络异常时前端会自动在 `localhost:8000` 与 `127.0.0.1:8000` 之间回退重试（普通请求与 AI 流式请求均支持）
- 若前端运行在局域网 IP 或非默认端口，请同步配置后端 `CORS_ORIGINS` / `CORS_ORIGIN_REGEX`
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

### 浏览器打不开前端页面
- 先确认前端进程正常启动：`cd d:\4C\frontend && npm run dev`
- 使用 `http://localhost:5173` 或 `http://127.0.0.1:5173` 访问
- 若你在同网段其他设备访问，使用本机局域网 IP：`http://<你的IP>:5173`
- 若端口被占用，先释放 5173 端口再重启前端

### AI 助手提示“初始化会话失败：Network Error”
- 先确认后端已启动并监听 8000：`cd d:\4C && .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000`
- 直接访问 `http://localhost:8000/docs` 验证后端可达
- 前端建议使用 `http://localhost:5173` 或 `http://127.0.0.1:5173`
- 若你使用自定义域名或反向代理，请配置 `VITE_API_BASE_URL`
- 后端默认放行 `localhost/127.0.0.1` 的 `5173/4173/3000` 端口及局域网私有网段来源；若仍报错，请显式设置 CORS：

```bash
# Windows CMD 示例
set CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.1.10:5173
set CORS_ORIGIN_REGEX=^https?://(localhost|127\.0\.0\.1|192\.168(?:\.\d{1,3}){2})(:\d+)?$
```

- 新版本前端会在 `localhost:8000` 与 `127.0.0.1:8000` 间自动回退重试（含 AI 流式请求）

### AI 助手提示“创建会话失败（404/500/503）”
- 先执行迁移，确保会话表存在：`cd d:\4C && .venv\Scripts\python.exe -m alembic upgrade head`
- 若浏览器 Network 中请求 URL 为 `http://localhost:5173/api/...` 或 `http://127.0.0.1:5173/api/...`，说明前端误请求到了自身端口，请刷新前端并重启后端后重试
- 若会话列表里出现大量“新对话/暂无消息”，可执行安全清理脚本：`cd d:\4C && .venv\Scripts\python.exe -m scripts.cleanup_empty_records`

### AI 助手查询天气仍未返回实时结果
- 确认提问包含城市信息（例如：`北京现在天气怎么样`）。
- 确认智能搜索开关已开启。
- 若返回“暂未获取到实时来源，已自动提供通用回答”，通常是当前环境外网受限；可稍后重试或更换网络。

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
4. 配置 CORS 白名单/正则（`CORS_ORIGINS` 或 `CORS_ORIGIN_REGEX`）
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

**最后更新**: 2026-04-13  
**项目状态**: 主题系统二轮打磨已完成（四模式主题、图表联动与页面转场已上线）  
**文档版本**: 3.7

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
- **前端界面**: http://localhost:5173 或 http://127.0.0.1:5173
- **实验报告**: http://localhost:5173/assignments
- **植物档案**: http://localhost:5173/plants
- **小组管理**: http://localhost:5173/groups
- **操作日志**: http://localhost:5173/logs（管理员）
- **数据大屏**: http://localhost:5173/display 或 http://127.0.0.1:5173/display (无需登录)
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
