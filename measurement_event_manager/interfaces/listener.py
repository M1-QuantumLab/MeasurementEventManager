"""
Listener messaging interfaces

These interfaces provide communication between the EventManager and Listener
instances, according to the MEM-LS protocol specification.
"""

from ..measurement import Measurement, from_json
from .generic import (
    BroadcastInterface,
    SubscribeInterface,
)


###############################################################################
## Listener protocol PUB and SUB interfaces
###############################################################################


## Server PUB interface
#######################


class ListenerPublishInterface(BroadcastInterface):
    """An interface for publishing in the Listener PUB-SUB paradigm

    This interface should be associated with the EventManager service,
    broadcasting information about the most recently completed measurement
    to any Listeners.
    """


    def publish(self, measurement_info: str) -> None:
        """Publish completed measurement information
        """
        self._send_broadcast(header="COM", body=[measurement_info])


## Listener SUB interface
#########################


class ListenerSubscribeInterface(SubscribeInterface):
    """An interface for receiving broadcasts in the Listener PUB-SUB paradigm

    This interface should be associated with the Listener service(s),
    receiving information about completed measurements, and executing
    further actions based on it.
    """

    def receive(self) -> Measurement:
        """Receive the measurement specification of the completed measurement
        """
        spec = self._receive_broadcast()
        return from_json(spec["body"][0])
