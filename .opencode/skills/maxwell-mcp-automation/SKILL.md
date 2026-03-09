---
name: maxwell-mcp-automation
description: 用于为 ANSYS Maxwell 搭建可调用的自动化能力（MCP + Skill），包含环境配置、工具契约、错误处理、结果导出与执行清单。适用于“让AI自动建模调参仿真”“为Maxwell实现自动化工作流”“先实现不执行实际求解”的任务。
---

# Maxwell MCP 自动化实现技能

## 目标

把 Maxwell 自动化能力实现为可复用的 MCP + Skill 组合：
- 可控：统一的工具接口（开项目、设参数、求解、导出）
- 可验：每步有状态和错误码
- 可扩：后续可接入 AGV 工况矩阵批量仿真

## 当前已确认环境（来自用户）

- AEDT/Maxwell 目录：`D:\Program Files\AnsysEM\v231\Win64`
- 版本：`2023 R1`（v231）
- 许可证文件：`C:\Program Files\AnsysEM\v231\Win64\licensingclient\winx64\license.lic`
- License Server：`1055@LAPTOP-DGVONA4D`

## 执行策略（本阶段）

- 本阶段默认：**实现自动化能力，不执行真实求解任务**。
- 只完成：结构搭建、配置模板、接口定义、校验清单。
- 若用户明确要求执行，再进入“真实连接 Maxwell 并仿真”步骤。

## 实施流程

### 1) 环境配置固化
- 读取 `references/maxwell_env_template.env`。
- 把用户路径写入配置模板，保留 `non_graphical`、`transport` 等开关。

### 2) MCP 工具契约定义
- 读取 `references/mcp_tool_contract.md`。
- 固定 v1 工具：
  1. `health_check`
  2. `open_or_create_project`
  3. `set_design_variables`
  4. `run_setup`
  5. `export_results`

### 2.1) 拓扑参数化（新增）
- 支持 `topology = rectangular | hexagonal | circular`。
- 三种拓扑在同一变量集下可一键生成并用于同工况对比。

### 3) 错误与结果规范
- 工具响应必须返回：`ok`, `code`, `message`, `data`。
- 失败必须归类（license/path/version/timeout/export）。

### 4) 交付清单检查
- 读取 `references/implementation_checklist.md`。
- 每项完成后打勾，确保后续可进入真实执行阶段。

## 输出物

- Maxwell 自动化 Skill（本技能本身）
- 环境模板（可直接落地）
- MCP 工具契约（可直接编码）
- 实施检查单（可直接验收）

## 结果分类与标注（新增）

每次执行必须按“运行批次”分类归档，推荐目录：

- `results/runs/<run_tag>_<timestamp>/01_input`
- `results/runs/<run_tag>_<timestamp>/02_precompute`
- `results/runs/<run_tag>_<timestamp>/03_auto_build`
- `results/runs/<run_tag>_<timestamp>/04_readiness`
- `results/runs/<run_tag>_<timestamp>/05_solve`
- `results/runs/<run_tag>_<timestamp>/06_exports`
- `results/runs/<run_tag>_<timestamp>/07_summary`

并输出 `run_manifest.json`，包含：`run_id`、输入参数、各步骤状态码、失败位置、关键结果路径。

同时自动生成中文标注说明：

- 每个阶段目录生成 `中文标注说明.md`
- `07_summary` 生成 `中文结果总览.md`

## 使用方式

```text
/skill maxwell-mcp-automation
根据当前 Maxwell 安装路径与 license server，先实现自动化能力（MCP + Skill），暂不执行真实求解。
```

```text
/skill maxwell-mcp-automation
输出 v1 工具契约、配置模板和验收检查单，并标注下一步执行所需缺失信息。
```

```bash
python ".opencode/skills/maxwell-mcp-automation/scripts/full_pipeline_run.py" --input-csv "results/agv_pdf_run/input_from_pdf_assumed.csv" --blueprint ".opencode/skills/maxwell-mcp-automation/references/default_blueprint_from_pdf.yaml" --run-tag "agv_pdf" --execute-solve
```

三拓扑一键生成（同参数可比）：

```bash
python ".opencode/skills/maxwell-mcp-automation/scripts/build_topology_batch.py" --blueprint ".opencode/skills/maxwell-mcp-automation/references/default_blueprint_from_pdf.yaml" --out-root "results/topology_compare"
```
