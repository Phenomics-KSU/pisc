#!/usr/bin/env python

import time

# Sensors
from sensors.irt_ue import IRT_UE
from sensors.cropcircle import CropCircle

# Data handlers
from data_handlers.csv_log import CSVLog

def create_sensors(sensor_info, time_source, position_source):
    
    sensors = []
    
    for sensor_id, info in enumerate(sensor_info):
        
        if len(info) < 2:
            print 'Invalid sensor configuration info.  Need at least type and name.\n\"{0}\"'.format(info)
            continue
        
        sensor_type = info[0]
        sensor_name = info[1]
        
        if sensor_type == 'irt_ue':
            # TODO: make data handler configurable
            csv_log = CSVLog(time.strftime("%Y%m%d-%H%M%S"), 0)
            port = info[2]
            baud = int(info[3])
            sample_rate = float(info[4])
            sensor = IRT_UE(sensor_name, sensor_id, port, baud, sample_rate, time_source, data_handlers=[csv_log])
            
        elif sensor_type == 'cropcircle':
            print 'Test Message: Creating crop circle.'
            sensor = CropCircle(sensor_name, sensor_id, *info[2:])
            
        else:
            print 'Sensor type \"{0}\" not valid.'.format(sensor_type)
            sensor = None
            continue

        sensors.append(sensor)
        
    return sensors
    