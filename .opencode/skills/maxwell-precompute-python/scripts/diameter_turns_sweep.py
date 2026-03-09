import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager


MU0 = 4 * np.pi * 1e-7


def configure_chinese_font() -> None:
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans CN",
        "WenQuanYi Zen Hei",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    selected = None
    for name in candidates:
        if name in available:
            selected = name
            break
    if selected is not None:
        plt.rcParams["font.sans-serif"] = [selected, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sweep coil diameter and turns, export Figure-2 style metrics to Excel"
    )
    parser.add_argument("--out", required=True, help="Output Excel file path")
    parser.add_argument("--diameter-min-cm", type=float, default=10.0)
    parser.add_argument("--diameter-max-cm", type=float, default=20.0)
    parser.add_argument("--diameter-step-cm", type=float, default=10.0)
    parser.add_argument("--turns-min", type=int, default=10)
    parser.add_argument("--turns-max", type=int, default=20)
    parser.add_argument("--turns-step", type=int, default=2)
    parser.add_argument("--freq-hz", type=float, default=85000.0)
    parser.add_argument("--air-gap-mm", type=float, default=50.0)
    parser.add_argument("--input-current-a", type=float, default=20.0)
    parser.add_argument("--wire-d-mm", type=float, default=1.5)
    parser.add_argument("--r1-ohm", type=float, default=0.3)
    parser.add_argument("--r2-ohm", type=float, default=0.3)
    parser.add_argument("--rload-ohm", type=float, default=10.0)
    return parser.parse_args()


def loop_self_inductance_h(radius_m: float, turns: int, wire_d_m: float) -> float:
    wire_radius_m = max(wire_d_m / 2.0, 1e-6)
    return MU0 * (turns**2) * radius_m * (np.log(8.0 * radius_m / wire_radius_m) - 2.0)


def mutual_inductance_h(radius_m: float, turns_tx: int, turns_rx: int, gap_m: float) -> float:
    denom = (radius_m**2 + gap_m**2) ** 1.5
    return MU0 * np.pi * turns_tx * turns_rx * (radius_m**4) / (2.0 * denom)


def efficiency_proxy(m_h: float, freq_hz: float, r1_ohm: float, r2_ohm: float, rload_ohm: float) -> float:
    w = 2.0 * np.pi * freq_hz
    wm2 = (w * m_h) ** 2
    numerator = wm2 * rload_ohm
    denominator = (r1_ohm * (r2_ohm + rload_ohm) + wm2) * (r2_ohm + rload_ohm)
    if denominator <= 0:
        return 0.0
    return float(np.clip(numerator / denominator, 0.0, 1.0))


def magnetic_flux_density_t(radius_m: float, turns: int, current_a: float, gap_m: float, offset_m: float = 0.0) -> float:
    denom = (radius_m**2 + gap_m**2 + offset_m**2) ** 1.5
    return MU0 * turns * current_a * (radius_m**2) / (2.0 * denom)


def build_sweep(args: argparse.Namespace) -> pd.DataFrame:
    diameters_cm = np.arange(args.diameter_min_cm, args.diameter_max_cm + 1e-12, args.diameter_step_cm)
    turns_values = np.arange(args.turns_min, args.turns_max + 1, args.turns_step)

    gap_m = args.air_gap_mm / 1000.0
    wire_d_m = args.wire_d_mm / 1000.0

    rows = []
    for d_cm in diameters_cm:
        radius_m = d_cm / 100.0 / 2.0
        for turns in turns_values:
            l_air = loop_self_inductance_h(radius_m=radius_m, turns=turns, wire_d_m=wire_d_m)
            m_air = mutual_inductance_h(radius_m=radius_m, turns_tx=turns, turns_rx=turns, gap_m=gap_m)
            k = m_air / l_air if l_air > 0 else 0.0
            eta = efficiency_proxy(
                m_h=m_air,
                freq_hz=args.freq_hz,
                r1_ohm=args.r1_ohm,
                r2_ohm=args.r2_ohm,
                rload_ohm=args.rload_ohm,
            )
            b_center = magnetic_flux_density_t(
                radius_m=radius_m,
                turns=turns,
                current_a=args.input_current_a,
                gap_m=gap_m,
                offset_m=0.0,
            )

            rows.append(
                {
                    "diameter_cm": float(d_cm),
                    "turns": int(turns),
                    "L_air_H": float(l_air),
                    "L_air_uH": float(l_air * 1e6),
                    "M_air_H": float(m_air),
                    "M_air_uH": float(m_air * 1e6),
                    "k": float(k),
                    "eta_theory": float(eta),
                    "B_map_center_T": float(b_center),
                    "B_map_center_mT": float(b_center * 1e3),
                }
            )

    df = pd.DataFrame(rows)
    return df.sort_values(["eta_theory", "k", "diameter_cm", "turns"], ascending=[False, False, True, True]).reset_index(drop=True)


def build_bmap_for_best(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    best = df.iloc[0]
    radius_m = float(best["diameter_cm"]) / 100.0 / 2.0
    turns = int(best["turns"])
    gap_m = args.air_gap_mm / 1000.0

    offsets_mm = np.arange(0.0, 150.0 + 1e-12, 10.0)
    b_values = []
    for off_mm in offsets_mm:
        b_t = magnetic_flux_density_t(
            radius_m=radius_m,
            turns=turns,
            current_a=args.input_current_a,
            gap_m=gap_m,
            offset_m=float(off_mm / 1000.0),
        )
        b_values.append(float(b_t))

    b_max = max(b_values) if b_values else 1.0
    return pd.DataFrame(
        {
            "offset_mm": offsets_mm,
            "B_T": b_values,
            "B_mT": np.array(b_values) * 1e3,
            "B_normalized": np.array(b_values) / b_max,
        }
    )


def build_meta(args: argparse.Namespace, best_row: pd.Series) -> pd.DataFrame:
    rows = [
        {"item": "frequency_hz", "value": args.freq_hz},
        {"item": "power_range_w", "value": "1000-2000"},
        {"item": "input_current_a", "value": args.input_current_a},
        {"item": "air_gap_mm", "value": args.air_gap_mm},
        {"item": "topology", "value": "rectangular"},
        {"item": "array_count", "value": "3"},
        {"item": "wire_type", "value": "stranded"},
        {"item": "rload_ohm", "value": args.rload_ohm},
        {"item": "wire_d_mm_for_formula", "value": args.wire_d_mm},
        {"item": "diameter_sweep_cm", "value": f"{args.diameter_min_cm}:{args.diameter_max_cm}:{args.diameter_step_cm}"},
        {"item": "turns_sweep", "value": f"{args.turns_min}:{args.turns_max}:{args.turns_step}"},
        {"item": "best_diameter_cm", "value": float(best_row["diameter_cm"])},
        {"item": "best_turns", "value": int(best_row["turns"])},
        {"item": "best_eta_theory", "value": float(best_row["eta_theory"])},
    ]
    return pd.DataFrame(rows)


def plot_efficiency_surface(df: pd.DataFrame, out_path: Path) -> None:
    data = df[["diameter_cm", "turns", "eta_theory"]].dropna().copy()
    if data.empty:
        return

    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    x = np.asarray(data["diameter_cm"], dtype=float)
    y = np.asarray(data["turns"], dtype=float)
    z = np.asarray(data["eta_theory"], dtype=float)
    if len(data) >= 3:
        plot_trisurf = getattr(ax, "plot_trisurf")
        plot_trisurf(
            x,
            y,
            z,
            linewidth=0.2,
            antialiased=True,
            cmap="viridis",
        )
    else:
        scatter = getattr(ax, "scatter")
        scatter(x, y, z, c=z, cmap="viridis", s=60)
    ax.set_title("Efficiency Surface (Diameter-Turns)")
    ax.set_xlabel("Diameter (cm)")
    ax.set_ylabel("Turns")
    set_zlabel = getattr(ax, "set_zlabel")
    set_zlabel("Efficiency")
    plt.tight_layout()
    plt.savefig(out_path, dpi=240)
    plt.close(fig)


def plot_efficiency_surface_cn(df: pd.DataFrame, out_path: Path) -> None:
    data = df[["diameter_cm", "turns", "eta_theory"]].dropna().copy()
    if data.empty:
        return

    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    configure_chinese_font()

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    x_mm = np.asarray(data["diameter_cm"], dtype=float) * 10.0
    y_n = np.asarray(data["turns"], dtype=float)
    z_eta = np.asarray(data["eta_theory"], dtype=float)
    if len(data) >= 3:
        plot_trisurf = getattr(ax, "plot_trisurf")
        plot_trisurf(
            x_mm,
            y_n,
            z_eta,
            linewidth=0.2,
            antialiased=True,
            cmap="viridis",
        )
    else:
        scatter = getattr(ax, "scatter")
        scatter(x_mm, y_n, z_eta, c=z_eta, cmap="viridis", s=60)
    ax.set_title("效率三维曲面图（直径-匝数-效率）")
    ax.set_xlabel("线圈直径 (mm)")
    ax.set_ylabel("匝数 N")
    set_zlabel = getattr(ax, "set_zlabel")
    set_zlabel("效率 η")
    plt.tight_layout()
    plt.savefig(out_path, dpi=240)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = build_sweep(args)
    best = df.iloc[0]
    bmap_df = build_bmap_for_best(df, args)
    meta_df = build_meta(args, best)
    fig3d_out = out_path.with_name(out_path.stem + "_efficiency_3d.png")
    fig3d_cn_out = out_path.with_name(out_path.stem + "_efficiency_3d_cn.png")
    plot_efficiency_surface(df, fig3d_out)
    plot_efficiency_surface_cn(df, fig3d_cn_out)

    csv_out = out_path.with_suffix(".csv")
    df.to_csv(csv_out, index=False)

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="figure2_data", index=False)
        bmap_df.to_excel(writer, sheet_name="bmap_best_combo", index=False)
        meta_df.to_excel(writer, sheet_name="meta_and_best", index=False)

    print(f"Saved: {out_path}")
    print(f"Saved: {csv_out}")
    print(f"Saved: {fig3d_out}")
    print(f"Saved: {fig3d_cn_out}")
    print(
        "Best combo: "
        f"diameter_cm={float(best['diameter_cm'])}, "
        f"turns={int(best['turns'])}, "
        f"eta_theory={float(best['eta_theory']):.6f}, "
        f"k={float(best['k']):.6f}"
    )


if __name__ == "__main__":
    main()
