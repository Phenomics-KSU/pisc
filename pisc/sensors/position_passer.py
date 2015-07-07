#!/usr/bin/env python

"""
Sensor Name:    Position Data Passer
Manufacturer:   None
Sensor Type:    Position 
"""

import time
import serial
import struct
import logging

from sensor import Sensor

class PositionPasser(Sensor):
    '''Simple class that passes data along from position source to data handlers.'''
    
    def __init__(self, name, sensor_id, time_source, position_source, data_handlers):
        '''Constructor.'''
        Sensor.__init__(self, 'position', name, sensor_id, time_source, data_handlers)
        
        self.position_source = position_source
        
        self.stop_passing = False # If true then sensor will passing data to handlers.

        self.is_open = False # internally flag to keep track of whether or not sensor is open.

    def open(self):
        '''Set internal open flag.'''
        self.is_open = True
    
    def is_closed(self):
        '''Return true if sensor is closed.'''
        return not self.is_open
        
    def start(self):
        '''Pass position data to handlers when it becomes available.'''
        while True:
            
            if self.received_close_request:
                break # end thread
            
            if self.stop_passing:
                # Don't want to pass data along right now.
                time.sleep(0.1)
                continue
            
            # Block until new position data arrives.
            if not self.position_source.wait(timeout = 0.5):
                continue # no new position data so check for close request
            
            time, frame, position, zone = self.position_source.position
            x, y, z = position
            if zone.lower() == 'none':
                self.handle_data((time, frame, x, y, z))
            else:
                self.handle_data((time, frame, x, y, z, zone))
            
        # Good idea to close at end of thread so no matter what causes break the sensor won't hang when trying to close.    
        self.received_close_request = False
        self.is_open = False
        
    def stop(self):
        '''Set flag to temporarily stop passing data. Thread safe.'''
        self.stop_passing = True
        
    def resume(self):
        '''Set flag to resume passing sensor data. Thread safe.'''
        self.stop_passing = False
