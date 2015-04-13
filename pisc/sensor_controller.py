#!/usr/bin/env python

class SensorController:
    
    def __init__(self, sensors):
        self.sensors = sensors
    
    def set_time(self, time):
        print 'Time is {0}.'.format(time)
        
    def set_position(self, x, y, z):
        print 'Position is {0}.'.format((x, y, z))
        
    def start_sensors(self):
        
        print 'Starting sensors'
        

