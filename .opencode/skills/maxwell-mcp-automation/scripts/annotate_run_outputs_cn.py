import argparse
import json
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Chinese annotations for classified run outputs")
    parser.add_argument("--run-dir", required=True, help="Path to a run folder containing 01..07 subfolders")
    return parser.parse_args()


def load_json(path: Path, default: dict | None = None) -> dict:
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_file_annotation(folder: Path, title: str, bullets: list[str]) -> None:
    p = folder / "中文标注说明.md"
    lines = [f"# {title}", ""]
    lines.extend([f"- {b}" for b in bullets])
    lines.append("")
    p.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    run_dir = Path(args.run_dir)

    p01 = run_dir / "01_input"
    p02 = run_dir / "02_precompute"
    p03 = run_dir / "03_auto_build"
    p04 = run_dir / "04_readiness"
    p05 = run_dir / "05_solve"
    p06 = run_dir / "06_exports"
    p07 = run_dir / "07_summary"

    inputs = load_json(p01 / "inputs.json")
    auto_status = load_json(p03 / "auto_build_status.json")
    readiness = load_json(p04 / "readiness_from_autobuild.json")
    solve = load_json(p05 / "solve_status.json")
    exports = load_json(p06 / "export_manifest.json")
    manifest = load_json(p07 / "run_manifest.json")
    em_params = load_json(p06 / "electromagnetic_parameters.json")

    # 01
    write_file_annotation(
        p01,
        "01_input 输入说明",
        [
            "本目录记录本次运行使用的输入文件与蓝图配置来源。",
            f"输入CSV：{inputs.get('input_csv', '未记录')}",
            f"蓝图YAML：{inputs.get('blueprint', '未记录')}",
            "用途：保证本次结果可复现、可追溯。",
        ],
    )

    # 02
    pre_files = sorted([x.name for x in p02.glob("*") if x.is_file()])
    write_file_annotation(
        p02,
        "02_precompute 预计算结果说明",
        [
            "本目录是Python预计算与作图结果。",
            "enriched_results.csv：计算主表（含M、k、效率代理值）。",
            "fig_3_*：按论文编号生成的图，可直接用于正文。",
            "figure_captions.md/csv：图题与编号映射，便于论文粘贴。",
            f"文件数量：{len(pre_files)}",
        ],
    )

    # 03
    actions_count = 0
    actions_file = p03 / "auto_build_actions.csv"
    if actions_file.exists():
        try:
            actions_count = len(pd.read_csv(actions_file))
        except Exception:
            actions_count = 0
    write_file_annotation(
        p03,
        "03_auto_build 自动建模说明",
        [
            "本目录记录自动建模、自动修复与变量快照。",
            f"工程文件：{(p03 / 'AGV_WPT_Base_auto_build.aedt').name if (p03 / 'AGV_WPT_Base_auto_build.aedt').exists() else '未找到'}",
            f"建模状态：ok={auto_status.get('ok', False)}，message={auto_status.get('message', '')}",
            f"执行动作条数：{actions_count}",
            "variable_snapshot.csv：本轮参数写入记录。",
        ],
    )

    # 04
    write_file_annotation(
        p04,
        "04_readiness 就绪检查说明",
        [
            "本目录是求解前可解性检查结果。",
            f"ok_to_solve：{readiness.get('ok_to_solve', '未记录')}",
            f"对象数量：{len(readiness.get('object_names', []))}",
            f"边界数量：{len(readiness.get('boundary_names', []))}",
            f"缺失项：{readiness.get('missing', [])}",
        ],
    )

    # 05
    write_file_annotation(
        p05,
        "05_solve 求解状态说明",
        [
            "本目录记录本轮是否执行求解、求解是否成功。",
            f"execute_requested：{solve.get('execute_requested', '未记录')}",
            f"executed：{solve.get('executed', '未记录')}",
            f"ok：{solve.get('ok', '未记录')}",
            f"message：{solve.get('message', '未记录')}",
        ],
    )

    # 06
    write_file_annotation(
        p06,
        "06_exports 导出说明",
        [
            "本目录记录计划导出项或已导出结果清单。",
            f"exports：{exports.get('exports', [])}",
            f"status：{exports.get('status', '未记录')}",
            f"参数文件：{exports.get('files', [])}",
            f"L1L2Mk状态：{em_params.get('status', '未记录')}",
            "说明：当 status=ok 时表示 L1/L2/M/k 已形成可追溯落盘文件。",
        ],
    )

    # 07 + global overview
    write_file_annotation(
        p07,
        "07_summary 运行总结说明",
        [
            "本目录保存本轮运行日志和总清单。",
            f"run_id：{manifest.get('run_id', run_dir.name)}",
            f"整体状态：{manifest.get('status', '未记录')}",
            "建议优先查看 run_manifest.json，然后回看各阶段 stdout/stderr 日志。",
        ],
    )

    overview = [
        f"# 本次运行中文总览（{run_dir.name}）",
        "",
        "## 目录级结论",
        "",
        f"- 01_input：输入来源已记录（CSV + 蓝图）。",
        f"- 02_precompute：预计算与作图已完成，论文图与图注可直接使用。",
        f"- 03_auto_build：自动建模已执行，详情见 auto_build_status.json。",
        f"- 04_readiness：可解性检查结果见 readiness_from_autobuild.json。",
        f"- 05_solve：求解状态见 solve_status.json。",
        f"- 06_exports：导出项计划见 export_manifest.json。",
        f"- 07_summary：总清单与日志汇总。",
        "",
        "## 关键状态快照",
        "",
        f"- run_id: {manifest.get('run_id', run_dir.name)}",
        f"- overall_status: {manifest.get('status', 'unknown')}",
        f"- readiness_ok_to_solve: {readiness.get('ok_to_solve', 'unknown')}",
        f"- solve_executed: {solve.get('executed', 'unknown')}",
        f"- solve_message: {solve.get('message', 'unknown')}",
        "",
        "## 阅读顺序建议",
        "",
        "- 先看 `07_summary/run_manifest.json` 获取总体状态。",
        "- 再看 `04_readiness/readiness_from_autobuild.json` 判断模型可解性。",
        "- 然后看 `05_solve/solve_status.json` 判断是否真正求解成功。",
        "- 最后使用 `02_precompute` 的图和 `figure_captions` 写论文。",
        "",
    ]
    (p07 / "中文结果总览.md").write_text("\n".join(overview), encoding="utf-8")

    print(f"Saved: {p07 / '中文结果总览.md'}")
    print("Saved: per-folder 中文标注说明.md")


if __name__ == "__main__":
    main()
