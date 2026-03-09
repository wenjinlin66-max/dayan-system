import argparse
import importlib
import json
import shutil
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Maxwell automation execution")
    parser.add_argument("--project", required=True, help="Path to .aedt project")
    parser.add_argument("--design", required=True, help="Design name")
    parser.add_argument("--setup", required=True, help="Setup name")
    parser.add_argument("--out", default="results/maxwell-mcp-run", help="Output directory")
    parser.add_argument("--execute", action="store_true", help="Actually execute solve")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    variables = {
        "turns": "12",
        "coil_gap_cm": "6cm",
        "f_op": "85kHz",
        "wire_d_mm": "1.2mm",
    }
    exports = ["L1", "L2", "M", "k"]

    status = {
        "ok": False,
        "project": args.project,
        "design": args.design,
        "setup": args.setup,
        "executed": False,
        "message": "not started",
    }

    try:
        source_project = Path(args.project)
        run_project = out_dir / f"{source_project.stem}_autorun.aedt"
        shutil.copy2(source_project, run_project)

        source_results = source_project.with_suffix(source_project.suffix + "results")
        run_results = run_project.with_suffix(run_project.suffix + "results")
        if source_results.exists():
            if run_results.exists():
                shutil.rmtree(run_results)
            shutil.copytree(source_results, run_results)
            for p in list(run_results.rglob("*.semaphore")) + list(run_results.rglob(".*.semaphore")):
                try:
                    p.unlink()
                except Exception:
                    pass

        maxwell_module = importlib.import_module("ansys.aedt.core")
        Maxwell3d = getattr(maxwell_module, "Maxwell3d")

        app = Maxwell3d(
            project=str(run_project),
            design=args.design,
            solution_type="EddyCurrent",
            version="2023.1",
            non_graphical=True,
            new_desktop=True,
            remove_lock=True,
        )

        for key, val in variables.items():
            app[key] = val

        if args.execute:
            run_ok = bool(app.analyze_setup(args.setup))
            status["executed"] = run_ok
            if run_ok:
                status["ok"] = True
                status["message"] = "maxwell setup solved successfully"
            else:
                status["ok"] = False
                status["message"] = "maxwell setup solve returned false (check model/setup completeness)"
        else:
            status["ok"] = True
            status["executed"] = False
            status["message"] = "maxwell session created and variables applied"
        status["run_project"] = str(run_project)

        # Save a lightweight run manifest for thesis traceability.
        pd.DataFrame(
            [{"name": k, "value": v} for k, v in variables.items()]
        ).to_csv(out_dir / "variable_snapshot.csv", index=False)

        pd.DataFrame(
            [{"export_name": e, "status": "pending_manual_report_binding"} for e in exports]
        ).to_csv(out_dir / "requested_exports_manifest.csv", index=False)

        app.save_project()
        app.release_desktop(close_projects=True, close_desktop=True)

    except Exception as exc:
        status["ok"] = False
        status["message"] = str(exc)

    with (out_dir / "maxwell_run_status.json").open("w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print(f"Saved: {out_dir / 'maxwell_run_status.json'}")
    if (out_dir / "variable_snapshot.csv").exists():
        print(f"Saved: {out_dir / 'variable_snapshot.csv'}")
    if (out_dir / "requested_exports_manifest.csv").exists():
        print(f"Saved: {out_dir / 'requested_exports_manifest.csv'}")


if __name__ == "__main__":
    main()
