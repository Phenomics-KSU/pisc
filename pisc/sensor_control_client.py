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
        self.sock.sendto("t,{}\n".format(time), self.address)

    def send_position(self, time, time_delay, frame, x, y, z, zone=None):
        '''Send time and position in the specified frame.'''
        self.sock.sendto("p,{},{},{},{},{},{},{}\n".format(time, time_delay, frame, x, y, z, zone), self.address)
        
    def send_orientation(self, time, time_delay, frame, rotation_type, r1, r2, r3, r4=0):
        '''Send time and orientation in the specified frame.'''
        self.sock.sendto("o,{},{},{},{},{},{},{},{}\n".format(time, time_delay, frame, rotation_type, r1, r2, r3, r4), self.address)
        
    def send_command_by_type(self, sensor_type, command):
        '''Send command to all sensors of specified type.'''
        self.sock.sendto("ct,{},{}\n".format(sensor_type, command), self.address)
        
    def send_command_by_name(self, sensor_name, command):
        '''Send command to all sensors with matching name (names aren't unique)'''
        self.sock.sendto("cn,{},{}\n".format(sensor_name, command), self.address)
        
    def send_command_by_id(self, sensor_id, command):
        '''Send command to sensor with matching ID. All ID's are unique.'''
        self.sock.sendto("ci,{},{}\n".format(sensor_id, command), self.address)
        
