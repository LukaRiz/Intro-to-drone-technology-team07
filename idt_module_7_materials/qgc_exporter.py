#!/usr/bin/env python3
"""
Module 7 - Step 4.6: Reusable QGroundControl (.plan) mission exporter class.

Encapsulates QGC JSON mission generation based on qgc_generate_plan_example.py
and hcaa_test_plan.plan (PX4 multirotor, relative altitude frame).
"""

import csv
import json
from pathlib import Path


class QGCPlanExporter:
    """Exports geographic waypoints (lat, lon, alt) to a QGroundControl .plan file."""

    # MAVLink command IDs
    CMD_NAV_WAYPOINT = 16
    CMD_NAV_RTL = 20
    CMD_NAV_TAKEOFF = 22

    # MAVLink coordinate frames
    FRAME_MISSION = 2
    FRAME_GLOBAL_RELATIVE_ALT = 3

    def __init__(
        self,
        cruise_speed: float = 15.0,
        hover_speed: float = 5.0,
        firmware_type: int = 12,  # 12 = PX4 Pro, 3 = ArduPilot
        vehicle_type: int = 2,    # 2 = Multirotor / Quadrotor
        include_rtl: bool = True,
    ):
        self.cruise_speed = cruise_speed
        self.hover_speed = hover_speed
        self.firmware_type = firmware_type
        self.vehicle_type = vehicle_type
        self.include_rtl = include_rtl

    def _make_nav_item(self, jump_id: int, command: int, lat: float, lon: float, alt: float) -> dict:
        return {
            "AMSLAltAboveTerrain": None,
            "Altitude": alt,
            "AltitudeMode": 1,
            "autoContinue": True,
            "command": command,
            "doJumpId": jump_id,
            "frame": self.FRAME_GLOBAL_RELATIVE_ALT,
            "params": [0, 0, 0, None, lat, lon, alt],
            "type": "SimpleItem",
        }

    def _make_rtl_item(self, jump_id: int) -> dict:
        return {
            "autoContinue": True,
            "command": self.CMD_NAV_RTL,
            "doJumpId": jump_id,
            "frame": self.FRAME_MISSION,
            "params": [0, 0, 0, 0, 0, 0, 0],
            "type": "SimpleItem",
        }

    def build_plan(self, waypoints: list[dict]) -> dict:
        """Build a QGroundControl .plan dictionary from a list of {latitude, longitude, altitude} dicts."""
        if not waypoints:
            raise ValueError("waypoints list cannot be empty")

        items = []
        for idx, wp in enumerate(waypoints, start=1):
            cmd = self.CMD_NAV_TAKEOFF if idx == 1 else self.CMD_NAV_WAYPOINT
            items.append(
                self._make_nav_item(
                    jump_id=idx,
                    command=cmd,
                    lat=float(wp["latitude"]),
                    lon=float(wp["longitude"]),
                    alt=float(wp["altitude"]),
                )
            )

        if self.include_rtl:
            items.append(self._make_rtl_item(jump_id=len(items) + 1))

        first = waypoints[0]
        plan = {
            "fileType": "Plan",
            "geoFence": {
                "circles": [],
                "polygons": [],
                "version": 2,
            },
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": self.cruise_speed,
                "firmwareType": self.firmware_type,
                "globalPlanAltitudeMode": 0,
                "hoverSpeed": self.hover_speed,
                "items": items,
                "plannedHomePosition": [float(first["latitude"]), float(first["longitude"]), None],
                "vehicleType": self.vehicle_type,
                "version": 2,
            },
            "rallyPoints": {
                "points": [],
                "version": 2,
            },
            "version": 1,
        }
        return plan

    def export(self, waypoints: list[dict], output_path: Path) -> Path:
        """Write waypoints to a QGroundControl .plan JSON file."""
        plan = self.build_plan(waypoints)
        with open(output_path, "w") as f:
            json.dump(plan, f, indent=4, sort_keys=True)
        return output_path

    @staticmethod
    def load_waypoints_csv(csv_path: Path) -> list[dict]:
        """Load geographic waypoints from a CSV with columns latitude,longitude,altitude."""
        waypoints = []
        with open(csv_path, "r", newline="") as f:
            for row in csv.DictReader(f):
                waypoints.append({
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "altitude": float(row["altitude"]),
                })
        return waypoints


if __name__ == "__main__":
    mod7_dir = Path(__file__).resolve().parent
    exporter = QGCPlanExporter(firmware_type=12, vehicle_type=2, include_rtl=True)

    exports = [
        ("waypoints_method2_rdp.csv", "mission_rdp.plan"),
        ("waypoints_method3_dist_bearing.csv", "mission_dist_bearing.plan"),
    ]

    for csv_name, plan_name in exports:
        wps = exporter.load_waypoints_csv(mod7_dir / csv_name)
        out_path = exporter.export(wps, mod7_dir / plan_name)
        data = json.loads(out_path.read_text())
        n_items = len(data["mission"]["items"])
        print(f"Exported {plan_name}: {len(wps)} waypoints -> {n_items} mission items (Takeoff + {len(wps)-1} WPs + RTL)")
