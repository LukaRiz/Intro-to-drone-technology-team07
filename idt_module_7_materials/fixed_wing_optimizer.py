#!/usr/bin/env python3
"""
Module 7 - Step 4.7: Fixed-wing route optimization using cubic Hermite splines.

Takes the simplified UTM route (RDP) and adds interpolation waypoints only on
legs with significant entry/exit turn angles, producing a smooth path that
reduces sharp turns and overshooting for a fixed-wing UAS.
"""

import math
from pathlib import Path

from utm_converter import TrackUTMConverter, load_utm_track
from track_simplifier import TrackSimplifier
from qgc_exporter import QGCPlanExporter


class CubicHermiteSpline:
    """Cubic Hermite spline (matching hermite.py from course materials)."""

    @staticmethod
    def _v2d_scalar_mul(v: tuple[float, float], f: float) -> tuple[float, float]:
        return (v[0] * f, v[1] * f)

    @staticmethod
    def _v2d_add(v1: tuple[float, float], v2: tuple[float, float]) -> tuple[float, float]:
        return (v1[0] + v2[0], v1[1] + v2[1])

    def interpolate(
        self,
        p1: tuple[float, float],
        t1: tuple[float, float],
        p2: tuple[float, float],
        t2: tuple[float, float],
        steps: int,
    ) -> list[tuple[float, float]]:
        """Evaluate `steps` points along the cubic Hermite curve for s in [0, 1)."""
        pts = []
        for i in range(steps):
            s = i / float(steps)
            h1 = 2 * s**3 - 3 * s**2 + 1
            h2 = -2 * s**3 + 3 * s**2
            h3 = s**3 - 2 * s**2 + s
            h4 = s**3 - s**2

            v1 = self._v2d_scalar_mul(p1, h1)
            v2 = self._v2d_scalar_mul(p2, h2)
            v3 = self._v2d_scalar_mul(t1, h3)
            v4 = self._v2d_scalar_mul(t2, h4)

            p = self._v2d_add(self._v2d_add(self._v2d_add(v1, v2), v3), v4)
            pts.append(p)
        return pts


def _unit_vec(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    mag = math.hypot(dx, dy)
    if mag == 0.0:
        return (0.0, 0.0)
    return (dx / mag, dy / mag)


def _angle_between_deg(u: tuple[float, float], v: tuple[float, float]) -> float:
    dot = max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))
    return math.degrees(math.acos(dot))


class FixedWingOptimizer:
    """
    Smooths a simplified 2D UTM waypoint route for fixed-wing flight by
    inserting cubic Hermite spline waypoints on legs with sharp entry/exit angles.
    """

    def __init__(
        self,
        angle_threshold_deg: float = 15.0,
        tangent_scale: float = 0.6,
        min_interp_points: int = 2,
        max_interp_points: int = 4,
    ):
        self.angle_threshold_deg = angle_threshold_deg
        self.tangent_scale = tangent_scale
        self.min_interp_points = min_interp_points
        self.max_interp_points = max_interp_points
        self.spline = CubicHermiteSpline()

    def _compute_unit_tangents(self, pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
        """Compute smooth unit tangent direction at every waypoint."""
        n = len(pts)
        tangents = []
        for i in range(n):
            if i == 0:
                t = _unit_vec(pts[0], pts[1])
            elif i == n - 1:
                t = _unit_vec(pts[-2], pts[-1])
            else:
                u_in = _unit_vec(pts[i - 1], pts[i])
                u_out = _unit_vec(pts[i], pts[i + 1])
                avg = (u_in[0] + u_out[0], u_in[1] + u_out[1])
                mag = math.hypot(avg[0], avg[1])
                t = (avg[0] / mag, avg[1] / mag) if mag > 1e-9 else u_out
            tangents.append(t)
        return tangents

    def optimize(self, utm_waypoints: list[dict]) -> tuple[list[dict], list[tuple[float, float]]]:
        """
        Return:
          - optimized_waypoints: list of UTM dicts (original + added spline waypoints)
          - dense_curve: high-resolution spline polyline for visualization
        """
        if len(utm_waypoints) < 3:
            xy = [(p["easting"], p["northing"]) for p in utm_waypoints]
            return list(utm_waypoints), xy

        pts = [(p["easting"], p["northing"]) for p in utm_waypoints]
        unit_t = self._compute_unit_tangents(pts)

        hemi = utm_waypoints[0]["hemisphere"]
        zone = utm_waypoints[0]["zone"]
        letter = utm_waypoints[0]["letter"]
        alt = utm_waypoints[0]["altitude"]

        optimized = []
        dense_curve = []

        for i in range(len(pts) - 1):
            p1, p2 = pts[i], pts[i + 1]
            leg_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            leg_dir = _unit_vec(p1, p2)

            entry_angle = _angle_between_deg(unit_t[i], leg_dir)
            exit_angle = _angle_between_deg(leg_dir, unit_t[i + 1])
            max_angle = max(entry_angle, exit_angle)

            # Scale tangents proportionally to leg length
            scale = self.tangent_scale * leg_len
            t1 = (unit_t[i][0] * scale, unit_t[i][1] * scale)
            t2 = (unit_t[i + 1][0] * scale, unit_t[i + 1][1] * scale)

            # Always add original start waypoint of leg
            optimized.append({
                "hemisphere": hemi,
                "zone": zone,
                "letter": letter,
                "easting": p1[0],
                "northing": p1[1],
                "altitude": alt,
                "interpolated": False,
            })

            if max_angle >= self.angle_threshold_deg and leg_len > 3.0:
                # Choose 2..4 intermediate points proportional to turn angle
                n_extra = min(
                    self.max_interp_points,
                    max(self.min_interp_points, int(round(max_angle / 20.0))),
                )
                steps = n_extra + 1
                seg_pts = self.spline.interpolate(p1, t1, p2, t2, steps=steps)
                for sp in seg_pts[1:]:
                    optimized.append({
                        "hemisphere": hemi,
                        "zone": zone,
                        "letter": letter,
                        "easting": sp[0],
                        "northing": sp[1],
                        "altitude": alt,
                        "interpolated": True,
                    })
                dense_curve.extend(self.spline.interpolate(p1, t1, p2, t2, steps=25))
            else:
                dense_curve.append(p1)

        # Add final waypoint
        optimized.append({
            "hemisphere": hemi,
            "zone": zone,
            "letter": letter,
            "easting": pts[-1][0],
            "northing": pts[-1][1],
            "altitude": alt,
            "interpolated": False,
        })
        dense_curve.append(pts[-1])

        return optimized, dense_curve


def turn_angles(route: list[dict]) -> list[float]:
    """Compute turn angles [deg] at every interior waypoint of a route."""
    pts = [(p["easting"], p["northing"]) for p in route]
    angles = []
    for i in range(1, len(pts) - 1):
        u1 = _unit_vec(pts[i - 1], pts[i])
        u2 = _unit_vec(pts[i], pts[i + 1])
        angles.append(_angle_between_deg(u1, u2))
    return angles


def plot_fixed_wing(
    clean_track: list[dict],
    rdp_route: list[dict],
    fw_route: list[dict],
    dense_curve: list[tuple[float, float]],
    output_png: Path,
) -> None:
    """Plot full route comparison + zoomed view of the sharp southeast corner."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    e0 = min(p["easting"] for p in clean_track)
    n0 = min(p["northing"] for p in clean_track)

    orig_e = [p["easting"] - e0 for p in clean_track]
    orig_n = [p["northing"] - n0 for p in clean_track]
    rdp_e = [p["easting"] - e0 for p in rdp_route]
    rdp_n = [p["northing"] - n0 for p in rdp_route]
    fw_e = [p["easting"] - e0 for p in fw_route]
    fw_n = [p["northing"] - n0 for p in fw_route]
    interp_e = [p["easting"] - e0 for p in fw_route if p.get("interpolated")]
    interp_n = [p["northing"] - n0 for p in fw_route if p.get("interpolated")]
    curve_e = [p[0] - e0 for p in dense_curve]
    curve_n = [p[1] - n0 for p in dense_curve]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.2), gridspec_kw={"width_ratios": [1.15, 1]})

    def _plot_common(ax):
        ax.plot(orig_e, orig_n, color="#cccccc", linewidth=1.8, label="Cleaned GNSS track", zorder=1)
        ax.plot(rdp_e, rdp_n, color="#2ca02c", linestyle="--", linewidth=1.4, marker="o",
                markersize=4.5, label=f"RDP route ({len(rdp_route)} wpts)", zorder=2)
        ax.plot(curve_e, curve_n, color="#1f77b4", linewidth=1.6,
                label=f"Fixed-wing Hermite ({len(fw_route)} wpts)", zorder=3)
        ax.scatter(interp_e, interp_n, color="#d62728", s=24, marker="d",
                   label=f"Added spline wpts ({len(interp_e)})", zorder=4)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, linestyle="--", alpha=0.4)

    # Left: full loop
    _plot_common(ax1)
    ax1.set_xlabel(f"Local Easting [m] (+{e0:.0f} m, UTM 32U)")
    ax1.set_ylabel(f"Local Northing [m] (+{n0:.0f} m)")
    ax1.set_title("Fixed-Wing Route Optimization (Full Loop)")
    ax1.legend(loc="center", fontsize=8)

    # Right: zoom into bottom-right / south-east sharp turn
    _plot_common(ax2)
    ax2.set_xlim(35, 108)
    ax2.set_ylim(-6, 48)
    ax2.set_xlabel(f"Local Easting [m] (+{e0:.0f} m)")
    ax2.set_ylabel(f"Local Northing [m] (+{n0:.0f} m)")
    ax2.set_title("Zoomed View: Smooth Corner Transition")
    ax2.legend(loc="upper left", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_png, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    mod7_dir = Path(__file__).resolve().parent
    clean_track = load_utm_track(mod7_dir / "gnss_track_utm_clean.csv")

    simplifier = TrackSimplifier(default_altitude=30.0)
    rdp_route = simplifier.simplify_distance(clean_track, max_distance_m=2.0)

    optimizer = FixedWingOptimizer(angle_threshold_deg=15.0, tangent_scale=0.6)
    fw_route, dense_curve = optimizer.optimize(rdp_route)

    rdp_angles = turn_angles(rdp_route)
    fw_angles = turn_angles(fw_route)

    n_added = sum(1 for p in fw_route if p.get("interpolated"))
    print(f"RDP route:        {len(rdp_route)} waypoints | max turn = {max(rdp_angles):.1f}°, mean turn = {sum(rdp_angles)/len(rdp_angles):.1f}°")
    print(f"Fixed-wing route: {len(fw_route)} waypoints (+{n_added} added) | max turn = {max(fw_angles):.1f}°, mean turn = {sum(fw_angles)/len(fw_angles):.1f}°")

    # Save plot
    plot_fixed_wing(clean_track, rdp_route, fw_route, dense_curve, mod7_dir / "step4_7_fixed_wing.png")

    # Export fixed-wing QGC plan (vehicleType=1 for fixed-wing)
    fw_geo = simplifier.to_geodetic_waypoints(fw_route, static_altitude=30.0)
    exporter = QGCPlanExporter(firmware_type=12, vehicle_type=1, include_rtl=True)
    exporter.export(fw_geo, mod7_dir / "mission_fixed_wing.plan")
    print("Saved step4_7_fixed_wing.png and mission_fixed_wing.plan")
