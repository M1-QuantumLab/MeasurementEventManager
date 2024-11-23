import argparse
import logging
import sys

import zmq

from measurement_event_manager.controller import Controller
from measurement_event_manager.server_plugins.pyhegel import PyHegelServer
from measurement_event_manager.util import log as mem_logging


###############################################################################


def main() -> None:
	'''Launch a measurement

	Launched automatically by the EventManager during normal operation. Can be
	run directly when debugging, but you should know what you're doing!
	
	Note that the arguments are passed in from the command-line and not to the
	function directly, to allow this function to be wrapped in a command-line
	executable entry point and draw all necessary input parameters from there.
	'''

	## Command-line arguments

	parser = argparse.ArgumentParser()

	parser.add_argument(
		'socket_endpoint',
		help='Endpoint for the socket used to communicate with a MEM instance',
		action='store',
	)

	parser.add_argument(
		'--file-log-level',
		help='Logging level for file output',
		default='info',
	)

	cmd_args = parser.parse_args()


	## Logging

	logger = logging.getLogger('MEM-Controller')
	logger = mem_logging.quick_config(
		logger,
		console_log_level=None,
		file_log_level=mem_logging.parse_log_level(
			cmd_args.file_log_level,
		),
	)
	logger.debug('Logging initialized.')

	## Redirect stderr to logger, preserving lower-level error messages that
	## would otherwise be lost on process crash
	sys.stderr = mem_logging.StreamToLogger(logger, logging.ERROR)


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
	instrument_interface = PyHegelServer(logger=logger)

	## Instantiate Controller client
	meas_controller = Controller(
		endpoint=ctrl_request_endpoint,
		logger=logger,
		zmq_context=context,
		server_plugin=instrument_interface,
	)


	## Controller tasks
	###################

	## Instrument server setup
	meas_controller.server_setup()
	## Request measurement params from the parent EventManager
	meas_controller.get_measurement_params()
	## Run the measurement
	meas_controller.run_measurement()


## Enables this fiile to be run as a script for debugging
## This debugging can mimic the command-line invocation
if __name__ == '__main__':
	main()
