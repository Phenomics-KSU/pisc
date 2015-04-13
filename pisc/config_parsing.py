#!/usr/bin/env python

def parse_config_file(file_name):
    
    file = open(file_name, "r")
    
    sensor_info = []
    version = "unknown"
    
    for line in file.readlines():
        
        if line.isspace():
            continue
        
        fields = [field.strip() for field in line.split(',')]
    
        if len(fields) == 0:
            continue
        
        if fields[0].startswith('#'):
            continue
        
        if fields[0].lower() == 'version':
            version = fields[1]
            continue
            
        sensor_info.append(fields)

    return (version, sensor_info)