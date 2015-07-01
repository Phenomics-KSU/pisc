#!/usr/bin/env python

"""
Sensor Name:    Canon EOS Camera (tested with T5i and 7D)
Manufacturer:   Canon
Sensor Type:    Camera
Modifications:  Equipped with Arduino mini pro microcontroller (MCU) with USB shield using PTP library.
Notes:          Due to how the PTP library and MCU are setup the very last captured image isn't logged. 
"""

import time
import serial
import logging

from sensor import Sensor

class CanonMCU(Sensor):
    '''Trigger canon camera using intermediate microcontroller.'''
    
    def __init__(self, name, sensor_id, port, baud, trigger_period, image_filename_prefix, time_source, data_handlers):
        '''Save properties for opening serial port later.'''
        Sensor.__init__(self, 'canon_mcu', name, sensor_id, time_source, data_handlers)

        self.port = port
        self.baud = baud
        
        self.trigger_period = trigger_period
        
        self.image_filename_prefix = image_filename_prefix

        self.stop_triggering = False # If true then will stop taking pictures.
        self.connection = None
        
        # Command to send to MCU to sync camera time. 
        self.sync_command = '\x73' # ascii s
        
        # Command to send to MCU to trigger camera. 
        self.trigger_command = '\x74' # ascii t
        
        # Acknowledgment command
        self.ack_command = '\x61' # ascii a
        
        # UTC timestamp that all MCU reported image times are relative to.
        self.synced_utc_time = 0
        
        # Last image filename received by camera.  
        self.last_image_filename = 'none'
        
        # How many dump messages that filename couldn't be extracted from.
        self.failed_image_name_parse_count = 0
        
        self.image_count = 0
        
        self.input_stream = '' # data buffer received from MCU that hasn't been used yet
        
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
        
        # Pause for two seconds before sending any commands to give MCU time to startup and fix weird timing issue.
        time.sleep(2)
        
        # Wait until have a valid time source before starting camera.
        current_time = self.time_source.time    
        while current_time == 0:
            time.sleep(0.25)
            current_time = self.time_source.time
        
        # Create mapping between our time source and relative MCU time source so we can tag images with times.
        self.sync_mcu_time()
            
        while True:
            
            if self.stop_triggering:
                # Don't want to take pictures right now.
                self.disable_periodic_triggering()
                time.sleep(0.5)
                continue

            # Tell camera how often we want to take pictures.  Do it each time through loop in case MCU doesn't pick up on one command.
            # Convert to an integer in milliseconds because that's what MCU is expecting.
            self.change_trigger_period(int(self.trigger_period * 1000))
            
            # Try to read in any new sensor data.  Set timeout so give camera time to respond, but can also warn user that no data is coming back.
            self.connection.timeout = self.trigger_period + 2
            newly_read_data = self.connection.read()
            
            if newly_read_data is None or len(newly_read_data) == 0:
                logging.getLogger().warning('No new data received from camera {}. Is it still plugged in?'.format(self.sensor_name))
                continue
            
            logging.getLogger().debug('Camera {} read in {} bytes'.format(self.sensor_name, len(newly_read_data)))
            #logging.getLogger().debug(newly_read_data)
            
            # Try to parse image filenames and relative time stamps out of the new data.
            messages = self.parse_new_data(newly_read_data)
            new_images = self.handle_new_messages(messages)

            for (image_utc_time, filename) in new_images:
                self.handle_data((image_utc_time, filename))
        
    def sync_mcu_time(self):
        '''
         Synchronize camera MCU to utc time.  This won't start taking pictures, but will tell the camera MCU
         to report all future image times relative to when it receives this 'sync' command.  
         This is better than have this driver send trigger commands since there's no guarantee this code
         can run at a constant rate since the OS isn't real-time.
         
         Notes: Time source must have a valid non-zero time before calling this method.
        '''
        sync_successful = False
        while not sync_successful:
            # Grab current UTC time so we can use relative MCU times when images come back.
            self.synced_utc_time = self.time_source.time
            sync_successful = self.send_command(self.sync_command, command_description='sync', ack_timeout=1)
            
    def change_trigger_period(self, new_trigger_period):
        '''Change how often camera is taking pictures.  Should be in milliseconds.  Set to zero to stop taking images.'''
        self.send_command('p{}\n'.format(new_trigger_period), 'change trigger period', ack_timeout=0)
        
    def disable_periodic_triggering(self):
        '''Tell MCU to stop triggering camera at specified rate.'''
        self.change_trigger_period(0)
        
    def send_command(self, command, command_description, ack_timeout):
        '''
        Send specified command over connection.  Command description should describe what type of command is being sent. 
        Ack timeout is the serial port read timeout specified in seconds.  If not ack is expected then set timeout argument 
        to zero.  Return true if method is successful.
        '''
        if self.connection is None:
            logging.getLogger().error('Could not send {} command to camera {} due to serial port not being open.'.format(command_description, self.sensor_name))
            return False
        
        self.connection.write(command)
        
        if ack_timeout <= 0:
            return True # don't want to wait for acknowledgment.
        
        # update read timeout on serial port
        self.connection.timeout = ack_timeout
        
        ack_response = self.connection.read()
        
        if ack_response is None or len(ack_response) == 0:
            logging.getLogger().error('Timed out when waiting for acknowledgment from camera {} to {} command.'.format(self.sensor_name, command_description))
            return False # no ack received
        
        if ack_response == self.ack_command:
            return True # received correct ack command
        else:
            logging.getLogger().error('Received \'{}\' from camera {} when waiting for ack command \'{}\'.'.format(ack_response, self.sensor_name, self.ack_commands))
            return False
        
    def parse_new_data(self, data):
        '''Return list of new images where an image is (utc timestamp, filename)''' 
        # Add data onto running list of data that hasn't been used.
        self.input_stream += data
        
        messages = []
        while True:
            new_message = self.extract_message_from_input_stream()
            if new_message is None:
                break # no more message right now
            messages.append(new_message)
        
        return messages
                
    def handle_new_messages(self, messages):
        '''Return list of new images where an image is a (utc_time, filename). Also logs any status messages.'''
        new_images = []
        
        for (message_type, contents) in messages:
        
            if message_type == 'status':
                logging.getLogger().warning('Camera {} reported status {}'.format(self.sensor_name, contents))
            elif message_type == 'dump':
                filename = self.parse_filename(contents)
                if filename is not None and len(filename) > 0:
                    self.last_image_filename = filename
                else:
                    self.failed_image_name_parse_count += 1
                    if self.image_count > 1:
                        # We've already parsed one successful image so we shouldn't have a failure here.
                        logging.getLogger().error('Could not parse filename from camera {} after successfully parsing one.'.format(self.sensor_name))
                    elif self.failed_image_name_parse_count > 3:
                        # Check how many we've failed to parse.  If it's too many than the user problem specified the wrong camera prefix.
                        logging.getLogger().error('Failed to parse filename from camera {} multiple times.  Is specified image prefix {} correct?'.format(self.sensor_name, self.image_filename_prefix))
            elif message_type == 'time':
                try:
                    relative_time = float(contents) / 1000.0 # convert from milliseconds to seconds
                except ValueError:
                    logging.getLogger().error('Camera {} MCU time could not be converted to a float.'.format(self.sensor_name))
                    continue # invalid time
                utc_time = self.synced_utc_time + relative_time  
                new_images.append((utc_time, filename))
                self.image_count += 1

        return new_images
    
    def extract_message_from_input_stream(self):
        '''
        Return first message from input stream where a message is a type (ie time) followed by contents.
        Once a message is parsed, it and anything before it is deleted from input stream.
        '''
        message_start = '<*<'
        message_end = '>*>'
        message_start_index = self.input_stream.find(message_start)
        if message_start_index < 0:
            return None
        message_end_index = self.input_stream.find(message_end)
        if message_end_index < 0:
            return None
        
        message = self.input_stream[message_start_index + len(message_start) : message_end_index]

        type_end_index = message.find('-')
        
        if type_end_index < 0:
            message_type = 'unknown'
        else:
            message_type = message[:type_end_index].lower()
            
        message_contents = message[type_end_index+1:]

        # Clear message from input buffer now that we've extracted it.
        very_end_index = message_end_index + len(message_end)
        self.input_stream = self.input_stream[very_end_index:]

        return (message_type, message_contents)

    def parse_filename(self, rawdata):
        '''Extract filename from raw event dump from camera.'''
        # Find index of filename prefix.
        filename_index = rawdata.find(self.image_filename_prefix)
        
        if filename_index < 0:
            # Couldn't find user's specified prefix so try default prefix.
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