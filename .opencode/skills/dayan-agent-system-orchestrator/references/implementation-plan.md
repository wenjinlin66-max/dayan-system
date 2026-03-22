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
   9. 前端建立四个工作台页面壳：WorkflowCanvasPage / ChatWorkbenchPage / MonitorWorkbenchPage / RecordsWorkbenchPage
   10. 提供本地 Mock Event Injector 与 Mock Records Gateway，供未接 Go 真实库时验证 workflow 主链
   11. 建立独立 Mock 业务数据库 `dayan_mock_records` 的设计与接入位
- 交付物：
  - Python 服务基础目录与启动入口
  - 数据库迁移脚本
  - 工作流草稿/发布 API
  - 工作流版本状态机初版
  - DSL schema 与编译器初版
  - 前端智能体协同模块基础目录
- 四个工作台空页面与基础路由
  - Mock Event Injector / Mock Records Gateway 初版
  - 独立 Mock 业务数据库方案初版
- 依赖：
  - Python 技术栈已确定
  - PostgreSQL 可用
- workflow DSL 已冻结第一版
- 风险：
  - DSL 早期频繁变化导致表结构返工
- 草稿与发布逻辑边界不清
  - 若早期 Mock 契约与未来 Go 正式契约不一致，后续联调会产生返工
- 验收标准：
  - 可创建工作流草稿
  - 可编译生成 execution_dag
  - 可发布并查询当前发布版
  - 数据表与 schema 对齐
- 前端模块可独立挂载并展示四个工作台占位页
  - 可使用 Mock Event Injector 触发至少一条基础 workflow

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
  11. 感知型节点第一阶段优先实现“数据库实时感知”配置界面
  12. 感知型节点配置支持：基础身份、数据选择、逻辑构建器、事件输出映射四区布局
  13. 决策型节点第一阶段实现“模式选择 + 模式专属配置”设置面板
   14. 控制节点完成统一定义与前端配置面板草案
   15. 基于 Mock Event Injector / Mock Records Gateway 完成画布沙盒联调，验证不接 Go 真实数据库时的 workflow 编排闭环
   16. 画布页提供面向 `sensor_agent` 的 mock event inject 验证入口，直接从制作区验证数据库实时感知链路
   17. 临时业务表格工作台完成“真实表格查询/编辑 -> 事件触发 -> 感知型 workflow”联调方案设计，并明确未来 Go 接入后的删除策略
- 交付物：
  - 前后端对齐的 workflow JSON DSL
  - 节点与边校验规则
  - 草稿保存 / 编译 / 发布 / 沙盒测试 API
  - workflow 版本历史查询 API
- 画布工作台可交互页面
  - 紧凑型 workflow 信息区 + 画布内 `+` 触发节点面板 + 节点点击弹窗配置 的工作台交互初版
  - 首屏画布优先布局：基础信息/编译预览/版本历史收敛为 tabs 或折叠式辅助信息区
  - 节点配置表单初版
- 感知型节点数据库实时感知配置页初版
- 决策型节点三模式配置页初版
- 控制节点配置草案初版
  - 基于 Mock Gateway 的 workflow 沙盒联调闭环
  - 画布页内置的 mock event inject 验证入口初版
  - 临时业务表格工作台设计稿、独立路由口径与未来删除策略
  - 第一批 Mock Records 实现：独立连接、表初始化、临时 API、前端工作台骨架
- 依赖：
  - M1 的 DSL schema 和 workflow 表结构可用
  - 前端原型明确节点配置面板需求
- 风险：
  - 画布编辑态字段过多污染执行态
- 子流程、循环节点规则复杂度上升
  - Mock 数据若未保留正式契约关键字段，容易掩盖真实联调问题
- 验收标准：
  - 画布可保存草稿并编译
  - 控制节点可通过结构校验
  - 可通过接口查询某个 workflow 的版本历史
- 前端可完成一次“画布编辑 -> 保存草稿 -> 编译 -> 发布”闭环
  - 前端/后端可在无 Go 真实库接入前完成一次“Mock 事件注入 -> workflow 启动 -> 审批/执行 -> 结果回传”闭环
- 前端可完成一次“数据库感知节点配置 -> 条件设置 -> 输出事件映射”闭环
- 前端可在 workflow 制作区直接完成一次“模拟数据库事件注入 -> sensor_agent 命中/未命中 -> execution 回传”闭环
- 前端临时业务表格区方案应支持一次“查看真实 Mock 表 -> 编辑记录 -> 触发感知 -> workflow 执行 -> 结果写回”的闭环设计
- 前端可完成一次“决策模式切换 -> 模式专属配置 -> 输出配置”闭环
- 前端可完成控制节点基本配置录入

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
  11. 前端增加独立审批工作区与执行结果卡片区域
  12. 增加部门工作流查询界面，支持按部门 / 职能分类查询
  13. 增加对话路由接口：ask / approve / command
  14. 增加多模态消息归一化入口（语音 / PDF / 图片）
  15. 对话型智能体补齐“语义理解 -> workflow registry 检索 -> 规则过滤 -> 二次确认 -> 启动执行”的选流主链
  16. 对话型智能体补齐“参数补齐 -> execution start -> 审批恢复 -> 结果回传”的触发主链
- 交付物：
  - Chat API
  - Approval API / 审批卡片事件
  - 执行恢复接口
  - 基础流式状态推送
  - 对话工作台页面初版
  - 审批卡片与执行状态回传 UI
  - 执行结果回传卡片 UI
  - 部门 workflow 查询界面初版
  - 对话路由 API 初版
- 对话型智能体 workflow 选流主链初版
- 对话型智能体 workflow 启动主链初版
- workflow 目录直接启动与候选 workflow 二次确认启动主链
- execution 状态 SSE + 前端轮询兜底主链
- workflow 缺参时的参数补齐卡片与补齐后启动主链
- 依赖：
  - M1 workflow / execution 主链可用
  - M2 至少有一个可运行的审批型 workflow
- 风险：
- Go 审批主记录与 Python 运行态镜像不一致
- 对话会话与 execution 关联关系复杂
  - workflow 数量上升后，若 registry 检索与过滤规则不足，容易误选流程
- 验收标准：
- 用户可通过对话入口发起命令
- 执行过程可产生审批卡片
- 审批后 execution 可恢复继续运行
- 前端可完整展示“对话命令 -> 审批卡片 -> 恢复执行 -> 结果回传”链路
- 对话型智能体可根据部门和职能分类，展示当前账号可用的 workflow 目录
- 对话型智能体可在多 workflow 候选场景下完成一次“候选检索 -> 用户确认 -> 启动正确 workflow”闭环
- 对话型智能体可在 required_inputs 缺失时完成一次“缺参提示 -> 前端参数补齐 -> 继续启动 execution”闭环
- workflow 画布页可在删除冗余辅助区后保持“画布优先”首屏，并支持全屏编辑
- 用户应能从画布工作台明确进入独立对话工作台，并在其中完成审批与执行结果查看
- 顶部导航栏应能让用户在工作流制作区、对话区、监控区、工作流查看区之间切换
- 工作流查看区当前应开始真正落地“部门 → 触发逻辑”两层分类；制作区同时补“所属部门”选择，使 workflow 从创建时就归入明确部门

## M4 智能体能力接入
- 目标：让五类智能体与 LangGraph 执行器真正联动，形成可运行的多智能体协同能力。
- 核心任务：
  1. 落地 `sensor_agent` handler：事件接入、定时巡检、数据标准化
  2. 落地 `decision_agent` handler：rule / model / llm 三模式接口骨架
  3. 落地 `execution_agent` handler：Go 泛型 API / 工具调用 / MCP 接口骨架
  4. 落地 `dialog_agent` handler：ask / approve / command 三类路由
  5. 建立三级记忆接口：context / history / knowledge
  6. 增加工具注册表与外部系统适配器
  7. 前端补齐五类智能体节点配置界面（监控型除外）
  8. 前端补齐工作流授权部门、风险等级、工具选择等配置项
  9. 前端对接对话型智能体问答、执行型智能体结果展示
  10. 执行型智能体补齐“手动目标 / AI 选择目标”两种模式
  11. 执行型智能体补齐“部门表格写入”执行对象，支持按部门路由到各自表格并写入结构化数据
  11.1 执行型节点开始真实消费 `dept_route_mode`，至少先支持 `fixed_dept` 把写入目标切到指定部门
  12. 执行型智能体优先打通“对话审批 + 结果回传”主链
  13. 审批提醒、审批结果、执行终态消息需可回写到当前部门对话框
  13. 决策型智能体补齐规则集、模型注册、LLM+RAG 三模式运行链路，并把三模式从“骨架可跑”推进到“详细配置 + 编译校验 + 下游可消费输出”
  14. 对话型智能体补齐 workflow registry 检索、歧义消解、部门隔离与多模态归一化主链
  15. 控制节点逐步实现 condition / approval / wait / exception 的运行时主链
- 交付物：
  - 五类智能体 handler 初版
- 三级记忆骨架
- Go API client 与工具调用注册表
- 至少 2 条完整示例工作流（如事件审批流、对话指令流）
- 感知型智能体数据库事件主链初版（Go 事件 -> Python 订阅匹配 -> workflow 触发）
- 非监控型智能体节点配置 UI
- 智能体结果展示 UI 初版
- 执行型智能体 `department_table` 执行目标初版（目标注册、字段映射、按部门路由、写入结果回传）
- 执行型节点 `department_table` 配置面板初版（目标模式、provider、route mode、字段映射、缺省值、幂等键）
- workflow 创建冲突处理初版（重复 code 返回 409，前端转成可读提示）
- execution runtime 最小主链初版（start 后解析 execution_dag、分发节点、写 checkpoint、回填 final_output）
- 决策型智能体三模式运行主链初版
- 决策型智能体三模式详细设计与实现增强版：规则型阈值规则、模型型候选动作评分、智能型 AI 结构化决策
- 工作流查看区到制作区的恢复链路已进入收口：从 workflow 卡片进入制作区时必须恢复已保存的节点与连线，而不是打开新的空白编辑器
- 感知型智能体输入标准化主链初版（事件/输入 -> 条件匹配 -> 输出映射）
- 三级记忆 runtime accessor 初版（context / history / knowledge）
- Mock Event Injector 初版（用于未接 Go 真实事件流前驱动 `sensor_agent -> decision_agent -> execution_agent` 主链）
- 执行型智能体审批与结果回传主链初版
- 审批工作区与 approval resume 最小闭环初版（待办列表 -> 同意/驳回 -> execution 恢复/终止）
- 对话型智能体部门路由与 workflow 目录主链初版
- 对话工作台从“workflow 目录平铺”演进为“部门对话框 + category 分组 workflow 目录”组织形态
- workflow 生命周期管理继续前进：制作区与查看区都应具备删除 workflow 的入口（当前按真实删除 workflow 定义数据实现）
 - Mock Records 独立数据库与业务表格测试工作台方案定案，并与未来 Go 正式接管后的整体删除路径对齐
 - 第一批 Mock Records 主链已落地：真实表查看/改表 + 最近事件流 + 改表触发 execution
  - 控制节点关键运行时主链初版
- 依赖：
  - M3 对话与审批基础能力可用
  - 模型/RAG 方案至少有占位实现
- 风险：
  - handler 之间职责耦合过深
  - 工具调用、审批、记忆同时接入导致复杂度激增
  - `department_table` 若缺少跨部门权限校验、幂等去重与字段映射校验，容易出现误写、重写或脏数据写入
- 验收标准：
  - 至少一条事件驱动工作流跑通
  - 至少一条对话驱动工作流跑通
- execution_agent 能调用 Go API 或工具执行动作
- execution_agent 能根据 `dept_id` 将结构化数据写入对应部门表格，并回传写入结果
- execution start 不再只停留在 `running` 初始态，而是能完成一轮最小 graph 执行并把结果写回 execution 记录
- `department_table` 主链需通过部门权限、幂等去重、审批恢复后单次写入三类校验
- 若 execution 运行到 `approval` 节点，应进入 `waiting_approval`，且审批后能继续恢复或被终止
- 前端可配置并展示五类智能体关键参数与执行结果
- 感知型智能体可基于数据库变更事件完成一次低库存类场景触发
- 决策型智能体可在规则型 / 模型型 / 智能型三种模式下分别完成一次决策输出
- 决策型智能体三模式应能通过浏览器/API 直接看到结构化 `decision_outputs`，且模型型/智能型不得继续依赖固定建议数量模板
- `sensor_agent` 可输出结构化感知结果并回写到 execution state
- `dialog_agent / decision_agent` 可通过统一记忆接口访问 context/history/knowledge
- 可通过 Mock Event Injector 驱动至少一条感知型触发链，而不依赖 Go 真实事件联调
  - 执行型智能体可在“审批执行”和“直接执行”两种路径下完成一次结果回传
  - ApprovalWorkbench 可展示真实待审批任务并提交同意/驳回
  - 对话型智能体可在 ask / approve / command 三类路径下分别完成一次处理
  - 控制节点可在至少 condition / approval / wait / exception 四类场景下完成一次主链流转

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
  9. 监控型智能体按独立控制平面实现，不进入 workflow 画布节点集
  10. 增加 incident 模型、分类规则与干预动作 API
- 交付物：
  - Monitor API
  - 审计与监控数据写入规范
  - 失败任务处理方案
  - 集成测试与契约测试初版
  - 发布前检查清单
  - 监控工作台页面初版
  - 前端模块合并说明
  - monitor incident 模型与干预动作接口
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
- 监控工作台可独立查看 incident，并对执行发起受控干预动作

## 当前收尾优先级（2026-03-17）
- 在不新增大功能的前提下，优先完成“代码事实 → references 同步 → 下一步上下文 → GitHub 同步”的收尾闭环
- M3/M4 当前近端优先级收口为：
  1. `include_all / dept_id / owner_dept_id` 权限闸与共享会话边界
  2. `parallel` 节点从最小分支调度继续补到更完整的 fork/join 语义
  3. Records 被动触发的运行日志/命中解释与后续 Go records 事件桥收口
  4. workflow 执行历史的分页/截断元信息与多结果展示
  5. `department_table / feishu / email / mcp` 目标注册表、真实 executor、权限/幂等校验
- 本阶段不再把“Gemini 中转 ask 路径最小验证”或“Vite 默认代理回到 8000”作为下一步功能项：这两项代码口径已完成，剩余的是本机 8000 旧监听等环境收口问题

## 当前收尾优先级（2026-03-19）
- 在不新增大功能的前提下，优先完成“对话工作台最近修复 → references 同步 → 下一步上下文 → GitHub 同步”的第二轮收尾闭环
- M3/M4 当前近端优先级收口为：
  0. 先用 Mock Records 跑通“产品主表 -> 产品 BOM -> 客户订单 -> 零件需求 -> 三张部门分发表”的最小业务闭环 demo；当前已完成“链路二 workflow 化 + 三条 released sensor workflow 下发表单”这一收口：`customer_order` 先触发 projection workflow 重建 `parts_demand`，再由三条 fan-out workflow 下发部门表；下一步再把最上游切到“对话型 workflow 直接写 `parts_demand`”
  1. dialog-trigger workflow 的发布/选流/启动链路继续收紧输入值校验，避免默认兜底值（如 `unknown-item`）继续写入业务表格
  2. workflow 历史查询、chat scope、CEO 聚焦部门口径继续统一，避免“查看区有、对话区没有”这类范围不一致
  3. chat 主链外的历史弹窗、records 时间展示继续统一到 `Asia/Shanghai` 时间工具
  4. workflow registry 去重、旧 active 条目失活、长耗时启动超时治理当前已收口到可用状态，下一步以回归验证和权限闸加固为主，不再继续扩功能
  5. 右侧“部门流程目录 + 中心工作台”布局与 dialog-trigger 目录行为已收口，后续仅继续做统一风格与可用性细化，不再重构结构

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
