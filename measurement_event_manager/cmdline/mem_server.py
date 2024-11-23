"""
Entry point 

Function defined here are installed as command-line entry points for the MEM
services, allowing execution as standalone command-line programs without the
need to launch a Python interpreter session explicitly.

In the course of regular operation, only the ``mem_server`` application should
be used, to launch the EventManager service.
The ``mem_launch_measurement`` application should only be used for debugging.
"""

import argparse
import logging
import os

from alive_progress import alive_bar
import yaml
import zmq

from measurement_event_manager import _const
from measurement_event_manager.event_manager import EventManager
from measurement_event_manager.interfaces.controller import ControllerReplyInterface
from measurement_event_manager.interfaces.guide import GuideReplyInterface
from measurement_event_manager.util import log as mem_logging


###############################################################################
## Default values
###############################################################################


#: Default server tick interval (in ms)
TICK_INTERVAL = 5000
## We pass this in to prevent infinite waits on poller.poll, which would result
## in being unable to process ctrl-c events on Windows (apparently?)

#: Default fetch counter for new EventManager processes
DEF_FETCH_COUNTER = 0
## Set the default fetch counter to 0 so there are no nasty surprises when
## launching a new process.


###############################################################################


def main() -> None:
	"""Start the EventManager service
	"""

	## Parse command-line arguments
	###############################

	parser = argparse.ArgumentParser()

	parser.add_argument(
		'instrument_config',
		help='Path to the instrument config specification',
		action='store',
	)

	parser.add_argument(
		'--guide-port',
		help='Port used for Guide communication',
		action='store',
		default=None,
	)

	parser.add_argument(
		'--meas-port',
		help='Port used for Controller communcation',
		action='store',
		default=None,
	)

	parser.add_argument(
		'--pub-port',
		help='Port used to publish information about completed measurements to'
			 ' Listener services',
		action='store',
		default=None,
	)

	parser.add_argument(
		'--console-log-level',
		help='Logging level for console output',
		default='info',
	)

	parser.add_argument(
		'--file-log-level',
		help='Logging level for file output',
		default='debug',
	)

	parser.add_argument(
		'--tick-interval',
		help='Set the server tick interval in ms; this sets the maximal '
			 'interval the poller will wait for incoming messages within a '
			 'single server tick',
		default=TICK_INTERVAL,
		type=int,
	)

	parser.add_argument(
		'--fetch-counter',
		help='Set the initial value of the fetch counter, indicating how many '
			 'measurements will be launched when supplied from the queue',
		default=DEF_FETCH_COUNTER,
		type=int,
	)

	parser.add_argument(
		'--disable-measurement-launch',
		help='For debug use only; disables the actual launch of the Controller'
			 ' as a subprocess, which must instead be started manually by the '
			 'user in a separate thread',
		action='store_true',
		default=False,
	)

	cmd_args = parser.parse_args()


	## Logging
	##########

	logger = mem_logging.quick_config(
		logging.getLogger('MEM-EventManager'),
		console_log_level=mem_logging.parse_log_level(
			cmd_args.console_log_level
		),
		file_log_level=mem_logging.parse_log_level(
			cmd_args.file_log_level
		),
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
		guide_port = _const.DEF_GUIDE_PORT
	guide_reply_endpoint = f'{_const.DEF_PROTOCOL}://*:{guide_port}'
	## Guide reply socket
	guide_reply_socket = context.socket(zmq.REP)
	guide_reply_socket.bind(guide_reply_endpoint)
	logger.debug('Guide reply socket bound to {}'.format(guide_reply_endpoint))

	## Controller reply address
	if cmd_args.meas_port is not None:
		ctrl_port = str(cmd_args.meas_port)
	else:
		ctrl_port = _const.DEF_CTRL_PORT
	ctrl_reply_endpoint = f'{_const.DEF_PROTOCOL}://*:{ctrl_port}'
	## Controller reply socket
	ctrl_reply_socket = context.socket(zmq.REP)
	ctrl_reply_socket.bind(ctrl_reply_endpoint)
	logger.debug(
		'Controller reply socket bound to {}'.format(ctrl_reply_endpoint)
	)

	## Controller request address
	## Passed to the instatiation function for the spawned Controller process
	ctrl_request_endpoint = f'{_const.DEF_PROTOCOL}://localhost:{ctrl_port}'

	## Listener broadcast address
	if cmd_args.pub_port is not None:
		pub_port = str(cmd_args.pub_port)
	else:
		pub_port = _const.DEF_PUB_PORT
	listener_pub_endpoint = f'{_const.DEF_PROTOCOL}://*:{pub_port}'
	## Listener broadcast socket
	listener_pub_socket = context.socket(zmq.PUB)
	listener_pub_socket.bind(listener_pub_endpoint)
	logger.debug(
		'Listener pub socket bound to {}'.format(listener_pub_endpoint)
	)


	## Set up poller for main event loop
	poller = zmq.Poller()
	## Register only incoming sockets
	poller.register(guide_reply_socket, zmq.POLLIN)
	poller.register(ctrl_reply_socket, zmq.POLLIN)


	## EventManager and interfaces
	##############################

	## Load instrument config
	instrument_config_path = os.path.abspath(cmd_args.instrument_config)
	with open(instrument_config_path, 'r') as config_file:
		instrument_config = yaml.safe_load(config_file)

	## Instantiate EventManager
	event_manager = EventManager(
		logger=logger,
		controller_endpoint=ctrl_request_endpoint,
		instrument_config=instrument_config,
		fetch_counter=cmd_args.fetch_counter,
	)

	## Instantiate interfaces

	guide_interface = GuideReplyInterface(
		server=event_manager,
		socket=guide_reply_socket,
		protocol_name='MEM-GR/0.1',
		logger=logger,
	)

	controller_interface = ControllerReplyInterface(
		server=event_manager,
		socket=ctrl_reply_socket,
		protocol_name='MEM-MS/0.1',
		logger=logger,
	)


	## Main event loop
	##################

	logger.info('Running main event loop.')

	spinner_kwargs = {
		"title": "Server listening",
		"bar": False,
		"enrich_print": False,
		"monitor": False,
		"elapsed": False,
		"stats": False,
	}

	with alive_bar(**spinner_kwargs) as spinner:
		while True:

			## Animate spinner
			## pylint: disable-next=not-callable
			spinner()

			## Attempt to start a new measurement
			## All the logic of incrementing the fetch counter etc is handled
			## by the MEM server instance
			event_manager.new_measurement_trigger(
				disable_launch=cmd_args.disable_measurement_launch,
			)

			## Communications

			## Get poll on all sockets
			# logger.info('Listening for messages on all sockets')
			poll_all = dict(poller.poll(cmd_args.tick_interval))

			## Identify incoming request by socket, and pass to the appropriate
			## interface along with the MEM server object

			if poll_all.get(guide_reply_socket, None) == zmq.POLLIN:
				logger.debug('Incoming message on guide reply socket')
				guide_interface.process_request()

			elif poll_all.get(ctrl_reply_socket, None) == zmq.POLLIN:
				logger.debug('Incoming message on controller reply socket')
				controller_interface.process_request()

			## End of main event loop


## Enables this fiile to be run as a script for debugging
## This debugging can mimic the command-line invocation
if __name__ == '__main__':
	main()
