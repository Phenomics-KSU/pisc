#!/usr/bin/env python

import sys
import os
import argparse
import socket
import serial
import time
import logging

from sensor_control_server import SensorControlServer
from sensor_controller import SensorController
from config_parsing import parse_config_file
from sensor_creation import create_sensors
from time_position_sources import *

current_pisc_version = '0.0'
current_config_version = '0.0'

if __name__ == "__main__":
    '''
    Create sensors using configuration file and listens on port for incoming time/position/commands from client.
    '''
    # Create root logger at lowest level since each handler will define its own level which will further filter.
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    
    # Add a console handler to show all messages to user.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    log.addHandler(console_handler)
    
    # Add another handler to record additional information to a log file.
    handler = logging.FileHandler('pisc.log')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s'))
    log.addHandler(handler)
    
    log.info('PISC Version {0}'.format(current_pisc_version))
    
    # Time is treated as a double-precision floating point number which should always be true.
    # If for some reason it's not then notify a user that all times will be incorrect.
    max_required_precision = 1e-13
    if sys.float_info.epsilon > max_required_precision:
        log.critical('System doesn\'t support required precision. Time\'s will not be correct. Aborting.')
        sys.exit(1)
        
    # Default command line argument values
    default_host = socket.gethostname()
    default_port = 5000
    
    # Define necessary and optional command line arguments.
    argparser = argparse.ArgumentParser(description='Uses config file to startup sensors and server.')
    argparser.add_argument('config_file', help='path to sensor configuration file')
    argparser.add_argument('-n', '--host', default=default_host, help='Server host name. Default {0}.'.format(default_host))
    argparser.add_argument('-p', '--port', default=default_port, help='Server port number. Default {0}.'.format(default_port))
    args = argparser.parse_args()

    # Validate command line arguments.
    config_file = args.config_file
    port = int(args.port)
    host = args.host
    if not os.path.isfile(config_file):
        log.error('The configuration file could not be found:\'{0}\''.format(config_file))
        sys.exit(1)
    
    (config_version, sensor_info) = parse_config_file(config_file)
    
    # Validate information parsed in from configuration file.
    if config_version != current_config_version:
        log.warn('config version: \"{0}\" doesn\'t match current version: \"{1}\"'.format(config_version, current_config_version))
    
    if len(sensor_info) == 0:
        log.error('No sensor information found in configuration file.')
        sys.exit(1)
        
    time_source = SimpleTimeSource()
    position_source = SimplePositionSource()
    
    sensors = create_sensors(sensor_info, time_source, position_source)
    
    log.info('Created {0} sensors.'.format(len(sensors)))

    sensor_controller = SensorController(sensors)

    # Start each sensor reading on its own thread.
    sensor_controller.startup_sensors()

    log.info('Server listening on {0}:{1}'.format(host, port))
    server = SensorControlServer(sensor_controller, time_source, position_source, host, port)

    # This will keep running until the program is interrupted with Ctrl-C
    try:
        server.activate()
    except KeyboardInterrupt:
        log.info("Keyboard interrupt detected")
        log.info("Closing all sensors")
        sensor_controller.close_sensors()
        # TODO terminate all data handlers
            
    log.info('Server shutting down.')
    