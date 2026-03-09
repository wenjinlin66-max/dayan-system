import argparse
import importlib
import json
import shutil
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build minimal solvable trial from array model")
    parser.add_argument("--project", required=True, help="Source .aedt project")
    parser.add_argument("--design", default="AGV_WPT_Base", help="Design name")
    parser.add_argument("--setup", default="Setup1", help="Setup name")
    parser.add_argument("--out", default="results/agv_pdf_run/minimal_trial", help="Output folder")
    return parser.parse_args()


def _delete_boundary(app, name: str) -> bool:
    if hasattr(app, "delete_boundary"):
        try:
            return bool(app.delete_boundary(name))
        except Exception:
            pass
    try:
        app.oboundary.DeleteBoundaries([name])
        return True
    except Exception:
        pass
    for b in list(getattr(app, "boundaries", [])):
        if getattr(b, "name", "") == name:
            try:
                return bool(b.delete())
            except Exception:
                return False
    return False


def _face_with_max_z(obj):
    best = None
    best_z = -1e18
    for f in obj.faces:
        try:
            c = f.center
            if c[2] > best_z:
                best = f
                best_z = c[2]
        except Exception:
            continue
    return best


def _face_with_min_z(obj):
    best = None
    best_z = 1e18
    for f in obj.faces:
        try:
            c = f.center
            if c[2] < best_z:
                best = f
                best_z = c[2]
        except Exception:
            continue
    return best


def _face_extreme_x(obj, want_max: bool):
    best = None
    bx = -1e18 if want_max else 1e18
    for f in obj.faces:
        try:
            x = f.center[0]
        except Exception:
            continue
        if (want_max and x > bx) or ((not want_max) and x < bx):
            bx = x
            best = f
    return best


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    source_project = Path(args.project)
    trial_project = out_dir / f"{source_project.stem}_minimal_trial.aedt"
    shutil.copy2(source_project, trial_project)

    core = importlib.import_module("ansys.aedt.core")
    Maxwell3d = getattr(core, "Maxwell3d")

    app = None
    status = {
        "ok": False,
        "project": str(trial_project),
        "design": args.design,
        "setup": args.setup,
        "actions": [],
        "validate_simple": False,
        "analyze": False,
        "message": "",
    }

    for open_attempt in range(1, 4):
        try:
            app = Maxwell3d(
                project=str(trial_project),
                design=args.design,
                solution_type="EddyCurrent",
                version="2023.1",
                non_graphical=True,
                new_desktop=True,
                remove_lock=True,
            )
            break
        except Exception as exc:
            status["actions"].append(f"open_attempt_{open_attempt} failed: {exc}")
            if open_attempt == 3:
                raise
            time.sleep(2)

    try:
        if app is None:
            raise RuntimeError("failed to open project session")

        tx_name = "tx_hex_r1_c1"
        rx_name = "rx_hex_r1_c1"

        for b in list(app.boundaries):
            name = str(getattr(b, "name", ""))
            btype = str(getattr(b, "type", ""))
            if name.startswith("J_TX") or name.startswith("J_RX") or "CurrentDensity" in btype:
                if _delete_boundary(app, name):
                    status["actions"].append(f"removed {name}")

        air = app.modeler["air_region"]
        x_min = min([f.center[0] for f in air.faces if f.center is not None])
        x_max = max([f.center[0] for f in air.faces if f.center is not None])

        for coil_name, lead_name, direction in [
            (tx_name, "lead_tx_min", "left"),
            (rx_name, "lead_rx_min", "right"),
        ]:
            coil = app.modeler[coil_name]
            if direction == "left":
                face = _face_extreme_x(coil, want_max=False)
                if face is None:
                    raise RuntimeError(f"failed to locate left face for {coil_name}")
                c = face.center
                lead_len = c[0] - x_min
                if lead_len <= 0:
                    lead_len = 20
                app.modeler.create_box(
                    origin=[x_min, c[1] - 1, c[2] - 1],
                    sizes=[lead_len, 2, 2],
                    name=lead_name,
                    material="copper",
                )
            else:
                face = _face_extreme_x(coil, want_max=True)
                if face is None:
                    raise RuntimeError(f"failed to locate right face for {coil_name}")
                c = face.center
                lead_len = x_max - c[0]
                if lead_len <= 0:
                    lead_len = 20
                app.modeler.create_box(
                    origin=[c[0], c[1] - 1, c[2] - 1],
                    sizes=[lead_len, 2, 2],
                    name=lead_name,
                    material="copper",
                )
            app.modeler.unite([coil_name, lead_name])
            status["actions"].append(f"created+united {lead_name} with {coil_name}")

        app.assign_current_density(
            [tx_name],
            current_density_name="J_TX_MIN",
            current_density_x="0",
            current_density_y="0",
            current_density_z="1A_per_meter_sq",
            coordinate_system="Global",
            coordinate_system_type="Cartesian",
        )
        app.assign_current_density(
            [rx_name],
            current_density_name="J_RX_MIN",
            current_density_x="0",
            current_density_y="0",
            current_density_z="-1A_per_meter_sq",
            coordinate_system="Global",
            coordinate_system_type="Cartesian",
        )
        status["actions"].append("assigned J_TX_MIN and J_RX_MIN")

        for coil_name, term_name, direction in [
            (tx_name, "JT_TX_MIN", "left"),
            (rx_name, "JT_RX_MIN", "right"),
        ]:
            target_face = _face_extreme_x(app.modeler[coil_name], want_max=(direction == "right"))
            if target_face is None:
                raise RuntimeError(f"failed to locate terminal face for {coil_name}")
            app.assign_current_density_terminal([target_face.id], current_density_name=term_name)
            status["actions"].append(f"assigned terminal {term_name}")

        status["validate_simple"] = bool(app.validate_simple())
        try:
            status["analyze"] = bool(app.analyze_setup(args.setup))
        except Exception as exc:
            status["message"] = f"analyze error: {exc}"

        msgs = []
        try:
            raw = app.odesktop.GetMessages("", "", 0)
            if isinstance(raw, (list, tuple)):
                msgs = [str(x) for x in raw][-30:]
        except Exception:
            pass
        status["messages_tail"] = msgs

        status["ok"] = bool(status["validate_simple"] and status["analyze"])
        if not status["message"]:
            status["message"] = "minimal trial finished"

        app.save_project()
    except Exception as exc:
        status["ok"] = False
        status["message"] = str(exc)
    finally:
        if app is not None:
            try:
                app.release_desktop(close_projects=True, close_desktop=True)
            except Exception:
                pass

    with (out_dir / "minimal_trial_status.json").open("w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print(f"Saved: {out_dir / 'minimal_trial_status.json'}")
    print(f"ok={status['ok']} validate={status['validate_simple']} analyze={status['analyze']}")


if __name__ == "__main__":
    main()
