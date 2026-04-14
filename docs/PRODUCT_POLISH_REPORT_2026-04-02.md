# 产品打磨报告（2026-04-02）

## 1. 目标与范围

本轮目标：
- 优化项目代码结构，降低重复逻辑与维护成本。
- 提升关键页面 UI/UX 体验。
- 在可回归验证的前提下完成改造。

范围：
- 后端：AI 业务服务层（可维护性重构）。
- 前端：监控页、作业页、教学内容页、API 错误处理。
- 文档：README 补充本轮变更与验证结果。

## 2. 实施方案与落地

### 2.1 可维护性优化

1) 统一前端错误处理
- 新增 `frontend/src/utils/error.ts`
- 提供：
  - `getErrorMessage(error, fallback)`
  - `getFetchErrorMessage(response, fallback)`
- 接入：
  - `frontend/src/components/Dashboard.vue`
  - `frontend/src/views/Assignments.vue`
  - `frontend/src/views/TeachingContents.vue`
  - `frontend/src/api/index.ts`（流式接口错误解析）

收益：
- 减少分散的 `error.response?.data?.detail` 重复写法。
- 消息展示逻辑一致，减少未来维护分叉。

2) 重构后端 AI 服务重复逻辑
- 文件：`app/services/ai_science_service.py`
- 改动：
  - 提炼知识上下文构建：`_build_knowledge_context`
  - 提炼统一问答编排：`_ask_science_assistant_with_context`
  - 统一 source 常量（`SOURCE_*`）
  - Qwen 直连调用参数改用配置项：`AI_TEMPERATURE`、`AI_MAX_TOKENS`

收益：
- 减少 ask/stream 路径的重复代码。
- source 返回策略一致，避免维护时出现分支偏差。
- 配置驱动替代硬编码，部署可控性更高。

### 2.2 UX 优化

1) 监控页 AI 面板
- 文件：`frontend/src/components/Dashboard.vue`
- 增强点：
  - 快捷提问标签
  - “停止生成”按钮（可中断流式请求）
  - 流式生成光标反馈
  - 来源标签视觉化展示
  - 输入框字数限制与空输入禁用

2) 教学内容编辑页
- 文件：`frontend/src/views/TeachingContents.vue`
- 增强点：
  - 新增“AI 语气偏好”输入并透传后端
  - 增加 AI 生成操作提示文案
  - 修复“新建内容沿用旧编辑态”的体验问题（重置编辑器状态）

3) 作业批改页
- 文件：`frontend/src/views/Assignments.vue`
- 增强点：
  - AI 点评建议展示来源标签
  - 切换批改对象时重置来源状态，避免误导

### 2.3 稳定性缺陷修复（补充）

1) 修复遥测上报异常被误改状态码
- 文件：`app/api/routes/telemetry.py`
- 问题：`receive_telemetry` 的通用异常分支会吞掉业务 `HTTPException`，把应返回的 404/403 误返回为 400。
- 修复：新增 `except HTTPException` 分支并原样抛出，仅对未知异常返回通用 400。

收益：
- 错误语义准确，线上排障效率提升。

2) 修复流式 AI 的重复回退与鉴权误重试
- 文件：`frontend/src/api/index.ts`、`frontend/src/components/Dashboard.vue`
- 问题：流式请求失败时缺少状态码语义，调用端会在 401/403 下继续发起二次非流式请求；流式已产出部分内容时仍可能触发回退调用。
- 修复：
  - 为流式异常补充 `status` 字段。
  - `Dashboard` 仅在“未收到任何 token 且非鉴权错误”时执行非流式回退。
  - 流式已产出内容中断时保留已生成文本并提示。

收益：
- 降低无效请求与重复调用，提升课堂演示稳定性。

3) 修复操作日志页维护分叉与筛选能力不足
- 文件：`frontend/src/views/OperationLogs.vue`、`frontend/src/api/index.ts`
- 问题：日志页自建 axios 客户端，绕过统一拦截与配置；未提供 AI 审计类型筛选；导出未复用筛选日期。
- 修复：
  - 新增统一 API：`getOperationLogs`、`exportOperationLogs`。
  - 日志页改为复用统一 API 客户端与错误解析工具。
  - 筛选项新增 `ai_science`、`ai_stream`、`ai_feedback`、`ai_polish`。
  - 导出支持沿用日期筛选参数。

收益：
- 降低页面级重复实现，提升可维护性和管理可观测性。

4) 修复 API 地址硬编码
- 文件：`frontend/src/api/index.ts`
- 问题：前端 API 地址固定为 `http://localhost:8000/api`，不利于容器/跨主机部署。
- 修复：支持 `VITE_API_BASE_URL` 环境变量，缺省走浏览器当前主机名推导。

收益：
- 提升部署灵活性，减少环境切换改代码风险。

5) 扩大统一错误处理覆盖面
- 文件：`frontend/src/components/NotificationBell.vue`、`frontend/src/views/Groups.vue`、`frontend/src/views/Plants.vue`
- 修复：接入 `getErrorMessage`，统一错误消息解析策略。

## 3. 回归验证

已执行：
- 前端构建：`npx vite build`（通过）
- 后端编译检查：`d:/4C/.venv/Scripts/python.exe -m compileall app main.py`（通过）
- 静态错误检查：`get_errors`（全量无错误）

备注：
- 前端构建仍提示 chunk 体积告警（`vendor-ep` 较大），不影响功能正确性，建议后续做分包优化。

## 4. 代码 Review 结论

### 高优先级问题
- 已发现并修复 1 项高优先级问题：
  - 遥测上报路由业务异常被通用异常分支吞掉（错误码失真）。

### 中优先级问题
- 已发现并修复 2 项中优先级问题：
  - 流式 AI 在鉴权失败/中断场景下的回退重试策略不够稳健。
  - 操作日志页存在独立 HTTP 客户端与筛选能力缺口。

### 低优先级/后续建议
- 前端包体偏大（构建 warning）：
  - 可在 Vite 中配置 `manualChunks`。
  - 对非首屏模块进行动态导入。

## 5. 结论

本轮已完成“方案 -> 实施 -> 回归 -> review -> 文档”闭环，当前版本达到可交付的稳定状态，且在可维护性与关键交互体验上均有实质提升。
