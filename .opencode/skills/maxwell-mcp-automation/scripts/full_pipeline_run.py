import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run full classified AGV workflow pipeline")
    parser.add_argument("--input-csv", required=True, help="Input CSV for precompute")
    parser.add_argument("--blueprint", required=True, help="Blueprint YAML for Maxwell auto build")
    parser.add_argument("--run-tag", default="agv_full", help="Run tag label")
    parser.add_argument("--run-root", default="results/runs", help="Root folder for classified runs")
    parser.add_argument("--execute-solve", action="store_true", help="Execute Setup solve in auto build step")
    return parser.parse_args()


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def main() -> None:
    args = parse_args()
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(args.run_root) / f"{args.run_tag}_{now}"

    paths = {
        "01_input": run_dir / "01_input",
        "02_precompute": run_dir / "02_precompute",
        "03_auto_build": run_dir / "03_auto_build",
        "04_readiness": run_dir / "04_readiness",
        "05_solve": run_dir / "05_solve",
        "06_exports": run_dir / "06_exports",
        "07_summary": run_dir / "07_summary",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

    workspace = Path(__file__).resolve().parents[4]
    input_csv = Path(args.input_csv)
    if not input_csv.is_absolute():
        input_csv = workspace / input_csv
    blueprint = Path(args.blueprint)
    if not blueprint.is_absolute():
        blueprint = workspace / blueprint

    manifest = {
        "run_id": f"{args.run_tag}_{now}",
        "run_tag": args.run_tag,
        "started_at": now,
        "input_csv": str(input_csv),
        "blueprint": str(blueprint),
        "steps": [],
        "status": "running",
    }

    # Copy input metadata
    (paths["01_input"] / "inputs.json").write_text(
        json.dumps({"input_csv": str(input_csv), "blueprint": str(blueprint)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    precompute_script = workspace / ".opencode/skills/maxwell-precompute-python/scripts/precompute_pipeline.py"
    auto_build_script = workspace / ".opencode/skills/maxwell-mcp-automation/scripts/auto_build_and_repair.py"
    readiness_script = workspace / ".opencode/skills/maxwell-mcp-automation/scripts/maxwell_readiness_check.py"
    annotate_script = workspace / ".opencode/skills/maxwell-mcp-automation/scripts/annotate_run_outputs_cn.py"

    # Step 1: precompute
    precompute_out = paths["02_precompute"]
    cmd = [
        sys.executable,
        str(precompute_script),
        "--input",
        str(input_csv),
        "--out",
        str(precompute_out),
        "--fig-chapter",
        "3",
        "--fig-start",
        "1",
    ]
    code, out, err = run_cmd(cmd, workspace)
    manifest["steps"].append({"name": "precompute", "code": code})
    (paths["07_summary"] / "precompute_stdout.log").write_text(out, encoding="utf-8")
    (paths["07_summary"] / "precompute_stderr.log").write_text(err, encoding="utf-8")
    if code != 0:
        manifest["status"] = "failed_precompute"
        (paths["07_summary"] / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: {paths['07_summary'] / 'run_manifest.json'}")
        return

    # Step 2: auto build + optional solve
    auto_build_out = paths["03_auto_build"]
    cmd = [
        sys.executable,
        str(auto_build_script),
        "--blueprint",
        str(blueprint),
        "--out",
        str(auto_build_out),
    ]
    if args.execute_solve:
        cmd.append("--execute")

    code, out, err = run_cmd(cmd, workspace)
    manifest["steps"].append({"name": "auto_build", "code": code})
    (paths["07_summary"] / "auto_build_stdout.log").write_text(out, encoding="utf-8")
    (paths["07_summary"] / "auto_build_stderr.log").write_text(err, encoding="utf-8")
    if code != 0:
        manifest["status"] = "failed_auto_build"
        (paths["07_summary"] / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: {paths['07_summary'] / 'run_manifest.json'}")
        return

    auto_status_path = auto_build_out / "auto_build_status.json"
    auto_status = json.loads(auto_status_path.read_text(encoding="utf-8"))
    run_project = auto_status.get("run_project", "")
    run_project_path = Path(run_project)
    if not run_project_path.is_absolute():
        run_project_path = workspace / run_project_path

    # Step 3: readiness recheck
    readiness_out = paths["04_readiness"]
    cmd = [
        sys.executable,
        str(readiness_script),
        "--project",
        str(run_project_path),
        "--design",
        str(auto_status.get("design", "AGV_WPT_Base")),
        "--out",
        str(readiness_out),
    ]
    code, out, err = run_cmd(cmd, workspace)
    manifest["steps"].append({"name": "readiness_recheck", "code": code})
    (paths["07_summary"] / "readiness_stdout.log").write_text(out, encoding="utf-8")
    (paths["07_summary"] / "readiness_stderr.log").write_text(err, encoding="utf-8")

    readiness_report = readiness_out / "readiness_report.json"
    if readiness_report.exists():
        shutil.copy2(readiness_report, readiness_out / "readiness_from_autobuild.json")

    # Step 4: classify solve/export status
    solve_status = {
        "execute_requested": bool(args.execute_solve),
        "auto_build_ok": auto_status.get("ok", False),
        "executed": auto_status.get("executed", False),
        "ok": auto_status.get("ok", False),
        "message": auto_status.get("message", ""),
        "solve_attempts": auto_status.get("solve_attempts", []),
    }
    (paths["05_solve"] / "solve_status.json").write_text(json.dumps(solve_status, ensure_ascii=False, indent=2), encoding="utf-8")

    # Step 4b: copy real electromagnetic parameter exports when available
    export_files: list[str] = []
    for name in ["electromagnetic_parameters.csv", "electromagnetic_parameters.json"]:
        src = auto_build_out / name
        if src.exists():
            dst = paths["06_exports"] / name
            shutil.copy2(src, dst)
            export_files.append(str(dst))

    em_json = auto_build_out / "electromagnetic_parameters.json"
    em_payload = {}
    if em_json.exists():
        em_payload = json.loads(em_json.read_text(encoding="utf-8"))

    # Export classification marker
    exports_file = auto_build_out / "requested_exports.csv"
    if exports_file.exists():
        exp_df = pd.read_csv(exports_file)
        exports: dict[str, object] = {"exports": exp_df["export_name"].dropna().astype(str).tolist()}
    else:
        exports = {"exports": []}

    exports["status"] = em_payload.get("status", "manifest_only")
    exports["files"] = export_files
    exports["solve_ok"] = bool(auto_status.get("executed", False))
    (paths["06_exports"] / "export_manifest.json").write_text(json.dumps(exports, ensure_ascii=False, indent=2), encoding="utf-8")

    em = em_payload.get("parameters", {})
    explain_lines = [
        "# L1/L2/M/k 导出说明",
        "",
        f"- 来源：`{auto_build_out / 'electromagnetic_parameters.json'}`（若存在）",
        f"- 导出状态：`{exports.get('status', 'unknown')}`",
        "",
        "## 字段解释（来源/是什么/作用）",
        "",
        f"- L1(发射线圈自感)：来源={em.get('L1', {}).get('source_expression', '未提取')}；是什么=发射线圈等效自感；作用=用于计算耦合与匹配网络设计。",
        f"- L2(接收线圈自感)：来源={em.get('L2', {}).get('source_expression', '未提取')}；是什么=接收线圈等效自感；作用=用于补偿网络与负载耦合分析。",
        f"- M(互感)：来源={em.get('M', {}).get('source_expression', '未提取')}；是什么=发射与接收线圈磁耦合强度；作用=用于估算传能能力与系统增益。",
        f"- k(耦合系数)：来源={em.get('k', {}).get('source_expression', '未提取')}；是什么=无量纲耦合指标；作用=用于不同拓扑与间隙工况的横向比较。",
        "",
    ]
    (paths["07_summary"] / "L1L2Mk导出说明.md").write_text("\n".join(explain_lines), encoding="utf-8")

    # Step 5: generate Chinese annotations for all 7 folders
    cmd = [
        sys.executable,
        str(annotate_script),
        "--run-dir",
        str(run_dir),
    ]
    code, out, err = run_cmd(cmd, workspace)
    manifest["steps"].append({"name": "annotate_cn", "code": code})
    (paths["07_summary"] / "annotate_stdout.log").write_text(out, encoding="utf-8")
    (paths["07_summary"] / "annotate_stderr.log").write_text(err, encoding="utf-8")

    manifest["status"] = "completed" if code == 0 else "completed_with_annotation_warning"
    (paths["07_summary"] / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved: {paths['07_summary'] / 'run_manifest.json'}")
    print(f"Run folder: {run_dir}")


if __name__ == "__main__":
    main()
