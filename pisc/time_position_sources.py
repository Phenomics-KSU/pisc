#!/usr/bin/env python

import threading
import time
import logging

class SimpleTimeSource(object):
    '''
    Wrapper for a simple time property that allows sensors/handlers thread-safe access to most recent time.
    '''
    def __init__(self, default_time = 0):
        '''Constructor'''
        self._time = default_time
        # Using a lock to be safe even though simple access/assignment should be atomic.
        self.lock = threading.Lock()

    @property
    def time(self):
        '''Return most recently reported time. Thread-safe.'''
        with self.lock:
            current_time = self._time
        return current_time

    @time.setter
    def time(self, new_time):
        '''Set new time. Thread-safe.'''
        with self.lock:
            self._time = new_time
        
class PreciseTimeSource(object):
    '''
    Allow for elapsed system time to be added into most recently reported time for more precise time measurements.
    '''
    def __init__(self, default_time = 0):
        '''Constructor.  Default time needs to be smaller than first actual time set.'''
        self._time = default_time
        self._default_time = default_time
        self.last_set_time = None
        self.lock = threading.Lock()
        
    @property
    def time(self):
        '''Return most recent time with elapsed system time added in. Thread-safe.'''
        with self.lock:
            current_time = self._time
            if self.last_set_time is not None:
                # We have a valid time reference so calculate the time since the last 'set' call.
                elapsed_time = time.time() - self.last_set_time
                
                # Make sure nothing weird happened, for example the system clock was changed.
                if elapsed_time >= 0:
                    current_time += elapsed_time
                else:
                    logging.getLogger().warning('Negative time elapsed in precise time source {0}.'.format(elapsed_time))

        return current_time
    
    @time.setter
    def time(self, new_time):
        '''Set new time if it's later than the last set time. Thread-safe.'''
        with self.lock:
            if self._time != new_time:
                # Only want to update time reference if we received an actual newer time.
                self.last_set_time = time.time()
                
            self._time = new_time

class RelativePreciseTimeSource(PreciseTimeSource):
    '''
    Base all future times off the first time.  Protects against negative times between sensor readings.
    '''
    @property
    def time(self):
        '''Return parent's time property'''
        return super(RelativePreciseTimeSource, self).time
    
    @time.setter
    def time(self, new_time):
        '''Set new time only if hasn't been set yet. Thread-safe.'''
        with self.lock:
            if self._time == self._default_time:
                self.last_set_time = time.time()
                self._time = new_time

class SimplePositionSource(object):
    '''
    Wrapper for a position tuple (x,y,z) that allows sensors/handlers thread-safe access to most recent position.
    '''
    def __init__(self, default_position = (0, 0, 0)):
        '''Constructor'''
        self._position = default_position
        # Using a lock to be safe even though simple access/assignment should be atomic.
        self.lock = threading.Lock()
        # Use an event to notify any interested threads when a new position arrives.
        self.event = threading.Event()
            
    def wait(self, timeout=None):
        '''Return when a new position reading is available.'''
        self.event.wait(timeout)
            
    @property
    def position(self):
        '''Return position (x,y,z) as tuple. Thread-safe.'''
        with self.lock:
            current_position = self._position
        return current_position

    @position.setter
    def position(self, new_position):
        '''Set new position. Thread-safe.'''
        with self.lock:
            self._position = new_position
            # reset event to wake up an waiting threads
            self.event.set()
            self.event.clear()
