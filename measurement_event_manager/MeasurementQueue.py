'''
A queue for storing measurement parameters, managed by the 
MeasurementEventManager.
'''

import collections
import copy


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
        del self.queue[index]
        return True

