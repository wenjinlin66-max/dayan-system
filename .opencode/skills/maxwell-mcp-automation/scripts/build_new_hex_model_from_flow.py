import argparse
import importlib
import inspect
import json
import shutil
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a fresh Maxwell model from the user flow")
    parser.add_argument("--out", default="results/agv_pdf_run/fresh_model_build", help="Output directory")
    parser.add_argument("--project-name", default="AGV_WPT_Fresh_220mm_10turns", help="Project base name")
    parser.add_argument("--design", default="AGV_WPT_Fresh", help="Design name")
    parser.add_argument(
        "--source-project",
        default="results/agv_pdf_run/auto_build/AGV_WPT_Base_auto_build.aedt",
        help="Template project to copy before rebuilding",
    )
    parser.add_argument("--source-design", default="AGV_WPT_Base", help="Design name in template project")
    return parser.parse_args()


def _filter_kwargs(fn, kwargs: dict) -> dict:
    try:
        sig = inspect.signature(fn)
    except Exception:
        return kwargs
    params = sig.parameters
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return kwargs
    return {k: v for k, v in kwargs.items() if k in params}


def _assign_stranded(app, object_names: list[str], name: str, amp: str, phase: str, turns_expr: str, actions: list[str]) -> None:
    if not hasattr(app, "assign_current"):
        actions.append(f"failed {name}: assign_current API missing")
        return

    candidates = [
        {"amplitude": amp, "phase": phase, "solid": False, "swap_direction": False, "name": name, "number_of_conductors": turns_expr},
        {"amplitude": amp, "phase": phase, "solid": False, "swap_direction": False, "name": name, "conductors_number": turns_expr},
        {"amplitude": amp, "phase": phase, "solid": False, "swap_direction": False, "name": name, "conductor_number": turns_expr},
        {"amplitude": amp, "phase": phase, "solid": False, "swap_direction": False, "name": name},
    ]
    last = "unknown error"
    for kwargs in candidates:
        try:
            app.assign_current(object_names, **_filter_kwargs(app.assign_current, kwargs))
            actions.append(f"assigned stranded current {name} on {object_names}")
            return
        except Exception as exc:
            last = str(exc)
    actions.append(f"failed assign stranded {name}: {last}")


def _try_assign_matrix(app, srcs: list[str], actions: list[str]) -> None:
    if hasattr(app, "assign_matrix"):
        try:
            app.assign_matrix(srcs)
            actions.append(f"assigned matrix by API on {srcs}")
            return
        except Exception as exc:
            actions.append(f"assign_matrix API failed: {exc}")

    if hasattr(app, "oboundary") and hasattr(app.oboundary, "AssignMatrix"):
        try:
            app.oboundary.AssignMatrix(
                [
                    "NAME:Matrix",
                    "SourceNames:=",
                    srcs,
                    "GroundSources:=",
                    [],
                ]
            )
            actions.append(f"assigned matrix by oboundary on {srcs}")
            return
        except Exception as exc:
            actions.append(f"AssignMatrix failed: {exc}")
    else:
        actions.append("matrix assignment API unavailable")


def _try_add_parametric_sweep(app, setup_name: str, actions: list[str]) -> None:
    # offset_x: 0mm -> 150mm step 10mm
    opti = getattr(app, "ooptimetrics", None)
    if opti is not None and hasattr(opti, "InsertSetup"):
        try:
            opti.InsertSetup(
                "OptiParametric",
                [
                    "NAME:ParametricSetup1",
                    "IsEnabled:=",
                    True,
                    ["NAME:ProdOptiSetupDataV2", "SaveFields:=", False, "CopyMesh:=", False, "SolveWithCopiedMeshOnly:=", False],
                    ["NAME:StartingPoint"],
                    "Sim. Setups:=",
                    [setup_name],
                    [
                        "NAME:Sweeps",
                        [
                            "NAME:SweepDefinition",
                            "Variable:=",
                            "Offset_x",
                            "Data:=",
                            "LIN 0mm 150mm 10mm",
                            "OffsetF1:=",
                            False,
                            "Synchronize:=",
                            0,
                        ],
                    ],
                    ["NAME:Sweep Operations"],
                    ["NAME:Goals"],
                ],
            )
            actions.append("added ParametricSetup1 for Offset_x")
            return
        except Exception as exc:
            actions.append(f"parametric sweep creation failed: {exc}")
            return
    actions.append("parametric sweep API unavailable")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    src_project = Path(args.source_project)
    project_file = out_dir / f"{args.project_name}.aedt"
    shutil.copy2(src_project, project_file)
    status_path = out_dir / "fresh_build_status.json"
    actions: list[str] = []
    status = {
        "ok": False,
        "project": str(project_file),
        "design": args.source_design,
        "actions": actions,
        "message": "not started",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    app = None
    try:
        core = importlib.import_module("ansys.aedt.core")
        Maxwell3d = getattr(core, "Maxwell3d")

        app = Maxwell3d(
            project=str(project_file),
            design=args.source_design,
            solution_type="EddyCurrent",
            version="2023.1",
            non_graphical=True,
            new_desktop=True,
            remove_lock=True,
        )
        app.set_active_design(args.source_design)
        actions.append(f"active design {args.source_design}")

        try:
            names = list(app.modeler.object_names)
            if names:
                app.modeler.delete(names)
                actions.append(f"deleted existing objects: {len(names)}")
        except Exception as exc:
            actions.append(f"delete existing objects failed: {exc}")

        # Step 1/2: Units + variables
        try:
            app.modeler.model_units = "mm"
            actions.append("units=mm")
        except Exception as exc:
            actions.append(f"set units failed: {exc}")

        vars_map = {
            "D_coil": "220mm",
            "N_turns": "10",
            "Pitch": "240mm",
            "Gap": "50mm",
            "Offset_x": "0mm",
            "Wire_d": "2mm",
            "Coil_h": "4mm",
        }
        for k, v in vars_map.items():
            app[k] = v
            actions.append(f"var {k}={v}")

        # Step 3: Geometry
        r_expr = "(D_coil)/2"
        h_expr = "Coil_h"
        tx1 = app.modeler.create_cylinder("Z", ["0mm", "0mm", "0mm"], r_expr, h_expr, num_sides=6, name="TX1", material="copper")
        tx2 = app.modeler.create_cylinder("Z", ["Pitch", "0mm", "0mm"], r_expr, h_expr, num_sides=6, name="TX2", material="copper")
        tx3 = app.modeler.create_cylinder("Z", ["Pitch*cos(60deg)", "Pitch*sin(60deg)", "0mm"], r_expr, h_expr, num_sides=6, name="TX3", material="copper")
        rx = app.modeler.create_cylinder("Z", ["Offset_x", "0mm", "Gap"], r_expr, h_expr, num_sides=6, name="RX", material="copper")
        actions.append("created TX1/TX2/TX3/RX hex coils")

        ferrite = app.modeler.create_box(["-0.6*Pitch", "-0.6*Pitch", "-2mm"], ["2.2*Pitch", "2.2*Pitch", "2mm"], name="FerritePlate", material="ferrite")
        al = app.modeler.create_box(["-0.6*Pitch", "-0.6*Pitch", "-4mm"], ["2.2*Pitch", "2.2*Pitch", "2mm"], name="AlShield", material="aluminum")
        actions.append("created ferrite and aluminum plates")

        app.modeler.create_region([100, 100, 100, 100, 100, 100], pad_type="Percentage Offset", name="air_region")
        actions.append("created air_region")

        # Step 4: Excitation + matrix
        _assign_stranded(app, [tx1.name], "I_TX1", "20A", "0deg", "N_turns", actions)
        _assign_stranded(app, [tx2.name], "I_TX2", "20A", "0deg", "N_turns", actions)
        _assign_stranded(app, [tx3.name], "I_TX3", "20A", "0deg", "N_turns", actions)
        _assign_stranded(app, [rx.name], "I_RX", "20A", "180deg", "N_turns", actions)

        _try_assign_matrix(app, ["I_TX1", "I_TX2", "I_TX3", "I_RX"], actions)

        # Step 5: Setup + sweep
        setup_name = "Setup1"
        setup = app.create_setup(setup_name, setup_type="EddyCurrent")
        setup.props["Frequency"] = "85kHz"
        setup.props["MaximumPasses"] = 10
        try:
            setup.update()
        except Exception:
            pass
        actions.append("created Setup1 (85kHz, max_passes=10)")

        _try_add_parametric_sweep(app, setup_name, actions)

        app.save_project()
        actions.append("project saved")

        status["ok"] = True
        status["message"] = "fresh model built"
    except Exception as exc:
        status["ok"] = False
        status["message"] = str(exc)
    finally:
        if app is not None:
            try:
                app.release_desktop(close_projects=True, close_desktop=True)
            except Exception:
                pass

    with status_path.open("w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print(f"Saved: {status_path}")
    print(f"Project: {project_file}")
    print(f"ok={status['ok']} message={status['message']}")


if __name__ == "__main__":
    main()
