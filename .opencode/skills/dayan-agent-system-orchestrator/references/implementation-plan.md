# 实施计划模板

## M1 基础底座
- 目标：完成 Python 智能体协同服务最小可运行底座，建立 workflow 真相源、核心表结构、基础 API 骨架与发布状态机。
- 核心任务：
  1. 初始化 Python 项目骨架（FastAPI + domain/runtime/db/tests 目录）
  2. 建立 `workflows` / `workflow_versions` / `execution_runs` / `approval_tasks` / `audit_logs` 等核心表
  3. 定义 `workflow-dsl.md` 对应的 Pydantic schema
  4. 实现 `ui_schema -> execution_dag` 的第一版编译器
  5. 实现 workflow 草稿保存、编译、发布、当前发布版查询 API
  6. 落地 workflow 发布状态机（draft / compiled / released / sandbox / archived）
  7. 落地基础鉴权依赖与 `dept_id` 上下文传递
  8. 前端建立智能体协同模块基础目录：pages / components / api / store / composables / types / router
  9. 前端建立三大工作台页面壳：WorkflowCanvasPage / ChatWorkbenchPage / MonitorWorkbenchPage
- 交付物：
  - Python 服务基础目录与启动入口
  - 数据库迁移脚本
  - 工作流草稿/发布 API
  - 工作流版本状态机初版
  - DSL schema 与编译器初版
  - 前端智能体协同模块基础目录
  - 三大工作台空页面与基础路由
- 依赖：
  - Python 技术栈已确定
  - PostgreSQL 可用
  - workflow DSL 已冻结第一版
- 风险：
  - DSL 早期频繁变化导致表结构返工
  - 草稿与发布逻辑边界不清
- 验收标准：
  - 可创建工作流草稿
  - 可编译生成 execution_dag
  - 可发布并查询当前发布版
  - 数据表与 schema 对齐
  - 前端模块可独立挂载并展示三大工作台占位页

## M2 画布与工作流编排
- 目标：打通前端画布工作台与 Python workflow 编排能力，使配置员可以通过画布构建、保存、编译、发布工作流。
- 核心任务：
  1. 定义前端画布 `ui_schema` 与后端 DSL 对应关系
  2. 完成节点类型配置：sensor / decision / execution / dialog / monitor / control nodes
  3. 完成边结构、entrypoint、子流程引用规则校验
  4. 增加草稿沙盒测试接口
  5. 增加 workflow version 列表与历史查询能力
  6. 实现 workflow 编译错误回传结构
  7. 前端实现 WorkflowCanvas 画布页、节点面板、节点配置面板、发布面板
  8. 前端完成 Vue Flow 节点注册与基础连线交互
  9. 前端完成 form-create 驱动的节点配置表单
  10. 前端对接草稿保存 / 编译 / 发布 / 版本历史接口
- 交付物：
  - 前后端对齐的 workflow JSON DSL
  - 节点与边校验规则
  - 草稿保存 / 编译 / 发布 / 沙盒测试 API
  - workflow 版本历史查询 API
  - 画布工作台可交互页面
  - 节点配置表单初版
- 依赖：
  - M1 的 DSL schema 和 workflow 表结构可用
  - 前端原型明确节点配置面板需求
- 风险：
  - 画布编辑态字段过多污染执行态
  - 子流程、循环节点规则复杂度上升
- 验收标准：
  - 画布可保存草稿并编译
  - 控制节点可通过结构校验
  - 可通过接口查询某个 workflow 的版本历史
  - 前端可完成一次“画布编辑 -> 保存草稿 -> 编译 -> 发布”闭环

## M3 对话视界与审批
- 目标：打通对话工作台、审批卡片、执行恢复能力，使用户能够通过对话界面发起命令、接收审批、查看执行结果。
- 核心任务：
  1. 建立 chat session / message 数据模型
  2. 实现对话入口 API（文本/语音/PDF 入口预留）
  3. 实现审批卡片事件输出与会话聚合展示
  4. 建立 `approval_tasks` 运行态镜像与 Go 审批主记录映射
  5. 实现 `resume execution` 接口和恢复上下文注入
  6. 实现执行状态 SSE / WebSocket 推送基础能力
  7. 前端实现对话工作台页面、会话侧栏、消息窗口、命令输入框
  8. 前端实现审批卡片组件与审批结果提交
  9. 前端预留语音 / PDF 上传入口并与消息流整合
  10. 前端接入 execution SSE 状态流
- 交付物：
  - Chat API
  - Approval API / 审批卡片事件
  - 执行恢复接口
  - 基础流式状态推送
  - 对话工作台页面初版
  - 审批卡片与执行状态回传 UI
- 依赖：
  - M1 workflow / execution 主链可用
  - M2 至少有一个可运行的审批型 workflow
- 风险：
  - Go 审批主记录与 Python 运行态镜像不一致
  - 对话会话与 execution 关联关系复杂
- 验收标准：
  - 用户可通过对话入口发起命令
  - 执行过程可产生审批卡片
  - 审批后 execution 可恢复继续运行
  - 前端可完整展示“对话命令 -> 审批卡片 -> 恢复执行 -> 结果回传”链路

## M4 智能体能力接入
- 目标：让五类智能体与 LangGraph 执行器真正联动，形成可运行的多智能体协同能力。
- 核心任务：
  1. 落地 `sensor_agent` handler：事件接入、定时巡检、数据标准化
  2. 落地 `decision_agent` handler：rule / model / llm 三模式接口骨架
  3. 落地 `execution_agent` handler：Go 泛型 API / 工具调用 / MCP 接口骨架
  4. 落地 `dialog_agent` handler：ask / approve / command 三类路由
  5. 落地 `monitor_agent` handler：主动/被动巡检输出
  6. 建立三级记忆接口：context / history / knowledge
  7. 增加工具注册表与外部系统适配器
  8. 前端补齐五类智能体节点配置界面
  9. 前端补齐工作流授权部门、风险等级、工具选择等配置项
  10. 前端对接对话型智能体问答、执行型智能体结果展示、监控型智能体巡检视图
- 交付物：
  - 五类智能体 handler 初版
  - 三级记忆骨架
  - Go API client 与工具调用注册表
  - 至少 2 条完整示例工作流（如事件审批流、对话指令流）
  - 五类智能体节点配置 UI
  - 智能体结果展示 UI 初版
- 依赖：
  - M3 对话与审批基础能力可用
  - 模型/RAG 方案至少有占位实现
- 风险：
  - handler 之间职责耦合过深
  - 工具调用、审批、记忆同时接入导致复杂度激增
- 验收标准：
  - 至少一条事件驱动工作流跑通
  - 至少一条对话驱动工作流跑通
  - execution_agent 能调用 Go API 或工具执行动作
  - 前端可配置并展示五类智能体关键参数与执行结果

## M5 监控运维与验收
- 目标：补齐监控、审计、失败恢复、测试门禁与上线前验收，使 Python 智能体协同模块具备可运维性。
- 核心任务：
  1. 实现 monitor API、执行列表、异常统计、失败率指标
  2. 建立 `audit_logs`、`tool_run_logs`、`monitor_snapshots` 的写入规范
  3. 增加死信/失败任务查询与补偿处理入口
  4. 补齐 contract tests（Go ↔ Python / 前端 ↔ Python）
  5. 补齐集成测试：workflow compile / publish / start / approve / resume / finish
  6. 接入测试治理 skill 的发布前门禁清单
  7. 前端实现监控工作台：指标卡片、执行列表、死信列表、告警面板
  8. 前端完成三大工作台联调验收与模块合并预适配
- 交付物：
  - Monitor API
  - 审计与监控数据写入规范
  - 失败任务处理方案
  - 集成测试与契约测试初版
  - 发布前检查清单
  - 监控工作台页面初版
  - 前端模块合并说明
- 依赖：
  - M4 多智能体主链已跑通
- 风险：
  - 监控口径与实际 execution 状态不一致
  - 测试覆盖不足导致发布风险高
- 验收标准：
  - 可查询执行状态、失败任务、关键指标
  - 核心主链具备自动化测试覆盖
  - 发布前检查具备明确门禁结论
  - 前端三大工作台具备完整联调结果

## 阶段间依赖关系
- M2 依赖 M1 的 workflow 真相源与编译能力
- M3 依赖 M1 + M2 的 workflow 主链
- M4 依赖 M3 的对话与审批恢复能力
- M5 依赖 M4 的多智能体示例工作流跑通

## 前后端并行开发分工建议
- M1：后端先给 schema / API 骨架，前端先搭模块与页面壳
- M2：前端主攻画布，后端主攻 workflow 编译/发布
- M3：前端主攻对话与审批卡片，后端主攻 chat / approval / resume / SSE
- M4：前后端围绕五类智能体节点配置与结果展示并行推进
- M5：以前后端联调、监控工作台、契约测试和验收为主

## 推荐 MVP 收敛路径
优先打通：
1. workflow 草稿 -> 编译 -> 发布
2. event -> execution start -> decision -> approval -> resume -> execution finish
3. 对话命令 -> workflow start -> 状态回传
