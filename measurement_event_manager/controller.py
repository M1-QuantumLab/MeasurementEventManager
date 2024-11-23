"""
Interfacing between the EventManager and an instrument server application
"""

import os
import logging
from typing import Optional

import yaml
import zmq

from .util import log as mem_logging
from .interfaces.controller import (
    ControllerRequestInterface,
)
from .server_plugins.base import BaseServer
from .server_plugins.sleeper import SleeperServer


###############################################################################
## Definitions and setup
###############################################################################

## ZMQ constants
MEAS_PROTOCOL = 'MEM-MS/0.1'
"""The Controller/measurement messaging protocol identifier
"""


###############################################################################
## MeasurementController class
###############################################################################


class Controller:
    """A bridge between the MEM ecosystem and the instrument server

    A Controller instance represents the launching of a measurement by the
    EventManager, and acts as a communications wrapper around the instrument
    server application.
    The user is not expected to control or communicate with the Controller
    directly.
    """

    def __init__(self,
        endpoint: str,
        server_plugin: Optional[BaseServer] = None,
        logger: Optional[logging.Logger] = None,
        zmq_context: Optional[zmq.Context] = None,
        ):
        """
        Args:
            endpoint: The address to communicate with the EventManager.
            server_plugin: The plugin used to interface with the instrument
                server application.
            logger: A logging object; a default one will be created if it is
                not provided.
            zmq_context: The ZeroMQ messaging context; one will be created if
                it is not provided, although this is not recommended.
        """

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
        if server_plugin is not None:
            self._server = server_plugin
        else:
            self._server = SleeperServer(logger=self.logger)

        ## Misc ##

        ## Current measurement params - initialize empty
        ## The params will be populated when provided by the EventManager in
        ## response to the appropriate request
        self._measurement_params = None


    ## Communications with MEM
    ##########################


    def get_measurement_params(self) -> None:
        """Request measurement parameters from the parent EventManager
        """

        ## Request new parameters from the EventManager
        new_params = self._interface.next()
        self.logger.info('New measurement params received from EventManager')
        self._measurement_params = new_params


    def confirm_start(self) -> None:
        """Confirm starting the measurement with the EventManager
        """
        self._interface.start()


    def confirm_end(self) -> None:
        """Confirm the end of the current measurement with the EventManager
        """
        self._interface.end(self._measurement_params)


    ## Instrument connections
    #########################


    def server_setup(self, **kwargs) -> None:
        """Initialize instrument connections etc. before running measurement

        Args:
            **kwargs: Passed to the setup() method of the instrument server
                plugin, in addition to the stored instrument config.
        """
        self.logger.info('Requesting instrument config from EventManager...')
        instrument_config = self._interface.config()
        self.logger.info('Instrument config received.')
        self.logger.info('Carrying out server setup...')
        self._server.setup(instrument_config, **kwargs)
        self.logger.info('Server setup completed.')


    ## Measurement execution
    ########################


    def run_measurement(self) -> bool:
        """Run the measurement described by the current parameter set

        Returns:
            True if the measurement completed successfully.
        """

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
        data_path = self._server.measure(self._measurement_params)
        self.logger.info('Measurement completed; finishing...')
        full_path = os.path.abspath(data_path)
        self.logger.info('Output saved to: {}'.format(full_path))
        ## TODO handle crashes related to the underlying measurement software

        ## Dump the config associated with the measurement
        ## Maybe allow this to be a separate directory?
        config_path = os.path.splitext(full_path)[0]+'.yaml'
        ## TODO if/when we upgrade everything to Py3, this can use the himl
        ## dumper, as when dumping to json
        ydump = yaml.safe_dump(
            self._measurement_params.as_config(),
            default_flow_style=False,
        )
        ## Write to file
        with open(config_path, "w") as cfg_file:
            cfg_file.write(ydump)
        self.logger.info('Config written to: {}'.format(config_path))

        ## Add metadata associated with the completed measurement
        self._measurement_params.set_end_time()
        self._measurement_params.output['data_path'] = full_path

        ## Measurement completion confirmation
        self.logger.debug('Controller tasks completed.')
        self.confirm_end()

        ## End gracefully
        return True
