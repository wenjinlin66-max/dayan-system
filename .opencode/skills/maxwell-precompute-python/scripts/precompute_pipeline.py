import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


MU0 = 4 * np.pi * 1e-7

CANONICAL_COLUMNS: Dict[str, List[str]] = {
    "distance_cm": [
        "distance_cm",
        "distance",
        "offset_cm",
        "displacement_cm",
        "偏移距离",
        "偏移距离cm",
        "距离cm",
        "distance(mm)",
        "distance_mm",
    ],
    "M_H": [
        "M_H",
        "M",
        "mutual_inductance",
        "mutual_inductance_h",
        "mutualinductance",
        "互感",
        "互感h",
        "m_uh",
        "互感uh",
    ],
    "L1_H": ["L1_H", "L1", "self_l1", "l1", "l1_uh", "发射侧自感", "自感l1"],
    "L2_H": ["L2_H", "L2", "self_l2", "l2", "l2_uh", "接收侧自感", "自感l2"],
    "x_cm": ["x_cm", "x", "x_offset", "offset_x", "水平偏移", "x_mm"],
    "z_cm": ["z_cm", "z", "z_offset", "offset_z", "垂直偏移", "z_mm"],
}


def _norm_token(s: str) -> str:
    return (
        s.strip()
        .lower()
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .replace("_", "")
        .replace("-", "")
    )


def _is_micro_h(name: str) -> bool:
    n = name.lower()
    return ("uh" in n) or ("μh" in n) or ("微亨" in n)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    source_to_target: Dict[str, str] = {}
    normalized_existing = {_norm_token(c): c for c in df.columns}

    for target, aliases in CANONICAL_COLUMNS.items():
        alias_tokens = {_norm_token(a) for a in aliases}
        for token, original in normalized_existing.items():
            if token in alias_tokens and original not in source_to_target:
                source_to_target[original] = target
                break

    df = df.rename(columns=source_to_target)

    # Unit normalization to canonical H/cm
    for original, target in source_to_target.items():
        if target in {"M_H", "L1_H", "L2_H"} and _is_micro_h(original):
            numeric = np.asarray(pd.to_numeric(df[target], errors="coerce"), dtype=float)
            df[target] = numeric * 1e-6
        if target in {"distance_cm", "x_cm", "z_cm"} and "mm" in original.lower():
            numeric = np.asarray(pd.to_numeric(df[target], errors="coerce"), dtype=float)
            df[target] = numeric / 10.0

    # Force numeric where expected
    for col in ["distance_cm", "M_H", "L1_H", "L2_H", "x_cm", "z_cm"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Maxwell precompute and plotting pipeline")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--out", default="results", help="Output directory")
    parser.add_argument("--freq", type=float, default=85000.0, help="Frequency in Hz")
    parser.add_argument("--r1", type=float, default=0.3, help="Primary equivalent resistance")
    parser.add_argument("--r2", type=float, default=0.3, help="Secondary equivalent resistance")
    parser.add_argument("--rload", type=float, default=10.0, help="Load resistance")

    parser.add_argument("--calc-theory", action="store_true", help="Enable Biot-Savart theory calculation")
    parser.add_argument("--turns", type=float, default=20.0, help="Coil turns for theory")
    parser.add_argument("--current", type=float, default=5.0, help="Current for theory")
    parser.add_argument("--radius", type=float, default=0.1, help="Loop radius in meters for theory")
    parser.add_argument("--z-max", type=float, default=0.3, help="Max z in meters for theory")
    parser.add_argument("--z-points", type=int, default=120, help="Number of z points for theory curve")
    parser.add_argument("--fig-chapter", type=int, default=3, help="Figure chapter number for thesis labels")
    parser.add_argument("--fig-start", type=int, default=1, help="Figure start index for thesis labels")
    return parser.parse_args()


def ensure_required_columns(df: pd.DataFrame) -> None:
    missing = [c for c in ["distance_cm", "M_H"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def compute_k(df: pd.DataFrame) -> pd.DataFrame:
    if {"L1_H", "L2_H"}.issubset(df.columns):
        denom = np.sqrt(df["L1_H"] * df["L2_H"])
        df["k"] = np.where(denom > 0, df["M_H"] / denom, np.nan)
    return df


def compute_efficiency_proxy(df: pd.DataFrame, freq: float, r1: float, r2: float, rload: float) -> pd.DataFrame:
    w = 2 * np.pi * freq
    wm2 = (w * df["M_H"]) ** 2
    numerator = wm2 * rload
    denominator = (r1 * (r2 + rload) + wm2) * (r2 + rload)
    eff = np.where(denominator > 0, numerator / denominator, np.nan)
    df["efficiency_proxy"] = np.clip(eff, 0.0, 1.0)
    return df


def plot_line(df: pd.DataFrame, x: str, y: str, title: str, xlabel: str, ylabel: str, out_path: Path) -> None:
    d = df[[x, y]].dropna().copy()
    x_num = np.asarray(pd.to_numeric(d[x], errors="coerce"), dtype=float)
    order = np.argsort(x_num)
    d = d.iloc[order]
    plt.figure(figsize=(7, 4.5))
    plt.plot(d[x], d[y], marker="o", linewidth=1.8)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.45)
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def plot_surface_if_possible(df: pd.DataFrame, out_path: Path) -> bool:
    needed = {"x_cm", "z_cm", "efficiency_proxy"}
    if not needed.issubset(df.columns):
        return False

    d = df[["x_cm", "z_cm", "efficiency_proxy"]].dropna()
    if d.empty:
        return False

    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_trisurf(d["x_cm"], d["z_cm"], d["efficiency_proxy"], linewidth=0.2, antialiased=True)  # type: ignore[attr-defined]
    ax.set_title("Efficiency Surface")
    ax.set_xlabel("x offset (cm)")
    ax.set_ylabel("z offset (cm)")
    ax.set_zlabel("efficiency")  # type: ignore[attr-defined]
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()
    return True


def biot_savart_on_axis(turns: float, current: float, radius: float, z_max: float, z_points: int) -> pd.DataFrame:
    z = np.linspace(0.0, z_max, z_points)
    b = MU0 * turns * current * radius**2 / (2.0 * (radius**2 + z**2) ** 1.5)
    return pd.DataFrame({"z_m": z, "B_T": b})


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    df = normalize_columns(df)
    ensure_required_columns(df)
    df = compute_k(df)
    df = compute_efficiency_proxy(df, args.freq, args.r1, args.r2, args.rload)

    enriched_csv = out_dir / "enriched_results.csv"
    df.to_csv(enriched_csv, index=False)

    plot_line(df, "distance_cm", "M_H", "Mutual Inductance vs Distance", "distance (cm)", "M (H)", out_dir / "fig_m_vs_distance.png")
    if "k" in df.columns:
        plot_line(df, "distance_cm", "k", "Coupling Coefficient vs Distance", "distance (cm)", "k", out_dir / "fig_k_vs_distance.png")
    plot_line(
        df,
        "distance_cm",
        "efficiency_proxy",
        "Efficiency Proxy vs Distance",
        "distance (cm)",
        "efficiency",
        out_dir / "fig_eff_vs_distance.png",
    )

    surface_ok = plot_surface_if_possible(df, out_dir / "fig_eff_surface.png")

    # Thesis figure numbering and caption export
    fig_index = args.fig_start
    captions: List[Tuple[str, str, str]] = []

    def register_figure(src_name: str, caption: str) -> None:
        nonlocal fig_index
        src = out_dir / src_name
        if not src.exists():
            return
        fig_id = f"图{args.fig_chapter}-{fig_index}"
        dst_name = f"fig_{args.fig_chapter}_{fig_index}_{src_name}"
        dst = out_dir / dst_name
        dst.write_bytes(src.read_bytes())
        captions.append((fig_id, dst_name, caption))
        fig_index += 1

    register_figure("fig_m_vs_distance.png", "互感 M 随偏移距离变化曲线")
    if "k" in df.columns:
        register_figure("fig_k_vs_distance.png", "耦合系数 k 随偏移距离变化曲线")
    register_figure("fig_eff_vs_distance.png", "效率代理值随偏移距离变化曲线")
    if surface_ok:
        register_figure("fig_eff_surface.png", "水平偏移-垂直偏移-效率三维曲面图")

    if args.calc_theory:
        theory_df = biot_savart_on_axis(args.turns, args.current, args.radius, args.z_max, args.z_points)
        theory_csv = out_dir / "theory_biot_savart.csv"
        theory_df.to_csv(theory_csv, index=False)
        plot_line(
            theory_df,
            "z_m",
            "B_T",
            "Biot-Savart On-axis Magnetic Flux Density",
            "z (m)",
            "B (T)",
            out_dir / "fig_biot_savart.png",
        )
        register_figure("fig_biot_savart.png", "Biot-Savart 理论磁感应强度曲线")

    if captions:
        cap_md = out_dir / "figure_captions.md"
        cap_csv = out_dir / "figure_captions.csv"
        with cap_md.open("w", encoding="utf-8") as f:
            f.write("# 论文图注清单\n\n")
            for fig_id, file_name, caption in captions:
                f.write(f"- {fig_id}（{file_name}）：{caption}\n")
        pd.DataFrame(captions, columns=["figure_id", "file_name", "caption"]).to_csv(cap_csv, index=False)

    print(f"Saved: {enriched_csv}")
    print(f"Saved: {out_dir / 'fig_m_vs_distance.png'}")
    if "k" in df.columns:
        print(f"Saved: {out_dir / 'fig_k_vs_distance.png'}")
    print(f"Saved: {out_dir / 'fig_eff_vs_distance.png'}")
    if surface_ok:
        print(f"Saved: {out_dir / 'fig_eff_surface.png'}")
    if args.calc_theory:
        print(f"Saved: {out_dir / 'theory_biot_savart.csv'}")
        print(f"Saved: {out_dir / 'fig_biot_savart.png'}")
    if captions:
        print(f"Saved: {out_dir / 'figure_captions.md'}")
        print(f"Saved: {out_dir / 'figure_captions.csv'}")


if __name__ == "__main__":
    main()
