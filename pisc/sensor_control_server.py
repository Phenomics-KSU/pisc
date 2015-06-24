#!/usr/bin/env python

import sys
import socket
import SocketServer
import logging

class SocketHandlerUDP(SocketServer.BaseRequestHandler):
    ''' The RequestHandler class for our server. '''
    
    # Class attributes. Subclass needs to override.
    # This class is responsible for giving data to the time/position sources.
    controller = None
    time_source = None
    position_source = None
    orientation_source = None
    
    # Used to notify user that messages are being received.
    first_message_received = False
    
    def handle(self):
        '''Process packet and pass data to its corresponding object.'''
        packet = self.request[0].strip()
        #socket = self.request[1]
        
        self.process_packet(packet)

    def process_packet(self, data):
        '''Parse packet and pass data to its corresponding object.'''
        fields = data.split(',')
        packet_type = fields[0]
        
        if packet_type == 't':
            time = float(fields[1])
            self.time_source.time = time
        elif packet_type == 'p':
            time = float(fields[1])
            frame = fields[2]
            x = float(fields[3])
            y = float(fields[4])
            z = float(fields[5])
            zone = fields[6]
            self.time_source.time = time
            # Store reported time for position since that was the exact time it was measured.
            self.position_source.position = (time, frame, (x, y, z), zone)
        elif packet_type == 'o':
            time = float(fields[1])
            frame = fields[2]
            rotation_type = fields[3]
            try:
                r1 = float(fields[4])
                r2 = float(fields[5])
                r3 = float(fields[6])
                r4 = float(fields[7])
            except ValueError:
                pass # Not all rotations have to be valid depending on rotation type.
 
            self.time_source.time = time
            # Store reported time for orientation since that was the exact time it was measured.
            self.orientation_source.orientation = (time, frame, rotation_type, (r1, r2, r3, r4))
        else:
            logging.getLogger().warning('Unhandled packet of type {0}'.format(packet_type))

        if not SocketHandlerUDP.first_message_received:
            SocketHandlerUDP.first_message_received = True
            logging.getLogger().info('Messages being received.')

class UDPServerPass(SocketServer.UDPServer):
    '''Override default error handling of only printing exception trace.'''
    def __init__(self, *args, **kwargs):
        '''Pass all arguments to base class.'''
        SocketServer.UDPServer.__init__(self, *args, **kwargs)
    def handle_error(self, request, client_address):
        '''Called when an exception occurs in handle()'''
        exception_type, value = sys.exc_info()[:2]
        if exception_type is KeyboardInterrupt:
            raise KeyboardInterrupt
        else:
            print 'Exception raised when handling UDP packet:\n{0} - {1}'.format(exception_type, value)

class SensorControlServer:
    
    def __init__(self, sensor_controller, t_source, pos_source, orient_source, host, port):
        # Subclass handler to use passed in sensor controller.  Weird, but I couldn't find a better way to do it.
        class SocketHandlerUDPWithController(SocketHandlerUDP):
                controller = sensor_controller
                time_source = t_source
                position_source = pos_source
                orientation_source = orient_source

        # Create the server at the specified address.
        self.server = UDPServerPass((host, port), SocketHandlerUDPWithController, bind_and_activate=False)
        
    def activate(self):
        '''Run the server until a termination signal is received.'''
        self.server.allow_reuse_address = True # Prevent 'cannot bind to address' errors on restart
        self.server.server_bind()     # Manually bind, to support allow_reuse_address
        self.server.server_activate() # (see above comment)
        self.server.serve_forever()
