'''
The server plugins act as translation layers between the (relatively-)
standardized measurement specifications of the MEM ecosystem, and the specific
structures and data formats of the user-selected instrument communications
software.

Here, the base class BaseServer is provided, which should be inherited from
for the user's custom plugin for specific software.
'''
import logging
from typing import Optional, Mapping

from measurement_event_manager.measurement_params import MeasurementParams

class BaseServer(object):


    def __init__(self, logger):
        self.logger = logger
        ## TODO make the plugin logger a child of the main Controller logger


    ## The following methods must be overridden by subclasses


    def setup(self):
        '''Set up and verify the connections to the required instruments
        '''
        pass


    def preset(self, params):
        '''Set all fixed instrument values before starting the measurement
        '''
        pass


    def measure(self, params):
        '''Execute the measurement based on the passed-in parameters object
        '''
        ## This function is expected to return the full path to the output
        ## file created by the measurement
        return None

