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
        
        self.last_utc_time = 0 # last position timestamp that was passed onto data handlers.

        self.max_closing_time = 3 # seconds

    def open(self):
        '''Set internal open flag.'''
        self.is_open = True
    
    def is_closed(self):
        '''Return true if sensor is closed.'''
        return not self.is_open
        
    def start(self):
        '''Pass position data to handlers when it becomes available.'''
        
        self.handle_metadata(['time (s)', 'x', 'y', 'z'])
        
        while True:
            
            if self.received_close_request:
                break # end thread
            
            if self.stop_passing:
                # Don't want to pass data along right now.
                time.sleep(0.1)
                continue
            
            # Block until new position data arrives or we time out.
            self.position_source.wait(timeout = 0.5)

            utc_time, position, zone = self.position_source.position
            
            if utc_time == self.last_utc_time:
                continue # never had new data.  Just timed out.

            x, y, z = position
            if zone.lower() == 'none':
                self.handle_data((utc_time, x, y, z))
            else:
                self.handle_data((utc_time, x, y, z, zone))
            
            self.last_utc_time = utc_time
            
        # Good idea to close at end of thread so no matter what causes break the sensor won't hang when trying to close.    
        self.received_close_request = False
        self.is_open = False
        
    def stop(self):
        '''Set flag to temporarily stop passing data. Thread safe.'''
        self.stop_passing = True
        
    def resume(self):
        '''Set flag to resume passing sensor data. Thread safe.'''
        self.stop_passing = False
