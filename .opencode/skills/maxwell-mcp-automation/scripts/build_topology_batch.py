import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="One-click build of rectangular/hexagonal/circular comparable models")
    parser.add_argument("--blueprint", required=True, help="Base blueprint yaml")
    parser.add_argument("--out-root", default="results/topology_compare", help="Output root directory")
    parser.add_argument("--execute", action="store_true", help="Execute setup solve for each topology")
    parser.add_argument("--existing-run-dir", default="", help="Reuse existing topology batch directory and regenerate comparison report")
    return parser.parse_args()


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def _read_parameters(auto_build_dir: Path) -> dict:
    csv_path = auto_build_dir / "electromagnetic_parameters.csv"
    if not csv_path.exists():
        return {}

    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return {}

    out = {}
    for sym in ["L1", "L2", "M", "k"]:
        sub = df[df["symbol"].astype(str) == sym]
        if len(sub) == 0:
            out[sym] = None
            continue
        val = sub.iloc[0].get("value")
        try:
            out[sym] = float(val)
        except Exception:
            out[sym] = None
    return out


def main() -> None:
    args = parse_args()
    workspace = Path(__file__).resolve().parents[4]

    base_bp = Path(args.blueprint)
    if not base_bp.is_absolute():
        base_bp = workspace / base_bp

    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = workspace / out_root
    if args.existing_run_dir:
        run_dir = Path(args.existing_run_dir)
        if not run_dir.is_absolute():
            run_dir = workspace / run_dir
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = out_root / f"topology_batch_{run_tag}"
        run_dir.mkdir(parents=True, exist_ok=True)

    auto_build_script = workspace / ".opencode/skills/maxwell-mcp-automation/scripts/auto_build_and_repair.py"

    with base_bp.open("r", encoding="utf-8") as f:
        bp_data = yaml.safe_load(f)

    result_rows = []
    for topology in ["rectangular", "hexagonal", "circular"]:
        topo_dir = run_dir / topology
        topo_dir.mkdir(parents=True, exist_ok=True)

        code = 0
        if not args.existing_run_dir:
            topo_bp = dict(bp_data)
            topo_bp["topology"] = topology
            topo_bp_path = topo_dir / f"blueprint_{topology}.yaml"
            topo_bp_path.write_text(yaml.safe_dump(topo_bp, sort_keys=False, allow_unicode=True), encoding="utf-8")

            cmd = [
                sys.executable,
                str(auto_build_script),
                "--blueprint",
                str(topo_bp_path),
                "--out",
                str(topo_dir / "auto_build"),
            ]
            if args.execute:
                cmd.append("--execute")

            code, out, err = run_cmd(cmd, workspace)
            (topo_dir / "stdout.log").write_text(out, encoding="utf-8")
            (topo_dir / "stderr.log").write_text(err, encoding="utf-8")

        status_file = topo_dir / "auto_build" / "auto_build_status.json"
        status = {}
        if status_file.exists():
            status = json.loads(status_file.read_text(encoding="utf-8"))

        result_rows.append(
            {
                "topology": topology,
                "return_code": code,
                "ok": status.get("ok", False),
                "executed": status.get("executed", False),
                "message": status.get("message", ""),
                "run_project": status.get("run_project", ""),
            }
        )

    summary = {
        "run_dir": str(run_dir),
        "models": result_rows,
        "note": "rectangular/hexagonal/circular generated under same variable set for comparable runs",
    }

    compare_rows = []
    for row in result_rows:
        topo = row["topology"]
        params = _read_parameters(run_dir / topo / "auto_build")
        compare_rows.append(
            {
                "topology": topo,
                "ok": row["ok"],
                "executed": row["executed"],
                "L1_H": params.get("L1"),
                "L2_H": params.get("L2"),
                "M_H": params.get("M"),
                "k": params.get("k"),
                "message": row["message"],
            }
        )

    compare_dir = run_dir / "summary"
    compare_dir.mkdir(parents=True, exist_ok=True)
    compare_csv = compare_dir / "topology_compare.csv"
    compare_json = compare_dir / "topology_compare.json"
    pd.DataFrame(compare_rows).to_csv(compare_csv, index=False)
    compare_json.write_text(json.dumps(compare_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    ranked = [r for r in compare_rows if isinstance(r.get("k"), float)]
    ranked.sort(key=lambda x: x.get("k") if x.get("k") is not None else -1.0, reverse=True)
    if ranked:
        best = ranked[0]
        conclusion = f"同条件下耦合系数 k 最大的是 {best['topology']}，建议优先作为后续优化起点。"
    else:
        conclusion = "本批次尚未获得完整 k 数值，请先检查求解状态与导出链路。"

    md_lines = [
        "# 三拓扑同条件对比报告",
        "",
        f"- 运行目录：`{run_dir}`",
        "- 条件说明：三种拓扑使用同一份基础蓝图变量，仅几何拓扑不同。",
        "",
        "| 拓扑 | 求解完成 | L1(H) | L2(H) | M(H) | k | 备注 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in compare_rows:
        md_lines.append(
            f"| {r['topology']} | {r['executed']} | {r['L1_H']} | {r['L2_H']} | {r['M_H']} | {r['k']} | {r['message']} |"
        )
    md_lines.extend(["", "## 结论", "", f"- {conclusion}", ""])
    (compare_dir / "三拓扑对比报告.md").write_text("\n".join(md_lines), encoding="utf-8")

    summary["comparison_files"] = {
        "csv": str(compare_csv),
        "json": str(compare_json),
        "md": str(compare_dir / "三拓扑对比报告.md"),
    }
    (run_dir / "batch_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved: {run_dir / 'batch_summary.json'}")
    print(f"Run dir: {run_dir}")


if __name__ == "__main__":
    main()
