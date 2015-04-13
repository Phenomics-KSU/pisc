#!/usr/bin/env python

import socket
from sensor_control_client import SensorControlClient
from time import sleep

if __name__ == "__main__":
    
    host = socket.gethostname()
    port = 5000
    
    print 'Trying to connect to server at {0}:{1}'.format(host, port)
    
    # TODO: Support multiple clients read in from config file
    client = SensorControlClient(host, port)

    for i in range(1, 10):
        
        client.send_time(i)
        sleep(.05)
        client.send_position(i, i+1, i+2)
        sleep(.05)

    print 'Shutting client down...'

    