#!/usr/bin/env python

import threading

from serial.serialutil import SerialException

class SensorController:
    '''Start/stop sensors and filter commands for individual sensors. '''
    
    def __init__(self, sensors):
        '''Constructor'''
        self.sensors = sensors
        self.threads = []
        
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
        '''Stop and close all sensors.'''
        for sensor in self.sensors:
            sensor.stop()
            sensor.close()
                       
        

