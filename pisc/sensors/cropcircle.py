#!/usr/bin/env python

"""
Sensor Name:    CropCircle ACS-470
Manufacturer:   Holland Scientific
Sensor Type:    NVDI
"""

# TODO: This class is untested and has not been used yet.

import serial

class CropCircle:
    
    def __init__(self, name, id, port, baud):
        self.name = name
        self.id = id
        self.port = port
        self.baud = baud
        
    def open(self):
        self.connection = serial.Serial(port=self.port,
                                        baudrate=self.baud,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS)
        
    def close(self):
        self.connection.close()
        
    def start(self):
        
        while True:
            data = self.connection.readline()
            print data
        