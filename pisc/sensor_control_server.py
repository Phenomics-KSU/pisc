#!/usr/bin/env python

import sys
import socket
import SocketServer
import logging

class SocketHandlerTCP(SocketServer.BaseRequestHandler):
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
        '''Called for each new connection.'''
        
        self.data = '' # data buffer
        
        while True:
            # Block until new data is ready.
            new_data = self.request.recv(1024)

            if not new_data:
                break # connection has been closed
            
            self.data += new_data.strip()

            while True: # Process all complete packets in data buffer.
                start_index = self.data.find('<')
                end_index = self.data.find('>')
                if start_index == -1 or end_index == -1:
                    break # wait for new data so we have a complete packet
    
                # Process the packet
                self.process_packet(self.data[start_index+1:end_index])
                
                # Remove what we just processed and anything before.
                self.data = self.data[end_index+1:]

            #self.request.send(self.data.upper())
        
        logging.getLogger().info('Connection to {0} closed.'.format(self.client_address[0]))
    
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

        if not SocketHandlerTCP.first_message_received:
            SocketHandlerTCP.first_message_received = True
            logging.getLogger().info('Messages being received.')

class TCPServerPass(SocketServer.TCPServer):
    '''Override default error handling of only printing exception trace.'''
    def __init__(self, *args, **kwargs):
        '''Pass all arguments to base class.'''
        SocketServer.TCPServer.__init__(self, *args, **kwargs)
    def handle_error(self, request, client_address):
        '''Called when an exception occurs in handle()'''
        exception_type, value = sys.exc_info()[:2]
        if exception_type is KeyboardInterrupt:
            raise KeyboardInterrupt
        else:
            print 'Exception raised when handling TCP connection:\n{0} - {1}'.format(exception_type, value)

class SensorControlServer:
    
    def __init__(self, sensor_controller, t_source, pos_source, orient_source, host, port):
        # Subclass handler to use passed in sensor controller.  Weird, but I couldn't find a better way to do it.
        class SocketHandlerTCPWithController(SocketHandlerTCP):
                controller = sensor_controller
                time_source = t_source
                position_source = pos_source
                orientation_source = orient_source

        # Create the server at the specified address.
        self.server = TCPServerPass((host, port), SocketHandlerTCPWithController, bind_and_activate=False)
        
    def activate(self):
        '''Run the server until a termination signal is received.'''
        self.server.allow_reuse_address = True # Prevent 'cannot bind to address' errors on restart
        self.server.server_bind()     # Manually bind, to support allow_reuse_address
        self.server.server_activate() # (see above comment)
        self.server.serve_forever()
