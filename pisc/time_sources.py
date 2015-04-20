#!/usr/bin/env python

class SimpleTimeSource:
    def __init__(self, default_time = 0):
        self.time = default_time
        
    def set_time(self, new_time):
        self.time = new_time
        
    def get_time(self):
        return self.time
        
