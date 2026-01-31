'''
Generic messaging interfaces for MEM messaging patterns

These interfaces are for advanced usage only.
Custom Guides, Controllers, and Listeners should subclass from their
corresponding specific messaging interface classes.
'''

from collections.abc import Sequence
import logging
from typing import Optional

import zmq

from measurement_event_manager.event_manager import EventManager
from measurement_event_manager.util.errors import (
    SocketUnavailableError,
    ConnectionTimeoutError,
)


###############################################################################
## Generic messaging interfaces
###############################################################################


## Base messaging interface
###########################


class MessageInterface:
    """Generic MEM messaging interface

    A wrapper around Python ZeroMQ functions to handle (un)packing messages
    using the MEM protocols.
    This is intended to be the parent class for all MEM interfaces.
    """


    def __init__(self,
        socket: Optional[zmq.Socket] = None,
        protocol_name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        ):
        """
        The socket and protocol name are optional on *creation*, but are
        required by the time the interface is first used to send messages.

        Args:
            socket: The corresponding ZeroMQ socket, already bound/connected.
            protocol_name: The name of the MEM protocol definition used to
                parse messages.
            logger: A logger instance; a stdlib logger will be created if it
                is not supplied here.

        Returns:
            A MessageInterface instance.
        """

        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.addHandler(logging.NullHandler())
        else:
            self.logger = logger
        self.set_socket(socket)
        self.protocol_name = protocol_name


    def set_socket(self,
        socket: Optional[zmq.Socket] = None,
        ) -> bool:
        """Set the ZeroMQ socket for messaging.

        Args:
            socket: A ZeroMQ socket, already bound/connected.

        Returns:
            True if the socket was successfully updated, False otherwise.
        """

        if socket is not None:
            self.socket = socket
            self.logger.debug('Socket updated.')
            return True
        return False


    def _pack_message(self,
        header: str,
        body: Optional[Sequence[str]] = None,
        ) -> list:
        """Prepare a message for sending

        Args:
            header: A valid message header under the specified MEM protocol.
            body: A sequence of strings making up the message contents.

        Returns:
            The message as a list of binary strings, ready for sending through
            ZeroMQ.
        """

        full_message_raw = [self.protocol_name, header]
        if body:
            full_message_raw.extend(body)
        full_message = [xx.encode() for xx in full_message_raw]
        return full_message


    def _unpack_message(self,
        message_raw: Sequence[str],
        ) -> dict:
        """Parse a received message

        Args:
            message_raw: A message received from a ZeroMQ socket.

        Returns:
            A dict containing the message protocol, header, and body, keyed as
            such. The protocol and header are single strings, while the body is
            a list.
        """

        ## Decode all parts of the message from binary
        message = [part.decode() for part in message_raw]
        ## Assign parts to output dict
        message_dict = {
            "protocol": message[0],
            "header": message[1],
            "body": message[2:],
        }
        return message_dict


    def _send_message(self,
        header: str,
        body: Optional[Sequence[str]] = None,
        ) -> None:
        """Send a message to the socket.

        Args:
            header: A valid message header under the specified MEM protocol.
            body: A sequence of strings making up the message contents.

        Raises:
            SocketUnavailableError: The socket does not exist or is closed.
        """

        ## Make sure we have an open socket
        if (self.socket is None) or (self.socket.closed):
            raise SocketUnavailableError

        ## Pack message
        message = self._pack_message(header, body)

        ## Send the message
        self.logger.debug('Sending message:')
        self.logger.debug(message)
        self.socket.send_multipart(message)


## Request interface for REQ-REP
################################


class RequestInterface(MessageInterface):
    """A generic interface for the REQ socket of a REQ-REP pattern
    """

    def _send_request(self,
        header: str,
        body: Optional[Sequence[str]] = None,
        ) -> dict:
        """Send a request and receive the reply

        Args:
            header: A valid message header under the specified MEM protocol.
            body: A sequence of strings making up the message contents.

        Returns:
            A dict containing the message protocol, header, and body, keyed as
            such. The protocol and header are single strings, while the body is
            a list.

        Raises:
            ConnectionTimeoutError: Receiving a reply took too long
        """

        ## Package and send the request
        self._send_message(header, body)

        ## Wait for the response
        try:
            reply_wrapped = self.socket.recv_multipart()
        except zmq.error.Again:
            self.socket.close()
            raise ConnectionTimeoutError

        ## Unpack the response
        self.logger.debug('Received reply:')
        self.logger.debug(reply_wrapped)
        reply_dict = self._unpack_message(reply_wrapped)
        return reply_dict


## Reply interface for REQ-REP
##############################


class ReplyInterface(MessageInterface):
    """A generic interface for the REP socket of a REQ-REP pattern
    """


    def __init__(self, server: EventManager, **kwargs):
        """
        Args:
            server: The object that will use this interface to send messages.
                Currently only EventManager is supported.
            **kwargs: Passed to the MessageInterface constructor.
        """
        self._server = server
        super(ReplyInterface, self).__init__(**kwargs)


    def _receive_request(self) -> dict:
        """Receive and parse a request

        Returns:
            A dict containing the request protocol, header, and body, keyed as
            such. The protocol and header are single strings, while the body is
            a list.
        """

        ## Receive and unpack request
        request_wrapped = self.socket.recv_multipart()
        self.logger.debug('Received request:')
        self.logger.debug(request_wrapped)
        request_dict = self._unpack_message(request_wrapped)

        return request_dict
    

    def _send_reply(self,
        header: str,
        body: Optional[Sequence[str]] = None,
        ) -> None:
        """Send a reply

        Args:
            header: A valid message header under the specified MEM protocol.
            body: A sequence of strings making up the message contents.
        """

        ## Package and send the reply
        self._send_message(header, body)


## Broadcast interface for PUB-SUB
##################################


class BroadcastInterface(MessageInterface):

    def _send_broadcast(self, header, body):
        
        self._send_message(header, body)

