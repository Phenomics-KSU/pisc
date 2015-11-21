#!/usr/bin/env python

import time
import os
import logging
import sys

# Sensors
from sensors.irt_ue import IRT_UE
from sensors.canon_mcu import CanonMCU
from sensors.green_seeker import GreenSeeker # Added for Green Seeker
from sensors.position_passer import PositionPasser
from sensors.orientation_passer import OrientationPasser

# Data handlers
from data_handlers.csv_log import CSVLog

def create_sensors(sensor_info, time_source, position_source, orientation_source, output_directory):
    '''
    Create new sensor for each element in sensor_info list and configures it with specified
     time and position sources.
    '''
    sensors = []
    
    log = logging.getLogger()
    
    # Make sure all sensor names are unique so that output files can only use name.
    sensor_names = [info.name for info in sensor_info]
    duplicate_names = list(set([name for name in sensor_names if sensor_names.count(name) > 1]))
    if len(duplicate_names) > 0:
        log.error('Error: All sensor names must be unique.  Found duplicate names.\n\"{}\"'.format(duplicate_names))
        sys.exit(1)
    
    for sensor_id, info in enumerate(sensor_info):
        
        if len(info) < 2:
            log.error('Invalid sensor configuration info.  Need at least type and name.\n\"{}\"'.format(info))
            continue
        
        sensor_type = info.type
        sensor_name = info.name
        optional_fields = info.optional_fields
        
        # TODO: make data handler configurable
        csv_file_name = '{}_{}.csv'.format(sensor_name, time.strftime("%Y-%m-%d-%H-%M-%S"))
        csv_file_path = os.path.join(output_directory, csv_file_name)
        csv_log = CSVLog(csv_file_path, 0)
        
        if sensor_type == 'irt_ue':
            port = optional_fields[0]
            baud = int(optional_fields[1])
            sample_rate = float(optional_fields[2])
            sensor = IRT_UE(sensor_name, sensor_id, port, baud, sample_rate, time_source, data_handlers=[csv_log])
            
        elif sensor_type == 'canon_mcu':
            port = optional_fields[0]
            baud = int(optional_fields[1])
            trigger_period = float(optional_fields[2])
            image_filename_prefix = optional_fields[3]
            sensor = CanonMCU(sensor_name, sensor_id, port, baud, trigger_period, image_filename_prefix, time_source, data_handlers=[csv_log])
            
        elif sensor_type == 'green_seeker':
            port = optional_fields[0]
            baud = int(optional_fields[1])
            sensor = GreenSeeker(sensor_name, sensor_id, port, baud, time_source, data_handlers=[csv_log])

        elif sensor_type == 'position':
            sensor = PositionPasser(sensor_name, sensor_id, time_source, position_source, data_handlers=[csv_log])
    
        elif sensor_type == 'orientation':
            sensor = OrientationPasser(sensor_name, sensor_id, time_source, orientation_source, data_handlers=[csv_log])

        else:
            log.error('Sensor type \"{}\" not valid.'.format(sensor_type))
            sensor = None
            continue

        sensors.append(sensor)
        
    return sensors
    
