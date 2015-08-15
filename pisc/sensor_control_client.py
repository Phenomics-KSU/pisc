#!/usr/bin/env python

import socket
import time

'''
List of common sensor commands.
stop - stop sensor from collecting data
start - start sensor again
'''

class SensorControlClient:
    '''UDP client that allows time, pose and commands to be sent to sensor controller.
        There is no connect() call since UDP has no connections.'''
    
    def __init__(self, host, port):
        # SOCK_DGRAM is the socket type to use for UDP sockets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (host, port)
        self.synced = False # set to True once host time is synced.
        self.next_sync_id = 0
        self.sync_id_times = {}
    
    def send_time(self, utc_time):
        '''Send UTC time over socket. Preferred option is using time sync method which accounts for latency.'''
        self.sock.sendto("t,{}\n".format(utc_time), self.address)
        
    def send_position(self, time, time_delay, frame, x, y, z, zone=None):
        '''Time is the UTC time reported by the receiver for the corresponding position.  
           Time delay is any additional time (in seconds) that has elapsed before calling this method.
           Frame is the coordinate frame of the XYZ position.  For example LLA (lat-long-alt), UTM, ENU, etc.
           Zone is for frames that are split into zones.  For example in UTM it could be 14S.'''
        self.sock.sendto("p,{},{},{},{},{},{},{}\n".format(time, time_delay, frame, x, y, z, zone), self.address)
        
    def send_orientation(self, time, time_delay, frame, rotation_type, r1, r2, r3, r4=0):
        '''Time is the UTC time reported by the receiver for the corresponding orientation.  
           Time delay is any additional time (in seconds) that has elapsed before calling this method.
           Frame is the coordinate system that the orientation is defined in. For example ENU for east-north-up.
           For Euler Angles the rotation_type is a 4 character string where the 1st letters is either 's' for static
           (extrinsic) rotations or 'r' for relative (intrinsic) rotations.  The following three letters correspond to
           the rotation order.  For example rzyx would be a relative rotation first about z, then y then x. 
           This rotation sequence is commonly referred to as yaw-pitch-roll. r1, r2 and r3 correspond to the rotation values. 
           In the example r1 would be the rotation about z (yaw). All rotations should be in radians.
           For quaternion representation the rotation_type should be 'quat' and r1-r4 correspond to [x, y, z, w]'''
        self.sock.sendto("o,{},{},{},{},{},{},{},{}\n".format(time, time_delay, frame, rotation_type, r1, r2, r3, r4), self.address)
        
    def send_command_by_type(self, sensor_type, command):
        '''Sensor type is the type of sensors to send command to.  For example canon_mcu.
            Command could be anything depending on sensor type. Common commands are list at top of file.'''
        self.sock.sendto("ct,{},{}\n".format(sensor_type, command), self.address)
        
    def send_command_by_name(self, sensor_name, command):
        '''Send command to all sensors with matching name (names aren't unique)'''
        self.sock.sendto("cn,{},{}\n".format(sensor_name, command), self.address)
        
    def send_command_by_id(self, sensor_id, command):
        '''Send command to sensor with matching ID. All ID's are unique for a given run.'''
        self.sock.sendto("ci,{},{}\n".format(sensor_id, command), self.address)
                    
    def send_time_sync(self, utc_time):
        '''
        More robust way of making sure that the UTC time the sensor control uses is accurate.
        To use this method effectively the sensor controller should be setup with the RelativePreciseTimeSource.
        This method uses the following steps to estimate the latency between the client and server.
        
        This method should be called for each new UTC time until it reports success (returns true). 
        
        Client: Records system time and id number
        Client: Sends UTC time (with processing delay added in) and id number
        Server: Stores UTC time + id number + its system clock
        Server: Acknowledges packet by sending back same ID number.
        Client: Calculates round trip time (RTT) and then sends back same ID and RTT value.
        Server: Cuts RTT value in half to estimate latency and adds it to the original UTC time it stored with the ID and system clock.
        Server: Checks if it has at least 10 messages.   If it does then adds checks if they're all consistent.  If they are then sends back 'true'. 
        
        This method returns true if sensor control is successfully synced.  After that orientation and position messages can start being sent.
        '''
        sync_id = self.next_sync_id
        self.sock.settimeout(1.0)
        self.sock.sendto("sync1,{},{}".format(sync_id, utc_time), self.address)
        self.sync_id_times[sync_id] = time.time()

        data, address = self.sock.recvfrom(1024)

        returned_sync_id = int(data)
        returned_sync_time = time.time()
        sent_sync_time = self.sync_id_times[returned_sync_id]
        elapsed_time = returned_sync_time - sent_sync_time
        
        self.sock.sendto("sync2,{},{}".format(sync_id, elapsed_time), self.address)
        
        data, address = self.sock.recvfrom(1024)
        if data == 'true':
            self.synced = True
            
        self.sock.settimeout(None)
        self.next_sync_id += 1
        
        return self.synced

        