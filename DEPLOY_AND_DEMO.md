# 部署与答辩演示指南

## 1. 一键部署（Docker）

在项目根目录执行：

```bash
docker-compose up -d --build
```

默认访问地址：
- 前端：http://localhost:8080
- 后端 API：http://localhost:8000/docs

说明：
- `docker-compose.yml` 已包含 MySQL、FastAPI、Vue 静态站点。
- 若需要 AI 科学助手接入通义千问，请在系统环境变量或 `.env` 中提供 `QWEN_API_KEY`。

## 2. 本地开发运行

后端：
```bash
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

前端：
```bash
cd frontend
npm install
npm run dev
```

## 3. 答辩演示推荐流程（3-5 分钟）

1. 登录教师账号进入大棚监控页面。
2. 在“课堂演示一键场景”中依次触发：
   - 干旱胁迫
   - 高温应激
   - 恢复健康态
3. 观察“微孪生”状态变化（水泵/风扇/灯光）和实时数据刷新。
4. 在“AI 科学助手”提问：
   - 例如：为什么干旱时叶片容易下垂？
5. 进入“教学分析”页面展示：
   - 任务提交率
   - 平均分
   - 设备环境稳定度

## 4. 新增关键接口

- `POST /api/ai/science-assistant`
  - 作用：面向师生的 AI 科学问答。
- `POST /api/demo/scenario/{device_id}`
  - 作用：一键切换教学演示场景。
- `WS /ws/telemetry/{device_id}?token=...`
  - 作用：实时推送传感与控制状态。

## 5. CI 流程

已提供 `.github/workflows/ci.yml`：
- 后端：依赖安装 + 语法检查
- 前端：依赖安装 + 打包构建
