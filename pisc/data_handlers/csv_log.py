#!/usr/bin/env python

import csv
from _ctypes import ArgumentError

class CSVLog:
    '''
    Log each sensor data sample on a new line separated by commas with a \r\n line terminator.
    If any element of the data contains a comma that element is enclosed in quotes.
    '''
    
    def __init__(self, file_name, buffer_size):
        '''
        Save properties for creating log file when first data is received.
        
        file_name must not already exist on the file system or an exception will be thrown.
        
        Buffer size is how many samples to buffer before writing (and flushing) to file.
        buffer_size =  0 or 1  flush every sample to file right when it's received.
        buffer_size =  n       buffer 'n' samples before flushing all of them to the file.
        '''
        self.file_name = file_name
        self.buffer_size = buffer_size
        self.buffer = []
        self.file = None
        
    def handle_data(self, sensor_type, sensor_id, data):
        '''Write data to file or buffer it depending on class settings. Data is a tuple.'''
                
        if (data is None) or (len(data) == 0):
            # Create blank one element tuple so it's obvious in log that no data was received.
            data = ' ',
        
        # Check if all we need to do is buffer data.
        if self.buffer_size > 1:
            if len(self.buffer) < (self.buffer_size - 1):
                self.buffer.append(data)
                return
             
        # Make sure file is open so we can write to it.
        if self.file is None:
            self.file = open(self.file_name, 'wb')
            self.writer = csv.writer(self.file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
        if len(self.buffer) > 0:
            # Write all the data we've been saving.
            self.writer.writerows(self.buffer)
            self.buffer = []
                    
        # Write current sample data.
        self.writer.writerow(data)
        
        # Make sure data gets written in case of power failure.
        self.file.flush()
            
    def handle_metadata(self, sensor_type, sensor_id, metadata): 
        '''Store metadata in buffer to be written out the first time handle_data is called.'''
        if len(metadata) == 0:
            raise ArgumentError('Metadata must contain at least one element')
        
        metadata[0] = '#' + str(metadata[0])
        self.buffer.append(metadata)
        
    def terminate(self):
        '''Write any buffered data to file and then close file.'''
        if self.writer is None:
            return # Never received any data.
        
        if len(self.buffer) > 1:
            self.writer.writerows(self.buffer)
        
        self.file.flush()
        self.file.close()
        self.file = None
        