#!/usr/bin/env python3
"""
Module 7 - Step 4.3: Plot UTM track and remove GNSS outliers based on
maximum physically feasible speed (distance vs. elapsed time).
"""

import csv
import math
from pathlib import Path

from utm_converter import load_utm_track


class OutlierFilter:
    """
    Removes GNSS outliers from a 2D UTM track based on the maximum feasible
    speed between consecutive valid points:
        dist(p_last, p_i) <= max_speed_mps * (t_i - t_last)

    To avoid locking onto an initial bad fix (e.g., cold-start convergence at
    the beginning of a recording), the filter first locates a stable anchor
    point where `anchor_window` consecutive steps are all within `max_speed_mps`.
    """

    def __init__(self, max_speed_mps: float = 3.0, anchor_window: int = 3):
        if max_speed_mps <= 0:
            raise ValueError("max_speed_mps must be positive")
        self.max_speed_mps = max_speed_mps
        self.anchor_window = max(1, anchor_window)

    @staticmethod
    def _distance(p1: dict, p2: dict) -> float:
        return math.hypot(p2["easting"] - p1["easting"], p2["northing"] - p1["northing"])

    def _find_anchor_index(self, track: list[dict]) -> int:
        """Find the first index followed by `anchor_window` consecutive valid steps."""
        n = len(track)
        if n <= self.anchor_window:
            return 0

        for start in range(n - self.anchor_window):
            stable = True
            for k in range(self.anchor_window):
                p1 = track[start + k]
                p2 = track[start + k + 1]
                dt = p2["timestamp"] - p1["timestamp"]
                if dt <= 0 or self._distance(p1, p2) > self.max_speed_mps * dt:
                    stable = False
                    break
            if stable:
                return start
        return 0

    def filter(self, track: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Filter outliers from `track`.

        Returns:
            (clean_track, outliers)
        """
        if not track:
            return [], []

        anchor_idx = self._find_anchor_index(track)
        outliers = list(track[:anchor_idx])
        clean_track = [track[anchor_idx]]

        for pt in track[anchor_idx + 1 :]:
            last_valid = clean_track[-1]
            dt = pt["timestamp"] - last_valid["timestamp"]
            if dt <= 0:
                outliers.append(pt)
                continue

            dist = self._distance(last_valid, pt)
            max_allowed_dist = self.max_speed_mps * dt

            if dist <= max_allowed_dist:
                clean_track.append(pt)
            else:
                outliers.append(pt)

        return clean_track, outliers


def save_utm_track(track: list[dict], output_csv: Path) -> None:
    """Save a UTM track list of dicts to CSV."""
    fieldnames = ["timestamp", "hemisphere", "zone", "letter", "easting", "northing", "altitude"]
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pt in track:
            writer.writerow({
                "timestamp": f"{pt['timestamp']:.3f}",
                "hemisphere": pt["hemisphere"],
                "zone": pt["zone"],
                "letter": pt["letter"],
                "easting": f"{pt['easting']:.4f}",
                "northing": f"{pt['northing']:.4f}",
                "altitude": f"{pt['altitude']:.3f}",
            })


def compute_speeds(track: list[dict]) -> tuple[list[float], list[float]]:
    """Compute relative timestamps and instantaneous 2D speeds between consecutive points."""
    if len(track) < 2:
        return [], []
    t0 = track[0]["timestamp"]
    times, speeds = [], []
    for i in range(1, len(track)):
        dt = track[i]["timestamp"] - track[i - 1]["timestamp"]
        if dt > 0:
            dist = math.hypot(
                track[i]["easting"] - track[i - 1]["easting"],
                track[i]["northing"] - track[i - 1]["northing"],
            )
            times.append(track[i]["timestamp"] - t0)
            speeds.append(dist / dt)
    return times, speeds


def plot_outlier_removal(
    raw_track: list[dict],
    clean_track: list[dict],
    outliers: list[dict],
    max_speed_mps: float,
    output_png: Path,
) -> None:
    """Create a report-ready figure comparing raw vs. filtered UTM track and speed."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Use local offset relative to track origin for cleaner axis labels
    e0 = min(p["easting"] for p in raw_track)
    n0 = min(p["northing"] for p in raw_track)

    raw_e = [p["easting"] - e0 for p in raw_track]
    raw_n = [p["northing"] - n0 for p in raw_track]
    clean_e = [p["easting"] - e0 for p in clean_track]
    clean_n = [p["northing"] - n0 for p in clean_track]
    out_e = [p["easting"] - e0 for p in outliers]
    out_n = [p["northing"] - n0 for p in outliers]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1.25, 1]})

    # Left: 2D UTM track (equal aspect ratio!)
    ax1.plot(raw_e, raw_n, color="#bbbbbb", linewidth=1.0, label=f"Raw track ({len(raw_track)} pts)", zorder=1)
    ax1.plot(clean_e, clean_n, color="#1f77b4", linewidth=1.6, label=f"Filtered track ({len(clean_track)} pts)", zorder=2)
    if outliers:
        ax1.scatter(out_e, out_n, color="#d62728", s=22, marker="x", linewidths=1.3,
                    label=f"Removed outliers ({len(outliers)} pts)", zorder=3)
    ax1.scatter([clean_e[0]], [clean_n[0]], color="#2ca02c", s=55, marker="o", label="Start", zorder=4)
    ax1.scatter([clean_e[-1]], [clean_n[-1]], color="#ff7f0e", s=55, marker="s", label="End", zorder=4)

    ax1.set_aspect("equal", adjustable="box")
    ax1.set_xlabel(f"Local Easting [m]  (+{e0:.0f} m, UTM 32U)")
    ax1.set_ylabel(f"Local Northing [m]  (+{n0:.0f} m)")
    ax1.set_title(f"GNSS Track Outlier Removal ($v_{{max}}$ = {max_speed_mps:.1f} m/s)")
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="best", fontsize=8.5)

    # Right: Speed profile before vs after
    t_raw, v_raw = compute_speeds(raw_track)
    t_clean, v_clean = compute_speeds(clean_track)
    ax2.plot(t_raw, v_raw, color="#bbbbbb", linewidth=0.9, label="Raw speed")
    ax2.plot(t_clean, v_clean, color="#1f77b4", linewidth=1.1, label="Filtered speed")
    ax2.axhline(max_speed_mps, color="#d62728", linestyle="--", linewidth=1.2,
                label=f"Threshold ({max_speed_mps:.1f} m/s)")
    ax2.set_xlabel("Elapsed time [s]")
    ax2.set_ylabel("Speed between samples [m/s]")
    ax2.set_title("Instantaneous Speed Profile")
    ax2.set_ylim(0, min(max(v_raw) * 1.05, 20.0))
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc="upper right", fontsize=8.5)

    plt.tight_layout()
    plt.savefig(output_png, dpi=200)
    plt.close(fig)


def plot_before_after(
    raw_track: list[dict],
    clean_track: list[dict],
    outliers: list[dict],
    max_speed_mps: float,
    before_png: Path,
    after_png: Path,
    combined_png: Path,
) -> None:
    """Save separate Before and After 2D UTM track plots (same axis limits) + combined side-by-side."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    e0 = min(p["easting"] for p in raw_track)
    n0 = min(p["northing"] for p in raw_track)

    raw_e = [p["easting"] - e0 for p in raw_track]
    raw_n = [p["northing"] - n0 for p in raw_track]
    clean_e = [p["easting"] - e0 for p in clean_track]
    clean_n = [p["northing"] - n0 for p in clean_track]
    out_e = [p["easting"] - e0 for p in outliers]
    out_n = [p["northing"] - n0 for p in outliers]

    pad = 5.0
    xlim = (min(raw_e) - pad, max(raw_e) + pad)
    ylim = (min(raw_n) - pad, max(raw_n) + pad)

    def _draw_before(ax):
        ax.plot(raw_e, raw_n, color="#1f77b4", linewidth=1.4, label=f"Raw track ({len(raw_track)} pts)")
        if outliers:
            ax.scatter(out_e, out_n, color="#d62728", s=24, marker="x", linewidths=1.3,
                       label=f"Detected outliers ({len(outliers)} pts)", zorder=3)
        ax.scatter([raw_e[0]], [raw_n[0]], color="#2ca02c", s=50, marker="o", label="Start", zorder=4)
        ax.scatter([raw_e[-1]], [raw_n[-1]], color="#ff7f0e", s=50, marker="s", label="End", zorder=4)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel(f"Local Easting [m] (+{e0:.0f} m, UTM 32U)")
        ax.set_ylabel(f"Local Northing [m] (+{n0:.0f} m)")
        ax.set_title("Before Outlier Removal (Raw UTM Track)")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(loc="center", fontsize=8.5)

    def _draw_after(ax):
        ax.plot(clean_e, clean_n, color="#1f77b4", linewidth=1.5, label=f"Filtered track ({len(clean_track)} pts)")
        ax.scatter([clean_e[0]], [clean_n[0]], color="#2ca02c", s=50, marker="o", label="Start", zorder=4)
        ax.scatter([clean_e[-1]], [clean_n[-1]], color="#ff7f0e", s=50, marker="s", label="End", zorder=4)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel(f"Local Easting [m] (+{e0:.0f} m, UTM 32U)")
        ax.set_ylabel(f"Local Northing [m] (+{n0:.0f} m)")
        ax.set_title(f"After Outlier Removal ($v_{{max}}$ = {max_speed_mps:.1f} m/s)")
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(loc="center", fontsize=8.5)

    # Separate Before image
    fig, ax = plt.subplots(figsize=(5.5, 5.8))
    _draw_before(ax)
    plt.tight_layout()
    plt.savefig(before_png, dpi=200)
    plt.close(fig)

    # Separate After image
    fig, ax = plt.subplots(figsize=(5.5, 5.8))
    _draw_after(ax)
    plt.tight_layout()
    plt.savefig(after_png, dpi=200)
    plt.close(fig)

    # Combined side-by-side image
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 5.4))
    _draw_before(ax1)
    _draw_after(ax2)
    plt.tight_layout()
    plt.savefig(combined_png, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    mod7_dir = Path(__file__).resolve().parent
    utm_csv = mod7_dir / "gnss_track_utm.csv"
    clean_csv = mod7_dir / "gnss_track_utm_clean.csv"
    plot_png = mod7_dir / "step4_3_outlier_removal.png"

    raw_track = load_utm_track(utm_csv)

    max_speed = 4.0  # m/s (walking median ~1.5 m/s + margin for 5 Hz GNSS jitter)
    flt = OutlierFilter(max_speed_mps=max_speed, anchor_window=3)
    clean_track, outliers = flt.filter(raw_track)

    save_utm_track(clean_track, clean_csv)
    plot_outlier_removal(raw_track, clean_track, outliers, max_speed, plot_png)
    plot_before_after(
        raw_track,
        clean_track,
        outliers,
        max_speed,
        mod7_dir / "step4_3_before.png",
        mod7_dir / "step4_3_after.png",
        mod7_dir / "step4_3_before_after.png",
    )

    print(f"Raw points:      {len(raw_track)}")
    print(f"Clean points:    {len(clean_track)}")
    print(f"Outliers removed:{len(outliers)} ({100.0 * len(outliers) / len(raw_track):.2f}%)")
    print(f"Saved clean CSV: {clean_csv.name}")
    print(f"Saved plot:      {plot_png.name}")
