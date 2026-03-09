import argparse
import inspect
import importlib
import json
import math
import shutil
import time
from pathlib import Path

import pandas as pd
import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto build and repair Maxwell model (steps 1-8)")
    parser.add_argument("--blueprint", required=True, help="Path to blueprint yaml")
    parser.add_argument("--out", default="results/maxwell-auto-build", help="Output directory")
    parser.add_argument("--execute", action="store_true", help="Run setup solve after repair")
    parser.add_argument("--max-fix-passes", type=int, default=2, help="Max auto-fix passes")
    parser.add_argument("--max-solve-retries", type=int, default=3, help="Max solve retries after readiness pass")
    parser.add_argument("--max-session-retries", type=int, default=3, help="Max AEDT session retries for transient gRPC errors")
    parser.add_argument("--session-retry-wait-s", type=int, default=5, help="Seconds to wait before session retry")
    parser.add_argument("--force-analyze-on-validate-fail", action="store_true", help="Try analyze_setup even when validate_simple is false")
    parser.add_argument("--strict-session-probe", action="store_true", help="Fail fast when health probe fails")
    return parser.parse_args()


def load_blueprint(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _obj_exists(app, name: str) -> bool:
    try:
        return name in app.modeler.object_names
    except Exception:
        return False


def _boundary_names(app) -> list[str]:
    try:
        return [b.name for b in app.boundaries]
    except Exception:
        return []


def _safe_boundaries(app) -> list:
    try:
        return list(app.boundaries)
    except Exception:
        return []


def _boundary_kind(boundary) -> str:
    kind = ""
    for attr in ["type", "boundary_type", "props"]:
        if not hasattr(boundary, attr):
            continue
        try:
            value = getattr(boundary, attr)
        except Exception:
            continue
        if isinstance(value, str):
            kind = value
            break
        if isinstance(value, dict):
            bt = value.get("BoundType") or value.get("Type")
            if isinstance(bt, str):
                kind = bt
                break
    return str(kind)


def _safe_setup_names(app) -> list[str]:
    try:
        return list(app.setup_names)
    except Exception:
        return []


def _delete_boundary_by_name(app, boundary_name: str) -> bool:
    boundaries = _safe_boundaries(app)

    for boundary in boundaries:
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


def sanitize_conduction_path_conflicts(app, bp: dict) -> list[str]:
    actions = []
    ex = bp.get("excitation", {})
    if str(ex.get("mode", "")).lower() != "current_density":
        return actions

    boundaries = _safe_boundaries(app)

    for boundary in boundaries:
        bname = str(getattr(boundary, "name", ""))
        bkind = _boundary_kind(boundary).lower()
        is_path_name = bname.lower().startswith("path")
        is_path_type = "conduction" in bkind and "path" in bkind
        if not (is_path_name or is_path_type):
            continue

        ok = _delete_boundary_by_name(app, bname)
        if ok:
            actions.append(f"removed conduction_path_conflict {bname}")
        else:
            actions.append(f"failed remove conduction_path_conflict {bname}")

    return actions


def sanitize_setups(app, setup_name_keep: str) -> list[str]:
    actions = []
    for name in _safe_setup_names(app):
        if name == setup_name_keep:
            continue
        ok = _delete_setup_by_name(app, name)
        if ok:
            actions.append(f"removed redundant_setup {name}")
        else:
            actions.append(f"failed remove redundant_setup {name}")
    return actions


def sanitize_radiation_boundaries(app, keep_name: str) -> list[str]:
    actions = []
    boundary_names = []
    for b in _safe_boundaries(app):
        bname = str(getattr(b, "name", ""))
        bkind = _boundary_kind(b).lower()
        if "radiation" in bkind or bname.lower().startswith("radiation"):
            boundary_names.append(bname)

    if not boundary_names:
        return actions

    keep_actual = keep_name if keep_name in boundary_names else boundary_names[0]
    for name in boundary_names:
        if name == keep_actual:
            continue
        ok = _delete_boundary_by_name(app, name)
        if ok:
            actions.append(f"removed redundant_radiation {name}")
        else:
            actions.append(f"failed remove redundant_radiation {name}")
    return actions


def _has_radiation_boundary(app) -> bool:
    for b in _safe_boundaries(app):
        bname = str(getattr(b, "name", "")).lower()
        bkind = _boundary_kind(b).lower()
        if "radiation" in bkind or bname.startswith("radiation"):
            return True
    return False


def sanitize_current_density_boundaries(app, expected_names: set[str]) -> list[str]:
    actions = []
    for boundary in _safe_boundaries(app):
        bname = str(getattr(boundary, "name", ""))
        bkind = _boundary_kind(boundary).lower()
        if "currentdensity" not in bkind:
            continue
        keep = False
        if bname in expected_names:
            keep = True
        else:
            for expected in expected_names:
                if expected and bname.startswith(f"{expected}_"):
                    keep = True
                    break
        if keep:
            continue
        ok = _delete_boundary_by_name(app, bname)
        if ok:
            actions.append(f"removed unexpected_current_density {bname}")
        else:
            actions.append(f"failed remove unexpected_current_density {bname}")
    return actions


def sanitize_current_boundaries(app, expected_names: set[str]) -> list[str]:
    actions = []
    for boundary in _safe_boundaries(app):
        bname = str(getattr(boundary, "name", ""))
        bkind = _boundary_kind(boundary).lower()
        if "current" not in bkind or "currentdensity" in bkind:
            continue
        keep = False
        if bname in expected_names:
            keep = True
        else:
            for expected in expected_names:
                if expected and bname.startswith(f"{expected}_"):
                    keep = True
                    break
        if keep:
            continue
        ok = _delete_boundary_by_name(app, bname)
        if ok:
            actions.append(f"removed unexpected_current {bname}")
        else:
            actions.append(f"failed remove unexpected_current {bname}")
    return actions


def collect_readiness(app, setup_name: str) -> dict:
    setup_names = _safe_setup_names(app)
    try:
        object_names = list(app.modeler.object_names)
    except Exception:
        object_names = []
    boundaries = _boundary_names(app)
    try:
        mesh_ops_count = len(app.mesh.meshoperations)
    except Exception:
        mesh_ops_count = 0
    try:
        var_names = list(app.variable_manager.design_variable_names)
    except Exception:
        var_names = []

    missing = []
    if setup_name not in setup_names:
        missing.append("setup")
    if len(object_names) == 0:
        missing.append("geometry")
    if len(boundaries) == 0:
        missing.append("boundaries")

    return {
        "setup_names": setup_names,
        "object_names": object_names,
        "boundary_names": boundaries,
        "mesh_ops_count": mesh_ops_count,
        "variable_names": var_names,
        "missing": missing,
        "ok_to_solve": len(missing) == 0,
    }


def _as_expr(value) -> str:
    return str(value)


def _add_expr(base, delta) -> str:
    base_s = _as_expr(base)
    delta_s = _as_expr(delta)
    return f"({base_s})+({delta_s})"


def _array_object_specs(bp: dict) -> tuple[list[tuple[str, list]], list[tuple[str, list]]]:
    g = bp["geometry"]
    arr = bp.get("array", {})
    enabled = bool(arr.get("enabled", False))
    if not enabled:
        return ([(g["tx_name"], g.get("tx_origin", [0, 0, 0]))], [(g["rx_name"], g.get("rx_origin", [0, 0, "coil_gap_cm"]))])

    rows = int(arr.get("rows", 2))
    cols = int(arr.get("cols", 2))
    pitch_x = arr.get("pitch_x", "80mm")
    pitch_y = arr.get("pitch_y", "80mm")
    tx_prefix = str(arr.get("tx_prefix", g["tx_name"]))
    rx_prefix = str(arr.get("rx_prefix", g["rx_name"]))
    centered = bool(arr.get("centered", True))

    cx = (cols - 1) / 2.0 if centered else 0.0
    cy = (rows - 1) / 2.0 if centered else 0.0

    tx_base = g.get("tx_origin", [0, 0, 0])
    rx_base = g.get("rx_origin", [0, 0, "coil_gap_cm"])

    tx_specs = []
    rx_specs = []
    for r in range(rows):
        for c in range(cols):
            dx = f"({c - cx})*({_as_expr(pitch_x)})"
            dy = f"({r - cy})*({_as_expr(pitch_y)})"
            tx_name = f"{tx_prefix}_r{r+1}_c{c+1}"
            rx_name = f"{rx_prefix}_r{r+1}_c{c+1}"
            tx_origin = [_add_expr(tx_base[0], dx), _add_expr(tx_base[1], dy), _as_expr(tx_base[2])]
            rx_origin = [_add_expr(rx_base[0], dx), _add_expr(rx_base[1], dy), _as_expr(rx_base[2])]
            tx_specs.append((tx_name, tx_origin))
            rx_specs.append((rx_name, rx_origin))

    return tx_specs, rx_specs


def _coil_name_groups(bp: dict) -> tuple[list[str], list[str]]:
    tx_specs, rx_specs = _array_object_specs(bp)
    return [n for n, _ in tx_specs], [n for n, _ in rx_specs]


def _export_coil_names(bp: dict) -> tuple[str, str]:
    export_cfg = bp.get("export_coils", {})
    if export_cfg.get("tx") and export_cfg.get("rx"):
        return str(export_cfg["tx"]), str(export_cfg["rx"])
    tx_names, rx_names = _coil_name_groups(bp)
    return tx_names[0], rx_names[0]


def ensure_geometry(app, bp: dict) -> list[str]:
    actions = []
    g = bp["geometry"]
    v = bp["variables"]

    air_name = g["air_name"]

    topology = str(bp.get("topology", "circular")).lower()
    if topology == "circular":
        sides = 0
    elif topology == "rectangular":
        sides = 4
    elif topology == "hexagonal":
        sides = 6
    else:
        sides = 0

    tx_specs, rx_specs = _array_object_specs(bp)
    for tx_name, tx_origin in tx_specs:
        if _obj_exists(app, tx_name):
            continue
        try:
            app.modeler.create_cylinder(
                g.get("orientation", "Z"),
                tx_origin,
                v["coil_radius_mm"],
                v["coil_height_mm"],
                num_sides=sides,
                name=tx_name,
                material=bp["materials"]["tx"],
            )
            actions.append(f"created {tx_name} topology={topology}")
        except Exception as exc:
            actions.append(f"failed create {tx_name}: {exc}")

    for rx_name, rx_origin in rx_specs:
        if _obj_exists(app, rx_name):
            continue
        try:
            app.modeler.create_cylinder(
                g.get("orientation", "Z"),
                rx_origin,
                v["coil_radius_mm"],
                v["coil_height_mm"],
                num_sides=sides,
                name=rx_name,
                material=bp["materials"]["rx"],
            )
            actions.append(f"created {rx_name} topology={topology}")
        except Exception as exc:
            actions.append(f"failed create {rx_name}: {exc}")

    if not _obj_exists(app, air_name):
        try:
            app.modeler.create_region(
                g.get("air_region_pad_percent", [100, 100, 100, 100, 150, 150]),
                pad_type="Percentage Offset",
                name=air_name,
            )
            actions.append(f"created {air_name}")
        except Exception as exc:
            actions.append(f"failed create {air_name}: {exc}")

    return actions


def ensure_materials(app, bp: dict) -> list[str]:
    actions = []
    g = bp["geometry"]
    mats = bp["materials"]

    tx_names, rx_names = _coil_name_groups(bp)
    targets = [(name, mats["tx"]) for name in tx_names] + [(name, mats["rx"]) for name in rx_names] + [(g["air_name"], mats["air"])]
    for obj_name, mat in targets:
        if _obj_exists(app, obj_name):
            try:
                app.assign_material([obj_name], mat)
                actions.append(f"material {obj_name}={mat}")
            except Exception as exc:
                actions.append(f"failed material {obj_name}={mat}: {exc}")
    return actions


def ensure_boundaries_and_excitation(app, bp: dict) -> list[str]:
    actions = []
    g = bp["geometry"]
    ex = bp["excitation"]
    bd = bp["boundaries"]

    actions.extend(sanitize_conduction_path_conflicts(app, bp))
    actions.extend(sanitize_setups(app, bp["setup_name"]))
    actions.extend(sanitize_current_density_boundaries(app, {ex["tx_name"], ex["rx_name"]}))
    actions.extend(sanitize_current_boundaries(app, {str(ex.get("tx_current_name", "I_TX")), str(ex.get("rx_current_name", "I_RX"))}))
    actions.extend(sanitize_radiation_boundaries(app, bd["radiation_name"]))
    names = _boundary_names(app)
    tx_names, rx_names = _coil_name_groups(bp)

    if ex["mode"] == "current_density":
        if ex["tx_name"] not in names:
            try:
                app.assign_current_density(
                    tx_names,
                    current_density_name=ex["tx_name"],
                    current_density_x="0",
                    current_density_y="0",
                    current_density_z=ex["tx_jz"],
                    coordinate_system="Global",
                    coordinate_system_type="Cartesian",
                )
                actions.append(f"excitation {ex['tx_name']}")
            except Exception as exc:
                actions.append(f"failed excitation {ex['tx_name']}: {exc}")

        if ex["rx_name"] not in names:
            try:
                app.assign_current_density(
                    rx_names,
                    current_density_name=ex["rx_name"],
                    current_density_x="0",
                    current_density_y="0",
                    current_density_z=ex["rx_jz"],
                    coordinate_system="Global",
                    coordinate_system_type="Cartesian",
                )
                actions.append(f"excitation {ex['rx_name']}")
            except Exception as exc:
                actions.append(f"failed excitation {ex['rx_name']}: {exc}")

    if ex["mode"] == "current_stranded":
        tx_current_name = str(ex.get("tx_current_name", "I_TX"))
        rx_current_name = str(ex.get("rx_current_name", "I_RX"))
        tx_amp = str(ex.get("tx_current_amp", "20A"))
        rx_amp = str(ex.get("rx_current_amp", "20A"))
        tx_phase = str(ex.get("tx_phase", "0deg"))
        rx_phase = str(ex.get("rx_phase", "180deg"))

        if tx_current_name not in names:
            try:
                app.assign_current(
                    tx_names,
                    amplitude=tx_amp,
                    phase=tx_phase,
                    solid=False,
                    swap_direction=False,
                    name=tx_current_name,
                )
                actions.append(f"excitation {tx_current_name}")
            except Exception as exc:
                actions.append(f"failed excitation {tx_current_name}: {exc}")

        if rx_current_name not in names:
            try:
                app.assign_current(
                    rx_names,
                    amplitude=rx_amp,
                    phase=rx_phase,
                    solid=False,
                    swap_direction=False,
                    name=rx_current_name,
                )
                actions.append(f"excitation {rx_current_name}")
            except Exception as exc:
                actions.append(f"failed excitation {rx_current_name}: {exc}")

    if not _has_radiation_boundary(app):
        try:
            rad_fn = app.assign_radiation
            kwargs = _filter_kwargs_for_callable(rad_fn, {"boundary_name": bd["radiation_name"], "name": bd["radiation_name"]})
            b = rad_fn([g["air_name"]], **kwargs)
            actions.append(f"boundary {getattr(b, 'name', 'Radiation_Auto')}")
        except Exception as exc:
            actions.append(f"failed boundary radiation: {exc}")

    return actions


def ensure_setup(app, bp: dict) -> list[str]:
    actions = []
    setup_name = bp["setup_name"]
    setup_cfg = bp.get("setup", {})
    max_passes = int(setup_cfg.get("maximum_passes", 12))
    min_passes = int(setup_cfg.get("minimum_passes", 2))
    min_converged = int(setup_cfg.get("minimum_converged_passes", 2))
    percent_error = float(setup_cfg.get("percent_error", 0.5))
    setup_names = _safe_setup_names(app)
    if setup_name not in setup_names:
        try:
            setup = app.create_setup(setup_name, setup_type=bp.get("solution_type", "EddyCurrent"))
        except Exception as exc:
            actions.append(f"failed create setup {setup_name}: {exc}")
            return actions
        setup.props["Frequency"] = bp.get("frequency", "85kHz")
        setup.props["MaximumPasses"] = max_passes
        setup.props["MinimumPasses"] = min_passes
        setup.props["MinimumConvergedPasses"] = min_converged
        setup.props["PercentError"] = percent_error
        try:
            setup.update()
        except Exception:
            pass
        actions.append(f"created setup {setup_name}")
    else:
        try:
            setup = app.get_setup(setup_name)
        except Exception as exc:
            actions.append(f"failed get setup {setup_name}: {exc}")
            return actions
        setup.props["Frequency"] = bp.get("frequency", "85kHz")
        setup.props["MaximumPasses"] = max_passes
        setup.props["MinimumPasses"] = min_passes
        setup.props["MinimumConvergedPasses"] = min_converged
        setup.props["PercentError"] = percent_error
        try:
            setup.update()
        except Exception:
            pass
        actions.append(f"updated setup {setup_name}")
    return actions


def _filter_kwargs_for_callable(fn, kwargs: dict) -> dict:
    try:
        sig = inspect.signature(fn)
    except Exception:
        return kwargs

    params = sig.parameters
    accepts_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    if accepts_var_kw:
        return kwargs

    return {k: v for k, v in kwargs.items() if k in params}


def _try_mesh_call(mesh_fn, target_objects: list[str], options: list[dict]) -> tuple[bool, dict, str]:
    errors = []
    for option in options:
        kwargs = _filter_kwargs_for_callable(mesh_fn, option)
        try:
            mesh_fn(target_objects, **kwargs)
            return True, kwargs, ""
        except Exception as exc:
            errors.append(str(exc))
    return False, {}, " | ".join(errors[:3])


def ensure_mesh(app, bp: dict) -> list[str]:
    actions = []
    mesh_cfg = bp.get("mesh", {})
    tx_names, rx_names = _coil_name_groups(bp)
    target_objects = tx_names + rx_names

    try:
        if len(app.mesh.meshoperations) > 0:
            actions.append(f"mesh existing_ops={len(app.mesh.meshoperations)}")
            return actions
    except Exception:
        pass

    meshop_name = str(mesh_cfg.get("operation_name", "mesh_coils_local"))
    max_len = str(mesh_cfg.get("max_length", "2mm"))

    if hasattr(app.mesh, "assign_length_mesh"):
        ok, used_kwargs, err = _try_mesh_call(
            app.mesh.assign_length_mesh,
            target_objects,
            [
                {"maximum_length": max_len, "meshop_name": meshop_name},
                {"maximum_length": max_len},
                {"max_length": max_len, "meshop_name": meshop_name},
                {"max_length": max_len},
                {"maxlength": max_len, "meshop_name": meshop_name},
                {"maxlength": max_len},
            ],
        )
        if ok:
            actions.append(f"mesh assign_length_mesh {used_kwargs}")
            return actions
        if err:
            actions.append(f"mesh assign_length_mesh failed: {err}")

    if hasattr(app.mesh, "assign_model_resolution"):
        ok, used_kwargs, err = _try_mesh_call(
            app.mesh.assign_model_resolution,
            target_objects,
            [
                {"defeature_length": max_len},
                {"model_resolution": max_len},
                {},
            ],
        )
        if ok:
            actions.append(f"mesh assign_model_resolution {used_kwargs}")
            return actions
        if err:
            actions.append(f"mesh assign_model_resolution failed: {err}")

    actions.append("mesh not created (no compatible mesh API found)")
    return actions


def run_validation(app, strict: bool) -> dict:
    result = {"strict": strict, "validate_simple": None, "note": ""}
    try:
        if hasattr(app, "change_validation_settings"):
            level = "Strict" if strict else "Basic"
            try:
                app.change_validation_settings(entity_check_level=level)
            except TypeError:
                app.change_validation_settings(level)
    except Exception as exc:
        result["note"] = f"change_validation_settings failed: {exc}"

    report = None
    try:
        if hasattr(app, "validate_full_design"):
            report = app.validate_full_design()
    except Exception as exc:
        note = f"validate_full_design failed: {exc}"
        result["note"] = f"{result['note']} | {note}" if result["note"] else note

    try:
        if hasattr(app, "validate_simple"):
            result["validate_simple"] = bool(app.validate_simple())
        else:
            result["validate_simple"] = True
    except Exception as exc:
        result["validate_simple"] = False
        note = f"validate_simple failed: {exc}"
        result["note"] = f"{result['note']} | {note}" if result["note"] else note

    if report is not None:
        text = str(report)
        text = text[:1500]
        result["report_excerpt"] = text
    return result


def apply_validation_fixes(app, bp: dict, validation: dict) -> list[str]:
    actions = []
    actions.extend(sanitize_conduction_path_conflicts(app, bp))
    actions.extend(sanitize_setups(app, bp["setup_name"]))
    ex = bp.get("excitation", {})
    expected = {str(ex.get("tx_name", "")), str(ex.get("rx_name", ""))}
    expected = {x for x in expected if x}
    actions.extend(sanitize_current_density_boundaries(app, expected))
    actions.extend(sanitize_radiation_boundaries(app, bp.get("boundaries", {}).get("radiation_name", "")))
    actions.extend(ensure_boundaries_and_excitation(app, bp))
    actions.extend(ensure_setup(app, bp))
    actions.extend(ensure_mesh(app, bp))
    return actions


def _to_float(value) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _extract_from_solution_data(solution_data, expression: str) -> float | None:
    if solution_data is None:
        return None

    for accessor in ["data_real", "data_magnitude", "data_db10"]:
        if not hasattr(solution_data, accessor):
            continue
        fn = getattr(solution_data, accessor)
        try:
            data = fn(expression)
        except TypeError:
            try:
                data = fn()
            except Exception:
                continue
        except Exception:
            continue

        if isinstance(data, (list, tuple)) and data:
            val = _to_float(data[-1])
            if val is not None:
                return val
        else:
            val = _to_float(data)
            if val is not None:
                return val

    if hasattr(solution_data, "data"):
        try:
            d = solution_data.data
            if isinstance(d, dict):
                candidate = d.get(expression)
                if isinstance(candidate, (list, tuple)) and candidate:
                    return _to_float(candidate[-1])
                return _to_float(candidate)
        except Exception:
            pass
    return None


def _query_expression(app, setup_name: str, expression: str) -> float | None:
    sweeps = [f"{setup_name} : LastAdaptive", setup_name]
    for sweep in sweeps:
        try:
            sd = app.post.get_solution_data(expressions=expression, setup_sweep_name=sweep)
        except TypeError:
            try:
                sd = app.post.get_solution_data(expression, setup_sweep_name=sweep)
            except Exception:
                sd = None
        except Exception:
            sd = None

        val = _extract_from_solution_data(sd, expression)
        if val is not None:
            return val
    return None


def export_em_parameters(app, bp: dict, setup_name: str, out_dir: Path, solved_ok: bool) -> dict:
    tx_name, rx_name = _export_coil_names(bp)
    candidates = {
        "L1": [f"L({tx_name},{tx_name})", "L1"],
        "L2": [f"L({rx_name},{rx_name})", "L2"],
        "M": [f"L({tx_name},{rx_name})", f"L({rx_name},{tx_name})", "M"],
        "k": [f"k({tx_name},{rx_name})", "k"],
    }

    extracted = {
        "solve_ok": solved_ok,
        "setup": setup_name,
        "parameters": {},
        "status": "not_attempted" if not solved_ok else "attempted",
    }

    for key, exprs in candidates.items():
        value = None
        source = ""
        if solved_ok:
            for expr in exprs:
                value = _query_expression(app, setup_name, expr)
                if value is not None:
                    source = expr
                    break

        extracted["parameters"][key] = {
            "value": value,
            "source_expression": source,
            "unit": "H" if key in {"L1", "L2", "M"} else "",
        }

    l1 = extracted["parameters"]["L1"]["value"]
    l2 = extracted["parameters"]["L2"]["value"]
    m = extracted["parameters"]["M"]["value"]
    k = extracted["parameters"]["k"]["value"]
    if k is None and all(v is not None for v in [l1, l2, m]) and l1 > 0 and l2 > 0:
        extracted["parameters"]["k"]["value"] = m / math.sqrt(l1 * l2)
        extracted["parameters"]["k"]["source_expression"] = "computed_from_M_L1_L2"

    values_ready = all(extracted["parameters"][p]["value"] is not None for p in ["L1", "L2", "M", "k"])
    extracted["status"] = "ok" if values_ready else ("partial" if solved_ok else "solve_not_ok")

    rows = []
    zh = {"L1": "发射线圈自感", "L2": "接收线圈自感", "M": "互感", "k": "耦合系数"}
    for key in ["L1", "L2", "M", "k"]:
        info = extracted["parameters"][key]
        rows.append(
            {
                "symbol": key,
                "symbol_zh": zh[key],
                "value": info["value"],
                "unit": info["unit"],
                "source_expression": info["source_expression"],
                "solve_ok": solved_ok,
            }
        )

    csv_path = out_dir / "electromagnetic_parameters.csv"
    json_path = out_dir / "electromagnetic_parameters.json"
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(extracted, f, ensure_ascii=False, indent=2)

    extracted["files"] = [str(csv_path), str(json_path)]
    return extracted


def apply_variables(app, bp: dict) -> list[str]:
    actions = []
    for k, v in bp["variables"].items():
        app[k] = str(v)
        actions.append(f"var {k}={v}")
    return actions


def _is_transient_grpc_error(message: str) -> bool:
    text = str(message).lower()
    keys = [
        "failed to execute grpc aedt command",
        "getsetups",
        "getobjectsingroup",
        "save",
        "rpc",
        "grpc",
    ]
    return any(k in text for k in keys)


def _session_health_probe(app) -> tuple[bool, str]:
    notes = []
    try:
        _ = list(app.modeler.object_names)
    except Exception as exc:
        notes.append(f"object_names failed: {exc}")

    try:
        _ = _safe_boundaries(app)
    except Exception as exc:
        notes.append(f"boundaries read failed: {exc}")

    try:
        _ = list(app.variable_manager.design_variable_names)
    except Exception as exc:
        notes.append(f"variables read failed: {exc}")

    try:
        _ = list(app.design_list)
    except Exception as exc:
        notes.append(f"design_list read failed (non-fatal): {exc}")

    return (len(notes) == 0), (" | ".join(notes) if notes else "ok")


def _save_project_with_fallback(app, run_project: Path, out_dir: Path, log_rows: list[dict]) -> str:
    try:
        app.save_project()
        log_rows.append({"stage": "save", "action": "save_project default"})
        return str(run_project)
    except Exception as exc:
        log_rows.append({"stage": "save", "action": f"save_project default failed: {exc}"})

    fallback = out_dir / f"{run_project.stem}_fallback_save.aedt"
    save_errors = []

    for mode in ["positional", "keyword", "oproject_saveas"]:
        try:
            if mode == "positional":
                app.save_project(str(fallback))
            elif mode == "keyword":
                app.save_project(project_file=str(fallback))
            else:
                if not hasattr(app, "oproject") or not hasattr(app.oproject, "SaveAs"):
                    raise RuntimeError("oproject SaveAs unavailable")
                app.oproject.SaveAs(str(fallback), True)

            log_rows.append({"stage": "save", "action": f"save fallback success mode={mode}"})
            return str(fallback)
        except Exception as exc:
            save_errors.append(f"{mode}: {exc}")

    raise RuntimeError("save_project failed in all modes: " + " ; ".join(save_errors))


def _cleanup_project_lock_files(run_project: Path) -> list[str]:
    removed = []
    lock_file = run_project.with_suffix(run_project.suffix + ".lock")
    if lock_file.exists():
        try:
            lock_file.unlink()
            removed.append(str(lock_file))
        except Exception:
            pass

    results_dir = run_project.with_suffix(run_project.suffix + "results")
    if results_dir.exists():
        for pat in ["*.semaphore", ".*.semaphore", "*.lock", ".*.lock"]:
            for p in results_dir.rglob(pat):
                try:
                    p.unlink()
                    removed.append(str(p))
                except Exception:
                    pass
    return removed


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    bp = load_blueprint(args.blueprint)

    source_project = Path(bp["project_path"])
    run_project = out_dir / f"{source_project.stem}_auto_build.aedt"
    shutil.copy2(source_project, run_project)

    maxwell_module = importlib.import_module("ansys.aedt.core")
    Maxwell3d = getattr(maxwell_module, "Maxwell3d")

    log_rows = []
    status = {
        "ok": False,
        "project": str(source_project),
        "run_project": str(run_project),
        "design": bp["design_name"],
        "setup": bp["setup_name"],
        "execute_requested": bool(args.execute),
        "executed": False,
        "session_attempts": [],
        "save_path": "",
        "solve_attempts": [],
        "parameter_export": {},
        "passes": [],
        "message": "not started",
    }

    session_ok = False
    for session_attempt in range(max(1, args.max_session_retries)):
        app = None
        removed_locks = _cleanup_project_lock_files(run_project)
        if removed_locks:
            for p in removed_locks:
                log_rows.append({"stage": f"session_{session_attempt+1}_lock_cleanup", "action": f"removed {p}"})

        attempt_record = {
            "attempt": session_attempt + 1,
            "transient_grpc": False,
            "error": "",
            "completed": False,
        }
        try:
            app = Maxwell3d(
                project=str(run_project),
                design=bp["design_name"],
                solution_type=bp.get("solution_type", "EddyCurrent"),
                version="2023.1",
                non_graphical=True,
                new_desktop=True,
                remove_lock=True,
            )

            if bp["design_name"] not in app.design_list:
                app.insert_design(bp["design_name"])
            app.set_active_design(bp["design_name"])

            for action in apply_variables(app, bp):
                log_rows.append({"stage": f"session_{session_attempt+1}_variables", "action": action})

            status["passes"] = []
            status["solve_attempts"] = []

            for idx in range(args.max_fix_passes):
                healthy, note = _session_health_probe(app)
                if not healthy:
                    log_rows.append({"stage": f"session_{session_attempt+1}_probe_pre_pass_{idx+1}", "action": f"health_probe_failed: {note}"})
                    if args.strict_session_probe:
                        raise RuntimeError(f"session health probe pre-pass failed: {note}")

                pass_actions = []
                pass_actions.extend(ensure_geometry(app, bp))
                pass_actions.extend(ensure_materials(app, bp))
                pass_actions.extend(ensure_boundaries_and_excitation(app, bp))
                pass_actions.extend(ensure_setup(app, bp))
                pass_actions.extend(ensure_mesh(app, bp))

                readiness = collect_readiness(app, bp["setup_name"])
                status["passes"].append(
                    {
                        "session_attempt": session_attempt + 1,
                        "pass": idx + 1,
                        "actions": pass_actions,
                        "readiness": readiness,
                    }
                )

                for action in pass_actions:
                    log_rows.append({"stage": f"session_{session_attempt+1}_pass_{idx+1}", "action": action})

                healthy_after, note_after = _session_health_probe(app)
                if not healthy_after:
                    log_rows.append({"stage": f"session_{session_attempt+1}_probe_post_pass_{idx+1}", "action": f"health_probe_failed: {note_after}"})
                    if args.strict_session_probe:
                        raise RuntimeError(f"session health probe post-pass failed: {note_after}")

                if readiness["ok_to_solve"]:
                    break

            final_ready = status["passes"][-1]["readiness"] if status["passes"] else {"ok_to_solve": False}
            status["ok"] = bool(final_ready.get("ok_to_solve", False))

            if args.execute and status["ok"]:
                solve_ok = False
                for attempt in range(max(1, args.max_solve_retries)):
                    attempt_actions = []
                    if attempt > 0:
                        attempt_actions.extend(ensure_boundaries_and_excitation(app, bp))
                        attempt_actions.extend(ensure_setup(app, bp))
                        attempt_actions.extend(ensure_mesh(app, bp))

                    if args.force_analyze_on_validate_fail:
                        validation = {
                            "strict": bool(attempt == 0),
                            "validate_simple": False,
                            "note": "validation skipped by --force-analyze-on-validate-fail",
                        }
                    else:
                        validation = run_validation(app, strict=(attempt == 0))
                    if validation["validate_simple"] is False:
                        fix_actions = apply_validation_fixes(app, bp, validation)
                        for action in fix_actions:
                            log_rows.append(
                                {
                                    "stage": f"session_{session_attempt+1}_solve_fix_{attempt+1}",
                                    "action": action,
                                }
                            )
                        validation_after_fix = run_validation(app, strict=False)
                        if validation_after_fix.get("validate_simple"):
                            validation = validation_after_fix
                            attempt_actions.extend(fix_actions)
                        elif not args.force_analyze_on_validate_fail:
                            status["solve_attempts"].append(
                                {
                                    "session_attempt": session_attempt + 1,
                                    "attempt": attempt + 1,
                                    "validation": validation,
                                    "validation_after_fix": validation_after_fix,
                                    "fix_actions": fix_actions,
                                    "actions": attempt_actions,
                                    "run_ok": False,
                                    "note": "validate_simple=false after auto-fix, skip analyze_setup",
                                }
                            )
                            continue

                    if validation["validate_simple"] is False and not args.force_analyze_on_validate_fail:
                        status["solve_attempts"].append(
                            {
                                "session_attempt": session_attempt + 1,
                                "attempt": attempt + 1,
                                "validation": validation,
                                "actions": attempt_actions,
                                "run_ok": False,
                                "note": "validate_simple=false, skip analyze_setup",
                            }
                        )
                        continue
                    if validation["validate_simple"] is False and args.force_analyze_on_validate_fail:
                        attempt_actions.append("force analyze on validate failure")

                    try:
                        run_ok = bool(
                            app.analyze_setup(
                                bp["setup_name"],
                                revert_to_initial_mesh=(attempt > 0),
                                blocking=True,
                            )
                        )
                    except TypeError:
                        run_ok = bool(app.analyze_setup(bp["setup_name"]))
                    solve_ok = run_ok
                    status["solve_attempts"].append(
                        {
                            "session_attempt": session_attempt + 1,
                            "attempt": attempt + 1,
                            "validation": validation,
                            "actions": attempt_actions,
                            "run_ok": run_ok,
                        }
                    )
                    if run_ok:
                        break

                status["executed"] = solve_ok
                if not solve_ok:
                    status["ok"] = False
                    status["message"] = "model built but solve returned false after retries"

            status["parameter_export"] = export_em_parameters(
                app=app,
                bp=bp,
                setup_name=bp["setup_name"],
                out_dir=out_dir,
                solved_ok=bool(status["executed"]),
            )

            if status["ok"] and not status["message"].startswith("model"):
                status["message"] = "auto build and readiness repair completed"
            elif not status["ok"] and status["message"] == "not started":
                status["message"] = "auto build finished but readiness still failed"

            healthy_before_save, note_before_save = _session_health_probe(app)
            if not healthy_before_save:
                log_rows.append({"stage": f"session_{session_attempt+1}_probe_pre_save", "action": f"health_probe_failed: {note_before_save}"})
                if args.strict_session_probe:
                    raise RuntimeError(f"session health probe pre-save failed: {note_before_save}")

            status["save_path"] = _save_project_with_fallback(app, run_project, out_dir, log_rows)
            attempt_record["completed"] = True
            session_ok = True
            break

        except Exception as exc:
            msg = str(exc)
            status["ok"] = False
            status["message"] = msg
            attempt_record["error"] = msg
            attempt_record["transient_grpc"] = _is_transient_grpc_error(msg)
            if attempt_record["transient_grpc"] and (session_attempt + 1) < max(1, args.max_session_retries):
                log_rows.append(
                    {
                        "stage": f"session_retry_{session_attempt+1}",
                        "action": f"transient_grpc_retry: {msg}",
                    }
                )
                time.sleep(max(0, int(args.session_retry_wait_s)))
            else:
                break
        finally:
            status["session_attempts"].append(attempt_record)
            if app is not None:
                try:
                    app.release_desktop(close_projects=True, close_desktop=True)
                except Exception:
                    pass
                time.sleep(1)

    if not session_ok and status["message"] == "not started":
        status["message"] = "aedt session failed before model workflow"

    pd.DataFrame(log_rows).to_csv(out_dir / "auto_build_actions.csv", index=False)
    pd.DataFrame([{"name": k, "value": v} for k, v in bp["variables"].items()]).to_csv(
        out_dir / "variable_snapshot.csv", index=False
    )
    pd.DataFrame([{"export_name": e} for e in bp.get("exports", [])]).to_csv(out_dir / "requested_exports.csv", index=False)

    with (out_dir / "auto_build_status.json").open("w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print(f"Saved: {out_dir / 'auto_build_status.json'}")
    print(f"Saved: {out_dir / 'auto_build_actions.csv'}")
    print(f"Saved: {out_dir / 'variable_snapshot.csv'}")
    print(f"Saved: {out_dir / 'requested_exports.csv'}")


if __name__ == "__main__":
    main()
