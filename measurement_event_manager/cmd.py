import argparse
import logging

import measurement_event_manager as mem
import measurement_event_manager.util.logger as mem_logging


###############################################################################
## MeasurementEventManager server
###############################################################################


def mem_server():
    '''Start up a MeasurementEventManager instance
    '''

    ## Logging
    ##########

    logger = mem_logging.quick_config(
                            logging.getLogger('MeasurementEventManager'),
                            console_log_level=logging.INFO,
                            file_log_level=logging.DEBUG,
                            )
    logger.debug('Logging initialized.')

    ## MeasurementEventManager
    ##########################

    ## Instantiate object
    mem_server = mem.MeasurementEventManager.MeasurementEventManager(logger)
    ## Set up connections
    ## TODO get connection parameters (addresses etc.) from user-defined config
    mem_server.connect_sockets()

    ## Main event loop
    mem_server.run_event_loop()



###############################################################################
## Individual measurement launch (as subprocess)
###############################################################################


def mem_launch_measurement():
    '''Launch a measurement

    To be used as a subprocess; do not run directly!
    '''

    ## Parse command-line arguments
    ###############################

    parser = argparse.ArgumentParser()
    parser.add_argument('socket_endpoint',
                        help='Endpoint for the socket used to communicate with a MEM instance',
                        action='store',
                        )
    cmd_args = parser.parse_args()


    ## MeasurementController
    ########################

    ## Initialize the MeasurementController object
    meas_controller = mem.MeasurementController.MeasurementController(
                            socket_endpoint=cmd_args.socket_endpoint,
                            )


if __name__ == '__main__':
    mem_server()
