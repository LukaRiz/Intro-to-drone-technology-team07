#!/usr/bin/env python3
"""ROS2 Jazzy node to log local and remote 3DR Radio RSSI values to CSV.

Adapted from idt_module_7_materials/ros2_ws/src/idt/idt/get_radio_rssi.py
for Module 8 outdoor antenna range testing.
"""

import argparse
import os
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy


class RSSIRangeLogger(Node):
    """Logs 3DR Radio local and remote RSSI/noise metrics to a CSV file."""

    def __init__(self, label: str = "run") -> None:
        super().__init__("log_radio_rssi")
        safe_label = label.strip().replace(" ", "_") or "run"
        run_stamp = time.strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"rssi_{safe_label}_{run_stamp}.csv"

        self.csv_file = open(self.csv_filename, "w", buffering=1, encoding="utf-8")
        self.csv_file.write(
            "timestamp,rssi_dbm,remote_rssi_dbm,noise_dbm,remote_noise_dbm\n"
        )
        self.csv_file.flush()

        self.sample_count = 0

        self.get_logger().info(
            f"Logging Radio RSSI to {os.path.abspath(self.csv_filename)}"
        )

        best_effort_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )

        self.subscription = self.create_subscription(
            DiagnosticArray,
            "/diagnostics",
            self.on_diagnostics,
            best_effort_qos,
        )

    def on_diagnostics(self, msg: DiagnosticArray) -> None:
        """Extract 3DR Radio RSSI fields from /diagnostics and log to CSV."""
        for status in msg.status:
            if "3DR Radio" not in status.name:
                continue

            fields = {item.key: item.value for item in status.values}
            rssi_dbm = fields.get("RSSI (dBm)", "")
            remote_rssi_dbm = fields.get("Remote RSSI (dBm)", "")
            noise_dbm = fields.get("Noise (dBm)", "")
            remote_noise_dbm = fields.get("Remote Noise (dBm)", "")

            if not rssi_dbm and not remote_rssi_dbm:
                continue

            timestamp = time.time()
            self.csv_file.write(
                f"{timestamp:.3f},{rssi_dbm},{remote_rssi_dbm},"
                f"{noise_dbm},{remote_noise_dbm}\n"
            )
            self.csv_file.flush()
            self.sample_count += 1

            self.get_logger().info(
                f"Local RSSI (dBm): {rssi_dbm or 'N/A'} | "
                f"Remote RSSI (dBm): {remote_rssi_dbm or 'N/A'} "
                f"[#{self.sample_count}]"
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
        description="Log MAVROS 3DR Radio RSSI diagnostics to a run-specific CSV file."
    )
    parser.add_argument(
        "label",
        nargs="?",
        default="run",
        help="Run label for output filename (e.g., reference, dipole).",
    )
    parsed_args, ros_args = parser.parse_known_args(args)

    rclpy.init(args=ros_args)
    node = RSSIRangeLogger(label=parsed_args.label)
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
