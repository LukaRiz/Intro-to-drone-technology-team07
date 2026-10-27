"""
Fresnel Zone Plotting – Section 3.2.3
======================================
Plots the first Fresnel zone radius along the propagation path for three
drone radio links:
  • 2.4 GHz  – C2 (Command and Control) link
  • 433 MHz  – Telemetry downlink
  • 5.8 GHz  – Video downlink

The radius of the n-th Fresnel zone at a point that is d1 from the TX and
d2 from the RX is:

    F_n = sqrt( n * lambda * d1 * d2 / (d1 + d2) )

For n = 1 (first Fresnel zone) and a fixed total distance D = d1 + d2,
the profile is swept along the path.

Reference:
    Parsons, J. D. (2000). The Mobile Radio Propagation Channel (2nd ed.).
    Wiley. [Equation 2.32]
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")          # non-interactive backend – safe on all platforms
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
SPEED_OF_LIGHT = 3e8          # m/s

LINKS = [
    {"label": "2.4 GHz – C2 link",        "freq_hz": 2.4e9, "color": "#0077BB", "dist_km": 1.0},
    {"label": "433 MHz – Telemetry link",  "freq_hz": 433e6, "color": "#EE7733", "dist_km": 1.0},
    {"label": "5.8 GHz – Video downlink",  "freq_hz": 5.8e9, "color": "#009988", "dist_km": 1.0},
]

TOTAL_DISTANCE_M = 1000.0     # link distance [m]
N_POINTS = 500                # resolution along the path

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def fresnel_radius(freq_hz: float, d_total: float, n: int = 1) -> tuple:
    """
    Return (x, F_n) arrays for the n-th Fresnel zone profile.

    Parameters
    ----------
    freq_hz : carrier frequency [Hz]
    d_total : total TX-RX distance [m]
    n       : Fresnel zone order (default 1)

    Returns
    -------
    x   : position along the path, centred at 0 [m]
    F_n : Fresnel zone radius [m]
    """
    wavelength = SPEED_OF_LIGHT / freq_hz
    d1 = np.linspace(0.01 * d_total, 0.99 * d_total, N_POINTS)
    d2 = d_total - d1
    F = np.sqrt(n * wavelength * d1 * d2 / (d_total))
    x = d1 - d_total / 2          # centre at 0
    return x, F


# ---------------------------------------------------------------------------
# Figure 1 – All three links on one axes (comparison)
# ---------------------------------------------------------------------------
fig1, ax1 = plt.subplots(figsize=(10, 5))

for link in LINKS:
    x, F = fresnel_radius(link["freq_hz"], TOTAL_DISTANCE_M)
    ax1.plot(x, F,  color=link["color"], lw=2, label=link["label"])
    ax1.plot(x, -F, color=link["color"], lw=2)
    ax1.fill_between(x, F, -F, color=link["color"], alpha=0.08)

ax1.axhline(0, color="black", lw=0.8, ls="--")
ax1.scatter([-TOTAL_DISTANCE_M / 2, TOTAL_DISTANCE_M / 2], [0, 0],
            s=80, zorder=5, color="black")
ax1.text(-TOTAL_DISTANCE_M / 2, -6, "TX", ha="center", fontsize=9)
ax1.text( TOTAL_DISTANCE_M / 2, -6, "RX", ha="center", fontsize=9)

ax1.set_xlabel("Position along the path (m, centred at mid-point)")
ax1.set_ylabel("Fresnel zone radius $F_1$ (m)")
ax1.set_title(
    "First Fresnel Zone – D = 1 km\n"
    "2.4 GHz C2 link, 433 MHz telemetry link, 5.8 GHz video downlink"
)
ax1.legend(loc="upper right")
ax1.grid(True, linestyle=":", alpha=0.6)
ax1.set_xlim(-TOTAL_DISTANCE_M / 2, TOTAL_DISTANCE_M / 2)

fig1.tight_layout()
out1 = os.path.join(OUTPUT_DIR, "fresnel_comparison.pdf")
fig1.savefig(out1, dpi=150)
out1_png = os.path.join(OUTPUT_DIR, "fresnel_comparison.png")
fig1.savefig(out1_png, dpi=150)
print(f"Saved: {out1}")
print(f"Saved: {out1_png}")


# ---------------------------------------------------------------------------
# Figure 2 – Three separate subplots (one per link)
# ---------------------------------------------------------------------------
fig2, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=True)

for ax, link in zip(axes, LINKS):
    x, F = fresnel_radius(link["freq_hz"], TOTAL_DISTANCE_M)
    lam = SPEED_OF_LIGHT / link["freq_hz"]
    F_max = np.max(F)

    ax.plot(x, F,  color=link["color"], lw=2)
    ax.plot(x, -F, color=link["color"], lw=2)
    ax.fill_between(x, F, -F, color=link["color"], alpha=0.15,
                    label=f"$F_1$ region  (max = {F_max:.1f} m)")

    # 60 % clearance line
    ax.plot(x, 0.6 * F,  color="red", lw=1.2, ls="--")
    ax.plot(x, -0.6 * F, color="red", lw=1.2, ls="--",
            label="60 % clearance threshold")

    ax.axhline(0, color="black", lw=0.8, ls="--")
    ax.scatter([-TOTAL_DISTANCE_M / 2, TOTAL_DISTANCE_M / 2], [0, 0],
               s=60, zorder=5, color="black")
    ax.text(-TOTAL_DISTANCE_M / 2, -F_max * 0.15, "TX", ha="center", fontsize=8)
    ax.text( TOTAL_DISTANCE_M / 2, -F_max * 0.15, "RX", ha="center", fontsize=8)

    ax.set_title(f"{link['label']}  |  λ = {lam*100:.1f} cm  |  "
                 f"$F_{{1,max}}$ = {F_max:.2f} m")
    ax.set_ylabel("$F_1$ radius (m)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, linestyle=":", alpha=0.6)

axes[-1].set_xlabel("Position along the path (m, centred at mid-point)")
fig2.suptitle("First Fresnel Zone Profiles – D = 1 km", fontsize=13, y=1.01)
fig2.tight_layout()

out2 = os.path.join(OUTPUT_DIR, "fresnel_subplots.pdf")
fig2.savefig(out2, dpi=150, bbox_inches="tight")
out2_png = os.path.join(OUTPUT_DIR, "fresnel_subplots.png")
fig2.savefig(out2_png, dpi=150, bbox_inches="tight")
print(f"Saved: {out2}")
print(f"Saved: {out2_png}")

plt.close("all")
print("Done.")
