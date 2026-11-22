# Module 8 Report: Drone Radio Antennas (434 MHz Half-Wave Dipole)

**Course:** Introduction to Drone Technology (IDT) — Fall 2026  
**Team:** Team 07  
**Reference Materials:** `idt_module_8.pdf` (Course notes, module 7: *Drone radio antennas*), `Understanding_Standing_Wave_Ratios.pdf`  
**Date:** 2026-11-20  
**Status:** In Progress (Lab & Report Draft)

---

## 1. Theory & Pre-Lab Calculations

### 1.1 Wavelength & Dipole Dimensions at 434 MHz
The target resonating frequency is the default center frequency of the MRO telemetry radio modems used for the UAS C2 link: $f = 434\text{ MHz}$.

Using the wave relation $f \cdot \lambda = \nu$, with $\nu \approx c = 3 \times 10^8\text{ m/s}$:

$$\lambda = \frac{c}{f} = \frac{3 \times 10^8\text{ m/s}}{434 \times 10^6\text{ Hz}} \approx 0.6912\text{ m} = 69.12\text{ cm}$$

- **Electrical half-wavelength ($\frac{1}{2}\lambda$):** $\approx 34.56\text{ cm}$ ($345.6\text{ mm}$)
- **Electrical quarter-wavelength per radial ($\frac{1}{4}\lambda$):** $\approx 17.28\text{ cm}$ ($172.8\text{ mm}$)

**Why the physical tuned length is shorter than $\frac{1}{2}\lambda$:**  
In practice, the resonant physical length of a wire dipole is slightly shorter than the theoretical free-space $\frac{1}{2}\lambda$ because of finite conductor thickness, any wire insulation/end effects (capacitive end loading / velocity factor), and electromagnetic interaction with the wooden mounting dowel, coax cable, ground, or nearby conductors. For construction, each radial is therefore initially cut slightly longer than $\frac{1}{4}\lambda$ (e.g., $\sim 185\text{–}190\text{ mm}$) so that the initial resonant frequency starts below $434\text{ MHz}$ and can be tuned upward iteratively by trimming wire from the ends.

### 1.2 Dipole Characteristics & Standing Wave Ratio (SWR)
- **Theoretical Gain & Radiation Pattern:** A free-space half-wave dipole has a toroidal radiation pattern with a peak gain of **$2.15\text{ dBi}$** perpendicular to the antenna axis (and nulls along the axis).
- **Impedance:** A center-fed half-wave dipole at resonance is purely resistive with a radiation resistance of approximately **$70\ \Omega$**, feeding a **$50\ \Omega$** coaxial transmission line. Above resonance the antenna impedance becomes inductive; below resonance it becomes capacitive.
- **Transmitted & Reflected Power:**
  $$p_t = p_f - p_r$$
  where $p_f$ is the forwarded power from the transmitter, $p_r$ is the power reflected back from the antenna, and $p_t$ is the power transmitted by the antenna.
- **SWR Formulas:**
  $$\text{SWR} = \frac{V_{\max}}{V_{\min}} = \frac{1 + \sqrt{\frac{P_r}{P_f}}}{1 - \sqrt{\frac{P_r}{P_f}}}, \qquad \frac{P_r}{P_f} = \left(\frac{S - 1}{S + 1}\right)^2$$
- **Mismatch Return Loss:**
  $$r_l = 10 \log_{10}\left(\frac{p_t}{p_f}\right) = 10 \log_{10}\left(1 - \left(\frac{S - 1}{S + 1}\right)^2\right)$$
- **Practical Thresholds & Amplifier Protection:**
  - **$\text{SWR} \le 1.5:1$:** Considered well matched; mismatch reflection loss at the antenna is negligible ($< 0.18\text{ dB}$), and the transmitter operates at full nominal output power ($P_n$).
  - **$\text{SWR} > 1.5:1$:** While pure mismatch reflection loss at $\text{SWR} = 3:1$ is only $\approx -1.25\text{ dB}$ ($25\%$ reflected), semiconductor transmitter output stages cannot absorb reflected power and activate protective foldback circuitry that limits forwarded power ($P_f \approx \frac{1}{(S - 0.5)^2} P_n$). At $\text{SWR} = 3:1$, this foldback drops forwarded power by $\approx 8\text{ dB}$, resulting in a severe total system loss of $\approx 9.25\text{ dB}$. (Note also that a lossy coax cable attenuates both forward and reflected waves, making the SWR measured at the transmitter appear artificially lower than the actual SWR at the antenna.)

---

## 2. Exercise 3.1 — Antenna Construction

### Construction Parameters
| Parameter | Value / Notes |
|---|---|
| Target Resonant Frequency ($f_r$) | $434\text{ MHz}$ |
| Conductor / Wire Type | Standard PVC-insulated electrical wire (green-yellow) |
| Coax Cable Prep (Insulation / Braid / Dielectric) | Stripped ~5–7 mm black outer jacket, braid folded back and soldered to Radial 2, ~3–4 mm white dielectric removed and center conductor soldered to Radial 1; continuity/short verified with Keysight U1231A multimeter (no short between radials, continuity confirmed to SMA connector). |
| Initial Length — Radial 1 (Center Conductor) | 190 mm (19.0 cm) |
| Initial Length — Radial 2 (Braid) | 190 mm (19.0 cm) |
| Total Initial Tip-to-Tip Length | 380 mm (38.0 cm) |
| Mounting & Strain Relief Notes | Mounted straight along round wooden dowel with white electrical tape (tips kept untaped during trimming, taped at end); coax cable routed cleanly at 90° perpendicular to the dipole with gentle bend radius (> soda can). |

### Required Photo Checklist (Section 3.1)
- [ ] **Photo 1 — Constructed Antenna (Pre-Tuning):** `[TBD — insert photo path/caption]`

---

## 3. Exercise 3.2 — Antenna Tuning (RigExpert)

### Iterative Tuning Log
| Step | Trim per Radial (mm) | Radial 1 / Radial 2 Length (mm) | Scan Range ($\pm\text{MHz}$) | Measured $f_r$ (MHz) | Min SWR | SWR @ 434 MHz | Photo / Notes |
|---|---|---|---|---|---|---|---|
| 0 (Initial) | 0 | 190 / 190 | $\pm 100$ | ~340 | ~1.4 | ~7 | [swr_scan_0_initial.jpg](images/swr_scan_0_initial.jpg) — clean free-hanging scan (initial held/near-desk check distorted dip to ~363 MHz, SWR ~2.6) |
| 1 | 10 | 180 / 180 | $\pm 100$ | ~366 | ~1.13 | ~5.5 | [swr_scan_1_180mm.jpg](images/swr_scan_1_180mm.jpg) — sharp dip, +26 MHz shift (~2.6 MHz/mm) |
| 2 | 10 | 170 / 170 | $\pm 100$ | ~391 | ~1.15 | ~4.0 | [swr_scan_2_170mm.jpg](images/swr_scan_2_170mm.jpg) — +25 MHz shift (~2.5 MHz/mm) |
| 3 | 5 | 165 / 165 | $\pm 50$ | ~400 | ~1.18 | ~3.0 | [swr_scan_3_165mm.jpg](images/swr_scan_3_165mm.jpg) — narrowed to $\pm 50\text{ MHz}$ |
| 4 | 6 | 159 / 159 | $\pm 50$ | ~411 | ~1.28 | ~2.5 | [swr_scan_4_159mm.jpg](images/swr_scan_4_159mm.jpg) — +11 MHz shift (~1.8–2.0 MHz/mm) |
| 5 | 5 | 154 / 154 | $\pm 25$ | ~426.5 | ~1.28 | ~1.40 | [swr_scan_5_154mm.jpg](images/swr_scan_5_154mm.jpg) — narrowed to $\pm 25\text{ MHz}$, SWR @ 434 MHz already $< 1.5$ |
| 6 | 2 | 152 / 152 | $\pm 25$ | ~437 | ~1.23 | ~1.33 | [swr_scan_6_152mm.jpg](images/swr_scan_6_152mm.jpg) — slight overshoot (+3 MHz above 434 MHz), SWR @ 434 MHz already ~1.33 (< 1.5) |
| Final | 0 (90° coax + taped ends) | 152 / 152 | $\pm 25$ | ~433 | ~1.15 | ~1.18 | [swr_scan_final_434mhz.jpg](images/swr_scan_final_434mhz.jpg) — clean 90° coax exit & electrical tape on ends pulled dip dead-center onto 434 MHz |

### Final Tuned Antenna Summary
- **Final Radial Lengths (Radial 1 / Radial 2):** `152 mm / 152 mm` *(from cumulative trims off 190 mm)*
- **Final Total Physical Dipole Length ($L_{\text{phys}}$):** `304 mm` (`30.4 cm`)
- **Empirical Shortening / Velocity Factor ($L_{\text{phys}} / \frac{1}{2}\lambda$):** `0.880` (`304 / 345.6`, where $\frac{1}{2}\lambda = 345.6\text{ mm}$; shorter than free-space $\frac{1}{2}\lambda$ due to PVC wire insulation, electrical tape end-loading, and wooden dowel dielectric)
- **Final Resonant Frequency ($f_r$):** `~433 MHz` (centered right on target `434 MHz`)
- **Final SWR at $434\text{ MHz}$ ($S$):** `~1.18:1` (min SWR `~1.15:1`)
- **Calculated Reflected Power ($P_r / P_f$):** `0.68%` $\left(\left(\frac{1.18 - 1}{1.18 + 1}\right)^2 = 0.00682\right)$ → **`99.32%` transmitted power**
- **Calculated Mismatch Return Loss ($r_l$):** `-0.03 dB` $\left(10 \log_{10}(0.9932)\right)$ — negligible loss, well below the $1.5:1$ threshold so the transmitter operates at full nominal output power.

### Required Photo Checklist (Section 3.2)
- [x] **Photo 2 — First SWR Scan ($\pm 100\text{ MHz}$ around $434\text{ MHz}$):** [swr_scan_0_initial.jpg](images/swr_scan_0_initial.jpg)
- [x] **Photo 3 — Intermediate SWR Scan(s):** [swr_scan_1_180mm.jpg](images/swr_scan_1_180mm.jpg), [swr_scan_2_170mm.jpg](images/swr_scan_2_170mm.jpg), [swr_scan_3_165mm.jpg](images/swr_scan_3_165mm.jpg), [swr_scan_4_159mm.jpg](images/swr_scan_4_159mm.jpg), [swr_scan_5_154mm.jpg](images/swr_scan_5_154mm.jpg), [swr_scan_6_152mm.jpg](images/swr_scan_6_152mm.jpg)
- [x] **Photo 4 — Final SWR Scan ($\pm 25\text{ MHz}$ around $434\text{ MHz}$):** [swr_scan_final_434mhz.jpg](images/swr_scan_final_434mhz.jpg)
- [x] **Photo 5 — Final Tuned Antenna:** [antenna_final.jpg](images/antenna_final.jpg)

---

## 4. Exercise 3.3 — Antenna Near-Field Obstacles

### Q1: Hand approaching along coax ($< 0.5\text{ m}$) — What happens to the SWR response?
As the hand moves closer than $0.5\text{ m}$ along the coaxial cable toward the antenna, the SWR across the band increases and the resonance dip noticeably flattens/broadens:
- **Free-hanging baseline ($\ge 0.5\text{ m}$):** min SWR $\approx 1.15$, SWR @ $434\text{ MHz} \approx 1.18$ ([swr_scan_final_434mhz.jpg](images/swr_scan_final_434mhz.jpg)).
- **Hand ~15 cm closer (~35 cm from antenna, [nearfield_hand_1.jpg](images/nearfield_hand_1.jpg)):** min SWR rises to $\approx 1.30$, and SWR @ $434\text{ MHz}$ rises to $\approx 1.35$.
- **Hand another ~15 cm closer (~20 cm from antenna, [nearfield_hand_2.jpg](images/nearfield_hand_2.jpg)):** min SWR rises to $\approx 1.62$ (above the $1.5:1$ threshold), SWR @ $434\text{ MHz}$ rises to $\approx 1.72$, and the entire SWR curve significantly broadens/flattens.

*Physical explanation:* Without a balun on the coax feed, the hand couples into the antenna's reactive near field and common-mode currents on the coax shield. Human tissue acts as a lossy dielectric/conductor that absorbs RF energy (reducing the antenna's quality factor $Q$ and flattening the dip) while altering the feedpoint impedance.

### Q2: Hand approaching along coax ($< 0.5\text{ m}$) — What happens to the antenna's center (resonant) frequency?
The resonant frequency $f_r$ shifts monotonically **downward (to the left)** as the hand approaches:
- **Baseline ($\ge 0.5\text{ m}$):** $f_r \approx 433\text{ MHz}$
- **Hand ~35 cm:** $f_r \approx 431\text{ MHz}$
- **Hand ~20 cm:** $f_r \approx 426\text{–}427\text{ MHz}$

*Physical explanation:* The high-permittivity human hand introduces additional shunt capacitance to the dipole's near field (capacitive loading), which effectively increases the antenna's electrical length and lowers its resonant frequency.

### Q3: Conducting obstacles at various distances — What happens?
| Obstacle | Distance | Position / Angle | Effect on $f_r$ | Effect on SWR | Notes |
|---|---|---|---|---|---|
| Office chair (metal frame) — Scan 1 | ~15 cm step (strong coupling) | Near metal chair frame | Strong downward shift to $\approx 413\text{ MHz}$ ($\approx -20\text{ MHz}$) | Min SWR $\approx 1.30$; SWR @ $434\text{ MHz}$ jumps to $\approx 2.2$ | [nearfield_chair_1.jpg](images/nearfield_chair_1.jpg) — severe detuning |
| Office chair (metal frame) — Scan 2 | ~15 cm step (moderate coupling) | Near office chair | Slight shift to $\approx 432\text{ MHz}$ | Broadened curve; min SWR $\approx 1.55$, SWR @ $434\text{ MHz} \approx 1.60$ | [nearfield_chair_2.jpg](images/nearfield_chair_2.jpg) — moderate impedance mismatch/broadening |

**Summary Answer:**  
Introducing conducting obstacles into the antenna's near field causes strong electromagnetic coupling and boundary reflections that alter both the radiation resistance and reactance. Depending on distance and orientation relative to the antenna's E- and H-fields, conducting objects severely detune the resonant frequency (shifting $f_r$ by up to $\approx -20\text{ MHz}$ to $\approx 413\text{ MHz}$ in the strongly coupled chair measurement) and raise SWR at $434\text{ MHz}$ above the practical $1.5:1$ matching limit (up to $\approx 2.2:1$), causing noticeable mismatch and potential TX power foldback.

### Q4: At which angles is the antenna most sensitive to near-field obstacles?
Based on the half-wave dipole's radiation pattern (Figure 1 in `idt_module_8.pdf`) and near-field distribution:
- **Most sensitive at $90^\circ$ perpendicular to the dipole axis (broadside / equatorial plane):** Peak gain ($2.15\text{ dBi}$) and radiated field intensity lie perpendicular to the center of the dipole. Conducting obstacles positioned broadside — especially when oriented **parallel** to the dipole radials (matching its linear polarization) — experience strong induced currents, causing the largest impedance mismatch and resonant frequency detuning.
- **Least sensitive at $0^\circ$ and $180^\circ$ along the dipole axis:** A half-wave dipole has radiation nulls along its own axis, so far-field/radiative coupling along the axis is minimal compared to broadside obstacles at comparable distances.
- **Reactive near-field caveat ($< \lambda / (2\pi) \approx 11\text{ cm}$ at $434\text{ MHz}$):** Within the immediate reactive near field, the electric field ($E$) is strongly concentrated at the high-voltage tips of the radials while current and magnetic field ($H$) peak at the center feedpoint; touching or bringing conductors/dielectrics within a few centimeters of the radial tips therefore still causes strong capacitive detuning even near the axis.

---

## 5. Exercise 3.4 — Outdoor Range Test

### Test Setup & Logging Configuration
| Parameter | Value / Notes |
|---|---|
| Test Location | `[TBD]` |
| Weather / Environment | `[TBD]` |
| Telemetry Modem TX Power | `[TBD] dBm` (default $20\text{ dBm}$, reduce equally on both modems if link does not drop out within test area) |
| Antenna Polarization / Orientation | `[TBD]` (e.g., vertical/horizontal, keep consistent across reference & dipole runs) |
| Drone Subteam Setup | Flight controller, GNSS, telemetry modem, power source |
| Ground Station Subteam Setup | ROS2 laptop, telemetry modem, logging nodes |
| ROS2 Logging Scripts | [log_global_pos.py](log_global_pos.py) & [log_radio_rssi.py](log_radio_rssi.py) (standalone Module 8 scripts adapted from Module 7's `get_global_pos.py` & `get_radio_rssi.py`) |

### Range Test Measurements Summary
| Configuration | Max Link Distance (m) | Ground RSSI Trend | Remote RSSI Trend | Log File / Notes |
|---|---|---|---|---|
| Reference (Issued Antennas on Both) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |
| Custom 434 MHz Dipole on Ground Station | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |

### Required Photos & Plots Checklist (Section 3.4)
- [ ] **Photo 6 — Outdoor Test Scenario (antennas, mounting, orientation, surroundings):** `[TBD]`
- [ ] **Plot 1 — Reference Antennas: RSSI & Remote RSSI (dB) vs. Distance (m):** `[TBD]`
- [ ] **Plot 2 — Custom Dipole Antenna: RSSI & Remote RSSI (dB) vs. Distance (m):** `[TBD]`
- [ ] **Plot 3 — Direct Comparison (Reference vs. Custom Dipole RSSI vs. Distance):** `[TBD]`

### Q5: How much higher gain does your antenna have compared to the issued antennas?
`[TBD]`

*(Analysis note: Estimate relative gain $\Delta G\text{ (dB)}$ from the measured difference in RSSI / Remote RSSI in dB between the custom dipole and the issued ground antenna at equivalent distances in the linear/clear-LOS region, and cross-check against the observed increase in maximum communication range using FSPL $\Delta\text{FSPL} = 20 \log_{10}(d_{\text{dipole}} / d_{\text{ref}})$.)*
