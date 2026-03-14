---
name: dayan-agent-system-orchestrator
description: 用于“大衍天工·多智能体协同系统”的项目总控与文档驱动开发治理。当用户围绕该项目讨论需求、架构、智能体设计、数据库设计、API/事件契约、实施步骤、开发进度、变更同步、GitHub 同步等事项时触发。该 skill 负责维护项目事实源文档，并在关键阶段主动引入测试治理 skill 做质量闸门检查。
---

# 大衍天工多智能体协同系统｜项目总控 Skill

## 概述

本 skill 是“大衍天工·多智能体协同系统”的项目总控中枢，负责将项目讨论、架构决策、技术方案、实施步骤与开发进度持续沉淀为结构化项目文档，并确保文档、方案、实施、GitHub 同步保持一致。

它是本项目的**默认执行入口**：凡进入实际开发、方案推进、模块变更、环境更新、联调、测试治理接入、GitHub 同步等执行性动作，默认优先通过本 skill 组织推进。

它不是一次性问答模板，而是长期陪跑的：
- 项目事实源维护器
- 架构推进器
- 开发计划管控器

核心目标：
- 把项目讨论沉淀为稳定文档，而不是停留在对话中
- 把需求、架构、数据库、契约、计划、进度统一管理
- 把“文档更新 -> 实施推进 -> 进度同步 -> GitHub 同步”形成闭环
- 在关键节点主动衔接测试治理 skill，形成质量门禁
- 前端界面设计默认参考 `frontend-design` skill，保证每轮前端迭代先对齐视觉与交互风格，再进入代码实现
- 日常多轮开发后的默认验证以 `webapp-testing` 打开前后端并进行网页交互验证为主，而不是每轮都立即执行单元测试 / pytest
- 明确工作流执行真相归 Python：工作流逻辑 JSON、版本、草稿/发布切换、执行 DAG 编译与运行均由 Python AI 中枢负责
- 确保每次执行方案后都更新项目进度与相关模块文档

## 触发条件

本 skill 采用“双层触发”机制。

### 1. 项目语境触发

仅在以下项目语境中优先触发：
- “大衍天工·多智能体协同系统”
- 多智能体协同平台
- Python 智能体中枢 + Go 数据底座协作系统
- 架构师画布工作台 / 员工对话工作台 / 运维监控工作台
- 感知型、决策型、执行型、对话型、监控型智能体
- 工作流节点、审批流、RAG、权限隔离、事件总线、审计、监控

### 2. 任务类型触发

当用户在该项目语境下提出以下任一任务时，优先触发本 skill：
- 新需求梳理、需求范围调整、优先级重排
- 系统架构设计、模块边界划分、目录结构规划
- 智能体体系设计、三级记忆设计、工作流编排设计
- 数据库设计、表结构设计、索引/约束/迁移策略设计
- API 契约、事件契约、错误码、鉴权规则设计
- 里程碑规划、实施步骤拆解、阶段目标定义
- 开发进度更新、已完成模块梳理、阻塞项维护
- 技术方案同步、实现方案同步、设计变更留痕
- GitHub 同步前后置检查要求

若进入“开始做 / 继续开发 / 执行下一步 / 搭骨架 / 更新模块 / 联调 / 修正方案”等执行性语境，也默认优先由本 skill 接管。

## 核心职责

本 skill 的职责必须与具体项目文档绑定，不允许只给抽象建议而不落到文档事实源。

1. **需求与范围冻结**：维护 `references/project-overview.md`
2. **系统架构与模块边界设计**：维护 `references/architecture.md`
3. **数据库设计**：维护 `references/database-design.md`
4. **API / 事件契约设计**：维护 `references/api-event-contracts.md`
5. **实施计划与里程碑编排**：维护 `references/implementation-plan.md`、`references/milestone-template.md`
6. **技术栈与关键决策追溯**：维护 `references/tech-decision-template.md`，必要时同步相关专题文档
7. **开发进度与完成状态同步**：维护 `references/progress-tracker.md`
8. **方案变更留痕**：维护 `references/change-log.md`
9. **GitHub 同步前后置治理**：维护 `checklists/doc-sync-checklist.md`、`checklists/github-sync-checklist.md`
10. **调用测试治理 Skill**：在关键阶段引入 `dayan-agent-system-test-governor`，获取质量门禁结果并纳入项目推进判断

## 不负责的边界

本 skill 不直接负责以下事项：
- 详细测试策略细则
- 回归测试门禁的最终判定
- 测试报告主体输出
- 与本项目无关的泛化架构咨询
- 脱离项目语境的一般性问答
- 将测试治理职责混入主 skill
- 以零散回答替代项目文档沉淀
- 在文档未同步的前提下直接推进新方案

测试相关事项应交由：
- `dayan-agent-system-test-governor`

## 默认维护的文档集合

### 核心事实源

- `references/project-overview.md`：项目背景、建设目标、范围与非目标、用户角色、核心使用模式、技术栈概览、里程碑概览、当前项目状态
- `references/architecture.md`：系统总架构、三大前端工作台、Go / Python 职责分工、五类智能体能力划分、工作流真相归属、流程控制节点模型、权限与数据隔离体系、三级记忆模型、监控与审计架构
- `references/database-design.md`：核心实体、字段定义、数据类型、必填/默认值、索引与唯一约束、关系设计、隔离策略、迁移策略与兼容策略
- `references/api-event-contracts.md`：HTTP API 契约、事件上行契约（Go -> Python）、事件下行/状态同步契约、工作流草稿与发布契约、审批卡片/审批回传契约、监控与审计契约、请求响应示例、错误码与鉴权规则、幂等策略与权限边界
- `references/go-python-contracts-v1.md`：Go 数据底座与 Python AI 中枢之间的正式数据、事件、执行、审批恢复、错误码与 Mock 协作契约总表
- `references/workflow-dsl.md`：工作流 JSON DSL、节点类型、边定义、节点配置结构、草稿编译规则、执行态约束
- `references/workflow-publish-state-machine.md`：Python 侧工作流从草稿到发布、废弃、沙盒测试、执行选择的状态机规则
- `references/python-service-api.md`：Python 智能体协同服务的分组 API、请求响应结构、鉴权与调用方边界
- `references/langgraph-runtime.md`：Python 执行器内部模块划分、LangGraph 状态模型、节点调度机制、handler 映射与异常恢复规则
- `references/memory-model.md`：上下文记忆、历史执行记忆、RAG 知识记忆三层接口、存储边界、权限过滤与调用方式
- `references/python-code-structure.md`：Python 智能体协同服务的推荐目录结构、模块职责与开发落位方式
- `references/frontend-code-structure.md`：Vue3 前端模块的推荐目录结构、共享层划分、与其他 Vue 模块的合并边界、以及画布/对话/监控三大工作台的前端落位方式
- `references/mock-records-architecture.md`：独立 Mock 业务数据库 `dayan_mock_records`、业务表格工作台、代码隔离边界，以及未来 Go 正式表格接入后的整体删除/回收方案
- `references/third-party-dependencies.md`：已确认或待确认的第三方基础设施、数据库扩展、模型 API、向量能力、前端库、消息队列、工具插件与可替换方案
- `references/environment-setup-checklist.md`：本地/测试环境落地前需要准备的数据库、Redis、模型密钥、对象存储、监控等外部资源与操作清单
- `references/python-environment-config.md`：Python 智能体协同服务的环境变量、配置分层、默认值与本地开发推荐配置

### 计划、追溯与模板

- `references/implementation-plan.md`：产品里程碑、阶段目标、阶段任务、依赖关系、风险点、验收口径、开发顺序建议
- `references/progress-tracker.md`：当前里程碑、当前阶段目标、已完成模块、进行中模块、未开始模块、阻塞项、风险项、下一步动作、文档同步状态
- `references/change-log.md`：变更主题、变更原因、影响范围、同步文档、是否影响数据库/契约/实施计划/测试、变更时间与说明
- `references/milestone-template.md`：统一里程碑拆解格式
- `references/tech-decision-template.md`：统一技术选型与关键决策记录格式

如需模板细节，按需读取上述 references 文件；不要把所有模板内容都塞进当前上下文。

## 默认执行主链（强制）

凡进入执行性工作，必须遵循以下主链；缺少任一步，视为未按项目主逻辑执行：

1. **定位阶段**：先依据 `references/implementation-plan.md` 判断当前所属阶段、目标与优先级
2. **按需读取**：再按当前任务类型读取必要的 `references/*` 文档，而不是把全部设计内容一次性塞入上下文
3. **基于事实执行**：按已确认的设计事实执行开发、搭建、联调或变更
4. **关键阶段引入测试治理**：若处于关键阶段，调用 `dayan-agent-system-test-governor`
5. **执行后回写**：执行完成后，回写 `references/progress-tracker.md` 与受影响的专题文档；若影响计划、变更或决策，连带更新对应文档

## 前端实现与验证附加规则（强制）

### 1. 前端设计默认参考
- 只要本轮任务涉及前端页面、组件、布局、交互、视觉风格、节点面板、工作台排布等内容，默认先参考 `frontend-design` skill 的风格方法再落代码
- 该参考不是“照搬样式”，而是要求在进入实现前先明确：页面目标、核心视觉方向、信息层级、交互重点、避免无意义按钮或装饰性控件
- 若用户给了截图、参考图或明确风格偏好，应优先把这些要求与 `frontend-design` 的实现方法合并，而不是仅做功能拼装

### 2. 每轮开发后的默认验证方式
- 每一轮日常开发完成后，默认**不自动执行单元测试**
- 每一轮日常开发完成后，默认**不自动执行 pytest**
- 若需要验证前后端联动、页面行为、交互流程、运行态展示，优先使用 `webapp-testing` skill：打开前端与后端，进行网页级交互测试与结果确认
- 对于前端多轮细化阶段，应优先采用“边开发边网页验证”的节奏，而不是每轮都跑完整测试套件

### 3. 单元测试 / pytest 的触发时机
- 单元测试与 pytest 不再作为每轮开发后的默认动作
- 只有在**累计完成很多轮开发**、或进入**较大阶段收口**、或用户明确要求进入测试收口时，才考虑集中执行单元测试 / pytest
- 在准备执行单元测试或 pytest 前，必须先明确询问用户：**是否要进行这一轮集中测试**
- 若用户未明确同意，则继续按实现 + 网页联调验证推进，不得擅自切换到大规模测试收口

## 工作流（按顺序执行）

### 第 1 步：识别任务类型

先判断当前输入属于：
- 新需求
- 需求变更
- 架构设计
- 数据库设计
- 契约设计
- 实施拆解
- 进度同步
- 变更留痕
- GitHub 同步前检查
- GitHub 同步后更新

如果当前输入带有“开始做 / 继续开发 / 实现 / 搭建 / 联调 / 修复 / 更新模块”等执行性语义，应优先回到 `references/implementation-plan.md` 确认当前阶段与任务归属。

### 第 2 步：定位应读取与应更新的文档

根据任务类型识别：
- 哪些 `references/*` 是本轮事实来源
- 哪些文档需要被更新

不允许只在对话中回答而不识别文档落点。常见映射：
- 数据库相关 → `references/database-design.md`
- 接口相关 → `references/api-event-contracts.md`
- 执行器相关 → `references/langgraph-runtime.md`
- 环境配置相关 → `references/python-environment-config.md`
- 前端模块相关 → `references/frontend-code-structure.md`

### 第 3 步：抽取新增事实与变更事实

必须区分：
- 新增内容
- 覆盖旧内容
- 补充旧内容
- 冲突内容
- 待确认假设

所有未明确的信息都必须标记为“假设”。读取 references 时遵循：
- 只读取与当前任务直接相关的文档
- 优先读取已有定案，而不是重复发明新方案
- 若某项事实已在 reference 中明确，不应再次用口头约定替代

### 第 4 步：同步项目文档

根据变更范围更新对应文档，保持项目事实源一致。

若本轮包含任何实际执行动作（如创建目录、搭骨架、补文档、调整结构、联调、部署环境），至少必须同步：
- `references/progress-tracker.md`
- 本轮实际影响到的主题文档

同时遵循以下规则：
- 若本轮执行参考了某个已有 reference 文档，并导致实现状态、约束、计划或模块边界发生变化，必须回写该 reference，而不是只更新进度
- 若本轮执行导致阶段任务、顺序、依赖、方法或验收标准发生变化，必须同步 `references/implementation-plan.md`
- 若本轮属于影响范围较大的变更，必须同步 `references/change-log.md`
- 若本轮涉及技术栈调整、架构边界调整、数据库结构变化、API / 事件契约变化、工作流发布机制变化、里程碑顺序变化，必须补充决策追溯
- 严禁把 `references/progress-tracker.md` 与 `references/change-log.md` 当作唯一同步目标；它们只负责“进度”和“留痕”，不能替代专题事实源
- 只要本轮已经形成新的稳定口径、交互规则、模块边界、实施形态或实现约束，就必须同步到对应的专题 reference（如 `frontend-code-structure.md`、`architecture.md`、`workflow-dsl.md`、`api-event-contracts.md`、`database-design.md` 等）
- 如果本轮新增的是“前端实际交互口径/页面结构约定”，默认至少同步：`references/frontend-code-structure.md`；若该交互影响阶段交付或验收口径，还必须同步 `references/implementation-plan.md`
- 如果本轮实现结果与原有 reference 不一致，必须优先修正文档事实源，再更新 `progress-tracker.md` 与 `change-log.md`，不得出现“实现已变、reference 仍是旧口径”的状态

### 第 5 步：若涉及实施，更新计划与进度

当方案进入可执行层面时，必须同步 `references/implementation-plan.md` 与 `references/progress-tracker.md`。

每次执行完成后，`references/progress-tracker.md` 至少维护以下字段：
- 当前里程碑
- 当前阶段目标
- 已完成模块
- 进行中模块
- 未开始模块
- 阻塞项
- 风险项
- 下一步动作
- 文档同步状态

如果本轮新增了模块、骨架、环境、依赖、接口、测试规则，也必须将其归入：
- 已完成模块
- 进行中模块
- 或未开始模块

### 第 6 步：若处于关键阶段，调用测试治理 skill

在以下场景必须接入 `dayan-agent-system-test-governor`：
1. 新模块设计完成后
2. 数据库 / API / 事件契约变化后
3. 某个里程碑准备收口时
4. 提交 / 发布前

补充执行规则：
- “接入测试治理 skill”用于获取质量门禁和风险视角，不等价于立刻执行单元测试 / pytest
- 在非收口阶段，即使接入了测试治理 skill，也应优先继续采用 `webapp-testing` 做前后端网页级验证
- 若判断需要集中执行单元测试 / pytest，仍必须先询问用户是否进入该测试轮次

若本轮讨论涉及以上任一场景，主 skill 不得直接给出“可以提交 / 可以发布 / 方案已完整”之类结论，而必须先引用测试治理 skill 的检查结果。

主 skill 调用测试治理 skill 时，至少应明确交代：
- 当前检查对象
- 当前里程碑或模块范围
- 最近变化的数据库 / API / 事件契约
- 需要重点检查的主链路

推荐在以下文件更新后立即引入测试治理 skill：
- `references/database-design.md`
- `references/api-event-contracts.md`
- `references/workflow-dsl.md`
- `references/workflow-publish-state-machine.md`
- `references/implementation-plan.md`

接收到测试治理结果后，必须：
1. 将“已覆盖项 / 缺失项 / 风险项 / 门禁结论”同步进当前决策上下文
2. 若门禁结论为“不通过”，不得推进到发布或完成结论
3. 若门禁结论为“有条件通过”，必须把条件写入实施计划、进度或变更记录
4. 若门禁结论为“通过”，才允许给出进入提交/发布阶段的建议

职责切分：
- 主 skill 负责：范围、架构、设计、实施、进度、发布节奏
- 测试治理 skill 负责：测试覆盖、契约风险、发布门禁、漏测项与质量结论
- 主 skill 不得替代测试治理 skill 给出门禁结论

### 第 7 步：若进入代码执行或同步阶段，检查 GitHub 前后置规则

GitHub 同步不是孤立动作，而是项目治理闭环的一部分。

#### 开发前必须检查

- 需求是否已沉淀
- 架构是否已同步
- 涉及的数据库 / API / 事件契约是否已更新
- 实施步骤是否已明确
- 文档与实现是否一致
- 若处于关键阶段，是否已请求测试治理 skill 做质量门禁检查

#### 开发后必须检查

- 实现方案与技术方案是否已同步
- 进度是否已更新
- 已完成模块是否已记录
- 是否产生新的变更记录

#### 主动同步触发条件

当出现以下任一情况时，主 skill 应主动执行 GitHub 同步，而不是等待额外提醒：
- 完成一个大型步骤
- 完成一个关键节点或关键模块开发
- 完成一次影响多份 reference 的关键修改
- 完成一个里程碑内的阶段性收口

同步前仍必须满足：
- 文档已同步
- `references/progress-tracker.md` 已更新
- 若需要门禁，则测试治理 skill 已给出结论
- 重要变更已写入 `references/change-log.md`

同步后必须：
- 将本次上传内容反映到 `references/progress-tracker.md`
- 若涉及方案变化，补写 `references/change-log.md`

## 技术决策记录规则

所有关键技术决策必须可追溯，至少记录以下内容：
- 决策主题
- 候选方案
- 每个候选方案的优点
- 每个候选方案的代价 / 风险
- 默认推荐
- 推荐理由
- 最终选择
- 放弃其他方案的原因
- 对架构、数据库、接口、实施计划的影响

适用场景包括但不限于：
- 前端技术栈
- 画布库选择
- Python 编排框架选择
- 工作流定义存储归属（Python 真相源）
- 工作流草稿/发布双模式
- 向量库 / 检索框架选择
- 事件总线方案
- 审批挂起与恢复机制
- 监控与审计方案

详细记录格式见：`references/tech-decision-template.md`

## 数据库 / API / 事件契约输出要求

### 数据库设计至少包含

- 表名 / 实体名
- 字段名
- 类型
- 是否必填
- 默认值
- 索引
- 唯一约束
- 关系说明
- 数据隔离字段（如 `dept_id` / `tenant_id`）
- 迁移策略

### API 契约至少包含

- 接口名称
- 路径
- 方法
- 鉴权要求
- 权限边界
- 作用对象（草稿 / 发布版 / 运行态）
- 请求体
- 响应体
- 错误码
- 幂等说明
- 示例

### 事件契约至少包含

- 事件名称
- 方向（Go -> Python / Python -> 前端 / 内部工作流事件）
- Topic / Channel / Queue
- 事件信封结构
- 关键业务字段
- `workflow_id / version / mode`（draft 或 released）
- 重试策略
- 死信策略
- 去重策略
- 安全与权限边界

### 工作流 DSL 至少包含

- `workflow_id`
- `version`
- `mode`（draft / released / sandbox）
- `ui_schema`
- `execution_dag`
- node 列表
- edge 列表
- `entrypoint`
- 节点配置 `schema_ref`
- 权限与部门范围
- 编译产物元信息

## references 使用规则

本 skill 的设计意图是：
- `SKILL.md` 负责总流程、总规则、默认执行主链
- `references/*` 负责事实、模板、专题设计与当前定案

因此，每次执行时应遵循：
1. 先从 `references/implementation-plan.md` 找当前阶段
2. 再按任务读取必要 reference
3. 尽量复用 reference 中已有事实，减少上下文重复消耗
4. 执行后把变化回写到对应 reference

## 用户反馈修正规则

在正式开发过程中，如果用户通过以下方式表达“不满意”或提出新效果要求：
- 截图标注
- 页面截图反馈
- 文字描述预期效果
- 直接指出“改成我想要的效果”
- 对当前步骤、页面、交互、文案、结构提出修正

主 skill 必须将其识别为“设计 / 实现修正输入”，而不是普通聊天反馈，并按以下闭环执行：
1. 先执行修正，达到新的目标效果
2. 判断修正影响的是哪一类文档：
   - `references/implementation-plan.md`
   - `references/progress-tracker.md`
   - `references/change-log.md`
   - 对应专题 reference
3. 将新口径同步写回文档

进一步约束：
- 如果用户反馈改变了原本步骤的目标、顺序、方法或验收标准，则必须同步 `references/implementation-plan.md`
- 如果用户反馈只改变了表现层效果，但会影响后续统一实现方式，也必须同步相关专题 reference，例如：
  - `references/frontend-code-structure.md`
  - `references/architecture.md`
  - `references/api-event-contracts.md`

结论：
- 用户反馈驱动的修正，不是临时补丁
- 修正完成后，必须把新效果回写进步骤与 reference

不得出现以下情况：
- 不看 `implementation-plan` 就直接进入开发
- 不读相关 reference 就重新口头设计
- 执行完成后只回答，不更新 reference
- 已有定案存在，却继续平行生成第二套口径

## 输出格式

默认输出顺序：
1. 当前任务归类
2. 本轮影响范围
3. 应更新的文档
4. 关键新增 / 变更内容
5. 若有，则附技术决策说明
6. 若有，则附实施计划变化
7. 若有，则附进度变化
8. 若需质量校验，则说明需引入测试治理 skill

输出风格要求：
- 以工程文档风为主
- 对关键架构决策补充业务解释
- 结论清晰
- 变更可追溯
- 避免空泛建议

## 质量检查清单

每次使用本 skill 后，至少自检以下内容：
- 是否仍处于本项目语境
- 是否识别了当前任务类型
- 是否定位了应维护的文档
- 是否把新增事实和假设区分开
- 是否同步了对应文档
- 是否记录了关键技术决策
- 是否同步了进度与计划
- 是否记录了变更影响
- 是否需要引入测试治理 skill
- 是否满足 GitHub 同步前后置要求

具体检查项见：
- `checklists/doc-sync-checklist.md`
- `checklists/github-sync-checklist.md`

## 目录与文件约定

本 skill 默认在自身目录下维护项目文档与检查清单：
- `references/`：项目事实源、设计文档、模板
- `checklists/`：执行前检查项、同步检查项
- `scripts/`：后续可扩展的自动化辅助脚本
- `SKILL.md`：主行为规则与调用说明

## 使用示例

```text
使用 skill: dayan-agent-system-orchestrator
请为大衍天工多智能体协同系统整理总需求，并输出三大工作台、五类智能体、流程控制节点的总体架构。
```

```text
/skill dayan-agent-system-orchestrator
请补全 Go 与 Python 之间的事件上行契约、审批唤醒契约、状态同步契约，并同步到项目文档。
```

```text
/skill dayan-agent-system-orchestrator
请把当前系统按里程碑拆成 M1~M5，并说明每个阶段的交付物、依赖关系和验收标准。
```

```text
/skill dayan-agent-system-orchestrator
请根据当前开发情况更新已完成模块、进行中模块、阻塞项和下一步计划，并同步文档。
```
