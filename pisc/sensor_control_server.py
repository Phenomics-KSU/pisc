#!/usr/bin/env python

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
    
    # Used to notify user that messages are being received.
    first_message_received = False
    
    def handle(self):
        '''Parse packet and pass data to its corresponding object.'''
        data = self.request[0].strip()
        #socket = self.request[1]
        
        fields = data.split(',')
        
        packet_type = fields[0]
        
        if packet_type == 't':
            time = float(fields[1])
            self.time_source.time = time
        if packet_type == 'p':
            x = float(fields[1])
            y = float(fields[2])
            z = float(fields[3])
            self.position_source.position = (x, y, z)
        if packet_type == 'tp':
            time = float(fields[1])
            x = float(fields[2])
            y = float(fields[3])
            z = float(fields[4])
            self.time_source.time = time
            self.position_source.position = (x, y, z)

        if not SocketHandlerUDP.first_message_received:
            SocketHandlerUDP.first_message_received = True
            logging.getLogger().info('Messages being received.')

        #socket.sendto(data.upper(), self.client_address)
        
class SensorControlServer:
    
    def __init__(self, sensor_controller, t_source, pos_source, host, port):

        # Subclass handler to use passed in sensor controller.  Weird, but I couldn't find a better way to do it.
        class SocketHandlerUDPWithController(SocketHandlerUDP):
                controller = sensor_controller
                time_source = t_source
                position_source = pos_source
        
        # Create the server at the specified address.
        self.server = SocketServer.UDPServer((host, port), SocketHandlerUDPWithController)
        
    def activate(self):
        '''Run the server until a termination signal is received.'''
        self.server.serve_forever()