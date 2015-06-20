#!/usr/bin/env python

"""
Sensor Name:    Orientation Data Passer
Manufacturer:   None
Sensor Type:    Orientation 
"""

import time
import serial
import struct
import logging

from sensor import Sensor

class OrientationPasser(Sensor):
    '''Simple class that passes data along from orientation source to data handlers.'''
    
    def __init__(self, name, sensor_id, time_source, orientation_source, data_handlers):
        '''Constructor.'''
        Sensor.__init__(self, 'orientation', name, sensor_id, time_source, data_handlers)
        
        self.orientation_source = orientation_source
        
        self.stop_passing = False # If true then sensor will passing data to handlers.

    def open(self):
        '''Do nothing.'''
        pass
    
    def close(self):
        '''Do nothing.'''
        pass
        
    def start(self):
        '''Pass orientation data to handlers when it becomes available.'''
        while True:
            
            if self.stop_passing:
                # Don't want to pass data along right now.
                time.sleep(0.1)
                continue
            
            # Block until new orientation data arrives.
            self.orientation_source.wait()
            
            time, frame, rotation_type, orientation = self.orientation_source.orientation
            r1, r2, r3, r4 = orientation
            self.handle_data((time, frame, rotation_type, r1, r2, r3, r4))
            
    def stop(self):
        '''Set flag to temporarily stop passing data. Thread safe.'''
        self.stop_passing = True
        
    def resume(self):
        '''Set flag to resume passing sensor data. Thread safe.'''
        self.stop_passing = False
