import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


MU0 = 4.0 * np.pi * 1e-7


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Optimize hex-array pitch for offset robustness (0-150 mm)."
    )
    parser.add_argument("--out-dir", required=True, help="Output folder")
    parser.add_argument("--diameter-mm", type=float, default=220.0, help="Coil diameter")
    parser.add_argument("--turns", type=int, default=10, help="Turns")
    parser.add_argument("--gap-mm", type=float, default=50.0, help="Air gap")
    parser.add_argument("--freq-hz", type=float, default=85000.0, help="Operating frequency")
    parser.add_argument("--r1-ohm", type=float, default=0.3)
    parser.add_argument("--r2-ohm", type=float, default=0.3)
    parser.add_argument("--rload-ohm", type=float, default=10.0)
    parser.add_argument("--array-count", type=int, default=3, help="Coils in 1xN array")
    parser.add_argument("--pitch-min-mm", type=float, default=220.0)
    parser.add_argument("--pitch-max-mm", type=float, default=420.0)
    parser.add_argument("--pitch-step-mm", type=float, default=10.0)
    parser.add_argument("--offset-min-mm", type=float, default=0.0)
    parser.add_argument("--offset-max-mm", type=float, default=150.0)
    parser.add_argument("--offset-step-mm", type=float, default=5.0)
    parser.add_argument("--eta-threshold", type=float, default=0.9, help="Coverage threshold")
    return parser.parse_args()


def m_single_h(radius_m: float, turns: int, gap_m: float, lateral_m: float) -> float:
    denom = (radius_m * radius_m + gap_m * gap_m + lateral_m * lateral_m) ** 1.5
    return MU0 * np.pi * turns * turns * (radius_m**4) / (2.0 * denom)


def eta_proxy(m_h: float, freq_hz: float, r1_ohm: float, r2_ohm: float, rload_ohm: float) -> float:
    w = 2.0 * np.pi * freq_hz
    wm2 = (w * m_h) ** 2
    numerator = wm2 * rload_ohm
    denominator = (r1_ohm * (r2_ohm + rload_ohm) + wm2) * (r2_ohm + rload_ohm)
    if denominator <= 0.0:
        return 0.0
    return float(np.clip(numerator / denominator, 0.0, 1.0))


def tx_positions_mm(pitch_mm: float, count: int) -> np.ndarray:
    start = -0.5 * (count - 1) * pitch_mm
    return np.array([start + i * pitch_mm for i in range(count)], dtype=float)


def evaluate_pitch(
    pitch_mm: float,
    offsets_mm: np.ndarray,
    radius_m: float,
    turns: int,
    gap_m: float,
    freq_hz: float,
    r1_ohm: float,
    r2_ohm: float,
    rload_ohm: float,
    array_count: int,
) -> pd.DataFrame:
    rows = []
    positions = tx_positions_mm(pitch_mm, array_count)
    for off_mm in offsets_mm:
        lateral_to_each = np.abs(positions - off_mm) / 1000.0
        m_each = np.array([m_single_h(radius_m, turns, gap_m, d) for d in lateral_to_each], dtype=float)
        best_idx = int(np.argmax(m_each))
        m_eff = float(m_each[best_idx])
        eta = eta_proxy(m_eff, freq_hz, r1_ohm, r2_ohm, rload_ohm)
        rows.append(
            {
                "pitch_mm": float(pitch_mm),
                "offset_mm": float(off_mm),
                "selected_tx_index": best_idx,
                "M_eff_H": m_eff,
                "M_eff_uH": m_eff * 1e6,
                "eta_proxy": eta,
            }
        )
    return pd.DataFrame(rows)


def summarize_pitch(df: pd.DataFrame, eta_threshold: float) -> pd.DataFrame:
    grouped = []
    for pitch_mm in sorted(float(x) for x in df["pitch_mm"].unique().tolist()):
        part = df[df["pitch_mm"] == pitch_mm]
        eta = part["eta_proxy"].to_numpy(dtype=float)
        eta_min = float(np.min(eta))
        eta_mean = float(np.mean(eta))
        eta_p10 = float(np.percentile(eta, 10))
        eta_std = float(np.std(eta))
        coverage = float(np.mean(eta >= eta_threshold))
        score = 0.6 * eta_min + 0.3 * eta_mean + 0.1 * coverage
        grouped.append(
            {
                "pitch_mm": float(pitch_mm),
                "eta_min": eta_min,
                "eta_mean": eta_mean,
                "eta_p10": eta_p10,
                "eta_std": eta_std,
                "coverage_eta_ge_threshold": coverage,
                "score": float(score),
            }
        )
    out = pd.DataFrame(grouped)
    return out.sort_values(["score", "eta_min", "eta_mean", "pitch_mm"], ascending=[False, False, False, True]).reset_index(drop=True)


def plot_summary(summary_df: pd.DataFrame, out_path: Path) -> None:
    d = summary_df.sort_values("pitch_mm")
    plt.figure(figsize=(8, 5))
    plt.plot(d["pitch_mm"], d["eta_min"], marker="o", label="eta_min")
    plt.plot(d["pitch_mm"], d["eta_mean"], marker="s", label="eta_mean")
    plt.plot(d["pitch_mm"], d["eta_p10"], marker="^", label="eta_p10")
    plt.xlabel("Pitch (mm)")
    plt.ylabel("Efficiency proxy")
    plt.title("Pitch robustness summary")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=240)
    plt.close()


def plot_heatmap(detail_df: pd.DataFrame, out_path: Path) -> None:
    pvals = sorted(float(x) for x in detail_df["pitch_mm"].unique().tolist())
    ovals = sorted(float(x) for x in detail_df["offset_mm"].unique().tolist())
    grid = np.full((len(pvals), len(ovals)), np.nan, dtype=float)
    p_to_i = {v: i for i, v in enumerate(pvals)}
    o_to_i = {v: i for i, v in enumerate(ovals)}
    for row in detail_df.to_dict(orient="records"):
        p = float(row["pitch_mm"])
        o = float(row["offset_mm"])
        e = float(row["eta_proxy"])
        grid[p_to_i[p], o_to_i[o]] = e

    plt.figure(figsize=(9, 5))
    plt.imshow(grid, aspect="auto", origin="lower", interpolation="nearest")
    plt.colorbar(label="Efficiency proxy")
    plt.xticks(np.linspace(0, len(ovals) - 1, min(len(ovals), 8)), [f"{int(ovals[i])}" for i in np.linspace(0, len(ovals) - 1, min(len(ovals), 8), dtype=int)])
    plt.yticks(np.arange(len(pvals)), [f"{int(v)}" for v in pvals])
    plt.xlabel("Offset (mm)")
    plt.ylabel("Pitch (mm)")
    plt.title("Offset-pitch efficiency map")
    plt.tight_layout()
    plt.savefig(out_path, dpi=240)
    plt.close()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    radius_m = args.diameter_mm / 2000.0
    gap_m = args.gap_mm / 1000.0
    pitches = np.arange(args.pitch_min_mm, args.pitch_max_mm + 1e-12, args.pitch_step_mm)
    offsets = np.arange(args.offset_min_mm, args.offset_max_mm + 1e-12, args.offset_step_mm)

    detail_parts = []
    for pitch in pitches:
        detail_parts.append(
            evaluate_pitch(
                pitch_mm=float(pitch),
                offsets_mm=offsets,
                radius_m=radius_m,
                turns=args.turns,
                gap_m=gap_m,
                freq_hz=args.freq_hz,
                r1_ohm=args.r1_ohm,
                r2_ohm=args.r2_ohm,
                rload_ohm=args.rload_ohm,
                array_count=args.array_count,
            )
        )

    detail_df = pd.concat(detail_parts, ignore_index=True)
    summary_df = summarize_pitch(detail_df, eta_threshold=args.eta_threshold)
    best = summary_df.iloc[0]

    detail_csv = out_dir / "pitch_offset_detail.csv"
    summary_csv = out_dir / "pitch_summary.csv"
    detail_df.to_csv(detail_csv, index=False)
    summary_df.to_csv(summary_csv, index=False)

    summary_fig = out_dir / "fig_pitch_summary.png"
    heatmap_fig = out_dir / "fig_pitch_offset_heatmap.png"
    plot_summary(summary_df, summary_fig)
    plot_heatmap(detail_df, heatmap_fig)

    best_df = pd.DataFrame(
        [
            {
                "best_pitch_mm": float(best["pitch_mm"]),
                "score": float(best["score"]),
                "eta_min": float(best["eta_min"]),
                "eta_mean": float(best["eta_mean"]),
                "eta_p10": float(best["eta_p10"]),
                "coverage_eta_ge_threshold": float(best["coverage_eta_ge_threshold"]),
            }
        ]
    )

    excel_out = out_dir / "pitch_optimization_results.xlsx"
    with pd.ExcelWriter(excel_out, engine="openpyxl") as writer:
        best_df.to_excel(writer, sheet_name="best_pitch", index=False)
        summary_df.to_excel(writer, sheet_name="pitch_summary", index=False)
        detail_df.to_excel(writer, sheet_name="pitch_offset_detail", index=False)

    config_rows = [
        {"name": "diameter_mm", "value": args.diameter_mm},
        {"name": "turns", "value": args.turns},
        {"name": "gap_mm", "value": args.gap_mm},
        {"name": "freq_hz", "value": args.freq_hz},
        {"name": "r1_ohm", "value": args.r1_ohm},
        {"name": "r2_ohm", "value": args.r2_ohm},
        {"name": "rload_ohm", "value": args.rload_ohm},
        {"name": "array_count", "value": args.array_count},
        {"name": "pitch_range_mm", "value": f"{args.pitch_min_mm}:{args.pitch_max_mm}:{args.pitch_step_mm}"},
        {"name": "offset_range_mm", "value": f"{args.offset_min_mm}:{args.offset_max_mm}:{args.offset_step_mm}"},
    ]
    config_df = pd.DataFrame(config_rows)
    config_csv = out_dir / "pitch_optimization_config.csv"
    config_df.to_csv(config_csv, index=False)

    print(f"Saved: {detail_csv}")
    print(f"Saved: {summary_csv}")
    print(f"Saved: {summary_fig}")
    print(f"Saved: {heatmap_fig}")
    print(f"Saved: {excel_out}")
    print(f"Saved: {config_csv}")
    print(
        "Best pitch: "
        f"{float(best['pitch_mm']):.1f} mm, "
        f"score={float(best['score']):.6f}, "
        f"eta_min={float(best['eta_min']):.6f}, "
        f"eta_mean={float(best['eta_mean']):.6f}"
    )


if __name__ == "__main__":
    main()
