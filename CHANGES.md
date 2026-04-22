# 变更记录（CHANGES）

本文档记录项目各版本的显著变更，按时间倒序排列。

---

## 2026-04-21 — 新增 ESP32-CAM 轻量视频监控

- 新增：设备摄像头元数据。
  - `app/db/models.py`：`Device` 增加 `has_camera` 字段（默认 false）。
  - `app/schemas/telemetry.py`：`DeviceResponse`、`DeviceCreateRequest` 增加 `has_camera`。
  - `alembic/versions/0010_device_camera_support.py`：新增迁移脚本，向 `devices` 表加列。

- 新增：后端摄像头接口（快照上传 + MJPEG 分发）。
  - `app/api/routes/telemetry.py`：
    - `POST /api/devices/{device_id}/camera`（设备 token 鉴权，上传 JPEG 快照）
    - `GET /api/devices/{device_id}/camera/stream`（私有流，支持 Bearer 或 query token）
    - `GET /api/public/devices/{device_id}/camera/stream`（公开流，供大屏展示）
  - 后端采用内存缓存最近帧并设置 TTL，避免落盘 IO 与数据库写入压力。

- 新增：前端监控页面画面接入。
  - `frontend/src/components/Dashboard.vue`：大棚监控页新增“监控画面”卡片，随设备切换自动切流。
  - `frontend/src/views/DashboardDisplay.vue`：公开大屏新增摄像头画面区域。
  - `frontend/src/api/index.ts`：新增 `getCameraStreamUrl(...)`，并扩展 `Device` 类型。

- 新增：硬件独立固件。
  - `esp32_cam_snapshot.ino`：ESP32-CAM(OV2640) 独立快照上报程序，默认每秒上传一帧。

## 2026-04-21 — 文档全面更新

- 重构：项目文档体系全面更新，确保准确反映当前项目状态。
  - `README.md`：从变更日志混合体重构为专业项目入口文档，覆盖核心功能、技术架构、快速开始、目录结构、API 参考、权限体系、数据库模型、环境变量、安全配置与常见问题。
  - `docs/PROJECT_STRUCTURE.md`：全面重写项目架构说明，覆盖后端模块（服务层/API 层/数据层/核心层）、前端模块（页面/组件/Composables/API 层）、数据库迁移、硬件集成与 AI 工作流。
  - `docs/MAINTENANCE_GUIDE.md`：全面重写维护手册，覆盖日常维护流程、数据库迁移、AI 模块维护要点、前后端编码规范、发布前检查清单、常见问题排查、工具脚本速查与安全维护要点。
  - `DEPLOY_AND_DEMO.md`：全面重写部署与演示指南，覆盖 Docker 一键部署、本地开发部署、生产环境部署（Nginx/Systemd）、答辩演示流程、CI 流程、数据备份与恢复、版本升级流程。
  - `CHANGES.md`：从流水日志重构为结构化版本变更记录。

---

## 2026-04-19 — 安全加固与稳定性修复

- 修复：后端安全与资源生命周期问题。
  - `app/api/routes/auth.py`：`/token` 新增登录失败频控（IP+用户名窗口），降低暴力破解风险。
  - `app/api/routes/content.py`：删除内容时同步清理 `uploads/content` 关联文件，并加入路径根校验。
  - `app/api/routes/market.py`：删除商品时同步清理 `uploads/market` 图片，并加入路径根校验。

- 修复：列表分页边界与兼容性。
  - `app/api/routes/content.py`、`app/api/routes/market.py`：补充分页参数边界校验（`page >= 1`、`page_size <= 100`）。
  - `app/api/routes/assignments.py`：新增可选分页模式（`with_pagination/page/page_size`），并保持旧数组响应兼容。
  - `app/schemas/assignments.py`：新增 `AssignmentListResponse`。
  - `app/schemas/market.py`：创建/更新模型启用 `extra=forbid`，拒绝未知字段输入。

- 修复：前端边界态与分页体验问题。
  - `frontend/src/composables/usePagination.ts`：新增页码钳制，避免"幽灵空页"。
  - `frontend/src/composables/useCurrentUser.ts`：失败后短冷却，降低弱网重试抖动。
  - `frontend/src/views/Plants.vue`：请求失败时清空旧列表；弹窗关闭后重置表单与上传状态。
  - `frontend/src/views/Assignments.vue`：接入分页加载与分页组件；统计逻辑改为不依赖当前页数据，避免分页后统计偏差。
  - `frontend/src/api/index.ts`、`frontend/src/api/assignments.ts`：扩展作业列表分页响应类型。

- 新增：稳定性专项回归脚本。
  - `scripts/stability_regression_probe.py`：覆盖登录限流、分页边界、作业分页兼容（旧数组 + 新分页对象）。

---

## 2026-04 — AI 能力全面升级

- 新增：AI 会话化能力。
  - 后端：新增 `AIConversation`、`AIConversationMessage` 数据模型与完整 CRUD 接口。
  - 接口：`GET /api/ai/conversations`（列表）、`POST /api/ai/conversations`（创建）、`GET /api/ai/conversations/{id}`（详情含消息）、`PATCH /api/ai/conversations/{id}/title`（重命名）、`DELETE /api/ai/conversations/{id}`（删除）、`POST /api/ai/conversations/{id}/pin`（置顶）。
  - 接口：会话内问答 `POST /api/ai/conversations/{id}/science-assistant` 与流式 `POST /api/ai/conversations/{id}/science-assistant/stream`。
  - 前端：`FloatingAIAssistant.vue` 支持会话列表、切换、重命名、删除、置顶、流式锁定。
  - 迁移：`0004_ai_conversation_history.py`、`0005_ai_conversation_pinning.py`、`0006_ai_conversation_pinning_server_default.py`。
  - 兼容性：旧接口 `/api/ai/science-assistant` 与 `/stream` 仍可用。

- 新增：深度思考模式。
  - 后端：`enable_deep_thinking` 参数切换 `deepseek-reasoner` 模型，提供更深层的推理能力。
  - 前端：AI 面板新增"深度思考"开关。
  - 配置：`AI_CHAT_MODEL` / `AI_REASONER_MODEL` 环境变量。

- 新增：智能搜索（联网检索）。
  - 后端：`enable_web_search` 参数启用联网检索，搜索结果作为上下文注入提示词。
  - 后端：引用对齐机制，确保回答中 `[n]` 与 `citations` 保持同序连续映射。
  - 后端：权威来源识别（`.gov.cn`/`.edu.cn` 等优先）与低信度来源降权（CSDN/知乎等）。
  - 前端：AI 面板新增"智能搜索"开关，展示来源链接。
  - 流式：`meta` 事件包含 `source`/`model`/`web_search_used`/`web_search_notice`/`citations`。

- 新增：天气实时问答。
  - 后端：天气意图识别（关键词+正则），自动调用 Open-Meteo API 获取实时天气数据。
  - 后端：地理编码（GeoNames API）→ 天气预报（Open-Meteo API）→ 自然语言回答。
  - 后端：离线声明检测与自动重试，清理 AI 返回的"无法联网"声明。
  - 前端：天气回答含温度/湿度/风速/天气现象/位置坐标等结构化信息。

- 新增：AI 回归探测脚本。
  - `scripts/ai_regression_probe.py`：覆盖问答/润色/点评/流式/Markdown 渲染/联网引用/天气意图。
  - 支持 `--strict-markdown` 与 `--strict-citations` 严格模式。

- 新增：AI 审计日志。
  - `app/services/ai_audit_service.py`：记录每次 AI 调用的模型、来源、耗时、Token 用量。

---

## 2026-03-27 — 实验报告提交与体验优化

- 新增：实验报告文档提交流程。
  - 后端：`AssignmentSubmission` 增加提交/批改时间、批改人及报告文件元数据字段。
  - 接口：`POST /api/assignments/{id}/submit-with-file`、`GET /api/assignments/submissions/{id}/file`。
  - 前端：Assignments 页面支持学生上传报告、教师下载附件并继续批改。

- 修复：迁移脚本增强幂等性，避免重复列/索引导致升级失败；缩短 Alembic revision id 以适配 MySQL 版本长度限制。

- 修复：`AssignmentSubmission` 与 `User` 的双外键关系显式指定 `foreign_keys`，修复 ORM 关联歧义。

- 优化：统一多页面导航文案与入口语义。
  - "返回大棚监控/返回监控"统一为"返回工作台"。
  - 首页"大棚监控"按钮文案统一为"环境监控"。

---

## 2026-03-26 — main.py 重构与安全加固

- 重构：操作日志域从 `main.py` 下沉到独立模块。
  - 新增：`app/api/routes/logs.py`（`/api/logs/operations`、`/api/logs/operations/export`）。
  - 调整：`main.py` 移除操作日志内联路由，改为 `include_router(logs_router)`。

- 重构：植物档案剩余内联路由下沉。
  - 调整：`app/api/routes/plants.py` 补齐植物档案主 CRUD、图片上传、生长记录删除与 legacy 兼容路由。
  - 调整：`main.py` 移除植物档案与 legacy 记录相关内联路由。

- 重构：继续瘦身 `main.py` 为装配入口。
  - 调整：移除 `main.py` 内联 Pydantic 模型定义，相关模型迁移至 `app/schemas/plants.py`、`app/schemas/groups.py`、`app/schemas/profile.py`。
  - 调整：`main.py` 仅保留应用初始化、启动种子逻辑、静态资源挂载、根路由与 `include_router(...)` 装配。

- 重构：实验任务域从 `main.py` 下沉到独立模块。
  - 新增：`app/schemas/assignments.py`、`app/api/routes/assignments.py`。

- 重构：用户与班级域从 `main.py` 下沉到独立模块。
  - 新增：`app/schemas/users.py`、`app/api/routes/users.py`。

- 重构：教学内容域从 `main.py` 下沉到独立模块。
  - 新增：`app/schemas/content.py`、`app/api/routes/content.py`。

- 重构：数据库种子/启动逻辑从 `main.py` 抽取到 `app/core/bootstrap.py`。

- 修复：`clear_contents.py` 在清空 `content_categories` 时因自引用外键 `parent_id` 导致删除失败，改为按叶子结点循环删除。

- 改进：`init_db.py` 移除硬编码弱密码，支持环境变量 `DEFAULT_ADMIN_PASSWORD` 等指定密码，未设置时生成强随机密码。

---

## 数据库迁移版本历史

| 版本 | 说明 | 日期 |
|------|------|------|
| 0001 | 初始 Schema | 2026-03 |
| 0002 | 实验报告文件字段 | 2026-03-27 |
| 0003 | 个人中心评论通知 | 2026-03 |
| 0004 | AI 会话历史 | 2026-04 |
| 0005 | AI 会话置顶 | 2026-04 |
| 0006 | 置顶字段 server default | 2026-04 |
| 0007 | 角色 owner 权限（created_by 字段） | 2026-04 |
| 0008 | 商城标签 | 2026-04 |
| 0009 | 设备执行器级别 | 2026-04 |
| 0010 | 设备摄像头支持（has_camera） | 2026-04-21 |

---

**维护说明**：后续变更请按相同格式追加到本文档顶部，包含日期、变更类型（新增/修复/重构/优化）与具体影响范围。
