#!/usr/bin/env python3
"""
Module 7 - Step 4.4 (and 4.5): Track simplification class with three methods:
  1. Maximum waypoints allowed (Visvalingam-Whyatt algorithm)
  2. Minimize distance deviation (Ramer-Douglas-Peucker algorithm)
  3. Minimize distance and bearing angle deviation (combined RDP-style split)

Also converts the simplified UTM waypoints back to geographic coordinates
(latitude, longitude, altitude) using TrackUTMConverter (Step 4.5).
"""

import csv
import math
from pathlib import Path

from utm_converter import TrackUTMConverter, load_utm_track


def _point_to_segment_distance(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Perpendicular distance from 2D point p to line segment a-b."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx = bx - ax
    dy = by - ay
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def _triangle_area(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    """Area of triangle formed by 2D points a, b, c."""
    return 0.5 * abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))


def _bearing_deg(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Bearing angle in degrees [0, 360) from point a to b (0 = North, 90 = East)."""
    de = b[0] - a[0]
    dn = b[1] - a[1]
    return math.degrees(math.atan2(de, dn)) % 360.0


def _angle_diff_deg(a1: float, a2: float) -> float:
    """Smallest angular difference between two bearings in degrees [0, 180]."""
    diff = abs(a1 - a2) % 360.0
    return min(diff, 360.0 - diff)


class TrackSimplifier:
    """Simplifies a 2D UTM track into a waypoint route plan."""

    def __init__(self, default_altitude: float = 30.0):
        self.default_altitude = default_altitude
        self.converter = TrackUTMConverter()

    @staticmethod
    def _xy(track: list[dict]) -> list[tuple[float, float]]:
        return [(p["easting"], p["northing"]) for p in track]

    # ------------------------------------------------------------------
    # Method 1: Maximum waypoints allowed (Visvalingam-Whyatt)
    # ------------------------------------------------------------------
    def simplify_max_waypoints(self, track: list[dict], max_waypoints: int) -> list[dict]:
        """
        Visvalingam-Whyatt simplification: iteratively removes the interior
        point forming the smallest triangle area with its neighbors until
        at most `max_waypoints` remain.
        """
        if max_waypoints < 2:
            raise ValueError("max_waypoints must be at least 2")
        if len(track) <= max_waypoints:
            return list(track)

        pts = self._xy(track)
        indices = list(range(len(track)))

        # Iteratively remove the interior point with the smallest effective area
        while len(indices) > max_waypoints:
            min_area = float("inf")
            min_pos = 1
            for pos in range(1, len(indices) - 1):
                area = _triangle_area(
                    pts[indices[pos - 1]],
                    pts[indices[pos]],
                    pts[indices[pos + 1]],
                )
                if area < min_area:
                    min_area = area
                    min_pos = pos
            indices.pop(min_pos)

        return [track[i] for i in indices]

    # ------------------------------------------------------------------
    # Method 2: Minimize distance deviation (Ramer-Douglas-Peucker)
    # ------------------------------------------------------------------
    def simplify_distance(self, track: list[dict], max_distance_m: float = 2.0) -> list[dict]:
        """
        Ramer-Douglas-Peucker simplification: guarantees every original point
        lies within `max_distance_m` of the simplified route.
        """
        if len(track) <= 2:
            return list(track)

        pts = self._xy(track)
        keep = [False] * len(track)
        keep[0] = True
        keep[-1] = True

        stack = [(0, len(track) - 1)]
        while stack:
            start, end = stack.pop()
            if end - start <= 1:
                continue

            max_dist = -1.0
            split_idx = -1
            for i in range(start + 1, end):
                d = _point_to_segment_distance(pts[i], pts[start], pts[end])
                if d > max_dist:
                    max_dist = d
                    split_idx = i

            if max_dist > max_distance_m and split_idx != -1:
                keep[split_idx] = True
                stack.append((start, split_idx))
                stack.append((split_idx, end))

        return [track[i] for i, flag in enumerate(keep) if flag]

    # ------------------------------------------------------------------
    # Method 3: Minimize distance AND bearing angle deviation
    # ------------------------------------------------------------------
    def simplify_distance_and_bearing(
        self,
        track: list[dict],
        max_distance_m: float = 2.0,
        max_bearing_deg: float = 25.0,
        min_spacing_m: float = 3.0,
        bearing_window: int = 5,
    ) -> list[dict]:
        """
        Combined RDP-style simplification: splits a segment if either the
        perpendicular distance exceeds `max_distance_m` OR the local track
        bearing deviates from the segment bearing by more than `max_bearing_deg`
        (only for points at least `min_spacing_m` from segment endpoints, so
        stationary GPS jitter does not stack waypoints).
        """
        n = len(track)
        if n <= 2:
            return list(track)

        pts = self._xy(track)

        # Precompute smoothed local bearings along the original track
        local_bearings = []
        for i in range(n):
            i0 = max(0, i - bearing_window)
            i1 = min(n - 1, i + bearing_window)
            if math.hypot(pts[i1][0] - pts[i0][0], pts[i1][1] - pts[i0][1]) > 1.0:
                local_bearings.append(_bearing_deg(pts[i0], pts[i1]))
            else:
                local_bearings.append(None)

        keep = [False] * n
        keep[0] = True
        keep[-1] = True

        stack = [(0, n - 1)]
        while stack:
            start, end = stack.pop()
            if end - start <= 1:
                continue

            seg_len = math.hypot(pts[end][0] - pts[start][0], pts[end][1] - pts[start][1])
            seg_bearing = _bearing_deg(pts[start], pts[end]) if seg_len > 1.0 else None

            best_score = 1.0  # must exceed 1.0 to trigger a split
            split_idx = -1

            for i in range(start + 1, end):
                d = _point_to_segment_distance(pts[i], pts[start], pts[end])
                d_score = d / max_distance_m if max_distance_m > 0 else 0.0

                b_score = 0.0
                if seg_bearing is not None and local_bearings[i] is not None:
                    dist_start = math.hypot(pts[i][0] - pts[start][0], pts[i][1] - pts[start][1])
                    dist_end = math.hypot(pts[i][0] - pts[end][0], pts[i][1] - pts[end][1])
                    if dist_start >= min_spacing_m and dist_end >= min_spacing_m:
                        b_diff = _angle_diff_deg(local_bearings[i], seg_bearing)
                        b_score = b_diff / max_bearing_deg if max_bearing_deg > 0 else 0.0

                score = max(d_score, b_score)
                if score > best_score:
                    best_score = score
                    split_idx = i

            if split_idx != -1:
                keep[split_idx] = True
                stack.append((start, split_idx))
                stack.append((split_idx, end))

        return [track[i] for i, flag in enumerate(keep) if flag]

    # ------------------------------------------------------------------
    # Step 4.5 helper: Convert UTM waypoints -> Geographic (lat, lon, alt)
    # ------------------------------------------------------------------
    def to_geodetic_waypoints(self, utm_waypoints: list[dict], static_altitude: float | None = None) -> list[dict]:
        """Convert simplified UTM waypoints back to WGS84 (latitude, longitude, altitude)."""
        alt_val = self.default_altitude if static_altitude is None else static_altitude
        waypoints = []
        for pt in utm_waypoints:
            lat, lon = self.converter.utm_to_geodetic(
                pt["hemisphere"], pt["zone"], pt["easting"], pt["northing"]
            )
            waypoints.append({
                "latitude": lat,
                "longitude": lon,
                "altitude": alt_val,
                "easting": pt["easting"],
                "northing": pt["northing"],
            })
        return waypoints


def evaluate_simplification(original: list[dict], simplified: list[dict]) -> dict:
    """Compute distance deviation and length metrics of a simplified track vs. original."""
    orig_xy = [(p["easting"], p["northing"]) for p in original]
    simp_xy = [(p["easting"], p["northing"]) for p in simplified]

    # Map simplified waypoints back to original indices by timestamp
    orig_ts = {p["timestamp"]: idx for idx, p in enumerate(original)}
    simp_indices = [orig_ts[p["timestamp"]] for p in simplified]

    dists = []
    bearing_errs = []
    for seg_i in range(len(simp_indices) - 1):
        i0 = simp_indices[seg_i]
        i1 = simp_indices[seg_i + 1]
        a = orig_xy[i0]
        b = orig_xy[i1]
        seg_len = math.hypot(b[0] - a[0], b[1] - a[1])
        seg_brg = _bearing_deg(a, b) if seg_len > 0.2 else None

        for k in range(i0, i1 + 1):
            dists.append(_point_to_segment_distance(orig_xy[k], a, b))
            if seg_brg is not None and 0 < k < len(orig_xy) - 1:
                k0 = max(0, k - 4)
                k1 = min(len(orig_xy) - 1, k + 4)
                if math.hypot(orig_xy[k1][0] - orig_xy[k0][0], orig_xy[k1][1] - orig_xy[k0][1]) > 0.2:
                    bearing_errs.append(_angle_diff_deg(_bearing_deg(orig_xy[k0], orig_xy[k1]), seg_brg))

    orig_len = sum(
        math.hypot(orig_xy[i + 1][0] - orig_xy[i][0], orig_xy[i + 1][1] - orig_xy[i][1])
        for i in range(len(orig_xy) - 1)
    )
    simp_len = sum(
        math.hypot(simp_xy[i + 1][0] - simp_xy[i][0], simp_xy[i + 1][1] - simp_xy[i][1])
        for i in range(len(simp_xy) - 1)
    )

    rmse = math.sqrt(sum(d * d for d in dists) / len(dists)) if dists else 0.0
    mean_b = sum(bearing_errs) / len(bearing_errs) if bearing_errs else 0.0
    p95_b = sorted(bearing_errs)[int(0.95 * len(bearing_errs))] if bearing_errs else 0.0

    return {
        "waypoints": len(simplified),
        "reduction_pct": 100.0 * (1.0 - len(simplified) / len(original)),
        "max_dist_m": max(dists) if dists else 0.0,
        "rmse_dist_m": rmse,
        "mean_bearing_err_deg": mean_b,
        "p95_bearing_err_deg": p95_b,
        "orig_len_m": orig_len,
        "simp_len_m": simp_len,
    }


def save_waypoints_csv(waypoints: list[dict], output_csv: Path) -> None:
    """Save geographic waypoints (lat, lon, alt) to CSV."""
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["latitude", "longitude", "altitude"])
        writer.writeheader()
        for wp in waypoints:
            writer.writerow({
                "latitude": f"{wp['latitude']:.7f}",
                "longitude": f"{wp['longitude']:.7f}",
                "altitude": f"{wp['altitude']:.2f}",
            })


def plot_comparison(
    original: list[dict],
    methods: list[tuple[str, list[dict], dict]],
    output_png: Path,
) -> None:
    """Plot visual comparison of the three simplification methods against the clean track."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    e0 = min(p["easting"] for p in original)
    n0 = min(p["northing"] for p in original)
    orig_e = [p["easting"] - e0 for p in original]
    orig_n = [p["northing"] - n0 for p in original]

    pad = 5.0
    xlim = (min(orig_e) - pad, max(orig_e) + pad)
    ylim = (min(orig_n) - pad, max(orig_n) + pad)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.9))
    colors = ["#d62728", "#2ca02c", "#9467bd"]

    for ax, (title, simp, stats), col in zip(axes, methods, colors):
        simp_e = [p["easting"] - e0 for p in simp]
        simp_n = [p["northing"] - n0 for p in simp]

        ax.plot(orig_e, orig_n, color="#bbbbbb", linewidth=2.0, label="Clean track (1440 pts)", zorder=1)
        ax.plot(simp_e, simp_n, color=col, linewidth=1.6, marker="o", markersize=4.5,
                label=f"Simplified ({stats['waypoints']} wpts)", zorder=2)
        ax.scatter([simp_e[0]], [simp_n[0]], color="#1f77b4", s=55, marker="^", label="Start", zorder=3)
        ax.scatter([simp_e[-1]], [simp_n[-1]], color="#ff7f0e", s=50, marker="s", label="End", zorder=3)

        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel(f"Local Easting [m] (+{e0:.0f} m)")
        ax.set_ylabel(f"Local Northing [m] (+{n0:.0f} m)")
        ax.set_title(
            f"{title}\n"
            f"max err = {stats['max_dist_m']:.2f} m, RMSE = {stats['rmse_dist_m']:.2f} m",
            fontsize=9.5,
        )
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(loc="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_png, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    mod7_dir = Path(__file__).resolve().parent
    clean_csv = mod7_dir / "gnss_track_utm_clean.csv"
    clean_track = load_utm_track(clean_csv)

    simplifier = TrackSimplifier(default_altitude=30.0)

    # 1. Maximum waypoints allowed (Visvalingam-Whyatt)
    m1 = simplifier.simplify_max_waypoints(clean_track, max_waypoints=20)
    s1 = evaluate_simplification(clean_track, m1)

    # 2. Minimize distance deviation (Ramer-Douglas-Peucker)
    m2 = simplifier.simplify_distance(clean_track, max_distance_m=2.0)
    s2 = evaluate_simplification(clean_track, m2)

    # 3. Minimize distance and bearing angle deviation
    m3 = simplifier.simplify_distance_and_bearing(clean_track, max_distance_m=2.0, max_bearing_deg=25.0)
    s3 = evaluate_simplification(clean_track, m3)

    methods = [
        ("1. Max Waypoints (VW, N=20)", m1, s1),
        ("2. Distance Dev. (RDP, 2.0 m)", m2, s2),
        ("3. Dist. + Bearing (2.0 m, 25°)", m3, s3),
    ]

    print(f"{'Method':<32} {'Wpts':>5} {'Red%':>7} {'MaxD[m]':>8} {'RMSE[m]':>8} {'MeanB[°]':>9} {'P95B[°]':>8} {'Len[m]':>8}")
    print("-" * 92)
    for name, _, st in methods:
        print(
            f"{name:<32} {st['waypoints']:>5d} {st['reduction_pct']:>6.1f}% "
            f"{st['max_dist_m']:>8.2f} {st['rmse_dist_m']:>8.2f} "
            f"{st['mean_bearing_err_deg']:>9.1f} {st['p95_bearing_err_deg']:>8.1f} "
            f"{st['simp_len_m']:>8.1f}"
        )
    print(f"Original clean track length: {s1['orig_len_m']:.1f} m")

    # Visual comparison plot
    plot_comparison(clean_track, methods, mod7_dir / "step4_4_simplification_comparison.png")

    # Step 4.5: Save geodetic waypoints for each method (default static altitude = 30 m)
    save_waypoints_csv(simplifier.to_geodetic_waypoints(m1), mod7_dir / "waypoints_method1_vw.csv")
    save_waypoints_csv(simplifier.to_geodetic_waypoints(m2), mod7_dir / "waypoints_method2_rdp.csv")
    save_waypoints_csv(simplifier.to_geodetic_waypoints(m3), mod7_dir / "waypoints_method3_dist_bearing.csv")
    print("\nSaved comparison plot and geodetic waypoint CSVs.")
