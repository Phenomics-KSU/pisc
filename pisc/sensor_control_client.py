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
        self.sock.sendall("<t,{0}>".format(time))
        
    def send_time_and_position(self, time, x, y, z):
        '''Send both time and position at same time.'''
        self.sock.sendall("<tp,{0},{1},{2},{3}>".format(time, x, y, z))
        
    def send_time_position_and_orientation(self, time, x, y, z, angle1, angle2, angle3):
        '''Send time, position and orientation at same time.'''
        self.sock.sendall("<tpo,{0},{1},{2},{3},{4},{5},{6}>".format(time, x, y, z, angle1, angle2, angle3))
        
    def send_command_by_type(self, sensor_type, command):
        '''Send command to all sensors of specified type.'''
        self.sock.sendall("<ct,{0},{1}>".format(sensor_type, command))
        
    def send_command_by_name(self, sensor_name, command):
        '''Send command to all sensors with matching name (names aren't unique)'''
        self.sock.sendall("<cn,{0},{1}>".format(sensor_name, command))
        
    def send_command_by_id(self, sensor_id, command):
        '''Send command to sensor with matching ID. All ID's are unique.'''
        self.sock.sendall("<ci,{0},{1}>".format(sensor_id, command))
        
