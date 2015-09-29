#!/usr/bin/env python

import os
import sys
import argparse
import socket
import serial
import math
import time

from gps_server import GPSServer
from nmea_parser import parse_nmea_sentence
from checksum_utils import check_nmea_checksum

# Default command line argument values.  Global so sensor controller can use as default host.
default_server_host = socket.gethostname()
default_server_port = 50005

if __name__ == "__main__":
    '''
    Read in NMEA messages from either a GPS or test file and immediately send time/position information
     to each sensor client.  Runs until keyboard interrupt.
    '''
    default_rate = 10 # Hz.  Rate to read messages out of test file.
    default_gps_baud = 9600 
    
    fix_types = { '0': 'None',
                  '1': 'GPS',
                  '2': 'DGPS',
                  '3': 'PPS',
                  '4': 'Fixed RTK',
                  '5': 'Float/Location RTK or OmniStar',
                  '6': 'Dead Reckoning',
                  '7': 'Manual',
                  '8': 'Simulation' }

    # Define command line arguments.
    argparser = argparse.ArgumentParser(description='Pass position/time from GPS to sensor controller.')
    argparser.add_argument('-n', '--host', default=default_server_host, help='Server host name. Default {}.'.format(default_server_host))
    argparser.add_argument('-x', '--server_port', default=default_server_port, help='Server port number. Default {}.'.format(default_server_port))
    argparser.add_argument('-f', '--test_file', default='', help='Path to NMEA test log file.')
    argparser.add_argument('-r', '--test_rate', default=default_rate, help='Rate to parse messages from test file. Default {} Hz'.format(default_rate))
    argparser.add_argument('-p', '--serial_port', default='None', help='Serial port name ie COM4 or /dev/ttyS1.')
    argparser.add_argument('-b', '--baud', default=default_gps_baud, help='Baud rate of serial port. Default {}.'.format(default_gps_baud))
    argparser.add_argument('-s', '--required_fix', default= 'None', help='Required fix quality indicator in GGA message. Options {}'.format(fix_types))
    argparser.add_argument('-z', '--required_precision', default= -1, help='Set the max standard deviation of latitude/longitude error for usable data.')
    args = argparser.parse_args()

    # Validate command line arguments.
    host = args.host
    server_port = args.server_port
    serial_port_name = args.serial_port
    baud_rate = int(args.baud)
    test_file_name = args.test_file
    required_fix = args.required_fix.lower()
    required_precision = float(args.required_precision)
    test_rate = float(args.test_rate)
    
    if test_rate <= 0.0:
        print 'Invalid test rate {}. Changing to {}.'.format(test_rate, default_rate)
        test_rate = default_rate
        
    if required_fix != 'none' and required_fix not in fix_types:
        print 'Invalid required fix {}. See options in --help.'.format(required_fix)
        sys.exit(1)
        
    # Initialize last_fix and last_error as values that will never occur
    last_fix = '-1'
    last_error = -1.0
    data_quality = True
    gga_count = 0 # how many gga messages have been received since last GST message.
    
    # First try to open a test file that contains NMEA messages.
    nmea_source = None
    using_test_file = False
    if test_file_name != '':
        if not os.path.isfile(test_file_name):
            print '\nThe test file could not be found:\n\'{}\'\n'.format(test_file_name)
            sys.exit(1)
        else:
            print 'Using provided test file.'
            nmea_source = open(test_file_name, 'r')
            using_test_file = True
    
    # If user didn't specify a test file then open the actual serial port.
    if nmea_source is None:
        try:
            print "\nOpening serial port {} with baud {}".format(serial_port_name, baud_rate)
            nmea_source = serial.Serial(port=serial_port_name, baudrate=baud_rate, timeout=2)
        except serial.serialutil.SerialException, e:
            print 'Failed to open GPS\n{}'.format(e)
            sys.exit(1)
    
    print "Starting server at {}:{}".format(host, server_port)
    server = GPSServer(host, server_port)
    server.setDaemon(True)
    server.start()

    send_counter = 0 # number of position/time messages sent 
    display_count = 10 # how many messages to send before displaying feedback character
    
    print 'Each period represents {} new position messages.'.format(display_count)
          
    if required_precision > 0:
        print 'Required precision set to {}'.format(required_precision)
        # Override to false until we know we have good precision.
        data_quality = False
          
    if required_fix != 'none':
        print 'Waiting for required fix of {}'.format(fix_types[required_fix])
          
    try:
        while True:
            # Delay when using test file so all messages don't get read out at once.
            if using_test_file:
                time.sleep(1.0/test_rate)
            
            nmea_string = nmea_source.readline().strip()
            
            # time (in seconds) that the most recent nmea message was read in.
            message_read_time = time.time()

            if not check_nmea_checksum(nmea_string):
                print "Received a sentence with an invalid checksum. Sentence was: {}".format(repr(nmea_string))
                continue
            
            parsed_sentence = parse_nmea_sentence(nmea_string)
            if not parsed_sentence:
                print "Failed to parse NMEA sentence. Sentence was: {}".format(nmea_string)
                continue
                               
            if required_precision > 0:
                
                if gga_count > 100:
                    print 'Received {} GGA messages and 0 GST messages'.format(gga_count)
                    gga_count = 0
                                                                
                if 'GST' in parsed_sentence:
                    data = parsed_sentence['GST']
                    
                    lat_error = data['latitude_error']
                    long_error = data['longitude_error']
                    
                    current_error = max(lat_error,long_error)
                    
                    data_quality = True  
                                  
                    gga_count = 0
                    
                    if current_error > required_precision:
                        
                        if current_error != last_error:
                            print 'Current error of {}m is too large.'.format(current_error)
                            last_error = current_error                        
                                             
                        data_quality = False
                        
            if 'GGA' in parsed_sentence:
                
                gga_count += 1
                                 
                data = parsed_sentence['GGA']
                           
                latitude = data['latitude']
                if data['latitude_direction'] == 'S':
                    latitude = -latitude
         
                longitude = data['longitude']
                if data['longitude_direction'] == 'W':
                    longitude = -longitude
                     
                # Altitude is above ellipsoid, so adjust for mean-sea-level
                altitude = data['altitude'] + data['mean_sea_level']
                 
                utc_time = data['utc_time']
                if math.isnan(utc_time):
                    print 'Invalid UTC time: {}'.format(utc_time)
                    continue
                
                if data_quality == True: 
                    
                    fix = str(data['fix_type'])
                    
                    if required_fix != 'none' and fix != required_fix:
                        
                        if fix != last_fix:
                            last_fix = fix
                            print 'Insufficient fix: {}'.format(fix_types[fix])
                            
                        continue # bad fix 
                        
                    if fix != last_fix:  
                        last_fix = fix
                        print 'Current fix: {}'.format(fix_types[fix])
                        
                    server.new_position(utc_time, message_read_time, latitude, longitude, altitude)
     
                    # Print out new period once for every 'display_count' messages for constant feedback that messages are being sent.
                    send_counter += 1
                    if (send_counter % display_count) == 0:
                        sys.stdout.write('.')
                        sys.stdout.flush()
           
                                            
    except KeyboardInterrupt:
        print "\nKeyboard interrupt detected"
        print "Shutting down..."
    
