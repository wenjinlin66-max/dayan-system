# 开发进度跟踪模板

> 使用规则：每次执行方案后必须更新本文件，至少同步“已完成模块 / 进行中模块 / 下一步 / 文档同步状态”。

> 补充规则：每次大型步骤完成、关键节点开发完成、或关键修改完成后，应主动进行一次 GitHub 同步，并将同步结果回写到本文件。

## 当前里程碑
- M2 画布与工作流编排

## 当前阶段目标
- 细化五类智能体与控制节点设计，优先收敛主链、执行目标边界、对话选流主链与控制节点定义边界

## 已完成模块
- Python 服务基础骨架
- 前端智能体协同模块基础骨架
- 感知型智能体高层架构定义
- 决策型智能体高层架构定义
- 执行型智能体高层架构定义
- 对话型智能体高层架构定义
- 监控型智能体高层架构定义
- 控制节点高层架构定义
- skill 文档全量审查与主要冲突修正
- 前后端代码骨架与最新 skill 文档口径对齐
- M1 最小后端主链已落地：workflow 创建/草稿更新/编译/发布/启动 execution 可运行
- M2 最小前端闭环已落地：画布页可增节点、连线、保存草稿、编译、发布
- M2 画布界面已增强为可拖拽 Graph Editor：Vue Flow 画布、节点点击选中、右侧设置面板联动可用
- M2 编辑器已进一步增强：节点配置弹窗按节点类型表单化、发布门禁收紧为 compile success 后才能 publish
- M2 画布编辑能力已增强：删除节点、删除连线、fit view、reset canvas、加载已有 workflow 草稿继续编辑
- M2 节点选择方式已切换为画布内 + 按钮打开节点面板，更接近参考图工作台样式
- M2 画布 UI 已继续按参考图收敛：移除无效顶部按钮、取消固定左侧节点栏、改为画布内浮动 + 号打开节点面板
- M2 编辑器正确性第一轮收口已完成：脏状态、编辑后 compile/publish 失效、workflow 切换/重置未保存提醒、compile error 就地提示、原生 connect 同步 store 已落地
- M2 画布交互已进一步收敛：节点面板从右侧 Drawer 改为画布内浮层，左下角补齐放大/缩小/居中控件，右下角重复 + 已删除
- M2 顶部信息区已进一步压缩为紧凑型工具条与单行元信息区，减少对画布主体的占屏比例
- M2 编辑器状态正确性第二轮已落地：workflowName/workflowCode 实时同步 store、save/compile/publish/load pending 锁、load workflow deep clone 分离编辑态与快照态
- M2 首屏布局已进一步重构：基础信息/编译预览/版本历史收进 tabs，首屏优先让画布成为主视觉区域
- M3 最小对话主链已落地：chat session/message、workflow catalog、ask/approve/command 路由、对话触发 execution 可运行
- M3 已增强：workflow 目录可直接启动、候选 workflow 可二次确认启动、execution 状态流已接入 SSE 并支持轮询兜底
- M3 已继续增强：workflow registry 中的 `required_inputs / input_schema` 已接入对话工作台，缺参时可在目录卡片或消息卡片中补齐参数后继续启动 execution
- M4 执行型 `department_table` 已开始落代码：后端新增 ExecutionNodeHandler 初版与部门表格写入 payload 组装逻辑，前端新增 ExecutionConfigPanel 初版
- workflow 创建冲突已收口：重复 `workflow.code` 不再报 500，而是返回 `409 / WORKFLOW_CODE_ALREADY_EXISTS`，前端默认草稿编码改为动态生成
- workflow 画布页已继续收敛为画布优先布局：删除右侧 Graph Utilities 区，并新增全屏编辑入口
- M4 运行时已推进一大步：`ExecutionService.start()` 现在会执行最小 graph runtime，依次分发 `dialog_agent / decision_agent / condition / execution_agent`，并将 `department_table` mock 写入结果回填到 execution 终态
- M4 adapter 结构已继续推进：`ToolRegistry`、`DepartmentTableExecutor`、`GoRecordsClient`、`MockRecordsGateway` 已接入，`execution_agent` 不再在 runtime 中写死 mock writer
- 智能体能力主线已继续推进：`sensor_agent` 已支持输入标准化与条件匹配，`decision_agent` 已支持 rule/model/llm 三模式骨架，三级记忆 runtime accessor 已接入 `dialog_agent / decision_agent / sensor_agent`
- 感知型与执行型节点设置界面已重做为专属 panel：感知型聚焦“来源 / 条件 / 输出映射”，执行型聚焦“策略 / 路由 / 写入映射”，节点设置弹窗不再把复杂配置挤在同一块里
- 所有智能体设置界面已进一步统一到同一套浅色分区式属性面板风格：`dialog / sensor / decision / execution` 均采用“左侧基础信息 + 右侧专属 panel”结构
- 节点设置面板已按最新口径继续重排：顶部一排为“基础信息 / 节点类型 / 节点 ID”，主要设置改为中部纵向主区，JSON 高级配置下沉到底部；`condition / approval / wait / exception` 也已切入同风格专属 panel
- 画布节点卡片已继续提高清晰度：信息层级更明确，节点与连线都已支持悬停浮现删除按钮的画布内直接删除交互
- Mock Event Injector 已接入：可在未联调 Go 真实事件流前，通过 execution API 直接触发 `sensor_agent` 主链
- M3/M4 审批恢复链已推进为最小闭环：`approval` 节点可让 execution 进入 `waiting_approval`，`ApprovalWorkbench` 已接真实待办列表与同意/驳回提交，`/approvals/resume` 可继续恢复或终止 execution
- 对话工作台已被显性补出：画布工作台新增“进入对话工作台”入口，`ChatWorkbenchPage` 已重构为独立对话主入口，用户可在同一工作台中完成会话、审批、目录检索与结果查看
- 顶部导航已开始收口：工作流制作区、对话区、监控区、工作流查看区已纳入统一导航；`WorkflowLibraryPage` 已可按发布状态、所属部门、关键词查询 workflow
- 工作流查看区已继续推进：`workflow_category` 已进入 `/v1/workflows` 返回，前端改为按 category 分组展示，跨部门权限从前端筛选改为后端 `dept_id` 硬限制
- 对话工作台已继续推进为“部门对话框”形态：侧栏强调部门会话，部门流程目录按 category 分组，审批提醒/审批结果/执行结果已开始回写到 chat message 流
- 上一轮 Oracle 收口项已补齐：chat session 消息读写、execution 查询/stream 也已按部门权限限制；发送消息/启动流程/提交审批后会主动刷新消息流
- 对话工作台已进一步朝“AI 主对话框”收口：中间主区域改为 `ChatWindow + MessageComposer` 的问答主窗口，右侧保留流程目录、审批、执行结果、附件作为辅助区
- 对话工作台 UI 已继续收口：移除中间主区域的重复说明卡，并按最新口径直接隐藏独立附件入口卡片；后续多模态能力将并入主输入框交互
- 对话工作台布局已继续优化：审批工作区与执行结果移动到左侧，会话列表改为仅展示少量最近记录，完整历史通过中间弹窗选择
- 工作流制作区顶部信息栏已继续压缩：在不改变字段内容的前提下进一步收紧标题区、状态胶囊、字段输入区与动作区的占高
- 顶部导航顺序已调整为“工作流制作区 → 工作流查看区 → 对话区 → 监控区”
- 工作流分类已继续收口：去掉助手自行定义的业务分类，当前先按“触发逻辑分类”保存与展示，并为未来“部门 → 触发逻辑”两层结构留位
- workflow 删除能力已补入制作区与查看区，当前以后端真实删除 workflow 定义数据方式实现
- Python 模型配置已从 DeepSeek 默认口径切换为 Gemini 中转站（OpenAI-compatible）默认口径，并补充统一 `LLMClient` 接入位
- 感知型智能体本轮继续完善：`sensor_agent` 已补来源匹配（`source_system / source_table / source_event_key`）、命中才继续向下游节点流转、并将结构化 `sensor_event` 与匹配结果回写到 `sensor_outputs`
- Workflow 制作区已补感知型联调入口：当画布内存在 `sensor_agent` 节点时，可直接从顶部动作栏打开 mock event inject 对话框，注入标准数据库事件并触发执行
- 编译期已补 `sensor_agent` 配置校验；对话工作台执行结果卡片已开始展示 `final_output.sensor_outputs`，便于联调感知命中结果
- 感知型面板已从自由输入继续升级：后端新增 `sensor-metadata` 元数据目录接口，前端开始改为按来源系统 / 表 / 事件键 / 字段 / 操作符联动选择与结构化规则配置
- Mock Records 独立数据库方案已定：用户决定新增独立 PostgreSQL 数据库 `dayan_mock_records`，并要求把业务表格工作台与现有四个页面并列、放在监控区旁边
- 进一步定案：该 Mock 数据库、业务表格区与 `app/mock_records/` 都只是测试过渡层；Go 端正式表格能力接入后应整体删除
- Mock Records 第一批代码已落地：独立数据库连接、自动建库/建表/种子数据、`/api/v1/records/*`、顶部导航中的业务表格区、`RecordsWorkbenchPage.vue`
- 当前已可在前端查看三张测试业务表，并通过后端记录修改事件流验证感知型联调闭环
- 本轮代码收尾已完成：Mock Records 相关 Python 重点文件的 basedpyright warning 已清理，前端 Vite 构建已增加 vendor 分包并压掉 chunk warning
- 浏览器级联调验证已完成：可从顶部导航进入业务表格区，新增记录成功后可看到新记录文本与 `record.created` 事件文本，页面无前端报错
- 已补文档-代码对齐收尾：将 mock records/records workbench 的“目标拆分结构”与“当前已实现结构”区分开，避免 reference 超前描述实现状态

## 进行中模块
- 感知型智能体详细设计（数据库实时感知优先）
- 决策型智能体详细设计（三种决策模式）
- 执行型智能体详细设计（对话审批、结果回传、部门表格执行对象）
- 对话型智能体详细设计（部门化路由、workflow 目录、选流与触发主链）
- 对话型智能体详细设计（部门对话框消息回流、审批与执行结果在消息流中的呈现细化）
- 监控型智能体详细设计（独立监控工作台、非画布节点）
- 独立 Mock 业务库与临时业务表格测试工作台详细设计
- 控制节点详细设计（定义先行，开发后置）
- M1/M2 代码实现从“骨架”进入“最小闭环可运行”阶段
- M2 从“最小闭环可运行”进入“交互增强阶段”
- M2 从“交互增强阶段”进入“编辑器正确性与细节收口阶段”
- M2 当前进入“参考图 UI 收敛完成，状态正确性待收口”阶段
- M2 当前进入“状态正确性第一轮已落地，等待继续完善细节体验”阶段
- M3 代码实现从“页面骨架”进入“最小对话闭环可运行”阶段
- M3 代码实现从“最小对话闭环可运行”进入“候选确认与状态流增强阶段”

## 未开始模块
- 感知型智能体 Go 事件接入实现
- 决策型节点真实配置表单实现
- 决策型智能体 rule/model/llm 三模式 handler 实现
- 执行型节点真实配置表单实现
- 执行型审批工作区细节增强（筛选、时间线、结果卡片联动）
- 执行型智能体目标注册表与 handler 实现
- 部门表格执行对象 adapter / executor 实现
- 部门表格写入幂等、防重复与失败回传实现
- 对话型 workflow 目录查询界面实现
- 对话型智能体 ask/approve/command 路由增强实现（歧义消解、审批主链）
- execution 状态流完整前端体验（断线重连、终态停流）进一步增强
- 多模态消息归一化实现
- monitor incident 模型实现
- monitor workbench 真实页面实现
- 监控干预动作 API 实现
- 控制节点配置面板实现
- 控制节点运行时主链实现

## 阻塞项
- Go 侧事件 envelope 最终字段与投递格式尚未完全联调

## 风险项
- 感知型节点前端配置过复杂，可能影响 M2 交付节奏
- 数据库实时感知与未来 IoT/Webhook 扩展需要统一抽象，避免后期重构
- 决策型三模式配置差异较大，需要避免前端面板过于复杂
- 执行型“手动目标 / AI 选择目标”与审批逻辑耦合，需避免前端面板过重
- 部门表格按部门路由时，若目标注册与权限边界不清，容易出现跨部门误写入
- 部门表格字段映射若缺少幂等键与必填校验，容易重复插入或写入脏数据
- 对话型 workflow 路由若过度依赖自然语言匹配，容易误选 workflow
- 若未增加“目录检索 + 规则过滤 + 二次确认”机制，部门 workflow 数量增多后对话型智能体准确率会快速下降
- 部门权限与用户个人记录若不拆开，容易出现同权不同记录混乱
- 监控型智能体若过度干预 execution，将演变成隐藏执行引擎
- 控制节点若定义不统一，后续 execution_dag 与前端配置可能分裂
- 前端构建已通过，但当前打包体积较大，后续需做代码分割优化
- 当前 editor 在状态正确性上仍需继续收口：编辑后应自动标脏并使 compile/publish 状态失效，防止旧编译结果误导发布

## 下一步
- 将执行型智能体 `department_table` 的 DSL、注册表配置、写入契约与前端配置项继续细化到可开发级
- 测试治理门禁结论：有条件通过；进入实现前需补齐跨部门权限校验、幂等去重、审批恢复后单次写入三类测试与契约检查
- 补充本地 Mock Event Injector 与 Mock Records Gateway 方案，用于未接 Go 真实数据库前验证感知型、对话型与执行型工作流主链
- 继续把 `sensor_agent` 从当前内存态匹配推进到正式 `sensor_event_inbox / sensor_subscriptions` 持久化与订阅分发主链
- 继续把 `sensor-metadata` 从当前后端内置目录推进到真实 Go/数据库元数据同步来源，减少 mock 目录占比
- 输出 `dayan_mock_records` 的落地实施文档，并继续从“方案设计”推进到“Python Mock Records API + 业务表格测试工作台 + 事件桥”的真实开发，同时保留后续整体删除计划
- 继续把当前 RecordsWorkbench 从页面骨架推进到更完整的列筛选、字段校验、执行写回展示，并补与 `department_table` 的默认映射示例
- 如需进一步收尾，可继续把项目范围内其他历史存量 basedpyright warning 做分批治理；当前新增/近期关键文件已完成 warning 清理
- 将对话型智能体“选 workflow + 触发 execution”的主链继续细化到可开发级
- 将数据库设计文档改造成“按功能分类 + 按开发步骤索引”的结构，方便后续按 skill 阶段快速定位表
- 基于 `go-python-contracts-v1.md` 将 records/query/error/auth/event/approval/mock 细化到实现级与测试级
- 继续补齐 M2 真实画布交互、M3 对话选流主链、以及 M4 感知/执行 handler 接入
- 优先增强 M3：workflow 候选确认、参数补齐、execution 状态流推送、审批恢复卡片
- 继续增强 M2：节点拖拽连线、节点分组布局、form-create 配置表单、更多 LangGraph 风格视觉细节
- 按 Oracle 结论优先修复 M2 编辑器正确性：脏状态管理、编辑后重新编译、workflow 加载/重置前未保存提醒、compile error 就地提示
- 按最新 Oracle 结论继续修复 M2 编辑器正确性：脏状态管理、connect 事件与 store 同步、workflow 加载/重置保护、compile error 紧贴 publish 提示
- 在本轮正确性收口基础上，继续补齐：compile 成功快照签名、workflow 切换前更细粒度比较、节点新增后自动打开设置聚焦首字段、原生删除键支持
- 继续增强 M3：候选 workflow 歧义消解、参数补齐、审批卡片与 resume 主链、execution 状态流断线恢复策略
- 继续增强 M4：将 ExecutionNodeHandler 真正接入 runtime，并补 execution_target_registry / adapter 层
- 继续增强 workflow 画布：在全屏编辑模式下补更细的沉浸式状态提示与快捷操作
- 继续增强 M4 runtime：补真实 department_table adapter、审批挂起/恢复、异步 worker 与 exception 路由
- 继续增强 department_table adapter：补真实 route registry 来源、Go records API 更完整 update/upsert 语义与权限/幂等校验返回
- 继续增强智能体主线：把 history memory 从 runtime state 推进到真实持久化、把 knowledge memory 接到 RAG、补 decision model/llm 真实推理 client
- 继续增强前端智能体配置：把 decision_agent、dialog_agent 也升级为与 sensor/execution 同级别的专属 panel
- 继续增强节点设置前端：补 section 级校验提示、折叠式 JSON 高级区、以及更多智能体字段的结构化控件
- 继续增强节点设置前端：补分区级校验提示、字段级 schema 迁移保护，以及更细的旧配置兼容映射
- 继续增强画布交互：补 hover 删除按钮的可达性细节、节点空画布状态验证，以及边标签/路径编辑交互
- 继续增强审批链：补真实审批任务创建验证、恢复后 checkpoint 继续链路、审批意见回写与驳回结果卡片展示
- 继续增强工作流查看区：补更细的分类方式、卡片摘要、版本信息与从查看区进入编辑/对话的联动
- 继续增强工作流查看区：补更细的分类字典、统计摘要与 category 级权限审计
- 继续增强对话工作台：补消息流里的审批卡片/执行结果卡片富展示，收口当前文本提醒为结构化卡片
- 继续增强模型主链：把当前 chat ask 路径的 OpenAI-compatible LLM 接口从“基础可调用”推进到真正的对话记忆/RAG/工具调用统一链路

## 文档同步状态
- project-overview.md：无需更新
- architecture.md：已同步对话型智能体的 workflow 选流与触发主链，以及执行型智能体 `department_table` 设计
- workflow-dsl.md：已同步执行型节点 `department_table` 目标类型、配置字段与示例
- database-design.md：已同步 `department_table` 配置要求，并补充按功能分类与按开发步骤索引的表结构导航
- go-python-contracts-v1.md：已新增 Go↔Python 数据、事件、执行、审批恢复、错误码与 Mock 正式总表
- api-event-contracts.md：已同步部门表格写入请求/响应契约
- api-event-contracts.md：已补充初期无 Go 真实库时的 Mock 联调契约方案
- api-event-contracts.md：已同步 chat 显式启动 workflow 接口与 execution 状态 SSE 契约
- api-event-contracts.md：已同步 workflow 缺参时的参数补齐卡片契约与 input_values 启动示例
- api-event-contracts.md：已同步 workflow 创建时重复 code 的 409 冲突约束
- frontend-code-structure.md：已同步执行型节点前端配置新增 `department_table` 配置要求
- frontend-code-structure.md：已同步 chat 工作台的目录启动、候选确认、execution 状态流交互口径
- frontend-code-structure.md：已同步 WorkflowParameterCard 与 ExecutionConfigPanel 当前交互口径
- frontend-code-structure.md：已同步 workflow 画布“删除右侧辅助栏 + 全屏编辑”交互口径
- third-party-dependencies.md：已同步部门表格 adapter 依赖抽象口径
- third-party-dependencies.md：已同步 tool registry + department_table adapter 当前实现状态
- implementation-plan.md：已同步对话型智能体选流/触发主链，以及执行型智能体新增部门表格执行对象任务与验收口径
- implementation-plan.md：已补充 Mock Event Injector / Mock Records Gateway 的阶段任务与验收口径
- implementation-plan.md：已同步 workflow 目录直接启动、候选确认启动、execution 状态流兜底交付口径
- implementation-plan.md：已同步 workflow 缺参参数补齐与 `department_table` 配置面板交付口径
- python-service-api.md：已同步新增 execution stream、chat 显式启动 workflow 接口与参数补齐请求示例
- python-service-api.md：已同步 workflow 创建冲突返回 409 的接口口径
- python-service-api.md：已同步 execution start 的最小 runtime 执行行为
- python-service-api.md：已同步 department_table adapter 的 registry / records API / mock fallback 行为
- langgraph-runtime.md：已同步当前 runtime 最小主链、dispatcher 接入节点与 final_output 回填口径
- python-environment-config.md：已同步 Go records / department_table adapter 新增环境变量
- memory-model.md：已同步三级记忆 runtime accessor 的当前实现口径
- frontend-code-structure.md：已同步节点设置弹窗与 sensor/execution 专属 panel 新口径
- frontend-code-structure.md：已同步 dialog/decision/execution/sensor 四类智能体统一的浅色属性面板口径
- python-service-api.md：已同步 Mock Event Injector 接口行为
- progress-tracker.md：已同步 M1/M2 最小闭环代码实现状态与下一步开发方向
- progress-tracker.md：已同步 M3 最小对话主链代码实现状态与下一步增强方向
- progress-tracker.md：已同步 M2 编辑器增强（节点面板、workflow 加载、发布门禁、画布内 + 交互）
- frontend-code-structure.md：已同步 workflow 画布工作台当前交互口径（紧凑信息区、画布内节点面板、节点弹窗、左下角控件）
- frontend-code-structure.md：已同步实时 store 回写、pending 锁、deep clone 快照分离等编辑器正确性规则
- implementation-plan.md：已同步 M2 当前工作台交付形态描述
- frontend-code-structure.md：已同步“首屏画布优先、tabs/折叠式辅助信息区”的布局原则
- implementation-plan.md：已同步 M2 首屏布局收口后的交付形态
- change-log.md：已同步本次新增设计变更
- architecture.md：已同步工作流查看区改为 `workflow_category + 后端权限收口`，以及部门对话框主入口口径
- frontend-code-structure.md：已同步部门对话框、category 分组目录、审批/结果消息回流口径
- frontend-code-structure.md：已同步中间主对话区去装饰化，以及多模态能力后续并入输入框、当前不展示独立附件卡片的口径
- frontend-code-structure.md：已同步左侧辅助区重排与历史记录弹窗选择口径
- architecture.md：已同步顶部导航顺序调整口径
- frontend-code-structure.md：已同步工作流制作区顶部信息栏继续压缩的布局原则
- api-event-contracts.md：已同步 workflow 触发逻辑分类与真实删除接口口径
- implementation-plan.md：已同步 workflow 删除入口与两层分类扩展方向
- api-event-contracts.md：已同步 `/v1/workflows` 分类返回、后端部门限制与 chat 消息回流契约
- python-environment-config.md：已同步 Gemini 中转站默认模型配置与环境变量口径
- third-party-dependencies.md：已同步大模型 API 默认项从 DeepSeek 切换到 Gemini 中转站的选型口径
- frontend-code-structure.md：已同步制作区内置 mock event inject 入口与 sensor 映射口径
- api-event-contracts.md：已同步 `inject/mock-event` 当前请求结构与 `sensor_agent` 来源匹配/命中回写规则
- implementation-plan.md：已同步感知型工作流在制作区内直接验证的交付口径
- python-service-api.md：已修正 Mock Event Injector 重复旧路由描述，并补充 `sensor-metadata` 与感知 gating 当前行为
- workflow-dsl.md：已修正 `sensor_agent` 的 `source_type/source_event_key` 示例口径，并补充元数据目录选择规则
- langgraph-runtime.md：已同步 `sensor_agent` gating 与 final_output 最新字段口径
- mock-records-architecture.md：已新增独立 Mock 业务数据库、业务表格工作台、代码隔离与未来 Go 替换方案
- architecture.md：已同步业务表格工作台与 `dayan_mock_records` 的系统定位
- frontend-code-structure.md：已同步业务表格工作台的页面与组件目录口径
- python-code-structure.md：已同步 `app/mock_records/` 目录隔离方案
- python-environment-config.md：已同步 `MOCK_PG*` 环境变量口径
- python-service-api.md：已同步 Mock Records API 与当前自动建库/建表/事件触发行为
- mock-records-architecture.md：已同步第一批真实实现状态
- progress-tracker.md：已补记录本轮 warning 清理与构建优化状态
