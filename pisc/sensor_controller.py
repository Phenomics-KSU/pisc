#!/usr/bin/env python

import threading

from serial.serialutil import SerialException

class SensorController:
    
    def __init__(self, sensors, time_source):
        self.sensors = sensors
        self.threads = []
        self.time_source = time_source
        self.position = (0, 0, 0)
    
    def set_time(self, new_time):
        print new_time
        self.time_source.set_time(new_time)
        
    def set_position(self, x, y, z):
        self.position = (x, y, z)

    def get_position(self):
        return self.position

    def startup_sensors(self):
        '''Open each sensor interface and create a new thread to start reading data.'''
                
        print 'Starting up sensors:'
                
        for sensor in self.sensors:
            print 'ID: {2}  Type: {0}  Name: {1}'.format(sensor.get_type(), sensor.get_name(), sensor.get_id())
            
            try:    
                sensor.open()
            except SerialException, e:
                print 'ERROR: Failed to open sensor\n{0}'.format(e)
                continue
                        
            # Now that sensor is open we can start a new thread to read data.
            # We want it to be a daemon thread so it doesn't keep the process from closing.
            t = threading.Thread(target=sensor.start)
            t.setDaemon(True)
            self.threads.append(t)
            t.start()
            
    def close_sensors(self):
        '''Close all sensors.'''
        
        for sensor in self.sensors:
            sensor.stop()
            sensor.close()
                       
        

