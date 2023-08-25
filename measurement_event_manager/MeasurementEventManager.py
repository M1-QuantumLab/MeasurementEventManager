'''
The main MeasurementEventManager class.
'''

import itertools

import zmq

from measurement_event_manager.MeasurementQueue import MeasurementQueue
from measurement_event_manager import Protocols

###############################################################################
## Defaults and definitions
###############################################################################


GUIDE_PROTOCOL = "MEM-GR/0.1"
GUIDE_TIMEOUT = 2500 # in ms
GUIDE_ENDPOINT = 'tcp://*:5555'

MEAS_PROTOCOL = 'MEM-MS/0.1'
MEAS_ENDPOINT = 'tcp://*:5556'
MEAS_SPAWN_ENDPOINT = 'tcp://localhost:5556'


###############################################################################
## Main MEM class
###############################################################################


class MeasurementEventManager(object):
    

    def __init__(self, logger):
        ## Assign logger
        self.logger = logger
        ## Create queue for measurements
        self.queue = MeasurementQueue()


    def connect_sockets(self):
        '''docstring.
        '''

        ## Create ZMQ context
        self.context = zmq.Context()

        ## Set up guide response socket
        self.guide_socket = self.context.socket(zmq.REP)
        self.guide_socket.bind(GUIDE_ENDPOINT)
        self.logger.debug('Guide response socket initialized.')

        ## Set up measurement controller response socket
        self.meas_socket = self.context.socket(zmq.REP)
        self.meas_socket.bind(MEAS_ENDPOINT)
        self.logger.debug('Measurement controller response socket initialized.')

        ## Initialize poller subscribed to all response sockets
        self.poller = zmq.Poller()
        self.poller.register(self.guide_socket, zmq.POLLIN)
        self.poller.register(self.meas_socket, zmq.POLLIN)


    def run_event_loop(self):
        '''Run the main event loop of the server

        Listens for messages on all registered sockets and responds to requests
        according to the defined protocol handlers.
        '''

        self.logger.info('Listening for messages on all sockets.')

        for server_tick in itertools.count():
            self.logger.debug('Server tick {}'.format(server_tick))

            ## TODO I think we need to check if we need to start the next 
            ## measurement *before* we do the blocking call to poll()

            ## Get poll on all sockets
            poll_all = dict(self.poller.poll())

            ## Identify request and pass to protocol handlers
            ## along with the state machine (the measurement queue)
            ## This way, the protocol handlers don't need to know any details
            ## of the MEM in order to modify the state.
            
            if poll_all.get(self.guide_socket, None) == zmq.POLLIN:
                self.logger.debug('Incoming message on guide socket.')
                Protocols.process_request(socket=self.guide_socket,
                                          socket_type='guide',
                                          logger=self.logger,
                                          queue=self.queue,
                                          )
            
            elif poll_all.get(self.meas_socket, None) == zmq.POLLIN:
                self.logger.debug('Incoming message on measurement socket.')
                Protocols.process_request(socket=self.meas_socket,
                                          socket_type='measurement',
                                          logger=self.logger,
                                          )
