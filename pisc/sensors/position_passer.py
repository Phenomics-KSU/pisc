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

    def open(self):
        '''Do nothing.'''
        pass
    
    def close(self):
        '''Do nothing.'''
        pass
        
    def start(self):
        '''Pass position data to handlers when it becomes available.'''
        while True:
            
            if self.stop_passing:
                # Don't want to pass data along right now.
                time.sleep(0.1)
                continue
            
            # Block until new position data arrives.
            self.position_source.wait()
            
            time, position = self.position_source.position
            x, y, z = position
            self.handle_data((time, x, y, z))
            
    def stop(self):
        '''Set flag to temporarily stop passing data. Thread safe.'''
        self.stop_passing = True
        
    def resume(self):
        '''Set flag to resume passing sensor data. Thread safe.'''
        self.stop_passing = False