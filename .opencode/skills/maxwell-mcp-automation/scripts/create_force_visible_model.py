import argparse
import importlib
import json
import shutil
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a force-visible Maxwell model copy")
    parser.add_argument("--project", required=True, help="Source .aedt project path")
    parser.add_argument("--design", required=True, help="Design name")
    parser.add_argument("--out", default="results/agv_pdf_run/auto_build", help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    source = Path(args.project)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = out_dir / f"{source.stem}_visible_{ts}.aedt"
    shutil.copy2(source, target)

    status = {
        "ok": False,
        "source_project": str(source),
        "visible_project": str(target),
        "design": args.design,
        "applied": [],
        "message": "not started",
    }

    app = None
    try:
        maxwell_module = importlib.import_module("ansys.aedt.core")
        Maxwell3d = getattr(maxwell_module, "Maxwell3d")

        app = Maxwell3d(
            project=str(target),
            design=args.design,
            solution_type="EddyCurrent",
            version="2023.1",
            non_graphical=True,
            new_desktop=True,
            remove_lock=True,
        )

        if args.design not in app.design_list:
            app.insert_design(args.design)
        app.set_active_design(args.design)

        modeler = app.modeler
        obj_names = set(modeler.object_names)

        if "tx_coil" in obj_names:
            tx = modeler["tx_coil"]
            tx.color = (255, 80, 80)
            tx.transparency = 0.1
            status["applied"].append("tx_coil color=red transparency=0.1")

        if "rx_coil" in obj_names:
            rx = modeler["rx_coil"]
            rx.color = (80, 160, 255)
            rx.transparency = 0.1
            status["applied"].append("rx_coil color=blue transparency=0.1")

        if "air_region" in obj_names:
            air = modeler["air_region"]
            air.color = (200, 200, 200)
            air.transparency = 0.9
            air.display_wireframe = True
            status["applied"].append("air_region color=gray transparency=0.9 wireframe=true")

        app.save_project()
        status["ok"] = True
        status["message"] = "force-visible copy generated"

    except Exception as exc:
        status["ok"] = False
        status["message"] = str(exc)
    finally:
        if app is not None:
            try:
                app.release_desktop(close_projects=True, close_desktop=True)
            except Exception:
                pass

    status_path = out_dir / "force_visible_status.json"
    with status_path.open("w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print(f"Saved: {status_path}")
    print(f"Visible model: {target}")


if __name__ == "__main__":
    main()
