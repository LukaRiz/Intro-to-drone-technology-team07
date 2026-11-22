#!/usr/bin/env python3
"""
Module 7 - Step 4.2 (and 4.5): Convert GNSS track coordinates between
geodetic (WGS84 lat/lon) and UTM using the Module 2 utmconv library.
"""

import csv
import sys
from pathlib import Path

# Reuse the Module 2 UTM conversion library
REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_2_UTM_DIR = REPO_ROOT / "idt_module_2_materials" / "exercise_utm"
if str(MODULE_2_UTM_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_2_UTM_DIR))

from utm import utmconv  # noqa: E402


class TrackUTMConverter:
    """Converts GNSS tracks between geodetic (lat, lon) and UTM (easting, northing)."""

    def __init__(self, zone_override: int = 0):
        self.uc = utmconv()
        if zone_override > 0:
            self.uc.set_zone_override(zone_override)

    def geodetic_to_utm(self, lat: float, lon: float):
        return self.uc.geodetic_to_utm(lat, lon)

    def utm_to_geodetic(self, hemisphere: str, zone: int, easting: float, northing: float):
        return self.uc.utm_to_geodetic(hemisphere, zone, easting, northing)

    def convert_csv_to_utm(self, input_csv: Path, output_csv: Path, only_fix_ok: bool = True):
        """Read geodetic GNSS CSV, filter invalid fixes, convert to UTM, and save."""
        converted = []
        skipped = 0

        with open(input_csv, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if only_fix_ok and row.get("fix", "").strip() != "Fix ok":
                    skipped += 1
                    continue

                lat = float(row["latitude"])
                lon = float(row["longitude"])
                if lat == 0.0 and lon == 0.0:
                    skipped += 1
                    continue

                timestamp = float(row["timestamp"])
                alt = float(row["altitude"])
                hemisphere, zone, letter, easting, northing = self.geodetic_to_utm(lat, lon)

                converted.append({
                    "timestamp": timestamp,
                    "hemisphere": hemisphere,
                    "zone": zone,
                    "letter": letter,
                    "easting": easting,
                    "northing": northing,
                    "altitude": alt,
                })

        fieldnames = ["timestamp", "hemisphere", "zone", "letter", "easting", "northing", "altitude"]
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for pt in converted:
                writer.writerow({
                    "timestamp": f"{pt['timestamp']:.3f}",
                    "hemisphere": pt["hemisphere"],
                    "zone": pt["zone"],
                    "letter": pt["letter"],
                    "easting": f"{pt['easting']:.4f}",
                    "northing": f"{pt['northing']:.4f}",
                    "altitude": f"{pt['altitude']:.3f}",
                })

        return converted, skipped


def load_utm_track(utm_csv: Path):
    """Load UTM track rows as a list of dicts with numeric fields."""
    track = []
    with open(utm_csv, "r", newline="") as f:
        for row in csv.DictReader(f):
            track.append({
                "timestamp": float(row["timestamp"]),
                "hemisphere": row["hemisphere"],
                "zone": int(row["zone"]),
                "letter": row["letter"],
                "easting": float(row["easting"]),
                "northing": float(row["northing"]),
                "altitude": float(row["altitude"]),
            })
    return track


if __name__ == "__main__":
    mod7_dir = Path(__file__).resolve().parent
    input_path = mod7_dir / "gnss_track.csv"
    output_path = mod7_dir / "gnss_track_utm.csv"

    converter = TrackUTMConverter()
    points, skipped = converter.convert_csv_to_utm(input_path, output_path)

    eastings = [p["easting"] for p in points]
    northings = [p["northing"] for p in points]
    zones = {(p["hemisphere"], p["zone"], p["letter"]) for p in points}

    print(f"Input:     {input_path.name}")
    print(f"Output:    {output_path.name}")
    print(f"Converted: {len(points)} points (skipped {skipped} non-fix rows)")
    print(f"UTM zone:  {zones}")
    print(f"Easting:   {min(eastings):.2f} .. {max(eastings):.2f} m (span {max(eastings) - min(eastings):.2f} m)")
    print(f"Northing:  {min(northings):.2f} .. {max(northings):.2f} m (span {max(northings) - min(northings):.2f} m)")

    # Quick round-trip verification on the first point
    p0 = points[0]
    lat_rt, lon_rt = converter.utm_to_geodetic(p0["hemisphere"], p0["zone"], p0["easting"], p0["northing"])
    print(f"Round-trip check (first point): lat={lat_rt:.7f}, lon={lon_rt:.7f}")
