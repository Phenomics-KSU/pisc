#!/usr/bin/env python

"""
Sensor Name:    Canon EOS Camera (tested with T5i and 7D)
Manufacturer:   Canon
Sensor Type:    Camera
Modifications:  Equipped with Arduino mini pro microcontroller with USB shield using PTP library.
NOTES:          Due to timing constraints the 1st (and sometimes 2nd) captured image doesn't get logged. 
"""

import time
import serial
import logging

from sensor import Sensor

class CanonMCU(Sensor):
    '''Trigger canon camera using intermediate microcontroller.'''
    
    def __init__(self, name, sensor_id, port, baud, trigger_period, time_source, data_handlers):
        '''Save properties for opening serial port later.'''
        Sensor.__init__(self, 'canon_mcu', name, sensor_id, time_source, data_handlers)

        self.port = port
        self.baud = baud
        
        self.trigger_period = trigger_period

        self.stop_triggering = False # If true then will stop taking pictures.
        self.connection = None
        
        # Command to send to MCU to trigger camera. Send many trigger commands to minimize chance one gets missed.
        self.trigger_command = '\x61' * 20
        
        self.image_count = 0
        
    def open(self):
        '''Open serial port.'''
        # Set short read timeout so can re-send trigger command on a failed ack.
        self.connection = serial.Serial(port=self.port,
                                        baudrate=self.baud,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        timeout=0.1)
        
    def close(self):
        '''Close serial port.'''
        if self.connection is not None:
            self.connection.close()
        
    def start(self):
        '''Enter infinite loop constantly taking pictures or waiting for trigger commands.'''
        self.connection.flushInput()
        self.connection.flushOutput()
        
        # Pause for two seconds before sending any commands to fix timing issue.
        time.sleep(2)
        
        while True:
            
            if self.stop_triggering:
                # Don't want to take pictures right now.
                time.sleep(0.5)
                continue
            
            if self.trigger_period <= 0:
                # Suspend thread until we receive a trigger command.
                # TODO block
                raise NotImplementedError
            
            # Grab time before sending trigger command to MCU since image should capture immediately after.
            time_of_reading = self.time_source.time
            
            if time_of_reading == 0:
                # Haven't received a valid time yet so don't take any images.
                time.sleep(0.25)
                continue
            
            # Tell microcontroller to tell camera to take picture. 
            self.connection.write(self.trigger_command)

            logging.getLogger().debug('Sending trigger command.')
            
            self.image_count += 1

            # Suspend execution until we want to trigger again. 
            # Normally this would happen at the end of the loop, but we need to wait for the image file name to get sent back.
            if self.image_count <= 1:
                # On first image we need to at least wait a couple seconds for camera to initialize and to receive large event dump.
                sleep_time = max(2, self.trigger_period)
            else:
                sleep_time = self.trigger_period
                
            time.sleep(sleep_time)
            
            # Read all available bytes from serial port.  This won't block.
            bytes_to_read = self.connection.inWaiting()
            raw_event_dump = self.connection.read(bytes_to_read)
            
            logging.getLogger().debug('Read in {0} bytes'.format(len(raw_event_dump)))
            #logging.getLogger().debug(raw_event_dump)
            
            if len(raw_event_dump) == 0:
                logging.getLogger().warning('Camera: {0} no data returned from MCU.'.format(self.sensor_name))
                continue
            
            if self.image_count <= 1:
                # Camera won't return filename until NEXT time we time a picture (lags 1 behind).
                continue
            
            # Try to parse a filename out of the camera event dump.
            image_filename = self.parse_filename(raw_event_dump)
            if len(image_filename) == 0:
                logging.getLogger().warning('Camera: {0} could not parse filename from event dump.'.format(self.sensor_name))
                # statuses = parse_status_message(raw_event_dump)
                continue
            
            logging.getLogger().debug(image_filename)
            
            self.handle_data((time_of_reading, image_filename))
        
    def parse_filename(self, rawdata):
        '''Extract filename from raw event dump from camera.'''
        # Find index of IMG prefix.
        filename_index = rawdata.find('IMG')
        
        if filename_index < 0:
            return "" # Can't find image name
            
        image_name = rawdata[filename_index : filename_index+12]

        image_number_index = image_name.find('_')
        
        if image_number_index < 0:
            return "" # Can't find image number so not a valid image name
        
        # Extract image number and extension
        image_number = image_name[image_number_index + 1 : image_number_index + 5]
        
        image_extension =  image_name[-3:]
        
        try:
            image_number = int(image_number)
        except ValueError:
            return "" # Image number not valid so can't produce valid image name

        # Need to increment image number since the event dump where parsing if for the PREVIOUS image
        image_number += 1
        
        # Check for rollover.  In this case 10000 is actually 0001.
        if image_number == 10000:
            image_number = 1
        
        # Combine back into valid file name but using camera name
        image_name = "{0}_{1}.{2}".format(self.sensor_name, image_number, image_extension)
        
        return image_name

    def stop(self):
        '''Set flag to temporarily stop reading data. Thread safe.'''
        self.stop_triggering = True
        
    def resume(self):
        '''Set flag to resume reading sensor data. Thread safe.'''
        self.stop_triggering = False