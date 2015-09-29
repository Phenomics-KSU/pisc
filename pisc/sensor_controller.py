#!/usr/bin/env python

import threading
import logging
import time

from serial.serialutil import SerialException

class SensorController:
    '''Start/stop sensors and filter commands for individual sensors. '''
    
    def __init__(self, sensors):
        '''Constructor'''
        self.sensors = sensors
        self.threads = []
        
    def startup_sensors(self):
        '''Open each sensor interface and create a new thread to start reading data.'''

        log = logging.getLogger()

        log.info('Starting up sensors:')
        
        failed_sensor_count = 0
        failed_sensor_error_messages = ""
                
        for sensor in self.sensors:
            log.info('ID: {2}  Type: {0}  Name: {1}'.format(sensor.get_type(), sensor.get_name(), sensor.get_id()))
            
            try:    
                sensor.open()
            except SerialException, e:
                failed_sensor_count += 1
                failed_sensor_error_messages += "\n{} (id-{}) {}".format(sensor.get_name(), sensor.get_id(), e)
                continue
                        
            # Now that sensor is open we can start a new thread to read data.
            # We want it to be a daemon thread so it doesn't keep the process from closing.
            t = threading.Thread(target=sensor.start)
            t.setDaemon(True)
            self.threads.append(t)
            t.start()

        if failed_sensor_count == 0:
            log.info("\nAll sensors opened successfully.\n")
        else:
            log.warn("\nFailed to open {} sensors. Details:{}\n".format(failed_sensor_count, failed_sensor_error_messages))
            
    def close_sensors(self):
        '''Stop and close all sensors.'''
        log = logging.getLogger()
        for sensor in self.sensors:
            
            if sensor.is_closed():
                log.info("Sensor {} already closed.".format(sensor.sensor_name))
                continue
            
            time_requested_to_close = float(sensor.time_needed_to_close())
            log.info('Giving sensor {} {} seconds to close.'.format(sensor.sensor_name, time_requested_to_close))
            first_close_time = time.time()
            sensor.close()
            while not sensor.is_closed():
                if time.time() - first_close_time > time_requested_to_close:
                    log.warn('Couldn\'t close sensor...moving to next sensor.')
                    break
                time.sleep(0.2)

                       
