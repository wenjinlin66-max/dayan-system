# AGV_WPT Maxwell 自动化输入卡片（可直接复用）

## 已确认工程信息

```yaml
project_path: D:\MaxwellProjects\AGV_WPT_Base.aedt
design_name: AGV_WPT_Base
setup_name: Setup1
variables:
  turns: 12
  coil_gap_cm: 6cm
  f_op: 85kHz
  wire_d_mm: 1.2mm
exports: [L1, L2, M, k]
execution_mode: implement_only
```

## 使用方式（当前阶段：不执行真实求解）

```text
/skill maxwell-mcp-automation
按 references/agv_wpt_input_card.md 的工程参数，输出可执行的 Maxwell MCP 调用顺序与参数校验结果，保持 implement_only，不执行真实求解。
```

## 切换到真实执行前（必核对）

1. 路径 `D:\MaxwellProjects\AGV_WPT_Base.aedt` 可读写，且未被其他进程锁定。
2. Design 名称与 Setup 名称完全一致（区分大小写与空格）。
3. 许可证可用（`ANSYSLMD_LICENSE_FILE=1055@LAPTOP-DGVONA4D`）。
4. 若要执行求解，把 `execution_mode` 从 `implement_only` 改成 `execute`。
