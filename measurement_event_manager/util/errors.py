'''
Custom errors and exceptions for the MeasurementEventManager 
ecosystem.
'''


###############################################################################
## Generic ecosystem errors
###############################################################################


## Python has some built-in network connectivity errors, but those are all
## subclasses of OSError and are all intended for system-level network issues.
## So we definitely don't want to be subclassing those! 
## If we start needing more of our own exceptions, we can probably do something
## like a generic NetworkError (iheriting from RuntimeError) which then
## subclasses to all the specific ones we would want.
class ConnectionTimeoutError(RuntimeError):
    pass


###############################################################################
## Measurement and queue-related errors
###############################################################################


## I don't think we want to subclass QueueEmptyError from IndexError directly,
## as it seems logical to distinguish when the queue is empty (which is not in
## of itself a bad occurrence) from when we have supplied an invalid index for
## queue operations, which indicates a bona-fide user error.
## So instead, we will subclass it from LookupError, which is the parent of
## IndexError.
class QueueEmptyError(LookupError):
    pass

