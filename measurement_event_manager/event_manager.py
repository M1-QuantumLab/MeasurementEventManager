'''
The main MeasurementEventManager class.
'''

## Python 3+ introduced the abc submodule in collections
try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable
import os
import subprocess

from measurement_event_manager import queue
from measurement_event_manager.util.errors import QueueEmptyError


###############################################################################
## Defaults and definitions
###############################################################################


GUIDE_PROTOCOL = "MEM-GR/0.1"
GUIDE_TIMEOUT = 2500 # in ms
MEAS_PROTOCOL = 'MEM-MS/0.1'


###############################################################################
## Main MEM class
###############################################################################


class EventManager(object):
    

    ## Setup and initialization
    ###########################


    def __init__(self,
        logger,
        controller_endpoint,
        instrument_config,
        fetch_counter=0,
        ):

        ## Assign logger
        self.logger = logger
        ## Create queue for measurements
        self.queue = queue.Queue()

        ## Measurement queue fetch counter
        self._fetch_counter = None
        self.set_fetch_counter(fetch_counter)

        ## Active measurement
        self._current_measurement = None

        ## Declare variables for later
        self._instrument_config = instrument_config
        self._meas_request_endpoint = controller_endpoint


    ## Config and instrument setup
    ##############################


    def get_config(self):
        '''Return the instrument config specified at launch
        '''
        return self._instrument_config


    ## Measurement status
    #####################


    def is_measurement_running(self):
        if self._current_measurement:
            return True
        else:
            return False


    def new_measurement_trigger(self, disable_launch=False):
        '''Start a new measurement if allowed and/or possible
        '''

        ## If there is already a measurement running, we cannot start a new one
        if self.is_measurement_running():
            self.logger.debug('A measurement is currently in progress')
            return False
        ## If the fetch counter is at 0, we cannot attempt to start a new
        ## measurement
        elif self._fetch_counter == 0:
            self.logger.info('Fetch counter is at 0; skipping fetch and'
                             ' waiting for increase')
            return False

        ## We are allowed to fetch a new measurement
        self.logger.debug('Attempting to fetch measurement from queue...')
        try:
            next_measurement = self.queue.pop_next()
        except QueueEmptyError:
            self.logger.warning('Queue is empty; cannot fetch measurement')
            ## Return without incrementing the fetch counter
            return False

        ## We successfully have a new measurement from the queue to run
        ## Pre-processing admin
        self._decrement_fetch_counter()
        self._current_measurement = next_measurement

        ## Actual subprocess launch can be disabled for debugging
        if disable_launch:
            self.logger.warning('Launch disabled; measurement thread is '
                                'expected to be started manually.')
        else:
            self.logger.info('Launching measurement...')
            ## Identify the OS as creating a detached process is handled
            ## differently
            ## Windows
            if os.name == 'nt':
                flags = 0
                flags |= 0x00000008  # DETACHED_PROCESS
                flags |= 0x00000200  # CREATE_NEW_PROCESS_GROUP
                # flags |= 0x08000000  # CREATE_NO_WINDOW
                proc = subprocess.Popen(['mem_launch_measurement',
                                        self._meas_request_endpoint],
                                        close_fds=True,
                                        creationflags=flags,
                                        )

            ## Unix-like
            elif os.name == 'posix':
                proc = subprocess.Popen(['nohup', 'mem_launch_measurement',
                                        self._meas_request_endpoint],
                                        preexec_fn=os.setpgrp,
                                    )

        return True


    def get_current_measurement(self):
        return self._current_measurement
    

    def get_current_measurement_json(self):
        return self.get_current_measurement().to_json()


    def clear_current_measurement(self):
        self.logger.debug('Clearing current measurement')
        self._current_measurement = None


    def measurement_finished(self, received_message):
        '''Cleanup and publishing of a finished measurement

        Takes in serialized measurement data and pipes it to the publishing
        socket.
        '''
        self.logger.info('Measurement completed; broadcasting to listeners...')
        ## Clear the current measurement attribute
        self.clear_current_measurement()
        ## Publish the serialized measurement data
        measurement_json = received_message[0]
        # self.publish_measurement(measurement_json)


    def publish_measurement(self, measurement_json):
        '''Publish serialized measurement data to the listener pub socket
        '''
        raise NotImplementedError


    def fetch_counter(self, set_counter=None):
        '''Set the number of measurements to be fetched before pausing
        '''
        if set_counter is not None:
            self._fetch_counter = int(set_counter)
        ## If set_counter is None, treat it as a query and return the value
        ## without modification
        return self._fetch_counter


    def get_fetch_counter(self):
        '''Get the number of measurements to be fetched before pausing
        '''
        return self._fetch_counter


    def set_fetch_counter(self, new_counter):
        '''Set the number of measurements to be fetched before pausing
        '''
        counter_input = int(new_counter)
        ## If the new value is < -1, we use -1 for consistency
        if counter_input <= -1:
            self._fetch_counter = -1
        else:
            self._fetch_counter = counter_input
        return self._fetch_counter


    def _decrement_fetch_counter(self):
        '''If the fetch counter is positive, decrement it by 1
        '''
        ## In principle we could just always decrement it, as any negative
        ## value would count as infinite, but we might as well be a bit more
        ## specific to avoid weird behaviour
        if self._fetch_counter >= 0:
            self._fetch_counter -= 1
            self.logger.info('Fetch counter decremented to '
                             '{}'.format(self._fetch_counter))
        else:
            self.logger.debug('Counter set for infinite fetch; not modified.')


    ## Queue handling
    #################


    def add_to_queue(self, measurement_or_iterable):
        '''Add a single measurement or an iterable of measurements to the queue
        '''
        if isinstance(measurement_or_iterable, Iterable):
            new_indices = []
            for meas_item in measurement_or_iterable:
                added_index = self.queue.add(meas_item)
                new_indices.append(added_index)
            return new_indices
        else:
            new_index = self.queue.add(meas_item)
            return new_index


    def remove_from_queue(self, index_list):
        removed_indices = self.queue.remove(index_list)
        return removed_indices


    def get_queue_elements(self):
        return self.queue.info()


    def get_queue_length(self):
        return len(self.queue)

