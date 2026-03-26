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
- **评论/问答系统**：学生提问，教师回复
- **学习统计**：教师可查看班级学习进度和完成率

#### 实验报告系统（新增）⭐
- **实验任务管理**：教师可布置实验任务，设置截止时间
- **在线提交报告**：学生可在线提交实验报告，记录观察数据
- **批改评分**：教师可在线批改报告，给出分数和评语
- **实验数据关联**：自动关联传感器历史数据

#### 植物生长档案（新增）⭐
- **植物档案管理**：为每株植物建立独立档案
- **生长记录跟踪**：记录植物各阶段生长数据（高度、叶片数、花朵数等）
- **生长阶段标记**：种子→发芽→幼苗→开花→结果→收获
- **时间轴展示**：以时间轴形式展示植物生长历程

#### 数据大屏展示（新增）⭐
- **全屏展示模式**：支持 F11 全屏，适合公开课展示
- **实时数据展示**：温度、湿度、土壤湿度、光照强度
- **设备状态监控**：水泵、风扇、植物灯状态
- **生长记录时间轴**：最近植物生长记录

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
                                   ▲
                                   │ HTTP/REST
                                   ▼
                            ┌─────────────┐
                            │  Vue 3 + TS │
                            │  (前端)     │
                            └─────────────┘
```

### 技术栈详情

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端** | Python, FastAPI, SQLAlchemy, PyJWT, Passlib | Python 3.10+ |
| **前端** | Vue 3, TypeScript, Vite, Element Plus, ECharts, Lucide Icons | Node.js 18+ |
| **数据库** | MySQL | 8.0+ |
| **硬件** | ESP32, ArduinoJson | - |
| **数据处理** | Pandas, OpenPyXL | Pandas 2.0+ |

## 📁 目录结构

```
d:\4C\
├── main.py                    # FastAPI 后端核心（API、权限、数据库模型）
├── requirements.txt           # Python 依赖
├── init_db.sql               # 数据库初始化脚本（已废弃，使用 SQLAlchemy 自动创建）
├── simulate_esp32.py         # ESP32 模拟器（无硬件时使用）
├── esp32_telemetry.ino       # ESP32 真实硬件代码（Arduino C++）
│
├── clear_contents.py         # 清空教学内容脚本
├── init_sample_contents.py   # 初始化示例教学内容脚本
├── migrate_users.py          # 用户数据迁移脚本
├── reset_admin_password.py   # 重置管理员密码脚本
│
└── frontend\                  # Vue 3 前端项目
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    └── src\
        ├── main.ts           # 入口文件
        ├── App.vue
        ├── api\index.ts      # API 封装（含 JWT 拦截器、导出功能）
        ├── router\index.ts   # 路由配置（含权限守卫）
        ├── components\
        │   ├── Dashboard.vue # 主仪表盘（含导出对话框、设备选择）
        │   └── TelemetryChart.vue  # ECharts 图表组件
        └── views\
            ├── Login.vue     # 登录页面
            ├── TeachingContents.vue  # 教学内容浏览页面
            └── UserManagement.vue    # 用户管理页面（仅管理员）
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
- **API 文档**: http://localhost:8000/docs
- **数据库**: `smart_greenhouse` (MySQL)

### 默认账号
| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | `admin` | `admin` | 全权限 |
| 教师 | `teacher` | `admin` | 查看 + 控制 + 教学内容管理 |
| 学生 | `student` | `admin` | 仅查看 |

## 🔌 核心 API 接口

### 认证
- `POST /token` - 登录获取 JWT Token

### 设备与传感器
- `GET /api/devices` - 获取设备列表（需认证）
- `POST /api/devices` - 创建设备（仅管理员）
- `GET /api/history/{device_id}` - 获取历史数据（最近 20 条）
- `POST /api/telemetry` - ESP32 上报数据
- `POST /api/control/{device_id}` - 远程控制设备（教师/管理员）
- `POST /api/telemetry/export` - 导出传感器数据（CSV/Excel，最多 31 天）

### 教学内容管理
- `GET /api/content/categories` - 获取分类列表
- `GET /api/content/categories/tree` - 获取分类树形结构
- `POST /api/content/categories` - 创建分类（教师/管理员）
- `PUT /api/content/categories/{id}` - 更新分类（教师/管理员）
- `DELETE /api/content/categories/{id}` - 删除分类（仅管理员）

- `GET /api/content/contents` - 获取内容列表（支持筛选、搜索）
- `GET /api/content/contents/{id}` - 获取内容详情
- `POST /api/content/contents` - 创建内容（教师/管理员）
- `PUT /api/content/contents/{id}` - 更新内容（教师/管理员）
- `DELETE /api/content/contents/{id}` - 删除内容（教师/管理员）
- `POST /api/content/contents/{id}/publish` - 发布/取消发布内容

### 学习记录
- `GET /api/content/my-learning` - 获取我的学习记录（学生）
- `POST /api/content/contents/{id}/start` - 开始学习
- `POST /api/content/contents/{id}/complete` - 完成学习
- `PUT /api/content/contents/{id}/progress` - 更新学习进度

### 评论/问答
- `GET /api/content/contents/{id}/comments` - 获取评论列表
- `POST /api/content/contents/{id}/comments` - 添加评论（学生）
- `PUT /api/content/comments/{id}` - 回复评论（教师/管理员）

### 学习统计（教师端）
- `GET /api/content/stats/overview` - 获取学习统计概览
- `GET /api/content/stats/students` - 获取所有学生学习进度
- `GET /api/content/stats/content/{id}` - 获取特定内容学习统计

### 用户管理（管理员）
- `GET /api/users` - 获取用户列表（支持搜索、筛选）
- `GET /api/users/{id}` - 获取用户详情
- `POST /api/users` - 创建用户
- `PUT /api/users/{id}` - 更新用户
- `DELETE /api/users/{id}` - 删除用户
- `POST /api/users/{id}/reset-password` - 重置密码
- `POST /api/users/{id}/toggle-active` - 启用/禁用账号
- `POST /api/users/batch-create` - 批量创建用户
- `POST /api/users/import` - Excel 导入用户
- `GET /api/users/export` - 导出用户列表（CSV）
- `GET /api/stats/users` - 获取用户统计

### 班级管理
- `GET /api/classes` - 获取班级列表
- `POST /api/classes` - 创建班级（管理员）
- `PUT /api/classes/{id}` - 更新班级（管理员）
- `DELETE /api/classes/{id}` - 删除班级（管理员）

### 实验报告系统（新增）
- `GET /api/assignments` - 获取实验任务列表
- `GET /api/assignments/{id}` - 获取任务详情
- `POST /api/assignments` - 创建实验任务（教师）
- `PUT /api/assignments/{id}` - 更新实验任务（教师）
- `DELETE /api/assignments/{id}` - 删除实验任务（教师）
- `GET /api/assignments/{id}/submissions` - 获取提交列表
- `GET /api/assignments/{id}/my-submission` - 获取我的提交
- `POST /api/assignments/{id}/submit` - 提交实验报告（学生）
- `POST /api/assignments/{id}/grade` - 批改报告（教师）

### 植物生长档案（新增）
- `GET /api/plants` - 获取植物档案列表
- `GET /api/plants/{id}` - 获取植物详情
- `POST /api/plants` - 创建植物档案（教师）
- `PUT /api/plants/{id}` - 更新植物档案（教师）
- `DELETE /api/plants/{id}` - 删除植物档案（教师）
- `GET /api/plants/{id}/records` - 获取生长记录
- `POST /api/plants/{id}/records` - 添加生长记录

### 小组合作学习（新增）
- `GET /api/groups` - 获取小组列表
- `POST /api/groups` - 创建小组（教师）
- `POST /api/groups/{id}/members` - 添加小组成员
- `DELETE /api/groups/members/{id}` - 移除小组成员

## 📊 数据库模型

### 核心模型

| 模型 | 表名 | 说明 |
|------|------|------|
| `User` | `users` | 用户表（id, username, hashed_password, role, email, real_name, student_id, teacher_id, class_id, is_active） |
| `Device` | `devices` | 设备表（id, device_name, status, last_seen, pump_state, fan_state, light_state） |
| `SensorReading` | `sensor_readings` | 传感器数据表（id, device_id, temp, humidity, soil_moisture, light, timestamp） |

### 教学内容模型

| 模型 | 表名 | 说明 |
|------|------|------|
| `ContentCategory` | `content_categories` | 内容分类表（id, name, parent_id, description, sort_order） |
| `TeachingContent` | `teaching_contents` | 教学内容表（id, title, category_id, content_type, content, video_url, file_path, author_id, view_count, is_published） |
| `StudentLearningRecord` | `student_learning_records` | 学生学习记录表（id, student_id, content_id, status, progress_percent, time_spent_seconds, completed_at） |
| `ContentComment` | `content_comments` | 评论/问答表（id, content_id, student_id, comment, teacher_reply, reply_at） |

### 用户管理模型

| 模型 | 表名 | 说明 |
|------|------|------|
| `Class` | `classes` | 班级表（id, class_name, grade, teacher_id, description, is_active） |
| `UserOperationLog` | `user_operation_logs` | 操作日志表（id, operator_id, operation_type, target_user_id, details） |

### 实验报告系统模型（新增）

| 模型 | 表名 | 说明 |
|------|------|------|
| `Assignment` | `assignments` | 实验任务表（id, title, description, device_id, class_id, teacher_id, start_date, due_date, requirement, template, is_published） |
| `AssignmentSubmission` | `assignment_submissions` | 实验报告提交表（id, assignment_id, student_id, status, experiment_date, observations, conclusion, temp_records, humidity_records, soil_moisture_records, light_records, photos, score, teacher_comment） |

### 植物生长档案模型（新增）

| 模型 | 表名 | 说明 |
|------|------|------|
| `PlantProfile` | `plant_profiles` | 植物档案表（id, plant_name, species, class_id, group_id, device_id, plant_date, cover_image, status, expected_harvest_date, description） |
| `GrowthRecord` | `growth_records` | 生长记录表（id, plant_id, record_date, stage, height_cm, leaf_count, flower_count, fruit_count, description, photos, recorded_by） |

### 小组合作学习模型（新增）

| 模型 | 表名 | 说明 |
|------|------|------|
| `StudyGroup` | `study_groups` | 学习小组表（id, group_name, class_id, device_id, description） |
| `GroupMember` | `group_members` | 小组成员表（id, group_id, student_id, role） |

## 📝 开发注意事项

### 后端开发
- 数据库连接字符串通过 `DATABASE_URL` 环境变量配置，默认：`mysql+pymysql://root:222710@localhost:3306/smart_greenhouse`
- JWT 密钥通过 `SECRET_KEY` 环境变量配置
- 新增 API 需添加 `Depends(get_current_user)` 进行认证
- 权限控制使用 `Depends(get_teacher_user)` 或 `Depends(get_admin_user)`
- 密码验证规则：至少 8 位，包含大小写字母和数字
- 用户名规则：只能包含字母、数字、下划线，长度 3-20 位

### 前端开发
- API 基础地址：`http://localhost:8000/api`
- Token 存储在 `localStorage`，通过 Axios 拦截器自动注入
- 401 错误自动跳转登录页
- 导出功能使用 `exportTelemetry()` 函数（`src/api/index.ts`）
- 路由权限守卫在 `src/router/index.ts` 中配置

### 权限说明

| 角色 | 监控仪表盘 | 远程控制 | 教学内容管理 | 用户管理 |
|------|-----------|---------|-------------|---------|
| 学生 | ✅ 只读 | ❌ | ❌ | ❌ |
| 教师 | ✅ | ✅ | ✅（自己创建的内容） | ❌ |
| 管理员 | ✅ | ✅ | ✅（所有内容） | ✅ |

## 🛠️ 常见问题

### 后端启动失败
- 检查 MySQL 服务是否运行
- 验证数据库连接字符串（用户名/密码/端口）
- 确认依赖已安装：`pip install -r requirements.txt`

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
- 密码必须至少 8 位
- 必须包含大写字母、小写字母和数字

## 📚 扩展方向

### 🤖 AI 应用扩展（推荐使用 Dify）

- **适用场景**：课堂助教（Q&A）、实验报告润色/批改建议、传感器数据趋势解读、教学内容快速检索、植物养护建议。
- **推荐方案**：自托管一套 Dify，作为 LLM 编排与知识库平台；FastAPI 作为“中间层”封装 Dify 的对话/工作流接口，前端通过现有 `frontend/src/api` 客户端调用。
- **接入步骤**
  1. **部署 Dify**：按照官方 `docker-compose` 一键部署（内网即可），配置模型供应商（如通义千问、OpenAI、Azure OpenAI 等）与向量库。
  2. **准备知识库**：将“教学内容、实验任务说明、历史实验报告示例、传感器导出数据摘要”整理为 Markdown/CSV 上传到 Dify Dataset；或在 Dify Workflow 中使用 **HTTP 请求节点** 调用现有 FastAPI 接口（如 `/api/assignments`、`/api/history/{device_id}`）实时取数。
  3. **设计应用/流程**：在 Dify 创建 Chatflow/Workflow，增加工具节点：
     - **检索工具**：连接 Dataset 做语义检索。
     - **实时数据工具**：HTTP 节点调用本项目 API 获取当前设备/植物数据。
     - **角色/权限上下文**：把用户角色、班级、设备 ID 作为 workflow 输入，限制回答范围。
  4. **后端封装**：在 FastAPI 新增轻量接口（示例命名：`POST /api/ai/chat` 或 `/api/ai/report-review`），读取 `DIFY_API_BASE_URL`、`DIFY_API_KEY` 环境变量，转发到 Dify 的 Completion/Workflow API，并透传用户上下文；建议使用 SSE/流式转发提升体验。
  5. **前端调用**：复用现有 axios 客户端，在 `frontend/src/api` 中新增对应方法，支持流式输出；UI 可沿用评论/问答或报告详情的交互布局。
- **安全与运维**：对转发接口开启鉴权与频控；不要在前端暴露 Dify Key；开启审计日志，避免模型误用；为 Dify 服务和本项目设置独立网络与环境变量。
- **如果不使用 Dify**：可用 LangChain/FastAPI 直接对接模型，但需要自行处理对话状态、工具调用和向量检索，开发与运维成本更高，故优先推荐 Dify。

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

### 规划中功能
1. ⏳ 班级与设备绑定（学生只能查看本班设备）
2. ⏳ 移动端适配优化
3. ⏳ 数据对比分析工具
4. ⏳ 课堂互动功能（投票、抢答）

### 数据库扩展建议
```sql
-- 学生 - 设备关联表（待实现）
CREATE TABLE class_device_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    class_id INT NOT NULL,
    device_id INT NOT NULL,
    student_id INT NOT NULL,
    FOREIGN KEY (class_id) REFERENCES classes(id),
    FOREIGN KEY (device_id) REFERENCES devices(id),
    FOREIGN KEY (student_id) REFERENCES users(id)
);

-- 作业表（待实现）
CREATE TABLE assignments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    class_id INT,
    title VARCHAR(200),
    description TEXT,
    due_date TIMESTAMP,
    created_by INT,
    FOREIGN KEY (class_id) REFERENCES classes(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

## 🔐 安全配置

### 生产环境必须修改
1. `SECRET_KEY` - 生成随机密钥（推荐使用 `openssl rand -hex 32`）
2. `DATABASE_URL` - 使用专用数据库用户，限制权限
3. 启用 HTTPS（使用 Nginx 反向代理或 Let's Encrypt）
4. 配置 CORS 白名单（修改 `main.py` 中的 `allow_origins`）
5. 修改默认账号密码

### 推荐的安全加固
```bash
# 生成随机密钥
openssl rand -hex 32

# 创建专用数据库用户
CREATE USER 'greenhouse'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON smart_greenhouse.* TO 'greenhouse'@'localhost';
```

---

**最后更新**: 2026-03-25
**项目状态**: 第一阶段优化完成（物联网监控 + 教学管理 + 用户管理 + 实验报告 + 植物档案 + 数据大屏）
**文档版本**: 3.0

## 🎯 第一阶段优化完成总结

### 新增功能
1. **实验报告系统**
   - 教师可布置实验任务，设置截止时间
   - 学生在线提交实验报告，自动关联传感器数据
   - 教师在线批改，给出分数和评语

2. **植物生长档案**
   - 为每株植物建立独立档案
   - 记录生长各阶段数据（高度、叶片数、花朵数、果实数）
   - 时间轴形式展示生长历程

3. **数据大屏展示**
   - 全屏展示模式，适合公开课
   - 实时显示传感器数据
   - 设备状态监控
   - 最近生长记录时间轴

4. **小组合作学习**
   - 创建学习小组
   - 分配角色（组长、记录员、操作员、汇报员）
   - 小组负责设备和植物

### 访问地址
- **前端界面**: http://localhost:5173
- **实验报告**: http://localhost:5173/assignments
- **植物档案**: http://localhost:5173/plants
- **数据大屏**: http://localhost:8000/display (无需登录)
- **API 文档**: http://localhost:8000/docs
