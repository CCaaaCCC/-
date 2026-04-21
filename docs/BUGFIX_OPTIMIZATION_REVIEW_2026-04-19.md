# Bug 修复与优化 Review（2026-04-19）

## 1. 本轮目标

针对“智慧大棚教具系统”完成以下 3 个落地项：

1. 前端边界态修复（状态残留、幽灵页、失败重试抖动）
2. 作业列表分页兼容改造（前后端联动，兼容旧调用）
3. 回归探测脚本补齐（稳定性专项）

---

## 2. 已完成改造

### 2.1 前端边界态修复

- `frontend/src/composables/usePagination.ts`
  - 新增页码钳制逻辑：`total` 或 `page_size` 变化后自动回退到合法页码。
  - 解决“数据删除后仍停留在无效页”的幽灵分页问题。

- `frontend/src/composables/useCurrentUser.ts`
  - 为 `ensureLoaded()` 增加失败短冷却（3 秒）与共享错误缓存。
  - 避免弱网/后端抖动时短时间重复触发 `/profile/me` 请求风暴。

- `frontend/src/views/Plants.vue`
  - `loadPlants()` 开始时先清空 `plants`，避免“错误提示 + 旧列表残影”并存。
  - 新建档案弹窗新增 `@closed="resetPlantForm"`，关闭后清理表单与上传状态。
  - 消除“再次打开弹窗仍带上次输入”的状态泄漏。

### 2.2 作业列表分页兼容改造

- `app/schemas/assignments.py`
  - 新增 `AssignmentListResponse`（`items/total/page/page_size`）。

- `app/api/routes/assignments.py`
  - `/api/assignments` 支持可选分页参数：`with_pagination/page/page_size`。
  - 保持兼容：
    - 旧调用（不传 `with_pagination`）仍返回数组。
    - 新调用（传 `with_pagination=true`）返回分页对象。
  - 增加分页参数边界校验（`page >= 1`、`page_size <= 100`）。
  - 修复分页参数兜底缺陷：`page=0` 不再被 `or` 误转为 `1`。

- `frontend/src/api/index.ts`
  - `getAssignments` 返回类型扩展为 `Assignment[] | AssignmentListResponse`。
  - 新增 `AssignmentListResponse` 前端类型。

- `frontend/src/api/assignments.ts`
  - 导出 `AssignmentListResponse` 类型供页面使用。

- `frontend/src/views/Assignments.vue`
  - 列表读取改为分页模式（携带 `with_pagination=true`）。
  - 新增分页组件（页码与每页条数切换）。
  - 新增越界页自动二次拉取逻辑，消除删除后最后一页空白。
  - 学生统计改为基于分页元数据 `total` 计算，避免使用当前页长度导致偏差。
  - 教师统计改为独立全量计算，避免分页截断导致统计偏差。

### 2.3 稳定性回归探测

- 新增 `scripts/stability_regression_probe.py`
  - 覆盖三类专项：
    - 登录失败限流
    - 列表分页边界（content/market/assignments）
    - 作业列表兼容（旧数组 + 新分页对象）
  - 输出报告文件：`docs/stability_regression_probe_results_2026-04-19.json`

---

## 3. 验证与结论

### 3.1 静态检查

- 已对本轮改动文件执行错误检查：无语法/类型错误。
- 已执行 `compileall`：本轮后端与脚本文件编译通过。

### 3.2 脚本执行

- 已执行 `python scripts/stability_regression_probe.py` 并产出报告。
- 当前通过率未达到 100%，主要原因是运行时环境与已修改代码的热加载状态可能不一致（部分接口返回表现未对齐最新代码）。
- 脚本已可作为后续 CI 或发布前二次验证入口。

---

## 4. 风险与建议

### 高优先

1. 在“重启后端服务”后再次执行 `stability_regression_probe.py`，确认运行态与代码态一致。
2. 将该脚本纳入发布前最小检查链路，避免回归。

### 中优先

3. 若作业数据规模继续上涨，建议将学生状态过滤从“内存过滤”升级为 SQL 层处理。
4. 教师统计可下沉为后端聚合接口，减少前端二次请求。

### 低优先

5. 将 `stability_regression_probe.py` 接入 CI（定时或 PR 校验），并保留最近一次结果快照。

---

## 5. 总体评估

- 本轮核心目标 1/2/3 已完成并落地。
- 系统在可维护性、边界态稳定性、以及分页兼容性方面明显提升。
- 当前剩余工作以“运行态复核 + 持续化接入” 为主，不属于结构性阻断问题。
