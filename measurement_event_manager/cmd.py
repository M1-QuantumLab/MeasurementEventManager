import argparse
import logging

import measurement_event_manager as mem
import measurement_event_manager.util.logging as mem_logging


###############################################################################
## Default values
###############################################################################


DEF_PROTOCOL = 'tcp'
DEF_GUIDE_PORT = '9010'
DEF_MEAS_PORT = '9011'


###############################################################################
## MeasurementEventManager server
###############################################################################


def mem_server():
    '''Start up a MeasurementEventManager instance
    '''

    ## Parse command-line arguments
    ###############################

    parser = argparse.ArgumentParser()
    parser.add_argument('--guide-port',
                        help='Port used for Guide communication',
                        action='store',
                        default=None)
    parser.add_argument('--meas-port',
                        help='Port used for Measurement Controller '
                             'communcation',
                        action='store',
                        default=None)
    cmd_args = parser.parse_args()


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
    
    ## Construct socket addresses
    if cmd_args.guide_port is not None:
        guide_port = str(cmd_args.guide_port)
    else:
        guide_port = DEF_GUIDE_PORT
    guide_reply_endpoint = '{}://*:{}'.format(DEF_PROTOCOL, guide_port)
    if cmd_args.meas_port is not None:
        meas_port = str(cmd_args.meas_port)
    else:
        meas_port = DEF_MEAS_PORT
    meas_reply_endpoint = '{}://*:{}'.format(DEF_PROTOCOL, meas_port)
    meas_request_endpoint = '{}://localhost:{}'.format(DEF_PROTOCOL, meas_port)

    ## Set up connections
    mem_server.connect_sockets(guide_reply=guide_reply_endpoint,
                               meas_reply=meas_reply_endpoint,
                               meas_request=meas_request_endpoint,
                               )

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
