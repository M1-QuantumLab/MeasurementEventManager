"""
A queue for storing measurement definitions

The user does not interact with the queue directly; it is instead managed by
the EventManager instance.
"""

import collections
import copy
from typing import Iterable, List, Optional

from .measurement_params import MeasurementParams
from .util.errors import QueueEmptyError


###############################################################################
## MeasurementQueue class
###############################################################################


class Queue(object):
    """
    """

    ## Init and setup
    #################

    def __init__(self):
        self.queue = collections.deque()


    ## Special methods
    ##################

    def __len__(self) -> int:
        return len(self.queue)


    ## Queue management
    ###################


    def add(self, measurement_params: MeasurementParams) -> int:
        """Add a measurement to the end of the queue

        Args:
            measurement_params: Measurement specification to be added.

        Returns:
            The index in the queue at which the measurement was added.
        """
        self.queue.append(measurement_params)
        ## Return the index at which the measurement was added
        return len(self.queue)-1


    def info(self) -> List[MeasurementParams]:
        """Give information about the queue to the client

        Returns:
            The current state of the queue as a list
        """
        ## Here, we want to ensure the client can't modify the queue, so we
        ## pass a deepcopy just to be safe.
        ## The client is responsible for displaying the information in the way
        ## the user wants.
        ## TODO Figure out if this deepcopy is necessary or if it is done
        ## naturally at some point in the process?
        return list(copy.deepcopy(self.queue))


    def remove(self, index_list: Optional[Iterable] = None) -> List[int]:
        """Remove the measurements at the specified indices

        Args:
            index_list: A list of valid positive integer indices. Validation is
                expected to be carried out on the client side, and invalid
                indices will be silently dropped.

        Returns:
            A list of the indices that were successfully removed from the
                queue.

        Raises:
            QueueEmptyError: If the queue is empty.
        """

        ## First, ensure there are items in the queue to delete
        if len(self.queue) == 0:
            raise QueueEmptyError
        ## Validity checks on indices - we only parse valid positive values
        ## All funky indexing needs to happen on the client side!
        valid_indices = [ii for ii in index_list if ii < len(self.queue)]
        ## Ensure indices are all modulo length so the sorting will be correct
        ## Remove dupes with a set, otherwise they will end up messing up the
        ## in-place deletion operation
        mod_set = set([ii % len(self.queue) for ii in valid_indices])
        ## Sort indices backwards, so we delete the highest-indexed values
        ## first so the lowest-indexed values don't have to move
        sorted_indices = sorted(list(mod_set), reverse=True)
        ## Iterate over indices and delete
        deleted_indices = []
        for index in sorted_indices:
            del self.queue[index]
            deleted_indices.append(index)
        return deleted_indices


    def pop_next(self) -> MeasurementParams:
        """Get the first measurement, removing it from the queue

        Returns:
            The measurement specification

        Raises:
            QueueEmptyError: No measurement can be fetched if the queue is
                empty.
        """

        try:
            meas = self.queue.popleft()
        except IndexError:
            ## In this case, as we are always trying to fetch the first
            ## element, an IndexError can only occur if the queue is empty.
            raise QueueEmptyError
        return meas
