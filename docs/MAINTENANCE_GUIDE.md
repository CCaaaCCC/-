# 项目维护手册

## 1. 目的与范围

本手册用于降低项目交接成本，统一日常维护、升级发布、故障排查与回归验证流程。

适用范围：
- 后端 FastAPI 与数据库迁移维护
- 前端 Vue 构建与页面回归
- AI 能力（问答、润色、点评）稳定性维护
- 线上/演示环境快速排障

## 2. 维护入口总览

核心文档：
- README：项目总览、接口清单、运行方式
- docs/PROJECT_STRUCTURE.md：模块结构与拆分说明
- DEPLOY_AND_DEMO.md：部署与答辩演示流程
- docs/MAINTENANCE_GUIDE.md（本文）：维护操作标准

常用目录：
- app/api/routes：后端路由入口
- app/services：核心业务逻辑（AI、小组、历史、植物、通知）
- app/schemas：接口数据模型
- frontend/src/views：页面业务逻辑
- frontend/src/api：前端 API 封装与类型
- alembic/versions：数据库迁移脚本

## 3. 日常维护流程

### 3.1 本地启动

后端（项目根目录）：
```powershell
.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

前端（frontend 目录）：
```powershell
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

AI 助手回归探测（涉及 AI 渲染/联网引用/会话流式改动时推荐）：
```powershell
python scripts/ai_regression_probe.py

# 严格模式：要求 Markdown 与 [n] 引用链路都满足
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

注意事项：
- 优先使用“增量迁移”，不要直接修改历史迁移文件
- 涉及线上字段变更时，先做向后兼容（可空字段、默认值）
- 迁移后必须执行一次关键页面冒烟（登录、教学内容、作业、AI）

## 5. AI 模块维护要点

关键位置：
- app/services/ai_science_service.py：问答/润色/点评编排与规则兜底
- app/services/langchain_service.py：LangChain 模型调用与提示词
- app/services/rag_service.py：教学内容索引与检索
- app/services/ai_audit_service.py：AI 调用审计日志

维护原则：
- 保留兜底链路：模型失败时仍可返回可用内容
- 调整提示词时，保持输出结构稳定（JSON 字段不可随意变）
- 发布后优先检查日志中的 source 与 fallback_reason
- 科学问答新增开关需联调验证：`enable_deep_thinking`（模型切换）与 `enable_web_search`（联网检索+来源链接）
- 流式问答 `meta` 事件需保持兼容：至少包含 `source`，建议包含 `model/web_search_used/web_search_notice/citations`
- 当启用“正文引用对齐”并过滤来源后，必须确保回答中的 `[n]` 与返回 `citations` 保持同序连续映射（避免会话重载后编号存在但链接缺失）

### 5.1 AI 会话化能力维护要点（2026-04-12）

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

## 6. 教学内容模块维护清单

改动以下任一位置时，需要联动检查：
- app/api/routes/content.py
- app/schemas/content.py
- frontend/src/api/index.ts
- frontend/src/api/teaching.ts
- frontend/src/views/TeachingContents.vue

检查项：
- 发布者、发布时间字段是否在后端返回
- 前端是否展示并正确处理空值
- 发布/取消发布按钮是否按权限显示
- 管理员与作者权限行为是否一致

## 7. 前端可维护性约定

建议执行标准：
- 统一使用 frontend/src/utils/error.ts 解析错误
- 避免在视图层新增大量 any，优先在 frontend/src/api/index.ts 补类型
- API 返回结构变化时，先改类型，再改页面逻辑
- 重复逻辑优先抽公共函数，减少页面内复制粘贴

## 8. 发布前检查清单

建议按顺序执行：
1. 数据库迁移可执行（如有）
2. 后端 compileall 通过
3. 前端 build 通过
4. 登录与权限校验通过（学生/教师/管理员）
5. 教学内容完整链路通过（创建、发布、查看、评论）
6. AI 三链路可用（问答、润色、点评）
7. AI 问答开关链路可用（深度思考模型切换、智能搜索来源链接、天气实时问答、联网失败自动回退提示）
8. AI 会话链路可用（新建/切换/重命名/删除/会话内问答与流式）
9. AI 最小回归脚本通过（`python scripts/ai_regression_probe.py`，按需启用 strict 参数）
10. 关键文档同步更新（README、本文档、变更说明）

## 9. 常见问题排查

### 9.1 前端调用失败但后端正常

优先检查：
- VITE_API_BASE_URL 是否正确
- Token 是否过期（401 会触发跳转登录）
- 浏览器 Network 中接口路径是否指向 /api
- 前端来源（Origin）是否被后端 CORS 放行（`CORS_ORIGINS` / `CORS_ORIGIN_REGEX`）
- 若使用 `vite preview`（4173）或局域网 IP 访问，确认 CORS 配置与访问地址一致

### 9.2 AI 输出异常短或风格不符

优先检查：
- langchain_service 中提示词是否被误改
- ai_science_service 中长度/风格兜底是否生效
- 环境变量 AI_MAX_TOKENS、AI_TIMEOUT_SECONDS 是否异常
- 深度思考模型配置是否有效（`AI_REASONER_MODEL` / `AI_CHAT_MODEL`）
- 若智能搜索开启但无来源，检查网络出口策略及 `web_search_notice` 是否正确返回

### 9.3 AI 天气问答未返回实时信息

优先检查：
- 提问是否包含城市（例如“北京现在天气怎么样”）
- 请求体是否开启 `enable_web_search=true`
- `web_search_notice` 是否返回“暂未获取到实时来源，已自动提供通用回答”

处理建议：
- 若已命中回退提示，优先排查部署环境外网访问策略
- 可在同机执行最小探测（示例）：
	`python scripts/ai_regression_probe.py`（必要时补充单独天气探测脚本）

### 9.4 发布按钮不可见

优先检查：
- 后端是否返回 can_publish/can_edit/can_delete
- 当前账号是否为内容作者或管理员
- 前端权限判断函数是否被改动

### 9.5 AI 会话列表为空或无法切换

优先检查：
- 是否已执行迁移：`python -m alembic upgrade head`
- `ai_conversations`、`ai_conversation_messages` 表是否创建成功
- 当前 Token 对应用户是否与会话 `user_id` 一致
- 前端是否仍处于流式生成状态（生成中会锁定切换）

### 9.6 AI 会话初始化 Network Error

优先检查：
- 后端是否已监听 8000 且可访问 `/docs`
- 前端访问地址是否为 `localhost:5173` 或 `127.0.0.1:5173`
- 若使用反向代理，`VITE_API_BASE_URL` 是否指向正确后端
- 浏览器控制台是否存在 CORS 或 Mixed Content 错误
- 如前端运行在 4173/3000 或局域网 IP，检查 `CORS_ORIGINS` / `CORS_ORIGIN_REGEX` 是否覆盖当前来源

补充说明：
- 后端默认 CORS 已包含 `localhost/127.0.0.1` 的 `5173/4173/3000`，并支持私有网段来源（教学演示场景）
- 前端 API 基址候选回退策略覆盖普通请求与 AI 流式请求，网络失败时会在 `localhost:8000` 与 `127.0.0.1:8000` 间自动重试

### 9.7 AI 会话创建失败（404/500/503）

优先检查：
- 是否已执行迁移：`python -m alembic upgrade head`
- 数据库中是否存在 `ai_conversations`、`ai_conversation_messages` 两张表
- 浏览器 Network 的请求 URL 是否错误落在前端地址（如 `:5173/api/...`）

处理建议：
- 若为历史残留空会话过多，执行：`python -m scripts.cleanup_empty_records`
- 清理后刷新页面，确认左侧仅保留有效会话或至多一个空占位会话

## 10. 文档维护规则

每次涉及以下变更时，必须更新文档：
- 新增/删除 API
- 变更权限行为
- 调整数据库结构
- 修改 AI 配置项或调用链路
- 更改部署或启动命令

推荐最少更新范围：
- README（对外可见变更）
- docs/MAINTENANCE_GUIDE.md（维护流程）
- docs/PROJECT_STRUCTURE.md（结构变化）
