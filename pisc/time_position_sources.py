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
    Base all future times off the first time.  Protects against negative time durations between sensor readings.
    '''
    @property
    def time(self):
        '''Return parent's time property'''
        return super(RelativePreciseTimeSource, self).time
    
    @time.setter
    def time(self, new_time):
        '''Set new time only if hasn't been set yet. Thread-safe.'''
        if self._time == self._default_time:
            with self.lock:
                self.last_set_time = time.time()
                self._time = new_time

    def set_time_with_ref(self, new_time, ref_time):
        '''Set new time only if hasn't been set yet. Allows a reference time (ref_time) which 
           comes from calling time.time() to be specified which then the elapsed time since 
           ref_time is taken into account once the lock is acquired.  Thread-safe.'''
        if self._time == self._default_time:
            with self.lock:
                self.last_set_time = time.time()
                self._time = new_time + (time.time() - ref_time)

class SimplePositionSource(object):
    '''
    Wrapper for a position tuple (time, frame, (x,y,z), zone) that allows sensors/handlers thread-safe access to most recent position.
    '''
    def __init__(self, default_position = (0, 'None', (0, 0, 0), 'None')):
        '''Constructor'''
        self._position = default_position
        # Using a lock to be safe even though simple access/assignment should be atomic.
        self.lock = threading.Lock()
        # Use an event to notify any interested threads when a new position arrives.
        self.event = threading.Event()
            
    def wait(self, timeout=None):
        '''Return when either timeout occurs or new data is ready. A timeout of None is the same as infinity. 
           The event.wait() method should return true if new data is ready, but due to a race condition some
           times it returns false since the event flag is cleared.   The caller of this should check if the
           utc_time of the new position has changed to determine if there really is new data.'''
        self.event.wait(timeout)
            
    @property
    def position(self):
        '''Return position (time, frame, (x,y,z), zone) as tuple. Thread-safe.'''
        with self.lock:
            current_position = self._position
        return current_position

    @position.setter
    def position(self, new_position):
        '''Set new position. Thread-safe.'''
        with self.lock:
            self._position = new_position
            # reset event to wake up waiting threads
            self.event.clear()
            self.event.set()

class SimpleOrientationSource(object):
    '''
    Wrapper for a orientation tuple (time, frame, rotation_type, (r1, r2, r3. r4)) that allows sensors/handlers thread-safe access to most recent orientation.
    '''
    def __init__(self, default_orientation = (0, 'None', 'None', (0, 0, 0, 0))):
        '''Constructor'''
        self._orientation = default_orientation
        # Using a lock to be safe even though simple access/assignment should be atomic.
        self.lock = threading.Lock()
        # Use an event to notify any interested threads when a new orientation arrives.
        self.event = threading.Event()
            
    def wait(self, timeout=None):
        '''Return when either timeout occurs or new data is ready. A timeout of None is the same as infinity. 
            The event.wait() method should return true if new data is ready, but due to a race condition some
            times it returns false since the event flag is cleared.   The caller of this should check if the
            utc_time of the new position has changed to determine if there really is new data.'''
        self.event.wait(timeout)
            
    @property
    def orientation(self):
        '''Return orientation (time, frame, rotation_type, (r1, r2, r3. r4)) as tuple. Thread-safe.'''
        with self.lock:
            current_orientation = self._orientation
        return current_orientation

    @orientation.setter
    def orientation(self, new_orientation):
        '''Set new orientation. Thread-safe.'''
        with self.lock:
            self._orientation = new_orientation
            # reset event to wake up an waiting threads
            self.event.set()
            self.event.clear()

