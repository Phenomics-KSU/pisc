#!/usr/bin/env python

"""
Sensor Name:    GreenSeeker Sensor 
Manufacturer:   Trimble
Sensor Type:    NDVI
Modifications:  
"""

import time
import serial
import struct
import logging

from sensor import Sensor

class GreenSeeker(Sensor):
    '''Request and handle data from the GreenSeeker sensor.'''
    
    def __init__(self, name, sensor_id, port, baud, time_source, data_handlers):
        '''Save properties for opening serial port later.'''
        Sensor.__init__(self, 'green_seeker', name, sensor_id, time_source, data_handlers)

        self.port = port
        self.baud = baud
        
        self.read_timeout = 2
               
        self.stop_reading = False # If true then sensor will stop reading data.
        self.connection = None
        
    def open(self):
        '''Open serial port.'''
        # Setting 'read' timeout to same as sample period so we can re-submit request for data.
        self.connection = serial.Serial(port=self.port,
                                        baudrate=self.baud,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        timeout= self.read_timeout)
        
    def is_closed(self):
        '''Return true if sensor is closed.'''
        return self.connection is None or not self.connection.isOpen()
        
    def actually_close(self):
        '''Actually closes serial port.  Called internally at a predefined time.'''
        try:
            self.connection.close()
        except (AttributeError, serial.SerialException):
            pass
        finally:
            self.connection = None 
        
    def start(self):
        '''Enter infinite loop constantly reading data.'''
               
        
        self.connection.flushInput()
        
        self.handle_metadata(['time (s)','NDVI'])
                
        while True:
            
            if self.received_close_request:
                break
            
            if self.stop_reading:
                # Don't want to take sensor readings right now.
                time.sleep(0.1)
                continue
            
            # Grab time here since it should, on average, represent the actual sensor measurement time.
            # If we grab it after the read/write we could have a context switch from I/O interactions.
            time_of_reading = self.time_source.time
            if time_of_reading <= 0:
                time.sleep(.1)          
                continue                                    
                      
            new_message = self.connection.readline()            
            
            if len(new_message) == 0: 
                logging.getLogger().warning('Sensor: {0} timed out on read.'.format(self.sensor_name))
                continue
                                
            # Removes white space while parsing the message to get the NDVI value                       
            parsed_data = [x.strip() for x in new_message.split(',')]
            if len(parsed_data) != 5:
                continue # ignores first message if it is incomplete
                
            ndvi = parsed_data[3]
            
            # Pass ndvi onto all data handlers if we have a valid timestamp.            
            self.handle_data((time_of_reading, ndvi))
        
        # Good idea to close at end of thread so no matter what causes break the sensor won't hang when trying to close.        
        self.received_close_request = False
        self.actually_close()
                        
    def stop(self):
        '''Set flag to temporarily stop reading data. Thread safe.'''
        self.stop_reading = True
        
    def resume(self):
        '''Set flag to resume reading sensor data. Thread safe.'''
        self.stop_reading = False