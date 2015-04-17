#!/usr/bin/env python

"""
Sensor Name:    ThermoMETER CT-SF02-C1 
Manufacturer:   Micro Epsilon (UE)
Sensor Type:    Infrared Temperature
"""

import time
import serial
import struct

class IRT_UE:
    '''Request and handle data from ThermoMETER-CT IRT sensor.'''
    
    def __init__(self, name, id, port, baud, sample_rate):
        '''Save properties for opening serial port later.'''
        self.name = name
        self.id = id
        self.port = port
        self.baud = baud
        self.sample_period = 1.0 / sample_rate
        
    def open(self):
        '''Open serial port.'''
        # Setting 'read' timeout to same as sample period so we can re-submit request for data.
        self.connection = serial.Serial(port=self.port,
                                        baudrate=self.baud,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        timeout=self.sample_period)
        
    def close(self):
        '''Close serial port.'''
        self.connection.close()
        
    def start(self):
        '''Enter infinite loop constantly reading data.'''
        
        # How many bytes to read each time sensor sends data.
        bytes_to_read = 2
        
        self.connection.flushInput()
                
        while True:
            
            # Request a new reading from the sensor. 
            self.connection.write("\x01")
            
            # Block until we get data or the timeout occurs.
            data = self.connection.read(bytes_to_read)
            
            if len(data) < bytes_to_read:
                # Timeout occured.
                # TODO: support general error reporting to a log file.  
                #report_error("Missed IRT UI reading.")
                print "no data received"
                continue
        
            # Convert data into a temperature value.
            d1 = struct.unpack("B", data[0])[0]
            d2 = struct.unpack("B", data[1])[0]
            temperature = (d1 * 256.0 + d2 - 1000.0) / 10.0
        
            # TODO: print isn't thread-safe.  Just using for temporary testing.
            #handle_data(data)
            print temperature
        
            # Suspend execution until we want to sample again.
            time.sleep(self.sample_period)