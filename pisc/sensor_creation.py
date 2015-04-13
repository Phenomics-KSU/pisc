#!/usr/bin/env python

from sensors.cropcircle import CropCircle

def create_sensors(sensor_info):
    
    sensors = []
    
    for sensor_id, info in enumerate(sensor_info):
        
        if len(info) < 2:
            print 'Invalid sensor configuration info.  Need at least type and name.\n\"{0}\"'.format(info)
            continue
        
        sensor_type = info[0]
        sensor_name = info[1]
        
        if sensor_type == 'cropcircle':
            print 'Test Message: Creating crop circle.'
            sensor = CropCircle(sensor_name, sensor_id, *info[2:])
        else:
            print 'Sensor type \"{0}\" not valid.'.format(sensor_type)
            sensor = None
            continue

        sensors.append(sensor)