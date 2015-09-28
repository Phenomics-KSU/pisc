#!/usr/bin/env python

import sys
import socket
import logging
import time

def mean(l):
    return float(sum(l)) / max(len(l),1)

class GPSClient():
    '''
    UDP client that makes connection with GPS server and then handles new data.
    First call connect() and then start().
    '''
    
    def __init__(self, server_addr, controller, time_source, position_source, orientation_source, sync_time_thresh=0.015):
        '''
        Constructor. Server address is tuple of (host, port).   Sync time thresh (in seconds) sets how close
        the client has to synchronize to the server time before calling it good enough.
        '''
        self.server_address = server_addr 
        self.controller = controller
        self.time_source = time_source
        self.position_source = position_source
        self.orientation_source = orientation_source
        self.sync_time_thresh = sync_time_thresh
    
        # UDP socket used to communicate with server.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Address of handler assigned to give us data. Figured out after connecting.
        self.handler_address = None
    
        # Used to notify user that messages are being received.
        self.first_message_received = False
        
        # Time-stamped sync messages originally received from client.
        self.uncorrected_sync_messages = []
        
        # Sync messages that have been corrected to account for latency.
        self.sync_messages = []
        
        # True if received a sync message, but haven't successfully synced yet.
        self.syncing = False
    
    def connect(self, require_sync):
        '''
        Keep trying to connect to server until it acknowledges that it's there.
        If require_sync is true then will request the server goes through the 
        time sync procedure before sending data. This sync will happen in start().  
        '''
        timeout = 2 # seconds
        connected = False
        
        logging.getLogger().info('Connecting to server at {}'.format(self.server_address))
        
        while not connected:
            connect_command = 'sync' if require_sync else 'add'
            self.sock.sendto(connect_command, self.server_address)
            try:
                self.sock.settimeout(timeout)
                # Make sure server sends some data back as an ack
                data, self.handler_address = self.sock.recvfrom(1024)
                if data != 'ack':
                    continue # wrong ack
            except socket.timeout:
                continue # try again
            except socket.error:
                time.sleep(timeout)
                continue

            connected = True
            
        logging.getLogger().info('Successfully connected.')
        
    def start(self):
        '''
        Infinite loop handling new data from server.  Must call connect() first.
        If connection to the server is lost then it will automatically try to reconnect.  
        '''
        while True:
            try:
                self.sock.settimeout(7)
                data, handler_address = self.sock.recvfrom(1024)
            except (socket.timeout, socket.error):
                logging.getLogger().warn('Connection to GPS server lost. Trying to reconnect.')
                # Don't need to sync since already have valid time reference.
                self.connect(require_sync=False)
                continue
        
            self.process_data(data, handler_address)

    def process_data(self, data, handler_address):
        '''Parse data then handle it if it's valid.'''
        fields = [f.strip() for f in data.split(',') if f.strip()]
        packet_type = fields[0]
        
        if not self.first_message_received:
            self.first_message_received = True
            logging.getLogger().info('Messages being received.')
        
        if packet_type == 't':
            utc_time = float(fields[1])
            time_delay = float(fields[2])
            self.time_source.time = utc_time + time_delay
            
        elif packet_type == 'p':
            utc_time = float(fields[1])
            time_delay = float(fields[2])
            x = float(fields[3])
            y = float(fields[4])
            z = float(fields[5])
            zone = fields[6]
            self.time_source.time = utc_time + time_delay
            # Store reported time for position since that was the exact time it was measured.
            self.position_source.position = (utc_time, (x, y, z), zone)
            
        elif packet_type == 'o':
            utc_time = float(fields[1])
            time_delay = float(fields[2])
            roll = float(fields[3])
            pitch = float(fields[4])
            yaw = float(fields[5])
            self.time_source.time = utc_time + time_delay
            # Store reported time for orientation since that was the exact time it was measured.
            self.orientation_source.orientation = (utc_time, (roll, pitch, yaw))
            
        elif packet_type == 'sync1':
            if not self.syncing:
                self.syncing = True
                logging.getLogger().info('Syncing')
            sync_id = int(fields[1])
            utc_time = float(fields[2])
            system_time = time.time()
            self.uncorrected_sync_messages.append({"id":sync_id, "utc_time":utc_time, "sys_time":system_time})
            # Ack sync message so client can calculate round trip time (RTT)
            self.sock.sendto(str(sync_id), handler_address)
            
        elif packet_type == 'sync2':
            sync_successful = False
            sync_id = int(fields[1])
            rtt = float(fields[2]) # round trip time
            estimated_latency = rtt / 2.0
            matching_messages = [message for message in self.uncorrected_sync_messages if message['id'] == sync_id]
            if len(matching_messages) == 1:
                matching_message = matching_messages[0]
                # Add in latency now that we know it.
                matching_message['utc_time'] += estimated_latency
                matching_message['latency'] = estimated_latency
                self.sync_messages.append(matching_message)
                self.uncorrected_sync_messages.remove(matching_message)

                if len(self.sync_messages) >= 5:
                    current_time = time.time()
                    # Take into account elapsed time since sync messages were received.  These should (hopefully) all be close to the same time now.
                    current_sync_times = [(m['utc_time'] + (current_time - m['sys_time'])) for m in self.sync_messages]
                    
                    avg_time = mean(current_sync_times)
                    #avg_offset = mean([abs(t-avg_time) for t in current_sync_times])
                    max_offset = max([abs(t-avg_time) for t in current_sync_times])

                    sync_successful = max_offset < self.sync_time_thresh
                    
                    if sync_successful:
                        try:
                            self.time_source.set_time_with_ref(avg_time, current_time)
                        except AttributeError:
                            # Fall back on setting time property.
                            self.time_source.time = avg_time
                        # log sync stats
                        latencies = [m['latency'] for m in self.sync_messages]
                        logging.getLogger().info('Success\nLatency {} / {} thresh {} / {}'.format(int(mean(latencies)*1000),
                                                                                                  int(max(latencies)*1000),
                                                                                                  int(max_offset*1000),
                                                                                                  int(self.sync_time_thresh*1000)))
                    else:
                        self.sync_messages = []
                        # Print additional period to show that it's still trying to sync
                        sys.stdout.write('.')
                        sys.stdout.flush()
                        
            self.sock.sendto(str(sync_successful).lower(), handler_address)

        else:
            logging.getLogger().warning('Unhandled packet of type {}'.format(packet_type))
