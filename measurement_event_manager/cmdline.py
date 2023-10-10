import argparse
import itertools
import logging

import zmq

from measurement_event_manager.controller import Controller
from measurement_event_manager.event_manager import EventManager
import measurement_event_manager.util.log as mem_logging

from measurement_event_manager.interfaces.guide import (
    GuideReplyInterface,
)
from measurement_event_manager.interfaces.controller import (
    ControllerReplyInterface,
)

from measurement_event_manager.server_plugins.pyhegel import PyHegelServer


###############################################################################
## Default values
###############################################################################


DEF_PROTOCOL = 'tcp'
DEF_GUIDE_PORT = '9025'
DEF_CTRL_PORT = '9026'
DEF_PUB_PORT = '9027'

## Max server tick time in ms
## We pass this in to prevent infinite waits on poller.poll, which would result
## in being unable to process ctrl-c events on Windows (apparently?)
POLL_TIMEOUT = 2000


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
    parser.add_argument('--pub-port',
                        help='Port used to publish information about '
                             'completed measurements to Listeners',
                        action='store',
                        default=None)
    parser.add_argument('--console-log-level',
                        help='Logging level for console output',
                        default='info')
    parser.add_argument('--file-log-level',
                        help='Logging level for file output',
                        default='debug')
    parser.add_argument('--disable-measurement-launch',
                        help='For debug use only; disables the actual launch '
                             'of the Controller as a subprocess, which must '
                             'instead be started manually by the user in a '
                             'separate thread',
                        action='store_true',
                        default=False)
    cmd_args = parser.parse_args()


    ## Logging
    ##########

    logger = mem_logging.quick_config(
        logging.getLogger('MEM-EventManager'),
        console_log_level=mem_logging.parse_log_level(
            cmd_args.console_log_level),
        file_log_level=mem_logging.parse_log_level(
            cmd_args.file_log_level),
        )
    logger.debug('Logging initialized.')


    ## Communications setup
    #######################


    ## Initialize context
    context = zmq.Context()


    ## Initialize sockets

    ## Guide reply address
    if cmd_args.guide_port is not None:
        guide_port = str(cmd_args.guide_port)
    else:
        guide_port = DEF_GUIDE_PORT
    guide_reply_endpoint = '{}://*:{}'.format(DEF_PROTOCOL, guide_port)
    ## Guide reply socket
    guide_reply_socket = context.socket(zmq.REP)
    guide_reply_socket.bind(guide_reply_endpoint)
    logger.debug('Guide reply socket bound to {}'.format(guide_reply_endpoint))

    ## Controller reply address
    if cmd_args.meas_port is not None:
        ctrl_port = str(cmd_args.meas_port)
    else:
        ctrl_port = DEF_CTRL_PORT
    ctrl_reply_endpoint = '{}://*:{}'.format(DEF_PROTOCOL, ctrl_port)
    ## Controller reply socket
    ctrl_reply_socket = context.socket(zmq.REP)
    ctrl_reply_socket.bind(ctrl_reply_endpoint)
    logger.debug('Controller reply socket bound to'
                 ' {}'.format(ctrl_reply_endpoint))

    ## Controller request address
    ## Passed to the instatiation function for the spawned Controller process
    ctrl_request_endpoint = '{}://localhost:{}'.format(DEF_PROTOCOL, ctrl_port)
    
    ## Listener broadcast address
    if cmd_args.pub_port is not None:
        pub_port = str(cmd_args.pub_port)
    else:
        pub_port = DEF_PUB_PORT
    listener_pub_endpoint = '{}://*:{}'.format(DEF_PROTOCOL, pub_port)
    ## Listener broadcast socket
    listener_pub_socket = context.socket(zmq.PUB)
    listener_pub_socket.bind(listener_pub_endpoint)
    logger.debug('Listener pub socket bound to'
                 ' {}'.format(listener_pub_endpoint))


    ## Set up poller for main event loop
    poller = zmq.Poller()
    ## Register only incoming sockets
    poller.register(guide_reply_socket, zmq.POLLIN)
    poller.register(ctrl_reply_socket, zmq.POLLIN)


    ## EventManager and interfaces
    ##############################


    ## Instantiate EventManager
    mem_server = EventManager(
                              logger=logger,
                              controller_endpoint=ctrl_request_endpoint,
                             )

    ## Instantiate interfaces

    guide_interface = GuideReplyInterface(
                                    server=mem_server,
                                    socket=guide_reply_socket,
                                    protocol_name='MEM-GR/0.1',
                                    logger=logger,
                                    )

    controller_interface = ControllerReplyInterface(
                                    server=mem_server,
                                    socket=ctrl_reply_socket,
                                    protocol_name='MEM-MS/0.1',
                                    logger=logger,
                                    )


    ## Main event loop
    ##################

    logger.info('Running main event loop.')

    for server_tick in itertools.count():
        logger.debug('Server tick {}'.format(server_tick))

        ## Attempt to start a new measurement
        ## All the logic of incrementing the fetch counter etc is handled by
        ## the MEM server instance
        mem_server.new_measurement_trigger(
                        disable_launch=cmd_args.disable_measurement_launch,
                        )

        ## Communications

        ## Get poll on all sockets
        logger.info('Listening for messages on all sockets')
        poll_all = dict(poller.poll(POLL_TIMEOUT))

        ## Identify incoming request by socket, and pass to the appropriate
        ## interface along with the MEM server object

        if poll_all.get(guide_reply_socket, None) == zmq.POLLIN:
            logger.debug('Incoming message on guide reply socket')
            guide_interface.process_request()

        elif poll_all.get(ctrl_reply_socket, None) == zmq.POLLIN:
            logger.debug('Incoming message on controller reply socket')
            controller_interface.process_request()

        ## End of main event loop



###############################################################################
## Individual measurement launch (as subprocess)
###############################################################################


def mem_launch_measurement():
    '''Launch a measurement

    Launched automatically by the EventManager during normal operation. Can be
    run directly when debugging, but you should know what you're doing!
    
    Note that the arguments are passed in from the command-line and not to the
    function directly, to allow this function to be wrapped in a command-line
    executable entry point and draw all necessary input parameters from there.
    '''

    ## Command-line arguments

    parser = argparse.ArgumentParser()
    parser.add_argument('socket_endpoint',
                        help='Endpoint for the socket used to communicate with a MEM instance',
                        action='store',
                        )
    parser.add_argument('--instrument-config',
                        help='Path to config file used for instrument driver '
                             'setup',
                        action='store',
                        default='mem_pyhegel.yaml',
                        )
    parser.add_argument('--file-log-level',
                        help='Logging level for file output',
                        default='info')
    cmd_args = parser.parse_args()


    ## Logging

    logger = logging.getLogger('MEM-Controller')
    logger = mem_logging.quick_config(
                logger,
                console_log_level=None,
                file_log_level=mem_logging.parse_log_level(
                                                cmd_args.file_log_level),
                )
    logger.debug('Logging initialized.')


    ## Communications setup
    #######################


    ## Initialize context
    ## Note that here, we do explicitly want to create our own context even
    ## though we could in principle pass in the one from the parent process
    ## (EventManager). This is so we can maintain full independence, including
    ## socket-alive-status independence, from the EventManager process, and 
    ## either side can crash, revive, reconnect, etc. without any problems.
    context = zmq.Context()

    ## Controller request address
    ## We require this to be specified explicitly in the command-line args, as
    ## it is not passed by a human, but by the EventManager code
    ctrl_request_endpoint = cmd_args.socket_endpoint


    ## Controller client
    ####################

    ## Instantiate server interface
    instrument_interface = PyHegelServer(
                            config_path=cmd_args.instrument_config,
                            logger=logger,
                            )

    ## Instantiate Controller client
    meas_controller = Controller(
                            endpoint=ctrl_request_endpoint,
                            logger=logger,
                            zmq_context=context,
                            server_plugin=instrument_interface,
                            )


    ## Controller tasks
    ###################

    ## Request measurement params from the parent EventManager
    meas_controller.get_measurement_params()
    ## Measurement preprocessing and instrument setup
    meas_controller.server_setup()
    ## Run the measurement
    meas_controller.run_measurement()


if __name__ == '__main__':
    mem_server()
