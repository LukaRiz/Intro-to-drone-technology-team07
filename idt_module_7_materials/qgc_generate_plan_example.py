#!/usr/bin/env python3
#/****************************************************************************
# QGroundControl example
# Copyright (c) 2018-2026, Kjeld Jensen <kjen@sdu.dk> <kj@kjen.dk>
# http://sdu.dk/uas
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

import json

plan = {}
geoFence = {}
plan['fileType'] = 'Plan'

geoFence['polygon'] = [] 
geoFence['version'] = 1 
plan['geoFence'] = geoFence

plan['groundStation'] = 'QGroundControl'

items = []

item = {}
item['autoContinue'] = True
item['command'] = 22
item['doJumpId'] = 1
item['frame'] = 3
item['params'] = [0,0,0,0,55.4713271,10.32561629,50]
item['type'] = 'SimpleItem'
items.append (item)

item = {}
item['autoContinue'] = True
item['command'] = 16
item['doJumpId'] = 2
item['frame'] = 3
item['params'] = [0,0,0,0,55.4714042,10.3256544,50]
item['type'] = 'SimpleItem'
items.append (item)

item = {}
item['autoContinue'] = True
item['command'] = 16
item['doJumpId'] = 3
item['frame'] = 3
item['params'] = [0,0,0,0,55.4710709,10.3246252,50]
item['type'] = 'SimpleItem'
items.append (item)

item = {}
item['autoContinue'] = True
item['command'] = 16
item['doJumpId'] = 4
item['frame'] = 3
item['params'] = [0,0,0,0,55.4708023,10.3263024,50]
item['type'] = 'SimpleItem'
items.append (item)

mission = {}
mission['cruiseSpeed'] = 15
mission['firmwareType'] = 3
mission['hoverSpeed'] = 5
mission['items'] = items
mission['plannedHomePosition'] = [55.4713, 10.3256, 50]
mission['vehicleType'] = 2
mission['version'] = 2
plan['mission'] = mission

rallyPoints = {}
rallyPoints['points'] = [] 
rallyPoints['version'] = 1 
plan['rallyPoints'] = rallyPoints

plan['version'] = 1

plan_json = json.dumps(plan, indent=4, sort_keys=True)

file = open('mission.plan','w') 
file.write (plan_json)
file.close()

