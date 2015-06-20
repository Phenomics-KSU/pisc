#!/usr/bin/env python

import socket

class SensorControlClient:
    '''Basic TCP client that allows client to send time, position and commands to sensors.'''
    
    def __init__(self, host, port):
        # SOCK_STREAM is the socket type to use for TCP sockets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = (host, port)
        
    def connect(self):
        '''Connect to server.'''
        self.sock.connect(self.address)
    
    def reconnect(self):
        '''Create new socket (cannot reuse old one) and connect to it.'''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()
    
    def close(self):
        '''Disconnect from server.'''
        self.sock.close()
        
    def is_connected(self):
        '''Return true if connected.  Check by trying to send data over connection.'''
        try:
            self.sock.send('?')
            return True
        except socket.error:
            return False
    
    def send_time(self, time):
        '''Send time over socket.'''
        self.sock.sendall("<t,{}>".format(time))
        
    def send_position(self, time, frame, x, y, z, zone=None):
        '''Send time and position in the specified frame.'''
        self.sock.sendall("<p,{},{},{},{},{},{}>".format(time, frame, x, y, z, zone))
        
    def send_orientation(self, time, frame, rotation_type, r1, r2, r3, r4=0):
        '''Send time and orientation in the specified frame.'''
        self.sock.sendall("<o,{},{},{},{},{},{},{}>".format(time, frame, rotation_type, r1, r2, r3, r4))
        
    def send_command_by_type(self, sensor_type, command):
        '''Send command to all sensors of specified type.'''
        self.sock.sendall("<ct,{},{}>".format(sensor_type, command))
        
    def send_command_by_name(self, sensor_name, command):
        '''Send command to all sensors with matching name (names aren't unique)'''
        self.sock.sendall("<cn,{},{}>".format(sensor_name, command))
        
    def send_command_by_id(self, sensor_id, command):
        '''Send command to sensor with matching ID. All ID's are unique.'''
        self.sock.sendall("<ci,{},{}>".format(sensor_id, command))
        
