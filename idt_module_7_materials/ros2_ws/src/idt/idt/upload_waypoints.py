#!/usr/bin/env python3
#/****************************************************************************
# upload_waypoint.py
# Copyright (c) 2026, Kjeld Jensen <kjen@sdu.dk> <kj@kjen.dk>
# SDU Drone Center, University of Southern Denmark http://sdu.dk/uas
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
2026-11-12 Kjeld Jensen, first version
'''

import rclpy
from rclpy.node import Node

from mavros_msgs.msg import Waypoint
from mavros_msgs.srv import WaypointPush, WaypointClear, WaypointPull

# Takeoff: latitude, longitude, altitude relative to home (m)
TAKEOFF = (55.471867, 10.325130, 30.0)

# Mission waypoints: latitude, longitude, relative altitude (m)
WAYPOINTS = [
    (55.472037, 10.324953, 30.0),
    (55.471940, 10.324655, 30.0),
    (55.471764, 10.324828, 30.0),
]
FRAME_GLOBAL_RELATIVE_ALT = 3

NAV_WAYPOINT = 16
NAV_LAND = 21
NAV_TAKEOFF = 22

def make_waypoint(command, lat, lon, alt, current=False):
    wp = Waypoint()
    wp.frame = FRAME_GLOBAL_RELATIVE_ALT
    wp.command = command
    wp.is_current = current
    wp.autocontinue = True

    wp.param1 = 0.0
    wp.param2 = 0.0
    wp.param3 = 0.0
    wp.param4 = float('nan')  # Unspecified yaw

    wp.x_lat = float(lat)
    wp.y_long = float(lon)
    wp.z_alt = float(alt)

    return wp


class MissionUploader(Node):

    def __init__(self):
        super().__init__('mission_uploader')

        self.clear_client = self.create_client(
            WaypointClear, '/mavros/mission/clear'
        )
        self.push_client = self.create_client(
            WaypointPush, '/mavros/mission/push'
        )
        self.pull_client = self.create_client(
            WaypointPull, '/mavros/mission/pull'
        )

    def call_service(self, client, request, timeout=30.0):
        if not client.wait_for_service(timeout_sec=10.0):
            raise RuntimeError('MAVROS service unavailable')

        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self, future, timeout_sec=timeout
        )

        if not future.done():
            raise RuntimeError('Service call timed out')

        result = future.result()

        if result is None:
            raise RuntimeError('Service call failed')

        return result

    def upload(self):

        lat_home, lon_home, alt_home = TAKEOFF

        # Build mission
        mission = []

        # 1. Takeoff
        mission.append(make_waypoint(
            NAV_TAKEOFF,
            lat_home, lon_home, alt_home,
            current=True
        ))

        # 2. Navigation waypoints
        for lat, lon, alt in WAYPOINTS:
            mission.append(make_waypoint(
                NAV_WAYPOINT, lat, lon, alt
            ))

        # 3. Return above takeoff location
        mission.append(make_waypoint(
            NAV_WAYPOINT,
            lat_home, lon_home, alt_home
        ))

        # 4. Land at takeoff location
        mission.append(make_waypoint(
            NAV_LAND,
            lat_home, lon_home, 0.0
        ))

        # 5. Delete previous mission
        self.get_logger().info('Clearing previous mission...')

        response = self.call_service(
            self.clear_client, WaypointClear.Request()
        )

        if not response.success:
            raise RuntimeError('Failed to clear previous mission')

        # 6. Verify mission was deleted
        response = self.call_service(
            self.pull_client, WaypointPull.Request()
        )

        if not response.success or response.wp_received != 0:
            raise RuntimeError(
                'Previous mission was not successfully cleared'
            )

        self.get_logger().info('Previous mission cleared')

        # 7. Upload new mission
        request = WaypointPush.Request()
        request.start_index = 0
        request.waypoints = mission

        self.get_logger().info(
            f'Uploading {len(mission)} mission items...'
        )

        response = self.call_service(self.push_client, request)

        if not response.success or response.wp_transfered != len(mission):
            raise RuntimeError(
                f'Mission upload failed: '
                f'{response.wp_transfered}/{len(mission)}'
            )

        # 8. Verify uploaded mission count
        response = self.call_service(
            self.pull_client, WaypointPull.Request()
        )

        if not response.success or response.wp_received != len(mission):
            raise RuntimeError(
                'Mission verification failed: '
                'unexpected mission item count'
            )

        self.get_logger().info(
            f'Mission uploaded successfully: '
            f'{len(mission)} mission items'
        )


def main():
    rclpy.init()
    node = MissionUploader()

    try:
        node.upload()
    except Exception as exc:
        node.get_logger().error(str(exc))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

