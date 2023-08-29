'''
Control a single measurement at a time
Delegated to by the MeasurementEventManager
'''

import logging
import time

import zmq

from measurement_event_manager import MeasurementParams
import measurement_event_manager.util.logger as mem_logging


###############################################################################
## Definitions and setup
###############################################################################

## ZMQ constants
MEAS_PROTOCOL = 'MEM-MS/0.1'


###############################################################################
## Measurement function wrapper
###############################################################################


def measurement_wrapper(measurement_params, logger):
    '''Wrapper for the actual measurement function
    '''
    for ii in range(10):
        time.sleep(1)
        logger.debug('Measurement tick {}'.format(ii))
    return True


###############################################################################
## MeasurementController class
###############################################################################


class MeasurementController(object):
    '''Wrapper to handle measurement control/administration. 
    
    Communicates status with main MeasurementEventManager process through ZMQ.
    '''

    def __init__(self, socket_endpoint):
        
        self.measurement_params = None
        
        ## Initialize logging
        logger = logging.getLogger('MeasurementController')
        ## TODO have some information in the log file name about the
        ## measurement itself, so we can quickly identify it
        self.logger = mem_logging.quick_config(logger,
                                               console_log_level=None,
                                               file_log_level=logging.DEBUG,
                                               )
        self.logger.debug('Logging initialized.')

        self.socket_endpoint = socket_endpoint
        ## Set up the ZMQ context
        self.context = zmq.Context()
        ## Connect to the endpoint
        self.connect_socket()

        ## Request measurement params from the parent MEM
        self.request_measurement_params()
        ## Run the measurement using the supplied params
        self.run_measurement()


    def connect_socket(self):
        self.meas_socket = self.context.socket(zmq.REQ)
        self.meas_socket.connect(self.socket_endpoint)
        self.logger.debug('Connected to socket at {}'.format(
                                                        self.socket_endpoint))


    ## Communications with MEM
    ##########################


    def request_measurement_params(self):
        '''Request measurement parameters from the parent MEM
        '''

        ## Send request
        self.logger.info('Requesting measurement parameters from MEM')
        self.meas_socket.send_multipart([MEAS_PROTOCOL.encode(),
                                         b'REQ',])
        self.logger.debug('Request sent.')
        
        ## Receive reply
        try:
            reply = self.meas_socket.recv_multipart()
        except zmq.error.Again:
            self.logger.error('Could not receive measurement parameters from MEM.')
            self.meas_socket.close()
        self.logger.debug('Reply received:')
        self.logger.debug(reply)

        ## Parse reply
        ## The protocol doesn't really give us any information
        reply_header = reply[1]
        reply_content = reply[2]
        ## Make sure the header is right; we can build in some error handling
        ## at some point
        if reply_header == 'REQ':
            self.measurement_params = MeasurementParams.from_json(
                                                                reply_content)
            self.logger.info('Measurement params processed.')


    ## Main measurement function
    ############################

    def run_measurement(self):

        ## Ensure that measurement parameters are present
        if not self.measurement_params:
            self.logger.error('No measurement params are present.')
            return False

        ## Send measurement start confirmation
        self.logger.debug('Sending measurement start confirmation...')
        self.meas_socket.send_multipart([MEAS_PROTOCOL.encode(), b'START'])
        ## Receive acknowledgement
        self.logger.debug('Awaiting acknowledgement...')
        response = self.meas_socket.recv_multipart()
        
        ## Run the actual measurement
        self.logger.debug('Starting measurement wrapper...')
        
        measurement_wrapper(self.measurement_params, self.logger)

        self.logger.debug('Measurement wrapper start completed.')

        ## Send measurement completion confirmation
        self.meas_socket.send_multipart([MEAS_PROTOCOL.encode(), b'END'])
        ## TODO add the measurement metadata that we want to transmit to the
        ## events listener (output file names etc.) in the end confirmation 
        ## message
        ## Receive acknowledgement
        response = self.meas_socket.recv_multipart()

        ## End gracefully
        return True
