#!/usr/bin/env python

import time
import os
import logging

# Sensors
from sensors.irt_ue import IRT_UE
from sensors.cropcircle import CropCircle
from sensors.canon_mcu import CanonMCU

# Data handlers
from data_handlers.csv_log import CSVLog

def create_sensors(sensor_info, time_source, position_source, output_directory):
    '''
    Create new sensor for each element in sensor_info list and configures it with specified
     time and position sources.
    '''
    sensors = []
    
    log = logging.getLogger()
    
    for sensor_id, info in enumerate(sensor_info):
        
        if len(info) < 2:
            log.error('Invalid sensor configuration info.  Need at least type and name.\n\"{0}\"'.format(info))
            continue
        
        sensor_type = info[0]
        sensor_name = info[1]
        
        # TODO: make data handler configurable
        csv_file_name = '{0}_{1}_{2}.csv'.format(sensor_name, sensor_id, time.strftime("%Y-%m-%d-%H-%M-%S"))
        csv_file_path = os.path.join(output_directory, csv_file_name)
        csv_log = CSVLog(csv_file_path, 0)
        
        if sensor_type == 'irt_ue':
            port = info[2]
            baud = int(info[3])
            sample_rate = float(info[4])
            sensor = IRT_UE(sensor_name, sensor_id, port, baud, sample_rate, time_source, data_handlers=[csv_log])
            
        elif sensor_type == 'canon_mcu':
            port = info[2]
            baud = int(info[3])
            trigger_period = float(info[4])
            sensor = CanonMCU(sensor_name, sensor_id, port, baud, trigger_period, time_source, data_handlers=[csv_log])
            
        elif sensor_type == 'cropcircle':
            sensor = CropCircle(sensor_name, sensor_id, *info[2:])
            
        else:
            log.error('Sensor type \"{0}\" not valid.'.format(sensor_type))
            sensor = None
            continue

        sensors.append(sensor)
        
    return sensors
    