'''
Control a single measurement at a time
Delegated to by the MeasurementEventManager
'''

import logging

import zmq

from measurement_event_manager.util import log as mem_logging
from measurement_event_manager.interfaces.controller import (
    ControllerRequestInterface,
)
from measurement_event_manager.server_plugins.sleeper import (
    SleeperServer,
)


###############################################################################
## Definitions and setup
###############################################################################

## ZMQ constants
MEAS_PROTOCOL = 'MEM-MS/0.1'


###############################################################################
## MeasurementController class
###############################################################################


class Controller(object):
    '''Wrapper to handle measurement control/administration. 
    
    Communicates status with main MeasurementEventManager process through ZMQ.
    '''

    def __init__(self,
        endpoint,
        server_plugin='sleeper',
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

        ## MEM ecosystem ##

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
        
        ## Initialize the interface to the EventManager
        self._interface = ControllerRequestInterface(
                                    socket=ctrl_request_socket,
                                    protocol_name='MEM-MC/0.1',
                                    logger=self.logger,
                                    )

        ## Instrument server plugin ##

        ## Load instrument server plugin
        if server_plugin == 'sleeper':
            self._server = SleeperServer(logger=self.logger)
        ## TODO make this dynamic, allowing the user to point to their own
        ## files and server plugin definitions

        ## Misc ##

        ## Current measurement params - initialize empty
        ## The params will be populated when provided by the EventManager in
        ## response to the appropriate request
        self._measurement_params = None


    ## Communications with MEM
    ##########################


    def get_measurement_params(self):
        '''Request measurement parameters from the parent EventManager
        '''

        ## Request new parameters from the EventManager
        new_params = self._interface.next()
        self.logger.info('New measurement params received from EventManager')
        self._measurement_params = new_params


    def confirm_start(self):
        '''Confirm starting the measurement with the EventManager
        '''
        self._interface.start()


    def confirm_end(self):
        '''Confirm the end of the current measurement with the EventManager
        '''
        self._interface.end(self._measurement_params)


    ## Instrument connections
    #########################


    def server_setup(self):
        '''Initialize instrument connections etc. before running measurement
        '''
        self.logger.debug('Carrying out server setup...')
        self._server.setup()
        self.logger.info('Server setup completed.')


    ## Measurement execution
    ########################


    def run_measurement(self):
        '''Run the measurement described by the current parameter set
        '''

        ## Preset fixed instrument values
        self.logger.info('Presetting instrument values...')
        self._server.preset(self._measurement_params)

        ## Send measurement start confirmation
        self.logger.debug('Sending measurement start confirmation...')
        self.confirm_start()

        ## Run the actual measurement
        self.logger.info('Starting measurement...')
        self._measurement_params.set_start_time()

        ## Launch the measurement function
        self._server.measure(self._measurement_params)
        ## TODO handle crashes related to the underlying measurement software
        self._measurement_params.set_end_time()
        ## TODO add the measurement metadata that we want to transmit to the
        ## events listener (output file names etc.) to the MeasurementParams
        ## object

        ## Measurement completion confirmation
        self.logger.debug('Measurement completed.')
        self.confirm_end()

        ## End gracefully
        return True
