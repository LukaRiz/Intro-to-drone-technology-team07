#!/usr/bin/env python3
"""ROS2 Jazzy node to log GNSS position from MAVROS to a timestamped CSV file.

Adapted from idt_module_7_materials/ros2_ws/src/idt/idt/get_global_pos.py
for Module 8 outdoor antenna range testing.
"""

import argparse
import os
import time

import rclpy
from mavros_msgs.msg import GPSRAW
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import NavSatFix


class GNSSRangeLogger(Node):
    """Logs raw GNSS fix messages with Unix timestamps into a run-specific CSV."""

    def __init__(self, label: str = "run") -> None:
        super().__init__("log_global_pos")
        safe_label = label.strip().replace(" ", "_") or "run"
        run_stamp = time.strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"gnss_{safe_label}_{run_stamp}.csv"

        self.csv_file = open(self.csv_filename, "w", buffering=1, encoding="utf-8")
        self.csv_file.write("timestamp,latitude,longitude,altitude,fix_status,fix\n")
        self.csv_file.flush()

        self.sample_count = 0
        self._last_gpsraw_log = 0.0

        self.get_logger().info(
            f"Logging GNSS positions to {os.path.abspath(self.csv_filename)}"
        )

        best_effort_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )

        self.sub_global_pos_raw = self.create_subscription(
            NavSatFix,
            "/mavros/global_position/raw/fix",
            self.on_global_pos_raw_msg,
            best_effort_qos,
        )

        self.sub_gpsstatus_gps1_raw = self.create_subscription(
            GPSRAW,
            "/mavros/gpsstatus/gps1/raw",
            self.on_gpsstatus_gps1_raw_msg,
            best_effort_qos,
        )

    def on_global_pos_raw_msg(self, msg: NavSatFix) -> None:
        """Write timestamped GNSS coordinate and fix status on each raw fix."""
        timestamp = time.time()
        fix = "No fix" if msg.status.status == -1 else "Fix ok"

        self.csv_file.write(
            f"{timestamp:.3f},{msg.latitude:.7f},{msg.longitude:.7f},"
            f"{msg.altitude:.3f},{msg.status.status},{fix}\n"
        )
        self.csv_file.flush()
        self.sample_count += 1

        self.get_logger().info(
            f"[#{self.sample_count}] {fix} | "
            f"lat={msg.latitude:.6f} lon={msg.longitude:.6f} alt={msg.altitude:.2f} m"
        )

    def on_gpsstatus_gps1_raw_msg(self, msg: GPSRAW) -> None:
        """Periodically log raw GPS fix type and satellite count to verify lock."""
        now = time.time()
        if now - self._last_gpsraw_log < 5.0:
            return
        self._last_gpsraw_log = now

        fix = "No fix" if msg.fix_type == 0 else f"Fix type {msg.fix_type}"
        sats = getattr(msg, "satellites_visible", "?")
        self.get_logger().info(
            f"/mavros/gpsstatus/gps1/raw: {fix}, sats={sats}, "
            f"lat={msg.lat / 1e7:.6f} lon={msg.lon / 1e7:.6f} alt={msg.alt / 1e3:.2f} m"
        )

    def destroy_node(self) -> None:
        """Flush and close the CSV file cleanly on shutdown."""
        if hasattr(self, "csv_file") and not self.csv_file.closed:
            self.csv_file.flush()
            self.csv_file.close()
            self.get_logger().info(
                f"Closed {self.csv_filename} ({self.sample_count} samples written)."
            )
        super().destroy_node()


def main(args=None) -> None:
    parser = argparse.ArgumentParser(
        description="Log MAVROS GNSS positions to a run-specific CSV file."
    )
    parser.add_argument(
        "label",
        nargs="?",
        default="run",
        help="Run label for output filename (e.g., reference, dipole).",
    )
    parsed_args, ros_args = parser.parse_known_args(args)

    rclpy.init(args=ros_args)
    node = GNSSRangeLogger(label=parsed_args.label)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
