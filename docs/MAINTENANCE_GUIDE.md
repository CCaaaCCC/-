# 项目维护手册

## 1. 目的与范围

本手册用于降低项目交接成本，统一日常维护、升级发布、故障排查与回归验证流程。

适用范围：
- 后端 FastAPI 与数据库迁移维护
- 前端 Vue 构建与页面回归
- AI 能力（问答、润色、点评、联网检索）稳定性维护
- Docker 部署环境维护
- 线上/演示环境快速排障

## 2. 维护入口总览

核心文档：
- [README.md](../README.md)：项目总览、接口清单、运行方式
- [docs/PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)：模块结构与设计说明
- [DEPLOY_AND_DEMO.md](../DEPLOY_AND_DEMO.md)：部署与演示流程
- [CHANGES.md](../CHANGES.md)：版本变更记录
- 本文档：维护操作标准

常用目录：
- `app/api/routes/`：后端路由入口
- `app/services/`：核心业务逻辑（AI、小组、历史、植物、通知）
- `app/schemas/`：接口数据模型
- `app/core/`：配置、安全、权限、校验
- `frontend/src/views/`：页面业务逻辑
- `frontend/src/api/`：前端 API 封装与类型
- `frontend/src/composables/`：复用逻辑
- `alembic/versions/`：数据库迁移脚本
- `scripts/`：工具与回归脚本

## 3. 日常维护流程

### 3.1 本地启动

后端（项目根目录）：
```powershell
.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

前端（frontend 目录）：
```powershell
cd frontend
npm install
npm run dev
```

### 3.2 每次改动后的最小验证

后端语法检查：
```powershell
python -m compileall app main.py
```

前端构建检查：
```powershell
cd frontend
npm run build
```

接口回归探测（可选但推荐）：
```powershell
python scripts/ux_api_probe.py
```

稳定性专项探测（分页边界/登录限流/作业分页兼容）：
```powershell
python scripts/stability_regression_probe.py
```

AI 助手回归探测（涉及 AI 渲染/联网引用/会话流式改动时推荐）：
```powershell
python scripts/ai_regression_probe.py

# 严格模式
python scripts/ai_regression_probe.py --strict-markdown --strict-citations
```

## 4. 数据库迁移维护

### 4.1 升级数据库

```powershell
python -m alembic upgrade head
```

### 4.2 新建迁移

```powershell
python -m alembic revision -m "your_migration_name"
```

### 4.3 迁移注意事项

- 优先使用增量迁移，不要直接修改历史迁移文件
- 涉及线上字段变更时，先做向后兼容（可空字段、默认值）
- 迁移后必须执行一次关键页面冒烟（登录、教学内容、作业、AI）
- 当前迁移版本 head: `0010_device_camera_support`
- 迁移脚本位于 `alembic/versions/`，共 10 个版本

### 4.4 迁移版本历史

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
| 0009 | 设备执行器级别 |
| 0010 | 设备摄像头支持（has_camera） |

## 5. AI 模块维护要点

### 5.1 关键文件

| 文件 | 职责 |
|------|------|
| `app/services/ai_science_service.py` | 问答/润色/点评编排、联网检索、天气查询、引用对齐 |
| `app/services/langchain_service.py` | LangChain 模型调用、提示词、大棚意图识别、标题生成 |
| `app/services/rag_service.py` | 教学内容向量索引与检索 |
| `app/services/ai_audit_service.py` | AI 调用审计日志 |
| `app/api/routes/telemetry.py` | AI 会话 CRUD 与问答/流式接口 |

### 5.2 维护原则

- 保留兜底链路：模型失败时仍可返回可用内容（rule-based fallback）
- 调整提示词时，保持输出结构稳定（JSON 字段不可随意变）
- 发布后优先检查日志中的 `source` 与 `fallback_reason`
- 科学问答新增开关需联调验证：`enable_deep_thinking`（模型切换）与 `enable_web_search`（联网检索+来源链接）
- 流式问答 `meta` 事件需保持兼容：至少包含 `source`，建议包含 `model/web_search_used/web_search_notice/citations`

### 5.3 引用对齐规则

当启用"正文引用对齐"并过滤来源后，必须确保回答中的 `[n]` 与返回 `citations` 保持同序连续映射（避免会话重载后编号存在但链接缺失）。

### 5.4 AI 会话化能力维护

关键位置：
- `app/api/routes/telemetry.py`：会话 CRUD 与会话内问答/流式接口
- `app/db/models.py`：`AIConversation`、`AIConversationMessage`
- `alembic/versions/0004_ai_conversation_history.py`：会话表迁移
- `frontend/src/components/FloatingAIAssistant.vue`：会话列表、切换、重命名、删除、流式锁定
- `frontend/src/api/index.ts`：会话接口封装

维护检查：
- 会话隔离：A 用户不可访问 B 用户会话
- 会话删除：删除会话后消息应一并删除（不可恢复）
- 流式锁定：生成中禁止切换会话，避免上下文错乱
- 兼容性：旧接口 `/api/ai/science-assistant` 与 `/stream` 仍可用
- 标题策略：首轮提问后可自动生成标题，手动重命名仍应生效
- 交互策略：当前会话标题单击可原地重命名，历史会话标题双击可原地重命名
- 置顶策略：会话支持置顶/取消置顶，置顶会话排在列表顶部

### 5.5 AI 环境变量速查

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_KEY` | - | API Key（必须配置才能使用 AI） |
| `AI_CHAT_MODEL` | deepseek-chat | 普通问答模型 |
| `AI_REASONER_MODEL` | deepseek-reasoner | 深度思考模型 |
| `AI_LANGCHAIN_ENABLED` | true | 启用 LangChain 编排 |
| `AI_STREAM_ENABLED` | true | 启用流式输出 |
| `AI_TEMPERATURE` | 0.4 | 模型温度 |
| `AI_MAX_TOKENS` | 600 | Token 上限 |
| `AI_TIMEOUT_SECONDS` | 20 | 调用超时 |
| `AI_STREAM_TIMEOUT_SECONDS` | 45 | 流式超时 |
| `AI_RETRY_COUNT` | 1 | 重试次数 |
| `RAG_ENABLED` | true | 启用 RAG |
| `RAG_TOP_K` | 4 | 检索片段数 |

## 6. 教学内容模块维护清单

改动以下任一位置时，需要联动检查：

| 位置 | 文件 |
|------|------|
| 后端路由 | `app/api/routes/content.py` |
| 后端模型 | `app/schemas/content.py` |
| 前端 API | `frontend/src/api/index.ts`, `frontend/src/api/teaching.ts` |
| 前端页面 | `frontend/src/views/TeachingContents.vue` |

检查项：
- 发布者、发布时间字段是否在后端返回
- 前端是否展示并正确处理空值
- 发布/取消发布按钮是否按权限显示
- 管理员与作者权限行为是否一致
- RAG 索引是否在内容创建/更新/发布/删除时触发增量同步

## 7. 前端可维护性约定

### 7.1 编码规范

- 统一使用 `frontend/src/utils/error.ts` 解析错误
- 避免在视图层新增大量 `any`，优先在 `frontend/src/api/` 补类型
- API 返回结构变化时，先改类型，再改页面逻辑
- 重复逻辑优先抽公共函数或 composable，减少页面内复制粘贴
- 分页逻辑统一使用 `usePagination` composable

### 7.2 主题与样式

- 主题变量定义在 `frontend/src/styles/theme.css`
- 组件内使用 CSS 变量引用，避免硬编码颜色值
- 图表配色通过 CSS 变量联动
- 新增组件遵循毛玻璃布局与统一圆角/阴影层级

### 7.3 路由与权限

- 新增页面需在 `frontend/src/router/index.ts` 注册路由
- 需要认证的页面设置 `meta: { requiresAuth: true }`
- 管理员专属页面设置 `meta: { requiresAdmin: true }`
- 教师专属页面设置 `meta: { requiresTeacher: true }`
- 角色分发模块（Assignments/Plants/Groups）遵循 index.vue 分发模式

## 8. 后端可维护性约定

### 8.1 新增 API 流程

1. 在 `app/schemas/` 定义请求/响应模型
2. 在 `app/services/` 实现业务逻辑
3. 在 `app/api/routes/` 添加路由，使用 `Depends()` 注入权限
4. 在 `main.py` 中 `include_router` 注册
5. 如需数据库变更，创建 Alembic 迁移

### 8.2 权限检查

- 认证：`Depends(get_current_user)`
- 教师/管理员：`Depends(get_teacher_user)`
- 管理员：`Depends(get_admin_user)`
- 资源所有权：`can_manage_owned_resource(current_user, resource.created_by)`
- 班级/设备可见范围：`get_allowed_class_ids()` / `get_allowed_device_ids()`

### 8.3 数据库模型变更

- 新增字段优先设为 nullable 或提供 server_default
- 新增表在 `app/db/models.py` 中定义
- 同步创建 Alembic 迁移脚本
- 迁移脚本需保证幂等性

## 9. 发布前检查清单

按顺序执行：

1. 数据库迁移可执行（如有新迁移）
2. 后端 `python -m compileall app main.py` 通过
3. 前端 `npm run build` 通过
4. 登录与权限校验通过（学生/教师/管理员三角色）
5. 教学内容完整链路通过（创建、发布、查看、评论）
6. AI 三链路可用（问答、润色、点评）
7. AI 问答开关链路可用（深度思考模型切换、智能搜索来源链接、天气实时问答、联网失败自动回退提示）
8. AI 会话链路可用（新建/切换/重命名/删除/置顶/会话内问答与流式）
9. AI 最小回归脚本通过（`python scripts/ai_regression_probe.py`，按需启用 strict 参数）
10. 稳定性专项脚本通过（`python scripts/stability_regression_probe.py`）
11. 摄像头链路检查通过（设备快照上传、监控页出图、大屏出图）
12. 关键文档同步更新（README、本文档、变更说明）

### 9.1 摄像头功能快速回归

适用场景：`ESP32-CAM + OV2640` 快照流模式。

后端接口联通测试（示例）：
```powershell
# 1) 上传一张测试 JPEG
curl -X POST "http://127.0.0.1:8000/api/devices/1/camera" \
	-H "X-Device-Token: <DEVICE_TOKEN>" \
	-H "Content-Type: image/jpeg" \
	--data-binary "@test.jpg"

# 2) 打开公开流（浏览器）
http://127.0.0.1:8000/api/public/devices/1/camera/stream
```

页面检查：
- 登录后打开监控页 `Dashboard.vue`，切到已绑定摄像头的设备应可看到实时画面。
- 打开公开大屏 `DashboardDisplay.vue?device_id=<id>`，应可看到同一设备画面。

## 10. 常见问题排查

### 10.1 前端调用失败但后端正常

优先检查：
- `VITE_API_BASE_URL` 是否正确
- Token 是否过期（401 会触发跳转登录）
- 浏览器 Network 中接口路径是否指向 `/api`
- 前端来源（Origin）是否被后端 CORS 放行（`CORS_ORIGINS` / `CORS_ORIGIN_REGEX`）
- 若使用 `vite preview`（4173）或局域网 IP 访问，确认 CORS 配置与访问地址一致
- 前端会自动在候选 API 基址间回退重试，检查控制台 Network 日志确认实际请求地址

### 10.2 AI 输出异常短或风格不符

优先检查：
- `langchain_service` 中提示词是否被误改
- `ai_science_service` 中长度/风格兜底是否生效
- 环境变量 `AI_MAX_TOKENS`、`AI_TIMEOUT_SECONDS` 是否异常
- 深度思考模型配置是否有效（`AI_REASONER_MODEL` / `AI_CHAT_MODEL`）
- 若智能搜索开启但无来源，检查网络出口策略及 `web_search_notice` 是否正确返回

### 10.3 AI 天气问答未返回实时信息

优先检查：
- 提问是否包含城市（例如"北京现在天气怎么样"）
- 请求体是否开启 `enable_web_search=true`
- `web_search_notice` 是否返回"暂未获取到实时来源，已自动提供通用回答"

处理建议：
- 若已命中回退提示，优先排查部署环境外网访问策略
- 可执行 `python scripts/ai_regression_probe.py` 进行最小探测

### 10.4 发布按钮不可见

优先检查：
- 后端是否返回 `can_publish` / `can_edit` / `can_delete`
- 当前账号是否为内容作者或管理员

### 10.5 AI 会话 404/503

优先检查：
- 是否已执行数据库迁移：`python -m alembic upgrade head`
- 会话表 `ai_conversations` / `ai_conversation_messages` 是否存在
- 若浏览器 Network 中请求 URL 指向前端自身端口，说明 API 基址推导异常，刷新前端并重启后端

### 10.6 登录失败频控触发

- 5 分钟内同一 IP+用户名最多 8 次失败
- 触发后返回 429，响应头含 `Retry-After`
- 等待窗口过期后自动解除

### 10.7 分页返回空数据

- 检查 `page` 是否从 1 开始（`page >= 1`）
- 检查 `page_size` 是否超过 100（`page_size <= 100`）
- 前端 `usePagination` 会自动钳制页码，避免"幽灵空页"

### 10.8 文件上传失败

- 检查文件大小限制：头像 2MB、作业附件 20MB
- 检查文件格式：头像 jpg/jpeg/png/webp、附件 Word/PPT/PDF
- 检查 `uploads/` 目录权限

### 10.9 WebSocket 连接断开

- 检查 Token 是否有效（WebSocket 通过 query 参数传递）
- 检查网络稳定性
- `TelemetryHub` 会自动清理断线连接

## 11. 工具脚本速查

| 脚本 | 用途 |
|------|------|
| `init_db.py` | 初始化数据库（环境变量优先+随机强密码） |
| `reset_admin_password.py` | 重置管理员密码 |
| `set_test_passwords.py` | 统一设置测试账号密码 |
| `simulate_esp32.py` | ESP32 数据模拟器 |
| `clear_contents.py` | 清空教学内容（含自引用外键安全删除） |
| `init_sample_contents.py` | 初始化示例教学内容 |
| `migrate_users.py` | 用户数据迁移 |
| `scripts/ux_api_probe.py` | API 闭环探测 |
| `scripts/ai_regression_probe.py` | AI 回归探测 |
| `scripts/stability_regression_probe.py` | 稳定性专项探测 |
| `scripts/frontend_critical_api_probe.py` | 前端关键 API 探测 |
| `scripts/cleanup_empty_records.py` | 清理空 AI 会话记录 |

## 12. 安全维护要点

### 12.1 生产环境必检项

- [ ] `SECRET_KEY` 已更换为随机强密钥
- [ ] `DATABASE_URL` 使用专用数据库用户（非 root）
- [ ] `DEVICE_TOKEN` 已更换为安全随机值
- [ ] `CORS_ORIGINS` 已限制为实际域名
- [ ] 默认账号密码已修改
- [ ] HTTPS 已启用

### 12.2 定期检查

- 检查操作日志中异常登录行为
- 检查 AI 审计日志中异常调用模式
- 检查 `uploads/` 目录是否有未授权文件
- 检查数据库连接池状态

---

**最后更新**: 2026-04-21
