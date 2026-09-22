#!/usr/bin/env python3
#/****************************************************************************
# nmea read function
# Copyright (c) 2018-2020, Kjeld Jensen <kj@kjen.dk>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#****************************************************************************/
'''
2018-03-13 Kjeld First version, that reads in CSV data
2020-02-03 Kjeld Python 3 compatible
2020-09-17 Kjeld Changed first line to python3
'''

from datetime import datetime, timedelta
from pathlib import Path
import sys


def _nmea_time_to_datetime(time_text, day_offset=0):
  """Change the NMEA time into a Python time value."""
  parsed_time = datetime.strptime(time_text, '%H%M%S.%f')
  return parsed_time + timedelta(days=day_offset)


def _nmea_coordinate_to_degrees(value, direction):
  """Change an NMEA coordinate into decimal degrees."""
  degrees_length = 2 if direction in ('N', 'S') else 3
  degrees = float(value[:degrees_length])
  minutes = float(value[degrees_length:])
  coordinate = degrees + minutes / 60.0

  if direction in ('S', 'W'):
    coordinate = -coordinate

  return coordinate


def _get_utm_converter():
  """Load the UTM converter supplied for exercise 4.1."""
  utm_folder = Path(__file__).resolve().parents[1] / 'exercise_utm'
  if str(utm_folder) not in sys.path:
    sys.path.insert(0, str(utm_folder))
  from utm import utmconv
  return utmconv()

class nmea_class:
  def __init__(self):
    self.data = []

  def import_file(self, file_name):
    """Read the NMEA file and split each line by ',' """
    self.data = []
    try:
      with open(file_name, encoding='ascii') as nmea_file:
        for line in nmea_file:
          line = line.strip()
          if line and not line.startswith('#'):
            self.data.append(line.split(','))
    except OSError as error:
      raise OSError("Could not read NMEA file '%s': %s" % (file_name, error)) from error

  def get_gga_altitudes(self):
    """Get the time and altitude from the GGA lines."""
    timestamps = []
    altitudes = []
    day_offset = 0
    previous_time = None

    for fields in self.data:
      # Only use GGA lines that contain time and altitude.
      if len(fields) <= 10 or not fields[0].endswith('GGA'):
        continue
      if not fields[1] or not fields[9] or fields[10] != 'M':
        continue

      try:
        timestamp = _nmea_time_to_datetime(fields[1], day_offset)
        altitude = float(fields[9])
      except ValueError:
        continue

      # Add one day if the recording goes past midnight.
      if previous_time is not None and timestamp < previous_time:
        day_offset += 1
        timestamp = _nmea_time_to_datetime(fields[1], day_offset)

      timestamps.append(timestamp)
      altitudes.append(altitude)
      previous_time = timestamp

    return timestamps, altitudes

  def get_gga_satellites(self):
    """Get the time and number of satellites from the GGA lines."""
    timestamps = []
    satellites = []
    day_offset = 0
    previous_time = None

    for fields in self.data:
      # Only use GGA lines that contain time and satellite data.
      if len(fields) <= 7 or not fields[0].endswith('GGA'):
        continue
      if not fields[1] or not fields[7]:
        continue

      try:
        timestamp = _nmea_time_to_datetime(fields[1], day_offset)
        satellite_count = int(fields[7])
      except ValueError:
        continue

      # Add one day if the recording goes past midnight.
      if previous_time is not None and timestamp < previous_time:
        day_offset += 1
        timestamp = _nmea_time_to_datetime(fields[1], day_offset)

      timestamps.append(timestamp)
      satellites.append(satellite_count)
      previous_time = timestamp

    return timestamps, satellites

  def get_gga_positions(self):
    """Get latitude and longitude from the GGA lines."""
    latitudes = []
    longitudes = []

    for fields in self.data:
      # Only use GGA lines that contain both coordinates.
      if len(fields) <= 5 or not fields[0].endswith('GGA'):
        continue
      if not fields[2] or not fields[3] or not fields[4] or not fields[5]:
        continue

      try:
        latitude = _nmea_coordinate_to_degrees(fields[2], fields[3])
        longitude = _nmea_coordinate_to_degrees(fields[4], fields[5])
      except ValueError:
        continue

      latitudes.append(latitude)
      longitudes.append(longitude)

    return latitudes, longitudes

  def get_local_utm_positions(self):
    """Convert the positions to metres from the starting point."""
    latitudes, longitudes = self.get_gga_positions()
    if not latitudes:
      return [], [], None, None

    converter = _get_utm_converter()
    eastings = []
    northings = []
    zone = None
    letter = None

    for latitude, longitude in zip(latitudes, longitudes):
      hemisphere, current_zone, current_letter, easting, northing = \
        converter.geodetic_to_utm(latitude, longitude)

      if zone is None:
        zone = current_zone
        letter = current_letter
      elif current_zone != zone:
        raise ValueError('The positions are not in the same UTM zone.')

      eastings.append(easting)
      northings.append(northing)

    # Subtract the start position to make the graph easier to read.
    start_easting = eastings[0]
    start_northing = northings[0]
    east_from_start = [value - start_easting for value in eastings]
    north_from_start = [value - start_northing for value in northings]

    return east_from_start, north_from_start, zone, letter

  def get_static_accuracy(self):
    """Find how far each static position is from the mean position."""
    timestamps = []
    eastings = []
    northings = []
    day_offset = 0
    previous_time = None
    converter = _get_utm_converter()

    for fields in self.data:
      # Only use GGA lines with a valid fix, time and position.
      if len(fields) <= 6 or not fields[0].endswith('GGA'):
        continue
      if not fields[1] or not fields[2] or not fields[4] or fields[6] == '0':
        continue

      try:
        timestamp = _nmea_time_to_datetime(fields[1], day_offset)
        latitude = _nmea_coordinate_to_degrees(fields[2], fields[3])
        longitude = _nmea_coordinate_to_degrees(fields[4], fields[5])
      except ValueError:
        continue

      # Add one day if the recording goes past midnight.
      if previous_time is not None and timestamp < previous_time:
        day_offset += 1
        timestamp = _nmea_time_to_datetime(fields[1], day_offset)

      hemisphere, zone, letter, easting, northing = \
        converter.geodetic_to_utm(latitude, longitude)
      timestamps.append(timestamp)
      eastings.append(easting)
      northings.append(northing)
      previous_time = timestamp

    if not timestamps:
      return [], [], [], []

    # The file is slightly longer than 24 hours, so only use the first 24.
    end_time = timestamps[0] + timedelta(hours=24)
    record_count = next(
      (index for index, time in enumerate(timestamps) if time > end_time),
      len(timestamps)
    )
    timestamps = timestamps[:record_count]
    eastings = eastings[:record_count]
    northings = northings[:record_count]

    # Use the mean position because the true antenna position is not provided.
    mean_easting = sum(eastings) / len(eastings)
    mean_northing = sum(northings) / len(northings)
    east_errors = [value - mean_easting for value in eastings]
    north_errors = [value - mean_northing for value in northings]
    horizontal_errors = [
      (east ** 2 + north ** 2) ** 0.5
      for east, north in zip(east_errors, north_errors)
    ]

    return timestamps, east_errors, north_errors, horizontal_errors

  def get_satellite_view(self):
    """Get satellite position and SNR data from the GSV lines."""
    satellite_records = []
    current_time = None
    previous_time = None
    start_time = None
    day_offset = 0

    for fields in self.data:
      # GSV lines do not contain time, so use the latest GGA time.
      if fields[0].endswith('GGA') and len(fields) > 1 and fields[1]:
        try:
          timestamp = _nmea_time_to_datetime(fields[1], day_offset)
        except ValueError:
          continue

        if previous_time is not None and timestamp < previous_time:
          day_offset += 1
          timestamp = _nmea_time_to_datetime(fields[1], day_offset)

        current_time = timestamp
        previous_time = timestamp
        if start_time is None:
          start_time = timestamp
        continue

      if current_time is None or not fields[0].endswith('GSV'):
        continue
      if current_time > start_time + timedelta(hours=24):
        continue

      # Each satellite uses four fields: number, elevation, azimuth and SNR.
      for index in range(4, len(fields) - 3, 4):
        snr_text = fields[index + 3].split('*')[0]
        if not fields[index] or not fields[index + 1] or not fields[index + 2]:
          continue
        try:
          satellite_number = int(fields[index])
          elevation = int(fields[index + 1])
          azimuth = int(fields[index + 2])
          snr = int(snr_text) if snr_text else None
        except ValueError:
          continue
        if elevation < 0 or elevation > 90 or azimuth < 0 or azimuth > 359:
          continue
        satellite_records.append(
          (current_time, satellite_number, elevation, azimuth, snr)
        )

    return satellite_records

  def get_satellite_snr(self):
    """Get the time, satellite number and SNR from the GSV lines."""
    snr_records = []
    current_time = None
    previous_time = None
    start_time = None
    day_offset = 0

    for fields in self.data:
      # GSV lines do not contain time, so use the latest GGA time.
      if fields[0].endswith('GGA') and len(fields) > 1 and fields[1]:
        try:
          timestamp = _nmea_time_to_datetime(fields[1], day_offset)
        except ValueError:
          continue

        if previous_time is not None and timestamp < previous_time:
          day_offset += 1
          timestamp = _nmea_time_to_datetime(fields[1], day_offset)

        current_time = timestamp
        previous_time = timestamp
        if start_time is None:
          start_time = timestamp
        continue

      if current_time is None or not fields[0].endswith('GSV'):
        continue
      if current_time > start_time + timedelta(hours=24):
        continue

      # SNR can still be valid when elevation or azimuth is missing.
      for index in range(4, len(fields) - 3, 4):
        snr_text = fields[index + 3].split('*')[0]
        if not fields[index] or not snr_text:
          continue
        try:
          satellite_number = int(fields[index])
          snr = int(snr_text)
        except ValueError:
          continue
        snr_records.append((current_time, satellite_number, snr))

    return snr_records

  def plot_altitude(self, output_file=None, show=True):
    """Make a graph of altitude against time."""
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    timestamps, altitudes = self.get_gga_altitudes()
    if not timestamps:
      raise ValueError('No valid GGA altitude records were found.')

    # Create the graph and add labels.
    fig, axis = plt.subplots(figsize=(10, 5))
    axis.plot(timestamps, altitudes, color='tab:blue', linewidth=1)
    axis.set_title('Drone flight altitude')
    axis.set_xlabel('Time (UTC)')
    axis.set_ylabel('Altitude above mean sea level (m)')
    axis.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    axis.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    # Save the graph if a file name was given.
    if output_file is not None:
      fig.savefig(output_file, dpi=200)
    if show:
      plt.show()
    else:
      plt.close(fig)

    return fig

  def plot_satellites(self, output_file=None, show=True):
    """Make a graph of the number of satellites against time."""
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    timestamps, satellites = self.get_gga_satellites()
    if not timestamps:
      raise ValueError('No valid GGA satellite records were found.')

    # Create the graph and add labels.
    fig, axis = plt.subplots(figsize=(10, 5))
    axis.step(timestamps, satellites, where='post', color='tab:orange', linewidth=1)
    axis.set_title('Satellites tracked during the drone flight')
    axis.set_xlabel('Time (UTC)')
    axis.set_ylabel('Number of satellites')
    axis.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    axis.set_yticks(range(min(satellites), max(satellites) + 1))
    axis.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    # Save the graph if a file name was given.
    if output_file is not None:
      fig.savefig(output_file, dpi=200)
    if show:
      plt.show()
    else:
      plt.close(fig)

    return fig

  def plot_track(self, output_file=None, show=True):
    """Make a map of the drone flight path."""
    import matplotlib.pyplot as plt

    eastings, northings, zone, letter = self.get_local_utm_positions()
    if not eastings:
      raise ValueError('No valid GGA position records were found.')

    # Draw the flight path and mark where it starts and ends.
    fig, axis = plt.subplots(figsize=(8, 7))
    axis.plot(eastings, northings, color='tab:blue', linewidth=1,
              label='Drone track')
    axis.scatter(eastings[0], northings[0], color='green', s=50,
                 label='Start', zorder=3)
    axis.scatter(eastings[-1], northings[-1], color='red', s=50,
                 marker='X', label='End', zorder=3)
    axis.set_title('Drone flight track - UTM zone %d%s' % (zone, letter))
    axis.set_xlabel('East from start (m)')
    axis.set_ylabel('North from start (m)')
    axis.set_aspect('equal', adjustable='datalim')
    axis.grid(True, alpha=0.3)
    axis.legend()
    fig.tight_layout()

    # Save the map if a file name was given.
    if output_file is not None:
      fig.savefig(output_file, dpi=200)
    if show:
      plt.show()
    else:
      plt.close(fig)

    return fig

  def export_track_kml(self, output_file):
    """Export the drone flight path to a KML file."""
    from exportkml import kmlclass

    latitudes, longitudes = self.get_gga_positions()
    timestamps, altitudes = self.get_gga_altitudes()
    if not latitudes:
      raise ValueError('No valid GGA position records were found.')
    if len(latitudes) != len(altitudes):
      raise ValueError('The position and altitude records do not match.')

    # The supplied KML class writes longitude, latitude and altitude.
    kml = kmlclass()
    kml.begin(
      str(output_file),
      'Drone flight track',
      'RTK-GNSS track from the EduQuad flight',
      1.0
    )
    # Keep the line on top of the Google Earth terrain.
    kml.trksegbegin('Drone track', '', 'red', 'clampToGround')
    for latitude, longitude, altitude in zip(
        latitudes, longitudes, altitudes):
      kml.pt(latitude, longitude, altitude)
    kml.trksegend()
    kml.end()

  def plot_static_accuracy(self, output_file=None, show=True):
    """Plot the accuracy of the static GNSS positions."""
    import matplotlib.pyplot as plt

    timestamps, east_errors, north_errors, horizontal_errors = \
      self.get_static_accuracy()
    if not timestamps:
      raise ValueError('No valid static GGA position records were found.')

    elapsed_hours = [
      (timestamp - timestamps[0]).total_seconds() / 3600.0
      for timestamp in timestamps
    ]
    sorted_errors = sorted(horizontal_errors)
    error_95 = sorted_errors[int(0.95 * (len(sorted_errors) - 1))]

    fig, axis = plt.subplots(figsize=(10, 5))

    # Show how the horizontal error changes during the recording.
    axis.plot(elapsed_hours, horizontal_errors, color='tab:blue',
              linewidth=0.6)
    axis.axhline(error_95, color='tab:red', linestyle='--',
                 label='95%% error = %.2f m' % error_95)
    axis.set_title('Static GNSS horizontal accuracy')
    axis.set_xlabel('Time since start (hours)')
    axis.set_ylabel('Distance from mean position (m)')
    axis.grid(True, alpha=0.3)
    axis.legend()
    fig.tight_layout()

    # Save the graph if a file name was given.
    if output_file is not None:
      fig.savefig(output_file, dpi=200)
    if show:
      plt.show()
    else:
      plt.close(fig)

    return fig

  def plot_satellite_snr(self, output_file=None, show=True):
    """Plot satellite SNR over 24 hours."""
    import matplotlib.pyplot as plt

    snr_records = self.get_satellite_snr()
    if not snr_records:
      raise ValueError('No valid GSV SNR records were found.')

    first_time = snr_records[0][0]
    satellite_numbers = sorted(set(record[1] for record in snr_records))
    bin_minutes = 5
    number_of_bins = int(24 * 60 / bin_minutes)

    # Add the SNR values together in five-minute groups.
    snr_sums = {}
    snr_counts = {}
    for timestamp, satellite_number, snr in snr_records:
      elapsed_minutes = (timestamp - first_time).total_seconds() / 60.0
      time_bin = min(int(elapsed_minutes / bin_minutes), number_of_bins - 1)
      key = (satellite_number, time_bin)
      snr_sums[key] = snr_sums.get(key, 0) + snr
      snr_counts[key] = snr_counts.get(key, 0) + 1

    # Each row is one satellite and each column is five minutes.
    snr_grid = []
    for satellite_number in satellite_numbers:
      row = []
      for time_bin in range(number_of_bins):
        key = (satellite_number, time_bin)
        if key in snr_sums:
          row.append(snr_sums[key] / snr_counts[key])
        else:
          row.append(float('nan'))
      snr_grid.append(row)

    fig, axis = plt.subplots(figsize=(12, 7))
    image = axis.imshow(
      snr_grid,
      aspect='auto',
      origin='lower',
      extent=[0, 24, 0.5, len(satellite_numbers) + 0.5],
      cmap='viridis',
      vmin=0,
      vmax=50,
      interpolation='nearest'
    )
    axis.set_title('GPS satellite SNR over 24 hours (5-minute averages)')
    axis.set_xlabel('Time since start (hours)')
    axis.set_ylabel('Satellite PRN')
    axis.set_yticks(range(1, len(satellite_numbers) + 1))
    axis.set_yticklabels(satellite_numbers)
    color_bar = fig.colorbar(image, ax=axis)
    color_bar.set_label('Average SNR (dB-Hz)')
    fig.tight_layout()

    # Save the graph if a file name was given.
    if output_file is not None:
      fig.savefig(output_file, dpi=200)
    if show:
      plt.show()
    else:
      plt.close(fig)

    return fig

  def plot_satellite_sky(self, output_file=None, second_output_file=None,
                         show=True):
    """Make a hemisphere map of the satellites over 24 hours."""
    from matplotlib.colors import hsv_to_rgb
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3DCollection
    import numpy as np

    satellite_records = self.get_satellite_view()
    if not satellite_records:
      raise ValueError('No valid GSV satellite positions were found.')

    first_time = satellite_records[0][0]
    bin_minutes = 5

    # Keep one position per satellite every five minutes.
    sampled_records = {}
    for timestamp, satellite_number, elevation, azimuth, snr in satellite_records:
      elapsed_minutes = (timestamp - first_time).total_seconds() / 60.0
      time_bin = int(elapsed_minutes / bin_minutes)
      key = (satellite_number, time_bin)
      if key not in sampled_records:
        sampled_records[key] = (
          timestamp, satellite_number, elevation, azimuth
        )

    records = list(sampled_records.values())

    # Create a wireframe hemisphere.
    azimuth_grid = np.linspace(0, 2 * np.pi, 25)
    elevation_grid = np.linspace(0, np.pi / 2, 7)
    grid_azimuth, grid_elevation = np.meshgrid(
      azimuth_grid, elevation_grid
    )
    grid_east = np.cos(grid_elevation) * np.sin(grid_azimuth)
    grid_north = np.cos(grid_elevation) * np.cos(grid_azimuth)
    grid_up = np.sin(grid_elevation)

    fig = plt.figure(figsize=(9, 7))
    axis = fig.add_subplot(111, projection='3d')
    axis.plot_surface(
      grid_east,
      grid_north,
      grid_up,
      color='lightskyblue',
      alpha=0.08,
      shade=False
    )
    axis.plot_wireframe(
      grid_east,
      grid_north,
      grid_up,
      color='lightgray',
      linewidth=0.6,
      alpha=0.7
    )

    # Add a flat ground plane at the horizon.
    ground_angles = np.linspace(0, 2 * np.pi, 50)
    ground_radii = np.linspace(0, 1, 2)
    ground_angle, ground_radius = np.meshgrid(ground_angles, ground_radii)
    ground_east = ground_radius * np.sin(ground_angle)
    ground_north = ground_radius * np.cos(ground_angle)
    ground_up = np.zeros_like(ground_east)
    axis.plot_surface(
      ground_east,
      ground_north,
      ground_up,
      color='lightgreen',
      alpha=0.18,
      shade=False
    )

    # Give each satellite its own colour.
    satellite_paths = {}
    for record in records:
      satellite_paths.setdefault(record[1], []).append(record)

    satellite_numbers = sorted(satellite_paths)
    for colour_number, satellite_number in enumerate(satellite_numbers):
      hue = colour_number / len(satellite_numbers)

      path = sorted(satellite_paths[satellite_number])
      path_parts = []
      path_part = []

      # Do not connect the line while a satellite is not visible.
      for record in path:
        if path_part and record[0] - path_part[-1][0] > timedelta(minutes=10):
          path_parts.append(path_part)
          path_part = []
        path_part.append(record)
      if path_part:
        path_parts.append(path_part)

      for path_part in path_parts:
        if len(path_part) < 2:
          continue

        elevations = np.radians([record[2] for record in path_part])
        azimuths = np.radians([record[3] for record in path_part])
        east = np.cos(elevations) * np.sin(azimuths)
        north = np.cos(elevations) * np.cos(azimuths)
        up = np.sin(elevations)
        points = np.column_stack((east, north, up))
        line_segments = np.stack((points[:-1], points[1:]), axis=1)

        # The colour gets brighter as time moves from 0 to 24 hours.
        segment_hours = np.array([
          (record[0] - first_time).total_seconds() / 3600.0
          for record in path_part[:-1]
        ])
        brightness = 0.08 + 0.92 * np.clip(segment_hours / 24.0, 0, 1)
        segment_colours = hsv_to_rgb(np.column_stack((
          np.full(len(brightness), hue),
          np.full(len(brightness), 0.95),
          brightness
        )))
        lines = Line3DCollection(
          line_segments,
          colors=segment_colours,
          linewidths=0.7
        )
        axis.add_collection3d(lines)

        # Add small arrows at one-third and two-thirds of the path.
        arrow_indexes = sorted(set([
          max(0, len(line_segments) // 3),
          max(0, 2 * len(line_segments) // 3)
        ]))
        for arrow_index in arrow_indexes:
          if arrow_index >= len(line_segments):
            continue
          start = line_segments[arrow_index][0]
          change = line_segments[arrow_index][1] - start
          axis.quiver(
            start[0], start[1], start[2],
            change[0], change[1], change[2],
            color=segment_colours[arrow_index],
            length=0.055,
            normalize=True,
            linewidth=0.9,
            arrow_length_ratio=0.45
          )

    # The static GNSS receiver is at the centre of the hemisphere.
    axis.scatter([0], [0], [0], color='red', marker='o', s=70,
                 depthshade=False)
    axis.text(0, 1.12, 0, 'N', ha='center', fontsize=12)
    axis.text(1.12, 0, 0, 'E', ha='center', fontsize=12)
    axis.text(0, -1.12, 0, 'S', ha='center', fontsize=12)
    axis.text(-1.12, 0, 0, 'W', ha='center', fontsize=12)
    axis.set_xlim(-1.15, 1.15)
    axis.set_ylim(-1.15, 1.15)
    axis.set_zlim(0, 1.05)
    axis.set_box_aspect((1, 1, 0.55), zoom=1.2)
    axis.set_axis_off()
    axis.view_init(elev=25, azim=-55)
    axis.set_title('GPS satellite paths in the visible sky', pad=15)
    fig.tight_layout()

    # Save the angled view.
    if output_file is not None:
      fig.savefig(output_file, dpi=200, bbox_inches='tight')

    # Save a second image looking down from above.
    if second_output_file is not None:
      axis.view_init(elev=90, azim=-90)
      axis.set_title('GPS satellite paths - top view', pad=15)
      fig.savefig(second_output_file, dpi=200, bbox_inches='tight')

    if show:
      plt.show()
    else:
      plt.close(fig)

    return fig

  def print_data(self):
    for i in range(len(self.data)):
      print (self.data[i])


if __name__ == "__main__":
  # The data and output image are in the same folder as this script.
  script_directory = Path(__file__).resolve().parent
  input_file = script_directory / 'nmea_trimble_gnss_eduquad_flight.txt'
  static_input_file = script_directory / 'nmea_ublox_neo_24h_static.txt'
  altitude_output_file = script_directory / 'nmea_flight_altitude.png'
  satellites_output_file = script_directory / 'nmea_flight_satellites.png'
  track_output_file = script_directory / 'nmea_flight_track.png'
  kml_output_file = script_directory / 'nmea_flight_track.kml'
  accuracy_output_file = script_directory / 'nmea_static_accuracy.png'
  snr_output_file = script_directory / 'nmea_static_snr.png'
  sky_output_file = script_directory / 'nmea_satellite_sky.png'
  sky_top_output_file = script_directory / 'nmea_satellite_sky_top.png'

  print('Importing %s' % input_file.name)
  nmea = nmea_class()
  nmea.import_file(input_file)
  timestamps, altitudes = nmea.get_gga_altitudes()
  print('Parsed %d altitude records' % len(altitudes))
  print('Saving altitude plot to %s' % altitude_output_file.name)
  nmea.plot_altitude(altitude_output_file, show=False)

  timestamps, satellites = nmea.get_gga_satellites()
  print('Parsed %d satellite records' % len(satellites))
  print('Saving satellite plot to %s' % satellites_output_file.name)
  nmea.plot_satellites(satellites_output_file, show=False)

  latitudes, longitudes = nmea.get_gga_positions()
  print('Parsed %d position records' % len(latitudes))
  print('Saving flight track to %s' % track_output_file.name)
  nmea.plot_track(track_output_file, show=False)
  print('Saving KML flight track to %s' % kml_output_file.name)
  nmea.export_track_kml(kml_output_file)

  print('Importing %s' % static_input_file.name)
  static_nmea = nmea_class()
  static_nmea.import_file(static_input_file)
  timestamps, east_errors, north_errors, horizontal_errors = \
    static_nmea.get_static_accuracy()
  print('Parsed %d static position records' % len(timestamps))
  print('Saving static accuracy plot to %s' % accuracy_output_file.name)
  static_nmea.plot_static_accuracy(accuracy_output_file, show=False)

  snr_records = static_nmea.get_satellite_snr()
  print('Parsed %d satellite SNR records' % len(snr_records))
  print('Saving satellite SNR plot to %s' % snr_output_file.name)
  static_nmea.plot_satellite_snr(snr_output_file, show=False)

  satellite_records = static_nmea.get_satellite_view()
  print('Parsed %d satellite position records' % len(satellite_records))
  print('Saving satellite sky plots')
  static_nmea.plot_satellite_sky(
    sky_output_file,
    sky_top_output_file,
    show=False
  )
 
