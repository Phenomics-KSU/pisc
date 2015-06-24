#!/usr/bin/env python

import socket
import threading
from Queue import Queue

class SensorControlClient(threading.Thread):
    
    def __init__(self, client_socket):
        ''' Constructor. '''
        threading.Thread.__init__(self)
        
        self.client_socket = client_socket
        
        self.queue = Queue()
        
        self.waiting_to_start # If true then waiting for start signal from server.
 
    def run(self):
        
        self.__connect()
        
        while True:
            
            if self.waiting_to_start:
                try:
                    self.client_socket.send('?')
                except socket.error:
                    print 'Socket error: client could not send data.'
                    self.__connect()
            
            data = self.queue.get(block=True, timeout=None)
            
            try:
                self.client_socket.send(data)
            except socket.error:
                print 'Socket error: client could not send data.'
                self.__connect()
                    
    def __connect(self):
        
        self.waiting_to_start = True
        
        print 'Connecting to server at ' + self.client_socket.address
        try:
            self.client_socket.connect()
        except socket.error, e:
            print 'Error connecting to server: {}'.format(e)
            
    def send_time(self, time):
        '''Send time over socket.'''
        self.queue.put("<t,{}>".format(time))
        
    def send_position(self, time, frame, x, y, z, zone=None):
        '''Send time and position in the specified frame.'''
        self.queue.put("<p,{},{},{},{},{},{}>".format(time, frame, x, y, z, zone))
        
    def send_orientation(self, time, frame, rotation_type, r1, r2, r3, r4=0):
        '''Send time and orientation in the specified frame.'''
        self.queue.put("<o,{},{},{},{},{},{},{}>".format(time, frame, rotation_type, r1, r2, r3, r4))
        
    def send_command_by_type(self, sensor_type, command):
        '''Send command to all sensors of specified type.'''
        self.queue.put("<ct,{},{}>".format(sensor_type, command))
        
    def send_command_by_name(self, sensor_name, command):
        '''Send command to all sensors with matching name (names aren't unique)'''
        self.queue.put("<cn,{},{}>".format(sensor_name, command))
        
    def send_command_by_id(self, sensor_id, command):
        '''Send command to sensor with matching ID. All ID's are unique.'''
        self.queue.put("<ci,{},{}>".format(sensor_id, command))

class TCPClientSocket:
    '''Basic TCP client that allows client to send time, position and commands to sensors.'''
    
    def __init__(self, host, port):
        '''Constructor'''
        self.address = (host, port)
        
    def connect(self):
        '''Connect to server.'''
        #Create new socket (cannot reuse old one)
        # SOCK_STREAM is the socket type to use for TCP sockets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.address)

    def close(self):
        '''Disconnect from server.'''
        if self.sock is not None:
            self.sock.close()
        
    def is_connected(self):
        '''Return true if connected.  Check by trying to send data over connection.'''
        try:
            self.sock.send('?')
            return True
        except (AttributeError, socket.error):
            return False
    
    def sendall(self, data):
        self.sock.sendall(data)
