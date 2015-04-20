#!/usr/bin/env python

import sys
import os
import argparse
import socket
import serial
import time

from sensor_control_server import SensorControlServer
from sensor_controller import SensorController
from config_parsing import parse_config_file
from sensor_creation import create_sensors
from time_sources import SimpleTimeSource

current_pisc_version = '0.0'
current_config_version = '0.0'

if __name__ == "__main__":
    
    print '\nPISC Version {0}'.format(current_pisc_version)
    
    # Define necessary and optional command line arguments.
    parser = argparse.ArgumentParser(description='Uses config file to startup sensors and server.')
    parser.add_argument('config_file', help='path to sensor configuration file')
    args = parser.parse_args()

    # Validate command line arguments.
    config_file = args.config_file
    if not os.path.isfile(config_file):
        print '\nThe configuration file could not be found:\n\'{0}\'\n'.format(config_file)
        sys.exit(1)
    
    (config_version, sensor_info) = parse_config_file(config_file)
    
    # Validate information parsed in from configuration file.
    if config_version != current_config_version:
        print '\nWARNING: config version: \"{0}\" doesn\'t match current version: \"{1}\"'.format(config_version, current_config_version)
    
    if len(sensor_info) == 0:
        print 'No sensor information found in configuration file.'
        sys.exit(1)
        
    time_source = SimpleTimeSource()
    
    sensors = create_sensors(sensor_info, time_source)
    
    print 'Created {0} sensors.'.format(len(sensors))
    
    sensor_controller = SensorController(sensors, time_source)

    # Start each sensor reading on its own thread.
    sensor_controller.startup_sensors()

    host = socket.gethostname()
    port = 5000

    print 'Server listening on {0}:{1}'.format(host, port)
    server = SensorControlServer(sensor_controller, host, port)

    # This will keep running until the program is interrupted with Ctrl-C
    try:
        server.activate()
    except KeyboardInterrupt:
        print "\nKeyboard interrupt detected"
        print "Closing all sensors"        
        sensor_controller.close_sensors()
        # TODO terminate all data handlers
            
    print 'Server shutting down...'
    