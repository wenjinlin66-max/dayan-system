# 开发进度跟踪模板

> 使用规则：每次执行方案后必须更新本文件，至少同步“已完成模块 / 进行中模块 / 下一步 / 文档同步状态”。

> 补充规则：每次大型步骤完成、关键节点开发完成、或关键修改完成后，应主动进行一次 GitHub 同步，并将同步结果回写到本文件。

## 当前里程碑
- M3 对话视界与审批 + M4 智能体能力接入（交叉收口）

## 当前阶段目标
- 在不新增大功能的前提下完成一轮“代码事实 → skill 文档 → 下一步上下文 → GitHub 同步”收尾；收口 workflow 部门化、执行历史查看器、records 临时页角色定位与当前环境残留问题

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
- M4 模型主链已继续向真实 AI 收口：统一 `LLMClient` 当前不再只服务 chat ask，而是已接入 `dialog_agent` 节点回复、`decision_agent.llm` 结构化决策，以及 `execution_agent.ai_select` 候选目标选择
- 当前 runtime 终态已额外回填 `dialog_outputs`，便于对话型节点在 execution 结果中保留节点级回复与选择痕迹
- 决策型智能体本轮已继续深开发：编译阶段开始校验 decision 节点三模式配置；运行时 `rule/model/llm` 三模式已从骨架推进到“规则阈值决策 / 候选动作评分 / AI 结构化决策”三条细化链路
- 前端决策型配置面板已继续深化：从简单三输入位升级为规则型、模型型、智能型分区配置；执行结果卡片也开始展示 `decision_outputs`
- 工作流查看区 → 制作区的恢复问题已定位并修复：workflow 卡片现在会携带 `workflowId` 进入制作区，`WorkflowCanvasPage.vue` 会自动加载对应 workflow 的最新 draft；若 draft 缺失则回退到 current release，已保存/已发布流程不再以空白画布打开
- 本轮已定位“只有感知输出、没有决策/执行输出”的真实原因：Records 自动触发命中的两个历史 workflow 当前 `ui_schema` 为空且 current release 仅残留单个 `sensor_agent` DAG；同时已验证一条真实三节点 workflow 在 source_system 对齐时可完整跑通 `sensor -> decision -> execution`
- 当前已补后端护栏：workflow 编译阶段开始阻止 `sensor_agent / decision_agent` 无下游边的假闭环发布；Mock Records 自动触发阶段开始跳过 `ui_schema.nodes` 为空的历史坏版本，避免旧残留发布版继续制造误判
- 已按用户要求撤回短标签显示试验：workflow / record / execution 重新回到与数据库原值一一对应的展示方式
- Records 居中执行结果视图已补 workflow 名称展示，并新增执行记录删除能力；删除后会同步清理 execution 主记录、checkpoint、审批任务，以及最近事件中的 execution 引用
- workflow 部门化第一批能力已开始落地：查看区支持按“部门 → 触发逻辑”两层分组；制作区增加 workflow 归属部门选择；workflow API 补显式部门作用域；执行型节点开始真实消费 `fixed_dept` 路由配置
- Records 居中弹窗的空“未触发 execution”结果块已移除，未触发事件不再额外占据一整块结果区域
- Records 原有“执行详情查看器”本轮已整体撤回；业务表格区重新只保留最近事件索引，不再在该页展开 execution 详情
- 工作流执行历史查看能力已落地到两个入口：工作流查看区可查看单条 workflow 的全量执行历史；对话区的部门 workflow 目录可查看当前部门下该 workflow 的执行历史，二者均按执行类型分类展示“执行任务 / 执行对象 / 执行时间”
- 本轮收尾同步已完成第一批清理：`progress-tracker` 的过期“下一步”已大幅裁剪；RecordsWorkbench 残留 workflow 拉取已移除；`AttachmentPanel.vue` 已删除；`useExecutionStream` 轮询兜底已补错误保护
- 本轮按最新反馈继续收口：业务表格区右侧最近事件流已改为仅展示“已触发 workflow”的卡片；工作流制作区已补显式“新建工作流”按钮；mock 注入改为“先返回 execution_id、后台继续执行”，后端会逐节点提交 `current_node`，画布可真实显示运行态炫彩高亮；Python 服务已补 `.env.local/.env` 与 `GEMINI_PROXY_*` 兼容读取，避免对话区误报模型未配置
- 本轮继续推进 relay 联调：本地已补 `python-agent-service/.env.local` 持久化 Gemini 中转配置，后端已支持通过 `LLM_REQUEST_PATH` 在 `/chat/completions` 与 `/responses` 之间切换，前端 Vite 代理也可通过 `VITE_API_TARGET` 指向 8001 等干净实例
- 已用干净 8001 后端实例完成最小 relay 实测：`create session -> send message('你好')` 已返回真实 assistant 回复，确认 ChatWorkbench 主链不再落入 `LLM_NOT_CONFIGURED` fallback
- 工作流执行历史查看器已继续增强：历史项现在会显示执行结果摘要，可直接看到本次是否成功、写入到了哪个对象，以及实际写入的字段值，不再只有“执行任务 / 执行对象 / 执行时间”三块粗信息
- 已定位并修复“看起来停在 decision / history 无结果”的真实链路：问题不在 workflow DAG，而在 mock inject 的后台续跑实现与 `final_output` JSON 快照持久化；修复后同一条 workflow 已重新验证可跑通 `sensor -> decision -> execution`，并能正确写入 `sensor_outputs / decision_outputs / tool_outputs`
- 已定位并修复“业务表格区改了库存表却不触发 workflow”的来源匹配问题：RecordsWorkbench 发出的事件源为 `dayan_mock_records`，而许多流程配置为 `erp_prod`；后端现已增加 `dayan_mock_records <-> erp_prod` 兼容匹配，库存表更新可直接触发这类正式 ERP 风格的感知流程

## 进行中模块
- 感知型智能体详细设计（数据库实时感知优先）
- 决策型智能体详细设计（三种决策模式）
- 执行型智能体详细设计（对话审批、结果回传、部门表格执行对象、跨部门结果投递）
- 对话型智能体详细设计（部门化路由、workflow 目录、选流与触发主链）
- 对话型智能体详细设计（部门对话框消息回流、审批与执行结果在消息流中的呈现细化）
- 监控型智能体详细设计（独立监控工作台、非画布节点）
- 独立 Mock 业务库与临时业务表格测试工作台详细设计
- 控制节点详细设计（定义先行，开发后置）
- workflow 部门化与执行历史查看能力已进入“功能完成，等待权限/分页/竞态等加固”阶段
- 本地运行环境治理（旧监听、端口冲突、热重载不一致）仍待继续收口
- 对话区中转 API 连通性已从“仅依赖进程环境”调整为“进程环境 + 本地 env 文件 + gemini proxy 别名兼容”，仍需在实际运行环境补入真实 key/base_url 后再做最终联调确认
- 本地 relay 配置当前已在 `python-agent-service/.env.local` 落地；但默认 8000 端口仍可能命中旧监听，因此网页实测时优先使用干净 8001 后端实例
- 浏览器开发态页面当前已能打开 `chat-workbench` 并发送消息；由于 8000 旧监听仍未清理，后续若恢复默认代理口径前仍建议继续使用 8001 干净实例做 relay 联调
- workflow 历史弹窗的信息密度已进一步提升，但当前仍以单条摘要为主；若后续要支持复杂多节点执行结果逐项展开，可能需要继续拆明细弹层或折叠区
- 决策型 llm 节点当前仍可能耗时 10~20 秒才进入 execution，这属于真实网关延迟而非“停死”；当前画布与 execution 查询应继续以 `running -> decision -> execution -> finished` 的渐进过程解释给配置员
- 感知来源元数据当前已新增 `dayan_mock_records` 选项，用于在制作区明确表示“业务表格区临时测试源”；但为兼容旧流程，运行时仍保留 `erp_prod` 与 `dayan_mock_records` 的双向兼容判断

## 未开始模块
- 感知型智能体 Go 事件接入实现
- 决策型智能体 rule/model/llm 三模式的进一步收口（补真实规则集来源、模型注册表/持久化参数、智能型 prompt registry 与 tool/RAG 深接）
- 执行型审批工作区细节增强（筛选、时间线、结果卡片联动）
- 执行型智能体目标注册表与 handler 实现
- 部门表格执行对象 adapter / executor 实现
- 部门表格写入幂等、防重复与失败回传实现
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
- 本机 8000 端口当前存在异常旧监听残留，导致最新 workflow 部门化 HTTP 行为无法稳定只命中新实例；干净 8001 实例已验证代码正确，但默认开发端口环境仍待清理

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
- `include_all`、`dept_id`、`owner_dept_id` 当前仍偏演示期口径，若不补后端权限闸，进入真实多部门联调时会出现跨部门可见性风险
- `result_target_dept_id` 当前仅落到配置和执行元数据，尚未真正接到 chat 回传部门决策，容易让配置员误以为跨部门结果投递已生效
- workflow 执行历史当前按 100 条硬限制返回且无分页元信息，后续若历史量增大会影响可用性与解释性
- 画布运行态高亮当前依赖 `execution_runs.current_node` 的逐步提交；若后续执行链切到独立 worker / 队列消费，需要同步维护等价的节点状态推送口径，避免高亮重新退化为终态展示

## 下一步
- 为 `include_all / dept_id / owner_dept_id` 增加后端权限闸，收口 workflow 查看区与执行历史查询的跨部门可见性
- 将 `result_target_dept_id` 真正接入对话结果回传链路，完成“执行结果投递到指定部门对话框”的闭环
- 为 workflow 执行历史接口补分页或至少显式截断元信息，并补前端请求竞态保护
- 清理本机默认开发端口 8000 的异常旧监听，恢复“代码与 HTTP 行为一致”的单实例环境
- 继续推进 `sensor_event_inbox / sensor_subscriptions` 持久化订阅链，以及 `sensor-metadata` 向真实 Go/数据库元数据来源收口
- 补齐 `department_table` 的真实 route registry、权限/幂等校验、审批恢复后单次写入验证与契约测试
- 继续推进对话型智能体：候选 workflow 歧义消解、参数补齐、审批恢复卡片与消息流结构化结果展示
- 准备 M5 收口前置项：监控 incident 模型、执行列表/异常统计、以及关键 execution 主链的契约/集成测试
- 在已补 `.env.local/.env` 读取后，用真实 Gemini 中转配置重新验证 ChatWorkbench 的 ask 路径，确认不再落入 `LLM_NOT_CONFIGURED` fallback
- 在 8000 旧监听彻底清理后，把前端默认代理目标重新收回单实例开发口径，避免每次联调都依赖 `VITE_API_TARGET`
- 继续观察 workflow 执行历史里“多节点、多次写入”的展示需求；若单条 history item 同时包含多个 tool output，后续需要从“首条结果摘要”升级为“多结果列表”
- 若后续仍出现“status 已 finished 但 history/tool_outputs 为空”，优先排查是否存在未重启后端实例吃到旧代码，而不是先怀疑 workflow 配置本身
- 后续若要彻底去掉兼容分支，应统一 `sensor_metadata.py` 与 RecordsWorkbench 真实发出的 `source_system` 命名，不再让 `erp_prod` 与 `dayan_mock_records` 双轨并存

## 文档同步状态
- 本轮已重点复核并再次同步：`progress-tracker.md`（补 workflow 历史结果增强、relay 联调状态与 mock inject/runtime 修复事实）、`frontend-code-structure.md`（补执行历史结果展示口径）、`python-service-api.md`（补 workflow history 新增结果字段与 mock inject 持久化规则）、`python-environment-config.md`（补 relay 请求路径切换与前端代理目标切换）、`third-party-dependencies.md`（补 OpenAI-compatible relay Chat/Responses 口径）、`change-log.md`（补本轮实现留痕）
- 本轮已重点复核并再次同步：`progress-tracker.md`（补业务表格区触发兼容修复）、`frontend-code-structure.md`（补表格区触发正式 ERP 风格流程的兼容口径）、`python-service-api.md`（补表格区 source_system 兼容规则）、`python-environment-config.md`（补 relay 请求路径切换与前端代理目标切换）、`third-party-dependencies.md`（补 OpenAI-compatible relay Chat/Responses 口径）、`change-log.md`（补本轮实现留痕）
- 其余已在前几轮同步过且本轮未发生事实变化的 references，本轮不再重复改写
