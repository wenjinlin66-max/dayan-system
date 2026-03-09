import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Segmented Maxwell pipeline: build -> validate/fix -> solve")
    parser.add_argument("--input-csv", required=True, help="Input csv for precompute stage")
    parser.add_argument("--blueprint", required=True, help="Blueprint yaml")
    parser.add_argument("--run-tag", default="agv_hex_segmented", help="Run tag prefix")
    parser.add_argument("--run-root", default="results/runs", help="Run root")
    parser.add_argument("--max-fix-passes", type=int, default=2)
    parser.add_argument("--max-solve-retries", type=int, default=3)
    parser.add_argument("--reuse-project-direct", action="store_true", help="Skip auto-build copy and run validate/solve directly on blueprint project")
    return parser.parse_args()


def run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def kill_ansys_processes() -> None:
    subprocess.run(["cmd", "/c", "taskkill /F /IM ansysedt.exe"], capture_output=True, text=True)


def cleanup_stale_locks(run_project: Path) -> list[str]:
    removed = []
    lock_file = run_project.with_suffix(run_project.suffix + ".lock")
    if lock_file.exists():
        lock_file.unlink(missing_ok=True)
        removed.append(str(lock_file))

    results_dir = run_project.with_suffix(run_project.suffix + "results")
    if results_dir.exists():
        for pat in ["*.semaphore", "*.lock", ".*.semaphore", ".*.lock"]:
            for p in results_dir.rglob(pat):
                try:
                    p.unlink()
                    removed.append(str(p))
                except Exception:
                    pass
    return removed


def main() -> None:
    args = parse_args()
    workspace = Path(__file__).resolve().parents[4]
    run_id = f"{args.run_tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = workspace / args.run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    p01 = run_dir / "01_precompute"
    p03 = run_dir / "03_auto_build"
    p04 = run_dir / "04_validate_fix"
    p05 = run_dir / "05_solve"
    p07 = run_dir / "07_summary"
    for p in [p01, p03, p04, p05, p07]:
        p.mkdir(parents=True, exist_ok=True)

    scripts = workspace / ".opencode/skills/maxwell-mcp-automation/scripts"
    preprocess = scripts / "preprocess_from_pdf_assumptions.py"
    autobuild = scripts / "auto_build_and_repair.py"
    validate_fix = scripts / "validate_autofix_loop.py"
    solve_script = scripts / "run_maxwell_execution.py"

    blueprint = Path(args.blueprint)
    if not blueprint.is_absolute():
        blueprint = workspace / blueprint

    with blueprint.open("r", encoding="utf-8") as f:
        bp = yaml.safe_load(f)

    manifest = {
        "run_id": run_id,
        "blueprint": str(blueprint),
        "steps": [],
    }

    code, out, err = run_cmd(
        [sys.executable, str(preprocess), "--input-csv", str(workspace / args.input_csv), "--out", str(p01)],
        workspace,
    )
    (p07 / "precompute_stdout.log").write_text(out, encoding="utf-8")
    (p07 / "precompute_stderr.log").write_text(err, encoding="utf-8")
    manifest["steps"].append({"name": "precompute", "code": code})

    kill_ansys_processes()

    if args.reuse_project_direct:
        run_project = Path(bp["project_path"])
        if not run_project.is_absolute():
            run_project = workspace / run_project
        manifest["steps"].append({"name": "build_only", "code": 0, "note": "skipped by --reuse-project-direct"})
    else:
        code, out, err = run_cmd(
            [
                sys.executable,
                str(autobuild),
                "--blueprint",
                str(blueprint),
                "--out",
                str(p03),
                "--max-fix-passes",
                str(args.max_fix_passes),
                "--max-solve-retries",
                str(args.max_solve_retries),
            ],
            workspace,
        )
        (p07 / "build_stdout.log").write_text(out, encoding="utf-8")
        (p07 / "build_stderr.log").write_text(err, encoding="utf-8")
        manifest["steps"].append({"name": "build_only", "code": code})

        auto_status_path = p03 / "auto_build_status.json"
        auto_status = json.loads(auto_status_path.read_text(encoding="utf-8")) if auto_status_path.exists() else {}
        run_project = Path(auto_status.get("run_project", p03 / "AGV_WPT_Base_auto_build.aedt"))
        if not run_project.is_absolute():
            run_project = workspace / run_project

    kill_ansys_processes()
    removed = cleanup_stale_locks(run_project)
    (p07 / "lock_cleanup.json").write_text(json.dumps({"removed": removed}, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["steps"].append({"name": "cleanup_locks", "removed": len(removed)})

    code, out, err = run_cmd(
        [
            sys.executable,
            str(validate_fix),
            "--project",
            str(run_project),
            "--design",
            str(bp["design_name"]),
            "--setup",
            str(bp["setup_name"]),
            "--blueprint",
            str(blueprint),
            "--out",
            str(p04),
            "--max-iterations",
            "6",
            "--session-retries",
            "2",
            "--retry-wait-s",
            "3",
            "--non-graphical",
        ],
        workspace,
    )
    (p07 / "validate_fix_stdout.log").write_text(out, encoding="utf-8")
    (p07 / "validate_fix_stderr.log").write_text(err, encoding="utf-8")
    manifest["steps"].append({"name": "validate_fix", "code": code})

    kill_ansys_processes()
    removed2 = cleanup_stale_locks(run_project)
    manifest["steps"].append({"name": "cleanup_locks_2", "removed": len(removed2)})

    code, out, err = run_cmd(
        [
            sys.executable,
            str(solve_script),
            "--project",
            str(run_project),
            "--design",
            str(bp["design_name"]),
            "--setup",
            str(bp["setup_name"]),
            "--out",
            str(p05),
            "--execute",
        ],
        workspace,
    )
    (p07 / "solve_stdout.log").write_text(out, encoding="utf-8")
    (p07 / "solve_stderr.log").write_text(err, encoding="utf-8")
    manifest["steps"].append({"name": "solve_only", "code": code})

    manifest_path = p07 / "segmented_run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {manifest_path}")
    print(f"Run folder: {run_dir}")


if __name__ == "__main__":
    main()
