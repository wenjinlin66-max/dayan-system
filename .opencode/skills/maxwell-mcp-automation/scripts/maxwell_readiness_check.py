import argparse
import importlib
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Maxwell project readiness before solve")
    parser.add_argument("--project", required=True, help="Path to .aedt project")
    parser.add_argument("--design", required=True, help="Design name")
    parser.add_argument("--out", default="results/maxwell-mcp-readiness", help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "project": args.project,
        "design": args.design,
        "ok_to_solve": False,
        "checks": {},
        "missing_items": [],
        "notes": [],
    }

    try:
        maxwell_module = importlib.import_module("ansys.aedt.core")
        Maxwell3d = getattr(maxwell_module, "Maxwell3d")

        app = Maxwell3d(
            project=args.project,
            design=args.design,
            solution_type="EddyCurrent",
            version="2023.1",
            non_graphical=True,
            new_desktop=True,
            remove_lock=True,
        )

        setup_names = app.setup_names
        object_count = len(app.modeler.object_names)
        boundary_count = len(app.boundaries)
        mesh_ops_count = len(app.mesh.meshoperations)
        var_names = list(app.variable_manager.design_variable_names)

        report["checks"] = {
            "setup_count": len(setup_names),
            "setup_names": setup_names,
            "object_count": object_count,
            "boundary_count": boundary_count,
            "mesh_operations": mesh_ops_count,
            "design_variables": var_names,
        }

        if len(setup_names) == 0:
            report["missing_items"].append("未创建 Setup（至少需要 Setup1）")
        if object_count == 0:
            report["missing_items"].append("无几何体（需创建发射线圈、接收线圈、空气域）")
        if boundary_count == 0:
            report["missing_items"].append("无边界/激励（需添加线圈激励与空气域边界）")
        if mesh_ops_count == 0:
            report["notes"].append("当前未设置显式网格操作，建议增加关键区域网格加密")

        report["ok_to_solve"] = len(report["missing_items"]) == 0

        app.release_desktop(close_projects=True, close_desktop=True)

    except Exception as exc:
        report["missing_items"].append("项目读取失败或会话创建失败")
        report["notes"].append(str(exc))

    json_path = out_dir / "readiness_report.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    md_path = out_dir / "readiness_report.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Maxwell 求解前就绪检查\n\n")
        f.write(f"- Project: `{report['project']}`\n")
        f.write(f"- Design: `{report['design']}`\n")
        f.write(f"- 可直接求解: **{'是' if report['ok_to_solve'] else '否'}**\n\n")
        f.write("## 检查结果\n\n")
        for k, v in report.get("checks", {}).items():
            f.write(f"- {k}: {v}\n")
        f.write("\n## 缺失项\n\n")
        if report["missing_items"]:
            for item in report["missing_items"]:
                f.write(f"- [ ] {item}\n")
        else:
            f.write("- 无\n")
        f.write("\n## 备注\n\n")
        if report["notes"]:
            for n in report["notes"]:
                f.write(f"- {n}\n")
        else:
            f.write("- 无\n")

    print(f"Saved: {json_path}")
    print(f"Saved: {md_path}")


if __name__ == "__main__":
    main()
