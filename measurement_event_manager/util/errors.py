'''
Custom errors and exceptions for the MeasurementEventManager 
ecosystem.
'''


###############################################################################
## Network errors
###############################################################################


## Python has some built-in network connectivity errors, but those are all
## subclasses of OSError and are all intended for system-level network issues.
## So we definitely don't want to be subclassing those!

class NetworkError(RuntimeError):
    """An error in the MEM communication layer
    """
    pass

class SocketUnavailableError(NetworkError):
    """The requested ZeroMQ socket is unavailable
    """
    pass

class ConnectionTimeoutError(NetworkError):
    """The associated ZeroMQ socket is taking too long to respond
    """
    pass


###############################################################################
## Protocol and messaging errors
###############################################################################


class ServerError(RuntimeError):
    """An unspecified error has occurred on the server-side
    """
    pass

class MessagingError(RuntimeError):
    """The received message is inappropriate or malformed
    """
    pass

class HeaderError(MessagingError):
    """The received message contains the wrong header
    """
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
    """The queue is empty, resulting in an invalid lookup
    """
    pass

