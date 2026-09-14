"""Module 1, section 3.3 gyro exercises.

Tasks 3.3.1-3.3.3: integrate the measured z-axis angular velocity
using actual time differences and estimate and subtract static bias.
"""

from math import pi
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "imu_razor_data_yaw_90deg.txt"
PLOT_FILE = BASE / "pics" / "section_3_3" / "relative_yaw.png"


def load_yaw_data(path):
    timestamps = []
    gyro_z_values = []

    with path.open() as data:
        for line in data:
            csv = line.replace("*", ",").split(",")
            timestamps.append(float(csv[0]))
            gyro_z_values.append(int(csv[7]) / 14.375 * pi / 180.0)

    return timestamps, gyro_z_values


def integrate_gyro(timestamps, angular_velocities):
    angles = [0.0]

    for i in range(1, len(timestamps)):
        dt = timestamps[i] - timestamps[i - 1]
        angles.append(angles[-1] + angular_velocities[i] * dt)

    return angles


def save_plot(times, angles_degrees, path, title_text="Relative yaw from z-axis gyro", show_zero=True, corrected=None, show_turn_reference=False):
    width, height = 1200, 700
    left, right, top, bottom = 110, 40, 70, 90
    plot_width = width - left - right
    plot_height = height - top - bottom
    all_angles = angles_degrees + ([] if corrected is None else corrected)
    padding = max((max(all_angles) - min(all_angles)) * 0.05, 0.1)
    minimum = min(all_angles) - padding
    maximum = max(all_angles) + padding

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        normal = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
        title = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
    except OSError:
        normal = ImageFont.load_default()
        title = normal

    def point(time, angle):
        x = left + time / times[-1] * plot_width
        y = top + (maximum - angle) / (maximum - minimum) * plot_height
        return x, y

    for i in range(6):
        time = times[-1] * i / 5
        x, _ = point(time, 0)
        draw.line((x, top, x, top + plot_height), fill="#dddddd", width=1)
        draw.text((x, top + plot_height + 12), f"{time:.1f}", fill="#222222",
                  font=normal, anchor="ma")

    for i in range(6):
        angle = minimum + (maximum - minimum) * i / 5
        _, y = point(0, angle)
        draw.line((left, y, left + plot_width, y), fill="#dddddd", width=1)
        draw.text((left - 12, y), f"{angle:.1f}", fill="#222222",
                  font=normal, anchor="rm")

    # Dashed reference line makes the return to the starting angle clear.
    _, zero_y = point(0, 0)
    if show_zero and top <= zero_y <= top + plot_height:
        for x in range(left, left + plot_width, 18):
            draw.line((x, zero_y, min(x + 10, left + plot_width), zero_y),
                      fill="#777777", width=2)
        draw.text((left + plot_width - 8, zero_y + 6), "0 degrees",
                  fill="#555555", font=normal, anchor="ra")

    if show_turn_reference:
        _, turn_y = point(0, -90)
        for x in range(left, left + plot_width, 18):
            draw.line((x, turn_y, min(x + 10, left + plot_width), turn_y),
                      fill="#777777", width=2)
        draw.text((left + plot_width - 8, turn_y - 6), "-90 degrees",
                  fill="#555555", font=normal, anchor="rs")

    draw.line((left, top, left, top + plot_height), fill="#222222", width=2)
    draw.line((left, top + plot_height, left + plot_width, top + plot_height),
              fill="#222222", width=2)
    draw.line([point(t, a) for t, a in zip(times, angles_degrees)],
              fill="#2368a0", width=3)
    if corrected is not None:
        draw.line([point(t, a) for t, a in zip(times, corrected)],
                  fill="#d35400", width=3)
    draw.text((width / 2, 30), title_text,
              fill="#222222", font=title, anchor="ma")
    draw.text((width / 2, height - 24), "Time (s)", fill="#222222",
              font=normal, anchor="ma")
    label = Image.new("RGBA", (240, 40), (255, 255, 255, 0))
    ImageDraw.Draw(label).text((120, 20), "Angle (degrees)", fill="#222222",
                              font=normal, anchor="mm")
    label = label.rotate(90, expand=True)
    image.paste(label, (12, (height - label.height) // 2), label)

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def main():
    timestamps, gyro_z = load_yaw_data(DATA_FILE)
    angles = integrate_gyro(timestamps, gyro_z)
    time = [value - timestamps[0] for value in timestamps]
    angles_degrees = [value * 180.0 / pi for value in angles]

    save_plot(time, angles_degrees, PLOT_FILE, show_turn_reference=True)

    print(f"Duration: {time[-1]:.3f} s")
    print(f"Minimum angle: {min(angles_degrees):.3f} degrees")
    print(f"Maximum angle: {max(angles_degrees):.3f} degrees")
    print(f"Final angle: {angles_degrees[-1]:.3f} degrees")

    # Task 3.3.2: use exactly the same integration without bias correction.
    static_ts, static_gyro = load_yaw_data(BASE / "data" / "imu_razor_data_static.txt")
    static_angles = [value * 180.0 / pi
                     for value in integrate_gyro(static_ts, static_gyro)]
    static_time = [value - static_ts[0] for value in static_ts]
    save_plot(static_time, static_angles, PLOT_FILE.with_name("static_yaw.png"),
              "Relative yaw while the IMU is stationary", show_zero=False)
    print(f"Static duration: {static_time[-1]:.3f} s")
    print(f"Static final angle: {static_angles[-1]:.3f} degrees")

    # Task 3.3.3: mean stationary angular velocity estimates constant bias.
    bias = sum(static_gyro) / len(static_gyro)  # rad/s, not rad/sample
    corrected_gyro = [omega - bias for omega in static_gyro]
    corrected_angles = [value * 180.0 / pi
                        for value in integrate_gyro(static_ts, corrected_gyro)]
    save_plot(static_time, static_angles, PLOT_FILE.with_name("static_bias_correction.png"),
              "Static gyro drift before and after bias correction", show_zero=True,
              corrected=corrected_angles)
    print(f"Estimated z-axis bias: {bias:.8f} rad/s ({bias*180/pi:.6f} degrees/s)")
    print(f"Corrected final angle: {corrected_angles[-1]:.6f} degrees")
    print(f"Corrected range: {min(corrected_angles):.6f} to {max(corrected_angles):.6f} degrees")
    # Same-record calibration demonstrates removal of average drift; it is
    # not independent evidence that the bias stays constant in a later run.


if __name__ == "__main__":
    main()
