#!/usr/bin/env python

import socket
import SocketServer

class SocketHandlerUDP(SocketServer.BaseRequestHandler):
    ''' The RequestHandler class for our server. '''
    
    # Class attribute.  Needs to be overriden in subclass.
    controller = None
    
    def handle(self):
        data = self.request[0].strip()
        #socket = self.request[1]
        if self.controller is None:
            print 'handler subclass not created correctly' 
            return;
        
        fields = data.split(',')
        
        packet_type = fields[0]
        
        if packet_type == 't':
            time = fields[1]
            self.controller.set_time(time)
        if packet_type == 'p':
            x = fields[1]
            y = fields[2]
            z = fields[3]
            self.controller.set_position(x, y, z)

        #socket.sendto(data.upper(), self.client_address)
        
class SensorControlServer:
    
    def __init__(self, sensor_controller, host, port):

        # Subclass handler to use passed in sensor controller.  Weird, but I couldn't find a better way to do it.
        class SocketHandlerUDPWithController(SocketHandlerUDP):
                controller = sensor_controller
        
        # Create the server at the specified address.
        self.server = SocketServer.UDPServer((host, port), SocketHandlerUDPWithController)
        
    def activate(self):
            self.server.serve_forever()