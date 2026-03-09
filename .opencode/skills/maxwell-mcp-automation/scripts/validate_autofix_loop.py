import argparse
import importlib
import json
import re
import time
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate + auto-fix loop for Maxwell project")
    parser.add_argument("--project", required=True, help="Path to .aedt project")
    parser.add_argument("--design", required=True, help="Design name")
    parser.add_argument("--setup", default="Setup1", help="Target setup name")
    parser.add_argument("--blueprint", default="", help="Optional blueprint yaml for excitation hints")
    parser.add_argument("--out", default="results/validate_autofix", help="Output directory")
    parser.add_argument("--version", default="2023.1", help="AEDT version")
    parser.add_argument("--max-iterations", type=int, default=6, help="Maximum validate-fix loops")
    parser.add_argument("--session-retries", type=int, default=2, help="Session retries on transient gRPC")
    parser.add_argument("--retry-wait-s", type=int, default=4, help="Seconds between session retries")
    parser.add_argument("--non-graphical", action="store_true", help="Run AEDT in non-graphical mode")
    return parser.parse_args()


def load_blueprint(path: str) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _safe_boundaries(app) -> list:
    try:
        return list(app.boundaries)
    except Exception:
        return []


def _boundary_kind(boundary) -> str:
    for attr in ["type", "boundary_type", "props"]:
        if not hasattr(boundary, attr):
            continue
        value = getattr(boundary, attr)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            bt = value.get("BoundType") or value.get("Type")
            if isinstance(bt, str):
                return bt
    return ""


def _safe_setup_names(app) -> list[str]:
    try:
        return list(app.setup_names)
    except Exception:
        return []


def _delete_boundary_by_name(app, boundary_name: str) -> bool:
    for boundary in _safe_boundaries(app):
        if getattr(boundary, "name", "") != boundary_name:
            continue
        if hasattr(boundary, "delete"):
            try:
                return bool(boundary.delete())
            except Exception:
                pass

    if hasattr(app, "delete_boundary"):
        try:
            return bool(app.delete_boundary(boundary_name))
        except Exception:
            pass

    if hasattr(app, "oboundary") and hasattr(app.oboundary, "DeleteBoundaries"):
        try:
            app.oboundary.DeleteBoundaries([boundary_name])
            return True
        except Exception:
            pass
    return False


def _delete_setup_by_name(app, setup_name: str) -> bool:
    if hasattr(app, "delete_setup"):
        try:
            return bool(app.delete_setup(setup_name))
        except Exception:
            pass

    if hasattr(app, "oanalysis") and hasattr(app.oanalysis, "DeleteSetups"):
        try:
            app.oanalysis.DeleteSetups([setup_name])
            return True
        except Exception:
            pass
    return False


def _collect_messages(app) -> list[str]:
    messages = []
    if hasattr(app, "odesktop") and hasattr(app.odesktop, "GetMessages"):
        for a, b, c in [("", "", 0), ("", "", 2), ("", "", 1)]:
            try:
                out = app.odesktop.GetMessages(a, b, c)
                if isinstance(out, (list, tuple)):
                    messages.extend([str(x) for x in out if str(x).strip()])
                elif out:
                    messages.append(str(out))
                if messages:
                    break
            except Exception:
                pass
    return messages


def cleanup_project_locks(project_file: str) -> list[str]:
    removed = []
    p = Path(project_file)
    lock_file = p.with_suffix(p.suffix + ".lock")
    if lock_file.exists():
        try:
            lock_file.unlink()
            removed.append(str(lock_file))
        except Exception:
            pass

    results_dir = p.with_suffix(p.suffix + "results")
    if results_dir.exists():
        for pat in ["*.semaphore", ".*.semaphore", "*.lock", ".*.lock"]:
            for fp in results_dir.rglob(pat):
                try:
                    fp.unlink()
                    removed.append(str(fp))
                except Exception:
                    pass
    return removed


def run_validation(app) -> dict:
    result = {"validate_simple": False, "report_excerpt": "", "messages": [], "note": ""}
    report = None
    try:
        if hasattr(app, "validate_full_design"):
            report = app.validate_full_design()
    except Exception as exc:
        result["note"] = f"validate_full_design failed: {exc}"

    try:
        if hasattr(app, "validate_simple"):
            result["validate_simple"] = bool(app.validate_simple())
        else:
            result["validate_simple"] = False
    except Exception as exc:
        note = f"validate_simple failed: {exc}"
        result["note"] = f"{result['note']} | {note}" if result["note"] else note

    if report is not None:
        result["report_excerpt"] = str(report)[:2000]
    result["messages"] = _collect_messages(app)[-30:]
    return result


def infer_model_context(app, bp: dict) -> dict:
    g = bp.get("geometry", {})
    ex = bp.get("excitation", {})
    arr = bp.get("array", {})

    tx_prefix = str(arr.get("tx_prefix", g.get("tx_name", "tx_coil")))
    rx_prefix = str(arr.get("rx_prefix", g.get("rx_name", "rx_coil")))
    tx_name = str(ex.get("tx_name", "J_TX"))
    rx_name = str(ex.get("rx_name", "J_RX"))
    tx_jz = str(ex.get("tx_jz", "1A_per_meter_sq"))
    rx_jz = str(ex.get("rx_jz", "-1A_per_meter_sq"))
    radiation_name = str(bp.get("boundaries", {}).get("radiation_name", "RAD1"))

    object_names = []
    try:
        object_names = list(app.modeler.object_names)
    except Exception:
        pass

    tx_objects = [n for n in object_names if n.startswith(f"{tx_prefix}_")]
    rx_objects = [n for n in object_names if n.startswith(f"{rx_prefix}_")]

    if not tx_objects and g.get("tx_name") in object_names:
        tx_objects = [g["tx_name"]]
    if not rx_objects and g.get("rx_name") in object_names:
        rx_objects = [g["rx_name"]]

    return {
        "tx_objects": tx_objects,
        "rx_objects": rx_objects,
        "tx_excitation": tx_name,
        "rx_excitation": rx_name,
        "tx_jz": tx_jz,
        "rx_jz": rx_jz,
        "radiation_name": radiation_name,
    }


def _has_radiation_boundary(app) -> bool:
    for b in _safe_boundaries(app):
        bname = str(getattr(b, "name", "")).lower()
        bkind = _boundary_kind(b).lower()
        if "radiation" in bkind or bname.startswith("radiation"):
            return True
    return False


def apply_fixes(app, setup_name: str, ctx: dict, validation: dict) -> list[str]:
    actions = []

    conduction_paths = []
    if hasattr(app, "oboundary") and hasattr(app.oboundary, "GetConductionPaths"):
        try:
            raw = app.oboundary.GetConductionPaths()
            if isinstance(raw, (list, tuple)):
                conduction_paths = [str(x) for x in raw if str(x).strip()]
            elif raw:
                conduction_paths = [str(raw)]
        except Exception:
            conduction_paths = []

    for pname in conduction_paths:
        if _delete_boundary_by_name(app, pname):
            actions.append(f"removed conduction_path {pname}")

    for b in _safe_boundaries(app):
        bname = str(getattr(b, "name", ""))
        bkind = _boundary_kind(b).lower()
        if bname.lower().startswith("path") or ("conduction" in bkind and "path" in bkind):
            if _delete_boundary_by_name(app, bname):
                actions.append(f"removed conduction_path {bname}")

    for sname in _safe_setup_names(app):
        if sname != setup_name and _delete_setup_by_name(app, sname):
            actions.append(f"removed redundant_setup {sname}")

    expected = {ctx["tx_excitation"], ctx["rx_excitation"]}
    for b in _safe_boundaries(app):
        bname = str(getattr(b, "name", ""))
        bkind = _boundary_kind(b).lower()
        if "currentdensity" not in bkind:
            continue
        keep = bname in expected or any(bname.startswith(f"{e}_") for e in expected if e)
        if not keep and _delete_boundary_by_name(app, bname):
            actions.append(f"removed stale_current_density {bname}")

    if ctx["tx_objects"]:
        bnames = [x.name for x in _safe_boundaries(app)]
        has_tx = ctx["tx_excitation"] in bnames or any(
            b.startswith(f"{ctx['tx_excitation']}_") for b in bnames
        )
        if not has_tx:
            try:
                app.assign_current_density(
                    ctx["tx_objects"],
                    current_density_name=ctx["tx_excitation"],
                    current_density_x="0",
                    current_density_y="0",
                    current_density_z=ctx["tx_jz"],
                    coordinate_system="Global",
                    coordinate_system_type="Cartesian",
                )
                actions.append(f"assigned {ctx['tx_excitation']}")
            except Exception as exc:
                actions.append(f"failed assign {ctx['tx_excitation']}: {exc}")

    if ctx["rx_objects"]:
        bnames = [x.name for x in _safe_boundaries(app)]
        has_rx = ctx["rx_excitation"] in bnames or any(
            b.startswith(f"{ctx['rx_excitation']}_") for b in bnames
        )
        if not has_rx:
            try:
                app.assign_current_density(
                    ctx["rx_objects"],
                    current_density_name=ctx["rx_excitation"],
                    current_density_x="0",
                    current_density_y="0",
                    current_density_z=ctx["rx_jz"],
                    coordinate_system="Global",
                    coordinate_system_type="Cartesian",
                )
                actions.append(f"assigned {ctx['rx_excitation']}")
            except Exception as exc:
                actions.append(f"failed assign {ctx['rx_excitation']}: {exc}")

    if not _has_radiation_boundary(app):
        try:
            app.assign_radiation(["air_region"])
            actions.append("assigned radiation")
        except Exception as exc:
            actions.append(f"failed assign radiation: {exc}")

    report_text = (validation.get("report_excerpt", "") + "\n" + "\n".join(validation.get("messages", []))).lower()
    path_names = sorted(set(re.findall(r"path\d+", report_text)))
    for pname in path_names:
        for b in _safe_boundaries(app):
            bname = str(getattr(b, "name", ""))
            if bname.lower() == pname and _delete_boundary_by_name(app, bname):
                actions.append(f"removed by_report {bname}")

    try:
        app.save_project()
        actions.append("save_project ok")
    except Exception as exc:
        actions.append(f"save_project failed: {exc}")
    return actions


def _is_transient_grpc_error(msg: str) -> bool:
    s = str(msg).lower()
    keys = ["grpc", "rpc", "getsetups", "getobjectsingroup", "validat", "save"]
    return any(k in s for k in keys)


def run_once(args: argparse.Namespace, bp: dict, out_dir: Path) -> dict:
    report = {
        "ok": False,
        "project": str(args.project),
        "design": args.design,
        "setup": args.setup,
        "iterations": [],
        "message": "",
    }

    app = None
    try:
        core = importlib.import_module("ansys.aedt.core")
        Maxwell3d = getattr(core, "Maxwell3d")
        app = Maxwell3d(
            project=str(args.project),
            design=args.design,
            solution_type="EddyCurrent",
            version=args.version,
            non_graphical=bool(args.non_graphical),
            new_desktop=True,
            remove_lock=True,
        )

        if args.design not in app.design_list:
            app.insert_design(args.design)
        app.set_active_design(args.design)

        ctx = infer_model_context(app, bp)
        for i in range(1, max(1, args.max_iterations) + 1):
            v = run_validation(app)
            item = {"iteration": i, "validation": v, "fix_actions": []}
            if v.get("validate_simple"):
                report["ok"] = True
                report["message"] = "validate passed"
                report["iterations"].append(item)
                break

            actions = apply_fixes(app, args.setup, ctx, v)
            item["fix_actions"] = actions
            report["iterations"].append(item)

        if not report["ok"]:
            report["message"] = "validate still failing after max iterations"
    except Exception as exc:
        report["ok"] = False
        report["message"] = str(exc)
    finally:
        if app is not None:
            try:
                app.release_desktop(close_projects=True, close_desktop=True)
            except Exception:
                pass

    with (out_dir / "validate_autofix_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    bp = load_blueprint(args.blueprint)
    lock_removed = cleanup_project_locks(args.project)

    final = {
        "ok": False,
        "message": "validate autofix not executed",
        "iterations": [],
    }
    for attempt in range(1, max(1, args.session_retries) + 1):
        final = run_once(args, bp, out_dir)
        if final.get("ok"):
            final["session_attempt"] = attempt
            break
        if attempt < max(1, args.session_retries) and _is_transient_grpc_error(final.get("message", "")):
            time.sleep(max(0, int(args.retry_wait_s)))
            continue
        final["session_attempt"] = attempt
        break

    with (out_dir / "validate_autofix_status.json").open("w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    with (out_dir / "lock_cleanup.json").open("w", encoding="utf-8") as f:
        json.dump({"removed": lock_removed}, f, ensure_ascii=False, indent=2)

    print(f"Saved: {out_dir / 'validate_autofix_status.json'}")
    print(f"Validate OK: {final.get('ok')}")
    print(f"Message: {final.get('message')}")


if __name__ == "__main__":
    main()
