# 部署与演示指南

## 1. Docker 一键部署（推荐生产环境）

### 1.1 环境准备

- Docker 20.10+
- Docker Compose 2.0+

### 1.2 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# 必须修改
SECRET_KEY=<openssl rand -hex 32 生成的密钥>

# 数据库（docker-compose 已内置 MySQL，通常无需修改）
# DATABASE_URL=mysql+pymysql://greenhouse_user:greenhouse_password@db:3306/smart_greenhouse

# AI 助手（推荐配置）
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# CORS（按实际域名修改）
CORS_ORIGINS=http://yourdomain.com,http://localhost:5173

# 演示数据（首次部署建议开启）
SEED_DEMO_DATA=true
DEMO_ADMIN_PASSWORD=your_secure_admin_pw
DEMO_TEACHER_PASSWORD=your_secure_teacher_pw
DEMO_STUDENT_PASSWORD=your_secure_student_pw
```

### 1.3 构建与启动

```bash
docker-compose up -d --build
```

### 1.4 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:80 |
| 后端 API 文档 | http://localhost:8000/docs |
| 数据大屏 | http://localhost:80/display |

### 1.5 容器管理

```bash
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启服务
docker-compose restart backend
docker-compose restart frontend

# 停止全部
docker-compose down

# 停止并清除数据卷
docker-compose down -v
```

### 1.6 Docker Compose 服务说明

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| `db` | mysql:8.0 | 3306（内部） | 数据库，数据持久化到 `db_data` 卷 |
| `backend` | 自建 (Python 3.11) | 8000（内部） | FastAPI 后端 |
| `frontend` | 自建 (Node 20 + Nginx) | 80（对外） | Vue 前端静态站点 |

### 1.7 数据持久化

Docker 部署的数据持久化通过卷挂载实现：

| 挂载 | 说明 |
|------|------|
| `db_data` | MySQL 数据目录 |
| `./data` | Chroma 向量索引 |
| `./uploads` | 上传文件（头像/附件/图片） |

---

## 2. 本地开发部署

### 2.1 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 2.2 数据库准备

```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE smart_greenhouse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户（推荐）
CREATE USER 'greenhouse_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON smart_greenhouse.* TO 'greenhouse_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2.3 后端配置

```bash
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 DATABASE_URL、SECRET_KEY 等

# 初始化数据库
python init_db.py

# 执行迁移（版本升级时）
python -m alembic upgrade head
```

### 2.4 前端配置

```bash
cd frontend
npm install

# 可选：配置 API 基址
# 在 .env.local 中设置 VITE_API_BASE_URL=http://localhost:8000/api
```

### 2.5 启动服务

```bash
# 后端（端口 8000）
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 前端（端口 5173，新终端）
cd frontend
npm run dev

# ESP32 模拟器（可选，新终端）
python simulate_esp32.py
```

### 2.6 访问地址

| 入口 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173 |
| 数据大屏 | http://localhost:5173/display（无需登录） |
| API 文档 | http://localhost:8000/docs |
| 用户注册 | http://localhost:5173/register |

---

## 3. 生产环境部署

### 3.1 Nginx 反向代理配置

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # 前端静态文件
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端认证端点
    location /token {
        proxy_pass http://127.0.0.1:8000/token;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # 上传文件
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
        proxy_set_header Host $host;
        client_max_body_size 20M;
    }

    # API 文档（可选：生产环境关闭）
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
}
```

### 3.2 Systemd 服务配置（Linux）

后端服务 `/etc/systemd/system/greenhouse-backend.service`：

```ini
[Unit]
Description=Greenhouse Backend API
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/4C
EnvironmentFile=/opt/4C/.env
ExecStart=/opt/4C/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3.3 安全检查清单

- [ ] `SECRET_KEY` 已更换为随机强密钥
- [ ] `DATABASE_URL` 使用专用数据库用户，强密码
- [ ] `DEVICE_TOKEN` 已更换为安全随机值
- [ ] `CORS_ORIGINS` 已限制为实际域名
- [ ] 默认账号密码已修改
- [ ] HTTPS 已启用（Let's Encrypt 或其他证书）
- [ ] `SEED_DEMO_DATA=false`（生产环境关闭演示数据）
- [ ] API 文档端点已限制访问（可选）
- [ ] 防火墙仅开放 80/443 端口
- [ ] MySQL 仅监听 localhost

---

## 4. 答辩演示流程

### 4.1 演示前准备（5 分钟）

1. 启动全部服务（后端 + 前端 + ESP32 模拟器）
2. 确认数据大屏可正常访问
3. 准备三个角色账号（管理员/教师/学生）
4. 确认 AI 助手可用（`DEEPSEEK_API_KEY` 已配置）

```bash
# 快速准备
python scripts/set_test_passwords.py
python simulate_esp32.py &
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
cd frontend && npm run dev &
```

### 4.2 推荐演示路线（3-5 分钟）

**第一站：教师监控页面（1 分钟）**
1. 登录教师账号 → 进入环境监控页面
2. 展示实时数据刷新（5 秒周期）
3. 通过"远程控制"切换水泵/风扇/植物灯与强度
4. 观察微孪生状态变化（风扇转动、水波纹、灯光）

**第二站：AI 科学助手（1 分钟）**
1. 在监控页 AI 面板提问："为什么干旱时叶片容易下垂？"
2. 展示流式输出与 Markdown 富文本渲染
3. 开启"深度思考"模式再次提问
4. 开启"智能搜索"提问天气："北京现在天气怎么样？"

**第三站：教学分析（1 分钟）**
1. 进入教学分析页面
2. 展示任务提交率、平均分
3. 展示设备环境稳定度

**第四站：数据大屏（1 分钟）**
1. 访问 `/display`（无需登录）
2. F11 全屏展示
3. 展示实时数据 + 设备状态 + 生长记录时间轴

**第五站（可选）：学生视角**
1. 切换学生账号
2. 展示实验报告提交
3. 展示植物生长记录添加

### 4.3 演示注意事项

- ESP32 模拟器必须持续运行，否则监控页无实时数据
- AI 助手依赖 DeepSeek API，确保网络可达
- 大屏页面无需登录，可直接全屏展示
- 若演示环境无外网，AI 联网检索功能不可用，但基础问答仍可工作（rule-based fallback）

---

## 5. CI 流程

项目已配置 GitHub Actions（`.github/workflows/ci.yml`）：

| 阶段 | 检查内容 |
|------|----------|
| backend-check | Python 3.11 依赖安装 + `main.py` 语法检查 |
| frontend-build | Node 20 依赖安装 + `npm run build` |

触发条件：`main`/`master` 分支的 push 和 PR。

---

## 6. 数据备份与恢复

### 6.1 数据库备份

```bash
# Docker 环境
docker exec greenhouse-db mysqldump -u root -proot_password smart_greenhouse > backup_$(date +%Y%m%d).sql

# 本地环境
mysqldump -u greenhouse_user -p smart_greenhouse > backup_$(date +%Y%m%d).sql
```

### 6.2 数据库恢复

```bash
# Docker 环境
docker exec -i greenhouse-db mysql -u root -proot_password smart_greenhouse < backup_20260421.sql

# 本地环境
mysql -u greenhouse_user -p smart_greenhouse < backup_20260421.sql
```

### 6.3 上传文件备份

```bash
# uploads 目录包含头像、附件、图片等
tar czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

### 6.4 RAG 索引备份

```bash
# Chroma 向量索引
tar czf chroma_backup_$(date +%Y%m%d).tar.gz data/chroma/
```

---

## 7. 版本升级流程

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 备份数据库
mysqldump -u greenhouse_user -p smart_greenhouse > backup_before_upgrade.sql

# 3. 执行数据库迁移
python -m alembic upgrade head

# 4. 更新后端依赖
pip install -r requirements.txt

# 5. 更新前端依赖并构建
cd frontend
npm install
npm run build

# 6. 重启服务
# Docker: docker-compose up -d --build
# 本地: 重启 uvicorn 进程

# 7. 验证
python scripts/ux_api_probe.py
python scripts/stability_regression_probe.py
```

---

## 8. 常见部署问题

### 前端容器构建失败（npm 超时）

Dockerfile 已配置 npmmirror 镜像源和重试策略。若仍超时，可手动构建：

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run build
```

### MySQL 容器启动失败

- 检查 `db_data` 卷权限
- 检查内存是否充足（MySQL 8.0 建议至少 512MB）
- 查看日志：`docker-compose logs db`

### 后端容器无法连接数据库

- 确认 `db` 服务已启动：`docker-compose ps db`
- 确认 `DATABASE_URL` 中主机名为 `db`（Docker 内部网络）
- 等待 MySQL 初始化完成（首次启动约 30 秒）

### 前端无法访问后端 API

- 检查 Nginx 配置中 `proxy_pass` 是否正确
- 检查后端 CORS 配置是否放行前端域名
- 检查 `VITE_API_BASE_URL` 是否正确

---

**最后更新**: 2026-04-21
