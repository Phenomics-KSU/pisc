#!/usr/bin/env python

import socket

class SensorControlClient:
    '''Basic UDP client that allows client to send time, position and commands to sensors.
    
        There is no connect() call since UDP has no connections.'''
    
    def __init__(self, host, port):
        # SOCK_DGRAM is the socket type to use for UDP sockets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (host, port)
    
    def send_time(self, time):
        '''Send time over socket.'''
        self.sock.sendto("t,{0}\n".format(time), self.address)
        
    def send_position(self, x, y, z):
        '''Send 3D position over socket.'''
        self.sock.sendto("p,{0},{1},{2}\n".format(x, y, z), self.address)
        
    def send_time_and_position(self, time, x, y, z):
        '''Send both time and position at same time.'''
        self.sock.sendto("tp,{0},{1},{2},{3}\n".format(time, x, y, z), self.address)
        
    def send_command_by_type(self, sensor_type, command):
        '''Send command to all sensors of specified type.'''
        self.sock.sendto("ct,{0},{1}\n".format(sensor_type, command), self.address)
        
    def send_command_by_name(self, sensor_name, command):
        '''Send command to all sensors with matching name (names aren't unique)'''
        self.sock.sendto("cn,{0},{1}\n".format(sensor_name, command), self.address)
        
    def send_command_by_id(self, sensor_id, command):
        '''Send command to sensor with matching ID. All ID's are unique.'''
        self.sock.sendto("ci,{0},{1}\n".format(sensor_id, command), self.address)
        
