#!/usr/bin/env python

import socket
from sensor_control_server import SensorControlServer
from sensor_controller import SensorController

if __name__ == "__main__":
    
    sensor_controller = SensorController()

    host = socket.gethostname()
    port = 5000

    print 'Server listening on {0}:{1}'.format(host, port)
    server = SensorControlServer(sensor_controller, host, port)

    # This will keep running until you the program is interrupted with Ctrl-C
    server.activate()
    
    print 'Server shutting down...'
    