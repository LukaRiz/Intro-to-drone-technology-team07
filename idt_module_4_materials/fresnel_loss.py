"""
Fresnel Zone Loss – Section 3.2.4
===================================
Scenario 1: Drone at 50 m, 400 m horizontal distance, TX at 0.5 m (operator sitting).
Scenario 2: Standing operator, drone at 200 m, building ridge at 100 m.

Fresnel zone radius at obstacle point (d1 from TX, d2 to RX):
    F1 = sqrt(lambda * d1 * d2 / (d1 + d2))

40% blockage rule: obstacle must be at least 0.6 * F1 BELOW the LOS.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

C = 3e8  # speed of light [m/s]

LINKS = [
    {"label": "433 MHz – Telemetry",  "freq_hz": 433e6,  "color": "#EE7733", "ls": "-"},
    {"label": "2.4 GHz – C2",         "freq_hz": 2.4e9,  "color": "#0077BB", "ls": "--"},
    {"label": "5.8 GHz – Video",       "freq_hz": 5.8e9,  "color": "#009988", "ls": "-."},
]

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1
# ─────────────────────────────────────────────────────────────────────────────
D1      = 400.0   # total link distance [m]
h_TX1   = 0.5     # TX height (operator sitting) [m]
h_RX1   = 50.0    # RX height (drone) [m]

N = 2000
x1 = np.linspace(0.5, D1 - 0.5, N)                      # avoid endpoints (F1=0)
h_los1 = h_TX1 + (h_RX1 - h_TX1) * x1 / D1              # LOS height above ground

print("=" * 60)
print("SCENARIO 1  –  Drone 50 m / 400 m / TX 0.5 m")
print("=" * 60)
print(f"{'Link':<25} {'x_worst [m]':>12} {'F1_worst [m]':>13} "
      f"{'60%F1 [m]':>10} {'clearance [m]':>14} {'Result':>10}")
print("-" * 88)

worst_results_1 = []

for link in LINKS:
    lam = C / link["freq_hz"]
    F1  = np.sqrt(lam * x1 * (D1 - x1) / D1)
    # ratio = clearance / F1  →  minimise
    ratio = h_los1 / F1
    idx   = np.argmin(ratio)
    xw    = x1[idx]
    F1w   = F1[idx]
    hw    = h_los1[idx]
    ok    = "CLEAR" if hw >= 0.6 * F1w else "BLOCKED"
    print(f"{link['label']:<25} {xw:>12.2f} {F1w:>13.3f} "
          f"{0.6*F1w:>10.3f} {hw:>14.3f} {ok:>10}")
    worst_results_1.append((link, xw, F1w, hw))

# ── Figure: LOS height vs 60 % F1 envelope ──────────────────────────────────
fig1, ax1 = plt.subplots(figsize=(10, 5))

ax1.fill_between(x1, 0, h_los1, alpha=0.08, color="grey", label="Ground clearance")
ax1.plot(x1, h_los1, "k-", lw=1.5, label="LOS height")

for link, xw, F1w, hw in worst_results_1:
    lam = C / link["freq_hz"]
    F1  = np.sqrt(lam * x1 * (D1 - x1) / D1)
    ax1.plot(x1, 0.6 * F1, color=link["color"], lw=1.8, ls=link["ls"],
             label=f"60 % $F_1$ – {link['label']}")
    ax1.scatter([xw], [0.6 * F1w], s=60, color=link["color"], zorder=5)

ax1.axhline(0, color="black", lw=0.8)
ax1.set_xlabel("Horizontal distance from operator (m)")
ax1.set_ylabel("Height above ground (m)")
ax1.set_title("Scenario 1 – LOS clearance vs 60 % first Fresnel zone radius\n"
              "Drone 50 m / Distance 400 m / Operator TX 0.5 m")
ax1.legend(fontsize=8, loc="center right")
ax1.set_xlim(0, D1)
ax1.set_ylim(-2, 55)
ax1.grid(True, ls=":", alpha=0.6)

fig1.tight_layout()
p1 = os.path.join(OUT_DIR, "fresnel_loss_scenario1.pdf")
fig1.savefig(p1, dpi=150)
fig1.savefig(p1.replace(".pdf", ".png"), dpi=150)
print(f"\nSaved: {p1}")

# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2
# ─────────────────────────────────────────────────────────────────────────────
D2   = 200.0   # total link distance [m]
d1_2 = 100.0   # TX → ridge [m]
d2_2 = 100.0   # ridge → RX [m]

print("\n" + "=" * 60)
print("SCENARIO 2  –  Building ridge at 100 m, drone at 200 m")
print("=" * 60)
print(f"  d1 = {d1_2} m  |  d2 = {d2_2} m  |  D = {D2} m")
print(f"{'Link':<25} {'lambda [m]':>11} {'F1 [m]':>8} "
      f"{'60%F1 [m]':>10}  (required clearance)")
print("-" * 65)

results_2 = []
for link in LINKS:
    lam = C / link["freq_hz"]
    F1  = np.sqrt(lam * d1_2 * d2_2 / (d1_2 + d2_2))
    clr = 0.6 * F1
    print(f"{link['label']:<25} {lam:>11.4f} {F1:>8.3f} {clr:>10.3f}")
    results_2.append((link, lam, F1, clr))

# ── Figure: required clearance bar chart ────────────────────────────────────
fig2, ax2 = plt.subplots(figsize=(7, 4.5))

labels   = [r["label"] for r, *_ in results_2]
clearances = [clr for _, _, _, clr in results_2]
colors     = [r["color"] for r, *_ in results_2]
bars = ax2.bar(labels, clearances, color=colors, width=0.5, zorder=3)

for bar, val in zip(bars, clearances):
    ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.05,
             f"{val:.2f} m", ha="center", va="bottom", fontsize=10, fontweight="bold")

ax2.set_ylabel("Required visual clearance above ridge line (m)")
ax2.set_title("Scenario 2 – Required clearance for 60 % first Fresnel zone\n"
              "Building ridge at 100 m, drone at 200 m")
ax2.set_ylim(0, max(clearances) * 1.25)
ax2.grid(True, axis="y", ls=":", alpha=0.6)
ax2.tick_params(axis="x", labelsize=9)

fig2.tight_layout()
p2 = os.path.join(OUT_DIR, "fresnel_loss_scenario2.pdf")
fig2.savefig(p2, dpi=150)
fig2.savefig(p2.replace(".pdf", ".png"), dpi=150)
print(f"Saved: {p2}")

plt.close("all")
print("\nDone.")
