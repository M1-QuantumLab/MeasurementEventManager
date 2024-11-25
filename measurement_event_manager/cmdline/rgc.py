"""
Command-line invocation of the Reference Guide Client (rgc)

The rgc is a fully-functional example implementation of a Guide service and
interface bundled with the main MEM package.

See :doc:`rgc </autoapi/measurement_event_manager/rgc/index>` for more
information about the client class and interactive shell-style interface.
"""

import argparse
import logging
import os

import zmq

from .._const import DEF_PROTOCOL, DEF_GUIDE_PORT
from ..rgc import ReferenceGuideClient, GuideClientShell
from ..util import log as mem_logging


###############################################################################


def main():
	"""Start the Reference Guide Client
	"""

	## Parse command-line arguments
	###############################

	parser = argparse.ArgumentParser()

	parser.add_argument(
		"config",
		help="Config file(s) containing measurement parameters",
		nargs="*",
	)

	parser.add_argument(
		"--endpoint",
		help="Endpoint address for MEM server connection",
		default=None,
	)

	parser.add_argument(
		"--interactive", "-i",
		help="Enable interactive mode",
		action="store_true",
	)

	parser.add_argument(
		"--console-log-level",
		help="Logging level for console output",
		default="info",
	)

	parser.add_argument(
		"--file-log-level",
		help="Logging level for file output",
		default="info",
	)

	cmd_args = parser.parse_args()


	## Logging
	##########


	logger = mem_logging.quick_config(
		logging.getLogger("ReferenceGuideClient"),
		console_log_level=mem_logging.parse_log_level(
			cmd_args.console_log_level,
		),
		file_log_level=mem_logging.parse_log_level(
			cmd_args.file_log_level
		),
	)


	## Communications setup
	#######################


	## Initialize context
	context = zmq.Context()

	## Guide request endpoint
	if cmd_args.endpoint is not None:
		guide_endpoint = cmd_args.endpoint
	else:
		guide_endpoint = f"{DEF_PROTOCOL}://localhost:{DEF_GUIDE_PORT}"


	## Guide client
	###############


	## Instantiate Guide client class
	guide_client = ReferenceGuideClient(
		endpoint=guide_endpoint,
		logger=logger,
		zmq_context=context,
	)


	## Process args
	###############


	## Add specified config(s)
	for config_file in cmd_args.config:
		guide_client.add_from_file(os.getcwd(), config_file)


	## Interactive mode
	###################


	if cmd_args.interactive:
		GuideClientShell(guide_client).cmdloop()


if __name__ == '__main__':
	main()
