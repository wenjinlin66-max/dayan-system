# Mock Records 独立数据库与业务表格工作台方案（临时测试层）

## 1. 目标
- 在暂时无法对接 Go 正式业务数据库的前提下，提供一套**可真实查看、编辑、触发感知、执行工作流、回看结果**的联调环境
- 保证 Mock 业务数据与 Python AI 中枢主库隔离，避免污染 `dayan_agentic2`
- 保证未来接入 Go 正式 records API 时，可以**整体删除**该测试层，而不影响正式 workflow / 感知型节点 / 对话审批主链

## 2. 最终选择
- Mock 业务数据库单独创建为：`dayan_mock_records`
- 该数据库与 Python AI 中枢主库 `dayan_agentic2` **完全分离**
- Python 服务同时维护两类数据库边界：
  1. **主库**：`dayan_agentic2`，承载 workflow / execution / chat / approval / memory / audit 真相数据
  2. **Mock 业务库**：`dayan_mock_records`，承载用于前端展示与联调的业务表（如 `inventory_stock` / `production_order` / `device_status`）

## 3. 为什么必须单独数据库
- 避免把 mock 业务表混入 Python 主库 schema，降低后续清理成本
- 避免 workflow/chat/approval/memory 领域迁移与 mock 业务表迁移耦合
- 让“业务数据联调层”与“AI 中枢控制层”边界清晰
- 未来对接 Go 时，可以直接删除该独立数据库、业务表格工作台与 `app/mock_records/` 相关代码，而不需要触碰 Python 主库真相数据

## 4. 前端信息架构

### 4.1 顶部导航新增工作区
顶部导航在现有四个页面基础上，新增：
- `业务表格区`

当前推荐顺序：
1. 工作流制作区
2. 工作流查看区
3. 对话区
4. 监控区
5. 业务表格区

说明：
- 用户要求该页面与现有四个页面并列，并放在监控区旁边
- 业务表格区不是监控区子页面，也不是画布页弹窗，而是**独立一级工作区**

### 4.2 业务表格区职责
业务表格区用于：
- 查看 `dayan_mock_records` 中的真实业务表数据
- 对记录做新增 / 编辑 / 删除
- 触发标准化数据库事件，驱动 `sensor_agent`
- 查看最近一次感知命中、workflow 执行与写回结果

定位约束：
- 业务表格区是**测试/联调工作区**，不是未来正式产品长期保留页面
- Go 端正式业务表格与 records API 接入后，该页面应整体删除或下线，不作为正式员工工作台保留

第一阶段页面结构建议：
- 左侧：数据源 / 表选择区
- 中间：真实表格展示区（支持分页、筛选、编辑弹窗）
- 右侧：最近一次事件、感知命中结果、触发的 workflow、执行回写摘要

## 5. 代码结构隔离方案

### 5.1 Python 侧
Mock 数据相关代码必须与 Python AI 中枢主领域分开，建议单独落位：

```text
app/
├─ api/
│  └─ v1/
│     └─ records.py
├─ mock_records/
│  ├─ schemas/
│  │  └─ records.py
│  ├─ service/
│  │  └─ records_service.py
│  ├─ repository/
│  │  └─ records_repository.py
│  └─ db/
│     ├─ base.py
│     ├─ models.py
│     └─ bootstrap.py
```

强制边界：
- `app/domain/` 继续只负责 AI 中枢主链
- `app/mock_records/` 负责 mock 业务库访问、表元数据、事件桥、前端表格 CRUD
- `mock_records` 不得直接承载 workflow/chat/approval 真相数据
- `app/mock_records/` 必须作为可整体删除的临时目录存在，不允许被主业务域反向依赖成长期基础设施

### 5.2 前端侧
建议新增：

```text
src/
├─ pages/
│  └─ RecordsWorkbenchPage.vue
├─ components/
│  └─ layout/
│     └─ WorkspaceTopNav.vue
├─ api/
│  └─ records.ts
├─ store/
│  └─ records.ts
└─ types/
   └─ records.ts
```

当前实现说明：
- 第一版 `RecordsWorkbenchPage.vue` 采用单页集成实现，尚未继续拆分成 `components/records/*`
- 右侧当前展示的是最近事件与触发 execution 摘要，还没有单独的“感知命中细节 + 写回结果”专属组件

## 6. 数据库设计边界

### 6.1 Python 主库（不变）
- 数据库名：`dayan_agentic2`
- 用途：workflow / execution / approval / chat / memory / audit / monitor

### 6.2 Mock 业务库（新增）
- 数据库名：`dayan_mock_records`
- 第一阶段建议表：
  - `inventory_stock`
  - `production_order`
  - `device_status`
  - `sensor_change_log`（可选，用于记录 UI 改表触发的标准事件）

### 6.3 关键原则
- Mock 业务库中的表结构应面向“业务字段 + 感知触发”设计，而不是完全复制 Python 主库结构
- 触发 `sensor_agent` 的标准事件，必须从 mock 业务库变更生成，不允许前端伪造“改成功了”的假状态

## 7. 运行链路

### 7.1 前端编辑表记录 → 感知触发主链
1. 用户进入业务表格区
2. 前端从 Python `mock_records` API 拉取真实表数据
3. 用户修改某条记录
4. Python 写入 `dayan_mock_records`
5. Python `event_bridge_service` 生成标准数据库事件信封
6. 事件投递给 `sensor_agent`
7. 若命中，触发对应 workflow execution
8. execution 结果继续写回 chat / execution / audit
9. 若 `execution_agent` 配置写回 mock records，则再把结果写回 `dayan_mock_records`
10. 前端业务表格区刷新后看到真实修改结果

当前阶段补充口径：
- 业务表格区的**被动事件触发不按当前登录账号部门过滤 workflow**；它应扫描所有已发布 workflow，只要 `sensor_agent` 的来源/表/事件键/条件命中就启动 execution
- 被动触发时，execution 的 `dept_id` 取命中 workflow 的 `owner_dept_id`，从而把执行结果、审批与对话框报告投递回对应部门，而不是投递到“当前修改数据的人”的部门
- CEO / 部门账号的差异只体现在“主动查看哪些对话框、主动启动哪些 workflow”的可见性与权限；业务表格的被动触发本身不应因为登录者是 CEO 还是部门账号而改变命中范围

### 7.2 必须保持的正式契约口径
- 事件信封结构继续沿用 Dayan `api-event-contracts.md`
- `sensor_agent` 配置结构继续沿用 workflow DSL
- 前端感知型面板、decision/execution 主链不因 mock 底座而变更
- 允许删除的仅是 Mock Records 测试层，不是 workflow / sensor / execution 主链本身

## 8. API 设计建议

第一阶段建议新增一组 Python Mock Records API：
- `GET /api/v1/records/sources`
- `GET /api/v1/records/tables`
- `GET /api/v1/records/tables/{table_name}/schema`
- `GET /api/v1/records/tables/{table_name}/rows`
- `POST /api/v1/records/tables/{table_name}/rows`
- `PUT /api/v1/records/tables/{table_name}/rows/{record_id}`
- `DELETE /api/v1/records/tables/{table_name}/rows/{record_id}`
- `GET /api/v1/records/events/recent`

说明：
- 这一组 API 服务于“业务表格区”与 mock records adapter
- 它们不是 Go 正式 records API 的替代真相，而是 Python 本地联调层

## 9. 与现有适配器的关系
- 当前 `MockRecordsGateway` 主要服务于 `execution_agent` 写回路径
- 新的 `dayan_mock_records` 方案当前通过 `app/api/v1/records.py + records_service.py` 直接落地，事件桥逻辑暂时内聚在 `records_service.py` 中，尚未单独拆成 `event_bridge_service.py`

建议拆分为两类能力：
1. **读写业务表能力**：供前端业务表格区和后端执行器共用
2. **事件桥能力**：供“记录修改 → sensor_agent”主链使用

## 10. 未来对接 Go 正式后端时如何删除/回收

### 10.1 接 Go 后继续保留的正式层
- 感知型节点配置 UI
- workflow DSL
- `sensor_agent / decision_agent / execution_agent` 主链
- 对话工作台、审批、执行结果回流逻辑

### 10.2 需要删除的层
- 前端业务表格区页面结构
- 顶部导航中的 `业务表格区`
- `app/mock_records/*`
- `dayan_mock_records` 独立数据库
- `app/mock_records/repository/*`
- `app/mock_records/service/records_service.py`
- `app/mock_records/service/metadata_service.py`
- `app/mock_records/service/event_bridge_service.py`

回收方式：
- 将底层数据访问正式切换到 Go records API / Go metadata API / Go event bus
- 删除 Python 本地 Mock Records API
- 删除前端业务表格区及其依赖组件、store、api、types
- 保持 workflow 契约、事件信封、感知型节点配置口径不变

### 10.3 推荐迁移步骤
1. 增加 `GoRecordsAdapter` 与 `GoMetadataAdapter`
2. 让感知事件来源切到 Go 正式事件总线
3. 验证“Go 改表 -> sensor_agent -> workflow -> 正式执行目标”主链通过
4. 删除顶部导航中的 `业务表格区`
5. 删除前端 `RecordsWorkbenchPage.vue` 与 `components/records/*`
6. 删除后端 `app/mock_records/*`
7. 删除独立数据库 `dayan_mock_records`

## 11. 风险与约束
- Mock 业务库字段若与未来 Go 正式 records 结构差异过大，会增加切换成本
- 前端业务表格区若直接依赖数据库物理字段，未来元数据演进会导致 UI 波动
- 必须通过 metadata/schema API 做字段解释层，不能把表结构细节散落到前端组件里

## 12. 当前定案
- 数据库名称：`dayan_mock_records`
- 前端新增一级导航：`业务表格区`
- 位置：与现有四个页面并列，放在 `监控区` 旁边
- Mock records 代码在 Python 代码框架中单独分层
- 所有 mock 数据库相关信息统一沉淀在本文件
- 后续接 Go 正式后端时，`dayan_mock_records`、`业务表格区`、`app/mock_records/` 都按临时测试层整体删除

## 13. 当前已实现的第一批能力
- 后端已新增 `GET/POST/PUT/DELETE /api/v1/records/*` 临时测试 API
- 后端已新增独立 Mock Records session，连接 `dayan_mock_records`
- 服务启动时会自动确保 `dayan_mock_records` 存在，并创建三张测试业务表与首批种子数据
- 记录修改会写入 `sensor_change_log` 并尝试触发匹配的已发布 workflow execution
- 前端已新增 `RecordsWorkbenchPage.vue` 与顶部导航入口，可直接查看/编辑三张测试业务表并查看最近事件流
