#!/usr/bin/env python

import os
import sys
import argparse
import socket
import serial
import math
import time

from sensor_control_client import SensorControlClient
from nmea_parser import parse_nmea_sentence
from checksum_utils import check_nmea_checksum

if __name__ == "__main__":
    
    default_rate = 10 # Hz.  Rate to read messages out of test file.
    
    # Define command line arguments.
    argparser = argparse.ArgumentParser(description='Pass position/time from GPS to PISC server.')
    argparser.add_argument('-f', '--test_file', default='', help='Path to NMEA test log file.')
    argparser.add_argument('-r', '--test_rate', default=default_rate, help='Rate to parse messages from test file. Default {0} Hz'.format(default_rate))
    argparser.add_argument('-p', '--port', default='None', help='Serial port name ie COM4 or /dev/ttyS1.')
    argparser.add_argument('-b', '--baud', default=9600, help='Baud rate of serial port. Default 9600.')
    args = argparser.parse_args()

    # Validate command line arguments.
    port_name = args.port
    baud_rate = int(args.baud)
    test_file_name = args.test_file
    test_rate = float(args.test_rate)
    if test_rate <= 0.0:
        print 'Invalid test rate {0}. Changing to {1}.'.format(test_rate, default_rate)
        test_rate = default_rate
    
    # First try to open a test file that contains NMEA messages.
    nmea_source = None
    using_test_file = False
    if test_file_name != '':
        if not os.path.isfile(test_file_name):
            print '\nThe test file could not be found:\n\'{0}\'\n'.format(test_file_name)
            sys.exit(1)
        else:
            print 'Using provided test file.'
            nmea_source = open(test_file_name, 'r')
            using_test_file = True
    
    # If user didn't specify a test file then open the actual serial port.
    if nmea_source is None:
        try:
            print "\nOpening port {0} with baud {1}".format(port_name, baud_rate)
            nmea_source = serial.Serial(port=port_name, baudrate=baud_rate, timeout=2)
        except serial.serialutil.SerialException, e:
            print 'Failed to open GPS\n{0}'.format(e)
            sys.exit(1)
    
    # TODO: Support multiple clients read in from config file
    host = socket.gethostname()
    port = 5000
    print 'Connecting to server at {0}:{1}'.format(host, port)
    client = SensorControlClient(host, port)
    
    send_counter = 0 # number of position/time messages sent to by client
    display_count = 10 # how many messages to send before displaying feedback character
    
    print 'Each period represents {0} sent messages.'.format(display_count)
    
    try:
        while True:
            # Delay when using test file so all messages don't get read out at once.
            if using_test_file:
                time.sleep(1.0/test_rate)
            
            nmea_string = nmea_source.readline().strip()

            if not check_nmea_checksum(nmea_string):
                print "Received a sentence with an invalid checksum. Sentence was: {0}".format(repr(nmea_string))
                continue
            
            parsed_sentence = parse_nmea_sentence(nmea_string)
            if not parsed_sentence:
                print "Failed to parse NMEA sentence. Sentence was: {0}".format(nmea_string)
                continue
            
            if 'GGA' in parsed_sentence:
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
                    print 'Invalid UTC time: {0}'.format(utc_time)
                    continue
                
                client.send_time_and_position(utc_time, latitude, longitude, altitude)

                # Printout period once for every 'display_count' messages for constant feedback that messages are being sent.
                send_counter += 1
                if (send_counter % display_count) == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()
            
    except KeyboardInterrupt:
        print "\nKeyboard interrupt detected"
        print "Shutting down..."
    