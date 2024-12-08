"""
The reference implementation of a Guide client
"""

from collections.abc import Iterable, Mapping, Sequence
import logging
import os
import sys
from typing import Optional

import himl
import zmq

from ..interfaces.guide import GuideRequestInterface
from ..measurement import Measurement
from ..util import log as mem_logging


###############################################################################
## Helper functions
###############################################################################


def load_config(base_dir: str, config_path: str) -> dict:
	"""Load a himl config via the config_path based on the base_dir
	"""

	cfg = himl.ConfigProcessor().process(
		cwd=base_dir,
		path=os.path.join(base_dir, config_path),
		type_strategies=[
			(list, ["override"]), (dict, ["merge"]),
		],
	)

	return cfg


###############################################################################
## Guide client class
###############################################################################


class ReferenceGuideClient:
	"""A reference implementation of a MEM Guide client class

	Note that this is *not* a base class which all Guide clients must inherit
	from, but rather an example of a generic implementation which interoperates
	with the appropriate interface.
	"""


	def __init__(self,
		endpoint: str,
		logger: Optional[logging.Logger] = None,
		zmq_context: Optional[zmq.Context] = None,
		):

		## Logging
		if logger is None:
			logger = logging.getLogger(__name__)
			self.logger = mem_logging.quick_config(
				logger,
				console_log_level=logging.INFO,
				file_log_level=None,
			)
		else:
			self.logger = logger

		## ZMQ messaging
		self._endpoint = endpoint
		if zmq_context is None:
			self._context = zmq.Context()
		else:
			self._context = zmq_context

		## Interface initialization
		## Start with empty socket - will be added when connecting
		self._interface = GuideRequestInterface(
			socket=None,
			protocol_name="MEM-GR/0.1",
			logger=self.logger,
		)

		## Set up connection
		## Automatic the first time; reconnects must be manual
		self.connect_to_server()


	## Server communication
	#######################


	def connect_to_server(self,
		endpoint: Optional[str] = None,
		) -> None:
		"""Connect to a server

		Updates the stored endpoint if one is provided as an arg.
		"""

		## Update the stored endpoint if a new one is specified
		if endpoint is not None:
			self._endpoint = endpoint

		## (Re)open the socket
		guide_request_socket = self._context.socket(zmq.REQ)
		guide_request_socket.connect(self._endpoint)
		self.logger.debug("Guide request socket bound to %s", self._endpoint)
		## Update the socket at the interface
		self._interface.set_socket(guide_request_socket)


	## Add measurements
	###################


	def add_from_file(self,
		base_dir: str,
		config_path: str,
		) -> None:
		"""Add a measurement defined by a himl config hierarchy
		"""

		## Load config using himl consolidation
		self.logger.info("Loading from file %s", config_path)
		self.logger.debug("himl base_dir is %s", base_dir)
		config = load_config(base_dir, config_path)
		## Add the measurement based on the loaded config
		self.add_from_dict(config)


	def add_from_dict(self, params_dict: Mapping) -> None:
		"""Add a measurement defined by a dict or mapping
		"""

		## Creating a Measurement object acts as a validity check on the
		## client side.
		self.logger.debug("Creating Measurement object...")
		measurement = Measurement(**params_dict)

		## Add the Measurement via the interface API
		self.logger.debug("Sending Measurement to server...")
		self._interface.add(measurement)


	## Remove measurements
	######################


	def remove(self, index_iterable: Iterable) -> list[int]:
		"""Remove measurements from the queue by index
		"""

		## Generate available queue indices
		if (queue_length := self.queue_length) == 0:
			self.logger.warning("Measurement queue is empty; cannot remove.")
			return []
		queue_indices = list(range(queue_length))

		## Apply each index specification directly to the available index list
		## to allow for full use of Python indexing constructs like slices
		resolved_indices = []
		for index_spec in index_iterable:
			target_indices = queue_indices[index_spec]
			## Check if target indices are a singleton or list to avoid nested
			## list elements
			if isinstance(target_indices, Sequence):
				resolved_indices.extend(target_indices)
			else:
				resolved_indices.append(target_indices)

		## De-dupe resolved indices via set
		index_list = list(set(resolved_indices))

		## Send the removal request
		removed_indices = self._interface.remove(index_list)

		## Return the indices that were actually removed according to the
		## server
		self.logger.info("Successfully removed indices %s", removed_indices)
		return removed_indices


	## Queue status
	###############


	@property
	def queue_length(self) -> int:
		"""Current queue length
		"""
		return self._interface.len()


	@property
	def queue(self) -> list[Measurement]:
		"""Current contents of the server queue
		"""

		queue = self._interface.query()
		return queue


	def dump_queue_contents(self, target: Optional[str] = None) -> None:
		"""Dump the contents of the server queue to a writable target
		"""

		## Iterate over measurements and get pretty print representation
		print_list = []
		for index, meas in enumerate(self.queue):
			## Get pretty representation
			pretty_str = meas.pretty_print()
			## Add header and footer
			pretty_header = f"== Index {index: <4}" + "="*46 + "\n"
			pretty_footer = "="*59 + "\n"
			print_list.append(pretty_header + pretty_str + pretty_footer)

		print_generator = (f"{pp}\n" for pp in print_list)
		## Write to file-like object
		if target:
			with open(target, 'w') as target_handle:
				target_handle.writelines(print_generator)
		## Fall back on stdout
		else:
			sys.stdout.writelines(print_generator)


	## Defining the fetch counter using the property decorator is extremely
	## convenient, but has the disadvantage that we cannot easily see what the
	## confirmed value from the server is outside of the log messages (as the
	## setter has no return). As such, this structure may change in the future.
	@property
	def fetch_counter(self) -> int:
		"""Server queue fetch counter value
		"""
		counter = self._interface.get_counter()
		self.logger.info("Fetch counter is %s", counter)
		return counter

	@fetch_counter.setter
	def fetch_counter(self, new_value: int):
		counter = self._interface.set_counter(new_value)
		self.logger.info("Fetch counter set to %s", counter)
