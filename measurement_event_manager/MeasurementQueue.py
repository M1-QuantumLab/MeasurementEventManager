'''
A queue for storing measurement parameters, managed by the 
MeasurementEventManager.
'''

import collections


###############################################################################
## MeasurementQueue class
###############################################################################


class MeasurementQueue(object):

    ## Init and setup
    #################

    def __init__(self):
        self.queue = collections.deque()

        ## Temporary incremental counter to test queue functionality
        self.meas_counter = 0

    ## Queue management
    ###################

    
    def add(self, measurement_params):
        self.queue.append([self.meas_counter])
        self.meas_counter += 1
        return True
    

    def info(self):
        ## TODO
        pass


    def remove(self, index=0):
        del self.queue[index]
        return True
    
