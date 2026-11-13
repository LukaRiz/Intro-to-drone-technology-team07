#!/usr/bin/env python3
#/****************************************************************************
# get_radio_rssi.py
# Copyright (c) 2024-2026, Kjeld Jensen <kjen@sdu.dk> <kj@kjen.dk>
# SDU Drone Center, University of Southern Denmark http://sdu.dk/uas
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
2024-11-13 Kjeld Jensen, first version
'''

import rclpy
from rclpy.node import Node
from rclpy.qos import ReliabilityPolicy, QoSProfile
from diagnostic_msgs.msg import DiagnosticArray

class RSSIListener(Node):
    def __init__(self):
        super().__init__('get_radio_rssi')
        # Subscribe to the /diagnostics topic
        self.subscription = self.create_subscription(
            DiagnosticArray,
            '/diagnostics',
            self.on_diagnostics,
            QoSProfile(depth=10,reliability=ReliabilityPolicy.BEST_EFFORT)
        )
        self.get_logger().info("get_radio_rssi node Started...")

    def on_diagnostics(self, msg):
        for status in msg.status:
            if status.name == "mavros: 3DR Radio":
                for value in status.values:
                    if value.key == "RSSI (dBm)":
                        rssi = value.value
                        self.get_logger().info(f"Local RSSI (dBm): {rssi}")
                    elif value.key == "Remote RSSI (dBm)":
                        remote_rssi = value.value
                        self.get_logger().info(f"Remote RSSI (dbm): {remote_rssi}")

def main(args=None):
    rclpy.init(args=args)
    rssi_listener = RSSIListener()
    rclpy.spin(rssi_listener)

    # Destroy the node explicitly
    rssi_listener.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

