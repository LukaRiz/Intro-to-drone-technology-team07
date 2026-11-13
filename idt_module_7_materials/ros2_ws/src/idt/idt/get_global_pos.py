#!/usr/bin/env python3
#/****************************************************************************
# get_global_pos.py
# Copyright (c) 2018-2026, Kjeld Jensen <kjen@sdu.dk> <kj@kjen.dk>
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
2018-03-20 Kjeld Jensen, first version
'''
import rclpy
from rclpy.node import Node
from rclpy.qos import ReliabilityPolicy, QoSProfile
from mavros_msgs.msg import GPSRAW
from sensor_msgs.msg import NavSatFix

class ros_node_class(Node):
    def __init__(self):
        super().__init__('get_global_pos')

        # publishers

        # subscribers
        self.sub_global_pos = self.create_subscription(
            NavSatFix,                             # message type
            '/mavros/global_position/global',      # topic to subscribe to
            self.on_global_pos_msg,                # callback function
            QoSProfile(depth=10,reliability=ReliabilityPolicy.BEST_EFFORT)
        )

        self.sub_global_pos_raw = self.create_subscription(
            NavSatFix, # message type
            '/mavros/global_position/raw/fix', # topic to subscribe to
            self.on_global_pos_raw_msg, # callback function 
            QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        )

        self.sub_gpsstatus_gps1_raw = self.create_subscription(
            GPSRAW, # message type
            '/mavros/gpsstatus/gps1/raw', # topic to subscribe to
            self.on_gpstatus_gps1_raw_msg, # callback function 
            QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        )

        # timers
        self.timer = self.create_timer(5.0, self.timer_update)
 
    def on_global_pos_msg(self, msg):
        self.get_logger().info('/mavros/global_position/global (FC estimate): %.6f %.6f %.3f WGS84' % (msg.latitude, msg.longitude, msg.altitude))

    def on_global_pos_raw_msg(self, msg):
        if msg.status.status == -1:
            fix = "No fix"
        else:
            fix = "Fix ok"
        self.get_logger().info('/mavros/global_position/raw/fix (GNSS raw): %s %.6f %.6f %.3f WGS84'  % (fix, msg.latitude, msg.longitude, msg.altitude))

    def on_gpstatus_gps1_raw_msg(self, msg):
        if msg.fix_type == 0:
            fix = "No fix"
        else:
            fix = "Fix ok"
        self.get_logger().info('/mavros/gpsstatus/gps1/raw (GNSS raw): %s %.6f %.6f %.3f AMSL' % (fix, msg.lat/10000000.0, msg.lon/10000000.0, msg.alt/1000.0))

    def timer_update(self):
        self.get_logger().info('Timer update')

def main(args=None):
    rclpy.init(args=args)
    ros_node = ros_node_class()
    rclpy.spin(ros_node)

    ros_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
