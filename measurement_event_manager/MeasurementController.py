'''
Control a single measurement at a time
Delegated to by the MeasurementEventManager
'''

## future imports must be at the top
from __future__ import print_function

import multiprocessing
import time

import zmq


###############################################################################
## Definitions and setup
###############################################################################

## ZMQ constants
MEAS_PROTOCOL = 'MEM-MS/0.1'


###############################################################################
## Measurement function wrapper
###############################################################################


def measurement_wrapper():
    '''Wrapper for the actual measurement function
    '''
    time.sleep(10)
    return True


###############################################################################
## MeasurementController class
###############################################################################


class MeasurementController(object):
    '''Wrapper to handle measurement control/administration. 
    
    Communicates status with main MeasurementEventManager process through ZMQ.
    '''

    def __init__(self, socket_endpoint, measurement_args=[]):
        self.running = False
        self.socket_endpoint = socket_endpoint
        ## Set up the ZMQ context
        self.context = zmq.Context()
        ## Connect to the endpoint
        self.connect_socket()
        ## Run the measurement
        self.run_measurement()
        ## Close?


    def connect_socket(self):
        self.meas_socket = self.context.socket(zmq.REQ)
        self.meas_socket.connect(self.socket_endpoint)


    ## Main measurement function
    ############################

    def run_measurement(self, measurement_args=[]):
        
        ## Check if a measurement is already running; only 1 measurement
        ## is allowed at a time!
        if self.running:
            return False

        ## Do measurement setup & preprocessing here...

        ## Measurement can officially start
        self.running = True
        ## Send measurement start confirmation
        print('Sending measurement start confirmation...')
        self.meas_socket.send_multipart([MEAS_PROTOCOL.encode(), b'START'])
        ## Receive acknowledgement
        print('Awaiting acknowledgement...')
        response = self.meas_socket.recv_multipart()
        
        ## Run the actual measurement
        print('Starting measurement wrapper...')
        
        measurement_wrapper()

        print('Measurement wrapper start completed.')

        ## Send measurement completion confirmation
        self.meas_socket.send_multipart([MEAS_PROTOCOL.encode(), b'END'])
        ## TODO add the measurement metadata that we want to transmit to the
        ## events listener (output file names etc.) in the end confirmation 
        ## message
        ## Receive acknowledgement
        response = self.meas_socket.recv_multipart()

        ## End gracefully
        self.running = False
        return True
