'''
Control a single measurement at a time
Delegated to by the MeasurementEventManager
'''

import logging
import time

import zmq

from measurement_event_manager import measurement_params
from measurement_event_manager.util import log as mem_logging
from measurement_event_manager.interfaces.controller import (
    ControllerRequestInterface,
)


###############################################################################
## Definitions and setup
###############################################################################

## ZMQ constants
MEAS_PROTOCOL = 'MEM-MS/0.1'


###############################################################################
## Measurement function wrapper
###############################################################################


def measurement_wrapper(params, logger):
    '''Wrapper for the actual measurement function
    '''
    for ii in range(10):
        time.sleep(1)
        logger.debug('Measurement tick {}'.format(ii))
    return True


###############################################################################
## MeasurementController class
###############################################################################


class Controller(object):
    '''Wrapper to handle measurement control/administration. 
    
    Communicates status with main MeasurementEventManager process through ZMQ.
    '''

    def __init__(self, endpoint,
        logger=None,
        zmq_context=None,
        ):
        
        ## Initialize logging
        if logger is None:
            logger = logging.getLogger(__name__)
            ## TODO have some information in the log file name about the
            ## measurement itself, so we can quickly identify it
            self.logger = mem_logging.quick_config(
                                            logger,
                                            console_log_level=None,
                                            file_log_level=logging.DEBUG,
                                            )
        else:
            self.logger = logger

        ## ZMQ messaging attributes
        self._endpoint = endpoint
        if zmq_context is None:
            self._context = zmq.Context()
        else:
            self._context = zmq_context

        ## Connect to the request socket
        ctrl_request_socket = self._context.socket(zmq.REQ)
        ctrl_request_socket.connect(self._endpoint)
        self.logger.debug('Connected to socket at {}'.format(self._endpoint))
        
        ## Initialize the interface
        self._interface = ControllerRequestInterface(
                                    socket=ctrl_request_socket,
                                    protocol_name='MEM-MC/0.1',
                                    logger=self.logger,
                                    )

        ## At this point, the setup is completed, but because the Controller
        ## lives in a process that the user doesn't interact with, we're not
        ## waiting for user input. 
        ## As such, we just execute all the functions that need to be executed
        ## in order as part of the __init__ call.
        ## If the paradigm changes in the future, for example if the Controller
        ## is kept alive between measurements, then everything below this point
        ## can be structured for on-demand execution rather that being run
        ## automatically.

        ## Measurement parameters and execution
        ## Initialize empty
        ## The params will be populated when provided by the EventManager
        self.measurement_params = None
        ## Request measurement params from the parent MEM
        self.get_measurement_params()
        ## Measurement preprocessing and setup (connecting to instruments etc.)
        self.init_measurement_setup()
        ## Run the measurement using the supplied params
        self.run_measurement()

        ## TODO I think at some point we need to explicitly kill the 
        ## Controller process? Especially if the logger is still open.


    ## Communications with MEM
    ##########################


    def get_measurement_params(self):
        '''Request measurement parameters from the parent EventManager
        '''

        ## Request new parameters from the EventManager
        new_params = self._interface.next()
        self.logger.info('New measurement params received from EventManager')
        self.measurement_params = new_params


    def confirm_start(self):
        '''Confirm starting the measurement with the EventManager
        '''
        self._interface.start()


    def confirm_end(self):
        '''Confirm the end of the current measurement with the EventManager
        '''
        self._interface.end(self.measurement_params)


    ## Measurement initialization
    #############################


    def init_measurement_setup(self):
        '''Initialize instrument connections etc. before running measurement
        '''
        self.logger.debug('Initializing measurement setup...')
        ## TODO
        self.logger.info('Measurement setup initialization completed.')


    ## Main measurement function
    ############################

    def run_measurement(self):
        '''Run the measurement described by the current parameter set
        '''

        ## Send measurement start confirmation
        self.logger.debug('Sending measurement start confirmation...')
        self.confirm_start()

        ## Run the actual measurement
        self.logger.info('Starting measurement...')
        self.measurement_params.set_start_time()

        ## Launch the measurement function
        measurement_wrapper(self.measurement_params, self.logger)
        self.measurement_params.set_end_time()
        ## TODO add the measurement metadata that we want to transmit to the
        ## events listener (output file names etc.) to the MeasurementParams
        ## object

        ## Measurement completion confirmation
        self.logger.debug('Measurement completed.')
        self.confirm_end()

        ## End gracefully
        return True
