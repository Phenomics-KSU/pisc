#!/usr/bin/env python

class Sensor:
    '''Base class for all sensors.''' 
    
    def __init__(self, sensor_type, sensor_name, sensor_id, time_source, data_handlers):
        '''Base constructor'''
        self.sensor_type = sensor_type
        self.sensor_name = sensor_name
        self.sensor_id = sensor_id
        self.time_source = time_source
        self.data_handlers = data_handlers

    def get_type(self):
        '''Return type of sensor.'''
        return self.sensor_type
    
    def get_name(self):
        '''Return sensor name. Not unique.'''
        return self.sensor_name
    
    def get_id(self):
        '''Return unique sensor ID number.'''
        return self.sensor_id
        
    def handle_data(self, data):
        '''Pass the data on to each data handler.'''
        for data_handler in self.data_handlers:
            data_handler.handle_data(data)
            
    def open(self):
        '''Open sensor interface.  Need to override.'''
        raise NotImplementedError

    def close(self):
        '''Close sensor interface.  Need to override.'''
        raise NotImplementedError

    def start(self):
        '''Start reading sensor data.  Need to override.'''
        raise NotImplementedError

    def stop(self):
        '''Stop reading sensor data.  Need to override.'''
        raise NotImplementedError
    
    def resume(self):
        '''Resume reading sensor data.  Need to override.'''
        raise NotImplementedError
    
    def do_action(self, action_type):
        '''Override to perform actions.'''
        return