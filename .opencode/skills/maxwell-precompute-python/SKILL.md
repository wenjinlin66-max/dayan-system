---
name: maxwell-precompute-python
description: 在ANSYS Maxwell建模前后，使用Python完成理论计算、参数清洗、效率计算与论文级作图。适用于“把MATLAB步骤替换成Python”“根据Maxwell导出的L/M数据计算效率并绘图”“生成偏移-互感/耦合系数/效率曲线与三维图”等任务。
---

# Maxwell 建模前计算与作图（Python）

## 目标

把“建模前理论推导 + 建模后数据计算 + 论文作图”统一为 Python 流程，替代 MATLAB 手工计算。

## 输入

- Maxwell 导出数据（CSV，至少包含 `distance_cm` 与 `M_H`）
- 可选列：`L1_H`, `L2_H`, `x_cm`, `z_cm`
- 电路参数：`f_hz`, `R1_ohm`, `R2_ohm`, `Rload_ohm`
- 可选理论参数：`N_turns`, `I_amp`, `loop_radius_m`, `z_eval_m`
- 支持“原始列名自动识别”，无需手动改列名（含常见中文列名、`*_uH`、`*_mm`）。

## 输出

- `results/enriched_results.csv`（补齐 `k`, `efficiency_proxy`）
- `results/fig_m_vs_distance.png`
- `results/fig_k_vs_distance.png`
- `results/fig_eff_vs_distance.png`
- 若有 `x_cm` 与 `z_cm`：`results/fig_eff_surface.png`
- 若给理论参数：`results/theory_biot_savart.csv` 与 `results/fig_biot_savart.png`
- 论文图注：`results/figure_captions.md` 与 `results/figure_captions.csv`
- 自动生成论文编号图：`results/fig_<章号>_<序号>_*.png`

## 结果分类与标注（新增）

- 若由总流程调用，precompute 输出固定放到：
  - `results/runs/<run_tag>_<timestamp>/02_precompute`
- 至少保留以下标签文件：
  - `enriched_results.csv`（计算主结果）
  - `figure_captions.md`（论文图注）
  - `figure_captions.csv`（图编号映射）

## 工作流（固定）

### 1) 数据准备
- 使用 `references/sample_maxwell_data.csv` 对齐字段。
- 缺失必需字段时先补齐，再计算。

### 2) 参数计算
- 互感 `M` 直接读取（单位 H）。
- 耦合系数：`k = M / sqrt(L1 * L2)`（有 `L1_H`,`L2_H` 时计算）。
- 效率（代理模型）：
  - `w = 2*pi*f`
  - `efficiency_proxy = (w*M)^2 * Rload / ((R1*(R2+Rload) + (w*M)^2) * (R2+Rload))`
  - 结果裁剪到 `[0, 1]`。

### 3) 理论计算（可选）
- 单圆线圈轴线上磁感应强度（Biot-Savart）：
  - `B(z) = mu0 * N * I * R^2 / (2 * (R^2 + z^2)^(3/2))`
- 用于“第二章/第三章理论验证图”。

### 4) 论文作图
- 画 `distance_cm` 对 `M_H / k / efficiency_proxy` 的折线图。
- 有二维偏移网格时画 `x-z-效率` 三维曲面图。
- 图名、轴标签、网格统一，直接用于论文。

## 执行命令

```bash
python ".opencode/skills/maxwell-precompute-python/scripts/precompute_pipeline.py" --input ".opencode/skills/maxwell-precompute-python/references/sample_maxwell_data.csv" --out "results"
```

带理论曲线：

```bash
python ".opencode/skills/maxwell-precompute-python/scripts/precompute_pipeline.py" --input ".opencode/skills/maxwell-precompute-python/references/sample_maxwell_data.csv" --out "results" --calc-theory --turns 20 --current 5 --radius 0.1 --z-max 0.3
```

带论文图编号：

```bash
python ".opencode/skills/maxwell-precompute-python/scripts/precompute_pipeline.py" --input "maxwell_export.csv" --out "results" --fig-chapter 3 --fig-start 1
```

## 质量检查

- 是否生成 `enriched_results.csv`。
- 是否生成三张核心曲线图（M/k/效率）。
- 若有网格数据，是否生成三维曲面图。
- 若开启理论计算，是否生成 Biot-Savart 数据与曲线。

## 参考

- 字段说明：`references/input_schema.md`
- 示例数据：`references/sample_maxwell_data.csv`
