import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Chinese solve diagnostic report")
    parser.add_argument("--run-dir", required=True, help="Run directory containing 03_auto_build/05_solve")
    return parser.parse_args()


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)

    auto_build = read_json(run_dir / "03_auto_build" / "auto_build_status.json")
    solve = read_json(run_dir / "05_solve" / "solve_status.json")
    readiness = read_json(run_dir / "04_readiness" / "readiness_from_autobuild.json")

    ok_to_solve = readiness.get("ok_to_solve", False)
    mesh_ops = readiness.get("mesh_ops_count", 0)
    executed = solve.get("executed", False)
    message = solve.get("message", "")
    attempts = solve.get("solve_attempts", [])

    causes = []
    if ok_to_solve and not executed:
        causes.append("模型结构已满足最小可解条件，但求解返回 false，通常是求解设置/激励强度/网格质量导致。")
    if mesh_ops == 0:
        causes.append("当前未设置显式网格加密（mesh_ops_count=0），建议先对线圈附近加密网格。")
    if "returned false" in message.lower():
        causes.append("Setup 执行返回 false，建议在 AEDT Message Manager 查看具体报错并补充约束。")
    if isinstance(attempts, list) and len(attempts) > 1 and not executed:
        causes.append("自动重试后仍失败，建议重点检查激励定义与局部网格策略是否被有效应用。")

    actions = [
        "在线圈邻域添加局部网格加密后重跑 Setup1。",
        "检查激励边界 J_TX/J_RX 的方向和幅值是否合理。",
        "确认 Setup1 频率字段与 f_op 一致（85kHz）。",
        "执行一次手工 Validate 检查并查看 Message Manager 详细错误。",
        "若仍失败，先只保留 tx/rx + air_region 做最小工况求解，再逐步增加复杂度。",
    ]

    lines = [
        "# 求解失败中文诊断报告",
        "",
        f"- 运行目录：`{run_dir}`",
        f"- readiness ok_to_solve：`{ok_to_solve}`",
        f"- solve executed：`{executed}`",
        f"- solve message：`{message}`",
        f"- solve attempts：`{len(attempts) if isinstance(attempts, list) else 0}`",
        "",
        "## 可能原因（按优先级）",
        "",
    ]

    if causes:
        lines.extend([f"- {c}" for c in causes])
    else:
        lines.append("- 暂未识别明确原因，请检查日志与Message Manager。")

    lines.extend(["", "## 建议处理步骤", ""])
    lines.extend([f"- {a}" for a in actions])

    out = run_dir / "07_summary" / "求解失败中文诊断报告.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
