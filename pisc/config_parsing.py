#!/usr/bin/env python

import sys
import logging
from collections import namedtuple

def parse_config_file(file_path):
    '''
    Read in sensor configuration file. Returns tuple where first element is the config version as a string and
     second element is a list of sensor information where each element in the list corresponds to a sensor.
    ''' 
    sensor_info = []
    version = "unknown"
    
    SensorInfo = namedtuple('SensorInfo', 'type name optional_fields')
    
    with open(file_path, "r") as config_file:
        
        for line in config_file.readlines():
            
            if line.isspace():
                continue
            
            fields = [field.strip() for field in line.split(',')]
            fields = [field for field in fields if len(field) > 0]
        
            if len(fields) == 0:
                continue
            
            if fields[0].startswith('#'):
                continue
            
            if fields[0].lower() == 'version':
                version = fields[1]
                continue
                
            if len(fields) < 2:
                logging.getLogger().error("\nParsing Error: every sensor must have type and name.\nBad line: {}".format(line))
                sys.exit(1)
            
            sensor_type = fields[0]
            sensor_name = fields[1]
            other_fields = fields[2:]
                    
            sensor_info.append(SensorInfo(sensor_type, sensor_name, other_fields))

    return (version, sensor_info)