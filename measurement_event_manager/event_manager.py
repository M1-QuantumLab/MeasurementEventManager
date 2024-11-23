"""
The main MeasurementEventManager class.
"""

from collections.abc import Mapping, Iterable
import logging
import os
import subprocess
from typing import Optional

from .measurement import Measurement
from .queue import Queue
from .util.errors import QueueEmptyError


###############################################################################
## Main MEM class
###############################################################################


class EventManager:
    """The main 'server' class of the MEM ecosystem

    The EventManager is responsible for:

    - Receiving input directives through the Guide interface
    - Maintaining the measurement queue
    - Launching the next measurement when permitted through the Controller
      interface
    - Broadcasting information about completed measurements through the
      Listener interface (incomplete)

    A single EventManager instance should in principle be associated with a
    single experimental 'session', that is, multiple measurements where the
    same equipment is used in the same way.
    The communication and startup parameters for the instrument drivers are
    provided when launching the EventManager (the `instrument_config`), and
    these cannot be modified during the lifetime of the EventManager.

    The EventManager is designed to run in the background, without additional
    input from the user post-launch.
    """

    ## Setup and initialization
    ###########################


    def __init__(self,
        logger: logging.Logger,
        controller_endpoint: str,
        instrument_config: Mapping,
        fetch_counter: int = 0,
        ):
        """Foo bar

        Args:
            logger: A logging object.
            controller_endpoint: The address which the Controller interface
            should use.
            instrument_config: Parameters for instrument drivers, passed to the
            instrument server plugin.
            fetch_counter: The initial value for the fetch counter, tracking
            how many measurements to pull from the queue automatically.
        """

        ## Assign logger
        self.logger: logging.Logger = logger
        ## Create queue for measurements
        self.queue: Queue = Queue()

        ## Measurement queue fetch counter
        self._fetch_counter = None
        self.set_fetch_counter(fetch_counter)

        ## Active measurement
        self._current_measurement: Measurement = None

        ## Declare variables for later
        self._instrument_config = instrument_config
        self._meas_request_endpoint = controller_endpoint


    ## Config and instrument setup
    ##############################


    def get_config(self) -> Mapping:
        """Return the instrument config specified at launch

        Returns:
            A dict corresponding to the instrument configuration stored by the
            EventManager.
        """
        return self._instrument_config


    ## Measurement status
    #####################


    def is_measurement_running(self) -> bool:
        """Check if there is an active measurement

        This is considered with respect to the EventManager state, and cannot
        recognize if eg. a measurement is hung or has been externally aborted.

        Returns:
            True if a measurement is active (considered running by the
            EventManager), False otherwise.
        """

        return bool(self._current_measurement)


    def new_measurement_trigger(self, disable_launch: bool = False) -> bool:
        """Start a new measurement

        Launching a measurement can fail or be prohibited by the following
        conditions:

        - Another measurement is currently in progress
        - The fetch counter is at 0, disallowing further measurements until it
            is changed
        - The measurement queue is empty

        Args:
            disable_launch: Debug flag used to disable the actual launching of
                the measurement process; the measurement process (Controller
                service) is expected to be started manually by the user.

        Returns:
            True if the measurement was successfully launched, False otherwise.
            Note that a 'successful' launch with the disable_launch flag set
            will return True, to mimic the non-debugging behaviour.
        """

        ## If there is already a measurement running, we cannot start a new one
        if self.is_measurement_running():
            self.logger.debug('A measurement is currently in progress')
            return False
        ## If the fetch counter is at 0, we cannot attempt to start a new
        ## measurement
        elif self._fetch_counter == 0:
            self.logger.debug('Fetch counter is at 0; skipping fetch and'
                             ' waiting for increase')
            return False

        ## We are allowed to fetch a new measurement
        self.logger.debug('Attempting to fetch measurement from queue...')
        try:
            next_measurement = self.queue.pop_next()
        except QueueEmptyError:
            self.logger.warning('Queue is empty; cannot fetch measurement')
            ## Return without incrementing the fetch counter
            return False

        ## We successfully have a new measurement from the queue to run
        ## Pre-processing admin
        self._decrement_fetch_counter()
        self._current_measurement = next_measurement

        ## Actual subprocess launch can be disabled for debugging
        if disable_launch:
            self.logger.warning('Launch disabled; measurement thread is '
                                'expected to be started manually.')
        else:
            self.logger.info('Launching measurement...')
            ## Identify the OS as creating a detached process is handled
            ## differently
            ## Windows
            if os.name == 'nt':
                flags = 0
                flags |= 0x00000008  # DETACHED_PROCESS
                flags |= 0x00000200  # CREATE_NEW_PROCESS_GROUP
                # flags |= 0x08000000  # CREATE_NO_WINDOW
                proc = subprocess.Popen(['mem_launch_measurement',
                                        self._meas_request_endpoint],
                                        close_fds=True,
                                        creationflags=flags,
                                        )

            ## Unix-like
            elif os.name == 'posix':
                proc = subprocess.Popen(['nohup', 'mem_launch_measurement',
                                        self._meas_request_endpoint],
                                        preexec_fn=os.setpgrp,
                                    )

        return True


    def get_current_measurement(self) -> Measurement:
        """Get the active measurement

        Returns:
            A MeasurementParams object corresponding to the active measurement,
            or None if there is no active measurement.
        """
        return self._current_measurement
    

    def get_current_measurement_json(self) -> str:
        """Get a serial JSON representation of the active measurement

        Returns:
            The active measurement as a JSON string.
        """
        return self.get_current_measurement().to_json()


    def clear_current_measurement(self) -> None:
        """Clear any active measurement
        """
        self.logger.debug('Clearing current measurement')
        self._current_measurement = None


    def measurement_finished(self, received_message: Iterable) -> None:
        """Indicate that the active measurement has finished

        Pipes the received measurement data to the publisher socket.

        Args:
            received_message: serialized measurement data
        """
        self.logger.info('Measurement completed; broadcasting to listeners...')
        ## Clear the current measurement attribute
        self.clear_current_measurement()
        ## Publish the serialized measurement data
        ## TODO clean this up so it's not a message, but the underlying object
        measurement_json = received_message[0]
        ## TODO implement the publication
        # self.publish_measurement(measurement_json)


    def publish_measurement(self, measurement_json: str):
        """Publish serialized measurement data to the listener pub socket

        This is currently not implemented! Do not use.
        """
        raise NotImplementedError


    def fetch_counter(self, set_counter: Optional[int] = None) -> int:
        """Set the number of measurements to be fetched before pausing

        Calling this method with no args will return the current counter value.

        Any negative integer will be interpreted as an infinite fetch, but may
        be changed to -1.

        Args:
            set_counter: The desired value for the fetch counter.

        Returns:
            The current fetch counter, after modification.
        """

        if set_counter is not None:
            self._fetch_counter = int(set_counter)
        ## If set_counter is None, treat it as a query and return the value
        ## without modification
        return self._fetch_counter


    def get_fetch_counter(self) -> int:
        """Get the number of measurements to be fetched before pausing

        Returns:
            The current fetch counter.
        """
        return self._fetch_counter


    def set_fetch_counter(self, new_counter: int) -> int:
        """Set the number of measurements to be fetched before pausing

        A negative value will be interpreted as infinite, but will be changed
        to -1 for consistency.

        Args:
            new_counter: The desired value for the fetch counter.

        Returns:
            The current fetch counter, after modification.
        """
        counter_input = int(new_counter)
        ## If the new value is < -1, we use -1 for consistency
        if counter_input <= -1:
            self._fetch_counter = -1
        else:
            self._fetch_counter = counter_input
        return self._fetch_counter


    def _decrement_fetch_counter(self) -> None:
        """Decrement the fetch counter

        If the counter is a positive integer, it is decremented by 1

        If the counter is at -1, it remains at that value.

        Raises:
            ValueError: Attempting to decrement a fetch counter from 0.
        """
        ## In principle we could just always decrement it, as any negative
        ## value would count as infinite, but we might as well be a bit more
        ## specific to avoid weird behaviour
        if self._fetch_counter > 0:
            self._fetch_counter -= 1
            self.logger.info('Fetch counter decremented to '
                             '{}'.format(self._fetch_counter))
        elif self._fetch_counter == 0:
            raise ValueError("Fetch counter is at 0; cannot be decremented")
        else:
            self.logger.debug('Counter set for infinite fetch; not modified.')


    ## Queue handling
    #################


    def add_to_queue(self,
        measurement_or_iterable: Iterable[Measurement]|Measurement,
        ) -> int|list[int]:
        """Add measurement(s) to the queue

        Args:
            measurement_or_iterable: A measurement definition, or an iterable
                container of them.

        Returns:
            The queue indice(s) at which the measurement(s) were added.
        """
        if isinstance(measurement_or_iterable, Iterable):
            new_indices = []
            for meas_item in measurement_or_iterable:
                added_index = self.queue.add(meas_item)
                new_indices.append(added_index)
            return new_indices
        else:
            new_index = self.queue.add(meas_item)
            return new_index


    def remove_from_queue(self, index_list: Iterable[int]) -> list[int]:
        """Remove measurement(s) from the queue by index

        Args:
            index_list: A container of indices to remove from the queue.

        Returns:
            Indices at which measurements were successfully removed.
        """
        removed_indices = self.queue.remove(index_list)
        return removed_indices


    def get_queue_elements(self) -> list[Measurement]:
        """Get the measurements in the queue

        Returns:
            Measurement definitions currently in the queue.
        """
        return self.queue.info()


    def get_queue_length(self) -> int:
        """Get the number of measurements currently in the queue

        Returns:
            The length of the queue.
        """
        return len(self.queue)
