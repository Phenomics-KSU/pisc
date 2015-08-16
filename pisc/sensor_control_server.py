#!/usr/bin/env python

import sys
import socket
import SocketServer
import logging
import traceback
import time

def mean(l):
    return float(sum(l)) / max(len(l),1)

class SocketHandlerUDP(SocketServer.BaseRequestHandler):
    ''' The RequestHandler class for our server. '''
    
    # Class attributes. Subclass needs to override.
    # This class is responsible for giving data to the time/position sources.
    controller = None
    time_source = None
    position_source = None
    orientation_source = None
    sync_time_thresh = None
    
    # Used to notify user that messages are being received.
    first_message_received = False
    
    # Time-stamped sync messages originally received from client.
    uncorrected_sync_messages = []
    
    # Sync messages that have been corrected to account for latency.
    sync_messages = []
    
    # True if received a sync message, but haven't successfully synced yet.
    syncing = False
    
    def handle(self):
        '''Process packet and pass data to its corresponding object.'''
        packet = self.request[0].strip()
        socket = self.request[1]
        
        self.process_packet(packet, socket)

    def process_packet(self, data, socket):
        '''Parse packet and pass data to its corresponding object.'''
        fields = data.split(',')
        packet_type = fields[0]
        
        if not SocketHandlerUDP.first_message_received:
            SocketHandlerUDP.first_message_received = True
            logging.getLogger().info('Messages being received.')
        
        if packet_type == 't':
            utc_time = float(fields[1])
            self.time_source.time = utc_time
            
        elif packet_type == 'p':
            utc_time = float(fields[1])
            time_delay = float(fields[2])
            frame = fields[3]
            x = float(fields[4])
            y = float(fields[5])
            z = float(fields[6])
            zone = fields[7]
            self.time_source.time = utc_time + time_delay
            # Store reported time for position since that was the exact time it was measured.
            self.position_source.position = (utc_time, frame, (x, y, z), zone)
            
        elif packet_type == 'o':
            utc_time = float(fields[1])
            time_delay = float(fields[2])
            frame = fields[3]
            rotation_type = fields[4]
            try:
                r1 = float(fields[5])
                r2 = float(fields[6])
                r3 = float(fields[7])
                r4 = float(fields[8])
            except ValueError:
                pass # Not all rotations have to be valid depending on rotation type.
            self.time_source.time = utc_time + time_delay
            # Store reported time for orientation since that was the exact time it was measured.
            self.orientation_source.orientation = (utc_time, frame, rotation_type, (r1, r2, r3, r4))
            
        elif packet_type == 'sync1':
            if not SocketHandlerUDP.syncing:
                SocketHandlerUDP.syncing = True
                logging.getLogger().info('Syncing')
            sync_id = int(fields[1])
            utc_time = float(fields[2])
            system_time = time.time()
            SocketHandlerUDP.uncorrected_sync_messages.append({"id":sync_id, "utc_time":utc_time, "sys_time":system_time})
            # Ack sync message so client can calculate round trip time (RTT)
            socket.sendto(str(sync_id), self.client_address)
            
        elif packet_type == 'sync2':
            sync_successful = False
            sync_id = int(fields[1])
            rtt = float(fields[2]) # round trip time
            estimated_latency = rtt / 2.0
            matching_messages = [message for message in SocketHandlerUDP.uncorrected_sync_messages if message['id'] == sync_id]
            if len(matching_messages) == 1:
                matching_message = matching_messages[0]
                # Add in latency now that we know it.
                matching_message['utc_time'] += estimated_latency
                matching_message['latency'] = estimated_latency
                SocketHandlerUDP.sync_messages.append(matching_message)
                SocketHandlerUDP.uncorrected_sync_messages.remove(matching_message)

                if len(SocketHandlerUDP.sync_messages) >= 5:
                    current_time = time.time()
                    # Take into account elapsed time since sync messages were received.  These should (hopefully) all be close to the same time now.
                    current_sync_times = [(m['utc_time'] + (current_time - m['sys_time'])) for m in SocketHandlerUDP.sync_messages]
                    
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
                        latencies = [m['latency'] for m in SocketHandlerUDP.sync_messages]
                        logging.getLogger().info('Success\nLatency {} / {} thresh {} / {}'.format(int(mean(latencies)*1000),
                                                                                                  int(max(latencies)*1000),
                                                                                                  int(max_offset*1000),
                                                                                                  int(self.sync_time_thresh*1000)))
                    else:
                        SocketHandlerUDP.sync_messages = []
                        # Print additional period to show that it's still trying to sync
                        sys.stdout.write('.')
                        sys.stdout.flush()
                        
            socket.sendto(str(sync_successful).lower(), self.client_address)

        else:
            logging.getLogger().warning('Unhandled packet of type {0}'.format(packet_type))

class UDPServerPass(SocketServer.UDPServer):
    '''Override default error handling of only printing exception trace.'''
    def __init__(self, *args, **kwargs):
        '''Pass all arguments to base class.'''
        SocketServer.UDPServer.__init__(self, *args, **kwargs)
    def handle_error(self, request, client_address):
        '''Called when an exception occurs in handle()'''
        exception_type, value, error_traceback = sys.exc_info()
        if exception_type is KeyboardInterrupt:
            raise KeyboardInterrupt
        else:
            for line in traceback.format_tb(error_traceback):
                print line.strip()
            print 'Exception raised when handling UDP packet:\n{} - {}'.format(exception_type, value)

class SensorControlServer:
    
    def __init__(self, sensor_controller, t_source, pos_source, orient_source, sync_thresh, host, port):
        # Subclass handler to use passed in sensor controller.  Weird, but I couldn't find a better way to do it.
        class SocketHandlerUDPWithController(SocketHandlerUDP):
                controller = sensor_controller
                time_source = t_source
                position_source = pos_source
                orientation_source = orient_source
                sync_time_thresh = sync_thresh

        # Create the server at the specified address.
        self.server = UDPServerPass((host, port), SocketHandlerUDPWithController, bind_and_activate=False)
        
    def activate(self):
        '''Run the server until a termination signal is received.'''
        self.server.allow_reuse_address = True # Prevent 'cannot bind to address' errors on restart
        self.server.server_bind()     # Manually bind, to support allow_reuse_address
        self.server.server_activate() # (see above comment)
        self.server.serve_forever()
