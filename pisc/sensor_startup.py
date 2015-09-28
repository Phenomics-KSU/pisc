#!/usr/bin/env python

import sys
import os
import argparse
import socket
import serial
import time
import logging

from gps_client import GPSClient
from sensor_controller import SensorController
from config_parsing import parse_config_file
from sensor_creation import create_sensors
from time_position_sources import *
from version import current_pisc_version, current_config_version
from gps_startup import default_server_host, default_server_port

if __name__ == "__main__":
    '''
    Create sensors using configuration file and listens on port for incoming time/position/commands from client.
    '''
    # Use home directory for root output directory. This is platform independent and works well with an installed package.
    home_directory = os.path.expanduser('~')
    
    # Create timestamped directory for current run.
    output_directory = os.path.join(home_directory, 'pisc-output/', time.strftime("pisc-%Y-%m-%d-%H-%M-%S/"))
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Create root logger at lowest level since each handler will define its own level which will further filter.
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    
    # Add a console handler to show all messages to user.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    log.addHandler(console_handler)
    
    # Add another handler to record additional information to a log file.
    handler = logging.FileHandler(os.path.join(output_directory, 'pisc.log'))
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s'))
    log.addHandler(handler)
 
    log.info('PISC Version {0}'.format(current_pisc_version))
    
    # Time is treated as a double-precision floating point number which should always be true.
    # If for some reason it's not then notify a user that all times will be incorrect.
    max_required_precision = 1e-13
    if sys.float_info.epsilon > max_required_precision:
        log.critical('System doesn\'t support required precision. Time\'s will not be correct. Aborting.')
        sys.exit(1)
        
    # Default time (in milliseconds) to use for threshold when syncing time on startup.  Smaller is stricter.
    default_sync_time = 15
    
    # Define necessary and optional command line arguments.
    argparser = argparse.ArgumentParser(description='Uses config file to startup sensors and server.')
    argparser.add_argument('config_file', help='path to sensor configuration file')
    argparser.add_argument('-n', '--host', default=default_server_host, help='Server host name. Default {}.'.format(default_server_host))
    argparser.add_argument('-p', '--port', default=default_server_port, help='Server port number. Default {}.'.format(default_server_port))
    argparser.add_argument('-s', '--sync_thresh', default=default_sync_time, help='Time (in milliseconds) to use for threshold when syncing time. Smaller is stricter. If not greater than 0 then will disable syncing. Default {}.'.format(default_sync_time))
    args = argparser.parse_args()

    # Validate command line arguments.
    config_file = args.config_file
    host = args.host
    port = int(args.port)
    sync_time_thresh = float(args.sync_thresh) / 1000.0 # convert from ms to seconds
    sync_required = (sync_time_thresh > 0)
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
        
    time_source = RelativePreciseTimeSource()
    position_source = SimplePositionSource()
    orientation_source = SimpleOrientationSource()
    
    sensors = create_sensors(sensor_info, time_source, position_source, orientation_source, output_directory)
    
    log.info('Created {} sensors.'.format(len(sensors)))

    sensor_controller = SensorController(sensors)

    # Start each sensor reading on its own thread.
    sensor_controller.startup_sensors()

    gps_client = GPSClient((host, port), sensor_controller, time_source, position_source, orientation_source, sync_time_thresh)

    # This will keep running until the program is interrupted with Ctrl-C
    try:
        gps_client.connect(sync_required)
        gps_client.start()
    except KeyboardInterrupt:
        log.info("Keyboard interrupt detected")
        log.info("Closing all sensors")
        sensor_controller.close_sensors()
        # TODO terminate all data handlers
            
    log.info('Shut down.')
    