'''
A queue for storing measurement parameters, managed by the 
MeasurementEventManager.
'''

import collections
import copy


###############################################################################
## Errors and warnings
###############################################################################


## I don't think we want to subclass QueueEmptyError from IndexError directly,
## as it seems logical to distinguish when the queue is empty (which is not in
## of itself a bad occurrence) from when we have supplied an invalid index for
## queue operations, which indicates a bona-fide user error.
## So instead, we will subclass it from LookupError, which is the parent of
## IndexError.
class QueueEmptyError(LookupError):
    pass


###############################################################################
## MeasurementQueue class
###############################################################################


class MeasurementQueue(object):

    ## Init and setup
    #################

    def __init__(self):
        self.queue = collections.deque()


    ## Queue management
    ###################


    def add(self, measurement_params):
        '''Add a measurement to the end of the queue
        '''
        self.queue.append(measurement_params)
        ## Return the index at which the measurement was added
        return len(self.queue)-1


    def info(self):
        '''Give information about the queue to the client
        '''
        ## Here, we want to ensure the client can't modify the queue, so we
        ## pass a deepcopy just to be safe.
        ## The client is responsible for displaying the information in the way
        ## the user wants.
        ## TODO Figure out if this deepcopy is necessary or if it is done
        ## naturally at some point in the process?
        return list(copy.deepcopy(self.queue))


    def remove(self, index=-1):
        '''Remove the measurement at the specified index
        '''
        ## TODO allow this to operate on a range of indices
        try:
            del self.queue[index]
        except IndexError:
            ## Index is out of range
            ## Can be because the index is invalid or the queue is empty
            ## TODO differentiate between these two cases properly
            return False
        else:
            return True


    def pop_next(self):
        '''Pop off and return the first measurement in the queue
        '''
        try:
            meas = self.queue.popleft()
        except IndexError:
            ## In this case, as we are always trying to fetch the first
            ## element, an IndexError can only occur if the queue is empty.
            raise QueueEmptyError
        else:
            return meas

