#!/usr/bin/env python

class SensorController:
    
    def set_time(self, time):
        print 'Time is {0}.'.format(time)
        
    def set_position(self, x, y, z):
        print 'Position is {0}.'.format((x, y, z))

