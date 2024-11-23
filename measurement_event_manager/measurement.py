"""
Data structures for specifying, storing, and translating measurement
definitions.
"""

from collections.abc import Mapping, Iterable
import copy
import datetime
import json
from typing import Optional


###############################################################################
## Measurement class definition
###############################################################################


class Measurement:
	"""A container class for a measurement specification
	"""

	def __init__(self,
		submitter: str,
		metadata: Optional[Mapping] = None,
		output: Optional[Mapping] = None,
		setvals: Optional[Mapping] = None,
		sweep: Optional[Iterable[Mapping] | Mapping] = None,
		):
		"""
		The output, setvals, and sweep containers must describe the data in the
		format expected by the corresponding instrument server plugin.

		Args:
			submitter: The person or entity responsible for the measurement.
			metadata: Administrative or informational data which is not passed
				to the instrument server or drivers.
			output: Specification for measurement outputs, eg which instruments
				to read data from.
			setvals: Specification for single-value stimulus settings, which
				will be set once at the beginning of the measurement and not
				changed.
			sweep: Specification for multi-value stimulus settings, as an
				ordered sequence that defines the progression of iteration for
				multivariate sweeps.
		"""

		## Measurement submitter identification
		## This may be extended with auth at some point
		self.submitter: str = submitter
		"""The name of the person responsible for the measurement.
		"""

		## Start and end datetime markers - begin uninitialized
		self.start_time: datetime.datetime = None
		"""Time at which the measurement was started, if applicable.
		"""
		self.end_time: datetime.datetime = None
		"""Time at which the measurement finished, if applicable.
		"""

		## Avoid mutable empty defaults

		## Metadata (administrative or informational data)
		## These are values which will not be parsed by pyHegel or instrument
		## drivers
		if metadata is None:
			self.metadata = {}
		else:
			self.metadata = metadata

		## Output channel parameters
		if output is None:
			self.output = {}
		else:
			self.output = output

		## Instrument parameters (measurement 'inputs')
		if setvals is None:
			self.setvals = {}
		else:
			self.setvals = setvals

		## Sweep values
		if sweep is None:
			self.sweep = []
		## Package a single sweep correctly to allow for MultiSweep
		elif isinstance(sweep, Mapping):
			self.sweep = [sweep,]
		## Otherwise, assume everything is correctly specified (ie list)
		else:
			self.sweep = sweep


	## JSON serialization
	#####################


	## Custom serialization method for encoding
	def _json(self) -> dict:
		return {'Measurement': self.__dict__}


	## User-facing serialization method
	def to_json(self) -> str:
		"""Serialize the Measurement object as JSON

		This can be converted back into Measurement using from_json().

		Returns:
			String representation of the Measurement.
		"""
		return json.dumps(self, cls=_MPEncoder)


	## Printed representation
	#########################


	def __repr__(self):
		repr_string_list = ['Measurement(']
		for key, value in self.__dict__.items():
			repr_string_list.append('{}={},'.format(key, repr(value)))
		repr_string_list.append(')')
		repr_string = ''.join(repr_string_list)
		return repr_string


	def as_config(self) -> dict:
		"""A dict representation appropriate for dumping as a config

		Excludes keys such as start_time and end_time which are specific to
		this instance of the measurement.

		Returns:
			A Python dict representation of the Measurement.
		"""

		## Get dict representation of all the parameters
		config_dict = copy.deepcopy(self.__dict__)
		## Exclude the keys specific to the measurement
		exclude_keys = ('start_time', 'end_time',)
		for exc_key in exclude_keys:
			## Use pop so we don't have to deal with exceptions
			config_dict.pop(exc_key, None)
		return config_dict


	def pretty_print(self) -> str:
		"""Pretty multi-line display, as a single string
		"""

		## Start with submitter information
		print_str = f"Submitter: {self.submitter}\n"

		## Metadata
		print_str += "Metadata:\n"
		for meta_key, meta_val in self.metadata.items():
			print_str += f"    {meta_key:-<20}: {meta_val}\n"

		## Outputs
		print_str += "Outputs:\n"
		for out_key, out_val in self.output.items():
			if out_key == "channels":
				channels_title = "Channels"
				print_str += f"    {channels_title}:\n"
				for channel_dict in out_val:
					print_str += f"    -- {channel_dict}\n"
			else:
				print_str += f"    {out_key:-<20}: {out_val}\n"

		## Setvals
		print_str += "Setvals:\n"
		for instr_name, instr_vals in self.setvals.items():
			print_str += f"--> {instr_name}:\n"
			for param_name, param_val in instr_vals.items():
				print_str += f"      {param_name:-<20}: {param_val}\n"

		## Sweeps
		if self.sweep:
			print_str += "Sweep: (Dims are SLOW to FAST)\n"
			for dim_index, sweep_dim in enumerate(self.sweep):
				print_str += f"--> Dim {dim_index}:\n"
				for param_name, param_val in sweep_dim.items():
					print_str += f"      {param_name:-<20}: {param_val}\n"

		return print_str


	## Measurement administration
	#############################


	def set_start_time(self,
		time: Optional[datetime.datetime] = None,
		) -> None:
		"""Indicate that the measurement has started

		Args:
			time: The start time of the measurement; if None, the current time
				will be used.
		"""

		if time is None:
			self.start_time = datetime.datetime.now()
		else:
			self.start_time = time


	def set_end_time(self,
		time: Optional[datetime.datetime] = None,
		) -> None:
		"""Indicate that the measurement has stopped or completed

		Args:
			time: The end time of the measurement; if None, the current time
				will be used.
		"""

		if time is None:
			self.end_time = datetime.datetime.now()
		else:
			self.end_time = time


###############################################################################
## Custom JSON encoder/decoder
###############################################################################


## Encoding (MP -> JSON)
########################


class _MPEncoder(json.JSONEncoder):
	'''Custom JSON encoder for Measurement objects
	'''

	def default(self, obj) -> str:

		## First, check if we have a datetime object
		if isinstance(obj, datetime.datetime):
			## This will return the ISO-formatted string representation
			return obj.isoformat()

		## Fall back on any available _json methods
		try:
			return obj._json()
		## Otherwise just use the default behaviour from the default encoder
		except AttributeError:
			return json.JSONEncoder.default(self, obj)


## Decoding (JSON -> MP)
########################

ISO_STRPTIME = '%Y-%m-%dT%H:%M:%S.%f'

def _mp_from_json(json_dict: Mapping) -> dict:
	'''object hook function for json.loads; use from_json() as a user!
	'''

	## Handle the whole Measurement object at the top level
	if 'Measurement' in json_dict:
		mp_dict = json_dict['Measurement']
		## Pull out the start and stop times
		## If they are present, we need to parse them back into datetime
		start_time = mp_dict.pop('start_time', None)
		if start_time is not None:
			start_time = datetime.datetime.strptime(start_time, ISO_STRPTIME)
		end_time = mp_dict.pop('end_time', None)
		if end_time is not None:
			end_time = datetime.datetime.strptime(end_time, ISO_STRPTIME)
		## Create the object
		mp_obj = Measurement(**mp_dict)
		## Set the start and stop times
		## Calling the function with a None argument sets it to the current
		## time, so we want to avoid setting a time that's not real
		## There is probably a better way of doing this...
		if start_time is not None:
			mp_obj.set_start_time(start_time)
		if end_time is not None:
			mp_obj.set_end_time(end_time)
		## Return the final object with updated special params
		return mp_obj
	## Handle any individual objects that require special parsing
	for key, value in json_dict.items():
		pass

	return json_dict


def from_json(json_object: str | bytes) -> Measurement:
	"""Construct a Measurement instance from a serial JSON object

	Args:
		json_object: A serial representation of a measurement specification

	Returns:
		A Measurement object
	"""
	return json.loads(json_object, object_hook=_mp_from_json)
