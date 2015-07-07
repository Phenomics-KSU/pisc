#!/usr/bin/env python

"""
Sensor Name:    ThermoMETER CT-SF02-C1 
Manufacturer:   Micro Epsilon (UE)
Sensor Type:    Infrared Temperature
Modifications:  Serial -> USB FTDI 3.3V DEV-09873
"""

import time
import serial
import struct
import logging

from sensor import Sensor

class IRT_UE(Sensor):
    '''Request and handle data from ThermoMETER-CT IRT sensor.'''
    
    def __init__(self, name, sensor_id, port, baud, sample_rate, time_source, data_handlers):
        '''Save properties for opening serial port later.'''
        Sensor.__init__(self, 'irt_ue', name, sensor_id, time_source, data_handlers)

        self.port = port
        self.baud = baud
        
        self.sample_period = 0.0
        if sample_rate != 0.0:
            self.sample_period = 1.0 / sample_rate
        
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
                                        timeout=self.sample_period)
        
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
        # How many bytes to read each time sensor sends data.
        bytes_to_read = 2
                
        while True:
            
            if self.received_close_request:
                break # end thread
            
            if self.stop_reading:
                # Don't want to take sensor readings right now.
                time.sleep(0.1)
                continue
            
            # Grab time here since it should, on average, represent the actual sensor measurement time.
            # If we grab it after the read/write we could have a context switch from I/O interactions.
            time_of_reading = self.time_source.time

            # Make sure nothing extra is sitting in buffer so that next two bytes we read in should be from new request. 
            self.connection.flushInput()

            # Request a new reading from the sensor. 
            self.connection.write("\x01")
            
            # Block until we get data or the timeout occurs.
            raw_data = self.connection.read(bytes_to_read)
            
            if len(raw_data) < bytes_to_read:
                logging.getLogger().warning('Sensor: {0} timed out on read.'.format(self.sensor_name))
                continue
        
            # Convert data into a temperature value.
            d1 = struct.unpack("B", raw_data[0])[0]
            d2 = struct.unpack("B", raw_data[1])[0]
            temperature = (d1 * 256.0 + d2 - 1000.0) / 10.0
        
            # Pass temperature onto all data handlers if we have a valid timestamp.
            if time_of_reading > 0:
                self.handle_data((time_of_reading, temperature))
        
            # Suspend execution until we want to sample again.
            time.sleep(self.sample_period)
        
        # Good idea to close at end of thread so no matter what causes break the sensor won't hang when trying to close.        
        self.received_close_request = False
        self.actually_close()
            
    def stop(self):
        '''Set flag to temporarily stop reading data. Thread safe.'''
        self.stop_reading = True
        
    def resume(self):
        '''Set flag to resume reading sensor data. Thread safe.'''
        self.stop_reading = False